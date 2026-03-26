#!/usr/bin/env python3
"""
測試 MassReportAlerts DynamoDB 資料表建立
"""

import os
from dotenv import load_dotenv
from database import create_mass_report_alerts_table

# 載入環境變數
load_dotenv()

def test_create_mass_report_alerts_table():
    """測試 MassReportAlerts 資料表建立"""
    print("=" * 50)
    print("🧪 測試 MassReportAlerts 資料表建立")
    print("=" * 50)
    
    print("\n1️⃣  建立/檢查 MassReportAlerts Table...")
    result = create_mass_report_alerts_table()
    
    if result:
        print("✅ MassReportAlerts 資料表準備就緒")
        print("\n" + "=" * 50)
        print("🎉 測試通過！")
        print("=" * 50)
        return True
    else:
        print("❌ MassReportAlerts 資料表建立失敗")
        return False

if __name__ == "__main__":
    # 檢查環境變數
    required_vars = ["aws_access_key_id", "aws_secret_access_key"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少環境變數: {', '.join(missing_vars)}")
        print("請確認 .env 檔案設定正確")
        exit(1)
    
    # 執行測試
    success = test_create_mass_report_alerts_table()
    exit(0 if success else 1)
