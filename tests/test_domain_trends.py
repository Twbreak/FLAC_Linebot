"""
測試詐騙網域趨勢 API

測試項目：
1. 測試網域統計功能
2. 測試網域排序（依通報次數降序）
3. 測試平均風險評分計算
4. 測試 www. 前綴移除
5. 測試前 20 名限制
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import dynamodb
from datetime import datetime
import uuid

client = TestClient(app)


@pytest.fixture
def reports_table():
    """取得 ScamReports 表"""
    return dynamodb.Table('ScamReports')


@pytest.fixture
def cleanup_reports(reports_table):
    """測試後清理 ScamReports 表"""
    report_ids = []
    yield report_ids
    
    # 清理測試資料
    for report_id in report_ids:
        try:
            reports_table.delete_item(Key={'report_id': report_id})
        except Exception as e:
            print(f"清理測試資料失敗: {str(e)}")


def test_domain_trends_basic(cleanup_reports, reports_table):
    """測試基本網域統計功能"""
    # 建立測試通報資料
    test_reports = [
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://scam-site.com/page1',
            'normalized_url': 'https://scam-site.com/page1',
            'reporter_uid': 'U123',
            'risk_score': 9,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://scam-site.com/page2',
            'normalized_url': 'https://scam-site.com/page2',
            'reporter_uid': 'U456',
            'risk_score': 10,
            'category': 'phishing',
            'points_earned': 20,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://another-scam.com/test',
            'normalized_url': 'https://another-scam.com/test',
            'reporter_uid': 'U789',
            'risk_score': 8,
            'category': 'fraud',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        }
    ]
    
    # 寫入測試資料
    for report in test_reports:
        reports_table.put_item(Item=report)
        cleanup_reports.append(report['report_id'])
    
    # 呼叫 API
    response = client.get("/api/trends/domains")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    assert 'domains' in data
    assert len(data['domains']) >= 2
    
    # 驗證網域統計
    domains = {d['domain']: d for d in data['domains']}
    
    # scam-site.com 應該有 2 則通報
    assert 'scam-site.com' in domains
    assert domains['scam-site.com']['report_count'] >= 2
    assert domains['scam-site.com']['avg_risk_score'] == 9.5  # (9+10)/2
    
    # another-scam.com 應該有 1 則通報
    assert 'another-scam.com' in domains
    assert domains['another-scam.com']['report_count'] >= 1
    assert domains['another-scam.com']['avg_risk_score'] == 8.0


def test_domain_trends_ordering(cleanup_reports, reports_table):
    """測試網域依通報次數降序排序"""
    domain_suffix = uuid.uuid4().hex[:8]
    domain_a = f'domain-a-{domain_suffix}.com'
    domain_b = f'domain-b-{domain_suffix}.com'
    domain_c = f'domain-c-{domain_suffix}.com'

    # 建立測試通報資料，使用較大的通報量避免被共享資料擠出前 10 名
    test_reports = []
    
    # domain-a: 30 則通報
    for i in range(30):
        test_reports.append({
            'report_id': str(uuid.uuid4()),
            'url': f'https://{domain_a}/page{i}',
            'normalized_url': f'https://{domain_a}/page{i}',
            'reporter_uid': f'U{i}',
            'risk_score': 9,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        })
    
    # domain-b: 20 則通報
    for i in range(20):
        test_reports.append({
            'report_id': str(uuid.uuid4()),
            'url': f'https://{domain_b}/page{i}',
            'normalized_url': f'https://{domain_b}/page{i}',
            'reporter_uid': f'U{i+10}',
            'risk_score': 8,
            'category': 'fraud',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        })
    
    # domain-c: 10 則通報
    for i in range(10):
        test_reports.append({
            'report_id': str(uuid.uuid4()),
            'url': f'https://{domain_c}/page{i}',
            'normalized_url': f'https://{domain_c}/page{i}',
            'reporter_uid': f'U{i+40}',
            'risk_score': 7,
            'category': 'scam',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        })
    
    # 寫入測試資料
    for report in test_reports:
        reports_table.put_item(Item=report)
        cleanup_reports.append(report['report_id'])
    
    # 呼叫 API
    response = client.get("/api/trends/domains")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    # 找出我們的測試網域
    test_domains = [d for d in data['domains'] if d['domain'] in [domain_a, domain_b, domain_c]]
    
    # 驗證排序（通報次數應該遞減）
    assert len(test_domains) == 3
    assert test_domains[0]['domain'] == domain_a
    assert test_domains[0]['report_count'] == 30
    assert test_domains[1]['domain'] == domain_b
    assert test_domains[1]['report_count'] == 20
    assert test_domains[2]['domain'] == domain_c
    assert test_domains[2]['report_count'] == 10


def test_domain_trends_www_removal(cleanup_reports, reports_table):
    """測試 www. 前綴移除"""
    # 建立測試通報資料（有些有 www.，有些沒有）
    test_reports = [
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://www.example-scam.com/page1',
            'normalized_url': 'https://www.example-scam.com/page1',
            'reporter_uid': 'U123',
            'risk_score': 9,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://example-scam.com/page2',
            'normalized_url': 'https://example-scam.com/page2',
            'reporter_uid': 'U456',
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        }
    ]
    
    # 寫入測試資料
    for report in test_reports:
        reports_table.put_item(Item=report)
        cleanup_reports.append(report['report_id'])
    
    # 呼叫 API
    response = client.get("/api/trends/domains")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    # 驗證 www. 前綴被移除，兩則通報合併為同一個網域
    domains = {d['domain']: d for d in data['domains']}
    assert 'example-scam.com' in domains
    assert domains['example-scam.com']['report_count'] >= 2
    assert domains['example-scam.com']['avg_risk_score'] == 8.5  # (9+8)/2


def test_domain_trends_avg_risk_calculation(cleanup_reports, reports_table):
    """測試平均風險評分計算"""
    # 建立測試通報資料
    test_reports = [
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://test-domain.com/page1',
            'normalized_url': 'https://test-domain.com/page1',
            'reporter_uid': 'U123',
            'risk_score': 10,
            'category': 'phishing',
            'points_earned': 20,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://test-domain.com/page2',
            'normalized_url': 'https://test-domain.com/page2',
            'reporter_uid': 'U456',
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://test-domain.com/page3',
            'normalized_url': 'https://test-domain.com/page3',
            'reporter_uid': 'U789',
            'risk_score': 9,
            'category': 'fraud',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        }
    ]
    
    # 寫入測試資料
    for report in test_reports:
        reports_table.put_item(Item=report)
        cleanup_reports.append(report['report_id'])
    
    # 呼叫 API
    response = client.get("/api/trends/domains")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    # 驗證平均風險評分
    domains = {d['domain']: d for d in data['domains']}
    assert 'test-domain.com' in domains
    assert domains['test-domain.com']['report_count'] >= 3
    assert domains['test-domain.com']['avg_risk_score'] == 9.0  # (10+8+9)/3


def test_domain_trends_top_20_limit(cleanup_reports, reports_table):
    """測試前 20 名限制"""
    # 建立 25 個不同網域的測試通報資料
    test_reports = []
    
    for i in range(25):
        test_reports.append({
            'report_id': str(uuid.uuid4()),
            'url': f'https://domain-{i}.com/page',
            'normalized_url': f'https://domain-{i}.com/page',
            'reporter_uid': f'U{i}',
            'risk_score': 9,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        })
    
    # 寫入測試資料
    for report in test_reports:
        reports_table.put_item(Item=report)
        cleanup_reports.append(report['report_id'])
    
    # 呼叫 API
    response = client.get("/api/trends/domains")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    
    # 驗證最多回傳 20 個網域
    assert len(data['domains']) <= 20
    
    # 驗證每個網域都有 rank 欄位
    for domain in data['domains']:
        assert 'rank' in domain
        assert 1 <= domain['rank'] <= 20


def test_domain_trends_empty_database():
    """測試空資料庫的情況"""
    # 呼叫 API（不新增任何測試資料）
    response = client.get("/api/trends/domains")
    
    # 驗證回應
    assert response.status_code == 200
    data = response.json()
    assert 'domains' in data
    # 可能有其他測試留下的資料，所以只檢查格式正確
    assert isinstance(data['domains'], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
