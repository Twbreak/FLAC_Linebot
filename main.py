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

import boto3
import json

# 載入 .env 檔案中的變數
load_dotenv()

bedrock_prompt = """

# Role: 專業防詐騙風險評估專員

## Description
你是一名經驗豐富、洞察力極強的防詐專員。你的任務是分析使用者提供的對話內容或訊息，並根據內建的詐騙知識庫進行嚴謹的風險評估。

## Evaluation Criteria
請針對以下特徵類別進行對比與評估：

### 1. [假投資詐騙]
- **特徵話術：** 社群媒體財富自由形象、高報酬幣種/錢包地址、假平台數據、出金需繳保證金、失聯。
- **犯罪手法：** 免費投資秘笈/書籍、股票健檢、LINE群組教學、內線消息/大戶當沖、低價申購新股/必中籤系統、AI投資機器人、面交現金、避開行員詢問（稱工程款/修繕/借款）、金管會稅金/自證金/風險認證金。

### 2. [假檢警詐騙]
- **特徵話術：** 稱身分遭冒用（健保卡/戶籍謄本/門號）、涉及洗錢或販毒刑案、偵查不公開/監聽中、要求線上筆錄、監管帳戶/保管財產、LINE傳送假公文、超商收傳真、支付保證金以防凍結、交付存摺/提款卡。

### 3. [假交友/徵婚詐財]
- **特徵話術：** 海外身分（美國軍醫/機長/建商）、寄送禮品/包裹需付運費、移民/返台結婚需財力證明、開通外幣收款、借用帳戶、家人醫藥費、投資認證、寄送SIM卡/存簿（賣貨便）。

## Output Format
請依據以下格式進行回覆：

---
### 🛡️ 防詐風險評估報告

- **風險評分：** [1-10分] 
*(1-3低風險、4-6中風險、7-9高風險、10極高風險)*
- **詐騙類別：** [例如：假檢警詐騙 / 假投資詐騙 / 假交友詐騙]
- **風險分析：** - [列出內容中符合上述特徵的具體關鍵字或行為]
- [分析其心理攻勢或威脅手段]
- **專員警示：** [給予使用者的具體行動建議，例如：掛斷電話、撥打165、切勿匯款等]
---

## Input Content
           
"""


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


    response = Bedrock_response(user_text)


    reply_message(event.reply_token, f"成功接收{msg_type}資料並已封裝，分析結果{response}。")

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


def Bedrock_response(content):

    client = boto3.client(
        "bedrock-runtime", 
        region_name="ap-southeast-2",
        aws_access_key_id='',
        aws_secret_access_key=''
    )
    
    # Gemma 3 的模型 ID
    model_id = 'google.gemma-3-4b-it'

    # 修正重點 1：Gemma 3 要求 messages 陣列
    native_request = {
        "messages": [
            {
                "role": "user",
                "content": bedrock_prompt + content
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(native_request)
        )
        
        response_body = json.loads(response.get('body').read())
        
        # 修正重點 2：解析回傳內容
        # Gemma 3 通常回傳格式為 {"choices": [{"message": {"content": "..."}}]}
        if 'choices' in response_body:
            return response_body['choices'][0]['message']['content']
        else:
            return f"格式不符，原始回應：{response_body}"

    except Exception as e:
        return f"發生錯誤：{str(e)}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)