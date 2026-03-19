import base64
import re
from fastapi import FastAPI, Request, HTTPException
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, 
    MessagingApiBlob, ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.exceptions import InvalidSignatureError
import os
from dotenv import load_dotenv

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

# --- 處理文字訊息 (含網址偵測) ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_text = event.message.text
    
    # 正則表達式偵測網址
    urls = re.findall(r'https?://[^\s]+', user_text)
    msg_type = "url" if urls else "text"

    # 整理標準 JSON
    standard_json = {
        "metadata": {
            "user_id": event.source.user_id,
            "timestamp": event.timestamp,
            "message_id": event.message.id
        },
        "payload": {
            "type": msg_type,
            "content": user_text,
            "url_list": urls
        }
    }
    
    # TODO: 此處將 standard_json 傳送給你的下一個後端 API
    print(f"成功整理文字資料: {standard_json}")
    reply_message(event.reply_token, f"成功接收{msg_type}資料並已封裝。")

# --- 處理圖片訊息 (轉 Base64) ---
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    with ApiClient(configuration) as api_client:
        line_bot_blob = MessagingApiBlob(api_client)
        # 下載二進位內容
        image_content = line_bot_blob.get_message_content(event.message.id)
        
        # 轉換為 Base64
        base64_image = base64.b64encode(image_content).decode('utf-8')

        # 整理標準 JSON
        standard_json = {
            "metadata": {
                "user_id": event.source.user_id,
                "timestamp": event.timestamp,
                "message_id": event.message.id
            },
            "payload": {
                "type": "image",
                "image_base64": base64_image,
                "extension": "jpg"
            }
        }

        # TODO: 此處將 standard_json 傳送給你的下一個後端 API
        print(f"成功整理圖片資料，Base64 長度: {len(base64_image)}")
        reply_message(event.reply_token, "成功接收圖片資料並已轉換為 Base64 格式。")

def reply_message(token, text):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=token,
                messages=[TextMessage(text=text)]
            )
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)