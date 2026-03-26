"""示範重複檢測功能的使用"""
from points_calculator import PointsCalculator
from database import dynamodb, create_team_tables_if_not_exist
from datetime import datetime
import uuid


def demo_check_duplicate():
    """示範重複檢測功能"""
    print("=" * 70)
    print("重複檢測功能示範")
    print("=" * 70)
    
    # 確保資料表存在
    print("\n📋 步驟 1: 確保 DynamoDB 資料表存在")
    create_team_tables_if_not_exist()
    
    # 建立 PointsCalculator 實例
    calc = PointsCalculator()
    scam_reports_table = dynamodb.Table('ScamReports')
    
    # 示範 1: 檢查新 URL（不存在）
    print("\n" + "=" * 70)
    print("📝 示範 1: 檢查新的 URL（尚未被通報）")
    print("=" * 70)
    
    new_url = "https://scam-example.com/fake-investment?ref=123"
    print(f"原始 URL: {new_url}")
    
    normalized = calc.normalize_url(new_url)
    print(f"標準化 URL: {normalized}")
    
    is_duplicate = calc.check_duplicate(normalized)
    print(f"是否重複: {is_duplicate}")
    print(f"結果: {'❌ 已被通報（重複）' if is_duplicate else '✅ 尚未被通報（可獲得積分）'}")
    
    # 示範 2: 寫入通報記錄
    print("\n" + "=" * 70)
    print("📝 示範 2: 寫入第一筆通報記錄")
    print("=" * 70)
    
    report_id = f"DEMO_{uuid.uuid4()}"
    print(f"通報 ID: {report_id}")
    print(f"通報者: U_ALICE")
    print(f"團隊: TEAM_001")
    print(f"風險評分: 8")
    
    scam_reports_table.put_item(
        Item={
            'report_id': report_id,
            'url': new_url,
            'normalized_url': normalized,
            'reporter_uid': 'U_ALICE',
            'team_id': 'TEAM_001',
            'risk_score': 8,
            'category': '假投資詐騙',
            'multiplier_applied': False,
            'points_earned': 8,
            'reported_at': datetime.now().isoformat()
        }
    )
    print("✅ 通報記錄已寫入 ScamReports 表")
    
    # 示範 3: 再次檢查相同 URL（應該重複）
    print("\n" + "=" * 70)
    print("📝 示範 3: 再次檢查相同的 URL")
    print("=" * 70)
    
    is_duplicate_now = calc.check_duplicate(normalized)
    print(f"原始 URL: {new_url}")
    print(f"標準化 URL: {normalized}")
    print(f"是否重複: {is_duplicate_now}")
    print(f"結果: {'❌ 已被通報（重複）' if is_duplicate_now else '✅ 尚未被通報（可獲得積分）'}")
    
    # 示範 4: 檢查不同 query parameters 的相同 URL
    print("\n" + "=" * 70)
    print("📝 示範 4: 檢查不同 query parameters 的相同 URL")
    print("=" * 70)
    
    different_query_url = "https://scam-example.com/fake-investment?ref=456&utm_source=line"
    print(f"新的 URL: {different_query_url}")
    
    normalized_2 = calc.normalize_url(different_query_url)
    print(f"標準化 URL: {normalized_2}")
    print(f"與原始標準化 URL 相同: {normalized == normalized_2}")
    
    is_duplicate_2 = calc.check_duplicate(normalized_2)
    print(f"是否重複: {is_duplicate_2}")
    print(f"結果: {'❌ 已被通報（重複）' if is_duplicate_2 else '✅ 尚未被通報（可獲得積分）'}")
    print("\n💡 說明: 即使 query parameters 不同，標準化後的 URL 相同，")
    print("   因此被視為重複通報，不會獲得積分。")
    
    # 示範 5: 檢查大小寫不同的相同 URL
    print("\n" + "=" * 70)
    print("📝 示範 5: 檢查大小寫不同的相同 URL")
    print("=" * 70)
    
    uppercase_url = "https://SCAM-EXAMPLE.COM/FAKE-INVESTMENT"
    print(f"大寫 URL: {uppercase_url}")
    
    normalized_3 = calc.normalize_url(uppercase_url)
    print(f"標準化 URL: {normalized_3}")
    print(f"與原始標準化 URL 相同: {normalized == normalized_3}")
    
    is_duplicate_3 = calc.check_duplicate(normalized_3)
    print(f"是否重複: {is_duplicate_3}")
    print(f"結果: {'❌ 已被通報（重複）' if is_duplicate_3 else '✅ 尚未被通報（可獲得積分）'}")
    print("\n💡 說明: URL 標準化會轉換為小寫，因此大小寫不同的相同 URL")
    print("   會被視為重複通報。")
    
    # 清理示範資料
    print("\n" + "=" * 70)
    print("🧹 清理示範資料")
    print("=" * 70)
    scam_reports_table.delete_item(Key={'report_id': report_id})
    print(f"✅ 已刪除示範記錄: {report_id}")
    
    print("\n" + "=" * 70)
    print("✅ 示範完成！")
    print("=" * 70)
    print("\n📚 重複檢測功能說明:")
    print("   1. 使用 normalize_url() 標準化 URL（移除 query params、trailing slash、轉小寫）")
    print("   2. 使用 check_duplicate() 查詢 ScamReports 表的 NormalizedUrlIndex GSI")
    print("   3. 如果找到記錄，表示 URL 已被通報，返回 True")
    print("   4. 如果沒有記錄，表示 URL 尚未被通報，返回 False")
    print("\n🎯 使用場景:")
    print("   - 在 update_team_points() 中使用，確保只有首位通報者獲得積分")
    print("   - 防止重複通報洗分")
    print("   - 符合 Requirements 11.1 和 11.3 的規範")


if __name__ == "__main__":
    try:
        demo_check_duplicate()
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
