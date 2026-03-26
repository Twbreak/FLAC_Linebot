"""
Unit tests for ScamReport model with mass report fields
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from models import ScamReport


def test_scam_report_with_default_mass_report_fields():
    """Test ScamReport creation with default mass report fields"""
    report = ScamReport(
        report_id="report_123",
        url="http://scam-site.com/fake",
        normalized_url="http://scam-site.com/fake",
        reporter_uid="U123456",
        team_id="team_001",
        risk_score=85,
        category="投資詐騙",
        points_earned=10,
        reported_at=datetime.now()
    )
    
    assert report.is_mass_reported is False
    assert report.mass_report_alert_id is None


def test_scam_report_with_mass_report_fields_set():
    """Test ScamReport creation with mass report fields explicitly set"""
    report = ScamReport(
        report_id="report_456",
        url="http://scam-site.com/fake",
        normalized_url="http://scam-site.com/fake",
        reporter_uid="U789012",
        team_id="team_002",
        risk_score=90,
        category="釣魚詐騙",
        points_earned=15,
        reported_at=datetime.now(),
        is_mass_reported=True,
        mass_report_alert_id="550e8400-e29b-41d4-a716-446655440000"
    )
    
    assert report.is_mass_reported is True
    assert report.mass_report_alert_id == "550e8400-e29b-41d4-a716-446655440000"


def test_scam_report_validation_fails_when_mass_reported_without_alert_id():
    """Test validation fails when is_mass_reported is True but mass_report_alert_id is None"""
    with pytest.raises(ValidationError) as exc_info:
        ScamReport(
            report_id="report_789",
            url="http://scam-site.com/fake",
            normalized_url="http://scam-site.com/fake",
            reporter_uid="U345678",
            risk_score=95,
            category="假冒詐騙",
            points_earned=20,
            reported_at=datetime.now(),
            is_mass_reported=True,
            mass_report_alert_id=None
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'] == ('mass_report_alert_id',)
    assert 'must not be None when is_mass_reported is True' in errors[0]['msg']


def test_scam_report_validation_passes_when_not_mass_reported_with_none_alert_id():
    """Test validation passes when is_mass_reported is False and mass_report_alert_id is None"""
    report = ScamReport(
        report_id="report_999",
        url="http://scam-site.com/fake",
        normalized_url="http://scam-site.com/fake",
        reporter_uid="U901234",
        risk_score=80,
        category="網路詐騙",
        points_earned=12,
        reported_at=datetime.now(),
        is_mass_reported=False,
        mass_report_alert_id=None
    )
    
    assert report.is_mass_reported is False
    assert report.mass_report_alert_id is None


def test_scam_report_validation_passes_when_not_mass_reported_with_alert_id():
    """Test validation passes when is_mass_reported is False but mass_report_alert_id is provided"""
    # This is an edge case - technically allowed by the validation rule
    report = ScamReport(
        report_id="report_888",
        url="http://scam-site.com/fake",
        normalized_url="http://scam-site.com/fake",
        reporter_uid="U567890",
        risk_score=88,
        category="簡訊詐騙",
        points_earned=18,
        reported_at=datetime.now(),
        is_mass_reported=False,
        mass_report_alert_id="660e8400-e29b-41d4-a716-446655440001"
    )
    
    assert report.is_mass_reported is False
    assert report.mass_report_alert_id == "660e8400-e29b-41d4-a716-446655440001"
