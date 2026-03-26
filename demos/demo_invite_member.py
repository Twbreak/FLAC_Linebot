# demo_invite_member.py
"""
邀請連結產生功能示範
展示如何使用 TeamService.invite_member() 方法
"""

import uuid
from team_service import TeamService
from database import create_team_tables_if_not_exist
from security import SecurityService


def main():
    print("\n" + "=" * 70)
    print("🎯 團隊邀請連結產生功能示範")
    print("=" * 70)
    
    # 建立測試環境
    print("\n🔧 步驟 1：建立 DynamoDB 資料表...")
    create_team_tables_if_not_exist()
    print("✅ 資料表建立完成")
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 建立測試團隊
    print("\n🔧 步驟 2：建立測試團隊...")
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name = "防詐先鋒隊"
    
    print(f"   隊長 UID: {leader_uid}")
    print(f"   團隊名稱: {team_name}")
    
    team = team_service.create_team(leader_uid, team_name)
    print(f"✅ 團隊建立成功")
    print(f"   Team ID: {team.team_id}")
    print(f"   團隊名稱: {team.team_name}")
    print(f"   隊長 UID: {team.leader_uid}")
    print(f"   總積分: {team.total_points}")
    print(f"   成員數: {team.member_count}")
    
    # 產生邀請連結
    print("\n🔧 步驟 3：產生邀請連結...")
    invite_url = team_service.invite_member(team.team_id, leader_uid)
    print(f"✅ 邀請連結產生成功")
    print(f"\n📋 邀請連結：")
    print(f"   {invite_url}")
    
    # 解析 URL 參數
    print("\n🔍 步驟 4：解析 URL 參數...")
    from urllib.parse import urlparse, parse_qs
    
    parsed_url = urlparse(invite_url)
    query_params = parse_qs(parsed_url.query)
    
    url_team_id = query_params['team_id'][0]
    url_signature = query_params['signature'][0]
    
    print(f"   LIFF Base URL: {parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")
    print(f"   Team ID: {url_team_id}")
    print(f"   Signature: {url_signature}")
    
    # 驗證簽章
    print("\n🔍 步驟 5：驗證 HMAC 簽章...")
    security_service = SecurityService()
    is_valid = security_service.verify_signature(url_team_id, url_signature)
    
    if is_valid:
        print(f"✅ 簽章驗證通過")
        print(f"   這是一個有效的邀請連結，可以安全地用於邀請成員加入團隊")
    else:
        print(f"❌ 簽章驗證失敗")
        print(f"   這個邀請連結可能已被竄改或過期")
    
    # 展示使用情境
    print("\n" + "=" * 70)
    print("📱 使用情境說明")
    print("=" * 70)
    print("""
1. 隊長在 LIFF 介面點擊「邀請隊員」按鈕
2. 系統呼叫 team_service.invite_member(team_id, leader_uid)
3. 系統產生包含 team_id 與 HMAC 簽章的 LIFF URL
4. 隊長透過 LINE ShareTargetPicker 將邀請連結發送給好友
5. 好友點擊連結後，LIFF 頁面開啟並解析 URL 參數
6. 系統驗證簽章，確認邀請連結未被竄改
7. 好友確認加入後，系統將其加入 TeamMembers 表
    """)
    
    print("=" * 70)
    print("🎉 示範完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
