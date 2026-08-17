from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.admit import admit


def test_named_tools_hold() -> None:
    skills = Path(os.environ["CB_SKILLS_ROOT"])
    wave = json.loads((skills / "cb-strategy-wave" / "wave.json").read_text())
    receipt = admit(wave, {})
    assert receipt["activated"] is False
    assert receipt["status"] in {"HOLD", "REFUSE"}


def test_context_wave_freezes_without_activating() -> None:
    skills = Path(os.environ["CB_SKILLS_ROOT"])
    wave = json.loads((skills / "cb-context-wave" / "wave.json").read_text())
    negatives = {
        "positive": "x",
        "reason_specific_negative": "x",
        "boundary": "x",
        "replay": "x",
        "severance": "x",
        "cancellation": "x",
        "receipt_tamper": "x",
    }
    contract = {
        "object_card": "card",
        "target_digest": "a" * 64,
        "context_epoch_digest": "b" * 64,
        "parent": "prove",
        "progress_measure": "execution exists",
        "claim_ceiling": "no promotion",
        "downstream_consumer": "route-truth",
        "promotion_allowed": False,
    }
    receipt = admit(wave, negatives, contract)
    assert receipt["status"] == "FROZEN"
    assert receipt["activated"] is False
    assert receipt["promotion_allowed"] is False
