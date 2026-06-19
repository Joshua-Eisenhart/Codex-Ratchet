#!/usr/bin/env python3
"""Composite envelope for foundation_r3_associator_medium."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_medium_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r3_associator_medium_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_pytorch_results.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
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
    }


def main() -> int:
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    j_h = float(julia["values"]["H"]["max_associator_norm"])
    j_o = float(julia["values"]["O"]["max_associator_norm"])
    x_h = float(jax["values"]["H"]["max_associator_norm"])
    x_o = float(jax["values"]["O"]["max_associator_norm"])
    max_divergence = max(abs(j_h - x_h), abs(j_o - x_o))
    z3_verdict = jax["smt_structural_proof"]["z3"]["O"]["assert_all_associators_zero_status"]
    cvc5_verdict = jax["smt_structural_proof"]["cvc5"]["O"]["assert_all_associators_zero_status"]
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and z3_verdict == cvc5_verdict == "unsat"
        and max_divergence <= 1.0e-12
        and jax["negative_control"]["erase_all_zero_constraint"]["flips"]
    )
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": "foundation_r3_associator_medium",
        "object_id": "foundation_r3_associator_medium_envelope",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch foundation R3 associator rung only. No promotion, no formal admission, no bridge or axis-level claim.",
        "M": {
            "name": "bracketing-distinguishability associator probe",
            "probe_family": "finite basis triples for [A,B,C]=(AB)C-A(BC)",
            "observable": "associator vector and norm",
        },
        "C": {
            "trace_equals_one": {
                "status": "not_applicable_to_carrier_table",
                "reason": "this rung admits finite multiplication structure constants, not density states",
            },
            "PSD": {
                "status": "not_applicable_to_carrier_table",
                "reason": "no state matrix is admitted or promoted by this rung",
            },
            "Hermiticity": {
                "status": "not_applicable_to_carrier_table",
                "reason": "carrier involution is represented by Cayley-Dickson conjugation signs instead",
            },
            "normalization": {
                "status": "enforced",
                "reason": "all tested algebra probes are unit basis triples with e0 as the multiplicative unit",
            },
            "base_constraints": ["unital finite real algebra", "unit basis vectors", "conjugation normalization", "computed multiplication structure constants"],
            "state_constraints_note": "trace=1, PSD, and Hermiticity are state-rung constraints; this carrier rung records the corresponding finite algebra admissibility constraints instead of fabricating a density state.",
            "rung_specific_constraint": "normed division algebra structure: package-computed H table and Cayley-Dickson O table",
        },
        "S_quotient_under_M": {
            "relation": "(AB)C ~ A(BC) iff associator(A,B,C) == 0",
            "H": "bracketings indistinguishable for every basis triple",
            "O": "bracketings distinguishable for the witness basis triple",
        },
        "quotient_summary": {
            "H_associator_norm": j_h,
            "O_associator_norm": j_o,
            "octonion_witness": julia["values"]["O"]["witness"],
            "H_equivalence_class": "single zero-associator bracketing class",
            "O_equivalence_class": "nonzero associator separates (AB)C from A(BC)",
        },
        "negative_control_flip": {
            "H_to_O_structure_flip": julia["negative_control"]["H_to_O_structure_flip"],
            "smt_erase_flip": jax["negative_control"]["erase_all_zero_constraint"],
            "torch_selector_flip": pytorch["negative_control"],
        },
        "octonion_structure": julia["octonion_structure"],
        "engines": {
            "julia": engine(julia, JULIA_RESULT),
            "jax": engine(jax, JAX_RESULT),
            "pytorch": engine(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": "Given computed O associator coefficients, asserting all associators are zero is UNSAT",
                "negative_control_verdict": jax["smt_structural_proof"]["z3"]["O"]["drop_all_zero_constraint_status"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": "Given computed O associator coefficients, asserting all associators are zero is UNSAT",
                "negative_control_verdict": jax["smt_structural_proof"]["cvc5"]["O"]["drop_all_zero_constraint_status"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "Grassmann", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": ["LinearAlgebra", "json", "hashlib"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"H_associator_norm": j_h, "O_associator_norm": j_o},
                "jax": {"H_associator_norm": x_h, "O_associator_norm": x_o},
                "pytorch": {
                    "H_associator_norm": pytorch["values"]["H_max_associator_norm"],
                    "O_associator_norm": pytorch["values"]["O_max_associator_norm"],
                    "jacrev_alpha_0_5": pytorch["values"]["jacrev_alpha_0_5"],
                },
            },
            "max_divergence": max_divergence,
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly only"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic receipt paths"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE all_pass={all_pass} H_norm={j_h} O_norm={j_o} z3={z3_verdict} cvc5={cvc5_verdict} max_divergence={max_divergence}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
