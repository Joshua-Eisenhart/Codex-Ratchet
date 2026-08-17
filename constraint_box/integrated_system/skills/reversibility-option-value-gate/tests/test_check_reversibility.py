from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_reversibility import check


def test_irreversible_without_receipt() -> None:
    assert check({"irreversible": True})["reason"] == "REFUSE_IRREVERSIBLE"
    assert check({"irreversible": True, "evidence_receipt": "abc"})["status"] == "REVERSIBLE_OR_EVIDENCED"
