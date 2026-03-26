# 需求文件

## 簡介

本功能旨在為團隊協作詐騙偵測系統新增一個公開透明的團隊詐騙通報記錄頁面，讓所有使用者可以查看**所有團隊**通報的詐騙訊息，包含通報時間、通報團隊、風險評分、詐騙類別等資訊。這是一個公開的資訊共享平台，讓 A 組可以看到 B、C 組通報的內容，促進跨團隊的資訊透明與協作。

## 術語表

- **Team_Scam_Reports_Page**：團隊詐騙通報記錄頁面，顯示所有團隊通報記錄的公開網頁介面
- **ScamReports_Table**：DynamoDB 資料表，儲存所有詐騙通報記錄
- **Backend_API**：後端 API 服務，負責查詢與回傳所有團隊的通報記錄
- **Frontend_Page**：前端網頁，負責顯示所有團隊的通報記錄清單
- **Public_User**：任何使用者，無需團隊成員身分即可查看所有團隊的通報記錄
- **Report_Record**：單筆詐騙通報記錄，包含 URL、風險評分、類別、通報團隊、通報時間等資訊
- **Teams_Table**：DynamoDB 資料表，儲存團隊資訊，用於顯示團隊名稱

## 需求

### 需求 1：查詢所有團隊通報記錄

**使用者故事：** 身為使用者，我想要查看所有團隊的詐騙通報記錄，以便了解整個社群的通報歷史與詐騙趨勢。

#### 驗收標準

1. WHEN 使用者請求查詢團隊通報記錄，THE Backend_API SHALL 掃描 ScamReports_Table 並篩選出 team_id 不為空的記錄
2. THE Backend_API SHALL 依通報時間降序排列查詢結果
3. WHEN 查詢結果超過 1MB，THE Backend_API SHALL 處理分頁並回傳所有記錄
4. THE Backend_API SHALL 回傳每筆記錄的 report_id、url、risk_score、category、team_id、reported_at、points_earned
5. THE Backend_API SHALL 從 Teams_Table 查詢每個 team_id 對應的 team_name
6. WHEN 查詢失敗，THE Backend_API SHALL 回傳 HTTP 500 錯誤與錯誤訊息

### 需求 2：顯示公開通報記錄清單

**使用者故事：** 身為使用者，我想要在網頁上看到清楚的通報記錄清單，包含各團隊的通報內容，以便快速瀏覽整個社群的詐騙通報資訊。

#### 驗收標準

1. THE Frontend_Page SHALL 顯示所有團隊的通報記錄清單，包含通報時間、團隊名稱、URL、風險評分、詐騙類別、獲得積分
2. THE Frontend_Page SHALL 依通報時間降序排列記錄（最新的在最上方）
3. WHEN URL 長度超過 50 字元，THE Frontend_Page SHALL 截斷並顯示省略符號
4. THE Frontend_Page SHALL 使用顏色標示風險等級（高風險：紅色、中風險：橘色、低風險：綠色）
5. WHEN 通報記錄為空，THE Frontend_Page SHALL 顯示「尚無通報記錄」訊息
6. WHEN API 查詢失敗，THE Frontend_Page SHALL 顯示錯誤訊息
7. THE Frontend_Page SHALL 在每筆記錄顯示通報團隊的名稱

### 需求 3：公開存取設計

**使用者故事：** 身為使用者，我想要無需登入或團隊身分即可查看所有團隊的通報記錄，以便促進資訊透明與跨團隊協作。

#### 驗收標準

1. THE Frontend_Page SHALL 允許任何使用者存取，無需驗證團隊成員身分
2. THE Frontend_Page SHALL 在頁面標題顯示「所有團隊通報記錄」
3. THE Frontend_Page SHALL 提供篩選功能，讓使用者可依團隊名稱篩選記錄
4. THE Frontend_Page SHALL 提供搜尋功能，讓使用者可搜尋特定 URL 或關鍵字
5. WHEN 使用者從 LIFF 環境存取，THE Frontend_Page SHALL 取得使用者的 LINE UID 以提供個人化功能（例如標示自己團隊的通報）

### 需求 4：提供頁面導航

**使用者故事：** 身為使用者，我想要從主選單快速進入通報記錄頁面，以便方便查看所有團隊的通報歷史。

#### 驗收標準

1. THE Frontend_Page SHALL 在主選單新增「所有團隊通報」連結
2. WHEN 使用者點擊「所有團隊通報」連結，THE Frontend_Page SHALL 導航至團隊通報記錄頁面
3. THE Team_Scam_Reports_Page SHALL 提供「返回首頁」按鈕
4. WHEN 使用者點擊「返回首頁」按鈕，THE Team_Scam_Reports_Page SHALL 導航回首頁

### 需求 5：顯示整體通報統計資訊

**使用者故事：** 身為使用者，我想要看到所有團隊的通報統計資訊，以便了解整個社群的詐騙偵測表現。

#### 驗收標準

1. THE Frontend_Page SHALL 在頁面頂部顯示整體通報統計資訊
2. THE Frontend_Page SHALL 顯示總通報數量（所有團隊）
3. THE Frontend_Page SHALL 顯示總獲得積分（所有團隊）
4. THE Frontend_Page SHALL 顯示平均風險評分
5. THE Frontend_Page SHALL 計算並顯示各風險等級的通報數量（高風險、中風險、低風險）
6. THE Frontend_Page SHALL 顯示參與通報的團隊總數
