"""Unit tests for MassReportAlert Pydantic model"""
import pytest
from datetime import datetime
import uuid
from pydantic import ValidationError
from models import MassReportAlert


def test_valid_mass_report_alert():
    """Test creating a valid MassReportAlert instance"""
    alert_id = str(uuid.uuid4())
    alert = MassReportAlert(
        alert_id=alert_id,
        normalized_url="http://scam-site.com/fake",
        report_count=10,
        alert_summary="詐騙摘要",
        alert_warning="警示訊息",
        notified_user_count=100,
        created_at=datetime.now(),
        status="completed"
    )
    
    assert alert.alert_id == alert_id
    assert alert.normalized_url == "http://scam-site.com/fake"
    assert alert.report_count == 10
    assert alert.status == "completed"


def test_invalid_alert_id_format():
    """Test that alert_id must be valid UUID format"""
    with pytest.raises(ValidationError) as exc_info:
        MassReportAlert(
            alert_id="not-a-uuid",
            normalized_url="http://scam-site.com/fake",
            report_count=10,
            alert_summary="詐騙摘要",
            alert_warning="警示訊息",
            notified_user_count=100,
            created_at=datetime.now(),
            status="completed"
        )
    
    assert "alert_id must be a valid UUID format" in str(exc_info.value)


def test_report_count_below_threshold():
    """Test that report_count must be >= 10"""
    alert_id = str(uuid.uuid4())
    
    with pytest.raises(ValidationError) as exc_info:
        MassReportAlert(
            alert_id=alert_id,
            normalized_url="http://scam-site.com/fake",
            report_count=9,  # Below threshold
            alert_summary="詐騙摘要",
            alert_warning="警示訊息",
            notified_user_count=100,
            created_at=datetime.now(),
            status="completed"
        )
    
    assert "report_count must be greater than or equal to 10" in str(exc_info.value)


def test_invalid_status():
    """Test that status must be one of the allowed values"""
    alert_id = str(uuid.uuid4())
    
    with pytest.raises(ValidationError) as exc_info:
        MassReportAlert(
            alert_id=alert_id,
            normalized_url="http://scam-site.com/fake",
            report_count=10,
            alert_summary="詐騙摘要",
            alert_warning="警示訊息",
            notified_user_count=100,
            created_at=datetime.now(),
            status="invalid_status"  # Invalid status
        )
    
    # Pydantic Literal validation error
    assert "status" in str(exc_info.value).lower()


def test_all_valid_statuses():
    """Test that all valid status values are accepted"""
    alert_id = str(uuid.uuid4())
    valid_statuses = ["pending", "processing", "completed", "failed"]
    
    for status in valid_statuses:
        alert = MassReportAlert(
            alert_id=alert_id,
            normalized_url="http://scam-site.com/fake",
            report_count=10,
            alert_summary="詐騙摘要",
            alert_warning="警示訊息",
            notified_user_count=100,
            created_at=datetime.now(),
            status=status
        )
        assert alert.status == status


def test_report_count_at_threshold():
    """Test that report_count exactly at threshold (10) is valid"""
    alert_id = str(uuid.uuid4())
    alert = MassReportAlert(
        alert_id=alert_id,
        normalized_url="http://scam-site.com/fake",
        report_count=10,
        alert_summary="詐騙摘要",
        alert_warning="警示訊息",
        notified_user_count=100,
        created_at=datetime.now(),
        status="pending"
    )
    
    assert alert.report_count == 10


def test_report_count_above_threshold():
    """Test that report_count above threshold is valid"""
    alert_id = str(uuid.uuid4())
    alert = MassReportAlert(
        alert_id=alert_id,
        normalized_url="http://scam-site.com/fake",
        report_count=50,
        alert_summary="詐騙摘要",
        alert_warning="警示訊息",
        notified_user_count=100,
        created_at=datetime.now(),
        status="completed"
    )
    
    assert alert.report_count == 50
