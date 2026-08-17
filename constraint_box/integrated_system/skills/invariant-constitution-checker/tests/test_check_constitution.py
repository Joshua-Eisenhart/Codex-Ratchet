from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_constitution import check


def test_rebase_and_promotion_refuse() -> None:
    assert check({"text": "git rebase the loop"})["reason"] == "REFUSE_CONSTITUTION"
    assert check({"text": "keep going", "promotion_allowed": True})["status"] == "REFUSE"


def test_ordinary_probe_holds() -> None:
    assert check({"text": "run seed-check and keep the antichain"})["status"] == "HOLDS"
