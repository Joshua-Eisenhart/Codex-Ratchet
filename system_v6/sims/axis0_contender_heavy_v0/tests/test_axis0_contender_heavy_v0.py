#!/usr/bin/env python3
"""Behavior tests for axis0_contender_heavy_v0."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "axis0_contender_heavy_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
COMMON_PATH = SIM_DIR / f"{SIM_ID}_common.py"
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

EXPECTED_VERDICTS = {
    "A0.CP.3_entropy_gradient_sign": "excluded-by-stability-class-mismatch",
    "A0.CP.4_pauli_participation_feedback_polarity": "excluded-by-stability-class-mismatch",
    "A0.CP.5_flux_direction_annular_or_edge_current": "excluded-by-distinction-boundary",
    "A0.CP.6_flux_continuity_n3_n4_current_sign": "excluded-by-distinction-boundary",
    "A0.CP.7_lyapunov_descent_direction": "excluded-by-functional-teeth-wrong-distinction",
    "A0.CP.8_hopfield_energy_gradient_sign": "excluded-by-retrieval-teeth-wrong-distinction",
    "A0.CP.9_holonomy_spectrum_sign": "excluded-by-holonomy-axis3-axis6-boundary",
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


def test_core_result_adjudicates_anchor_alias_class():
    common = load_common()
    result = common.build_core_result()

    assert result["all_pass"] is True
    assert result["family_adjudication_sentence"] == "Axis-0 = the anchor alias class"
    assert {row["candidate"]: row["final_verdict"] for row in result["final_verdict_table"]} == EXPECTED_VERDICTS
    assert all(row["co_survivor"] is False for row in result["final_verdict_table"])


def test_envelope_keeps_three_engine_and_boundary_contract():
    envelope = load_envelope()

    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["sim_id"] == SIM_ID
    assert sorted(envelope["engines"]) == ["jax", "julia", "pytorch"]
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["boundary"]["no_builder_audit_verdict"] is True
    assert envelope["boundary"]["packet_audit_verdict_absent"] is True


def test_heavy_rows_have_vectors_teeth_and_witnesses():
    envelope = load_envelope()
    rows = envelope["candidate_verdict_table"]

    assert len(rows) == 7
    for row in rows:
        assert len(row["sign_vector"]) == 33
        assert row["adapter_status"] == "computed_source_backed_33_cell_variants"
        assert row["teeth_run"] is True
        assert row["variant_count"] >= 1
        assert row["witness"]["row"]
        assert "stability_class_comparison" in row
        assert "distinction_boundary_check" in row
        assert row["candidate_vector"]


def test_controls_and_light_regressions_fire():
    envelope = load_envelope()
    controls = {row["id"]: row["verdict"] for row in envelope["control_verdicts"]}
    light = {row["candidate"]: row["verdict"] for row in envelope["light_regression_verdicts"]}

    assert controls["control.anchor_self"] == "alias-of-anchor"
    assert controls["control.deliberate_alias"] == "alias-of-anchor"
    assert controls["control.constant_readout_erased"].startswith("excluded-by")
    assert controls["control.zero_readout_erased"].startswith("excluded-by")
    assert controls["control.degree_only_baseline"] == "excluded-by-degree-teeth-wrong-distinction"
    assert light["A0.CP.1_unweighted_edge_gradient_count_balance"].startswith("excluded-by")
    assert light["A0.CP.2_incoming_vs_outgoing_gradient_current"].startswith("excluded-by")
    assert light["A0.CP.10_transition_graph_in_out_degree_imbalance"].startswith("excluded-by")


def test_smt_and_strict_tool_surface_are_recorded():
    envelope = load_envelope()
    proofs = envelope["crossover_proofs"]

    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["julia_z3"]["verdict"] == "unsat"
    assert proofs["z3"]["flip_control_verdict"] == "sat"
    assert proofs["cvc5"]["flip_control_verdict"] == "sat"
    assert proofs["julia_z3"]["flip_control_verdict"] == "sat"
    assert "tool_intent" in envelope
    assert envelope["TOOL_INTEGRATION_DEPTH"]["torch_geometric"] == "load_bearing"
