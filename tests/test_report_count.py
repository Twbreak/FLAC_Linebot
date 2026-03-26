"""Unit tests for database.get_report_count()."""

from unittest.mock import MagicMock

from database import get_report_count


def test_get_report_count_returns_single_page_count():
    table = MagicMock()
    table.query.return_value = {"Count": 7}

    count = get_report_count("https://example.com/scam", scam_reports_table=table)

    assert count == 7
    table.query.assert_called_once()


def test_get_report_count_accumulates_paginated_counts():
    table = MagicMock()
    table.query.side_effect = [
        {"Count": 5, "LastEvaluatedKey": {"report_id": "r1"}},
        {"Count": 4, "LastEvaluatedKey": {"report_id": "r2"}},
        {"Count": 3},
    ]

    count = get_report_count("https://example.com/scam", scam_reports_table=table)

    assert count == 12
    assert table.query.call_count == 3
