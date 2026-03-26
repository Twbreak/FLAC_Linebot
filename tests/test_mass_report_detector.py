"""
測試 MassReportDetector 類別
"""

import pytest
from datetime import datetime
from mass_report_detector import MassReportDetector
from database import dynamodb, create_team_tables_if_not_exist
import uuid


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
def cleanup_test_data():
    """測試後清理資料"""
    test_report_ids = []
    yield test_report_ids
    
    # 清理 ScamReports 表
    scam_reports_table = dynamodb.Table('ScamReports')
    for report_id in test_report_ids:
        try:
            scam_reports_table.delete_item(Key={'report_id': report_id})
        except Exception as e:
            print(f"清理失敗: {e}")


def test_check_report_threshold_below_threshold(setup_tables, detector, cleanup_test_data):
    """測試通報次數低於閾值"""
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://test-scam-{uuid.uuid4()}.com"
    
    # 建立 5 筆通報（低於閾值 10）
    for i in range(5):
        report_id = f"test-user-{i}#{datetime.now().isoformat()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://test-scam.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat()
        })
        cleanup_test_data.append(report_id)
    
    # 檢查是否達到閾值
    result = detector.check_report_threshold(normalized_url)
    
    # 驗證：應該返回 False（未達閾值）
    assert result is False


def test_check_report_threshold_at_threshold(setup_tables, detector, cleanup_test_data):
    """測試通報次數剛好達到閾值"""
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://test-scam-{uuid.uuid4()}.com"
    
    # 建立 10 筆通報（剛好達到閾值）
    for i in range(10):
        report_id = f"test-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://test-scam.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat()
        })
        cleanup_test_data.append(report_id)
    
    # 檢查是否達到閾值
    result = detector.check_report_threshold(normalized_url)
    
    # 驗證：應該返回 True（達到閾值）
    assert result is True


def test_check_report_threshold_above_threshold(setup_tables, detector, cleanup_test_data):
    """測試通報次數超過閾值"""
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://test-scam-{uuid.uuid4()}.com"
    
    # 建立 15 筆通報（超過閾值）
    for i in range(15):
        report_id = f"test-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://test-scam.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat()
        })
        cleanup_test_data.append(report_id)
    
    # 檢查是否達到閾值
    result = detector.check_report_threshold(normalized_url)
    
    # 驗證：應該返回 True（超過閾值）
    assert result is True


def test_get_original_message(setup_tables, detector, cleanup_test_data):
    """測試提取原始訊息內容"""
    import time
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://test-scam-{uuid.uuid4()}.com"
    original_url = "http://test-scam.com/fake-investment?ref=123"
    
    # 建立一筆通報
    report_id = f"test-user#{datetime.now().isoformat()}-{uuid.uuid4()}"
    scam_reports_table.put_item(Item={
        'report_id': report_id,
        'url': original_url,
        'normalized_url': normalized_url,
        'reporter_uid': 'U0123456789',
        'risk_score': 9,
        'category': 'investment_scam',
        'points_earned': 10,
        'reported_at': datetime.now().isoformat()
    })
    cleanup_test_data.append(report_id)
    
    # 等待 DynamoDB GSI 更新（eventual consistency）
    time.sleep(1)
    
    # 提取原始訊息
    result = detector.get_original_message(normalized_url)
    
    # 驗證：應該返回原始 URL
    assert result == original_url


def test_get_original_message_not_found(setup_tables, detector):
    """測試提取不存在的 URL 的原始訊息"""
    normalized_url = f"http://nonexistent-{uuid.uuid4()}.com"
    
    # 提取原始訊息
    result = detector.get_original_message(normalized_url)
    
    # 驗證：應該返回 None
    assert result is None


def test_mark_as_mass_reported(setup_tables, detector, cleanup_test_data):
    """測試標記 URL 為大量通報狀態"""
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://test-scam-{uuid.uuid4()}.com"
    alert_id = str(uuid.uuid4())
    
    # 建立 3 筆通報
    report_ids = []
    for i in range(3):
        report_id = f"test-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://test-scam.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat(),
            'is_mass_reported': False
        })
        report_ids.append(report_id)
        cleanup_test_data.append(report_id)
    
    # 標記為大量通報
    result = detector.mark_as_mass_reported(normalized_url, alert_id)
    
    # 驗證：應該返回 True
    assert result is True
    
    # 驗證：所有通報記錄都已標記
    for report_id in report_ids:
        report = scam_reports_table.get_item(Key={'report_id': report_id})['Item']
        assert report['is_mass_reported'] is True
        assert report['mass_report_alert_id'] == alert_id


def test_mark_as_mass_reported_duplicate_prevention(setup_tables, detector, cleanup_test_data):
    """測試重複標記防護：當警示記錄已存在時應返回 False"""
    import time
    from database import create_mass_report_alerts_table
    
    # 確保 MassReportAlerts 表存在
    create_mass_report_alerts_table()
    
    scam_reports_table = dynamodb.Table('ScamReports')
    mass_report_alerts_table = dynamodb.Table('MassReportAlerts')
    normalized_url = f"http://test-scam-{uuid.uuid4()}.com"
    alert_id_1 = str(uuid.uuid4())
    alert_id_2 = str(uuid.uuid4())
    
    # 建立 3 筆通報
    report_ids = []
    for i in range(3):
        report_id = f"test-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://test-scam.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat(),
            'is_mass_reported': False
        })
        report_ids.append(report_id)
        cleanup_test_data.append(report_id)
    
    # 建立一個已存在的警示記錄
    mass_report_alerts_table.put_item(Item={
        'alert_id': alert_id_1,
        'normalized_url': normalized_url,
        'report_count': 10,
        'alert_summary': 'Test alert',
        'alert_warning': 'Test warning',
        'notified_user_count': 0,
        'created_at': datetime.now().isoformat(),
        'status': 'completed'
    })
    
    # 等待 GSI 更新
    time.sleep(1)
    
    # 嘗試再次標記（應該失敗）
    result = detector.mark_as_mass_reported(normalized_url, alert_id_2)
    
    # 驗證：應該返回 False（因為警示已存在）
    assert result is False
    
    # 驗證：通報記錄不應該被更新為新的 alert_id
    for report_id in report_ids:
        report = scam_reports_table.get_item(Key={'report_id': report_id})['Item']
        # 記錄應該保持原狀（未被標記）
        assert report.get('is_mass_reported', False) is False
    
    # 清理警示記錄
    try:
        mass_report_alerts_table.delete_item(Key={'alert_id': alert_id_1})
    except Exception as e:
        print(f"清理警示記錄失敗: {e}")
