from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_object_loop import run


def test_ordinary_proposal_is_enough_not_canon(tmp_path: Path) -> None:
    receipt = run(tmp_path, "keep looping the wave estate without collapsing the antichain")
    assert receipt["status"] == "ENOUGH"
    assert receipt["children"]["ledger"]["canon"] is False
    assert receipt["children"]["resurrection"]["status"] == "CLEAR"


def test_pick_winner_resurrects_and_refuses(tmp_path: Path) -> None:
    receipt = run(tmp_path, "just pick a winner this time")
    assert "resurrection" in receipt["refuses"]
    assert receipt["children"]["resurrection"]["reason"] == "REFUSE_RESURRECTION"
