"""
Demo script for BedrockSummarizer class
Tests the generate_mass_report_alert() method
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bedrock_service import BedrockSummarizer

def main():
    print("=== BedrockSummarizer Demo ===\n")
    
    # Initialize the summarizer
    summarizer = BedrockSummarizer()
    print("✓ BedrockSummarizer initialized\n")
    
    # Test case: Fake investment scam message
    original_message = """
    🎉 恭喜您！您已被選中參加我們的獨家投資計劃！
    
    💰 只需投資 10,000 元，每月保證回報 30%！
    📈 我們的 AI 投資機器人已幫助 10,000+ 人實現財富自由！
    
    ⚠️ 名額有限，請立即加入我們的 LINE 群組：
    https://line.me/R/ti/g/fake-investment-group
    
    💳 請將款項匯入以下帳戶：
    銀行：XX銀行
    帳號：123-456-789
    戶名：投資顧問公司
    """
    
    report_count = 15
    
    print(f"原始訊息長度: {len(original_message)} 字元")
    print(f"通報次數: {report_count}\n")
    
    # Generate alert
    print("正在生成警示摘要...\n")
    result = summarizer.generate_mass_report_alert(original_message, report_count)
    
    # Display results
    print("=== 生成結果 ===\n")
    print(f"📝 警示摘要:\n{result['alert_summary']}\n")
    print(f"⚠️ 防範建議:\n{result['alert_warning']}\n")
    
    # Verify the summary doesn't contain the original message
    if original_message not in result['alert_summary']:
        print("✓ 驗證通過：摘要不包含原始訊息完整內容")
    else:
        print("✗ 警告：摘要包含原始訊息內容")

if __name__ == "__main__":
    main()
