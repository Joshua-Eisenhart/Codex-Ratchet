#!/usr/bin/env python3
"""Z3 negative control for bare Pauli labels without Hopf/Weyl carrier metrics."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import z3
from receipt_boundary import apply_default_receipt_boundary


NAME = "z3_bare_pauli_no_carrier_fiber_base_metric_unsat"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "checks SAT/UNSAT controls for whether bare Pauli labels can satisfy declared carrier/projection metric predicates",
    }
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}


def solver_result(*formulas: z3.BoolRef) -> str:
    solver = z3.Solver()
    solver.add(*formulas)
    result = solver.check()
    if result == z3.sat:
        return "sat"
    if result == z3.unsat:
        return "unsat"
    return "unknown"


def carrier_metric_axioms() -> dict[str, z3.BoolRef | z3.BoolRef]:
    has_carrier = z3.Bool("has_carrier")
    has_projection = z3.Bool("has_projection")
    has_only_pauli_label = z3.Bool("has_only_pauli_label")
    fiber_s3_visible = z3.Bool("fiber_s3_visible")
    fiber_s2_hidden = z3.Bool("fiber_s2_hidden")
    base_s3_visible = z3.Bool("base_s3_visible")
    base_s2_visible = z3.Bool("base_s2_visible")
    pole_base_s2_collapsed = z3.Bool("pole_base_s2_collapsed")
    axioms = z3.And(
        z3.Implies(has_only_pauli_label, z3.And(z3.Not(has_carrier), z3.Not(has_projection))),
        z3.Implies(z3.Not(has_carrier), z3.And(z3.Not(fiber_s3_visible), z3.Not(base_s3_visible))),
        z3.Implies(z3.Not(has_projection), z3.And(z3.Not(base_s2_visible), fiber_s2_hidden)),
        z3.Implies(z3.And(has_carrier, has_projection), pole_base_s2_collapsed),
    )
    return {
        "has_carrier": has_carrier,
        "has_projection": has_projection,
        "has_only_pauli_label": has_only_pauli_label,
        "fiber_s3_visible": fiber_s3_visible,
        "fiber_s2_hidden": fiber_s2_hidden,
        "base_s3_visible": base_s3_visible,
        "base_s2_visible": base_s2_visible,
        "pole_base_s2_collapsed": pole_base_s2_collapsed,
        "axioms": axioms,
    }


def run_checks() -> tuple[dict[str, object], dict[str, object]]:
    c = carrier_metric_axioms()
    required_metric_pattern = z3.And(
        c["fiber_s3_visible"],
        c["fiber_s2_hidden"],
        c["base_s3_visible"],
        c["base_s2_visible"],
        c["pole_base_s2_collapsed"],
    )
    positive = {
        "carrier_and_projection_can_satisfy_metric_pattern": {
            "z3_result": solver_result(c["axioms"], c["has_carrier"], c["has_projection"], required_metric_pattern),
            "expected": "sat",
        },
        "bare_pauli_label_without_metric_claim_is_consistent": {
            "z3_result": solver_result(c["axioms"], c["has_only_pauli_label"]),
            "expected": "sat",
        },
    }
    graveyards = {
        "bare_pauli_label_cannot_supply_s3_carrier_motion": {
            "z3_result": solver_result(c["axioms"], c["has_only_pauli_label"], c["fiber_s3_visible"]),
            "expected": "unsat",
        },
        "bare_pauli_label_cannot_supply_base_projection_motion": {
            "z3_result": solver_result(c["axioms"], c["has_only_pauli_label"], c["base_s2_visible"]),
            "expected": "unsat",
        },
        "bare_pauli_label_cannot_satisfy_full_fiber_base_metric_pattern": {
            "z3_result": solver_result(c["axioms"], c["has_only_pauli_label"], required_metric_pattern),
            "expected": "unsat",
        },
        "projection_without_carrier_cannot_supply_s3_motion": {
            "z3_result": solver_result(c["axioms"], z3.Not(c["has_carrier"]), c["has_projection"], c["base_s3_visible"]),
            "expected": "unsat",
        },
        "carrier_without_projection_cannot_supply_base_s2_motion": {
            "z3_result": solver_result(c["axioms"], c["has_carrier"], z3.Not(c["has_projection"]), c["base_s2_visible"]),
            "expected": "unsat",
        },
    }
    for row in positive.values():
        row["passed"] = row["z3_result"] == row["expected"]
    for row in graveyards.values():
        row["passed"] = row["z3_result"] == row["expected"]
    return positive, graveyards


def main() -> int:
    positive, graveyards = run_checks()
    all_pass = bool(all(row["passed"] for row in positive.values()) and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Z3 bare-Pauli/no-carrier negative-control baseline only; this formalizes that label-only Pauli predicates "
            "cannot supply declared Hopf/Weyl S3-carrier and S2-projection metric facts; no physical geometry, no flux, "
            "no QIT, GStack, axis, bridge, nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "bare_pauli_no_carrier_negative_control",
        "promotion_condition": "No promotion from this receipt; use only as a negative control beside carrier-geometry receipts.",
        "demotion_condition": (
            "Demote if bare Pauli labels become SAT for S3 carrier motion, base S2 projection motion, or the full "
            "fiber/base metric pattern without explicit carrier and projection predicates."
        ),
        "blocked_until": "blocked from all topology, carrier, flux, and target-system claims until separate carrier receipts exist",
        "out_of_scope": [
            "No Hopf/Weyl carrier is constructed.",
            "No S3 or S2 metric is computed.",
            "No flux representation or Pauli-boundary shortcut.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This negative control is intentionally label-only. It supports the boundary that Pauli labels do not replace "
            "carrier/projection geometry."
        ),
        "operation_sequence": [
            "declare Boolean predicates for carrier, projection, and bare Pauli label availability",
            "declare Boolean predicates for S3 carrier motion and S2 projection motion readouts",
            "assert that bare Pauli labels imply no carrier and no projection",
            "assert that absent carrier prevents S3 motion readouts",
            "assert that absent projection prevents base S2 motion readouts",
            "check that the full carrier/projection metric pattern is SAT only when carrier and projection are present",
            "check that bare Pauli label controls are UNSAT for the metric pattern",
        ],
        "carrier_topology": "none; finite Boolean predicate model separating bare label availability from carrier/projection availability",
        "observable": "Z3 SAT/UNSAT outcomes for carrier/projection metric predicates under bare Pauli label controls",
        "pass_fail_predicate": (
            "carrier plus projection can satisfy the metric pattern, bare Pauli label alone is consistent only without "
            "metric claims, and bare Pauli label plus any carrier/projection metric claim is UNSAT"
        ),
        "graveyards": [
            "bare Pauli label cannot supply S3 carrier motion",
            "bare Pauli label cannot supply base S2 projection motion",
            "bare Pauli label cannot satisfy full fiber-base metric pattern",
            "projection without carrier cannot supply S3 motion",
            "carrier without projection cannot supply base S2 motion",
        ],
        "baselines": [
            "Pauli orientation integer predicate baseline",
            "SymPy Hopf/Weyl S3/S2 exact identity baseline",
            "Geomstats Hopf/Weyl S3/S2 distance baseline",
        ],
        "alternative_formulations": [
            "cvc5 Boolean negative control for the same predicates",
            "SymPy carrier-free Pauli label gap identity",
            "Clifford bare-generator control without carrier coordinates",
        ],
        "exact_tool_function_needs": {
            "z3": ["Bool", "And", "Not", "Implies", "Solver.check"],
        },
        "lego_or_coupling_target": "bare_pauli_no_carrier_negative_control",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
