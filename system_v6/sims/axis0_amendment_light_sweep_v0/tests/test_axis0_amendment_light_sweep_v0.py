#!/usr/bin/env python3
"""Behavior tests for axis0_amendment_light_sweep_v0."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "axis0_amendment_light_sweep_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_DIR = SIM_DIR / "results"


def load_module():
    spec = importlib.util.spec_from_file_location(SIM_ID, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[SIM_ID] = module
    spec.loader.exec_module(module)
    return module


def test_candidate_space_is_amendment_bound():
    module = load_module()
    payload = module.build_result()
    assert sorted(payload["per_candidate_verdicts"]) == ["A0.CP.11", "A0.CP.12", "A0.CP.13", "A0.CP.14"]
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["build_gates"]["candidate_space_bound"] is True


def test_light_rows_have_vectors_alias_forms_boundary_and_owner_guard():
    module = load_module()
    payload = module.build_result()
    rows = {row["candidate"]: row for row in payload["candidate_verdict_table"]}
    for cid in ["A0.CP.11", "A0.CP.13", "A0.CP.14"]:
        row = rows[cid]
        assert row["vector_status"] == "computed_33_cell"
        assert len(row["sign_vector"]) == 33
        assert row["canonical_alias_form_sha256"]
        assert "reads_axis0_feedback_distinction" in row["distinction_boundary_check"]
        assert "tracks_type1_type2_chirality" in row["owner_chirality_guard"]
        assert len(row["cell_level_disagreement_table"]) == 33
    assert rows["A0.CP.12"]["verdict"] == "open + queued-heavy"
    assert rows["A0.CP.12"]["vector_status"] == "not_computed_heavy_adapter_required"


def test_controls_and_prior_regressions_fire():
    module = load_module()
    payload = module.build_result()
    controls = {row["id"]: row for row in payload["control_verdicts"]}
    assert controls["control.anchor_self"]["verdict"] == "alias"
    assert controls["control.deliberate_alias"]["verdict"] == "alias"
    assert controls["control.deliberate_chirality_tracker"]["verdict"] == "excluded-by-owner-type1-type2-chirality-guard"
    assert controls["control.deliberate_chirality_tracker"]["owner_chirality_guard"]["tracks_type1_type2_chirality"] is True
    assert all(row["still_excluded"] for row in payload["light_regression_verdicts"])


def test_fork_row_and_heavy_queue_are_explicit():
    module = load_module()
    payload = module.build_result()
    assert payload["fork_row"]["fork"] == "marginal_entropy_CP14_vs_correlation_family_anchor_CP0"
    assert payload["fork_row"]["outcome"] in {"disagrees", "aliases_anchor"}
    assert "A0.CP.12" in payload["queued_heavy"]
    assert "A0.CP.13" in payload["queued_heavy"]


def test_smt_binds_computed_counts_with_real_flip():
    module = load_module()
    payload = module.build_result()
    assert payload["crossover_proofs"]["z3"]["verdict"] == "unsat"
    assert payload["crossover_proofs"]["z3"]["flip_control_verdict"] == "sat"
    assert payload["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
    assert payload["crossover_proofs"]["cvc5"]["flip_control_verdict"] == "sat"


def test_envelope_and_validator_outputs_after_run():
    envelope_path = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
    validator_path = RESULT_DIR / f"{SIM_ID}_validator_results.json"
    if not envelope_path.exists() or not validator_path.exists():
        return
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    validator = json.loads(validator_path.read_text(encoding="utf-8"))
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["sim_id"] == SIM_ID
    assert envelope["envelope_built_with_helper"] is True
    assert validator["ok"] is True
