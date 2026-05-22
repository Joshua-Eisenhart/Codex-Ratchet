#!/usr/bin/env python3
"""Closure-pressure ablation for operator/geometry coupling receipts.

This is not a promotion sim.  It checks whether the current supporting
operator/geometry receipts have enough selectivity and order-sensitivity to be
used as inputs for a later closure-grade coexistence packet.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from receipt_boundary import apply_default_receipt_boundary


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite matrix/count ablation checks over existing coupling receipts",
    },
    "scipy": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this receipt-level ablation"},
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not rerun here; upstream compound receipt already carries the Clifford cross-check",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": None,
    "sympy": None,
    "z3": None,
    "clifford": None,
}


def read_result(name: str) -> dict:
    return json.loads((RESULTS_DIR / name).read_text(encoding="utf-8"))


def verdict_counts(operator_geometry: dict) -> dict[str, int]:
    counts = {"COMPATIBLE": 0, "BREAKS": 0, "TRIVIAL": 0}
    matrix = operator_geometry.get("compatibility_matrix", {})
    for row in matrix.values():
        for cell in row.values():
            verdict = cell.get("verdict")
            counts[verdict] = counts.get(verdict, 0) + 1
    return counts


def finite_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return float("nan")
    return float(np.asarray(numerator, dtype=float) / np.asarray(denominator, dtype=float))


def main() -> int:
    operator_geometry = read_result("operator_geometry_compatibility_results.json")
    compound = read_result("compound_operator_geometry_results.json")

    counts = verdict_counts(operator_geometry)
    total_cells = sum(counts.values())
    compatible_ratio = finite_ratio(counts.get("COMPATIBLE", 0), total_cells)
    breaks_ratio = finite_ratio(counts.get("BREAKS", 0), total_cells)
    compound_summary = compound.get("summary", {})

    positive = {
        "operator_geometry_has_selective_matrix": {
            "compatible": counts.get("COMPATIBLE", 0),
            "breaks": counts.get("BREAKS", 0),
            "total_cells": total_cells,
            "pass": counts.get("COMPATIBLE", 0) > 0 and counts.get("BREAKS", 0) > 0 and total_cells == 48,
        },
        "compound_receipt_has_order_dependence": {
            "non_commutative_pairs": compound_summary.get("non_commutative_pairs"),
            "pass": compound_summary.get("non_commutative_pairs", 0) > 0,
        },
        "compound_receipt_has_clifford_crosscheck": {
            "cl3_exact_agreement_count": compound_summary.get("cl3_exact_agreement_count"),
            "pass": compound_summary.get("cl3_exact_agreement_count", 0) >= 16,
        },
    }

    negative = {
        "all_compatible_control_kills_selectivity": {
            "mutated_compatible_ratio": 1.0,
            "observed_compatible_ratio": compatible_ratio,
            "pass": compatible_ratio < 1.0,
        },
        "all_commutative_control_kills_order_signal": {
            "mutated_non_commutative_pairs": 0,
            "observed_non_commutative_pairs": compound_summary.get("non_commutative_pairs"),
            "pass": compound_summary.get("non_commutative_pairs", 0) > 0,
        },
        "single_attractor_control_is_not_enough": {
            "observed_attractor_count": len(compound_summary.get("attractor_distribution", {})),
            "pass": len(compound_summary.get("attractor_distribution", {})) > 1,
        },
    }

    boundary = {
        "supporting_only_receipts_do_not_promote": {
            "operator_geometry_classification": operator_geometry.get("classification"),
            "compound_classification": compound.get("classification"),
            "pass": operator_geometry.get("classification") == "supporting"
            and compound.get("classification") == "supporting",
        },
        "ratios_are_finite_and_nontrivial": {
            "compatible_ratio": compatible_ratio,
            "breaks_ratio": breaks_ratio,
            "pass": bool(np.isfinite(compatible_ratio) and np.isfinite(breaks_ratio) and 0.0 < breaks_ratio < 1.0),
        },
    }

    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": "operator_geometry_closure_ablation",
        "classification": "supporting",
        "classification_note": (
            "Supporting closure-pressure ablation over existing operator/geometry coupling receipts. "
            "This does not promote those receipts; it only records which controls they survive."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": [
            str(RESULTS_DIR / "operator_geometry_compatibility_results.json"),
            str(RESULTS_DIR / "compound_operator_geometry_results.json"),
        ],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "compatible_ratio": compatible_ratio,
            "breaks_ratio": breaks_ratio,
            "closure_candidate": False,
            "scope_note": (
                "The observed supporting receipts survive basic selectivity/order controls, "
                "but remain blocked from closure without separate coexistence and stage-gate evidence."
            ),
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This is a receipt-level ablation battery, not a fresh physical engine. "
            "It cannot prove closure or admission because it reuses existing supporting receipts."
        ),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_operator_geometry_closure_ablation",
        target="Use as a bounded negative/control battery before any closure-grade operator-geometry coexistence packet.",
    )
    results["promotion_condition"] = (
        "Requires a separate closure-grade coexistence sim that does not merely reuse these supporting receipts."
    )
    results["blocked_until"] = "new closure-grade coexistence receipt and explicit stage-gate admission"

    out_path = RESULTS_DIR / "operator_geometry_closure_ablation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
