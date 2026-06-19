#!/usr/bin/env python3
"""Packet-local exact-strength validator for geo_s1_scaling_stress_678q_exact_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_scaling_stress_678q_exact_v0"
RESULT = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_envelope_results.json"
RUNG_NS = ("6", "7", "8")
REQUIRED_RECEIPTS = [
    "F01_finitude_receipt",
    "N01_noncommutation_receipt",
    "T01_bracketing_receipt",
    "W1_carrier_quotient",
    "W2_Cl2n_exact_floor",
    "W3_max_anticommuting_family",
    "W4_finite_pauli_string_stress",
    "W5_named_stabilizer_controls",
    "W6_scaling_boundary_ceiling",
    "W7_classification_table",
]
EXPECTED = {
    "6": {
        "hilbert_dim": 64,
        "operator_basis_count": 4096,
        "mixed_density_real_dim": 4095,
        "gamma_count": 12,
        "split": [32, 32],
        "max_family": 13,
        "sphere": "S^127 subset C^64",
        "quotient": "CP^63",
    },
    "7": {
        "hilbert_dim": 128,
        "operator_basis_count": 16384,
        "mixed_density_real_dim": 16383,
        "gamma_count": 14,
        "split": [64, 64],
        "max_family": 15,
        "sphere": "S^255 subset C^128",
        "quotient": "CP^127",
    },
    "8": {
        "hilbert_dim": 256,
        "operator_basis_count": 65536,
        "mixed_density_real_dim": 65535,
        "gamma_count": 16,
        "split": [128, 128],
        "max_family": 17,
        "sphere": "S^511 subset C^256",
        "quotient": "CP^255",
    },
}
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
    "negative_control",
}
FORBIDDEN = {
    "bare_float_tolerance",
    "sample_only",
    "max_deviation_only",
    "abs_error_only",
    "visual agreement",
    "validator-green only",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_strength_labels(value: Any, found: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "strength_label" and isinstance(item, str):
                found.append(item)
            else:
                walk_strength_labels(item, found)
    elif isinstance(value, list):
        for item in value:
            walk_strength_labels(item, found)


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "bad schema")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal admission drift")
    require(payload["builder_self_check_is_evidence"] is False, "builder self-check flag drift")
    require(payload["gate_pass"]["per_rung_receipt_tables_complete"]["pass"] is True, "receipt table gate failed")
    require(payload["gate_pass"]["expected_scalars_exact"]["pass"] is True, "expected scalar gate failed")
    require(payload["gate_pass"]["resource_rows_diagnostic_nonclaim"]["pass"] is True, "resource row gate failed")
    require(payload["divergence"]["max_divergence"] == 0, "engine divergence present")

    for engine, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        result = ROOT / record["result_path"]
        require(source.exists(), f"{engine} source missing")
        require(result.exists(), f"{engine} result missing")
        require(sha256(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["reads_peer_result"] is False, f"{engine} reads_peer_result drift")
        require(record["classification"] == "scratch_diagnostic", f"{engine} classification drift")
        require(record["promotion_allowed"] is False, f"{engine} promotion drift")
        require(record["formal_admission_allowed"] is False, f"{engine} formal admission drift")

    for rung in RUNG_NS:
        n = int(rung)
        expected = EXPECTED[rung]
        table = payload["per_rung_receipt_tables"][rung]
        require(sorted(table) == sorted(REQUIRED_RECEIPTS), f"{rung}Q receipt names incomplete")
        for receipt in REQUIRED_RECEIPTS:
            require(all(table[receipt].values()), f"{rung}Q receipt {receipt} did not pass all engines")

        jax = payload["rungs"][rung]["jax"]
        f01 = jax["F01_finitude_receipt"]
        require(f01["hilbert_dim"] == expected["hilbert_dim"], f"{rung}Q hilbert dim")
        require(f01["computational_basis_count"] == expected["hilbert_dim"], f"{rung}Q basis count")
        require(f01["operator_basis_count"] == expected["operator_basis_count"], f"{rung}Q operator count")
        require(f01["mixed_density_real_dim"] == expected["mixed_density_real_dim"], f"{rung}Q density dim")
        require(f01["pure_sphere"] == expected["sphere"], f"{rung}Q sphere")
        require(f01["phase_quotient"] == expected["quotient"], f"{rung}Q quotient")
        require(f01["active_probe_family_count"]["arbitrary_dense_state_enumeration"] == "not_used", f"{rung}Q dense state enumeration used")

        n01 = jax["N01_noncommutation_receipt"]
        require(n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_minus_BA_nonzero"] is True, f"{rung}Q O3 commutator")
        require(n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_plus_BA_nonzero"] is True, f"{rung}Q O3 anticommutator")
        require(n01["O4_anticommuting_Clifford_witness"]["AB_plus_BA_zero"] is True, f"{rung}Q O4 anticommutator")
        require(n01["O6_Clifford_family_capacity_row_kept_separate"]["not_collapsed"] is True, f"{rung}Q capacity collapsed")

        t01 = jax["T01_bracketing_receipt"]
        require(t01["matrix_associator_control"]["failures"] == 0, f"{rung}Q associator failures")
        require(t01["schedule_or_channel_associator_test"]["status"] == "not_scoped", f"{rung}Q schedule status")
        require("octonion" in t01["octonion_lane_boundary_statement"], f"{rung}Q octonion boundary missing")

        w1 = jax["W1_carrier_quotient"]
        require(w1["phase_erasure_symbolic_proof"]["pass"] is True, f"{rung}Q phase erasure")
        require(w1["mixed_state_domain"]["real_affine_dimension"] == expected["mixed_density_real_dim"], f"{rung}Q mixed domain")

        w2 = jax["W2_Cl2n_exact_floor"]
        require(w2["all_pairs_exact"] is True, f"{rung}Q Clifford pairs")
        require(w2["anticommutation_pairs_checked"] == expected["gamma_count"] ** 2, f"{rung}Q pair count")
        require(w2["chirality_computation"]["phase_is_plus_one"] is True, f"{rung}Q chirality phase")
        require(w2["chirality_computation"]["label_matches_Zn"] is True, f"{rung}Q chirality label")
        require(sorted(w2["gamma_2n_plus_1_eigenspace_split"].values()) == expected["split"], f"{rung}Q chirality split")

        w3 = jax["W3_max_anticommuting_family"]
        require(w3["constructed_family_size"] == expected["max_family"], f"{rung}Q family size")
        require(w3["pairwise_anticommutation_exact"] is True, f"{rung}Q family anticommutes")
        require(w3["representation_bound_instantiations"][f"m_{expected['max_family'] + 1}_blocked"]["allowed"] is False, f"{rung}Q next family allowed")

        w4 = jax["W4_finite_pauli_string_stress"]
        require(w4["full_family_extension_scan"]["searched_nonidentity_pauli_strings"] == 4**n - 1, f"{rung}Q scan size")
        require(w4["full_family_extension_scan"]["candidate_count"] == 0, f"{rung}Q extension candidates")
        require(w4["erased_chirality_positive_control_scan"]["candidate_count"] == 1, f"{rung}Q erased chirality control")
        for row_name, row in w4["resource_rows"].items():
            require(row["strength_label"] == "diagnostic_float_nonclaim", f"{rung}Q resource row {row_name} strength")

        w5 = jax["W5_named_stabilizer_controls"]
        require(w5["GHZ"]["entropy_qubit_0"] == "log(2)", f"{rung}Q GHZ entropy")
        require(w5["product"]["entropy_qubit_0"] == "0", f"{rung}Q product entropy")
        require(w5["Bell_pair_plus_spectators"]["entropy_qubits_0_1"] == "0", f"{rung}Q Bell pair entropy")

        w6 = jax["W6_scaling_boundary_ceiling"]
        require(w6["new_minimum_claimed"] is False, f"{rung}Q minimum claimed")
        require(w6["minimum_floor_moved_from_3Q"] is False, f"{rung}Q floor moved")
        require(w6["eight_qubit_ceiling"] is (rung == "8"), f"{rung}Q 8Q ceiling flag")

        w7 = jax["W7_classification_table"]
        require(w7["zero_claim_bearing_bare_float_rows"] is True, f"{rung}Q bare float rows")
        require(not w7["invalid_strength_rows"], f"{rung}Q invalid strength rows")
        require(not w7["forbidden_strength_rows"], f"{rung}Q forbidden strength rows")

    labels: list[str] = []
    walk_strength_labels(payload, labels)
    require(all(label in ALLOWED_STRENGTHS for label in labels), "non-literal strength label found")
    require(not any(label in FORBIDDEN for label in labels), "forbidden strength label found")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
