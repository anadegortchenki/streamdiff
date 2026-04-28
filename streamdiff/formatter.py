"""Output formatters for diff records."""

import json
from enum import Enum
from typing import Iterable, Iterator

from streamdiff.differ import ChangeType, DiffRecord
from streamdiff.stats import DiffStats, collect_stats


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    UNIFIED = "unified"


_COLORS = {
    ChangeType.ADDED: "\033[32m",
    ChangeType.REMOVED: "\033[31m",
    ChangeType.UNCHANGED: "",
}
_RESET = "\033[0m"


def _colorize(text: str, change_type: ChangeType) -> str:
    color = _COLORS.get(change_type, "")
    if not color:
        return text
    return f"{color}{text}{_RESET}"


def format_text(
    records: Iterable[DiffRecord], *, color: bool = False
) -> Iterator[str]:
    """Yield human-readable lines for each changed record."""
    for record in records:
        if record.change_type == ChangeType.UNCHANGED:
            continue
        prefix = "+" if record.change_type == ChangeType.ADDED else "-"
        line = f"{prefix} {record.line}"
        if color:
            line = _colorize(line, record.change_type)
        yield line


def format_json(
    records: Iterable[DiffRecord], *, emit_unchanged: bool = False
) -> Iterator[str]:
    """Yield JSON-encoded lines for each diff record."""
    for record in records:
        if not emit_unchanged and record.change_type == ChangeType.UNCHANGED:
            continue
        yield json.dumps(
            {
                "change": record.change_type.value,
                "line_number": record.line_number,
                "line": record.line,
            }
        )


def format_unified(records: Iterable[DiffRecord]) -> Iterator[str]:
    """Yield unified-diff style lines."""
    for record in records:
        if record.change_type == ChangeType.ADDED:
            yield f"+{record.line}"
        elif record.change_type == ChangeType.REMOVED:
            yield f"-{record.line}"
        else:
            yield f" {record.line}"


def format_summary(stats: DiffStats) -> str:
    """Return a one-line summary string from DiffStats."""
    return (
        f"Summary: +{stats.added} added, -{stats.removed} removed, "
        f"{stats.unchanged} unchanged ({stats.total} total lines, "
        f"{stats.change_ratio:.1%} changed)"
    )


def format_records(
    records: Iterable[DiffRecord],
    fmt: OutputFormat = OutputFormat.TEXT,
    *,
    color: bool = False,
    show_summary: bool = False,
) -> Iterator[str]:
    """Dispatch to the appropriate formatter and optionally append a summary."""
    accumulated = list(records)
    if fmt == OutputFormat.TEXT:
        yield from format_text(accumulated, color=color)
    elif fmt == OutputFormat.JSON:
        yield from format_json(accumulated)
    elif fmt == OutputFormat.UNIFIED:
        yield from format_unified(accumulated)
    if show_summary:
        yield format_summary(collect_stats(accumulated))
