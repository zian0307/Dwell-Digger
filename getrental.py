#!/usr/bin/env python
# coding=utf-8
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import time

# 設定 Firefox 瀏覽器選項
firefox_options = Options()
firefox_options.headless = False  # 如果你想要背景執行，設置為 True

# 初始化瀏覽器，使用 webdriver-manager 自動下載和設置 geckodriver
firefox_service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

try:
    # 瀏覽到目標網頁
    driver.get('https://rent.591.com.tw/?region=1')
    time.sleep(5)
    
    # 取得最後一個頁碼元素
    last_page_element = driver.find_elements(By.CLASS_NAME, 'pageNum-form')[-1]
    last_page_number = int(last_page_element.text)

    rental_ids = []
    
    # 用迴圈跑所有頁面
    for page in range(2, last_page_number + 1):
        try:
            first_row = page * 30
            
            # 構建目標 URL
            url = f'https://rent.591.com.tw/?region=1&firstRow={first_row}'
    
            # 訪問目標 URL
            driver.get(url)
            time.sleep(5)  # 可以根據網頁加載情況調整
    
            # 找到所有具有指定 class 和 data-bind 屬性的元素
            elements = driver.find_elements(By.XPATH, '//*[@class="vue-list-rent-item"][@data-bind]')
    
            # 提取每個元素的 data-bind 屬性值，並將其存儲到列表中
            for element in elements:
                data_bind_value = element.get_attribute('data-bind')
                rental_ids.append(data_bind_value)
    
            print(f"目前第 {page} 頁，已取得 {len(rental_ids)} 筆資料")
            
        except Exception as e:
            print(f"第 {page} 頁搜尋時發生錯誤：{e}")
        
    unique_rental_ids = list(set(rental_ids))
    
finally:
    # 關閉瀏覽器
    driver.quit()