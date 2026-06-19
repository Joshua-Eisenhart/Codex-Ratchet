#!/usr/bin/env python3
"""Boundary checks for ecd04_record_conditioned_navigation_v0."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


classification = "scratch_diagnostic"
claim_ceiling = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == classification, "classification must stay scratch_diagnostic")
    require(errors, payload.get("claim_ceiling") == claim_ceiling, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")

    gates = payload.get("witness_gates", {})
    require(errors, gates.get("basin_nontriviality", {}).get("status") == "pass", "basin nontriviality gate failed")
    parity = gates.get("information_parity", {})
    require(errors, parity.get("status") == "pass", "information parity gate failed")
    require(errors, parity.get("computed_before_discriminator") is True, "information parity must run before discriminator")
    require(errors, parity.get("qit_environment_hash") == parity.get("baseline_environment_hash"), "environment hash mismatch")
    require(errors, parity.get("qit_access_manifest") == parity.get("baseline_access_manifest"), "access manifest mismatch")

    metric = payload.get("metric_pin", {})
    require(errors, metric.get("primary_success_gate") == 1.0, "metric must require target success first")
    require(errors, metric.get("penalizes_trivially_injective_readouts") is True, "fair metric gate missing")
    require(errors, metric.get("does_not_reward_failure") is True, "metric failure guard missing")

    controls = payload.get("controls", {})
    require(errors, controls.get("record_erasure_regression", {}).get("degraded") is True, "record erasure did not degrade")
    require(errors, controls.get("scrambled_records", {}).get("degraded") is True, "scrambled records did not degrade")
    require(errors, controls.get("order_blind_collapse", {}).get("primary_eligible") is False, "order-blind collapse stayed eligible")
    require(errors, controls.get("no_identity_leak", {}).get("status") == "pass", "no identity leak failed")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {
        "QIT-engine admission",
        "basin theorem",
        "thermodynamic heat/work/bath claim",
        "physical Landauer engine",
        "axis/manifold/physics claim",
        "formal admission",
    }:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
