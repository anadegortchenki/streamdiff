"""Checkpoint support: save and resume diff progress by line offset."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


_CHECKPOINT_VERSION = 1


@dataclass
class Checkpoint:
    """Persisted state allowing a diff run to be resumed."""

    left_offset: int = 0
    right_offset: int = 0
    version: int = _CHECKPOINT_VERSION

    def advance(self, left: int = 0, right: int = 0) -> None:
        """Increment offsets by the given amounts."""
        self.left_offset += left
        self.right_offset += right

    def is_fresh(self) -> bool:
        return self.left_offset == 0 and self.right_offset == 0


def save_checkpoint(path: Path | str, checkpoint: Checkpoint) -> None:
    """Atomically write *checkpoint* to *path* as JSON."""
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(checkpoint), indent=2))
    os.replace(tmp, path)


def load_checkpoint(path: Path | str) -> Optional[Checkpoint]:
    """Return a :class:`Checkpoint` loaded from *path*, or ``None`` if absent."""
    path = Path(path)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if data.get("version") != _CHECKPOINT_VERSION:
        raise ValueError(
            f"Unsupported checkpoint version: {data.get('version')!r}"
        )
    return Checkpoint(
        left_offset=int(data["left_offset"]),
        right_offset=int(data["right_offset"]),
    )


def delete_checkpoint(path: Path | str) -> None:
    """Remove *path* if it exists; silently ignore missing files."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
