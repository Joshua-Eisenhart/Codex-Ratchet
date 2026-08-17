from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.admit_delta import admit


def test_recency_cannot_outrank_primary() -> None:
    assert admit({"class": "proposal", "outranks_primary": True})["reason"] == "REFUSE_RECENCY_OUTRANKS_PRIMARY"


def test_observation_admits() -> None:
    assert admit({"class": "observation", "text": "seed ADMIT"})["status"] == "ADMITTED"
