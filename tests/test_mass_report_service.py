"""Unit tests for mass_report_service.process_mass_report()."""

from unittest.mock import MagicMock, patch

from mass_report_service import process_mass_report
from database import retry_database_write


class FakeMassReportAlertsTable:
    """In-memory fake table for mass report alerts."""

    def __init__(self, existing_items=None):
        self.items = {}
        self.put_calls = []
        self.update_calls = []
        for item in existing_items or []:
            self.items[item["alert_id"]] = item

    def query(self, **kwargs):
        normalized_url = kwargs["ExpressionAttributeValues"][":url"]
        matches = [
            item for item in self.items.values()
            if item["normalized_url"] == normalized_url
        ]
        return {"Items": matches[: kwargs.get("Limit", len(matches) or 1)]}

    def put_item(self, Item, **kwargs):
        stored_item = dict(Item)
        self.put_calls.append(dict(Item))
        self.items[Item["alert_id"]] = stored_item

    def update_item(self, **kwargs):
        self.update_calls.append(kwargs)
        item = self.items[kwargs["Key"]["alert_id"]]
        values = kwargs["ExpressionAttributeValues"]
        item["status"] = values[":status"]
        item["notified_user_count"] = values[":count"]


class FlakyMassReportAlertsTable(FakeMassReportAlertsTable):
    """Fake table that fails initial writes before succeeding."""

    def __init__(self, failures_before_success: int):
        super().__init__()
        self.failures_before_success = failures_before_success
        self.attempts = 0

    def put_item(self, Item):
        self.attempts += 1
        if self.attempts <= self.failures_before_success:
            raise RuntimeError("temporary dynamodb failure")
        super().put_item(Item)


class ConflictingMassReportAlertsTable(FakeMassReportAlertsTable):
    """Fake table that simulates concurrent conditional write conflict."""

    def put_item(self, Item, ConditionExpression=None):
        self.items[Item["alert_id"]] = dict(Item)
        raise RuntimeError("conditional write conflict")


class FakeScamReportsTable:
    """In-memory fake table for scam reports."""

    def __init__(self, report_ids):
        self.report_ids = report_ids
        self.updated = []

    def query(self, **kwargs):
        return {"Items": [{"report_id": report_id} for report_id in self.report_ids]}

    def update_item(self, **kwargs):
        self.updated.append(kwargs)


def test_process_mass_report_returns_threshold_not_reached_when_count_too_low():
    detector = MagicMock()
    detector.threshold = 10

    result = process_mass_report(
        normalized_url="http://example.com/scam",
        current_report_count=9,
        detector=detector,
        summarizer=MagicMock(),
        dispatcher=MagicMock(),
        mass_report_alerts_table=FakeMassReportAlertsTable(),
        scam_reports_table=FakeScamReportsTable([]),
    )

    assert result == {"triggered": False, "reason": "threshold_not_reached"}
    detector.check_report_threshold.assert_not_called()


@patch("mass_report_service.create_mass_report_alerts_table")
def test_process_mass_report_returns_already_notified_when_alert_exists(mock_create_table):
    detector = MagicMock()
    detector.threshold = 10
    detector.check_report_threshold.return_value = True

    existing_alert = {
        "alert_id": "existing-alert-id",
        "normalized_url": "http://example.com/scam",
        "status": "completed",
    }

    result = process_mass_report(
        normalized_url="http://example.com/scam",
        current_report_count=10,
        detector=detector,
        summarizer=MagicMock(),
        dispatcher=MagicMock(),
        mass_report_alerts_table=FakeMassReportAlertsTable([existing_alert]),
        scam_reports_table=FakeScamReportsTable(["r1"]),
    )

    assert result["triggered"] is False
    assert result["reason"] == "already_notified"
    assert result["alert_id"] == "existing-alert-id"


@patch("mass_report_service.create_mass_report_alerts_table")
def test_process_mass_report_creates_alert_marks_reports_and_completes(mock_create_table):
    detector = MagicMock()
    detector.threshold = 10
    detector.check_report_threshold.return_value = True
    detector.get_original_message.return_value = "http://example.com/original"

    summarizer = MagicMock()
    summarizer.generate_mass_report_alert.return_value = {
        "alert_summary": "這是整理後的風險摘要",
        "alert_warning": "請勿點擊連結並撥打 165 查證",
    }

    dispatcher = MagicMock()
    dispatcher.broadcast_mass_report_alert.return_value = {
        "success_count": 12,
        "failed_count": 2,
        "failed_users": ["U3", "U4"],
    }

    alerts_table = FakeMassReportAlertsTable()
    reports_table = FakeScamReportsTable(["r1", "r2", "r3"])

    result = process_mass_report(
        normalized_url="http://example.com/scam",
        current_report_count=12,
        detector=detector,
        summarizer=summarizer,
        dispatcher=dispatcher,
        mass_report_alerts_table=alerts_table,
        scam_reports_table=reports_table,
    )

    assert result["triggered"] is True
    assert result["status"] == "completed"
    assert result["marked_report_count"] == 3
    assert result["notified_users"] == 12
    assert result["failed_count"] == 2
    assert result["failed_users"] == ["U3", "U4"]
    assert len(alerts_table.put_calls) == 1
    assert alerts_table.put_calls[0]["status"] == "processing"
    assert alerts_table.items[result["alert_id"]]["status"] == "completed"
    assert alerts_table.items[result["alert_id"]]["notified_user_count"] == 12
    assert len(reports_table.updated) == 3
    dispatcher.broadcast_mass_report_alert.assert_called_once_with(
        alert_summary="這是整理後的風險摘要",
        alert_warning="請勿點擊連結並撥打 165 查證",
        report_count=12,
    )


@patch("mass_report_service.create_mass_report_alerts_table")
def test_process_mass_report_marks_alert_failed_when_broadcast_raises(mock_create_table):
    detector = MagicMock()
    detector.threshold = 10
    detector.check_report_threshold.return_value = True
    detector.get_original_message.return_value = "http://example.com/original"

    summarizer = MagicMock()
    summarizer.generate_mass_report_alert.return_value = {
        "alert_summary": "摘要",
        "alert_warning": "警示",
    }

    dispatcher = MagicMock()
    dispatcher.broadcast_mass_report_alert.side_effect = RuntimeError("LINE API unavailable")

    alerts_table = FakeMassReportAlertsTable()
    reports_table = FakeScamReportsTable(["r1"])

    result = process_mass_report(
        normalized_url="http://example.com/scam",
        current_report_count=10,
        detector=detector,
        summarizer=summarizer,
        dispatcher=dispatcher,
        mass_report_alerts_table=alerts_table,
        scam_reports_table=reports_table,
    )

    assert result["triggered"] is False
    assert result["reason"] == "processing_failed"
    assert alerts_table.items[result["alert_id"]]["status"] == "failed"
    assert alerts_table.items[result["alert_id"]]["notified_user_count"] == 0


def test_retry_database_write_retries_until_success():
    state = {"attempts": 0}

    def flaky_operation():
        state["attempts"] += 1
        if state["attempts"] < 3:
            raise RuntimeError("temporary failure")
        return "ok"

    with patch("database.time.sleep"):
        result = retry_database_write(flaky_operation)

    assert result == "ok"
    assert state["attempts"] == 3


@patch("mass_report_service.create_mass_report_alerts_table")
def test_process_mass_report_returns_database_error_when_alert_save_fails(mock_create_table):
    detector = MagicMock()
    detector.threshold = 10
    detector.check_report_threshold.return_value = True
    detector.get_original_message.return_value = "http://example.com/original"

    summarizer = MagicMock()
    summarizer.generate_mass_report_alert.return_value = {
        "alert_summary": "摘要",
        "alert_warning": "警示",
    }

    dispatcher = MagicMock()
    alerts_table = FlakyMassReportAlertsTable(failures_before_success=3)

    with patch("database.time.sleep"):
        result = process_mass_report(
            normalized_url="http://example.com/scam",
            current_report_count=10,
            detector=detector,
            summarizer=summarizer,
            dispatcher=dispatcher,
            mass_report_alerts_table=alerts_table,
            scam_reports_table=FakeScamReportsTable(["r1"]),
        )

    assert result == {"triggered": False, "reason": "database_error"}
    dispatcher.broadcast_mass_report_alert.assert_not_called()


@patch("mass_report_service.create_mass_report_alerts_table")
def test_process_mass_report_returns_already_notified_when_conditional_write_conflicts(mock_create_table):
    detector = MagicMock()
    detector.threshold = 10
    detector.check_report_threshold.return_value = True
    detector.get_original_message.return_value = "http://example.com/original"

    summarizer = MagicMock()
    summarizer.generate_mass_report_alert.return_value = {
        "alert_summary": "摘要",
        "alert_warning": "警示",
    }

    dispatcher = MagicMock()
    alerts_table = ConflictingMassReportAlertsTable()

    with patch("database.time.sleep"):
        result = process_mass_report(
            normalized_url="http://example.com/scam",
            current_report_count=10,
            detector=detector,
            summarizer=summarizer,
            dispatcher=dispatcher,
            mass_report_alerts_table=alerts_table,
            scam_reports_table=FakeScamReportsTable(["r1"]),
        )

    assert result["triggered"] is False
    assert result["reason"] == "already_notified"
    dispatcher.broadcast_mass_report_alert.assert_not_called()
