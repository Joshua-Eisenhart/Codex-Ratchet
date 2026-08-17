from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.watch import watch


def test_fake_full_is_blocked() -> None:
    receipt = watch({"route_truth": "FULL", "model_free": True})
    assert "drift" in receipt["findings"]
    assert receipt["verb"] == "block_full"
    assert receipt["content_vote"] is False
