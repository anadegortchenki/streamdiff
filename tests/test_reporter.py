"""Tests for streamdiff.reporter."""
import json
import pytest

from streamdiff.stats import DiffStats
from streamdiff.reporter import (
    ReportMeta,
    DiffReport,
    build_report,
    render_text,
    render_json,
)


def _stats(added=0, removed=0, unchanged=0) -> DiffStats:
    s = DiffStats()
    for _ in range(added):
        s.added += 1
    for _ in range(removed):
        s.removed += 1
    for _ in range(unchanged):
        s.unchanged += 1
    s._recalc()
    return s


def _report(added=2, removed=1, unchanged=5, elapsed=1.23) -> DiffReport:
    stats = _stats(added=added, removed=removed, unchanged=unchanged)
    return build_report(stats, "left.csv", "right.csv", elapsed_seconds=elapsed)


class TestBuildReport:
    def test_meta_sources_stored(self):
        r = _report()
        assert r.meta.left_source == "left.csv"
        assert r.meta.right_source == "right.csv"

    def test_elapsed_stored(self):
        r = _report(elapsed=2.5)
        assert r.meta.elapsed_seconds == 2.5

    def test_elapsed_optional_none(self):
        stats = _stats()
        r = build_report(stats, "a", "b")
        assert r.meta.elapsed_seconds is None

    def test_generated_at_is_iso_string(self):
        r = _report()
        # Should not raise
        from datetime import datetime
        datetime.fromisoformat(r.meta.generated_at)

    def test_stats_attached(self):
        r = _report(added=3, removed=2, unchanged=10)
        assert r.stats.added == 3
        assert r.stats.removed == 2
        assert r.stats.unchanged == 10


class TestRenderText:
    def test_contains_sources(self):
        text = render_text(_report())
        assert "left.csv" in text
        assert "right.csv" in text

    def test_contains_counts(self):
        text = render_text(_report(added=4, removed=1, unchanged=10))
        assert "4" in text
        assert "1" in text
        assert "10" in text

    def test_contains_elapsed(self):
        text = render_text(_report(elapsed=3.14))
        assert "3.140" in text

    def test_no_elapsed_line_when_none(self):
        stats = _stats()
        r = build_report(stats, "a", "b", elapsed_seconds=None)
        text = render_text(r)
        assert "Time" not in text

    def test_change_percentage_present(self):
        text = render_text(_report(added=1, removed=1, unchanged=8))
        assert "%" in text


class TestRenderJson:
    def test_valid_json(self):
        out = render_json(_report())
        data = json.loads(out)  # must not raise
        assert "meta" in data
        assert "stats" in data

    def test_json_sources(self):
        data = json.loads(render_json(_report()))
        assert data["meta"]["left_source"] == "left.csv"

    def test_json_stats_keys(self):
        data = json.loads(render_json(_report(added=2, removed=1, unchanged=7)))
        s = data["stats"]
        assert s["added"] == 2
        assert s["removed"] == 1
        assert s["unchanged"] == 7
        assert s["total"] == 10

    def test_change_ratio_rounded(self):
        data = json.loads(render_json(_report(added=1, removed=0, unchanged=3)))
        assert data["stats"]["change_ratio"] == 0.25

    def test_to_dict_roundtrip(self):
        r = _report()
        d = r.to_dict()
        assert d["meta"]["right_source"] == "right.csv"
        assert isinstance(d["stats"]["change_ratio"], float)
