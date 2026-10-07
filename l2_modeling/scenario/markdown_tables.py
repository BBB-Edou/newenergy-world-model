"""Deterministic Markdown table detection for ScenarioData extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_PAGE_RE = re.compile(r"<!--\s*page:\s*(\d+)\s*-->", re.IGNORECASE)
_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_TIME_NAMES = {"time", "timestamp", "时间", "时刻", "datetime"}
_WIND_NAMES = {"wind", "wind_power", "风电", "风力"}
_PV_NAMES = {"pv", "pv_power", "solar", "photovoltaic", "光伏"}
_LOAD_NAMES = {"load", "load_power", "demand", "负荷", "用电"}
_PRICE_NAMES = {"price", "electricity_price", "电价", "价格"}


@dataclass(frozen=True, slots=True)
class MarkdownTable:
    table_id: str
    page: int | None
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    header_line: int
    metadata: dict[str, object] = field(default_factory=dict)


def _split_row(line: str) -> tuple[str, ...]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return tuple(cell.strip() for cell in text.split("|"))


def _normalize_header(value: str) -> str:
    return re.sub(r"[\s_\-]+", "_", value.strip().lower())


def detect_markdown_tables(markdown: str) -> list[MarkdownTable]:
    lines = markdown.splitlines()
    tables: list[MarkdownTable] = []
    page: int | None = None
    index = 0
    table_number = 0
    while index < len(lines):
        page_match = _PAGE_RE.search(lines[index])
        if page_match:
            page = int(page_match.group(1))
        if index + 1 >= len(lines) or "|" not in lines[index] or not _SEPARATOR_RE.match(lines[index + 1]):
            index += 1
            continue
        headers = _split_row(lines[index])
        rows: list[tuple[str, ...]] = []
        cursor = index + 2
        while cursor < len(lines) and "|" in lines[cursor] and lines[cursor].strip():
            page_match = _PAGE_RE.search(lines[cursor])
            if page_match:
                break
            row = _split_row(lines[cursor])
            if len(row) != len(headers):
                row = row + ("",) * max(0, len(headers) - len(row))
            rows.append(row[: len(headers)])
            cursor += 1
        table_number += 1
        tables.append(
            MarkdownTable(
                table_id=f"table_{table_number:02d}",
                page=page,
                headers=headers,
                rows=tuple(rows),
                header_line=index + 1,
            )
        )
        index = cursor
    return tables


def is_scenario_candidate(table: MarkdownTable) -> bool:
    normalized = {_normalize_header(header) for header in table.headers}
    has_time = bool(normalized & _TIME_NAMES)
    has_measure = bool(normalized & (_WIND_NAMES | _PV_NAMES | _LOAD_NAMES | _PRICE_NAMES))
    return has_time and has_measure


def scenario_candidates(markdown: str) -> list[MarkdownTable]:
    return [table for table in detect_markdown_tables(markdown) if is_scenario_candidate(table)]