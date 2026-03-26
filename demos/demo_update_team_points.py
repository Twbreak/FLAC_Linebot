#!/usr/bin/env python3
# demo_update_team_points.py
"""
手動測試 PointsCalculator.update_team_points() 方法
"""
from points_calculator import PointsCalculator
from database import dynamodb, create_team_tables_if_not_exist
from datetime import datetime
import uuid


def setup_test_team():
    """建立測試團隊"""
    team_id = str(uuid.uuid4())
    leader_uid = f"U{uuid.uuid4().hex[:10]}"
    
    print(f"📝 建立測試團隊...")
    print(f"   Team ID: {team_id}")
    print(f"   Leader UID: {leader_uid}")
    
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
    
    print("✅ 測試團隊建立成功\n")
    return team_id, leader_uid


def test_first_report():
    """測試 1: 首次通報應該獲得積分"""
    print("=" * 60)
    print("測試 1: 首次通報應該獲得積分")
    print("=" * 60)
    
    calculator = PointsCalculator()
    team_id, member_uid = setup_test_team()
    
    url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/fake"
    risk_score = 7
    
    print(f"📊 通報詐騙 URL: {url}")
    print(f"   風險評分: {risk_score}")
    
    result = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="測試詐騙"
    )
    
    print(f"\n結果:")
    print(f"   Success: {result['success']}")
    print(f"   Points Earned: {result['points_earned']}")
    print(f"   Is Duplicate: {result['is_duplicate']}")
    print(f"   Multiplier Applied: {result['multiplier_applied']}")
    print(f"   Message: {result.get('message', 'N/A')}")
    
    # 驗證團隊積分
    teams_table = dynamodb.Table('Teams')
    team = teams_table.get_item(Key={'team_id': team_id})['Item']
    print(f"\n團隊積分: {team['total_points']}")
    
    # 驗證成員積分
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team_id}#{member_uid}"
    member = team_members_table.get_item(Key={'member_id': member_id})['Item']
    print(f"成員貢獻積分: {member['contribution_points']}")
    print(f"成員通報次數: {member['report_count']}")
    
    assert result['success'] is True
    assert result['points_earned'] == 7
    assert team['total_points'] == 7
    assert member['contribution_points'] == 7
    assert member['report_count'] == 1
    
    print("\n✅ 測試 1 通過！\n")


def test_duplicate_report():
    """測試 2: 重複通報不應該獲得積分"""
    print("=" * 60)
    print("測試 2: 重複通報不應該獲得積分")
    print("=" * 60)
    
    calculator = PointsCalculator()
    team_id, member_uid = setup_test_team()
    
    url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/duplicate"
    risk_score = 8
    
    # 第一次通報
    print(f"📊 第一次通報: {url}")
    result1 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="測試詐騙"
    )
    print(f"   結果: Success={result1['success']}, Points={result1['points_earned']}")
    
    # 第二次通報（重複）
    print(f"\n📊 第二次通報（重複）: {url}")
    result2 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="測試詐騙"
    )
    print(f"   結果: Success={result2['success']}, Points={result2['points_earned']}")
    print(f"   Is Duplicate: {result2['is_duplicate']}")
    print(f"   Message: {result2.get('message', 'N/A')}")
    
    assert result1['success'] is True
    assert result1['points_earned'] == 8
    assert result2['success'] is False
    assert result2['points_earned'] == 0
    assert result2['is_duplicate'] is True
    
    print("\n✅ 測試 2 通過！\n")


def test_high_risk_multiplier():
    """測試 3: 極高風險通報應該獲得 2x 積分"""
    print("=" * 60)
    print("測試 3: 極高風險通報應該獲得 2x 積分")
    print("=" * 60)
    
    calculator = PointsCalculator()
    team_id, member_uid = setup_test_team()
    
    url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/high-risk"
    risk_score = 9
    
    print(f"📊 通報高風險詐騙: {url}")
    print(f"   風險評分: {risk_score}")
    
    result = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url,
        risk_score=risk_score,
        category="高風險詐騙"
    )
    
    print(f"\n結果:")
    print(f"   Success: {result['success']}")
    print(f"   Points Earned: {result['points_earned']}")
    print(f"   Multiplier Applied: {result['multiplier_applied']}")
    print(f"   Message: {result.get('message', 'N/A')}")
    
    # 驗證通報記錄
    scam_reports_table = dynamodb.Table('ScamReports')
    report = scam_reports_table.get_item(Key={'report_id': result['report_id']})['Item']
    print(f"\n通報記錄:")
    print(f"   Multiplier Applied: {report['multiplier_applied']}")
    print(f"   Points Earned: {report['points_earned']}")
    
    assert result['success'] is True
    assert result['points_earned'] == 18  # 9 * 2
    assert result['multiplier_applied'] is True
    assert report['multiplier_applied'] is True
    
    print("\n✅ 測試 3 通過！\n")


def test_url_normalization():
    """測試 4: URL 標準化在重複檢測中的作用"""
    print("=" * 60)
    print("測試 4: URL 標準化在重複檢測中的作用")
    print("=" * 60)
    
    calculator = PointsCalculator()
    team_id, member_uid = setup_test_team()
    
    base_url = f"https://scam-test-{uuid.uuid4().hex[:8]}.com/path"
    
    # 第一次通報（帶 query parameters）
    url1 = f"{base_url}?ref=123&utm_source=test"
    print(f"📊 第一次通報: {url1}")
    result1 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url1,
        risk_score=6,
        category="測試詐騙"
    )
    print(f"   結果: Success={result1['success']}, Points={result1['points_earned']}")
    print(f"   Normalized URL: {result1['normalized_url']}")
    
    # 第二次通報（不同的 query parameters）
    url2 = f"{base_url}?different=456"
    print(f"\n📊 第二次通報: {url2}")
    result2 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url2,
        risk_score=7,
        category="測試詐騙"
    )
    print(f"   結果: Success={result2['success']}, Is Duplicate={result2['is_duplicate']}")
    print(f"   Normalized URL: {result2['normalized_url']}")
    
    # 第三次通報（帶 trailing slash）
    url3 = f"{base_url}/"
    print(f"\n📊 第三次通報: {url3}")
    result3 = calculator.update_team_points(
        team_id=team_id,
        member_uid=member_uid,
        url=url3,
        risk_score=8,
        category="測試詐騙"
    )
    print(f"   結果: Success={result3['success']}, Is Duplicate={result3['is_duplicate']}")
    print(f"   Normalized URL: {result3['normalized_url']}")
    
    assert result1['success'] is True
    assert result2['is_duplicate'] is True
    assert result3['is_duplicate'] is True
    assert result1['normalized_url'] == result2['normalized_url'] == result3['normalized_url']
    
    print("\n✅ 測試 4 通過！\n")


def test_atomic_counter():
    """測試 5: 原子性計數器更新（多次通報累積積分）"""
    print("=" * 60)
    print("測試 5: 原子性計數器更新（多次通報累積積分）")
    print("=" * 60)
    
    calculator = PointsCalculator()
    team_id, member_uid = setup_test_team()
    
    # 進行 3 次不同的通報
    urls = [
        f"https://scam-test-{uuid.uuid4().hex[:8]}.com/report1",
        f"https://scam-test-{uuid.uuid4().hex[:8]}.com/report2",
        f"https://scam-test-{uuid.uuid4().hex[:8]}.com/report3"
    ]
    risk_scores = [5, 7, 9]
    expected_points = [5, 7, 18]  # 第三個是 9*2
    
    print(f"📊 進行 3 次通報...")
    for i, (url, risk_score, expected) in enumerate(zip(urls, risk_scores, expected_points), 1):
        print(f"\n   通報 {i}: risk_score={risk_score}")
        result = calculator.update_team_points(
            team_id=team_id,
            member_uid=member_uid,
            url=url,
            risk_score=risk_score,
            category="測試詐騙"
        )
        print(f"   獲得積分: {result['points_earned']} (預期: {expected})")
        assert result['success'] is True
        assert result['points_earned'] == expected
    
    total_expected = sum(expected_points)
    
    # 驗證團隊總積分
    teams_table = dynamodb.Table('Teams')
    team = teams_table.get_item(Key={'team_id': team_id})['Item']
    print(f"\n團隊總積分: {team['total_points']} (預期: {total_expected})")
    
    # 驗證成員貢獻積分
    team_members_table = dynamodb.Table('TeamMembers')
    member_id = f"{team_id}#{member_uid}"
    member = team_members_table.get_item(Key={'member_id': member_id})['Item']
    print(f"成員貢獻積分: {member['contribution_points']} (預期: {total_expected})")
    print(f"成員通報次數: {member['report_count']} (預期: 3)")
    
    assert team['total_points'] == total_expected
    assert member['contribution_points'] == total_expected
    assert member['report_count'] == 3
    
    print("\n✅ 測試 5 通過！\n")


def main():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("開始測試 PointsCalculator.update_team_points()")
    print("=" * 60 + "\n")
    
    # 確保資料表存在
    print("🔧 檢查並建立資料表...")
    create_team_tables_if_not_exist()
    print("✅ 資料表準備完成\n")
    
    try:
        test_first_report()
        test_duplicate_report()
        test_high_risk_multiplier()
        test_url_normalization()
        test_atomic_counter()
        
        print("=" * 60)
        print("🎉 所有測試通過！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        raise


if __name__ == "__main__":
    main()
