from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.compile_output import compile_output


def test_hidden_failures_refuse() -> None:
    assert compile_output({"schema": "constraintbox.wave-execution.v1"}, {"hide_failures": True})["reason"] == "REFUSE_CLEAN_PROSE"


def test_model_free_full_is_marked_missing() -> None:
    surface = compile_output({"schema": "constraintbox.wave-execution.v1", "route_truth": "FULL", "model_free": True, "state": "PARTIAL"})
    assert "fake_full" in surface["missing_evidence"]
    assert surface["promotion_allowed"] is False
