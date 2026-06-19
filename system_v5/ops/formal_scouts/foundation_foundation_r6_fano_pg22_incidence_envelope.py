#!/usr/bin/env python3
"""Composite envelope for foundation_r6_fano_pg22_incidence.

The envelope reads completed Julia, JAX, and PyTorch leg receipts after the
legs have run. It does not recompute the engine legs or promote the rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_fano_pg22_incidence"
OBJECT_ID = "foundation_r6_fano_pg22_incidence_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_fano_pg22_incidence_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r6_fano_pg22_incidence_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from completed engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for source and result receipts"},
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_values(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    return {
        "points": int(summary["points"]),
        "line_count": int(summary["line_count"]),
        "fano_axioms_hold": bool(summary["fano_axioms_hold"]),
        "control_line_count": int(summary["control_line_count"]),
        "control_fano_axioms_hold": bool(summary["control_fano_axioms_hold"]),
        "lines": summary["lines"],
    }


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


def fences_ok(*payloads: dict[str, Any]) -> bool:
    return all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in payloads
    )


def max_divergence(values: dict[str, dict[str, Any]]) -> float:
    keys = ["points", "line_count", "control_line_count"]
    diffs = []
    for key in keys:
        nums = [float(row[key]) for row in values.values()]
        diffs.append(max(nums) - min(nums))
    return max(diffs)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    julia_values = engine_values(julia)
    jax_values = engine_values(jax)
    pytorch_values = engine_values(pytorch)
    values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(values)
    same_lines = julia_values["lines"] == jax_values["lines"] == pytorch_values["lines"]
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    negative = {
        "non_octonion_erased_pair_axioms_hold_true_to_false": bool(
            julia["negative_control_flip"]["non_octonion_erased_pair_axioms_hold_true_to_false"]
            and jax["negative_control_flip"]["non_octonion_erased_pair_axioms_hold_true_to_false"]
            and pytorch["negative_control_flip"]["non_octonion_erased_pair_axioms_hold_true_to_false"]
        ),
        "line_count_7_to_control": julia["negative_control_flip"]["line_count_7_to_control"],
        "mutated_pair": julia["negative_control_flip"]["mutated_pair"],
        "mutated_pair_wrong_support": julia["negative_control_flip"]["mutated_pair_wrong_support"],
        "mutated_pair_unique_line_count": julia["negative_control_flip"]["mutated_pair_unique_line_count"],
        "z3_true_line_not_collinear_unsat_to_erased_sat": bool(jax["negative_control_flip"]["z3_true_line_not_collinear_unsat_to_erased_sat"]),
        "cvc5_true_line_not_collinear_unsat_to_erased_sat": bool(jax["negative_control_flip"]["cvc5_true_line_not_collinear_unsat_to_erased_sat"]),
        "z3_nonline_not_collinear_sat": bool(jax["negative_control_flip"]["z3_nonline_not_collinear_sat"]),
        "cvc5_nonline_not_collinear_sat": bool(jax["negative_control_flip"]["cvc5_nonline_not_collinear_sat"]),
        "torch_func_jacrev_independent_sensitivity": bool(pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]),
    }
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and jax["crossover_proofs"]["z3"]["negative_control_verdict"] == "sat"
        and jax["crossover_proofs"]["cvc5"]["negative_control_verdict"] == "sat"
        and div == 0.0
        and same_lines
        and fences_ok(julia, jax, pytorch)
        and all(value for value in negative.values() if isinstance(value, bool))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
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
            "Scratch foundation R6 Fano PG(2,2) incidence rung only: the seven imaginary "
            "octonion units derive seven Fano lines under the collinearity probe e_i*e_j=+/-e_k. "
            "No promotion, no physics bridge, no downstream manifold claim."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "octonion_collinearity_probe_family",
            "explicit_probe_family": julia["M"]["explicit_probe_family"],
            "finite_probe_counts": julia["M"]["finite_probe_counts"],
            "measurement_map": "M(e_i,e_j) computes the signed support of e_i*e_j for each of 21 unordered imaginary-unit pairs.",
        },
        "C": {
            "trace_eq_1": bool(julia["C"]["trace_eq_1"] and jax["C"]["trace_eq_1"] and pytorch["C"]["trace_eq_1"]),
            "psd": bool(julia["C"]["psd"] and jax["C"]["psd"] and pytorch["C"]["psd"]),
            "hermitian": bool(julia["C"]["hermitian"] and jax["C"]["hermitian"] and pytorch["C"]["hermitian"]),
            "normalization": julia["C"]["normalization"],
            "rung_specific_constraint": "Cayley-Dickson octonion structure constants; a triple is a line iff e_i*e_j = +/-e_k.",
            "structure_constants_sha256": julia["C"]["structure_constants_sha256"],
        },
        "S_mod_M": {
            "definition": julia["S_mod_M"]["definition"],
            "points": julia["S_mod_M"]["points"],
            "equivalence_classes": julia_values["lines"],
            "quotient_line_count": julia_values["line_count"],
            "incidence_structure": "PG(2,2) Fano plane",
        },
        "fano_axioms": julia["fano_axioms"],
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
                "nonline_verdict": jax["crossover_proofs"]["z3"]["nonline_verdict"],
                "claim": jax["crossover_proofs"]["z3"]["claim"],
                "dimension_derived_without_dim_literal": True,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "nonline_verdict": jax["crossover_proofs"]["cvc5"]["nonline_verdict"],
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
                "dimension_derived_without_dim_literal": True,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["true_line"]["status"],
                "negative_control_verdict": julia["julia_z3"]["erased_pair"]["status"],
                "nonline_verdict": julia["julia_z3"]["nonline"]["status"],
                "claim": "Julia Z3.jl repeats the computed-table collinearity guard for a true line, erased pair, and nonline.",
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
            "engine_values": values,
            "max_divergence": div,
            "same_lines": same_lines,
            "notes": [
                "Julia is authoritative: QuantumOptics encodes finite point/line probes, CliffordAlgebras checks each derived line as a quaternionic triple, and Z3.jl guards collinearity.",
                "JAX supplies z3+cvc5 structural proof over computed table entries; the solver derives product coordinates and the erase control flips UNSAT to SAT.",
                "PyTorch supplies torch.func.jacrev sensitivity for differentiable erasure of a true line product; it is a genuine independent sensitivity check, not a finite-geometry proof authority.",
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
        "FOUNDATION_R6_FANO_PG22_INCIDENCE_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"lines={result['S_mod_M']['equivalence_classes']} "
        f"control_lines={result['negative_control_flip']['line_count_7_to_control'][1]} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
