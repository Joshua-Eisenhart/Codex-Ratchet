#!/usr/bin/env python3
"""Tests for topology_parity_cell_model_v1."""

from __future__ import annotations

import json
from pathlib import Path
import sys


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import topology_parity_cell_model_v1_common as common  # noqa: E402
import validate_topology_parity_cell_model_v1 as validator  # noqa: E402


def test_reference_gate_recovers_s3_and_s2xs1_before_cover_rows() -> None:
    refs = common.run_reference_gate()

    assert refs["explicit_s3"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert refs["explicit_s2xs1"]["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
    assert refs["reference_gate_passed"] is True


def test_v0_controls_and_mislabeled_negative() -> None:
    controls = common.run_controls()

    assert controls["torus_reference"]["betti_b0_b1_b2_b3"][:3] == [1, 2, 1]
    assert controls["sphere_reference"]["betti_b0_b1_b2_b3"][:3] == [1, 0, 1]
    assert controls["disk_reference"]["betti_b0_b1_b2_b3"][:3] == [1, 0, 0]
    assert controls["mislabeled_torus_as_sphere_negative"]["pass"] is True


def test_cover_rows_derive_degree_from_committed_clutching() -> None:
    payload = common.build_topology_parity_cell_model_object()

    assert payload["reference_gate"]["reference_gate_passed"] is True
    assert payload["cover_inputs"]["v1"]["fiber_phase_count"] == 3
    assert payload["cover_inputs"]["v1"]["seam_lifted_shift_steps"] == [1, 1, 1, 0]
    assert payload["cover_inputs"]["v1"]["degree"] == 1
    assert payload["cover_inputs"]["zero_shift_product"]["degree"] == 0
    assert payload["complexes"]["v1_degree_one_cover"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert payload["complexes"]["zero_shift_product_cover"]["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]


def test_wrong_gluing_control_moves_betti_profile() -> None:
    payload = common.build_topology_parity_cell_model_object()
    wrong = payload["controls"]["wrong_gluing_erased_v1_seam"]

    assert wrong["pass"] is True
    assert wrong["wrong_betti_b0_b1_b2_b3"] != payload["complexes"]["v1_degree_one_cover"]["betti_b0_b1_b2_b3"]
    assert wrong["wrong_betti_b0_b1_b2_b3"] == payload["complexes"]["zero_shift_product_cover"]["betti_b0_b1_b2_b3"]


def test_validator_accepts_current_packet_payload() -> None:
    payload = common.build_topology_parity_cell_model_object()
    assert validator.validate_payload(payload) == []


def test_runner_writes_result_json(tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    payload = common.build_topology_parity_cell_model_object()
    common.write_json(out, payload)
    reloaded = json.loads(out.read_text(encoding="utf-8"))

    assert reloaded["sim_id"] == common.SIM_ID
    assert reloaded["classification"] == "scratch_diagnostic"
    assert reloaded["promotion_allowed"] is False
    assert reloaded["no_builder_audit_verdict"] is True
