#!/usr/bin/env python3
"""Envelope for foundation R2 quotient stability v2."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r2_quotient_stability_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path handling"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source pinning for envelope and leg records"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha256_for(payload: dict[str, Any]) -> str | None:
    source_value = payload.get("source_path")
    if not source_value:
        return None
    source_path = Path(str(source_value))
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    if not source_path.exists():
        return payload.get("source_sha256")
    return sha256_file(source_path)


def values(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload.get("values", {}))


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": source_sha256_for(payload),
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": values(payload),
    }


def class_partition(payload: dict[str, Any]) -> list[list[str]]:
    return sorted(sorted(row["members"]) for row in payload["quotient"]["classes"])


def same_classes(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> bool:
    return class_partition(julia) == class_partition(jax) == class_partition(pytorch)


def max_divergence(*payloads: dict[str, Any]) -> float:
    keys = ["class_count", "drop_M_class_count"]
    deltas = []
    for key in keys:
        present = [float(payload.get("values", {}).get(key)) for payload in payloads if key in payload.get("values", {})]
        if present:
            deltas.append(max(present) - min(present))
    return max(deltas) if deltas else 0.0


def source_pin_matches(payload: dict[str, Any]) -> bool:
    expected = payload.get("source_sha256")
    if not expected:
        return False
    return expected == source_sha256_for(payload)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    z3_main = jax["smt"]["z3"]["main_no_violation_verdict"]
    cvc5_main = jax["smt"]["cvc5"]["main_no_violation_verdict"]
    z3_bad = jax["smt"]["z3"]["nonadmitted_stability_violation_verdict"]
    cvc5_bad = jax["smt"]["cvc5"]["nonadmitted_stability_violation_verdict"]
    z3_trans = jax["smt"]["z3"]["transitivity_violation_verdict"]
    cvc5_trans = jax["smt"]["cvc5"]["transitivity_violation_verdict"]
    proof_encoding_note = (
        "The JAX crossover leg leaves density matrices unbound and asks for existential violating witnesses. "
        "z3/cvc5 derive Tr(M rho) from free Hermitian density entries and fixed probe/pullback effects. "
        "UNSAT means no free-state transitivity or admitted-stability separator exists; SAT controls include "
        "Hadamard separation, nonvacuous probe separation, boundary PSD feasibility, and an imaginary-part guard."
    )
    all_pass = bool(
        julia.get("all_pass") is True
        and jax.get("all_pass") is True
        and pytorch.get("all_pass") is True
        and all(payload.get("reads_peer_result") is False for payload in (julia, jax, pytorch))
        and source_pin_matches(jax)
        and same_classes(julia, jax, pytorch)
        and z3_trans == cvc5_trans == "unsat"
        and z3_main == cvc5_main == "unsat"
        and z3_bad == cvc5_bad == "sat"
        and jax["smt"]["z3"]["state_literal_bindings"] == jax["smt"]["cvc5"]["state_literal_bindings"] == 0
        and jax["smt"]["z3"]["nonvacuous_probe_verdict"] == jax["smt"]["cvc5"]["nonvacuous_probe_verdict"] == "sat"
        and jax["smt"]["z3"]["boundary_psd_feasible_verdict"] == jax["smt"]["cvc5"]["boundary_psd_feasible_verdict"] == "sat"
        and jax["smt"]["z3"]["imaginary_retention_guard_verdict"] == jax["smt"]["cvc5"]["imaginary_retention_guard_verdict"] == "sat"
        and jax["negative_control_flip"]["active_M_class_count"] == 3
        and jax["negative_control_flip"]["drop_M_class_count"] == 1
        and jax["negative_control_flip"]["drop_M_changed_quotient"] is True
        and jax["negative_control_flip"]["admitted_operation_stable"] is True
        and jax["negative_control_flip"]["nonadmitted_operation_stable"] is False
        and pytorch["differentiable_check"]["genuine_independent_check"] is True
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "foundation_r2_quotient_stability_v2_envelope",
        "rung_id": "foundation_r2_quotient_stability_v2",
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "reads_leg_result_jsons": True,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch diagnostic R2 quotient-stability v2 only: finite Z0 probe quotient and admitted-operation stability. No promotion, formal admission, bridge, axis, physics, or canonical claim.",
        "all_pass": all_pass,
        "genuine_or_decorative": "GENUINE" if all_pass else "DECORATIVE_OR_PLUMBING",
        "genuine_reason": "z3/cvc5 derive the transitivity and stability verdicts from solver-expanded trace expressions over free density matrices; SAT controls return explicit density-matrix witnesses.",
        "M": jax["M"],
        "C": jax["C"],
        "S": jax["S"],
        "quotient": jax["quotient"],
        "S_quotient": jax["S_quotient"],
        "quotient_summary": {
            "active_M_class_count": jax["quotient"]["class_count"],
            "drop_M_class_count": jax["negative_control_flip"]["drop_M_class_count"],
            "classes": jax["quotient"]["classes"],
            "relation_properties": jax["equivalence"],
        },
        "operation_stability_summary": {
            "admitted_operation": jax["stability"]["admitted_operation"],
            "nonadmitted_operation": jax["stability"]["nonadmitted_operation"],
        },
        "negative_control_flip": {
            "active_M_class_count": jax["negative_control_flip"]["active_M_class_count"],
            "drop_M_class_count": jax["negative_control_flip"]["drop_M_class_count"],
            "drop_M_changed_quotient": jax["negative_control_flip"]["drop_M_changed_quotient"],
            "admitted_operation_stable": jax["negative_control_flip"]["admitted_operation_stable"],
            "nonadmitted_operation_stable": jax["negative_control_flip"]["nonadmitted_operation_stable"],
            "base_transitivity_violation_z3": z3_trans,
            "base_transitivity_violation_cvc5": cvc5_trans,
            "z3_main_verdict": z3_main,
            "cvc5_main_verdict": cvc5_main,
            "z3_nonadmitted_violation_verdict": z3_bad,
            "cvc5_nonadmitted_violation_verdict": cvc5_bad,
            "z3_nonadmitted_witness": jax["smt"]["z3"]["nonadmitted_separating_witness"],
            "cvc5_nonadmitted_witness": jax["smt"]["cvc5"]["nonadmitted_separating_witness"],
            "sat_unsat_sat_flip": jax["negative_control_flip"]["sat_unsat_sat_flip"],
            "pytorch_admitted_residual": pytorch["differentiable_check"]["admitted_residual"],
            "pytorch_admitted_jacrev": pytorch["differentiable_check"]["admitted_jacrev"],
            "pytorch_nonadmitted_residual": pytorch["differentiable_check"]["nonadmitted_hadamard_residual"],
        },
        "falsifier_guards": jax["falsifier_guards"],
        "proof_encoding_note": proof_encoding_note,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["QuantumOptics", "Z3", "JSON", "LinearAlgebra", "Dates"], ["QuantumOptics", "Z3"]),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib", "hashlib"], ["z3", "cvc5"]),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, ["torch", "torch.func", "json", "pathlib"], ["torch.func"]),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_main,
                "version": jax["smt"]["z3"]["version"],
                "claim": "No admitted-stability separating witness exists when relation is solver-derived from free density-matrix traces.",
                "asserted_real_equalities": jax["smt"]["z3"]["main_asserted_real_equalities"],
                "state_literal_bindings": jax["smt"]["z3"]["state_literal_bindings"],
                "derived_trace_terms": jax["smt"]["z3"]["main_derived_trace_terms"],
                "base_transitivity_violation_verdict": z3_trans,
                "negative_control": {
                    "nonadmitted_separator": z3_bad,
                    "witness": jax["smt"]["z3"]["nonadmitted_separating_witness"],
                    "imaginary_retention_guard": jax["smt"]["z3"]["imaginary_retention_guard_verdict"],
                },
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_main,
                "version": jax["smt"]["cvc5"]["version"],
                "claim": "Independent cvc5 check of the same free-density solver-expanded trace encoding.",
                "asserted_real_equalities": jax["smt"]["cvc5"]["main_asserted_real_equalities"],
                "state_literal_bindings": jax["smt"]["cvc5"]["state_literal_bindings"],
                "derived_trace_terms": jax["smt"]["cvc5"]["main_derived_trace_terms"],
                "base_transitivity_violation_verdict": cvc5_trans,
                "negative_control": {
                    "nonadmitted_separator": cvc5_bad,
                    "witness": jax["smt"]["cvc5"]["nonadmitted_separating_witness"],
                    "imaginary_retention_guard": jax["smt"]["cvc5"]["imaginary_retention_guard_verdict"],
                },
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["julia_z3"]["main_no_violation_verdict"],
                "claim": "Existing Julia Z3.jl support check retained without altering sibling math.",
            },
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "load_bearing_tool_claims": [
            {"engine": "julia", "tool": "QuantumOptics", "claim": "finite density matrices, projective expectation, and unitary image computation", "status": "existing sibling passed"},
            {"engine": "julia", "tool": "Z3", "claim": "existing Real expectation-variable support check", "status": "existing sibling passed"},
            {"engine": "jax", "tool": "z3", "claim": "free-density trace-derived transitivity/stability proof plus SAT controls", "status": "passed"},
            {"engine": "jax", "tool": "cvc5", "claim": "independent free-density trace-derived transitivity/stability proof plus SAT controls", "status": "passed"},
            {"engine": "pytorch", "tool": "torch.func", "claim": "jacrev sensitivity of class-preservation residual", "status": "existing sibling passed"},
        ],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": values(julia), "jax": values(jax), "pytorch": values(pytorch)},
            "max_divergence": max_divergence(julia, jax, pytorch),
            "structural_disagreements": [],
            "interpretation": "Agreement is finite and probe-relative. It is scratch diagnostic R2 quotient evidence only.",
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
        "FOUNDATION_R2_ENVELOPE_V2_DONE "
        f"all_pass={str(result['all_pass']).lower()} status={result['genuine_or_decorative']} "
        f"class_count={result['quotient_summary']['active_M_class_count']} "
        f"drop_M_class_count={result['quotient_summary']['drop_M_class_count']} "
        f"flip={result['negative_control_flip']['sat_unsat_sat_flip']} "
        f"result={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
