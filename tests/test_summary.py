"""Tests for streamdiff.summary."""
import pytest

from streamdiff.stats import DiffStats
from streamdiff.summary import SummaryOptions, build_summary, print_summary


def _stats(
    added: int = 0,
    removed: int = 0,
    modified: int = 0,
    unchanged: int = 0,
) -> DiffStats:
    s = DiffStats()
    s.added = added
    s.removed = removed
    s.modified = modified
    s.unchanged = unchanged
    s._recalc()
    return s


class TestBuildSummary:
    def test_counts_appear_in_output(self):
        s = _stats(added=3, removed=1, modified=2, unchanged=10)
        result = build_summary(s)
        assert "+3 added" in result
        assert "-1 removed" in result
        assert "~2 modified" in result

    def test_unchanged_hidden_by_default(self):
        s = _stats(unchanged=5)
        result = build_summary(s)
        assert "unchanged" not in result

    def test_unchanged_shown_when_option_set(self):
        s = _stats(unchanged=5)
        opts = SummaryOptions(show_unchanged=True)
        result = build_summary(s, opts)
        assert "5 unchanged" in result

    def test_identical_files_message(self):
        s = _stats(unchanged=20)
        result = build_summary(s)
        assert "identical" in result.lower()

    def test_only_additions_message(self):
        s = _stats(added=5, unchanged=10)
        opts = SummaryOptions(label_b="new_file.txt")
        result = build_summary(s, opts)
        assert "Only additions" in result
        assert "new_file.txt" in result

    def test_only_removals_message(self):
        s = _stats(removed=3, unchanged=7)
        opts = SummaryOptions(label_a="old_file.txt")
        result = build_summary(s, opts)
        assert "Only removals" in result
        assert "old_file.txt" in result

    def test_ratio_shown_by_default(self):
        s = _stats(added=1, unchanged=3)
        result = build_summary(s)
        assert "Change ratio" in result
        assert "%" in result

    def test_ratio_hidden_when_disabled(self):
        s = _stats(added=1, unchanged=3)
        opts = SummaryOptions(show_ratio=False)
        result = build_summary(s, opts)
        assert "Change ratio" not in result

    def test_zero_total_skips_ratio(self):
        s = _stats()
        result = build_summary(s)
        assert "Change ratio" not in result

    def test_multiline_output(self):
        s = _stats(added=2, removed=1)
        result = build_summary(s)
        assert "\n" in result


def test_print_summary_runs_without_error(capsys):
    s = _stats(added=1)
    print_summary(s)
    captured = capsys.readouterr()
    assert "+1 added" in captured.out


def test_print_summary_prefix(capsys):
    s = _stats(added=1)
    print_summary(s, prefix=">>> ")
    captured = capsys.readouterr()
    for line in captured.out.strip().splitlines():
        assert line.startswith(">>> ")
