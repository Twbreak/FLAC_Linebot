"""
測試團隊資訊查詢 API (Task 6.4)
測試 GET /api/teams/{team_id} 和 GET /api/teams/{team_id}/members 端點
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from team_service import TeamService
import uuid

client = TestClient(app)
team_service = TeamService()


def test_get_team_info_success():
    """測試成功取得團隊資訊"""
    # 建立測試團隊
    leader_uid = f"U_test_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    
    team = team_service.create_team(leader_uid=leader_uid, team_name=team_name)
    
    # 呼叫 API
    response = client.get(f"/api/teams/{team.team_id}")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    assert data["team_id"] == team.team_id
    assert data["team_name"] == team_name
    assert data["leader_uid"] == leader_uid
    assert data["total_points"] == 0
    assert data["member_count"] == 1
    assert "created_at" in data


def test_get_team_info_not_found():
    """測試查詢不存在的團隊"""
    fake_team_id = str(uuid.uuid4())
    
    response = client.get(f"/api/teams/{fake_team_id}")
    
    assert response.status_code == 404
    assert "團隊不存在或已解散" in response.json()["detail"]


def test_get_team_members_success():
    """測試成功取得團隊成員清單"""
    # 建立測試團隊
    leader_uid = f"U_test_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊成員"
    
    team = team_service.create_team(leader_uid=leader_uid, team_name=team_name)
    
    # 呼叫 API
    response = client.get(f"/api/teams/{team.team_id}/members")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    assert "members" in data
    assert len(data["members"]) == 1
    
    # 驗證隊長資訊
    leader = data["members"][0]
    assert leader["line_uid"] == leader_uid
    assert leader["contribution_points"] == 0
    assert leader["report_count"] == 0
    assert leader["is_leader"] is True
    assert "joined_at" in leader


def test_get_team_members_with_multiple_members():
    """測試取得有多個成員的團隊清單"""
    # 建立測試團隊
    leader_uid = f"U_test_{uuid.uuid4().hex[:8]}"
    team_name = "多成員測試團隊"
    
    team = team_service.create_team(leader_uid=leader_uid, team_name=team_name)
    
    # 產生邀請連結並加入成員
    invite_url = team_service.invite_member(team_id=team.team_id, inviter_uid=leader_uid)
    
    # 從 URL 提取 signature
    import re
    match = re.search(r'signature=([^&]+)', invite_url)
    signature = match.group(1) if match else ""
    
    # 加入第二個成員
    member_uid = f"U_test_{uuid.uuid4().hex[:8]}"
    team_service.join_team(team_id=team.team_id, member_uid=member_uid, signature=signature)
    
    # 呼叫 API
    response = client.get(f"/api/teams/{team.team_id}/members")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    assert "members" in data
    assert len(data["members"]) == 2
    
    # 驗證成員資訊
    line_uids = [member["line_uid"] for member in data["members"]]
    assert leader_uid in line_uids
    assert member_uid in line_uids


def test_get_team_members_not_found():
    """測試查詢不存在團隊的成員"""
    fake_team_id = str(uuid.uuid4())
    
    response = client.get(f"/api/teams/{fake_team_id}/members")
    
    assert response.status_code == 404
    assert "團隊不存在或已解散" in response.json()["detail"]


if __name__ == "__main__":
    print("執行團隊資訊查詢 API 測試...")
    pytest.main([__file__, "-v"])
