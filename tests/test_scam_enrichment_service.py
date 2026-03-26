from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from scam_enrichment_service import (
    AlertFormatter,
    CategoryMapping,
    CategoryStatisticsFetcher,
    ScamCategoryEnricher,
)


class FakeCache:
    def __init__(self, initial=None):
        self.initial = initial
        self.saved = None

    def get(self, cache_key: str):
        return self.initial

    def set(self, cache_key: str, stats: dict):
        self.saved = {"cache_key": cache_key, "stats": stats}


def test_category_mapping_resolves_alias():
    mapping = CategoryMapping()

    resolved = mapping.resolve("投資詐騙")

    assert resolved is not None
    assert resolved["canonical_name"] == "假投資詐騙"
    assert "假投資" in resolved["source_categories"]


def test_statistics_fetcher_parses_csv_and_ignores_zero_loss():
    recent_date = datetime.utcnow().strftime("%Y-%m-%d")
    csv_text = "\n".join(
        [
            "案件日期,詐騙類別,損失金額,案件描述",
            f"{recent_date},假投資,100000,案例一",
            f"{recent_date},假投資,50000,案例二",
            f"{recent_date},假投資,0,應忽略",
            f"{recent_date},假檢警,200000,不同類別",
        ]
    )

    cache = FakeCache()
    fetcher = CategoryStatisticsFetcher(cache=cache, data_source_url="https://example.com/data.csv")
    response = Mock()
    response.content = csv_text.encode("utf-8")
    response.raise_for_status.return_value = None

    with patch("scam_enrichment_service.requests.get", return_value=response):
        stats = fetcher.get_statistics(
            {"canonical_name": "假投資詐騙", "source_categories": ["假投資", "投資詐騙"]}
        )

    assert stats["recent_case_count"] == 2
    assert stats["total_loss_amount"] == 150000
    assert stats["average_loss_amount"] == 75000
    assert cache.saved["cache_key"] == "假投資詐騙"


def test_statistics_fetcher_supports_alternative_headers_and_roc_dates():
    roc_date = f"{datetime.utcnow().year - 1911}-03-01"
    csv_text = "\n".join(
        [
            "通報日期,案件類別,財產損失,案件描述",
            f"{roc_date},假投資,NT$88,000 元,案例一",
            f"{roc_date},假投資,約 12,000 元,案例二",
            f"{roc_date},假檢警,30000,不同類別",
        ]
    )

    cache = FakeCache()
    fetcher = CategoryStatisticsFetcher(cache=cache, data_source_url="https://example.com/data.csv")
    response = Mock()
    response.content = csv_text.encode("utf-8")
    response.raise_for_status.return_value = None

    with patch("scam_enrichment_service.requests.get", return_value=response):
        stats = fetcher.get_statistics(
            {"canonical_name": "假投資詐騙", "source_categories": ["假投資", "投資詐騙"]}
        )

    assert stats["recent_case_count"] == 2
    assert stats["total_loss_amount"] == 100000
    assert stats["average_loss_amount"] == 50000


def test_statistics_fetcher_returns_cached_data_when_request_fails():
    cached = {
        "recent_case_count": 4,
        "total_loss_amount": 880000,
        "average_loss_amount": 220000,
        "updated_at": (datetime.utcnow() - timedelta(hours=30)).isoformat(),
        "source": "cache",
    }
    cache = FakeCache(initial=cached)
    fetcher = CategoryStatisticsFetcher(cache=cache, data_source_url="https://example.com/data.csv")

    with patch("scam_enrichment_service.requests.get", side_effect=RuntimeError("network error")):
        stats = fetcher.get_statistics(
            {"canonical_name": "假投資詐騙", "source_categories": ["假投資"]}
        )

    assert stats == cached


def test_alert_formatter_renders_stats_and_case():
    block = AlertFormatter.format_category_alert_block(
        {
            "canonical_name": "假投資詐騙",
            "statistics": {
                "recent_case_count": 12,
                "total_loss_amount": 3600000,
                "average_loss_amount": 300000,
            },
            "case": {
                "title": "假投資案例",
                "summary": "以穩賺不賠為名義要求持續匯款。",
                "loss_range": "10 萬至 100 萬元",
            },
        }
    )

    assert "防詐補充提醒" in block
    assert "近期通報案件：約 12 件" in block
    assert "累計財損金額：約 NT$3,600,000" in block
    assert "案例參考｜假投資案例" in block
    assert "撥打 165 查證" in block


def test_enricher_returns_case_even_without_statistics():
    fake_mapping = Mock()
    fake_mapping.resolve.return_value = {
        "canonical_name": "假投資詐騙",
        "source_categories": ["假投資"],
    }
    fake_fetcher = Mock()
    fake_fetcher.get_statistics.return_value = None
    fake_repository = Mock()
    fake_repository.get_case.return_value = {
        "title": "案例",
        "summary": "說明",
        "loss_range": "1 萬至 10 萬元",
    }

    enricher = ScamCategoryEnricher(
        category_mapping=fake_mapping,
        case_repository=fake_repository,
        statistics_fetcher=fake_fetcher,
    )

    category_alert = enricher.build_category_alert("假投資詐騙")

    assert category_alert["canonical_name"] == "假投資詐騙"
    assert category_alert["statistics"] is None
    assert category_alert["case"]["title"] == "案例"
