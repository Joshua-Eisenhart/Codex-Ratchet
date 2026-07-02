#!/usr/bin/env python3
"""Aggregate the fresh non-flux post-nesting JAX diagnostic reruns.

This does not run Julia, does not import PyTorch, and does not promote any row.
It is a controller receipt for the bounded JAX diagnostics that sit below the
blocked flux/Axis0/FEP/physics consumers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUT = Path("jax_post_nesting_nonflux_batch_refresh_results.json")

ROWS = {
    "pairwise_leaf_coupling": Path("jax_nested_hopf_pairwise_leaf_coupling_audit_results.json"),
    "weyl_dirac_radial_coupling": Path("jax_weyl_dirac_coupling_radial_mirror_results.json"),
    "multishell_lindblad_cascade": Path("jax_multishell_lindblad_cascade_mirror_results.json"),
    "multishell_coexistence": Path("jax_multishell_coexistence_mirror_results.json"),
    "emergent_basin_recurrence_prune": Path("jax_emergent_basin_recurrence_prune_mirror_results.json"),
    "noncommutative_finitude_ratchet_basin_hierarchy": Path(
        "jax_noncommutative_finitude_ratchet_basin_hierarchy_results.json"
    ),
    "noncommutative_finitude_ratchet_deepening_falsifier": Path(
        "jax_noncommutative_finitude_ratchet_deepening_falsifier_results.json"
    ),
}

ORACLE = Path("jax_nested_hopf_stack_status_oracle_results.json")
BLOCKED_FLUX_RECEIPT = Path(
    "system_v5/ops/wizard_admissions/"
    "blocked_flux_impedance_dependency_preflight_20260602T080320Z.json"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def pass_field(d: dict[str, Any]) -> bool:
    if "AUDIT_PASS" in d:
        return bool(d["AUDIT_PASS"])
    if "all_pass" in d:
        return bool(d["all_pass"])
    return False


def row_summary(name: str, path: Path) -> dict[str, Any]:
    d = load(path)
    return {
        "name": name,
        "path": str(path),
        "pass": pass_field(d),
        "classification": d.get("classification"),
        "promotion_allowed": d.get("promotion_allowed"),
        "ran_julia": d.get("ran_julia"),
        "ran_pytorch": d.get("ran_pytorch"),
        "blocked_consumers": d.get("blocked_consumers", []),
    }


def main() -> int:
    rows = [row_summary(name, path) for name, path in ROWS.items()]
    oracle = load(ORACLE)
    blocked_flux = load(BLOCKED_FLUX_RECEIPT)
    rows_green = all(
        r["pass"]
        and r["promotion_allowed"] is False
        and r["ran_julia"] is not True
        and r["ran_pytorch"] is not True
        for r in rows
    )
    oracle_flux_row = {
        r["name"]: r for r in oracle.get("downstream_blocked_rows", [])
    }.get("flux_impedance_falsifier", {})
    dependency_open = (
        oracle.get("independent_layer_geometry_coverage_closed") is True
        and oracle.get("nesting_order_gate_closed") is True
    )
    oracle_ok = (
        oracle.get("AUDIT_PASS") is True
        and oracle.get("flux_allowed") is False
        and oracle.get("axis0_allowed") is False
        and oracle_flux_row.get("blocked_reason_receipt_valid") is True
    )
    receipt = {
        "name": "jax_post_nesting_nonflux_batch_refresh",
        "classification": "diagnostic_batch_refresh",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_ceiling": (
            "Fresh local rerun receipt for six non-flux JAX diagnostics only. "
            "No layer completion, no stacking readiness, no flux/Axis0/FEP/physics unlock."
        ),
        "rows": rows,
        "rows_green": rows_green,
        "stack_status_oracle": {
            "path": str(ORACLE),
            "AUDIT_PASS": oracle.get("AUDIT_PASS"),
            "flux_allowed": oracle.get("flux_allowed"),
            "axis0_allowed": oracle.get("axis0_allowed"),
            "independent_layer_geometry_coverage_closed": oracle.get("independent_layer_geometry_coverage_closed"),
            "nesting_order_gate_closed": oracle.get("nesting_order_gate_closed"),
            "dependency_open": dependency_open,
            "flux_blocked_reason_receipt_valid": oracle_flux_row.get("blocked_reason_receipt_valid"),
            "flux_blocked_reason_receipt_path": oracle_flux_row.get("blocked_reason_receipt_path"),
        },
        "blocked_flux_receipt": {
            "path": str(BLOCKED_FLUX_RECEIPT),
            "kind": blocked_flux.get("kind"),
            "status": blocked_flux.get("status"),
            "created_at": blocked_flux.get("created_at"),
        },
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking_readiness",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "AUDIT_PASS": rows_green and oracle_ok and dependency_open,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_post_nesting_nonflux_batch_refresh "
        f"rows_green={rows_green} oracle_ok={oracle_ok} dependency_open={dependency_open} "
        f"AUDIT_PASS={receipt['AUDIT_PASS']}"
    )
    return 0 if receipt["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
