#!/usr/bin/env python3
"""Boundary checks for fiber_cover_incidence_structure_v0."""

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
REQUIRED_CEILING = "scratch_diagnostic_committed_incidence_structure_plumbing_only_no_betti"
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "checks post-audit-idempotent G.2a boundary flags"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves packet and helper paths for boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "supportive",
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
    if payload.get("betti_computed") is not False:
        errors.append("packet must not compute Betti")
    if "betti" in payload:
        errors.append("packet must not emit a top-level betti field")

    derivation = payload.get("derivation_honesty", {})
    if derivation.get("derivation_introduced_count") != 0:
        errors.append("derivation_introduced_count must be 0")
    if derivation.get("base_2_cell_count", 0) <= 0:
        errors.append("no source-derived 2-cells emitted")
    if derivation.get("exhaustive_as_base_s2_cell_structure") is not False:
        errors.append("packet must not claim exhaustive S2 incidence")
    for row in derivation.get("face_derivation_table", []):
        if row.get("introduced") is not False:
            errors.append(f"face {row.get('face_id')} is marked introduced")
        if len(row.get("source_edge_ids", [])) != 4:
            errors.append(f"face {row.get('face_id')} does not trace to four source edge rows")

    source = payload.get("source_cover", {})
    if source.get("base_state_count") != 33:
        errors.append("source cover base_state_count must be 33")
    if source.get("base_edge_count") != 198:
        errors.append("source cover base_edge_count must be 198")
    if source.get("fiber_phase_count") != 3:
        errors.append("source cover fiber_phase_count must be 3")
    if source.get("seam_lifted_shift_steps") != [1, 1, 1, 0]:
        errors.append("source seam shifts must match committed cover-v1")

    base = payload.get("base_incidence", {})
    total = payload.get("total_space_incidence", {})
    if base.get("chain_checks", {}).get("d_squared_zero") is not True:
        errors.append("base d^2 check must be zero")
    if total.get("chain_checks", {}).get("d_squared_zero") is not True:
        errors.append("total d^2 check must be zero")
    if total.get("cell_counts") != {"C0": 99, "C1": 693, "C2": 630, "C3": 36}:
        errors.append("total cell counts mismatch")

    for surface_name, surface in (("base", base), ("total", total)):
        for matrix_name, matrix in surface.get("boundary_matrices", {}).items():
            if matrix.get("format") != "sparse_coo":
                errors.append(f"{surface_name} {matrix_name} must use sparse_coo")
            if not matrix.get("sha256"):
                errors.append(f"{surface_name} {matrix_name} missing sha256")

    if payload.get("no_builder_audit_verdict") is not True:
        errors.append("no_builder_audit_verdict helper gate must be true")
    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
