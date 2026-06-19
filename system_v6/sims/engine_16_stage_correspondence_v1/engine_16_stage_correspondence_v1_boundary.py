#!/usr/bin/env python3
"""Boundary checks for engine_16_stage_correspondence_v1."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "hypothesis_test_only"
EXPECTED_GCM_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("claim_ceiling") == CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(
        errors,
        payload.get("no_builder_audit_verdict_envelope_gate") is True,
        "no_builder_audit_verdict_envelope_gate must be true",
    )

    gates = payload.get("builder_gates", {})
    require(errors, gates.get("G_2a_idempotency_from_birth") is True, "G.2a gate missing")
    require(errors, gates.get("file_disjoint_packet") is True, "file-disjoint boundary missing")
    require(errors, gates.get("definitions_pinned_before_correspondence") is True, "definition pin missing")
    require(errors, gates.get("substrate_first_gcm_lineage") is True, "GCM lineage gate missing")
    require(errors, gates.get("no_stage_admission") is True, "stage-admission fence missing")

    lineage = payload.get("gcm_lineage", {})
    require(errors, isinstance(lineage, dict), "gcm_lineage must be an object")
    if isinstance(lineage, dict):
        require(errors, lineage.get("gcm_object_id") == EXPECTED_GCM_OBJECT_ID, "wrong GCM object id")
    substrate = gcm_substrate_check(payload)
    require(errors, substrate.get("ok") is True, f"GCM substrate check failed: {substrate.get('errors')}")

    negative = payload.get("lineage_free_negative_control", {})
    require(errors, negative.get("ok") is False, "lineage-free negative must fail red")
    require(errors, bool(negative.get("errors")), "lineage-free negative must carry helper errors")

    corr = payload.get("correspondence", {})
    require(errors, corr.get("verdict") in {"full_bijection", "partial", "0-match_again"}, "bad correspondence verdict")
    require(errors, len(corr.get("match_matrix_16x16", [])) == 16, "match matrix row count mismatch")
    require(errors, all(len(row) == 16 for row in corr.get("match_matrix_16x16", [])), "match matrix col count mismatch")

    controls = payload.get("controls", {})
    require(errors, controls.get("order_erasure", {}).get("collapsed_toward_8") is True, "order-erasure control failed")
    scramble = controls.get("pairing_scramble", {})
    require(
        errors,
        scramble.get("wrong_pairing_scores_worse") is True or scramble.get("pairing_convention_doing_nothing") is True,
        "pairing-scramble control must be worse or explicitly non-informative",
    )
    require(
        errors,
        controls.get("label_permutation_invariance", {}).get("fingerprint_ids_unchanged") is True,
        "label-permutation invariance failed",
    )
    require(
        errors,
        controls.get("commuting_pair_honest_null_rule", {}).get("reported_all_commuting_pairs") is True,
        "commuting-pair honest-null reporting failed",
    )

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in (
        "stage admission",
        "Matrix64 admission",
        "QIT-engine admission",
        "axis admission",
        "bridge admission",
        "manifold admission",
        "physics claim",
        "target-system claim",
    ):
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
