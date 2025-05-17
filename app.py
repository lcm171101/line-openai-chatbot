
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import openai

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def GPT_response(text):
    try:
        # 預設使用 GPT-4
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return "[GPT-4]\n" + response.choices[0].message.content.strip()

    except openai.APIError as e:
        # 若 quota 用盡，顯示簡潔訊息
        if "insufficient_quota" in str(e):
            return "⚠️ 你的 OpenAI API 配額已用盡，請前往 OpenAI 平台儲值後再使用。"
        print(f"⚠️ GPT-4 Error: {e}")

        try:
            # 嘗試切換 GPT-3.5
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": text}]
            )
            return "[GPT-3.5]\n" + response.choices[0].message.content.strip()
        except Exception as ee:
            if "insufficient_quota" in str(ee):
                return "⚠️ 你的 OpenAI API 配額已用盡，請至 https://platform.openai.com/account/billing 儲值。"
            return f"❌ 無法處理請求：{str(ee)}"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    reply = GPT_response(user_text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
