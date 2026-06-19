#!/usr/bin/env python3
"""Validate geo_s5_alternative_flow_families_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s5_alternative_flow_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    if not ENVELOPE.exists():
        errors.append(f"missing envelope: {ENVELOPE}")
    if not JULIA.exists():
        errors.append(f"missing julia result: {JULIA}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}

    if payload:
        if payload.get("schema_version") != "three_engine_sim_result_v1":
            errors.append("schema_version must be three_engine_sim_result_v1")
        if payload.get("classification") != "scratch_diagnostic":
            errors.append("classification must remain scratch_diagnostic")
        if payload.get("promotion_allowed") is not False:
            errors.append("promotion_allowed must be false")
        if payload.get("formal_admission_allowed") is not False:
            errors.append("formal_admission_allowed must be false")
        if payload.get("all_pass") is not True:
            errors.append("envelope all_pass must be true")
        if payload.get("answer", {}).get("any_alternative_reproduces_full_committed_signature") is not False:
            errors.append("answer must report no full-signature alternative")
        if payload.get("answer", {}).get("full_signature_alternative_survivors") != []:
            errors.append("full_signature_alternative_survivors must be empty")
        matrix = payload.get("survival_matrix", {})
        for key in [
            "A_gradient_zero_antisymmetric",
            "B_hamiltonian_only",
            "C_shuffled_coefficients_null",
            "D_bounded_quadratic_non_affine",
        ]:
            if key not in matrix:
                errors.append(f"missing survival matrix row: {key}")
        if matrix.get("B_hamiltonian_only", {}).get("quotient_survival_56") is not True:
            errors.append("B_hamiltonian_only should be named as quotient co-survivor")
        if matrix.get("B_hamiltonian_only", {}).get("full_signature_match") is not False:
            errors.append("B_hamiltonian_only must not match full committed signature")
        if matrix.get("C_shuffled_coefficients_null", {}).get("killing_row") != "validity":
            errors.append("null model must die on validity")
        if matrix.get("D_bounded_quadratic_non_affine", {}).get("killing_row") != "affine_validity":
            errors.append("non-affine model must die on affine_validity")
        gates = payload.get("build_gates", {})
        for gate in [
            "committed_control_reproduces_parent_selected_values",
            "no_alternative_full_signature_match",
            "null_model_dies",
            "deliberately_non_cp_flow_fails_validity",
            "z3_cvc5_agree",
            "erased_flip_controls_fire",
            "julia_leg_loaded",
            "julia_reads_no_peer_result",
            "julia_values_match_python",
            "one_to_one_tool_calls",
            "no_audit_verdict_written",
        ]:
            if gates.get(gate) is not True:
                errors.append(f"build gate failed: {gate}")
        if [call.get("tool") for call in payload.get("tool_calls", [])] != ["sympy", "z3", "cvc5", "Z3"]:
            errors.append("tool_calls must be one-to-one for sympy,z3,cvc5,Z3")
        errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    if julia:
        if julia.get("all_pass") is not True:
            errors.append("julia all_pass must be true")
        if julia.get("reads_peer_result") is not False:
            errors.append("julia must not read peer result")
        if julia.get("engine_values") != payload.get("divergence", {}).get("engine_values", {}).get("jax"):
            errors.append("julia engine_values must match envelope jax engine values")

    result = {"ok": not errors, "errors": errors, "result_json": str(ENVELOPE)}
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
