#!/usr/bin/env python3
"""Packet-local self-check for geo_s4_operator_stage_v0.

This is not audit evidence; it only catches builder/schema drift.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s4_operator_stage_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s4_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s4_build_spec_20260610.md"
DIRECTIVE = Path("/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md")
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"

REQUIRED = {
    "P1_pauli_table_exact",
    "P2_affine_channel_table_exact",
    "P3_ellipsoid_image_exact",
    "P4_fixed_sets_exact",
    "P5_basin_classes_exact",
    "P6_commutator_table_symbolic",
    "P7_prior_reuse_lineage",
    "P8_claim_ceiling",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "schema drift")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(all(value is True for value in payload["build_gates"].values()), "one or more build gates failed")
    require(REQUIRED <= set(payload["receipts"]), "missing required positive receipt")
    require(all(payload["positive_ledger"][key]["pass"] is True for key in REQUIRED), "positive ledger has failing row")
    require(payload["convention_pin"]["source_locked_bloch_basis"] == ["sigma_x", "sigma_y_standard", "sigma_z"], "source-locked Bloch basis drift")
    require(payload["convention_pin"]["s1_pinned_bloch_basis"] == ["sigma_x", "-sigma_y_standard", "sigma_z"], "S1 pinned Bloch basis drift")
    require(payload["basis_conversion_layer"]["all_pass"] is True, "basis conversion layer failed")
    require("pin_row=(q_z=3/10,q_x=3/10,theta_x=pi/2,phi_z=pi/2)" in payload["pin_spec"], "PIN row missing")
    require(len({record["pin_sha256"] for record in payload["engines"].values()}) == 1, "engine PIN hashes differ")
    require(all(record["convention_pin"] == payload["convention_pin"] for record in payload["engines"].values()), "engine convention pins differ")
    require(SPEC_COPY.exists() and sha256(SPEC_COPY) == sha256(SPEC), "S4 spec copy missing or changed")
    require(DIRECTIVE_COPY.exists(), "directive copy missing")
    if DIRECTIVE.exists():
        require(sha256(DIRECTIVE_COPY) == sha256(DIRECTIVE), "directive copy differs from /tmp directive")

    for engine, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{engine} source missing")
        require(sha256(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["ran"] is True, f"{engine} did not run")
        require(record["reads_peer_result"] is False, f"{engine} reads peer result")
        require(record["aligned_packages_load_bearing"], f"{engine} has no load-bearing package")

    affine = payload["affine_channel_table"]
    require(affine["D_z"]["symbolic"]["M"] == [["1 - q_z", "0", "0"], ["0", "1 - q_z", "0"], ["0", "0", "1"]], "D_z M drift")
    require(affine["D_x"]["symbolic"]["M"] == [["1", "0", "0"], ["0", "1 - q_x", "0"], ["0", "0", "1 - q_x"]], "D_x M drift")
    require(affine["R_x"]["symbolic"]["M"] == [["1", "0", "0"], ["0", "cos(theta_x)", "-sin(theta_x)"], ["0", "sin(theta_x)", "cos(theta_x)"]], "R_x M drift")
    require(affine["R_z"]["symbolic"]["M"] == [["cos(phi_z)", "-sin(phi_z)", "0"], ["sin(phi_z)", "cos(phi_z)", "0"], ["0", "0", "1"]], "R_z M drift")
    require(affine["R_x"]["s1_pinned_basis"]["symbolic"]["M"] == [["1", "0", "0"], ["0", "cos(theta_x)", "sin(theta_x)"], ["0", "-sin(theta_x)", "cos(theta_x)"]], "R_x S1 pinned conversion drift")
    require(all(row["symbolic"]["c"] == ["0", "0", "0"] for row in affine.values()), "nonzero affine shift found")
    require(affine["D_z"]["pinned"]["M"] == [["7/10", "0", "0"], ["0", "7/10", "0"], ["0", "0", "1"]], "D_z pin drift")
    require(affine["R_z"]["pinned"]["M"] == [["0", "-1", "0"], ["1", "0", "0"], ["0", "0", "1"]], "R_z pin drift")

    ell = payload["ellipsoid_images"]
    require(ell["D_z"]["image_classification"]["q_z=1"] == "line_limit_z_axis", "D_z q=1 classification drift")
    require(ell["D_x"]["image_classification"]["q_x=1"] == "line_limit_x_axis", "D_x q=1 classification drift")
    require(ell["R_x"]["determinant"] == "1" and ell["R_z"]["determinant"] == "1", "rotation determinant drift")
    require(payload["fixed_sets"]["D_z"]["0<q_z<1"].startswith("z-axis fixed"), "D_z fixed axis drift")
    require(payload["fixed_sets"]["D_x"]["0<q_x<1"].startswith("x-axis fixed"), "D_x fixed axis drift")
    require(payload["basin_classes"]["D_z"]["closed_form_limit"]["limit_n_to_infinity"] == ["0", "0", "z_0"], "D_z closed-form limit drift")
    require(payload["basin_classes"]["D_x"]["closed_form_limit"]["limit_n_to_infinity"] == ["x_0", "0", "0"], "D_x closed-form limit drift")
    require(payload["basin_classes"]["R_x"]["computed_pin_orbit_receipt"]["period_check"] == "r_4-r_0=(0,0,0)", "R_x period-four receipt missing")
    require(payload["basin_classes"]["R_z"]["computed_pin_orbit_receipt"]["period_check"] == "r_4-r_0=(0,0,0)", "R_z period-four receipt missing")
    require(payload["basin_classes"]["R_z"]["invariant"] == "x_n^2 + y_n^2 = x_0^2 + y_0^2", "R_z invariant drift")

    comm_rows = payload["commutator_table"]["rows"]
    require(len(comm_rows) == 16, "commutator table not 16 ordered pairs")
    by_pair = {(row["left"], row["right"]): row for row in comm_rows}
    require(by_pair[("D_z", "D_x")]["zero_symbolic"] is True, "D_z/D_x should commute")
    require(by_pair[("D_z", "R_z")]["zero_symbolic"] is True, "D_z/R_z should commute")
    require(by_pair[("D_x", "R_x")]["zero_symbolic"] is True, "D_x/R_x should commute")
    require(by_pair[("D_z", "R_x")]["zero_symbolic"] is False, "D_z/R_x generic noncommutator missing")
    require(by_pair[("D_z", "R_x")]["pinned_linear_commutator"] == [["0", "0", "0"], ["0", "0", "3/10"], ["0", "3/10", "0"]], "D_z/R_x pinned commutator drift")
    require(by_pair[("D_x", "R_z")]["pinned_linear_commutator"] == [["0", "-3/10", "0"], ["-3/10", "0", "0"], ["0", "0", "0"]], "D_x/R_z pinned commutator drift")
    require(by_pair[("R_x", "R_z")]["pinned_linear_commutator"] == [["0", "-1", "-1"], ["-1", "0", "-1"], ["1", "-1", "0"]], "R_x/R_z pinned commutator drift")
    require(all(row["affine_shift_commutator"] == ["0", "0", "0"] for row in comm_rows), "affine commutator shift not zero")

    neg = payload["negative_controls"]
    for key in [
        "C1_wrong_bloch_convention",
        "C2_wrong_basis_dephase",
        "C3_fake_nonunital_shift",
        "C4_rotation_as_contraction_error",
        "C5_dephase_as_rotation_error",
        "C6_commutator_echo_error",
        "C7_numeric_only_table_error",
        "C8_terrain_leakage_error",
    ]:
        require(neg[key]["selectivity_pass"] is True, f"{key} selectivity failed")
        require(neg[key]["executed"] is True, f"{key} was not executed")
        require(neg[key]["gate_passed_after_mutation"] is False, f"{key} mutation did not fail")
        require(neg[key]["expected_failure_observed"] is True, f"{key} expected failure missing")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"]:
        require(proofs[key]["verdict"] == "unsat", f"{key} proof verdict drift")
        require(proofs[key]["load_bearing"] is True, f"{key} proof not load-bearing")
        require(proofs[key]["asserted_precomputed_boolean"] is False, f"{key} binds a boolean")
        require(proofs[key]["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table", f"{key} proof scope drift")
        require(proofs[key]["bound_raw_values"]["10*entry"] == 3, f"{key} bound raw value drift")

    require(payload["julia_density_channel_derivation"]["all_pass"] is True, "Julia density derivation failed")
    require(payload["julia_density_channel_derivation"]["rows"]["R_x"]["M"] == [["1", "0", "0"], ["0", "cos(theta_x)", "-sin(theta_x)"], ["0", "sin(theta_x)", "cos(theta_x)"]], "Julia R_x derivation drift")

    require(set(payload["claim_path_tools"]).isdisjoint({"numpy", "scipy", "mpmath"}), "control-only tool in claim path")
    require("global phase" in payload["quotient_erasure_note"]["erases"], "quotient erasure note missing phase boundary")
    require("Builder self-checks" in payload["self_check_notice"], "self-check notice missing")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
