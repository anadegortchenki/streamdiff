"""Statistics collection for diff results."""

from dataclasses import dataclass, field
from typing import Iterable

from streamdiff.differ import ChangeType, DiffRecord


@dataclass
class DiffStats:
    """Aggregated statistics over a stream of DiffRecords."""

    added: int = 0
    removed: int = 0
    unchanged: int = 0
    total: int = field(init=False)

    def __post_init__(self) -> None:
        self._recalc()

    def _recalc(self) -> None:
        self.total = self.added + self.removed + self.unchanged

    @property
    def changed(self) -> int:
        return self.added + self.removed

    @property
    def change_ratio(self) -> float:
        """Fraction of lines that are added or removed (0.0 – 1.0)."""
        if self.total == 0:
            return 0.0
        return self.changed / self.total

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DiffStats(added={self.added}, removed={self.removed}, "
            f"unchanged={self.unchanged}, total={self.total})"
        )


def collect_stats(records: Iterable[DiffRecord]) -> DiffStats:
    """Consume an iterable of DiffRecords and return aggregated DiffStats.

    The iterable is consumed exactly once; suitable for use with generators.
    """
    added = removed = unchanged = 0
    for record in records:
        if record.change_type == ChangeType.ADDED:
            added += 1
        elif record.change_type == ChangeType.REMOVED:
            removed += 1
        else:
            unchanged += 1
    stats = DiffStats(added=added, removed=removed, unchanged=unchanged)
    stats._recalc()
    return stats
