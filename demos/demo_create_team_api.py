"""
演示建立團隊 API 端點 (Task 6.1)
使用 requests 直接測試 API
"""

import requests
import uuid
import json

# API 基礎 URL（假設 FastAPI 運行在 localhost:8080）
BASE_URL = "http://localhost:8080"


def test_create_team_success():
    """測試成功建立團隊"""
    print("\n=== 測試 1: 成功建立團隊 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "測試團隊"
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        data = response.json()
        assert "team_id" in data
        assert "team_name" in data
        assert "invite_url" in data
        assert data["team_name"] == "測試團隊"
        print("✅ 測試通過")
    else:
        print("❌ 測試失敗")


def test_create_team_empty_name():
    """測試空白團隊名稱"""
    print("\n=== 測試 2: 空白團隊名稱 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "   "
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 400 and "團隊名稱不可為空" in response.json()["detail"]:
        print("✅ 測試通過")
    else:
        print("❌ 測試失敗")


def test_create_team_name_too_long():
    """測試團隊名稱過長"""
    print("\n=== 測試 3: 團隊名稱過長 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    response = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "A" * 31
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 400 and "不可超過 30 字元" in response.json()["detail"]:
        print("✅ 測試通過")
    else:
        print("❌ 測試失敗")


def test_create_team_duplicate_leader():
    """測試重複建立團隊"""
    print("\n=== 測試 4: 重複建立團隊 ===")
    
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    # 第一次建立
    response1 = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "第一個團隊"
        }
    )
    print(f"第一次建立 - 狀態碼: {response1.status_code}")
    
    # 第二次建立
    response2 = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "leader_uid": leader_uid,
            "team_name": "第二個團隊"
        }
    )
    print(f"第二次建立 - 狀態碼: {response2.status_code}")
    print(f"回應: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")
    
    if response2.status_code == 409 and "已經是隊長" in response2.json()["detail"]:
        print("✅ 測試通過")
    else:
        print("❌ 測試失敗")


if __name__ == "__main__":
    print("=" * 60)
    print("建立團隊 API 測試")
    print("=" * 60)
    print("\n⚠️  請確保 FastAPI 伺服器正在運行 (python main.py)")
    print("⚠️  如果伺服器未運行，請先執行: python main.py")
    
    try:
        # 檢查伺服器是否運行
        response = requests.get(f"{BASE_URL}/")
        print(f"\n✅ 伺服器正在運行")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 無法連接到伺服器 ({BASE_URL})")
        print("請先啟動 FastAPI 伺服器: python main.py")
        exit(1)
    
    # 執行測試
    test_create_team_success()
    test_create_team_empty_name()
    test_create_team_name_too_long()
    test_create_team_duplicate_leader()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
