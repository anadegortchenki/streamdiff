"""Tests for the streaming differ."""

import io
from unittest.mock import patch

import pytest

from streamdiff.differ import ChangeType, DiffRecord, diff_streams


def _mock_streams(lines_a, lines_b):
    """Patch stream_lines to return controlled iterators."""
    streams = {"a": iter(lines_a), "b": iter(lines_b)}
    call_order = ["a", "b"]
    call_count = [0]

    def fake_stream_lines(path, encoding="utf-8"):
        key = call_order[call_count[0] % 2]
        call_count[0] += 1
        return streams[key]

    return fake_stream_lines


def run_diff(lines_a, lines_b, show_unchanged=False):
    with patch("streamdiff.differ.stream_lines", side_effect=_mock_streams(lines_a, lines_b)):
        return list(diff_streams("a.txt", "b.txt", show_unchanged=show_unchanged))


def test_all_added():
    records = run_diff([], ["apple", "banana"])
    assert all(r.change == ChangeType.ADDED for r in records)
    assert [r.line for r in records] == ["apple", "banana"]


def test_all_removed():
    records = run_diff(["apple", "banana"], [])
    assert all(r.change == ChangeType.REMOVED for r in records)


def test_no_changes():
    records = run_diff(["a", "b", "c"], ["a", "b", "c"], show_unchanged=True)
    assert all(r.change == ChangeType.UNCHANGED for r in records)
    assert len(records) == 3


def test_no_changes_hidden_by_default():
    records = run_diff(["a", "b"], ["a", "b"])
    assert records == []


def test_mixed_diff():
    records = run_diff(["a", "b", "d"], ["a", "c", "d"], show_unchanged=True)
    changes = [(r.change, r.line) for r in records]
    assert (ChangeType.UNCHANGED, "a") in changes
    assert (ChangeType.REMOVED, "b") in changes
    assert (ChangeType.ADDED, "c") in changes
    assert (ChangeType.UNCHANGED, "d") in changes


def test_diff_record_str_formatting():
    assert str(DiffRecord(ChangeType.ADDED, "foo")) == "+ foo"
    assert str(DiffRecord(ChangeType.REMOVED, "foo")) == "- foo"
    assert str(DiffRecord(ChangeType.UNCHANGED, "foo")) == "  foo"
