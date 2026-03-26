# Task 4.7 實作總結：團隊積分更新功能

## 實作內容

在 `PointsCalculator` 類別中實作了 `update_team_points()` 方法，整合了前面已完成的 `normalize_url()`、`check_duplicate()` 和 `calculate_points()` 方法。

## 核心功能

### 1. 標準化 URL
- 使用 `normalize_url()` 方法移除 query parameters 和 trailing slash
- 轉換為小寫以確保一致性

### 2. 重複檢測
- 使用 `check_duplicate()` 方法查詢 ScamReports 表的 NormalizedUrlIndex GSI
- 如果 URL 已被通報，返回失敗結果且不給予積分

### 3. 積分計算
- 使用 `calculate_points()` 方法計算積分
- 當 risk_score >= 9 時自動套用 2x 倍數獎勵

### 4. 原子性更新團隊積分
- 使用 DynamoDB 的 `ADD` 操作更新 Teams.total_points
- 確保並發安全，多個通報同時進行時積分正確累加

### 5. 原子性更新成員積分
- 使用 DynamoDB 的 `ADD` 操作同時更新：
  - TeamMembers.contribution_points（貢獻積分）
  - TeamMembers.report_count（通報次數）
- 如果更新失敗，嘗試回滾團隊積分（盡力而為）

### 6. 寫入通報記錄
- 在 ScamReports 表中記錄完整的通報資訊：
  - report_id: `{member_uid}#{timestamp}`
  - url: 原始 URL
  - normalized_url: 標準化後的 URL
  - reporter_uid: 通報者 LINE UID
  - team_id: 所屬團隊 ID
  - risk_score: 風險評分
  - category: 詐騙類別
  - multiplier_applied: 是否套用倍數獎勵
  - points_earned: 實際獲得積分
  - reported_at: 通報時間（ISO 8601 格式）

## 方法簽名

```python
def update_team_points(
    self, 
    team_id: str, 
    member_uid: str, 
    url: str, 
    risk_score: int, 
    category: str = "未分類"
) -> Dict
```

## 返回值格式

### 成功情況
```python
{
    'success': True,
    'points_earned': 18,
    'is_duplicate': False,
    'multiplier_applied': True,
    'normalized_url': 'https://scam-site.com/path',
    'report_id': 'U1234567890#2024-01-15T14:25:30.123456',
    'message': '成功通報！獲得 18 積分 (極高風險 2x 獎勵)'
}
```

### 重複通報情況
```python
{
    'success': False,
    'points_earned': 0,
    'is_duplicate': True,
    'multiplier_applied': False,
    'normalized_url': 'https://scam-site.com/path',
    'message': '此 URL 已被通報'
}
```

### 錯誤情況
```python
{
    'success': False,
    'points_earned': 0,
    'is_duplicate': False,
    'multiplier_applied': False,
    'normalized_url': 'https://scam-site.com/path',
    'error': '更新團隊積分失敗: ...'
}
```

## 測試結果

所有測試均通過：

### ✅ 測試 1: 首次通報應該獲得積分
- 驗證首次通報成功獲得積分
- 驗證團隊積分正確更新
- 驗證成員貢獻積分正確更新
- 驗證通報記錄正確寫入

### ✅ 測試 2: 重複通報不應該獲得積分
- 驗證第一次通報成功
- 驗證第二次通報被拒絕（重複）
- 驗證積分不會重複累加

### ✅ 測試 3: 極高風險通報應該獲得 2x 積分
- 驗證 risk_score >= 9 時獲得 2x 積分
- 驗證 multiplier_applied 標記正確
- 驗證通報記錄中的倍數標記

### ✅ 測試 4: URL 標準化在重複檢測中的作用
- 驗證帶不同 query parameters 的 URL 被視為重複
- 驗證帶 trailing slash 的 URL 被視為重複
- 驗證標準化後的 URL 一致性

### ✅ 測試 5: 原子性計數器更新（多次通報累積積分）
- 驗證多次通報積分正確累加
- 驗證團隊總積分正確（5 + 7 + 18 = 30）
- 驗證成員貢獻積分正確（30）
- 驗證通報次數正確（3）

## 滿足的需求

- ✅ **Requirements 4.4**: 首位通報者獲得積分
- ✅ **Requirements 4.5**: 積分加入團隊 Team_Points
- ✅ **Requirements 4.6**: 積分加入成員 Contribution_Points
- ✅ **Requirements 4.8**: 更新 Teams 表的 Team_Points
- ✅ **Requirements 4.9**: 更新 TeamMembers 表的 Contribution_Points

## 技術特點

1. **原子性操作**: 使用 DynamoDB 的 ADD 操作確保並發安全
2. **錯誤處理**: 完善的錯誤處理和回滾機制
3. **資料一致性**: 確保團隊積分、成員積分和通報記錄的一致性
4. **可擴展性**: 支援未來新增更多積分計算規則
5. **可測試性**: 清晰的返回值格式便於測試和除錯

## 整合點

此方法將在以下場景中被呼叫：

1. **LINE Bot Webhook Handler** (`main.py`):
   - 當團隊成員透過 LINE Bot 通報詐騙 URL 時
   - 在 Bedrock AI 分析完成後呼叫此方法

2. **團隊通報 API** (未來實作):
   - 透過 REST API 直接通報詐騙內容
   - 支援批次通報功能

## 後續工作

- [ ] 整合到 LINE Bot webhook handler (Task 7.1)
- [ ] 實作團隊任務檢測 (Task 8.1)
- [ ] 撰寫 property-based tests (Task 4.8)

## 檔案清單

- `points_calculator.py`: 主要實作
- `demo_update_team_points.py`: 手動測試腳本
- `test_update_team_points.py`: pytest 測試套件（需要安裝 pytest）
- `TASK_4.7_IMPLEMENTATION_SUMMARY.md`: 本文件
