"""
測試團隊排行榜 API (Task 6.5)
測試 GET /api/leaderboard/teams 端點
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from team_service import TeamService
import uuid

client = TestClient(app)
team_service = TeamService()


def test_get_team_leaderboard_empty():
    """測試空排行榜"""
    response = client.get("/api/leaderboard/teams")
    
    assert response.status_code == 200
    data = response.json()
    assert "teams" in data
    assert isinstance(data["teams"], list)


def test_get_team_leaderboard_with_teams():
    """測試有團隊的排行榜"""
    # 建立測試團隊
    teams = []
    for i in range(3):
        leader_uid = f"U{uuid.uuid4().hex[:10]}"
        team = team_service.create_team(
            leader_uid=leader_uid,
            team_name=f"測試團隊{i+1}"
        )
        teams.append(team)
        
        # 設定不同的積分
        team_service.teams_table.update_item(
            Key={'team_id': team.team_id},
            UpdateExpression='SET total_points = :points',
            ExpressionAttributeValues={':points': (3 - i) * 100}  # 300, 200, 100
        )
    
    # 呼叫 API
    response = client.get("/api/leaderboard/teams")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    assert "teams" in data
    assert len(data["teams"]) >= 3
    
    # 驗證排序（依 total_points 降序）
    teams_list = data["teams"]
    for i in range(len(teams_list) - 1):
        assert teams_list[i]["total_points"] >= teams_list[i + 1]["total_points"]
    
    # 驗證排名
    for idx, team in enumerate(teams_list):
        assert team["rank"] == idx + 1
    
    # 驗證必要欄位
    first_team = teams_list[0]
    assert "team_id" in first_team
    assert "team_name" in first_team
    assert "total_points" in first_team
    assert "member_count" in first_team
    assert "report_count" in first_team
    
    # 清理測試資料
    for team in teams:
        try:
            team_service.teams_table.delete_item(Key={'team_id': team.team_id})
            member_id = f"{team.team_id}#{team.leader_uid}"
            team_service.team_members_table.delete_item(Key={'member_id': member_id})
        except:
            pass


def test_get_team_leaderboard_top_10():
    """測試排行榜只回傳前 10 名"""
    # 建立 15 個測試團隊
    teams = []
    for i in range(15):
        leader_uid = f"U{uuid.uuid4().hex[:10]}"
        team = team_service.create_team(
            leader_uid=leader_uid,
            team_name=f"測試團隊{i+1}"
        )
        teams.append(team)
        
        # 設定不同的積分
        team_service.teams_table.update_item(
            Key={'team_id': team.team_id},
            UpdateExpression='SET total_points = :points',
            ExpressionAttributeValues={':points': (15 - i) * 10}
        )
    
    # 呼叫 API
    response = client.get("/api/leaderboard/teams")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    # 驗證只回傳前 10 名
    assert len(data["teams"]) <= 10
    
    # 清理測試資料
    for team in teams:
        try:
            team_service.teams_table.delete_item(Key={'team_id': team.team_id})
            member_id = f"{team.team_id}#{team.leader_uid}"
            team_service.team_members_table.delete_item(Key={'member_id': member_id})
        except:
            pass


if __name__ == "__main__":
    print("執行團隊排行榜 API 測試...")
    pytest.main([__file__, "-v"])
