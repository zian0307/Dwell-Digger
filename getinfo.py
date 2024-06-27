import os
import xlwings as xw
import time
import random
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def initialize_excel(filename):
    app = xw.App(visible=False)
    if os.path.exists(filename):
        wb = app.books.open(filename)
    else:
        wb = app.books.add()
        sheet = wb.sheets[0]
        sheet.range("A1:M1").value = [
            "租屋編號", "標題", "區域", "區段", "類型", "價格", "型態",
            "房數", "坪數", "樓層", "地址", "發布日期", "連結"
        ]
        sheet.range("A2").options(transpose=True).value = rental_ids
        wb.save(filename)
    return app, wb

def process_rental(rental_id, row_index):
    try:
        time.sleep(random.uniform(1, 3))
        rental_detail = get_rental_detail(rental_id)
        gtm_detail_data = rental_detail.get("gtm_detail_data", {})
        fav_data = rental_detail.get("favData", {})
        
        try:
            post_date = datetime.datetime.fromtimestamp(fav_data.get("posttime")).date()
        except Exception as e:
            post_date = ""
            print(f"轉換時間戳時發生錯誤，編號: {rental_id}，錯誤訊息：{e}")

        row_data = [
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
        return row_index, row_data
    except Exception as e:
        print(f"無法取得第{row_index}筆租屋詳細資訊，編號: {rental_id}，錯誤訊息：{e}")
        return row_index, None

def main():
    filename = "591_rental_data.xlsx"
    app, wb = initialize_excel(filename)
    sheet = wb.sheets[0]

    num_rental_rows = len(sheet.range("A1").expand("down"))

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for row_index in range(2, num_rental_rows + 1):
            rental_id = int(sheet[f"A{row_index}"].value)
            futures.append(executor.submit(process_rental, rental_id, row_index))

        for future in as_completed(futures):
            row_index, row_data = future.result()
            if row_data:
                sheet[f"B{row_index}"].value = row_data
                print(f"第{row_index}筆資料取得成功，編號為{sheet[f'A{row_index}'].value}的租屋資訊")
            wb.save(filename)

    wb.close()
    app.quit()

if __name__ == "__main__":
    main()