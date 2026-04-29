"""High-level pipeline: wire reader → differ → filter → stats, with optional checkpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional

from streamdiff.differ import DiffRecord, diff_streams, ChangeType
from streamdiff.filter import apply_filters, filter_unchanged
from streamdiff.reader import stream_lines
from streamdiff.stats import DiffStats
from streamdiff.checkpoint import (
    Checkpoint,
    load_checkpoint,
    save_checkpoint,
    delete_checkpoint,
)


@dataclass
class PipelineConfig:
    left_path: str
    right_path: str
    show_unchanged: bool = False
    change_types: Optional[List[ChangeType]] = None
    pattern: Optional[str] = None
    checkpoint_path: Optional[str] = None


@dataclass
class PipelineResult:
    records: List[DiffRecord] = field(default_factory=list)
    stats: DiffStats = field(default_factory=DiffStats)


def _records_with_stats(
    source: Iterator[DiffRecord],
) -> tuple[list[DiffRecord], DiffStats]:
    stats = DiffStats()
    records: list[DiffRecord] = []
    for rec in source:
        stats.update(rec)
        records.append(rec)
    return records, stats


def _skip_lines(stream: Iterator[str], n: int) -> Iterator[str]:
    for _ in range(n):
        try:
            next(stream)
        except StopIteration:
            return
    yield from stream


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Execute the full diff pipeline according to *config*."""
    checkpoint: Checkpoint = Checkpoint()
    if config.checkpoint_path:
        loaded = load_checkpoint(config.checkpoint_path)
        if loaded is not None:
            checkpoint = loaded

    left_stream = stream_lines(config.left_path)
    right_stream = stream_lines(config.right_path)

    if not checkpoint.is_fresh():
        left_stream = _skip_lines(left_stream, checkpoint.left_offset)
        right_stream = _skip_lines(right_stream, checkpoint.right_offset)

    raw = diff_streams(left_stream, right_stream)
    filtered = apply_filters(
        raw,
        change_types=config.change_types,
        pattern=config.pattern,
    )
    if not config.show_unchanged:
        filtered = filter_unchanged(filtered)

    records, stats = _records_with_stats(filtered)

    if config.checkpoint_path:
        new_cp = Checkpoint(
            left_offset=checkpoint.left_offset + stats.total,
            right_offset=checkpoint.right_offset + stats.total,
        )
        if stats.total > 0:
            save_checkpoint(config.checkpoint_path, new_cp)
        else:
            delete_checkpoint(config.checkpoint_path)

    return PipelineResult(records=records, stats=stats)
