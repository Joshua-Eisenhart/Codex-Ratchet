from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.remember import remember, resurrect


def test_resurrection_needs_bridge_or_evidence(tmp_path: Path) -> None:
    memory = tmp_path / "m.jsonl"
    assert remember(memory, {"kind": "failed_candidate", "id": "pick-winner", "why": "vote"})["status"] == "REMEMBERED"
    assert resurrect(memory, {"id": "pick-winner"})["reason"] == "REFUSE_RESURRECTION"
    assert resurrect(memory, {"id": "pick-winner", "new_bridge": "independent dualsolve"})["status"] == "CLEAR"
