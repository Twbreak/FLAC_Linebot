"""
測試 webhook handler 與團隊積分系統的整合
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import update_team_points_for_report, format_reply_with_team_points


class TestWebhookTeamIntegration:
    """測試 webhook handler 與團隊積分整合"""
    
    @patch('main.team_service')
    @patch('points_calculator.PointsCalculator')
    def test_update_team_points_for_report_success(self, mock_calculator_class, mock_team_service):
        """測試成功更新團隊積分"""
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
        
        # 模擬 PointsCalculator 回傳成功結果
        mock_calculator = Mock()
        mock_calculator.update_team_points.return_value = {
            'success': True,
            'points_earned': 18,
            'is_duplicate': False,
            'multiplier_applied': True,
            'normalized_url': 'https://scam-site.com/fake',
            'report_id': 'U1234567890#2024-01-15T14:25:30Z',
            'message': '成功通報！獲得 18 積分 (極高風險 2x 獎勵)'
        }
        mock_calculator_class.return_value = mock_calculator
        
        # 執行測試
        result = update_team_points_for_report(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake?ref=123',
            risk_score=9,
            category='假投資詐騙'
        )
        
        # 驗證結果
        assert result is not None
        assert result['success'] is True
        assert result['points_earned'] == 18
        assert result['multiplier_applied'] is True
        
        # 驗證呼叫
        mock_table.query.assert_called_once()
        mock_calculator.update_team_points.assert_called_once_with(
            team_id='team123',
            member_uid='U1234567890',
            url='https://scam-site.com/fake?ref=123',
            risk_score=9,
            category='假投資詐騙'
        )
    
    @patch('main.team_service')
    def test_update_team_points_for_report_no_team(self, mock_team_service):
        """測試使用者不屬於任何團隊"""
        # 模擬使用者不屬於任何團隊
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_team_service.team_members_table = mock_table
        
        # 執行測試
        result = update_team_points_for_report(
            reporter_uid='U9999999999',
            url='https://scam-site.com/fake',
            risk_score=7,
            category='假投資詐騙'
        )
        
        # 驗證結果
        assert result is None
        
        # 驗證呼叫
        mock_table.query.assert_called_once()
    
    @patch('main.team_service')
    @patch('points_calculator.PointsCalculator')
    def test_update_team_points_for_report_duplicate(self, mock_calculator_class, mock_team_service):
        """測試重複通報不獲得積分"""
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
        
        # 模擬 PointsCalculator 回傳重複通報結果
        mock_calculator = Mock()
        mock_calculator.update_team_points.return_value = {
            'success': False,
            'points_earned': 0,
            'is_duplicate': True,
            'multiplier_applied': False,
            'normalized_url': 'https://scam-site.com/fake',
            'message': '此 URL 已被通報'
        }
        mock_calculator_class.return_value = mock_calculator
        
        # 執行測試
        result = update_team_points_for_report(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake',
            risk_score=7,
            category='假投資詐騙'
        )
        
        # 驗證結果
        assert result is not None
        assert result['success'] is False
        assert result['points_earned'] == 0
        assert result['is_duplicate'] is True
    
    def test_format_reply_with_team_points_success(self):
        """測試格式化包含團隊積分的回覆訊息（成功獲得積分）"""
        analysis = {
            'risk_score': 9,
            'category': '假投資詐騙',
            'analysis': '這是一個高風險的詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }
        
        team_result = {
            'success': True,
            'points_earned': 18,
            'is_duplicate': False,
            'multiplier_applied': True
        }
        
        reply = format_reply_with_team_points(analysis, team_result)
        
        # 驗證回覆訊息包含必要資訊
        assert '🚨' in reply  # 高風險表情符號
        assert '9/10' in reply
        assert '假投資詐騙' in reply
        assert '請勿點擊連結或提供個人資訊' in reply
        assert '🏆 團隊積分更新' in reply
        assert '18 積分' in reply
        assert '極高風險 2x 獎勵' in reply
    
    def test_format_reply_with_team_points_duplicate(self):
        """測試格式化包含團隊積分的回覆訊息（重複通報）"""
        analysis = {
            'risk_score': 7,
            'category': '假投資詐騙',
            'analysis': '這是一個高風險的詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }
        
        team_result = {
            'success': False,
            'points_earned': 0,
            'is_duplicate': True,
            'multiplier_applied': False
        }
        
        reply = format_reply_with_team_points(analysis, team_result)
        
        # 驗證回覆訊息包含必要資訊
        assert '🚨' in reply  # 高風險表情符號
        assert '7/10' in reply
        assert '假投資詐騙' in reply
        assert '🏆 團隊積分更新' in reply
        assert '此 URL 已被通報' in reply
        assert '未獲得積分' in reply
    
    def test_format_reply_with_team_points_no_multiplier(self):
        """測試格式化包含團隊積分的回覆訊息（無倍數獎勵）"""
        analysis = {
            'risk_score': 6,
            'category': '假投資詐騙',
            'analysis': '這是一個中風險的詐騙網站',
            'expert_warning': '請小心查證'
        }
        
        team_result = {
            'success': True,
            'points_earned': 6,
            'is_duplicate': False,
            'multiplier_applied': False
        }
        
        reply = format_reply_with_team_points(analysis, team_result)
        
        # 驗證回覆訊息包含必要資訊
        assert '⚠️' in reply  # 中風險表情符號
        assert '6/10' in reply
        assert '🏆 團隊積分更新' in reply
        assert '6 積分' in reply
        assert '極高風險 2x 獎勵' not in reply  # 不應包含倍數獎勵訊息
    
    def test_format_reply_with_team_points_quest_completed(self):
        """測試格式化包含每日任務完成通知的回覆訊息"""
        analysis = {
            'risk_score': 7,
            'category': '假投資詐騙',
            'analysis': '這是一個高風險的詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }
        
        team_result = {
            'success': True,
            'points_earned': 7,
            'is_duplicate': False,
            'multiplier_applied': False,
            'quest_result': {
                'quest_completed': True,
                'already_claimed': False,
                'bonus_awarded': 50,
                'daily_report_count': 5,
                'message': '🎉 完成每日任務！團隊獲得 50 點獎勵積分'
            }
        }
        
        reply = format_reply_with_team_points(analysis, team_result)
        
        # 驗證回覆訊息包含必要資訊
        assert '🚨' in reply  # 高風險表情符號
        assert '7/10' in reply
        assert '🏆 團隊積分更新' in reply
        assert '7 積分' in reply
        assert '🎉 每日任務完成！' in reply
        assert '50 點獎勵積分' in reply
        assert '今日已通報 5 則 URL' in reply
    
    def test_format_reply_with_team_points_quest_already_claimed(self):
        """測試格式化回覆訊息（每日任務已完成且已領取）"""
        analysis = {
            'risk_score': 7,
            'category': '假投資詐騙',
            'analysis': '這是一個高風險的詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }
        
        team_result = {
            'success': True,
            'points_earned': 7,
            'is_duplicate': False,
            'multiplier_applied': False,
            'quest_result': {
                'quest_completed': True,
                'already_claimed': True,  # 已領取，不應顯示通知
                'bonus_awarded': 0,
                'daily_report_count': 0,
                'message': '今日任務已完成'
            }
        }
        
        reply = format_reply_with_team_points(analysis, team_result)
        
        # 驗證回覆訊息不包含任務完成通知
        assert '🚨' in reply  # 高風險表情符號
        assert '7/10' in reply
        assert '🏆 團隊積分更新' in reply
        assert '7 積分' in reply
        assert '🎉 每日任務完成！' not in reply  # 不應包含任務完成通知
        assert '50 點獎勵積分' not in reply
    
    @patch('main.team_service')
    @patch('points_calculator.PointsCalculator')
    def test_update_team_points_with_quest_check(self, mock_calculator_class, mock_team_service):
        """測試更新團隊積分時檢查每日任務"""
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
        
        # 模擬 PointsCalculator 回傳成功結果
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
        result = update_team_points_for_report(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake',
            risk_score=7,
            category='假投資詐騙'
        )
        
        # 驗證結果
        assert result is not None
        assert result['success'] is True
        assert result['points_earned'] == 7
        assert 'quest_result' in result
        assert result['quest_result']['quest_completed'] is True
        assert result['quest_result']['bonus_awarded'] == 50
        
        # 驗證 check_daily_quest 被呼叫
        mock_calculator.check_daily_quest.assert_called_once_with(team_id='team123')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
