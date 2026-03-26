# 測試檔案目錄

此目錄包含所有團隊協作系統的測試檔案。

## 測試檔案分類

### 安全模組測試
- `test_security.py` - HMAC 簽章功能測試
- `test_security_simple.py` - 簡化版安全測試

### 團隊服務測試
- `test_team_service.py` - 團隊服務完整測試
- `test_team_service_simple.py` - 簡化版團隊服務測試
- `test_invite_member.py` - 邀請成員功能測試
- `test_join_team.py` - 加入團隊功能測試
- `test_team_info.py` - 團隊資訊查詢測試

### 積分計算器測試
- `test_points_calculator.py` - 積分計算器測試
- `test_normalize_url_manual.py` - URL 標準化手動測試
- `test_check_duplicate.py` - 重複檢測測試
- `test_check_duplicate_manual.py` - 重複檢測手動測試
- `test_update_team_points.py` - 團隊積分更新測試

### API 端點測試
- `test_create_team_api.py` - 建立團隊 API 測試
- `test_create_team_unit.py` - 建立團隊單元測試
- `test_join_team_api.py` - 加入團隊 API 測試
- `test_join_team_api_unit.py` - 加入團隊單元測試
- `test_team_info_api.py` - 團隊資訊 API 測試
- `test_team_leaderboard_api.py` - 團隊排行榜 API 測試
- `test_team_leaderboard_unit.py` - 團隊排行榜單元測試

### 資料庫測試
- `test_dynamodb.py` - DynamoDB 連線與操作測試

## 執行測試

### 執行所有測試
```bash
pytest tests/
```

### 執行特定測試檔案
```bash
pytest tests/test_team_service.py
```

### 執行特定測試函數
```bash
pytest tests/test_team_service.py::test_create_team
```

### 顯示詳細輸出
```bash
pytest tests/ -v
```

### 顯示 print 輸出
```bash
pytest tests/ -s
```

## 測試覆蓋率

查看測試覆蓋率：
```bash
pytest tests/ --cov=. --cov-report=html
```

## 注意事項

- 所有測試都需要 DynamoDB Local 或 AWS DynamoDB 連線
- 測試會自動建立和清理測試資料
- 部分測試需要設定環境變數（參考 .env.example）
