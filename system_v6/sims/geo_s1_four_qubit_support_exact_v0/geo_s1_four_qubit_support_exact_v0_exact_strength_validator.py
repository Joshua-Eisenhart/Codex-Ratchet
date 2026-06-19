#!/usr/bin/env python3
"""Packet-local exact-strength validator for geo_s1_four_qubit_support_exact_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_four_qubit_support_exact_v0"
RESULT = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_envelope_results.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    receipts = payload["receipts"]
    gates = payload["build_gates"]
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "bad schema")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(not [name for name, gate in gates.items() if gate["pass"] is not True], "failed build gate present")

    f01 = receipts["F01_finitude_receipt"]
    require(f01["hilbert_dim"] == 16, "F01 hilbert_dim")
    require(f01["computational_basis_count"] == 16, "F01 basis count")
    require(f01["operator_basis_count"] == 256, "F01 operator count")
    require(f01["mixed_density_real_dim"] == 255, "F01 mixed dimension")

    n01 = receipts["N01_noncommutation_receipt"]
    require(n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_minus_BA_nonzero"] is True, "N01 O3 commutator")
    require(n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_plus_BA_nonzero"] is True, "N01 O3 anticommutator")
    require(n01["O4_anticommuting_Clifford_witness"]["AB_plus_BA_zero"] is True, "N01 O4 anticommutator")
    require(n01["O5_order_gap_receipt_on_state"]["gap_norm_squared"] == "4", "N01 order gap")

    t01 = receipts["T01_bracketing_receipt"]
    require(t01["matrix_associator_control"]["failures"] == 0, "T01 associator failures")
    require(t01["schedule_or_channel_associator_test"]["status"] == "not_scoped", "T01 schedule status")

    z1 = receipts["Z1_carrier_quotient"]
    require(len(z1["basis_dictionary"]) == 16, "Z1 basis dictionary")
    require(z1["global_phase_quotient"] == "S^31/S^1 = CP^15", "Z1 quotient")
    require(z1["rank_1_density_phase_erasure_identity"]["pass"] is True, "Z1 phase erasure")

    z2 = receipts["Z2_entanglement_controls"]["states"]
    require(z2["GHZ4"]["one_qubit"]["0"]["rho"] == [["1/2", "0"], ["0", "1/2"]], "Z2 GHZ4 rho")
    require(z2["GHZ4"]["one_qubit"]["0"]["entropy"] == "log(2)", "Z2 GHZ4 entropy")
    require(z2["product_0000"]["AB"]["entropy"] == "0", "Z2 product entropy")
    require(z2["Bell_AB_tensor_Bell_CD"]["AB"]["entropy"] == "0", "Z2 Bell AB entropy")
    require(z2["Bell_AB_tensor_Bell_CD"]["AC"]["entropy"] == "log(4)", "Z2 Bell AC entropy")
    require(z2["linear_cluster_4"]["stabilizer_receipt"]["pass"] is True, "Z2 cluster stabilizer")

    z3 = receipts["Z3_Cl8_exact_floor"]
    require(z3["all_64_pairs_exact"] is True, "Z3 anticommutation")
    require(z3["algebra_generated_dimension"] == 256, "Z3 generated dimension")
    require(z3["gamma9_squared_identity"] is True, "Z3 gamma9 square")
    require(z3["gamma9_trace"] == "0", "Z3 gamma9 trace")
    require(sorted(z3["gamma9_eigenspace_split"].values()) == [8, 8], "Z3 gamma9 split")

    z4 = receipts["Z4_max_anticommuting_family"]
    require(z4["constructed_family_size"] == 9, "Z4 family size")
    require(z4["pairwise_anticommutation_exact"] is True, "Z4 family anticommutation")
    require(z4["upper_bound_theorem"]["m_10_allowed"] is False, "Z4 m10 theorem")
    require(z4["attempted_10_member_extension_negative_control"]["finite_extension_scan"]["size_10_extension_exists"] is False, "Z4 extension scan")

    z5 = receipts["Z5_Spin8_triality_pressure"]
    require(z5["full_triality_automorphism_claimed"] is False, "Z5 triality overclaim")
    require(z5["triality_pressure_open"]["status"] == "open-with-reason", "Z5 open status")

    z7 = receipts["Z7_classification_table"]
    require(z7["bare_float_rows"] == [], "Z7 bare float rows")
    require(all(row["achieved_strength"] in z7["allowed_strengths"] for row in z7["classification_table"]), "Z7 strength labels")

    for engine, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{engine} source missing")
        require(sha256(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["reads_peer_result"] is False, f"{engine} reads peer result")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
