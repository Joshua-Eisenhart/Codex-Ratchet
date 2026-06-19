#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_five_qubit_safety_margin_exact_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_five_qubit_safety_margin_exact_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s1_five_qubit_safety_margin_exact_v0|five_qubit_C32_safety_margin|"
    "S63_to_CP31_density_quotient|Cl10_Jordan_Wigner_gamma11_minus_i_product|"
    "max_family_11_by_clifford_representation_bound|F01_N01_T01_corrected_directive|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independently regenerated lane receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing and pin equality checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "claim_path_tools": payload["claim_path_tools"],
        "shared_scalars": payload["shared_scalars"],
        "receipt_pass": {name: receipt.get("pass") for name, receipt in payload["receipts"].items()},
        "proof_pass": {name: proof.get("pass") for name, proof in payload["proofs"].items()},
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def divergence(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: payload["shared_scalars"] for engine, payload in payloads.items()}
    keys = sorted(set().union(*(set(v) for v in values.values())))
    rows = []
    max_divergence = 0
    for key in keys:
        row_values = {engine: values[engine].get(key) for engine in values}
        exact_match = len(set(row_values.values())) == 1
        rows.append({"key": key, "values": row_values, "exact_match": exact_match})
        if not exact_match:
            max_divergence = 1
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "max_divergence": max_divergence,
        "comparison": {"rows": rows, "exact_match": max_divergence == 0},
    }


def all_status(payloads: dict[str, dict[str, Any]], receipt_name: str) -> dict[str, bool]:
    return {engine: payload["receipts"].get(receipt_name, {}).get("pass") is True for engine, payload in payloads.items()}


def build_result() -> dict[str, Any]:
    payloads = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT), "pytorch": load_json(PYTORCH_RESULT)}
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    j = jax["receipts"]
    proofs = jax["proofs"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    div = divergence(payloads)
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    required_receipts = [
        "F01_finitude_receipt",
        "N01_noncommutation_receipt",
        "T01_bracketing_receipt",
        "W1_carrier_quotient",
        "W2_Cl10_exact_floor",
        "W3_max_anticommuting_family",
        "W4_validator_scaling",
        "W5_named_state_controls",
        "W6_no_new_minimum_boundary",
        "W7_classification_table",
    ]
    receipt_matrix = {name: all_status(payloads, name) for name in required_receipts}
    source_backing_declared = {
        engine: {
            "source_path": payload["source_path"],
            "packages_used": payload["packages_used"],
            "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        }
        for engine, payload in payloads.items()
    }
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "root_receipts_present_all_engines": require_gate(
            all(all(statuses.values()) for statuses in receipt_matrix.values()),
            "root_receipts_present_all_engines",
            receipt_matrix,
        ),
        "F01_exact_finitude": require_gate(
            j["F01_finitude_receipt"]["hilbert_dim"] == 32
            and j["F01_finitude_receipt"]["computational_basis_count"] == 32
            and j["F01_finitude_receipt"]["operator_basis_count"] == 1024
            and j["F01_finitude_receipt"]["mixed_density_real_dim"] == 1023
            and j["F01_finitude_receipt"]["active_probe_family_count"]["arbitrary_dense_clique_enumeration"] == "not_used",
            "F01_exact_finitude",
            j["F01_finitude_receipt"],
        ),
        "N01_noncommutation_not_collapsed": require_gate(
            j["N01_noncommutation_receipt"]["O3_noncommuting_but_not_anticommuting_witness"]["AB_minus_BA_nonzero"] is True
            and j["N01_noncommutation_receipt"]["O3_noncommuting_but_not_anticommuting_witness"]["AB_plus_BA_nonzero"] is True
            and j["N01_noncommutation_receipt"]["O4_anticommuting_Clifford_witness"]["AB_plus_BA_zero"] is True
            and j["N01_noncommutation_receipt"]["O6_Clifford_family_capacity_row_kept_separate"]["not_collapsed"] is True,
            "N01_noncommutation_not_collapsed",
            j["N01_noncommutation_receipt"],
        ),
        "T01_associator_boundary": require_gate(
            j["T01_bracketing_receipt"]["matrix_associator_control"]["failures"] == 0
            and j["T01_bracketing_receipt"]["schedule_or_channel_associator_test"]["status"] == "not_scoped"
            and "octonion" in j["T01_bracketing_receipt"]["octonion_lane_boundary_statement"],
            "T01_associator_boundary",
            j["T01_bracketing_receipt"],
        ),
        "W1_carrier_quotient": require_gate(
            j["W1_carrier_quotient"]["basis_dictionary"]["|00000>"] == 0
            and j["W1_carrier_quotient"]["basis_dictionary"]["|11111>"] == 31
            and j["W1_carrier_quotient"]["phase_erasure_symbolic_proof"]["pass"] is True
            and j["W1_carrier_quotient"]["mixed_state_domain"]["real_affine_dimension"] == 1023,
            "W1_carrier_quotient",
            j["W1_carrier_quotient"],
        ),
        "W2_Cl10_exact": require_gate(
            j["W2_Cl10_exact_floor"]["all_100_pairs_exact"] is True
            and j["W2_Cl10_exact_floor"]["gamma11_squared_identity"] is True
            and j["W2_Cl10_exact_floor"]["gamma11_trace"] == "0"
            and sorted(j["W2_Cl10_exact_floor"]["gamma11_eigenspace_split"].values()) == [16, 16]
            and j["W2_Cl10_exact_floor"]["gamma11_equals_ZZZZZ"] is True
            and pytorch["receipts"]["W2_Cl10_exact_floor"]["pytorch_exact_integer_tensor_mirror"]["pass"] is True,
            "W2_Cl10_exact",
            {"jax": j["W2_Cl10_exact_floor"], "pytorch_mirror": pytorch["receipts"]["W2_Cl10_exact_floor"]["pytorch_exact_integer_tensor_mirror"]},
        ),
        "W3_max_family_11": require_gate(
            j["W3_max_anticommuting_family"]["constructed_pairwise_anticommuting"] is True
            and j["W3_max_anticommuting_family"]["attempted_12_member_extension_negative_control"]["status"] == "theorem_blocked"
            and proofs["P2_max_family_bound"]["z3_no_12_member_family_by_representation_bound"] == "unsat"
            and proofs["P2_max_family_bound"]["z3_11_member_boundary_control"] == "sat",
            "W3_max_family_11",
            j["W3_max_anticommuting_family"],
        ),
        "W4_scaling_honest": require_gate(
            j["W4_validator_scaling"]["resource_rows"]["full_nonidentity_clique_enumeration"] == "not_run"
            and j["W4_validator_scaling"]["resource_rows"]["gamma_anticommutator_pairs_exact"] == 100,
            "W4_scaling_honest",
            j["W4_validator_scaling"],
        ),
        "W5_named_states_exact": require_gate(
            j["W5_named_state_controls"]["GHZ5"]["entropy_qubit_0"] == "log(2)"
            and j["W5_named_state_controls"]["product"]["entropy_qubit_0"] == "0"
            and j["W5_named_state_controls"]["Bell_pair_plus_spectators"]["entropy_qubits_0_1"] == "0"
            and j["W5_named_state_controls"]["scope_boundary"]["full_5_party_entanglement_classification"] == "not_scoped",
            "W5_named_states_exact",
            j["W5_named_state_controls"],
        ),
        "W6_no_new_minimum": require_gate(
            j["W6_no_new_minimum_boundary"]["negative_control_against_5Q_minimum_overclaim"]["verdict"] == "rejected"
            and j["W6_no_new_minimum_boundary"]["negative_control_against_5Q_minimum_overclaim"]["z3_5_equals_3_control"] == "unsat",
            "W6_no_new_minimum",
            j["W6_no_new_minimum_boundary"],
        ),
        "proofs_flip": require_gate(
            proofs["P1_anticommutation_table"]["z3_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["corrupted_gamma_control_z3"] == "sat"
            and proofs["P1_anticommutation_table"]["corrupted_gamma_control_cvc5"] == "sat"
            and proofs["P2_max_family_bound"]["z3_no_12_member_family_by_representation_bound"] == "unsat"
            and proofs["P2_max_family_bound"]["cvc5_no_12_member_family_by_representation_bound"] == "unsat"
            and proofs["P3_named_state_controls"]["z3_product_GHZ_label_swap_detected"] == "unsat"
            and proofs["P3_named_state_controls"]["cvc5_product_GHZ_label_swap_detected"] == "unsat",
            "proofs_flip",
            proofs,
        ),
        "exact_strength_no_bare_float_rows": require_gate(
            all(
                payload["receipts"]["W7_classification_table"]["zero_claim_bearing_bare_float_rows"] is True
                and payload["receipts"]["W7_classification_table"]["invalid_strength_rows"] == []
                for payload in payloads.values()
            ),
            "exact_strength_no_bare_float_rows",
            {engine: payload["receipts"]["W7_classification_table"] for engine, payload in payloads.items()},
        ),
        "cross_engine_shared_scalars_match": require_gate(div["comparison"]["exact_match"] is True, "cross_engine_shared_scalars_match", div),
        "source_backing_declared": require_gate(
            all(payload["aligned_packages_load_bearing"] for payload in payloads.values()),
            "source_backing_declared",
            source_backing_declared,
        ),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "The five-qubit carrier (C^2)^{tensor 5} ~= C^32 is a scratch diagnostic safety-margin rung: it supports S63/CP31, D(C32) dimension 1023, exact Cl10, gamma11 split 16+16, and max anticommuting family 11, while preserving the 3Q minimum-floor boundary.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "five_qubit_safety_margin_exact_cl10_z3",
            "proof_pass": julia["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "Jordan-Wigner Cl(10), gamma11=(-i)^5 gamma1...gamma10; M32(C) matrix multiplication is associative",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "canon exact Symbolics/CliffordAlgebras/Z3 receipt"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": jax["packages_used"], "role": "sympy plus z3/cvc5 exact sidecar"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": pytorch["packages_used"], "role": "torch exact integer tensor mirror plus z3/cvc5/sympy controls"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "allowed_claims": [
            "scratch diagnostic five-qubit safety-margin facts listed in claim",
            "exact negative control that 5Q does not move the 3Q minimum-floor claim",
        ],
        "must_not_claim_fences": [
            "carrier admission",
            "formal admission",
            "final M(C)",
            "QIT-engine admission",
            "physics claim",
            "bridge claim",
            "theorem-of-everything claim",
        ],
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "receipts": {
            "julia": julia["receipts"],
            "jax": jax["receipts"],
            "pytorch": pytorch["receipts"],
        },
        "proofs": {
            "julia": julia["proofs"],
            "jax": jax["proofs"],
            "pytorch": pytorch["proofs"],
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_assert_some_bad": proofs["P1_anticommutation_table"]["z3_assert_some_bad"],
                    "P2_no_12_family": proofs["P2_max_family_bound"]["z3_no_12_member_family_by_representation_bound"],
                    "P3_product_GHZ_label_swap": proofs["P3_named_state_controls"]["z3_product_GHZ_label_swap_detected"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_gamma_control_z3"],
                    "P2_11_boundary_control": proofs["P2_max_family_bound"]["z3_11_member_boundary_control"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_assert_some_bad": proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"],
                    "P2_no_12_family": proofs["P2_max_family_bound"]["cvc5_no_12_member_family_by_representation_bound"],
                    "P3_product_GHZ_label_swap": proofs["P3_named_state_controls"]["cvc5_product_GHZ_label_swap_detected"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_gamma_control_cvc5"],
                    "P2_11_boundary_control": proofs["P2_max_family_bound"]["cvc5_11_member_boundary_control"],
                },
            },
            "julia_z3": {"ran": True, "verdict": "unsat", "load_bearing": True, "proofs": julia["proofs"]["P1_anticommutation_table"]},
            "pytorch_z3": {"ran": True, "verdict": "unsat", "load_bearing": True, "proofs": pytorch["proofs"]["P1_anticommutation_table"]},
            "pytorch_cvc5": {"ran": True, "verdict": "unsat", "load_bearing": True, "proofs": pytorch["proofs"]["P1_anticommutation_table"]},
        },
        "gate_pass": gates,
        "divergence": div,
        "blind_audit_expected_values": jax["blind_audit_expected_values"],
        "builder_self_check_is_evidence": False,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
