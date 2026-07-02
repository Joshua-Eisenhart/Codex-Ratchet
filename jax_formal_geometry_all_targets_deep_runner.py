#!/usr/bin/env python3
"""Run every JAX native geometry formal-scout target independently.

This controller runner is intentionally fenced:
- JAX lane only; it does not execute Julia or PyTorch.
- Each geometry target is run in its own Python subprocess so a stuck target
  cannot stall the whole audit.
- Green results remain formal-scout evidence only and do not promote layer,
  G-structure, nesting, flux, Axis0, FEP, physics, or final-manifold claims.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


RESULT_PATH = pathlib.Path("jax_formal_geometry_all_targets_deep_runner_results.json")
ENGINE_DIR = pathlib.Path("system_v5/ops/formal_scouts")
ENGINE_RESULTS = ENGINE_DIR / "results"

TARGETS = [
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

PRIORITY_REHYDRATE_TARGETS = {
    "s3_spinor_carrier",
    "u1_hopf_principal_bundle",
    "so3_orientation_frame_reduction",
    "pin3_spin3_chirality_split",
    "seiberg_witten_8d",
    "contact_sasakian_s3",
    "higher_hopf_s7_to_s4",
}

EXPECTED_SCALES = [8, 16, 32, 64, 128]
PER_TARGET_TIMEOUT_SECONDS = int(os.environ.get("JAX_GEOMETRY_TARGET_TIMEOUT_SECONDS", "240"))
PARALLELISM = max(1, int(os.environ.get("JAX_GEOMETRY_TARGET_PARALLELISM", "4")))
BLOCKED_CONSUMERS = [
    "layer_embedding",
    "stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics/gravity",
    "physics_gravity",
    "final_manifold_admission",
]


def _json_load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tail_text(value: Any, limit: int = 1200) -> str:
    """TimeoutExpired may carry bytes even when subprocess.run used text=True."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-limit:]
    return str(value)[-limit:]


def _run_target(target: str) -> dict[str, Any]:
    started = time.time()
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(ENGINE_DIR)!r}); "
        "import jax_native_geometry_engine as engine; "
        f"engine.main({target!r})"
    )
    env = os.environ.copy()
    env.update(
        {
            "JAX_ENABLE_X64": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "MPLCONFIGDIR": "/tmp/codex-mpl",
            "NUMBA_CACHE_DIR": "/tmp/codex-numba",
        }
    )
    result_path = ENGINE_RESULTS / f"jax_native_geometry_{target}_probe_results.json"
    row: dict[str, Any] = {
        "target": target,
        "priority_rehydrate": target in PRIORITY_REHYDRATE_TARGETS,
        "result_path": str(result_path),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            text=True,
            capture_output=True,
            timeout=PER_TARGET_TIMEOUT_SECONDS,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        row.update(
            {
                "pass": False,
                "status": "timeout",
                "elapsed_seconds": round(time.time() - started, 6),
                "stdout_tail": _tail_text(exc.stdout),
                "stderr_tail": _tail_text(exc.stderr),
                "failures": ["target_timeout"],
            }
        )
        return row

    row.update(
        {
            "exit_code": proc.returncode,
            "elapsed_seconds": round(time.time() - started, 6),
            "stdout_tail": proc.stdout[-1200:],
            "stderr_tail": proc.stderr[-1200:],
        }
    )
    if proc.returncode != 0:
        row.update({"pass": False, "status": "nonzero_exit", "failures": ["target_nonzero_exit"]})
        return row
    if not result_path.exists():
        row.update({"pass": False, "status": "missing_result", "failures": ["missing_result_json"]})
        return row

    try:
        data = _json_load(result_path)
    except Exception as exc:  # noqa: BLE001 - fail closed in receipt audit.
        row.update(
            {
                "pass": False,
                "status": "unreadable_result",
                "failures": [f"unreadable_result:{type(exc).__name__}"],
            }
        )
        return row

    failures: list[str] = []
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
    scale_results = data.get("scale_results")
    if not isinstance(scale_results, list) or len(scale_results) != len(EXPECTED_SCALES):
        failures.append("scale_results_missing_or_wrong_count")
    if data.get("ran_julia") is True:
        failures.append("ran_julia_true")
    if data.get("ran_pytorch") is True:
        failures.append("ran_pytorch_true")
    boundary = data.get("boundary", {})
    blocked = boundary.get("downstream_consumers_locked", {}).get("blocked_consumers", [])
    for consumer in BLOCKED_CONSUMERS:
        if consumer not in blocked:
            failures.append(f"blocked_consumer_missing:{consumer}")
    row.update(
        {
            "pass": not failures,
            "status": "ok" if not failures else "receipt_failed",
            "failures": failures,
            "all_pass": data.get("all_pass"),
            "classification": data.get("classification"),
            "promotion_allowed": data.get("promotion_allowed"),
            "backend": data.get("backend"),
            "scales": data.get("scales"),
            "scale_result_count": len(scale_results) if isinstance(scale_results, list) else None,
            "max_scale_attempted": data.get("max_scale_attempted"),
            "claim_ceiling": data.get("claim_ceiling"),
            "finite_map": data.get("finite_map"),
            "min_order_gap": data.get("summary", {}).get("min_order_gap"),
            "min_scrambled_control_delta": data.get("summary", {}).get("min_scrambled_control_delta"),
            "max_target_invariant_residual": data.get("summary", {}).get("max_target_invariant_residual"),
            "min_negative_control_signal_delta": data.get("summary", {}).get("min_negative_control_signal_delta"),
            "target_negative_controls_all_pass": data.get("known_value_checks", {}).get("all_target_negative_controls_fail_claim"),
            "result_elapsed_seconds": data.get("summary", {}).get("elapsed_seconds"),
        }
    )
    return row


def main() -> int:
    started = time.time()
    rows_by_target: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=PARALLELISM) as pool:
        futures = {pool.submit(_run_target, target): target for target in TARGETS}
        for future in as_completed(futures):
            target = futures[future]
            try:
                rows_by_target[target] = future.result()
            except Exception as exc:  # noqa: BLE001 - controller runner fails closed per target.
                rows_by_target[target] = {
                    "target": target,
                    "priority_rehydrate": target in PRIORITY_REHYDRATE_TARGETS,
                    "pass": False,
                    "status": "runner_exception",
                    "failures": [f"runner_exception:{type(exc).__name__}"],
                    "exception_message": str(exc)[:1200],
                    "result_path": str(ENGINE_RESULTS / f"jax_native_geometry_{target}_probe_results.json"),
                }
    rows = [rows_by_target[target] for target in TARGETS]
    failed = [row for row in rows if not row.get("pass")]
    priority_failed = [row for row in rows if row["priority_rehydrate"] and not row.get("pass")]
    receipt = {
        "name": "jax_formal_geometry_all_targets_deep_runner",
        "classification": "diagnostic_jax_formal_geometry_deep_runner",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_boundary": (
            "Runs every JAX native geometry formal-scout target independently. "
            "This is diagnostic/receipt hydration only; it does not admit a layer, "
            "choose an official G-structure, open nesting, or unlock flux/Axis0/FEP/physics."
        ),
        "blocked_consumers": BLOCKED_CONSUMERS,
        "engine_path": str(ENGINE_DIR / "jax_native_geometry_engine.py"),
        "result_dir": str(ENGINE_RESULTS),
        "expected_scales": EXPECTED_SCALES,
        "target_timeout_seconds": PER_TARGET_TIMEOUT_SECONDS,
        "target_parallelism": PARALLELISM,
        "target_count": len(TARGETS),
        "priority_rehydrate_targets": sorted(PRIORITY_REHYDRATE_TARGETS),
        "passed_targets": [row["target"] for row in rows if row.get("pass")],
        "failed_targets": [row["target"] for row in failed],
        "priority_rehydrate_failed_targets": [row["target"] for row in priority_failed],
        "AUDIT_PASS": not failed,
        "all_target_rows": rows,
        "summary": {
            "target_count": len(TARGETS),
            "passed": len(rows) - len(failed),
            "failed": len(failed),
            "priority_rehydrate_passed": len(PRIORITY_REHYDRATE_TARGETS) - len(priority_failed),
            "priority_rehydrate_failed": len(priority_failed),
            "elapsed_seconds": round(time.time() - started, 6),
        },
    }
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "JAX_FORMAL_GEOMETRY_DEEP_RUN "
        f"pass={receipt['AUDIT_PASS']} targets={len(TARGETS)} "
        f"passed={receipt['summary']['passed']} failed={receipt['summary']['failed']} "
        f"priority_rehydrated={receipt['summary']['priority_rehydrate_passed']}/{len(PRIORITY_REHYDRATE_TARGETS)}"
    )
    print(f"receipt={RESULT_PATH}")
    return 0 if receipt["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
