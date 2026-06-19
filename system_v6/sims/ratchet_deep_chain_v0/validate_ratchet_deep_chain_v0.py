#!/usr/bin/env python3
"""Validate ratchet_deep_chain_v0 result shape and bounded gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_deep_chain_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
EXPECTED_PARENTS = {
    "ratchet_s1_single_shell_pilot_v0",
    "ratchet_s2_two_shell_flux_v0",
    "ratchet_s6_terrain_operator_shell_v0",
    "ratchet_g2_family_v0",
    "ratchet_s2_three_shell_chain_v0",
    "geo_disintegration_machinery_v0",
    "geo_union_rule_k_leaves_v0",
    "geo_s1_finite_phase_lens_v0",
    "compression_flow_radiated_record_v0",
}


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("mode") == "RATCHETED", errors, "mode must be RATCHETED")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    parents = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    require(set(parents) == EXPECTED_PARENTS, errors, "parent_lineage must contain exactly the prompt parents and cited committed towers")
    for name in EXPECTED_PARENTS:
        parent = as_dict(parents.get(name), f"parent_lineage.{name}", errors)
        for key in ("committed_tree", "committed_commit", "envelope_sha256", "top_source_sha256", "allowed_use"):
            require(bool(parent.get(key)), errors, f"{name}.{key} missing")

    engines = as_dict(payload.get("engines"), "engines", errors)
    require(set(engines) == {"julia", "jax"}, errors, "engines must contain scoped julia and jax")
    for engine_name in ("julia", "jax"):
        engine = as_dict(engines.get(engine_name), f"engines.{engine_name}", errors)
        require(engine.get("ran") is True, errors, f"{engine_name} must be marked ran")
        require(engine.get("reads_peer_result") is False, errors, f"{engine_name} must not read peer result")
        require(bool(engine.get("source_path")), errors, f"{engine_name}.source_path required")
        require(bool(engine.get("aligned_packages_load_bearing")), errors, f"{engine_name}.aligned load-bearing required")

    sequence = as_dict(payload.get("ratchet_sequence"), "ratchet_sequence", errors)
    ledger = as_dict(sequence.get("per_step_ledger"), "per_step_ledger", errors)
    rows = ledger.get("rows")
    require(isinstance(rows, list) and len(rows) >= 7, errors, "per-step ledger must have at least seven rows")
    if isinstance(rows, list):
        require([row.get("step") for row in rows] == list(range(1, len(rows) + 1)), errors, "ledger steps must be sequential")
        require(rows[0].get("constraint") == "condition_on_T_pi_over_6", errors, "step 1 must condition T_pi/6")
        require(rows[1].get("constraint") == "Z4_finite_phase_lens_quotient", errors, "step 2 must be Z4")
        require(rows[2].get("constraint") == "descended_single_leaf_phase_window", errors, "step 3 must be phase window")
        require(rows[3].get("constraint") == "second_Z2_lens_on_quotient", errors, "step 4 must be second Z2 quotient")
        require(rows[4].get("constraint") == "terrain_basin_restriction_Se_Funnel_L", errors, "step 5 must be terrain basin")
        require(rows[-1].get("entropy", {}).get("delta_nats") == "0", errors, "saturation row entropy delta must be zero")
    require(ledger.get("final_effective_denominator") == 16, errors, "final denominator must be 16")
    require(ledger.get("final_chart_volume") == "pi**2/4", errors, "final chart volume mismatch")
    band_limit = str(ledger.get("band_limit_convention", ""))
    require("Band-limit convention:" in band_limit, errors, "band-limit convention must be text-pinned")
    require(
        "conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart|chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|conditional_chart_density=1/(4*pi^2)|finite_grid_physical_points=N^2/2|controls=naive_zero_denominator,positive_eta_band,flat_marginal_wrong,null_set_modification"
        in band_limit,
        errors,
        "committed disintegration convention fragment must be pinned literally",
    )
    composite = as_dict(ledger.get("composite_action_adjudication"), "composite_action_adjudication", errors)
    require(composite.get("earned_composite_structure") == "Z4 x Z2", errors, "composite structure must be computed as Z4 x Z2")
    require(len(composite.get("second_stage_orbit_table", [])) == 8, errors, "second-stage orbit table must contain eight representative rows")
    require(len(composite.get("product_order_table", [])) == 8, errors, "composite product order table must contain eight products")
    if isinstance(composite.get("product_order_table"), list):
        require(max(row.get("order", 0) for row in composite["product_order_table"]) == 4, errors, "Z4 x Z2 action must have max element order 4")
    rivals = as_dict(composite.get("rival_discriminators"), "composite_action_adjudication.rival_discriminators", errors)
    require(rivals.get("Z4_x_Z2", {}).get("has_order_8_element") is False, errors, "Z4 x Z2 discriminator must have no order-8 element")
    require(rivals.get("Z8", {}).get("has_order_8_element") is True, errors, "Z8 rival must expose an order-8 element")
    require(rivals.get("quotient_collapse_b_equals_a_squared", {}).get("orbit_size_from_q0r0") == 4, errors, "collapse rival must have orbit size 4")
    if isinstance(rows, list) and len(rows) >= 4:
        for idx in (2, 3):
            geom = as_dict(rows[idx].get("induced_geometry"), f"rows[{idx}].induced_geometry", errors)
            require(bool(geom.get("connection_coefficient_dchi")), errors, f"step {idx + 1} induced connection missing")
            require(bool(geom.get("holonomy_data")), errors, f"step {idx + 1} holonomy data missing")
            require(bool(geom.get("orbit_object")), errors, f"step {idx + 1} orbit object missing")

    path = as_dict(sequence.get("path_sensitivity"), "path_sensitivity", errors)
    require(path.get("adjacent_swap_commuting", {}).get("honest_commutation") is True, errors, "commuting adjacent swap missing")
    require(path.get("adjacent_swap_mortality", {}).get("mortality", {}).get("class") == "quotient_well_definedness_equivariance_failure", errors, "mortality class mismatch")
    require(path.get("terrain_order_gap", {}).get("Se_then_Rx_gap_norm_squared") == "4/25", errors, "terrain order gap mismatch")

    mortality = as_dict(sequence.get("mortality_exhibit"), "mortality_exhibit", errors)
    require(mortality.get("Z4_equivariant") is False, errors, "Z4 mortality exhibit must fail equivariance")
    require(mortality.get("Z2_equivariant") is False, errors, "Z2 mortality exhibit must fail equivariance")
    saturation = as_dict(sequence.get("saturation"), "saturation", errors)
    require(saturation.get("status") == "saturated_for_available_committed_constraint_set", errors, "saturation status mismatch")

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(controls.get("nothing_excluded_step", {}).get("byte_exact_pass_through") is True, errors, "nothing-excluded control must be byte-exact")
    require(controls.get("naive_conditioning_fails", {}).get("pass") is True, errors, "naive conditioning failure must pass")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_verdict") == "sat", errors, f"{solver} erased flip must be sat")
        require(row.get("erased_flip_detected") is True, errors, f"{solver} erased flip must be detected")
    julia_z3 = as_dict(proofs.get("julia_z3"), "julia_z3", errors)
    require(julia_z3.get("verdict") == "unsat", errors, "Julia Z3 verdict must be unsat")
    require(julia_z3.get("erased_flip_verdict") == "sat", errors, "Julia Z3 erased flip must be sat")
    require(julia_z3.get("erased_flip_detected") is True, errors, "Julia Z3 erased flip missing")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool calls must be load-bearing")
        sympy_call = as_dict(calls[0], "tool_calls[0]", errors)
        for key in ("positive_case", "negative/erased_control", "boundary_case", "demotion_condition"):
            require(bool(sympy_call.get(key)), errors, f"sympy tool call missing {key}")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    addendum = as_dict(payload.get("builder_hardening_addendum"), "builder_hardening_addendum", errors)
    closed = addendum.get("closed", [])
    for closure in ("G1_G2_composite_action", "G3_induced_geometry_steps_3_4", "G4_band_limit_convention", "G6_sympy_full_receipt"):
        require(closure in closed, errors, f"builder hardening addendum missing {closure}")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "ceilings_preserved",
        "parent_lineage_all_prompt_parents_present",
        "per_step_ledger_present",
        "entropy_deltas_computed",
        "composite_group_derived",
        "composite_group_adjudicated_against_rivals",
        "induced_geometry_steps_3_4_present",
        "band_limit_convention_pinned",
        "sympy_receipt_full_shape",
        "order_sensitivity_two_adjacent_swaps",
        "mortality_exhibit_genuine",
        "saturation_scoped",
        "controls_fired",
        "smt_positive_and_erased_flip",
        "julia_result_loaded",
        "julia_source_hash_matches",
        "julia_reads_no_peer_result",
        "julia_engine_values_match_python_exact_rows",
        "julia_z3_positive_and_erased_flip",
        "one_to_one_tool_calls",
        "capability_receipts_present",
        "audit_verdict_consumed_as_input_not_builder_output",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be zero")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "Julia and Python rows must match")
    else:
        errors.append("engine_values must contain julia and jax")
    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    out = {
        "ok": not errors,
        "result_json": rel(result_path),
        "validator": rel(Path(__file__)),
        "validated_mode": payload.get("mode"),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
