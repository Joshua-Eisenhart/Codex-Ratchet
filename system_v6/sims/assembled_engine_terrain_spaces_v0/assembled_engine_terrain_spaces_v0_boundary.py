#!/usr/bin/env python3
"""Boundary checks for assembled_engine_terrain_spaces_v0."""

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
REQUIRED_CEILING = "rung_1_terrain_spaces_component_only_no_stage_or_engine_claim"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == REQUIRED_CEILING, "claim_ceiling mismatch")
    require(errors, "not the terrains simmed" in payload.get("component_boundary", ""), "component boundary must refuse terrain-simmed wording")
    require(errors, len(payload.get("terrain_spaces", [])) == 8, "must emit exactly eight terrain spaces")
    require(errors, payload.get("cross_terrain_distinctness", {}).get("all_pairs_distinguished_by_computed_structure") is True, "pairwise distinctness must pass")
    require(errors, payload.get("cross_terrain_distinctness", {}).get("homology_only_indistinguishable_pairs") not in (None, []), "homology-only collisions must be reported")

    gates = payload.get("builder_gates", {})
    require(errors, gates.get("g2a_boundary_from_birth") is True, "G.2a from-birth boundary missing")
    require(errors, gates.get("file_disjoint_packet") is True, "file-disjoint packet boundary missing")
    require(errors, gates.get("builder_must_not_write_audit_verdict") is True, "builder audit verdict write boundary missing")
    require(errors, gates.get("no_stage_region_rows") is True, "rung 1 must not emit stage rows")
    require(errors, gates.get("no_engine_traversal_rows") is True, "rung 1 must not emit engine traversal rows")
    require(errors, gates.get("no_axis_probe_rows") is True, "rung 1 must not emit axis probe rows")
    require(errors, gates.get("no_target_betti_fitting") is True, "target Betti fitting boundary missing")

    flags = payload.get("design_conformance", {}).get("owner_choice_flags", {})
    for key in ("substrate", "topology4_meaning", "flux_invariant", "ne_policy", "si_projector_frame", "finite_time_policy", "closure", "matrix64"):
        require(errors, key in flags, f"missing owner-choice flag: {key}")
        require(errors, flags.get(key, {}).get("owner_override_allowed") is True, f"{key} must be owner-overridable")
    require(errors, payload.get("design_conformance", {}).get("all_design_defaults_consumed") is True, "all design defaults must be consumed")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {
        "the terrains simmed",
        "sixteen stages constructed",
        "operator residency",
        "engine traversal",
        "axis probe result",
        "formal admission",
        "canonical by process",
        "bridge/physics/manifold claim",
    }:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    for terrain in payload.get("terrain_spaces", []):
        cert = terrain.get("topology_certificate", {})
        require(errors, cert.get("d_squared_zero") is True, f"{terrain.get('terrain_id')} d^2 failed")
        require(errors, cert.get("euler_cross_check", {}).get("passed") is True, f"{terrain.get('terrain_id')} Euler check failed")
        require(errors, terrain.get("homology_certificate_ref") == cert.get("certificate_sha256"), f"{terrain.get('terrain_id')} certificate ref mismatch")
        require(errors, terrain.get("flux_orientation", {}).get("computed_from_committed_structure") is True, f"{terrain.get('terrain_id')} flux not computed from structure")
        require(errors, terrain.get("terrain_generator", {}).get("law_ref", {}).get("source_refs") not in (None, []), f"{terrain.get('terrain_id')} missing law refs")

    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors

