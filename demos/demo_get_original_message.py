"""
Demo: 測試 get_original_message() 方法

此 demo 展示如何使用 MassReportDetector.get_original_message() 方法
從 ScamReports 表中提取原始訊息內容。
"""

import sys
sys.path.insert(0, '.')

from mass_report_detector import MassReportDetector
from database import dynamodb, create_team_tables_if_not_exist
from datetime import datetime
import uuid

def demo_get_original_message():
    """展示 get_original_message() 方法的使用"""
    
    # 確保資料表存在
    create_team_tables_if_not_exist()
    
    # 建立 MassReportDetector 實例
    detector = MassReportDetector(threshold=10)
    
    # 準備測試資料
    scam_reports_table = dynamodb.Table('ScamReports')
    normalized_url = f"http://demo-scam-{uuid.uuid4()}.com"
    original_url = "http://demo-scam.com/fake-investment?ref=abc123&utm_source=line"
    
    print("=" * 60)
    print("Demo: get_original_message() 方法")
    print("=" * 60)
    
    # 建立測試通報記錄
    report_id = f"demo-user#{datetime.now().isoformat()}-{uuid.uuid4()}"
    print(f"\n📝 建立測試通報記錄...")
    print(f"   Report ID: {report_id}")
    print(f"   Original URL: {original_url}")
    print(f"   Normalized URL: {normalized_url}")
    
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
    
    # 等待 GSI 更新（eventual consistency）
    print("\n⏳ 等待 DynamoDB GSI 更新...")
    import time
    time.sleep(1)
    
    # 測試 1: 提取存在的原始訊息
    print(f"\n🔍 測試 1: 提取存在的原始訊息")
    result = detector.get_original_message(normalized_url)
    
    if result:
        print(f"✅ 成功提取原始訊息:")
        print(f"   {result}")
    else:
        print(f"❌ 未找到原始訊息")
    
    # 測試 2: 提取不存在的 URL
    print(f"\n🔍 測試 2: 提取不存在的 URL")
    nonexistent_url = f"http://nonexistent-{uuid.uuid4()}.com"
    result = detector.get_original_message(nonexistent_url)
    
    if result is None:
        print(f"✅ 正確返回 None（URL 不存在）")
    else:
        print(f"❌ 應該返回 None，但返回了: {result}")
    
    # 清理測試資料
    print(f"\n🧹 清理測試資料...")
    try:
        scam_reports_table.delete_item(Key={'report_id': report_id})
        print(f"✅ 清理完成")
    except Exception as e:
        print(f"❌ 清理失敗: {e}")
    
    print("\n" + "=" * 60)
    print("Demo 完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo_get_original_message()
