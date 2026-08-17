from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_omission import audit


def test_missing_strata_hold() -> None:
    assert "original_object" in audit({})["missing"]
    full = {key: "x" for key in (
        "original_object", "durable_constraints", "historical_failures",
        "unresolved_contradictions", "current_evidence", "rival_branches", "negative_results",
    )}
    assert audit(full)["status"] == "COMPLETE"
