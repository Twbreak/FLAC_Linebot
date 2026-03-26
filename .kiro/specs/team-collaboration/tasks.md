# Implementation Plan: Team Collaboration System

## Overview

本實作計畫將團隊協作系統整合至現有的 FLAC Linebot 詐騙偵測系統。實作採用 Python (FastAPI + boto3) 後端，搭配 LINE LIFF 前端，並透過 DynamoDB 儲存團隊資料。實作順序遵循「資料層 → 業務邏輯 → API 端點 → 前端整合」的原則，確保每個步驟都能獨立測試與驗證。

## Tasks

- [x] 1. 建立 DynamoDB 資料表與索引
  - 建立 Teams、TeamMembers、ScamReports 三個資料表
  - 為 TeamMembers 建立 TeamIdIndex 與 LineUidIndex GSI
  - 為 ScamReports 建立 NormalizedUrlIndex 與 TeamIdIndex GSI
  - 在 database.py 新增 create_team_tables_if_not_exist() 函數
  - 在應用程式啟動時自動檢查並建立資料表
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 2. 實作資料模型與安全模組
  - [x] 2.1 擴充 Pydantic 資料模型
    - 在 models.py 新增 Team、TeamMember、ScamReport 模型
    - 新增 CreateTeamRequest、JoinTeamRequest、TeamLeaderboard 模型
    - 實作資料驗證規則（team_name 長度 1-30 字元）
    - _Requirements: 1.7, 2.3, 3.4_

  - [ ] 2.2 撰寫資料模型的 property test
    - **Property 3: Team Name Validation**
    - **Validates: Requirements 1.7**

  - [x] 2.3 實作 HMAC 簽章模組
    - 建立 security.py 模組
    - 實作 SecurityService 類別，包含 generate_signature() 與 verify_signature() 方法
    - 使用 HMAC-SHA256 演算法對 team_id 進行簽章
    - 從環境變數讀取 TEAM_INVITE_SECRET_KEY
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [ ] 2.4 撰寫 HMAC 簽章的 property test
    - **Property 16: HMAC Signature Round-Trip**
    - **Validates: Requirements 10.1, 10.3**

- [ ] 3. 實作團隊管理業務邏輯
  - [x] 3.1 建立團隊服務模組
    - 建立 team_service.py 模組
    - 實作 TeamService 類別的 create_team() 方法
    - 產生 UUID 格式的 team_id
    - 檢查使用者是否已是隊長（查詢 Teams 表）
    - 寫入 Teams 表與 TeamMembers 表（隊長作為首位成員）
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 3.2 撰寫團隊建立的 property tests
    - **Property 1: Team ID Uniqueness**
    - **Property 2: Team Creation Completeness**
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [x] 3.3 實作邀請連結產生功能
    - 在 TeamService 實作 invite_member() 方法
    - 產生包含 team_id 與 signature 的 LIFF URL
    - 整合 SecurityService 進行簽章
    - _Requirements: 2.3, 10.2_

  - [ ] 3.4 撰寫邀請 URL 的 property test
    - **Property 4: Invite URL Generation**
    - **Validates: Requirements 2.3**

  - [x] 3.5 實作加入團隊功能
    - 在 TeamService 實作 join_team() 方法
    - 驗證 HMAC 簽章
    - 檢查團隊是否存在
    - 檢查使用者是否已是成員或屬於其他團隊
    - 寫入 TeamMembers 表
    - _Requirements: 3.2, 3.3, 3.5, 3.6, 3.8, 3.9, 10.3, 10.4_

  - [ ] 3.6 撰寫加入團隊的 property test
    - **Property 7: Team Join Completeness**
    - **Validates: Requirements 3.5, 3.6**

  - [x] 3.7 實作團隊資訊查詢功能
    - 在 TeamService 實作 get_team_info() 方法
    - 從 Teams 表查詢團隊基本資訊
    - 實作 get_team_members() 方法，使用 TeamIdIndex GSI 查詢成員清單
    - 依 contribution_points 降序排序成員
    - _Requirements: 6.4, 6.5, 7.1, 7.3_

  - [ ] 3.8 撰寫成員排序的 property test
    - **Property 12: Member Contribution Ordering**
    - **Validates: Requirements 6.6, 7.4**

- [ ] 4. 實作積分計算模組
  - [x] 4.1 建立積分計算器模組
    - 建立 points_calculator.py 模組
    - 實作 PointsCalculator 類別的 normalize_url() 方法
    - 移除 URL 的 query parameters 與 trailing slash
    - 轉換為小寫
    - _Requirements: 11.2_

  - [ ] 4.2 撰寫 URL 標準化的 property test
    - **Property 17: URL Normalization Idempotence**
    - **Validates: Requirements 11.2**

  - [x] 4.3 實作重複檢測功能
    - 在 PointsCalculator 實作 check_duplicate() 方法
    - 使用 NormalizedUrlIndex GSI 查詢 ScamReports 表
    - _Requirements: 11.1, 11.3_

  - [ ] 4.4 撰寫重複檢測的 property test
    - **Property 9: Duplicate Report Rejection**
    - **Validates: Requirements 4.7, 11.3**

  - [x] 4.5 實作積分計算與倍數獎勵
    - 在 PointsCalculator 實作 calculate_points() 方法
    - 當 risk_score >= 9 時套用 2x 倍數
    - _Requirements: 5.1, 5.2_

  - [ ] 4.6 撰寫倍數獎勵的 property test
    - **Property 10: High Risk Multiplier**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

  - [x] 4.7 實作團隊積分更新功能
    - 在 PointsCalculator 實作 update_team_points() 方法
    - 使用 DynamoDB 原子性計數器更新 Teams.total_points
    - 使用原子性計數器更新 TeamMembers.contribution_points
    - 寫入 ScamReports 表記錄通報
    - _Requirements: 4.4, 4.5, 4.6, 4.8, 4.9_

  - [ ] 4.8 撰寫首位通報者的 property test
    - **Property 8: First Reporter Points Award**
    - **Validates: Requirements 4.4, 4.5, 4.6**

- [ ] 5. Checkpoint - 確認核心業務邏輯測試通過
  - 執行所有 unit tests 與 property tests
  - 確認資料表操作正常
  - 確認 HMAC 簽章驗證正確
  - 如有問題請詢問使用者

- [ ] 6. 實作 FastAPI 端點
  - [x] 6.1 實作建立團隊 API
    - 在 main.py 新增 POST /api/teams/create 端點
    - 整合 TeamService.create_team()
    - 回傳 team_id 與邀請 URL
    - 處理錯誤情況（重複隊長、無效名稱）
    - _Requirements: 1.1, 1.5, 1.6, 1.7_

  - [ ] 6.2 撰寫建立團隊 API 的 unit tests
    - 測試成功建立團隊
    - 測試重複隊長錯誤
    - 測試無效團隊名稱

  - [x] 6.3 實作加入團隊 API
    - 在 main.py 新增 POST /api/teams/join 端點
    - 整合 TeamService.join_team()
    - 驗證簽章並處理各種錯誤情況
    - _Requirements: 3.1, 3.7, 10.4_

  - [ ] 6.4 撰寫加入團隊 API 的 unit tests
    - 測試成功加入團隊
    - 測試無效簽章
    - 測試重複加入

  - [x] 6.4 實作團隊資訊查詢 API
    - 在 main.py 新增 GET /api/teams/{team_id} 端點
    - 在 main.py 新增 GET /api/teams/{team_id}/members 端點
    - 整合 TeamService 查詢方法
    - _Requirements: 6.4, 6.5, 7.1, 7.2, 7.3, 7.5_

  - [x] 6.5 實作團隊排行榜 API
    - 在 main.py 新增 GET /api/leaderboard/teams 端點
    - 從 Teams 表掃描所有團隊
    - 依 total_points 降序排序
    - 回傳前 10 名團隊
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 6.6 撰寫排行榜的 property test
    - **Property 11: Team Leaderboard Ordering**
    - **Validates: Requirements 6.2**

- [ ] 7. 整合詐騙通報與團隊積分
  - [x] 7.1 修改 webhook handler
    - 修改 main.py 的 handle_text() 函數
    - 在 Bedrock AI 分析後查詢使用者所屬團隊
    - 呼叫 PointsCalculator.update_team_points()
    - 修改回覆訊息，加入團隊積分資訊
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 7.2 撰寫整合測試
    - 測試團隊成員通報詐騙後積分正確更新
    - 測試非團隊成員通報不影響團隊積分
    - 測試重複通報不增加積分

- [ ] 8. 實作團隊任務系統
  - [x] 8.1 實作每日任務檢測
    - 在 points_calculator.py 新增 check_daily_quest() 方法
    - 查詢團隊當日通報數量（使用 TeamIdIndex GSI）
    - 當達到 5 則時給予 50 點獎勵
    - 檢查 completed_quests 避免重複獎勵
    - 更新 Teams.completed_quests 欄位
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_

  - [ ] 8.2 撰寫任務系統的 property test
    - **Property 13: Daily Quest Completion**
    - **Validates: Requirements 8.2, 8.3, 8.4, 8.6**

  - [x] 8.3 整合任務檢測至通報流程
    - 在 update_team_points() 方法中呼叫 check_daily_quest()
    - 在 LINE Bot 回覆中加入任務完成通知
    - _Requirements: 8.5_

- [ ] 9. 實作詐騙趨勢地圖 API
  - [x] 9.1 實作網域統計功能
    - 在 main.py 新增 GET /api/trends/domains 端點
    - 從 ScamReports 表掃描所有通報
    - 使用 urlparse 提取網域名稱
    - 統計每個網域的通報次數與平均風險評分
    - 依通報次數降序排序，回傳前 20 名
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 9.2 撰寫網域統計的 property tests
    - **Property 14: Domain Extraction**
    - **Property 15: Domain Trend Ordering**
    - **Validates: Requirements 9.2, 9.5**

- [ ] 10. Checkpoint - 確認後端 API 完整性
  - 使用 Postman 或 curl 測試所有 API 端點
  - 確認錯誤處理正確
  - 確認資料庫操作原子性
  - 如有問題請詢問使用者

- [ ] 11. 實作 LIFF 前端頁面
  - [x] 11.1 建立團隊管理頁面 HTML
    - 建立 static/team.html
    - 引入 LIFF SDK 與 Tailwind CSS
    - 建立團隊建立表單
    - 建立團隊資訊顯示區塊
    - 建立成員清單顯示區塊
    - _Requirements: 1.1, 6.4, 7.1_

  - [x] 11.2 實作團隊管理 JavaScript
    - 建立 static/team.js
    - 實作 LIFF 初始化與登入檢查
    - 實作 createTeam() 函數，呼叫 POST /api/teams/create
    - 實作 loadTeamInfo() 函數，呼叫 GET /api/teams/{team_id}
    - 實作 loadTeamMembers() 函數，呼叫 GET /api/teams/{team_id}/members
    - _Requirements: 1.1, 1.5, 6.4, 7.1_

  - [x] 11.3 實作 ShareTargetPicker 邀請功能
    - 在 team.js 實作 inviteMembers() 函數
    - 檢查 liff.isApiAvailable('shareTargetPicker')
    - 建立 Flex Message 邀請卡片
    - 呼叫 liff.shareTargetPicker() 發送邀請
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6_

  - [ ] 11.4 撰寫 Flex Message 的 property test
    - **Property 5: Flex Message Completeness**
    - **Validates: Requirements 2.4**

  - [x] 11.5 實作加入團隊頁面
    - 建立 static/team-join.html（或複用 team.html）
    - 實作 URL 參數解析（team_id 與 signature）
    - 呼叫 POST /api/teams/join API
    - 顯示加入成功或錯誤訊息
    - _Requirements: 3.1, 3.4, 3.7_

  - [ ] 11.6 撰寫 URL 參數解析的 property test
    - **Property 6: URL Parameter Parsing**
    - **Validates: Requirements 3.1**

- [ ] 12. 實作團隊排行榜前端頁面
  - [x] 12.1 建立排行榜 HTML
    - 建立 static/team-leaderboard.html
    - 建立團隊排行榜表格
    - 建立成員貢獻度展示區塊
    - _Requirements: 6.1, 6.3, 7.2_

  - [x] 12.2 實作排行榜 JavaScript
    - 建立 static/team-leaderboard.js
    - 呼叫 GET /api/leaderboard/teams API
    - 渲染前 10 名團隊
    - 實作團隊詳細資訊展開功能
    - 標示 MVP 成員
    - _Requirements: 6.3, 6.6, 7.5_

- [ ] 13. 實作詐騙趨勢地圖前端
  - [x] 13.1 建立趨勢地圖頁面
    - 建立 static/trends.html
    - 建立網域統計表格
    - 呼叫 GET /api/trends/domains API
    - 顯示前 20 名網域與通報次數
    - _Requirements: 9.1, 9.4_

- [ ] 14. 環境變數與部署設定
  - [ ] 14.1 更新環境變數
    - 在 .env 新增 TEAM_INVITE_SECRET_KEY（至少 32 字元）
    - 在 .env 新增 LIFF_ID_TEAM_MANAGEMENT
    - 在 .env 新增 LIFF_ID_TEAM_JOIN
    - 更新 README.md 說明新增的環境變數

  - [ ] 14.2 建立資料庫初始化腳本
    - 建立 scripts/init_team_tables.py
    - 呼叫 create_team_tables_if_not_exist()
    - 提供獨立執行選項

- [ ] 15. 整合測試與驗證
  - [ ] 15.1 執行完整的端對端測試
    - 測試建立團隊 → 邀請成員 → 加入團隊流程
    - 測試團隊成員通報詐騙 → 積分更新流程
    - 測試排行榜顯示正確
    - 測試重複通報檢測
    - 測試極高風險倍數獎勵
    - 測試每日任務完成

  - [ ] 15.2 執行效能測試
    - 測試 100 個團隊的排行榜查詢效能
    - 測試 10 個並發通報的原子性
    - 測試 1000 筆通報的趨勢地圖查詢效能

- [ ] 16. Final Checkpoint - 完整功能驗證
  - 確認所有 API 端點正常運作
  - 確認 LIFF 頁面可正常開啟與操作
  - 確認 ShareTargetPicker 邀請功能正常
  - 確認積分計算與排行榜正確
  - 確認所有測試通過
  - 如有問題請詢問使用者

## Notes

- 標記 `*` 的任務為選擇性測試任務，可跳過以加速 MVP 開發
- 每個任務都標註對應的需求編號，確保可追溯性
- Checkpoint 任務確保階段性驗證，及早發現問題
- Property tests 驗證通用正確性屬性，unit tests 驗證特定範例與邊界情況
- 使用 Python + FastAPI + boto3 技術棧，與現有系統一致
- DynamoDB 原子性計數器確保並發安全
- HMAC-SHA256 簽章確保邀請連結安全性
