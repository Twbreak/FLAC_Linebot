# test_team_service.py
"""
團隊服務模組測試
測試 TeamService 類別的功能
"""

import pytest
import uuid
from datetime import datetime
from team_service import TeamService
from models import Team, TeamMember
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
def cleanup_test_data():
    """清理測試資料"""
    yield
    # 測試後清理（可選）
    pass


def test_create_team_success(setup_tables, team_service, cleanup_test_data):
    """測試成功建立團隊"""
    print("\n🧪 測試：成功建立團隊")
    
    # 產生唯一的測試 UID
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    
    # 建立團隊
    team = team_service.create_team(leader_uid, team_name)
    
    # 驗證團隊物件
    assert team is not None
    assert team.team_id is not None
    assert team.team_name == team_name
    assert team.leader_uid == leader_uid
    assert team.total_points == 0
    assert team.member_count == 1
    assert isinstance(team.created_at, datetime)
    assert team.completed_quests == []
    
    # 驗證 UUID 格式
    try:
        uuid.UUID(team.team_id)
        print(f"✅ Team ID 格式正確: {team.team_id}")
    except ValueError:
        pytest.fail(f"Team ID 不是有效的 UUID 格式: {team.team_id}")
    
    # 驗證 Teams 表中的資料
    teams_table = dynamodb.Table('Teams')
    response = teams_table.get_item(Key={'team_id': team.team_id})
    assert 'Item' in response
    db_team = response['Item']
    assert db_team['team_name'] == team_name
    assert db_team['leader_uid'] == leader_uid
    assert db_team['total_points'] == 0
    assert db_team['member_count'] == 1
    print(f"✅ Teams 表資料正確")
    
    # 驗證 TeamMembers 表中的資料
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team.team_id}#{leader_uid}"
    response = team_members_table.get_item(Key={'member_id': member_id})
    assert 'Item' in response
    db_member = response['Item']
    assert db_member['team_id'] == team.team_id
    assert db_member['line_uid'] == leader_uid
    assert db_member['contribution_points'] == 0
    assert db_member['report_count'] == 0
    assert db_member['is_leader'] == True
    print(f"✅ TeamMembers 表資料正確（隊長作為首位成員）")
    
    print(f"✅ 測試通過：團隊建立成功")


def test_create_team_duplicate_leader(setup_tables, team_service, cleanup_test_data):
    """測試重複建立團隊（同一使用者已是隊長）"""
    print("\n🧪 測試：拒絕重複建立團隊")
    
    # 產生唯一的測試 UID
    leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
    team_name_1 = "第一個團隊"
    team_name_2 = "第二個團隊"
    
    # 第一次建立團隊（應該成功）
    team1 = team_service.create_team(leader_uid, team_name_1)
    assert team1 is not None
    print(f"✅ 第一次建立團隊成功: {team1.team_id}")
    
    # 第二次建立團隊（應該失敗）
    with pytest.raises(ValueError) as exc_info:
        team_service.create_team(leader_uid, team_name_2)
    
    assert "您已經是隊長，無法建立多個團隊" in str(exc_info.value)
    print(f"✅ 測試通過：正確拒絕重複建立團隊")


def test_create_team_uuid_uniqueness(setup_tables, team_service, cleanup_test_data):
    """測試 Team ID 唯一性"""
    print("\n🧪 測試：Team ID 唯一性")
    
    team_ids = set()
    
    # 建立多個團隊
    for i in range(5):
        leader_uid = f"U_TEST_{uuid.uuid4().hex[:8]}"
        team_name = f"測試團隊 {i+1}"
        team = team_service.create_team(leader_uid, team_name)
        
        # 檢查 Team ID 是否唯一
        assert team.team_id not in team_ids, f"Team ID 重複: {team.team_id}"
        team_ids.add(team.team_id)
        print(f"✅ 團隊 {i+1} 建立成功，Team ID: {team.team_id}")
    
    print(f"✅ 測試通過：所有 Team ID 都是唯一的")


if __name__ == "__main__":
    # 直接執行測試
    pytest.main([__file__, "-v", "-s"])
