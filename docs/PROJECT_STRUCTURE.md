# FLAC Linebot 專案結構說明

## 目錄結構總覽

```
FLAC_Linebot/
├── 📁 核心程式碼
│   ├── main.py                    # FastAPI 主程式與路由
│   ├── models.py                  # Pydantic 資料模型
│   ├── database.py                # DynamoDB 資料庫操作
│   ├── bedrock_service.py         # AWS Bedrock AI 服務
│   ├── security.py                # HMAC 簽章安全模組
│   ├── team_service.py            # 團隊管理業務邏輯
│   └── points_calculator.py       # 積分計算與重複檢測
│
├── 📁 tests/                      # 測試檔案
│   ├── README.md                  # 測試說明文件
│   ├── test_security*.py          # 安全模組測試
│   ├── test_team_service*.py      # 團隊服務測試
│   ├── test_points_calculator*.py # 積分計算器測試
│   ├── test_*_api*.py             # API 端點測試
│   └── test_dynamodb.py           # 資料庫測試
│
├── 📁 demos/                      # 功能示範腳本
│   ├── README.md                  # 示範說明文件
│   ├── demo_security_usage.py     # 安全模組示範
│   ├── demo_team_*.py             # 團隊功能示範
│   ├── demo_*_api.py              # API 端點示範
│   └── verify_join_team.py        # 加入團隊驗證
│
├── 📁 docs/                       # 文件
│   └── task_summaries/            # 任務實作總結
│       ├── README.md              # 總結文件索引
│       ├── TASK_2.3_*.md          # 安全模組實作總結
│       ├── TASK_3.*_*.md          # 團隊管理實作總結
│       ├── TASK_4.*_*.md          # 積分系統實作總結
│       └── TASK_6.*_*.md          # API 端點實作總結
│
├── 📁 static/                     # LIFF 前端頁面
│   ├── index.html                 # 個人儀表板
│   └── leaderboard.html           # 全球排行榜
│
├── 📁 .kiro/                      # Kiro AI 設定
│   └── specs/
│       └── team-collaboration/
│           ├── requirements.md    # 需求文件
│           ├── design.md          # 設計文件
│           └── tasks.md           # 任務清單
│
├── 📄 設定檔案
│   ├── .env                       # 環境變數（需自行建立）
│   ├── .gitignore                 # Git 忽略清單
│   ├── README.md                  # 專案說明
│   ├── PROJECT_STRUCTURE.md       # 本文件
│   ├── DYNAMODB_SETUP.md          # DynamoDB 設定說明
│   └── QUICK_START_DYNAMODB.md    # DynamoDB 快速開始
│
└── 📁 其他
    ├── .venv/                     # Python 虛擬環境
    ├── __pycache__/               # Python 快取
    └── scam_detection_db.json     # 舊版資料庫（已棄用）
```

## 核心模組說明

### 1. main.py
FastAPI 應用程式主檔案，包含：
- LINE Bot Webhook 處理
- 所有 API 路由定義
- 團隊協作 API 端點
- 個人記錄 API 端點

### 2. models.py
Pydantic 資料模型定義：
- `ScamDetectionRecord` - 詐騙偵測記錄
- `Team` - 團隊資訊
- `TeamMember` - 團隊成員
- `ScamReport` - 詐騙通報記錄
- 各種 Request/Response 模型

### 3. database.py
DynamoDB 資料庫操作：
- 資料表自動建立與檢查
- CRUD 操作封裝
- GSI 查詢支援

### 4. security.py
安全模組：
- HMAC-SHA256 簽章產生
- 簽章驗證
- 邀請連結安全保護

### 5. team_service.py
團隊管理業務邏輯：
- 建立團隊
- 產生邀請連結
- 加入團隊
- 查詢團隊資訊與成員

### 6. points_calculator.py
積分計算系統：
- URL 標準化
- 重複通報檢測
- 積分計算（含倍數獎勵）
- 團隊積分更新（原子性操作）

### 7. bedrock_service.py
AWS Bedrock AI 服務：
- 詐騙內容分析
- 風險評分計算
- AI 回應處理

## 測試與示範

### tests/ 目錄
包含所有自動化測試：
- 單元測試（Unit Tests）
- 整合測試（Integration Tests）
- API 端點測試

執行方式：
```bash
pytest tests/                    # 執行所有測試
pytest tests/test_team_service.py  # 執行特定測試
pytest tests/ -v                 # 詳細輸出
```

### demos/ 目錄
包含功能示範腳本：
- 展示各模組的使用方式
- 提供實際執行範例
- 可用於手動測試

執行方式：
```bash
python3 demos/demo_security_usage.py
python3 demos/demo_team_info.py
```

## 文件系統

### docs/task_summaries/
包含所有已完成任務的詳細實作總結：
- 實作內容與技術細節
- 測試結果與驗證
- 符合的需求規範
- 使用範例與整合說明

### .kiro/specs/
Kiro AI 規格文件：
- `requirements.md` - 功能需求定義
- `design.md` - 系統設計文件
- `tasks.md` - 實作任務清單

## API 端點總覽

### 團隊協作 API
- `POST /api/teams/create` - 建立團隊
- `POST /api/teams/join` - 加入團隊
- `GET /api/teams/{team_id}` - 取得團隊資訊
- `GET /api/teams/{team_id}/members` - 取得成員清單
- `GET /api/leaderboard/teams` - 團隊排行榜

### 個人記錄 API
- `GET /api/history/{user_id}` - 個人歷史記錄
- `GET /api/leaderboard` - 全球排行榜

### LINE Bot
- `POST /callback` - LINE Webhook 接收端點

## 資料庫結構

### DynamoDB Tables

1. **ScamDetectionRecords** - 詐騙偵測記錄
   - PK: `record_id`
   - GSI: `UserIdIndex` (user_id + created_at)

2. **Teams** - 團隊資訊
   - PK: `team_id`

3. **TeamMembers** - 團隊成員
   - PK: `member_id` (格式: `{team_id}#{line_uid}`)
   - GSI: `TeamIdIndex` (team_id)
   - GSI: `LineUidIndex` (line_uid)

4. **ScamReports** - 詐騙通報記錄
   - PK: `report_id`
   - GSI: `NormalizedUrlIndex` (normalized_url)
   - GSI: `TeamIdIndex` (team_id + reported_at)

## 開發工作流程

### 1. 新增功能
1. 在 `.kiro/specs/team-collaboration/requirements.md` 定義需求
2. 在 `design.md` 設計實作方案
3. 在 `tasks.md` 建立任務清單
4. 實作功能程式碼
5. 撰寫測試（`tests/`）
6. 建立示範腳本（`demos/`）
7. 撰寫實作總結（`docs/task_summaries/`）

### 2. 測試流程
1. 執行單元測試：`pytest tests/`
2. 執行示範腳本驗證功能
3. 手動測試 API 端點
4. 檢查診斷錯誤：`getDiagnostics`

### 3. 部署流程
1. 確保所有測試通過
2. 更新環境變數（`.env`）
3. 啟動服務：`python main.py`
4. 設定 LINE Webhook URL
5. 監控日誌與錯誤

## 環境變數

必要的環境變數（`.env`）：
```env
# LINE Bot
LINE_CHANNEL_ACCESS_TOKEN=你的_TOKEN
LINE_CHANNEL_SECRET=你的_SECRET

# AWS
aws_access_key_id=你的_KEY
aws_secret_access_key=你的_SECRET
AWS_REGION=us-east-1

# 團隊系統
TEAM_INVITE_SECRET_KEY=至少32字元的密鑰
LIFF_ID_TEAM_MANAGEMENT=你的_LIFF_ID
LIFF_ID_TEAM_JOIN=你的_LIFF_ID
```

## 相關文件

- [README.md](README.md) - 專案說明與快速開始
- [DYNAMODB_SETUP.md](DYNAMODB_SETUP.md) - DynamoDB 詳細設定
- [tests/README.md](tests/README.md) - 測試說明
- [demos/README.md](demos/README.md) - 示範腳本說明
- [docs/task_summaries/README.md](docs/task_summaries/README.md) - 實作總結索引

## 技術棧

- **後端框架**: FastAPI
- **資料庫**: AWS DynamoDB
- **AI 服務**: AWS Bedrock (Gemma 3)
- **訊息平台**: LINE Messaging API
- **前端**: LINE LIFF (HTML/CSS/JavaScript)
- **測試框架**: pytest
- **Python 版本**: 3.8+

## 授權

MIT License
