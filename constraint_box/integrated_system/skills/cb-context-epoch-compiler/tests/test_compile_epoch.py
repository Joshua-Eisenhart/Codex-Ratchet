from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.compile_epoch import compile_epoch


def test_orphan_and_genesis() -> None:
    assert compile_epoch(None, [])["reason"] == "REFUSE_ORPHAN_EPOCH"
    sealed = compile_epoch(None, [{"class": "observation"}], genesis=True)
    assert sealed["status"] == "SEALED"
    assert sealed["truth_disposition"] is None
