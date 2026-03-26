"""測試重複檢測功能"""
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
    # 清理測試資料
    cleanup_test_data()


def cleanup_test_data():
    """清理測試資料"""
    try:
        scam_reports_table = dynamodb.Table('ScamReports')
        # 掃描所有測試資料並刪除
        response = scam_reports_table.scan()
        for item in response.get('Items', []):
            if item.get('report_id', '').startswith('TEST_'):
                scam_reports_table.delete_item(Key={'report_id': item['report_id']})
    except Exception as e:
        print(f"清理測試資料時發生錯誤: {e}")


def test_check_duplicate_not_exists(setup_tables):
    """測試檢查不存在的 URL"""
    calc = PointsCalculator()
    
    # 使用唯一的測試 URL
    test_url = f"https://test-unique-{uuid.uuid4()}.com/path"
    normalized_url = calc.normalize_url(test_url)
    
    # 檢查重複（應該不存在）
    is_duplicate = calc.check_duplicate(normalized_url)
    
    assert is_duplicate == False, "新 URL 不應該被標記為重複"


def test_check_duplicate_exists(setup_tables):
    """測試檢查已存在的 URL"""
    calc = PointsCalculator()
    scam_reports_table = dynamodb.Table('ScamReports')
    
    # 建立測試 URL
    test_url = f"https://test-duplicate-{uuid.uuid4()}.com/path"
    normalized_url = calc.normalize_url(test_url)
    
    # 先寫入一筆通報記錄
    report_id = f"TEST_{uuid.uuid4()}"
    scam_reports_table.put_item(
        Item={
            'report_id': report_id,
            'url': test_url,
            'normalized_url': normalized_url,
            'reporter_uid': 'U_TEST_USER',
            'team_id': 'T_TEST_TEAM',
            'risk_score': 8,
            'category': '測試詐騙',
            'multiplier_applied': False,
            'points_earned': 8,
            'reported_at': datetime.now().isoformat()
        }
    )
    
    # 檢查重複（應該存在）
    is_duplicate = calc.check_duplicate(normalized_url)
    
    assert is_duplicate == True, "已通報的 URL 應該被標記為重複"
    
    # 清理測試資料
    scam_reports_table.delete_item(Key={'report_id': report_id})


def test_check_duplicate_with_different_query_params(setup_tables):
    """測試不同 query parameters 的 URL 應該被視為相同"""
    calc = PointsCalculator()
    scam_reports_table = dynamodb.Table('ScamReports')
    
    # 建立測試 URL（含 query parameters）
    base_url = f"https://test-query-{uuid.uuid4()}.com/path"
    url_with_query1 = f"{base_url}?ref=123"
    url_with_query2 = f"{base_url}?ref=456&utm_source=test"
    
    # 標準化後應該相同
    normalized_url = calc.normalize_url(url_with_query1)
    
    # 先寫入第一個 URL 的通報記錄
    report_id = f"TEST_{uuid.uuid4()}"
    scam_reports_table.put_item(
        Item={
            'report_id': report_id,
            'url': url_with_query1,
            'normalized_url': normalized_url,
            'reporter_uid': 'U_TEST_USER',
            'team_id': 'T_TEST_TEAM',
            'risk_score': 7,
            'category': '測試詐騙',
            'multiplier_applied': False,
            'points_earned': 7,
            'reported_at': datetime.now().isoformat()
        }
    )
    
    # 檢查第二個 URL（不同 query params）是否被視為重複
    normalized_url2 = calc.normalize_url(url_with_query2)
    is_duplicate = calc.check_duplicate(normalized_url2)
    
    assert normalized_url == normalized_url2, "不同 query parameters 應該標準化為相同 URL"
    assert is_duplicate == True, "相同基礎 URL（不同 query params）應該被視為重複"
    
    # 清理測試資料
    scam_reports_table.delete_item(Key={'report_id': report_id})


def test_check_duplicate_case_insensitive(setup_tables):
    """測試大小寫不敏感的重複檢測"""
    calc = PointsCalculator()
    scam_reports_table = dynamodb.Table('ScamReports')
    
    # 建立測試 URL（大寫）
    test_url_upper = f"https://TEST-CASE-{uuid.uuid4()}.COM/Path"
    test_url_lower = test_url_upper.lower()
    
    normalized_url = calc.normalize_url(test_url_upper)
    
    # 先寫入大寫版本的通報記錄
    report_id = f"TEST_{uuid.uuid4()}"
    scam_reports_table.put_item(
        Item={
            'report_id': report_id,
            'url': test_url_upper,
            'normalized_url': normalized_url,
            'reporter_uid': 'U_TEST_USER',
            'team_id': 'T_TEST_TEAM',
            'risk_score': 6,
            'category': '測試詐騙',
            'multiplier_applied': False,
            'points_earned': 6,
            'reported_at': datetime.now().isoformat()
        }
    )
    
    # 檢查小寫版本是否被視為重複
    normalized_url_lower = calc.normalize_url(test_url_lower)
    is_duplicate = calc.check_duplicate(normalized_url_lower)
    
    assert normalized_url == normalized_url_lower, "大小寫不同應該標準化為相同 URL"
    assert is_duplicate == True, "大小寫不同的相同 URL 應該被視為重複"
    
    # 清理測試資料
    scam_reports_table.delete_item(Key={'report_id': report_id})


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])
