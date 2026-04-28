"""Tests for streamdiff.stats."""

import pytest

from streamdiff.differ import ChangeType, DiffRecord
from streamdiff.stats import DiffStats, collect_stats


def _rec(change: ChangeType, line: str = "x", n: int = 1) -> DiffRecord:
    return DiffRecord(change_type=change, line=line, line_number=n)


class TestDiffStats:
    def test_defaults_are_zero(self):
        s = DiffStats()
        assert s.added == 0
        assert s.removed == 0
        assert s.unchanged == 0
        assert s.total == 0

    def test_total_is_sum(self):
        s = DiffStats(added=3, removed=2, unchanged=10)
        assert s.total == 15

    def test_changed_property(self):
        s = DiffStats(added=4, removed=1, unchanged=5)
        assert s.changed == 5

    def test_change_ratio_normal(self):
        s = DiffStats(added=1, removed=1, unchanged=8)
        assert s.change_ratio == pytest.approx(0.2)

    def test_change_ratio_zero_total(self):
        s = DiffStats()
        assert s.change_ratio == 0.0

    def test_change_ratio_all_changed(self):
        s = DiffStats(added=5, removed=5, unchanged=0)
        assert s.change_ratio == pytest.approx(1.0)


class TestCollectStats:
    def test_empty_iterable(self):
        stats = collect_stats([])
        assert stats.total == 0

    def test_all_added(self):
        records = [_rec(ChangeType.ADDED) for _ in range(3)]
        stats = collect_stats(records)
        assert stats.added == 3
        assert stats.removed == 0
        assert stats.unchanged == 0

    def test_all_removed(self):
        records = [_rec(ChangeType.REMOVED) for _ in range(2)]
        stats = collect_stats(records)
        assert stats.removed == 2

    def test_mixed_records(self):
        records = [
            _rec(ChangeType.ADDED),
            _rec(ChangeType.REMOVED),
            _rec(ChangeType.UNCHANGED),
            _rec(ChangeType.UNCHANGED),
        ]
        stats = collect_stats(records)
        assert stats.added == 1
        assert stats.removed == 1
        assert stats.unchanged == 2
        assert stats.total == 4

    def test_consumes_generator(self):
        """collect_stats should work with a one-shot generator."""

        def gen():
            yield _rec(ChangeType.ADDED)
            yield _rec(ChangeType.UNCHANGED)

        stats = collect_stats(gen())
        assert stats.added == 1
        assert stats.unchanged == 1

    def test_change_ratio_via_collect(self):
        records = [
            _rec(ChangeType.ADDED),
            _rec(ChangeType.UNCHANGED),
            _rec(ChangeType.UNCHANGED),
            _rec(ChangeType.UNCHANGED),
        ]
        stats = collect_stats(records)
        assert stats.change_ratio == pytest.approx(0.25)
