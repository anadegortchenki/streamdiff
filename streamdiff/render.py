"""High-level rendering helpers that combine formatter + summary output."""
from __future__ import annotations

import sys
from typing import Iterable, TextIO

from streamdiff.differ import DiffRecord
from streamdiff.formatter import OutputFormat, format_json, format_text, format_unified
from streamdiff.stats import DiffStats
from streamdiff.summary import SummaryOptions, build_summary

_FORMATTERS = {
    OutputFormat.TEXT: format_text,
    OutputFormat.JSON: format_json,
    OutputFormat.UNIFIED: format_unified,
}


def render_diff(
    records: Iterable[DiffRecord],
    *,
    fmt: OutputFormat = OutputFormat.TEXT,
    out: TextIO = sys.stdout,
    color: bool = False,
) -> DiffStats:
    """Stream *records* to *out* using *fmt* and return accumulated stats."""
    stats = DiffStats()
    formatter = _FORMATTERS[fmt]

    for line in formatter(records, color=color):
        out.write(line)
        if not line.endswith("\n"):
            out.write("\n")

    return stats


def render_with_summary(
    records: Iterable[DiffRecord],
    *,
    fmt: OutputFormat = OutputFormat.TEXT,
    out: TextIO = sys.stdout,
    color: bool = False,
    summary_options: SummaryOptions | None = None,
    stats: DiffStats | None = None,
) -> DiffStats:
    """Render diff records then append a summary block.

    If *stats* is provided it is used for the summary directly (useful when
    the caller already collected stats from the pipeline).  Otherwise a fresh
    :class:`DiffStats` placeholder is returned and the summary will reflect
    zero counts — callers should prefer passing pre-computed stats.
    """
    render_diff(records, fmt=fmt, out=out, color=color)

    effective_stats = stats if stats is not None else DiffStats()
    summary = build_summary(effective_stats, summary_options)

    out.write("\n")
    for line in summary.splitlines():
        out.write(f"# {line}\n")

    return effective_stats
