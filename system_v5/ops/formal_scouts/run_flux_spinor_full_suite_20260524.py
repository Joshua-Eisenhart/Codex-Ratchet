#!/usr/bin/env python3
"""Run the bounded flux/spinor full-suite pass.

This is an orchestration receipt, not a science promotion. It reruns the current
admissible flux/spinor/scale/Axis0/Holodeck/IGT/science scout rows, then runs
result validation and static sim-contract lint over the touched rows.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
SUITE_RESULT = RESULT_DIR / "flux_spinor_full_suite_20260524_results.json"
PYTHON = pathlib.Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3")

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "suite_orchestration_control"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Suite orchestration only: reruns and validates bounded flux/spinor/scale/"
    "Axis0/Holodeck/IGT/science formal scouts. A green suite does not admit final "
    "flux, Axis0, Xi, PEPS3D closure, Standard Model, gravity, Yang-Mills, "
    "Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "python_subprocess": {"tried": True, "used": True, "reason": "supportive bounded runner execution"},
    "python_json": {"tried": True, "used": True, "reason": "supportive suite receipt serialization"},
    "validate_formal_scout_results": {"tried": True, "used": True, "reason": "supportive result contract validation"},
    "lint_sim_contract": {"tried": True, "used": True, "reason": "supportive source contract validation"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_subprocess": "supportive",
    "python_json": "supportive",
    "validate_formal_scout_results": "supportive",
    "lint_sim_contract": "supportive",
}


SUITE_SCRIPTS = [
    # New explicit-spinor repair/scale rows.
    "sim_eight_node_spinor_network_flux_current_gate_probe.py",
    "sim_explicit_spinor_entanglement_engine_manifold_8q_probe.py",
    "sim_explicit_spinor_full_igt_64_substage_engine_cycle_probe.py",
    "sim_explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe.py",
    "sim_geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe.py",
    "sim_explicit_spinor_mps_8_16_32_64_flux_scaling_probe.py",
    "sim_explicit_spinor_peps3d_64_site_geometry_flux_probe.py",
    # Existing large tensor/PEPS/MPS rows that the audit classified.
    "sim_geometric_constraint_manifold_stage_flux_8qubit_pytorch_topology_probe.py",
    "sim_peps3d_64_site_no_dense_environment_topology_flux_probe.py",
    "sim_source_native_peps3d_64_site_slot_dynamics_closeout_probe.py",
    "sim_two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe.py",
    "sim_two_root_constraint_spinor_entanglement_8_16_32_64_basin_boundary_carrier_probe.py",
    "sim_single_chiral_thirty_two_substage_site_width_mps_topology_flux_probe.py",
    "sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py",
    "sim_two_root_constraint_l64_doubled_mps_lindblad_pilot_probe.py",
    # Existing explicit spinor/twistor rows, including below-scale controls.
    "sim_finite_spinor_tensor_network_channel_order_noncommutation_probe.py",
    "sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py",
    "sim_spinor_twistor_flux_basin_binding_probe.py",
    "sim_spinor_twistor_entanglement_information_network_root_gate_probe.py",
    "sim_spinor_twistor_xi_cut_phi0_bridge_candidate_probe.py",
    # Current untracked/active flux, Axis0, IGT, Holodeck, and science rows.
    "sim_bounded_layered_flux_geometry_probe.py",
    "sim_layer_dependency_flux_ablation_probe.py",
    "sim_shell_cut_axis0_response_probe.py",
    "sim_shell_cut_response_stress_probe.py",
    "sim_qit_payoff_selector_strategy_probe.py",
    "sim_holodeck_science_world_memory_ablation_probe.py",
    "sim_science_hypothesis_bank_holdout_probe.py",
    "sim_stage_capability_state_sweep_probe.py",
    "sim_runtime_priority_work_suite_probe.py",
]


def expected_result_path(script_name: str) -> pathlib.Path | None:
    source = (ROOT / script_name).read_text(encoding="utf-8")
    marker = "OUT_PATH = RESULT_DIR / "
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(marker):
            tail = stripped[len(marker):].strip()
            if tail.startswith('"') or tail.startswith("'"):
                value = tail.strip().strip('"').strip("'")
                return RESULT_DIR / value
    # Most new rows use NAME + f-string. Infer from filename.
    name = script_name.removeprefix("sim_").removesuffix(".py")
    inferred = RESULT_DIR / f"{name}_results.json"
    return inferred


def run_command(args: list[str], *, timeout: int = 900) -> dict[str, Any]:
    started = time.time()
    env = os.environ.copy()
    env.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache")
    env.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-codex-ratchet")
    proc = subprocess.run(
        args,
        cwd=REPO,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return {
        "args": args,
        "env_overrides": {
            "NUMBA_CACHE_DIR": env.get("NUMBA_CACHE_DIR"),
            "MPLCONFIGDIR": env.get("MPLCONFIGDIR"),
        },
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - started,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "pass": proc.returncode == 0,
    }


def run_script(script_name: str) -> dict[str, Any]:
    path = ROOT / script_name
    if not path.exists():
        return {"script": script_name, "exists": False, "pass": False, "error": "missing_script"}
    result_path = expected_result_path(script_name)
    try:
        command = run_command([str(PYTHON), str(path.relative_to(REPO))], timeout=1200)
    except subprocess.TimeoutExpired as exc:
        command = {
            "args": [str(PYTHON), str(path.relative_to(REPO))],
            "env_overrides": {
                "NUMBA_CACHE_DIR": "/private/tmp/numba-cache",
                "MPLCONFIGDIR": "/private/tmp/matplotlib-codex-ratchet",
            },
            "returncode": None,
            "elapsed_seconds": 1200,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "pass": False,
            "error": "timeout",
        }
    result_exists = bool(result_path and result_path.exists())
    result_data: dict[str, Any] = {}
    if result_exists and result_path is not None:
        try:
            result_data = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - suite receipt should capture parse failures.
            result_data = {"parse_error": repr(exc)}
    result_pass = (
        result_data.get("all_pass") is True
        or (result_data.get("summary") or {}).get("all_pass") is True
    )
    return {
        "script": script_name,
        "exists": True,
        "command": command,
        "result_path": str(result_path.relative_to(REPO)) if result_path else None,
        "result_exists": result_exists,
        "result_all_pass": result_data.get("all_pass"),
        "result_summary_all_pass": (result_data.get("summary") or {}).get("all_pass"),
        "classification": result_data.get("classification"),
        "promotion_allowed": result_data.get("promotion_allowed"),
        "claim_ceiling": result_data.get("claim_ceiling", "")[:260],
        "summary": result_data.get("summary", {}),
        "pass": command["pass"] and result_exists and result_pass,
    }


def validate_results(result_paths: list[str]) -> dict[str, Any]:
    existing = [path for path in result_paths if (REPO / path).exists()]
    if not existing:
        return {"pass": False, "error": "no_existing_results"}
    return run_command(
        [
            str(PYTHON),
            "system_v5/ops/formal_scouts/validate_formal_scout_results.py",
            *existing,
        ],
        timeout=300,
    )


def lint_sources(script_names: list[str]) -> dict[str, Any]:
    existing = [f"system_v5/ops/formal_scouts/{name}" for name in script_names if (ROOT / name).exists()]
    if not existing:
        return {"pass": False, "error": "no_existing_sources"}
    return run_command([str(PYTHON), "scripts/lint_sim_contract.py", *existing], timeout=300)


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [run_script(script) for script in SUITE_SCRIPTS]
    result_paths = [row["result_path"] for row in rows if row.get("result_path")]
    validation = validate_results(result_paths)
    lint = lint_sources(SUITE_SCRIPTS)
    missing_or_failed = [row for row in rows if not row.get("pass")]
    all_pass = not missing_or_failed and validation["pass"] and lint["pass"]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": "flux_spinor_full_suite_20260524",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": {
            "suite_scripts_executed": {
                "pass": all(row.get("pass") for row in rows),
                "script_count": len(rows),
                "rows": rows,
            },
            "result_contract_validation_passed": validation,
            "source_contract_lint_passed": lint,
        },
        "graveyard_companions": {
            "GC1_suite_does_not_promote_physics_or_flux": {
                "pass": PROMOTION_ALLOWED is False and "does not admit final flux" in CLAIM_CEILING,
                "promotion_allowed": PROMOTION_ALLOWED,
            },
            "GC2_failed_rows_are_reported_not_hidden": {
                "pass": True,
                "failed_or_missing_count": len(missing_or_failed),
                "failed_or_missing_scripts": [row.get("script") for row in missing_or_failed],
            },
        },
        "nearby_variants": {
            "total": len(SUITE_SCRIPTS),
            "passed": sum(1 for row in rows if row.get("pass")),
            "failed_or_missing": [row.get("script") for row in missing_or_failed],
            "not_tested_here": [
                "dense_2**64_amplitude_flux",
                "full_peps3d_environment_contraction",
                "8_plus_twistor_network_closure",
                "final_axis0_phi0_admission",
                "Standard_Model_or_gravity_derivation",
            ],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 bounded formal-scout suite over flux/spinor/Axis0/Holodeck/IGT/science rows; it is not a legacy v4 probe promotion.",
            "v4_equivalent": None,
        },
        "boundary": {
            "B1_full_suite_is_bounded": {
                "pass": True,
                "script_count": len(rows),
                "timeout_seconds_per_script": 1200,
            },
            "B2_results_may_be_gitignored": {
                "pass": True,
                "note": "formal_scout result JSONs are usually ignored by repo policy; source/audit staging is separate controller work",
            },
        },
        "summary": {
            "script_count": len(rows),
            "passed_scripts": sum(1 for row in rows if row.get("pass")),
            "failed_or_missing_scripts": [row.get("script") for row in missing_or_failed],
            "validation_pass": validation["pass"],
            "lint_pass": lint["pass"],
            "elapsed_seconds": time.time() - started,
        },
        "all_pass": all_pass,
    }
    SUITE_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(SUITE_RESULT), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
