# Task 4.5 實作摘要：積分計算與倍數獎勵

## 任務概述

實作 `PointsCalculator.calculate_points()` 方法，當風險評分 >= 9 時套用 2x 倍數獎勵。

## 需求對應

- **Requirement 5.1**: 當 risk_score >= 9 時，啟用 Risk_Multiplier 機制 ✓
- **Requirement 5.2**: 計算獎勵積分為 risk_score 乘以 2 ✓

## 實作細節

### 方法簽名

```python
def calculate_points(self, risk_score: int) -> int:
    """計算積分（含倍數獎勵）
    
    Args:
        risk_score: 風險評分 (1-10)
        
    Returns:
        計算後的積分
    """
```

### 實作邏輯

```python
# 極高風險 (risk_score >= 9) 給予 2x 倍數獎勵
if risk_score >= 9:
    return risk_score * 2
return risk_score
```

### 積分計算規則

| 風險評分 | 倍數 | 獲得積分 | 說明 |
|---------|------|---------|------|
| 1-8     | 1x   | = risk_score | 一般通報 |
| 9       | 2x   | 18      | 極高風險獎勵 ⭐ |
| 10      | 2x   | 20      | 極高風險獎勵 ⭐ |

## 測試驗證

### 測試案例

1. **一般風險評分測試**
   - risk_score = 1 → 積分 = 1 ✓
   - risk_score = 5 → 積分 = 5 ✓
   - risk_score = 7 → 積分 = 7 ✓
   - risk_score = 8 → 積分 = 8 ✓

2. **極高風險倍數獎勵測試**
   - risk_score = 9 → 積分 = 18 (9 × 2) ✓
   - risk_score = 10 → 積分 = 20 (10 × 2) ✓

3. **邊界值測試**
   - risk_score = 8 → 積分 = 8 (不觸發倍數) ✓
   - risk_score = 9 → 積分 = 18 (觸發倍數) ✓

### 測試結果

```bash
$ python3 test_task_4_5_verification.py
測試一般風險評分...
✓ 一般風險評分測試通過

測試極高風險倍數獎勵...
✓ 極高風險倍數獎勵測試通過

測試邊界值...
✓ 邊界值測試通過

==================================================
Task 4.5 驗證完成！
==================================================
✓ Requirements 5.1: 當 risk_score >= 9 時啟用 Risk_Multiplier
✓ Requirements 5.2: 獎勵積分 = risk_score * 2
```

## 實際應用場景

### 案例 1：假冒銀行登入頁面
- URL: `https://fake-bank.com/login`
- AI 風險評分: 8/10
- **獲得積分: 8**

### 案例 2：已知詐騙投資平台
- URL: `https://scam-investment.com/join`
- AI 風險評分: 9/10
- **⭐ 觸發倍數獎勵！**
- 基礎積分: 9
- 倍數: 2x
- **實際獲得: 18 積分**

### 案例 3：大規模釣魚詐騙網站
- URL: `https://phishing-site.com/prize`
- AI 風險評分: 10/10
- **⭐ 觸發倍數獎勵！**
- 基礎積分: 10
- 倍數: 2x
- **實際獲得: 20 積分**

## 設計目的

倍數獎勵機制的設計目的：

1. **鼓勵高品質通報**：引導使用者通報真正危險的詐騙內容
2. **提升團隊競爭力**：極高風險通報能快速提升團隊排名
3. **強化防詐效果**：優先處理最危險的詐騙網站

## 相關檔案

- **實作檔案**: `points_calculator.py`
- **測試檔案**: `test_points_calculator.py`
- **驗證腳本**: `test_task_4_5_verification.py`
- **示範腳本**: `demo_task_4_5.py`

## 完成狀態

✅ **Task 4.5 已完成**

- [x] 實作 `calculate_points()` 方法
- [x] 當 risk_score >= 9 時套用 2x 倍數
- [x] 驗證 Requirements 5.1
- [x] 驗證 Requirements 5.2
- [x] 所有測試通過
- [x] 建立示範腳本

## 後續整合

此方法將在 `update_team_points()` 中被調用，用於計算團隊與成員的實際獲得積分：

```python
def update_team_points(self, team_id: str, member_uid: str, 
                      url: str, risk_score: int) -> Dict:
    # 1. 標準化 URL
    normalized_url = self.normalize_url(url)
    
    # 2. 檢查重複
    if self.check_duplicate(normalized_url):
        return {"points_earned": 0, "is_duplicate": True}
    
    # 3. 計算積分（含倍數獎勵）
    points = self.calculate_points(risk_score)  # ← 使用此方法
    
    # 4. 更新團隊與成員積分
    # ... (後續任務實作)
```

---

**實作日期**: 2024
**實作者**: Kiro AI Assistant
**狀態**: ✅ 完成
