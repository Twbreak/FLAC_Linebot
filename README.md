# FLAC Linebot - 防詐騙風險評估系統

## 專案架構

```
FLAC_Linebot/
├── main.py                    # FastAPI 主程式（路由 + webhook）
├── models.py                  # 資料模型定義
├── database.py                # DynamoDB 資料庫操作
├── bedrock_service.py         # AWS Bedrock AI 分析服務
├── security.py                # HMAC 簽章安全模組
├── team_service.py            # 團隊管理服務
├── points_calculator.py       # 積分計算器
├── static/                    # 靜態網頁（LIFF 應用）
│   ├── index.html            # 個人儀表板
│   └── leaderboard.html      # 全球排行榜
├── tests/                     # 測試檔案
│   ├── test_security.py      # 安全模組測試
│   ├── test_team_service.py  # 團隊服務測試
│   ├── test_points_calculator.py  # 積分計算器測試
│   └── test_*_api.py         # API 端點測試
├── demos/                     # 功能示範腳本
│   ├── demo_security_usage.py
│   ├── demo_team_info.py
│   └── demo_*.py
├── docs/                      # 文件
│   └── task_summaries/       # 任務實作總結
│       ├── TASK_2.3_IMPLEMENTATION_SUMMARY.md
│       ├── TASK_3.1_IMPLEMENTATION_SUMMARY.md
│       └── TASK_*.md
├── .kiro/                     # Kiro AI 設定與 Spec 文件
│   └── specs/
│       └── team-collaboration/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
├── .env                       # 環境變數（需自行建立）
└── scam_detection_db.json    # 舊版資料庫檔案（已棄用）
```

## 功能說明

### 1. LINE Bot Webhook
- 接收使用者傳送的文字訊息
- 使用 AWS Bedrock (Gemma 3) 進行詐騙風險分析
- 回傳風險評估報告給使用者
- 自動儲存分析記錄到資料庫
- 支援團隊積分系統（團隊成員通報可獲得積分）

### 2. 團隊協作系統 API
- `POST /api/teams/create` - 建立團隊
- `POST /api/teams/join` - 加入團隊（需邀請連結）
- `GET /api/teams/{team_id}` - 取得團隊資訊
- `GET /api/teams/{team_id}/members` - 取得團隊成員清單
- `GET /api/leaderboard/teams` - 取得團隊排行榜

### 3. 個人記錄 API
- `GET /api/history/{user_id}` - 取得個人歷史記錄
- `GET /api/leaderboard` - 取得全球排行榜

### 4. LIFF 網頁應用
- 個人儀表板：查看自己的偵測記錄、總分、優惠券
- 全球排行榜：查看所有使用者的排名
- 團隊管理：建立團隊、邀請成員、查看團隊資訊
- 團隊排行榜：查看團隊積分排名

## 環境設定

### 1. 建立 `.env` 檔案

```env
LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET=你的_LINE_CHANNEL_SECRET
aws_access_key_id=你的_AWS_ACCESS_KEY_ID
aws_secret_access_key=你的_AWS_SECRET_ACCESS_KEY
AWS_REGION=us-east-1
TEAM_INVITE_SECRET_KEY=你的_32字元以上的密鑰
LIFF_ID_TEAM_MANAGEMENT=你的_LIFF_ID
LIFF_ID_TEAM_JOIN=你的_LIFF_ID
```

### 2. 安裝相依套件

```bash
pip install fastapi uvicorn python-dotenv line-bot-sdk boto3
```

### 3. 啟動服務

```bash
python main.py
```

服務會在 `http://0.0.0.0:8080` 啟動

## 部署到 EC2

### 使用 ngrok（開發測試）

```bash
# 終端 1：啟動應用程式
python main.py

# 終端 2：啟動 ngrok
ngrok http 8080
```

將 ngrok 提供的 HTTPS URL 設定到 LINE Developers Console 的 Webhook URL：
```
https://your-ngrok-url.ngrok-free.app/callback
```

### 使用 systemd（正式環境）

建立 `/etc/systemd/system/flac-linebot.service`：

```ini
[Unit]
Description=FLAC Linebot Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/FLAC_Linebot
Environment="PATH=/home/ubuntu/FLAC_Linebot/.venv/bin"
ExecStart=/home/ubuntu/FLAC_Linebot/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

啟動服務：
```bash
sudo systemctl daemon-reload
sudo systemctl enable flac-linebot
sudo systemctl start flac-linebot
sudo systemctl status flac-linebot
```

## 資料庫

使用 AWS DynamoDB 儲存詐騙偵測記錄和團隊資料。

### Tables 資訊

#### ScamDetectionRecords
- **Primary Key**: `record_id` (String)
- **GSI**: `UserIdIndex` (user_id + created_at)
- 用途：儲存詐騙偵測記錄

#### Teams（團隊協作系統）
- **Primary Key**: `team_id` (String)
- 用途：儲存團隊基本資訊

#### TeamMembers
- **Primary Key**: `member_id` (String, 格式: `{team_id}#{line_uid}`)
- **GSI**: `TeamIdIndex` (team_id)
- **GSI**: `LineUidIndex` (line_uid)
- 用途：儲存團隊成員資訊

#### ScamReports
- **Primary Key**: `report_id` (String)
- **GSI**: `NormalizedUrlIndex` (normalized_url)
- **GSI**: `TeamIdIndex` (team_id + reported_at)
- 用途：儲存團隊成員的詐騙通報記錄

### 自動建立
程式啟動時會自動檢查並建立所有 DynamoDB tables（如果不存在）。

詳細設定請參考：[DYNAMODB_SETUP.md](DYNAMODB_SETUP.md)

## API 測試

```bash
# 測試取得歷史記錄
curl http://localhost:8080/api/history/U1234567890

# 測試取得排行榜
curl http://localhost:8080/api/leaderboard

# 測試建立團隊
curl -X POST http://localhost:8080/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{"leader_uid": "U1234567890", "team_name": "防詐先鋒隊"}'

# 測試取得團隊排行榜
curl http://localhost:8080/api/leaderboard/teams
```

## 測試

### 執行所有測試
```bash
pytest tests/
```

### 執行特定測試
```bash
pytest tests/test_team_service.py
pytest tests/test_points_calculator.py
```

### 執行示範腳本
```bash
python3 demos/demo_security_usage.py
python3 demos/demo_team_info.py
```

詳細測試說明請參考：
- [tests/README.md](tests/README.md)
- [demos/README.md](demos/README.md)

## 開發注意事項

1. **模組化設計**：每個功能獨立成檔案，方便維護
2. **資料模型**：使用 Pydantic 確保資料格式正確
3. **錯誤處理**：所有 API 都有適當的錯誤處理
4. **擴充性**：可輕鬆替換資料庫或 AI 服務

## 授權

MIT License
