from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_proxy import check


def _base() -> dict:
    return {
        "score": 100,
        "seed_admit": True,
        "light_decides_control": True,
        "valid_v1": 10,
        "zip_valid": True,
        "tests_passed": 13,
        "promotion_allowed": False,
        "test_failures": [],
    }


def test_score_up_seed_down_is_proxy() -> None:
    before = _base()
    after = {**before, "score": 200, "seed_admit": False}
    assert check(before, after)["reason"] == "REFUSE_PROXY"


def test_score_up_tests_down_is_proxy() -> None:
    before = _base()
    after = {**before, "score": 200, "tests_passed": 12}
    assert check(before, after)["status"] == "REFUSE"


def test_score_up_protected_holds_is_clean() -> None:
    before = _base()
    after = {**before, "score": 150, "tests_passed": 14}
    assert check(before, after)["status"] == "PROXY_CLEAN"
