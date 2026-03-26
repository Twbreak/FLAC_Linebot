# notification_dispatcher.py
"""
通知分發服務模組
負責將大量通報警示推送給所有活躍使用者
"""

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, TextMessage, 
    PushMessageRequest, MulticastRequest
)
from linebot.v3.exceptions import BaseError
import boto3
from decimal import Decimal
from database import get_all_active_user_ids
from security import validate_line_channel_access_token

MAX_LINE_MESSAGE_LENGTH = 5000
DEFAULT_ALERT_SUMMARY = "系統偵測到大量使用者通報相同詐騙訊息，請留意可疑話術與連結。"
DEFAULT_ALERT_WARNING = "請勿點擊不明連結、提供個人資料或進行匯款，如有疑慮請撥打 165 反詐騙專線。"
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# DynamoDB 設定
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")

# 初始化 DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


def format_mass_report_notification(alert_summary: str, alert_warning: str, report_count: int) -> str:
    """格式化大量通報通知訊息。"""
    safe_summary = (alert_summary or "").strip() or DEFAULT_ALERT_SUMMARY
    safe_warning = (alert_warning or "").strip() or DEFAULT_ALERT_WARNING

    message = (
        "🚨 社群防詐警示\n\n"
        "📊 系統偵測到大量通報\n"
        f"已有 {report_count} 位使用者通報相同詐騙訊息\n\n"
        "⚠️ 風險摘要：\n"
        f"{safe_summary}\n\n"
        "💡 防範建議：\n"
        f"{safe_warning}\n\n"
        "🛡️ 請提高警覺，保護自己與親友的財產安全！\n\n"
        "📱 如收到類似訊息，請立即通報給我們。"
    )

    if len(message) <= MAX_LINE_MESSAGE_LENGTH:
        return message

    static_length = len(
        message.replace(safe_summary, "", 1).replace(safe_warning, "", 1)
    )
    available_dynamic_length = max(0, MAX_LINE_MESSAGE_LENGTH - static_length)
    summary_budget = max(0, available_dynamic_length // 2)
    warning_budget = max(0, available_dynamic_length - summary_budget)

    truncated_summary = safe_summary[:summary_budget]
    truncated_warning = safe_warning[:warning_budget]

    return (
        "🚨 社群防詐警示\n\n"
        "📊 系統偵測到大量通報\n"
        f"已有 {report_count} 位使用者通報相同詐騙訊息\n\n"
        "⚠️ 風險摘要：\n"
        f"{truncated_summary}\n\n"
        "💡 防範建議：\n"
        f"{truncated_warning}\n\n"
        "🛡️ 請提高警覺，保護自己與親友的財產安全！\n\n"
        "📱 如收到類似訊息，請立即通報給我們。"
    )


class NotificationDispatcher:
    """通知分發服務類別"""
    
    def __init__(self):
        """初始化通知分發服務"""
        # 初始化 LINE Bot API 客戶端
        channel_access_token = validate_line_channel_access_token(
            os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        )
        
        self.configuration = Configuration(access_token=channel_access_token)
        
        # 初始化 DynamoDB 客戶端
        self.scam_reports_table = dynamodb.Table('ScamReports')
        self.team_members_table = dynamodb.Table('TeamMembers')
    
    def get_all_active_users(self) -> List[str]:
        """
        取得所有活躍使用者的 LINE UID
        
        活躍使用者定義：曾經提交過通報或與系統互動過的使用者
        
        Returns:
            List[str]: 有效的 LINE UID 列表（以 'U' 開頭），若無活躍使用者則返回空列表
        """
        try:
            return get_all_active_user_ids(
                scam_reports_table=self.scam_reports_table,
                team_members_table=self.team_members_table
            )
        except Exception as e:
            logger.exception("Failed to load active users: error=%s", e)
            return []
    
    def _build_alert_message(
        self,
        alert_message: str = None,
        alert_summary: str = None,
        alert_warning: str = None,
        report_count: int = None
    ) -> str:
        """建立最終要推送的警示訊息。"""
        if alert_summary is not None or alert_warning is not None or report_count is not None:
            return format_mass_report_notification(
                alert_summary=alert_summary or DEFAULT_ALERT_SUMMARY,
                alert_warning=alert_warning or DEFAULT_ALERT_WARNING,
                report_count=report_count or 0
            )

        if not alert_message:
            raise ValueError("alert_message or alert content fields must be provided")

        if len(alert_message) <= MAX_LINE_MESSAGE_LENGTH:
            return alert_message

        return alert_message[:MAX_LINE_MESSAGE_LENGTH]

    def _split_valid_and_invalid_user_ids(self, user_ids: List[str]) -> tuple[List[str], List[str]]:
        """驗證 UID 格式，避免對無效 ID 呼叫 LINE API。"""
        valid_user_ids = []
        invalid_user_ids = []

        for user_id in user_ids:
            if isinstance(user_id, str) and user_id.startswith('U'):
                valid_user_ids.append(user_id)
            else:
                invalid_user_ids.append(user_id)
                logger.error("Invalid LINE user ID skipped: user_id=%r", user_id)

        return valid_user_ids, invalid_user_ids

    def broadcast_mass_report_alert(
        self,
        alert_message: str = None,
        alert_summary: str = None,
        alert_warning: str = None,
        report_count: int = None
    ) -> Dict[str, any]:
        """
        廣播大量通報警示給所有使用者
        
        Args:
            alert_message: 已格式化的警示訊息內容（不超過 5000 字元）
            alert_summary: 警示摘要
            alert_warning: 防範建議
            report_count: 通報數量
        
        Returns:
            Dict: 包含 success_count, failed_count, failed_users 的結果字典
        """
        message = self._build_alert_message(
            alert_message=alert_message,
            alert_summary=alert_summary,
            alert_warning=alert_warning,
            report_count=report_count
        )

        # 取得所有活躍使用者
        user_ids = self.get_all_active_users()
        
        if not user_ids:
            logger.info("No active users found; skipping mass report broadcast")
            return {
                "success_count": 0,
                "failed_count": 0,
                "failed_users": []
            }
        
        # 呼叫批次推送
        return self.send_push_message(user_ids, message)
    
    def send_push_message(self, user_ids: List[str], message: str) -> Dict[str, any]:
        """
        批次推送訊息給指定使用者
        
        Args:
            user_ids: LINE UID 列表
            message: 推送訊息內容
        
        Returns:
            Dict: 包含 success_count, failed_count, failed_users 的結果字典
        """
        success_count = 0
        failed_users = []
        valid_user_ids, invalid_user_ids = self._split_valid_and_invalid_user_ids(user_ids)
        failed_users.extend(invalid_user_ids)
        
        # LINE API 批次推送限制：每次最多 500 個使用者
        BATCH_SIZE = 500

        if not valid_user_ids:
            logger.info("No valid LINE user IDs available for push delivery")
            return {
                "success_count": 0,
                "failed_count": len(failed_users),
                "failed_users": failed_users
            }
        
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # 分批處理使用者列表
            for i in range(0, len(valid_user_ids), BATCH_SIZE):
                batch = valid_user_ids[i:i + BATCH_SIZE]
                
                try:
                    # 呼叫 LINE Messaging API 批次推送（multicast）
                    line_bot_api.multicast(
                        multicast_request=MulticastRequest(
                            to=batch,
                            messages=[TextMessage(text=message)]
                        )
                    )
                    
                    # 批次推送成功
                    success_count += len(batch)
                    logger.info("Batch push succeeded for %s users", len(batch))
                
                except BaseError as e:
                    # 批次推送失敗，進行單一推送重試
                    logger.warning("Batch push failed; retrying individually: error=%s", e)
                    
                    for user_id in batch:
                        try:
                            # 單一推送
                            line_bot_api.push_message(
                                push_message_request=PushMessageRequest(
                                    to=user_id,
                                    messages=[TextMessage(text=message)]
                                )
                            )
                            success_count += 1
                        
                        except BaseError as retry_error:
                            # 單一推送也失敗，記錄失敗
                            failed_users.append(user_id)
                            logger.error(
                                "Push retry failed: user_id=%s error=%s",
                                user_id,
                                retry_error
                            )
                
                except Exception as e:
                    # 其他未預期的錯誤
                    logger.exception("Unexpected batch push failure: error=%s", e)
                    failed_users.extend(batch)
        
        failed_count = len(failed_users)
        logger.info("Push result: success_count=%s failed_count=%s", success_count, failed_count)
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_users": failed_users
        }
