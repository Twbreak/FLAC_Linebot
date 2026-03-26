from bedrock_service import parse_bedrock_response


def test_parse_expert_warning_from_next_line_bullet():
    response_text = """### 🛡️ 防詐風險評估報告

- **風險評分：** 8/10
- **詐騙類別：** 假投資詐騙
- **風險分析：**
  - 對方要求加入投資群組並保證獲利
- **專員警示：**
  * 請立即停止互動，勿匯款，並撥打 165 查證
---
"""

    result = parse_bedrock_response(response_text)

    assert result["expert_warning"] == "請立即停止互動，勿匯款，並撥打 165 查證"


def test_parse_expert_warning_from_same_line():
    response_text = """### 🛡️ 防詐風險評估報告

- **風險評分：** 6/10
- **詐騙類別：** 假投資詐騙
- **專員警示：** 請勿點擊連結或提供個人資料
"""

    result = parse_bedrock_response(response_text)

    assert result["expert_warning"] == "請勿點擊連結或提供個人資料"
