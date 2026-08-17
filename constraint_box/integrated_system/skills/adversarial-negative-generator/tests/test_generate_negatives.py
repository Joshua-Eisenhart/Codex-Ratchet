from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.generate_negatives import generate


def test_five_twins() -> None:
    receipt = generate({"name": "wave-estate"})
    assert receipt["count"] == 5
    assert {row["id"] for row in receipt["twins"]} == {
        "reward_hack",
        "shortcut",
        "metric_gaming",
        "reversed_objective",
        "degenerate",
    }
