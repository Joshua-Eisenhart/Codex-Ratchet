#!/usr/bin/env python3
"""Receipt the partial hydrated JAX formal-scout refresh.

This controller audit does not run Julia, does not import PyTorch, and does not
promote formal scouts. It records which JAX formal-scout probes were actually
fresh/hydrated in this session and which surfaces are blocked by dataless files
or stalled reruns.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any


OUT = Path("jax_formal_scout_hydrated_geometry_refresh_results.json")
DEEP_GEOMETRY_RUNNER = Path("jax_formal_geometry_all_targets_deep_runner_results.json")
BLOCKED_OUT = Path(
    "system_v5/ops/wizard_admissions/"
    "blocked_jax_formal_scout_dataless_and_stalled_refresh_20260602T082420Z.json"
)

FORMAL_SCOUT_DIR = Path("system_v5/ops/formal_scouts")
RESULT_DIR = FORMAL_SCOUT_DIR / "results"
GEOMETRY_TARGETS = [
    "s3_spinor_carrier",
    "s2_hopf_base_surface",
    "hopf_fibration_s3_to_s2",
    "nested_hopf_tori",
    "clifford_torus_t2_in_s3",
    "twistor_incidence_spinor_geometry",
    "u1_hopf_principal_bundle",
    "su2_spin3_unit_quaternion_double_cover",
    "so3_orientation_frame_reduction",
    "pin3_spin3_chirality_split",
    "clifford_geometries_cl3_cl6",
    "symplectic_structure",
    "almost_complex_structure",
    "spin_c_structure",
    "su3_calabi_yau_structure",
    "g2_structure",
    "spin7_structure",
    "seiberg_witten_8d",
    "dirac_monopole_u1",
    "spectral_triple",
    "finite_cell_complex_boundary",
    "contact_sasakian_s3",
    "cp1_fubini_study",
    "higher_hopf_s7_to_s4",
]
EXPECTED_SCALES = [8, 16, 32, 64, 128]

ATTEMPTED = {
    "g2_structure": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_geometry_g2_structure_probe.py",
        "result": RESULT_DIR / "jax_native_geometry_g2_structure_probe_results.json",
        "attempt_status": "completed_fresh_stdout",
    },
    "higher_hopf_s7_to_s4": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_geometry_higher_hopf_s7_to_s4_probe.py",
        "result": RESULT_DIR / "jax_native_geometry_higher_hopf_s7_to_s4_probe_results.json",
        "attempt_status": "stalled_killed",
        "killed_pid": 51355,
    },
    "hopf_fibration_s3_to_s2": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_geometry_hopf_fibration_s3_to_s2_probe.py",
        "result": RESULT_DIR / "jax_native_geometry_hopf_fibration_s3_to_s2_probe_results.json",
        "attempt_status": "completed_fresh_result_no_stdout_capture",
    },
    "spin7_structure": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_geometry_spin7_structure_probe.py",
        "result": RESULT_DIR / "jax_native_geometry_spin7_structure_probe_results.json",
        "attempt_status": "completed_fresh_result_no_stdout_capture",
    },
    "u1_hopf_principal_bundle": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_geometry_u1_hopf_principal_bundle_probe.py",
        "result": RESULT_DIR / "jax_native_geometry_u1_hopf_principal_bundle_probe_results.json",
        "attempt_status": "stalled_killed",
        "killed_pid": 51378,
    },
    "l0_response_effect_path_quotient": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_l0_response_effect_path_quotient_layer_probe.py",
        "result": RESULT_DIR / "jax_native_l0_response_effect_path_quotient_layer_probe_results.json",
        "attempt_status": "stalled_killed",
        "killed_pid": 51342,
    },
    "l1_boundary_environment": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_l1_boundary_environment_layer_probe.py",
        "result": RESULT_DIR / "jax_native_l1_boundary_environment_layer_probe_results.json",
        "attempt_status": "stalled_killed",
        "killed_pid": 51396,
    },
    "l3_quaternion_clifford_orientation": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_l3_quaternion_clifford_orientation_layer_probe.py",
        "result": RESULT_DIR / "jax_native_l3_quaternion_clifford_orientation_layer_probe_results.json",
        "attempt_status": "completed_fresh_stdout",
    },
    "l5_operator_substage_cell": {
        "script": FORMAL_SCOUT_DIR / "sim_jax_native_l5_operator_substage_cell_layer_probe.py",
        "result": RESULT_DIR / "jax_native_l5_operator_substage_cell_layer_probe_results.json",
        "attempt_status": "stalled_killed",
        "killed_pid": 51402,
    },
}

FRESH_AFTER = dt.datetime(2026, 6, 2, 1, 18, 0)


def apfs_flags(path: Path) -> str:
    if not path.exists():
        return "missing"
    proc = subprocess.run(
        ["stat", "-f", "%Sf", str(path)],
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    return dt.datetime.fromtimestamp(path.stat().st_mtime) >= FRESH_AFTER


def load_json_if_hydrated(path: Path) -> dict[str, Any] | None:
    if not path.exists() or "dataless" in apfs_flags(path):
        return None
    return json.loads(path.read_text())


def pass_field(data: dict[str, Any] | None) -> bool | None:
    if data is None:
        return None
    if "AUDIT_PASS" in data:
        return bool(data["AUDIT_PASS"])
    if "all_pass" in data:
        return bool(data["all_pass"])
    return None


def attempted_row(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    script = spec["script"]
    result = spec["result"]
    script_flags = apfs_flags(script)
    result_flags = apfs_flags(result)
    data = load_json_if_hydrated(result)
    row_pass = pass_field(data)
    fresh = is_fresh(result)
    if "dataless" in script_flags:
        status = "blocked_dataless_script"
    elif "dataless" in result_flags:
        status = "blocked_dataless_result_after_attempt"
    elif spec["attempt_status"].startswith("stalled"):
        status = "attempt_stalled_killed"
    elif fresh and row_pass is True:
        status = "fresh_green"
    elif row_pass is True:
        status = "stale_green"
    else:
        status = "red_or_unreadable"
    return {
        "name": name,
        "script": str(script),
        "script_flags": script_flags,
        "result": str(result),
        "result_flags": result_flags,
        "result_mtime": mtime_iso(result),
        "fresh_after": FRESH_AFTER.isoformat(),
        "fresh_this_wave": fresh,
        "attempt_status": spec["attempt_status"],
        "status": status,
        "pass": row_pass,
        "classification": None if data is None else data.get("classification"),
        "promotion_allowed": None if data is None else data.get("promotion_allowed"),
        "claim_ceiling": None if data is None else data.get("claim_ceiling"),
        "killed_pid": spec.get("killed_pid"),
    }


def inventory_source_scripts() -> list[dict[str, Any]]:
    scripts = sorted(FORMAL_SCOUT_DIR.glob("sim_jax_native_geometry_*_probe.py"))
    scripts += sorted(FORMAL_SCOUT_DIR.glob("sim_jax_native_l*_probe.py"))
    rows = []
    for path in scripts:
        flags = apfs_flags(path)
        rows.append({"path": str(path), "flags": flags, "blocked_dataless": "dataless" in flags})
    return rows


def main() -> int:
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    rows = [attempted_row(name, spec) for name, spec in ATTEMPTED.items()]
    inventory = inventory_source_scripts()
    deep_runner = load_json_if_hydrated(DEEP_GEOMETRY_RUNNER)
    geometry_rows = []
    for target in GEOMETRY_TARGETS:
        path = RESULT_DIR / f"jax_native_geometry_{target}_probe_results.json"
        data = load_json_if_hydrated(path)
        failures = []
        if data is None:
            failures.append("missing_or_unreadable")
        else:
            if data.get("all_pass") is not True:
                failures.append("all_pass_not_true")
            if data.get("classification") != "formal_scout":
                failures.append("classification_not_formal_scout")
            if data.get("promotion_allowed") is not False:
                failures.append("promotion_allowed_not_false")
            if data.get("backend") != "jax_native_x64":
                failures.append("backend_not_jax_native_x64")
            if data.get("scales") != EXPECTED_SCALES:
                failures.append("scales_not_full_expected_ladder")
            if len(data.get("scale_results", [])) != len(EXPECTED_SCALES):
                failures.append("scale_results_missing_or_wrong_count")
        geometry_rows.append(
            {
                "target": target,
                "path": str(path),
                "pass": not failures,
                "failures": failures,
                "all_pass": None if data is None else data.get("all_pass"),
                "classification": None if data is None else data.get("classification"),
                "promotion_allowed": None if data is None else data.get("promotion_allowed"),
                "backend": None if data is None else data.get("backend"),
                "scales": None if data is None else data.get("scales"),
                "mtime": mtime_iso(path),
            }
        )
    geometry_refresh_complete = (
        deep_runner is not None
        and deep_runner.get("AUDIT_PASS") is True
        and deep_runner.get("target_count") == len(GEOMETRY_TARGETS)
        and all(row["pass"] for row in geometry_rows)
    )
    fresh_green = [row["name"] for row in rows if row["status"] == "fresh_green"]
    stalled_or_blocked = [
        row["name"]
        for row in rows
        if row["status"] in {"attempt_stalled_killed", "blocked_dataless_result_after_attempt", "blocked_dataless_script"}
    ]
    dataless_scripts = [row["path"] for row in inventory if row["blocked_dataless"]]
    checks = {
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "formal_geometry_targets_hydrated": geometry_refresh_complete,
        "fresh_green_rows_present": len(fresh_green) >= 1,
        "broad_layer_refresh_incomplete_fenced": len(stalled_or_blocked) > 0 or len(dataless_scripts) > 0,
        "promotion_disabled": True,
    }
    receipt = {
        "name": "jax_formal_scout_hydrated_geometry_refresh",
        "generated_at": generated_at,
        "classification": "partial_formal_scout_refresh_receipt",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_ceiling": (
            "JAX formal geometry target refresh only. The 24 geometry target receipts are standalone scouts. "
            "Dataless and stalled layer/source rows still block any broad formal-scout completion, official "
            "G-structure selection, layer completion, stacking readiness, flux, Axis0, FEP, "
            "physics, or final manifold claim."
        ),
        "deep_geometry_runner": None if deep_runner is None else {
            "path": str(DEEP_GEOMETRY_RUNNER),
            "AUDIT_PASS": deep_runner.get("AUDIT_PASS"),
            "summary": deep_runner.get("summary"),
            "target_parallelism": deep_runner.get("target_parallelism"),
        },
        "geometry_targets": {
            "count": len(GEOMETRY_TARGETS),
            "hydrated_full_scale": sum(1 for row in geometry_rows if row["pass"]),
            "rows": geometry_rows,
        },
        "attempted_rows": rows,
        "fresh_green_rows": fresh_green,
        "stalled_or_blocked_attempts": stalled_or_blocked,
        "source_inventory": {
            "total_scripts": len(inventory),
            "hydrated_scripts": len(inventory) - len(dataless_scripts),
            "dataless_scripts": len(dataless_scripts),
            "dataless_script_paths": dataless_scripts,
        },
        "checks": checks,
        "FORMAL_GEOMETRY_REFRESH_COMPLETE": geometry_refresh_complete,
        "FORMAL_SCOUT_REFRESH_COMPLETE": False,
        "RECEIPT_PASS": all(checks.values()),
        "AUDIT_PASS": bool(geometry_refresh_complete and checks["no_julia_execution"] and checks["no_pytorch_execution"] and checks["promotion_disabled"]),
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
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    blocked = {
        "kind": "blocked_reason",
        "created_at": generated_at,
        "status": "blocked_broad_layer_refresh_geometry_targets_complete",
        "scope": "JAX formal_scouts broad geometry/layer refresh",
        "reason": (
            "The 24 JAX geometry targets have been hydrated by the deep runner, but the "
            "older broad runner/layer source refresh still includes APFS dataless or "
            "previously stalled layer/source rows. Geometry target receipts may be cited "
            "as standalone formal scouts; broad layer/formal-scout completion remains blocked."
        ),
        "receipt_path": str(OUT),
        "fresh_green_rows": fresh_green,
        "stalled_or_blocked_attempts": stalled_or_blocked,
        "dataless_script_count": len(dataless_scripts),
        "next_admissible_step": "Run or repair layer/source formal scouts separately if broad formal-scout completion is needed; do not promote from the geometry target refresh.",
        "ran_julia": False,
        "ran_pytorch": False,
        "blocked_consumers": receipt["blocked_consumers"],
    }
    BLOCKED_OUT.parent.mkdir(parents=True, exist_ok=True)
    BLOCKED_OUT.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n")

    print(
        "jax_formal_scout_hydrated_geometry_refresh "
        f"geometry_hydrated={sum(1 for row in geometry_rows if row['pass'])}/{len(GEOMETRY_TARGETS)} "
        f"fresh_green={len(fresh_green)} stalled_or_blocked={len(stalled_or_blocked)} "
        f"dataless_scripts={len(dataless_scripts)} RECEIPT_PASS={receipt['RECEIPT_PASS']} "
        f"AUDIT_PASS={receipt['AUDIT_PASS']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
