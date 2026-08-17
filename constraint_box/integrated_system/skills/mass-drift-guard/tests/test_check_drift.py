from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_drift import check


def test_missing_context_is_drift() -> None:
    assert check(None, None)["reason"] == "REFUSE_MASS_DRIFT"


def test_merged_corpora_is_drift() -> None:
    context = {"status": "REFUSE", "reason": "REFUSE_MERGED_CORPORA"}
    assert check(context, None)["status"] == "REFUSE"


def test_ready_context_and_open_antichain_is_clean() -> None:
    context = {"status": "CONTEXT_SNAPSHOT_READY", "admission_disposition": "demote_RUNTIME_ONLY"}
    harvest = {"winner_selected": False, "family_count": 7}
    assert check(context, harvest)["status"] == "DRIFT_CLEAN"
