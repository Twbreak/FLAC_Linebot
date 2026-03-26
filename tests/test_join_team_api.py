# test_join_team_api.py
"""
測試 POST /api/teams/join API 端點
驗證加入團隊 API 的各種情境
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from team_service import TeamService
from security import SecurityService
from database import create_team_tables_if_not_exist

# 建立 FastAPI 測試客戶端
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_tables():
    """設定測試環境：建立資料表"""
    print("\n🔧 設定測試環境：建立 DynamoDB 資料表...")
    create_team_tables_if_not_exist()
    yield
    print("\n✅ 測試完成")


@pytest.fixture
def team_service():
    """建立 TeamService 實例"""
    return TeamService()


@pytest.fixture
def security_service():
    """建立 SecurityService 實例"""
    return SecurityService()


def test_join_team_api_success(setup_tables, team_service, security_service):
    """測試成功加入團隊 API"""
    print("\n🧪 測試：成功加入團隊 API")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    team = team_service.create_team(leader_uid, team_name)
    print(f"✅ 建立測試團隊: {team.team_id}")
    
    # 2. 產生有效簽章
    signature = security_service.generate_signature(team.team_id)
    print(f"✅ 產生簽章: {signature[:20]}...")
    
    # 3. 呼叫 API 加入團隊
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    response = client.post("/api/teams/join", json={
        "team_id": team.team_id,
        "member_uid": member_uid,
        "signature": signature
    })
    
    # 4. 驗證回應
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["team_name"] == team_name
    assert data["member_count"] == 2  # 隊長 + 新成員
    print(f"✅ API 回應正確: {data}")
    
    print(f"✅ 測試通過：成功加入團隊 API")


def test_join_team_api_invalid_signature(setup_tables, team_service):
    """測試無效簽章被拒絕"""
    print("\n🧪 測試：API 拒絕無效簽章")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team = team_service.create_team(leader_uid, "測試團隊")
    
    # 2. 使用無效簽章呼叫 API
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    response = client.post("/api/teams/join", json={
        "team_id": team.team_id,
        "member_uid": member_uid,
        "signature": "invalid_signature_12345"
    })
    
    # 3. 驗證回應
    assert response.status_code == 403
    data = response.json()
    assert "無效的邀請連結" in data["detail"]
    print(f"✅ API 正確拒絕無效簽章: {data['detail']}")
    
    print(f"✅ 測試通過：API 正確拒絕無效簽章")


def test_join_team_api_nonexistent_team(setup_tables, security_service):
    """測試加入不存在的團隊"""
    print("\n🧪 測試：API 拒絕加入不存在的團隊")
    
    # 1. 產生不存在的 team_id
    fake_team_id = str(uuid.uuid4())
    signature = security_service.generate_signature(fake_team_id)
    
    # 2. 呼叫 API 嘗試加入不存在的團隊
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    response = client.post("/api/teams/join", json={
        "team_id": fake_team_id,
        "member_uid": member_uid,
        "signature": signature
    })
    
    # 3. 驗證回應
    assert response.status_code == 404
    data = response.json()
    assert "團隊不存在或已解散" in data["detail"]
    print(f"✅ API 正確拒絕加入不存在的團隊: {data['detail']}")
    
    print(f"✅ 測試通過：API 正確拒絕加入不存在的團隊")


def test_join_team_api_already_member(setup_tables, team_service, security_service):
    """測試重複加入同一團隊"""
    print("\n🧪 測試：API 拒絕重複加入同一團隊")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team = team_service.create_team(leader_uid, "測試團隊")
    signature = security_service.generate_signature(team.team_id)
    
    # 2. 成員首次加入
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    response1 = client.post("/api/teams/join", json={
        "team_id": team.team_id,
        "member_uid": member_uid,
        "signature": signature
    })
    assert response1.status_code == 200
    print(f"✅ 首次加入成功")
    
    # 3. 嘗試再次加入同一團隊
    response2 = client.post("/api/teams/join", json={
        "team_id": team.team_id,
        "member_uid": member_uid,
        "signature": signature
    })
    
    # 4. 驗證回應
    assert response2.status_code == 409
    data = response2.json()
    assert "您已經是團隊成員" in data["detail"]
    print(f"✅ API 正確拒絕重複加入: {data['detail']}")
    
    print(f"✅ 測試通過：API 正確拒絕重複加入")


def test_join_team_api_already_in_other_team(setup_tables, team_service, security_service):
    """測試加入其他團隊（使用者已在另一團隊）"""
    print("\n🧪 測試：API 拒絕加入其他團隊（使用者已在另一團隊）")
    
    # 1. 建立第一個團隊
    leader_uid_1 = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team1 = team_service.create_team(leader_uid_1, "第一個團隊")
    signature1 = security_service.generate_signature(team1.team_id)
    
    # 2. 成員加入第一個團隊
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    response1 = client.post("/api/teams/join", json={
        "team_id": team1.team_id,
        "member_uid": member_uid,
        "signature": signature1
    })
    assert response1.status_code == 200
    print(f"✅ 成員加入第一個團隊成功")
    
    # 3. 建立第二個團隊
    leader_uid_2 = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team2 = team_service.create_team(leader_uid_2, "第二個團隊")
    signature2 = security_service.generate_signature(team2.team_id)
    
    # 4. 嘗試加入第二個團隊（應該失敗）
    response2 = client.post("/api/teams/join", json={
        "team_id": team2.team_id,
        "member_uid": member_uid,
        "signature": signature2
    })
    
    # 5. 驗證回應
    assert response2.status_code == 409
    data = response2.json()
    assert "您已加入其他團隊" in data["detail"]
    print(f"✅ API 正確拒絕跨團隊加入: {data['detail']}")
    
    print(f"✅ 測試通過：API 正確拒絕跨團隊加入")


def test_join_team_api_missing_parameters(setup_tables):
    """測試缺少必要參數"""
    print("\n🧪 測試：API 拒絕缺少必要參數的請求")
    
    # 1. 缺少 signature
    response1 = client.post("/api/teams/join", json={
        "team_id": "some_team_id",
        "member_uid": "U123456"
    })
    assert response1.status_code == 422  # FastAPI validation error
    print(f"✅ 缺少 signature 被拒絕")
    
    # 2. 缺少 team_id
    response2 = client.post("/api/teams/join", json={
        "member_uid": "U123456",
        "signature": "some_signature"
    })
    assert response2.status_code == 422
    print(f"✅ 缺少 team_id 被拒絕")
    
    # 3. 缺少 member_uid
    response3 = client.post("/api/teams/join", json={
        "team_id": "some_team_id",
        "signature": "some_signature"
    })
    assert response3.status_code == 422
    print(f"✅ 缺少 member_uid 被拒絕")
    
    print(f"✅ 測試通過：API 正確驗證必要參數")


def test_join_team_api_empty_parameters(setup_tables):
    """測試空字串參數"""
    print("\n🧪 測試：API 拒絕空字串參數")
    
    response = client.post("/api/teams/join", json={
        "team_id": "",
        "member_uid": "",
        "signature": ""
    })
    
    # 驗證回應（應該被拒絕）
    assert response.status_code == 400
    data = response.json()
    assert "缺少必要參數" in data["detail"]
    print(f"✅ API 正確拒絕空字串參數: {data['detail']}")
    
    print(f"✅ 測試通過：API 正確拒絕空字串參數")


if __name__ == "__main__":
    # 直接執行測試
    pytest.main([__file__, "-v", "-s"])
