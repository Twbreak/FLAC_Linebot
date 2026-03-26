"""
Demo: 團隊資訊查詢 API (Task 6.4)
展示如何使用 GET /api/teams/{team_id} 和 GET /api/teams/{team_id}/members 端點
"""

import requests
import uuid
from team_service import TeamService

# 初始化服務
team_service = TeamService()

# API 基礎 URL（假設 FastAPI 運行在 localhost:8080）
BASE_URL = "http://localhost:8080"

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
    
    try:
        response = requests.get(f"{BASE_URL}/api/teams/{team.team_id}")
        
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
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API (請確保 FastAPI 伺服器正在運行)")
        print("   可以直接使用 TeamService 查詢:")
        team_info = team_service.get_team_info(team.team_id)
        if team_info:
            print(f"   Team ID: {team_info.team_id}")
            print(f"   團隊名稱: {team_info.team_name}")
            print(f"   隊長 UID: {team_info.leader_uid}")
            print(f"   總積分: {team_info.total_points}")
            print(f"   成員數: {team_info.member_count}")
    
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
    
    # 步驟 4: 使用 API 查詢團隊成員清單
    print("\n步驟 4: 查詢團隊成員清單 (GET /api/teams/{team_id}/members)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/teams/{team.team_id}/members")
        
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
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API (請確保 FastAPI 伺服器正在運行)")
        print("   可以直接使用 TeamService 查詢:")
        members = team_service.get_team_members(team.team_id)
        print(f"   成員總數: {len(members)}")
        print()
        
        for i, member in enumerate(members, 1):
            print(f"   成員 {i}:")
            print(f"      LINE UID: {member.line_uid}")
            print(f"      貢獻積分: {member.contribution_points}")
            print(f"      通報次數: {member.report_count}")
            print(f"      是否為隊長: {'是' if member.is_leader else '否'}")
            print(f"      加入時間: {member.joined_at.isoformat()}")
            print()
    
    # 步驟 5: 測試查詢不存在的團隊
    print("\n步驟 5: 測試查詢不存在的團隊")
    print("-" * 60)
    
    fake_team_id = str(uuid.uuid4())
    
    try:
        response = requests.get(f"{BASE_URL}/api/teams/{fake_team_id}")
        
        if response.status_code == 404:
            print(f"✅ 正確回應 404 錯誤")
            print(f"   錯誤訊息: {response.json()['detail']}")
        else:
            print(f"⚠️  預期 404，但收到: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API (請確保 FastAPI 伺服器正在運行)")
        print("   可以直接使用 TeamService 查詢:")
        team_info = team_service.get_team_info(fake_team_id)
        if team_info is None:
            print(f"   ✅ 正確回傳 None (團隊不存在)")
    
    print("\n" + "=" * 60)
    print("Demo 完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo_team_info_api()
