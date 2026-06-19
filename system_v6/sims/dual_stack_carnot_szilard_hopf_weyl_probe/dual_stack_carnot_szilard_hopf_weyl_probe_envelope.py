#!/usr/bin/env python3
"""Composite envelope for dual_stack_carnot_szilard_hopf_weyl_probe."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "dual_stack_carnot_szilard_hopf_weyl_probe"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULTS_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULTS_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULTS_DIR / f"{SIM_ID}_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOL = 5.0e-7

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently run engine receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result-path binding",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def numeric_shared_scalars(payload: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in payload.get("shared_scalars", {}).items():
        if isinstance(value, (int, float)):
            out[key] = float(value)
    return out


def scalar_spreads(engine_scalars: dict[str, dict[str, float]]) -> dict[str, dict[str, Any]]:
    common = set.intersection(*(set(values) for values in engine_scalars.values()))
    rows: dict[str, dict[str, Any]] = {}
    for key in sorted(common):
        values = {engine: scalars[key] for engine, scalars in engine_scalars.items()}
        spread = max(values.values()) - min(values.values())
        rows[key] = {"values": values, "spread": spread, "within_tolerance": spread <= TOL}
    return rows


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload.get("packages_used", []),
        "aligned_packages_load_bearing": payload.get("aligned_packages_load_bearing", []),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": numeric_shared_scalars(payload),
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    engine_scalars = {
        "julia": numeric_shared_scalars(julia),
        "jax": numeric_shared_scalars(jax),
        "pytorch": numeric_shared_scalars(pytorch),
    }
    spreads = scalar_spreads(engine_scalars)
    max_divergence = max((row["spread"] for row in spreads.values()), default=0.0)
    out_of_tolerance = {key: row for key, row in spreads.items() if not row["within_tolerance"]}

    z3_status = jax["smt"]["z3"]["equality_status"]
    cvc5_status = jax["smt"]["cvc5"]["equality_status"]
    control_z3 = jax["smt"]["commuting_control_z3"]["equality_status"]
    control_cvc5 = jax["smt"]["commuting_control_cvc5"]["equality_status"]
    julia_z3 = julia["smt"]["julia_z3"]["equality_status"]
    julia_control = julia["smt"]["commuting_control_julia_z3"]["equality_status"]
    joint_cptp_ok = all(
        payload["legality_ledgers"]["cptp"][name]["choi_shape"] == [16, 16]
        and payload["legality_ledgers"]["cptp"][name]["choi_psd"] is True
        and payload["legality_ledgers"]["cptp"][name]["trace_preserving"] is True
        for payload in (julia, jax, pytorch)
        for name in ("M", "F", "R")
    )

    all_pass = bool(
        julia.get("all_pass") is True
        and jax.get("all_pass") is True
        and pytorch.get("all_pass") is True
        and joint_cptp_ok
        and not out_of_tolerance
        and z3_status == cvc5_status == julia_z3 == "unsat"
        and control_z3 == control_cvc5 == julia_control == "sat"
        and all(payload.get("reads_peer_result") is False for payload in (julia, jax, pytorch))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )

    headline = {
        "Delta_trace_norm": engine_scalars["julia"]["headline_delta_trace_norm"],
        "literal_loop_g_DI_trace_norm": engine_scalars["julia"]["literal_loop_g_DI_trace_norm"],
        "legacy_reduced_delta_trace_norm": engine_scalars["julia"]["legacy_reduced_delta_trace_norm"],
        "coherent_reduced_delta_trace_norm": engine_scalars["julia"]["coherent_reduced_delta_trace_norm"],
        "Type1_vs_Type2_trace_norm": engine_scalars["julia"]["type1_type2_trace_norm"],
        "ax6_order_gap_U_E_trace_norm": engine_scalars["julia"]["ax6_order_gap_U_E_trace_norm"],
        "commuting_control_delta_trace_norm": engine_scalars["julia"]["commuting_control_delta_trace_norm"],
        "headline_loop": "section_15_literal_inductive_loop",
    }
    szilard = {
        "quantum_coherent_MI": engine_scalars["julia"]["quantum_coherent_MI"],
        "quantum_coherent_MI_gate": engine_scalars["julia"]["quantum_coherent_MI_gate"],
        "I_c_S_to_M": engine_scalars["julia"]["I_c_S_to_M"],
        "I_c_S_to_M_gate": engine_scalars["julia"]["I_c_S_to_M_gate"],
        "classical_measured_MI": engine_scalars["julia"]["classical_measured_MI"],
        "classical_control_I_c_S_to_M": engine_scalars["julia"]["classical_control_I_c_S_to_M"],
        "information_gained_nats": engine_scalars["julia"]["information_gained_nats"],
        "information_gained_bits": engine_scalars["julia"]["information_gained_bits"],
        "work_extracted": engine_scalars["julia"]["work_extracted"],
        "feedback_energy_before": engine_scalars["julia"]["feedback_energy_before"],
        "feedback_energy_after": engine_scalars["julia"]["feedback_energy_after"],
        "landauer_reset_cost": engine_scalars["julia"]["landauer_reset_cost"],
        "landauer_lower_bound_ln2_p_excited": engine_scalars["julia"]["landauer_lower_bound_ln2_p_excited"],
        "landauer_margin_W_minus_reset_cost": engine_scalars["julia"]["landauer_margin_W_minus_reset_cost"],
        "bound_lhs_W_minus_kTln2I": engine_scalars["julia"]["szilard_bound_lhs_W_minus_kTln2I"],
        "work_source": "feedback_energy_drop_Tr_H_rho_before_minus_after",
        "work_placeholder": False,
    }
    axis0 = {
        "Phi0_Ic_S_to_M": engine_scalars["julia"]["I_c_S_to_M"],
        "quantum_coherent_MI": engine_scalars["julia"]["quantum_coherent_MI"],
        "classical_measured_MI": engine_scalars["julia"]["classical_measured_MI"],
        "stage_labeled_cut_table": julia["axis0_cut"]["stage_labeled_cut_table"],
    }

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": f"{SIM_ID}_envelope",
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "finite-map dual-stack Carnot/Szilard Hopf-Weyl witness probe only; no engine, M(C), Axis0, bridge, or admission claim",
        "all_pass": all_pass,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "pinned_spec": julia.get("pinned_spec"),
        "headline": headline,
        "szilard_ledger_summary": szilard,
        "axis0_cut_summary": axis0,
        "joint_cptp_summary": {
            "joint_M_F_R_choi_16x16_psd_tp_all_engines": joint_cptp_ok,
            "pytorch": {name: pytorch["legality_ledgers"]["cptp"][name] for name in ("M", "F", "R")},
            "jax": {name: jax["legality_ledgers"]["cptp"][name] for name in ("M", "F", "R")},
            "julia": {name: julia["legality_ledgers"]["cptp"][name] for name in ("M", "F", "R")},
        },
        "smt_verdicts": {
            "z3": z3_status,
            "cvc5": cvc5_status,
            "julia_z3": julia_z3,
            "commuting_control_z3": control_z3,
            "commuting_control_cvc5": control_cvc5,
            "commuting_control_julia_z3": julia_control,
        },
        "controls": {
            "chirality_erasure_H_L_equals_H_R": {
                "gamma5_odd_L": engine_scalars["julia"]["gamma5_odd_L"],
                "chirality_erasure_death_value": engine_scalars["julia"]["chirality_erasure_death_value"],
                "dies": abs(engine_scalars["julia"]["chirality_erasure_death_value"]) <= 1.0e-9,
            },
            "sign_flip_diagnostic": {
                "gamma5_odd_L": engine_scalars["julia"]["gamma5_odd_L"],
                "gamma5_odd_HR_flip_diagnostic": engine_scalars["julia"]["gamma5_odd_HR_flip_diagnostic"],
                "sign_flip_diagnostic_trace_norm": engine_scalars["julia"]["sign_flip_diagnostic_trace_norm"],
            },
            "label_shuffle": julia["controls"]["label_shuffle"],
            "classical_diagonal_control": {
                "classical_measured_MI": engine_scalars["julia"]["classical_measured_MI"],
                "I_c_S_to_M": engine_scalars["julia"]["classical_control_I_c_S_to_M"],
                "qit_coherence_work_term": engine_scalars["julia"]["classical_control_qit_coherence_work"],
                "work_extracted": engine_scalars["julia"]["classical_control_work_extracted"],
            },
            "no_measurement": {
                "work_extracted": engine_scalars["julia"]["no_measurement_work_extracted"],
                "quantum_coherent_MI": engine_scalars["julia"]["no_measurement_quantum_coherent_MI"],
                "I_c_S_to_M": engine_scalars["julia"]["no_measurement_I_c_S_to_M"],
            },
            "no_bath": {
                "entropy_production": engine_scalars["julia"]["no_bath_entropy_production"],
                "state_trace_norm_from_input": engine_scalars["julia"]["no_bath_state_trace_norm_from_input"],
            },
            "commuting_control": {
                "commuting_pair_gap_trace_norm": engine_scalars["julia"]["commuting_pair_gap_trace_norm"],
                "commuting_control_delta_trace_norm": engine_scalars["julia"]["commuting_control_delta_trace_norm"],
            },
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_status,
                "claim": "4x4 joint M/F/R object bound: D_joint after I_joint equals I_joint after D_joint is UNSAT",
                "object_scope": jax["smt"]["z3"].get("object_scope"),
                "commuting_control_verdict": control_z3,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_status,
                "claim": "Independent 4x4 joint M/F/R entry-wise bound superoperator equality check matches z3",
                "object_scope": jax["smt"]["cvc5"].get("object_scope"),
                "commuting_control_verdict": control_cvc5,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3,
                "claim": "Julia Z3.jl binds the same 4x4 joint M/F/R object for the UNSAT equality; commuting control is explicitly reduced",
                "object_scope": julia["smt"]["julia_z3"].get("object_scope"),
                "commuting_control_verdict": julia_control,
            },
        },
        "claim_path_tools": ["Z3", "z3", "cvc5", "jax", "jax.numpy", "torch", "torch.func"],
        "control_only_tools": [],
        "shared_scalar_spreads": spreads,
        "out_of_tolerance_shared_scalars": out_of_tolerance,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_scalars,
            "max_divergence": max_divergence,
            "tolerance": TOL,
            "comparison_rule": "same-named shared scalar readouts only",
        },
        "ledger_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "DUAL_STACK_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"Delta={result['headline']['Delta_trace_norm']} "
        f"Type1Type2={result['headline']['Type1_vs_Type2_trace_norm']} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"z3={result['smt_verdicts']['z3']} "
        f"cvc5={result['smt_verdicts']['cvc5']} "
        f"julia_z3={result['smt_verdicts']['julia_z3']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
