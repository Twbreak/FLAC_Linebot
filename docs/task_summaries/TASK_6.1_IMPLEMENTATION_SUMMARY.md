# Task 6.1 實作總結：建立團隊 API

## 任務描述
實作 POST /api/teams/create 端點，整合 TeamService.create_team() 方法，並處理各種錯誤情況。

## 實作內容

### 1. API 端點實作 (main.py)

新增 `POST /api/teams/create` 端點，功能包括：

- **輸入驗證**：
  - 檢查團隊名稱是否為空（去除空白後）
  - 檢查團隊名稱長度是否超過 30 字元
  - Pydantic 模型自動驗證資料格式

- **業務邏輯整合**：
  - 呼叫 `TeamService.create_team()` 建立團隊
  - 呼叫 `TeamService.invite_member()` 產生邀請連結
  - 回傳團隊 ID、名稱與邀請 URL

- **錯誤處理**：
  - 400: 團隊名稱為空或無效
  - 409: 使用者已是其他團隊的隊長
  - 422: Pydantic 驗證失敗（例如名稱過長）
  - 500: 其他未預期的錯誤

### 2. 程式碼修改

#### main.py 修改點：

1. **匯入 TeamService 與 CreateTeamRequest**：
```python
from models import ScamDetectionRecord, UserHistory, LeaderboardEntry, CreateTeamRequest
from team_service import TeamService
```

2. **初始化 TeamService**：
```python
team_service = TeamService()
```

3. **新增 API 端點**：
```python
@app.post("/api/teams/create")
async def create_team(request: CreateTeamRequest):
    # 驗證團隊名稱
    team_name = request.team_name.strip()
    
    if not team_name:
        raise HTTPException(status_code=400, detail="團隊名稱不可為空")
    
    if len(team_name) > 30:
        raise HTTPException(status_code=400, detail="團隊名稱不可超過 30 字元")
    
    try:
        # 建立團隊
        team = team_service.create_team(
            leader_uid=request.leader_uid,
            team_name=team_name
        )
        
        # 產生邀請連結
        invite_url = team_service.invite_member(
            team_id=team.team_id,
            inviter_uid=request.leader_uid
        )
        
        return {
            "team_id": team.team_id,
            "team_name": team.team_name,
            "invite_url": invite_url
        }
        
    except ValueError as e:
        error_msg = str(e)
        if "已經是隊長" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"建立團隊失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立團隊失敗: {str(e)}")
```

## 測試結果

### 單元測試 (test_create_team_unit.py)

所有測試通過 ✅：

1. **test_create_team_success**: 成功建立團隊
   - 驗證回傳包含 team_id、team_name、invite_url
   - 驗證 team_id 是有效的 UUID 格式
   - 驗證 invite_url 包含必要參數（team_id、signature）

2. **test_create_team_empty_name**: 空白團隊名稱
   - 回傳 400 錯誤
   - 錯誤訊息：「團隊名稱不可為空」

3. **test_create_team_name_too_long**: 團隊名稱過長
   - 回傳 422 錯誤（Pydantic 驗證）
   - 正確拒絕超過 30 字元的名稱

4. **test_create_team_duplicate_leader**: 重複建立團隊
   - 第一次建立成功（200）
   - 第二次建立失敗（409）
   - 錯誤訊息：「您已經是隊長，無法建立多個團隊」

5. **test_create_team_valid_name_length**: 有效的團隊名稱長度
   - 1 字元名稱：成功（200）
   - 30 字元名稱：成功（200）

### 測試執行結果

```
============================================================
建立團隊 API 單元測試
============================================================

=== 測試 1: 成功建立團隊 ===
狀態碼: 200
✅ team_id 是有效的 UUID
✅ 測試通過

=== 測試 2: 空白團隊名稱 ===
狀態碼: 400
✅ 測試通過

=== 測試 3: 團隊名稱過長 ===
狀態碼: 422
✅ 測試通過（Pydantic 驗證）

=== 測試 4: 重複建立團隊 ===
第一次建立 - 狀態碼: 200
第二次建立 - 狀態碼: 409
✅ 測試通過

=== 測試 5: 有效的團隊名稱長度 ===
1 字元 - 狀態碼: 200
30 字元 - 狀態碼: 200
✅ 測試通過

============================================================
🎉 所有測試通過！
============================================================
```

## API 使用範例

### 請求範例

```bash
curl -X POST http://localhost:8080/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "leader_uid": "U1234567890",
    "team_name": "防詐先鋒隊"
  }'
```

### 成功回應 (200)

```json
{
  "team_id": "5ad7f5e1-29b0-4acb-ab31-9f3f9ae1b36c",
  "team_name": "防詐先鋒隊",
  "invite_url": "https://liff.line.me/2009609029-RlBZuNs2?team_id=5ad7f5e1-29b0-4acb-ab31-9f3f9ae1b36c&signature=c7cbc668c13b25c3011f186cd7c8a6ab46b9b06cc9ec9cb9a1eccbbfb85a4aee"
}
```

### 錯誤回應範例

#### 空白名稱 (400)
```json
{
  "detail": "團隊名稱不可為空"
}
```

#### 名稱過長 (422)
```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "team_name"],
      "msg": "String should have at most 30 characters",
      "input": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
      "ctx": {"max_length": 30}
    }
  ]
}
```

#### 重複隊長 (409)
```json
{
  "detail": "您已經是隊長，無法建立多個團隊"
}
```

## 滿足的需求

- ✅ **Requirement 1.1**: 使用者可在 LIFF 介面建立團隊
- ✅ **Requirement 1.5**: 團隊建立完成後顯示成功訊息
- ✅ **Requirement 1.6**: 拒絕已是隊長的使用者建立新團隊
- ✅ **Requirement 1.7**: 驗證團隊名稱長度（1-30 字元）

## 相關檔案

- `main.py`: API 端點實作
- `team_service.py`: 團隊服務業務邏輯
- `models.py`: CreateTeamRequest 資料模型
- `test_create_team_unit.py`: 單元測試
- `demo_create_team_api.py`: 演示腳本（需要伺服器運行）

## 下一步

Task 6.1 已完成，可以繼續執行：
- Task 6.2: 撰寫建立團隊 API 的 unit tests（已完成）
- Task 6.3: 實作加入團隊 API
- Task 6.4: 實作團隊資訊查詢 API

## 注意事項

1. **Pydantic 驗證優先**：Pydantic 會在請求到達端點前驗證資料，因此某些驗證錯誤會回傳 422 而非 400
2. **錯誤處理順序**：先檢查 HTTPException，避免被通用 Exception 處理器捕獲
3. **團隊名稱處理**：使用 `.strip()` 移除前後空白，確保驗證準確性
4. **UUID 格式**：team_id 使用標準 UUID v4 格式，確保唯一性
5. **邀請連結安全**：包含 HMAC-SHA256 簽章，防止偽造

## 實作時間

- 實作時間：約 30 分鐘
- 測試時間：約 15 分鐘
- 總計：約 45 分鐘
