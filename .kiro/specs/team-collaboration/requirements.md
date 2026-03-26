# Requirements Document

## Introduction

團隊協作系統 (Team Collaboration System) 是 FLAC Linebot 詐騙偵測系統的社交擴充功能，允許使用者透過 LINE LIFF 建立團隊、邀請好友加入，並透過集體通報詐騙內容來累積團隊積分。系統整合現有的 AI 詐騙偵測能力，將個人防詐行為轉化為團隊競賽與協作機制，並在 Scam Hero Dashboard 上展示團隊排行榜與成員貢獻度。

## Glossary

- **Team_Collaboration_System**: 團隊協作系統，負責管理團隊建立、成員管理、積分計算與排行榜
- **LIFF_Client**: LINE Front-end Framework 客戶端，運行於 LINE 應用程式內的網頁介面
- **Team**: 團隊實體，包含唯一識別碼 (Team_ID)、團隊名稱、隊長與成員清單
- **Team_Leader**: 團隊隊長，建立團隊的使用者，擁有邀請成員的權限
- **Team_Member**: 團隊成員，透過邀請加入團隊的使用者
- **LINE_UID**: LINE 使用者唯一識別碼，用於識別使用者身分
- **Team_ID**: 團隊唯一識別碼，格式為 UUID
- **Scam_Report**: 詐騙通報記錄，包含 URL、風險評分、通報者與所屬團隊
- **Team_Points**: 團隊總積分，由所有成員的有效通報累積
- **Contribution_Points**: 成員個人貢獻積分，記錄該成員為團隊賺取的積分
- **Scam_Hero_Dashboard**: 詐騙英雄儀表板，展示團隊排行榜與詳細數據的管理後台
- **ShareTargetPicker**: LIFF SDK 提供的好友選擇器 API，用於發送邀請訊息
- **Flex_Message**: LINE 訊息格式，支援豐富的卡片式排版
- **Bedrock_AI**: AWS Bedrock 服務，使用 Gemma 3 模型進行詐騙內容分析
- **DynamoDB**: AWS NoSQL 資料庫服務，儲存團隊、成員與通報記錄
- **Teams_Table**: DynamoDB 資料表，儲存團隊基本資訊
- **Team_Members_Table**: DynamoDB 資料表，儲存團隊成員關聯與貢獻積分
- **Scam_Reports_Table**: DynamoDB 資料表，儲存詐騙通報記錄與團隊關聯
- **First_Reporter_Rule**: 首位通報者規則，同一 URL 僅首位通報者所屬團隊獲得積分
- **Risk_Multiplier**: 風險倍數機制，極高風險 (risk_score >= 9) 的通報給予倍數積分
- **Team_Quest**: 團隊任務，達成特定條件後給予額外獎勵積分

## Requirements

### Requirement 1: 建立團隊

**User Story:** 身為使用者，我想要在 LIFF 介面建立一個新團隊，以便邀請好友一起參與詐騙通報競賽。

#### Acceptance Criteria

1. WHEN 使用者在 LIFF_Client 點擊「創建團隊」按鈕，THE Team_Collaboration_System SHALL 顯示團隊名稱輸入表單
2. WHEN 使用者提交有效的團隊名稱（1-30 字元），THE Team_Collaboration_System SHALL 產生唯一的 Team_ID
3. WHEN Team_ID 產生成功，THE Team_Collaboration_System SHALL 將該使用者的 LINE_UID 設定為 Team_Leader
4. THE Team_Collaboration_System SHALL 將新團隊資料寫入 Teams_Table，包含 Team_ID、團隊名稱、Team_Leader 的 LINE_UID、建立時間與初始積分 0
5. WHEN 團隊建立完成，THE LIFF_Client SHALL 顯示成功訊息並導向團隊管理頁面
6. IF 使用者已經是某個團隊的 Team_Leader，THEN THE Team_Collaboration_System SHALL 拒絕建立新團隊並顯示錯誤訊息「您已經是隊長，無法建立多個團隊」
7. IF 團隊名稱為空或超過 30 字元，THEN THE Team_Collaboration_System SHALL 顯示驗證錯誤訊息

### Requirement 2: 邀請好友加入團隊

**User Story:** 身為團隊隊長，我想要透過 LINE 邀請好友加入我的團隊，以便擴大團隊規模並增加通報能量。

#### Acceptance Criteria

1. WHEN Team_Leader 在 LIFF_Client 點擊「邀請隊員」按鈕，THE Team_Collaboration_System SHALL 呼叫 ShareTargetPicker API
2. WHEN ShareTargetPicker 開啟，THE LIFF_Client SHALL 顯示 Team_Leader 的 LINE 好友清單
3. WHEN Team_Leader 選擇一位或多位好友並確認，THE Team_Collaboration_System SHALL 產生包含 Team_ID 參數的專屬 LIFF URL
4. THE Team_Collaboration_System SHALL 建立 Flex_Message 邀請卡片，包含團隊名稱、隊長暱稱、當前成員數與加入按鈕
5. THE LIFF_Client SHALL 透過 ShareTargetPicker 發送 Flex_Message 給選定的好友
6. WHEN 邀請訊息發送成功，THE LIFF_Client SHALL 顯示「邀請已發送」確認訊息
7. IF Team_Leader 不屬於任何團隊，THEN THE Team_Collaboration_System SHALL 拒絕邀請操作並顯示錯誤訊息「您尚未建立團隊」

### Requirement 3: 加入團隊

**User Story:** 身為收到邀請的使用者，我想要點擊邀請卡片加入團隊，以便與朋友一起參與詐騙通報活動。

#### Acceptance Criteria

1. WHEN 使用者點擊 Flex_Message 中的加入按鈕，THE LIFF_Client SHALL 開啟並解析 URL 中的 Team_ID 參數
2. WHEN Team_ID 解析成功，THE Team_Collaboration_System SHALL 從 Teams_Table 查詢該團隊資訊
3. IF 團隊不存在，THEN THE LIFF_Client SHALL 顯示錯誤訊息「團隊不存在或已解散」
4. IF 團隊存在，THEN THE LIFF_Client SHALL 顯示確認對話框，包含團隊名稱與當前成員數
5. WHEN 使用者點擊「確認加入」，THE Team_Collaboration_System SHALL 將該使用者的 LINE_UID 寫入 Team_Members_Table
6. THE Team_Collaboration_System SHALL 記錄加入時間與初始 Contribution_Points 為 0
7. WHEN 加入操作完成，THE LIFF_Client SHALL 顯示「成功加入團隊」訊息並導向團隊頁面
8. IF 使用者已經是該團隊成員，THEN THE Team_Collaboration_System SHALL 顯示訊息「您已經是團隊成員」
9. IF 使用者已經是其他團隊成員，THEN THE Team_Collaboration_System SHALL 顯示錯誤訊息「您已加入其他團隊，請先退出」

### Requirement 4: 詐騙通報與團隊積分計算

**User Story:** 身為團隊成員，我想要透過 LINE Bot 通報詐騙 URL 時自動為團隊累積積分，以便提升團隊排名。

#### Acceptance Criteria

1. WHEN Team_Member 透過 LINE Bot 發送包含 URL 的訊息，THE Team_Collaboration_System SHALL 識別該成員的 LINE_UID
2. THE Team_Collaboration_System SHALL 從 Team_Members_Table 查詢該成員所屬的 Team_ID
3. WHEN Bedrock_AI 完成詐騙分析並回傳 risk_score，THE Team_Collaboration_System SHALL 檢查該 URL 是否已被通報
4. IF 該 URL 尚未被通報，THEN THE Team_Collaboration_System SHALL 將 risk_score 加入該團隊的 Team_Points
5. THE Team_Collaboration_System SHALL 將 risk_score 加入該成員的 Contribution_Points
6. THE Team_Collaboration_System SHALL 將通報記錄寫入 Scam_Reports_Table，包含 URL、risk_score、通報者 LINE_UID、Team_ID 與通報時間
7. IF 該 URL 已被其他使用者通報，THEN THE Team_Collaboration_System SHALL 不增加任何積分（First_Reporter_Rule）
8. WHEN 積分更新完成，THE Team_Collaboration_System SHALL 更新 Teams_Table 中的 Team_Points
9. THE Team_Collaboration_System SHALL 更新 Team_Members_Table 中該成員的 Contribution_Points

### Requirement 5: 極高風險通報倍數獎勵

**User Story:** 身為團隊成員，我想要通報極高風險的詐騙內容時獲得倍數積分，以便鼓勵高品質通報。

#### Acceptance Criteria

1. WHEN Bedrock_AI 回傳的 risk_score 大於或等於 9，THE Team_Collaboration_System SHALL 啟用 Risk_Multiplier 機制
2. THE Team_Collaboration_System SHALL 計算獎勵積分為 risk_score 乘以 2
3. THE Team_Collaboration_System SHALL 將獎勵積分加入團隊的 Team_Points
4. THE Team_Collaboration_System SHALL 將獎勵積分加入通報者的 Contribution_Points
5. WHEN 倍數獎勵計算完成，THE Team_Collaboration_System SHALL 在通報記錄中標記 multiplier_applied 為 true

### Requirement 6: 團隊排行榜顯示

**User Story:** 身為使用者，我想要在 Scam_Hero_Dashboard 查看團隊排行榜，以便了解各團隊的表現與排名。

#### Acceptance Criteria

1. WHEN 使用者開啟 Scam_Hero_Dashboard 的團隊排行榜頁面，THE Team_Collaboration_System SHALL 從 Teams_Table 查詢所有團隊
2. THE Team_Collaboration_System SHALL 依據 Team_Points 降序排列團隊
3. THE Scam_Hero_Dashboard SHALL 顯示前 10 名團隊，包含排名、團隊名稱、總通報次數與總積分
4. WHEN 使用者點擊某個團隊，THE Scam_Hero_Dashboard SHALL 顯示該團隊的詳細資訊頁面
5. THE Scam_Hero_Dashboard SHALL 在詳細頁面顯示團隊成員清單，包含成員暱稱與 Contribution_Points
6. THE Scam_Hero_Dashboard SHALL 依據 Contribution_Points 降序排列成員，標示「通報王」給貢獻最高的成員

### Requirement 7: 團隊成員貢獻度統計

**User Story:** 身為團隊隊長，我想要查看每位成員的貢獻度，以便了解團隊內部的活躍程度。

#### Acceptance Criteria

1. WHEN Team_Leader 在 LIFF_Client 開啟團隊管理頁面，THE Team_Collaboration_System SHALL 從 Team_Members_Table 查詢該團隊所有成員
2. THE Team_Collaboration_System SHALL 計算每位成員的通報次數與 Contribution_Points
3. THE LIFF_Client SHALL 顯示成員清單，包含成員暱稱、通報次數與貢獻積分
4. THE LIFF_Client SHALL 依據 Contribution_Points 降序排列成員
5. THE LIFF_Client SHALL 標示貢獻最高的成員為「MVP」

### Requirement 8: 團隊任務系統

**User Story:** 身為團隊成員，我想要完成團隊任務以獲得額外獎勵積分，以便加速團隊排名提升。

#### Acceptance Criteria

1. THE Team_Collaboration_System SHALL 定義 Team_Quest「單日通報 5 則 URL」
2. WHEN 團隊在單日內累積 5 則有效通報，THE Team_Collaboration_System SHALL 檢測任務完成條件
3. WHEN 任務條件滿足，THE Team_Collaboration_System SHALL 給予該團隊額外 50 點獎勵積分
4. THE Team_Collaboration_System SHALL 將任務完成記錄寫入 Teams_Table 的 completed_quests 欄位
5. THE Team_Collaboration_System SHALL 透過 LINE Bot 發送任務完成通知給 Team_Leader
6. IF 團隊已完成該任務，THEN THE Team_Collaboration_System SHALL 不重複給予獎勵

### Requirement 9: 詐騙趨勢地圖

**User Story:** 身為使用者，我想要在 Scam_Hero_Dashboard 查看所有團隊通報的詐騙網域趨勢，以便了解當前最活躍的詐騙類型。

#### Acceptance Criteria

1. WHEN 使用者開啟 Scam_Hero_Dashboard 的詐騙地圖頁面，THE Team_Collaboration_System SHALL 從 Scam_Reports_Table 查詢所有通報記錄
2. THE Team_Collaboration_System SHALL 提取每則通報的網域名稱（從 URL 解析）
3. THE Team_Collaboration_System SHALL 統計每個網域的通報次數
4. THE Scam_Hero_Dashboard SHALL 顯示前 20 名最頻繁通報的網域，包含網域名稱、通報次數與平均風險評分
5. THE Scam_Hero_Dashboard SHALL 依據通報次數降序排列網域

### Requirement 10: 團隊 ID 傳輸安全驗證

**User Story:** 身為系統管理員，我想要確保 LIFF URL 中的 Team_ID 參數經過加密或校驗，以便防止惡意使用者偽造邀請連結洗分。

#### Acceptance Criteria

1. WHEN Team_Collaboration_System 產生邀請 LIFF URL，THE Team_Collaboration_System SHALL 使用 HMAC-SHA256 演算法對 Team_ID 進行簽章
2. THE Team_Collaboration_System SHALL 將簽章附加在 URL 參數中（格式：?team_id=xxx&signature=yyy）
3. WHEN LIFF_Client 接收到邀請 URL，THE Team_Collaboration_System SHALL 驗證 signature 是否與 Team_ID 匹配
4. IF 簽章驗證失敗，THEN THE Team_Collaboration_System SHALL 拒絕加入請求並顯示錯誤訊息「無效的邀請連結」
5. THE Team_Collaboration_System SHALL 使用儲存在環境變數中的密鑰進行簽章與驗證

### Requirement 11: 重複通報檢測

**User Story:** 身為系統管理員，我想要確保同一 URL 僅首位通報者獲得積分，以便鼓勵快速通報並防止重複洗分。

#### Acceptance Criteria

1. WHEN Team_Collaboration_System 接收到詐騙通報，THE Team_Collaboration_System SHALL 從 Scam_Reports_Table 查詢該 URL 是否已存在
2. THE Team_Collaboration_System SHALL 使用 URL 的標準化形式進行比對（移除 query parameters 與 trailing slash）
3. IF 該 URL 已存在於 Scam_Reports_Table，THEN THE Team_Collaboration_System SHALL 不增加任何積分
4. THE Team_Collaboration_System SHALL 在 LINE Bot 回覆中標示「此 URL 已被通報」
5. IF 該 URL 不存在，THEN THE Team_Collaboration_System SHALL 將通報記錄寫入 Scam_Reports_Table 並計算積分

### Requirement 12: 資料庫表格結構

**User Story:** 身為系統開發者，我想要定義清晰的資料庫表格結構，以便支援團隊協作功能的所有查詢與更新操作。

#### Acceptance Criteria

1. THE Team_Collaboration_System SHALL 建立 Teams_Table，包含欄位：team_id (Primary Key)、team_name、leader_uid、total_points、created_at、completed_quests
2. THE Team_Collaboration_System SHALL 建立 Team_Members_Table，包含欄位：member_id (Primary Key, 格式：team_id#line_uid)、team_id (GSI Partition Key)、line_uid、contribution_points、joined_at
3. THE Team_Collaboration_System SHALL 建立 Scam_Reports_Table，包含欄位：report_id (Primary Key)、url、normalized_url (GSI Partition Key)、reporter_uid、team_id、risk_score、multiplier_applied、reported_at
4. THE Team_Collaboration_System SHALL 在 Team_Members_Table 建立 Global Secondary Index，使用 team_id 作為 Partition Key
5. THE Team_Collaboration_System SHALL 在 Scam_Reports_Table 建立 Global Secondary Index，使用 normalized_url 作為 Partition Key

