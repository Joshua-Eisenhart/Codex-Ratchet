#!/usr/bin/env python3
"""Contract tests for axis_triple_consistency_b6_v0."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
SIM_ID = "axis_triple_consistency_b6_v0"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"


def load_common():
    spec = importlib.util.spec_from_file_location("axis_triple_common_under_test", SIM_DIR / f"{SIM_ID}_common.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_envelope() -> dict:
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


def test_packet_files_and_build_card_boundary():
    required = [
        "build_card.md",
        f"{SIM_ID}_common.py",
        f"{SIM_ID}_julia.jl",
        f"{SIM_ID}_jax.py",
        f"{SIM_ID}_pytorch.py",
        "write_envelope_spec.py",
        f"validate_{SIM_ID}.py",
    ]
    for rel_path in required:
        assert (SIM_DIR / rel_path).is_file(), rel_path
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert "b_6 = -b_0 b_3" in text
    assert "axis_readout_candidate_only + consistency_row_only" in text
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_common_rebuild_counts_and_panel_points():
    common = load_common()
    obj = common.build_axis_triple_object()
    summary = obj["consistency_summary"]
    assert obj["claim_ceiling"] == "axis_readout_candidate_only + consistency_row_only"
    assert summary["sample_total"] == 48
    assert summary["agreement_count"] == 16
    assert summary["violation_count"] == 32
    assert summary["nonneutral_total"] == 32
    assert summary["nonneutral_agreement_count"] == 16
    assert len(obj["consistency_table"]) == 48
    assert len(obj["violation_rows"]) == 32
    assert all(row["computed_b6_sign"] == -1 for row in obj["panel_point_checks"])
    assert all(row["panel_expected_b6"] == -1 for row in obj["panel_point_checks"])
    assert all(row["matches_panel_expected"] for row in obj["panel_point_checks"])


def test_controls_and_smt_are_not_tautological():
    payload = load_envelope()
    controls = payload["controls"]
    assert controls["convention_flip_control"]["all_flipped_expected_equals_positive_product"] is True
    assert controls["scrambled_b6_control"]["agreement_fraction_nonzero_expected"] <= 0.75
    assert controls["commuting_control"]["all_neutral"] is True
    assert controls["relation_can_fail_control"]["violation_count"] == 32
    assert payload["independence_reminder_row"] == "consistency != independence; agreement supports only a consistency row and cannot prove axis independence."
    smt_rows = payload["smt_rows"]
    assert set(smt_rows) == {"z3_computed_table", "cvc5_computed_table"}
    for row in smt_rows.values():
        assert row["ran"] is True
        assert row["load_bearing"] is True
        assert row["verdict"] == "unsat"
        assert row["erased_flip_verdict"] == "sat"
        assert row["asserted_precomputed_boolean"] is False
        assert row["bound_agreement_count"] == 16
        assert row["bound_violation_count"] == 32


def test_envelope_and_validator_result():
    payload = load_envelope()
    validator = json.loads(VALIDATOR_RESULT.read_text(encoding="utf-8"))
    assert validator["ok"] is True
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["sim_id"] == SIM_ID
    assert payload["all_pass"] is True
    assert payload["envelope_built_with_helper"] is True
    assert payload["build_helper_path"] == "scripts/build_three_engine_envelope.py"
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["ceiling"]["claim_ceiling"] == "axis_readout_candidate_only + consistency_row_only"
    assert payload["consistency_summary"]["agreement_fraction"] == 16 / 48
    assert payload["consistency_summary"]["nonneutral_agreement_fraction"] == 16 / 32
    assert payload["engines"]["julia"]["result_all_pass"] is True
    assert payload["engines"]["jax"]["result_all_pass"] is True
    assert payload["engines"]["pytorch"]["result_all_pass"] is True
