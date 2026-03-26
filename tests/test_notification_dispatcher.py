"""
Unit tests for NotificationDispatcher
Tests the notification dispatcher component for mass report alerts
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from notification_dispatcher import (
    NotificationDispatcher,
    format_mass_report_notification,
    MAX_LINE_MESSAGE_LENGTH,
    DEFAULT_ALERT_SUMMARY,
    DEFAULT_ALERT_WARNING,
)


class TestNotificationDispatcher:
    """Test suite for NotificationDispatcher class"""
    
    def test_initialization(self):
        """Test NotificationDispatcher can be initialized"""
        dispatcher = NotificationDispatcher()
        
        assert dispatcher is not None
        assert dispatcher.configuration is not None
        assert dispatcher.scam_reports_table is not None
        assert dispatcher.team_members_table is not None
    
    def test_get_all_active_users_returns_list(self):
        """Test get_all_active_users returns a list"""
        dispatcher = NotificationDispatcher()
        
        users = dispatcher.get_all_active_users()
        
        assert isinstance(users, list)
    
    def test_get_all_active_users_filters_valid_uids(self):
        """Test get_all_active_users only returns UIDs starting with 'U'"""
        dispatcher = NotificationDispatcher()
        
        # Mock the table scan to return test data
        mock_reports_response = {
            'Items': [
                {'reporter_uid': 'U1234567890'},
                {'reporter_uid': 'U0987654321'},
                {'reporter_uid': 'InvalidUID'},  # Should be filtered out
                {'reporter_uid': 'B1234567890'},  # Should be filtered out
            ]
        }
        
        mock_members_response = {
            'Items': [
                {'line_uid': 'U1111111111'},
                {'line_uid': 'U2222222222'},
            ]
        }
        
        with patch.object(dispatcher.scam_reports_table, 'scan', return_value=mock_reports_response):
            with patch.object(dispatcher.team_members_table, 'scan', return_value=mock_members_response):
                users = dispatcher.get_all_active_users()
        
        # Should only include valid UIDs starting with 'U'
        assert 'U1234567890' in users
        assert 'U0987654321' in users
        assert 'U1111111111' in users
        assert 'U2222222222' in users
        assert 'InvalidUID' not in users
        assert 'B1234567890' not in users
    
    def test_get_all_active_users_returns_empty_when_no_users(self):
        """Test get_all_active_users returns empty list when no active users"""
        dispatcher = NotificationDispatcher()
        
        # Mock empty responses
        mock_empty_response = {'Items': []}
        
        with patch.object(dispatcher.scam_reports_table, 'scan', return_value=mock_empty_response):
            with patch.object(dispatcher.team_members_table, 'scan', return_value=mock_empty_response):
                users = dispatcher.get_all_active_users()
        
        assert users == []
    
    def test_get_all_active_users_deduplicates(self):
        """Test get_all_active_users removes duplicate UIDs"""
        dispatcher = NotificationDispatcher()
        
        # Mock responses with duplicate UIDs
        mock_reports_response = {
            'Items': [
                {'reporter_uid': 'U1234567890'},
                {'reporter_uid': 'U1234567890'},  # Duplicate
                {'reporter_uid': 'U0987654321'},
            ]
        }
        
        mock_members_response = {
            'Items': [
                {'line_uid': 'U1234567890'},  # Also in reports
                {'line_uid': 'U1111111111'},
            ]
        }
        
        with patch.object(dispatcher.scam_reports_table, 'scan', return_value=mock_reports_response):
            with patch.object(dispatcher.team_members_table, 'scan', return_value=mock_members_response):
                users = dispatcher.get_all_active_users()
        
        # Should have 3 unique users
        assert len(users) == 3
        assert 'U1234567890' in users
        assert 'U0987654321' in users
        assert 'U1111111111' in users

    def test_get_all_active_users_handles_pagination(self):
        """Test get_all_active_users combines paginated scan results"""
        dispatcher = NotificationDispatcher()

        paged_reports = [
            {
                'Items': [{'reporter_uid': 'U1234567890'}],
                'LastEvaluatedKey': {'report_id': 'r1'}
            },
            {
                'Items': [{'reporter_uid': 'U0987654321'}]
            }
        ]
        paged_members = [
            {
                'Items': [{'line_uid': 'U1111111111'}],
                'LastEvaluatedKey': {'member_id': 'm1'}
            },
            {
                'Items': [{'line_uid': 'U2222222222'}]
            }
        ]

        with patch.object(dispatcher.scam_reports_table, 'scan', side_effect=paged_reports):
            with patch.object(dispatcher.team_members_table, 'scan', side_effect=paged_members):
                users = dispatcher.get_all_active_users()

        assert users == ['U0987654321', 'U1111111111', 'U1234567890', 'U2222222222']

    def test_get_all_active_users_ignores_non_string_values(self):
        """Test get_all_active_users ignores malformed non-string IDs"""
        dispatcher = NotificationDispatcher()

        mock_reports_response = {
            'Items': [
                {'reporter_uid': None},
                {'reporter_uid': 12345},
                {'reporter_uid': 'U1234567890'},
            ]
        }
        mock_members_response = {
            'Items': [
                {'line_uid': ['U-not-valid']},
                {'line_uid': 'U2222222222'},
            ]
        }

        with patch.object(dispatcher.scam_reports_table, 'scan', return_value=mock_reports_response):
            with patch.object(dispatcher.team_members_table, 'scan', return_value=mock_members_response):
                users = dispatcher.get_all_active_users()

        assert users == ['U1234567890', 'U2222222222']
    
    def test_broadcast_mass_report_alert_with_no_users(self):
        """Test broadcast_mass_report_alert returns zero counts when no users"""
        dispatcher = NotificationDispatcher()
        
        # Mock get_all_active_users to return empty list
        with patch.object(dispatcher, 'get_all_active_users', return_value=[]):
            result = dispatcher.broadcast_mass_report_alert("Test message")
        
        assert result['success_count'] == 0
        assert result['failed_count'] == 0
        assert result['failed_users'] == []
    
    def test_send_push_message_with_empty_list(self):
        """Test send_push_message handles empty user list"""
        dispatcher = NotificationDispatcher()
        
        result = dispatcher.send_push_message([], "Test message")
        
        assert result['success_count'] == 0
        assert result['failed_count'] == 0
        assert result['failed_users'] == []
    
    @patch('notification_dispatcher.MessagingApi')
    @patch('notification_dispatcher.ApiClient')
    def test_send_push_message_splits_into_batches(self, mock_api_client, mock_messaging_api):
        """Test send_push_message splits large user lists into batches of 500"""
        dispatcher = NotificationDispatcher()
        
        # Create a list of 1200 users (should split into 3 batches: 500, 500, 200)
        user_ids = [f'U{str(i).zfill(10)}' for i in range(1200)]
        
        # Mock the LINE API
        mock_api_instance = MagicMock()
        mock_messaging_api.return_value = mock_api_instance
        mock_api_client.return_value.__enter__.return_value = mock_api_instance
        
        result = dispatcher.send_push_message(user_ids, "Test message")
        
        # Should have called multicast 3 times (for 3 batches)
        assert mock_api_instance.multicast.call_count == 3
        
        # Verify batch sizes
        calls = mock_api_instance.multicast.call_args_list
        assert len(calls[0][1]['multicast_request'].to) == 500  # First batch
        assert len(calls[1][1]['multicast_request'].to) == 500  # Second batch
        assert len(calls[2][1]['multicast_request'].to) == 200  # Third batch
        
        # All should succeed
        assert result['success_count'] == 1200
        assert result['failed_count'] == 0
    
    @patch('notification_dispatcher.MessagingApi')
    @patch('notification_dispatcher.ApiClient')
    def test_send_push_message_retries_on_batch_failure(self, mock_api_client, mock_messaging_api):
        """Test send_push_message retries individual users when batch fails"""
        dispatcher = NotificationDispatcher()
        
        user_ids = ['U1234567890', 'U0987654321', 'U1111111111']
        
        # Mock the LINE API
        mock_api_instance = MagicMock()
        mock_messaging_api.return_value = mock_api_instance
        mock_api_client.return_value.__enter__.return_value = mock_api_instance
        
        # Make multicast fail
        from linebot.v3.exceptions import BaseError
        mock_api_instance.multicast.side_effect = BaseError("Batch failed")
        
        # Make individual push_message succeed
        mock_api_instance.push_message.return_value = None
        
        result = dispatcher.send_push_message(user_ids, "Test message")
        
        # Should have tried multicast once
        assert mock_api_instance.multicast.call_count == 1
        
        # Should have retried with individual push_message for each user
        assert mock_api_instance.push_message.call_count == 3
        
        # All should succeed via retry
        assert result['success_count'] == 3
        assert result['failed_count'] == 0

    @patch('notification_dispatcher.MessagingApi')
    @patch('notification_dispatcher.ApiClient')
    def test_send_push_message_tracks_failed_users_after_retry(self, mock_api_client, mock_messaging_api):
        """Test send_push_message records failed users when individual retry also fails"""
        dispatcher = NotificationDispatcher()

        user_ids = ['U1234567890', 'U0987654321', 'U1111111111']

        mock_api_instance = MagicMock()
        mock_messaging_api.return_value = mock_api_instance
        mock_api_client.return_value.__enter__.return_value = mock_api_instance

        from linebot.v3.exceptions import BaseError
        mock_api_instance.multicast.side_effect = BaseError("Batch failed")
        mock_api_instance.push_message.side_effect = [
            None,
            BaseError("Blocked user"),
            BaseError("Invalid user"),
        ]

        result = dispatcher.send_push_message(user_ids, "Test message")

        assert result['success_count'] == 1
        assert result['failed_count'] == 2
        assert result['failed_users'] == ['U0987654321', 'U1111111111']

    @patch('notification_dispatcher.MessagingApi')
    @patch('notification_dispatcher.ApiClient')
    def test_send_push_message_marks_invalid_user_ids_as_failed_without_api_calls(self, mock_api_client, mock_messaging_api):
        """Test invalid LINE user IDs are filtered out and counted as failures"""
        dispatcher = NotificationDispatcher()

        user_ids = ['U1234567890', 'bad-user', None, 'C123']

        mock_api_instance = MagicMock()
        mock_messaging_api.return_value = mock_api_instance
        mock_api_client.return_value.__enter__.return_value = mock_api_instance

        result = dispatcher.send_push_message(user_ids, "Test message")

        assert mock_api_instance.multicast.call_count == 1
        sent_batch = mock_api_instance.multicast.call_args[1]['multicast_request'].to
        assert sent_batch == ['U1234567890']
        assert result['success_count'] == 1
        assert result['failed_count'] == 3
        assert result['failed_users'] == ['bad-user', None, 'C123']

    @patch('notification_dispatcher.MessagingApi')
    @patch('notification_dispatcher.ApiClient')
    def test_send_push_message_keeps_accounting_on_unexpected_batch_error(self, mock_api_client, mock_messaging_api):
        """Test unexpected batch errors still produce complete success and failure accounting"""
        dispatcher = NotificationDispatcher()

        user_ids = ['U1234567890', 'U0987654321']

        mock_api_instance = MagicMock()
        mock_messaging_api.return_value = mock_api_instance
        mock_api_client.return_value.__enter__.return_value = mock_api_instance
        mock_api_instance.multicast.side_effect = RuntimeError("Service unavailable")

        result = dispatcher.send_push_message(user_ids, "Test message")

        assert result['success_count'] == 0
        assert result['failed_count'] == 2
        assert result['failed_users'] == user_ids
        assert result['success_count'] + result['failed_count'] == len(user_ids)
    
    @patch('notification_dispatcher.MessagingApi')
    @patch('notification_dispatcher.ApiClient')
    def test_broadcast_mass_report_alert_calls_send_push_message(self, mock_api_client, mock_messaging_api):
        """Test broadcast_mass_report_alert delegates to send_push_message"""
        dispatcher = NotificationDispatcher()
        
        # Mock get_all_active_users
        test_users = ['U1234567890', 'U0987654321']
        
        with patch.object(dispatcher, 'get_all_active_users', return_value=test_users):
            with patch.object(dispatcher, 'send_push_message', return_value={'success_count': 2, 'failed_count': 0, 'failed_users': []}) as mock_send:
                result = dispatcher.broadcast_mass_report_alert("Test alert")
        
        # Should have called send_push_message with correct arguments
        mock_send.assert_called_once_with(test_users, "Test alert")
        assert result['success_count'] == 2

    def test_broadcast_mass_report_alert_formats_message_from_components(self):
        """Test broadcast_mass_report_alert can format a message from summary, warning, and count"""
        dispatcher = NotificationDispatcher()

        test_users = ['U1234567890', 'U0987654321']

        with patch.object(dispatcher, 'get_all_active_users', return_value=test_users):
            with patch.object(dispatcher, 'send_push_message', return_value={'success_count': 2, 'failed_count': 0, 'failed_users': []}) as mock_send:
                dispatcher.broadcast_mass_report_alert(
                    alert_summary="常見手法是假冒投資老師要求加入外部群組。",
                    alert_warning="請勿依指示轉帳，並先向 165 查證。",
                    report_count=18,
                )

        sent_message = mock_send.call_args[0][1]
        assert "已有 18 位使用者通報相同詐騙訊息" in sent_message
        assert "常見手法是假冒投資老師要求加入外部群組。" in sent_message
        assert "請勿依指示轉帳，並先向 165 查證。" in sent_message


class TestFormatMassReportNotification:
    """Test suite for notification message formatting"""

    def test_format_mass_report_notification_includes_required_sections(self):
        """Test formatted notification contains required Traditional Chinese sections"""
        message = format_mass_report_notification(
            alert_summary="這類訊息常以高報酬投資為誘因，要求使用者加入外部群組。",
            alert_warning="請勿依指示轉帳或提供帳號密碼，並可先向 165 查證。",
            report_count=15,
        )

        assert "🚨 社群防詐警示" in message
        assert "已有 15 位使用者通報相同詐騙訊息" in message
        assert "⚠️ 風險摘要：" in message
        assert "💡 防範建議：" in message
        assert "📱 如收到類似訊息，請立即通報給我們。" in message

    def test_format_mass_report_notification_uses_default_content_when_blank(self):
        """Test blank summary or warning falls back to safe default text"""
        message = format_mass_report_notification(
            alert_summary="",
            alert_warning="   ",
            report_count=10,
        )

        assert DEFAULT_ALERT_SUMMARY in message
        assert DEFAULT_ALERT_WARNING in message

    def test_format_mass_report_notification_caps_length(self):
        """Test formatted notification never exceeds the LINE 5000-character limit"""
        long_summary = "詐騙摘要" * 2000
        long_warning = "防範建議" * 2000

        message = format_mass_report_notification(
            alert_summary=long_summary,
            alert_warning=long_warning,
            report_count=999,
        )

        assert len(message) <= MAX_LINE_MESSAGE_LENGTH
        assert "🚨 社群防詐警示" in message
        assert "💡 防範建議：" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
