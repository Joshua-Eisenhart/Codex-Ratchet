#!/usr/bin/env python3
"""Composite envelope for foundation_r3_associator_xhigh.

The envelope reads completed Julia, JAX, and PyTorch leg receipts after the
legs have run. It does not recompute the engine legs or promote the rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_associator_xhigh"
CANONICAL_RUNG_ID = "foundation_r3_associator"
OBJECT_ID = "foundation_r3_associator_xhigh_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_xhigh_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r3_associator_xhigh_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_pytorch_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed engine receipts; not part of the algebra claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for source and result receipts",
    },
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


def summary_values(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    return {
        "H_associator_max_norm": float(summary["H_associator_max_norm"]),
        "O_associator_max_norm": float(summary["O_associator_max_norm"]),
        "O_witness_basis_indices": summary["O_witness_basis_indices"],
        "O_witness_vector": summary["O_witness_vector"],
    }


def max_divergence(values: dict[str, dict[str, Any]]) -> float:
    keys = ["H_associator_max_norm", "O_associator_max_norm"]
    diffs: list[float] = []
    for key in keys:
        rows = [float(row[key]) for row in values.values() if key in row]
        if rows:
            diffs.append(max(rows) - min(rows))
    return max(diffs) if diffs else 0.0


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = summary_values(julia)
    jax_values = summary_values(jax)
    pytorch_values = {
        **summary_values(pytorch),
        "jacrev_alpha_0": float(pytorch["summary"]["jacrev_alpha_0"]),
        "jacrev_alpha_1": float(pytorch["summary"]["jacrev_alpha_1"]),
        "energy_alpha_0": float(pytorch["differentiable_associator_selector"]["energy_alpha_0"]),
        "energy_alpha_1": float(pytorch["differentiable_associator_selector"]["energy_alpha_1"]),
    }
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(engine_values)

    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    negative = {
        "H_to_O_flip": bool(julia["negative_control_flip"]["H_to_O_flip"] and jax["negative_control_flip"]["H_to_O_flip"] and pytorch["negative_control_flip"]["H_to_O_flip"]),
        "drop_M_coarsens_O_witness_quotient": bool(
            julia["negative_control_flip"]["drop_M_coarsens_O_witness_quotient"]
            and jax["negative_control_flip"]["drop_M_coarsens_O_witness_quotient"]
            and pytorch["negative_control_flip"]["drop_M_coarsens_O_witness_quotient"]
        ),
        "z3_O_all_zero_unsat_to_erased_sat": bool(jax["negative_control_flip"]["O_drop_zero_constraint_unsat_to_sat"]),
        "cvc5_O_all_zero_unsat_to_erased_sat": bool(jax["negative_control_flip"]["O_drop_zero_constraint_unsat_to_sat"]),
        "H_all_zero_smt_sat": bool(jax["negative_control_flip"]["H_all_zero_sat"]),
        "O_all_zero_smt_unsat": bool(jax["negative_control_flip"]["O_all_zero_unsat"]),
        "torch_jacrev_sensitivity_grows": bool(pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]),
    }
    same_witness = (
        julia_values["O_witness_basis_indices"]
        == jax_values["O_witness_basis_indices"]
        == pytorch_values["O_witness_basis_indices"]
    )
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
        and same_witness
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
        "canonical_rung_id": CANONICAL_RUNG_ID,
        "hardening_variant": "xhigh_v3_solver_derived_associator",
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation R3 associator rung only: bracketing distinguishability "
            "under the associator probe for H versus O. No promotion, no formal "
            "admission, no adjacent foundation rung, no bridge/manifold/axis claim."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "bracketing_distinguishability_probe",
            "explicit_probe_family": ["associator[A,B,C] = (AB)C - A(BC)"],
            "finite_probe_domain": "basis triples in H and O; PyTorch differentiates the computed O witness triple",
            "witness_probe": {
                "algebra": "O",
                "basis_triple": julia_values["O_witness_basis_indices"],
                "associator_vector": julia_values["O_witness_vector"],
            },
        },
        "C": {
            "trace_one": "basis probes are represented as rank-one coordinate projectors rho=|e_i><e_i| with trace 1",
            "psd": "rank-one coordinate projectors are positive semidefinite",
            "hermitian": "rank-one coordinate projectors are real symmetric/Hermitian",
            "normalization": "basis probes have unit norm; Julia also samples norm multiplicativity",
            "rung_specific_constraint": "normed division algebra multiplication/structure constants with H associative and O alternative non-associative",
            "construction_limit": "Julia O is Cayley-Dickson doubled from the package-derived CliffordAlgebras H table; no package-native octonion type was available/used.",
            "finite_projector_checks": julia["C"]["finite_projector_checks"],
            "SMT_binding": "z3/cvc5 Real table variables T[k,i,j] are asserted equal to computed Cayley-Dickson entries; associators are expanded from T inside the solvers",
        },
        "S_mod_M": {
            "definition": "(AB)C ~_M A(BC) iff associator[A,B,C] is zero",
            "H_bracketing_classes_under_M": julia["S_mod_M"]["class_counts"]["H_bracketing_classes_under_M"],
            "O_witness_bracketing_classes_under_M": julia["S_mod_M"]["class_counts"]["O_witness_bracketing_classes_under_M"],
            "drop_M_bracketing_classes": julia["S_mod_M"]["class_counts"]["drop_M_bracketing_classes"],
            "interpretation": "H bracketings are indistinguishable under M; the O witness bracketings are distinguishable; erasing M coarsens the quotient.",
        },
        "associator_values": {
            "H_associator_max_norm": julia_values["H_associator_max_norm"],
            "O_associator_max_norm": julia_values["O_associator_max_norm"],
            "O_witness_basis_indices": julia_values["O_witness_basis_indices"],
            "O_witness_vector": julia_values["O_witness_vector"],
            "O_nonzero_basis_triple_count": julia["summaries"]["O"]["associator"]["nonzero_basis_triple_count"],
        },
        "structural_facts": {
            "O_alternativity": julia["summaries"]["O"]["alternativity"],
            "O_antisymmetry": julia["summaries"]["O"]["antisymmetry"],
            "SMT_derives_associator_from_table_entries": {
                "z3_O": jax["smt"]["z3"]["O"]["derivation"],
                "cvc5_O": jax["smt"]["cvc5"]["O"]["derivation"],
                "asserted_precomputed_associator_coefficients": {
                    "z3": jax["smt"]["z3"]["O"]["asserted_precomputed_associator_coefficients"],
                    "cvc5": jax["smt"]["cvc5"]["O"]["asserted_precomputed_associator_coefficients"],
                    "julia_z3": julia["julia_z3"]["O"]["asserted_precomputed_associator_coefficients"],
                },
                "bound_table_entry_equalities": {
                    "z3_O": jax["smt"]["z3"]["O"]["bound_table_entry_equalities"],
                    "cvc5_O": jax["smt"]["cvc5"]["O"]["bound_table_entry_equalities"],
                    "julia_z3_O": julia["julia_z3"]["O"]["bound_table_entry_equalities"],
                },
                "derived_assoc_component_count": {
                    "z3_O": jax["smt"]["z3"]["O"]["derived_assoc_component_count"],
                    "cvc5_O": jax["smt"]["cvc5"]["O"]["derived_assoc_component_count"],
                    "julia_z3_O": julia["julia_z3"]["O"]["derived_assoc_component_count"],
                },
            },
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
                "H_all_zero_verdict": jax["crossover_proofs"]["z3"]["H_all_zero_verdict"],
                "claim": "Given bound computed O Cayley-Dickson table entries, z3 derives all basis-triple associator components in solver; asserting they are all zero is UNSAT, erasing that zero constraint is SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "H_all_zero_verdict": jax["crossover_proofs"]["cvc5"]["H_all_zero_verdict"],
                "claim": "Independent cvc5 check derives the same associator components from bound O table entries and agrees with z3.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["O"]["all_coefficients_zero_status"],
                "negative_control_verdict": julia["julia_z3"]["O"]["drop_zero_constraint_status"],
            },
        },
        "claim_path_tools": [
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
            "engine_values": engine_values,
            "max_divergence": div,
            "same_witness": same_witness,
            "notes": [
                "Julia is authoritative for H via CliffordAlgebras and O via Cayley-Dickson over that package H table.",
                "JAX supplies the dual-SMT structural proof by deriving associator components from bound Cayley-Dickson table entries.",
                "PyTorch supplies the torch.func.jacrev associator-energy sensitivity, not exact algebra authority.",
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
        "FOUNDATION_R3_ASSOCIATOR_XHIGH_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"H_norm={result['associator_values']['H_associator_max_norm']} "
        f"O_norm={result['associator_values']['O_associator_max_norm']} "
        f"O_witness={result['associator_values']['O_witness_basis_indices']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
