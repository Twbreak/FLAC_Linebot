# test_join_team.py
"""
測試 TeamService.join_team() 方法
驗證加入團隊功能的各種情境
"""

import pytest
import uuid
from datetime import datetime
from team_service import TeamService
from security import SecurityService
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
def security_service():
    """建立 SecurityService 實例"""
    return SecurityService()


def test_join_team_success(setup_tables, team_service, security_service):
    """測試成功加入團隊"""
    print("\n🧪 測試：成功加入團隊")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team_name = "測試團隊"
    team = team_service.create_team(leader_uid, team_name)
    print(f"✅ 建立測試團隊: {team.team_id}")
    
    # 2. 產生有效簽章
    signature = security_service.generate_signature(team.team_id)
    print(f"✅ 產生簽章: {signature[:20]}...")
    
    # 3. 新成員加入團隊
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    result = team_service.join_team(team.team_id, member_uid, signature)
    
    assert result == True
    print(f"✅ 成員加入成功")
    
    # 4. 驗證 TeamMembers 表中的資料
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team.team_id}#{member_uid}"
    response = team_members_table.get_item(Key={'member_id': member_id})
    
    assert 'Item' in response
    db_member = response['Item']
    assert db_member['team_id'] == team.team_id
    assert db_member['line_uid'] == member_uid
    assert db_member['contribution_points'] == 0
    assert db_member['report_count'] == 0
    assert db_member['is_leader'] == False
    print(f"✅ TeamMembers 表資料正確")
    
    # 5. 驗證 Teams 表的 member_count 已更新
    teams_table = dynamodb.Table('Teams')
    team_response = teams_table.get_item(Key={'team_id': team.team_id})
    assert 'Item' in team_response
    assert team_response['Item']['member_count'] == 2  # 隊長 + 新成員
    print(f"✅ member_count 已更新為 2")
    
    print(f"✅ 測試通過：成功加入團隊")


def test_join_team_invalid_signature(setup_tables, team_service):
    """測試無效簽章被拒絕"""
    print("\n🧪 測試：拒絕無效簽章")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team = team_service.create_team(leader_uid, "測試團隊")
    
    # 2. 使用無效簽章嘗試加入
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    invalid_signature = "invalid_signature_12345"
    
    with pytest.raises(ValueError) as exc_info:
        team_service.join_team(team.team_id, member_uid, invalid_signature)
    
    assert "無效的邀請連結" in str(exc_info.value)
    print(f"✅ 測試通過：正確拒絕無效簽章")


def test_join_team_nonexistent_team(setup_tables, team_service, security_service):
    """測試加入不存在的團隊"""
    print("\n🧪 測試：拒絕加入不存在的團隊")
    
    # 1. 產生不存在的 team_id
    fake_team_id = str(uuid.uuid4())
    signature = security_service.generate_signature(fake_team_id)
    
    # 2. 嘗試加入不存在的團隊
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    
    with pytest.raises(ValueError) as exc_info:
        team_service.join_team(fake_team_id, member_uid, signature)
    
    assert "團隊不存在或已解散" in str(exc_info.value)
    print(f"✅ 測試通過：正確拒絕加入不存在的團隊")


def test_join_team_already_member(setup_tables, team_service, security_service):
    """測試重複加入同一團隊"""
    print("\n🧪 測試：拒絕重複加入同一團隊")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team = team_service.create_team(leader_uid, "測試團隊")
    
    # 2. 成員首次加入
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    signature = security_service.generate_signature(team.team_id)
    result = team_service.join_team(team.team_id, member_uid, signature)
    assert result == True
    print(f"✅ 首次加入成功")
    
    # 3. 嘗試再次加入同一團隊
    with pytest.raises(ValueError) as exc_info:
        team_service.join_team(team.team_id, member_uid, signature)
    
    assert "您已經是團隊成員" in str(exc_info.value)
    print(f"✅ 測試通過：正確拒絕重複加入")


def test_join_team_already_in_other_team(setup_tables, team_service, security_service):
    """測試加入其他團隊（使用者已在另一團隊）"""
    print("\n🧪 測試：拒絕加入其他團隊（使用者已在另一團隊）")
    
    # 1. 建立第一個團隊
    leader_uid_1 = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team1 = team_service.create_team(leader_uid_1, "第一個團隊")
    
    # 2. 成員加入第一個團隊
    member_uid = f"U_MEMBER_{uuid.uuid4().hex[:8]}"
    signature1 = security_service.generate_signature(team1.team_id)
    result = team_service.join_team(team1.team_id, member_uid, signature1)
    assert result == True
    print(f"✅ 成員加入第一個團隊成功")
    
    # 3. 建立第二個團隊
    leader_uid_2 = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team2 = team_service.create_team(leader_uid_2, "第二個團隊")
    
    # 4. 嘗試加入第二個團隊（應該失敗）
    signature2 = security_service.generate_signature(team2.team_id)
    
    with pytest.raises(ValueError) as exc_info:
        team_service.join_team(team2.team_id, member_uid, signature2)
    
    assert "您已加入其他團隊，請先退出" in str(exc_info.value)
    print(f"✅ 測試通過：正確拒絕跨團隊加入")


def test_join_team_leader_is_already_member(setup_tables, team_service, security_service):
    """測試隊長嘗試再次加入自己的團隊"""
    print("\n🧪 測試：隊長嘗試再次加入自己的團隊")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team = team_service.create_team(leader_uid, "測試團隊")
    
    # 2. 隊長嘗試加入自己的團隊
    signature = security_service.generate_signature(team.team_id)
    
    with pytest.raises(ValueError) as exc_info:
        team_service.join_team(team.team_id, leader_uid, signature)
    
    assert "您已經是團隊成員" in str(exc_info.value)
    print(f"✅ 測試通過：正確拒絕隊長重複加入")


def test_join_team_multiple_members(setup_tables, team_service, security_service):
    """測試多位成員依序加入團隊"""
    print("\n🧪 測試：多位成員依序加入團隊")
    
    # 1. 建立測試團隊
    leader_uid = f"U_LEADER_{uuid.uuid4().hex[:8]}"
    team = team_service.create_team(leader_uid, "測試團隊")
    signature = security_service.generate_signature(team.team_id)
    
    # 2. 5 位成員依序加入
    member_uids = []
    for i in range(5):
        member_uid = f"U_MEMBER_{i}_{uuid.uuid4().hex[:8]}"
        member_uids.append(member_uid)
        result = team_service.join_team(team.team_id, member_uid, signature)
        assert result == True
        print(f"✅ 成員 {i+1} 加入成功")
    
    # 3. 驗證 member_count
    teams_table = dynamodb.Table('Teams')
    team_response = teams_table.get_item(Key={'team_id': team.team_id})
    assert team_response['Item']['member_count'] == 6  # 隊長 + 5 位成員
    print(f"✅ member_count 正確：6")
    
    # 4. 驗證所有成員都在 TeamMembers 表中
    team_members_table = dynamodb.Table('TeamMembers')
    for member_uid in member_uids:
        member_id = f"{team.team_id}#{member_uid}"
        response = team_members_table.get_item(Key={'member_id': member_id})
        assert 'Item' in response
    print(f"✅ 所有成員資料都已寫入")
    
    print(f"✅ 測試通過：多位成員成功加入團隊")


if __name__ == "__main__":
    # 直接執行測試
    pytest.main([__file__, "-v", "-s"])
