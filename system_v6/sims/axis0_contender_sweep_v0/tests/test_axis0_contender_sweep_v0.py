#!/usr/bin/env python3
"""Behavior tests for axis0_contender_sweep_v0."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "axis0_contender_sweep_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_DIR = SIM_DIR / "results"


def load_module():
    spec = importlib.util.spec_from_file_location(SIM_ID, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_registry_bound_candidate_space_and_light_heavy_boundary():
    module = load_module()
    payload = module.build_result()

    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["registry_binding"]["read_in_full"] is True
    assert payload["counts"]["registered_candidate_count"] == 11
    assert payload["counts"]["light_symbolic_registered_count"] == 4
    assert payload["counts"]["heavy_queued_count"] == 7
    assert payload["counts"]["extra_candidates_added_after_results"] == 0
    assert payload["phase_boundary"]["no_teeth_before_alias_pair_table"] is True


def test_light_rows_get_exact_vectors_alias_forms_and_witnesses():
    module = load_module()
    payload = module.build_result()
    verdicts = {row["candidate"]: row for row in payload["candidate_verdict_table"]}

    assert verdicts["A0.CP.0_committed_signed_outgoing_gradient_flux"]["verdict"] == "alias-of-anchor"
    assert verdicts["A0.CP.1_unweighted_edge_gradient_count_balance"]["verdict"].startswith("excluded-by-")
    assert verdicts["A0.CP.2_incoming_vs_outgoing_gradient_current"]["verdict"].startswith("excluded-by-")
    assert verdicts["A0.CP.10_transition_graph_in_out_degree_imbalance"]["classification"] == "wrong_distinction"
    assert verdicts["A0.CP.10_transition_graph_in_out_degree_imbalance"]["verdict"].startswith("excluded-by-")

    for cid in [
        "A0.CP.0_committed_signed_outgoing_gradient_flux",
        "A0.CP.1_unweighted_edge_gradient_count_balance",
        "A0.CP.2_incoming_vs_outgoing_gradient_current",
        "A0.CP.10_transition_graph_in_out_degree_imbalance",
    ]:
        row = verdicts[cid]
        assert row["vector_status"] == "computed"
        assert len(row["sign_vector"]) == 33
        assert row["canonical_alias_form_sha256"]
        assert row["witness"]["row"]


def test_heavy_candidates_stay_open_and_queued_without_adapter():
    module = load_module()
    payload = module.build_result()
    verdicts = {row["candidate"]: row for row in payload["candidate_verdict_table"]}
    heavy_ids = [cid for cid in verdicts if cid.startswith("A0.CP.") and cid.split(".")[2].split("_")[0] in {str(i) for i in range(3, 10)}]

    assert len(heavy_ids) == 7
    for cid in heavy_ids:
        row = verdicts[cid]
        assert row["verdict"] == "co-survivor-open"
        assert row["queued_heavy"] is True
        assert row["vector_status"] == "not_computed_adapter_required"
        assert row["teeth_run"] is False


def test_controls_and_independence_note_are_bounded():
    module = load_module()
    payload = module.build_result()
    controls = {row["id"]: row for row in payload["control_verdicts"]}

    assert controls["control.anchor_self"]["verdict"] == "alias-of-anchor"
    assert controls["control.sign_flipped_monotone_reparameterized_anchor"]["verdict"] == "alias-of-anchor"
    assert controls["control.axis6_style_order_readout"]["verdict"] == "not-axis0-contender-by-distinction-boundary"
    assert payload["independence_note"]["co_survivor_independent_flags"] == []
    assert payload["independence_note"]["not_run_heavy_rows_open_queued"] is True


def test_smt_binds_computed_table_with_flip_controls():
    module = load_module()
    payload = module.build_result()
    proofs = payload["crossover_proofs"]

    assert proofs["z3"]["ran"] is True
    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["z3"]["flip_control_verdict"] == "sat"
    assert proofs["cvc5"]["ran"] is True
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["cvc5"]["flip_control_verdict"] == "sat"


def test_envelope_and_packet_validator_results_after_run():
    envelope_path = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
    validator_path = RESULT_DIR / f"{SIM_ID}_validator_results.json"
    if not envelope_path.exists() or not validator_path.exists():
        return

    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    validator = json.loads(validator_path.read_text(encoding="utf-8"))
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["sim_id"] == SIM_ID
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["envelope_built_with_helper"] is True
    assert envelope["build_helper_path"] == "scripts/build_three_engine_envelope.py"
    assert validator["ok"] is True
