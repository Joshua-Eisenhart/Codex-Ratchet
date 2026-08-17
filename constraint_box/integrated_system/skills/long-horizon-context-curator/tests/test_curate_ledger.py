from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.curate_ledger import append, head_digest, load_entries


def test_append_intent_then_unbound_proposal_holds(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    first = append(ledger, {"kind": "intent", "text": "Light is the OS"})
    assert first["status"] == "APPENDED"
    assert first["canon"] is True
    held = append(ledger, {"kind": "proposal", "text": "newest prompt redefines the object"})
    assert held["status"] == "HOLD"
    assert held["reason"] == "HOLD_LEDGER_UNBOUND"


def test_proposal_bound_to_head_is_not_canon(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    first = append(ledger, {"kind": "intent", "text": "keep the antichain"})
    ok = append(ledger, {"kind": "proposal", "text": "try a new wave", "head": first["entry_digest"]})
    assert ok["status"] == "APPENDED"
    assert ok["canon"] is False
    entries = load_entries(ledger)
    assert head_digest(entries) == ok["entry_digest"]
    assert entries[0]["kind"] == "intent"


def test_rewrite_and_recency_as_canon_refuse(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    first = append(ledger, {"kind": "invariant", "text": "code decides"})
    assert append(ledger, {"kind": "proposal", "rewrite_index": 0, "head": first["entry_digest"]})["reason"] == "REFUSE_REWRITE"
    assert append(
        ledger,
        {"kind": "proposal", "text": "this is law now", "head": first["entry_digest"], "treat_as_canon": True},
    )["reason"] == "REFUSE_RECENCY_AS_CANON"
