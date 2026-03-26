# Task 6.3 實作總結：加入團隊 API

## 任務概述

實作 POST /api/teams/join API 端點，整合 TeamService.join_team() 方法，並提供完整的簽章驗證與錯誤處理。

## 實作內容

### 1. API 端點實作 (main.py)

新增 POST /api/teams/join 端點：

```python
@app.post("/api/teams/join")
async def join_team(request: JoinTeamRequest):
    """加入團隊
    
    Request Body:
    {
        "team_id": "550e8400-e29b-41d4-a716-446655440000",
        "member_uid": "U9876543210",
        "signature": "abc123..."
    }
    
    Response:
    {
        "success": true,
        "team_name": "防詐先鋒隊",
        "member_count": 5
    }
    """
```

### 2. 核心功能

#### 2.1 參數驗證
- 驗證 team_id、member_uid、signature 必要參數
- 空字串參數回傳 HTTP 400

#### 2.2 簽章驗證
- 呼叫 TeamService.join_team() 進行 HMAC-SHA256 簽章驗證
- 無效簽章回傳 HTTP 403

#### 2.3 業務邏輯處理
- 檢查團隊是否存在（不存在回傳 HTTP 404）
- 檢查使用者是否已是成員（重複加入回傳 HTTP 409）
- 檢查使用者是否屬於其他團隊（跨團隊加入回傳 HTTP 409）

#### 2.4 成功回應
- 回傳團隊名稱與更新後的成員數量
- HTTP 200 狀態碼

### 3. 錯誤處理映射

| 錯誤情況 | HTTP 狀態碼 | 錯誤訊息 |
|---------|------------|---------|
| 缺少必要參數 | 400 | 缺少必要參數 |
| 無效簽章 | 403 | 無效的邀請連結 |
| 團隊不存在 | 404 | 團隊不存在或已解散 |
| 重複加入 | 409 | 您已經是團隊成員 |
| 跨團隊加入 | 409 | 您已加入其他團隊，請先退出 |
| 其他錯誤 | 500 | 加入團隊失敗: {詳細訊息} |

### 4. 程式碼修改

#### main.py
- 新增 POST /api/teams/join 端點
- 匯入 JoinTeamRequest 模型
- 實作完整的錯誤處理邏輯

## 測試驗證

### 測試檔案
1. `test_join_team_api_unit.py` - 單元測試（不需啟動伺服器）
2. `demo_join_team_api.py` - 示範腳本（需啟動伺服器）

### 測試結果

所有測試通過 ✅

```
✅ 測試 1：成功加入團隊
✅ 測試 2：拒絕無效簽章 (403)
✅ 測試 3：拒絕重複加入同一團隊 (409)
✅ 測試 4：拒絕加入不存在的團隊 (404)
✅ 測試 5：拒絕跨團隊加入 (409)
✅ 測試 6：驗證錯誤訊息到 HTTP 狀態碼的映射
```

### 驗證項目
- ✅ 成功加入團隊
- ✅ 拒絕無效簽章 (403)
- ✅ 拒絕重複加入 (409)
- ✅ 拒絕加入不存在的團隊 (404)
- ✅ 拒絕跨團隊加入 (409)
- ✅ 正確回傳團隊資訊（團隊名稱、成員數量）

## 符合需求

### Requirements 驗證

- ✅ **Requirement 3.1**: 解析 URL 中的 Team_ID 參數
- ✅ **Requirement 3.7**: 顯示加入成功或錯誤訊息
- ✅ **Requirement 10.4**: 驗證簽章，拒絕無效邀請連結

### Design Document 驗證

API 端點完全符合設計文件規格：
- ✅ Request Body 格式正確
- ✅ Response 格式正確
- ✅ 錯誤處理完整
- ✅ HTTP 狀態碼映射正確

## 使用範例

### 成功加入團隊

```bash
curl -X POST http://localhost:8080/api/teams/join \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "970c5e36-8d89-40a8-8d4f-6b2651e45224",
    "member_uid": "U_MEMBER_abc123",
    "signature": "087c693d00248461c07a8d56e1fee6..."
  }'
```

**回應 (200 OK):**
```json
{
  "success": true,
  "team_name": "防詐先鋒隊",
  "member_count": 2
}
```

### 無效簽章

```bash
curl -X POST http://localhost:8080/api/teams/join \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "970c5e36-8d89-40a8-8d4f-6b2651e45224",
    "member_uid": "U_MEMBER_abc123",
    "signature": "invalid_signature"
  }'
```

**回應 (403 Forbidden):**
```json
{
  "detail": "無效的邀請連結"
}
```

## 整合說明

### 與現有系統整合
- 使用現有的 TeamService 進行業務邏輯處理
- 使用現有的 SecurityService 進行簽章驗證
- 使用現有的 DynamoDB 資料表（Teams、TeamMembers）

### 前端整合
LIFF 前端可透過以下方式呼叫 API：

```javascript
async function joinTeam(teamId, memberUid, signature) {
    const response = await fetch('/api/teams/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            team_id: teamId,
            member_uid: memberUid,
            signature: signature
        })
    });
    
    if (response.ok) {
        const data = await response.json();
        alert(`成功加入團隊：${data.team_name}`);
    } else {
        const error = await response.json();
        alert(`加入失敗：${error.detail}`);
    }
}
```

## 後續任務

- [ ] Task 6.4: 撰寫加入團隊 API 的完整單元測試（使用 pytest）
- [ ] Task 6.5: 實作團隊資訊查詢 API (GET /api/teams/{team_id})
- [ ] Task 11.5: 實作 LIFF 加入團隊頁面

## 技術細節

### 依賴項
- FastAPI: Web 框架
- Pydantic: 資料驗證
- TeamService: 團隊管理業務邏輯
- SecurityService: HMAC 簽章驗證

### 安全性
- HMAC-SHA256 簽章驗證防止邀請連結偽造
- 完整的輸入驗證防止注入攻擊
- 詳細的錯誤訊息幫助除錯但不洩漏敏感資訊

### 效能考量
- 使用 DynamoDB GSI (LineUidIndex) 快速查詢使用者所屬團隊
- 原子性更新 member_count 避免競態條件

## 結論

Task 6.3 已完成實作，POST /api/teams/join API 端點功能完整，包含：
- ✅ 完整的簽章驗證
- ✅ 詳細的錯誤處理
- ✅ 正確的 HTTP 狀態碼映射
- ✅ 所有測試通過
- ✅ 符合設計文件規格
- ✅ 滿足需求文件要求

API 已準備好供前端整合使用。
