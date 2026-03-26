# Task 7.1 實作摘要：修改 Webhook Handler 整合團隊積分

## 任務概述

修改 `main.py` 的 `handle_text()` 函數，在 Bedrock AI 分析詐騙內容後，自動查詢使用者所屬團隊並更新團隊積分，同時在回覆訊息中加入團隊積分資訊。

## 實作內容

### 1. 修改 `handle_text()` 函數

**檔案：** `main.py`

**修改重點：**
- 在 Bedrock AI 分析完成後，檢查訊息是否包含 URL
- 若包含 URL，呼叫 `update_team_points_for_report()` 更新團隊積分
- 根據積分更新結果，選擇適當的回覆訊息格式

**程式碼片段：**
```python
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    """處理文字訊息（整合團隊積分）"""
    user_text = event.message.text
    user_id = event.source.user_id
    
    # 偵測網址
    urls = re.findall(r'https?://[^\s]+', user_text)
    
    # 使用 Bedrock 分析詐騙風險
    analysis_result = analyze_scam_content(user_text)
    
    # 儲存到資料庫
    record = ScamDetectionRecord(...)
    add_detection_record(record)
    
    # 新增：團隊積分計算（僅當訊息包含 URL 時）
    team_result = None
    if urls:
        team_result = update_team_points_for_report(
            reporter_uid=user_id,
            url=urls[0],
            risk_score=analysis_result['risk_score'],
            category=analysis_result['category']
        )
    
    # 修改回覆訊息，加入團隊積分資訊
    if team_result and team_result.get('points_earned', 0) > 0:
        reply_text = format_reply_with_team_points(analysis_result, team_result)
    else:
        reply_text = format_reply_message(analysis_result)
    
    reply_message(event.reply_token, reply_text)
```

### 2. 新增 `update_team_points_for_report()` 函數

**功能：** 查詢使用者所屬團隊並更新團隊積分

**實作邏輯：**
1. 使用 `LineUidIndex` GSI 查詢使用者所屬團隊
2. 若使用者不屬於任何團隊，回傳 `None`（不影響主流程）
3. 若使用者屬於團隊，呼叫 `PointsCalculator.update_team_points()` 更新積分
4. 回傳積分更新結果

**錯誤處理：**
- 積分更新失敗不應影響主流程
- 記錄錯誤日誌但繼續執行
- 回傳 `None` 表示積分更新失敗

### 3. 新增 `format_reply_with_team_points()` 函數

**功能：** 格式化包含團隊積分資訊的回覆訊息

**訊息格式：**
- 基本風險評估報告（與原有格式相同）
- 新增「🏆 團隊積分更新」區塊
- 顯示獲得的積分數量
- 若有倍數獎勵，顯示「(極高風險 2x 獎勵)」
- 若為重複通報，顯示「此 URL 已被通報，未獲得積分」

**範例訊息：**

**成功獲得積分（有倍數獎勵）：**
```
🚨 防詐風險評估報告

風險評分：9/10 (高風險)
詐騙類別：假投資詐騙

💡 專員警示：
請勿點擊連結或提供個人資訊

🏆 團隊積分更新
✅ 成功通報！您的團隊獲得 18 積分 (極高風險 2x 獎勵)

📊 查看完整分析記錄，請點選下方選單「我的儀表板」
```

**重複通報：**
```
🚨 防詐風險評估報告

風險評分：9/10 (高風險)
詐騙類別：假投資詐騙

💡 專員警示：
請勿點擊連結或提供個人資訊

🏆 團隊積分更新
ℹ️ 此 URL 已被通報，未獲得積分

📊 查看完整分析記錄，請點選下方選單「我的儀表板」
```

## 測試結果

### 單元測試

**檔案：** `tests/test_webhook_team_integration.py`

**測試案例：**
1. ✅ `test_update_team_points_for_report_success` - 成功更新團隊積分
2. ✅ `test_update_team_points_for_report_no_team` - 使用者不屬於任何團隊
3. ✅ `test_update_team_points_for_report_duplicate` - 重複通報不獲得積分
4. ✅ `test_format_reply_with_team_points_success` - 格式化成功獲得積分的訊息
5. ✅ `test_format_reply_with_team_points_duplicate` - 格式化重複通報的訊息
6. ✅ `test_format_reply_with_team_points_no_multiplier` - 格式化無倍數獎勵的訊息

**測試結果：** 6 passed, 0 failed

### 整合測試

**檔案：** `demos/demo_webhook_team_integration.py`

**測試場景：**
1. ✅ 建立測試團隊
2. ✅ 加入第二位成員
3. ✅ 隊長通報詐騙 URL（首次通報，高風險 9 分）
   - 獲得 18 積分（2x 倍數獎勵）
4. ✅ 成員通報詐騙 URL（首次通報，中風險 6 分）
   - 獲得 6 積分
5. ✅ 成員重複通報相同 URL
   - 不獲得積分
6. ✅ 查詢團隊最終積分
   - 總積分：24 分（18 + 6）
7. ✅ 查詢成員貢獻度
   - 隊長：18 分（1 次通報）
   - 成員：6 分（1 次通報）

**測試結果：** 所有場景通過

## 驗證的需求

- ✅ **Requirement 4.1** - 識別團隊成員的 LINE_UID
- ✅ **Requirement 4.2** - 查詢成員所屬的 Team_ID
- ✅ **Requirement 4.3** - 在 Bedrock AI 分析後檢查 URL 是否已被通報

## 技術細節

### 資料庫查詢

**查詢使用者所屬團隊：**
```python
team_members_table.query(
    IndexName='LineUidIndex',
    KeyConditionExpression='line_uid = :uid',
    ExpressionAttributeValues={':uid': reporter_uid},
    Limit=1
)
```

### 錯誤處理策略

1. **使用者不屬於團隊：** 回傳 `None`，不影響主流程
2. **積分更新失敗：** 記錄錯誤日誌，回傳 `None`，不影響主流程
3. **重複通報：** 回傳包含 `is_duplicate: True` 的結果，顯示適當訊息

### 效能考量

- 使用 GSI 查詢，避免全表掃描
- 限制查詢結果為 1 筆（`Limit=1`），提升效能
- 積分更新失敗不阻擋主流程，確保使用者體驗

## 相關檔案

- `main.py` - 修改 webhook handler
- `tests/test_webhook_team_integration.py` - 單元測試
- `demos/demo_webhook_team_integration.py` - 整合測試 demo

## 後續工作

Task 7.1 已完成，可以繼續執行：
- Task 7.2 - 撰寫整合測試

## 注意事項

1. **向後相容性：** 若使用者不屬於任何團隊，系統仍正常運作，不影響現有功能
2. **錯誤容忍：** 積分更新失敗不會導致 webhook 處理失敗
3. **日誌記錄：** 所有積分更新操作都有詳細的日誌記錄，便於除錯

## 結論

Task 7.1 已成功完成，webhook handler 現在能夠：
- 自動識別團隊成員
- 在詐騙通報後更新團隊積分
- 在回覆訊息中顯示團隊積分資訊
- 處理重複通報與倍數獎勵
- 優雅地處理錯誤情況

所有測試通過，功能運作正常。
