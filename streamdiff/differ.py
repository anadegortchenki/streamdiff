"""Core diffing logic for streamdiff."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional

from streamdiff.reader import stream_lines


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass
class DiffRecord:
    change_type: ChangeType
    content: str
    line_a: Optional[int] = field(default=None)
    line_b: Optional[int] = field(default=None)

    def __str__(self) -> str:
        prefix = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.UNCHANGED: " ",
        }[self.change_type]
        return f"{prefix} {self.content}"


def diff_streams(
    path_a: str,
    path_b: str,
    context: int = 0,
    ignore_whitespace: bool = False,
) -> Iterator[DiffRecord]:
    """Yield DiffRecord objects by comparing two line-oriented streams.

    Uses a simple LCS-free greedy approach suitable for large files:
    reads both streams line by line and emits records without buffering
    the full file. When lines differ it buffers a small window to detect
    matching lines ahead (up to `context` lines of look-ahead).
    """
    LOOKAHEAD = max(context, 8)

    def normalize(line: str) -> str:
        return line.strip() if ignore_whitespace else line

    iter_a = stream_lines(path_a)
    iter_b = stream_lines(path_b)

    buf_a: list[tuple[int, str]] = []
    buf_b: list[tuple[int, str]] = []

    line_num_a = 0
    line_num_b = 0

    def pull_a(n: int = 1):
        nonlocal line_num_a
        for _ in range(n):
            try:
                line_num_a += 1
                buf_a.append((line_num_a, next(iter_a)))
            except StopIteration:
                break

    def pull_b(n: int = 1):
        nonlocal line_num_b
        for _ in range(n):
            try:
                line_num_b += 1
                buf_b.append((line_num_b, next(iter_b)))
            except StopIteration:
                break

    pull_a(LOOKAHEAD)
    pull_b(LOOKAHEAD)

    while buf_a or buf_b:
        if not buf_a:
            la, line = buf_b.pop(0)
            pull_b()
            yield DiffRecord(ChangeType.ADDED, line, line_b=la)
            continue
        if not buf_b:
            la, line = buf_a.pop(0)
            pull_a()
            yield DiffRecord(ChangeType.REMOVED, line, line_a=la)
            continue

        la, line_a = buf_a[0]
        lb, line_b = buf_b[0]

        if normalize(line_a) == normalize(line_b):
            buf_a.pop(0)
            buf_b.pop(0)
            pull_a()
            pull_b()
            yield DiffRecord(ChangeType.UNCHANGED, line_a, line_a=la, line_b=lb)
        else:
            # Look ahead to find a match
            match_in_b = next(
                (i for i, (_, l) in enumerate(buf_b) if normalize(l) == normalize(line_a)),
                None,
            )
            match_in_a = next(
                (i for i, (_, l) in enumerate(buf_a) if normalize(l) == normalize(line_b)),
                None,
            )

            if match_in_b is not None and (
                match_in_a is None or match_in_b <= match_in_a
            ):
                lb2, line_b2 = buf_b.pop(0)
                pull_b()
                yield DiffRecord(ChangeType.ADDED, line_b2, line_b=lb2)
            else:
                la2, line_a2 = buf_a.pop(0)
                pull_a()
                yield DiffRecord(ChangeType.REMOVED, line_a2, line_a=la2)
