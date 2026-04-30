"""Export helpers: write a DiffReport to a file path or stdout."""
from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from streamdiff.reporter import DiffReport, render_json, render_text


class ExportFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


def _render(report: DiffReport, fmt: ExportFormat) -> str:
    if fmt is ExportFormat.JSON:
        return render_json(report)
    return render_text(report)


def export_report(
    report: DiffReport,
    fmt: ExportFormat = ExportFormat.TEXT,
    output_path: Optional[str] = None,
) -> None:
    """Render *report* and write to *output_path* (or stdout if None)."""
    content = _render(report, fmt)
    if output_path is None:
        sys.stdout.write(content + "\n")
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def report_to_string(
    report: DiffReport,
    fmt: ExportFormat = ExportFormat.TEXT,
) -> str:
    """Return the rendered report as a string (useful for testing / embedding)."""
    return _render(report, fmt)
