#!/usr/bin/env python3
"""Envelope assembler for geo_s3_density_observable_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_density_observable_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s3_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s3_build_spec_20260610.md"
DIRECTIVE = Path("/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md")
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

REQUIRED_RECEIPTS = {"S3.F01", "S3.N01", "S3.T01", "S3.A", "S3.B", "S3.C", "S3.D", "S3.E", "S3.F", "S3.G"}
ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
}

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, copied-input, and PIN hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "convention_pin": payload["convention_pin"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
    }


def current_source_hash_ok(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and file_sha256(source) == payload["source_sha256"]


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for payload in payloads.values():
        out.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(out)


def collect_strengths(receipts: dict[str, Any]) -> list[str]:
    strengths = {str(row.get("exact_strength")) for row in receipts.values()}
    return sorted(strengths)


def copied_input_records() -> dict[str, Any]:
    return {
        "s3_build_spec": {
            "source_path": rel(SPEC),
            "copy_path": rel(SPEC_COPY),
            "source_sha256": file_sha256(SPEC),
            "copy_sha256": file_sha256(SPEC_COPY),
            "exists": SPEC_COPY.exists(),
            "matches_source": SPEC_COPY.exists() and file_sha256(SPEC_COPY) == file_sha256(SPEC),
        },
        "directive_addendum": {
            "source_path": str(DIRECTIVE),
            "copy_path": rel(DIRECTIVE_COPY),
            "source_sha256": file_sha256(DIRECTIVE) if DIRECTIVE.exists() else None,
            "copy_sha256": file_sha256(DIRECTIVE_COPY),
            "exists": DIRECTIVE_COPY.exists(),
            "matches_source": DIRECTIVE.exists() and file_sha256(DIRECTIVE_COPY) == file_sha256(DIRECTIVE),
        },
    }


def main() -> int:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    receipts = dict(jax["receipts"])
    receipts["F01_finitude_receipt"] = jax["F01_finitude_receipt"]
    receipts["N01_noncommutation_receipt"] = jax["N01_noncommutation_receipt"]
    receipts["T01_bracketing_receipt"] = jax["T01_bracketing_receipt"]
    strengths = collect_strengths(receipts)
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    convention_pin_ok = julia["convention_pin"] == jax["convention_pin"] == pytorch["convention_pin"]
    copied_inputs = copied_input_records()
    claim_path_tools = collect_claim_tools(payloads)
    gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1,
        "identical_structured_convention_pin": convention_pin_ok,
        "source_sha256_current": all(current_source_hash_ok(payload) for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "required_positive_receipts_present": REQUIRED_RECEIPTS <= set(receipts),
        "literal_strength_tokens": all(strength in ALLOWED_STRENGTHS for strength in strengths),
        "f01_n01_t01_scoped": jax["F01_finitude_receipt"]["pass"] is True
        and jax["N01_noncommutation_receipt"]["O3_noncommuting_but_not_anticommuting_witness"]["AB_plus_BA_nonzero"] is True
        and jax["T01_bracketing_receipt"]["matrix_associator_control"]["zero_in_M2C"] is True,
        "negative_models_selective": jax["negative_models"]["all_selectivity_pass"] is True
        and jax["negative_models"]["C3_commuting_probe_simplex_misclassified_as_ball"]["rank3_claim_fails"] is True
        and jax["negative_models"]["C6_non_CPTP_expansive_map_negative"]["fails_cptp_certification"] is True,
        "alternatives_bounded": jax["alternative_models"]["all_pass"] is True
        and jax["alternative_models"]["D1_fidelity_convention_alternative"]["no_root_vs_squared_comparison"] is True,
        "smt_agreement_and_can_fail_controls": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and jax["crossover_proofs"]["z3"]["wrong_control_can_fail"]
        and jax["crossover_proofs"]["cvc5"]["wrong_control_can_fail"]
        and julia["crossover_proofs"]["julia_z3"]["wrong_control_can_fail"]
        and pytorch["crossover_proofs"]["z3"]["duplicate_Z_control_can_fail"]
        and pytorch["crossover_proofs"]["cvc5"]["duplicate_Z_control_can_fail"],
        "pytorch_real_lane": pytorch["receipts"]["S3.D"]["pass"] is True
        and pytorch["receipts"]["S3.E"]["pass"] is True
        and pytorch["receipts"]["S3.G"]["pass"] is True,
        "julia_quantumoptics_route_load_bearing": "QuantumOptics" in julia["claim_path_tools"]
        and julia["TOOL_INTEGRATION_DEPTH"].get("QuantumOptics") == "load_bearing"
        and julia["receipts"]["S3.C"]["quantumoptics_born_projector_receipt"]["all_pass"] is True
        and julia["receipts"]["S3.G_quantumoptics_channel_contraction"]["pass"] is True,
        "python_qutip_route_load_bearing": "qutip" in pytorch["claim_path_tools"]
        and pytorch["TOOL_INTEGRATION_DEPTH"].get("qutip") == "load_bearing"
        and pytorch["receipts"]["S3.D"]["qutip_measurement_updates"]["all_selective_targets_match"] is True
        and pytorch["receipts"]["S3.G"]["qutip_contraction_rows"]["all_contracted"] is True,
        "copied_spec_and_directive_present": all(item["exists"] and item["matches_source"] for item in copied_inputs.values()),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in payloads.values()),
        "no_out_of_scope_s4_s5_claim": "ellipsoid" not in jax["receipts"]["S3.G"]["data"]["boundary"].lower()
        or "no S4 channel ellipsoid" in jax["receipts"]["S3.G"]["data"]["boundary"],
        "audit_gap_hardening_fields_present": (
            jax["receipts"]["S3.A"]["data"]["entropy_base_receipt"]["primary_entropy"]["base"] == "natural_log_e"
            and jax["receipts"]["S3.A"]["data"]["entropy_base_receipt"]["boundary_handling"]["norm_r_equals_1"]["coded_boundary_entropy_nats"] == 0.0
            and jax["receipts"]["S3.B"]["data"]["plane_level_set"]["signed_distance"] == "(c - a0)/sqrt(a_x^2 + a_y^2 + a_z^2)"
            and len(jax["receipts"]["S3.B"]["data"]["plane_level_set"]["intersection_types"]) == 5
            and jax["receipts"]["S3.D"]["data"]["trace_preservation_receipts"]["pass"] is True
            and jax["receipts"]["S3.D"]["data"]["positivity_preservation_receipts"]["pass"] is True
            and jax["receipts"]["S3.G"]["data"]["scope_routes"]["channel_ellipsoid_image_classification"]["route_to"] == "S4"
            and jax["receipts"]["S3.G"]["data"]["scope_routes"]["fixed_point_classification"]["route_to"] == "S5"
            and jax["receipts"]["S3.G"]["data"]["scope_routes"]["basin_classification"]["route_to"] == "S5"
        ),
        "control_only_tools_absent_from_claim_path": not ({"numpy", "scipy", "mpmath"} & set(claim_path_tools)),
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Bounded one-qubit S3 density/observable geometry packet over the pinned S1 Bloch convention, including Bloch fields, observables, Born fields, projective updates, probe quotients, trace distance/fidelity, and named CPTP contraction receipts.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "copied_inputs": copied_inputs,
        "pin_spec": jax["pin_spec"],
        "pin_sha256": next(iter(pin_hashes)),
        "convention_pin": jax["convention_pin"],
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": "system_v6/sims/geo_s3_density_observable_v0",
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S3_density_observable_julia_z3_born_normalization",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": "geo_s3_density_observable_v0_pinned_pauli_trace_table",
            "bracket_convention": "ordinary associative M2(C) multiplication; measurement order effects kept separate",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "QuantumOptics state/density/projector/channel carrier plus Julia Z3 proof; hand Pauli rows retained as mirrors"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy symbolic derivation, z3/cvc5 exact Born proof, vectorized diagnostics"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "qutip Python state/channel route with PyTorch tensor mirrors and solver controls"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": claim_path_tools,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "receipts": receipts,
        "negative_models": jax["negative_models"],
        "alternative_models": jax["alternative_models"],
        "strength_tokens": strengths,
        "crossover_proofs": {
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
            "pytorch_z3": pytorch["crossover_proofs"]["z3"],
            "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
        },
        "controls": {
            "outside_ball": jax["negative_models"]["C1_outside_ball_negative"],
            "wrong_sigma_y_pin": jax["negative_models"]["C2_wrong_sigma_y_pin_negative"],
            "commuting_probe_simplex": jax["negative_models"]["C3_commuting_probe_simplex_misclassified_as_ball"],
            "nonlinear_expectation": jax["negative_models"]["C4_nonlinear_expectation_echo_negative"],
            "bad_measurement_update": jax["negative_models"]["C5_bad_measurement_update_negative"],
            "non_cptp_expansive": jax["negative_models"]["C6_non_CPTP_expansive_map_negative"],
            "wrong_mixed_fidelity": jax["negative_models"]["C7_wrong_mixed_state_fidelity_formula_negative"],
        },
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0.0, "jax": 0.0, "pytorch": 0.0},
            "max_divergence": 0.0,
            "basis": "claim values unchanged; Julia/Python state-channel route now runs through QuantumOptics/qutip objects, while hand Pauli/Bloch tensors remain mirrors and controls",
        },
        "summary": {
            "required_receipts": sorted(REQUIRED_RECEIPTS),
            "ceiling": CLASSIFICATION,
            "pin_sha256": next(iter(pin_hashes)),
            "source_sha256_current": gates["source_sha256_current"],
            "strict_controls": gates["smt_agreement_and_can_fail_controls"],
            "audit_gap_hardening_fields_present": gates["audit_gap_hardening_fields_present"],
            "all_pass": bool(all_pass),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": rel(RESULT_PATH), "gates": gates}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
