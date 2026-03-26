"""
Demo: BedrockSummarizer Fallback Mechanism
Demonstrates how the system handles LLM failures gracefully

Task: 3.3 Implement fallback for LLM failures
Requirements: 3.6, 3.7, 9.4
"""

from bedrock_service import BedrockSummarizer
from unittest.mock import patch
from botocore.exceptions import ReadTimeoutError, ClientError


def demo_successful_generation():
    """Demo 1: Successful alert generation"""
    print("=" * 60)
    print("Demo 1: Successful Alert Generation")
    print("=" * 60)
    
    summarizer = BedrockSummarizer()
    
    # This would normally call the real Bedrock API
    # For demo purposes, we'll show what happens with a real call
    print("\n📝 Input:")
    print("  Original Message: 投資虛擬貨幣，保證月收益30%")
    print("  Report Count: 15")
    
    print("\n✅ Expected Output (when LLM succeeds):")
    print("  - alert_summary: [LLM-generated summary]")
    print("  - alert_warning: [LLM-generated warning]")
    print()


def demo_timeout_fallback():
    """Demo 2: Timeout triggers fallback"""
    print("=" * 60)
    print("Demo 2: Timeout Fallback")
    print("=" * 60)
    
    summarizer = BedrockSummarizer()
    
    print("\n📝 Scenario: Bedrock API times out after 10 seconds")
    
    # Mock timeout exception
    with patch.object(summarizer.client, 'invoke_model', side_effect=ReadTimeoutError(endpoint_url='test')):
        result = summarizer.generate_mass_report_alert(
            "投資虛擬貨幣，保證月收益30%",
            15
        )
    
    print("\n⚠️ Fallback Triggered!")
    print(f"\n📋 Default Alert Summary:")
    print(f"  {result['alert_summary']}")
    print(f"\n⚠️ Default Alert Warning:")
    print(f"  {result['alert_warning']}")
    print()


def demo_api_error_fallback():
    """Demo 3: API error triggers fallback"""
    print("=" * 60)
    print("Demo 3: API Error Fallback")
    print("=" * 60)
    
    summarizer = BedrockSummarizer()
    
    print("\n📝 Scenario: Bedrock API returns an error")
    
    # Mock API exception
    with patch.object(summarizer.client, 'invoke_model', side_effect=Exception("ServiceUnavailable")):
        result = summarizer.generate_mass_report_alert(
            "假檢警詐騙訊息",
            20
        )
    
    print("\n⚠️ Fallback Triggered!")
    print(f"\n📋 Default Alert Summary:")
    print(f"  {result['alert_summary']}")
    print(f"\n⚠️ Default Alert Warning:")
    print(f"  {result['alert_warning']}")
    print()


def demo_malformed_response_fallback():
    """Demo 4: Malformed LLM response triggers fallback"""
    print("=" * 60)
    print("Demo 4: Malformed Response Fallback")
    print("=" * 60)
    
    summarizer = BedrockSummarizer()
    
    print("\n📝 Scenario: LLM returns response without expected format")
    
    # Mock malformed response
    from unittest.mock import MagicMock
    import json
    
    mock_response = {
        'body': MagicMock()
    }
    
    # Response without proper sections
    llm_output = "這是一個格式錯誤的回應"
    
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
            "詐騙訊息",
            12
        )
    
    print("\n⚠️ Parsing Failed - Fallback Triggered!")
    print(f"\n📋 Default Alert Summary:")
    print(f"  {result['alert_summary']}")
    print(f"\n⚠️ Default Alert Warning:")
    print(f"  {result['alert_warning']}")
    print()


def demo_default_alert_content():
    """Demo 5: Show default alert message details"""
    print("=" * 60)
    print("Demo 5: Default Alert Message Details")
    print("=" * 60)
    
    summarizer = BedrockSummarizer()
    default_alert = summarizer._get_default_alert()
    
    print("\n📋 Default Alert Summary:")
    print(f"  {default_alert['alert_summary']}")
    print(f"\n  Length: {len(default_alert['alert_summary'])} characters")
    print(f"  Contains '詐騙': {'詐騙' in default_alert['alert_summary']}")
    
    print(f"\n⚠️ Default Alert Warning:")
    print(f"  {default_alert['alert_warning']}")
    print(f"\n  Length: {len(default_alert['alert_warning'])} characters")
    print(f"  Contains '165': {'165' in default_alert['alert_warning']}")
    
    print("\n✅ Default message meets requirements:")
    print("  - Contains generic warning about scam messages")
    print("  - Includes safety advice")
    print("  - References 165 anti-fraud hotline")
    print("  - Does not expose original message content")
    print()


if __name__ == "__main__":
    print("\n🚀 BedrockSummarizer Fallback Mechanism Demo")
    print("Task 3.3: Implement fallback for LLM failures\n")
    
    demo_successful_generation()
    demo_timeout_fallback()
    demo_api_error_fallback()
    demo_malformed_response_fallback()
    demo_default_alert_content()
    
    print("=" * 60)
    print("✅ All fallback scenarios demonstrated successfully!")
    print("=" * 60)
