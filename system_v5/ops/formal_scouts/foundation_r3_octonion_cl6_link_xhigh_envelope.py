#!/usr/bin/env python3
"""Composite three-engine envelope for foundation_r3_octonion_cl6_link_xhigh v2."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


OBJECT_ID = "foundation_r3_octonion_cl6_link_xhigh"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_octonion_cl6_link_xhigh_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r3_octonion_cl6_link_xhigh_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly after standalone engine receipts were written",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for engine receipts",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def shared_values(payload: dict[str, Any]) -> dict[str, float]:
    summary = payload["summary"]
    return {
        "octonion_cl6_rank": float(summary["octonion_cl6_rank"]),
        "octonion_all7_matrix_rank": float(summary["octonion_all7_matrix_rank"]),
        "octonion_spinor_dim": float(summary["octonion_spinor_dim"]),
        "quaternion_cl2_rank": float(summary["quaternion_cl2_rank"]),
        "quaternion_all3_matrix_rank": float(summary["quaternion_all3_matrix_rank"]),
        "quaternion_spinor_dim": float(summary["quaternion_spinor_dim"]),
        "octonion_anticommutation_max_residual": float(summary["octonion_anticommutation_max_residual"]),
        "quaternion_anticommutation_max_residual": float(summary["quaternion_anticommutation_max_residual"]),
        "pseudoscalar_link_plus_residual": float(summary["pseudoscalar_link_plus_residual"]),
        "full_quotient_class_count": float(summary["full_quotient_class_count"]),
        "coarse_quotient_class_count": float(summary["coarse_quotient_class_count"]),
    }


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str], role: str) -> dict[str, Any]:
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
        "role": role,
        "all_pass": payload["all_pass"],
        "values": shared_values(payload),
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    keys = sorted(next(iter(values.values())).keys())
    max_seen = 0.0
    for key in keys:
        rows = [engine_values[key] for engine_values in values.values()]
        max_seen = max(max_seen, max(rows) - min(rows))
    return max_seen


def same_contract_flags(*payloads: dict[str, Any]) -> bool:
    return all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in payloads
    )


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}
    engine_values = {name: shared_values(payload) for name, payload in payloads.items()}
    divergence_max = max_divergence(engine_values)

    julia_z3 = julia["julia_z3_clifford_proof"]
    z3 = jax["smt"]["z3"]
    cvc5 = jax["smt"]["cvc5"]

    negative_control_flip = {
        "quaternion_H_control": {
            "octonion_rank": julia["summary"]["octonion_cl6_rank"],
            "quaternion_rank": julia["summary"]["quaternion_cl2_rank"],
            "octonion_spinor_dim": julia["summary"]["octonion_spinor_dim"],
            "quaternion_spinor_dim": julia["summary"]["quaternion_spinor_dim"],
            "flips": julia["summary"]["octonion_cl6_rank"] != julia["summary"]["quaternion_cl2_rank"],
        },
        "drop_dimension_and_rank_probe": julia["quotient"]["coarsening_flip"],
        "smt_erase_L_entry_binding_flip": {
            "z3_with_L_entry_bindings": z3["verdict"],
            "z3_after_erasing_L_entry_bindings": z3["erase_L_entry_binding_flip"]["status"],
            "cvc5_with_L_entry_bindings": cvc5["verdict"],
            "cvc5_after_erasing_L_entry_bindings": cvc5["erase_L_entry_binding_flip"]["status"],
            "flips": z3["verdict"] != z3["erase_L_entry_binding_flip"]["status"]
            and cvc5["verdict"] != cvc5["erase_L_entry_binding_flip"]["status"],
        },
        "wrong_sign_plus_I_control": {
            "z3_violation_verdict": z3["wrong_sign_plus_I_violation_control"]["status"],
            "cvc5_violation_verdict": cvc5["wrong_sign_plus_I_violation_control"]["status"],
            "flips_against_correct_violation": z3["verdict"] != z3["wrong_sign_plus_I_violation_control"]["status"]
            and cvc5["verdict"] != cvc5["wrong_sign_plus_I_violation_control"]["status"],
        },
        "torch_func_normalization_sensitivity": {
            "jacobian_frobenius_norm": pytorch["summary"]["jacobian_frobenius_norm"],
            "self_diagonal_sensitivities": pytorch["summary"]["self_diagonal_sensitivities"],
            "genuine_independent_check": True,
        },
    }

    all_pass = bool(
        all(payload["all_pass"] is True for payload in payloads.values())
        and same_contract_flags(julia, jax, pytorch)
        and divergence_max == 0.0
        and z3["verdict"] == cvc5["verdict"] == "unsat"
        and z3["offdiag_pair_violation"]["status"] == cvc5["offdiag_pair_violation"]["status"] == "unsat"
        and z3["self_square_violation"]["status"] == cvc5["self_square_violation"]["status"] == "unsat"
        and z3["erase_L_entry_binding_flip"]["status"] == cvc5["erase_L_entry_binding_flip"]["status"] == "sat"
        and z3["wrong_sign_plus_I_violation_control"]["status"] == cvc5["wrong_sign_plus_I_violation_control"]["status"] == "sat"
        and julia_z3["verdict"] == "unsat"
        and negative_control_flip["quaternion_H_control"]["flips"]
        and negative_control_flip["drop_dimension_and_rank_probe"]["flips"]
        and negative_control_flip["smt_erase_L_entry_binding_flip"]["flips"]
        and negative_control_flip["wrong_sign_plus_I_control"]["flips_against_correct_violation"]
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "codex_ratchet.three_engine_sim_result.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "envelope_controller",
        "executable": sys.executable,
        "reads_peer_result": False,
        "reads_engine_result_jsons": True,
        "reads_peer_result_note": "Engine legs have reads_peer_result=false. This envelope only reads completed leg receipts after standalone execution.",
        "claim_ceiling": "Strict scratch foundation rung only: octonion Cayley-Dickson left-multiplication operators link to the finite Cl(0,6) spinor carrier. No formal admission, no promotion, no physics claim.",
        "all_pass": all_pass,
        "M": {
            "name": "finite octonion left-multiplication / anticommutator probe family",
            "operators": ["L_e1", "L_e2", "L_e3", "L_e4", "L_e5", "L_e6", "L_e7"],
            "probe_entries": "<basis_a | (L_ei L_ej + L_ej L_ei) | basis_b> for i,j=1..7 and a,b=1..8",
            "pair_probe_count": 49,
            "entry_probe_count": 49 * 8 * 8,
            "observable_realization": "Julia QuantumOptics NLevelBasis(8) operators i*L_ei are Hermitian finite observables",
            "quotient_discriminators": ["generator_count", "carrier_dimension", "anticommutation_signature", "generated_clifford_rank", "spinor_dimension"],
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "rung_specific_constraints": [
                "Cayley-Dickson octonion multiplication table",
                "L_ei^T = -L_ei",
                "L_ei L_ej + L_ej L_ei = -2 delta_ij I",
                "first six L_ei generate a 64-dimensional Cl(0,6) matrix image on an 8-dimensional spinor",
                "L_e1 L_e2 L_e3 L_e4 L_e5 L_e6 = L_e7 pseudoscalar-link residual is zero",
            ],
            "density_constraint_witness": julia["C"]["density_constraint_witness"],
        },
        "quotient_summary": {
            "S": julia["quotient"]["S"],
            "equivalence_relation": julia["quotient"]["equivalence_relation"],
            "full_probe_signatures": julia["quotient"]["full_probe_signatures"],
            "coarse_probe_signatures_after_dropping_dimension_and_rank": julia["quotient"]["coarse_probe_signatures_after_dropping_dimension_and_rank"],
            "full_probe_class_count": julia["quotient"]["full_probe_class_count"],
            "drop_dimension_and_rank_probe_class_count": julia["quotient"]["drop_dimension_and_rank_probe_class_count"],
            "octonion_class": julia["quotient"]["octonion_class"],
            "quaternion_control_class": julia["quotient"]["quaternion_control_class"],
        },
        "negative_control_flip": negative_control_flip,
        "engine_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
        },
        "engines": {
            "julia": engine_record(
                julia,
                JULIA_RESULT,
                packages_used=["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
                load_bearing=["QuantumOptics", "CliffordAlgebras", "Z3"],
                role="authoritative",
            ),
            "jax": engine_record(
                jax,
                JAX_RESULT,
                packages_used=["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
                load_bearing=["z3", "cvc5"],
                role="dual_smt_structural_proof",
            ),
            "pytorch": engine_record(
                pytorch,
                PYTORCH_RESULT,
                packages_used=["torch", "torch.func", "json", "hashlib", "pathlib"],
                load_bearing=["torch.func"],
                role="differentiable_sensitivity_check",
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3["verdict"],
                "offdiag_violation_verdict": z3["offdiag_pair_violation"]["status"],
                "self_square_violation_verdict": z3["self_square_violation"]["status"],
                "erase_flip_verdict": z3["erase_L_entry_binding_flip"]["status"],
                "wrong_sign_control_verdict": z3["wrong_sign_plus_I_violation_control"]["status"],
                "claim": "All-entry Real SMT proof: a Clifford-relation violation over bound octonion L entries is UNSAT; erasing L-entry bindings and wrong-sign +2I violation controls are SAT.",
                "version": z3["version"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5["verdict"],
                "offdiag_violation_verdict": cvc5["offdiag_pair_violation"]["status"],
                "self_square_violation_verdict": cvc5["self_square_violation"]["status"],
                "erase_flip_verdict": cvc5["erase_L_entry_binding_flip"]["status"],
                "wrong_sign_control_verdict": cvc5["wrong_sign_plus_I_violation_control"]["status"],
                "claim": "Independent cvc5 all-entry Real SMT mirror of the z3 in-solver matrix-product proof.",
                "version": cvc5["version"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "erase_flip_verdict": julia_z3["erase_L_entry_binding_flip"]["status"],
                "wrong_sign_control_verdict": julia_z3["wrong_sign_plus_I_violation_control"]["status"],
                "claim": "Julia Z3.jl derives the same anticommutator entries from bound integer L entries; Real dual-SMT authority is in the JAX leg.",
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
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": divergence_max,
            "notes": [
                "Shared finite ranks, spinor dimensions, quotient counts, and residuals agree across Julia, JAX, and PyTorch.",
                "PyTorch additionally contributes torch.func.jacrev sensitivity, not a mirror-only scalar.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"octonion_cl6_rank={result['quotient_summary']['octonion_class']['generated_rank']} "
        f"quaternion_cl2_rank={result['quotient_summary']['quaternion_control_class']['generated_rank']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"wrong_sign_z3={result['crossover_proofs']['z3']['wrong_sign_control_verdict']} "
        f"wrong_sign_cvc5={result['crossover_proofs']['cvc5']['wrong_sign_control_verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
