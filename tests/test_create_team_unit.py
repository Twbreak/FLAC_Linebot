"""
單元測試建立團隊 API 端點 (Task 6.1)
使用 FastAPI TestClient，不需要啟動伺服器
"""

from fastapi.testclient import TestClient
from main import app
import uuid
from urllib.parse import urlparse, parse_qs, unquote

client = TestClient(app)


def test_create_team_success():
    """測試成功建立團隊"""
    print("\n=== 測試 1: 成功建立團隊 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "測試團隊"
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "team_id" in data
    assert "team_name" in data
    assert "invite_url" in data
    assert data["team_name"] == "測試團隊"
    
    # 驗證 team_id 是 UUID 格式
    try:
        uuid.UUID(data["team_id"])
        print("✅ team_id 是有效的 UUID")
    except ValueError:
        raise AssertionError("team_id 不是有效的 UUID 格式")
    
    # 驗證 invite_url 為 LIFF URL，且 team_id / signature 透過 liff.state 傳遞
    assert "liff.line.me" in data["invite_url"]
    parsed_url = urlparse(data["invite_url"])
    query = parse_qs(parsed_url.query)
    assert "liff.state" in query

    decoded_state = unquote(query["liff.state"][0])
    assert "team_id=" in decoded_state
    assert "signature=" in decoded_state
    
    print("✅ 測試通過")


def test_create_team_empty_name():
    """測試空白團隊名稱"""
    print("\n=== 測試 2: 空白團隊名稱 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "   "
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    assert response.status_code == 400
    assert "團隊名稱不可為空" in response.json()["detail"]
    print("✅ 測試通過")


def test_create_team_name_too_long():
    """測試團隊名稱過長"""
    print("\n=== 測試 3: 團隊名稱過長 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "A" * 31
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # Pydantic 會在 422 狀態碼回傳驗證錯誤，或我們的程式碼在 400 回傳
    assert response.status_code in [400, 422]
    response_data = response.json()
    
    # 檢查錯誤訊息（可能在 detail 或 detail[0]['msg'] 中）
    if response.status_code == 422:
        # Pydantic 驗證錯誤
        assert "detail" in response_data
        assert len(response_data["detail"]) > 0
        print("✅ 測試通過（Pydantic 驗證）")
    else:
        # 我們的程式碼驗證
        assert "不可超過 30 字元" in response_data["detail"]
        print("✅ 測試通過（應用程式驗證）")


def test_create_team_duplicate_leader():
    """測試重複建立團隊"""
    print("\n=== 測試 4: 重複建立團隊 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    # 第一次建立
    response1 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "第一個團隊"
        }
    )
    print(f"第一次建立 - 狀態碼: {response1.status_code}")
    assert response1.status_code == 200
    
    # 第二次建立（應該失敗）
    response2 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "第二個團隊"
        }
    )
    print(f"第二次建立 - 狀態碼: {response2.status_code}")
    print(f"回應: {response2.json()}")
    
    assert response2.status_code == 409
    assert "已經是隊長" in response2.json()["detail"]
    print("✅ 測試通過")


def test_create_team_valid_name_length():
    """測試有效的團隊名稱長度"""
    print("\n=== 測試 5: 有效的團隊名稱長度 ===")
    
    # 測試 1 字元
    leader_uid1 = f"U{uuid.uuid4().hex[:10]}"
    response1 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid1,
            "team_name": "A"
        }
    )
    print(f"1 字元 - 狀態碼: {response1.status_code}")
    assert response1.status_code == 200
    
    # 測試 30 字元
    leader_uid2 = f"U{uuid.uuid4().hex[:10]}"
    response2 = client.post(
        "/api/teams/create",
        json={
            "leader_uid": leader_uid2,
            "team_name": "A" * 30
        }
    )
    print(f"30 字元 - 狀態碼: {response2.status_code}")
    assert response2.status_code == 200
    
    print("✅ 測試通過")


if __name__ == "__main__":
    print("=" * 60)
    print("建立團隊 API 單元測試")
    print("=" * 60)
    
    try:
        test_create_team_success()
        test_create_team_empty_name()
        test_create_team_name_too_long()
        test_create_team_duplicate_leader()
        test_create_team_valid_name_length()
        
        print("\n" + "=" * 60)
        print("🎉 所有測試通過！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
