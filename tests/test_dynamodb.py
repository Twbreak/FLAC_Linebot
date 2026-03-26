#!/usr/bin/env python3
"""
測試 DynamoDB 連線和基本操作
"""

import os
from dotenv import load_dotenv
from database import create_table_if_not_exists, add_detection_record, get_user_history, get_leaderboard
from models import ScamDetectionRecord

# 載入環境變數
load_dotenv()

def test_connection():
    """測試 DynamoDB 連線"""
    print("=" * 50)
    print("🧪 測試 DynamoDB 連線")
    print("=" * 50)
    
    # 1. 建立 table
    print("\n1️⃣  檢查/建立 Table...")
    if create_table_if_not_exists():
        print("✅ Table 準備就緒")
    else:
        print("❌ Table 建立失敗")
        return False
    
    # 2. 新增測試資料
    print("\n2️⃣  新增測試資料...")
    test_record = ScamDetectionRecord(
        user_id="TEST_USER_123",
        input_content="這是測試訊息：投資保證獲利，月報酬30%",
        risk_score=9,
        category="假投資詐騙",
        analysis=["提到保證獲利", "不合理的高報酬率"],
        expert_warning="這是典型的投資詐騙話術，切勿相信！"
    )
    
    try:
        result = add_detection_record(test_record)
        print(f"✅ 新增成功: {result['record_id']}")
    except Exception as e:
        print(f"❌ 新增失敗: {e}")
        return False
    
    # 3. 查詢使用者歷史
    print("\n3️⃣  查詢使用者歷史...")
    try:
        history = get_user_history("TEST_USER_123")
        print(f"✅ 查詢成功，找到 {len(history)} 筆記錄")
        if history:
            print(f"   最新記錄: {history[0].input_content[:30]}...")
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        return False
    
    # 4. 取得排行榜
    print("\n4️⃣  取得排行榜...")
    try:
        leaderboard = get_leaderboard()
        print(f"✅ 查詢成功，共 {len(leaderboard)} 位使用者")
        if leaderboard:
            print(f"   第一名: {leaderboard[0].user_id} ({leaderboard[0].total_points} 分)")
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有測試通過！DynamoDB 運作正常")
    print("=" * 50)
    return True

if __name__ == "__main__":
    # 檢查環境變數
    required_vars = ["aws_access_key_id", "aws_secret_access_key"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少環境變數: {', '.join(missing_vars)}")
        print("請確認 .env 檔案設定正確")
        exit(1)
    
    # 執行測試
    success = test_connection()
    exit(0 if success else 1)
