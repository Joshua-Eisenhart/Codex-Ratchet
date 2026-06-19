#!/usr/bin/env python3
"""Packet-local validator for geo_s3_density_observable_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_density_observable_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s3_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s3_build_spec_20260610.md"
DIRECTIVE = Path("/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md")
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"

REQUIRED_RECEIPTS = {"S3.F01", "S3.N01", "S3.T01", "S3.A", "S3.B", "S3.C", "S3.D", "S3.E", "S3.F", "S3.G"}
PIN_FIELDS = {
    "sigma_y_standard",
    "bloch_basis",
    "component_rule",
    "rho_rule",
    "hopf_lineage",
    "trace_distance_convention",
    "fidelity_convention",
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
}


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

    require(payload["schema_version"] == "three_engine_sim_result_v1", "schema drift")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(all(value is True for value in gates.values()), "one or more envelope gates failed")
    require(REQUIRED_RECEIPTS <= set(receipts), "missing required S3 receipt")
    require(set(payload["convention_pin"]) == PIN_FIELDS, "convention pin field drift")
    require(payload["convention_pin"]["bloch_basis"] == ["sigma_x", "-sigma_y_standard", "sigma_z"], "pinned basis drift")
    require("squared_Uhlmann" in payload["pin_spec"], "PIN does not name squared Uhlmann convention")
    require(len({record["pin_sha256"] for record in payload["engines"].values()}) == 1, "engine PIN hashes differ")
    require(all(record["convention_pin"] == payload["convention_pin"] for record in payload["engines"].values()), "engine convention pins differ")

    require(SPEC_COPY.exists() and sha256(SPEC_COPY) == sha256(SPEC), "S3 spec copy missing or changed")
    require(DIRECTIVE_COPY.exists(), "directive copy missing")
    if DIRECTIVE.exists():
        require(sha256(DIRECTIVE_COPY) == sha256(DIRECTIVE), "directive copy differs from /tmp directive")

    for engine, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{engine} source missing")
        require(sha256(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["reads_peer_result"] is False, f"{engine} reads peer result")
        require(record["ran"] is True, f"{engine} did not run")
        require(record["aligned_packages_load_bearing"], f"{engine} has no aligned load-bearing package")

    for rid, row in receipts.items():
        strength = row.get("exact_strength")
        require(strength in ALLOWED_STRENGTHS, f"{rid} has non-literal strength {strength!r}")
        if rid.startswith("S3."):
            require(row.get("convention_pin") == payload["convention_pin"], f"{rid} missing identical convention pin")

    f01 = receipts["F01_finitude_receipt"]
    require(f01["hilbert_dim"] == 2, "F01 hilbert_dim drift")
    require(f01["operator_basis_count"] == 4, "F01 operator basis drift")
    require(f01["mixed_density_real_dim"] == 3, "F01 mixed dimension drift")
    require("finite Pauli basis" in f01["proof_objects"], "F01 finite proof object missing")

    n01 = receipts["N01_noncommutation_receipt"]
    require(n01["O1_commuting_control"]["AB_minus_BA_zero"] is True, "N01 commuting control failed")
    require(n01["O2_general_noncommuting_witness"]["AB_minus_BA_nonzero"] is True, "N01 O2 failed")
    require(n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_minus_BA_nonzero"] is True, "N01 O3 commutator failed")
    require(n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_plus_BA_nonzero"] is True, "N01 O3 anticommutator boundary failed")
    require(n01["O4_Clifford_anticommuting_witness"]["AB_plus_BA_zero"] is True, "N01 O4 Clifford control failed")
    require(n01["O5_measurement_order_gap"]["gap"] == "1/4", "N01 order gap drift")

    t01 = receipts["T01_bracketing_receipt"]
    require(t01["matrix_associator_control"]["zero_in_M2C"] is True, "T01 matrix associator failed")
    require(t01["schedule_or_channel_associator_test"]["status"] == "open_with_reason", "T01 schedule boundary drift")

    s3a = receipts["S3.A"]["data"]
    require(s3a["trace"] == "1", "S3.A trace drift")
    require(s3a["component_traces"] == ["r_x", "r_y", "r_z"], "S3.A component trace drift")
    require(s3a["determinant"] == "-r_x**2/4 - r_y**2/4 - r_z**2/4 + 1/4", "S3.A determinant drift")
    require(s3a["purity"] == "r_x**2/2 + r_y**2/2 + r_z**2/2 + 1/2", "S3.A purity drift")
    require(s3a["entropy_base_receipt"]["primary_entropy"]["base"] == "natural_log_e", "S3.A primary entropy base drift")
    require(s3a["entropy_base_receipt"]["auxiliary_H2_log2_row"]["base"] == "log2", "S3.A H2/log2 row unlabeled")
    require(s3a["entropy_base_receipt"]["boundary_handling"]["norm_r_equals_1"]["coded_boundary_entropy_nats"] == 0.0, "S3.A pure-boundary entropy drift")
    require("x->0+" in s3a["entropy_base_receipt"]["boundary_handling"]["norm_r_equals_1"]["zero_times_log_zero_limit"], "S3.A 0*log(0) limit missing")

    s3b = receipts["S3.B"]["data"]
    require(s3b["expectation"] == "a0 + a_x*r_x + a_y*r_y + a_z*r_z", "S3.B expectation drift")
    require(s3b["plane_level_set"]["equation"] == "a_x*r_x + a_y*r_y + a_z*r_z = c - a0", "S3.B plane drift")
    require(s3b["plane_level_set"]["signed_distance"] == "(c - a0)/sqrt(a_x^2 + a_y^2 + a_z^2)", "S3.B signed distance missing")
    require({row["type"] for row in s3b["plane_level_set"]["intersection_types"]} == {"whole_ball", "empty", "tangent_point", "disk"}, "S3.B intersection rows missing")
    require("pinned-y" in s3b["pinned_y_sign_compatibility"], "S3.B pinned-y compatibility missing")

    s3c = receipts["S3.C"]["data"]
    require(s3c["normalization"] == "1", "S3.C normalization drift")
    require(s3c["boundary_certainty"]["r=+n"]["p_plus"] == "1", "S3.C boundary certainty drift")

    s3d = receipts["S3.D"]["data"]
    require(s3d["selective_update"]["r_to_plus_n"] == ["n_x", "n_y", "n_z"], "S3.D selective update drift")
    require(s3d["nonselective_update"]["diff_after_unit_constraint"] == ["0", "0", "0"], "S3.D nonselective derivation drift")
    require("r -> (n.r)n" in s3d["nonselective_update"]["rule"], "S3.D nonselective rule missing")
    require(s3d["trace_preservation_receipts"]["pass"] is True, "S3.D trace preservation receipt missing")
    require(s3d["positivity_preservation_receipts"]["pass"] is True, "S3.D positivity preservation receipt missing")
    require(s3d["positivity_preservation_receipts"]["nonselective"]["positive_semidefinite"] is True, "S3.D nonselective positivity receipt failed")

    ranks = {row["family"]: row["rank"] for row in receipts["S3.E"]["data"]["rows"]}
    require(ranks == {"Z_only": 1, "X_Z": 2, "X_Y_Z": 3, "duplicate_Z": 1, "tetrahedral_refinement_control": 3}, "S3.E rank table drift")
    require(receipts["S3.E"]["data"]["commuting_probe_simplex_lesson"].startswith("Z_only rank=1"), "S3.E simplex lesson missing")

    s3f = receipts["S3.F"]["data"]
    require(s3f["trace_distance"] == "sqrt((r_x - s_x)**2 + (r_y - s_y)**2 + (r_z - s_z)**2)/2", "S3.F trace distance drift")
    require(s3f["controls"]["mixed_interior"]["r=(1/2,0,0), s=(0,1/2,0)"]["F"] == "7/8", "S3.F mixed fidelity control drift")
    require("never compared against squared-F" in s3f["root_fidelity_auxiliary"], "S3.F root/squared boundary missing")

    s3g = receipts["S3.G"]["data"]
    require("no S4 channel ellipsoid" in s3g["boundary"], "S3.G S4 boundary missing")
    require("no S5 fixed-point" in s3g["boundary"], "S3.G S5 boundary missing")
    require(s3g["scope_routes"]["channel_ellipsoid_image_classification"]["route_to"] == "S4", "S3.G ellipsoid route missing")
    require(s3g["scope_routes"]["fixed_point_classification"]["route_to"] == "S5", "S3.G fixed-point route missing")
    require(s3g["scope_routes"]["basin_classification"]["computed_here"] is False, "S3.G basin scope drift")
    require(len(s3g["channels"]) == 3, "S3.G channel count drift")
    require(s3g["fidelity_monotonicity"]["strength"] == "measure_theorem", "S3.G fidelity theorem strength drift")

    neg = payload["negative_models"]
    require(neg["C1_outside_ball_negative"]["selectivity_pass"] is True, "C1 selectivity failed")
    require(neg["C2_wrong_sigma_y_pin_negative"]["must_not_silently_repin"] is True, "C2 repin guard missing")
    require(neg["C3_commuting_probe_simplex_misclassified_as_ball"]["rank3_claim_fails"] is True, "C3 rank failure missing")
    require(neg["C4_nonlinear_expectation_echo_negative"]["sample_only_plane_fit_not_accepted"] is True, "C4 sample-only guard missing")
    require(neg["C5_bad_measurement_update_negative"]["wrong_update_distinguished_from_wrong_probability"] is True, "C5 distinction missing")
    require(neg["C6_non_CPTP_expansive_map_negative"]["D_after"] == "3/10", "C6 contraction control drift")
    require(neg["C7_wrong_mixed_state_fidelity_formula_negative"]["mixed_interior_control"]["correct_F"] == "7/8", "C7 mixed fidelity control drift")

    alt = payload["alternative_models"]
    require(alt["D1_fidelity_convention_alternative"]["no_root_vs_squared_comparison"] is True, "D1 convention boundary failed")
    require(alt["D2_probe_family_alternatives"]["all_pass"] is True, "D2 probe alternatives failed")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"]:
        require(proofs[key]["verdict"] == "unsat", f"{key} proof verdict drift")
        require(proofs[key]["load_bearing"] is True, f"{key} proof not load-bearing")
    require(proofs["z3"]["asserted_precomputed_boolean"] is False, "z3 proof binds boolean")
    require(proofs["cvc5"]["asserted_precomputed_boolean"] is False, "cvc5 proof binds boolean")
    require(proofs["pytorch_z3"]["asserted_precomputed_boolean"] is False, "pytorch z3 proof binds boolean")
    require(payload["build_gates"]["smt_agreement_and_can_fail_controls"] is True, "SMT can-fail controls gate false")
    require(set(payload["claim_path_tools"]).isdisjoint({"numpy", "scipy", "mpmath"}), "control-only tool in claim path")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
