#!/usr/bin/env python3
"""
Demo: NotificationDispatcher 基本功能測試
測試通知分發服務的初始化與方法呼叫
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notification_dispatcher import NotificationDispatcher

def main():
    print("🔧 初始化 NotificationDispatcher...")
    
    try:
        # 初始化通知分發服務
        dispatcher = NotificationDispatcher()
        print("✅ NotificationDispatcher 初始化成功")
        
        # 測試取得活躍使用者
        print("\n📋 取得活躍使用者清單...")
        active_users = dispatcher.get_all_active_users()
        print(f"✅ 找到 {len(active_users)} 位活躍使用者")
        
        if active_users:
            print(f"   前 5 位使用者: {active_users[:5]}")
        else:
            print("   目前沒有活躍使用者")
        
        # 測試訊息格式（不實際發送）
        print("\n📝 測試訊息格式...")
        test_message = """🚨 社群防詐警示

📊 系統偵測到大量通報
已有 15 位使用者通報相同詐騙訊息

⚠️ 風險摘要：
這是一則測試警示訊息

💡 防範建議：
請提高警覺，避免點擊可疑連結

🛡️ 請保護自己與親友的財產安全！
"""
        print(f"訊息長度: {len(test_message)} 字元")
        print(f"訊息內容:\n{test_message}")
        
        # 注意：不實際發送推送，避免打擾真實使用者
        print("\n⚠️ 此 Demo 不會實際發送推送訊息")
        print("   如需測試推送功能，請使用測試帳號")
        
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
