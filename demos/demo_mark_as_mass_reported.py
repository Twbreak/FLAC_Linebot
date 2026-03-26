"""
示範 mark_as_mass_reported() 方法的重複通知防護功能

此示範展示：
1. 首次標記 URL 為大量通報狀態（成功）
2. 嘗試再次標記相同 URL（失敗，因為警示已存在）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mass_report_detector import MassReportDetector
from database import dynamodb, create_team_tables_if_not_exist, create_mass_report_alerts_table
from datetime import datetime
import uuid
import time

def main():
    print("=" * 60)
    print("示範：mark_as_mass_reported() 重複通知防護")
    print("=" * 60)
    
    # 確保資料表存在
    print("\n📋 步驟 1: 確保資料表存在...")
    create_team_tables_if_not_exist()
    create_mass_report_alerts_table()
    
    # 建立偵測器
    detector = MassReportDetector(threshold=10)
    scam_reports_table = dynamodb.Table('ScamReports')
    mass_report_alerts_table = dynamodb.Table('MassReportAlerts')
    
    # 生成測試資料
    normalized_url = f"http://demo-scam-{uuid.uuid4()}.com"
    alert_id_1 = str(uuid.uuid4())
    alert_id_2 = str(uuid.uuid4())
    
    print(f"\n📝 測試 URL: {normalized_url}")
    print(f"🆔 警示 ID 1: {alert_id_1}")
    print(f"🆔 警示 ID 2: {alert_id_2}")
    
    # 建立測試通報記錄
    print("\n📋 步驟 2: 建立 5 筆測試通報記錄...")
    report_ids = []
    for i in range(5):
        report_id = f"demo-user-{i}#{datetime.now().isoformat()}-{uuid.uuid4()}"
        scam_reports_table.put_item(Item={
            'report_id': report_id,
            'url': f"http://demo-scam.com?param={i}",
            'normalized_url': normalized_url,
            'reporter_uid': f"U{i:010d}",
            'risk_score': 8,
            'category': 'phishing',
            'points_earned': 10,
            'reported_at': datetime.now().isoformat(),
            'is_mass_reported': False
        })
        report_ids.append(report_id)
        print(f"  ✅ 建立通報 {i+1}/5")
    
    # 首次標記為大量通報（應該成功）
    print("\n📋 步驟 3: 首次標記為大量通報...")
    result_1 = detector.mark_as_mass_reported(normalized_url, alert_id_1)
    print(f"  結果: {'✅ 成功' if result_1 else '❌ 失敗'}")
    
    # 驗證通報記錄已更新
    print("\n📋 步驟 4: 驗證通報記錄已更新...")
    for i, report_id in enumerate(report_ids):
        report = scam_reports_table.get_item(Key={'report_id': report_id})['Item']
        is_marked = report.get('is_mass_reported', False)
        linked_alert = report.get('mass_report_alert_id', 'None')
        print(f"  通報 {i+1}: is_mass_reported={is_marked}, alert_id={linked_alert[:8]}...")
    
    # 建立警示記錄（模擬完整流程）
    print("\n📋 步驟 5: 建立警示記錄...")
    mass_report_alerts_table.put_item(Item={
        'alert_id': alert_id_1,
        'normalized_url': normalized_url,
        'report_count': 10,
        'alert_summary': '測試警示摘要',
        'alert_warning': '測試警示訊息',
        'notified_user_count': 0,
        'created_at': datetime.now().isoformat(),
        'status': 'completed'
    })
    print("  ✅ 警示記錄已建立")
    
    # 等待 GSI 更新
    print("\n⏳ 等待 GSI 更新...")
    time.sleep(2)
    
    # 嘗試再次標記（應該失敗，因為警示已存在）
    print("\n📋 步驟 6: 嘗試再次標記相同 URL（應該失敗）...")
    result_2 = detector.mark_as_mass_reported(normalized_url, alert_id_2)
    print(f"  結果: {'✅ 成功' if result_2 else '❌ 失敗（預期行為）'}")
    
    # 驗證通報記錄未被更新為新的 alert_id
    print("\n📋 步驟 7: 驗證通報記錄未被更新...")
    for i, report_id in enumerate(report_ids):
        report = scam_reports_table.get_item(Key={'report_id': report_id})['Item']
        linked_alert = report.get('mass_report_alert_id', 'None')
        is_still_first_alert = linked_alert == alert_id_1
        print(f"  通報 {i+1}: alert_id={linked_alert[:8]}... (仍為第一個警示: {is_still_first_alert})")
    
    # 清理測試資料
    print("\n🧹 清理測試資料...")
    for report_id in report_ids:
        try:
            scam_reports_table.delete_item(Key={'report_id': report_id})
        except Exception as e:
            print(f"  ⚠️ 清理通報失敗: {e}")
    
    try:
        mass_report_alerts_table.delete_item(Key={'alert_id': alert_id_1})
    except Exception as e:
        print(f"  ⚠️ 清理警示失敗: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 示範完成！")
    print("=" * 60)
    print("\n📊 總結：")
    print(f"  • 首次標記: {'成功' if result_1 else '失敗'}")
    print(f"  • 重複標記: {'成功（異常）' if result_2 else '失敗（正常，防止重複通知）'}")
    print("\n💡 重點：")
    print("  mark_as_mass_reported() 方法會先檢查 MassReportAlerts 表")
    print("  如果該 URL 已有警示記錄，則返回 False，避免重複通知")


if __name__ == "__main__":
    main()
