# Task 3.3 實作總結：邀請連結產生功能

## 任務描述

實作 TeamService 的 `invite_member()` 方法，產生包含 team_id 與 HMAC 簽章的 LIFF URL，整合 SecurityService 進行簽章。

## 實作內容

### 1. 核心功能實作

在 `team_service.py` 中實作了 `invite_member()` 方法：

```python
def invite_member(self, team_id: str, inviter_uid: str) -> str:
    """
    產生邀請連結（含 HMAC 簽章）
    
    Args:
        team_id: 團隊唯一識別碼
        inviter_uid: 邀請者的 LINE UID（用於驗證權限）
        
    Returns:
        str: 包含 team_id 與 signature 的 LIFF URL
        
    Raises:
        ValueError: 當團隊不存在或邀請者不是團隊成員時
    """
```

### 2. 功能特點

#### 2.1 團隊驗證
- 驗證團隊是否存在於 Teams 表
- 若團隊不存在，拋出 ValueError: "團隊不存在或已解散"

#### 2.2 成員權限驗證
- 驗證邀請者是否為團隊成員
- 若非成員，拋出 ValueError: "您不是該團隊成員，無法邀請他人"

#### 2.3 HMAC 簽章產生
- 整合 SecurityService 產生 HMAC-SHA256 簽章
- 使用 team_id 作為簽章訊息
- 確保邀請連結無法被偽造或竄改

#### 2.4 LIFF URL 組合
- 從環境變數讀取 LIFF_ID_TEAM_JOIN（預設值：2009609029-RlBZuNs2）
- 組合格式：`https://liff.line.me/{liff_id}?team_id={team_id}&signature={signature}`

### 3. 測試驗證

建立了完整的測試套件 `test_invite_member.py`，包含 4 個測試案例：

#### 測試 1：成功產生邀請連結
- ✅ 驗證 URL 格式正確
- ✅ 驗證包含 team_id 參數
- ✅ 驗證包含 signature 參數
- ✅ 驗證簽章有效性

#### 測試 2：團隊不存在時拒絕產生邀請連結
- ✅ 正確拋出 ValueError
- ✅ 錯誤訊息包含 "團隊不存在"

#### 測試 3：非團隊成員無法產生邀請連結
- ✅ 正確拋出 ValueError
- ✅ 錯誤訊息包含 "不是該團隊成員"

#### 測試 4：不同團隊產生不同的簽章
- ✅ 驗證簽章唯一性
- ✅ 確保不同 team_id 產生不同簽章

### 4. 測試結果

```
============================================================
🎉 所有測試通過！
============================================================
```

所有 4 個測試案例均通過，驗證了：
- 邀請連結產生功能正常運作
- HMAC 簽章正確產生且可驗證
- 錯誤處理機制完善
- 權限驗證機制有效

### 5. 示範程式

建立了 `demo_invite_member.py` 展示完整使用流程：

1. 建立測試團隊
2. 產生邀請連結
3. 解析 URL 參數
4. 驗證 HMAC 簽章
5. 展示使用情境說明

## 符合需求

### Requirements 2.3
✅ **邀請連結產生**：實作了產生包含 team_id 參數的專屬 LIFF URL

### Requirements 10.2
✅ **HMAC 簽章**：使用 HMAC-SHA256 演算法對 team_id 進行簽章，並附加在 URL 參數中

## 設計文件對應

### Component: TeamService.invite_member()
✅ 完整實作設計文件中定義的方法簽名與功能

### Integration: SecurityService
✅ 正確整合 SecurityService.generate_signature() 方法

### URL Format
✅ 產生的 URL 格式符合設計文件規範：
```
https://liff.line.me/{liff_id}?team_id={team_id}&signature={signature}
```

## 檔案清單

### 實作檔案
- `team_service.py` - 新增 invite_member() 方法

### 測試檔案
- `test_invite_member.py` - 完整測試套件（4 個測試案例）
- `demo_invite_member.py` - 功能示範程式

### 文件檔案
- `TASK_3.3_IMPLEMENTATION_SUMMARY.md` - 本實作總結

## 使用範例

```python
from team_service import TeamService

# 建立 TeamService 實例
team_service = TeamService()

# 產生邀請連結
invite_url = team_service.invite_member(
    team_id="550e8400-e29b-41d4-a716-446655440000",
    inviter_uid="U1234567890"
)

print(invite_url)
# 輸出：https://liff.line.me/2009609029-RlBZuNs2?team_id=550e8400-e29b-41d4-a716-446655440000&signature=abc123...
```

## 安全性考量

1. **HMAC 簽章**：使用 HMAC-SHA256 確保邀請連結無法被偽造
2. **權限驗證**：只有團隊成員才能產生邀請連結
3. **團隊驗證**：確保團隊存在才能產生邀請連結
4. **環境變數**：LIFF_ID 可透過環境變數配置，提高靈活性

## 後續整合

此功能已準備好整合至：
1. FastAPI 端點（`/api/teams/invite`）
2. LIFF 前端介面（team.html）
3. LINE ShareTargetPicker 流程

## 結論

Task 3.3 已完整實作並通過所有測試。邀請連結產生功能正常運作，符合設計文件規範與需求定義，並具備完善的錯誤處理與安全性機制。
