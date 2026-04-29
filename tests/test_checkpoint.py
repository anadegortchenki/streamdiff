"""Tests for streamdiff.checkpoint."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from streamdiff.checkpoint import (
    Checkpoint,
    save_checkpoint,
    load_checkpoint,
    delete_checkpoint,
)


# ---------------------------------------------------------------------------
# Checkpoint dataclass
# ---------------------------------------------------------------------------

class TestCheckpoint:
    def test_defaults_are_zero(self):
        cp = Checkpoint()
        assert cp.left_offset == 0
        assert cp.right_offset == 0

    def test_is_fresh_true_on_default(self):
        assert Checkpoint().is_fresh()

    def test_is_fresh_false_after_advance(self):
        cp = Checkpoint()
        cp.advance(left=5)
        assert not cp.is_fresh()

    def test_advance_increments_both(self):
        cp = Checkpoint(left_offset=10, right_offset=20)
        cp.advance(left=3, right=7)
        assert cp.left_offset == 13
        assert cp.right_offset == 27

    def test_advance_partial(self):
        cp = Checkpoint(left_offset=1, right_offset=1)
        cp.advance(right=4)
        assert cp.left_offset == 1
        assert cp.right_offset == 5


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    cp = Checkpoint(left_offset=42, right_offset=17)
    p = tmp_path / "state.json"
    save_checkpoint(p, cp)
    loaded = load_checkpoint(p)
    assert loaded is not None
    assert loaded.left_offset == 42
    assert loaded.right_offset == 17


def test_load_returns_none_for_missing_file(tmp_path):
    result = load_checkpoint(tmp_path / "nonexistent.json")
    assert result is None


def test_save_is_atomic(tmp_path):
    """Saving should not leave a .tmp file behind."""
    p = tmp_path / "state.json"
    save_checkpoint(p, Checkpoint(left_offset=1, right_offset=2))
    assert not (tmp_path / "state.tmp").exists()


def test_load_raises_on_wrong_version(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"left_offset": 0, "right_offset": 0, "version": 99}))
    with pytest.raises(ValueError, match="Unsupported checkpoint version"):
        load_checkpoint(p)


def test_delete_removes_file(tmp_path):
    p = tmp_path / "state.json"
    save_checkpoint(p, Checkpoint())
    delete_checkpoint(p)
    assert not p.exists()


def test_delete_silently_ignores_missing(tmp_path):
    delete_checkpoint(tmp_path / "ghost.json")  # should not raise
