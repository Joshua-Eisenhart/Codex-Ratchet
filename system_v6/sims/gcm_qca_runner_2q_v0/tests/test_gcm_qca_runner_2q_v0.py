#!/usr/bin/env python3
"""Tests for gcm_qca_runner_2q_v0."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "gcm_qca_runner_2q_v0"
COMMON_PATH = SIM_DIR / "gcm_qca_runner_2q_v0_common.py"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")


def load_common():
    spec = importlib.util.spec_from_file_location("gcm_qca_runner_2q_v0_common", COMMON_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_card_declares_boundary_phrases():
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for phrase in (
        "dynamics | integrated-onto-the-carve | 2Q",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "J_ent",
        "J_cut",
        "gated on 3Q",
        "conditional on the 2Q registry audit verdict",
    ):
        assert phrase in text


def test_rank_extraction_rows_and_controls():
    common = load_common()
    packet = common.build_packet()
    by_id = {row["rule_id"]: row for row in packet["qca_index_rows"]}
    assert by_id["engine_L_flux_IN_left_O1"]["signed_log2_index"] == -2
    assert by_id["engine_R_flux_OUT_right_O1"]["signed_log2_index"] == 2
    assert packet["chirality_row"]["opposite"] is True
    assert by_id["nonchiral_onsite_index0"]["signed_log2_index"] == 0
    assert by_id["balanced_pair_swap_index0"]["index_ratio"] == "1/1"
    assert packet["controls"]["swap_L_to_R_flips_sign"] is True
    assert packet["quantization_check"]["all_indices_integer"] is True
    assert all(row["metadata_flow_fields_present"] is False for row in packet["qca_index_rows"])


def test_substrate_positive_and_lineage_free_negative():
    common = load_common()
    packet = common.build_packet()
    positive = common.gcm_substrate_check(packet, common.REGISTRY_PATH)
    assert positive["ok"] is True
    negative = common.gcm_substrate_check(common.make_lineage_free_negative(packet), common.REGISTRY_PATH)
    assert negative["ok"] is False
    assert "GCM_OBJECT_ID_MISMATCH" in negative["error_codes"]
    assert "GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH" in negative["error_codes"]
    assert "GCM_LINEAGE_CONSUMPTION_MISSING" in negative["error_codes"]


def test_m_c_and_fences():
    common = load_common()
    packet = common.build_packet()
    assert packet["M_C_preservation_summary"]["all_rows_preserve_M_C"] is True
    assert packet["M_C_preservation_summary"]["predicate_text_sha256"] == common.CARVE_PREDICATE_TEXT_SHA256
    assert packet["registry_dependency"]["claims_conditional_on_audit_verdict"] is True
    boundary = packet["qca_boundary"]
    assert boundary["finite_ring_nonzero_gnvw_claim"] == "not_claimed"
    assert boundary["first_runtime_flux_piece"] is True
    assert "J_ent" in boundary["runtime_flux_family_fence"]
    assert "J_cut" in boundary["runtime_flux_family_fence"]
    assert "gated on 3Q" in boundary["runtime_flux_family_fence"]


def test_script_and_validator_pass():
    runner = subprocess.run(
        [str(SIM_PY), str(SIM_DIR / "gcm_qca_runner_2q_v0.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert runner.returncode == 0, runner.stderr + runner.stdout
    validator = subprocess.run(
        [str(SIM_PY), str(SIM_DIR / "validate_gcm_qca_runner_2q_v0.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validator.returncode == 0, validator.stderr + validator.stdout
    result = json.loads((SIM_DIR / "results" / "gcm_qca_runner_2q_v0_validator_results.json").read_text())
    assert result["ok"] is True
