#!/usr/bin/env python3
"""Composite envelope for foundation_r4 spinor holonomy path-integral variant.

The envelope reads completed leg receipts only after the independent legs have
run. It does not recompute the claim and does not promote this scratch rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_spinor_holonomy_path_integral_variant"
OBJECT_ID = "foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_pytorch_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from completed engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], *, result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
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
        "values": values,
    }


def values(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    return {
        "spinor_holonomy_scalar": float(summary["spinor_holonomy_scalar"]),
        "spinor_minus_identity_residual": float(summary["spinor_minus_identity_residual"]),
        "vector_holonomy_trace_half": float(summary["vector_holonomy_trace_half"]),
        "vector_plus_identity_residual": float(summary["vector_plus_identity_residual"]),
    }


def max_divergence(engine_values: dict[str, dict[str, Any]]) -> float:
    keys = ["spinor_holonomy_scalar", "vector_holonomy_trace_half"]
    diffs = []
    for key in keys:
        rows = [float(row[key]) for row in engine_values.values() if key in row]
        if rows:
            diffs.append(max(rows) - min(rows))
    return max(diffs) if diffs else 0.0


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    julia_values = values(julia)
    jax_values = values(jax)
    pytorch_values = {
        **values(pytorch),
        "jacrev_bivector_first": float(pytorch["summary"]["jacrev_bivector_first"]),
        "jacrev_bivector_max_residual": float(pytorch["summary"]["jacrev_bivector_max_residual"]),
        "finite_linearization_residual": float(pytorch["summary"]["finite_linearization_residual"]),
    }
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(engine_values)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    negative = {
        "spinor_vs_vector_holonomy_flip": bool(julia["negative_control_flip"]["spinor_vs_vector_holonomy_flip"] and jax["negative_control_flip"]["spinor_vs_vector_holonomy_flip"] and pytorch["negative_control_flip"]["spinor_vs_vector_holonomy_flip"]),
        "drop_M_coarsens_quotient": bool(julia["negative_control_flip"]["drop_M_coarsens_quotient"] and jax["negative_control_flip"]["drop_M_coarsens_quotient"] and pytorch["negative_control_flip"]["drop_M_coarsens_quotient"]),
        "z3_drop_spinor_constraint_unsat_to_sat": bool(jax["negative_control_flip"]["z3_drop_spinor_constraint_unsat_to_sat"]),
        "cvc5_drop_spinor_constraint_unsat_to_sat": bool(jax["negative_control_flip"]["cvc5_drop_spinor_constraint_unsat_to_sat"]),
        "wrong_half_angle_control_flips_to_plus_identity": bool(julia["negative_control_flip"]["wrong_half_angle_control_flips_to_plus_identity"] and jax["negative_control_flip"]["wrong_half_angle_control_flips_to_plus_identity"] and pytorch["negative_control_flip"]["wrong_half_angle_control_flips_to_plus_identity"]),
        "torch_func_jacrev_independent_sensitivity": bool(pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]),
    }
    fences_ok = all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in (julia, jax, pytorch)
    )
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and div <= TOL
        and all(negative.values())
        and fences_ok
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch foundation R4 spinor holonomy/path-integral micro-lego only: SU(2) 2pi holonomy -1 versus SO(3) vector +1. No promotion or formal admission.",
        "all_pass": all_pass,
        "M": {
            "name": "holonomy_loop_probe",
            "explicit_probe_family": ["ordered_product_spinor_SU2_loop", "ordered_product_vector_SO3_loop", "path_increment_sensitivity_probe"],
            "finite_probe_domain": {"loop_discretizations": [2, 4, 8, 16, 32, 64], "axis": "z", "loop_angle": "2pi"},
        },
        "C": {
            "trace_equals_one": "Probe states can be encoded as normalized rank-one spinor/vector projectors with trace 1.",
            "psd": "Those rank-one probe projectors are PSD.",
            "hermiticity": "Probe projectors are Hermitian; the exact SMT step matrices are real signed-permutation representations.",
            "normalization": "Spinor rotors are unit norm; SO(3) steps are orthogonal; path increments sum to 2pi.",
            "rung_specific_constraint": "Spinor/SU(2) half-angle double-cover structure for the ordered loop product.",
        },
        "S_mod_M": {
            "definition": "Equivalence classes under probe-indistinguishability by the holonomy-loop probe.",
            "spinor_SU2_class": "2pi_holonomy_minus_identity",
            "vector_SO3_class": "2pi_holonomy_plus_identity",
            "with_M_classes": 2,
            "drop_M_classes": 1,
        },
        "holonomy_values": {
            "spinor_holonomy": -1.0,
            "vector_holonomy": 1.0,
            "julia_spinor_scalar": julia_values["spinor_holonomy_scalar"],
            "jax_spinor_scalar": jax_values["spinor_holonomy_scalar"],
            "pytorch_spinor_scalar": pytorch_values["spinor_holonomy_scalar"],
            "julia_vector_trace_half": julia_values["vector_holonomy_trace_half"],
            "jax_vector_trace_half": jax_values["vector_holonomy_trace_half"],
            "pytorch_vector_trace_half": pytorch_values["vector_holonomy_trace_half"],
            "path_integral_discretization_convergence": julia["summary"]["discretization_convergence"],
            "vector_control_convergence": julia["summary"]["vector_control_convergence"],
        },
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, result_path=JULIA_RESULT, values=julia_values),
            "jax": engine_record(jax, result_path=JAX_RESULT, values=jax_values),
            "pytorch": engine_record(pytorch, result_path=PYTORCH_RESULT, values=pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["z3"]["negative_control_verdict"],
                "erase_flip_verdict": jax["crossover_proofs"]["z3"]["erase_flip_verdict"],
                "vector_control_verdict": jax["smt"]["z3"]["vector_plus_identity_status"],
                "claim": "Given bound N=2 spinor step entries, z3 derives step^2 = -I; asserting not -I is UNSAT. Erasing the spinor step binding flips to SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "erase_flip_verdict": jax["crossover_proofs"]["cvc5"]["erase_flip_verdict"],
                "vector_control_verdict": jax["smt"]["cvc5"]["vector_plus_identity_status"],
                "claim": "cvc5 agrees with z3 over the same in-solver ordered matrix product.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["spinor_negated_claim_status"],
                "erase_flip_verdict": julia["julia_z3"]["drop_spinor_step_binding_status"],
                "vector_control_verdict": julia["julia_z3"]["vector_plus_identity_status"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": ["LinearAlgebra", "json", "pathlib", "math"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": div,
            "notes": [
                "Julia is authoritative for the CliffordAlgebras rotor product.",
                "JAX supplies z3+cvc5 exact structural proof over ordered matrix products.",
                "PyTorch supplies a genuine torch.func.jacrev sensitivity check; it is not exact algebra authority.",
            ],
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
        "FOUNDATION_R4_SPINOR_HOLONOMY_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"spinor={result['holonomy_values']['julia_spinor_scalar']} "
        f"vector={result['holonomy_values']['julia_vector_trace_half']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
