from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_resurrection import check, remember


def test_resurrect_without_evidence_refuses(tmp_path: Path) -> None:
    memory = tmp_path / "fail.jsonl"
    remember(memory, {"approach_id": "pick-winner", "why": "induction must keep an antichain", "demotion_cause": "REFUSE_WINNER"})
    receipt = check(memory, {"approach_id": "pick-winner", "text": "just pick the best future"})
    assert receipt["reason"] == "REFUSE_RESURRECTION"
    phrase = check(memory, {"text": "just pick a winner this time"})
    assert phrase["reason"] == "REFUSE_RESURRECTION"


def test_new_evidence_clears(tmp_path: Path) -> None:
    memory = tmp_path / "fail.jsonl"
    remember(memory, {"approach_id": "merged-corpora", "why": "user and project MMMs mixed"})
    receipt = check(
        memory,
        {"approach_id": "merged-corpora", "new_evidence_digest": "a" * 64},
    )
    assert receipt["status"] == "CLEAR"
