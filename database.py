import boto3
import os
from datetime import datetime
from typing import List, Dict
from decimal import Decimal
from dotenv import load_dotenv
from models import ScamDetectionRecord, UserHistory, LeaderboardEntry

# 載入環境變數
load_dotenv()

# DynamoDB 設定
TABLE_NAME = "ScamDetectionRecords"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# 取得 AWS 憑證（支援大小寫）
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")

# 檢查憑證是否存在
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError(
        "❌ AWS 憑證未設定！\n"
        "請確認 .env 檔案包含：\n"
        "  - aws_access_key_id=你的key\n"
        "  - aws_secret_access_key=你的secret\n"
        "  - AWS_REGION=us-east-1"
    )

# 初始化 DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def get_table():
    """取得 DynamoDB table"""
    return dynamodb.Table(TABLE_NAME)

def convert_decimal_to_int(obj):
    """將 Decimal 轉換為 int（DynamoDB 回傳的數字是 Decimal 型別）"""
    if isinstance(obj, list):
        return [convert_decimal_to_int(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_int(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def add_detection_record(record: ScamDetectionRecord):
    """新增偵測記錄到 DynamoDB"""
    table = get_table()
    
    # 設定時間戳記
    if record.created_at is None:
        record.created_at = datetime.now()
    
    # 生成唯一 ID（使用 user_id + timestamp）
    record_id = f"{record.user_id}#{record.created_at.isoformat()}"
    
    # 準備資料
    item = {
        'record_id': record_id,  # Primary Key
        'user_id': record.user_id,  # GSI Partition Key
        'created_at': record.created_at.isoformat(),
        'timestamp': record.created_at.isoformat(),  # 相容舊格式
        'input_content': record.input_content,
        'risk_score': record.risk_score,
        'category': record.category,
        'analysis': record.analysis,
        'expert_warning': record.expert_warning
    }
    
    # 寫入 DynamoDB
    table.put_item(Item=item)
    
    return item

def get_user_history(user_id: str) -> List[UserHistory]:
    """取得使用者歷史記錄"""
    table = get_table()
    
    # 使用 GSI 查詢特定使用者的所有記錄
    response = table.query(
        IndexName='UserIdIndex',
        KeyConditionExpression='user_id = :uid',
        ExpressionAttributeValues={
            ':uid': user_id
        },
        ScanIndexForward=False  # 降序排列（最新的在前）
    )
    
    items = response.get('Items', [])
    
    # 轉換 Decimal 為 int
    items = convert_decimal_to_int(items)
    
    # 轉換為 UserHistory 物件
    return [UserHistory(**item) for item in items]

def get_leaderboard() -> List[LeaderboardEntry]:
    """取得排行榜"""
    table = get_table()
    
    # Scan 所有記錄（注意：大量資料時效能較差，建議使用聚合表）
    response = table.scan()
    items = response.get('Items', [])
    
    # 處理分頁（如果資料超過 1MB）
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    # 轉換 Decimal 為 int
    items = convert_decimal_to_int(items)
    
    # 統計每個使用者的數據
    user_stats = {}
    for record in items:
        user_id = record.get('user_id')
        if not user_id:
            continue
            
        if user_id not in user_stats:
            user_stats[user_id] = {
                'user_id': user_id,
                'total_scams': 0,
                'total_points': 0,
                'coupons': 0
            }
        
        user_stats[user_id]['total_scams'] += 1
        user_stats[user_id]['total_points'] += record.get('risk_score', 0)
        
        # 風險分數 >= 8 可獲得優惠券
        if record.get('risk_score', 0) >= 8:
            user_stats[user_id]['coupons'] += 1
    
    # 轉換為列表並排序（按總分排序）
    leaderboard = list(user_stats.values())
    leaderboard.sort(key=lambda x: x['total_points'], reverse=True)
    
    return [LeaderboardEntry(**entry) for entry in leaderboard]

def create_table_if_not_exists():
    """建立 DynamoDB table（如果不存在）"""
    try:
        # 檢查 table 是否存在
        table = dynamodb.Table(TABLE_NAME)
        table.load()
        print(f"✅ DynamoDB table '{TABLE_NAME}' 已存在")
        return True
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        print(f"⚠️  DynamoDB table '{TABLE_NAME}' 不存在，正在建立...")
        
        # 建立 table
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'record_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'record_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIdIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # 等待 table 建立完成
        print("⏳ 等待 table 建立完成...")
        table.wait_until_exists()
        print(f"✅ DynamoDB table '{TABLE_NAME}' 建立成功！")
        return True
    except Exception as e:
        print(f"❌ 建立 DynamoDB table 失敗: {e}")
        return False

def create_team_tables_if_not_exist():
    """建立團隊協作相關的 DynamoDB 資料表（Teams, TeamMembers, ScamReports）"""
    
    tables_config = [
        # Teams Table
        {
            'name': 'Teams',
            'key_schema': [
                {'AttributeName': 'team_id', 'KeyType': 'HASH'}
            ],
            'attribute_definitions': [
                {'AttributeName': 'team_id', 'AttributeType': 'S'}
            ],
            'gsi': []
        },
        # TeamMembers Table
        {
            'name': 'TeamMembers',
            'key_schema': [
                {'AttributeName': 'member_id', 'KeyType': 'HASH'}
            ],
            'attribute_definitions': [
                {'AttributeName': 'member_id', 'AttributeType': 'S'},
                {'AttributeName': 'team_id', 'AttributeType': 'S'},
                {'AttributeName': 'line_uid', 'AttributeType': 'S'},
                {'AttributeName': 'contribution_points', 'AttributeType': 'N'}
            ],
            'gsi': [
                {
                    'IndexName': 'TeamIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'team_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'contribution_points', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'LineUidIndex',
                    'KeySchema': [
                        {'AttributeName': 'line_uid', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ]
        },
        # ScamReports Table
        {
            'name': 'ScamReports',
            'key_schema': [
                {'AttributeName': 'report_id', 'KeyType': 'HASH'}
            ],
            'attribute_definitions': [
                {'AttributeName': 'report_id', 'AttributeType': 'S'},
                {'AttributeName': 'normalized_url', 'AttributeType': 'S'},
                {'AttributeName': 'team_id', 'AttributeType': 'S'},
                {'AttributeName': 'reported_at', 'AttributeType': 'S'}
            ],
            'gsi': [
                {
                    'IndexName': 'NormalizedUrlIndex',
                    'KeySchema': [
                        {'AttributeName': 'normalized_url', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'KEYS_ONLY'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'TeamIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'team_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'reported_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ]
        }
    ]
    
    for table_config in tables_config:
        table_name = table_config['name']
        try:
            # 檢查 table 是否存在
            table = dynamodb.Table(table_name)
            table.load()
            print(f"✅ DynamoDB table '{table_name}' 已存在")
        except dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"⚠️  DynamoDB table '{table_name}' 不存在，正在建立...")
            
            # 準備建立參數
            create_params = {
                'TableName': table_name,
                'KeySchema': table_config['key_schema'],
                'AttributeDefinitions': table_config['attribute_definitions'],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
            
            # 如果有 GSI，加入設定
            if table_config['gsi']:
                create_params['GlobalSecondaryIndexes'] = table_config['gsi']
            
            # 建立 table
            table = dynamodb.create_table(**create_params)
            
            # 等待 table 建立完成
            print(f"⏳ 等待 table '{table_name}' 建立完成...")
            table.wait_until_exists()
            print(f"✅ DynamoDB table '{table_name}' 建立成功！")
        except Exception as e:
            print(f"❌ 建立 DynamoDB table '{table_name}' 失敗: {e}")
            return False
    
    return True
