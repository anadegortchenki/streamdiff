"""Tests for streamdiff.formatter module."""

import io
import json
import pytest

from streamdiff.differ import ChangeType, DiffRecord
from streamdiff.formatter import (
    OutputFormat,
    format_text,
    format_json,
    format_unified,
    get_formatter,
)


def _record(change: ChangeType, content: str, line_a=1, line_b=1) -> DiffRecord:
    return DiffRecord(
        change_type=change,
        content=content,
        line_a=line_a if change != ChangeType.ADDED else None,
        line_b=line_b if change != ChangeType.REMOVED else None,
    )


SAMPLE_RECORDS = [
    _record(ChangeType.REMOVED, "old line", line_a=1),
    _record(ChangeType.ADDED, "new line", line_b=1),
    _record(ChangeType.UNCHANGED, "same line", line_a=2, line_b=2),
]


class TestFormatText:
    def test_only_changed_lines_emitted(self):
        out = io.StringIO()
        count = format_text(SAMPLE_RECORDS, out=out)
        lines = out.getvalue().splitlines()
        assert count == 2
        assert len(lines) == 2

    def test_unchanged_lines_skipped(self):
        out = io.StringIO()
        format_text(SAMPLE_RECORDS, out=out)
        assert "same line" not in out.getvalue()

    def test_empty_diff_produces_no_output(self):
        out = io.StringIO()
        count = format_text([], out=out)
        assert count == 0
        assert out.getvalue() == ""


class TestFormatJson:
    def test_output_is_valid_ndjson(self):
        out = io.StringIO()
        format_json(SAMPLE_RECORDS, out=out)
        lines = [l for l in out.getvalue().splitlines() if l]
        for line in lines:
            obj = json.loads(line)
            assert "change" in obj
            assert "content" in obj

    def test_unchanged_excluded(self):
        out = io.StringIO()
        format_json(SAMPLE_RECORDS, out=out)
        changes = [json.loads(l)["change"] for l in out.getvalue().splitlines() if l]
        assert "unchanged" not in changes

    def test_added_content_uses_line_b(self):
        records = [_record(ChangeType.ADDED, "hello", line_b=5)]
        out = io.StringIO()
        format_json(records, out=out)
        obj = json.loads(out.getvalue())
        assert obj["content"] == "hello"
        assert obj["line_b"] == 5


class TestFormatUnified:
    def test_added_lines_prefixed_with_plus(self):
        records = [_record(ChangeType.ADDED, "new")]
        out = io.StringIO()
        format_unified(records, out=out)
        assert out.getvalue().startswith("+ ")

    def test_removed_lines_prefixed_with_minus(self):
        records = [_record(ChangeType.REMOVED, "old")]
        out = io.StringIO()
        format_unified(records, out=out)
        assert out.getvalue().startswith("- ")

    def test_unchanged_lines_prefixed_with_space(self):
        records = [_record(ChangeType.UNCHANGED, "same")]
        out = io.StringIO()
        format_unified(records, out=out)
        assert out.getvalue().startswith("  ")

    def test_returns_changed_count(self):
        out = io.StringIO()
        count = format_unified(SAMPLE_RECORDS, out=out)
        assert count == 2


def test_get_formatter_returns_correct_callable():
    assert get_formatter(OutputFormat.TEXT) is format_text
    assert get_formatter(OutputFormat.JSON) is format_json
    assert get_formatter(OutputFormat.UNIFIED) is format_unified
