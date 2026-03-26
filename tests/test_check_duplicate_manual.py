"""手動測試重複檢測功能"""
from points_calculator import PointsCalculator
from database import dynamodb, create_team_tables_if_not_exist
from datetime import datetime
import uuid


def test_check_duplicate():
    """測試重複檢測功能"""
    print("=" * 60)
    print("測試重複檢測功能")
    print("=" * 60)
    
    # 確保資料表存在
    print("\n1. 確保 ScamReports 資料表存在...")
    create_team_tables_if_not_exist()
    print("✅ 資料表檢查完成")
    
    # 建立 PointsCalculator 實例
    calc = PointsCalculator()
    scam_reports_table = dynamodb.Table('ScamReports')
    
    # 測試 1: 檢查不存在的 URL
    print("\n2. 測試檢查不存在的 URL...")
    test_url_1 = f"https://test-unique-{uuid.uuid4()}.com/path"
    normalized_url_1 = calc.normalize_url(test_url_1)
    is_duplicate_1 = calc.check_duplicate(normalized_url_1)
    print(f"   URL: {test_url_1}")
    print(f"   標準化 URL: {normalized_url_1}")
    print(f"   是否重複: {is_duplicate_1}")
    assert is_duplicate_1 == False, "❌ 新 URL 不應該被標記為重複"
    print("✅ 測試通過：新 URL 正確識別為非重複")
    
    # 測試 2: 寫入一筆記錄後檢查重複
    print("\n3. 測試檢查已存在的 URL...")
    test_url_2 = f"https://test-duplicate-{uuid.uuid4()}.com/path"
    normalized_url_2 = calc.normalize_url(test_url_2)
    report_id_2 = f"TEST_{uuid.uuid4()}"
    
    # 寫入通報記錄
    print(f"   寫入測試記錄: {report_id_2}")
    scam_reports_table.put_item(
        Item={
            'report_id': report_id_2,
            'url': test_url_2,
            'normalized_url': normalized_url_2,
            'reporter_uid': 'U_TEST_USER',
            'team_id': 'T_TEST_TEAM',
            'risk_score': 8,
            'category': '測試詐騙',
            'multiplier_applied': False,
            'points_earned': 8,
            'reported_at': datetime.now().isoformat()
        }
    )
    
    # 檢查重複
    is_duplicate_2 = calc.check_duplicate(normalized_url_2)
    print(f"   URL: {test_url_2}")
    print(f"   標準化 URL: {normalized_url_2}")
    print(f"   是否重複: {is_duplicate_2}")
    assert is_duplicate_2 == True, "❌ 已通報的 URL 應該被標記為重複"
    print("✅ 測試通過：已通報 URL 正確識別為重複")
    
    # 清理測試資料
    print(f"   清理測試記錄: {report_id_2}")
    scam_reports_table.delete_item(Key={'report_id': report_id_2})
    
    # 測試 3: 不同 query parameters 應該被視為相同
    print("\n4. 測試不同 query parameters 的 URL...")
    base_url = f"https://test-query-{uuid.uuid4()}.com/path"
    url_with_query1 = f"{base_url}?ref=123"
    url_with_query2 = f"{base_url}?ref=456&utm_source=test"
    
    normalized_url_3a = calc.normalize_url(url_with_query1)
    normalized_url_3b = calc.normalize_url(url_with_query2)
    
    print(f"   URL 1: {url_with_query1}")
    print(f"   URL 2: {url_with_query2}")
    print(f"   標準化 URL 1: {normalized_url_3a}")
    print(f"   標準化 URL 2: {normalized_url_3b}")
    
    assert normalized_url_3a == normalized_url_3b, "❌ 不同 query parameters 應該標準化為相同 URL"
    print("✅ 測試通過：不同 query parameters 標準化為相同 URL")
    
    # 寫入第一個 URL
    report_id_3 = f"TEST_{uuid.uuid4()}"
    print(f"   寫入測試記錄: {report_id_3}")
    scam_reports_table.put_item(
        Item={
            'report_id': report_id_3,
            'url': url_with_query1,
            'normalized_url': normalized_url_3a,
            'reporter_uid': 'U_TEST_USER',
            'team_id': 'T_TEST_TEAM',
            'risk_score': 7,
            'category': '測試詐騙',
            'multiplier_applied': False,
            'points_earned': 7,
            'reported_at': datetime.now().isoformat()
        }
    )
    
    # 檢查第二個 URL 是否被視為重複
    is_duplicate_3 = calc.check_duplicate(normalized_url_3b)
    print(f"   第二個 URL 是否重複: {is_duplicate_3}")
    assert is_duplicate_3 == True, "❌ 相同基礎 URL（不同 query params）應該被視為重複"
    print("✅ 測試通過：相同基礎 URL（不同 query params）正確識別為重複")
    
    # 清理測試資料
    print(f"   清理測試記錄: {report_id_3}")
    scam_reports_table.delete_item(Key={'report_id': report_id_3})
    
    # 測試 4: 大小寫不敏感
    print("\n5. 測試大小寫不敏感的重複檢測...")
    test_url_upper = f"https://TEST-CASE-{uuid.uuid4()}.COM/Path"
    test_url_lower = test_url_upper.lower()
    
    normalized_url_4a = calc.normalize_url(test_url_upper)
    normalized_url_4b = calc.normalize_url(test_url_lower)
    
    print(f"   URL (大寫): {test_url_upper}")
    print(f"   URL (小寫): {test_url_lower}")
    print(f"   標準化 URL (大寫): {normalized_url_4a}")
    print(f"   標準化 URL (小寫): {normalized_url_4b}")
    
    assert normalized_url_4a == normalized_url_4b, "❌ 大小寫不同應該標準化為相同 URL"
    print("✅ 測試通過：大小寫不同標準化為相同 URL")
    
    # 寫入大寫版本
    report_id_4 = f"TEST_{uuid.uuid4()}"
    print(f"   寫入測試記錄: {report_id_4}")
    scam_reports_table.put_item(
        Item={
            'report_id': report_id_4,
            'url': test_url_upper,
            'normalized_url': normalized_url_4a,
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
    is_duplicate_4 = calc.check_duplicate(normalized_url_4b)
    print(f"   小寫版本是否重複: {is_duplicate_4}")
    assert is_duplicate_4 == True, "❌ 大小寫不同的相同 URL 應該被視為重複"
    print("✅ 測試通過：大小寫不同的相同 URL 正確識別為重複")
    
    # 清理測試資料
    print(f"   清理測試記錄: {report_id_4}")
    scam_reports_table.delete_item(Key={'report_id': report_id_4})
    
    print("\n" + "=" * 60)
    print("✅ 所有測試通過！重複檢測功能運作正常")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_check_duplicate()
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
