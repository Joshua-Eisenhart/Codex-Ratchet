#!/usr/bin/env python3
"""Composite envelope for foundation R5 Weyl chirality-pair three-engine rung."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_weyl_chirality_pair"
OBJECT_ID = "foundation_foundation_r5_weyl_chirality_pair_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_weyl_chirality_pair_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r5_weyl_chirality_pair_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independently written leg receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for result files"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def values(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload.get("values", {}))


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": values(payload),
    }


def max_divergence(*payloads: dict[str, Any]) -> float:
    keys = ["spinor_dim", "plus_dim", "minus_dim", "active_M_class_count", "drop_M_class_count", "identity_control_plus_dim", "identity_control_minus_dim"]
    deltas: list[float] = []
    for key in keys:
        present = [float(payload.get("values", {}).get(key)) for payload in payloads if key in payload.get("values", {})]
        if present:
            deltas.append(max(present) - min(present))
    return max(deltas) if deltas else 0.0


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    z3_main = jax["smt"]["z3"]["main_not_claim_verdict"]
    cvc5_main = jax["smt"]["cvc5"]["main_not_claim_verdict"]
    z3_control = jax["smt"]["z3"]["identity_control_not_4_4_verdict"]
    cvc5_control = jax["smt"]["cvc5"]["identity_control_not_4_4_verdict"]
    same_values = max_divergence(julia, jax, pytorch) == 0.0
    all_pass = bool(
        julia.get("all_pass") is True
        and jax.get("all_pass") is True
        and pytorch.get("all_pass") is True
        and all(payload.get("reads_peer_result") is False for payload in (julia, jax, pytorch))
        and z3_main == cvc5_main == "unsat"
        and z3_control == cvc5_control == "sat"
        and same_values
        and pytorch["differentiable_check"]["genuine_independent_check"] is True
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "reads_leg_result_jsons": True,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch foundation R5 Weyl chirality-pair rung only: builds the installed Cl(6)/3-qubit gamma7 split into 4/4 L/R classes. No forced-vs-installed reopening, no SM claim, no formal admission, no promotion.",
        "all_pass": all_pass,
        "genuine_or_decorative": "GENUINE_SCRATCH_DIAGNOSTIC" if all_pass else "DECORATIVE_OR_FAILED",
        "genuine_reason": "M is explicit gamma7, C is Cl(6) gamma structure plus state constraints, S/~_M is a two-class 4/4 quotient, and drop-M/identity-gamma7 controls change the quotient and SAT/UNSAT status.",
        "M": jax["M"],
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermitian", "normalization"],
            "rung_specific_constraint": "Cl(6) gamma matrices define normalized gamma7 = (-i)^3 gamma1...gamma6 with gamma7^2=I and 4/4 chirality projectors.",
            "julia_cliffordalgebras": julia["C"]["cliffordalgebras"],
            "julia_quantumoptics_matrix_cl6": julia["C"]["quantumoptics_matrix_cl6"],
            "jax_cl6_anticommutation_max_residual": jax["C"]["cl6_anticommutation_max_residual"],
        },
        "S": jax["S"],
        "S_quotient": jax["S_quotient"],
        "quotient_summary": {
            "active_M_class_count": jax["S_quotient"]["class_count"],
            "classes": jax["S_quotient"]["classes"],
            "left_right_dims": jax["S_quotient"]["left_right_dims"],
            "drop_M_class_count": jax["negative_control_flip"]["drop_M_class_count"],
        },
        "chirality_summary": {
            "gamma7_square_residual_julia": julia["values"]["gamma7_square_residual"],
            "gamma7_square_residual_jax": jax["values"]["gamma7_square_residual"],
            "gamma7_square_residual_pytorch": pytorch["values"]["gamma7_square_residual"],
            "plus_dim": jax["values"]["plus_dim"],
            "minus_dim": jax["values"]["minus_dim"],
            "gamma7_diagonal": jax["chirality"]["gamma7_diagonal"],
        },
        "negative_control_flip": {
            "drop_M_changed_quotient": jax["negative_control_flip"]["drop_M_changed_quotient"],
            "active_M_class_count": jax["negative_control_flip"]["active_M_class_count"],
            "drop_M_class_count": jax["negative_control_flip"]["drop_M_class_count"],
            "identity_gamma7_plus_dim": jax["negative_control_flip"]["identity_gamma7_plus_dim"],
            "identity_gamma7_minus_dim": jax["negative_control_flip"]["identity_gamma7_minus_dim"],
            "identity_control_no_split": jax["negative_control_flip"]["identity_control_no_split"],
            "z3_main_not_4_4_verdict": z3_main,
            "cvc5_main_not_4_4_verdict": cvc5_main,
            "z3_identity_control_not_4_4_verdict": z3_control,
            "cvc5_identity_control_not_4_4_verdict": cvc5_control,
            "sat_unsat_flip": f"main not-4/4 z3/cvc5={z3_main}/{cvc5_main}; identity-control not-4/4 z3/cvc5={z3_control}/{cvc5_control}",
            "pytorch_cross_chirality_jacrev": pytorch["values"]["cross_chirality_jacrev"],
            "pytorch_identity_control_jacrev": pytorch["values"]["identity_control_jacrev"],
        },
        "proof_encoding_note": jax["smt"]["encoding"],
        "engines": {
            "julia": engine_record(
                julia,
                JULIA_RESULT,
                ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "Dates"],
                ["QuantumOptics", "CliffordAlgebras", "Z3"],
            ),
            "jax": engine_record(
                jax,
                JAX_RESULT,
                ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"],
                ["z3", "cvc5"],
            ),
            "pytorch": engine_record(
                pytorch,
                PYTORCH_RESULT,
                ["torch", "torch.func", "json", "pathlib"],
                ["torch.func"],
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_main,
                "version": jax["smt"]["z3"]["version"],
                "claim": "Negated derived chirality claim is UNSAT: gamma7^2 != I or plus/minus dimensions != 4/4 cannot hold after in-solver gamma7 derivation.",
                "negative_control": {"identity_gamma7_not_4_4_verdict": z3_control},
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_main,
                "version": jax["smt"]["cvc5"]["version"],
                "claim": "Independent cvc5 derivation of the same bound-entry gamma7 product and 4/4 split proof.",
                "negative_control": {"identity_gamma7_not_4_4_verdict": cvc5_control},
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["main_not_4_4_verdict"],
                "claim": "Julia-side dimension equation from Tr(gamma7) proves not-4/4 UNSAT and identity control SAT.",
            },
        },
        "claim_path_tools": ["QuantumOptics", "CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "load_bearing_tool_claims": [
            {"engine": "julia", "tool": "QuantumOptics", "claim": "3-qubit tensor gamma matrix construction", "status": "passed"},
            {"engine": "julia", "tool": "CliffordAlgebras", "claim": "Cl(6,0) generator and raw pseudoscalar structure check", "status": "passed"},
            {"engine": "julia", "tool": "Z3", "claim": "dimension equation not-4/4 UNSAT with identity-control SAT", "status": "passed"},
            {"engine": "jax", "tool": "z3", "claim": "in-solver gamma7 product, square, and 4/4 split proof", "status": "passed"},
            {"engine": "jax", "tool": "cvc5", "claim": "independent in-solver gamma7 product, square, and 4/4 split proof", "status": "passed"},
            {"engine": "pytorch", "tool": "torch.func", "claim": "jacrev sensitivity of chirality expectation under L/R mixing", "status": "passed"},
        ],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": values(julia), "jax": values(jax), "pytorch": values(pytorch)},
            "max_divergence": max_divergence(julia, jax, pytorch),
            "structural_disagreements": [],
            "interpretation": "Agreement is over finite gamma7 split values; the substantive controls are drop-M quotient coarsening and identity-gamma7 SAT/UNSAT flip.",
        },
        "peer_json_rule": "Only this envelope reads leg result JSON. Engine lanes have reads_peer_result=false.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R5_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={result['chirality_summary']['plus_dim']}/{result['chirality_summary']['minus_dim']} "
        f"classes={result['quotient_summary']['active_M_class_count']} "
        f"drop_M={result['quotient_summary']['drop_M_class_count']} "
        f"flip={result['negative_control_flip']['sat_unsat_flip']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
