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

from main import (
    update_team_points_for_report,
    format_reply_with_team_points,
    format_reply_message,
    build_mass_report_context,
    handle_text,
    trigger_mass_report_check,
    save_scam_report,
)


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

    def test_format_reply_message_shows_team_notice_when_message_has_no_url(self):
        """測試有團隊但未附 URL 時，回覆會明確說明不累計團隊積分"""
        analysis = {
            'risk_score': 5,
            'category': '可疑訊息',
            'analysis': '這是一個需要小心的訊息',
            'expert_warning': '請勿提供個人資料'
        }

        reply = format_reply_message(
            analysis,
            has_team=True,
            team_points_eligible=False
        )

        assert '團隊積分提醒' in reply
        assert '未包含 URL' in reply
        assert '只會記入個人分數' in reply

    def test_format_reply_with_team_points_shows_error_when_team_update_failed(self):
        """測試團隊積分更新失敗時，回覆不再靜默降級"""
        analysis = {
            'risk_score': 8,
            'category': '假投資詐騙',
            'analysis': '這是一個高風險的詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }

        team_result = {
            'success': False,
            'points_earned': 0,
            'is_duplicate': False,
            'multiplier_applied': False,
            'error': '團隊積分更新失敗: TeamMembers update failed'
        }

        reply = format_reply_with_team_points(analysis, team_result)

        assert '團隊積分更新失敗' in reply
        assert '個人分析' in reply
        assert 'TeamMembers update failed' in reply
    
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

    def test_build_mass_report_context_uses_team_report_when_report_saved(self):
        """測試團隊通報成功寫入時直接沿用 normalized_url"""
        context = build_mass_report_context(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake',
            risk_score=7,
            category='假投資詐騙',
            team_result={
                'report_id': 'U123#2024-01-01T00:00:00',
                'normalized_url': 'https://scam-site.com/fake',
                'is_duplicate': False
            }
        )

        assert context == {'normalized_url': 'https://scam-site.com/fake'}

    @patch('main.save_scam_report')
    @patch('points_calculator.PointsCalculator')
    def test_build_mass_report_context_saves_non_team_report(self, mock_calculator_class, mock_save_report):
        """測試非團隊使用者仍會寫入 ScamReports 並建立 mass report context"""
        mock_calculator = Mock()
        mock_calculator.normalize_url.return_value = 'https://scam-site.com/fake'
        mock_calculator_class.return_value = mock_calculator

        context = build_mass_report_context(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake?ref=1',
            risk_score=8,
            category='假投資詐騙',
            team_result=None
        )

        assert context == {'normalized_url': 'https://scam-site.com/fake'}
        mock_save_report.assert_called_once_with(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake?ref=1',
            normalized_url='https://scam-site.com/fake',
            risk_score=8,
            category='假投資詐騙'
        )

    @patch('main.dynamodb')
    def test_save_scam_report_omits_team_id_for_non_team_users(self, mock_dynamodb):
        """測試非團隊通報寫入 ScamReports 時不帶 team_id 欄位"""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        save_scam_report(
            reporter_uid='U1234567890',
            url='https://scam-site.com/fake?ref=1',
            normalized_url='https://scam-site.com/fake',
            risk_score=8,
            category='假投資詐騙'
        )

        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args.kwargs['Item']
        assert item['reporter_uid'] == 'U1234567890'
        assert item['normalized_url'] == 'https://scam-site.com/fake'
        assert 'team_id' not in item

    @patch('main.threading.Thread')
    @patch('main.process_mass_report')
    @patch('main.get_report_count')
    def test_trigger_mass_report_check_runs_in_background(self, mock_get_report_count, mock_process_mass_report, mock_thread):
        """測試大量通報檢查以背景執行方式觸發"""
        mock_get_report_count.return_value = 11

        thread_target = None

        def capture_thread(*args, **kwargs):
            nonlocal thread_target
            thread_target = kwargs['target']
            thread = Mock()
            thread.start.side_effect = lambda: thread_target()
            return thread

        mock_thread.side_effect = capture_thread

        trigger_mass_report_check('https://scam-site.com/fake')

        mock_get_report_count.assert_called_once_with('https://scam-site.com/fake')
        mock_process_mass_report.assert_called_once_with(
            normalized_url='https://scam-site.com/fake',
            current_report_count=11
        )

    @patch('main.reply_message')
    @patch('main.trigger_mass_report_check')
    @patch('main.build_mass_report_context')
    @patch('main.update_team_points_for_report')
    @patch('main.get_user_team_membership')
    @patch('main.add_detection_record')
    @patch('main.analyze_scam_content')
    def test_handle_text_replies_before_triggering_mass_report(
        self,
        mock_analyze,
        mock_add_detection_record,
        mock_get_user_team_membership,
        mock_update_team_points,
        mock_build_context,
        mock_trigger_mass_report_check,
        mock_reply_message
    ):
        """測試使用者先收到標準回覆，再觸發大量通報背景檢查"""
        mock_analyze.return_value = {
            'risk_score': 8,
            'category': '假投資詐騙',
            'analysis': ['測試分析'],
            'expert_warning': '請勿點擊連結'
        }
        mock_update_team_points.return_value = {
            'success': True,
            'points_earned': 8,
            'multiplier_applied': False
        }
        mock_build_context.return_value = {'normalized_url': 'https://scam-site.com/fake'}
        mock_get_user_team_membership.return_value = {'team_id': 'team123'}

        call_order = []
        mock_reply_message.side_effect = lambda *args, **kwargs: call_order.append('reply')
        mock_trigger_mass_report_check.side_effect = lambda *args, **kwargs: call_order.append('trigger')

        event = Mock()
        event.message.text = '請幫我看 https://scam-site.com/fake'
        event.source.user_id = 'U1234567890'
        event.reply_token = 'reply-token'

        handle_text(event)

        assert call_order == ['reply', 'trigger']
        mock_trigger_mass_report_check.assert_called_once_with(normalized_url='https://scam-site.com/fake')

    @patch('main.reply_message')
    @patch('main.get_user_team_membership')
    @patch('main.add_detection_record')
    @patch('main.analyze_scam_content')
    def test_handle_text_shows_team_notice_for_team_member_without_url(
        self,
        mock_analyze,
        mock_add_detection_record,
        mock_get_user_team_membership,
        mock_reply_message
    ):
        """測試有團隊的使用者傳送非 URL 訊息時，會收到團隊不計分提醒"""
        mock_analyze.return_value = {
            'risk_score': 4,
            'category': '可疑訊息',
            'analysis': ['測試分析'],
            'expert_warning': '請勿提供個資'
        }
        mock_get_user_team_membership.return_value = {'team_id': 'team123'}

        event = Mock()
        event.message.text = '這段訊息感覺很可疑'
        event.source.user_id = 'U1234567890'
        event.reply_token = 'reply-token'

        handle_text(event)

        mock_reply_message.assert_called_once()
        reply_text = mock_reply_message.call_args.args[1]
        assert '團隊積分提醒' in reply_text
        assert '未包含 URL' in reply_text

    @patch('main.reply_message')
    @patch('main.rate_limiter')
    @patch('main.analyze_scam_content')
    def test_handle_text_rejects_when_rate_limit_exceeded(
        self,
        mock_analyze,
        mock_rate_limiter,
        mock_reply_message
    ):
        """測試超過 rate limit 時會立即回覆且不進入分析流程"""
        mock_rate_limiter.allow_request.return_value = False

        event = Mock()
        event.message.text = 'https://scam-site.com/fake'
        event.source.user_id = 'U1234567890'
        event.reply_token = 'reply-token'

        handle_text(event)

        mock_reply_message.assert_called_once()
        mock_analyze.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
