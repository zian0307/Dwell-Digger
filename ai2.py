import re
import os
import sqlite3
import pandas as pd
from openai import OpenAI

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 創建數據庫連接
conn = sqlite3.connect('rental_database.db')

def generate_sql_query(user_query):
    prompt = f"""
    Given the following SQLite table schema:
    
    CREATE TABLE rentals (
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

    Generate a SQL query to answer the following user question:
    {user_query}

    The query should be valid SQLite syntax and should only return relevant columns.
    Only return the SQL query without any additional text or explanation.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates SQL queries based on user questions about rental properties."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def extract_sql_query(response):
    # 使用正則表達式提取 SQL 查詢
    sql_pattern = r"```sql\s*([\s\S]*?)\s*```"
    match = re.search(sql_pattern, response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        # 如果沒有找到 SQL 代碼塊，就返回整個回應
        return response.strip()

def execute_sql_query(query):
    try:
        result = pd.read_sql_query(query, conn)
        return result
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return None

def natural_language_query(user_query):
    generated_response = generate_sql_query(user_query)
    sql_query = extract_sql_query(generated_response)
    print(f"Generated SQL query: {sql_query}")
    results = execute_sql_query(sql_query)
    return results

# 使用示例
user_query = "找出花蓮縣花蓮市的租屋，價格在10000以下的前5筆資料"
results = natural_language_query(user_query)

if results is not None and not results.empty:
    print(results)
else:
    print("No results found or an error occurred.")

# 關閉數據庫連接
conn.close()