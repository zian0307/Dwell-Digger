import sqlite3
import pandas as pd

# 創建數據庫連接
conn = sqlite3.connect('rental_database.db')
cursor = conn.cursor()

# 創建租屋表
cursor.execute('''
CREATE TABLE IF NOT EXISTS rentals (
    id INTEGER PRIMARY KEY,
    title TEXT,
    region TEXT,
    section TEXT,
    type TEXT,
    price INTEGER,
    shape TEXT,
    rooms TEXT,
    area REAL,
    floor INTEGER,
    address TEXT,
    post_date DATE,
    link TEXT
)
''')

# 從Excel文件讀取數據
df = pd.read_excel("591_rental_data.xlsx")

# 將數據插入到數據庫
df.to_sql('rentals', conn, if_exists='append', index=False)

conn.commit()