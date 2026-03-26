# Task 9.1 實作摘要：詐騙網域趨勢 API

## 任務描述
實作 GET /api/trends/domains API 端點，提供詐騙網域統計資訊，包含通報次數與平均風險評分。

## 實作內容

### 1. API 端點實作 (main.py)
- **端點**: `GET /api/trends/domains`
- **功能**:
  - 從 ScamReports 表掃描所有通報記錄
  - 提取每個 URL 的網域名稱
  - 統計每個網域的通報次數與平均風險評分
  - 依通報次數降序排序，回傳前 20 名

### 2. 核心功能
- **網域提取**: 使用 `urlparse` 從 URL 提取網域名稱
- **www. 前綴處理**: 自動移除 www. 前綴，統一網域統計
- **平均風險計算**: 計算每個網域的平均風險評分（四捨五入至小數點後 1 位）
- **排序與限制**: 依通報次數降序排序，最多回傳前 20 名
- **分頁處理**: 處理 DynamoDB scan 的分頁機制（LastEvaluatedKey）

### 3. 回應格式
```json
{
  "domains": [
    {
      "rank": 1,
      "domain": "scam-site.com",
      "report_count": 45,
      "avg_risk_score": 9.2
    }
  ]
}
```

## 測試結果

### 測試檔案: `tests/test_domain_trends.py`
- ✅ `test_domain_trends_basic`: 測試基本網域統計功能
- ✅ `test_domain_trends_ordering`: 測試網域依通報次數降序排序
- ✅ `test_domain_trends_www_removal`: 測試 www. 前綴移除
- ✅ `test_domain_trends_avg_risk_calculation`: 測試平均風險評分計算
- ✅ `test_domain_trends_top_20_limit`: 測試前 20 名限制
- ✅ `test_domain_trends_empty_database`: 測試空資料庫情況

**測試結果**: 6/6 通過 ✅

## Demo 腳本

### 檔案: `demos/demo_domain_trends.py`
提供兩種操作模式：
1. 使用現有資料查詢
2. 建立範例資料後查詢（會自動清理）

執行方式：
```bash
python demos/demo_domain_trends.py
```

## 技術細節

### 1. 網域提取邏輯
```python
parsed = urlparse(url)
domain = parsed.netloc.lower()

# 移除 www. 前綴
if domain.startswith('www.'):
    domain = domain[4:]
```

### 2. 統計資料結構
使用 `defaultdict` 統計每個網域的通報次數與總風險評分：
```python
domain_stats = defaultdict(lambda: {'count': 0, 'total_risk': 0})
```

### 3. 平均風險計算
```python
avg_risk = round(stats['total_risk'] / stats['count'], 1)
```

### 4. 排序與限制
```python
domains_data.sort(key=lambda x: x['report_count'], reverse=True)
top_domains = domains_data[:20]
```

## 錯誤處理
- URL 解析失敗時記錄錯誤並跳過該筆資料
- API 執行失敗時回傳 500 錯誤與詳細錯誤訊息
- 空資料庫時回傳空陣列

## 效能考量
- 使用 DynamoDB scan 操作（適合小到中型資料集）
- 處理分頁機制以支援大量資料
- 在記憶體中進行統計與排序（適合前 20 名的需求）

## 相關需求
- Requirements 9.1: 實作網域統計功能
- Requirements 9.2: 提取網域名稱
- Requirements 9.3: 統計通報次數
- Requirements 9.4: 計算平均風險評分
- Requirements 9.5: 依通報次數排序

## 後續優化建議
1. 考慮使用 DynamoDB Streams 或 Lambda 進行即時統計
2. 加入快取機制（如 Redis）以提升查詢效能
3. 支援時間範圍篩選（如最近 7 天、30 天）
4. 加入網域黑名單功能
5. 提供更多統計維度（如類別分布、時間趨勢）

## 完成時間
2026-03-26

## 狀態
✅ 完成並通過所有測試
