from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_kill_criteria import check


def test_missing_and_fired() -> None:
    assert check({"failure_modes": ["x"]})["status"] == "HOLD"
    plan = {"failure_modes": ["proxy"], "tripwires": ["seed_red"], "stop_or_demote": "stop", "already_fired": ["seed_red"]}
    assert check(plan)["reason"] == "REFUSE_DEAD_PLAN"


def test_armed() -> None:
    assert check({"failure_modes": ["proxy"], "tripwires": ["seed_red"], "stop_or_demote": "stop"})["status"] == "ARMED"
