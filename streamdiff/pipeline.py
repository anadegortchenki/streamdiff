"""High-level pipeline: read → diff → filter → format."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import IO, Iterator, List, Optional

from streamdiff.differ import ChangeType, DiffRecord, diff_streams
from streamdiff.filter import apply_filters
from streamdiff.formatter import OutputFormat, format_json, format_text, format_unified
from streamdiff.reader import stream_lines
from streamdiff.stats import DiffStats


@dataclass
class PipelineConfig:
    """All knobs for a single diff pipeline run."""

    output_format: OutputFormat = OutputFormat.TEXT
    skip_unchanged: bool = False
    change_types: Optional[List[ChangeType]] = None
    pattern: Optional[str] = None
    pattern_flags: int = 0
    context_lines: int = 3  # used by unified format
    color: bool = True


@dataclass
class PipelineResult:
    """Outcome of :func:`run_pipeline`."""

    lines: List[str] = field(default_factory=list)
    stats: DiffStats = field(default_factory=DiffStats)


def _records_with_stats(
    records: Iterator[DiffRecord],
    stats: DiffStats,
) -> Iterator[DiffRecord]:
    """Pass-through iterator that accumulates stats as records flow."""
    for record in records:
        stats.update(record)
        yield record


def run_pipeline(
    left: IO[str],
    right: IO[str],
    config: Optional[PipelineConfig] = None,
) -> PipelineResult:
    """Execute the full diff pipeline and return formatted lines + stats.

    Parameters
    ----------
    left:
        File-like object for the *old* stream.
    right:
        File-like object for the *new* stream.
    config:
        Pipeline configuration; defaults to :class:`PipelineConfig` defaults.
    """
    if config is None:
        config = PipelineConfig()

    result = PipelineResult()

    left_lines = stream_lines(left)
    right_lines = stream_lines(right)

    raw_records = diff_streams(left_lines, right_lines)

    tracked = _records_with_stats(raw_records, result.stats)

    filtered = apply_filters(
        tracked,
        change_types=config.change_types,
        pattern=config.pattern,
        pattern_flags=config.pattern_flags,
        skip_unchanged=config.skip_unchanged,
    )

    fmt = config.output_format
    if fmt == OutputFormat.JSON:
        output_iter = format_json(filtered)
    elif fmt == OutputFormat.UNIFIED:
        output_iter = format_unified(filtered, context=config.context_lines)
    else:
        output_iter = format_text(filtered, color=config.color)

    result.lines = list(output_iter)
    return result
