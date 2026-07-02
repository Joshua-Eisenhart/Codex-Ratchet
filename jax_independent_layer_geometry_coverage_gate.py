#!/usr/bin/env python3
"""Coverage gate for independent JAX layer/geometry sims before nesting order.

Read-only with respect to Julia and PyTorch: this script only reads receipts and
writes its own gate receipt. It does not execute Julia, does not execute
PyTorch, and does not promote layer completion.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import subprocess
from pathlib import Path
from typing import Any


OUT = Path("jax_independent_layer_geometry_coverage_gate_results.json")
RESULTS = Path("system_v5/ops/formal_scouts/results")

REFERENCE_RUNNER = Path("jax_julia_reference_geometric_constraint_layer_runner_results.json")
STACK_ORACLE = Path("jax_nested_hopf_stack_status_oracle_results.json")
JAX_SUITE = Path("jax_manifold_layer_independent_suite_results.json")

EXPECTED_INDIVIDUAL_LAYER_RECEIPTS = {
    "L0_response_effect_path_quotient": RESULTS / "jax_native_l0_response_effect_path_quotient_layer_probe_results.json",
    "L1_boundary_environment": RESULTS / "jax_native_l1_boundary_environment_layer_probe_results.json",
    "L2_weyl_spinor_chirality": RESULTS / "jax_native_l2_weyl_spinor_chirality_layer_probe_results.json",
    "L3_quaternion_clifford_orientation": RESULTS / "jax_native_l3_quaternion_clifford_orientation_layer_probe_results.json",
    "L4_terrain_channel_generator": RESULTS / "jax_native_l4_terrain_channel_generator_layer_probe_results.json",
    "L5_operator_substage_cell": RESULTS / "jax_native_l5_operator_substage_cell_layer_probe_results.json",
    "L6_entropy_cut_communication": RESULTS / "jax_native_l6_entropy_cut_communication_layer_probe_results.json",
    "L7_hopf_shell_projection": RESULTS / "jax_native_l7_hopf_shell_projection_layer_probe_results.json",
    "L8_gluing_groupoid": RESULTS / "jax_native_l8_gluing_groupoid_layer_probe_results.json",
}

EXPECTED_SOURCE_BACKED_RECEIPTS = {
    "finite_carrier_probe_path_geometry": RESULTS / "independent_layer_finite_carrier_probe_path_geometry_probe_results.json",
    "finite_spinor_network_carrier": RESULTS / "independent_layer_finite_spinor_network_carrier_probe_results.json",
    "s3_unit_spinor_geometry": RESULTS / "independent_layer_s3_unit_spinor_geometry_probe_results.json",
    "cp1_s2_projective_hopf_base": RESULTS / "independent_layer_cp1_s2_projective_hopf_base_probe_results.json",
    "u1_hopf_fiber": RESULTS / "independent_layer_u1_hopf_fiber_probe_results.json",
    "hopf_connection_holonomy": RESULTS / "independent_layer_hopf_connection_holonomy_probe_results.json",
    "nested_hopf_tori": RESULTS / "independent_layer_nested_hopf_tori_probe_results.json",
    "left_right_weyl_spinor_sheets": RESULTS / "independent_layer_left_right_weyl_spinor_sheets_probe_results.json",
    "chirality_orientation_cover": RESULTS / "independent_layer_chirality_orientation_cover_probe_results.json",
    "clifford_quaternion_rotor_geometry": RESULTS / "independent_layer_clifford_quaternion_rotor_geometry_probe_results.json",
    "local_weyl_dynamical_laws": RESULTS / "independent_layer_local_weyl_dynamical_laws_probe_results.json",
    "local_operator_channel_actions": RESULTS / "independent_layer_local_operator_channel_actions_probe_results.json",
    "patch_gluing_groupoid_compatibility": RESULTS / "independent_layer_patch_gluing_groupoid_compatibility_probe_results.json",
}

WEYL_LAW_RECEIPTS = {
    "left_funnel": RESULTS / "independent_layer_weyl_law_left_funnel_probe_results.json",
    "left_vortex": RESULTS / "independent_layer_weyl_law_left_vortex_probe_results.json",
    "left_pit": RESULTS / "independent_layer_weyl_law_left_pit_probe_results.json",
    "left_hill": RESULTS / "independent_layer_weyl_law_left_hill_probe_results.json",
    "right_cannon": RESULTS / "independent_layer_weyl_law_right_cannon_probe_results.json",
    "right_spiral": RESULTS / "independent_layer_weyl_law_right_spiral_probe_results.json",
    "right_source": RESULTS / "independent_layer_weyl_law_right_source_probe_results.json",
    "right_citadel": RESULTS / "independent_layer_weyl_law_right_citadel_probe_results.json",
}


def _read_json_worker(path: str, queue: mp.Queue) -> None:
    try:
        p = Path(path)
        data = json.loads(p.read_text())
        queue.put({"ok": True, "data": data})
    except Exception as exc:  # noqa: BLE001 - this is a gate, not a library.
        queue.put({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]})


def apfs_flags(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        proc = subprocess.run(
            ["stat", "-f", "%Sf", str(path)],
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception as exc:  # noqa: BLE001 - gate should fail closed.
        return f"flag_error:{type(exc).__name__}"
    return proc.stdout.strip()


def safe_load(path: Path, timeout_s: float = 3.0) -> dict[str, Any]:
    if not path.exists():
        return {"read_status": "missing", "path": str(path)}
    flags = apfs_flags(path)
    if "dataless" in flags:
        return {"read_status": "dataless", "path": str(path), "apfs_flags": flags}
    ctx = mp.get_context("fork")
    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_read_json_worker, args=(str(path), queue))
    proc.start()
    proc.join(timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {"read_status": "timeout", "path": str(path)}
    if queue.empty():
        return {"read_status": "no_result", "path": str(path)}
    payload = queue.get()
    if not payload.get("ok"):
        return {
            "read_status": "malformed",
            "path": str(path),
            "error": payload.get("error"),
            "message": payload.get("message"),
        }
    data = payload["data"]
    return {"read_status": "ok", "path": str(path), "data": data}


def pass_field(data: dict[str, Any]) -> bool:
    if "AUDIT_PASS" in data:
        return bool(data["AUDIT_PASS"])
    if "all_pass" in data:
        return bool(data["all_pass"])
    if "summary" in data and isinstance(data["summary"], dict) and "all_pass" in data["summary"]:
        return bool(data["summary"]["all_pass"])
    return False


def receipt_row(name: str, path: Path, timeout_s: float = 1.0) -> dict[str, Any]:
    loaded = safe_load(path, timeout_s=timeout_s)
    row: dict[str, Any] = {
        "name": name,
        "path": str(path),
        "read_status": loaded["read_status"],
        "apfs_flags": loaded.get("apfs_flags", apfs_flags(path)),
        "present": path.exists(),
    }
    if loaded["read_status"] != "ok":
        row["pass"] = False
        row["promotion_allowed"] = None
        row["classification"] = None
        row["failures"] = [loaded["read_status"]]
        if "error" in loaded:
            row["error"] = loaded["error"]
            row["message"] = loaded.get("message")
        return row
    data = loaded["data"]
    failures: list[str] = []
    if not pass_field(data):
        failures.append("pass_field_false")
    if data.get("promotion_allowed") is not False:
        failures.append("promotion_allowed_not_false")
    row.update(
        {
            "pass": pass_field(data),
            "classification": data.get("classification"),
            "promotion_allowed": data.get("promotion_allowed"),
            "ran_julia": data.get("ran_julia"),
            "ran_pytorch": data.get("ran_pytorch"),
            "all_pass": data.get("all_pass"),
            "AUDIT_PASS": data.get("AUDIT_PASS"),
            "failures": failures,
        }
    )
    return row


def load_required(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"read_status": "missing", "path": str(path), "data": {}}
    flags = apfs_flags(path)
    if "dataless" in flags:
        return {"read_status": "dataless", "path": str(path), "apfs_flags": flags, "data": {}}
    try:
        return {"read_status": "ok", "path": str(path), "data": json.loads(path.read_text())}
    except Exception as exc:  # noqa: BLE001 - gate should fail closed.
        return {"read_status": "malformed", "path": str(path), "error": type(exc).__name__, "message": str(exc)[:500], "data": {}}


def main() -> int:
    reference = load_required(REFERENCE_RUNNER)["data"]
    stack = load_required(STACK_ORACLE)["data"]
    suite = load_required(JAX_SUITE)["data"]

    individual_layer_rows = [receipt_row(name, path, timeout_s=1.0) for name, path in EXPECTED_INDIVIDUAL_LAYER_RECEIPTS.items()]
    source_backed_rows = [receipt_row(name, path, timeout_s=1.0) for name, path in EXPECTED_SOURCE_BACKED_RECEIPTS.items()]
    weyl_law_rows = [receipt_row(name, path, timeout_s=1.0) for name, path in WEYL_LAW_RECEIPTS.items()]
    geometry_paths = sorted(RESULTS.glob("jax_native_geometry_*_probe_results.json"))
    geometry_rows = [receipt_row(path.stem.removeprefix("jax_native_geometry_").removesuffix("_probe_results"), path, timeout_s=0.75) for path in geometry_paths]

    red_reference_rows = reference.get("red_independent_reference_rows", [])
    unresolved_red_reference_rows = reference.get("red_independent_reference_rows_unresolved", red_reference_rows)
    missing_reference_rows = reference.get("missing_independent_jax_rows", reference.get("missing_jax_rows", []))
    future_phase_rows = reference.get("future_phase_reference_layers", [])

    unreadable_individual = [
        row for row in individual_layer_rows + source_backed_rows + weyl_law_rows + geometry_rows
        if row["read_status"] != "ok"
    ]
    failed_individual = [
        row for row in individual_layer_rows + source_backed_rows + weyl_law_rows + geometry_rows
        if row["read_status"] == "ok" and row["failures"]
    ]

    suite_rows = suite.get("layer_results", [])
    checks = {
        "reference_runner_pass": bool(reference.get("AUDIT_PASS")),
        "reference_independent_rows_present": not missing_reference_rows,
        "reference_no_unresolved_red_independent_rows": not unresolved_red_reference_rows,
        "jax_suite_pass": bool(suite.get("AUDIT_PASS")),
        "jax_suite_has_19_rows": len(suite_rows) == 19,
        "individual_receipts_readable": not unreadable_individual,
        "individual_receipts_pass_and_fenced": not failed_individual,
        "coverage_gate_does_not_open_nesting": True,
        "stack_oracle_has_required_rows": stack.get("required_ok") is True,
        "stack_oracle_not_used_as_coverage_dependency": True,
    }

    coverage_closed = all(checks.values())
    receipt = {
        "name": "jax_independent_layer_geometry_coverage_gate",
        "classification": "coverage_gate",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_boundary": (
            "Coverage gate only. It does not admit all layers/geometries, does not open nesting order, "
            "and does not promote flux, Axis0, FEP, physics, or final manifold admission."
        ),
        "active_stage": "independent_layer_and_geometry_sims",
        "coverage_closed": coverage_closed,
        "nesting_order_allowed": False,
        "checks": checks,
        "reference_runner": {
            "path": str(REFERENCE_RUNNER),
            "AUDIT_PASS": reference.get("AUDIT_PASS"),
            "independent_rows": len(reference.get("rows", [])),
            "independent_reference_layers": len(reference.get("independent_reference_layers", [])),
            "missing_independent_jax_rows": missing_reference_rows,
            "red_independent_reference_rows": red_reference_rows,
            "red_independent_reference_rows_unresolved": unresolved_red_reference_rows,
            "red_independent_reference_supersession_receipts": reference.get("red_independent_reference_supersession_receipts", {}),
            "future_phase_reference_layers_blocked": future_phase_rows,
        },
        "suite": {
            "path": str(JAX_SUITE),
            "AUDIT_PASS": suite.get("AUDIT_PASS"),
            "layer_result_count": len(suite_rows),
            "failed_layer_results": [row for row in suite_rows if not row.get("pass")],
        },
        "individual_layer_rows": individual_layer_rows,
        "source_backed_rows": source_backed_rows,
        "weyl_law_rows": weyl_law_rows,
        "geometry_rows": geometry_rows,
        "unreadable_individual_receipts": unreadable_individual,
        "failed_or_unfenced_individual_receipts": failed_individual,
        "downstream_blocked": [
            "nesting_order_search",
            "pairwise_layer_order_tests",
            "noncommutative_finitude_ratchet",
            "basin_hierarchy",
            "flux",
            "xi_phi0",
            "axis0",
            "fep_holodeck",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "next_admissible_repairs": [
            "Repair red independent reference rows or explicitly supersede them with current independent JAX receipts.",
            "Regenerate unreadable/malformed individual JAX/native geometry receipts.",
            "Keep future-phase basin, ratchet, and flux rows blocked until coverage closes.",
        ],
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_independent_layer_geometry_coverage_gate "
        f"coverage_closed={coverage_closed} "
        f"red_refs={len(red_reference_rows)} "
        f"unresolved_red_refs={len(unresolved_red_reference_rows)} "
        f"missing_refs={len(missing_reference_rows)} "
        f"unreadable={len(unreadable_individual)} "
        f"failed_or_unfenced={len(failed_individual)} "
        f"geometry_rows={len(geometry_rows)} "
        f"nesting_order_allowed=False"
    )
    return 0 if coverage_closed else 2


if __name__ == "__main__":
    raise SystemExit(main())
