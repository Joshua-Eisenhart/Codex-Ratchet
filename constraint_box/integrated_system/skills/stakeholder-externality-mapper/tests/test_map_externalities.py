from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.map_externalities import check


def test_omission_and_map() -> None:
    assert check({"beneficiaries": ["loop score"], "bearers": ["evidence base"], "absent": ["future users"]})["reason"] == "REFUSE_OMISSION"
    ok = {
        "beneficiaries": ["operator"],
        "bearers": ["evidence base"],
        "absent": ["future users"],
        "mitigation": "append-only ledger and failure memory",
    }
    assert check(ok)["status"] == "MAPPED"
