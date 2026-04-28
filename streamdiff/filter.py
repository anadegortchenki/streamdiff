"""Filtering utilities for diff records."""

from __future__ import annotations

import re
from typing import Iterable, Iterator, Optional

from streamdiff.differ import ChangeType, DiffRecord


def filter_by_change_type(
    records: Iterable[DiffRecord],
    *types: ChangeType,
) -> Iterator[DiffRecord]:
    """Yield only records whose change_type is in *types."""
    allowed = frozenset(types)
    for record in records:
        if record.change_type in allowed:
            yield record


def filter_by_pattern(
    records: Iterable[DiffRecord],
    pattern: str,
    flags: int = 0,
) -> Iterator[DiffRecord]:
    """Yield only records whose content matches *pattern*.

    The regex is applied to whichever side is non-empty
    (``new_value`` for additions, ``old_value`` for removals,
    either for changes, and ``new_value`` for unchanged lines).
    """
    compiled = re.compile(pattern, flags)

    for record in records:
        text = record.new_value if record.new_value is not None else record.old_value
        if text is not None and compiled.search(text):
            yield record


def filter_unchanged(
    records: Iterable[DiffRecord],
) -> Iterator[DiffRecord]:
    """Convenience wrapper: drop UNCHANGED records."""
    return filter_by_change_type(
        records,
        ChangeType.ADDED,
        ChangeType.REMOVED,
        ChangeType.CHANGED,
    )


def apply_filters(
    records: Iterable[DiffRecord],
    *,
    change_types: Optional[list[ChangeType]] = None,
    pattern: Optional[str] = None,
    pattern_flags: int = 0,
    skip_unchanged: bool = False,
) -> Iterator[DiffRecord]:
    """Apply all requested filters in sequence.

    Parameters
    ----------
    records:
        Source iterable of :class:`DiffRecord`.
    change_types:
        When given, only records with a matching :class:`ChangeType` pass.
    pattern:
        When given, only records whose content matches this regex pass.
    pattern_flags:
        ``re`` flags forwarded to :func:`filter_by_pattern`.
    skip_unchanged:
        When *True*, UNCHANGED records are dropped (applied last).
    """
    stream: Iterable[DiffRecord] = records

    if change_types:
        stream = filter_by_change_type(stream, *change_types)

    if pattern is not None:
        stream = filter_by_pattern(stream, pattern, flags=pattern_flags)

    if skip_unchanged:
        stream = filter_unchanged(stream)

    yield from stream
