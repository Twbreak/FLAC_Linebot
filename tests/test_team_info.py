"""
測試團隊資訊查詢功能 (Task 3.7)
"""

from team_service import TeamService
from datetime import datetime


def test_get_team_info_success():
    """測試成功取得團隊資訊"""
    service = TeamService()
    
    # 建立測試團隊
    team = service.create_team("U_TEST_INFO_001", "測試團隊資訊")
    team_id = team.team_id
    
    # 查詢團隊資訊
    retrieved_team = service.get_team_info(team_id)
    
    # 驗證
    assert retrieved_team is not None
    assert retrieved_team.team_id == team_id
    assert retrieved_team.team_name == "測試團隊資訊"
    assert retrieved_team.leader_uid == "U_TEST_INFO_001"
    assert retrieved_team.total_points == 0
    assert retrieved_team.member_count == 1
    assert isinstance(retrieved_team.created_at, datetime)
    assert retrieved_team.completed_quests == []
    
    print(f"✅ 成功取得團隊資訊: {retrieved_team.team_name}")


def test_get_team_info_not_found():
    """測試查詢不存在的團隊"""
    service = TeamService()
    
    # 查詢不存在的團隊
    result = service.get_team_info("non-existent-team-id")
    
    # 驗證
    assert result is None
    
    print("✅ 正確處理不存在的團隊")


def test_get_team_members_single_member():
    """測試取得團隊成員清單（僅隊長）"""
    service = TeamService()
    
    # 建立測試團隊
    team = service.create_team("U_TEST_MEMBERS_001", "測試成員清單")
    team_id = team.team_id
    
    # 查詢成員清單
    members = service.get_team_members(team_id)
    
    # 驗證
    assert len(members) == 1
    assert members[0].line_uid == "U_TEST_MEMBERS_001"
    assert members[0].team_id == team_id
    assert members[0].contribution_points == 0
    assert members[0].report_count == 0
    assert members[0].is_leader is True
    assert isinstance(members[0].joined_at, datetime)
    
    print(f"✅ 成功取得成員清單: {len(members)} 位成員")


def test_get_team_members_multiple_members():
    """測試取得團隊成員清單（多位成員）"""
    service = TeamService()
    
    # 建立測試團隊
    team = service.create_team("U_TEST_MULTI_001", "測試多位成員")
    team_id = team.team_id
    
    # 產生邀請連結
    invite_url = service.invite_member(team_id, "U_TEST_MULTI_001")
    signature = invite_url.split("signature=")[1]
    
    # 加入多位成員
    service.join_team(team_id, "U_TEST_MULTI_002", signature)
    service.join_team(team_id, "U_TEST_MULTI_003", signature)
    
    # 查詢成員清單
    members = service.get_team_members(team_id)
    
    # 驗證
    assert len(members) == 3
    
    # 驗證成員 UID
    member_uids = [m.line_uid for m in members]
    assert "U_TEST_MULTI_001" in member_uids
    assert "U_TEST_MULTI_002" in member_uids
    assert "U_TEST_MULTI_003" in member_uids
    
    # 驗證隊長標記
    leaders = [m for m in members if m.is_leader]
    assert len(leaders) == 1
    assert leaders[0].line_uid == "U_TEST_MULTI_001"
    
    print(f"✅ 成功取得多位成員清單: {len(members)} 位成員")


def test_get_team_members_empty_team():
    """測試查詢不存在團隊的成員清單"""
    service = TeamService()
    
    # 查詢不存在的團隊
    members = service.get_team_members("non-existent-team-id")
    
    # 驗證
    assert members == []
    
    print("✅ 正確處理不存在團隊的成員查詢")


def test_get_team_members_sorted_by_contribution():
    """測試成員清單依 contribution_points 降序排序"""
    service = TeamService()
    
    # 建立測試團隊
    team = service.create_team("U_TEST_SORT_001", "測試排序")
    team_id = team.team_id
    
    # 產生邀請連結
    invite_url = service.invite_member(team_id, "U_TEST_SORT_001")
    signature = invite_url.split("signature=")[1]
    
    # 加入成員
    service.join_team(team_id, "U_TEST_SORT_002", signature)
    service.join_team(team_id, "U_TEST_SORT_003", signature)
    
    # 手動更新成員積分（模擬通報）
    from decimal import Decimal
    service.team_members_table.update_item(
        Key={'member_id': f"{team_id}#U_TEST_SORT_001"},
        UpdateExpression='SET contribution_points = :points',
        ExpressionAttributeValues={':points': Decimal('100')}
    )
    service.team_members_table.update_item(
        Key={'member_id': f"{team_id}#U_TEST_SORT_002"},
        UpdateExpression='SET contribution_points = :points',
        ExpressionAttributeValues={':points': Decimal('250')}
    )
    service.team_members_table.update_item(
        Key={'member_id': f"{team_id}#U_TEST_SORT_003"},
        UpdateExpression='SET contribution_points = :points',
        ExpressionAttributeValues={':points': Decimal('150')}
    )
    
    # 查詢成員清單
    members = service.get_team_members(team_id)
    
    # 驗證排序（降序）
    assert len(members) == 3
    assert members[0].line_uid == "U_TEST_SORT_002"  # 250 分
    assert members[0].contribution_points == 250
    assert members[1].line_uid == "U_TEST_SORT_003"  # 150 分
    assert members[1].contribution_points == 150
    assert members[2].line_uid == "U_TEST_SORT_001"  # 100 分
    assert members[2].contribution_points == 100
    
    print("✅ 成員清單正確依 contribution_points 降序排序")


if __name__ == "__main__":
    print("開始測試團隊資訊查詢功能...\n")
    
    try:
        test_get_team_info_success()
        test_get_team_info_not_found()
        test_get_team_members_single_member()
        test_get_team_members_multiple_members()
        test_get_team_members_empty_team()
        test_get_team_members_sorted_by_contribution()
        
        print("\n" + "="*50)
        print("✅ 所有測試通過！Task 3.7 實作完成")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        raise
