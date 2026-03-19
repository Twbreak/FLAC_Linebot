import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 載入 .env 檔案中的變數
load_dotenv()

app = FastAPI()

# --- 從環境變數中讀取資訊 ---
# os.getenv 會去讀取 .env 檔案裡對應的 Key
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 安全檢查：確保環境變數有被正確讀取
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("請確保 .env 檔案中已設定 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_CHANNEL_SECRET")
# ----------------------------

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        print("簽章驗證失敗，請檢查 CHANNEL_SECRET")
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        user_text = event.message.text
        print(f"成功接收訊息: {user_text}")

        # 回傳訊息給使用者
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"後端接收成功！你說了：{user_text}")]
            )
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)