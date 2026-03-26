"""
Demo: 團隊資訊查詢 API (Task 6.4) - 使用 TestClient
展示如何使用 GET /api/teams/{team_id} 和 GET /api/teams/{team_id}/members 端點
"""

import uuid
from fastapi.testclient import TestClient
from main import app
from team_service import TeamService

# 初始化 TestClient 和服務
client = TestClient(app)
team_service = TeamService()

def demo_team_info_api():
    """展示團隊資訊查詢 API 的使用"""
    
    print("=" * 60)
    print("團隊資訊查詢 API Demo (Task 6.4)")
    print("=" * 60)
    
    # 步驟 1: 建立測試團隊
    print("\n步驟 1: 建立測試團隊")
    print("-" * 60)
    
    leader_uid = f"U_demo_{uuid.uuid4().hex[:8]}"
    team_name = "防詐先鋒隊"
    
    team = team_service.create_team(leader_uid=leader_uid, team_name=team_name)
    print(f"✅ 團隊建立成功！")
    print(f"   Team ID: {team.team_id}")
    print(f"   團隊名稱: {team.team_name}")
    print(f"   隊長 UID: {team.leader_uid}")
    
    # 步驟 2: 使用 API 查詢團隊資訊
    print("\n步驟 2: 查詢團隊資訊 (GET /api/teams/{team_id})")
    print("-" * 60)
    
    response = client.get(f"/api/teams/{team.team_id}")
    
    if response.status_code == 200:
        team_info = response.json()
        print(f"✅ API 回應成功！")
        print(f"   Team ID: {team_info['team_id']}")
        print(f"   團隊名稱: {team_info['team_name']}")
        print(f"   隊長 UID: {team_info['leader_uid']}")
        print(f"   總積分: {team_info['total_points']}")
        print(f"   成員數: {team_info['member_count']}")
        print(f"   建立時間: {team_info['created_at']}")
    else:
        print(f"❌ API 回應失敗: {response.status_code}")
        print(f"   錯誤訊息: {response.json()}")
    
    # 步驟 3: 加入新成員
    print("\n步驟 3: 加入新成員")
    print("-" * 60)
    
    # 產生邀請連結
    invite_url = team_service.invite_member(team_id=team.team_id, inviter_uid=leader_uid)
    
    # 從 URL 提取 signature
    import re
    match = re.search(r'signature=([^&]+)', invite_url)
    signature = match.group(1) if match else ""
    
    # 加入第二個成員
    member_uid = f"U_demo_{uuid.uuid4().hex[:8]}"
    team_service.join_team(team_id=team.team_id, member_uid=member_uid, signature=signature)
    print(f"✅ 成員加入成功！")
    print(f"   Member UID: {member_uid}")
    
    # 加入第三個成員
    member_uid_2 = f"U_demo_{uuid.uuid4().hex[:8]}"
    team_service.join_team(team_id=team.team_id, member_uid=member_uid_2, signature=signature)
    print(f"✅ 成員加入成功！")
    print(f"   Member UID: {member_uid_2}")
    
    # 步驟 4: 使用 API 查詢團隊成員清單
    print("\n步驟 4: 查詢團隊成員清單 (GET /api/teams/{team_id}/members)")
    print("-" * 60)
    
    response = client.get(f"/api/teams/{team.team_id}/members")
    
    if response.status_code == 200:
        data = response.json()
        members = data['members']
        print(f"✅ API 回應成功！")
        print(f"   成員總數: {len(members)}")
        print()
        
        for i, member in enumerate(members, 1):
            print(f"   成員 {i}:")
            print(f"      LINE UID: {member['line_uid']}")
            print(f"      貢獻積分: {member['contribution_points']}")
            print(f"      通報次數: {member['report_count']}")
            print(f"      是否為隊長: {'是' if member['is_leader'] else '否'}")
            print(f"      加入時間: {member['joined_at']}")
            print()
    else:
        print(f"❌ API 回應失敗: {response.status_code}")
        print(f"   錯誤訊息: {response.json()}")
    
    # 步驟 5: 測試查詢不存在的團隊
    print("\n步驟 5: 測試查詢不存在的團隊")
    print("-" * 60)
    
    fake_team_id = str(uuid.uuid4())
    response = client.get(f"/api/teams/{fake_team_id}")
    
    if response.status_code == 404:
        print(f"✅ 正確回應 404 錯誤")
        print(f"   錯誤訊息: {response.json()['detail']}")
    else:
        print(f"⚠️  預期 404，但收到: {response.status_code}")
    
    # 步驟 6: 測試查詢不存在團隊的成員
    print("\n步驟 6: 測試查詢不存在團隊的成員")
    print("-" * 60)
    
    response = client.get(f"/api/teams/{fake_team_id}/members")
    
    if response.status_code == 404:
        print(f"✅ 正確回應 404 錯誤")
        print(f"   錯誤訊息: {response.json()['detail']}")
    else:
        print(f"⚠️  預期 404，但收到: {response.status_code}")
    
    # 步驟 7: 驗證團隊資訊更新
    print("\n步驟 7: 驗證團隊資訊已更新成員數")
    print("-" * 60)
    
    response = client.get(f"/api/teams/{team.team_id}")
    
    if response.status_code == 200:
        team_info = response.json()
        print(f"✅ 團隊資訊已更新！")
        print(f"   成員數: {team_info['member_count']} (預期: 3)")
        
        if team_info['member_count'] == 3:
            print(f"   ✅ 成員數正確！")
        else:
            print(f"   ⚠️  成員數不符預期")
    
    print("\n" + "=" * 60)
    print("Demo 完成！")
    print("=" * 60)
    print("\n📝 總結:")
    print("   ✅ GET /api/teams/{team_id} - 取得團隊資訊")
    print("   ✅ GET /api/teams/{team_id}/members - 取得團隊成員清單")
    print("   ✅ 404 錯誤處理正確")
    print("   ✅ 成員數自動更新")


if __name__ == "__main__":
    demo_team_info_api()
