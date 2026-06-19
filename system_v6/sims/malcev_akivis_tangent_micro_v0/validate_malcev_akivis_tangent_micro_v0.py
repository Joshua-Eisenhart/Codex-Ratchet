#!/usr/bin/env python3
"""Packet-local validator for malcev_akivis_tangent_micro_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "malcev_akivis_tangent_micro_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
    f"{SIM_ID}_julia.jl",
    f"{SIM_ID}_jax.py",
    f"{SIM_ID}_envelope.py",
    f"validate_{SIM_ID}.py",
    f"{SIM_ID}_common.py",
]
EXPECTED_ARTIFACT_SHA256 = "824a0a2c794a949a83e4bd650c9620464b96eb0d1dcb3d0fe4901a4e86d05f2c"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("claim_ceiling") == "tool_function_micro_only", f"{name} claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass false")
    canon = payload.get("canon_runtime", {})
    require(errors, canon.get("artifact_sha256") == EXPECTED_ARTIFACT_SHA256, f"{name} artifact hash mismatch")
    checks = payload.get("finite_checks", {})
    require(errors, checks.get("imaginary_dimension") == 7, f"{name} imaginary dimension mismatch")
    require(errors, checks.get("basis_triples_checked") == 343, f"{name} basis triple count mismatch")
    require(errors, checks.get("jacobi_identity_holds") is False, f"{name} Jacobi must fail")
    witness = checks.get("jacobi_failure_witness", {})
    require(errors, witness.get("basis_labels") == ["e1", "e2", "e4"], f"{name} Jacobi witness labels mismatch")
    require(errors, witness.get("sparse") == {"e5": -12}, f"{name} Jacobi witness value mismatch")
    require(errors, checks.get("malcev_compact_identity_holds") is True, f"{name} compact Malcev identity failed")
    require(errors, checks.get("malcev_expanded_identity_holds") is True, f"{name} expanded Malcev identity failed")
    q = checks.get("quaternion_control", {})
    require(errors, q.get("basis_labels") == ["e1", "e2", "e3"], f"{name} quaternion control labels mismatch")
    require(errors, q.get("triples_checked") == 27, f"{name} quaternion triple count mismatch")
    require(errors, q.get("jacobi_identity_holds") is True, f"{name} quaternion Jacobi control failed")
    neg = checks.get("non_malcev_control", {})
    require(errors, neg.get("malcev_identity_holds_after_perturbation") is False, f"{name} perturbed control must fail")
    require(errors, neg.get("failure_witness", {}).get("sparse") == {"e2": -4}, f"{name} perturbed witness mismatch")


def validate_envelope(errors: list[str], env: dict[str, Any]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "sim id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification mismatch")
    require(errors, env.get("claim_ceiling") == "tool_function_micro_only", "claim ceiling mismatch")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal admission must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass false")
    require(errors, set(env.get("engines", {})) == {"julia", "jax"}, "honest two-engine envelope required")
    require(errors, "pytorch" in env.get("engine_contract", {}).get("omitted_lanes", {}), "pytorch omission missing")
    require(errors, env.get("canon_runtime", {}).get("artifact_sha256") == EXPECTED_ARTIFACT_SHA256, "envelope artifact hash mismatch")
    require(errors, env.get("malcev_verdict") == "PASS_EXACT_IMAGINARY_OCTONION_COMMUTATOR_MALCEV_MICRO", "verdict mismatch")
    require(errors, env.get("positive_section", {}).get("jacobi_failure_witness", {}).get("sparse") == {"e5": -12}, "positive Jacobi witness mismatch")
    require(errors, env.get("positive_section", {}).get("malcev_compact_identity_holds") is True, "compact identity missing")
    require(errors, env.get("positive_section", {}).get("malcev_expanded_identity_holds") is True, "expanded identity missing")
    require(errors, env.get("boundary_section", {}).get("quaternion_subalgebra_control", {}).get("jacobi_identity_holds") is True, "quaternion control missing")
    require(errors, env.get("negative_section", {}).get("non_malcev_control", {}).get("failure_witness", {}).get("sparse") == {"e2": -4}, "negative control mismatch")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip must be sat")
    require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip must be sat")
    require(errors, env.get("relevance_fence", {}).get("nonassociativity") == "diagnostic_readout_only", "nonassociativity fence missing")
    errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
    require(errors, env.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict missing")
    require(errors, env.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict gate missing")
    generic_errors = validate_three_engine(env, require_pytorch=False)
    errors.extend(f"generic validator: {err}" for err in generic_errors)


def main() -> int:
    errors: list[str] = []
    for rel_path in REQUIRED_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    julia = load(JULIA) if JULIA.exists() else {}
    jax = load(JAX) if JAX.exists() else {}
    env = load(ENVELOPE) if ENVELOPE.exists() else {}
    if julia:
        validate_leg(errors, "julia", julia)
    else:
        errors.append(f"missing result: {JULIA.relative_to(ROOT)}")
    if jax:
        validate_leg(errors, "jax", jax)
    else:
        errors.append(f"missing result: {JAX.relative_to(ROOT)}")
    if env:
        validate_envelope(errors, env)
    else:
        errors.append(f"missing result: {ENVELOPE.relative_to(ROOT)}")
    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
