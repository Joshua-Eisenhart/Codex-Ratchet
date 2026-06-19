from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT = SIM_DIR / "results" / "engines_run_with_axes_v0_results.json"

sys.path.insert(0, str(SIM_DIR))
import engines_run_with_axes_v0_common as common  # noqa: E402


def test_build_card_names_boundaries_and_baseline() -> None:
    card = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert common.SIM_ID in card
    assert "NO git add/commit" in card
    assert "boundary helper" in card
    assert "classical_baseline" in card
    assert common.CLAIM_CEILING in card


def test_carnot_and_szilard_execute_as_33_cell_dynamics() -> None:
    payload = common.build_packet()
    assert payload["execution_kind"] == "dynamics_on_committed_33_cell_carrier"
    assert payload["carrier"]["state_count"] == 33
    assert set(payload["running_engines"]) == {"carnot", "szilard"}

    for engine_name in ("carnot", "szilard"):
        engine = payload["running_engines"][engine_name]
        assert engine["row_classification"] == "classical_baseline"
        assert len(engine["strokes"]) == 4
        assert engine["trajectory"]["initial_cell_count"] == 33
        assert engine["trajectory"]["final_cell_count"] == 33
        assert engine["typed_ledger"]
        for stroke in engine["strokes"]:
            assert stroke["transition_count"] == 33
            assert stroke["missing_transition_count"] == 0
            assert len(stroke["state_trajectory"]) == 33
            assert stroke["typed_ledger"]["stroke"]
            assert stroke["axis_signature"]["computed_on"] == "post_stroke_running_trajectory"


def test_axis_signatures_are_consumed_from_committed_readouts() -> None:
    payload = common.build_packet()
    locks = payload["axis_readout_source_locks"]
    assert locks["axis0"]["commit_hint"] == "5d330b427"
    assert locks["axis6"]["commit_hint"] == "b6fafc67f"
    assert locks["axis4"]["commit_hint"] == "99c4f84b3"
    assert locks["axis5_family_partial"]["commit_hint"] == "99906e7d7"

    for engine in payload["running_engines"].values():
        for stroke in engine["strokes"]:
            sig = stroke["axis_signature"]
            assert set(sig["axis_profiles"]) == {"axis0", "axis6", "axis4", "axis5_family"}
            for axis_name, profile in sig["axis_profiles"].items():
                assert profile["ordered_signature_sha256"]
                assert profile["count_signature_sha256"]
                assert profile["source_readout"] == locks[axis_name if axis_name != "axis5_family" else "axis5_family_partial"]["sim_id"]
            assert sig["per_stroke_polarity_row"]["stroke_index"] == stroke["stroke_index"]


def test_controls_comparison_and_baseline_row() -> None:
    payload = common.build_packet()
    assert payload["all_pass"] is True
    assert payload["baseline_row"]["classification"] == "classical_baseline"
    assert payload["baseline_row"]["role"] == "classical_baseline_for_future_qit_engine_signature"
    assert payload["ledger_continuity"]["ledger_v1_commit_hint"] == "d79d71a0d"
    assert payload["ledger_continuity"]["carnot_stroke_names_match"] is True
    assert payload["ledger_continuity"]["szilard_paid_row_sat"] is True

    controls = payload["controls"]
    assert controls["do_nothing_identity_engine"]["degenerate_signatures"] is True
    assert controls["do_nothing_identity_engine"]["all_strokes_identity"] is True
    assert controls["shuffled_stroke_order_N01"]["carnot"]["signature_changed"] is True
    assert controls["shuffled_stroke_order_N01"]["szilard"]["signature_changed"] is True

    comparison = payload["carnot_vs_szilard_signature_comparison"]
    assert comparison["computed"] is True
    assert comparison["profiles_differ"] is True
    assert comparison["differing_stroke_rows"]


def test_generated_result_and_validator_pass() -> None:
    assert RESULT.is_file()
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors = common.validate_payload(payload)
    assert errors == []
