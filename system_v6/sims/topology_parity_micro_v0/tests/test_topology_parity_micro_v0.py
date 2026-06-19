#!/usr/bin/env python3
"""Tests for topology_parity_micro_v0."""

from __future__ import annotations

import json
from pathlib import Path
import sys


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import topology_parity_micro_v0_common as common  # noqa: E402
import validate_topology_parity_micro_v0 as validator  # noqa: E402


def test_reference_controls_have_known_betti_numbers() -> None:
    controls = common.run_reference_controls()

    assert controls["torus_reference"]["gudhi_betti"] == [1, 2, 1]
    assert controls["torus_reference"]["hodge_kernel_dims"][:3] == [1, 2, 1]
    assert controls["disk_reference"]["gudhi_betti"] == [1, 0, 0]
    assert controls["disk_reference"]["hodge_kernel_dims"][:3] == [1, 0, 0]
    assert controls["sphere_reference"]["gudhi_betti"] == [1, 0, 1]
    assert controls["sphere_reference"]["hodge_kernel_dims"][:3] == [1, 0, 1]
    assert controls["mislabeled_torus_as_sphere_negative"]["pass"] is True


def test_cover_and_product_complexes_are_built_from_v1_cover_hashes() -> None:
    payload = common.build_topology_parity_object()
    complexes = payload["complexes"]
    source_cover = payload["source_cover"]

    assert complexes["v1_degree_one_cover"]["vertex_count"] == 99
    assert complexes["zero_shift_product_cover"]["vertex_count"] == 99
    assert source_cover["v1_cover_sha256"] == complexes["v1_degree_one_cover"]["source_cover_sha256"]
    assert source_cover["zero_shift_cover_sha256"] == complexes["zero_shift_product_cover"]["source_cover_sha256"]
    assert source_cover["v1_transition_rows_sha256"]
    assert source_cover["zero_shift_transition_rows_sha256"]


def test_expected_profiles_are_preregistered_before_computed_profiles() -> None:
    payload = common.build_topology_parity_object()
    expected = payload["expected_profiles_preregistered_from_math"]

    assert expected["v1_degree_one_cover"]["ideal_space"] == "S3_like_total_space"
    assert expected["v1_degree_one_cover"]["expected_betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert expected["zero_shift_product_cover"]["ideal_space"] == "S2xS1_product_total_space"
    assert expected["zero_shift_product_cover"]["expected_betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
    assert payload["preregistration_order"] == "expected_profiles_declared_before_computation"


def test_validator_accepts_current_packet_payload() -> None:
    payload = common.build_topology_parity_object()
    errors = validator.validate_payload(payload)
    assert errors == []


def test_runner_writes_result_json(tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    payload = common.build_topology_parity_object()
    common.write_json(out, payload)
    reloaded = json.loads(out.read_text(encoding="utf-8"))

    assert reloaded["sim_id"] == common.SIM_ID
    assert reloaded["classification"] == "scratch_diagnostic"
    assert reloaded["promotion_allowed"] is False
