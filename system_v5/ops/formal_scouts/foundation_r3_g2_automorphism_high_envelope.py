#!/usr/bin/env python3
"""Composite envelope for foundation_r3_g2_automorphism_high."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_g2_automorphism_high_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r3_g2_automorphism_high_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_pytorch_results.json"
OBJECT_ID = "foundation_r3_g2_automorphism_high"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
EXPECTED_LADDER = {"R": 0, "C": 0, "H": 3, "O": 14}


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
            "derivation_dimensions": payload["quotient"]["class_dimensions"],
            "O_constraint_rank": payload["values"]["O"]["constraint_rank"],
            "O_probe_count": payload["values"]["O"]["probe_count"],
            "O_variable_count": payload["values"]["O"]["variable_count"],
            "O_commutative_projection_control_dim": payload["values"]["O_commutative_projection_control"]["derivation_dimension"],
        },
    }


def max_dim_divergence(*records: dict[str, int]) -> int:
    max_seen = 0
    for key in ("R", "C", "H", "O"):
        vals = [int(record[key]) for record in records]
        max_seen = max(max_seen, max(vals) - min(vals))
    return max_seen


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    julia_dims = {k: int(v) for k, v in julia["quotient"]["class_dimensions"].items()}
    jax_dims = {k: int(v) for k, v in jax["quotient"]["class_dimensions"].items()}
    pytorch_dims = {k: int(v) for k, v in pytorch["quotient"]["class_dimensions"].items()}

    z3_o = jax["smt_structural_proof"]["z3"]["all_g2_generators_leibniz_negation"]["status"]
    cvc5_o = jax["smt_structural_proof"]["cvc5"]["all_g2_generators_leibniz_negation"]["status"]
    z3_erased = jax["smt_structural_proof"]["z3"]["drop_D00_binding_flip"]["status"]
    cvc5_erased = jax["smt_structural_proof"]["cvc5"]["drop_D00_binding_flip"]["status"]
    z3_control = jax["smt_structural_proof"]["z3"]["nonderivation_control_has_defect"]["status"]
    cvc5_control = jax["smt_structural_proof"]["cvc5"]["nonderivation_control_has_defect"]["status"]
    asserted_precomputed_kernel_relations = int(jax["smt_structural_proof"]["asserted_precomputed_kernel_relations"])
    derived_leibniz_defect_count = int(jax["smt_structural_proof"]["derived_leibniz_defect_count"])

    max_divergence = max_dim_divergence(julia_dims, jax_dims, pytorch_dims)
    engine_fences_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in (julia, jax, pytorch)
    )
    ladder_ok = julia_dims == jax_dims == pytorch_dims == EXPECTED_LADDER
    if "drop_multiplication_preservation_flip" in jax["negative_control"]:
        drop_constraint_flip_ok = jax["negative_control"]["drop_multiplication_preservation_flip"]["pass"] is True
    else:
        drop_constraint_flip_ok = jax["negative_control"]["drop_D00_binding_flip"]["pass"] is True
    negative_flip_ok = bool(
        julia["negative_control"]["force_commutativity_flip"]["pass"] is True
        and julia["negative_control"]["unit_fixing_rank"]["pass"] is True
        and julia["negative_control"]["imaginary_only_probe_quotient_widens_to_15"]["pass"] is True
        and drop_constraint_flip_ok
        and jax["negative_control"]["force_commutativity_flip"]["pass"] is True
        and jax["negative_control"]["nonderivation_control_flip"]["pass"] is True
        and jax["negative_control"]["unit_fixing_rank"]["pass"] is True
        and jax["negative_control"]["imaginary_only_probe_quotient_widens_to_15"]["pass"] is True
        and pytorch["negative_control"]["residual_sensitivity_flip"]["pass"] is True
    )
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and engine_fences_ok
        and ladder_ok
        and negative_flip_ok
        and z3_o == cvc5_o == "unsat"
        and z3_erased == cvc5_erased == z3_control == cvc5_control == "sat"
        and asserted_precomputed_kernel_relations == 0
        and derived_leibniz_defect_count > 0
        and max_divergence == 0
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
        "claim_ceiling": "Scratch foundation rung for Der(O)=g2 dimension only. No formal admission, no promotion, no SU(3), SM, bridge, manifold, basin, or axis-level claim.",
        "all_pass": all_pass,
        "M_probe_family": {
            "id": "basis_pair_derivation_defect_coordinates",
            "observable": "P[k,a,b](D)=D(e_a e_b)-D(e_a)e_b-e_aD(e_b)",
            "finite_family": {"R": 1, "C": 8, "H": 64, "O": 512},
            "indistinguishability_rule": "D1 and D2 are equivalent when every derivation-defect coordinate probe agrees on D1-D2",
        },
        "C_constraints": {
            "trace": "finite probe weights are normalized to trace one for the measurement-family envelope",
            "PSD": "probe Gram/readout norm is positive semidefinite",
            "Hermiticity": "real coordinate probes are self-adjoint observables",
            "normalization": "e0 is the identity; basis units are norm-one; imaginary units square to -e0 in the Cayley-Dickson ladder",
            "rung_specific": "multiplication preservation: D(xy)=D(x)y+xD(y) for every ordered basis pair",
        },
        "quotient_summary": {
            "S": "End_R(A), the finite-dimensional space of linear maps on each carrier algebra",
            "equivalence": "D1 ~_M D2 iff M(D1-D2)=0",
            "symmetry_classes": "Der(A)=ker(M); class dimension is nullity of the computed derivation matrix",
            "derivation_dimensions": julia_dims,
            "expected_ladder": EXPECTED_LADDER,
            "O_identification": "dim Der(O)=14, the g2 Lie algebra dimension; fenced as scratch diagnostic only",
            "dimension_honesty": "Julia is the authoritative dim=14 rank/nullspace source; z3/cvc5 derive the Leibniz condition for candidate generators, not the dimension.",
        },
        "smt_derivation_summary": {
            "asserted_precomputed_kernel_relations": asserted_precomputed_kernel_relations,
            "derived_leibniz_defect_count": derived_leibniz_defect_count,
            "generator_count_checked": jax["candidate_generators"]["generator_count"],
            "proof_encoding": jax["smt_structural_proof"]["encoding"],
        },
        "negative_control_flip": {
            "division_algebra_ladder": {
                "pass": ladder_ok,
                "dimensions": julia_dims,
                "meaning": "R/C/H/O computed dimensions jump 0/0/3/14 from computed tables.",
            },
            "unit_fixing_rank": {
                "pass": julia["negative_control"]["unit_fixing_rank"]["pass"] and jax["negative_control"]["unit_fixing_rank"]["pass"],
                "rank": julia["negative_control"]["unit_fixing_rank"]["rank"],
            },
            "imaginary_only_probe_quotient_widens_to_15": {
                "pass": (
                    julia["negative_control"]["imaginary_only_probe_quotient_widens_to_15"]["pass"]
                    and jax["negative_control"]["imaginary_only_probe_quotient_widens_to_15"]["pass"]
                ),
                "full_O_derivation_dimension": julia_dims["O"],
                "imaginary_only_derivation_dimension": julia["negative_control"]["imaginary_only_probe_quotient_widens_to_15"]["imaginary_only_derivation_dimension"],
            },
            "solver_erased_D00_binding": {
                "pass": z3_o == cvc5_o == "unsat" and z3_erased == cvc5_erased == "sat",
                "all_generator_defect_negation": {"z3": z3_o, "cvc5": cvc5_o},
                "D00_binding_erased": {"z3": z3_erased, "cvc5": cvc5_erased},
            },
            "nonderivation_control": {
                "pass": z3_control == cvc5_control == "sat",
                "identity_matrix_defect": {"z3": z3_control, "cvc5": cvc5_control},
            },
            "force_commutativity": {
                "pass": julia["negative_control"]["force_commutativity_flip"]["pass"],
                "O_derivation_dimension": julia_dims["O"],
                "commutative_projection_derivation_dimension": julia["negative_control"]["force_commutativity_flip"]["commutative_projection_derivation_dimension"],
            },
            "torch_residual_sensitivity": pytorch["negative_control"]["residual_sensitivity_flip"],
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["CliffordAlgebras", "Z3", "JSON", "LinearAlgebra", "Dates"], ["CliffordAlgebras", "Z3"], "authoritative"),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "z3", "cvc5", "json", "fractions", "hashlib"], ["z3", "cvc5"], "structural_smt"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, ["torch", "torch.func", "json"], ["torch.func"], "differentiable_support"),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_o,
                "claim": "z3 expands L_k(i,j) from bound octonion T[k,i,j] and bound g2-generator D entries; asserting any Leibniz defect is nonzero is UNSAT for all 14 generators.",
                "negative_control_verdict": z3_erased,
                "nonderivation_control_verdict": z3_control,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_o,
                "claim": "Independent cvc5 expansion of the same in-solver Leibniz-defect equations agrees with z3.",
                "negative_control_verdict": cvc5_erased,
                "nonderivation_control_verdict": cvc5_control,
            },
            "julia_z3": {
                **julia["finite_certificates"]["julia_z3"],
                "verdict": julia["finite_certificates"]["julia_z3"]["O_dim_not_14_status"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_dims,
                "jax": jax_dims,
                "pytorch": pytorch_dims,
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
    dims = result["quotient_summary"]["derivation_dimensions"]
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims_R_C_H_O={dims['R']}/{dims['C']}/{dims['H']}/{dims['O']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
