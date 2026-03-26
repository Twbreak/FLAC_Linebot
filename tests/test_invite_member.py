# test_invite_member.py
"""
測試 TeamService.invite_member() 方法
驗證邀請連結產生功能
"""

import uuid
import os
from team_service import TeamService
from database import create_team_tables_if_not_exist
from security import SecurityService
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


def test_invite_member_success():
    """測試成功產生邀請連結"""
    print("\n" + "=" * 60)
    print("🧪 測試 1：成功產生邀請連結")
    print("=" * 60)
    
    # 建立測試環境
    print("🔧 設定測試環境：建立 DynamoDB 資料表...")
    create_team_tables_if_not_exist()
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 建立測試團隊
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    
    print(f"\n📝 建立測試團隊...")
    print(f"   隊長 UID: {leader_uid}")
    print(f"   團隊名稱: {team_name}")
    
    team = team_service.create_team(leader_uid, team_name)
    print(f"✅ 團隊建立成功: {team.team_id}")
    
    # 產生邀請連結
    print(f"\n📝 產生邀請連結...")
    invite_url = team_service.invite_member(team.team_id, leader_uid)
    
    print(f"\n✅ 邀請連結產生成功！")
    print(f"   URL: {invite_url}")
    
    # 驗證 URL 格式
    assert invite_url is not None, "邀請連結不應為 None"
    assert invite_url.startswith("https://liff.line.me/"), "邀請連結應以 https://liff.line.me/ 開頭"
    assert f"team_id={team.team_id}" in invite_url, "邀請連結應包含 team_id 參數"
    assert "signature=" in invite_url, "邀請連結應包含 signature 參數"
    
    # 解析 URL 參數
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(invite_url)
    query_params = parse_qs(parsed_url.query)
    
    assert 'team_id' in query_params, "URL 應包含 team_id 參數"
    assert 'signature' in query_params, "URL 應包含 signature 參數"
    
    url_team_id = query_params['team_id'][0]
    url_signature = query_params['signature'][0]
    
    print(f"\n🔍 驗證 URL 參數...")
    print(f"   team_id: {url_team_id}")
    print(f"   signature: {url_signature}")
    
    assert url_team_id == team.team_id, f"URL 中的 team_id 不符：期望 {team.team_id}，實際 {url_team_id}"
    
    # 驗證簽章
    print(f"\n🔍 驗證 HMAC 簽章...")
    security_service = SecurityService()
    is_valid = security_service.verify_signature(url_team_id, url_signature)
    assert is_valid, "簽章驗證失敗"
    print(f"✅ 簽章驗證通過")
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 1 通過：邀請連結產生成功且簽章有效")
    print("=" * 60)


def test_invite_member_team_not_exist():
    """測試團隊不存在時的錯誤處理"""
    print("\n" + "=" * 60)
    print("🧪 測試 2：團隊不存在時拒絕產生邀請連結")
    print("=" * 60)
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 使用不存在的 team_id
    fake_team_id = str(uuid.uuid4())
    inviter_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    
    print(f"\n📝 嘗試為不存在的團隊產生邀請連結...")
    print(f"   Team ID: {fake_team_id}")
    print(f"   Inviter UID: {inviter_uid}")
    
    try:
        invite_url = team_service.invite_member(fake_team_id, inviter_uid)
        raise AssertionError("應該拋出 ValueError，但卻成功產生邀請連結")
    except ValueError as e:
        error_message = str(e)
        print(f"✅ 正確拋出 ValueError: {error_message}")
        assert "團隊不存在" in error_message or "查詢團隊失敗" in error_message, f"錯誤訊息不符：{error_message}"
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 2 通過：正確拒絕不存在的團隊")
    print("=" * 60)


def test_invite_member_not_team_member():
    """測試非團隊成員無法產生邀請連結"""
    print("\n" + "=" * 60)
    print("🧪 測試 3：非團隊成員無法產生邀請連結")
    print("=" * 60)
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 建立測試團隊
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    
    print(f"\n📝 建立測試團隊...")
    team = team_service.create_team(leader_uid, team_name)
    print(f"✅ 團隊建立成功: {team.team_id}")
    
    # 使用非成員的 UID 嘗試產生邀請連結
    non_member_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    
    print(f"\n📝 非成員嘗試產生邀請連結...")
    print(f"   Team ID: {team.team_id}")
    print(f"   Non-member UID: {non_member_uid}")
    
    try:
        invite_url = team_service.invite_member(team.team_id, non_member_uid)
        raise AssertionError("應該拋出 ValueError，但卻成功產生邀請連結")
    except ValueError as e:
        error_message = str(e)
        print(f"✅ 正確拋出 ValueError: {error_message}")
        assert "不是該團隊成員" in error_message or "驗證成員身分失敗" in error_message, f"錯誤訊息不符：{error_message}"
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 3 通過：正確拒絕非團隊成員")
    print("=" * 60)


def test_invite_member_signature_uniqueness():
    """測試不同團隊產生不同的簽章"""
    print("\n" + "=" * 60)
    print("🧪 測試 4：不同團隊產生不同的簽章")
    print("=" * 60)
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 建立兩個測試團隊
    leader_uid_1 = f"U_TEST_{uuid.uuid4().hex[:8]}"
    leader_uid_2 = f"U_TEST_{uuid.uuid4().hex[:8]}"
    
    print(f"\n📝 建立兩個測試團隊...")
    team1 = team_service.create_team(leader_uid_1, "團隊 1")
    team2 = team_service.create_team(leader_uid_2, "團隊 2")
    print(f"✅ 團隊 1: {team1.team_id}")
    print(f"✅ 團隊 2: {team2.team_id}")
    
    # 產生邀請連結
    print(f"\n📝 產生邀請連結...")
    invite_url_1 = team_service.invite_member(team1.team_id, leader_uid_1)
    invite_url_2 = team_service.invite_member(team2.team_id, leader_uid_2)
    
    # 解析簽章
    from urllib.parse import urlparse, parse_qs
    
    parsed_url_1 = urlparse(invite_url_1)
    query_params_1 = parse_qs(parsed_url_1.query)
    signature_1 = query_params_1['signature'][0]
    
    parsed_url_2 = urlparse(invite_url_2)
    query_params_2 = parse_qs(parsed_url_2.query)
    signature_2 = query_params_2['signature'][0]
    
    print(f"\n🔍 驗證簽章唯一性...")
    print(f"   團隊 1 簽章: {signature_1}")
    print(f"   團隊 2 簽章: {signature_2}")
    
    assert signature_1 != signature_2, "不同團隊應該產生不同的簽章"
    print(f"✅ 簽章唯一性驗證通過")
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 4 通過：不同團隊產生不同的簽章")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 開始執行邀請連結測試")
    print("=" * 60)
    
    try:
        # 執行測試
        test_invite_member_success()
        test_invite_member_team_not_exist()
        test_invite_member_not_team_member()
        test_invite_member_signature_uniqueness()
        
        print("\n" + "=" * 60)
        print("🎉 所有測試通過！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 測試執行錯誤: {e}")
        raise
