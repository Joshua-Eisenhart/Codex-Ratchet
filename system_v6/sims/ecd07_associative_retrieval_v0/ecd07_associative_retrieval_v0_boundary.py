#!/usr/bin/env python3
"""Boundary checks for the ECD.07 associative retrieval packet."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402

import ecd07_associative_retrieval_v0_common as common  # noqa: E402


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict gate must be true")

    storage = payload.get("storage_nontriviality_gate", {})
    require(errors, storage.get("status") == "passed", "storage nontriviality gate failed")
    require(errors, storage.get("qit_accuracy", 0.0) > storage.get("chance_floor", 1.0), "QIT storage not above chance")
    require(errors, storage.get("classical_accuracy", 0.0) > storage.get("chance_floor", 1.0), "classical storage not above chance")

    parity = payload.get("information_parity_gate", {})
    require(errors, parity.get("status") == "information_parity_passed", "information parity gate failed")
    require(errors, parity.get("computed_before_discriminator_rows") is True, "information parity must be row-first")
    require(errors, parity.get("parity_passed") is True, "information parity not passed")
    require(errors, parity.get("qit_side", {}).get("prediction_inputs") == parity.get("baseline_side", {}).get("prediction_inputs"), "prediction input parity mismatch")
    require(errors, parity.get("asymmetric_access") == {"training": [], "prediction": [], "evaluation_only": [], "forbidden_touched": []}, "asymmetric access detected")

    metric = payload.get("metric_pin", {})
    require(errors, metric.get("retrieval_accuracy_curve") == [str(level) for level in common.CORRUPTION_LEVELS], "full corruption curve not pinned")
    require(errors, metric.get("capacity_threshold") == common.CAPACITY_THRESHOLD, "capacity threshold drift")

    discriminator = payload.get("discriminator", {})
    require(errors, discriminator.get("either_outcome_valid") is True, "either-outcome contract missing")
    require(errors, discriminator.get("verdict") in {"SURVIVES_v0", "DIES_TIE_v0", "DIES_CLASSICAL_STRONGER_v0"}, "bad discriminator verdict")
    require(errors, discriminator.get("qit_best", {}).get("full_curve") is True, "QIT best row must carry full curve")
    require(errors, discriminator.get("classical_best", {}).get("full_curve") is True, "classical best row must carry full curve")
    require(errors, discriminator.get("qit_candidates"), "QIT side must be searched")
    require(errors, discriminator.get("classical_candidates"), "classical side must be searched")

    controls = payload.get("controls", {})
    leak = controls.get("no_identity_leak", {})
    require(errors, leak.get("status") == "pass", "no-identity-leak control failed")
    require(errors, "identity_leak_detected" in leak, "identity_leak_detected missing")
    require(errors, "identity_leak_excluded_best_accuracy" in leak, "identity_leak_excluded_best_accuracy missing")
    require(errors, bool(leak.get("identity_leak_exclusion_rule")), "identity leak exclusion rule missing")
    require(errors, controls.get("dropped_half_both_sides", {}).get("both_sides_run") is True, "dropped-half control missing both sides")
    require(errors, "spurious_attractor_recurrence" in controls, "spurious-attractor recurrence control missing")
    require(errors, controls.get("scrambled_pattern_regression", {}).get("margin_moved") is True, "scrambled-pattern regression did not move")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {"global quantum-Hopfield theorem", "canonical by process", "formal admission", "physics admission"}:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
