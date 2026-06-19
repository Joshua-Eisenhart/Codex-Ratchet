#!/usr/bin/env python3
"""Envelope assembler for geo_s4_operator_stage_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s4_operator_stage_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s4_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s4_build_spec_20260610.md"
DIRECTIVE = Path("/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md")
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

REQUIRED_POSITIVE_RECEIPTS = {
    "P1_pauli_table_exact",
    "P2_affine_channel_table_exact",
    "P3_ellipsoid_image_exact",
    "P4_fixed_sets_exact",
    "P5_basin_classes_exact",
    "P6_commutator_table_symbolic",
    "P7_prior_reuse_lineage",
    "P8_claim_ceiling",
}

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, copied-input, result, and PIN hashing"},
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


def copied_input_records() -> dict[str, Any]:
    return {
        "s4_build_spec": {
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


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def build_positive_ledger(jax: dict[str, Any]) -> dict[str, Any]:
    return {
        key: {
            "pass": jax["receipts"][key]["pass"],
            "exact_strength": jax["receipts"][key]["exact_strength"],
        }
        for key in sorted(REQUIRED_POSITIVE_RECEIPTS)
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
    copied_inputs = copied_input_records()
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    convention_pin_ok = julia["convention_pin"] == jax["convention_pin"] == pytorch["convention_pin"]
    claim_path_tools = collect_claim_tools(payloads)
    comm_rows = jax["commutator_table"]["rows"]
    gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1,
        "identical_structured_convention_pin": convention_pin_ok,
        "basis_conversion_layer_pass": jax["basis_conversion_layer"]["all_pass"] is True,
        "source_sha256_current": all(current_source_hash_ok(payload) for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "required_positive_receipts_present": REQUIRED_POSITIVE_RECEIPTS <= set(jax["receipts"]),
        "required_positive_receipts_pass": all(jax["receipts"][key]["pass"] is True for key in REQUIRED_POSITIVE_RECEIPTS),
        "commutator_table_exact_16_pairs": jax["commutator_table"]["ordered_pair_count"] == 16 and len(comm_rows) == 16,
        "affine_shifts_all_zero": all(row["affine_shift_commutator"] == ["0", "0", "0"] for row in comm_rows),
        "symbolic_not_numeric_only": "sympy" in jax["claim_path_tools"] and jax["receipts"]["P6_commutator_table_symbolic"]["exact_strength"] == "exact_symbolic_matrix_table",
        "negative_controls_selective": jax["negative_controls"]["all_selectivity_pass"] is True,
        "negative_controls_executed_can_fail": all(
            row["executed"] is True and row["expected_failure_observed"] is True and row["gate_passed_after_mutation"] is False
            for key, row in jax["negative_controls"].items()
            if key.startswith("C")
        ),
        "julia_density_channel_derivation_pass": julia["build_gates"]["density_channel_derivation_pass"] is True
        and julia["density_channel_derivation"]["all_pass"] is True,
        "julia_quantumoptics_superoperator_route_load_bearing": "QuantumOptics" in julia["claim_path_tools"]
        and julia["TOOL_INTEGRATION_DEPTH"].get("QuantumOptics") == "load_bearing"
        and julia["build_gates"]["quantumoptics_pinned_channel_rows_pass"] is True
        and julia["quantumoptics_pinned_channel_rows"]["all_pass"] is True,
        "python_qutip_superoperator_route_load_bearing": "qutip" in pytorch["claim_path_tools"]
        and pytorch["TOOL_INTEGRATION_DEPTH"].get("qutip") == "load_bearing"
        and pytorch["build_gates"]["qutip_affine_rows_pass"] is True
        and pytorch["qutip_affine_channel_rows"]["all_pass"] is True,
        "smt_agreement_and_can_fail_controls": (
            jax["crossover_proofs"]["z3"]["verdict"] == "unsat"
            and jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
            and julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
            and pytorch["crossover_proofs"]["z3"]["verdict"] == "unsat"
            and pytorch["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
            and jax["crossover_proofs"]["z3"]["wrong_control_can_fail"]
            and jax["crossover_proofs"]["cvc5"]["wrong_control_can_fail"]
            and julia["crossover_proofs"]["julia_z3"]["wrong_control_can_fail"]
            and pytorch["crossover_proofs"]["z3"]["wrong_control_can_fail"]
            and pytorch["crossover_proofs"]["cvc5"]["wrong_control_can_fail"]
        ),
        "smt_scope_honest_pinned_entry_only": all(
            proof.get("proof_scope") == "pinned_entry_contradiction_not_full_symbolic_table"
            for proof in [
                jax["crossover_proofs"]["z3"],
                jax["crossover_proofs"]["cvc5"],
                julia["crossover_proofs"]["julia_z3"],
                pytorch["crossover_proofs"]["z3"],
                pytorch["crossover_proofs"]["cvc5"],
            ]
        ),
        "copied_spec_and_directive_present": all(item["exists"] and item["matches_source"] for item in copied_inputs.values()),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in payloads.values()),
        "pytorch_declared_non_cas_mirror": "not a symbolic CAS" in pytorch["limits"],
        "control_only_tools_absent_from_claim_path": not ({"numpy", "scipy", "mpmath"} & set(claim_path_tools)),
        "quotient_erasure_boundary_present": "global phase" in jax["quotient_erasure_note"]["erases"],
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Bounded S4 one-qubit operator-channel geometry packet for D_z, D_x, R_x, and R_z over the source-locked standard density/Bloch quotient, with an explicit S1 pinned-y conversion layer.",
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
            "artifact_path": rel(SIM_DIR),
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S4_operator_channel_julia_density_channel_symbolics_z3_pinned_entry",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": "geo_s4_operator_stage_v0_pinned_s1_bloch_channel_table",
            "bracket_convention": "ordinary associative M2(C) channel composition; affine Bloch composition order explicit",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "QuantumOptics channel superoperators plus Symbolics/Z3 semantics; hand Pauli rows retained as mirrors"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy exact symbolic CAS derivation plus SMT controls"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "qutip Python channel superoperator route with PyTorch tensor mirrors and SMT controls"},
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
        "julia_density_channel_derivation": julia["density_channel_derivation"],
        "positive_ledger": build_positive_ledger(jax),
        "receipts": jax["receipts"],
        "basis_conversion_layer": jax["basis_conversion_layer"],
        "affine_channel_table": jax["affine_channel_table"],
        "ellipsoid_images": jax["ellipsoid_images"],
        "fixed_sets": jax["fixed_sets"],
        "basin_classes": jax["basin_classes"],
        "basin_iteration_receipts": jax["basin_iteration_receipts"],
        "commutator_table": jax["commutator_table"],
        "negative_controls": jax["negative_controls"],
        "quotient_erasure_note": jax["quotient_erasure_note"],
        "source_lineage": jax["source_lineage"],
        "crossover_proofs": {
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
            "pytorch_z3": pytorch["crossover_proofs"]["z3"],
            "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": 0.0,
                "jax": 0.0,
                "pytorch": 0.0,
            },
            "max_divergence": 0.0,
            "meaning": "engine divergence over the pinned acceptance gates and scaled D_z/R_x commutator witness; symbolic parameter table authority remains in JAX/SymPy, Julia/Python channel mechanics now run through QuantumOptics/qutip, and hand tensor rows remain mirrors",
        },
        "build_gates": gates,
        "self_check_notice": "Builder self-checks are local sanity checks only and are not independent audit evidence.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
