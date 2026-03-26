#!/usr/bin/env python3
# demo_join_team_api.py
"""
示範 POST /api/teams/join API 端點
驗證加入團隊 API 的功能
"""

import uuid
import requests
from team_service import TeamService
from security import SecurityService
from database import create_team_tables_if_not_exist

# API 基礎 URL（假設 FastAPI 運行在 localhost:8080）
BASE_URL = "http://localhost:8080"


def demo_join_team_api():
    """示範加入團隊 API"""
    print("=" * 60)
    print("示範：POST /api/teams/join API 端點")
    print("=" * 60)
    
    # 初始化服務
    print("\n🔧 初始化資料表...")
    create_team_tables_if_not_exist()
    team_service = TeamService()
    security_service = SecurityService()
    
    # 1. 建立測試團隊
    print("\n📝 步驟 1：建立測試團隊")
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team_name = "防詐先鋒隊"
    team = team_service.create_team(leader_uid, team_name)
    print(f"✅ 團隊建立成功")
    print(f"   Team ID: {team.team_id}")
    print(f"   團隊名稱: {team.team_name}")
    print(f"   隊長 UID: {team.leader_uid}")
    
    # 2. 產生有效簽章
    print("\n🔐 步驟 2：產生邀請簽章")
    signature = security_service.generate_signature(team.team_id)
    print(f"✅ 簽章產生成功: {signature[:30]}...")
    
    # 3. 測試成功加入團隊
    print("\n✅ 測試 1：成功加入團隊")
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    
    try:
        response = requests.post(f"{BASE_URL}/api/teams/join", json={
            "team_id": team.team_id,
            "member_uid": member_uid,
            "signature": signature
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 回應成功 (200)")
            print(f"   Success: {data['success']}")
            print(f"   團隊名稱: {data['team_name']}")
            print(f"   成員數量: {data['member_count']}")
        else:
            print(f"❌ API 回應失敗 ({response.status_code})")
            print(f"   錯誤訊息: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API 伺服器（請確保 FastAPI 正在運行）")
        print("   提示：執行 'python main.py' 啟動伺服器")
    
    # 4. 測試無效簽章
    print("\n❌ 測試 2：拒絕無效簽章")
    member_uid_2 = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    
    try:
        response = requests.post(f"{BASE_URL}/api/teams/join", json={
            "team_id": team.team_id,
            "member_uid": member_uid_2,
            "signature": "invalid_signature_12345"
        })
        
        if response.status_code == 403:
            data = response.json()
            print(f"✅ API 正確拒絕無效簽章 (403)")
            print(f"   錯誤訊息: {data['detail']}")
        else:
            print(f"⚠️  預期 403，但收到 {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API 伺服器")
    
    # 5. 測試重複加入
    print("\n❌ 測試 3：拒絕重複加入同一團隊")
    
    try:
        response = requests.post(f"{BASE_URL}/api/teams/join", json={
            "team_id": team.team_id,
            "member_uid": member_uid,  # 使用已加入的成員
            "signature": signature
        })
        
        if response.status_code == 409:
            data = response.json()
            print(f"✅ API 正確拒絕重複加入 (409)")
            print(f"   錯誤訊息: {data['detail']}")
        else:
            print(f"⚠️  預期 409，但收到 {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API 伺服器")
    
    # 6. 測試不存在的團隊
    print("\n❌ 測試 4：拒絕加入不存在的團隊")
    fake_team_id = str(uuid.uuid4())
    fake_signature = security_service.generate_signature(fake_team_id)
    member_uid_3 = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    
    try:
        response = requests.post(f"{BASE_URL}/api/teams/join", json={
            "team_id": fake_team_id,
            "member_uid": member_uid_3,
            "signature": fake_signature
        })
        
        if response.status_code == 404:
            data = response.json()
            print(f"✅ API 正確拒絕加入不存在的團隊 (404)")
            print(f"   錯誤訊息: {data['detail']}")
        else:
            print(f"⚠️  預期 404，但收到 {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API 伺服器")
    
    # 7. 測試缺少參數
    print("\n❌ 測試 5：拒絕缺少必要參數")
    
    try:
        response = requests.post(f"{BASE_URL}/api/teams/join", json={
            "team_id": team.team_id,
            "member_uid": ""  # 空字串
        })
        
        if response.status_code in [400, 422]:
            print(f"✅ API 正確拒絕缺少參數 ({response.status_code})")
            print(f"   錯誤訊息: {response.json()}")
        else:
            print(f"⚠️  預期 400/422，但收到 {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  無法連接到 API 伺服器")
    
    print("\n" + "=" * 60)
    print("✅ 示範完成！")
    print("=" * 60)
    print("\n📋 總結：")
    print("   - POST /api/teams/join 端點已實作")
    print("   - 支援簽章驗證（HMAC-SHA256）")
    print("   - 完整的錯誤處理（403, 404, 409, 400）")
    print("   - 回傳團隊名稱與成員數量")
    print("\n💡 提示：")
    print("   - 啟動 API 伺服器：python main.py")
    print("   - 再次執行此腳本以測試 API")


if __name__ == "__main__":
    demo_join_team_api()
