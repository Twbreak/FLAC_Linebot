import boto3
import json
import os
import re
import logging
from typing import Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

BEDROCK_PROMPT = """
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
請依據以下格式進行回覆（必須嚴格遵守格式）：

---
### 🛡️ 防詐風險評估報告

- **風險評分：** [1-10分] 
*(1-3低風險、4-6中風險、7-9高風險、10極高風險)*
- **詐騙類別：** [例如：假檢警詐騙 / 假投資詐騙 / 假交友詐騙]
- **風險分析：**
  - [列出內容中符合上述特徵的具體關鍵字或行為]
  - [分析其心理攻勢或威脅手段]
- **專員警示：** [給予使用者的具體行動建議，例如：掛斷電話、撥打165、切勿匯款等]
---

## Input Content
"""

def parse_bedrock_response(response_text: str) -> Dict:
    """解析 Bedrock 回應，提取結構化資料"""
    
    # 預設值
    result = {
        "risk_score": 0,
        "category": "未分類",
        "analysis": [],
        "expert_warning": "請保持警覺"
    }
    
    try:
        # 提取風險評分（支援多種格式）
        # 格式範例：8、8分、8/10、[8]、**8**、** 8 **
        score_patterns = [
            r'風險評分[：:]\s*\*?\*?\s*\[?\s*(\d+)\s*\]?\s*(?:分|/10)?',  # 主要格式
            r'\*\*風險評分[：:]\*\*\s*(\d+)',  # Markdown 粗體格式
            r'風險評分.*?(\d+)',  # 備用：任何包含數字的格式
        ]
        
        score_found = False
        for pattern in score_patterns:
            score_match = re.search(pattern, response_text)
            if score_match:
                score = int(score_match.group(1))
                # 確保分數在 0-10 範圍內
                result["risk_score"] = max(0, min(10, score))
                logger.info("Bedrock score parsed successfully: score=%s", result['risk_score'])
                score_found = True
                break
        
        if not score_found:
            # 如果找不到明確的風險評分，嘗試從內容推斷
            # 檢查是否包含高風險關鍵字
            high_risk_keywords = ['極高風險', '高風險', '詐騙', '假投資', '假檢警', '假交友']
            medium_risk_keywords = ['中風險', '可疑', '需注意']
            
            content_lower = response_text.lower()
            if any(keyword in response_text for keyword in high_risk_keywords):
                # 如果內容提到高風險但沒有明確分數，給予 7 分
                result["risk_score"] = 7
                logger.warning("No explicit Bedrock score found; inferred score=7 from content")
            elif any(keyword in response_text for keyword in medium_risk_keywords):
                result["risk_score"] = 5
                logger.warning("No explicit Bedrock score found; inferred score=5 from content")
        
        # 提取詐騙類別
        category_match = re.search(r'詐騙類別[：:]\s*\*?\*?([^\n]+)', response_text)
        if category_match:
            result["category"] = category_match.group(1).strip()
        
        # 提取風險分析（多行）
        analysis_section = re.search(r'風險分析[：:]\s*\*?\*?(.*?)(?=\*?\*?專員警示|$)', response_text, re.DOTALL)
        if analysis_section:
            analysis_text = analysis_section.group(1).strip()
            # 分割成多個要點
            analysis_points = [line.strip('- ').strip() for line in analysis_text.split('\n') if line.strip() and line.strip() != '-']
            result["analysis"] = [p for p in analysis_points if p]
        
        # 提取專員警示
        warning_match = re.search(r'專員警示[：:]\s*\*?\*?([^\n]+)', response_text)
        if warning_match:
            result["expert_warning"] = warning_match.group(1).strip()
        
        # 除錯輸出
        logger.info("Bedrock response parsed: risk_score=%s category=%s", result['risk_score'], result['category'])
            
    except Exception as e:
        logger.exception("Failed to parse Bedrock response: error=%s", e)
    
    return result

def analyze_scam_content(content: str) -> Dict:
    """使用 AWS Bedrock 分析詐騙內容"""
    
    try:
        # 取得 AWS 憑證（支援大小寫）
        aws_access_key_id = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        model_id = 'google.gemma-3-12b-it'
        
        native_request = {
            "messages": [
                {
                    "role": "user",
                    "content": BEDROCK_PROMPT + content
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(native_request)
        )
        
        response_body = json.loads(response.get('body').read())
        
        # 提取回應內容
        if 'choices' in response_body:
            raw_response = response_body['choices'][0]['message']['content']
        else:
            raw_response = str(response_body)
        
        # 解析結構化資料
        parsed_result = parse_bedrock_response(raw_response)
        parsed_result['raw_response'] = raw_response  # 保留原始回應
        
        return parsed_result
        
    except Exception as e:
        return {
            "risk_score": 0,
            "category": "系統錯誤",
            "analysis": [f"分析失敗：{str(e)}"],
            "expert_warning": "系統暫時無法分析，請稍後再試",
            "raw_response": str(e)
        }


# Prompt for mass report alert generation
MASS_REPORT_ALERT_PROMPT = """
# Role: 社群防詐警示生成專員

## Description
你是一名專業的防詐警示生成專員。你的任務是根據大量使用者通報的詐騙訊息，生成簡潔、安全的警示摘要與防範建議。

## Important Guidelines
1. **隱私保護**：絕對不要在摘要中包含原始訊息的完整內容或敏感資訊
2. **簡潔明確**：摘要應該簡短（50-100字），重點突出詐騙手法特徵
3. **實用建議**：提供具體、可執行的防範建議

## Output Format
請依據以下格式進行回覆（必須嚴格遵守格式）：

---
### 警示摘要
[簡短描述詐騙手法特徵，不包含原始訊息內容]

### 防範建議
[具體的防範措施與行動建議]
---

## Input Information
- **通報次數：** {report_count} 次
- **訊息內容：** {original_message}
"""


class BedrockSummarizer:
    """使用 AWS Bedrock LLM 生成大量通報警示摘要"""
    
    def __init__(self):
        """初始化 Bedrock 客戶端與模型配置"""
        # 取得 AWS 憑證（支援大小寫）
        self.aws_access_key_id = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = 'google.gemma-3-12b-it'
        
        # 初始化 Bedrock 客戶端（配置 10 秒超時）
        from botocore.config import Config
        config = Config(
            read_timeout=10,
            connect_timeout=10
        )
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=config
        )
    
    def generate_mass_report_alert(self, original_message: str, report_count: int) -> dict:
        """
        生成大量通報警示摘要
        
        Args:
            original_message: 原始詐騙訊息內容
            report_count: 通報次數
        
        Returns:
            dict: 包含 alert_summary 和 alert_warning 的字典
        
        Requirements: 3.2, 3.3, 3.4, 3.7
        """
        try:
            # 構建提示詞
            prompt = MASS_REPORT_ALERT_PROMPT.format(
                report_count=report_count,
                original_message=original_message
            )
            
            # 構建請求
            native_request = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 512,
                "temperature": 0.5
            }
            
            # 呼叫 Bedrock API（10 秒超時）
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(native_request)
            )
            
            response_body = json.loads(response.get('body').read())
            
            # 提取回應內容
            if 'choices' in response_body:
                raw_response = response_body['choices'][0]['message']['content']
            else:
                raw_response = str(response_body)
            
            # 解析摘要與警示
            parsed_result = self._parse_alert_response(raw_response)
            
            logger.info("Bedrock mass-report alert generated successfully")
            
            return parsed_result
            
        except Exception as e:
            logger.error("Bedrock mass-report alert generation failed: error=%s", e)
            # 返回預設警示訊息
            return self._get_default_alert()
    
    def _parse_alert_response(self, response_text: str) -> dict:
        """解析 LLM 回應，提取警示摘要與防範建議"""
        
        result = {
            "alert_summary": "",
            "alert_warning": ""
        }
        
        try:
            # 提取警示摘要
            summary_match = re.search(r'警示摘要[：:]\s*\*?\*?(.*?)(?=###|防範建議|$)', response_text, re.DOTALL)
            if summary_match:
                result["alert_summary"] = summary_match.group(1).strip()
            
            # 提取防範建議
            warning_match = re.search(r'防範建議[：:]\s*\*?\*?(.*?)(?=###|---|\Z)', response_text, re.DOTALL)
            if warning_match:
                result["alert_warning"] = warning_match.group(1).strip()
            
            # 如果解析失敗，使用預設值
            if not result["alert_summary"] or not result["alert_warning"]:
                logger.warning("Bedrock alert parsing failed; using default alert")
                return self._get_default_alert()
            
        except Exception as e:
            logger.exception("Bedrock alert parsing error: error=%s", e)
            return self._get_default_alert()
        
        return result
    
    def _get_default_alert(self) -> dict:
        """返回預設的安全警示訊息"""
        return {
            "alert_summary": "系統偵測到大量使用者通報相同詐騙訊息，該訊息可能包含詐騙連結或不實資訊",
            "alert_warning": "請提高警覺，避免點擊可疑連結、提供個人資訊或進行任何金錢交易。如有疑慮請撥打 165 反詐騙專線"
        }
