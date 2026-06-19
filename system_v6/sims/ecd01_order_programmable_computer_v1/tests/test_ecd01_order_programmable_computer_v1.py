#!/usr/bin/env python3
"""Pytest checks for the repaired ECD.01 Szilard baseline enumeration."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def _common():
    return importlib.import_module("ecd01_order_programmable_computer_v1_common")


def test_strongest_form_szilard_baseline_is_computed_table_not_constant() -> None:
    common = _common()
    obj = common.build_order_programmability_object()

    baseline = obj["szilard_baseline"]
    assert baseline["enumeration_policy"]["policy_id"] == "plain_szilard_strongest_form_same_carrier_v1"
    assert baseline["candidate_permutation_count"] == 24
    assert baseline["admissible_order_count"] == 4
    assert baseline["distinct_channel_count"] == baseline["computed_distinct_channel_count"]
    assert baseline["hardcoded_distinct_count"] is None
    assert len(baseline["channel_table"]) == baseline["admissible_order_count"]
    assert {row["channel_word"] for row in baseline["channel_table"]} == {"UEUE", "EUUE", "EUEU"}

    metric = obj["capability_metric"]
    assert metric["qit_distinct_channel_count"] == 3
    assert metric["szilard_max_distinct_channel_count"] == 2
    assert metric["qit_minus_szilard_margin"] == 1
    assert metric["qit_diversity_strictly_exceeds_szilard"] is True


def test_positive_predicate_can_admit_baseline_and_no_identity_leak() -> None:
    common = _common()
    obj = common.build_order_programmability_object()

    predicate = obj["szilard_baseline"]["positive_predicate"]
    assert predicate["predicate_id"] == "baseline_can_win_if_distinct_gte_qit"
    assert predicate["can_admit_stronger_baseline"] is True
    assert predicate["would_admit_if_szilard_distinct_count"] == 3
    assert predicate["actual_admitted"] is False
    synthetic = obj["szilard_baseline"]["synthetic_stronger_baseline_control"]
    assert synthetic["actual_admitted"] is True
    assert synthetic["ecd01_would_die"] is True

    no_leak = obj["controls"]["no_identity_leak_between_schedule_labels_and_fingerprints"]
    assert no_leak["status"] == "pass"
    assert no_leak["fingerprint_payload_excludes_schedule_label"] is True
    assert no_leak["renamed_schedule_fingerprints_match"] is True
    assert no_leak["label_only_fingerprint_collision_count"] == 0


def test_weakened_enumeration_control_reports_sensitivity() -> None:
    common = _common()
    obj = common.build_order_programmability_object()

    control = obj["controls"]["weakened_enumeration_drop_half"]
    assert control["status"] == "sensitive"
    assert control["dropped_schedule_count"] == 2
    assert control["full_distinct_channel_count"] == 2
    assert control["weakened_distinct_channel_count"] == 1
    assert control["positive_predicate_input_changed"] is True


def test_generated_result_validator_and_boundaries() -> None:
    common = _common()
    result_path = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
    if not result_path.exists():
        return
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["no_builder_audit_verdict"] is True
    assert builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    assert payload["builder_gates"]["boundary_helper_fully_used"] is True
    assert payload["source_import_audit"]["authority"]["v0_audit_verdict"]["commit_hint"] == "6e73efa2f"
    assert "universal quantum computer" in payload["disallowed_claims"]
    assert payload["TOOL_MANIFEST"]["szilard_schedule_enumerator"]["reason"]
