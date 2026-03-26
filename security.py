# security.py
"""
團隊邀請連結安全模組
使用 HMAC-SHA256 演算法對 team_id 進行簽章與驗證，防止邀請連結偽造
"""

import hmac
import hashlib
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class SecurityService:
    """安全服務類別，負責 HMAC 簽章的產生與驗證"""
    
    def __init__(self):
        """初始化安全服務，從環境變數讀取密鑰"""
        self.secret_key = os.getenv("TEAM_INVITE_SECRET_KEY")
        if not self.secret_key:
            raise ValueError(
                "❌ TEAM_INVITE_SECRET_KEY 未設定！\n"
                "請在 .env 檔案中加入：\n"
                "  TEAM_INVITE_SECRET_KEY=your-secret-key-here-min-32-chars"
            )
    
    def generate_signature(self, team_id: str) -> str:
        """
        產生 HMAC-SHA256 簽章
        
        Args:
            team_id: 團隊唯一識別碼
            
        Returns:
            str: 十六進位格式的簽章字串
            
        Example:
            >>> security = SecurityService()
            >>> signature = security.generate_signature("550e8400-e29b-41d4-a716-446655440000")
            >>> print(signature)
            'abc123def456...'
        """
        message = team_id.encode('utf-8')
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, team_id: str, signature: str) -> bool:
        """
        驗證 HMAC-SHA256 簽章
        
        Args:
            team_id: 團隊唯一識別碼
            signature: 待驗證的簽章字串
            
        Returns:
            bool: 簽章是否有效
            
        Example:
            >>> security = SecurityService()
            >>> signature = security.generate_signature("550e8400-e29b-41d4-a716-446655440000")
            >>> is_valid = security.verify_signature("550e8400-e29b-41d4-a716-446655440000", signature)
            >>> print(is_valid)
            True
        """
        expected_signature = self.generate_signature(team_id)
        # 使用 compare_digest 防止時序攻擊（timing attack）
        return hmac.compare_digest(expected_signature, signature)


def validate_line_channel_access_token(token: str) -> str:
    """驗證 LINE Channel Access Token 必須來自環境變數且不可為占位值。"""
    invalid_placeholders = {
        "",
        "YOUR_CHANNEL_ACCESS_TOKEN",
        "your-channel-access-token",
        "LINE_CHANNEL_ACCESS_TOKEN",
        "test-token",
    }

    normalized = (token or "").strip()
    if normalized in invalid_placeholders:
        raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is missing or appears to be hardcoded/placeholder text")

    return normalized


class RateLimiter:
    """簡單的使用者請求速率限制器。"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(deque)

    def allow_request(self, user_id: str, now: datetime | None = None) -> bool:
        """檢查指定使用者是否仍可在時間窗口內送出請求。"""
        current_time = now or datetime.now(UTC)
        window_start = current_time - timedelta(seconds=self.window_seconds)
        requests = self._requests[user_id]

        while requests and requests[0] <= window_start:
            requests.popleft()

        if len(requests) >= self.max_requests:
            return False

        requests.append(current_time)
        return True
