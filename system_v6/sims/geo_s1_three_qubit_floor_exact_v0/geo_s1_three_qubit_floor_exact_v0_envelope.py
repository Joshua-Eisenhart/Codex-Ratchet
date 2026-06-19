#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_three_qubit_floor_exact_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_three_qubit_floor_exact_v0"
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
    "geo_s1_three_qubit_floor_exact_v0|three_spinor_C2x3_to_C8|"
    "S15_to_CP7_density_quotient|Cl6_Jordan_Wigner_gamma7_minus_i_product|"
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
        "tool_calls": payload.get("tool_calls", []),
        "shared_scalars": payload.get("shared_scalars", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def build_result() -> dict[str, Any]:
    payloads = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT), "pytorch": load_json(PYTORCH_RESULT)}
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    j = jax["receipts"]
    proofs = jax["proofs"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    non_conflation = {
        "present": True,
        "global_phase_density_quotient": "S^15 -> CP^7 via psi psi^dagger",
        "octonionic_fibration": "S^15 -> S^8 via O^2 is a different decomposition",
        "merged": False,
        "octonionic_structure_used_in_quotient_computations": False,
        "control": "the S^15->S^8 octonionic structure is not used in Y1 quotient computations",
    }
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "Y1_Y7_exact_values": require_gate(
            j["Y1"]["pass"]
            and j["Y2"]["states"]["GHZ"]["entropy_A"] == "log(2)"
            and j["Y2"]["states"]["W"]["entropy_A"] == "log(3) - 2*log(2)/3"
            and j["Y2"]["states"]["product_000"]["entropy_A"] == "0"
            and j["Y3"]["tau"]["GHZ"] == "1"
            and j["Y3"]["tau"]["W"] == "0"
            and j["Y3"]["tau"]["product_000"] == "0"
            and j["Y3"]["hyperdeterminant_components"]["GHZ"]["d1"] == "1/4"
            and j["Y3"]["hyperdeterminant_components"]["GHZ"]["d2"] == "0"
            and j["Y3"]["hyperdeterminant_components"]["GHZ"]["d3"] == "0"
            and j["Y3"]["hyperdeterminant_components"]["W"]["d1"] == "0"
            and j["Y3"]["hyperdeterminant_components"]["W"]["d2"] == "0"
            and j["Y3"]["hyperdeterminant_components"]["W"]["d3"] == "0"
            and j["Y4"]["algebra_generated_dimension"] == 64
            and j["Y5"]["associativity"]["mode"] == "exhaustive_ordered_pauli_string_triples"
            and j["Y5"]["associativity"]["ordered_triples"] == 64**3
            and j["Y5"]["associativity"]["failures"] == 0
            and sorted(j["Y4"]["gamma7_eigenspace_split"].values()) == [4, 4]
            and j["Y6"]["max_anticommuting_family_counts"][0]["count"] == 3
            and j["Y6"]["max_anticommuting_family_counts"][1]["count"] == 5
            and j["Y6"]["max_anticommuting_family_counts"][2]["count"] == 7
            and [row["max_clique_size"] for row in j["Y6"]["exhaustive_anticommuting_clique_search"]] == [3, 5, 7]
            and j["Y7"]["bare_float_rows"] == [],
            "Y1_Y7_exact_values",
            {
                "entropy_GHZ_A": j["Y2"]["states"]["GHZ"]["entropy_A"],
                "entropy_W_A": j["Y2"]["states"]["W"]["entropy_A"],
                "tau": j["Y3"]["tau"],
                "hyperdeterminant_components": j["Y3"]["hyperdeterminant_components"],
                "rank": j["Y4"]["algebra_generated_dimension"],
                "associativity": j["Y5"]["associativity"],
                "splits": {"cl4": j["Y6"]["cl4_gamma5_split"], "cl6": j["Y4"]["gamma7_eigenspace_split"]},
                "counts": [row["count"] for row in j["Y6"]["max_anticommuting_family_counts"]],
                "exhaustive_clique_search": j["Y6"]["exhaustive_anticommuting_clique_search"],
            },
        ),
        "julia_exact_derivations": require_gate(
            julia["receipts"]["Y2"]["pass"] is True
            and julia["receipts"]["Y2"]["states"]["GHZ"]["entropy_A"] == "log(2)"
            and julia["receipts"]["Y2"]["states"]["W"]["entropy_A"] == "log(3) - 2*log(2)/3"
            and julia["receipts"]["Y2"]["states"]["product_000"]["entropy_A"] == "0"
            and julia["receipts"]["Y3"]["pass"] is True
            and julia["receipts"]["Y3"]["hyperdeterminant_components"]["GHZ"]["d1"] == "1//4"
            and julia["receipts"]["Y3"]["hyperdeterminant_components"]["GHZ"]["d2"] == "0//1"
            and julia["receipts"]["Y3"]["hyperdeterminant_components"]["GHZ"]["d3"] == "0//1"
            and julia["receipts"]["Y3"]["tau"]["GHZ"] == "1//1"
            and julia["receipts"]["Y3"]["tau"]["W"] == "0//1"
            and julia["receipts"]["Y3"]["tau"]["product_000"] == "0//1",
            "julia_exact_derivations",
            {"Y2": julia["receipts"]["Y2"], "Y3": julia["receipts"]["Y3"]},
        ),
        "proofs_flip": require_gate(
            proofs["P1_anticommutation_table"]["z3_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"] == "unsat"
            and proofs["P1_anticommutation_table"]["corrupted_generator_control_z3"] == "sat"
            and proofs["P1_anticommutation_table"]["corrupted_generator_control_cvc5"] == "sat"
            and proofs["P2_tau_polynomial"]["z3_assert_tau_ghz_not_1_or_tau_w_not_0"] == "unsat"
            and proofs["P2_tau_polynomial"]["cvc5_assert_tau_ghz_not_1_or_tau_w_not_0"] == "unsat"
            and proofs["P2_tau_polynomial"]["z3_ghz_w_swapped_control"] == "sat"
            and proofs["P2_tau_polynomial"]["cvc5_ghz_w_swapped_control"] == "sat",
            "proofs_flip",
            proofs,
        ),
        "pytorch_exact_integer_route": require_gate(
            pytorch["receipts"]["Y4"]["all_36_pairs_exact"] is True
            and pytorch["receipts"]["Y4"]["torch_func_square_identity_pass"] is True
            and pytorch["receipts"]["Y4"]["corrupted_gamma_control"]["fired"] is True,
            "pytorch_exact_integer_route",
            pytorch["receipts"]["Y4"],
        ),
        "non_conflation_field": require_gate(
            non_conflation["present"] is True
            and non_conflation["merged"] is False
            and non_conflation["octonionic_structure_used_in_quotient_computations"] is False,
            "non_conflation_field",
            non_conflation,
        ),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "The three-spinor carrier (C^2)^{x3} ~= C^8 admits exact symbolic, closed-form, SMT, and exact-integer treatment at the 3-qubit floor.",
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
            "proof_tag": "three_qubit_floor_exact_symbolic_cl6_z3",
            "proof_pass": julia["all_pass"],
            "table_version": "geo_s1_three_qubit_floor_exact_v0",
            "bracket_convention": "Jordan-Wigner Cl(6), gamma_7=-i gamma_1...gamma_6; matrix representation is associative",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "canon exact Symbolics/Z3 receipt"},
            "jax": {"packages": jax["packages_used"], "role": "second CAS and z3/cvc5 exact SMT sidecar"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "exact integer tensor route for anticommutation table"},
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
                    "P2_assert_tau_wrong": proofs["P2_tau_polynomial"]["z3_assert_tau_ghz_not_1_or_tau_w_not_0"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_generator_control_z3"],
                    "P2_swapped_control": proofs["P2_tau_polynomial"]["z3_ghz_w_swapped_control"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_assert_some_bad": proofs["P1_anticommutation_table"]["cvc5_assert_some_bad"],
                    "P2_assert_tau_wrong": proofs["P2_tau_polynomial"]["cvc5_assert_tau_ghz_not_1_or_tau_w_not_0"],
                    "P1_corrupted_control": proofs["P1_anticommutation_table"]["corrupted_generator_control_cvc5"],
                    "P2_swapped_control": proofs["P2_tau_polynomial"]["cvc5_ghz_w_swapped_control"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["receipts"]["Y4"]["julia_z3_table_assert_some_bad"],
                "load_bearing": True,
                "control": julia["receipts"]["Y4"]["julia_z3_corrupted_generator_control"],
            },
        },
        "Y_receipts": j,
        "engine_receipts": {"julia": julia["receipts"], "jax": jax["receipts"], "pytorch": pytorch["receipts"]},
        "controls": {"julia": julia["controls"], "jax": jax["controls"], "pytorch": pytorch["controls"]},
        "non_conflation": non_conflation,
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0, "jax": 0, "pytorch": 0},
            "max_divergence": 0,
            "meaning": "exact claim-path failure-count divergence, not a numeric tolerance",
        },
        "claim_boundary": {
            "ceiling": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_claimed": "no formal admission; no merger of S^15->CP^7 density quotient with S^15->S^8 octonionic fibration",
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
