"""
簡單測試 security.py 模組的 HMAC 簽章功能
"""

from security import SecurityService


def test_security_service():
    """測試 SecurityService 的基本功能"""
    print("🧪 測試 SecurityService 初始化...")
    security = SecurityService()
    print(f"✅ 密鑰已載入: {security.secret_key[:10]}...")
    
    print("\n🧪 測試簽章產生...")
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    signature = security.generate_signature(team_id)
    print(f"✅ 簽章產生成功: {signature}")
    print(f"   簽章長度: {len(signature)} 字元")
    
    print("\n🧪 測試有效簽章驗證...")
    is_valid = security.verify_signature(team_id, signature)
    print(f"✅ 簽章驗證結果: {is_valid}")
    assert is_valid is True, "有效簽章應該通過驗證"
    
    print("\n🧪 測試無效簽章驗證...")
    invalid_signature = "0" * 64
    is_invalid = security.verify_signature(team_id, invalid_signature)
    print(f"✅ 無效簽章驗證結果: {is_invalid}")
    assert is_invalid is False, "無效簽章應該被拒絕"
    
    print("\n🧪 測試竄改 team_id 的簽章驗證...")
    tampered_team_id = "550e8400-e29b-41d4-a716-446655440001"
    is_tampered = security.verify_signature(tampered_team_id, signature)
    print(f"✅ 竄改後的驗證結果: {is_tampered}")
    assert is_tampered is False, "竄改的 team_id 應該被拒絕"
    
    print("\n🧪 測試簽章一致性...")
    signature1 = security.generate_signature(team_id)
    signature2 = security.generate_signature(team_id)
    signature3 = security.generate_signature(team_id)
    print(f"✅ 簽章 1: {signature1}")
    print(f"✅ 簽章 2: {signature2}")
    print(f"✅ 簽章 3: {signature3}")
    assert signature1 == signature2 == signature3, "相同輸入應產生相同簽章"
    
    print("\n🧪 測試不同 team_id 產生不同簽章...")
    team_id2 = "550e8400-e29b-41d4-a716-446655440001"
    signature_a = security.generate_signature(team_id)
    signature_b = security.generate_signature(team_id2)
    print(f"✅ Team ID 1 簽章: {signature_a}")
    print(f"✅ Team ID 2 簽章: {signature_b}")
    assert signature_a != signature_b, "不同 team_id 應產生不同簽章"
    
    print("\n" + "=" * 60)
    print("🎉 所有測試通過！HMAC 簽章模組運作正常")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_security_service()
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
