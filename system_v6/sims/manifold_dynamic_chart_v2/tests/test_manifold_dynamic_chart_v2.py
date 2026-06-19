from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "manifold_dynamic_chart_v2"
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"


def load_common():
    common_path = SIM_DIR / f"{SIM_ID}_common.py"
    assert common_path.is_file(), f"missing common module: {common_path}"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", common_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_envelope() -> dict:
    assert ENVELOPE.is_file(), f"missing envelope result: {ENVELOPE}"
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


def test_build_card_pins_axis0_experiment_and_g2a() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "Axis-0 EXPERIMENT v2" in text
    assert "32/33" in text
    assert "STABILITY-axis" in text
    assert "shell-weighted TV" in text
    assert "NO git add/commit" in text
    assert "G.2a idempotency-from-birth" in text
    assert "scripts/builder_audit_boundary.py" in text
    assert "no admission" in text.lower()


def test_full_sweep_grid_and_v0_regression_are_computed() -> None:
    common = load_common()
    payload = common.build_packet()
    experiment = payload["axis0_experiment_v2"]

    assert payload["classification"] == "scratch_diagnostic"
    assert payload["claim_ceiling"] == "scratch_diagnostic_axis0_experiment_v2_no_admission"
    assert experiment["criterion_rule"] == common.SEPARATION_RULE_VERBATIM
    assert [row["family_id"] for row in experiment["perturbation_families"]] == [
        "unitary_kicks",
        "dephasing_kicks",
        "amplitude_kicks",
        "generator_biased_kicks",
        "purity_projective_resets",
    ]
    assert [row["strength_steps"] for row in experiment["strength_ladder"]] == [1, 2, 3, 4]
    assert [row["target_mode"] for row in experiment["target_modes"]] == ["single_cell", "neighborhood", "shell_boundary"]
    assert experiment["v1_anchor_corner"] == common.V1_ANCHOR_CORNER
    assert experiment["window_ladder"] == common.window_ladder()
    assert 12 in experiment["window_ladder"]
    assert experiment["relaxation_scale_calibration"]["slowest_relaxation_tau_steps"] > 12
    assert max(experiment["window_ladder"]) >= int(experiment["relaxation_scale_calibration"]["slowest_relaxation_tau_steps"])
    assert [row["classifier_id"] for row in experiment["classifiers"]] == [
        "v0_divergence",
        "baseline_growth_rate_sign",
        "recovery_return_time",
        "shell_weighted_tv",
    ]

    expected_rows = 5 * 4 * 3 * len(common.window_ladder()) * 4
    assert experiment["sweep_row_count"] == expected_rows
    assert len(experiment["full_sweep_grid"]) == expected_rows
    assert experiment["agreement_threshold_row_count"] == len(experiment["agreement_threshold_rows"])
    assert experiment["v1_anchor_disagreement"]["v1_best_partial_regression"]["pass"] is True
    assert payload["v0_regression"]["observed_distribution"] == {"DAMP": 1, "SPREAD": 32}
    assert payload["v0_regression"]["pass"] is True


def test_witness_gates_controls_and_criterion_fields() -> None:
    common = load_common()
    payload = common.build_packet()
    gates = payload["witness_gates"]
    assert gates["density_validity"]["pass"] is True
    assert gates["entropy_source"]["pass"] is True
    assert gates["dynamics_nontriviality"]["pass"] is True
    assert gates["perturbation_bite_per_family"]["pass"] is True
    assert gates["full_grid_gate"]["pass"] is True
    assert gates["agreement_threshold_gate"]["pass"] is True
    assert gates["classifier_gate"]["pass"] is True
    assert gates["relaxation_window_gate"]["pass"] is True
    assert gates["v0_regression_gate"]["pass"] is True
    assert gates["v1_anchor_regression_gate"]["pass"] is True

    controls = payload["controls"]
    assert controls["identity_dynamics"]["classifier_status"] == "refuse_degenerate_static"
    assert controls["scrambled_adjacency"]["ran"] is True
    assert controls["label_permutation"]["ran"] is True
    assert controls["dropped_half_per_family"]["ran"] is True
    assert controls["no_identity_leak"]["classifier_input_fields_exclude_identity"] is True

    first_row = next(row for row in payload["axis0_experiment_v2"]["full_sweep_grid"] if row["row_status"] == "ran")
    for key in [
        "class_distribution",
        "majority_baseline_accuracy",
        "best_non_identity_predictor",
        "negative_controls",
        "criterion_rule",
        "criterion_verdict",
        "failure_reasons",
    ]:
        assert key in first_row
    assert first_row["criterion_rule"] == common.SEPARATION_RULE_VERBATIM


def test_state_rows_remain_state_derived_density_rows() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["trajectory"]["T"] == max(common.window_ladder())
    assert len(payload["state_rows"]) == 33 * (max(common.window_ladder()) + 1)
    assert {row["entropy_source"] for row in payload["state_rows"]} == {"computed_from_rho_eigenvalues"}
    assert all(row["density_trace_close_to_one"] for row in payload["state_rows"])
    assert all(row["density_psd"] for row in payload["state_rows"])
    assert all(row["density_hermitian"] for row in payload["state_rows"])
    assert payload["dynamic_shell_motion"]["shells_can_move"] is True
    assert len(payload["jk_fuzz_rows"]) == len(payload["state_rows"])


def test_three_engine_envelope_validator_and_tests_pass() -> None:
    payload = load_envelope()
    assert payload["schema"] == "manifold_dynamic_chart_v2_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert payload["engine_consensus"]["state_count_agreement"] is True
    assert payload["engine_consensus"]["trajectory_signature_agreement"] is True
    assert payload["builder_gates"]["boundary_helper_fully_used"] is True
    assert payload["no_builder_audit_verdict"] is True
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        ["/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
