"""
測試 security.py 模組的 HMAC 簽章功能
"""

import pytest
from security import SecurityService


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


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])
