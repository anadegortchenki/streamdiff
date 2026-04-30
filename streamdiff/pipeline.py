"""High-level pipeline: wire reader → differ → filter → stats → report."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from streamdiff.differ import DiffRecord, ChangeType, diff_streams
from streamdiff.filter import apply_filters, filter_unchanged
from streamdiff.stats import DiffStats
from streamdiff.reporter import DiffReport, build_report
from streamdiff.export import ExportFormat, export_report


@dataclass
class PipelineConfig:
    left_source: str
    right_source: str
    include_unchanged: bool = False
    change_types: Optional[List[ChangeType]] = None
    pattern: Optional[str] = None
    report_format: ExportFormat = ExportFormat.TEXT
    report_output: Optional[str] = None  # None → stdout
    emit_report: bool = True


@dataclass
class PipelineResult:
    records: List[DiffRecord]
    stats: DiffStats
    report: Optional[DiffReport] = None
    elapsed_seconds: float = 0.0


def _records_with_stats(
    stream: Iterator[DiffRecord],
) -> tuple[List[DiffRecord], DiffStats]:
    stats = DiffStats()
    records: List[DiffRecord] = []
    for rec in stream:
        records.append(rec)
        if rec.change_type is ChangeType.ADDED:
            stats.added += 1
        elif rec.change_type is ChangeType.REMOVED:
            stats.removed += 1
        else:
            stats.unchanged += 1
    stats._recalc()
    return records, stats


def _skip_lines(records: List[DiffRecord], n: int) -> List[DiffRecord]:
    return records[n:]


def run_pipeline(
    left_iter: Iterator[str],
    right_iter: Iterator[str],
    config: PipelineConfig,
) -> PipelineResult:
    start = time.monotonic()

    raw = diff_streams(left_iter, right_iter)

    filters = []
    if not config.include_unchanged:
        filters.append(filter_unchanged)

    filtered = apply_filters(raw, filters)

    records, stats = _records_with_stats(filtered)

    elapsed = time.monotonic() - start

    report: Optional[DiffReport] = None
    if config.emit_report:
        report = build_report(
            stats,
            left_source=config.left_source,
            right_source=config.right_source,
            elapsed_seconds=elapsed,
        )
        export_report(report, fmt=config.report_format, output_path=config.report_output)

    return PipelineResult(
        records=records,
        stats=stats,
        report=report,
        elapsed_seconds=elapsed,
    )
