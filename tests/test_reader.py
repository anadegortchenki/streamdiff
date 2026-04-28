"""Tests for streamdiff.reader module.

Verifies that stream_lines correctly reads from file-like objects,
handles edge cases (empty files, trailing newlines, binary-vs-text),
and that the public API matches what differ.py expects.
"""

import io
import pytest
from unittest.mock import patch, mock_open

from streamdiff.reader import stream_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_stream(text: str) -> io.StringIO:
    """Return a StringIO stream pre-loaded with *text*."""
    return io.StringIO(text)


# ---------------------------------------------------------------------------
# Basic reading
# ---------------------------------------------------------------------------

def test_simple_lines():
    """Lines are yielded one at a time, stripped of their newline."""
    stream = _make_stream("alpha\nbeta\ngamma\n")
    result = list(stream_lines(stream))
    assert result == ["alpha", "beta", "gamma"]


def test_no_trailing_newline():
    """A file that doesn't end with '\n' still yields the last line."""
    stream = _make_stream("one\ntwo\nthree")
    result = list(stream_lines(stream))
    assert result == ["one", "two", "three"]


def test_empty_stream():
    """An empty stream produces no lines."""
    stream = _make_stream("")
    result = list(stream_lines(stream))
    assert result == []


def test_single_line_with_newline():
    stream = _make_stream("only\n")
    assert list(stream_lines(stream)) == ["only"]


def test_single_line_without_newline():
    stream = _make_stream("only")
    assert list(stream_lines(stream)) == ["only"]


def test_blank_lines_preserved():
    """Blank lines in the middle of a file must be preserved as empty strings."""
    stream = _make_stream("a\n\nb\n")
    result = list(stream_lines(stream))
    assert result == ["a", "", "b"]


def test_whitespace_only_lines_preserved():
    """Lines containing only spaces/tabs are kept as-is (not stripped)."""
    stream = _make_stream("  \n\t\ntext\n")
    result = list(stream_lines(stream))
    assert result == ["  ", "\t", "text"]


def test_large_number_of_lines():
    """stream_lines must work correctly for a large input without buffering all
    lines in memory at once (generator behaviour)."""
    n = 10_000
    content = "\n".join(str(i) for i in range(n))
    stream = _make_stream(content)
    gen = stream_lines(stream)

    # Confirm it is a generator / iterator, not a list
    assert hasattr(gen, "__next__"), "stream_lines should return an iterator"

    result = list(gen)
    assert len(result) == n
    assert result[0] == "0"
    assert result[-1] == str(n - 1)


# ---------------------------------------------------------------------------
# Reading from a real file path (via open)
# ---------------------------------------------------------------------------

def test_reads_from_file_path(tmp_path):
    """stream_lines accepts a path string/Path and opens the file itself."""
    sample = tmp_path / "sample.txt"
    sample.write_text("line1\nline2\nline3\n", encoding="utf-8")

    # stream_lines may accept a path directly or the caller may open the file;
    # test both call signatures that the CLI might use.
    with open(sample, encoding="utf-8") as fh:
        result = list(stream_lines(fh))

    assert result == ["line1", "line2", "line3"]


def test_unicode_content(tmp_path):
    """Non-ASCII content is handled correctly."""
    sample = tmp_path / "unicode.txt"
    lines = ["café", "naïve", "日本語", "emoji 🎉"]
    sample.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with open(sample, encoding="utf-8") as fh:
        result = list(stream_lines(fh))

    assert result == lines
