"""Summary reporting: render DiffStats + metadata into human-readable or JSON reports."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from streamdiff.stats import DiffStats


@dataclass
class ReportMeta:
    left_source: str
    right_source: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    elapsed_seconds: Optional[float] = None


@dataclass
class DiffReport:
    meta: ReportMeta
    stats: DiffStats

    def to_dict(self) -> dict:
        return {
            "meta": {
                "left_source": self.meta.left_source,
                "right_source": self.meta.right_source,
                "generated_at": self.meta.generated_at,
                "elapsed_seconds": self.meta.elapsed_seconds,
            },
            "stats": {
                "added": self.stats.added,
                "removed": self.stats.removed,
                "unchanged": self.stats.unchanged,
                "total": self.stats.total,
                "changed": self.stats.changed,
                "change_ratio": round(self.stats.change_ratio, 4),
            },
        }


def render_text(report: DiffReport) -> str:
    m = report.meta
    s = report.stats
    lines = [
        f"Diff Report — {m.generated_at}",
        f"  Left  : {m.left_source}",
        f"  Right : {m.right_source}",
    ]
    if m.elapsed_seconds is not None:
        lines.append(f"  Time  : {m.elapsed_seconds:.3f}s")
    lines += [
        "",
        f"  Added    : {s.added}",
        f"  Removed  : {s.removed}",
        f"  Unchanged: {s.unchanged}",
        f"  Total    : {s.total}",
        f"  Changed %: {s.change_ratio * 100:.1f}%",
    ]
    return "\n".join(lines)


def render_json(report: DiffReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def build_report(
    stats: DiffStats,
    left_source: str,
    right_source: str,
    elapsed_seconds: Optional[float] = None,
) -> DiffReport:
    meta = ReportMeta(
        left_source=left_source,
        right_source=right_source,
        elapsed_seconds=elapsed_seconds,
    )
    return DiffReport(meta=meta, stats=stats)
