# test_team_service_simple.py
"""
團隊服務模組簡單測試
測試 TeamService 類別的 create_team() 功能
"""

import uuid
from datetime import datetime
from team_service import TeamService
from database import create_team_tables_if_not_exist
import boto3
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# DynamoDB 設定
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")

# 初始化 DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


def test_create_team_success():
    """測試成功建立團隊"""
    print("\n" + "=" * 60)
    print("🧪 測試 1：成功建立團隊")
    print("=" * 60)
    
    # 建立測試環境
    print("🔧 設定測試環境：建立 DynamoDB 資料表...")
    create_team_tables_if_not_exist()
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 產生唯一的測試 UID
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    
    print(f"\n📝 建立團隊...")
    print(f"   隊長 UID: {leader_uid}")
    print(f"   團隊名稱: {team_name}")
    
    # 建立團隊
    team = team_service.create_team(leader_uid, team_name)
    
    # 驗證團隊物件
    print(f"\n✅ 團隊建立成功！")
    print(f"   Team ID: {team.team_id}")
    print(f"   團隊名稱: {team.team_name}")
    print(f"   隊長 UID: {team.leader_uid}")
    print(f"   總積分: {team.total_points}")
    print(f"   成員數: {team.member_count}")
    print(f"   建立時間: {team.created_at}")
    
    assert team is not None, "團隊物件不應為 None"
    assert team.team_id is not None, "Team ID 不應為 None"
    assert team.team_name == team_name, f"團隊名稱不符：期望 {team_name}，實際 {team.team_name}"
    assert team.leader_uid == leader_uid, f"隊長 UID 不符：期望 {leader_uid}，實際 {team.leader_uid}"
    assert team.total_points == 0, f"初始積分應為 0，實際 {team.total_points}"
    assert team.member_count == 1, f"初始成員數應為 1，實際 {team.member_count}"
    assert isinstance(team.created_at, datetime), "建立時間應為 datetime 物件"
    assert team.completed_quests == [], f"初始任務清單應為空，實際 {team.completed_quests}"
    
    # 驗證 UUID 格式
    try:
        uuid.UUID(team.team_id)
        print(f"\n✅ Team ID 格式驗證通過（UUID 格式）")
    except ValueError:
        raise AssertionError(f"Team ID 不是有效的 UUID 格式: {team.team_id}")
    
    # 驗證 Teams 表中的資料
    print(f"\n🔍 驗證 Teams 表資料...")
    teams_table = dynamodb.Table('Teams')
    response = teams_table.get_item(Key={'team_id': team.team_id})
    assert 'Item' in response, "Teams 表中找不到團隊資料"
    db_team = response['Item']
    assert db_team['team_name'] == team_name, "Teams 表中的團隊名稱不符"
    assert db_team['leader_uid'] == leader_uid, "Teams 表中的隊長 UID 不符"
    assert db_team['total_points'] == 0, "Teams 表中的初始積分不為 0"
    assert db_team['member_count'] == 1, "Teams 表中的初始成員數不為 1"
    print(f"✅ Teams 表資料驗證通過")
    
    # 驗證 TeamMembers 表中的資料
    print(f"\n🔍 驗證 TeamMembers 表資料...")
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team.team_id}#{leader_uid}"
    response = team_members_table.get_item(Key={'member_id': member_id})
    assert 'Item' in response, "TeamMembers 表中找不到成員資料"
    db_member = response['Item']
    assert db_member['team_id'] == team.team_id, "TeamMembers 表中的 team_id 不符"
    assert db_member['line_uid'] == leader_uid, "TeamMembers 表中的 line_uid 不符"
    assert db_member['contribution_points'] == 0, "TeamMembers 表中的初始貢獻積分不為 0"
    assert db_member['report_count'] == 0, "TeamMembers 表中的初始通報次數不為 0"
    assert db_member['is_leader'] == True, "TeamMembers 表中的 is_leader 應為 True"
    print(f"✅ TeamMembers 表資料驗證通過（隊長作為首位成員）")
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 1 通過：團隊建立成功")
    print("=" * 60)
    
    return team


def test_create_team_duplicate_leader():
    """測試重複建立團隊（同一使用者已是隊長）"""
    print("\n" + "=" * 60)
    print("🧪 測試 2：拒絕重複建立團隊")
    print("=" * 60)
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    # 產生唯一的測試 UID
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name_1 = "第一個團隊"
    team_name_2 = "第二個團隊"
    
    # 第一次建立團隊（應該成功）
    print(f"\n📝 第一次建立團隊...")
    print(f"   隊長 UID: {leader_uid}")
    print(f"   團隊名稱: {team_name_1}")
    team1 = team_service.create_team(leader_uid, team_name_1)
    assert team1 is not None, "第一次建立團隊失敗"
    print(f"✅ 第一次建立團隊成功: {team1.team_id}")
    
    # 第二次建立團隊（應該失敗）
    print(f"\n📝 第二次建立團隊（應該失敗）...")
    print(f"   隊長 UID: {leader_uid}")
    print(f"   團隊名稱: {team_name_2}")
    
    try:
        team2 = team_service.create_team(leader_uid, team_name_2)
        raise AssertionError("第二次建立團隊應該失敗，但卻成功了")
    except ValueError as e:
        error_message = str(e)
        print(f"✅ 正確拋出 ValueError: {error_message}")
        assert "您已經是隊長，無法建立多個團隊" in error_message, f"錯誤訊息不符：{error_message}"
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 2 通過：正確拒絕重複建立團隊")
    print("=" * 60)


def test_create_team_uuid_uniqueness():
    """測試 Team ID 唯一性"""
    print("\n" + "=" * 60)
    print("🧪 測試 3：Team ID 唯一性")
    print("=" * 60)
    
    # 建立 TeamService 實例
    team_service = TeamService()
    
    team_ids = set()
    
    # 建立多個團隊
    print(f"\n📝 建立 5 個團隊，驗證 Team ID 唯一性...")
    for i in range(5):
        leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
        team_name = f"測試團隊 {i+1}"
        team = team_service.create_team(leader_uid, team_name)
        
        # 檢查 Team ID 是否唯一
        assert team.team_id not in team_ids, f"Team ID 重複: {team.team_id}"
        team_ids.add(team.team_id)
        print(f"   ✅ 團隊 {i+1} - Team ID: {team.team_id}")
    
    print(f"\n" + "=" * 60)
    print(f"✅ 測試 3 通過：所有 Team ID 都是唯一的")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 開始執行團隊服務測試")
    print("=" * 60)
    
    try:
        # 執行測試
        test_create_team_success()
        test_create_team_duplicate_leader()
        test_create_team_uuid_uniqueness()
        
        print("\n" + "=" * 60)
        print("🎉 所有測試通過！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 測試執行錯誤: {e}")
        raise
