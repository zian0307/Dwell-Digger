import os
import time
import random
import datetime
import requests
import sqlite3
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException
from webdriver_manager.firefox import GeckoDriverManager
from fake_useragent import UserAgent
from functools import lru_cache
import pandas as pd
import concurrent.futures

@lru_cache(maxsize=1)
def get_user_agent():
    return UserAgent()

def setup_driver():
    firefox_options = Options()
    firefox_options.headless = True
    user_agent = get_user_agent().random
    firefox_options.add_argument(f'user-agent={user_agent}')
    firefox_service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=firefox_service, options=firefox_options)

def get_rental_ids(driver, page, region):
    first_row = (page - 1) * 30
    url = f'https://rent.591.com.tw/?region={region}&firstRow={first_row}'
    
    try:
        driver.get(url)
        
        # 處理可能出現的警告對話框
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.dismiss()
            print(f"警告對話框已關閉：{alert.text}")
        except TimeoutException:
            pass
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@class="vue-list-rent-item"][@data-bind]'))
        )
        elements = driver.find_elements(By.XPATH, '//*[@class="vue-list-rent-item"][@data-bind]')
        return [element.get_attribute('data-bind') for element in elements]
    except UnexpectedAlertPresentException as e:
        print(f"第 {page} 頁搜尋時發生警告對話框：{e}")
        return []
    except Exception as e:
        print(f"第 {page} 頁搜尋時發生錯誤：{e}")
        return []

def get_rental_ids_with_retry(driver, page, region, max_retries=3):
    for attempt in range(max_retries):
        try:
            ids = get_rental_ids(driver, page, region)
            if ids:
                return ids
        except Exception as e:
            print(f"嘗試 {attempt + 1}/{max_retries} 失敗: {e}")
        time.sleep(random.uniform(2, 5))  # 隨機等待
    print(f"第 {page} 頁在 {max_retries} 次嘗試後仍然失敗")
    return []

def get_rental_detail(rental_id, retries=5, backoff_factor=0.3):
    ua = get_user_agent()
    headers = {"User-Agent": ua.random}
    
    session = requests.Session()
    
    for attempt in range(retries):
        try:
            initial_url = f"https://rent.591.com.tw/home/{rental_id}"
            response = session.get(initial_url, headers=headers, timeout=10)
            response.raise_for_status()

            cookies = session.cookies.get_dict()
            headers.update({
                "deviceid": cookies.get("T591_TOKEN"),
                "device": "pc",
                "X-CSRF-TOKEN": cookies.get("XSRF-TOKEN")
            })

            detail_url = f"https://bff.591.com.tw/v1/house/rent/detail?id={rental_id}"
            response = session.get(detail_url, headers=headers, timeout=10)
            response.raise_for_status()

            return response.json().get("data")

        except requests.RequestException as e:
            if attempt == retries - 1:
                print(f"無法取得租屋詳細資訊，編號: {rental_id}，錯誤訊息：{e}")
                return None
            wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(wait_time)

def process_rental(rental_id):
    rental_detail = get_rental_detail(rental_id)
    if not rental_detail:
        return None

    gtm_detail_data = rental_detail.get("gtm_detail_data", {})
    fav_data = rental_detail.get("favData", {})
    
    try:
        post_date = datetime.datetime.fromtimestamp(fav_data.get("posttime")).date()
    except Exception as e:
        post_date = ""
        print(f"轉換時間戳時發生錯誤，編號: {rental_id}，錯誤訊息：{e}")

    return [
        rental_id,
        gtm_detail_data.get("item_name", ""),
        gtm_detail_data.get("region_name", ""),
        gtm_detail_data.get("section_name", ""),
        gtm_detail_data.get("kind_name", ""),
        gtm_detail_data.get("price_name", ""),
        gtm_detail_data.get("shape_name", ""),
        gtm_detail_data.get("layout_name", ""),
        gtm_detail_data.get("area_name", ""),
        gtm_detail_data.get("floor_name", "").replace("F", ""),
        fav_data.get("address", ""),
        post_date,
        f"https://rent.591.com.tw/home/{rental_id}",
    ]

def main():
    region = input("請輸入要搜尋的區域代碼：")
    driver = setup_driver()
    conn = sqlite3.connect('rental_database.db')
    cursor = conn.cursor()

    try:
        driver.get(f'https://rent.591.com.tw/?region={region}')
        
        # 等待租屋列表加載
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@class="vue-list-rent-item"][@data-bind]'))
        )
        
        # 嘗試獲取最後一頁的數字
        try:
            last_page_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pageNum-form'))
            )
            last_page_number = int(last_page_element.text)
        except TimeoutException:
            # 如果找不到分頁元素，假設只有一頁
            last_page_number = 1
        
        print(f"總共有 {last_page_number} 頁")

        rental_ids = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_page = {executor.submit(get_rental_ids_with_retry, driver, page, region): page 
                              for page in range(1, last_page_number + 1)}
            for future in concurrent.futures.as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    page_ids = future.result()
                    rental_ids.update(page_ids)
                    print(f"目前第 {page} 頁，總共取得 {len(rental_ids)} 筆資料")
                    time.sleep(random.uniform(1, 3))  # 隨機等待 1-3 秒
                except Exception as e:
                    print(f"處理第 {page} 頁時發生錯誤：{e}")
    finally:
        driver.quit()

    print(f"總共取得 {len(rental_ids)} 筆唯一資料")

    # 處理租屋詳細資訊
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_id = {executor.submit(process_rental, rental_id): rental_id for rental_id in rental_ids}
        for future in concurrent.futures.as_completed(future_to_id):
            rental_id = future_to_id[future]
            try:
                result = future.result()
                if result:
                    data.append(result)
                    print(f"處理成功：租屋編號 {rental_id}")
            except Exception as e:
                print(f"處理租屋編號 {rental_id} 時發生錯誤：{e}")

    # 創建 DataFrame 並保存到數據庫
    df = pd.DataFrame(data, columns=[
        "id", "title", "region", "section", "type", "price", "shape",
        "rooms", "area", "floor", "address", "post_date", "link"
    ])
    df.to_sql('rentals', conn, if_exists='append', index=False)
    print("資料已保存到數據庫")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()