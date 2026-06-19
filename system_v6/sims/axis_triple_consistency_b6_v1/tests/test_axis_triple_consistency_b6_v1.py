#!/usr/bin/env python3
"""Tests for axis_triple_consistency_b6_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import axis_triple_consistency_b6_v1_common as common


def test_common_object_records_blocked_faithful_gate() -> None:
    obj = common.build_axis_triple_object()
    assert obj["all_pass"] is True
    assert obj["shared_carrier_decision"]["status"] == "blocked_open_no_faithful_axis3_on_33_cell_adapter"
    assert obj["carrier_faithfulness_audit"]["faithful_33_cell_placement_possible_from_current_sources"] is False


def test_proxy_consistency_table_can_fail() -> None:
    obj = common.build_axis_triple_object()
    summary = obj["consistency_summary"]
    assert summary["sample_total"] == 33
    assert summary["agreement_count"] == 16
    assert summary["violation_count"] == 17
    assert summary["nonneutral_total"] == 32
    assert summary["nonneutral_agreement_count"] == 15
    assert summary["relation_can_fail"] is True


def test_panel_and_v0_regression_controls() -> None:
    obj = common.build_axis_triple_object()
    assert len(obj["panel_anchor_checks"]) == 2
    assert all(row["computed_b6_sign"] == -1 for row in obj["panel_anchor_checks"])
    v0 = obj["v0_hopf_transplant_regression"]
    assert v0["matches_expected_v0_negative"] is True
    assert v0["total_agreement"] == 16
    assert v0["total_violations"] == 32
    assert v0["nonneutral_agreement"] == 16
    assert v0["nonneutral_total"] == 32


def test_envelope_if_present_matches_common() -> None:
    envelope = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
    if not envelope.exists():
        return
    payload = json.loads(envelope.read_text(encoding="utf-8"))
    obj = common.build_axis_triple_object()
    assert payload["shared_carrier_decision"] == obj["shared_carrier_decision"]
    assert payload["consistency_summary"] == obj["consistency_summary"]
    assert payload["sign_vector_sha256"] == obj["sign_vector_sha256"]


def test_no_builder_audit_verdict() -> None:
    assert not Path(common.SIM_DIR / "audit_verdict.md").exists()
