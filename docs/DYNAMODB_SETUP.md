# DynamoDB 設定指南

## 自動建立 Table（推薦）

程式會在啟動時自動檢查並建立 DynamoDB table。

只需確保：
1. AWS 憑證正確設定在 `.env`
2. IAM 使用者有 DynamoDB 權限

啟動程式：
```bash
python main.py
```

你會看到：
```
🔧 正在檢查 DynamoDB table...
✅ DynamoDB table 'ScamDetectionRecords' 建立成功！
```

## 手動建立 Table（選擇性）

如果你想手動建立，可以使用 AWS CLI：

```bash
aws dynamodb create-table \
    --table-name ScamDetectionRecords \
    --attribute-definitions \
        AttributeName=record_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --key-schema \
        AttributeName=record_id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"UserIdIndex\",
                \"KeySchema\": [
                    {\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"},
                    {\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\":\"ALL\"},
                \"ProvisionedThroughput\": {
                    \"ReadCapacityUnits\": 5,
                    \"WriteCapacityUnits\": 5
                }
            }
        ]" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

## Table 結構

### Primary Key
- `record_id` (String, HASH) - 格式：`{user_id}#{timestamp}`

### Attributes
- `user_id` (String) - LINE 使用者 ID
- `created_at` (String) - ISO 格式時間戳記
- `timestamp` (String) - 相容舊格式
- `input_content` (String) - 使用者輸入內容
- `risk_score` (Number) - 風險分數 (0-10)
- `category` (String) - 詐騙類別
- `analysis` (List) - 風險分析要點
- `expert_warning` (String) - 專員警示

### Global Secondary Index (GSI)
- **IndexName**: `UserIdIndex`
- **Partition Key**: `user_id`
- **Sort Key**: `created_at`
- **用途**: 快速查詢特定使用者的所有記錄

## IAM 權限設定

你的 IAM 使用者需要以下權限：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:us-east-1:*:table/ScamDetectionRecords",
                "arn:aws:dynamodb:us-east-1:*:table/ScamDetectionRecords/index/*"
            ]
        }
    ]
}
```

## 檢查 Table 狀態

### 使用 AWS CLI
```bash
aws dynamodb describe-table --table-name ScamDetectionRecords --region us-east-1
```

### 使用 AWS Console
1. 前往 https://console.aws.amazon.com/dynamodb/
2. 選擇 Region: us-east-1
3. 點選 "Tables"
4. 找到 "ScamDetectionRecords"

## 查看資料

### 使用 AWS CLI
```bash
# 查看所有資料
aws dynamodb scan --table-name ScamDetectionRecords --region us-east-1

# 查詢特定使用者
aws dynamodb query \
    --table-name ScamDetectionRecords \
    --index-name UserIdIndex \
    --key-condition-expression "user_id = :uid" \
    --expression-attribute-values '{":uid":{"S":"U1234567890"}}' \
    --region us-east-1
```

## 成本估算

### Provisioned Capacity (預設)
- Read: 5 RCU = ~$0.00065/hour
- Write: 5 WCU = ~$0.00065/hour
- Storage: $0.25/GB/month
- **預估月費**: ~$1-2 USD（低流量）

### On-Demand (選擇性)
如果流量不穩定，可以改用 On-Demand 模式：
- 只在實際使用時付費
- 適合開發測試或低流量應用

## 遷移現有資料

如果你有舊的 JSON 資料想遷移到 DynamoDB：

```python
import json
import boto3
from datetime import datetime

# 讀取舊資料
with open('scam_detection_db.json', 'r') as f:
    old_data = json.load(f)

# 連接 DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ScamDetectionRecords')

# 遷移資料
for record in old_data:
    record_id = f"{record['user_id']}#{record['created_at']}"
    record['record_id'] = record_id
    table.put_item(Item=record)
    print(f"✅ 遷移: {record_id}")

print("🎉 遷移完成！")
```

## 故障排除

### 錯誤：ResourceNotFoundException
- Table 不存在，程式會自動建立
- 等待 30-60 秒讓 table 完全建立

### 錯誤：AccessDeniedException
- 檢查 IAM 權限
- 確認 AWS 憑證正確

### 錯誤：ValidationException
- 檢查資料格式
- 確認 attribute 型別正確

## 效能優化建議

### 1. 使用 Batch Operations
大量寫入時使用 `batch_writer()`：
```python
with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)
```

### 2. 排行榜優化
目前使用 Scan（效能較差），建議：
- 建立聚合表（每日更新）
- 使用 DynamoDB Streams + Lambda 即時更新
- 使用 ElastiCache 快取排行榜

### 3. 監控
在 AWS Console 設定 CloudWatch 警報：
- Read/Write Capacity 使用率
- Throttled Requests
- System Errors
