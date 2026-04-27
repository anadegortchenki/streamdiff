"""Streaming line reader for large datasets.

Provides an iterator-based interface for reading lines from files or stdin
without loading the entire dataset into memory.
"""

import sys
from typing import Iterator, Optional


def stream_lines(path: Optional[str] = None, encoding: str = "utf-8") -> Iterator[str]:
    """Yield stripped lines from a file path or stdin.

    Args:
        path: Path to the file to read. If None or '-', reads from stdin.
        encoding: File encoding (default: utf-8).

    Yields:
        Stripped lines from the source.
    """
    if path is None or path == "-":
        yield from _read_stream(sys.stdin)
    else:
        with open(path, "r", encoding=encoding) as fh:
            yield from _read_stream(fh)


def _read_stream(stream) -> Iterator[str]:
    """Yield stripped, non-empty lines from an open stream."""
    for line in stream:
        stripped = line.rstrip("\n")
        yield stripped
