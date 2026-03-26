# Task 3.7 實作總結

## 任務描述
實作團隊資訊查詢功能，包含：
- 在 TeamService 實作 `get_team_info()` 方法
- 從 Teams 表查詢團隊基本資訊
- 實作 `get_team_members()` 方法，使用 TeamIdIndex GSI 查詢成員清單
- 依 contribution_points 降序排序成員

## 實作內容

### 1. 新增輔助方法 `_convert_decimal_to_int()`
```python
def _convert_decimal_to_int(self, obj):
    """將 Decimal 轉換為 int（DynamoDB 回傳的數字是 Decimal 型別）"""
```
- 遞迴處理 dict、list、Decimal 類型
- 確保 DynamoDB 回傳的數值正確轉換為 Python 原生類型

### 2. 實作 `get_team_info()` 方法
```python
def get_team_info(self, team_id: str) -> Optional[Team]:
    """取得團隊資訊"""
```

**功能：**
- 從 Teams 表使用 `get_item()` 查詢團隊資訊
- 轉換 Decimal 為 int
- 將 ISO 格式時間字串轉換為 datetime 物件
- 回傳 Team 物件，若團隊不存在則回傳 None

**錯誤處理：**
- 捕捉所有異常並記錄錯誤訊息
- 查詢失敗時回傳 None

### 3. 實作 `get_team_members()` 方法
```python
def get_team_members(self, team_id: str) -> List[TeamMember]:
    """取得團隊成員清單（使用 TeamIdIndex GSI，依 contribution_points 降序排序）"""
```

**功能：**
- 使用 TeamIdIndex GSI 查詢團隊所有成員
- 設定 `ScanIndexForward=False` 實現降序排序
- 轉換 Decimal 為 int
- 將 ISO 格式時間字串轉換為 datetime 物件
- 回傳 TeamMember 物件列表

**排序機制：**
- TeamIdIndex GSI 的 Sort Key 為 `contribution_points`
- `ScanIndexForward=False` 確保依貢獻積分降序排列
- 最高貢獻者排在第一位

**錯誤處理：**
- 捕捉所有異常並記錄錯誤訊息
- 查詢失敗時回傳空列表 `[]`

## 測試結果

### 單元測試 (test_team_info.py)
✅ 所有測試通過：
1. `test_get_team_info_success` - 成功取得團隊資訊
2. `test_get_team_info_not_found` - 正確處理不存在的團隊
3. `test_get_team_members_single_member` - 取得單一成員（隊長）
4. `test_get_team_members_multiple_members` - 取得多位成員
5. `test_get_team_members_empty_team` - 正確處理不存在團隊
6. `test_get_team_members_sorted_by_contribution` - 驗證排序正確性

### 示範程式 (demo_team_info.py)
✅ 完整功能展示：
- 建立團隊並加入成員
- 模擬成員通報更新積分
- 使用 `get_team_info()` 查詢團隊資訊
- 使用 `get_team_members()` 查詢成員清單
- 驗證成員依貢獻積分降序排列
- 測試錯誤處理（不存在的團隊）

## 符合需求

### Requirements 6.4
✅ 查詢團隊資訊
- `get_team_info()` 從 Teams 表查詢團隊基本資訊
- 回傳團隊 ID、名稱、隊長、總積分、成員數、建立時間

### Requirements 6.5
✅ 顯示團隊成員清單
- `get_team_members()` 查詢團隊所有成員
- 包含成員 UID、貢獻積分、通報次數、角色

### Requirements 7.1
✅ 查詢團隊所有成員
- 使用 TeamIdIndex GSI 高效查詢
- 回傳完整成員資訊

### Requirements 7.3
✅ 計算每位成員的貢獻度
- 成員清單包含 contribution_points 和 report_count
- 依貢獻積分降序排序，最高貢獻者排在第一位

## 技術細節

### DynamoDB GSI 使用
- **Index Name:** TeamIdIndex
- **Partition Key:** team_id
- **Sort Key:** contribution_points
- **Projection:** ALL
- **排序方向:** ScanIndexForward=False (降序)

### 資料轉換
- DynamoDB 回傳的數字為 Decimal 類型
- 使用 `_convert_decimal_to_int()` 遞迴轉換
- ISO 時間字串使用 `datetime.fromisoformat()` 轉換

### 錯誤處理策略
- 查詢失敗時不拋出異常
- `get_team_info()` 回傳 None
- `get_team_members()` 回傳空列表
- 記錄錯誤訊息供除錯使用

## 檔案清單

### 修改的檔案
- `team_service.py` - 新增 2 個方法和 1 個輔助方法

### 新增的測試檔案
- `test_team_info.py` - 單元測試
- `demo_team_info.py` - 功能示範

## 執行方式

### 執行測試
```bash
python test_team_info.py
```

### 執行示範
```bash
python demo_team_info.py
```

## 總結

✅ Task 3.7 實作完成！

**實作功能：**
1. ✅ `get_team_info()` - 查詢團隊基本資訊
2. ✅ `get_team_members()` - 查詢成員清單（使用 GSI）
3. ✅ 成員依 contribution_points 降序排序
4. ✅ 正確處理不存在的團隊
5. ✅ Decimal 轉換為 int
6. ✅ 完整的錯誤處理

**測試覆蓋：**
- ✅ 6 個單元測試全部通過
- ✅ 完整的功能示範
- ✅ 邊界情況測試（不存在的團隊）
- ✅ 排序正確性驗證

**符合需求：**
- ✅ Requirements 6.4 (查詢團隊資訊)
- ✅ Requirements 6.5 (顯示成員清單)
- ✅ Requirements 7.1 (查詢所有成員)
- ✅ Requirements 7.3 (計算貢獻度)
