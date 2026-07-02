#!/usr/bin/env python3
"""Aggregate fresh foundation/reference JAX coverage after L6/L12 row repair.

This is a receipt combiner only. It does not run Julia, does not import
PyTorch, and does not promote any manifold, layer, flux, or Axis0 claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUT = Path("jax_foundation_reference_coverage_refresh_results.json")

FILES = {
    "julia_reference_runner": Path("jax_julia_reference_geometric_constraint_layer_runner_results.json"),
    "independent_layer_suite": Path("jax_manifold_layer_independent_suite_results.json"),
    "geometric_engine_suite": Path("jax_geometric_evolution_engine_layer_suite_results.json"),
    "entropy_geometry_stress": Path("jax_qit_entropy_geometry_separation_stress_results.json"),
    "geometry_is_information_audit": Path("system_v5/julia_carrier/jax_geometry_is_information_audit_results.json"),
    "coverage_gate": Path("jax_independent_layer_geometry_coverage_gate_results.json"),
    "nesting_order_gate": Path("jax_nested_hopf_nesting_order_gate_results.json"),
    "stack_status_oracle": Path("jax_nested_hopf_stack_status_oracle_results.json"),
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def pass_field(d: dict[str, Any]) -> bool:
    if "AUDIT_PASS" in d:
        return bool(d["AUDIT_PASS"])
    if "all_pass" in d:
        return bool(d["all_pass"])
    if "coverage_closed" in d:
        return bool(d["coverage_closed"])
    return False


def main() -> int:
    loaded = {name: load(path) for name, path in FILES.items()}
    ref = loaded["julia_reference_runner"]
    coverage = loaded["coverage_gate"]
    nesting = loaded["nesting_order_gate"]
    oracle = loaded["stack_status_oracle"]
    row_summaries = {
        name: {
            "path": str(FILES[name]),
            "pass": pass_field(data),
            "classification": data.get("classification"),
            "promotion_allowed": data.get("promotion_allowed"),
            "ran_julia": data.get("ran_julia"),
            "ran_pytorch": data.get("ran_pytorch"),
        }
        for name, data in loaded.items()
    }
    ref_row_names = {row.get("julia_reference_result") for row in ref.get("rows", [])}
    ref_rows_complete = (
        len(ref.get("rows", [])) == len(ref.get("independent_reference_layers", []))
        and ref.get("missing_independent_jax_rows") == []
        and ref.get("red_independent_reference_rows_unresolved", []) == []
    )
    l6_l12_closed = {
        "L6_layer_results.json": "L6_layer_results.json" in ref_row_names,
        "L12_layer_results.json": "L12_layer_results.json" in ref_row_names,
    }
    checks = {
        "julia_reference_runner_pass": ref.get("AUDIT_PASS") is True,
        "julia_reference_rows_complete": ref_rows_complete,
        "julia_reference_missing_empty": ref.get("missing_independent_jax_rows") == [],
        "l6_l12_reference_rows_closed": all(l6_l12_closed.values()),
        "coverage_gate_closed": coverage.get("coverage_closed") is True,
        "nesting_order_gate_closed": nesting.get("nesting_order_gate_closed") is True and nesting.get("AUDIT_PASS") is True,
        "stack_status_oracle_pass": oracle.get("AUDIT_PASS") is True,
        "flux_still_blocked": oracle.get("flux_allowed") is False,
        "axis0_still_blocked": oracle.get("axis0_allowed") is False,
        "all_rows_promotion_blocked": all(data.get("promotion_allowed") is not True for data in loaded.values()),
        "no_julia_execution": all(data.get("ran_julia") is not True for data in loaded.values()),
        "no_pytorch_execution": all(data.get("ran_pytorch") is not True for data in loaded.values()),
    }
    receipt = {
        "name": "jax_foundation_reference_coverage_refresh",
        "classification": "diagnostic_coverage_refresh",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_ceiling": (
            "Fresh JAX foundation/reference coverage receipt after adding L6 and L12 "
            "Julia-reference JAX rows. This is not layer completion, stacking readiness, "
            "flux/Axis0/FEP/physics progress, official G-structure selection, or final admission."
        ),
        "checks": checks,
        "row_summaries": row_summaries,
        "l6_l12_closed": l6_l12_closed,
        "reference_runner": {
            "path": str(FILES["julia_reference_runner"]),
            "independent_rows": len(ref.get("rows", [])),
            "independent_reference_layers": len(ref.get("independent_reference_layers", [])),
            "future_phase_reference_layers": ref.get("future_phase_reference_layers", []),
            "red_independent_reference_rows": ref.get("red_independent_reference_rows", []),
            "red_independent_reference_rows_unresolved": ref.get("red_independent_reference_rows_unresolved", []),
        },
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "layer_stacking_readiness",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "AUDIT_PASS": all(checks.values()),
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_foundation_reference_coverage_refresh "
        f"ref_rows={len(ref.get('rows', []))}/{len(ref.get('independent_reference_layers', []))} "
        f"coverage={coverage.get('coverage_closed')} "
        f"nesting={nesting.get('nesting_order_gate_closed')} "
        f"flux_allowed={oracle.get('flux_allowed')} "
        f"axis0_allowed={oracle.get('axis0_allowed')} "
        f"AUDIT_PASS={receipt['AUDIT_PASS']}"
    )
    return 0 if receipt["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
