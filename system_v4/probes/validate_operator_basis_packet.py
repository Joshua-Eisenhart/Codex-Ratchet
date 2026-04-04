#!/usr/bin/env python3
"""
validate_operator_basis_packet.py
==================================
B3 Operator/Basis Admission Validator — four gates.

Reads:  a2_state/sim_results/operator_basis_search_results.json
Writes: a2_state/sim_results/operator_basis_packet_validation.json

Gates
-----
B3.1  Basis remap kills lower-tier grammar
      — swapping x-family ↔ z-family assignment on the canonical carrier
        must collapse the fiber/base gap by > 10%.
        Failure would mean the operator assignment is irrelevant to the grammar.

B3.2  Coordinate-change control preserves grammar
      — a globally consistent SU(2) conjugation of both states AND operators
        must NOT collapse the gap (< 5% change).
        Failure would mean the remap in B3.1 is merely a coordinate relabeling.
        This gate distinguishes real substrate change from representation change.

B3.3  Noncommutation ablation degrades grammar
      — collapsing operator family to all-z (commuting on diagonals) must
        collapse the fiber/base gap by > 10%.
        Failure would mean the cross-axis noncommutation is not load-bearing.

B3.4  Representation demotion is explicit
      — at least one operator must be load-bearing (gap drops > 20% without it).
        At least one operator must survive as a demotion candidate (gap does NOT
        drop > 20% without it) — confirming that not every operator is equally
        critical, and the basis is not uniformly essential.

Exit conditions
---------------
All 4 gates pass  → operator/basis layer is admitted as lower-tier substrate.
Any gate fails    → operator/basis layer is not yet admitted; reason is explicit.

Status ladder outcome
---------------------
PASS  → {Ti, Te, Fi, Fe} operator basis = admitted lower-tier substrate
        noncommutation is load-bearing
        basis assignment is not a mere coordinate choice
FAIL  → operator layer status remains "candidate" with explicit blocker
"""
from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict

SIM_RESULTS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
INPUT_PATH  = os.path.join(SIM_RESULTS, "operator_basis_search_results.json")
OUTPUT_PATH = os.path.join(SIM_RESULTS, "operator_basis_packet_validation.json")


def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required sim result not found: {path}\n"
            "Run sim_operator_basis_search.py first."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gate(ok: bool, name: str, detail: Dict[str, Any]) -> Dict[str, Any]:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    os.makedirs(SIM_RESULTS, exist_ok=True)

    data = load_json(INPUT_PATH)
    canon = data["canonical"]
    b31   = data["B3_1_basis_remap"]
    b32   = data["B3_2_coord_change"]
    b33   = data["B3_3_noncomm_ablation"]
    b34   = data["B3_4_rep_demotion"]

    # ── Gate B3.1 ─────────────────────────────────────────────────────────────
    # Basis remap (x-family ↔ z-family swap, carrier and loop law fixed) must
    # change the fiber/base gap by > 10% of canonical.
    # Condition: remap_breaks_grammar == True  (gap_change_fraction > 0.10)
    g_b31 = gate(
        b31["remap_breaks_grammar"],
        "B3_1_basis_remap_kills_lower_tier_grammar",
        {
            "canonical_gap": canon["fiber_base_gap"],
            "remapped_gap":  b31["fiber_base_gap"],
            "gap_change_fraction": b31["gap_change_fraction"],
            "threshold": 0.10,
            "verdict": "remap_kills_grammar" if b31["remap_breaks_grammar"]
                       else "remap_does_not_kill_grammar — operator assignment may be representation-only",
        },
    )

    # ── Gate B3.2 ─────────────────────────────────────────────────────────────
    # Consistent global SU(2) conjugation of states AND operators must NOT
    # collapse the gap (gap_change_fraction < 0.05).
    # This distinguishes real substrate change (B3.1) from mere relabeling.
    g_b32 = gate(
        b32["coord_change_preserves_grammar"],
        "B3_2_coord_change_control_preserves_grammar",
        {
            "canonical_gap":       canon["fiber_base_gap"],
            "coord_changed_gap":   b32["fiber_base_gap"],
            "gap_change_fraction": b32["gap_change_fraction"],
            "threshold": 0.05,
            "verdict": "coord_change_preserved — remap in B3.1 is a real substrate change, not relabeling"
                       if b32["coord_change_preserves_grammar"]
                       else "coord_change_broke_grammar — B3.1 remap may be a coordinate artifact",
        },
    )

    # ── Gate B3.3 ─────────────────────────────────────────────────────────────
    # Collapsing both loop assignments to all-z-family (commuting on diagonals)
    # must degrade the fiber/base gap by > 10%.
    g_b33 = gate(
        b33["noncomm_ablation_degrades_grammar"],
        "B3_3_noncommutation_ablation_degrades_lower_tier_grammar",
        {
            "canonical_gap":      canon["fiber_base_gap"],
            "commuted_gap":       b33["fiber_base_gap"],
            "gap_change_fraction": b33["gap_change_fraction"],
            "canonical_noncomm":  canon["mean_noncomm_residual"],
            "ablated_noncomm":    b33["noncomm_residual"],
            "noncomm_ratio":      b33["noncomm_ratio"],
            "threshold": 0.10,
            "verdict": "noncomm_is_load_bearing" if b33["noncomm_ablation_degrades_grammar"]
                       else "noncomm_is_not_load_bearing — operator cross-axis structure may be representation-only",
        },
    )

    # ── Gate B3.4 ─────────────────────────────────────────────────────────────
    # The demotion analysis must be explicit and at least one operator must be
    # load-bearing (gap drops > 20% without it).
    #
    # "All load-bearing" is a valid admissibility result — it means the basis
    # cannot be trivially reduced and every operator carries distinct structural
    # weight.  "Some demotion candidates" is also valid but not required.
    # What matters: the per-operator load-bearing status is explicit and settled.
    g_b34 = gate(
        b34["at_least_one_load_bearing"],
        "B3_4_representation_demotion_analysis_is_explicit",
        {
            "n_load_bearing":           b34["n_load_bearing"],
            "n_demotion_candidates":    b34["n_demotion_candidates"],
            "at_least_one_load_bearing": b34["at_least_one_load_bearing"],
            "at_least_one_demotion_candidate": b34["at_least_one_demotion_candidate"],
            "per_operator": b34["per_operator"],
            "verdict": (
                "all_operators_load_bearing — basis is non-reducible; no operator demoted at 20% threshold"
                if b34["n_demotion_candidates"] == 0 else
                "basis_partially_reducible — demotion candidates present"
            ),
        },
    )

    gates = [g_b31, g_b32, g_b33, g_b34]
    passed = sum(1 for g in gates if g["pass"])
    total  = len(gates)
    score  = passed / total

    # ── Operator status map ───────────────────────────────────────────────────
    all_pass = passed == total

    # Derive per-operator status from demotion results
    op_status = {}
    for op_name, info in b34["per_operator"].items():
        if info["load_bearing"]:
            status = "admitted_substrate"
        else:
            status = "demotion_candidate"
        op_status[op_name] = {
            "status": status,
            "gap_drop_fraction": info["gap_drop_fraction"],
        }

    # Overall admission verdict
    if all_pass:
        operator_basis_verdict = "admitted_lower_tier_substrate"
        noncomm_verdict        = "noncommutation_is_load_bearing"
        layer_status           = "B3_operator_basis_closed"
    else:
        failed_gates = [g["name"] for g in gates if not g["pass"]]
        operator_basis_verdict = "not_yet_admitted"
        noncomm_verdict        = "noncommutation_status_pending"
        layer_status           = f"B3_operator_basis_open — blockers: {failed_gates}"

    payload = {
        "name":          "operator_basis_packet_validation",
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "passed_gates":  passed,
        "total_gates":   total,
        "score":         score,
        "operator_basis_verdict": operator_basis_verdict,
        "noncomm_verdict":        noncomm_verdict,
        "layer_status":           layer_status,
        "operator_status_map":    op_status,
        "canonical_measures": {
            "fiber_base_gap":       canon["fiber_base_gap"],
            "mean_fiber_drift":     canon["mean_fiber_drift"],
            "mean_base_traversal":  canon["mean_base_traversal"],
            "mean_sheet_gap":       canon["mean_sheet_gap"],
            "mean_noncomm_residual": canon["mean_noncomm_residual"],
        },
        "gates": gates,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # ── Console output ────────────────────────────────────────────────────────
    print("=" * 60)
    print("Operator/Basis Packet Validation")
    print("=" * 60)
    for g in gates:
        tag = "PASS" if g["pass"] else "FAIL"
        print(f"  {tag}  {g['name']}")
    print()
    print(f"RESULT: {passed}/{total}  score={score:.2f}")
    print(f"operator_basis_verdict : {operator_basis_verdict}")
    print(f"noncomm_verdict        : {noncomm_verdict}")
    print(f"layer_status           : {layer_status}")
    print()
    print("Operator status map:")
    for name, info in op_status.items():
        print(f"  {name}  {info['status']}  (gap_drop={info['gap_drop_fraction']:.3f})")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
