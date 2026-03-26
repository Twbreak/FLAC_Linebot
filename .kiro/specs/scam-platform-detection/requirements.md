# 需求文件

## 簡介

本功能旨在增強 Line Bot 詐騙偵測系統的警示能力。系統已能識別詐騙類別（如假投資詐騙、解除分期付款詐騙、假交友詐騙等），本功能將根據已識別的詐騙類別，自動從 165 打詐儀錶板 (https://165dashboard.tw) 或政府開放資料平台查詢該類型詐騙的統計數據（案件數、被騙總金額、平均損失）以及具體的歷史事件案例，將這些資訊整合到現有回覆訊息中，增強警示效果，提高民眾警戒心。

## 術語表

- **System**: Line Bot 詐騙偵測系統
- **Scam_Category**: 詐騙類別，由現有 Bedrock AI 模組識別（如：假投資詐騙、解除分期付款詐騙、假交友詐騙等）
- **Category_Statistics_Fetcher**: 類別統計擷取模組，負責根據詐騙類別從 165 打詐儀錶板或政府開放資料平台取得該類型詐騙的統計數據
- **Case_Repository**: 案例儲存庫，儲存各類型詐騙的歷史事件案例
- **Alert_Formatter**: 警示訊息格式化模組，負責將類別統計數據與案例整合至現有回覆訊息
- **165_Dashboard**: 165 打詐儀錶板網站 (https://165dashboard.tw)
- **Open_Data_Platform**: 政府開放資料平台，提供 CSV 格式的詐騙案件資料集
- **Category_Mapping**: 類別對應表，將系統識別的詐騙類別對應到 165 資料集的分類欄位
- **Statistics_Cache**: 統計數據快取，用於暫存從外部來源取得的統計數據以提升效能

## 需求

### 需求 1：根據詐騙類別查詢統計數據

**使用者故事：** 作為一名 Line Bot 使用者，我希望在收到詐騙風險評估報告時，能看到該詐騙類別的統計數據（案件數、被騙總金額、平均損失），以便我了解該類型詐騙的嚴重程度。

#### 驗收標準

1. WHEN Bedrock AI 識別出詐騙類別，THE Category_Statistics_Fetcher SHALL 從 165_Dashboard 或 Open_Data_Platform 擷取該類別的統計數據
2. THE Category_Statistics_Fetcher SHALL 提供以下統計數據：近期案件數、總損失金額（新台幣）、平均財損金額（新台幣）
3. THE Category_Mapping SHALL 將系統識別的詐騙類別對應到 165 資料集的分類欄位
4. WHEN 外部數據來源無法連線，THE Category_Statistics_Fetcher SHALL 回傳快取的統計數據
5. WHEN 快取數據不存在且外部來源無法連線，THE Category_Statistics_Fetcher SHALL 回傳預設訊息而不中斷主流程
6. THE Category_Statistics_Fetcher SHALL 在 5 秒內完成數據擷取，若超時則使用快取數據

### 需求 2：提供該類型詐騙的歷史事件案例

**使用者故事：** 作為一名 Line Bot 使用者，我希望看到該詐騙類別的具體歷史事件案例，以便我更清楚了解詐騙手法並提高警覺。

#### 驗收標準

1. WHEN 詐騙類別被識別出來，THE Case_Repository SHALL 提供至少一則該類別的歷史詐騙事件案例
2. THE Case_Repository SHALL 儲存每個詐騙類別至少 3 則歷史案例
3. WHEN 案例數量超過 1 則，THE Case_Repository SHALL 隨機選擇一則案例回傳
4. 每則案例 SHALL 包含以下資訊：案例標題、詐騙手法簡述、受害金額範圍
5. THE Case_Repository SHALL 每週從 165_Dashboard 或 Open_Data_Platform 更新案例資料

### 需求 3：整合類別統計資訊至警示訊息

**使用者故事：** 作為一名 Line Bot 使用者，我希望在收到詐騙風險評估報告時，同時看到該類別的統計數據與歷史案例，以便我獲得更完整的警示資訊。

#### 驗收標準

1. WHEN 詐騙類別被識別且統計數據與案例可用，THE Alert_Formatter SHALL 將類別統計資訊整合至回覆訊息中
2. THE Alert_Formatter SHALL 在現有的風險評估報告後附加類別警示區塊
3. 類別警示區塊 SHALL 包含：詐騙類別名稱、近期案件數、總損失金額、平均財損、一則歷史案例
4. WHEN 統計數據或案例不可用，THE Alert_Formatter SHALL 僅顯示原有的風險評估報告
5. THE Alert_Formatter SHALL 使用清晰的視覺分隔符號區分風險評估與類別警示區塊

### 需求 4：資料來源整合與解析

**使用者故事：** 作為系統管理員，我希望系統能從 165 打詐儀錶板或政府開放資料平台取得 CSV 格式的詐騙資料集並正確解析，以便系統能提供準確的統計數據。

#### 驗收標準

1. THE Category_Statistics_Fetcher SHALL 支援從 Open_Data_Platform 下載 CSV 格式的詐騙資料集
2. THE Category_Statistics_Fetcher SHALL 解析 CSV 檔案並提取以下欄位：案件日期、詐騙類別、損失金額、案件描述
3. WHEN CSV 檔案格式不正確或欄位缺失，THE Category_Statistics_Fetcher SHALL 記錄錯誤並使用快取數據
4. THE Category_Statistics_Fetcher SHALL 支援 UTF-8 與 Big5 編碼的 CSV 檔案
5. THE Category_Statistics_Fetcher SHALL 過濾掉損失金額為 0 或空值的記錄

### 需求 5：詐騙類別對應表維護

**使用者故事：** 作為系統管理員，我希望能維護詐騙類別對應表，將系統識別的類別對應到 165 資料集的分類欄位，以便系統能正確查詢統計數據。

#### 驗收標準

1. THE Category_Mapping SHALL 儲存於獨立的設定檔案中
2. THE System SHALL 在啟動時載入 Category_Mapping 設定檔案
3. WHEN Category_Mapping 設定檔案更新，THE System SHALL 在下次啟動時套用新的對應規則
4. THE Category_Mapping SHALL 支援一對多對應（一個系統類別可對應多個 165 分類）
5. THE Category_Mapping 設定檔案 SHALL 使用 JSON 格式以便於編輯

### 需求 6：效能與快取機制

**使用者故事：** 作為一名 Line Bot 使用者，我希望系統能快速回應我的查詢，即使在外部數據來源回應緩慢時也能獲得即時的警示資訊。

#### 驗收標準

1. THE Statistics_Cache SHALL 使用 DynamoDB 儲存快取數據
2. THE Statistics_Cache SHALL 為每筆快取數據記錄更新時間戳記
3. WHEN 快取數據的年齡超過 24 小時，THE Category_Statistics_Fetcher SHALL 嘗試從外部來源更新數據
4. WHEN 外部來源回應時間超過 5 秒，THE Category_Statistics_Fetcher SHALL 中斷連線並使用快取數據
5. THE System SHALL 在回覆使用者訊息時總處理時間不超過 10 秒

### 需求 7：錯誤處理與降級機制

**使用者故事：** 作為一名 Line Bot 使用者，我希望即使統計數據擷取失敗，系統仍能提供基本的詐騙風險評估，以便我不會因為部分功能故障而失去警示資訊。

#### 驗收標準

1. WHEN Category_Statistics_Fetcher 發生錯誤，THE System SHALL 繼續執行風險評估並回傳基本報告
2. WHEN Category_Statistics_Fetcher 無法取得統計數據，THE System SHALL 在回覆訊息中省略統計數據區塊
3. WHEN Case_Repository 無法提供案例，THE System SHALL 在回覆訊息中省略案例區塊
4. IF 任何模組發生錯誤，THEN THE System SHALL 記錄錯誤日誌並通知系統管理員
5. THE System SHALL 確保至少回傳基本的風險評估報告給使用者

### 需求 8：資料隱私與安全

**使用者故事：** 作為一名 Line Bot 使用者，我希望我的通報內容與個人資訊受到保護，不會被不當使用或外洩。

#### 驗收標準

1. THE System SHALL 在傳送資料至外部 API 前移除使用者的個人識別資訊
2. THE System SHALL 僅儲存必要的統計數據，不儲存個別使用者的通報內容
3. THE System SHALL 使用 HTTPS 協定與外部數據來源通訊
4. THE System SHALL 遵守 LINE 平台的隱私政策與服務條款
5. THE Statistics_Cache SHALL 設定適當的存取權限，僅允許授權的服務存取
