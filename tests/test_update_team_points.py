# test_update_team_points.py
"""
測試 PointsCalculator.update_team_points() 方法
"""
import pytest
from points_calculator import PointsCalculator
from database import dynamodb, create_team_tables_if_not_exist
from datetime import datetime
import uuid


@pytest.fixture(scope="module")
def setup_tables():
    """確保測試資料表存在"""
    create_team_tables_if_not_exist()
    yield
    # 清理測試資料（可選）


@pytest.fixture
def calculator():
    """建立 PointsCalculator 實例"""
    return PointsCalculator()


@pytest.fixture
def test_team():
    """建立測試團隊"""
    team_id = str(uuid.uuid4())
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    # 建立團隊
    teams_table = dynamodb.Table('Teams')
    teams_table.put_item(
        Item={
            'team_id': team_id,
            'team_name': '測試團隊',
            'leader_uid': leader_uid,
            'total_points': 0,
            'member_count': 1,
            'created_at': datetime.now().isoformat(),
            'completed_quests': []
        }
    )
    
    # 建立團隊成員
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team_id}#{leader_uid}"
    team_members_table.put_item(
        Item={
            'member_id': member_id,
            'team_id': team_id,
            'line_uid': leader_uid,
            'contribution_points': 0,
            'report_count': 0,
            'joined_at': datetime.now().isoformat(),
            'is_leader': True
        }
    )
    
    yield {'team_id': team_id, 'leader_uid': leader_uid}
    
    # 清理測試資料
    try:
        teams_table.delete_item(Key={'team_id': team_id})
        team_members_table.delete_item(Key={'member_id': member_id})
    except:
        pass


def test_first_report_awards_points(setup_tables, calculator, test_team):
    """測試首次通報應該獲得積分"""
    team_id = test_team['team_id']
    member_uid = test_team['leader_uid']
    url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/fake"
    risk_score = 7
    
    result = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="測試詐騙"
    )
    
    # 驗證結果
    assert result['success'] is True
    assert result['points_earned'] == 7
    assert result['is_duplicate'] is False
    assert result['multiplier_applied'] is False
    assert 'report_id' in result
    
    # 驗證團隊積分已更新
    teams_table = dynamodb.Table('Teams')
    team = teams_table.get_item(Key={'team_id': team_id})['Item']
    assert team['total_points'] == 7
    
    # 驗證成員積分已更新
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team_id}#{member_uid}"
    member = team_members_table.get_item(Key={'member_id': member_id})['Item']
    assert member['contribution_points'] == 7
    assert member['report_count'] == 1
    
    # 驗證通報記錄已寫入
    scam_reports_table = dynamodb.Table('ScamReports')
    report = scam_reports_table.get_item(Key={'report_id': result['report_id']})['Item']
    assert report['url'] == url
    assert report['risk_score'] == risk_score
    assert report['team_id'] == team_id
    assert report['reporter_uid'] == member_uid


def test_duplicate_report_no_points(setup_tables, calculator, test_team):
    """測試重複通報不應該獲得積分"""
    team_id = test_team['team_id']
    member_uid = test_team['leader_uid']
    url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/duplicate"
    risk_score = 8
    
    # 第一次通報
    result1 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="測試詐騙"
    )
    assert result1['success'] is True
    assert result1['points_earned'] == 8
    
    # 第二次通報（重複）
    result2 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="測試詐騙"
    )
    assert result2['success'] is False
    assert result2['points_earned'] == 0
    assert result2['is_duplicate'] is True
    assert '此 URL 已被通報' in result2['message']


def test_high_risk_multiplier(setup_tables, calculator, test_team):
    """測試極高風險通報應該獲得 2x 積分"""
    team_id = test_team['team_id']
    member_uid = test_team['leader_uid']
    url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/high-risk"
    risk_score = 9
    
    result = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="高風險詐騙"
    )
    
    # 驗證結果
    assert result['success'] is True
    assert result['points_earned'] == 18  # 9 * 2
    assert result['multiplier_applied'] is True
    assert '極高風險 2x 獎勵' in result['message']
    
    # 驗證通報記錄
    scam_reports_table = dynamodb.Table('ScamReports')
    report = scam_reports_table.get_item(Key={'report_id': result['report_id']})['Item']
    assert report['multiplier_applied'] is True
    assert report['points_earned'] == 18


def test_url_normalization_in_duplicate_check(setup_tables, calculator, test_team):
    """測試 URL 標準化在重複檢測中的作用"""
    team_id = test_team['team_id']
    member_uid = test_team['leader_uid']
    base_url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/path"
    
    # 第一次通報（帶 query parameters）
    url1 = f"{base_url}?ref=123&utm_source=test"
    result1 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url1,
        risk_score=6,
        category="測試詐騙"
    )
    assert result1['success'] is True
    assert result1['points_earned'] == 6
    
    # 第二次通報（不同的 query parameters，但標準化後相同）
    url2 = f"{base_url}?different=456"
    result2 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url2,
        risk_score=7,
        category="測試詐騙"
    )
    assert result2['success'] is False
    assert result2['is_duplicate'] is True
    
    # 第三次通報（帶 trailing slash）
    url3 = f"{base_url}/"
    result3 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url3,
        risk_score=8,
        category="測試詐騙"
    )
    assert result3['success'] is False
    assert result3['is_duplicate'] is True


def test_atomic_counter_updates(setup_tables, calculator, test_team):
    """測試原子性計數器更新（多次通報累積積分）"""
    team_id = test_team['team_id']
    member_uid = test_team['leader_uid']
    
    # 進行 3 次不同的通報
    urls = [
        f"https://scam-test-{uuid.uuid4().hex[:8]}.com/report1",
        f"https://scam-test-{uuid.uuid4().hex[:8]}.com/report2",
        f"https://scam-test-{uuid.uuid4().hex[:8]}.com/report3"
    ]
    risk_scores = [5, 7, 9]
    expected_points = [5, 7, 18]  # 第三個是 9*2
    
    total_expected = sum(expected_points)
    
    for url, risk_score in zip(urls, risk_scores):
        result = calculator.update_team_points(
            team_id=team_id,
            member_uid=member_uid,
            url=url,
            risk_score=risk_score,
            category="測試詐騙"
        )
        assert result['success'] is True
    
    # 驗證團隊總積分
    teams_table = dynamodb.Table('Teams')
    team = teams_table.get_item(Key={'team_id': team_id})['Item']
    assert team['total_points'] == total_expected
    
    # 驗證成員貢獻積分
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team_id}#{member_uid}"
    member = team_members_table.get_item(Key={'member_id': member_id})['Item']
    assert member['contribution_points'] == total_expected
    assert member['report_count'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
