#!/usr/bin/env python3
"""Boundary checks for the ECD.06 v1 regime-repair packet."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402

import ecd06_prediction_first_inference_v1_common as common  # noqa: E402


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "enforces G.2a post-audit-idempotent boundary"},
    "regime_validity_gate": {"tried": True, "used": True, "reason": "blocks discriminator rows if the transition table is learnable"},
}
TOOL_INTEGRATION_DEPTH = {"builder_audit_boundary": "load_bearing", "regime_validity_gate": "load_bearing"}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == "scratch_diagnostic", "claim_ceiling mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict helper gate must be true")

    gate = payload.get("regime_validity_gate", {})
    require(errors, gate.get("gate_name") == "G7_partial_observability_transition_table_not_exactly_learnable", "missing G7 regime gate")
    require(errors, gate.get("status") == common.REGIME_PASS_STATUS, "regime gate must pass before discriminator rows")
    require(errors, gate.get("computably_not_exactly_learnable") is True, "transition table must be computably not exact")
    require(errors, 0.0 < float(gate.get("transition_table_fill_fraction", 0.0)) < 1.0, "table fill fraction must be strictly partial")
    require(errors, float(gate.get("eval_pair_coverage_fraction", 1.0)) < 1.0, "heldout eval pairs must not all be table-covered")

    require(errors, payload.get("discriminator_refused") is False, "accepted payload must not refuse discriminator rows")
    require(errors, payload.get("status") == "discriminator_rows_admitted_after_regime_gate", "status mismatch")

    baseline = payload.get("baseline_side", {})
    require(errors, baseline.get("v0_killer_included") is True, "v0 killer transition table baseline must be included")
    policies = {row.get("policy_id") for row in baseline.get("candidates", [])}
    for policy in {
        "persistence_source_state",
        "global_empirical_one_step_mean",
        "per_state_conditional_table_train_budget",
        "source_generator_transition_table_v0_killer_included_train_budget",
    }:
        require(errors, policy in policies, f"missing widened baseline policy: {policy}")
    require(errors, any(str(policy).startswith("searched_policy_class") for policy in policies), "missing searched policy class")

    controls = payload.get("controls", {})
    full = controls.get("v0_regression_full_observability", {})
    require(errors, full.get("passes") is True, "full-observability v0 regression must pass")
    require(errors, full.get("transition_table_adjusted_error") == 0.0, "full-observability table must be exact")
    require(errors, controls.get("no_identity_leak", {}).get("status") == "pass", "no identity leak control failed")
    require(errors, controls.get("scrambled_error_regression", {}).get("margin_moved") is True, "scrambled control must move margin")
    require(
        errors,
        set(controls.get("dropped_half_data_budget_sensitivity_both_sides", {}))
        == {"first_half_train_second_half_eval", "second_half_train_first_half_eval"},
        "dropped-half sensitivity rows missing",
    )

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {"holodeck admission", "FEP admission", "physics admission", "formal admission", "canonical by process"}:
        require(errors, claim in disallowed, f"disallowed_claims missing {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
