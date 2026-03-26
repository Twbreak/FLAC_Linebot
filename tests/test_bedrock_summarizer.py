"""
Unit tests for BedrockSummarizer.generate_mass_report_alert() method
Tests Requirements: 3.2, 3.3, 3.4, 3.7
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bedrock_service import BedrockSummarizer
import json
from botocore.exceptions import ReadTimeoutError, ConnectTimeoutError


class TestBedrockSummarizer:
    """Test suite for BedrockSummarizer class"""
    
    def test_init_configures_timeout(self):
        """Test that BedrockSummarizer initializes with 10-second timeout"""
        with patch('bedrock_service.boto3.client') as mock_client:
            summarizer = BedrockSummarizer()
            
            # Verify boto3.client was called with timeout config
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert 'config' in call_kwargs
            config = call_kwargs['config']
            assert config.read_timeout == 10
            assert config.connect_timeout == 10
    
    def test_generate_mass_report_alert_success(self):
        """Test successful alert generation with valid LLM response"""
        summarizer = BedrockSummarizer()
        
        # Mock successful Bedrock response
        mock_response = {
            'body': MagicMock()
        }
        
        # Use the exact format expected by the parser (without ### prefix)
        llm_output = """
警示摘要：
這是一則假投資詐騙訊息，宣稱高額回報並要求匯款至指定帳戶

防範建議：
切勿相信保證獲利的投資方案，避免匯款給陌生帳戶，如有疑慮請撥打 165 反詐騙專線
"""
        
        response_body = {
            'choices': [{
                'message': {
                    'content': llm_output
                }
            }]
        }
        
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        
        with patch.object(summarizer.client, 'invoke_model', return_value=mock_response):
            result = summarizer.generate_mass_report_alert(
                "這是一則詐騙訊息，請匯款到帳戶 123-456-789",
                15
            )
        
        # Verify result structure
        assert 'alert_summary' in result
        assert 'alert_warning' in result
        assert len(result['alert_summary']) > 0
        assert len(result['alert_warning']) > 0
        assert '假投資詐騙' in result['alert_summary']
        assert '165' in result['alert_warning']
    
    def test_generate_mass_report_alert_timeout(self):
        """Test that timeout triggers fallback to default message"""
        summarizer = BedrockSummarizer()
        
        # Mock timeout exception
        with patch.object(summarizer.client, 'invoke_model', side_effect=ReadTimeoutError(endpoint_url='test')):
            result = summarizer.generate_mass_report_alert(
                "詐騙訊息內容",
                10
            )
        
        # Verify fallback to default message
        assert result['alert_summary'] == "系統偵測到大量使用者通報相同詐騙訊息，該訊息可能包含詐騙連結或不實資訊"
        assert result['alert_warning'] == "請提高警覺，避免點擊可疑連結、提供個人資訊或進行任何金錢交易。如有疑慮請撥打 165 反詐騙專線"
    
    def test_generate_mass_report_alert_api_failure(self):
        """Test that API failures trigger fallback to default message"""
        summarizer = BedrockSummarizer()
        
        # Mock API exception
        with patch.object(summarizer.client, 'invoke_model', side_effect=Exception("API Error")):
            result = summarizer.generate_mass_report_alert(
                "詐騙訊息內容",
                10
            )
        
        # Verify fallback to default message
        assert result['alert_summary'] == "系統偵測到大量使用者通報相同詐騙訊息，該訊息可能包含詐騙連結或不實資訊"
        assert result['alert_warning'] == "請提高警覺，避免點擊可疑連結、提供個人資訊或進行任何金錢交易。如有疑慮請撥打 165 反詐騙專線"
    
    def test_generate_mass_report_alert_malformed_response(self):
        """Test handling of malformed LLM response"""
        summarizer = BedrockSummarizer()
        
        # Mock malformed response (missing expected sections)
        mock_response = {
            'body': MagicMock()
        }
        
        llm_output = "這是一個格式錯誤的回應，沒有正確的標題"
        
        response_body = {
            'choices': [{
                'message': {
                    'content': llm_output
                }
            }]
        }
        
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        
        with patch.object(summarizer.client, 'invoke_model', return_value=mock_response):
            result = summarizer.generate_mass_report_alert(
                "詐騙訊息內容",
                10
            )
        
        # Verify fallback to default message when parsing fails
        assert result['alert_summary'] == "系統偵測到大量使用者通報相同詐騙訊息，該訊息可能包含詐騙連結或不實資訊"
        assert result['alert_warning'] == "請提高警覺，避免點擊可疑連結、提供個人資訊或進行任何金錢交易。如有疑慮請撥打 165 反詐騙專線"
    
    def test_generate_mass_report_alert_constructs_correct_prompt(self):
        """Test that the method constructs the prompt with correct parameters"""
        summarizer = BedrockSummarizer()
        
        original_message = "測試詐騙訊息"
        report_count = 20
        
        mock_response = {
            'body': MagicMock()
        }
        
        response_body = {
            'choices': [{
                'message': {
                    'content': "### 警示摘要\n測試摘要\n\n### 防範建議\n測試建議"
                }
            }]
        }
        
        mock_response['body'].read.return_value = json.dumps(response_body).encode()
        
        with patch.object(summarizer.client, 'invoke_model', return_value=mock_response) as mock_invoke:
            result = summarizer.generate_mass_report_alert(original_message, report_count)
            
            # Verify invoke_model was called
            mock_invoke.assert_called_once()
            
            # Verify the request body contains the correct parameters
            call_args = mock_invoke.call_args
            body_str = call_args[1]['body']
            body = json.loads(body_str)
            
            # Check that the prompt includes report_count and original_message
            prompt_content = body['messages'][0]['content']
            assert str(report_count) in prompt_content
            assert original_message in prompt_content
    
    def test_default_alert_message_format(self):
        """Test that default alert message has correct format"""
        summarizer = BedrockSummarizer()
        default_alert = summarizer._get_default_alert()
        
        # Verify structure
        assert 'alert_summary' in default_alert
        assert 'alert_warning' in default_alert
        
        # Verify content is non-empty
        assert len(default_alert['alert_summary']) > 0
        assert len(default_alert['alert_warning']) > 0
        
        # Verify contains key safety information
        assert '詐騙' in default_alert['alert_summary']
        assert '165' in default_alert['alert_warning']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
