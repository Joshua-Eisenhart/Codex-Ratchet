#!/usr/bin/env python3
"""Composite envelope for foundation_cross_model_readout_matrix_v0.

The envelope reads completed Julia, JAX, and PyTorch leg receipts only after
each leg has computed locally with reads_peer_result=false.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "cross_model_readout_matrix_v0"
OBJECT_ID = "foundation_cross_model_readout_matrix_v0_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_cross_model_readout_matrix_v0_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_cross_model_readout_matrix_v0_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_pytorch_results.json"
CARRIER_SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_clifford_spinor_carrier_envelope.py"
CARRIER_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_clifford_spinor_carrier_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-7

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed engine receipts; not in the claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source fingerprint",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fences_ok(payload: dict[str, Any]) -> bool:
    return (
        payload.get("classification") == CLASSIFICATION
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        and payload.get("reads_peer_result") is False
        and bool(payload.get("source_path"))
        and bool(payload.get("source_sha256"))
    )


def engine_values(payload: dict[str, Any]) -> dict[str, float]:
    summary = payload["summary"]
    return {
        "support_size": float(summary["support_size"]),
        "lens_count": float(summary["lens_count"]),
        "full_probe_class_count": float(summary["full_probe_class_count"]),
        "carrier_erased_class_count": float(summary["carrier_erased_class_count"]),
        "label_shuffle_delta": float(summary["label_shuffle_delta"]),
        "real_structure_norm": float(summary["real_structure_norm"]),
        "erased_structure_norm": float(summary["erased_structure_norm"]),
        "readout_map_erasure_before": float(summary["readout_map_erasure_before"]),
        "readout_map_erasure_after": float(summary["readout_map_erasure_after"]),
        "order_reversal_delta": float(summary["order_reversal_delta"]),
    }


def max_divergence(values_by_engine: dict[str, dict[str, float]]) -> tuple[float, list[dict[str, Any]]]:
    keys = sorted(next(iter(values_by_engine.values())).keys())
    max_seen = 0.0
    disagreements: list[dict[str, Any]] = []
    for key in keys:
        rows = {engine: values[key] for engine, values in values_by_engine.items()}
        diff = max(rows.values()) - min(rows.values())
        max_seen = max(max_seen, diff)
        if diff > TOL:
            disagreements.append({"key": key, "values": rows, "max_minus_min": diff})
    return max_seen, disagreements


def engine_record(payload: dict[str, Any], result_path: Path, values: dict[str, float], role: str) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role": role,
        "all_pass": payload["all_pass"],
        "values": values,
    }


def combined_controls(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> dict[str, Any]:
    controls = {}
    for key in ["label_shuffle", "carrier_erasure", "readout_map_erasure", "order_composition_reversal"]:
        rows = {"julia": julia["controls"][key], "jax": jax["controls"][key], "pytorch": pytorch["controls"][key]}
        controls[key] = {
            "falsifies": julia["controls"][key]["falsifies"],
            "per_engine": rows,
            "flips_all_engines": all(row["flips"] is True for row in rows.values()),
        }
    controls["torch_func_jacrev_cross_vs_same"] = {
        "falsifies": "PyTorch being a decorative third mirror with no differentiable readout sensitivity",
        "per_engine": {"pytorch": pytorch["torch_func_jacrev"]},
        "flips_all_engines": bool(pytorch["torch_func_jacrev"]["cross_vs_same_gradient_flip"]),
    }
    controls["dual_smt_carrier_erasure"] = {
        "falsifies": "SMT proof re-checking a precomputed scalar instead of deriving carrier erasure collapse from entries",
        "per_engine": {"jax": jax["smt"]},
        "flips_all_engines": bool(
            jax["smt"]["z3"]["verdict"] == jax["smt"]["cvc5"]["verdict"] == "unsat"
            and jax["smt"]["z3"]["negative_control_verdict"] == jax["smt"]["cvc5"]["negative_control_verdict"] == "sat"
        ),
    }
    return controls


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    values_by_engine = {
        "julia": engine_values(julia),
        "jax": engine_values(jax),
        "pytorch": engine_values(pytorch),
    }
    divergence_max, structural_disagreements = max_divergence(values_by_engine)
    controls = combined_controls(julia, jax, pytorch)
    z3_record = jax["smt"]["z3"]
    cvc5_record = jax["smt"]["cvc5"]
    all_controls_flip = all(control["flips_all_engines"] is True for control in controls.values())
    all_fences_ok = all(fences_ok(payload) for payload in (julia, jax, pytorch))
    constraints_ok = all(
        payload["C"]["trace_eq_1"]
        and payload["C"]["psd"]
        and payload["C"]["hermitian"]
        and payload["C"]["normalization"]
        for payload in (julia, jax, pytorch)
    )
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and all_fences_ok
        and constraints_ok
        and all_controls_flip
        and not structural_disagreements
        and z3_record["verdict"] == cvc5_record["verdict"] == "unsat"
        and z3_record["negative_control_verdict"] == cvc5_record["negative_control_verdict"] == "sat"
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "codex_ratchet.three_engine_sim_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "reads_engine_result_jsons_after_local_legs": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "julia_authoritative": True,
            "legs_compute_locally_before_peer_comparison": True,
            "reads_peer_result_false_required_on_legs": True,
        },
        "carrier_source_pin": {
            "source_path": str(CARRIER_SOURCE_PATH),
            "result_path": str(CARRIER_RESULT_PATH),
            "read_only": True,
            "rebuilt": False,
            "support_reconstruction": "same finite Cl(6) spinor/density support shape used locally in each leg; prior carrier packet was not rebuilt",
        },
        "claim_ceiling": (
            "Scratch diagnostic Stage-4 cross-model readout matrix v0 only. It shows four distinct readout maps over one fixed finite Clifford-spinor support. "
            "It does not establish readout identity, canon, formal admission, IGT truth, holodeck truth, physics bridge, Axis0, or any promoted carrier claim."
        ),
        "all_pass": all_pass,
        "M": {
            "explicit_finite_probe_family": julia["M"]["explicit_finite_probe_family"],
            "matrix_shape": julia["M"]["matrix_shape"],
            "lens_order": julia["M"]["lens_order"],
            "non_overlapping_outputs": {
                "qit": ["von_neumann_entropy", "coherence_l1", "purity", "subsystem_entropy_q0"],
                "igt": ["abs(P[q0,q1]-P[q1,q0])", "abs(P[q0,q2]-P[q2,q0])", "abs(P[q1,q2]-P[q2,q1])"],
                "holodeck_runtime": ["final_accumulator_mod97", "unique_runtime_states", "threshold_step_mod11_zero", "weighted_path_sum"],
                "physics_math": ["pauli_x_q0", "pauli_y_q0", "pauli_z_q0", "clifford_grade1_norm", "density_frobenius_norm"],
            },
            "identity_assertion": False,
        },
        "C": {
            "trace_eq_1": constraints_ok and all(payload["C"]["trace_eq_1"] for payload in (julia, jax, pytorch)),
            "psd": constraints_ok and all(payload["C"]["psd"] for payload in (julia, jax, pytorch)),
            "hermitian": constraints_ok and all(payload["C"]["hermitian"] for payload in (julia, jax, pytorch)),
            "normalization": constraints_ok and all(payload["C"]["normalization"] for payload in (julia, jax, pytorch)),
            "rung_specific_constraint": julia["C"]["rung_specific_constraint"],
        },
        "S_mod_M": {
            "S": julia["S_mod_M"]["S"],
            "equivalence_relation": julia["S_mod_M"]["equivalence_relation"],
            "full_probe_class_count": julia["S_mod_M"]["full_probe_class_count"],
            "carrier_erased_class_count": julia["S_mod_M"]["carrier_erased_class_count"],
            "quotient_flip": {
                "full_to_erased_class_count": [
                    julia["S_mod_M"]["full_probe_class_count"],
                    julia["S_mod_M"]["carrier_erased_class_count"],
                ],
                "flips": julia["S_mod_M"]["full_probe_class_count"] > julia["S_mod_M"]["carrier_erased_class_count"],
            },
        },
        "readout_matrix_source": {
            "authoritative_engine": "julia",
            "rows": julia["readout_rows"],
        },
        "controls": controls,
        "control_summary": {
            "label_shuffle_delta": values_by_engine["julia"]["label_shuffle_delta"],
            "carrier_erasure_structure_norm": [
                values_by_engine["julia"]["real_structure_norm"],
                values_by_engine["julia"]["erased_structure_norm"],
            ],
            "readout_map_erasure_igt_column_structure": [
                values_by_engine["julia"]["readout_map_erasure_before"],
                values_by_engine["julia"]["readout_map_erasure_after"],
            ],
            "order_reversal_delta": values_by_engine["julia"]["order_reversal_delta"],
            "dual_smt_real_no_asymmetry_to_erased_no_asymmetry": {
                "z3": [z3_record["verdict"], z3_record["negative_control_verdict"]],
                "cvc5": [cvc5_record["verdict"], cvc5_record["negative_control_verdict"]],
            },
            "torch_func_jacrev_same_vs_cross": [
                pytorch["torch_func_jacrev"]["same_axis_jacrev"],
                pytorch["torch_func_jacrev"]["cross_axis_jacrev"],
            ],
        },
        "engine_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, values_by_engine["julia"], "authoritative_quantumoptics_cliffordalgebras"),
            "jax": engine_record(jax, JAX_RESULT, values_by_engine["jax"], "rich_mirror_dual_smt"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, values_by_engine["pytorch"], "required_third_substrate_torch_func_jacrev"),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_record["verdict"],
                "negative_control_verdict": z3_record["negative_control_verdict"],
                "version": z3_record["version"],
                "claim": jax["smt"]["claim"],
                "derive_in_solver": z3_record["real_no_asymmetry"]["derived_relation"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_record["verdict"],
                "negative_control_verdict": cvc5_record["negative_control_verdict"],
                "version": cvc5_record["version"],
                "claim": jax["smt"]["claim"],
                "derive_in_solver": cvc5_record["real_no_asymmetry"]["derived_relation"],
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "CliffordAlgebras",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": ["json", "pathlib", "hashlib", "LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": values_by_engine,
            "max_divergence": divergence_max,
            "structural_disagreements": structural_disagreements,
            "notes": [
                "The envelope compares shared scalar control summaries only; it does not assert equality of the four readout output spaces.",
                "Julia is authoritative because QuantumOptics and CliffordAlgebras carry the QIT and grade-content readouts.",
                "JAX is load-bearing for dual-SMT derive-in-solver carrier-erasure proof.",
                "PyTorch is load-bearing for torch.func.jacrev same-vs-cross readout sensitivity.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["control_summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "CROSS_MODEL_READOUT_MATRIX_V0_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"classes={result['S_mod_M']['full_probe_class_count']}->{result['S_mod_M']['carrier_erased_class_count']} "
        f"label_delta={summary['label_shuffle_delta']} "
        f"carrier_structure={summary['carrier_erasure_structure_norm']} "
        f"map_erasure={summary['readout_map_erasure_igt_column_structure']} "
        f"order_delta={summary['order_reversal_delta']} "
        f"z3={result['crossover_proofs']['z3']['verdict']}->{result['crossover_proofs']['z3']['negative_control_verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}->{result['crossover_proofs']['cvc5']['negative_control_verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
