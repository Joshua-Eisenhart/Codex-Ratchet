#!/usr/bin/env python3
"""Composite envelope for foundation_r3_associator_high."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_high_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_high_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r3_associator_high_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_high_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_high_pytorch_results.json"
OBJECT_ID = "foundation_r3_associator_high"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-9


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str], authority: str) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "authority": authority,
        "values": {
            "H_associator_max_norm": float(payload["values"]["H"]["associator_max_norm"]),
            "O_associator_max_norm": float(payload["values"]["O"]["associator_max_norm"]),
            "O_witness": payload["values"]["O"]["witness"],
            "H_quotient_class_count": payload["quotient"]["H_quotient_class_count"],
            "O_quotient_class_count": payload["quotient"]["O_quotient_class_count"],
        },
    }


def max_diff(*values: float) -> float:
    return max(values) - min(values)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    z3_o = jax["smt_structural_proof"]["z3"]["O_all_zero"]["status"]
    cvc5_o = jax["smt_structural_proof"]["cvc5"]["O_all_zero"]["status"]
    z3_erased = jax["smt_structural_proof"]["z3"]["O_drop_all_zero_constraint"]["status"]
    cvc5_erased = jax["smt_structural_proof"]["cvc5"]["O_drop_all_zero_constraint"]["status"]
    z3_h = jax["smt_structural_proof"]["z3"]["H_all_zero"]["status"]
    cvc5_h = jax["smt_structural_proof"]["cvc5"]["H_all_zero"]["status"]

    h_values = [
        float(julia["values"]["H"]["associator_max_norm"]),
        float(jax["values"]["H"]["associator_max_norm"]),
        float(pytorch["values"]["H"]["associator_max_norm"]),
    ]
    o_values = [
        float(julia["values"]["O"]["associator_max_norm"]),
        float(jax["values"]["O"]["associator_max_norm"]),
        float(pytorch["values"]["O"]["associator_max_norm"]),
    ]
    max_divergence = max(max_diff(*h_values), max_diff(*o_values))
    engine_fences_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in (julia, jax, pytorch)
    )
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and engine_fences_ok
        and z3_o == cvc5_o == "unsat"
        and z3_h == cvc5_h == "sat"
        and z3_erased == cvc5_erased == "sat"
        and max_divergence <= TOL
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "controller_reads_engine_results_after_lanes": True,
        "claim_ceiling": "Scratch R3 bracketing-associator foundation rung only. No formal admission, no promotion, no bridge, no axis-level claim.",
        "all_pass": all_pass,
        "M_probe_family": {
            "id": "basis_triple_associator_coordinates",
            "observable": "[A,B,C]=(AB)C-A(BC)",
            "finite_family": {"H_basis_triples": 4**3, "O_basis_triples": 8**3},
            "indistinguishability_rule": "two bracketings are equivalent iff all associator coordinate probes vanish",
        },
        "C_constraints": {
            "domain": "finite real normed division algebra structure constants through H and O",
            "unit": "e0 is the two-sided identity",
            "normalization": "basis units have unit norm; imaginary units square to -e0",
            "rung_specific": "computed associator coefficients decide bracketing distinguishability",
            "density_matrix_constraints_applicable": False,
            "density_matrix_note": "trace=1, PSD, and Hermiticity are not the carrier constraints for this algebraic rung",
        },
        "quotient_summary": {
            "definition": "(AB)C ~ A(BC) iff associator == 0 under M",
            "H": {"associator_max_norm": h_values[0], "class_count": 1, "status": "bracketings_indistinguishable"},
            "O": {"associator_max_norm": o_values[0], "class_count": 2, "status": "bracketings_distinguishable", "witness": julia["values"]["O"]["witness"]},
        },
        "negative_control_flip": {
            "H_to_O_structure_flip": {
                "pass": h_values[0] <= TOL and o_values[0] > TOL,
                "H_associator_max_norm": h_values[0],
                "O_associator_max_norm": o_values[0],
            },
            "SMT_zero_associator_constraint": {
                "pass": z3_o == cvc5_o == "unsat" and z3_erased == cvc5_erased == "sat",
                "H_all_zero_status": z3_h,
                "O_all_zero_status": z3_o,
                "O_drop_all_zero_constraint_status": z3_erased,
            },
            "torch_selector_erasure": pytorch["negative_control"]["selector_erasure_flip"],
        },
        "structural_facts": {
            "O_alternativity": julia["structure_checks"]["O_alternativity"],
            "O_associator_antisymmetry": julia["structure_checks"]["O_associator_antisymmetry"],
            "O_power_associativity": julia["structure_checks"]["O_power_associativity"],
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["CliffordAlgebras", "Z3", "JSON", "LinearAlgebra", "Dates"], ["CliffordAlgebras", "Z3"], "authoritative"),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib"], ["z3", "cvc5"], "structural_smt_mirror"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, ["torch", "torch.func", "json"], ["torch.func"], "differentiable_support"),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_o,
                "claim": "All-zero octonion associator claim over computed coefficients is UNSAT.",
                "H_all_zero_verdict": z3_h,
                "negative_control_verdict": z3_erased,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_o,
                "claim": "Independent cvc5 check for the same all-zero octonion associator claim.",
                "H_all_zero_verdict": cvc5_h,
                "negative_control_verdict": cvc5_erased,
            },
            "julia_z3": {
                **julia["finite_certificates"]["julia_z3"],
                "verdict": julia["finite_certificates"]["julia_z3"]["O_all_zero_status"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"H_associator_max_norm": h_values[0], "O_associator_max_norm": o_values[0]},
                "jax": {"H_associator_max_norm": h_values[1], "O_associator_max_norm": o_values[1]},
                "pytorch": {"H_associator_max_norm": h_values[2], "O_associator_max_norm": o_values[2]},
            },
            "max_divergence": max_divergence,
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive result-envelope assembly only"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"H_assoc={result['quotient_summary']['H']['associator_max_norm']} "
        f"O_assoc={result['quotient_summary']['O']['associator_max_norm']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
