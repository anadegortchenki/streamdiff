"""Tests for streamdiff.filter."""

from __future__ import annotations

import pytest

from streamdiff.differ import ChangeType, DiffRecord
from streamdiff.filter import (
    apply_filters,
    filter_by_change_type,
    filter_by_pattern,
    filter_unchanged,
)


def _rec(
    change_type: ChangeType,
    old: str | None = None,
    new: str | None = None,
    line: int = 1,
) -> DiffRecord:
    return DiffRecord(line_number=line, change_type=change_type, old_value=old, new_value=new)


SAMPLE = [
    _rec(ChangeType.UNCHANGED, old="alpha", new="alpha", line=1),
    _rec(ChangeType.ADDED, new="beta", line=2),
    _rec(ChangeType.REMOVED, old="gamma", line=3),
    _rec(ChangeType.CHANGED, old="delta old", new="delta new", line=4),
]


class TestFilterByChangeType:
    def test_keep_added_only(self):
        result = list(filter_by_change_type(SAMPLE, ChangeType.ADDED))
        assert len(result) == 1
        assert result[0].change_type == ChangeType.ADDED

    def test_keep_multiple_types(self):
        result = list(filter_by_change_type(SAMPLE, ChangeType.ADDED, ChangeType.REMOVED))
        types = {r.change_type for r in result}
        assert types == {ChangeType.ADDED, ChangeType.REMOVED}

    def test_empty_source(self):
        assert list(filter_by_change_type([], ChangeType.ADDED)) == []


class TestFilterByPattern:
    def test_matches_new_value_for_addition(self):
        result = list(filter_by_pattern(SAMPLE, r"beta"))
        assert len(result) == 1
        assert result[0].change_type == ChangeType.ADDED

    def test_matches_old_value_for_removal(self):
        result = list(filter_by_pattern(SAMPLE, r"gamma"))
        assert len(result) == 1
        assert result[0].change_type == ChangeType.REMOVED

    def test_case_insensitive_flag(self):
        import re
        result = list(filter_by_pattern(SAMPLE, r"BETA", flags=re.IGNORECASE))
        assert len(result) == 1

    def test_no_match_returns_empty(self):
        result = list(filter_by_pattern(SAMPLE, r"zzznomatch"))
        assert result == []


class TestFilterUnchanged:
    def test_drops_unchanged_records(self):
        result = list(filter_unchanged(SAMPLE))
        assert all(r.change_type != ChangeType.UNCHANGED for r in result)

    def test_preserves_count(self):
        result = list(filter_unchanged(SAMPLE))
        assert len(result) == 3


class TestApplyFilters:
    def test_no_filters_passes_all(self):
        result = list(apply_filters(SAMPLE))
        assert result == SAMPLE

    def test_skip_unchanged_flag(self):
        result = list(apply_filters(SAMPLE, skip_unchanged=True))
        assert all(r.change_type != ChangeType.UNCHANGED for r in result)

    def test_change_types_and_pattern_combined(self):
        result = list(
            apply_filters(
                SAMPLE,
                change_types=[ChangeType.CHANGED],
                pattern=r"delta",
            )
        )
        assert len(result) == 1
        assert result[0].change_type == ChangeType.CHANGED

    def test_pattern_with_skip_unchanged(self):
        result = list(apply_filters(SAMPLE, pattern=r"alpha", skip_unchanged=True))
        # 'alpha' only appears in UNCHANGED, which is then dropped
        assert result == []
