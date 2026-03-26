# Task 3.5 實作總結：加入團隊功能

## 任務描述

在 TeamService 實作 `join_team()` 方法，實現使用者加入團隊的完整功能。

## 實作內容

### 1. 核心功能實作

在 `team_service.py` 中實作了 `join_team()` 方法，包含以下功能：

```python
def join_team(self, team_id: str, member_uid: str, signature: str) -> bool
```

### 2. 功能檢查清單

✅ **驗證 HMAC 簽章**
- 使用 `SecurityService.verify_signature()` 驗證簽章
- 拒絕無效簽章並拋出 `ValueError("無效的邀請連結")`

✅ **檢查團隊是否存在**
- 從 Teams 表查詢 team_id
- 若團隊不存在，拋出 `ValueError("團隊不存在或已解散")`

✅ **檢查使用者是否已是成員**
- 查詢 TeamMembers 表檢查 member_id 是否存在
- 若已是成員，拋出 `ValueError("您已經是團隊成員")`

✅ **檢查使用者是否屬於其他團隊**
- 使用 LineUidIndex GSI 查詢使用者是否已在其他團隊
- 若已在其他團隊，拋出 `ValueError("您已加入其他團隊，請先退出")`

✅ **寫入 TeamMembers 表**
- 建立 TeamMember 物件
- 寫入所有必要欄位：
  - `member_id`: `{team_id}#{line_uid}` 格式
  - `team_id`: 團隊 ID
  - `line_uid`: 成員 LINE UID
  - `contribution_points`: 初始值 0
  - `report_count`: 初始值 0
  - `joined_at`: 加入時間（ISO 8601 格式）
  - `is_leader`: False

✅ **更新團隊成員數**
- 使用 DynamoDB 原子性更新 `member_count`
- 使用 `UpdateExpression='SET member_count = member_count + :inc'`

### 3. 測試驗證

建立了完整的測試檔案：

#### `test_join_team.py`
包含 7 個測試案例：
1. ✅ 成功加入團隊
2. ✅ 拒絕無效簽章
3. ✅ 拒絕加入不存在的團隊
4. ✅ 拒絕重複加入同一團隊
5. ✅ 拒絕加入其他團隊（使用者已在另一團隊）
6. ✅ 拒絕隊長重複加入
7. ✅ 多位成員依序加入團隊

#### `demo_join_team.py`
示範腳本展示完整的加入團隊流程，包含：
- 建立測試團隊
- 產生邀請連結
- 新成員加入
- 錯誤情境測試

#### `verify_join_team.py`
驗證腳本確認所有需求都已正確實作：
- ✅ 驗證 HMAC 簽章
- ✅ 檢查團隊是否存在
- ✅ 檢查使用者是否已是成員
- ✅ 檢查使用者是否屬於其他團隊
- ✅ 寫入 TeamMembers 表
- ✅ 更新團隊成員數

### 4. 執行結果

所有測試都通過：

```
======================================================================
🔍 驗證 Task 3.5: 實作加入團隊功能
======================================================================

✅ 需求檢查清單：
----------------------------------------------------------------------

1️⃣  驗證 HMAC 簽章
   ✅ 正確驗證 HMAC 簽章並拒絕無效簽章

2️⃣  檢查團隊是否存在
   ✅ 正確檢查團隊是否存在

3️⃣  檢查使用者是否已是成員
   ✅ 正確檢查使用者是否已是成員

4️⃣  檢查使用者是否屬於其他團隊
   ✅ 正確檢查使用者是否屬於其他團隊

5️⃣  寫入 TeamMembers 表
   ✅ 正確寫入 TeamMembers 表，包含所有必要欄位

6️⃣  更新團隊成員數
   ✅ 正確更新 member_count: 3

======================================================================
✅ Task 3.5 驗證完成！
======================================================================
```

## 符合的需求

此實作滿足以下需求：

- **Requirement 3.2**: 從 Teams_Table 查詢該團隊資訊
- **Requirement 3.3**: 檢查團隊是否存在
- **Requirement 3.5**: 將使用者的 LINE_UID 寫入 Team_Members_Table
- **Requirement 3.6**: 記錄加入時間與初始 Contribution_Points 為 0
- **Requirement 3.8**: 檢查使用者是否已經是該團隊成員
- **Requirement 3.9**: 檢查使用者是否已經是其他團隊成員
- **Requirement 10.3**: 驗證 signature 是否與 Team_ID 匹配
- **Requirement 10.4**: 簽章驗證失敗時拒絕加入請求

## 技術細節

### 錯誤處理
- 所有錯誤都拋出 `ValueError` 並附帶清晰的中文錯誤訊息
- 使用 try-except 處理 DynamoDB 查詢異常

### 資料一致性
- 使用 DynamoDB 原子性更新確保 `member_count` 正確
- 即使 `member_count` 更新失敗，成員資料仍已寫入（記錄警告但不回滾）

### 安全性
- 使用 HMAC-SHA256 簽章驗證邀請連結
- 使用 LineUidIndex GSI 檢查跨團隊加入

## 檔案清單

### 修改的檔案
- `team_service.py`: 新增 `join_team()` 方法

### 新增的檔案
- `test_join_team.py`: 完整的單元測試
- `demo_join_team.py`: 功能示範腳本
- `verify_join_team.py`: 需求驗證腳本
- `TASK_3.5_IMPLEMENTATION_SUMMARY.md`: 本文件

## 下一步

Task 3.5 已完成，可以繼續執行：
- Task 3.6: 撰寫加入團隊的 property test
- Task 3.7: 實作團隊資訊查詢功能

## 結論

✅ Task 3.5 已成功完成，所有需求都已正確實作並通過驗證！
