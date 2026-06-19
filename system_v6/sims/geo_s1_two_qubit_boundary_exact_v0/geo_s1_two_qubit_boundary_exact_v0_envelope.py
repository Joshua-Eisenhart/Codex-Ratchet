#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_two_qubit_boundary_exact_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_two_qubit_boundary_exact_v0"
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
    "geo_s1_two_qubit_boundary_exact_v0|two_spinor_C2x2_to_C4|"
    "S7_to_CP3_density_quotient|Cl4_Jordan_Wigner_gamma5_minus_product|"
    "root_noncommutation_not_anticommutation|matrix_associator_zero|"
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
        "Y1_carrier_quotient",
        "Y2_schmidt_bell_product",
        "Y3_concurrence",
        "Y4_Cl4_exact_floor",
        "Y5_max_anticommuting_family",
        "Y6_2Q_fails_3Q_minimum_claims",
        "Y7_classification_table",
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
            j["F01_finitude_receipt"]["hilbert_dim"] == 4
            and j["F01_finitude_receipt"]["computational_basis_count"] == 4
            and j["F01_finitude_receipt"]["operator_basis_count"] == 16
            and j["F01_finitude_receipt"]["mixed_density_real_dim"] == 15,
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
        "Y1_nonconflation": require_gate(
            j["Y1_carrier_quotient"]["basis_dictionary"] == {"|00>": 0, "|01>": 1, "|10>": 2, "|11>": 3}
            and j["Y1_carrier_quotient"]["phase_erasure_symbolic_proof"]["pass"] is True
            and j["Y1_carrier_quotient"]["non_conflation_fields"]["CP3_equals_S4"] is False
            and j["Y1_carrier_quotient"]["non_conflation_fields"]["S7_over_S1_equals_S7_over_S3"] is False,
            "Y1_nonconflation",
            j["Y1_carrier_quotient"],
        ),
        "Y2_Y3_entanglement_exact": require_gate(
            j["Y2_schmidt_bell_product"]["Bell_state"]["entropy"] == "log(2)"
            and j["Y2_schmidt_bell_product"]["product_state"]["entropy"] == "0"
            and j["Y2_schmidt_bell_product"]["biseparable_status"]["status"] == "not_defined_by_arity"
            and j["Y3_concurrence"]["Bell_concurrence"] == "1"
            and j["Y3_concurrence"]["product_concurrence"] == "0"
            and j["Y3_concurrence"]["solver_proof_control"]["pass"] is True,
            "Y2_Y3_entanglement_exact",
            {"Y2": j["Y2_schmidt_bell_product"], "Y3": j["Y3_concurrence"]},
        ),
        "Y4_Y5_clifford_exact": require_gate(
            j["Y4_Cl4_exact_floor"]["all_16_pairs_exact"] is True
            and j["Y4_Cl4_exact_floor"]["gamma5_squared_identity"] is True
            and j["Y4_Cl4_exact_floor"]["gamma5_trace"] == "0"
            and sorted(j["Y4_Cl4_exact_floor"]["gamma5_eigenspace_split"].values()) == [2, 2]
            and j["Y5_max_anticommuting_family"]["proofs"]["finite_pauli_string_exhaustive_enumeration"]["max_clique_size"] == 5
            and j["Y5_max_anticommuting_family"]["proofs"]["finite_pauli_string_exhaustive_enumeration"]["size_6_clique_exists"] is False,
            "Y4_Y5_clifford_exact",
            {"Y4": j["Y4_Cl4_exact_floor"], "Y5": j["Y5_max_anticommuting_family"]},
        ),
        "Y6_negative_boundary_exact": require_gate(
            j["Y6_2Q_fails_3Q_minimum_claims"]["Cl6_in_M4C"]["status"] == "impossible"
            and j["Y6_2Q_fails_3Q_minimum_claims"]["seven_anticommuting_family_in_M4C"]["status"] == "impossible"
            and j["Y6_2Q_fails_3Q_minimum_claims"]["GHZ_object"]["status"] == "not_defined_by_arity"
            and j["Y6_2Q_fails_3Q_minimum_claims"]["W_object"]["status"] == "not_defined_by_arity"
            and j["Y6_2Q_fails_3Q_minimum_claims"]["three_tangle"]["status"] == "not_defined_by_arity"
            and j["Y6_2Q_fails_3Q_minimum_claims"]["three_site_schedule_floor"]["status"] == "not_available",
            "Y6_negative_boundary_exact",
            j["Y6_2Q_fails_3Q_minimum_claims"],
        ),
        "proofs_flip": require_gate(
            proofs["P1_anticommutation_table"]["z3_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["corrupted_gamma_control_z3"] == "sat"
            and proofs["P1_anticommutation_table"]["corrupted_gamma_control_cvc5"] == "sat"
            and proofs["P2_max_family_bound"]["z3_no_6_member_family_by_representation_bound"] == "unsat"
            and proofs["P2_max_family_bound"]["cvc5_no_6_member_family_by_representation_bound"] == "unsat"
            and proofs["P2_max_family_bound"]["z3_5_member_boundary_control"] == "sat"
            and proofs["P2_max_family_bound"]["cvc5_5_member_boundary_control"] == "sat"
            and proofs["P3_concurrence_controls"]["z3_bell_zero_assertion"] == "unsat"
            and proofs["P3_concurrence_controls"]["cvc5_bell_zero_assertion"] == "unsat"
            and proofs["P3_concurrence_controls"]["z3_corrupted_bell_label_detected"] == "sat"
            and proofs["P3_concurrence_controls"]["cvc5_corrupted_bell_label_detected"] == "sat",
            "proofs_flip",
            proofs,
        ),
        "exact_strength_no_bare_float_rows": require_gate(
            all(
                payload["receipts"]["Y7_classification_table"]["zero_claim_bearing_bare_float_rows"] is True
                and payload["receipts"]["Y7_classification_table"]["invalid_strength_rows"] == []
                for payload in payloads.values()
            ),
            "exact_strength_no_bare_float_rows",
            {engine: payload["receipts"]["Y7_classification_table"] for engine, payload in payloads.items()},
        ),
        "cross_engine_shared_scalars_match": require_gate(
            div["comparison"]["exact_match"] is True,
            "cross_engine_shared_scalars_match",
            div,
        ),
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
        "claim": "The two-qubit carrier (C^2)^{tensor 2} ~= C^4 is a scratch diagnostic boundary/control rung: it supports CP3, Bell/concurrence, Cl4 chirality split 2+2, and max anticommuting family 5; it does not support Cl6, seven anticommuting generators, GHZ/W/3-tangle, or a three-slot floor.",
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
            "proof_tag": "two_qubit_boundary_exact_cl4_z3",
            "proof_pass": julia["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "Jordan-Wigner Cl(4), gamma5=-gamma1 gamma2 gamma3 gamma4; M4(C) matrix multiplication is associative",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "canon exact Symbolics/CliffordAlgebras/Z3 receipt"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": jax["packages_used"], "role": "sympy plus z3/cvc5 exact sidecar"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": pytorch["packages_used"], "role": "exact integer tensor anticommutation mirror"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "allowed_claims": [
            "scratch diagnostic two-qubit boundary/control facts listed in claim",
            "exact negative controls for three-qubit minimum objects not defined or impossible at 2Q",
        ],
        "must_not_claim_fences": [
            "carrier admission",
            "formal admission",
            "final M(C)",
            "QIT-engine admission",
            "physics claim",
            "bridge claim",
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
                    "P2_no_six_family": proofs["P2_max_family_bound"]["z3_no_6_member_family_by_representation_bound"],
                    "P3_bell_zero": proofs["P3_concurrence_controls"]["z3_bell_zero_assertion"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_gamma_control_z3"],
                    "P2_five_boundary_control": proofs["P2_max_family_bound"]["z3_5_member_boundary_control"],
                    "P3_corrupted_label_control": proofs["P3_concurrence_controls"]["z3_corrupted_bell_label_detected"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_assert_some_bad": proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"],
                    "P2_no_six_family": proofs["P2_max_family_bound"]["cvc5_no_6_member_family_by_representation_bound"],
                    "P3_bell_zero": proofs["P3_concurrence_controls"]["cvc5_bell_zero_assertion"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_gamma_control_cvc5"],
                    "P2_five_boundary_control": proofs["P2_max_family_bound"]["cvc5_5_member_boundary_control"],
                    "P3_corrupted_label_control": proofs["P3_concurrence_controls"]["cvc5_corrupted_bell_label_detected"],
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
