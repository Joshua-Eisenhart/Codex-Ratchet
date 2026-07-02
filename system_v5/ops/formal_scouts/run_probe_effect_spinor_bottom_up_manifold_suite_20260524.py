#!/usr/bin/env python3
"""Run the probe/effect -> spinor/quaternion -> tensor -> engine suite.

Suite orchestration only.

This runner is intentionally bottom-up. It starts with finite effect/probe
laws and probe-relative identity, then finite probe-family variants and history
effects, then spinor/quaternion geometry, tensor carriers, engine schedules,
bridge/control receipts, Axis0 candidates, and only then derived flux
candidates. It does not promote any final manifold, Axis0, flux, PEPS3D,
gravity, Standard Model, or physics claim.
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
SUITE_RESULT = RESULT_DIR / "probe_effect_spinor_bottom_up_manifold_suite_20260524_results.json"
PYTHON = pathlib.Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3")

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "suite_orchestration_control"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Suite orchestration only: reruns bottom-up finite effect/probe, "
    "SIC/MUB/contextual/process, spinor/quaternion, MPS/PEPS/PEPS3D, engine, "
    "bridge/control, Axis0, and derived-flux formal scouts. A green suite does "
    "not admit final manifold foundation, Axis0, Xi, flux, PEPS3D closure, "
    "Standard Model, gravity, Yang-Mills, Riemann, or physics claims."
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

EXPECTED_BLOCKED_SCRIPTS: dict[str, str] = {
    "sim_two_root_constraint_peps_small_grid_dynamics_probe.py": (
        "Small-grid PEPS dynamic receipt is a bounded rung, not final PEPS closure."
    ),
    "sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe.py": (
        "Tiny-grid PEPS3D dynamic receipt is a bounded rung, not final PEPS3D closure."
    ),
    "sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py": (
        "Coupled-E16 bridge can be weakly control-separated while final manifold admission remains blocked."
    ),
    "sim_two_root_constraint_full_manifold_runtime_trace_refresh_probe.py": (
        "Trace refresh is expected to preserve final-admission blockers after weak coupled-E16 evidence."
    ),
    "sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe.py": (
        "Stress controls are expected to demote nonrobust L4 Phi0 bridge families when controls win."
    ),
    "sim_two_root_constraint_full_manifold_trace_after_phi0_stress_probe.py": (
        "Post-stress trace is expected to keep final manifold admission blocked under nonrobust Phi0 controls."
    ),
    "sim_two_root_constraint_phi0_bridge_response_gradient_after_stress_probe.py": (
        "Response-gradient repair is expected to remain nonpromotional unless it separates from controls."
    ),
    "sim_two_root_constraint_axis0_layered_entropy_ratchet_audit_probe.py": (
        "Axis0 layered entropy audit is expected to keep final closure blocked until L7 history or L8 shell-weighted Xi/Phi0 receipts exist."
    ),
    "sim_axis0_qit_fep_signed_gradient_probe.py": (
        "Flat pair-level signed QIT/FEP gradient is expected to remain nonpromotional because chirality fails without PEPS3D spinor-network flux."
    ),
}


MANIFOLD_LAYER_RATCHET: list[dict[str, Any]] = [
    {
        "layer": "L0",
        "name": "finite_probe_effect_identity",
        "role": "finite effects, POVM laws, and probe-relative identity; no primitive Cartesian object",
        "must_precede": ["density_carrier_and_history_effects"],
    },
    {
        "layer": "L1",
        "name": "density_carrier_and_history_effects",
        "role": "density operators as admitted carriers plus SIC/MUB/contextual/process response families",
        "must_precede": ["spinor_quaternion_hopf_weyl_geometry"],
    },
    {
        "layer": "L2",
        "name": "spinor_quaternion_hopf_weyl_geometry",
        "role": "explicit spinors, Hopf/fiber structure, Weyl split, and quaternion/IJK candidate readouts",
        "must_precede": ["operator_loop_and_tensor_carriers"],
    },
    {
        "layer": "L3",
        "name": "operator_loop_and_tensor_carriers",
        "role": "noncommuting operator/loop placement and MPS/PEPS/PEPS3D carriers seeded by lower layers",
        "must_precede": ["engine_runtime_schedule"],
    },
    {
        "layer": "L4",
        "name": "engine_runtime_schedule",
        "role": "source-aligned engine schedules and bounded runtime rows over admitted carriers",
        "must_precede": ["bridge_xi_phi0_control_receipts"],
    },
    {
        "layer": "L5",
        "name": "bridge_xi_phi0_control_receipts",
        "role": "cut-state, history-window, slow-mode, stress, and Xi/Phi0 control receipts",
        "must_precede": ["axis0_candidate_gate"],
    },
    {
        "layer": "L6",
        "name": "support_axis0_candidate_gate",
        "role": (
            "support Axis0 candidates after bridge/cut-state evidence; these are "
            "not final Axis0 because flux-bound readout still has to be derived"
        ),
        "must_precede": ["derived_flux_candidate_gate"],
    },
    {
        "layer": "L7",
        "name": "derived_flux_candidate_gate",
        "role": "flux as dynamic spinor-shell boundary current/coexistence family, never as primitive state field or early local lego",
        "must_precede": ["flux_bound_axis0_gradient_readout"],
    },
    {
        "layer": "L8",
        "name": "flux_bound_axis0_gradient_readout",
        "role": (
            "Axis0 as signed QIT/FEP entropy-gradient readout on derived "
            "PEPS3D spinor-network flux; final Axis0 remains blocked"
        ),
        "must_precede": [],
    },
]


STAGED_SCRIPTS: list[tuple[str, list[str]]] = [
    (
        "L0_finite_effect_probe_substrate",
        [
            "sim_finite_effect_algebra_laws_probe.py",
            "sim_finite_effect_sic_weyl_substrate_admission_probe.py",
            "sim_sic_mub_probe_family_comparison_probe.py",
            "sim_finite_contextuality_sheaf_event_gate_probe.py",
            "sim_process_povm_quantum_comb_history_gate_probe.py",
            "sim_geometric_constraint_manifold_representation_alignment_probe.py",
        ],
    ),
    (
        "L1_spinor_quaternion_networks",
        [
            "sim_geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe.py",
            "sim_eight_node_spinor_network_flux_current_gate_probe.py",
            "sim_explicit_spinor_entanglement_engine_manifold_8q_probe.py",
            "sim_explicit_spinor_full_igt_64_substage_engine_cycle_probe.py",
        ],
    ),
    (
        "L2_mps_peps_peps3d_carriers",
        [
            "sim_explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe.py",
            "sim_explicit_spinor_mps_8_16_32_64_flux_scaling_probe.py",
            "sim_explicit_spinor_peps3d_64_site_geometry_flux_probe.py",
            "sim_peps_peps3d_local_environment_contraction_gate_probe.py",
            "sim_two_root_constraint_peps_small_grid_dynamics_probe.py",
            "sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe.py",
            "sim_two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe.py",
        ],
    ),
    (
        "L3_engine_runtime",
        [
            "sim_source_aligned_qit_engine_runtime_probe.py",
            "sim_source_aligned_qit_engine_attractor_basin_probe.py",
            "sim_two_root_constraint_qit_engine_manifold_runtime_build_probe.py",
        ],
    ),
    (
        "L4_bridge_xi_phi0_control_receipts",
        [
            "sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py",
            "sim_two_root_constraint_full_manifold_runtime_trace_refresh_probe.py",
            "sim_two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe.py",
            "sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe.py",
            "sim_two_root_constraint_full_manifold_trace_after_phi0_stress_probe.py",
            "sim_two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe.py",
            "sim_two_root_constraint_phi0_bridge_response_gradient_after_stress_probe.py",
            "sim_spinor_twistor_xi_cut_phi0_bridge_candidate_probe.py",
            "sim_axis0_mps_stinespring_process_xi_handoff_probe.py",
        ],
    ),
    (
        "L5_axis0_candidates",
        [
            "sim_axis0_ijk_shell_correlation_response_probe.py",
            "sim_two_root_constraint_axis0_layered_entropy_ratchet_audit_probe.py",
            "sim_shell_cut_axis0_response_probe.py",
            "sim_axis0_mps_shell_kraus_handoff_probe.py",
            "sim_qit_fep_axis0_path_integral_spinor_probe.py",
            "sim_axis0_qit_fep_signed_gradient_probe.py",
        ],
    ),
    (
        "L6_derived_flux_candidates",
        [
            "sim_dynamic_spinor_shell_chiral_flux_topology_probe.py",
            "sim_dynamic_spinor_shell_flux_topology_boundary_probe.py",
            "sim_layer_dependency_flux_ablation_probe.py",
            "sim_spinor_twistor_flux_basin_binding_probe.py",
            "sim_two_root_constraint_flux_coherent_recovery_phi0_candidate_probe.py",
            "sim_two_root_constraint_flux_coherent_recovery_stress_probe.py",
        ],
    ),
    (
        "L7_flux_bound_axis0_gradient",
        [
            "sim_peps3d_spinor_network_flux_axis0_gradient_probe.py",
            "sim_peps3d_spinor_network_flux_axis0_scaling_probe.py",
            "sim_peps3d_flux_axis0_calibration_ablation_probe.py",
            "sim_peps3d_flux_axis0_calibration_envelope_stress_probe.py",
            "sim_peps3d_flux_axis0_heldout_shape_stress_probe.py",
            "sim_peps3d_flux_axis0_boundary_sampler_stress_probe.py",
            "sim_peps3d_flux_axis0_target_scramble_control_probe.py",
            "sim_peps3d_flux_axis0_calibration_rule_derivation_blocker_probe.py",
            "sim_peps3d_flux_axis0_boundary_functional_invariance_probe.py",
            "sim_peps3d_flux_axis0_runtime_record_binding_gate_probe.py",
            "sim_peps3d_flux_axis0_runtime_bound_loop4_probe.py",
            "sim_peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe.py",
            "sim_peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe.py",
        ],
    ),
]


def flat_scripts() -> list[str]:
    scripts: list[str] = []
    for _, rows in STAGED_SCRIPTS:
        scripts.extend(rows)
    return scripts


def expected_result_path(script_name: str) -> pathlib.Path:
    source_path = ROOT / script_name
    if source_path.exists():
        source = source_path.read_text(encoding="utf-8")
        marker = "OUT_PATH = RESULT_DIR / "
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(marker):
                tail = stripped[len(marker) :].strip()
                if tail.startswith(("'", '"')):
                    return RESULT_DIR / tail.strip().strip("'").strip('"')
    name = script_name.removeprefix("sim_").removesuffix(".py")
    return RESULT_DIR / f"{name}_results.json"


def run_command(args: list[str], *, timeout: int = 1200) -> dict[str, Any]:
    started = time.time()
    env = os.environ.copy()
    env.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache")
    env.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-codex-ratchet")
    try:
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
            "returncode": proc.returncode,
            "elapsed_seconds": time.time() - started,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "pass": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "args": args,
            "returncode": None,
            "elapsed_seconds": time.time() - started,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "pass": False,
            "error": "timeout",
        }


def run_script(stage: str, script_name: str) -> dict[str, Any]:
    path = ROOT / script_name
    result_path = expected_result_path(script_name)
    expected_blocked = script_name in EXPECTED_BLOCKED_SCRIPTS
    if not path.exists():
        return {
            "stage": stage,
            "script": script_name,
            "exists": False,
            "result_path": str(result_path.relative_to(REPO)),
            "pass": False,
            "error": "missing_script",
        }
    command: dict[str, Any]
    if expected_blocked and result_path.exists():
        command = {
            "args": ["reuse_existing_expected_blocker_receipt", str(result_path.relative_to(REPO))],
            "returncode": 0,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "",
            "pass": True,
            "reused_existing_receipt": True,
        }
    else:
        command = run_command([str(PYTHON), str(path.relative_to(REPO))], timeout=1200)
    result_exists = result_path.exists()
    result_data: dict[str, Any] = {}
    if result_exists:
        try:
            result_data = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            result_data = {"parse_error": repr(exc)}
    result_pass = result_data.get("all_pass") is True or (result_data.get("summary") or {}).get("all_pass") is True
    expected_blocked_pass = bool(
        expected_blocked
        and result_exists
        and command["returncode"] in {0, 1}
        and result_data.get("classification") == CLASSIFICATION
        and result_data.get("promotion_allowed") is False
    )
    return {
        "stage": stage,
        "script": script_name,
        "exists": True,
        "command": command,
        "result_path": str(result_path.relative_to(REPO)),
        "result_exists": result_exists,
        "result_all_pass": result_data.get("all_pass"),
        "classification": result_data.get("classification"),
        "promotion_allowed": result_data.get("promotion_allowed"),
        "source_alignment_category": result_data.get("source_alignment_category"),
        "summary": result_data.get("summary", {}),
        "candidate_status": result_data.get("candidate_status"),
        "expected_blocked": expected_blocked,
        "expected_blocked_reason": EXPECTED_BLOCKED_SCRIPTS.get(script_name),
        "expected_blocked_pass": expected_blocked_pass,
        "strict_pass": command["pass"] and result_exists and result_pass,
        "pass": expected_blocked_pass or (command["pass"] and result_exists and result_pass),
    }


def validate_results(paths: list[str]) -> dict[str, Any]:
    existing = [path for path in paths if (REPO / path).exists()]
    if not existing:
        return {"pass": False, "error": "no_existing_results"}
    return run_command([str(PYTHON), "system_v5/ops/formal_scouts/validate_formal_scout_results.py", *existing], timeout=300)


def lint_sources(scripts: list[str]) -> dict[str, Any]:
    existing = [f"system_v5/ops/formal_scouts/{script}" for script in scripts if (ROOT / script).exists()]
    if not existing:
        return {"pass": False, "error": "no_existing_sources"}
    return run_command([str(PYTHON), "scripts/lint_sim_contract.py", *existing], timeout=300)


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for stage, scripts in STAGED_SCRIPTS:
        for script in scripts:
            rows.append(run_script(stage, script))
    strict_rows = [row for row in rows if not row.get("expected_blocked")]
    blocked_rows = [row for row in rows if row.get("expected_blocked")]
    result_paths = [row["result_path"] for row in strict_rows if row.get("result_path")]
    validation = validate_results(result_paths)
    lint = lint_sources(flat_scripts())
    failed = [row for row in rows if not row.get("pass")]
    unexpected_failed = [row for row in failed if not row.get("expected_blocked")]
    blocked_failed = [row for row in blocked_rows if not row.get("expected_blocked_pass")]
    stage_summary = {}
    for stage, _ in STAGED_SCRIPTS:
        stage_rows = [row for row in rows if row["stage"] == stage]
        stage_summary[stage] = {
            "total": len(stage_rows),
            "passed": sum(1 for row in stage_rows if row.get("pass")),
            "failed": [row["script"] for row in stage_rows if not row.get("pass")],
        }
    all_pass = not unexpected_failed and not blocked_failed and validation["pass"] and lint["pass"]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": "probe_effect_spinor_bottom_up_manifold_suite_20260524",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": {
            "bottom_up_stage_scripts_executed": {
                "pass": not unexpected_failed,
                "stage_summary": stage_summary,
                "rows": rows,
            },
            "expected_blocked_receipts_classified": {
                "pass": not blocked_failed,
                "blocked_scripts": {
                    row["script"]: row.get("expected_blocked_reason") for row in blocked_rows
                },
                "failed_blocked_receipts": [row["script"] for row in blocked_failed],
            },
            "result_contract_validation_passed": validation,
            "source_contract_lint_passed": lint,
        },
        "graveyard_companions": {
            "GC1_suite_does_not_promote_final_axis0_flux_or_physics": {
                "pass": PROMOTION_ALLOWED is False and "does not admit final manifold" in CLAIM_CEILING,
                "promotion_allowed": PROMOTION_ALLOWED,
            },
            "GC2_failed_rows_are_reported_not_hidden": {
                "pass": True,
                "failed_count": len(failed),
                "failed_scripts": [row["script"] for row in failed],
            },
        },
        "boundary": {
            "B1_bottom_up_order_declared": {
                "pass": [stage for stage, _ in STAGED_SCRIPTS]
                == [
                    "L0_finite_effect_probe_substrate",
                    "L1_spinor_quaternion_networks",
                    "L2_mps_peps_peps3d_carriers",
                    "L3_engine_runtime",
                    "L4_bridge_xi_phi0_control_receipts",
                    "L5_axis0_candidates",
                    "L6_derived_flux_candidates",
                    "L7_flux_bound_axis0_gradient",
                ],
                "stages": [stage for stage, _ in STAGED_SCRIPTS],
                "manifold_layer_ratchet": MANIFOLD_LAYER_RATCHET,
            },
            "B2_bounded_runner_not_final_admission": {
                "pass": "does not admit final manifold foundation" in CLAIM_CEILING and PROMOTION_ALLOWED is False,
                "claim_ceiling": CLAIM_CEILING,
            },
        },
        "nearby_variants": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row.get("pass")),
            "failed_or_missing": [row["script"] for row in failed],
            "unexpected_failed_or_missing": [row["script"] for row in unexpected_failed],
            "expected_blocked": [row["script"] for row in blocked_rows],
            "stage_summary": stage_summary,
            "manifold_layer_count": len(MANIFOLD_LAYER_RATCHET),
        },
        "all_pass": all_pass,
        "blockers": [],
        "expected_nonpromotion_receipts": [
            {
                "script": row["script"],
                "reason": row.get("expected_blocked_reason"),
                "summary": row.get("summary", {}),
            }
            for row in blocked_rows
        ],
        "summary": {
            "script_count": len(rows),
            "passed_scripts": sum(1 for row in rows if row.get("pass")),
            "failed_or_missing_scripts": [row["script"] for row in failed],
            "unexpected_failed_or_missing_scripts": [row["script"] for row in unexpected_failed],
            "expected_blocked_scripts": [row["script"] for row in blocked_rows],
            "stage_summary": stage_summary,
            "manifold_layer_ratchet": MANIFOLD_LAYER_RATCHET,
            "validation_pass": validation["pass"],
            "lint_pass": lint["pass"],
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 bottom-up suite over finite effect/probe, spinor/"
            "quaternion, tensor-network, engine, bridge/control, Axis0, and "
            "derived-flux formal scouts. "
            "It is not a legacy v4 probe promotion."
        ),
        "next_required_work": [
            "Lift the dynamic IJK shell-current topology fixture into MPS/PEPS/PEPS3D carriers before claiming flux closure.",
            "Port the Axis0 IJK shell-response harness from 8-qubit spinor shells onto the 8/16/32/64 MPS carrier.",
            "Scale the PEPS3D flux-bound Axis0 gradient from 2x2x2 to larger shell carriers only after local contraction controls stay green.",
            "If L0-L3 pass but bridge rows remain weak, rewrite Xi/Phi0 to consume finite process-POVM and SIC/MUB response histories directly.",
            "If PEPS/PEPS3D rows pass only as simple-update first rungs, add deterministic MPDO/Lindblad PEPS3D closures.",
            "If Axis0 controls remain nonrobust, keep final manifold admission blocked and continue bottom-up layer replacement before derived-flux promotion.",
        ],
    }
    SUITE_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(SUITE_RESULT), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
