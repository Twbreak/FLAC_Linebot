# tests/test_daily_quest.py
"""
Unit tests for daily quest system (Task 8.1)
Tests the check_daily_quest() method in PointsCalculator
"""

import pytest
from datetime import datetime, timezone
from points_calculator import PointsCalculator
from moto import mock_aws
import boto3
import os


@pytest.fixture
def setup_dynamodb():
    """設定 mock DynamoDB 環境"""
    with mock_aws():
        # 設定環境變數
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        # 建立 DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # 建立 Teams 表
        teams_table = dynamodb.create_table(
            TableName='Teams',
            KeySchema=[
                {'AttributeName': 'team_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'team_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # 建立 ScamReports 表（含 TeamIdIndex GSI）
        scam_reports_table = dynamodb.create_table(
            TableName='ScamReports',
            KeySchema=[
                {'AttributeName': 'report_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'report_id', 'AttributeType': 'S'},
                {'AttributeName': 'team_id', 'AttributeType': 'S'},
                {'AttributeName': 'reported_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'TeamIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'team_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'reported_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield dynamodb


def test_daily_quest_not_completed_insufficient_reports(setup_dynamodb):
    """測試：當日通報數量不足 5 則，任務未完成"""
    dynamodb = setup_dynamodb
    calculator = PointsCalculator()
    
    team_id = 'test-team-001'
    today = datetime.now(timezone.utc).date()
    
    # 建立團隊
    teams_table = dynamodb.Table('Teams')
    teams_table.put_item(Item={
        'team_id': team_id,
        'team_name': '測試團隊',
        'total_points': 100,
        'completed_quests': []
    })
    
    # 建立 3 則今日通報（不足 5 則）
    scam_reports_table = dynamodb.Table('ScamReports')
    for i in range(3):
        scam_reports_table.put_item(Item={
            'report_id': f'report-{i}',
            'team_id': team_id,
            'reported_at': datetime.now(timezone.utc).isoformat(),
            'url': f'https://scam-{i}.com',
            'normalized_url': f'https://scam-{i}.com',
            'reporter_uid': f'U{i}',
            'risk_score': 7
        })
    
    # 執行任務檢測
    result = calculator.check_daily_quest(team_id)
    
    # 驗證結果
    assert result['quest_completed'] == False
    assert result['already_claimed'] == False
    assert result['bonus_awarded'] == 0
    assert result['daily_report_count'] == 3
    assert '3/5' in result['message']


def test_daily_quest_completed_first_time(setup_dynamodb):
    """測試：當日通報達到 5 則，首次完成任務並獲得獎勵"""
    dynamodb = setup_dynamodb
    calculator = PointsCalculator()
    
    team_id = 'test-team-002'
    today = datetime.now(timezone.utc).date()
    
    # 建立團隊
    teams_table = dynamodb.Table('Teams')
    teams_table.put_item(Item={
        'team_id': team_id,
        'team_name': '測試團隊',
        'total_points': 100,
        'completed_quests': []
    })
    
    # 建立 5 則今日通報
    scam_reports_table = dynamodb.Table('ScamReports')
    for i in range(5):
        scam_reports_table.put_item(Item={
            'report_id': f'report-{i}',
            'team_id': team_id,
            'reported_at': datetime.now(timezone.utc).isoformat(),
            'url': f'https://scam-{i}.com',
            'normalized_url': f'https://scam-{i}.com',
            'reporter_uid': f'U{i}',
            'risk_score': 7
        })
    
    # 執行任務檢測
    result = calculator.check_daily_quest(team_id)
    
    # 驗證結果
    assert result['quest_completed'] == True
    assert result['already_claimed'] == False
    assert result['bonus_awarded'] == 50
    assert result['daily_report_count'] == 5
    assert '完成每日任務' in result['message']
    
    # 驗證團隊積分已更新
    team_data = teams_table.get_item(Key={'team_id': team_id})['Item']
    assert team_data['total_points'] == 150  # 100 + 50 獎勵
    
    # 驗證 completed_quests 已更新
    quest_id = f"daily_5_reports_{today.isoformat()}"
    assert quest_id in team_data['completed_quests']


def test_daily_quest_already_claimed(setup_dynamodb):
    """測試：今日任務已完成，不重複給予獎勵"""
    dynamodb = setup_dynamodb
    calculator = PointsCalculator()
    
    team_id = 'test-team-003'
    today = datetime.now(timezone.utc).date()
    quest_id = f"daily_5_reports_{today.isoformat()}"
    
    # 建立團隊（已完成今日任務）
    teams_table = dynamodb.Table('Teams')
    teams_table.put_item(Item={
        'team_id': team_id,
        'team_name': '測試團隊',
        'total_points': 150,
        'completed_quests': [quest_id]  # 已完成今日任務
    })
    
    # 執行任務檢測
    result = calculator.check_daily_quest(team_id)
    
    # 驗證結果
    assert result['quest_completed'] == True
    assert result['already_claimed'] == True
    assert result['bonus_awarded'] == 0
    assert '已完成' in result['message']
    
    # 驗證團隊積分未變動
    team_data = teams_table.get_item(Key={'team_id': team_id})['Item']
    assert team_data['total_points'] == 150  # 未增加


def test_daily_quest_team_not_exist(setup_dynamodb):
    """測試：團隊不存在時的錯誤處理"""
    dynamodb = setup_dynamodb
    calculator = PointsCalculator()
    
    # 執行任務檢測（團隊不存在）
    result = calculator.check_daily_quest('non-existent-team')
    
    # 驗證結果
    assert result['quest_completed'] == False
    assert result['already_claimed'] == False
    assert result['bonus_awarded'] == 0
    assert '團隊不存在' in result['message']


def test_daily_quest_more_than_5_reports(setup_dynamodb):
    """測試：當日通報超過 5 則，仍然只給予一次獎勵"""
    dynamodb = setup_dynamodb
    calculator = PointsCalculator()
    
    team_id = 'test-team-004'
    today = datetime.now(timezone.utc).date()
    
    # 建立團隊
    teams_table = dynamodb.Table('Teams')
    teams_table.put_item(Item={
        'team_id': team_id,
        'team_name': '測試團隊',
        'total_points': 200,
        'completed_quests': []
    })
    
    # 建立 8 則今日通報
    scam_reports_table = dynamodb.Table('ScamReports')
    for i in range(8):
        scam_reports_table.put_item(Item={
            'report_id': f'report-{i}',
            'team_id': team_id,
            'reported_at': datetime.now(timezone.utc).isoformat(),
            'url': f'https://scam-{i}.com',
            'normalized_url': f'https://scam-{i}.com',
            'reporter_uid': f'U{i}',
            'risk_score': 7
        })
    
    # 執行任務檢測
    result = calculator.check_daily_quest(team_id)
    
    # 驗證結果
    assert result['quest_completed'] == True
    assert result['bonus_awarded'] == 50
    assert result['daily_report_count'] == 8
    
    # 驗證團隊積分只增加 50 點
    team_data = teams_table.get_item(Key={'team_id': team_id})['Item']
    assert team_data['total_points'] == 250  # 200 + 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
