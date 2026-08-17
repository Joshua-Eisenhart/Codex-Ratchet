from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.judge_enough import judge


def test_stop_and_continue() -> None:
    assert judge({"delta": 0})["reason"] == "NO_IMPROVE"
    assert judge({"delta": 10, "round": 1, "round_cap": 8})["status"] == "CONTINUE"
    assert judge({"delta": 10, "handoff": True})["reason"] == "HUMAN_HANDOFF"
