#!/usr/bin/env python3
"""Behavior tests for basin_criterion_pilot_v0."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "basin_criterion_pilot_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}.py"


def load_module():
    spec = importlib.util.spec_from_file_location(SIM_ID, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_panel_rows_classify_affine_and_conditioned_shell_without_promotion():
    module = load_module()
    payload = module.build_payload()

    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["all_pass"] is True
    assert payload["TOOL_MANIFEST"]
    assert payload["TOOL_INTEGRATION_DEPTH"]["sympy"] == "load_bearing"

    ne = payload["criterion_rows"]["Ne_Spiral_R"]
    assert ne["affine_panel"]["charpoly"] == "lambda*(lambda**2 + 4)"
    assert ne["affine_panel"]["whole_ball_classification"] == "invariant_not_attracting"
    assert ne["conditioned_T_pi_over_6"]["z_dot"] == "sqrt(2)*cos(theta + pi/4)"
    assert ne["conditioned_T_pi_over_6"]["classification"] == [
        "shell_breaking",
        "neither",
        "empty_conditioned_survivor",
    ]
    assert ne["earned_vocabulary_term"] == "invariant affine orbit family on the whole Bloch ball"

    ni = payload["criterion_rows"]["Ni_Source_R"]
    assert ni["affine_panel"]["charpoly"] == "lambda**3 + lambda**2 + 189*lambda/400 + 203/2400"
    assert ni["affine_panel"]["whole_ball_classification"] == "attracting"
    assert ni["affine_panel"]["fixed_norm_squared"] == "37113/41209"
    assert ni["conditioned_T_pi_over_6"]["z_dot"] == "sqrt(2)*cos(theta + pi/4)/5 + 1/4"
    assert ni["conditioned_T_pi_over_6"]["radial_derivative"] == "-1/8"
    assert ni["conditioned_T_pi_over_6"]["classification"] == [
        "shell_breaking",
        "neither",
        "empty_conditioned_survivor",
    ]
    assert ni["earned_vocabulary_term"] == "attracting affine fixed point on the whole Bloch ball"

    se = payload["criterion_rows"]["Se_Funnel_L"]
    assert se["affine_panel"]["charpoly"] == "lambda**3 + 12*lambda**2/5 + 52*lambda/25 + 16/25"
    assert se["affine_panel"]["whole_ball_classification"] == "attracting"
    assert se["affine_panel"]["fixed_point_or_set"] == ["0", "0", "0"]
    assert se["affine_panel"]["fresh_recompute"]["eigenvalues_exact"] == [
        "-4/5",
        "-4/5 - 2*I/5",
        "-4/5 + 2*I/5",
    ]
    assert se["affine_panel"]["fresh_recompute"]["bloch_ball_inward_derivative"] == "-8*x**2/5 - 8*y**2/5 - 8*z**2/5"
    assert se["conditioned_T_pi_over_6"]["z_dot"] == "-sqrt(2)*cos(theta + pi/4)/5 - 2/5"
    assert se["earned_vocabulary_term"] == "attracting affine fixed point on the whole Bloch ball"

    pit = payload["criterion_rows"]["Ni_Pit_L"]
    assert pit["affine_panel"]["charpoly"] == "lambda**3 + lambda**2 + 189*lambda/400 + 203/2400"
    assert pit["affine_panel"]["whole_ball_classification"] == "attracting"
    assert pit["affine_panel"]["fresh_recompute"]["fixed_point"] == [
        "-8*(8 + 5*sqrt(3))/203",
        "8*(-8 + 5*sqrt(3))/203",
        "-139/203",
    ]
    assert pit["affine_panel"]["fresh_recompute"]["eigenvalues_numeric"] == [
        "-0.341645905918435",
        "-0.329177047040782 - 0.373119941592383*I",
        "-0.329177047040782 + 0.373119941592383*I",
    ]
    assert pit["conditioned_T_pi_over_6"]["z_dot"] == "-sqrt(2)*cos(theta + pi/4)/5 - 3/4"
    assert pit["conditioned_T_pi_over_6"]["radial_derivative"] == "-9/8"
    assert pit["earned_vocabulary_term"] == "attracting affine fixed point on the whole Bloch ball"

    banned_term = "terminal/closed" + "_communicating_class"
    assert banned_term not in str(payload)


def test_binding_basin_packet_contract_and_frontier_are_explicit():
    module = load_module()
    payload = module.build_payload()

    contract = payload["binding_basin_packet_contract"]
    assert contract["M_C_native_fields"]["S"]["status"] == "pass"
    assert contract["M_C_native_fields"]["R_C"]["status"] == "blocked"
    assert contract["clustering_model_agreement_guard"]["basin_language_allowed"] is False
    assert len(contract["nine_card_requirements"]) == 9
    assert [row["requirement"] for row in contract["nine_card_requirements"]] == [
        "finite S",
        "Adm_C",
        "R_C explicit",
        "trapping test",
        "Lyapunov/monotone-exclusion observable",
        "escape tests",
        "basin partition",
        "engine-DoF perturbation test",
        "negative controls",
    ]
    assert contract["conley_lattice_read"]["same_finite_morse_graph_instantiated"] is False

    frontier = payload["sub_basin_frontier"]
    assert frontier["affine_multiple_attractor_answer"] == "no_not_generically"
    assert frontier["first_sub_basin_target"] == "ratchet_deep_chain_v0"
    assert frontier["frontier_status"] == "candidate"
    assert "nonlinear/composite/stage-word rows" in frontier["next_frontier"]


def test_ratchet_step_negative_controls_and_engine_dof_are_bounded():
    module = load_module()
    payload = module.build_payload()

    ratchet = payload["ratchet_chain_step"]
    assert ratchet["source"] == "ratchet_deep_chain_v0"
    assert ratchet["final_effective_denominator"] == 16
    assert ratchet["V_narrow"]["candidate_role"] == "Lyapunov_type_candidate"
    assert ratchet["entropy_deltas"]["telemetry_role"] == "typed_telemetry"

    controls = payload["negative_controls"]
    assert sorted(controls) == [
        "F01_only",
        "N01_only",
        "commutative_collapse",
        "quotient_erased",
        "root_off",
        "shuffled_order",
        "similarity_only_cluster",
    ]
    assert all(row["result_status"] in {"diagnostic_only", "blocked"} for row in controls.values())

    perturbation = payload["engine_DoF_perturbation"]
    assert perturbation["perturbation"] == "stage_order_swap_steps_2_3"
    assert perturbation["membership_or_stability_changed"] is True
    assert perturbation["stage_classification"] == "earned_order_DoF_for_this_packet"
