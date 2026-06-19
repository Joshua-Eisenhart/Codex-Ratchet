#!/usr/bin/env python3
"""Pytest checks for carnot_szilard_landauer_ledger_v1."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "carnot_szilard_landauer_ledger_v1"
RESULT = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_envelope_results.json"


def load_payload() -> dict:
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_ledger_derived_carnot_rows() -> None:
    payload = load_payload()
    reversible = payload["cycle_ledger_tables"]["reversible_carnot_cycle"]
    sub = payload["cycle_ledger_tables"]["sub_carnot_irreversible_cycle"]
    super_row = payload["cycle_ledger_tables"]["candidate_super_carnot_cycle"]
    assert reversible["derived"]["eta"]["string"] == "1/2"
    assert reversible["derived"]["entropy_production"]["string"] == "0/1"
    assert sub["derived"]["eta"]["string"] == "1/4"
    assert sub["derived"]["entropy_production"]["num"] > 0
    assert super_row["derived"]["eta"]["string"] == "3/4"
    assert super_row["derived"]["entropy_production"]["num"] < 0
    assert payload["builder_gates"]["super_carnot_unsat_from_ledger_constraints"] is True


def test_persisted_witnesses_and_broken_fence_model() -> None:
    payload = load_payload()
    for engine in payload["persisted_witnesses"].values():
        for section in ("cycle_rows", "szilard_landauer_rows"):
            for row in engine[section].values():
                assert all(row.values())
    for engine, row in payload["controls"]["broken_fence_drop_entropy_constraint_super_carnot"].items():
        keys = ["julia_z3"] if engine == "julia" else ["z3", "cvc5"]
        assert row["numeric_eta_gt_eta_c"] is True
        for key in keys:
            assert row[key]["status"] == "sat"
            assert row[key].get("model")


def test_n01_and_no_builder_audit_verdict_gate() -> None:
    payload = load_payload()
    assert payload["no_builder_audit_verdict"] is True
    assert not (ROOT / "system_v6" / "sims" / SIM_ID / "audit_verdict.md").exists()
    for control in payload["controls"]["n01_order"].values():
        assert control["normal"]["verdict"] == "sat"
        assert control["permuted"]["verdict"] == "unsat"
        assert control["computed_by"]
    for control in payload["controls"]["misledgered_control"].values():
        assert control["status"] == "caught"
        assert control["errors"]
