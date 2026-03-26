#!/usr/bin/env python3
"""
Demo: 每日任務系統 (Daily Quest System)
展示團隊達成「單日通報 5 則 URL」任務時的獎勵機制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from points_calculator import PointsCalculator
from database import dynamodb
from datetime import datetime, timezone
import uuid


def setup_demo_team():
    """建立示範團隊"""
    team_id = f"demo-team-{uuid.uuid4().hex[:8]}"
    teams_table = dynamodb.Table('Teams')
    
    teams_table.put_item(Item={
        'team_id': team_id,
        'team_name': '防詐先鋒隊',
        'leader_uid': 'U_demo_leader',
        'total_points': 100,
        'member_count': 3,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'completed_quests': []
    })
    
    print(f"✅ 建立示範團隊: {team_id}")
    print(f"   團隊名稱: 防詐先鋒隊")
    print(f"   初始積分: 100")
    print()
    return team_id


def simulate_reports(team_id, count):
    """模擬團隊成員通報詐騙"""
    scam_reports_table = dynamodb.Table('ScamReports')
    calculator = PointsCalculator()
    
    print(f"📝 模擬 {count} 則詐騙通報...")
    print()
    
    for i in range(count):
        url = f"https://scam-demo-{i}.com/fake-investment"
        normalized_url = calculator.normalize_url(url)
        
        scam_reports_table.put_item(Item={
            'report_id': f"demo-report-{i}-{uuid.uuid4().hex[:8]}",
            'team_id': team_id,
            'url': url,
            'normalized_url': normalized_url,
            'reporter_uid': f'U_demo_member_{i % 3}',
            'risk_score': 7 + (i % 3),
            'category': '假投資詐騙',
            'multiplier_applied': False,
            'points_earned': 7 + (i % 3),
            'reported_at': datetime.now(timezone.utc).isoformat()
        })
        
        print(f"   [{i+1}] {url} (風險評分: {7 + (i % 3)})")
    
    print()


def check_quest_status(team_id):
    """檢查任務狀態"""
    calculator = PointsCalculator()
    
    print("🔍 檢查每日任務狀態...")
    result = calculator.check_daily_quest(team_id)
    
    print(f"   任務完成: {'✅ 是' if result['quest_completed'] else '❌ 否'}")
    print(f"   已領取獎勵: {'✅ 是' if result['already_claimed'] else '❌ 否'}")
    print(f"   當日通報數: {result['daily_report_count']}")
    print(f"   獎勵積分: {result['bonus_awarded']}")
    print(f"   訊息: {result['message']}")
    print()
    
    return result


def show_team_points(team_id):
    """顯示團隊積分"""
    teams_table = dynamodb.Table('Teams')
    team_data = teams_table.get_item(Key={'team_id': team_id})['Item']
    
    print("📊 團隊積分狀態:")
    print(f"   總積分: {team_data['total_points']}")
    print(f"   已完成任務: {team_data.get('completed_quests', [])}")
    print()


def cleanup_demo_data(team_id):
    """清理示範資料"""
    print("🧹 清理示範資料...")
    
    # 刪除團隊
    teams_table = dynamodb.Table('Teams')
    teams_table.delete_item(Key={'team_id': team_id})
    
    # 刪除通報記錄
    scam_reports_table = dynamodb.Table('ScamReports')
    response = scam_reports_table.query(
        IndexName='TeamIdIndex',
        KeyConditionExpression='team_id = :tid',
        ExpressionAttributeValues={':tid': team_id}
    )
    
    for item in response.get('Items', []):
        scam_reports_table.delete_item(Key={'report_id': item['report_id']})
    
    print("✅ 清理完成")
    print()


def main():
    print("=" * 60)
    print("每日任務系統示範 (Daily Quest System Demo)")
    print("=" * 60)
    print()
    
    # 1. 建立示範團隊
    team_id = setup_demo_team()
    
    # 2. 顯示初始積分
    show_team_points(team_id)
    
    # 3. 模擬 3 則通報（未達成任務）
    print("【場景 1】通報 3 則詐騙（未達成任務）")
    print("-" * 60)
    simulate_reports(team_id, 3)
    check_quest_status(team_id)
    show_team_points(team_id)
    
    # 4. 再模擬 2 則通報（達成任務）
    print("【場景 2】再通報 2 則詐騙（達成任務！）")
    print("-" * 60)
    simulate_reports(team_id, 2)
    result = check_quest_status(team_id)
    show_team_points(team_id)
    
    # 5. 再次檢查（已領取獎勵）
    print("【場景 3】再次檢查任務（已領取獎勵）")
    print("-" * 60)
    result = check_quest_status(team_id)
    show_team_points(team_id)
    
    # 6. 清理示範資料
    cleanup_demo_data(team_id)
    
    print("=" * 60)
    print("示範完成！")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
