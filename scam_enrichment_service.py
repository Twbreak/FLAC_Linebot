import csv
import io
import json
import logging
import os
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Optional

import requests

from database import dynamodb

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CATEGORY_MAPPING_PATH = BASE_DIR / "config" / "category_mapping.json"
DEFAULT_CASE_REPOSITORY_PATH = BASE_DIR / "data" / "scam_cases.json"
DEFAULT_STATS_CACHE_TABLE = "ScamCategoryStatsCache"


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _safe_int(value) -> int:
    if value is None:
        return 0

    text = str(value).strip()
    if not text:
        return 0

    text = text.replace(",", "").replace("，", "")
    text = text.replace("NT$", "").replace("nt$", "").replace("$", "")
    text = text.replace("元", "").replace("約", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match:
        text = match.group(0)

    try:
        return int(float(text))
    except (TypeError, ValueError):
        return 0


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None

    for parser in (datetime.fromisoformat,):
        try:
            return parser(value)
        except ValueError:
            continue
    return None


class CategoryMapping:
    def __init__(self, mapping_path: Path = DEFAULT_CATEGORY_MAPPING_PATH):
        self.mapping_path = Path(mapping_path)
        self.mapping = self._load_mapping()

    def _load_mapping(self) -> Dict[str, dict]:
        with self.mapping_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def resolve(self, category: str) -> Optional[dict]:
        normalized_input = _normalize_text(category)
        if not normalized_input:
            return None

        for canonical_name, config in self.mapping.items():
            aliases = [_normalize_text(alias) for alias in config.get("aliases", [])]
            if normalized_input == _normalize_text(canonical_name) or normalized_input in aliases:
                return {
                    "canonical_name": canonical_name,
                    "source_categories": config.get("source_categories", []),
                }
        return None


class CaseRepository:
    def __init__(self, repository_path: Path = DEFAULT_CASE_REPOSITORY_PATH):
        self.repository_path = Path(repository_path)
        self.cases = self._load_cases()

    def _load_cases(self) -> Dict[str, list]:
        with self.repository_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def get_case(self, canonical_category: str) -> Optional[dict]:
        category_cases = self.cases.get(canonical_category, [])
        if not category_cases:
            return None
        return random.choice(category_cases)


class StatisticsCache:
    def __init__(self, table_name: str = DEFAULT_STATS_CACHE_TABLE):
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)

    def get(self, cache_key: str) -> Optional[dict]:
        try:
            response = self.table.get_item(Key={"cache_key": cache_key})
        except Exception as exc:
            logger.warning("Stats cache read failed: key=%s error=%s", cache_key, exc)
            return None

        item = response.get("Item")
        if not item:
            return None

        return {
            "recent_case_count": _safe_int(item.get("recent_case_count")),
            "total_loss_amount": _safe_int(item.get("total_loss_amount")),
            "average_loss_amount": _safe_int(item.get("average_loss_amount")),
            "updated_at": item.get("updated_at"),
            "source": item.get("source", "cache"),
        }

    def set(self, cache_key: str, stats: dict) -> None:
        try:
            self.table.put_item(
                Item={
                    "cache_key": cache_key,
                    "recent_case_count": stats["recent_case_count"],
                    "total_loss_amount": stats["total_loss_amount"],
                    "average_loss_amount": stats["average_loss_amount"],
                    "updated_at": stats["updated_at"],
                    "source": stats.get("source", "open_data"),
                }
            )
        except Exception as exc:
            logger.warning("Stats cache write failed: key=%s error=%s", cache_key, exc)


class CategoryStatisticsFetcher:
    def __init__(
        self,
        cache: StatisticsCache,
        data_source_url: Optional[str] = None,
        timeout_seconds: int = 5,
        cache_ttl_hours: int = 24,
        lookback_days: int = 180,
    ):
        self.cache = cache
        self.data_source_url = data_source_url or os.getenv("SCAM_OPEN_DATA_URL")
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_hours = cache_ttl_hours
        self.lookback_days = lookback_days

    def get_statistics(self, mapping: dict) -> Optional[dict]:
        cache_key = mapping["canonical_name"]
        cached_stats = self.cache.get(cache_key)

        if cached_stats and not self._is_expired(cached_stats.get("updated_at")):
            cached_stats["source"] = "cache"
            return cached_stats

        if not self.data_source_url:
            return cached_stats

        try:
            response = requests.get(self.data_source_url, timeout=self.timeout_seconds)
            response.raise_for_status()
            rows = self._parse_csv_rows(response.content)
            stats = self._aggregate_statistics(rows, mapping["source_categories"])
            if not stats:
                return cached_stats

            stats["updated_at"] = datetime.utcnow().isoformat()
            stats["source"] = self.data_source_url
            self.cache.set(cache_key, stats)
            return stats
        except Exception as exc:
            logger.warning("Fetch category stats failed: category=%s error=%s", cache_key, exc)
            return cached_stats

    def _is_expired(self, updated_at: Optional[str]) -> bool:
        updated_dt = _parse_iso_datetime(updated_at or "")
        if not updated_dt:
            return True
        return datetime.utcnow() - updated_dt > timedelta(hours=self.cache_ttl_hours)

    def _parse_csv_rows(self, payload: bytes) -> list[dict]:
        for encoding in ("utf-8-sig", "utf-8", "big5", "cp950"):
            try:
                text = payload.decode(encoding)
                return self._read_csv(text)
            except UnicodeDecodeError:
                continue
        raise ValueError("Unsupported CSV encoding")

    def _read_csv(self, csv_text: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = []
        for row in reader:
            normalized_row = {self._normalize_header(key): (value or "").strip() for key, value in row.items()}
            rows.append(normalized_row)
        return rows

    def _normalize_header(self, key: Optional[str]) -> str:
        return (key or "").strip().lstrip("\ufeff")

    def _aggregate_statistics(self, rows: Iterable[dict], source_categories: Iterable[str]) -> Optional[dict]:
        category_set = {_normalize_text(item) for item in source_categories}
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        matched_amounts = []

        for row in rows:
            row_category = self._pick_value(
                row,
                "詐騙類別",
                "詐欺類型",
                "詐騙類型",
                "案類",
                "案類別",
                "案件類別",
                "category",
                "fraud_type",
            )
            if _normalize_text(row_category) not in category_set:
                continue

            amount = _safe_int(
                self._pick_value(
                    row,
                    "損失金額",
                    "財損金額",
                    "財損",
                    "財產損失",
                    "受騙金額",
                    "loss",
                    "loss_amount",
                    "amount",
                )
            )
            if amount <= 0:
                continue

            case_date = self._parse_row_date(
                self._pick_value(
                    row,
                    "案件日期",
                    "受理日期",
                    "通報日期",
                    "發生日期",
                    "建立日期",
                    "date",
                    "created_at",
                )
            )
            if case_date and case_date < cutoff_date:
                continue

            matched_amounts.append(amount)

        if not matched_amounts:
            return None

        total_loss = sum(matched_amounts)
        case_count = len(matched_amounts)
        return {
            "recent_case_count": case_count,
            "total_loss_amount": total_loss,
            "average_loss_amount": total_loss // case_count,
        }

    def _pick_value(self, row: dict, *candidate_keys: str) -> str:
        for key in candidate_keys:
            if key in row and row[key]:
                return row[key]
        return ""

    def _parse_row_date(self, value: str) -> Optional[datetime]:
        if not value:
            return None

        normalized = value.strip().replace("/", "-")
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue

        roc_match = re.match(r"^(\d{2,3})-(\d{1,2})-(\d{1,2})(?:\s+\d{1,2}:\d{1,2}:\d{1,2})?$", normalized)
        if roc_match:
            year = int(roc_match.group(1)) + 1911
            month = int(roc_match.group(2))
            day = int(roc_match.group(3))
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

        return None


class AlertFormatter:
    @staticmethod
    def format_category_alert_block(category_alert: Optional[dict]) -> str:
        if not category_alert:
            return ""

        lines = ["", "----------", "防詐補充提醒"]
        canonical_name = category_alert.get("canonical_name")
        if canonical_name:
            lines.append(f"高風險類型：{canonical_name}")

        stats = category_alert.get("statistics")
        if stats:
            lines.append(f"近期通報案件：約 {stats['recent_case_count']} 件")
            lines.append(f"累計財損金額：約 NT${stats['total_loss_amount']:,}")
            lines.append(f"平均單案損失：約 NT${stats['average_loss_amount']:,}")

        case_item = category_alert.get("case")
        if case_item:
            lines.append("")
            lines.append(f"案例參考｜{case_item['title']}")
            lines.append(case_item["summary"])
            lines.append(f"常見受害金額：{case_item['loss_range']}")

        lines.append("提醒：若對方要求匯款、提供帳戶或加入陌生投資群組，請立即停止互動並撥打 165 查證。")

        return "\n".join(lines)


class ScamCategoryEnricher:
    def __init__(
        self,
        category_mapping: Optional[CategoryMapping] = None,
        case_repository: Optional[CaseRepository] = None,
        statistics_fetcher: Optional[CategoryStatisticsFetcher] = None,
    ):
        self.category_mapping = category_mapping or CategoryMapping()
        self.case_repository = case_repository or CaseRepository()
        self.statistics_fetcher = statistics_fetcher or CategoryStatisticsFetcher(cache=StatisticsCache())

    def build_category_alert(self, category: str) -> Optional[dict]:
        mapping = self.category_mapping.resolve(category)
        if not mapping:
            return None

        category_alert = {
            "canonical_name": mapping["canonical_name"],
            "statistics": self.statistics_fetcher.get_statistics(mapping),
            "case": self.case_repository.get_case(mapping["canonical_name"]),
        }

        if not category_alert["statistics"] and not category_alert["case"]:
            return None

        return category_alert
