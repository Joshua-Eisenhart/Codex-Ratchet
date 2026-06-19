#!/usr/bin/env python3
"""Behavior tests for basin_two_engine_joint_v4_within_sector_v0."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "basin_two_engine_joint_v4_within_sector_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}_common.py"


def load_module():
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_flux_erased_reproduces_corrected_v3_cores():
    module = load_module()
    payload = module.build_flux_payload()
    continuity = payload["controls"]["flux_erased_continuity"]

    assert continuity["all_pass"] is True
    for engine in ("L", "R"):
        assert continuity["per_engine"]["A_readout_transition_dwell"][engine]["observed"]["terminal_class_count"] == 1
        assert continuity["per_engine"]["A_readout_transition_dwell"][engine]["observed"]["terminal_sizes"] == [28]
        assert continuity["per_engine"]["D_matrix64_b_order_overlay"][engine]["observed"]["terminal_class_count"] == 1
        assert continuity["per_engine"]["D_matrix64_b_order_overlay"][engine]["observed"]["terminal_sizes"] == [24]


def test_conserved_flux_is_sector_decomposition_not_genuine_hit():
    module = load_module()
    payload = module.build_flux_payload()
    family = payload["realization_family"]
    conserved = family["rows"]["conserved_flux_control"]["variants"]

    assert payload["controls"]["conserved_flux"]["all_pass"] is True
    for variant_rows in conserved.values():
        for row in variant_rows.values():
            assert row["flux_carried"]["terminal_class_count"] == 2
            assert row["conclusion"]["reproduces_v4_sector_decomposition"] is True
            assert row["projection_and_symmetry_checks"]["genuine_terminal_count"] == 0


def test_registered_family_has_state_dependent_flip_edges():
    module = load_module()
    payload = module.build_flux_payload()
    family = payload["realization_family"]["rows"]

    candidate_flip_edges = []
    for law_id, law_rows in family.items():
        if law_id == "conserved_flux_control":
            continue
        for variant_rows in law_rows["variants"].values():
            for row in variant_rows.values():
                candidate_flip_edges.append(row["flux_flip_edge_count"])
    assert any(count > 0 for count in candidate_flip_edges)


def test_projection_and_symmetry_orbit_gate_rejects_sector_duplicates():
    module = load_module()
    payload = module.build_flux_payload()

    for law_rows in payload["realization_family"]["rows"].values():
        for variant_rows in law_rows["variants"].values():
            for row in variant_rows.values():
                for terminal in row["projection_and_symmetry_checks"]["terminal_checks"]:
                    if terminal["sector_duplicate_under_flux_involution"]:
                        assert terminal["genuine_candidate_under_panel6_q3"] is False
                    if terminal["full_projection_echo"] and not terminal["in_class_flux_flipping"]:
                        assert terminal["genuine_candidate_under_panel6_q3"] is False


def test_packet_ceiling_and_boundary_helper_contract():
    module = load_module()
    payload = module.build_flux_payload()

    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["build_gates"]["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()
    assert payload["build_gates"]["projection_tests_present"] is True
    assert payload["build_gates"]["symmetry_orbit_tests_present"] is True
