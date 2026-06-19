#!/usr/bin/env python3
"""Boundary checks for topology_parity_cell_model_v1."""

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
REQUIRED_CEILING = "scratch_diagnostic_independent_topology_guard_for_fiber_augmented_cover_v1_only"
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "checks post-audit-idempotent builder/audit boundary flags"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves packet and helper paths for boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "load_bearing",
    "pathlib": "supportive",
}


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification must stay scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if payload.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed must be false")
    if payload.get("claim_ceiling") != REQUIRED_CEILING:
        errors.append("claim_ceiling mismatch")
    if payload.get("no_builder_audit_verdict") is not True:
        errors.append("no_builder_audit_verdict must be true")
    if payload.get("no_builder_audit_verdict_envelope_gate") is not True:
        errors.append("no_builder_audit_verdict_envelope_gate must be true")
    if payload.get("preregistration_order") != "cell_rules_and_expected_profiles_declared_before_computation":
        errors.append("cell rules and expected profiles must be preregistered before computation")

    rules = payload.get("cell_rules_pinned_before_computation", {})
    if rules.get("no_target_betti_fitting") is not True:
        errors.append("cell rules must explicitly reject target-Betti fitting")
    if "33 base faces" not in str(rules.get("base_rule", "")):
        errors.append("base cell rule must preserve the 33-face committed surface")
    if "seam" not in str(rules.get("gluing_rule", "")):
        errors.append("gluing rule must be seam/transition based")

    expected = payload.get("expected_profiles_preregistered_from_math", {})
    if expected.get("v1_degree_one_cover", {}).get("expected_betti_b0_b1_b2_b3") != [1, 0, 0, 1]:
        errors.append("v1 ideal expected Betti profile mismatch")
    if expected.get("zero_shift_product_cover", {}).get("expected_betti_b0_b1_b2_b3") != [1, 1, 1, 1]:
        errors.append("product ideal expected Betti profile mismatch")

    gate = payload.get("reference_gate", {})
    if gate.get("reference_gate_passed") is not True:
        errors.append("reference gate must pass before cover rows are accepted")
    if gate.get("explicit_s3", {}).get("betti_b0_b1_b2_b3") != [1, 0, 0, 1]:
        errors.append("explicit S3 reference profile mismatch")
    if gate.get("explicit_s2xs1", {}).get("betti_b0_b1_b2_b3") != [1, 1, 1, 1]:
        errors.append("explicit S2xS1 reference profile mismatch")

    cover_inputs = payload.get("cover_inputs", {})
    v1 = cover_inputs.get("v1", {})
    product = cover_inputs.get("zero_shift_product", {})
    if v1.get("fiber_phase_count") != 3:
        errors.append("v1 cover input must pin |F|=3")
    if v1.get("seam_lifted_shift_steps") != [1, 1, 1, 0]:
        errors.append("v1 seam shifts must be the committed degree-one shifts")
    if v1.get("degree") != 1:
        errors.append("v1 degree must be extracted as 1 from source transitions")
    if product.get("degree") != 0:
        errors.append("zero-shift product degree must be 0")

    controls = payload.get("controls", {})
    if controls.get("all_reference_controls_pass") is not True:
        errors.append("v0 reference controls must pass")
    if controls.get("mislabeled_torus_as_sphere_negative", {}).get("pass") is not True:
        errors.append("mislabeled-complex negative must pass")
    if controls.get("wrong_gluing_erased_v1_seam", {}).get("pass") is not True:
        errors.append("wrong-gluing control must move the Betti profile")
    torsion = controls.get("torsion_trap_degree_2", {})
    if torsion.get("homology_torsion", {}).get("H1") != [2] or torsion.get("betti_only_underpowered") is not True:
        errors.append("degree-2 torsion trap must expose Betti-only underpowering")

    complexes = payload.get("complexes", {})
    v1_complex = complexes.get("v1_degree_one_cover", {})
    product_complex = complexes.get("zero_shift_product_cover", {})
    if v1_complex.get("betti_b0_b1_b2_b3") != [1, 0, 0, 1]:
        errors.append("v1 cover Betti profile mismatch")
    if product_complex.get("betti_b0_b1_b2_b3") != [1, 1, 1, 1]:
        errors.append("product cover Betti profile mismatch")
    for key, row in complexes.items():
        if row.get("d_squared_zero") is not True:
            errors.append(f"{key} chain complex has d^2 != 0")
        if row.get("metadata", {}).get("base_face_count") != 33:
            errors.append(f"{key} missing 33-face metadata")

    parity = payload.get("parity_adjudication", {})
    if parity.get("guard_status") not in {"distinction_resolved_degree_one_side", "machinery_insufficient", "still_insufficient"}:
        errors.append("invalid parity guard status")
    if parity.get("guard_status") == "distinction_resolved_degree_one_side" and parity.get("independent_guard_earned") is not True:
        errors.append("resolved distinction must mark independent guard earned")

    forbidden_claims = {"new bundle claim", "formal admission", "canonical by process", "axis-level closure", "bridge claim", "physics/manifold claim"}
    if not forbidden_claims <= set(payload.get("disallowed_claims", [])):
        errors.append("disallowed_claims missing standard blockers")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
