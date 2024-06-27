import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# 載入數據
df = pd.read_excel("591_rental_data.xlsx")

# 準備文本數據
df['text'] = df['標題'] + ' ' + df['區域'] + ' ' + df['區段'] + ' ' + df['類型'] + ' ' + df['型態']

# 創建TF-IDF向量
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(df['text'])

# 自然語言查詢函數
def natural_language_query(query):
    # 對查詢進行預處理
    tokens = word_tokenize(query.lower())
    stop_words = set(stopwords.words('chinese'))
    tokens = [token for token in tokens if token not in stop_words]
    processed_query = ' '.join(tokens)

    # 將查詢轉換為TF-IDF向量
    query_vector = vectorizer.transform([processed_query])

    # 計算相似度
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # 獲取最相似的結果
    similar_indices = cosine_similarities.argsort()[::-1][:5]  # 取前5個結果
    similar_items = df.iloc[similar_indices]

    return similar_items

# 使用示例
query = "我想找台北市大安區的兩房公寓，預算在30000以下"
results = natural_language_query(query)
print(results[['標題', '區域', '區段', '類型', '價格', '房數']])