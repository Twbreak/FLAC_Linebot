"""
大量通報主流程服務

協調大量通報偵測、LLM 摘要生成、警示記錄建立與推送通知流程。
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from database import create_mass_report_alerts_table, dynamodb, retry_database_write
from models import MassReportAlert
from mass_report_detector import MassReportDetector
from bedrock_service import BedrockSummarizer
from notification_dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


def _serialize_mass_report_alert(alert: MassReportAlert) -> Dict[str, Any]:
    """將 Pydantic 模型轉換為可寫入 DynamoDB 的格式。"""
    return {
        "alert_id": alert.alert_id,
        "normalized_url": alert.normalized_url,
        "report_count": alert.report_count,
        "alert_summary": alert.alert_summary,
        "alert_warning": alert.alert_warning,
        "notified_user_count": alert.notified_user_count,
        "created_at": alert.created_at.isoformat(),
        "status": alert.status,
    }


def _query_existing_alert(normalized_url: str, mass_report_alerts_table=None) -> Optional[Dict[str, Any]]:
    """查詢指定 URL 是否已有大量通報警示。"""
    table = mass_report_alerts_table or dynamodb.Table("MassReportAlerts")
    response = table.query(
        IndexName="NormalizedUrlIndex",
        KeyConditionExpression="normalized_url = :url",
        ExpressionAttributeValues={":url": normalized_url},
        Limit=1,
    )
    items = response.get("Items", [])
    return items[0] if items else None


def _save_mass_report_alert(alert: MassReportAlert, mass_report_alerts_table=None) -> None:
    """建立大量通報警示記錄。"""
    table = mass_report_alerts_table or dynamodb.Table("MassReportAlerts")
    retry_database_write(
        lambda: table.put_item(
            Item=_serialize_mass_report_alert(alert),
            ConditionExpression="attribute_not_exists(alert_id)",
        )
    )


def _update_alert_status(
    alert_id: str,
    status: str,
    notified_user_count: int,
    mass_report_alerts_table=None,
) -> None:
    """更新大量通報警示狀態與通知成功數量。"""
    table = mass_report_alerts_table or dynamodb.Table("MassReportAlerts")
    retry_database_write(
        lambda: table.update_item(
            Key={"alert_id": alert_id},
            UpdateExpression="SET #status = :status, notified_user_count = :count",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": status,
                ":count": notified_user_count,
            },
        )
    )


def _mark_reports_as_processed(normalized_url: str, alert_id: str, scam_reports_table=None) -> int:
    """將同一 URL 的所有通報標記為已處理並關聯 alert_id。"""
    table = scam_reports_table or dynamodb.Table("ScamReports")
    response = table.query(
        IndexName="NormalizedUrlIndex",
        KeyConditionExpression="normalized_url = :url",
        ExpressionAttributeValues={":url": normalized_url},
    )
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.query(
            IndexName="NormalizedUrlIndex",
            KeyConditionExpression="normalized_url = :url",
            ExpressionAttributeValues={":url": normalized_url},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    for item in items:
        retry_database_write(
            lambda item=item: table.update_item(
                Key={"report_id": item["report_id"]},
                UpdateExpression="SET is_mass_reported = :flag, mass_report_alert_id = :alert_id",
                ConditionExpression="attribute_not_exists(is_mass_reported) OR is_mass_reported = :false",
                ExpressionAttributeValues={
                    ":flag": True,
                    ":alert_id": alert_id,
                    ":false": False,
                },
            )
        )

    return len(items)


def process_mass_report(
    normalized_url: str,
    current_report_count: int,
    detector: Optional[MassReportDetector] = None,
    summarizer: Optional[BedrockSummarizer] = None,
    dispatcher: Optional[NotificationDispatcher] = None,
    mass_report_alerts_table=None,
    scam_reports_table=None,
) -> Dict[str, Any]:
    """
    處理大量通報偵測與通知流程。

    Returns:
        dict: 包含是否觸發、警示 ID、成功/失敗通知數等資訊
    """
    detector = detector or MassReportDetector()
    summarizer = summarizer or BedrockSummarizer()
    dispatcher = dispatcher or NotificationDispatcher()

    try:
        create_mass_report_alerts_table()
    except Exception as exc:
        logger.exception("Failed to ensure MassReportAlerts table exists: error=%s", exc)
        return {"triggered": False, "reason": "database_error"}

    if current_report_count < detector.threshold:
        return {"triggered": False, "reason": "threshold_not_reached"}

    if not detector.check_report_threshold(normalized_url):
        return {"triggered": False, "reason": "threshold_not_reached"}

    try:
        existing_alert = _query_existing_alert(
            normalized_url=normalized_url,
            mass_report_alerts_table=mass_report_alerts_table,
        )
    except Exception as exc:
        logger.exception("Failed to query existing mass report alert: normalized_url=%s error=%s", normalized_url, exc)
        return {"triggered": False, "reason": "database_error"}
    if existing_alert is not None:
        return {
            "triggered": False,
            "reason": "already_notified",
            "alert_id": existing_alert.get("alert_id"),
        }

    original_message = detector.get_original_message(normalized_url)
    if not original_message:
        return {"triggered": False, "reason": "no_message_content"}

    llm_result = summarizer.generate_mass_report_alert(original_message, current_report_count)
    alert_id = str(uuid.uuid5(uuid.NAMESPACE_URL, normalized_url))
    alert_record = MassReportAlert(
        alert_id=alert_id,
        normalized_url=normalized_url,
        report_count=current_report_count,
        alert_summary=llm_result["alert_summary"],
        alert_warning=llm_result["alert_warning"],
        notified_user_count=0,
        created_at=datetime.now(),
        status="processing",
    )

    try:
        _save_mass_report_alert(
            alert=alert_record,
            mass_report_alerts_table=mass_report_alerts_table,
        )
    except Exception as exc:
        logger.exception("Failed to save mass report alert: normalized_url=%s error=%s", normalized_url, exc)
        try:
            existing_alert = _query_existing_alert(
                normalized_url=normalized_url,
                mass_report_alerts_table=mass_report_alerts_table,
            )
        except Exception:
            existing_alert = None

        if existing_alert is not None:
            return {
                "triggered": False,
                "reason": "already_notified",
                "alert_id": existing_alert.get("alert_id"),
            }
        return {"triggered": False, "reason": "database_error"}

    try:
        marked_report_count = _mark_reports_as_processed(
            normalized_url=normalized_url,
            alert_id=alert_id,
            scam_reports_table=scam_reports_table,
        )
        push_result = dispatcher.broadcast_mass_report_alert(
            alert_summary=alert_record.alert_summary,
            alert_warning=alert_record.alert_warning,
            report_count=current_report_count,
        )
        _update_alert_status(
            alert_id=alert_id,
            status="completed",
            notified_user_count=push_result["success_count"],
            mass_report_alerts_table=mass_report_alerts_table,
        )
    except Exception as exc:
        logger.exception("Mass report processing failed: normalized_url=%s error=%s", normalized_url, exc)
        try:
            _update_alert_status(
                alert_id=alert_id,
                status="failed",
                notified_user_count=0,
                mass_report_alerts_table=mass_report_alerts_table,
            )
        except Exception as status_exc:
            logger.exception("Failed to update mass report alert status to failed: alert_id=%s error=%s", alert_id, status_exc)
        return {
            "triggered": False,
            "reason": "processing_failed",
            "alert_id": alert_id,
        }

    return {
        "triggered": True,
        "alert_id": alert_id,
        "status": "completed",
        "marked_report_count": marked_report_count,
        "notified_users": push_result["success_count"],
        "failed_count": push_result["failed_count"],
        "failed_users": push_result["failed_users"],
    }
