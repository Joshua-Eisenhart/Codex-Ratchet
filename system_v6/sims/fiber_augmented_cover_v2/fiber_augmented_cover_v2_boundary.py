#!/usr/bin/env python3
"""Boundary checks for fiber_augmented_cover_v2."""

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
REQUIRED_CEILING = "axis_readout_candidate_only + cellular_cover_law_test_v2_no_admission"
VALID_LAW_STATUS = {
    "holds_on_cellular_nontrivial_cover",
    "fails_on_cellular_nontrivial_cover",
    "inconclusive_no_nonneutral_rows",
}
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "checks post-audit-idempotent G.2a boundary flags"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves packet and helper paths for boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "supportive",
    "pathlib": "supportive",
}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == REQUIRED_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("betti_computed") is False, "builder packet must not compute Betti")
    require(errors, "betti" not in payload, "builder packet must not emit top-level betti")

    base = payload.get("cellular_base", {})
    require(errors, base.get("construction_status") == "committed_cellular_sphere_mesh", "cellular base construction status mismatch")
    require(errors, base.get("cell_counts") == {"C0": 33, "C1": 92, "C2": 61}, "cellular base counts mismatch")
    require(errors, base.get("euler_characteristic") == 2, "cellular base chi must be 2")
    require(errors, base.get("euler_gate_passed") is True, "cellular base Euler gate failed")
    require(errors, base.get("edge_incidence_counts") == {"2": 92}, "cellular edge incidence must be two-sided")
    require(errors, base.get("all_face_transition_sums_close_mod_fiber") is True, "face cocycle closure failed")
    require(errors, base.get("v1_dense_graph_relation", {}).get("objects_have_different_roles") is True, "v1 dense graph fence missing")

    witness = payload.get("bundle_witness", {})
    require(errors, witness.get("directed_winding") in {-1, 1}, "winding witness must be +/-1")
    require(errors, witness.get("directed_winding") == 1, "v2 pinned clutching witness must be +1")
    require(errors, witness.get("nontrivial_gate_passed") is True, "nontrivial witness gate must pass")
    require(errors, witness.get("total_lifted_phase_shift_steps") == 3, "lifted seam shift total mismatch")

    total = payload.get("total_space_cellular_structure", {})
    require(errors, total.get("cell_counts") == {"C0": 99, "C1": 375, "C2": 459, "C3": 183}, "total-space cellular counts mismatch")
    require(errors, total.get("euler_characteristic") == 0, "total-space Euler characteristic mismatch")
    require(errors, total.get("chain_checks", {}).get("d_squared_zero") is True, "total-space d^2 check failed")
    for surface_name, surface in (("base", base), ("total", total)):
        for matrix_name, matrix in surface.get("boundary_matrices", {}).items():
            require(errors, matrix.get("format") == "sparse_coo", f"{surface_name} {matrix_name} must use sparse_coo")
            require(errors, bool(matrix.get("sha256")), f"{surface_name} {matrix_name} missing sha256")

    law = payload.get("b6_law_test", {})
    require(errors, law.get("table_kind") == "faithful_cellular_nontrivial_fiber_augmented_cover_table", "wrong law table kind")
    require(errors, law.get("witness_gate_required") is True, "law table must require witness gate")
    require(errors, law.get("witness_gate_passed") is True, "law table witness gate failed")
    require(errors, law.get("sample_total") == 99, "law table must have 99 cover states")
    require(errors, law.get("law_test_status") in VALID_LAW_STATUS, "invalid v2 law status")
    require(errors, law.get("relation_not_used_to_assign_axis3") is True, "Axis3 must not be assigned from b6 relation")
    require(errors, len(payload.get("sign_variant_table", [])) == 8, "full 8-variant table is required")

    faith = payload.get("faithfulness", {})
    require(errors, faith.get("axis0", {}).get("projects_to_committed_axis0") is True, "Axis0 pullback faithfulness failed")
    require(errors, faith.get("axis3", {}).get("source_backed_equivalent_adapter") is True, "Axis3 source-backed adapter missing")
    require(errors, faith.get("axis3", {}).get("predicate_mismatch_count") == 0, "Axis3 predicate mismatch count must be zero")
    require(errors, faith.get("axis6", {}).get("projects_to_committed_axis6") is True, "Axis6 pullback faithfulness failed")

    controls = payload.get("controls", {})
    trivial = controls.get("zero_shift_v2_cover_regression", {})
    require(errors, trivial.get("bundle_witness", {}).get("directed_winding") == 0, "zero-shift regression must have winding 0")
    require(errors, trivial.get("law_table_ran") is False, "zero-shift regression must refuse law rows")
    require(errors, controls.get("scrambled_control", {}).get("ran") is True, "scrambled control must run")
    require(errors, controls.get("convention_flip_control", {}).get("ran") is True, "convention-flip control must run")
    require(errors, controls.get("v1_comparison_row", {}).get("agreement_count") == 46, "v1 comparison row missing or drifted")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {
        "Betti computation",
        "homology certificate",
        "formal admission",
        "canonical by process",
        "physics/manifold claim",
        "global disproof of b6 law",
    }:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
