"""Output formatters for diff results."""

from enum import Enum
from typing import Iterable, TextIO
import sys
import json

from streamdiff.differ import DiffRecord, ChangeType


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    UNIFIED = "unified"


ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"


def _colorize(text: str, change_type: ChangeType, use_color: bool) -> str:
    if not use_color:
        return text
    if change_type == ChangeType.ADDED:
        return f"{ANSI_GREEN}{text}{ANSI_RESET}"
    if change_type == ChangeType.REMOVED:
        return f"{ANSI_RED}{text}{ANSI_RESET}"
    return text


def format_text(
    records: Iterable[DiffRecord],
    out: TextIO = sys.stdout,
    use_color: bool = False,
) -> int:
    """Write diff records as plain text. Returns count of changed lines."""
    count = 0
    for record in records:
        if record.change_type == ChangeType.UNCHANGED:
            continue
        line = str(record)
        out.write(_colorize(line, record.change_type, use_color) + "\n")
        count += 1
    return count


def format_json(
    records: Iterable[DiffRecord],
    out: TextIO = sys.stdout,
) -> int:
    """Write diff records as newline-delimited JSON. Returns count of changed lines."""
    count = 0
    for record in records:
        if record.change_type == ChangeType.UNCHANGED:
            continue
        payload = {
            "change": record.change_type.value,
            "line_a": record.line_a,
            "line_b": record.line_b,
            "content": record.line_b if record.change_type == ChangeType.ADDED else record.line_a,
        }
        out.write(json.dumps(payload) + "\n")
        count += 1
    return count


def format_unified(
    records: Iterable[DiffRecord],
    out: TextIO = sys.stdout,
    use_color: bool = False,
) -> int:
    """Write diff records in unified-diff style. Returns count of changed lines."""
    count = 0
    for record in records:
        if record.change_type == ChangeType.ADDED:
            line = f"+ {record.content}"
            out.write(_colorize(line, ChangeType.ADDED, use_color) + "\n")
            count += 1
        elif record.change_type == ChangeType.REMOVED:
            line = f"- {record.content}"
            out.write(_colorize(line, ChangeType.REMOVED, use_color) + "\n")
            count += 1
        else:
            out.write(f"  {record.content}\n")
    return count


def get_formatter(fmt: OutputFormat):
    return {
        OutputFormat.TEXT: format_text,
        OutputFormat.JSON: format_json,
        OutputFormat.UNIFIED: format_unified,
    }[fmt]
