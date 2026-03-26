"""
Performance test for check_report_threshold() method
Validates: Requirement 1.5 - Query completes within 50ms
"""

import pytest
import time
import uuid
from datetime import datetime
from mass_report_detector import MassReportDetector
from database import dynamodb, create_team_tables_if_not_exist


@pytest.fixture(scope="module")
def setup_tables():
    """確保測試所需的資料表存在"""
    create_team_tables_if_not_exist()
    yield


@pytest.fixture
def detector():
    """建立 MassReportDetector 實例"""
    return MassReportDetector(threshold=10)


@pytest.fixture
def setup_test_data():
    """建立測試資料"""
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://perf-test-{uuid.uuid4()}.com"
    report_ids = []
    
    # 建立 20 筆通報記錄
    for i in range(20):
        report_id = f"perf-test-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://perf-test.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat()
        })
        report_ids.append(report_id)
    
    # 等待 GSI 更新
    time.sleep(2)
    
    yield normalized_url, report_ids
    
    # 清理測試資料
    for report_id in report_ids:
        try:
            scam_reports_table.delete_item(Key={'report_id': report_id})
        except Exception as e:
            print(f"清理失敗: {e}")


def test_check_report_threshold_performance(setup_tables, detector, setup_test_data):
    """測試 check_report_threshold() 查詢效能
    
    驗證：查詢應在 50ms 內完成
    Validates: Requirement 1.5
    """
    normalized_url, _ = setup_test_data
    
    # 執行多次測試以獲得平均值
    execution_times = []
    
    for _ in range(10):
        start_time = time.perf_counter()
        result = detector.check_report_threshold(normalized_url)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        execution_times.append(execution_time_ms)
        
        # 驗證結果正確
        assert result is True  # 20 筆通報 >= 10 閾值
    
    # 計算平均執行時間
    avg_time = sum(execution_times) / len(execution_times)
    max_time = max(execution_times)
    min_time = min(execution_times)
    
    print(f"\n📊 效能測試結果:")
    print(f"   平均執行時間: {avg_time:.2f} ms")
    print(f"   最大執行時間: {max_time:.2f} ms")
    print(f"   最小執行時間: {min_time:.2f} ms")
    
    # 驗證：平均執行時間應小於 50ms
    assert avg_time < 50, f"平均執行時間 {avg_time:.2f}ms 超過 50ms 限制"

    # 驗證：排除首次冷查詢後，後續穩態延遲應小於 50ms
    warmed_execution_times = execution_times[1:]
    warmed_max_time = max(warmed_execution_times)
    assert warmed_max_time < 50, f"穩態最大執行時間 {warmed_max_time:.2f}ms 超過 50ms 限制"
