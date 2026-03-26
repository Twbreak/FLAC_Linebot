# Task 8.1 Implementation Summary: 每日任務檢測系統

## 任務概述

實作團隊每日任務檢測功能，當團隊在單日內累積 5 則有效通報時，自動給予 50 點獎勵積分，並防止重複領取獎勵。

## 實作內容

### 1. 核心功能實作

在 `points_calculator.py` 新增 `check_daily_quest()` 方法：

**功能特點：**
- 查詢團隊當日通報數量（使用 TeamIdIndex GSI）
- 檢查是否達到 5 則通報門檻
- 檢查 `completed_quests` 欄位避免重複獎勵
- 自動更新團隊積分並記錄任務完成狀態
- 使用 UTC 時區確保日期一致性

**方法簽名：**
```python
def check_daily_quest(self, team_id: str) -> Dict:
    """檢查並處理每日任務完成狀態
    
    Returns:
        {
            'quest_completed': bool,      # 是否完成任務
            'already_claimed': bool,      # 是否已領取獎勵
            'bonus_awarded': int,         # 獎勵積分（0 或 50）
            'daily_report_count': int,    # 當日通報數量
            'message': str                # 結果訊息
        }
    """
```

### 2. 實作邏輯流程

1. **查詢團隊資訊**
   - 從 Teams 表取得團隊資料
   - 檢查 `completed_quests` 欄位是否包含今日任務 ID
   - 任務 ID 格式：`daily_5_reports_YYYY-MM-DD`

2. **查詢當日通報數量**
   - 使用 ScamReports 表的 TeamIdIndex GSI
   - 查詢條件：`team_id = :tid AND reported_at BETWEEN :start AND :end`
   - 計算今日通報總數

3. **檢查任務條件**
   - 若通報數 < 5：返回未完成狀態
   - 若通報數 >= 5：執行獎勵發放

4. **發放獎勵**
   - 使用原子性操作更新 `total_points`（ADD 50）
   - 使用 `list_append` 更新 `completed_quests`
   - 防止並發問題

### 3. 測試覆蓋

建立 `tests/test_daily_quest.py`，包含 5 個測試案例：

1. **test_daily_quest_not_completed_insufficient_reports**
   - 測試通報數不足 5 則時，任務未完成

2. **test_daily_quest_completed_first_time**
   - 測試達到 5 則通報時，首次完成任務並獲得 50 點獎勵
   - 驗證 `total_points` 正確增加
   - 驗證 `completed_quests` 正確更新

3. **test_daily_quest_already_claimed**
   - 測試今日任務已完成時，不重複給予獎勵

4. **test_daily_quest_team_not_exist**
   - 測試團隊不存在時的錯誤處理

5. **test_daily_quest_more_than_5_reports**
   - 測試通報超過 5 則時，仍只給予一次獎勵

**測試結果：** ✅ 5/5 通過

### 4. 示範程式

建立 `demos/demo_daily_quest.py`，展示完整流程：

**場景 1：** 通報 3 則詐騙（未達成任務）
- 顯示當日通報進度：3/5

**場景 2：** 再通報 2 則詐騙（達成任務）
- 自動發放 50 點獎勵
- 團隊積分從 100 增加到 150
- 記錄任務完成狀態

**場景 3：** 再次檢查任務（已領取獎勵）
- 顯示今日任務已完成
- 不重複給予獎勵

## 技術細節

### DynamoDB 操作

**查詢當日通報：**
```python
scam_reports_table.query(
    IndexName='TeamIdIndex',
    KeyConditionExpression='team_id = :tid AND reported_at BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':tid': team_id,
        ':start': today_start,
        ':end': today_end
    }
)
```

**原子性更新積分與任務狀態：**
```python
teams_table.update_item(
    Key={'team_id': team_id},
    UpdateExpression='ADD total_points :bonus SET completed_quests = list_append(if_not_exists(completed_quests, :empty_list), :quest)',
    ExpressionAttributeValues={
        ':bonus': 50,
        ':quest': [quest_id],
        ':empty_list': []
    }
)
```

### 時區處理

使用 UTC 時區確保全球一致性：
```python
from datetime import datetime, timezone

today = datetime.now(timezone.utc).date()
today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()
today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc).isoformat()
```

## 符合的需求

- ✅ **Requirement 8.1**: 定義每日任務「單日通報 5 則 URL」
- ✅ **Requirement 8.2**: 檢測任務完成條件
- ✅ **Requirement 8.3**: 給予 50 點獎勵積分
- ✅ **Requirement 8.4**: 記錄任務完成狀態
- ✅ **Requirement 8.6**: 防止重複獎勵

## 後續整合

Task 8.3 將整合此功能至通報流程：
- 在 `update_team_points()` 方法中呼叫 `check_daily_quest()`
- 在 LINE Bot 回覆中加入任務完成通知
- 當團隊達成任務時，自動通知隊長

## 檔案清單

### 新增檔案
- `tests/test_daily_quest.py` - 單元測試
- `demos/demo_daily_quest.py` - 示範程式
- `docs/task_summaries/TASK_8.1_IMPLEMENTATION_SUMMARY.md` - 本文件

### 修改檔案
- `points_calculator.py` - 新增 `check_daily_quest()` 方法

## 執行方式

### 執行測試
```bash
python -m pytest tests/test_daily_quest.py -v
```

### 執行示範
```bash
python demos/demo_daily_quest.py
```

## 注意事項

1. **時區一致性**：所有時間戳記使用 UTC 時區
2. **原子性操作**：使用 DynamoDB 的 ADD 和 list_append 確保並發安全
3. **任務 ID 格式**：`daily_5_reports_YYYY-MM-DD`，每日唯一
4. **GSI 查詢**：使用 TeamIdIndex 提升查詢效能
5. **錯誤處理**：完整的異常捕獲與錯誤訊息

## 效能考量

- **查詢效率**：使用 GSI 避免全表掃描
- **原子性**：單次 update_item 操作完成積分與狀態更新
- **快取機會**：已完成任務的檢查可提前返回，無需查詢通報記錄

## 總結

Task 8.1 成功實作每日任務檢測系統，提供完整的任務檢測、獎勵發放與重複防護機制。所有測試通過，示範程式驗證功能正常運作。
