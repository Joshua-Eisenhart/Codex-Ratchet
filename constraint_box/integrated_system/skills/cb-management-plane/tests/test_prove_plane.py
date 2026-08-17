from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.prove_plane import prove


def test_prove_emits_execution_not_full_and_not_heavy(tmp_path: Path) -> None:
    receipt = prove(tmp_path)
    assert receipt["execution_schema"] == "constraintbox.wave-execution.v1"
    assert receipt["route_truth"] == "NOT_FULL"
    assert receipt["model_free"] is True
    assert receipt["recipe_activated"] is False
    assert receipt["heavy_execution_verified"] is False
    assert receipt["promotion_allowed"] is False
    assert (tmp_path / "receipts/management_plane/wave-execution.v1.json").is_file()
