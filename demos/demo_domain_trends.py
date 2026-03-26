"""
Demo: 詐騙網域趨勢 API

展示如何使用 GET /api/trends/domains API 查詢詐騙網域統計資訊。

功能：
1. 查詢所有詐騙網域的通報次數
2. 查看平均風險評分
3. 依通報次數排序，顯示前 20 名

使用方式：
    python demos/demo_domain_trends.py
"""

import requests
import json
from datetime import datetime
import uuid

# API 基礎 URL
BASE_URL = "http://localhost:8000"


def create_sample_reports():
    """建立範例通報資料（用於測試）"""
    from points_calculator import PointsCalculator
    
    calculator = PointsCalculator()
    
    # 建立範例通報
    sample_reports = [
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://scam-site-1.com/phishing',
            'normalized_url': 'https://scam-site-1.com/phishing',
            'reporter_uid': 'U123',
            'risk_score': 10,
            'category': 'phishing',
            'points_earned': 20,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://scam-site-1.com/login',
            'normalized_url': 'https://scam-site-1.com/login',
            'reporter_uid': 'U456',
            'risk_score': 9,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://www.scam-site-2.com/fraud',
            'normalized_url': 'https://www.scam-site-2.com/fraud',
            'reporter_uid': 'U789',
            'risk_score': 8,
            'category': 'fraud',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        },
        {
            'report_id': str(uuid.uuid4()),
            'url': 'https://scam-site-3.com/scam',
            'normalized_url': 'https://scam-site-3.com/scam',
            'reporter_uid': 'U111',
            'risk_score': 7,
            'category': 'scam',
            'points_earned': 10,
            'reported_at': datetime.utcnow().isoformat()
        }
    ]
    
    print("📝 建立範例通報資料...")
    for report in sample_reports:
        calculator.reports_table.put_item(Item=report)
        print(f"  ✓ 通報 {report['url']} (風險評分: {report['risk_score']})")
    
    print()
    return [r['report_id'] for r in sample_reports]


def get_domain_trends():
    """查詢詐騙網域趨勢"""
    print("=" * 60)
    print("詐騙網域趨勢查詢 Demo")
    print("=" * 60)
    print()
    
    # 呼叫 API
    print("🔍 查詢詐騙網域趨勢...")
    response = requests.get(f"{BASE_URL}/api/trends/domains")
    
    if response.status_code == 200:
        data = response.json()
        domains = data.get('domains', [])
        
        print(f"✅ 查詢成功！共找到 {len(domains)} 個詐騙網域")
        print()
        
        if domains:
            print("📊 詐騙網域排行榜（依通報次數排序）：")
            print("-" * 60)
            print(f"{'排名':<6} {'網域':<30} {'通報次數':<10} {'平均風險':<10}")
            print("-" * 60)
            
            for domain in domains[:10]:  # 只顯示前 10 名
                rank = domain['rank']
                domain_name = domain['domain']
                report_count = domain['report_count']
                avg_risk = domain['avg_risk_score']
                
                print(f"{rank:<6} {domain_name:<30} {report_count:<10} {avg_risk:<10.1f}")
            
            print("-" * 60)
            print()
            
            # 顯示統計資訊
            total_reports = sum(d['report_count'] for d in domains)
            avg_risk_all = sum(d['avg_risk_score'] * d['report_count'] for d in domains) / total_reports if total_reports > 0 else 0
            
            print("📈 統計資訊：")
            print(f"  • 總通報次數: {total_reports}")
            print(f"  • 平均風險評分: {avg_risk_all:.1f}")
            print(f"  • 最高風險網域: {domains[0]['domain']} (平均風險: {domains[0]['avg_risk_score']})")
            print()
            
        else:
            print("⚠️  目前沒有詐騙通報資料")
            print()
        
        return data
    else:
        print(f"❌ 查詢失敗: {response.status_code}")
        print(f"錯誤訊息: {response.text}")
        return None


def cleanup_sample_reports(report_ids):
    """清理範例通報資料"""
    from points_calculator import PointsCalculator
    
    calculator = PointsCalculator()
    
    print("🧹 清理範例通報資料...")
    for report_id in report_ids:
        try:
            calculator.reports_table.delete_item(Key={'report_id': report_id})
            print(f"  ✓ 刪除通報 {report_id}")
        except Exception as e:
            print(f"  ✗ 刪除失敗: {str(e)}")
    print()


def main():
    """主程式"""
    # 選項 1: 使用現有資料查詢
    print("選擇操作模式：")
    print("1. 使用現有資料查詢")
    print("2. 建立範例資料後查詢（會自動清理）")
    choice = input("請選擇 (1/2): ").strip()
    print()
    
    if choice == "2":
        # 建立範例資料
        report_ids = create_sample_reports()
        
        # 查詢趨勢
        get_domain_trends()
        
        # 清理範例資料
        cleanup_sample_reports(report_ids)
    else:
        # 直接查詢現有資料
        get_domain_trends()
    
    print("=" * 60)
    print("Demo 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
