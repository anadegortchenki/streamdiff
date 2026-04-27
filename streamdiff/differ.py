"""Core streaming diff logic.

Compares two sorted line streams and emits diff records without buffering
both streams fully in memory.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterator

from streamdiff.reader import stream_lines


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass
class DiffRecord:
    change: ChangeType
    line: str

    def __str__(self) -> str:
        prefix = {
            ChangeType.ADDED: "+ ",
            ChangeType.REMOVED: "- ",
            ChangeType.UNCHANGED: "  ",
        }[self.change]
        return f"{prefix}{self.line}"


def diff_streams(
    path_a: str,
    path_b: str,
    show_unchanged: bool = False,
) -> Iterator[DiffRecord]:
    """Diff two sorted line streams, yielding DiffRecord instances.

    Both inputs must be pre-sorted. Uses a merge-step approach so only
    one line per stream is held in memory at a time.

    Args:
        path_a: Path to the 'old' file (or '-' for stdin).
        path_b: Path to the 'new' file (or '-' for stdin).
        show_unchanged: Whether to emit UNCHANGED records.

    Yields:
        DiffRecord for each line encountered.
    """
    iter_a = stream_lines(path_a)
    iter_b = stream_lines(path_b)

    sentinel = object()
    a = next(iter_a, sentinel)
    b = next(iter_b, sentinel)

    while a is not sentinel and b is not sentinel:
        if a == b:
            if show_unchanged:
                yield DiffRecord(ChangeType.UNCHANGED, a)
            a = next(iter_a, sentinel)
            b = next(iter_b, sentinel)
        elif a < b:
            yield DiffRecord(ChangeType.REMOVED, a)
            a = next(iter_a, sentinel)
        else:
            yield DiffRecord(ChangeType.ADDED, b)
            b = next(iter_b, sentinel)

    while a is not sentinel:
        yield DiffRecord(ChangeType.REMOVED, a)
        a = next(iter_a, sentinel)

    while b is not sentinel:
        yield DiffRecord(ChangeType.ADDED, b)
        b = next(iter_b, sentinel)
