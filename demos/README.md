# 示範腳本目錄

此目錄包含所有團隊協作系統功能的示範腳本。

## 示範腳本分類

### 安全模組示範
- `demo_security_usage.py` - HMAC 簽章功能示範

### 團隊服務示範
- `demo_invite_member.py` - 邀請成員功能示範
- `demo_join_team.py` - 加入團隊功能示範
- `demo_team_info.py` - 團隊資訊查詢示範
- `verify_join_team.py` - 加入團隊驗證腳本

### 積分計算器示範
- `demo_points_calculator.py` - URL 標準化功能示範
- `demo_check_duplicate.py` - 重複檢測功能示範
- `demo_task_4_5.py` - 積分計算與倍數獎勵示範
- `demo_update_team_points.py` - 團隊積分更新示範

### API 端點示範
- `demo_create_team_api.py` - 建立團隊 API 示範
- `demo_join_team_api.py` - 加入團隊 API 示範
- `demo_team_info_api.py` - 團隊資訊 API 示範
- `demo_team_info_api_testclient.py` - 團隊資訊 API TestClient 示範
- `demo_team_leaderboard_api.py` - 團隊排行榜 API 示範

## 使用方式

### 執行示範腳本

確保已啟動 DynamoDB 和設定環境變數後：

```bash
# 執行特定示範
python3 demos/demo_security_usage.py

# 或使用相對路徑
cd demos
python3 demo_security_usage.py
```

### API 示範腳本

部分 API 示範腳本需要先啟動 FastAPI 伺服器：

```bash
# 終端機 1：啟動伺服器
uvicorn main:app --reload --port 8080

# 終端機 2：執行 API 示範
python3 demos/demo_create_team_api.py
```

使用 TestClient 的示範腳本不需要啟動伺服器：
```bash
python3 demos/demo_team_info_api_testclient.py
```

## 示範腳本說明

每個示範腳本都會：
1. 展示功能的基本使用方式
2. 提供實際的使用範例
3. 顯示預期的輸出結果
4. 自動清理測試資料

## 注意事項

- 示範腳本會在 DynamoDB 中建立測試資料
- 大部分腳本會在執行結束後自動清理資料
- 確保已設定正確的環境變數（.env 檔案）
- API 示範腳本需要 FastAPI 伺服器運行（除非使用 TestClient）
