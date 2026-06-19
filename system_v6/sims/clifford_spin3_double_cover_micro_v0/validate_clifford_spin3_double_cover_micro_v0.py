#!/usr/bin/env python3
"""Packet-local validator for clifford_spin3_double_cover_micro_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "clifford_spin3_double_cover_micro_v0"
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
]

PINNED_ANGLE_IDS = {"theta_pi_over_2", "theta_pi", "theta_2pi", "theta_4pi"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass false")
    require(errors, payload.get("fixed_dimension", {}).get("cl_pq") == "Cl(3,0)", f"{name} fixed Cl(3,0) missing")
    require(errors, payload.get("fixed_dimension", {}).get("basis_blade_count") == 8, f"{name} blade count must be 8")
    require(errors, set(payload.get("pinned_angles", {})) >= PINNED_ANGLE_IDS, f"{name} pinned angles missing")

    double_cover = payload.get("double_cover_rows", {})
    row = double_cover.get("theta_pi_over_2_vs_theta_plus_2pi", {})
    require(errors, row.get("rotors_differ_by_sign") is True, f"{name} pi/2 rotor sign distinction missing")
    require(errors, row.get("so3_actions_equal") is True, f"{name} SO(3) equality missing")
    require(errors, row.get("rotor_relation") == "R(theta_plus_2pi)=-R(theta)", f"{name} rotor relation mismatch")
    require(errors, row.get("action_matrix_theta") == row.get("action_matrix_theta_plus_2pi"), f"{name} SO(3) matrices drift")

    boundary = payload.get("boundary_rows", {})
    require(errors, boundary.get("theta_2pi", {}).get("rotor") == "-1", f"{name} 360 sign flip missing")
    require(errors, boundary.get("theta_2pi", {}).get("same_so3_as_identity") is True, f"{name} 360 action not identity")
    require(errors, boundary.get("theta_4pi", {}).get("rotor") == "1", f"{name} 720 closure missing")
    require(errors, boundary.get("theta_4pi", {}).get("same_so3_as_identity") is True, f"{name} 720 action not identity")

    controls = payload.get("controls", {})
    require(errors, controls.get("single_cover_matrix_cannot_distinguish_2pi", {}).get("pass") is True, f"{name} single-cover control failed")
    require(errors, controls.get("non_unit_even_multivector_fails_rotor_predicate", {}).get("pass") is True, f"{name} non-unit even control failed")
    require(errors, controls.get("odd_grade_element_fails_rotor_predicate", {}).get("pass") is True, f"{name} odd-grade control failed")


def validate_envelope(errors: list[str], env: dict[str, Any]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "sim id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, env.get("claim_ceiling") == "tool_function_micro_only", "claim ceiling mismatch")
    require(errors, env.get("all_pass") is True, "envelope all_pass false")
    require(errors, set(env.get("engines", {})) == {"julia", "jax"}, "honest two-engine envelope required")
    require(errors, "pytorch" not in env.get("engines", {}), "pytorch must be omitted for this mode")
    require(errors, env.get("engine_contract", {}).get("mode") == "julia_canon_jax_exact_symbolic", "engine mode mismatch")
    require(errors, "pytorch" in env.get("engine_contract", {}).get("omitted_lanes", {}), "pytorch omission missing")

    errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
    require(errors, env.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict missing")
    require(errors, env.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict envelope gate missing")
    require(errors, env.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder no-audit gate false")

    generic_errors = validate_three_engine(env, require_pytorch=False)
    errors.extend(f"generic validator: {err}" for err in generic_errors)

    require(errors, env.get("double_cover_verdict") == "PASS_EXACT_SPIN3_DOUBLE_COVER_MICRO", "double-cover verdict mismatch")
    require(errors, env.get("relevance_fence", {}).get("o6_720_coupling_candidate") == "background_only_not_claimed", "O6 fence mismatch")
    require(errors, env.get("relevance_fence", {}).get("engine_coupling_claims") == "not_claimed", "engine/coupling fence mismatch")

    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 positive proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 positive proof must be unsat")
    require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip control must be sat")
    require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip control must be sat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 proof must be unsat")

    boundary = env.get("boundary_section", {})
    require(errors, boundary.get("theta_2pi", {}).get("rotor") == "-1", "360 sign flip missing")
    require(errors, boundary.get("theta_4pi", {}).get("rotor") == "1", "720 closure missing")
    require(errors, bool(env.get("positive_section")), "positive section missing")
    require(errors, bool(env.get("negative_section")), "negative section missing")
    require(errors, bool(env.get("TOOL_MANIFEST")), "TOOL_MANIFEST missing")
    require(errors, bool(env.get("TOOL_INTEGRATION_DEPTH")), "TOOL_INTEGRATION_DEPTH missing")
    require(errors, bool(env.get("validator_expected_commands")), "validator command ledger missing")


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
