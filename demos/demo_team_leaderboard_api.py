"""
Demo: 團隊排行榜 API (Task 6.5)
展示如何使用 GET /api/leaderboard/teams 端點
"""

import uuid
from fastapi.testclient import TestClient
from main import app
from team_service import TeamService

# 初始化 TestClient 和服務
client = TestClient(app)
team_service = TeamService()

def demo_team_leaderboard_api():
    """示範團隊排行榜 API 功能"""
    
    print("=" * 60)
    print("團隊排行榜 API 示範 (Task 6.5)")
    print("=" * 60)
    
    # 步驟 1: 建立多個測試團隊
    print("\n步驟 1: 建立測試團隊")
    print("-" * 60)
    
    teams_data = [
        ("防詐先鋒隊", 2500),
        ("網路守護者", 1800),
        ("詐騙剋星", 1200),
        ("安全聯盟", 950),
        ("反詐騙小組", 600)
    ]
    
    created_teams = []
    for team_name, points in teams_data:
        leader_uid = f"U{uuid.uuid4().hex[:10]}"
        team = team_service.create_team(
            leader_uid=leader_uid,
            team_name=team_name
        )
        
        # 設定團隊積分
        team_service.teams_table.update_item(
            Key={'team_id': team.team_id},
            UpdateExpression='SET total_points = :points',
            ExpressionAttributeValues={':points': points}
        )
        
        created_teams.append(team)
        print(f"✅ 建立團隊: {team_name} (積分: {points})")
    
    # 步驟 2: 查詢團隊排行榜
    print("\n步驟 2: 查詢團隊排行榜 (GET /api/leaderboard/teams)")
    print("-" * 60)
    
    response = client.get("/api/leaderboard/teams")
    
    if response.status_code == 200:
        data = response.json()
        teams = data["teams"]
        
        print(f"✅ 成功取得排行榜，共 {len(teams)} 個團隊")
        print("\n排行榜:")
        print(f"{'排名':<6} {'團隊名稱':<20} {'總積分':<10} {'成員數':<10}")
        print("-" * 60)
        
        for team in teams[:10]:  # 只顯示前 10 名
            print(f"{team['rank']:<6} {team['team_name']:<20} {team['total_points']:<10} {team['member_count']:<10}")
    else:
        print(f"❌ 查詢失敗: {response.status_code}")
        print(f"錯誤訊息: {response.json()}")
    
    # 步驟 3: 驗證排序正確性
    print("\n步驟 3: 驗證排序正確性")
    print("-" * 60)
    
    if response.status_code == 200:
        teams = data["teams"]
        is_sorted = all(
            teams[i]["total_points"] >= teams[i + 1]["total_points"]
            for i in range(len(teams) - 1)
        )
        
        if is_sorted:
            print("✅ 排序正確：團隊依 total_points 降序排列")
        else:
            print("❌ 排序錯誤：團隊未依 total_points 降序排列")
        
        # 驗證排名
        correct_ranks = all(
            team["rank"] == idx + 1
            for idx, team in enumerate(teams)
        )
        
        if correct_ranks:
            print("✅ 排名正確：排名從 1 開始遞增")
        else:
            print("❌ 排名錯誤：排名未正確設定")
    
    # 步驟 4: 驗證回應格式
    print("\n步驟 4: 驗證回應格式")
    print("-" * 60)
    
    if response.status_code == 200 and teams:
        first_team = teams[0]
        required_fields = ["rank", "team_id", "team_name", "total_points", "member_count", "report_count"]
        
        missing_fields = [field for field in required_fields if field not in first_team]
        
        if not missing_fields:
            print("✅ 回應格式正確，包含所有必要欄位:")
            for field in required_fields:
                print(f"   - {field}: {first_team[field]}")
        else:
            print(f"❌ 回應格式錯誤，缺少欄位: {missing_fields}")
    
    # 清理測試資料
    print("\n清理測試資料...")
    print("-" * 60)
    
    for team in created_teams:
        try:
            team_service.teams_table.delete_item(Key={'team_id': team.team_id})
            member_id = f"{team.team_id}#{team.leader_uid}"
            team_service.team_members_table.delete_item(Key={'member_id': member_id})
            print(f"✅ 刪除團隊: {team.team_name}")
        except Exception as e:
            print(f"❌ 刪除失敗: {str(e)}")
    
    # 總結
    print("\n" + "=" * 60)
    print("📝 總結:")
    print("   ✅ GET /api/leaderboard/teams - 取得團隊排行榜")
    print("   ✅ 從 Teams 表掃描所有團隊")
    print("   ✅ 依 total_points 降序排序")
    print("   ✅ 回傳前 10 名團隊")
    print("   ✅ 包含排名、團隊名稱、總積分、成員數等資訊")
    print("=" * 60)


if __name__ == "__main__":
    demo_team_leaderboard_api()
