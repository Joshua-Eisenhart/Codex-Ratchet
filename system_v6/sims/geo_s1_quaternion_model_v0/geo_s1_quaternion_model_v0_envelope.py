#!/usr/bin/env python3
"""Envelope for geo_s1_quaternion_model_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s1_quaternion_model_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
NUMPY_RESULT = RESULT_DIR / f"{SIM_ID}_numpy_control_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s1_quaternion_model_v0|stage:1|model:unit_quaternion|"
    "dictionary:z1=a+bi,z2=c-di for q=a+bi+cj+dk|"
    "hopf_quaternion=q*i*qbar|R=[[0,0,-1],[0,1,0],[1,0,0]]|"
    "complex_hopf=(2Re(z1*conj(z2)),2Im(z1*conj(z2)),|z1|^2-|z2|^2)|"
    "seed_ledger=jax.random.PRNGKey[42017:q_n20000,42018:r_n20000];"
    "torch.Generator.manual_seed[57001:volume_mc_n80000_160000_320000];"
    "numpy.default_rng[777:control_n15000]|"
    "rerun=SIM_PY geo_s1_quaternion_model_v0_{jax,julia,pytorch,numpy_control,envelope}|"
    "classification=scratch_diagnostic"
)

SEED_LEDGER = {
    "status": "declared_recompute_metadata_only",
    "rng_api": ["jax.random.PRNGKey", "torch.Generator.manual_seed", "numpy.random.default_rng"],
    "seeds": [
        {"engine": "jax", "seed": 42017, "use": "quaternion_sample_q", "sample_count": 20000},
        {"engine": "jax", "seed": 42018, "use": "quaternion_sample_r", "sample_count": 20000},
        {
            "engine": "pytorch",
            "seed": 57001,
            "use": "volume_monte_carlo_shell_rows",
            "sample_counts": [80000, 160000, 320000],
        },
        {"engine": "numpy_control", "seed": 777, "use": "wrong_convention_control", "sample_count": 15000},
    ],
    "deterministic_legs": ["julia_quaternion_table_samples"],
    "rerun_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3; $SIM_PY system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py && JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_julia.jl && $SIM_PY system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_pytorch.py && $SIM_PY system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_numpy_control.py && $SIM_PY system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_envelope.py",
}

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent leg receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing and pin checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    numpy_control = load_json(NUMPY_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}
    pin_hashes = {payload["pin_sha256"] for payload in [julia, jax, pytorch, numpy_control]}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in [julia, jax, pytorch, numpy_control]
    )
    q1 = {
        "julia": julia["Q_receipts"]["Q1_model_dictionary"],
        "jax": jax["Q_receipts"]["Q1_model_dictionary"],
    }
    q2 = {
        "julia": julia["Q_receipts"]["Q2_hopf_agreement"],
        "jax": jax["Q_receipts"]["Q2_hopf_agreement"],
        "numpy_control": numpy_control["shared_scalars"],
    }
    q3 = {
        "gauss_integral": pytorch["Q_receipts"]["Q3_linking_gauss_method"],
        "hopf_invariant_integral": jax["Q_receipts"]["Q3_linking_hopf_invariant_method"],
        "projected_crossing_count": pytorch["Q_receipts"]["Q3_linking_crossing_method"],
    }
    q4 = {
        "monte_carlo": pytorch["Q_receipts"]["Q4_volume_monte_carlo_method"],
        "metric_lattice": jax["Q_receipts"]["Q4_volume_metric_lattice_method"],
        "quaternion_measure": julia["Q_receipts"]["Q4_volume_quaternion_measure_method"],
    }
    q5 = {"julia": julia["Q_receipts"]["Q5_double_cover"], "jax": jax["Q_receipts"]["Q5_double_cover"]}
    controls = {
        "wrong_convention": {
            "julia": julia["controls"]["wrong_convention_skip_R"],
            "jax": jax["controls"]["wrong_convention_skip_R"],
            "numpy_control": numpy_control["controls"]["wrong_convention_skip_R"],
        },
        "broken_dictionary": {
            "julia": julia["controls"]["broken_dictionary_conjugation_error"],
            "jax": jax["controls"]["broken_dictionary_conjugation_error"],
        },
        "single_method": {
            "jax": jax["controls"]["single_method_control"],
            "pytorch": pytorch["controls"]["single_method_control"],
            "numpy_control": numpy_control["controls"]["single_method_control"],
        },
        "scrambled_fiber": jax["controls"]["scrambled_fiber_control"],
    }
    multi_method_tables = {
        "linking_number": [
            {"method": "Gauss linking integral", "engine": "pytorch", "value": q3["gauss_integral"]["final_value"], "target": 1.0},
            {"method": "Hopf invariant integral form", "engine": "jax", "value": q3["hopf_invariant_integral"]["final_value"], "target": 1.0},
            {"method": "Projected crossing count", "engine": "pytorch", "value": q3["projected_crossing_count"]["final_value"], "target": 1.0},
        ],
        "volume_s3": [
            {
                "method": "Monte Carlo quaternion shell",
                "engine": "pytorch",
                "value": q4["monte_carlo"]["final_volume"],
                "target": 2.0 * math.pi**2,
                "mc_volume_role": q4["monte_carlo"]["convergence"][-1]["mc_volume_role"],
            },
            {"method": "Metric determinant lattice with 2:1 correction", "engine": "jax", "value": q4["metric_lattice"]["final_corrected_volume"], "target": 2.0 * math.pi**2, "naive_chart_integral": q4["metric_lattice"]["convergence"][-1]["naive_chart_integral_2_to_1_cover"], "naive_target": 4.0 * math.pi**2},
            {"method": "Quaternion radial measure", "engine": "julia", "value": q4["quaternion_measure"]["value"], "target": 2.0 * math.pi**2},
        ],
    }
    q_gates = {
        "legs_exit_0_by_receipt": all(payload["all_pass"] is True for payload in [julia, jax, pytorch, numpy_control]),
        "pin_identical": len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC),
        "ceiling_exact": ceilings_exact,
        "Q1_receipts_pass": all(row["pass"] for row in q1.values()),
        "Q2_receipts_pass": q2["julia"]["pass"] and q2["jax"]["pass"] and q2["numpy_control"]["after_R_deviation"] <= 1.0e-8,
        "Q3_all_linking_methods_equal_1": all(abs(row["value"] - 1.0) < 1.0e-3 for row in multi_method_tables["linking_number"]),
        "Q4_all_volume_methods_near_2pi2": all(abs(row["value"] - 2.0 * math.pi**2) < (0.55 if row["method"].startswith("Monte Carlo") else 1.0e-4) for row in multi_method_tables["volume_s3"]),
        "Q5_double_cover_pass": all(row["pass"] for row in q5.values()),
        "controls_fired": all(item["fired"] for group in controls.values() for item in (group.values() if isinstance(group, dict) and "fired" not in group else [group])),
        "proofs_pass": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["pass"],
    }
    all_pass = all(q_gates.values())
    claim_path_tools = sorted({tool for payload in payloads.values() for tool in payload.get("claim_path_tools", [])})
    engine_values = {
        "julia": max(julia["shared_scalars"].values()),
        "jax": max(jax["shared_scalars"].values()),
        "pytorch": max(abs(pytorch["shared_scalars"]["gauss_linking_final"] - 1.0), abs(pytorch["shared_scalars"]["crossing_linking_final"] - 1.0)),
    }
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Stage-1 S1/Hopf geometry through the unit-quaternion model agrees pointwise with the pinned complex-pair model and multi-method invariants agree.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": SEED_LEDGER,
        "engine_contract": {"mode": "all_three_full_sims", "lanes": ["julia", "jax", "pytorch"], "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"]},
        "canon_runtime": {"semantic_owner": "julia", "julia_project": julia.get("julia_project"), "artifact_path": None, "artifact_sha256": None, "source_sha256": julia["source_sha256"], "receipt_path": julia["result_path"], "proof_tag": "quaternion_dictionary_Z3_raw_residual_check", "proof_pass": julia["proofs"]["julia_z3_raw_residuals_inside_tolerance"]["pass"], "table_version": None, "bracket_convention": "Hamilton i*j=k; dictionary z1=a+bi,z2=c-di", "consumer_policy": "independent engine recomputation; no peer-result reads"},
        "foreign_runtime_manifest": {"julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "canon quaternion dictionary and raw Z3 residuals"}, "jax": {"packages": jax["packages_used"], "role": "batched Haar sweeps plus z3/cvc5 proof"}, "pytorch": {"packages": pytorch["packages_used"], "role": "independent Gauss/crossing/Monte-Carlo methods"}, "numpy_control": {"packages": ["numpy"], "role": "control lane only"}, "tensor_exchange": "none_no_cross_engine_tensor_exchange", "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"]},
        "claim_path_tools": claim_path_tools,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {"julia": engine_record(julia, JULIA_RESULT), "jax": engine_record(jax, JAX_RESULT), "pytorch": engine_record(pytorch, PYTORCH_RESULT)},
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["z3_verdict"], "load_bearing": True, "raw_value_binding": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["raw_scaled_values"], "scrambled_fiber_control": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["scrambled_fiber_control_z3"]},
            "cvc5": {"ran": True, "verdict": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["cvc5_verdict"], "load_bearing": True, "raw_value_binding": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["raw_scaled_values"], "scrambled_fiber_control": jax["proofs"]["linking_methods_disagree_beyond_tolerance"]["scrambled_fiber_control_cvc5"]},
            "julia_z3": {"ran": True, "verdict": julia["proofs"]["julia_z3_raw_residuals_inside_tolerance"]["verdict"], "load_bearing": True, "proof": julia["proofs"]["julia_z3_raw_residuals_inside_tolerance"]},
        },
        "Q_receipts": {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5},
        "multi_method_tables": multi_method_tables,
        "controls": controls,
        "build_gates": q_gates,
        "divergence": {"julia_authoritative": True, "engine_values": engine_values, "max_divergence": max(engine_values.values()), "meaning": "max residual among engine-local agreement checks, not a promotion metric"},
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "envelope", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
