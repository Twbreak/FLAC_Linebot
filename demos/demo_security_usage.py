"""
示範 security.py 模組在團隊邀請流程中的使用方式
"""

from security import SecurityService


def generate_invite_url(team_id: str, base_liff_url: str) -> str:
    """
    產生包含簽章的團隊邀請 URL
    
    Args:
        team_id: 團隊 ID
        base_liff_url: LIFF 基礎 URL
        
    Returns:
        完整的邀請 URL（包含 team_id 和 signature 參數）
    """
    security = SecurityService()
    signature = security.generate_signature(team_id)
    
    # 格式：?team_id=xxx&signature=yyy
    invite_url = f"{base_liff_url}?team_id={team_id}&signature={signature}"
    return invite_url


def verify_invite_url(team_id: str, signature: str) -> bool:
    """
    驗證邀請 URL 的簽章
    
    Args:
        team_id: URL 中的團隊 ID
        signature: URL 中的簽章
        
    Returns:
        簽章是否有效
    """
    security = SecurityService()
    return security.verify_signature(team_id, signature)


def main():
    """示範完整的邀請流程"""
    print("=" * 70)
    print("團隊邀請連結安全驗證示範")
    print("=" * 70)
    
    # 模擬場景：隊長建立團隊並產生邀請連結
    team_id = "550e8400-e29b-41d4-a716-446655440000"
    team_name = "防詐先鋒隊"
    base_liff_url = "https://liff.line.me/1234567890-abcdefgh"
    
    print(f"\n📋 場景：隊長建立團隊「{team_name}」")
    print(f"   Team ID: {team_id}")
    
    # 步驟 1: 產生邀請連結
    print("\n🔐 步驟 1: 產生包含簽章的邀請連結...")
    invite_url = generate_invite_url(team_id, base_liff_url)
    print(f"   邀請連結: {invite_url}")
    
    # 從 URL 中提取參數（模擬接收方解析 URL）
    parts = invite_url.split("?")[1].split("&")
    received_team_id = parts[0].split("=")[1]
    received_signature = parts[1].split("=")[1]
    
    print(f"\n   解析參數:")
    print(f"   - team_id: {received_team_id}")
    print(f"   - signature: {received_signature[:32]}...")
    
    # 步驟 2: 好友點擊連結，系統驗證簽章
    print("\n✅ 步驟 2: 好友點擊連結，系統驗證簽章...")
    is_valid = verify_invite_url(received_team_id, received_signature)
    
    if is_valid:
        print("   ✅ 簽章驗證成功！允許加入團隊")
        print(f"   → 使用者可以加入團隊「{team_name}」")
    else:
        print("   ❌ 簽章驗證失敗！拒絕加入請求")
        print("   → 顯示錯誤訊息：「無效的邀請連結」")
    
    # 步驟 3: 模擬攻擊者竄改 team_id
    print("\n🚨 步驟 3: 模擬攻擊者竄改 team_id...")
    tampered_team_id = "550e8400-e29b-41d4-a716-446655440001"
    print(f"   原始 team_id: {received_team_id}")
    print(f"   竄改後 team_id: {tampered_team_id}")
    
    is_tampered_valid = verify_invite_url(tampered_team_id, received_signature)
    
    if is_tampered_valid:
        print("   ❌ 危險！竄改的連結通過驗證（不應該發生）")
    else:
        print("   ✅ 安全！竄改的連結被成功阻擋")
        print("   → 顯示錯誤訊息：「無效的邀請連結」")
    
    # 步驟 4: 模擬攻擊者偽造簽章
    print("\n🚨 步驟 4: 模擬攻擊者偽造簽章...")
    fake_signature = "0" * 64
    print(f"   原始簽章: {received_signature[:32]}...")
    print(f"   偽造簽章: {fake_signature[:32]}...")
    
    is_fake_valid = verify_invite_url(received_team_id, fake_signature)
    
    if is_fake_valid:
        print("   ❌ 危險！偽造的簽章通過驗證（不應該發生）")
    else:
        print("   ✅ 安全！偽造的簽章被成功阻擋")
        print("   → 顯示錯誤訊息：「無效的邀請連結」")
    
    print("\n" + "=" * 70)
    print("✅ 示範完成！HMAC-SHA256 簽章機制有效防止邀請連結偽造")
    print("=" * 70)


if __name__ == "__main__":
    main()
