#!/usr/bin/env python3
"""External oracle for the bottom-up nested Hopf JAX receipt.

This script deliberately does not trust the receipt's AUDIT_PASS flag. It reads
the metric fields and rejects corrupted copies that break the finite placement,
ratchet, noncommutation, or boundary claims.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


SOURCE = Path("jax_nested_hopf_bottom_up_branch_prune_audit_results.json")
OUT = Path("jax_nested_hopf_bottom_up_external_oracle_results.json")
N_BRANCH = 4096
ALL_16 = list(range(1, 17))


def validate(d: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []

    def need(name: str, ok: bool) -> None:
        if not ok:
            failures.append(name)

    need("receipt_boundary", d.get("ran_julia") is False and d.get("ran_pytorch") is False and d.get("promotion_allowed") is False)

    local = d.get("local_16_lindblad", {})
    lm = local.get("metrics", {})
    need("local_trace", lm.get("max_trace_error", 1.0) < 1.0e-6)
    need("local_psd", lm.get("min_eigenvalue", -1.0) > -1.0e-7)
    need("local_bloch_finite", lm.get("max_bloch_norm", 2.0) <= 1.0 + 1.0e-6)
    need("pit_sink_south", lm.get("pit_final_bloch", [0, 0, 0])[2] < -0.95)
    need("source_sink_north", lm.get("source_final_bloch", [0, 0, 0])[2] > 0.95)

    area = d.get("leaf_area_ratchet", {})
    areas = area.get("areas", [])
    need("finite_leaf_count", len(areas) == 9)
    if areas:
        need("clifford_max_leaf", max(range(len(areas)), key=lambda i: areas[i]) == area.get("max_leaf_zero_based") == 4)
        need("area_decreases_left_from_clifford", all(areas[i] < areas[i + 1] for i in range(4)))
        need("area_decreases_right_from_clifford", all(areas[i] > areas[i + 1] for i in range(4, 8)))

    order = d.get("order_sensitivity", {}).get("metrics", {})
    need("n01_order_gap", order.get("pit_then_hill_vs_hill_then_pit_gap", 0.0) > 1.0e-4)
    need("order_control_zero", order.get("same_generator_order_control_gap", 1.0) < 1.0e-12)

    path_rows = d.get("path_geometry", {}).get("rows", {})
    need("path_geometry_present", set(path_rows.keys()) == {"L", "R"})
    for sheet, row in path_rows.items():
        need(f"{sheet}_fiber_density_invariant", row.get("fiber_density_delta", 1.0) < 1.0e-10)
        need(f"{sheet}_fiber_vertical_nonzero", row.get("fiber_vertical_connection_abs", 0.0) > 0.9)
        need(f"{sheet}_base_density_moves", row.get("base_density_delta", 0.0) > 1.0e-2)
        need(f"{sheet}_base_horizontal", row.get("base_horizontal_residual", 1.0) < 1.0e-12)

    runs = d.get("nested_runs", {})
    genuine = runs.get("genuine", {})
    commuting = runs.get("commuting_control", {})
    ratchet_off = runs.get("ratchet_off_control", {})
    expansive = runs.get("expansive_prune_control", {})
    flat = runs.get("flat_area_control", {})

    for name, row in runs.items():
        need(f"bookkeeping_{name}", row.get("survivors") == N_BRANCH - row.get("pruned", -1))

    need("genuine_all_16", genuine.get("populated_placements") == ALL_16)
    need("genuine_not_pruned", genuine.get("pruned") == 0)
    need("genuine_clifford_concentration", genuine.get("central_leaf_fraction", 0.0) > 0.70)
    need("n01_off_collapses", commuting.get("populated_placements") == [1])
    need("n01_off_not_pruned", commuting.get("pruned") == 0)
    need("ratchet_off_differs", ratchet_off.get("leaf_histogram") != genuine.get("leaf_histogram"))
    need("ratchet_off_less_central", ratchet_off.get("central_leaf_fraction", 1.0) < genuine.get("central_leaf_fraction", 0.0) - 0.20)
    need("flat_area_differs", flat.get("leaf_histogram") != genuine.get("leaf_histogram"))
    need("flat_area_less_central", flat.get("central_leaf_fraction", 1.0) < genuine.get("central_leaf_fraction", 0.0) - 0.20)
    need("f01_prune_fires", expansive.get("pruned", 0) > 0 and expansive.get("survivors") == 0)

    need("cl3_jaxga", d.get("cl3_jaxga", {}).get("pass") is True)
    need("dlpack", d.get("dlpack_snapshot", {}).get("pass") is True)
    need("riemannax_status_recorded", d.get("riemannax", {}).get("status") in {"available", "blocked_missing_package"})

    return not failures, failures


def main() -> int:
    original = json.loads(SOURCE.read_text())
    original_ok, original_failures = validate(original)

    corrupt_basin = copy.deepcopy(original)
    corrupt_basin["nested_runs"]["genuine"]["populated_placements"] = [1]
    corrupt_basin_ok, corrupt_basin_failures = validate(corrupt_basin)

    corrupt_order = copy.deepcopy(original)
    corrupt_order["order_sensitivity"]["metrics"]["pit_then_hill_vs_hill_then_pit_gap"] = 0.0
    corrupt_order_ok, corrupt_order_failures = validate(corrupt_order)

    corrupt_boundary = copy.deepcopy(original)
    corrupt_boundary["ran_julia"] = True
    corrupt_boundary["promotion_allowed"] = True
    corrupt_boundary_ok, corrupt_boundary_failures = validate(corrupt_boundary)

    audit_pass = original_ok and not corrupt_basin_ok and not corrupt_order_ok and not corrupt_boundary_ok
    receipt = {
        "name": "jax_nested_hopf_bottom_up_external_oracle",
        "classification": "external_negative_oracle",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "source_receipt": str(SOURCE),
        "accept_original": original_ok,
        "original_failures": original_failures,
        "reject_corrupt_basin": not corrupt_basin_ok,
        "corrupt_basin_failures": corrupt_basin_failures,
        "reject_corrupt_order": not corrupt_order_ok,
        "corrupt_order_failures": corrupt_order_failures,
        "reject_corrupt_boundary": not corrupt_boundary_ok,
        "corrupt_boundary_failures": corrupt_boundary_failures,
        "AUDIT_PASS": audit_pass,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "nested_hopf_external_oracle "
        f"accept_original={original_ok} reject_basin={not corrupt_basin_ok} "
        f"reject_order={not corrupt_order_ok} reject_boundary={not corrupt_boundary_ok} "
        f"AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
