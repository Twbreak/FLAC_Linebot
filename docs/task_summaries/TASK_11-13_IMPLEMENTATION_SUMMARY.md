# Task 11-13 實作摘要：LIFF 前端頁面

## 任務描述
實作團隊協作系統的 LINE LIFF 前端介面，包含團隊管理、團隊排行榜和詐騙趨勢地圖三個主要頁面。

## 實作內容

### Task 11: 團隊管理頁面

#### 11.1 & 11.2: 團隊管理 HTML & JavaScript (`team.html` + `team.js`)

**功能特色**:
- **LIFF 初始化與登入檢查**: 自動處理 LINE 登入流程
- **三種模式支援**:
  1. 建立團隊模式：使用者尚未加入任何團隊
  2. 團隊管理模式：顯示團隊資訊與成員清單
  3. 加入團隊模式：從邀請連結進入

**建立團隊功能**:
- 團隊名稱輸入（1-30 字元限制）
- 即時字元計數顯示
- 呼叫 `POST /api/teams/create` API
- 建立成功後自動重新載入頁面

**團隊資訊顯示**:
- 團隊名稱、隊長、總積分
- 成員數量、個人貢獻積分
- 成員清單（依貢獻積分降序排序）
- 隊長/MVP 徽章標示

**API 整合**:
- `GET /api/users/{user_id}/team`: 查詢使用者所屬團隊
- `GET /api/teams/{team_id}`: 取得團隊資訊
- `GET /api/teams/{team_id}/members`: 取得成員清單
- `POST /api/teams/create`: 建立團隊
- `POST /api/teams/join`: 加入團隊

#### 11.3: ShareTargetPicker 邀請功能

**實作細節**:
- 檢查 `liff.isApiAvailable('shareTargetPicker')` 可用性
- 呼叫 `GET /api/teams/{team_id}/invite` 取得簽章邀請 URL
- 建立 Flex Message 邀請卡片（包含團隊資訊）
- 使用 `liff.shareTargetPicker()` 發送邀請

**Flex Message 結構**:
```javascript
{
  type: 'flex',
  altText: '團隊邀請',
  contents: {
    type: 'bubble',
    hero: { /* 標題區塊 */ },
    body: { /* 團隊資訊 */ },
    footer: { /* 加入按鈕 */ }
  }
}
```

#### 11.5: 加入團隊頁面

**URL 參數解析**:
- `team_id`: 團隊 ID
- `signature`: HMAC 簽章（防偽造）

**加入流程**:
1. 解析 URL 參數
2. 查詢團隊資訊（驗證團隊存在）
3. 顯示確認對話框
4. 呼叫 `POST /api/teams/join` API
5. 加入成功後導向團隊管理頁面

### Task 12: 團隊排行榜頁面

#### 12.1 & 12.2: 排行榜 HTML & JavaScript (`team-leaderboard.html` + `team-leaderboard.js`)

**功能特色**:
- **前 10 名團隊展示**: 依團隊總積分降序排序
- **排名徽章**: 前三名特殊樣式（🥇🥈🥉）
- **展開/收合功能**: 點擊查看團隊成員詳情
- **成員清單**: 顯示每個成員的貢獻積分與通報次數
- **MVP 標示**: 標示團隊內貢獻最高的成員

**視覺設計**:
- 前三名團隊使用漸層色邊框（金/銀/銅）
- 排名徽章使用圓形設計
- 成員清單使用卡片式排版

**API 整合**:
- `GET /api/leaderboard/teams`: 取得團隊排行榜
- `GET /api/teams/{team_id}/members`: 取得團隊成員清單

**互動功能**:
- 展開/收合團隊成員清單
- 動態載入成員資料（避免初始載入過慢）
- 記錄已展開的團隊（避免重複載入）

### Task 13: 詐騙趨勢地圖頁面

#### 13.1: 趨勢地圖 HTML & JavaScript (`trends.html` + `trends.js`)

**功能特色**:
- **TOP 20 詐騙網域展示**: 依通報次數降序排序
- **統計摘要**: 總網域數、總通報次數、平均風險評分
- **視覺化設計**: 
  - 通報次數進度條（相對於最高通報次數）
  - 風險評分進度條（0-10 分）
  - 風險等級顏色標示（綠/橙/紅）

**風險等級分類**:
- 低風險 (< 4): 綠色
- 中風險 (4-6): 橙色
- 高風險 (≥ 7): 紅色

**API 整合**:
- `GET /api/trends/domains`: 取得詐騙網域趨勢統計

**資料展示**:
- 排名徽章（前三名特殊標示）
- 網域名稱（支援長網域名稱截斷）
- 通報次數與平均風險評分
- 雙進度條視覺化（通報次數 + 風險評分）

## 新增後端 API

### 1. 查詢使用者所屬團隊
```
GET /api/users/{user_id}/team
```

**Response**:
```json
{
  "has_team": true,
  "team_id": "xxx",
  "team_name": "防詐先鋒隊",
  "is_leader": false
}
```

### 2. 取得團隊邀請 URL
```
GET /api/teams/{team_id}/invite?inviter_uid={uid}
```

**Response**:
```json
{
  "invite_url": "https://liff.line.me/xxx?team_id=xxx&signature=xxx"
}
```

## 技術細節

### LIFF SDK 整合
- 使用 LIFF SDK 2.x
- 支援自動登入與登出
- 整合 ShareTargetPicker API
- 處理 LIFF 初始化失敗情況

### 響應式設計
- 使用 Tailwind CSS 框架
- 支援手機與桌面版面
- 使用 `sm:` 前綴處理不同螢幕尺寸

### 錯誤處理
- Loading 狀態顯示
- 錯誤訊息提示
- Toast 通知系統
- 空狀態處理

### 動畫效果
- Fade-in 動畫
- Loading spinner
- Hover 效果
- 平滑過渡

## 檔案結構

```
static/
├── index.html                    # 主儀表板（已更新導航連結）
├── leaderboard.html              # 個人排行榜
├── team.html                     # 團隊管理頁面 ✨ NEW
├── team.js                       # 團隊管理 JS ✨ NEW
├── team-leaderboard.html         # 團隊排行榜頁面 ✨ NEW
├── team-leaderboard.js           # 團隊排行榜 JS ✨ NEW
├── trends.html                   # 詐騙趨勢地圖頁面 ✨ NEW
└── trends.js                     # 詐騙趨勢地圖 JS ✨ NEW
```

## 使用者流程

### 建立團隊流程
1. 使用者開啟 `team.html`
2. 輸入團隊名稱（1-30 字元）
3. 點擊「建立團隊」按鈕
4. 系統建立團隊並設定使用者為隊長
5. 頁面重新載入，顯示團隊管理介面

### 邀請成員流程
1. 隊長點擊「邀請好友加入」按鈕
2. 系統開啟 ShareTargetPicker
3. 隊長選擇要邀請的好友
4. 系統發送 Flex Message 邀請卡片
5. 好友點擊「加入團隊」按鈕
6. 開啟 `team.html?team_id=xxx&signature=xxx`
7. 顯示確認對話框
8. 好友確認加入團隊

### 查看排行榜流程
1. 使用者開啟 `team-leaderboard.html`
2. 系統載入前 10 名團隊
3. 使用者點擊「查看成員」展開團隊詳情
4. 系統載入並顯示成員清單
5. 標示 MVP 成員（貢獻最高）

### 查看趨勢地圖流程
1. 使用者開啟 `trends.html`
2. 系統載入 TOP 20 詐騙網域
3. 顯示統計摘要（總網域數、總通報次數、平均風險）
4. 以視覺化方式展示每個網域的通報次數與風險評分

## 安全性考量

### HMAC 簽章驗證
- 邀請 URL 包含 HMAC-SHA256 簽章
- 後端驗證簽章防止偽造邀請連結
- 簽章包含 team_id 確保連結唯一性

### LIFF 登入驗證
- 所有團隊操作需要 LIFF 登入
- 使用 LINE UID 識別使用者身分
- 排行榜與趨勢地圖可公開查看（不需登入）

## 相關需求
- Requirements 1.1-1.7: 建立團隊
- Requirements 2.1-2.6: 邀請好友加入團隊
- Requirements 3.1-3.9: 加入團隊
- Requirements 6.1-6.6: 團隊排行榜
- Requirements 7.1-7.5: 成員貢獻度展示
- Requirements 9.1-9.5: 詐騙趨勢地圖

## 後續優化建議

### 功能增強
1. 加入團隊搜尋功能
2. 支援團隊解散與退出
3. 加入團隊聊天室功能
4. 支援團隊頭像上傳
5. 加入團隊成就系統

### 效能優化
1. 實作前端快取機制
2. 使用 WebSocket 實現即時更新
3. 圖片懶載入
4. API 請求防抖動

### UX 改善
1. 加入骨架屏（Skeleton Screen）
2. 優化 Loading 動畫
3. 加入下拉刷新功能
4. 支援深色模式

## 完成時間
2026-03-26

## 狀態
✅ 完成並整合至系統
