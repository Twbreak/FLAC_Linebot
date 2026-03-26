"""
示範 MassReportDetector 的使用方式

此示範展示如何使用大量通報偵測器來監控訊息通報次數。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mass_report_detector import MassReportDetector
from database import create_team_tables_if_not_exist, dynamodb
from datetime import datetime
import uuid


def main():
    print("=" * 60)
    print("🔍 大量通報偵測器示範")
    print("=" * 60)
    
    # 確保資料表存在
    print("\n1. 確保資料表存在...")
    create_team_tables_if_not_exist()
    print("✅ 資料表檢查完成")
    
    # 建立 MassReportDetector 實例（閾值設為 3 以便示範）
    print("\n2. 建立 MassReportDetector 實例（閾值=3）...")
    detector = MassReportDetector(threshold=3)
    print("✅ 偵測器建立完成")
    
    # 準備測試資料
    normalized_url = f"http://demo-scam-{uuid.uuid4()}.com"
    scam_reports_table = dynamodb.Table('ScamReports')
    
    # 示範 1: 檢查通報次數（未達閾值）
    print(f"\n3. 示範 1: 檢查通報次數（0 筆通報）")
    result = detector.check_report_threshold(normalized_url)
    print(f"   結果: {result}")
    print(f"   ✅ 預期為 False（未達閾值）")
    
    # 建立 2 筆通報
    print(f"\n4. 建立 2 筆通報...")
    report_ids = []
    for i in range(2):
        report_id = f"demo-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://demo-scam.com/fake?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat(),
            'is_mass_reported': False
        })
        report_ids.append(report_id)
    print(f"   ✅ 已建立 2 筆通報")
    
    # 示範 2: 檢查通報次數（仍未達閾值）
    print(f"\n5. 示範 2: 檢查通報次數（2 筆通報）")
    result = detector.check_report_threshold(normalized_url)
    print(f"   結果: {result}")
    print(f"   ✅ 預期為 False（未達閾值 3）")
    
    # 建立第 3 筆通報
    print(f"\n6. 建立第 3 筆通報...")
    report_id = f"demo-user-3#{datetime.now().isoformat()}-{uuid.uuid4()}"
    scam_reports_table.put_item(Item={
        'report_id': report_id,
        'url': "http://demo-scam.com/fake?param=3",
        'normalized_url': normalized_url,
        'reporter_uid': 'U0000000003',
        'risk_score': 9,
        'category': 'investment_scam',
        'points_earned': 10,
        'reported_at': datetime.now().isoformat(),
        'is_mass_reported': False
    })
    report_ids.append(report_id)
    print(f"   ✅ 已建立第 3 筆通報")
    
    # 示範 3: 檢查通報次數（達到閾值）
    print(f"\n7. 示範 3: 檢查通報次數（3 筆通報）")
    result = detector.check_report_threshold(normalized_url)
    print(f"   結果: {result}")
    print(f"   ✅ 預期為 True（達到閾值 3）")
    
    # 示範 4: 提取原始訊息
    print(f"\n8. 示範 4: 提取原始訊息內容")
    original_message = detector.get_original_message(normalized_url)
    print(f"   原始訊息: {original_message}")
    print(f"   ✅ 成功提取原始 URL")
    
    # 示範 5: 標記為大量通報
    print(f"\n9. 示範 5: 標記為大量通報狀態")
    alert_id = str(uuid.uuid4())
    result = detector.mark_as_mass_reported(normalized_url, alert_id)
    print(f"   結果: {result}")
    print(f"   警示 ID: {alert_id}")
    
    # 驗證標記結果
    print(f"\n10. 驗證標記結果...")
    for i, report_id in enumerate(report_ids):
        report = scam_reports_table.get_item(Key={'report_id': report_id})['Item']
        print(f"   通報 {i+1}: is_mass_reported={report['is_mass_reported']}, "
              f"alert_id={report.get('mass_report_alert_id', 'N/A')}")
    print(f"   ✅ 所有通報已標記為大量通報")
    
    # 清理測試資料
    print(f"\n11. 清理測試資料...")
    for report_id in report_ids:
        scam_reports_table.delete_item(Key={'report_id': report_id})
    print(f"   ✅ 已清理 {len(report_ids)} 筆測試資料")
    
    print("\n" + "=" * 60)
    print("✅ 示範完成！")
    print("=" * 60)
    
    print("\n📚 使用說明:")
    print("   1. MassReportDetector(threshold=10) - 建立偵測器實例")
    print("   2. check_report_threshold(url) - 檢查是否達到閾值")
    print("   3. get_original_message(url) - 提取原始訊息內容")
    print("   4. mark_as_mass_reported(url, alert_id) - 標記為大量通報")


if __name__ == "__main__":
    main()
