from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.audit_proxy import audit


def test_missing_card_holds() -> None:
    assert audit({"object": "F"}, None, None)["status"] == "HOLD"


def test_named_card_without_delta() -> None:
    card = {
        "object": "finite Light seed F",
        "proxy": "wave-estate score",
        "bad_intervention": "add empty tests",
    }
    assert audit(card, None, None)["status"] == "NAMED"
