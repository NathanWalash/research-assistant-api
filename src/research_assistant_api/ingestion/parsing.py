import csv
import re
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

PIPE_DELIMITER = "|"
TOPIC_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def iter_csv_rows(csv_path: str | Path) -> Iterator[dict[str, str]]:
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def split_pipe_values(value: str | None) -> list[str]:
    normalized = normalize_optional_text(value)
    if not normalized:
        return []
    return [item.strip() for item in normalized.split(PIPE_DELIMITER)]


def parse_bool(value: str | None, default: bool = False) -> bool:
    normalized = normalize_optional_text(value)
    if normalized is None:
        return default
    return normalized.lower() in {"true", "1", "yes"}


def parse_int(value: str | None, default: int = 0) -> int:
    normalized = normalize_optional_text(value)
    if normalized is None:
        return default
    return int(normalized)


def parse_date(value: str | None) -> date | None:
    normalized = normalize_optional_text(value)
    if normalized is None:
        return None
    return date.fromisoformat(normalized)


def build_topic_id(topic_name: str) -> str:
    slug = TOPIC_SLUG_PATTERN.sub("-", topic_name.strip().lower()).strip("-")
    return f"topic:{slug}"


def compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
