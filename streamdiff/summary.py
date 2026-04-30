"""Human-readable summary generation for diff results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from streamdiff.stats import DiffStats


@dataclass
class SummaryOptions:
    show_ratio: bool = True
    show_unchanged: bool = False
    label_a: str = "a"
    label_b: str = "b"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_summary(stats: DiffStats, options: Optional[SummaryOptions] = None) -> str:
    """Return a concise multi-line summary string for *stats*."""
    if options is None:
        options = SummaryOptions()

    lines: list[str] = []

    lines.append(
        f"Compared {stats.total} line(s): "
        f"+{stats.added} added, "
        f"-{stats.removed} removed, "
        f"~{stats.modified} modified"
        + (f", {stats.unchanged} unchanged" if options.show_unchanged else "")
        + "."
    )

    if options.show_ratio and stats.total > 0:
        lines.append(
            f"Change ratio: {_pct(stats.change_ratio)} "
            f"({stats.changed}/{stats.total} lines affected)."
        )

    if stats.changed == 0:
        lines.append("Files are identical.")
    elif stats.removed == 0 and stats.modified == 0:
        lines.append(f"Only additions detected in {options.label_b}.")
    elif stats.added == 0 and stats.modified == 0:
        lines.append(f"Only removals detected relative to {options.label_a}.")

    return "\n".join(lines)


def print_summary(
    stats: DiffStats,
    options: Optional[SummaryOptions] = None,
    prefix: str = "",
) -> None:
    """Print the summary to stdout, optionally prefixed."""
    text = build_summary(stats, options)
    if prefix:
        text = "\n".join(f"{prefix}{line}" for line in text.splitlines())
    print(text)
