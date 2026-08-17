from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.ledger import append, head, load


def test_owner_statement_is_canon_and_proposal_needs_head(tmp_path: Path) -> None:
    ledger = tmp_path / "l.jsonl"
    first = append(ledger, {"kind": "owner_statement", "text": "Light is the OS"})
    assert first["canon"] is True
    assert append(ledger, {"kind": "proposal", "text": "new prompt"})["reason"] == "HOLD_LEDGER_UNBOUND"
    ok = append(ledger, {"kind": "proposal", "text": "new prompt", "head": first["entry_digest"]})
    assert ok["canon"] is False
    assert head(load(ledger)) == ok["entry_digest"]


def test_delete_refuses(tmp_path: Path) -> None:
    assert append(tmp_path / "l.jsonl", {"kind": "failure", "delete": True})["reason"] == "REFUSE_REWRITE"
