"""
測試建立團隊 API 端點 (Task 6.1)
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import uuid
from urllib.parse import urlparse, parse_qs, unquote

client = TestClient(app)


def test_create_team_success():
    """測試成功建立團隊"""
    # 使用唯一的 leader_uid 避免重複
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "測試團隊"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 驗證回傳資料
    assert "team_id" in data
    assert "team_name" in data
    assert "invite_url" in data
    assert data["team_name"] == "測試團隊"
    
    # 驗證 team_id 是 UUID 格式
    try:
        uuid.UUID(data["team_id"])
    except ValueError:
        pytest.fail("team_id 不是有效的 UUID 格式")
    
    # 驗證 invite_url 為 LIFF URL，且 team_id / signature 透過 liff.state 傳遞
    assert "liff.line.me" in data["invite_url"]
    parsed_url = urlparse(data["invite_url"])
    query = parse_qs(parsed_url.query)
    assert "liff.state" in query

    decoded_state = unquote(query["liff.state"][0])
    assert "team_id=" in decoded_state
    assert "signature=" in decoded_state
    
    print(f"✅ 成功建立團隊: {data['team_id']}")


def test_create_team_empty_name():
    """測試空白團隊名稱"""
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "   "  # 只有空白字元
        }
    )
    
    assert response.status_code == 400
    assert "團隊名稱不可為空" in response.json()["detail"]
    print("✅ 正確拒絕空白團隊名稱")


def test_create_team_name_too_long():
    """測試團隊名稱過長"""
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "A" * 31  # 超過 30 字元
        }
    )
    
    assert response.status_code == 422
    assert "at most 30 characters" in str(response.json()["detail"])
    print("✅ 正確拒絕過長的團隊名稱")


def test_create_team_duplicate_leader():
    """測試重複建立團隊（同一隊長）"""
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    # 第一次建立
    response1 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "第一個團隊"
        }
    )
    assert response1.status_code == 200
    
    # 第二次建立（應該失敗）
    response2 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "第二個團隊"
        }
    )
    
    assert response2.status_code == 409
    assert "已經是隊長" in response2.json()["detail"]
    print("✅ 正確拒絕重複建立團隊")


def test_create_team_valid_name_length():
    """測試有效的團隊名稱長度（1-30 字元）"""
    # 測試 1 字元
    leader_uid1 = f"U{uuid.uuid4().hex[:10]}"
    response1 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid1,
            "team_name": "A"
        }
    )
    assert response1.status_code == 200
    print("✅ 1 字元團隊名稱有效")
    
    # 測試 30 字元
    leader_uid2 = f"U{uuid.uuid4().hex[:10]}"
    response2 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid2,
            "team_name": "A" * 30
        }
    )
    assert response2.status_code == 200
    print("✅ 30 字元團隊名稱有效")


if __name__ == "__main__":
    print("開始測試建立團隊 API...")
    print()
    
    test_create_team_success()
    test_create_team_empty_name()
    test_create_team_name_too_long()
    test_create_team_duplicate_leader()
    test_create_team_valid_name_length()
    
    print()
    print("🎉 所有測試通過！")
