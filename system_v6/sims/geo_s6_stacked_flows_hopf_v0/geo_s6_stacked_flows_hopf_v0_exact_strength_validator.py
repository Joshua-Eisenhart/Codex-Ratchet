#!/usr/bin/env python3
"""Packet-local exact-strength validator for geo_s6_stacked_flows_hopf_v0.

This is a builder drift guard, not independent audit evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s6_stacked_flows_hopf_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s6_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s6_build_spec_20260610.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"

REQUIRED = {
    "P1_prior_reuse_lineage",
    "P2_arrow_typing_and_mode",
    "P3_z_dot_from_exported_A_b",
    "P4_shell_classification",
    "P5_leakage_integrals_are_flux",
    "P6_A_F_h_action_status",
    "P7_sixteen_placements_computed",
    "P8_matrix64_reuse_not_rebuild",
    "P9_loop_order_gap",
    "P10_round_trip_gates",
    "P11_consistency_gates",
    "P12_executed_mutation_controls",
    "P13_cross_engine_fatality",
    "P14_claim_ceiling",
}

ALLOWED_STRENGTHS = {
    "lineage_citation_only",
    "exact_symbolic_leakage_formula",
    "closed_form_leakage_integral",
    "flow_solver_with_exact_matrix_exponential_check",
    "transported_loop_connection_action",
    "undefined_without_mixed_lift",
    "computed_placement_pairing",
    "matrix64_reuse_overlay",
    "computed_loop_order_metric",
    "executed_mutation_control",
    "cross_engine_signature",
    "scratch_ceiling_token",
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
    require(payload["engine_contract"]["mode"] == "all_three_full_sims", "engine mode drift")
    require(set(payload["engine_contract"]["lanes"]) == {"julia", "jax", "pytorch"}, "engine lane drift")
    require(all(value is True for value in payload["build_gates"].values()), "one or more build gates failed")
    require(REQUIRED <= set(payload["receipts"]), "missing required positive receipt")
    require(all(payload["positive_ledger"][key]["pass"] is True for key in REQUIRED), "positive ledger has failing row")
    require(set(payload["strength_tokens"]) == ALLOWED_STRENGTHS, "strength token set drift")
    require("Builder self-checks are not audit evidence" in payload["self_check_notice"], "self-check boundary missing")
    require("chi0=pi/7" in payload["pin_spec"], "generic chi0 pin missing")
    require("chi0=pi/8" not in payload["pin_spec"], "stale accidental chi0 pin remains")
    require(payload["genericity_check"]["pass"] is True, "genericity check failed")
    require(payload["genericity_check"]["no_special_trig_zeros"] is True, "special trig zero remains on claim path")
    require(payload["blind_expected_comparison"]["pass"] is True, "blind expected comparison failed")
    require(payload["round_trip_report"]["pass"] is True, "round-trip report failed")
    require(payload["build_gates"]["julia_flow_solver_route"] is True, "Julia flow solver route gate failed")
    require(payload["build_gates"]["jax_loop_flow_solver_route"] is True, "JAX loop flow solver route gate failed")
    require(payload["build_gates"]["jax_shell_flow_solver_route"] is True, "JAX shell flow solver route gate failed")
    require(payload["receipts"]["P10_round_trip_gates"]["exact_strength"] == "flow_solver_with_exact_matrix_exponential_check", "P10 strength route drift")
    require(payload["receipts"]["P10_round_trip_gates"]["data"]["shell_flow_solver_all_pass"] is True, "P10 shell solver route missing or failed")
    require(payload["receipts"]["P10_round_trip_gates"]["data"]["flow_solver_route"]["pass"] is True, "P10 loop solver route missing or failed")
    require(payload["round_trip_report"]["symbolic_z_dot_residuals_zero"] is True, "symbolic z-dot residuals nonzero")
    require(payload["round_trip_report"]["finite_time_derivative_max_error"] <= 1.0e-7, "finite-time derivative round-trip too large")
    require(payload["round_trip_report"]["loop_order_map_recompute_max_error"] <= 1.0e-10, "loop-order map recompute mismatch")

    require(SPEC_COPY.exists() and sha256(SPEC_COPY) == sha256(SPEC), "S6 spec copy missing or changed")
    require(DIRECTIVE_COPY.exists(), "directive copy missing")
    require(payload["copied_inputs"]["s6_build_spec"]["matches_source"] is True, "copied spec record mismatch")
    require(payload["copied_inputs"]["directive_addendum"]["exists"] is True, "directive record mismatch")

    engines = payload["engines"]
    require(set(engines) == {"julia", "jax", "pytorch"}, "engine set drift")
    require(len({record["pin_sha256"] for record in engines.values()}) == 1, "engine PIN hashes differ")
    for engine, record in engines.items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{engine} source missing")
        require(sha256(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["ran"] is True, f"{engine} did not run")
        require(record["reads_peer_result"] is False, f"{engine} reads peer result")
        require(record["aligned_packages_load_bearing"], f"{engine} has no load-bearing package")
        require(record["classification"] == "scratch_diagnostic", f"{engine} classification drift")
        require(record["promotion_allowed"] is False and record["formal_admission_allowed"] is False, f"{engine} ceiling drift")
    require(sha256(ROOT / payload["source_path"]) == payload["source_sha256"], "envelope source hash mismatch")

    require(payload["cross_engine_consistency"]["all_pass"] is True, "cross-engine fatality gate failed")
    require(payload["divergence"]["max_divergence"] == 0, "divergence is nonzero")
    loop_values = payload["cross_engine_consistency"]["loop_order_g_DI_scaled_1e9"]
    require(len(set(loop_values.values())) == 1 and next(iter(loop_values.values())) > 0, "loop-order scaled g_DI mismatch")
    for row_id, row in payload["cross_engine_consistency"]["row_reports"].items():
        require(row["pass"] is True, f"{row_id} cross-engine leakage signature mismatch")

    shell_rows = payload["shell_leakage_rows"]
    require(len(shell_rows) == 8, "shell row count drift")
    allowed_classes = {
        "preserve_T_eta",
        "projected_shell_preserve_but_Hopf_leave",
        "move_leaf",
        "cross_shell",
        "leave_foliation",
    }
    for row_id, row in shell_rows.items():
        require(row["mode"] == "RESTRICTED/STACKED", f"{row_id} mode missing")
        require(row["arrow_type"] == "dynamical/flow", f"{row_id} arrow type drift")
        require(row["derived_from_exported_A_b"] is True, f"{row_id} not derived from exported A,b")
        require(row["s5_A"] and row["s5_b"], f"{row_id} missing S5 A,b")
        require(len(row["eta_rows"]) == 5, f"{row_id} eta row count drift")
        for eta_row in row["eta_rows"]:
            cls = eta_row["classification"]["classification"]
            require(cls in allowed_classes, f"{row_id} invalid class {cls}")
            require(eta_row["leakage_integrals"]["flux_layer"] == "S6_restricted_shell_leakage_flux", f"{row_id} flux layer drift")
            require("L_inner" in eta_row["leakage_integrals"] and "L_outer" in eta_row["leakage_integrals"] and "bar_L" in eta_row["leakage_integrals"], f"{row_id} missing leakage integral")
    require(payload["terrain_summary"]["Si/Hill"]["classifications"] == ["projected_shell_preserve_but_Hopf_leave"], "Si/Hill projection/Hopf-leave class drift")
    require(payload["terrain_summary"]["Ne/Vortex"]["classifications"] == ["cross_shell"], "Ne/Vortex class drift")

    action_rows = payload["terrain_action_rows"]
    require(len(action_rows) == 8, "terrain action row count drift")
    for row_id, row in action_rows.items():
        if row_id.startswith("Ne_"):
            require(row["status"] == "computed_pure_lift_transport_action", f"{row_id} transported pure action missing")
            require("sample_connection_delta_max" not in row, f"{row_id} stale local connection sample remains")
            require(row["transported_loop_A_delta_max"] <= 5.0e-4, f"{row_id} transported A loop delta too large")
            require(row["transported_loop_integrals"], f"{row_id} transported loop integrals missing")
            require(any(by_loop["outer"]["Phi_ij"] == "undefined_no_coherent_shell_map" for by_loop in row["transported_loop_integrals"].values()), f"{row_id} transported outer loop did not expose undefined Phi_ij")
        else:
            require(row["status"] == "blocked_for_A_F_h_without_mixed_lift", f"{row_id} nonunitary mixed-lift boundary drift")
            require(row["Phi_T_star_A_minus_A"] == "undefined_without_mixed_lift", f"{row_id} A smuggle")

    placements = payload["placement_rows"]
    require(len(placements) == 16, "placement row count drift")
    require({row["placement_id"] for row in placements} == set(range(1, 17)), "placement ids drift")
    require(all(row["imported_s5"]["row_id"] and row["z_dot_formula"] for row in placements), "placement missing computed pairing data")
    relevant_swaps = [row for row in placements if row["swap_control"]["relevant_density_visible_row"]]
    require(relevant_swaps, "no relevant swap controls")
    require(all(row["swap_control"]["swap_changes_relevant_rows"] is True for row in relevant_swaps), "not every phase-sensitive swap control changed after chi0 repin")
    phase_sensitive_terrains = {row["terrain_row_id"] for row in placements if row["swap_control"]["phase_sensitive_formula"]}
    require({"Ne_Vortex_L", "Ne_Spiral_R", "Se_Funnel_L", "Se_Cannon_R", "Ni_Pit_L", "Ni_Source_R", "Si_Citadel_R"} <= phase_sensitive_terrains, "generic phase-sensitive terrain set incomplete")

    overlay = payload["matrix64_overlay_rows"]
    require(len(overlay) == 64, "Matrix64 overlay row count drift")
    require(all(row["recomputed_matrix64"] is False for row in overlay), "Matrix64 recompute drift")
    require(all("Delta_T_O_fro" in row["matrix64_reuse"] for row in overlay), "Matrix64 Delta_T,O missing")

    loop = payload["loop_order_gap"]
    require(loop["shared_carrier"] == "density/Bloch carrier because E=Si_Hill_L is nonunitary dephasing", "loop shared carrier drift")
    require(loop["max_g_DI_scaled_1e9"] == next(iter(loop_values.values())), "loop gap scalar drift")
    require(loop["controls"]["commuting_erased_control"]["pass"] is True, "commuting control failed")
    require(loop["controls"]["noncommuting_control"]["pass"] is True, "noncommuting control failed")
    require(loop["controls"]["carrier_mismatch_control"]["gate_passed_after_mutation"] is False, "carrier mismatch control did not fail")
    require(len(loop["sample_rows"]) == 20, "loop-order sample row count drift")
    require(loop["flow_solver_route"]["pass"] is True, "loop-order solver route failed")
    routes = payload["flow_solver_routes"]
    require(routes["julia_loop"]["tool"] == "DifferentialEquations" and routes["julia_loop"]["pass"] is True, "Julia DifferentialEquations loop route missing or failed")
    require(routes["jax_loop"]["tool"] == "diffrax" and routes["jax_loop"]["pass"] is True, "JAX diffrax loop route missing or failed")
    require(routes["jax_shell_eta_rows_all_pass"] is True, "JAX diffrax shell eta route missing or failed")
    require("exact" in routes["matrix_exponential_role"] and "not the primary" in routes["matrix_exponential_role"], "matrix exponential role was not relabeled as special-case check")

    controls = payload["negative_controls"]
    for i in range(1, 19):
        key_prefix = f"C{i:02d}_"
        matches = [name for name in controls if name.startswith(key_prefix)]
        require(len(matches) == 1, f"C{i:02d} missing")
        row = controls[matches[0]]
        require(row["executed"] is True, f"{matches[0]} was not executed")
        require(row["computed_mutation"] is True, f"{matches[0]} was not computed")
        require(row["mutation_rerun_through_same_gate"] is True, f"{matches[0]} was not rerun through same gate")
        require("rerun_gate_result" in row and row["rerun_gate_result"]["pass"] is False, f"{matches[0]} rerun gate result missing or passing")
        require(bool(row.get("failing_values")), f"{matches[0]} failing values missing")
        require(row["gate_passed_after_mutation"] is False, f"{matches[0]} mutation did not fail")
        require(row["expected_failure_observed"] is True, f"{matches[0]} expected failure missing")
    require(controls["all_executed_can_fail"] is True, "controls aggregate failed")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"]:
        require(proofs[key]["ran"] is True, f"{key} did not run")
        require(proofs[key]["verdict"] == "unsat", f"{key} proof verdict drift")
        require(proofs[key]["load_bearing"] is True, f"{key} proof not load-bearing")
        require(proofs[key]["bound_raw_values"]["g_DI_scaled_1e9"] == loop["max_g_DI_scaled_1e9"], f"{key} bound value drift")

    require(set(payload["claim_path_tools"]).isdisjoint({"numpy", "scipy", "mpmath"}), "control-only tool in claim path")
    require("undefined_without_lift" in payload["pin_spec"], "literal undefined-without-lift token missing")
    require("RESTRICTED_STACKED" in payload["pin_spec"], "literal mode token missing")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
