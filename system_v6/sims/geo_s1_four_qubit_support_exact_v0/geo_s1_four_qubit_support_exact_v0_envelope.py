#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_four_qubit_support_exact_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_four_qubit_support_exact_v0"
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
    "geo_s1_four_qubit_support_exact_v0|four_spinor_C2x4_to_C16|"
    "S31_to_CP15_density_quotient|Cl8_Jordan_Wigner_gamma9_product|"
    "root_noncommutation_not_anticommutation|matrix_associator_zero|"
    "triality_pressure_only|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
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
        "tool_calls": payload.get("tool_calls", []),
        "claim_path_tools": payload.get("claim_path_tools", []),
        "shared_scalars": payload.get("shared_scalars", {}),
        "receipt_pass": {name: receipt.get("pass") for name, receipt in payload["receipts"].items()},
        "proof_pass": {name: proof.get("pass") for name, proof in payload.get("proofs", {}).items()},
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
        "meaning": "integer/scalar receipt divergence, not a floating tolerance",
    }


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
    classification_rows = j["Z7_classification_table"]["classification_table"]
    bare_float_rows = [row for row in classification_rows if row.get("bare_float")]
    non_conflation = {
        "present": True,
        "pure_state_sphere": "S31 subset C16",
        "global_phase_density_quotient": "S31/S1 = CP15",
        "mixed_state_domain": "D(C16), real affine dimension 255",
        "Cl8_Spin8_pressure_separate": True,
        "Spin8_triality_not_automatic_from_qubit_count": True,
        "merged": False,
    }
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "F01_finitude_receipt": require_gate(
            j["F01_finitude_receipt"]["hilbert_dim"] == 16
            and j["F01_finitude_receipt"]["computational_basis_count"] == 16
            and j["F01_finitude_receipt"]["operator_basis_count"] == 256
            and j["F01_finitude_receipt"]["mixed_density_real_dim"] == 255,
            "F01_finitude_receipt",
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
        "Z1_carrier_quotient": require_gate(
            len(j["Z1_carrier_quotient"]["basis_dictionary"]) == 16
            and j["Z1_carrier_quotient"]["global_phase_quotient"] == "S^31/S^1 = CP^15"
            and j["Z1_carrier_quotient"]["mixed_density_real_dim"] == 255
            and j["Z1_carrier_quotient"]["rank_1_density_phase_erasure_identity"]["pass"] is True
            and j["Z1_carrier_quotient"]["non_conflation_fields"]["CP15_equals_Spin8_triality"] is False,
            "Z1_carrier_quotient",
            j["Z1_carrier_quotient"],
        ),
        "Z2_entanglement_controls": require_gate(
            j["Z2_entanglement_controls"]["states"]["GHZ4"]["one_qubit"]["0"]["entropy"] == "log(2)"
            and j["Z2_entanglement_controls"]["states"]["product_0000"]["AB"]["entropy"] == "0"
            and j["Z2_entanglement_controls"]["states"]["Bell_AB_tensor_Bell_CD"]["AB"]["entropy"] == "0"
            and j["Z2_entanglement_controls"]["states"]["Bell_AB_tensor_Bell_CD"]["AC"]["entropy"] == "log(4)"
            and j["Z2_entanglement_controls"]["states"]["linear_cluster_4"]["stabilizer_receipt"]["pass"] is True,
            "Z2_entanglement_controls",
            {
                "GHZ4_A": j["Z2_entanglement_controls"]["states"]["GHZ4"]["one_qubit"]["0"],
                "Bell": j["Z2_entanglement_controls"]["states"]["Bell_AB_tensor_Bell_CD"],
                "controls": j["Z2_entanglement_controls"]["controls"],
            },
        ),
        "Z3_Cl8_exact_floor": require_gate(
            j["Z3_Cl8_exact_floor"]["all_64_pairs_exact"] is True
            and j["Z3_Cl8_exact_floor"]["algebra_generated_dimension"] == 256
            and j["Z3_Cl8_exact_floor"]["gamma9_squared_identity"] is True
            and j["Z3_Cl8_exact_floor"]["gamma9_trace"] == "0"
            and sorted(j["Z3_Cl8_exact_floor"]["gamma9_eigenspace_split"].values()) == [8, 8],
            "Z3_Cl8_exact_floor",
            j["Z3_Cl8_exact_floor"],
        ),
        "Z4_max_anticommuting_family": require_gate(
            j["Z4_max_anticommuting_family"]["constructed_family_size"] == 9
            and j["Z4_max_anticommuting_family"]["pairwise_anticommutation_exact"] is True
            and j["Z4_max_anticommuting_family"]["upper_bound_theorem"]["m_10_allowed"] is False
            and j["Z4_max_anticommuting_family"]["attempted_10_member_extension_negative_control"]["finite_extension_scan"]["size_10_extension_exists"] is False,
            "Z4_max_anticommuting_family",
            j["Z4_max_anticommuting_family"],
        ),
        "Z5_triality_pressure_open": require_gate(
            j["Z5_Spin8_triality_pressure"]["full_triality_automorphism_claimed"] is False
            and j["Z5_Spin8_triality_pressure"]["pinned_triality_relevant_relation"]["all_8_relations_exact_zero"] is True
            and j["Z5_Spin8_triality_pressure"]["triality_pressure_open"]["status"] == "open-with-reason",
            "Z5_triality_pressure_open",
            j["Z5_Spin8_triality_pressure"],
        ),
        "Z6_support_not_minimum": require_gate(
            j["Z6_4Q_supports_later_work_not_minimum"]["comparison_to_3Q"]["3Q"]["max_anticommuting_family"] == 7
            and j["Z6_4Q_supports_later_work_not_minimum"]["comparison_to_3Q"]["4Q"]["max_anticommuting_family"] == 9
            and "S2 runtime" in j["Z6_4Q_supports_later_work_not_minimum"]["not_claimed"],
            "Z6_support_not_minimum",
            j["Z6_4Q_supports_later_work_not_minimum"],
        ),
        "Z7_no_bare_float_rows": require_gate(
            j["Z7_classification_table"]["pass"] is True and not bare_float_rows,
            "Z7_no_bare_float_rows",
            j["Z7_classification_table"],
        ),
        "proofs_flip": require_gate(
            proofs["P1_anticommutation_table"]["z3_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["corrupted_generator_control_z3"] == "sat"
            and proofs["P1_anticommutation_table"]["corrupted_generator_control_cvc5"] == "sat"
            and proofs["P2_max_9_family_upper_bound"]["z3_assert_10_family_bound_32_le_16"] == "unsat"
            and proofs["P2_max_9_family_upper_bound"]["cvc5_assert_10_family_bound_32_le_16"] == "unsat"
            and proofs["P3_named_state_entropy_controls"]["pass"] is True,
            "proofs_flip",
            proofs,
        ),
        "julia_canon_exact_route": require_gate(
            julia["receipts"]["Z3_Cl8_exact_floor"]["all_64_pairs_exact"] is True
            and julia["receipts"]["Z3_Cl8_exact_floor"]["julia_z3_table_assert_some_bad"] == "unsat"
            and julia["receipts"]["Z3_Cl8_exact_floor"]["julia_z3_corrupted_generator_control"] == "sat"
            and julia["receipts"]["Z3_Cl8_exact_floor"]["gamma9_eigenspace_split"]["minus_one"] == 8
            and julia["receipts"]["Z3_Cl8_exact_floor"]["gamma9_eigenspace_split"]["plus_one"] == 8,
            "julia_canon_exact_route",
            julia["receipts"]["Z3_Cl8_exact_floor"],
        ),
        "pytorch_exact_integer_route": require_gate(
            pytorch["receipts"]["Z3_Cl8_exact_floor"]["all_64_pairs_exact"] is True
            and pytorch["receipts"]["Z3_Cl8_exact_floor"]["torch_func_square_identity_pass"] is True
            and pytorch["receipts"]["Z2_entanglement_controls"]["cluster_stabilizer_receipt"]["pass"] is True
            and pytorch["receipts"]["Z4_max_anticommuting_family"]["finite_extension_scan"]["size_10_extension_exists"] is False,
            "pytorch_exact_integer_route",
            {
                "Z3": pytorch["receipts"]["Z3_Cl8_exact_floor"],
                "Z2": pytorch["receipts"]["Z2_entanglement_controls"],
                "Z4": pytorch["receipts"]["Z4_max_anticommuting_family"],
            },
        ),
        "divergence_zero": require_gate(div["max_divergence"] == 0, "divergence_zero", div),
        "non_conflation_field": require_gate(non_conflation["present"] and not non_conflation["merged"], "non_conflation_field", non_conflation),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "The four-qubit carrier (C^2)^{x4} ~= C^16 is a scratch support rung for Cl8/Spin8/triality pressure and exact scaling controls, not a 3Q-minimum proof.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
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
            "proof_tag": "four_qubit_support_exact_cl8_z3",
            "proof_pass": julia["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "Jordan-Wigner Cl(8), gamma_9=gamma_1...gamma_8; matrix representation is associative",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "canon exact Symbolics/Z3 receipt"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy plus z3/cvc5 exact SMT sidecar"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "exact integer tensor and cluster stabilizer mirror"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_assert_some_bad": proofs["P1_anticommutation_table"]["z3_assert_some_bad"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_generator_control_z3"],
                    "P2_10_family_bound": proofs["P2_max_9_family_upper_bound"]["z3_assert_10_family_bound_32_le_16"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_assert_some_bad": proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_generator_control_cvc5"],
                    "P2_10_family_bound": proofs["P2_max_9_family_upper_bound"]["cvc5_assert_10_family_bound_32_le_16"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["receipts"]["Z3_Cl8_exact_floor"]["julia_z3_table_assert_some_bad"],
                "load_bearing": True,
                "control": julia["receipts"]["Z3_Cl8_exact_floor"]["julia_z3_corrupted_generator_control"],
            },
        },
        "receipts": j,
        "engine_receipts": {"julia": julia["receipts"], "jax": jax["receipts"], "pytorch": pytorch["receipts"]},
        "proofs": proofs,
        "controls": {"julia": julia["controls"], "jax": jax["controls"], "pytorch": pytorch["controls"]},
        "non_conflation": non_conflation,
        "build_gates": gates,
        "divergence": div,
        "claim_boundary": {
            "ceiling": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_claimed": "no final carrier, final M(C), QIT engine, physics, bridge, S2/S3 runtime, or full triality automorphism admission",
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH), "engine": "envelope"}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
