#!/usr/bin/env python3
"""Behavior tests for axis0_cosurvivor_heavy_v0."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "axis0_cosurvivor_heavy_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
COMMON_PATH = SIM_DIR / f"{SIM_ID}_common.py"
ENVELOPE = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"

EXPECTED_VERDICTS = {
    "A0.CP.11": "excluded-by-stability-class-mismatch",
    "A0.CP.14": "excluded-by-stability-class-mismatch",
}


def load_common():
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", COMMON_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_envelope() -> dict:
    assert ENVELOPE.exists()
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


def test_core_result_excludes_light_cosurvivors_at_heavy_stability():
    common = load_common()
    result = common.build_core_result()

    assert result["all_pass"] is True
    assert result["family_adjudication_sentence"] == "Axis-0 = the anchor alias class"
    assert {row["candidate"]: row["final_verdict"] for row in result["final_verdict_table"]} == EXPECTED_VERDICTS
    assert all(row["boundary_reads_axis0"] is True for row in result["final_verdict_table"])
    assert all(row["stability_matches_anchor"] is False for row in result["final_verdict_table"])


def test_envelope_contract_and_three_lanes():
    envelope = load_envelope()

    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert sorted(envelope["engines"]) == ["jax", "julia", "pytorch"]
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["build_gates"]["three_engine_final_tables_match"] is True


def test_heavy_rows_have_full_teeth():
    envelope = load_envelope()
    rows = envelope["candidate_verdict_table"]

    assert len(rows) == 2
    for row in rows:
        assert len(row["sign_vector"]) == 33
        assert len(row["cell_level_disagreement_table"]) == 33
        assert row["matches_accepted_light_vector_hash"] is True
        assert row["distinction_boundary_check"]["reads_axis0_feedback_distinction"] is True
        assert row["stability_class_comparison"]["matches_anchor_profile"] is False
        assert "depth_2_all_ordered_sequences" in row["multi_step_stability_extension"]["anchor_multi_step_stability_profile"]["depths"]
        assert "depth_3_all_ordered_sequences" in row["multi_step_stability_extension"]["anchor_multi_step_stability_profile"]["depths"]


def test_controls_and_proofs():
    envelope = load_envelope()
    controls = {row.get("id"): row.get("verdict") for row in envelope["control_verdicts"]}
    proofs = envelope["crossover_proofs"]

    assert controls["control.anchor_self"] == "alias-of-anchor"
    assert controls["control.deliberate_alias"] == "alias-of-anchor"
    assert all(row.get("still_excluded") is True for row in envelope["control_verdicts"] if row.get("candidate"))
    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["julia_z3"]["verdict"] == "unsat"
    assert proofs["z3"]["flip_control_verdict"] == "sat"
    assert proofs["cvc5"]["flip_control_verdict"] == "sat"
    assert proofs["julia_z3"]["flip_control_verdict"] == "sat"
