#!/usr/bin/env python3

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_j3o_jordan"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_j3o_jordan_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r3_j3o_jordan_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_pytorch_results.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": payload.get("values", {}),
        "M": payload.get("M", {}),
        "C": payload.get("C", {}),
        "quotient": payload.get("quotient", {}),
    }


def max_abs_diff(left: dict[str, Any], right: dict[str, Any], keys: list[str]) -> float:
    diffs = [abs(float(left[key]) - float(right[key])) for key in keys if key in left and key in right]
    return max(diffs) if diffs else 0.0


def main() -> int:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    jv = julia["values"]
    xv = jax["values"]
    pv = pytorch["values"]

    shared_keys = [
        "jordan_identity_residual_norm",
        "jordan_identity_residual_max_abs",
        "raw_control_residual_norm",
        "raw_control_residual_max_abs",
        "formal_reality_trace_sum_squares",
        "primitive_idempotent_trace",
        "primitive_idempotent_square_residual",
        "nonhermitian_control_norm",
        "nonhermitian_control_square_norm",
    ]
    max_divergence = max_abs_diff(jv, xv, shared_keys)
    z3_proof = jax["smt_structural_proof"]["z3"]
    cvc5_proof = jax["smt_structural_proof"]["cvc5"]
    z3_verdict = z3_proof["verdict"]
    cvc5_verdict = cvc5_proof["verdict"]
    control_z3 = z3_proof["control_verdict"]
    control_cvc5 = cvc5_proof["control_verdict"]

    negative = {
        "non_jordan_product_identity_flip": bool(julia["negative_control_flip"]["non_jordan_product_identity_flip"]),
        "drop_hermiticity_formal_reality_flip": bool(julia["negative_control_flip"]["drop_hermiticity_formal_reality_flip"]),
        "julia_z3_raw_product_zero_negative_unsat": bool(julia["negative_control_flip"]["z3_raw_product_zero_negative_unsat"]),
        "smt_non_jordan_control_sat": bool(jax["negative_control_flip"]["non_jordan_product_control_sat"]),
        "smt_erase_jordan_product_flip": bool(jax["negative_control_flip"]["drop_jordan_product_constraint_flip"]),
        "torch_jacrev_deformation_flip": bool(pytorch["negative_control_flip"]["flipped"]),
    }
    negative["flipped"] = all(negative.values())

    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and max_divergence <= 1.0e-10
        and z3_verdict == cvc5_verdict == "unsat"
        and control_z3 == control_cvc5 == "sat"
        and negative["flipped"]
    )

    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": RUNG_ID,
        "rebuild_version": "v2",
        "classification": "scratch_diagnostic",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation rung for the observable side of octonionic non-associativity: "
            "J3(O) as a finite Hermitian Jordan-algebra probe only. No promotion, formal "
            "admission, bridge, basin, or axis-level claim."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "J3(O) Jordan identity and formal-reality probe family",
            "finite_probe_family": [
                "A,B: explicit Hermitian 3x3 octonionic observable probes with fixed finite entries",
                "P: trace-1 primitive positive/idempotent J3(O) state probe",
                "QuantumOptics diagonal PSD state probe with spectrum [0, 1/2, 1/2]",
                "SMT representative component of (A o B) o (A o A) - A o (B o (A o A))",
                "formal-reality trace tr(A o A + B o B)",
                "negative controls: raw non-Jordan product, non-Hermitian square-zero matrix, SMT Jordan-product erasure, torch product deformation",
            ],
            "observable_dimension": 27,
            "smt_scope": jax["smt_structural_proof"]["scope"],
            "smt_representative_component": z3_proof["representative_component"],
        },
        "C": {
            "constraints": [
                "trace=1 on P",
                "PSD/positive-cone witness by P o P = P and QuantumOptics nonnegative diagonal spectrum",
                "Hermiticity by octonionic conjugate transpose for A,B,P",
                "normalization by fixed finite integer-coordinate probe family and no peer-result reads",
                "rung-specific Jordan product X o Y = (XY + YX)/2",
                "SMT binds A/B entries and derives the residual from octonion structure constants inside each solver",
            ],
            "admissible_state_probe": {
                "trace": jv["primitive_idempotent_trace"],
                "idempotent_residual": jv["primitive_idempotent_square_residual"],
                "quantumoptics_trace": jv["quantumoptics_state_trace"],
                "quantumoptics_min_eigenvalue": jv["quantumoptics_state_min_eigenvalue"],
            },
        },
        "quotient_summary": {
            "symbol": "S/~_M",
            "rule": "structures are equivalent only when the finite Hermiticity, normalized positive/idempotent, formal-reality, Jordan-identity, and SMT residual probes agree",
            "J3O_class": "observable layer keeps the Jordan identity and formal-reality probes",
            "separated_controls": [
                "raw non-Jordan product: SAT for representative identity failure",
                "drop Hermiticity: nonzero square-zero control breaks formal-reality",
                "erase/drop Jordan product constraint: UNSAT becomes SAT for the same representative SMT component",
                "torch deformation: jacrev detects nonzero sensitivity away from the Jordan product",
            ],
        },
        "key_values": {
            "julia_jordan_identity_residual_norm": jv["jordan_identity_residual_norm"],
            "julia_raw_control_residual_norm": jv["raw_control_residual_norm"],
            "formal_reality_trace_sum_squares": jv["formal_reality_trace_sum_squares"],
            "primitive_idempotent_trace": jv["primitive_idempotent_trace"],
            "primitive_idempotent_square_residual": jv["primitive_idempotent_square_residual"],
            "nonhermitian_square_zero_norm": jv["nonhermitian_control_square_norm"],
            "smt_representative_component": z3_proof["representative_component"],
            "smt_selected_jordan_component": xv["selected_smt_jordan_residual_component"],
            "smt_selected_raw_component": xv["selected_smt_raw_residual_component"],
            "smt_jordan_identity_verdict": z3_verdict,
            "smt_non_jordan_control_verdict": control_z3,
            "torch_jacrev_gradient_mid": pv["jacrev_gradient_at_theta_0_5"],
        },
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": "negated representative Jordan identity component derived from bound J3(O) entries is unsatisfiable",
                "control_verdict": control_z3,
                "drop_jordan_product_constraint_verdict": z3_proof["drop_jordan_product_constraint_verdict"],
                "representative_component": z3_proof["representative_component"],
                "bound_entry_equalities": z3_proof["bound_entry_equalities"],
                "octonion_nonzero_structure_constants": z3_proof["octonion_nonzero_structure_constants"],
                "computed_entry_bindings": jax["computed_entry_bindings"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": "negated representative Jordan identity component derived from bound J3(O) entries is unsatisfiable",
                "control_verdict": control_cvc5,
                "drop_jordan_product_constraint_verdict": cvc5_proof["drop_jordan_product_constraint_verdict"],
                "representative_component": cvc5_proof["representative_component"],
                "bound_entry_equalities": cvc5_proof["bound_entry_equalities"],
                "octonion_nonzero_structure_constants": cvc5_proof["octonion_nonzero_structure_constants"],
                "computed_entry_bindings": jax["computed_entry_bindings"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["z3_julia_admissibility_gate"]["positive_admissibility_status"],
                "negative_control_verdict": julia["z3_julia_admissibility_gate"]["raw_product_zero_negative_status"],
                "claim": "Julia Z3.jl admissibility/control gate over Julia-computed J3(O) values",
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "CliffordAlgebras",
            "Z3",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": ["json", "pathlib", "LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {
                    "jordan_identity_residual_norm": jv["jordan_identity_residual_norm"],
                    "raw_control_residual_norm": jv["raw_control_residual_norm"],
                    "formal_reality_trace_sum_squares": jv["formal_reality_trace_sum_squares"],
                    "primitive_idempotent_trace": jv["primitive_idempotent_trace"],
                },
                "jax": {
                    "jordan_identity_residual_norm": xv["jordan_identity_residual_norm"],
                    "raw_control_residual_norm": xv["raw_control_residual_norm"],
                    "formal_reality_trace_sum_squares": xv["formal_reality_trace_sum_squares"],
                    "primitive_idempotent_trace": xv["primitive_idempotent_trace"],
                },
                "pytorch": {
                    "theta_0_jordan_identity_residual_squared": pv["theta_0_jordan_identity_residual_squared"],
                    "theta_1_raw_identity_residual_squared": pv["theta_1_raw_identity_residual_squared"],
                    "jacrev_gradient_at_theta_0_5": pv["jacrev_gradient_at_theta_0_5"],
                },
            },
            "max_divergence": max_divergence,
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent leg receipts"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result paths"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"rung={RUNG_ID} all_pass={all_pass} "
        f"z3={z3_verdict} cvc5={cvc5_verdict} "
        f"control={control_z3} max_divergence={max_divergence}"
    )
    print(f"wrote: {RESULT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
