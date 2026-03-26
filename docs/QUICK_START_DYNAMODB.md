# 🚀 DynamoDB 快速啟動指南

## 前置檢查

確認你的 `.env` 檔案包含：

```env
LINE_CHANNEL_ACCESS_TOKEN=你的token
LINE_CHANNEL_SECRET=你的secret
aws_access_key_id=你的key
aws_secret_access_key=你的secret
AWS_REGION=us-east-1
```

## 步驟 1：測試 DynamoDB 連線

```bash
python test_dynamodb.py
```

你應該會看到：

```
==================================================
🧪 測試 DynamoDB 連線
==================================================

1️⃣  檢查/建立 Table...
✅ DynamoDB table 'ScamDetectionRecords' 建立成功！
✅ Table 準備就緒

2️⃣  新增測試資料...
✅ 新增成功: TEST_USER_123#2024-03-26T...

3️⃣  查詢使用者歷史...
✅ 查詢成功，找到 1 筆記錄

4️⃣  取得排行榜...
✅ 查詢成功，共 1 位使用者

==================================================
🎉 所有測試通過！DynamoDB 運作正常
==================================================
```

## 步驟 2：啟動應用程式

```bash
python main.py
```

你會看到：

```
🔧 正在檢查 DynamoDB table...
✅ DynamoDB table 'ScamDetectionRecords' 已存在
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## 步驟 3：測試功能

### 3.1 傳送訊息給 LINE Bot

傳送任何訊息給你的 LINE Bot，例如：
```
我收到一個投資訊息，說保證月報酬30%
```

Bot 會分析並回覆風險評估報告。

### 3.2 查看網頁記錄

在 LINE 內開啟你的 LIFF URL：
```
https://liff.line.me/2009609029-RlBZuNs2
```

你應該會看到剛才的分析記錄！

### 3.3 檢查 DynamoDB

前往 AWS Console：
1. https://console.aws.amazon.com/dynamodb/
2. 選擇 Region: us-east-1
3. 點選 Tables → ScamDetectionRecords
4. 點選 "Explore table items"

你會看到剛才儲存的記錄！

## 常見問題

### Q: 測試失敗，顯示 AccessDeniedException？

**解決方法**：
1. 檢查 IAM 使用者權限
2. 確認 AWS 憑證正確
3. 參考 `DYNAMODB_SETUP.md` 的 IAM 權限設定

### Q: Table 建立很慢？

**正常現象**：DynamoDB table 建立需要 30-60 秒，請耐心等待。

### Q: 想刪除測試資料？

```bash
# 使用 AWS CLI
aws dynamodb delete-item \
    --table-name ScamDetectionRecords \
    --key '{"record_id":{"S":"TEST_USER_123#2024-03-26T..."}}' \
    --region us-east-1
```

或在 AWS Console 手動刪除。

### Q: 想刪除整個 Table？

```bash
aws dynamodb delete-table --table-name ScamDetectionRecords --region us-east-1
```

下次啟動程式會自動重新建立。

## 遷移舊資料（選擇性）

如果你有舊的 `scam_detection_db.json` 資料：

```bash
python migrate_json_to_dynamodb.py
```

（需要先建立這個腳本，或手動遷移）

## 成功指標

✅ `test_dynamodb.py` 全部通過
✅ 應用程式啟動無錯誤
✅ LINE Bot 可以接收並回覆訊息
✅ LIFF 網頁可以顯示記錄
✅ AWS Console 可以看到資料

## 下一步

- 設定 CloudWatch 監控
- 調整 Read/Write Capacity
- 設定備份策略
- 優化排行榜查詢效能

詳細資訊請參考 `DYNAMODB_SETUP.md`
