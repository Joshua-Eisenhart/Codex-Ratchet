#!/usr/bin/env python3
"""Composite envelope for foundation_r1_f01_finitude three-engine receipts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "foundation_foundation_r1_f01_finitude_envelope_results.json"
)
JULIA_RESULT = (
    ROOT
    / "system_v5"
    / "julia_carrier"
    / "results"
    / "foundation_foundation_r1_f01_finitude_julia_results.json"
)
JAX_RESULT = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "foundation_foundation_r1_f01_finitude_jax_results.json"
)
PYTORCH_RESULT = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "foundation_foundation_r1_f01_finitude_pytorch_results.json"
)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result-envelope assembly from independent engine receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for receipt files",
    },
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload.get("source_sha256"),
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": {
            "finite_cardinality": payload["summary"]["finite_cardinality"],
            "probe_count": payload["M"]["probe_count"],
            "class_count": payload["quotient"]["class_count"],
            "identity_residual": payload["M"].get(
                "identity_residual", payload["M"]["identity_residual_projectors_only"]
            ),
            "admitted_rank": payload["computed_candidates"]["admitted_reference"]["computed_rank"],
            "over_support_rank": payload["computed_candidates"]["excluded_over_support"]["computed_rank"],
            "all_pass": payload["all_pass"],
        },
    }


def main() -> int:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    z3_verdict = jax["smt"]["z3"]["over_support_with_f01"]
    cvc5_verdict = jax["smt"]["cvc5"]["over_support_with_f01"]
    z3_erased = jax["smt"]["z3"]["over_support_without_f01"]
    cvc5_erased = jax["smt"]["cvc5"]["over_support_without_f01"]
    z3_solver_support = jax["smt"]["z3"]["solver_derived_supports"]["over_support_without_f01"]
    cvc5_solver_support = jax["smt"]["cvc5"]["solver_derived_supports"]["over_support_without_f01"]
    admitted_verdicts = {
        "z3": jax["smt"]["z3"]["admitted_with_f01"],
        "cvc5": jax["smt"]["cvc5"]["admitted_with_f01"],
        "julia_z3": julia["z3"]["admitted_with_f01"],
    }
    finite_values = {
        "julia": julia["summary"]["finite_cardinality"],
        "jax": jax["summary"]["finite_cardinality"],
        "pytorch": pytorch["summary"]["finite_cardinality"],
    }
    max_divergence = max(
        abs(float(finite_values["julia"]) - float(finite_values["jax"])),
        abs(float(finite_values["julia"]) - float(finite_values["pytorch"])),
    )
    over_ranks = {
        "julia": julia["computed_candidates"]["excluded_over_support"]["computed_rank"],
        "jax": jax["computed_candidates"]["excluded_over_support"]["computed_rank"],
        "pytorch": pytorch["computed_candidates"]["excluded_over_support"]["computed_rank"],
    }
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and admitted_verdicts["z3"] == admitted_verdicts["cvc5"] == admitted_verdicts["julia_z3"] == "sat"
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_erased == cvc5_erased == "sat"
        and max_divergence == 0.0
        and len(set(over_ranks.values())) == 1
        and over_ranks["julia"] == finite_values["julia"] + 1
    )

    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": "foundation_r1_f01_finitude",
        "object_id": "foundation_r1_f01_finitude_three_engine_envelope",
        "classification": CLASSIFICATION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "F01 finite support fence at micro scale; scratch diagnostic only, no promotion or later-rung claim.",
        "all_pass": all_pass,
        "M": {
            "description": "finite probe family M = {P0, P1, P2, X01_half} on a d=3 carrier",
            "probe_names": julia["M"]["probe_names"],
            "carrier_dimension": julia["M"]["carrier_dimension"],
            "probe_count": julia["M"]["probe_count"],
            "resolves_identity": julia["M"]["resolves_identity"]
            and jax["M"]["resolves_identity"]
            and pytorch["M"]["resolves_identity"],
            "identity_residuals": {
                "julia": julia["M"]["identity_residual_projectors_only"],
                "jax": jax["M"]["identity_residual_projectors_only"],
                "pytorch": pytorch["M"]["identity_residual_projectors_only"],
            },
        },
        "C": {
            "trace_equals_one": julia["C"]["trace_equals_one"]
            and jax["C"]["trace_equals_one"]
            and pytorch["C"]["trace_equals_one"],
            "psd": julia["C"]["psd"] and jax["C"]["psd"] and pytorch["C"]["psd"],
            "hermitian": julia["C"]["hermitian"] and jax["C"]["hermitian"] and pytorch["C"]["hermitian"],
            "normalization": julia["C"]["normalization"]
            and jax["C"]["normalization"]
            and pytorch["C"]["normalization"],
            "rung_specific_constraint": "F01 admits candidate iff computed support rank r <= reference carrier dimension d",
            "computed_rank_binding": {
                "admitted": {
                    "d": finite_values["julia"],
                    "r": julia["computed_candidates"]["admitted_reference"]["computed_rank"],
                },
                "over_support": {"d": finite_values["julia"], "r": over_ranks["julia"]},
            },
            "jax_smt_rank_binding": {
                "method": "z3/cvc5 bind exact rho_ij rationals, constrain unbound lambdas by diagonal characteristic relation lambda_i == bound rho_ii, and derive support=sum(ite(lambda_i > tol, 1, 0)) in-solver",
                "z3_solver_derived_over_support": z3_solver_support,
                "cvc5_solver_derived_over_support": cvc5_solver_support,
                "solver_supports_match_jax_ranks": jax["summary"]["solver_supports_match_jax_ranks"],
                "falsifier_guards": jax["falsifier_guards"],
            },
        },
        "quotient": {
            "relation": "rho ~_M sigma iff all finite probe expectations in M match",
            "admitted_cardinality": julia["quotient"]["admitted_cardinality"],
            "class_count": julia["quotient"]["class_count"],
            "classes": julia["quotient"]["classes"],
            "drop_probe": "X01_half",
            "drop_probe_class_count": julia["quotient"]["drop_probe_class_count"],
            "drop_probe_coarsened": julia["quotient"]["drop_probe_class_count"] < julia["quotient"]["class_count"],
            "jax_class_count": jax["quotient"]["class_count"],
            "pytorch_class_count": pytorch["quotient"]["class_count"],
            "pytorch_sensitivity_rank": pytorch["torch_func_check"]["jacobian_rank"],
        },
        "negative_control": {
            "erase": "drop_f01_finite_support_constraint for computed over-support candidate",
            "admitted_with_f01": admitted_verdicts,
            "over_support_with_f01": {
                "z3": z3_verdict,
                "cvc5": cvc5_verdict,
                "julia_z3": julia["z3"]["over_support_with_f01"],
            },
            "over_support_without_f01": {
                "z3": z3_erased,
                "cvc5": cvc5_erased,
                "julia_z3": julia["z3"]["over_support_without_f01"],
            },
            "flipped": z3_verdict == cvc5_verdict == "unsat" and z3_erased == cvc5_erased == "sat",
            "computed_rank_values": {"d": finite_values["julia"], "over_support_r": over_ranks["julia"]},
            "jax_solver_derived_rank_values": {
                "z3_over_support_without_f01": z3_solver_support,
                "cvc5_over_support_without_f01": cvc5_solver_support,
                "over_rank_source": "the padded diagonal rho has four exact nonzero 1/4 entries; no lower support bound is asserted",
            },
            "drop_probe_control": {
                "drop_probe": "X01_half",
                "full_probe_class_count": julia["quotient"]["class_count"],
                "drop_probe_class_count": julia["quotient"]["drop_probe_class_count"],
                "coarsened": julia["quotient"]["drop_probe_class_count"] < julia["quotient"]["class_count"],
            },
            "interpretation": "The JAX over-support UNSAT is tied to solver-derived support from bound exact rho_ij entries; erasing only F01 keeps the same bound rho and admits the rank-four state.",
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
                "verdict": z3_verdict,
                "erased_f01_verdict": z3_erased,
                "admitted_verdict": admitted_verdicts["z3"],
                "bound_values": jax["smt"]["z3"]["bound_values"],
                "solver_derived_support": z3_solver_support,
                "claim": "z3 derives support from exact bound rho_ij entries via unbound lambda_i == rho_ii; the rank-four padded state is UNSAT with F01 support <= d and SAT when F01 is erased.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "erased_f01_verdict": cvc5_erased,
                "admitted_verdict": admitted_verdicts["cvc5"],
                "bound_values": jax["smt"]["cvc5"]["bound_values"],
                "solver_derived_support": cvc5_solver_support,
                "claim": "cvc5 derives support from exact bound rho_ij entries via unbound lambda_i == rho_ii; the rank-four padded state is UNSAT with F01 support <= d and SAT when F01 is erased.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["z3"]["over_support_with_f01"],
                "erased_f01_verdict": julia["z3"]["over_support_without_f01"],
                "admitted_verdict": julia["z3"]["admitted_with_f01"],
                "claim": "Julia-side Z3 check is the existing QuantumOptics sibling receipt; the hardened JAX crossover is the rho-entry SMT leg.",
            },
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": finite_values,
            "max_divergence": max_divergence,
            "computed_over_support_ranks": over_ranks,
            "notes": [
                "Finite-cardinality agreement is plumbing only; the JAX load-bearing crossover derives support in-solver from bound exact rho_ij entries before the F01 erase flip.",
                "PyTorch contributes torch.func jacrev sensitivity of finite probe/eigenvalue readouts, not a second SMT proof.",
            ],
        },
        "audit_boundary": {
            "builder_does_not_grade_own_work": True,
            "reason": "The JAX crossover solvers receive neither a precomputed support integer nor precomputed spectrum literals: they bind exact rho_ij entries, constrain unbound lambdas from rho_ii in-solver, define support by ite(lambda_i > tol), then flip UNSAT to SAT when F01 support<=d is erased.",
            "remaining_limit": "This is still scratch_diagnostic finitude plumbing only; promotion_allowed=false and formal_admission_allowed=false.",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_F01_DONE "
        f"all_pass={str(all_pass).lower()} d={finite_values['julia']} over_r={over_ranks['julia']} "
        f"flip={z3_verdict}/{cvc5_verdict}->{z3_erased}/{cvc5_erased} "
        f"max_divergence={max_divergence}"
    )
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
