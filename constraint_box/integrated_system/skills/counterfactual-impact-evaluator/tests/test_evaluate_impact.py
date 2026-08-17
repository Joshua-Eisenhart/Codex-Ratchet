from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.evaluate_impact import evaluate


def test_score_up_seed_down_is_theater() -> None:
    before = {"score": 1, "seed_admit": True, "light_decides_control": True, "valid_v1": 10, "zip_valid": True}
    after = {**before, "score": 9, "seed_admit": False}
    assert evaluate(before, after)["reason"] == "REFUSE_THEATER"
