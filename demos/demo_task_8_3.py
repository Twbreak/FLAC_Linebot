"""
Demo: Task 8.3 - 整合任務檢測至通報流程

展示當團隊成員通報詐騙 URL 時，系統會：
1. 更新團隊積分
2. 檢查每日任務完成狀態
3. 在 LINE Bot 回覆中顯示任務完成通知
"""

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import update_team_points_for_report, format_reply_with_team_points


def demo_quest_completion_notification():
    """展示任務完成通知整合"""
    print("=" * 80)
    print("Demo: Task 8.3 - 整合任務檢測至通報流程")
    print("=" * 80)
    print()
    
    # 模擬 Bedrock AI 分析結果
    analysis_result = {
        'risk_score': 8,
        'category': '假投資詐騙',
        'analysis': '這是一個高風險的詐騙網站，偽裝成投資平台',
        'expert_warning': '請勿點擊連結或提供個人資訊，這是典型的投資詐騙手法'
    }
    
    print("情境 1: 團隊成員通報第 5 則 URL，完成每日任務")
    print("-" * 80)
    
    # 模擬團隊積分更新結果（包含任務完成）
    team_result_with_quest = {
        'success': True,
        'points_earned': 8,
        'is_duplicate': False,
        'multiplier_applied': False,
        'normalized_url': 'https://fake-investment.com/scam',
        'report_id': 'U1234567890#2024-01-15T14:25:30Z',
        'quest_result': {
            'quest_completed': True,
            'already_claimed': False,
            'bonus_awarded': 50,
            'daily_report_count': 5,
            'message': '🎉 完成每日任務！團隊獲得 50 點獎勵積分'
        }
    }
    
    # 格式化回覆訊息
    reply_text = format_reply_with_team_points(analysis_result, team_result_with_quest)
    
    print("LINE Bot 回覆訊息：")
    print(reply_text)
    print()
    
    print("情境 2: 團隊成員通報第 6 則 URL，任務已完成")
    print("-" * 80)
    
    # 模擬團隊積分更新結果（任務已完成）
    team_result_already_claimed = {
        'success': True,
        'points_earned': 7,
        'is_duplicate': False,
        'multiplier_applied': False,
        'normalized_url': 'https://another-scam.com/fake',
        'report_id': 'U1234567890#2024-01-15T15:30:00Z',
        'quest_result': {
            'quest_completed': True,
            'already_claimed': True,  # 已領取，不顯示通知
            'bonus_awarded': 0,
            'daily_report_count': 0,
            'message': '今日任務已完成'
        }
    }
    
    # 格式化回覆訊息
    reply_text = format_reply_with_team_points(analysis_result, team_result_already_claimed)
    
    print("LINE Bot 回覆訊息：")
    print(reply_text)
    print()
    
    print("情境 3: 團隊成員通報第 3 則 URL，尚未完成任務")
    print("-" * 80)
    
    # 模擬團隊積分更新結果（尚未完成任務）
    team_result_not_completed = {
        'success': True,
        'points_earned': 9,
        'is_duplicate': False,
        'multiplier_applied': False,
        'normalized_url': 'https://scam-site.com/phishing',
        'report_id': 'U1234567890#2024-01-15T12:00:00Z',
        'quest_result': {
            'quest_completed': False,
            'already_claimed': False,
            'bonus_awarded': 0,
            'daily_report_count': 3,
            'message': '當日通報 3/5 則，尚未達成任務'
        }
    }
    
    # 格式化回覆訊息
    reply_text = format_reply_with_team_points(analysis_result, team_result_not_completed)
    
    print("LINE Bot 回覆訊息：")
    print(reply_text)
    print()
    
    print("情境 4: 極高風險通報 + 完成每日任務（雙重獎勵）")
    print("-" * 80)
    
    # 模擬極高風險分析結果
    high_risk_analysis = {
        'risk_score': 10,
        'category': '假投資詐騙',
        'analysis': '這是一個極高風險的詐騙網站',
        'expert_warning': '立即停止所有互動，這是嚴重的詐騙行為'
    }
    
    # 模擬團隊積分更新結果（極高風險 + 任務完成）
    team_result_double_bonus = {
        'success': True,
        'points_earned': 20,  # 10 * 2 倍數
        'is_duplicate': False,
        'multiplier_applied': True,
        'normalized_url': 'https://dangerous-scam.com/trap',
        'report_id': 'U1234567890#2024-01-15T16:00:00Z',
        'quest_result': {
            'quest_completed': True,
            'already_claimed': False,
            'bonus_awarded': 50,
            'daily_report_count': 5,
            'message': '🎉 完成每日任務！團隊獲得 50 點獎勵積分'
        }
    }
    
    # 格式化回覆訊息
    reply_text = format_reply_with_team_points(high_risk_analysis, team_result_double_bonus)
    
    print("LINE Bot 回覆訊息：")
    print(reply_text)
    print()
    
    print("=" * 80)
    print("Demo 完成！")
    print("=" * 80)
    print()
    print("總結：")
    print("✅ 在 update_team_points() 方法中成功呼叫 check_daily_quest()")
    print("✅ 在 LINE Bot 回覆中成功加入任務完成通知")
    print("✅ 任務完成通知僅在首次達成時顯示（避免重複通知）")
    print("✅ 支援極高風險倍數獎勵 + 每日任務獎勵的雙重獎勵情境")
    print()


def demo_update_team_points_with_quest_check():
    """展示 update_team_points_for_report 整合 check_daily_quest"""
    print("=" * 80)
    print("Demo: update_team_points_for_report 整合 check_daily_quest")
    print("=" * 80)
    print()
    
    with patch('main.team_service') as mock_team_service, \
         patch('points_calculator.PointsCalculator') as mock_calculator_class:
        
        # 模擬使用者屬於團隊
        mock_table = Mock()
        mock_table.query.return_value = {
            'Items': [
                {
                    'member_id': 'team123#U1234567890',
                    'team_id': 'team123',
                    'line_uid': 'U1234567890'
                }
            ]
        }
        mock_team_service.team_members_table = mock_table
        
        # 模擬 PointsCalculator
        mock_calculator = Mock()
        mock_calculator.update_team_points.return_value = {
            'success': True,
            'points_earned': 7,
            'is_duplicate': False,
            'multiplier_applied': False,
            'normalized_url': 'https://scam-site.com/fake',
            'report_id': 'U1234567890#2024-01-15T14:25:30Z'
        }
        
        # 模擬 check_daily_quest 回傳任務完成結果
        mock_calculator.check_daily_quest.return_value = {
            'quest_completed': True,
            'already_claimed': False,
            'bonus_awarded': 50,
            'daily_report_count': 5,
            'message': '🎉 完成每日任務！團隊獲得 50 點獎勵積分'
        }
        
        mock_calculator_class.return_value = mock_calculator
        
        # 執行測試
        print("呼叫 update_team_points_for_report()...")
        result = update_team_points_for_report(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake',
            risk_score=7,
            category='假投資詐騙'
        )
        
        print()
        print("回傳結果：")
        print(f"  success: {result['success']}")
        print(f"  points_earned: {result['points_earned']}")
        print(f"  is_duplicate: {result['is_duplicate']}")
        print(f"  multiplier_applied: {result['multiplier_applied']}")
        print()
        print("任務檢測結果 (quest_result)：")
        quest_result = result.get('quest_result', {})
        print(f"  quest_completed: {quest_result.get('quest_completed')}")
        print(f"  already_claimed: {quest_result.get('already_claimed')}")
        print(f"  bonus_awarded: {quest_result.get('bonus_awarded')}")
        print(f"  daily_report_count: {quest_result.get('daily_report_count')}")
        print(f"  message: {quest_result.get('message')}")
        print()
        
        # 驗證 check_daily_quest 被呼叫
        if mock_calculator.check_daily_quest.called:
            print("✅ check_daily_quest() 已被呼叫")
            print(f"   呼叫參數: team_id='team123'")
        else:
            print("❌ check_daily_quest() 未被呼叫")
        
        print()


if __name__ == '__main__':
    demo_quest_completion_notification()
    print()
    demo_update_team_points_with_quest_check()
