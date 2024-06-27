from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import threading
from new_rental import main as scraper_main  # 導入您的爬蟲主函數

app = Flask(__name__)

# 填入您的 Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi('D5kiI87mZfuOalafrZ12KGVWQ8D9WPjE8p0ubn0rhBY5KroF0tjEFiH8s4fQTt+q/MiPeuSMra8hfXi1zGIqErKB2aJumTOjpWuUJokHQR/cFp+chw2Gv+QCuFpKXr0TNU9QsUpmD91rOqfSUDbiPQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('4e0486fd4afacd867242d62a2a282a4d')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "開始爬取":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="開始爬取租屋資訊，這可能需要一些時間...")
        )
        threading.Thread(target=run_scraper, args=(event.source.user_id,)).start()
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入「開始爬取」來啟動爬蟲程序。")
        )

def run_scraper(user_id):
    try:
        scraper_main()  # 運行爬蟲
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="爬取完成！資料已保存到 591_rental_data.xlsx")
        )
    except Exception as e:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=f"爬取過程中發生錯誤：{str(e)}")
        )

if __name__ == "__main__":
    app.run()