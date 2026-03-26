"""
測試 security.py 模組的 HMAC 簽章功能
"""

import pytest
from datetime import datetime, timedelta
from security import SecurityService, RateLimiter, validate_line_channel_access_token


def test_security_service_initialization():
    """測試 SecurityService 初始化"""
    security = SecurityService()
    assert security.secret_key is not None
    assert len(security.secret_key) > 0


def test_generate_signature():
    """測試簽章產生功能"""
    security = SecurityService()
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    
    signature = security.generate_signature(team_id)
    
    # 驗證簽章格式（應為 64 字元的十六進位字串，SHA256 輸出）
    assert isinstance(signature, str)
    assert len(signature) == 64
    assert all(c in '0123456789abcdef' for c in signature)


def test_verify_signature_valid():
    """測試有效簽章的驗證"""
    security = SecurityService()
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # 產生簽章
    signature = security.generate_signature(team_id)
    
    # 驗證簽章應該成功
    assert security.verify_signature(team_id, signature) is True


def test_verify_signature_invalid():
    """測試無效簽章的驗證"""
    security = SecurityService()
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # 使用錯誤的簽章
    invalid_signature = "0" * 64
    
    # 驗證應該失敗
    assert security.verify_signature(team_id, invalid_signature) is False


def test_verify_signature_tampered_team_id():
    """測試竄改 team_id 後的簽章驗證"""
    security = SecurityService()
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # 產生原始簽章
    signature = security.generate_signature(team_id)
    
    # 使用不同的 team_id 驗證（模擬攻擊者竄改 team_id）
    tampered_team_id = "550e8400-e29b-41d4-a716-446655440001"
    
    # 驗證應該失敗
    assert security.verify_signature(tampered_team_id, signature) is False


def test_signature_consistency():
    """測試相同輸入產生相同簽章（確定性）"""
    security = SecurityService()
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # 多次產生簽章
    signature1 = security.generate_signature(team_id)
    signature2 = security.generate_signature(team_id)
    signature3 = security.generate_signature(team_id)
    
    # 所有簽章應該相同
    assert signature1 == signature2 == signature3


def test_different_team_ids_different_signatures():
    """測試不同 team_id 產生不同簽章"""
    security = SecurityService()
    team_id1 = "550e8400-e29b-41d4-a716-446655440000"
    team_id2 = "550e8400-e29b-41d4-a716-446655440001"
    
    signature1 = security.generate_signature(team_id1)
    signature2 = security.generate_signature(team_id2)
    
    # 簽章應該不同
    assert signature1 != signature2


def test_validate_line_channel_access_token_rejects_placeholder():
    """測試 LINE token placeholder 會被拒絕"""
    with pytest.raises(ValueError):
        validate_line_channel_access_token("LINE_CHANNEL_ACCESS_TOKEN")


def test_validate_line_channel_access_token_accepts_env_value():
    """測試有效 LINE token 會通過驗證"""
    token = validate_line_channel_access_token("real-token-from-env")
    assert token == "real-token-from-env"


def test_rate_limiter_blocks_requests_over_limit_within_window():
    """測試每分鐘超過 10 次請求會被阻擋"""
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    start = datetime(2026, 1, 1, 0, 0, 0)

    for i in range(10):
        assert limiter.allow_request("U123", now=start + timedelta(seconds=i)) is True

    assert limiter.allow_request("U123", now=start + timedelta(seconds=30)) is False


def test_rate_limiter_allows_requests_after_window_expires():
    """測試超過時間窗口後可再次請求"""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    start = datetime(2026, 1, 1, 0, 0, 0)

    assert limiter.allow_request("U123", now=start) is True
    assert limiter.allow_request("U123", now=start + timedelta(seconds=1)) is True
    assert limiter.allow_request("U123", now=start + timedelta(seconds=2)) is False
    assert limiter.allow_request("U123", now=start + timedelta(seconds=61)) is True


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])
