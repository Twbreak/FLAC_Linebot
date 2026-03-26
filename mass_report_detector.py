"""
大量通報偵測器模組

此模組負責監控訊息通報次數，當達到閾值時觸發通知流程。
"""

import boto3
import os
import logging
import time
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# AWS 設定
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")


class MassReportDetector:
    """大量通報偵測器
    
    監控訊息通報次數，當達到閾值時觸發通知流程。
    """
    
    def __init__(self, threshold: int = 10):
        """初始化 MassReportDetector
        
        Args:
            threshold: 觸發大量通報的閾值，預設為 10
        """
        # 初始化 DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.threshold = threshold
        self.scam_reports_table = self.dynamodb.Table('ScamReports')
        self.mass_report_alerts_table = self.dynamodb.Table('MassReportAlerts')
        self._threshold_cache = {}
        self._threshold_cache_ttl_seconds = 5
    
    def check_report_threshold(self, normalized_url: str) -> bool:
        """檢查 URL 通報次數是否達到閾值
        
        前置條件：
        - normalized_url 為非空字串且格式有效
        - ScamReports 資料表可存取
        
        後置條件：
        - 返回布林值
        - 當且僅當該 URL 的通報次數 >= threshold 時返回 True
        - 不修改資料庫狀態（唯讀操作）
        
        Args:
            normalized_url: 正規化後的 URL
            
        Returns:
            True 如果通報次數達到閾值，False 否則
        """
        try:
            cached_result = self._threshold_cache.get(normalized_url)
            now = time.time()
            if cached_result and now - cached_result["timestamp"] < self._threshold_cache_ttl_seconds:
                return cached_result["result"]

            # 使用 NormalizedUrlIndex GSI 查詢該 URL 的通報記錄
            # 優化：只查詢到閾值數量即可，使用 Limit 參數減少資料傳輸
            # 使用 Select='COUNT' 只取得計數，不取得實際項目
            response = self.scam_reports_table.query(
                IndexName='NormalizedUrlIndex',
                KeyConditionExpression='normalized_url = :url',
                ExpressionAttributeValues={
                    ':url': normalized_url
                },
                Select='COUNT',
                Limit=self.threshold  # 只需要知道是否達到閾值，不需要全部計數
            )
            
            # 取得通報次數
            report_count = response.get('Count', 0)
            
            # 如果第一頁就達到閾值，直接返回 True
            if report_count >= self.threshold:
                self._threshold_cache[normalized_url] = {
                    "result": True,
                    "timestamp": now,
                }
                return True
            
            # 如果有更多資料（分頁），繼續查詢直到達到閾值或確認未達標
            while 'LastEvaluatedKey' in response:
                response = self.scam_reports_table.query(
                    IndexName='NormalizedUrlIndex',
                    KeyConditionExpression='normalized_url = :url',
                    ExpressionAttributeValues={
                        ':url': normalized_url
                    },
                    Select='COUNT',
                    Limit=self.threshold,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                report_count += response.get('Count', 0)
                
                # 一旦達到閾值就立即返回
                if report_count >= self.threshold:
                    self._threshold_cache[normalized_url] = {
                        "result": True,
                        "timestamp": now,
                    }
                    return True
            
            # 所有資料都查完了，仍未達閾值
            self._threshold_cache[normalized_url] = {
                "result": False,
                "timestamp": now,
            }
            return False
            
        except Exception as e:
            logger.exception("Mass report threshold query failed: normalized_url=%s error=%s", normalized_url, e)
            return False
    
    def mark_as_mass_reported(self, normalized_url: str, alert_id: str) -> bool:
        """標記 URL 為大量通報狀態
        
        前置條件：
        - normalized_url 為非空字串
        - alert_id 為有效的 UUID 字串
        - ScamReports 資料表可存取
        - MassReportAlerts 資料表可存取
        
        後置條件：
        - 若該 URL 已有警示記錄，返回 False（避免重複通知）
        - 若該 URL 無警示記錄，所有該 URL 的通報記錄的 is_mass_reported 設為 True
        - 若該 URL 無警示記錄，所有該 URL 的通報記錄的 mass_report_alert_id 設為 alert_id
        - 返回操作是否成功
        
        Args:
            normalized_url: 正規化後的 URL
            alert_id: 警示記錄的 UUID
            
        Returns:
            True 如果標記成功，False 如果警示已存在或操作失敗
        """
        try:
            # Step 1: 檢查 MassReportAlerts 表中是否已存在該 URL 的警示記錄
            # 使用 NormalizedUrlIndex GSI 查詢
            alert_response = self.mass_report_alerts_table.query(
                IndexName='NormalizedUrlIndex',
                KeyConditionExpression='normalized_url = :url',
                ExpressionAttributeValues={
                    ':url': normalized_url
                },
                Limit=1  # 只需要知道是否存在
            )
            
            # 如果已存在警示記錄，返回 False（避免重複通知）
            if alert_response.get('Items'):
                logger.info("Mass report alert already exists: normalized_url=%s", normalized_url)
                return False
            
            # Step 2: 查詢該 URL 的所有通報記錄
            response = self.scam_reports_table.query(
                IndexName='NormalizedUrlIndex',
                KeyConditionExpression='normalized_url = :url',
                ExpressionAttributeValues={
                    ':url': normalized_url
                }
            )
            
            reports = response.get('Items', [])
            
            # Step 3: 更新每一筆通報記錄
            for report in reports:
                self.scam_reports_table.update_item(
                    Key={'report_id': report['report_id']},
                    UpdateExpression='SET is_mass_reported = :flag, mass_report_alert_id = :alert_id',
                    ExpressionAttributeValues={
                        ':flag': True,
                        ':alert_id': alert_id
                    }
                )
            
            logger.info("Marked reports as mass reported: normalized_url=%s count=%s", normalized_url, len(reports))
            return True
            
        except Exception as e:
            logger.exception("Failed to mark reports as mass reported: normalized_url=%s error=%s", normalized_url, e)
            return False
    
    def get_original_message(self, normalized_url: str) -> Optional[str]:
        """提取原始訊息內容
        
        前置條件：
        - normalized_url 為非空字串
        - ScamReports 資料表可存取
        
        後置條件：
        - 返回該 URL 的第一筆通報的原始訊息內容
        - 若無記錄則返回 None
        - 不修改資料庫狀態（唯讀操作）
        
        Args:
            normalized_url: 正規化後的 URL
            
        Returns:
            原始訊息內容，若無記錄則返回 None
        """
        try:
            # 使用 NormalizedUrlIndex GSI 查詢該 URL 的通報記錄
            # 注意：此 GSI 的 ProjectionType 為 KEYS_ONLY，只返回 report_id 和 normalized_url
            response = self.scam_reports_table.query(
                IndexName='NormalizedUrlIndex',
                KeyConditionExpression='normalized_url = :url',
                ExpressionAttributeValues={
                    ':url': normalized_url
                },
                Limit=1,  # 只需要第一筆記錄
                ConsistentRead=False  # GSI 不支援強一致性讀取
            )
            
            items = response.get('Items', [])
            
            if not items:
                return None
            
            # 由於 GSI 只返回 keys，需要使用 report_id 查詢完整記錄
            report_id = items[0].get('report_id')
            if not report_id:
                return None
            
            # 使用 report_id 查詢完整記錄
            full_item_response = self.scam_reports_table.get_item(
                Key={'report_id': report_id}
            )
            
            full_item = full_item_response.get('Item')
            if not full_item:
                return None
            
            # 返回原始 URL（作為原始訊息內容）
            return full_item.get('url', None)
            
        except Exception as e:
            logger.exception("Failed to get original message: normalized_url=%s error=%s", normalized_url, e)
            return None
