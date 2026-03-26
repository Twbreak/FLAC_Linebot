#!/usr/bin/env python3
"""
測試 Bedrock 分析詐騙訊息
"""

from bedrock_service import analyze_scam_content

# 測試訊息（從截圖中提取）
test_message = """《輕鬆借》30 萬內當日撥款 可本利攤還 免押免保 有工作來就借
0972326557 陳怡潔（小潔）
線上諮詢 csms.tw/OxGHQ2
"""

print("=" * 80)
print("測試詐騙訊息分析")
print("=" * 80)
print(f"輸入訊息：\n{test_message}")
print("=" * 80)

result = analyze_scam_content(test_message)

print("\n分析結果：")
print(f"風險評分：{result['risk_score']}/10")
print(f"詐騙類別：{result['category']}")
print(f"風險分析：{result['analysis']}")
print(f"專員警示：{result['expert_warning']}")
print("\n" + "=" * 80)
print("原始 Bedrock 回應：")
print("=" * 80)
print(result.get('raw_response', 'N/A'))
