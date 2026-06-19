#!/usr/bin/env python3
"""Boundary checks for topology_parity_guard_v2."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
REQUIRED_CEILING = "scratch_diagnostic_consumer_guard_only_no_new_construction"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == REQUIRED_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    require(errors, payload.get("builder_gates", {}).get("no_new_cells_introduced") is True, "new-cell introduction must be forbidden")
    require(errors, payload.get("builder_gates", {}).get("consumer_only") is True, "packet must stay consumer-only")

    source = payload.get("source_complex_lock", {})
    require(errors, source.get("builder_result_commit") == "cc2f61b2a", "builder commit pin mismatch")
    require(errors, source.get("builder_betti_computed") is False, "builder Betti citation boundary failed")
    require(errors, source.get("hash_verification_passed") is True, "committed hash verification failed")
    require(errors, source.get("consumer_boundary", {}).get("builder_consumer_separation") is True, "consumer boundary missing")

    refs = payload.get("reference_gate", {})
    require(errors, refs.get("reference_gate_passed") is True, "reference gate must pass first")
    require(
        errors,
        refs.get("explicit_s3_like", {}).get("homology", {}).get("betti_b0_b1_b2_b3") == [1, 0, 0, 1],
        "S3-like reference profile mismatch",
    )
    require(
        errors,
        refs.get("explicit_s2xs1", {}).get("homology", {}).get("betti_b0_b1_b2_b3") == [1, 1, 1, 1],
        "S2xS1 reference profile mismatch",
    )

    total = payload.get("complexes", {}).get("committed_v2_total_space", {})
    require(errors, total.get("d_squared_zero") is True, "total-space d^2 must be zero")
    require(errors, "homology" in total, "total-space homology missing")
    zero_shift = payload.get("complexes", {}).get("zero_shift_product_cover", {})
    require(errors, zero_shift.get("status") == "INSUFFICIENT", "zero-shift committed-chain gap must be explicit")

    controls = payload.get("controls", {})
    require(errors, controls.get("torsion_trap_degree_2", {}).get("pass") is True, "torsion trap must pass")
    require(errors, controls.get("wrong_gluing_control", {}).get("status") == "INSUFFICIENT", "wrong-gluing gap must be explicit")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {"new construction", "new cell introduction", "formal admission", "canonical by process", "builder Betti citation"}:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
