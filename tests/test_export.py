"""Tests for streamdiff.export."""
import json
from pathlib import Path

import pytest

from streamdiff.stats import DiffStats
from streamdiff.reporter import build_report
from streamdiff.export import ExportFormat, export_report, report_to_string


def _make_report(added=3, removed=1, unchanged=6):
    s = DiffStats()
    s.added = added
    s.removed = removed
    s.unchanged = unchanged
    s._recalc()
    return build_report(s, "old.txt", "new.txt", elapsed_seconds=0.5)


class TestReportToString:
    def test_text_format_contains_sources(self):
        out = report_to_string(_make_report(), ExportFormat.TEXT)
        assert "old.txt" in out
        assert "new.txt" in out

    def test_json_format_is_valid(self):
        out = report_to_string(_make_report(), ExportFormat.JSON)
        data = json.loads(out)
        assert "stats" in data

    def test_default_format_is_text(self):
        out = report_to_string(_make_report())
        assert "Added" in out


class TestExportReport:
    def test_writes_to_file_text(self, tmp_path):
        dest = tmp_path / "report.txt"
        export_report(_make_report(), ExportFormat.TEXT, str(dest))
        content = dest.read_text()
        assert "old.txt" in content

    def test_writes_to_file_json(self, tmp_path):
        dest = tmp_path / "report.json"
        export_report(_make_report(), ExportFormat.JSON, str(dest))
        data = json.loads(dest.read_text())
        assert data["meta"]["left_source"] == "old.txt"

    def test_creates_parent_dirs(self, tmp_path):
        dest = tmp_path / "nested" / "deep" / "report.txt"
        export_report(_make_report(), ExportFormat.TEXT, str(dest))
        assert dest.exists()

    def test_stdout_no_path(self, capsys):
        export_report(_make_report(), ExportFormat.TEXT, output_path=None)
        captured = capsys.readouterr()
        assert "old.txt" in captured.out

    def test_stdout_json_no_path(self, capsys):
        export_report(_make_report(), ExportFormat.JSON, output_path=None)
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert "stats" in data

    def test_file_encoding_utf8(self, tmp_path):
        dest = tmp_path / "report.txt"
        export_report(_make_report(), ExportFormat.TEXT, str(dest))
        # read_text defaults to platform encoding; force utf-8
        content = dest.read_text(encoding="utf-8")
        assert len(content) > 0
