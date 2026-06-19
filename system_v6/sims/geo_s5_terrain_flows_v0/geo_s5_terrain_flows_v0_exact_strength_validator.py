#!/usr/bin/env python3
"""Packet-local exact-strength validator for geo_s5_terrain_flows_v0.

This is a builder drift guard, not independent audit evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s5_terrain_flows_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s5_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s5_build_spec_20260610.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"

REQUIRED = {
    "P1_source_lineage_and_pins",
    "P2_exact_bloch_generator_table",
    "P3_flow_solutions_exact",
    "P4_cptp_all_t_proof",
    "P5_fixed_points_exact",
    "P6_basin_limits_exact",
    "P7_pure_hamiltonian_purity_preserved",
    "P8_nonunitality_witnesses",
    "P9_executed_negative_controls",
    "P10_claim_ceiling",
}

ALLOWED_STRENGTHS = {
    "basin_limit_formula",
    "exact_fixed_point_solution",
    "exact_flow_formula",
    "exact_symbolic_generator_table",
    "executed_mutation_control",
    "gksl_all_t_semigroup_proof",
    "lineage_citation_only",
    "purity_spectrum_invariant",
    "scratch_ceiling_token",
    "unitality_identity_witness",
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
    require(set(payload["strength_tokens"]) <= ALLOWED_STRENGTHS, "non-literal or unexpected strength token")
    require(set(payload["strength_tokens"]) == ALLOWED_STRENGTHS, "strength token set drift")

    require(payload["convention_pin"]["source_locked_bloch_basis"] == ["sigma_x", "sigma_y_standard", "sigma_z"], "primary Bloch basis drift")
    require(payload["convention_pin"]["s1_pinned_bloch_basis"] == ["sigma_x", "-sigma_y_standard", "sigma_z"], "pinned-y basis drift")
    require(payload["convention_pin"]["standard_to_s1_pinned_J"] == [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]], "J conversion drift")
    require(payload["convention_pin"]["si_frame_pin"] == {"Hill": "z frame", "Citadel": "x frame"}, "Si frame pin drift")
    require("H_L=+H0|H_R=-H0" in payload["pin_spec"], "Hamiltonian sign pin missing")
    require(len({record["pin_sha256"] for record in payload["engines"].values()}) == 1, "engine PIN hashes differ")
    require(all(record["convention_pin"] == payload["convention_pin"] for record in payload["engines"].values()), "engine convention pins differ")

    require(SPEC_COPY.exists() and sha256(SPEC_COPY) == sha256(SPEC), "S5 spec copy missing or changed")
    require(DIRECTIVE_COPY.exists(), "directive copy missing")

    for engine, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{engine} source missing")
        require(sha256(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["ran"] is True, f"{engine} did not run")
        require(record["reads_peer_result"] is False, f"{engine} reads peer result")
        require(record["aligned_packages_load_bearing"], f"{engine} has no load-bearing package")

    rows = payload["bloch_generator_table"]
    ne_vortex_A = [["0", "-2*sqrt(3)/3", "2*sqrt(3)/3"], ["2*sqrt(3)/3", "0", "-2*sqrt(3)/3"], ["-2*sqrt(3)/3", "2*sqrt(3)/3", "0"]]
    ne_spiral_A = [["0", "2*sqrt(3)/3", "-2*sqrt(3)/3"], ["-2*sqrt(3)/3", "0", "2*sqrt(3)/3"], ["2*sqrt(3)/3", "-2*sqrt(3)/3", "0"]]
    require(set(rows) == {"Se_Funnel_L", "Se_Cannon_R", "Ne_Vortex_L", "Ne_Spiral_R", "Ni_Pit_L", "Ni_Source_R", "Si_Hill_L", "Si_Citadel_R"}, "terrain row set drift")
    require(rows["Se_Funnel_L"]["symbolic"]["A"] == [["-4*lambda_Se_L", "-2*sqrt(3)*epsilon_Se_L/3", "2*sqrt(3)*epsilon_Se_L/3"], ["2*sqrt(3)*epsilon_Se_L/3", "-4*lambda_Se_L", "-2*sqrt(3)*epsilon_Se_L/3"], ["-2*sqrt(3)*epsilon_Se_L/3", "2*sqrt(3)*epsilon_Se_L/3", "-4*lambda_Se_L"]], "Se Funnel A drift")
    require(rows["Se_Cannon_R"]["symbolic"]["A"][0][1] == "2*sqrt(3)*epsilon_Se_R/3", "Se Cannon handedness drift")
    require(payload["generator_consistency_gates"]["all_pass"] is True, "generator consistency gate failed")
    require(rows["Ne_Vortex_L"]["symbolic"]["A"] == ne_vortex_A, "Ne Vortex A drift or zero-precession regression")
    require(rows["Ne_Spiral_R"]["symbolic"]["A"] == ne_spiral_A, "Ne Spiral A drift or zero-precession regression")
    require(rows["Ne_Vortex_L"]["symbolic"]["b"] == ["0", "0", "0"], "Ne Vortex b drift")
    require(rows["Ne_Spiral_R"]["symbolic"]["b"] == ["0", "0", "0"], "Ne Spiral b drift")
    require(rows["Ni_Pit_L"]["symbolic"]["b"] == ["0", "0", "-gamma_Ni_L"], "Pit non-unital b drift")
    require(rows["Ni_Source_R"]["symbolic"]["b"] == ["0", "0", "gamma_Ni_R"], "Source non-unital b drift")
    require(rows["Si_Hill_L"]["symbolic"]["A"] == [["-kappa_Si_L", "-2*omega_Si_L", "0"], ["2*omega_Si_L", "-kappa_Si_L", "0"], ["0", "0", "0"]], "Si Hill z-frame drift")
    require(rows["Si_Citadel_R"]["symbolic"]["A"] == [["0", "0", "0"], ["0", "-kappa_Si_R", "-2*omega_Si_R"], ["0", "2*omega_Si_R", "-kappa_Si_R"]], "Si Citadel x-frame drift")

    flows = payload["flow_solutions"]
    require(payload["flow_round_trip_gates"]["all_pass"] is True, "flow round-trip gate failed")
    for key, row in payload["flow_round_trip_gates"].items():
        if key == "all_pass":
            continue
        require(row["computed"] is True and row["pass"] is True, f"{key} flow did not differentiate back to exported A,b")
        require(row["residual"] == ["0", "0", "0"], f"{key} flow residual drift")
    require(flows["Ne_Vortex_L"]["formula"] == "r(t)=R_n(+2t) r0", "Ne Vortex flow formula drift")
    require(flows["Ne_Spiral_R"]["formula"] == "r(t)=R_n(-2t) r0", "Ne Spiral flow formula drift")
    require("exp(-4*lambda_Se_L*t)" in flows["Se_Funnel_L"]["formula"], "Se decay formula missing")
    require(flows["Si_Hill_L"]["limit_receipt"]["kappa_Si_L>0"] == ["0", "0", "z0"], "Si Hill limit drift")
    require(flows["Si_Citadel_R"]["limit_receipt"]["kappa_Si_R>0"] == ["x0", "0", "0"], "Si Citadel limit drift")
    require(flows["Ni_Pit_L"]["erased_H_control"]["epsilon_Ni_L=0"] == ["0", "0", "-1"], "Pit erased-H target drift")
    require(flows["Ni_Source_R"]["erased_H_control"]["epsilon_Ni_R=0"] == ["0", "0", "1"], "Source erased-H target drift")

    fixed = payload["fixed_points_and_basins"]
    require(payload["build_gates"]["fixed_set_consistency_from_exported_A_b"] is True, "fixed-set A,b consistency gate failed")
    require(payload["build_gates"]["basin_orbit_consistency_from_exported_A_b"] is True, "basin/orbit A,b consistency gate failed")
    require(fixed["Ne_Vortex_L"]["fixed"]["derived_from"].startswith("exported symbolic A,b"), "Ne fixed set not derived from exported A,b")
    require(fixed["Ne_Vortex_L"]["fixed"]["kernel_basis"] == [["1", "1", "1"]], "Ne fixed kernel drift")
    require(fixed["Ne_Vortex_L"]["fixed"]["fixed_axis"] == "span(n)", "Ne fixed axis drift")
    require(fixed["Ne_Vortex_L"]["basin_or_orbit"]["computed_from"] == "exported A,b", "Ne basin not computed from exported A,b")
    require(fixed["Ne_Vortex_L"]["basin_or_orbit"]["nonlimit_witness"]["velocity_at_initial"] != ["0", "0", "0"], "Ne nonlimit witness lost precession velocity")
    require(fixed["Ne_Vortex_L"]["basin_or_orbit"]["nonlimit_witness"]["norm_derivative"] == "0", "Ne norm derivative drift")
    require(fixed["Ne_Vortex_L"]["basin_or_orbit"]["class"].startswith("non-attracting"), "Ne orbit class drift")
    require(fixed["Si_Hill_L"]["fixed"]["fixed_set"] == "{(0,0,z) : -1 <= z <= 1}", "Hill fixed set drift")
    require(fixed["Si_Citadel_R"]["fixed"]["fixed_set"] == "{(x,0,0) : -1 <= x <= 1}", "Citadel fixed set drift")
    require(fixed["Se_Funnel_L"]["fixed"]["fixed_point"] == ["0", "0", "0"], "Se fixed point drift")

    gksl = payload["gksl_all_t_proofs"]
    samples = payload["sampled_choi_fixtures"]
    require(all(row["pass"] is True for row in gksl.values()), "GKSL all-time proof row failed")
    require(all(row["sampled_only_not_all_t_proof"] is True and row["pass"] is True for row in samples.values()), "sampled Choi fixture drift")

    purity = payload["purity_preservation"]
    require(purity["Ne_Vortex_L"]["pass"] is True and purity["Ne_Spiral_R"]["pass"] is True, "pure Ne purity failed")
    require(purity["weak_ne_negative_control"]["gate_passed_after_mutation"] is False, "weak-Ne control did not fail")

    unitality = payload["nonunitality_witnesses"]
    require(unitality["Ni_Pit_L"]["X(I)_bloch_coefficients"] == ["0", "0", "-gamma_Ni_L"], "Pit X(I) drift")
    require(unitality["Ni_Source_R"]["X(I)_bloch_coefficients"] == ["0", "0", "gamma_Ni_R"], "Source X(I) drift")
    require(all(row["X(I)=0"] is True for key, row in unitality.items() if key.startswith(("Se_", "Ne_", "Si_"))), "scoped unital row drift")

    controls = payload["negative_controls"]
    for key in [f"C{i}" for i in range(1, 13)]:
        match = [name for name in controls if name.startswith(key + "_")]
        require(len(match) == 1, f"{key} missing")
        row = controls[match[0]]
        require(row["executed"] is True, f"{match[0]} was not executed")
        require(row["computed_mutation"] is True, f"{match[0]} was not computed")
        require(row["gate_passed_after_mutation"] is False, f"{match[0]} mutation did not fail")
        require(row["expected_failure_observed"] is True, f"{match[0]} expected failure missing")
    require(controls["all_executed_can_fail"] is True, "controls aggregate failed")

    require(payload["build_gates"]["cross_engine_load_bearing_rows_agree"] is True, "cross-engine fatality gate failed")
    require(payload["build_gates"]["julia_flow_solver_route"] is True, "Julia flow solver route gate failed")
    require(payload["build_gates"]["jax_flow_solver_route"] is True, "JAX flow solver route gate failed")
    require(payload["cross_engine_consistency"]["all_pass"] is True, "cross-engine consistency failed")
    require(all(row["pass"] is True for row in payload["cross_engine_consistency"]["rows"].values()), "one or more cross-engine rows disagree")
    require(payload["receipts"]["P3_flow_solutions_exact"]["solver_route"]["all_pass"] is True, "P3 solver route missing or failed")
    routes = payload["flow_solver_routes"]
    require(routes["julia"]["tool"] == "DifferentialEquations" and routes["julia"]["all_pass"] is True, "Julia DifferentialEquations route missing or failed")
    require(routes["jax"]["tool"] == "diffrax" and routes["jax"]["all_pass"] is True, "JAX diffrax route missing or failed")
    require("exact" in routes["matrix_exponential_role"] and "not the primary" in routes["matrix_exponential_role"], "matrix exponential role was not relabeled as special-case check")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"]:
        require(proofs[key]["verdict"] == "unsat", f"{key} proof verdict drift")
        require(proofs[key]["load_bearing"] is True, f"{key} proof not load-bearing")
        require(proofs[key]["asserted_precomputed_boolean"] is False, f"{key} binds a boolean")
        require(proofs[key]["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof", f"{key} proof scope drift")
        require(proofs[key]["bound_raw_values"]["2*Pit_b_z"] == -1, f"{key} bound raw value drift")
        require(proofs[key]["wrong_control_can_fail"] is True, f"{key} wrong control missing")

    require(payload["julia_density_generator_derivation"]["all_pass"] is True, "Julia density derivation failed")
    require(payload["pytorch_pinned_mirror"]["affine_batch"]["pass"] is True, "PyTorch affine batch failed")
    require(set(payload["claim_path_tools"]).isdisjoint({"numpy", "scipy", "mpmath"}), "control-only tool in claim path")
    require("global spinor phase" in payload["quotient_erasure_note"]["erases"], "quotient erasure note missing phase boundary")
    require("Builder self-checks" in payload["self_check_notice"], "self-check notice missing")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
