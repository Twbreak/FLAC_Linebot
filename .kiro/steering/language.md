---
inclusion: auto
---

# 語言規範

## 回應語言要求

所有與使用者的對話、說明、註解和文件，必須使用**繁體中文**回應。

## 適用範圍

- AI 助理的所有回應訊息
- 程式碼註解（除非是英文專有名詞）
- 文件說明
- 錯誤訊息
- 提示訊息

## 例外情況

以下情況可使用英文：
- 程式碼變數名稱、函數名稱（遵循 Python/JavaScript 命名慣例）
- 技術專有名詞（如 API、SDK、DynamoDB）
- Git commit 訊息（可選）
- 第三方套件名稱

## 範例

✅ 正確：
```python
# 取得使用者歷史記錄
def get_user_history(user_id: str):
    """查詢特定使用者的所有偵測記錄"""
    pass
```

❌ 錯誤：
```python
# Get user history
def get_user_history(user_id: str):
    """Query all detection records for a specific user"""
    pass
```
