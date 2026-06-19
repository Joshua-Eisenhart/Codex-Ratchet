from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "manifold_dynamic_chart_v0"
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


def test_build_card_pins_owner_boundary_and_g2a() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "Family A 33-cell dynamic density-state chart" in text
    assert "final substrate remains OWNER-CHOICE" in text
    assert "scratch_diagnostic" in text
    assert "NO git add/commit" in text
    assert "G.2a idempotency-from-birth" in text
    assert "scripts/builder_audit_boundary.py" in text
    assert "NO Axis-0 admission" in text


def test_state_rows_are_density_trajectories_and_entropy_is_state_derived() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["claim_ceiling"] == "scratch_diagnostic_dynamic_chart_v0_first_measurement_attempt_only"
    assert payload["carrier"]["state_count"] == 33
    assert payload["trajectory"]["T"] > 1
    assert payload["witness_gates"]["density_validity"]["pass"] is True
    assert payload["witness_gates"]["entropy_source"]["pass"] is True
    assert payload["witness_gates"]["dynamics_nontriviality"]["pass"] is True

    state_rows = payload["state_rows"]
    assert len(state_rows) == 33 * (payload["trajectory"]["T"] + 1)
    assert {row["entropy_source"] for row in state_rows} == {"computed_from_rho_eigenvalues"}
    assert all(row["density_trace_close_to_one"] for row in state_rows)
    assert all(row["density_psd"] for row in state_rows)
    assert all(row["density_hermitian"] for row in state_rows)
    assert any(row["current_cell"] != row["state_id"] for row in state_rows if row["t"] > 0)
    assert payload["entropy_field"]["entropy_type"] == "local_von_neumann"
    assert payload["entropy_field"]["state_source"] == "rho_c(t)_from_bloch_cell_density_matrix"
    assert "phi" not in payload["entropy_field"]["computed_from"].lower()


def test_dynamic_shells_jk_fuzz_and_perturb_classifier_are_computed() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["witness_gates"]["shell_gate"]["pass"] is True
    assert payload["witness_gates"]["jk_gate"]["pass"] is True
    assert payload["witness_gates"]["perturbation_bite"]["pass"] is True

    shell_rows = payload["dynamic_shell_rows"]
    assert len(shell_rows) == payload["trajectory"]["T"] + 1
    assert {row["shell_rule_id"] for row in shell_rows} == {"entropy_level_recomputed_each_t"}
    assert any(row["boundary_edge_count"] > 0 for row in shell_rows)
    assert payload["dynamic_shell_motion"]["total_entered_or_exited"] > 0
    assert payload["dynamic_shell_alternatives"]["correlation_boundary_shell"] == "blocked_until_rho_AB_or_surface_cut"

    jk_rows = payload["jk_fuzz_rows"]
    assert len(jk_rows) == len(payload["state_rows"])
    assert all(row["candidate_continuations_k"] >= row["admissible_continuations_j"] for row in jk_rows)
    assert all(row["admissible_target_count"] <= row["admissible_continuations_j"] for row in jk_rows)
    assert any(row["fuzz_class"] in {"split", "broad", "low"} for row in jk_rows)

    classifier = payload["axis0_response_protocol_v0"]
    assert classifier["protocol"] == "perturb->watch->classify"
    assert classifier["axis0_admission"] == "not_admitted_first_honest_attempt"
    assert classifier["classifier_input_fields_exclude_identity"] is True
    assert "cell_id" not in classifier["classifier_feature_fields"]
    assert classifier["perturbation_family"]["small_committed_kick"]["changed_initial_state_count"] > 0
    assert classifier["region_classifications"]
    assert {row["spread_or_damp"] for row in classifier["region_classifications"].values()} <= {"SPREAD", "DAMP", "NEUTRAL", "REFUSE"}


def test_controls_and_static_phi_bridge_are_falsifiable_not_assumed() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["controls"]
    assert controls["identity_dynamics"]["classifier_status"] == "refuse_degenerate_static"
    assert controls["identity_dynamics"]["dynamics_nontrivial"] is False
    assert controls["scrambled_adjacency"]["ran"] is True
    assert controls["dropped_half_perturbation_family"]["ran"] is True
    assert controls["no_identity_leak"]["identity_fields_excluded"] == ["cell_id", "state_id", "start_cell", "current_cell"]
    assert controls["no_identity_leak"]["classifier_input_fields_exclude_identity"] is True

    bridge = payload["static_phi_bridge_row"]
    assert bridge["old_anchor_role"] == "static_proxy_equilibrium_shadow_candidate_only"
    assert bridge["falsifier"] == "old_phi_sign fails to predict spread/damp better than control/null"
    assert bridge["tested_not_assumed"] is True
    assert bridge["accuracy"] >= 0.0
    assert bridge["majority_baseline_accuracy"] >= 0.0
    assert bridge["outcome"] in {"predicts_above_chance", "fails_above_chance"}


def test_three_engine_envelope_validator_and_tests_pass() -> None:
    payload = load_envelope()
    assert payload["schema"] == "manifold_dynamic_chart_v0_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert payload["engine_consensus"]["state_count_agreement"] is True
    assert payload["engine_consensus"]["trajectory_signature_agreement"] is True
    assert payload["engine_consensus"]["entropy_signature_agreement"] is True
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
