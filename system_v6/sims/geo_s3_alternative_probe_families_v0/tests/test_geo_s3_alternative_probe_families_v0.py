#!/usr/bin/env python3
"""Behavior tests for geo_s3_alternative_probe_families_v0."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "geo_s3_alternative_probe_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}.py"


def load_module():
    spec = importlib.util.spec_from_file_location(SIM_ID, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_rank_survival_and_deliberate_single_axis_failure():
    module = load_module()
    payload = module.build_payload(run_julia=False)
    matrix = payload["survival_matrix"]

    assert matrix["A_sic_tetrahedron"]["informationally_complete"] is True
    assert matrix["A_sic_tetrahedron"]["frame_rank"] == 4
    assert matrix["B_mub_xyz"]["informationally_complete"] is True
    assert matrix["B_mub_xyz"]["frame_rank"] == 4
    assert matrix["C_single_axis_z"]["informationally_complete"] is False
    assert matrix["C_single_axis_z"]["frame_rank"] == 2
    assert matrix["C_single_axis_z"]["distinguished_pair_count"] < payload["battery"]["total_pair_count"]
    assert matrix["D_random_frame_null"]["frame_rank"] < 4
    assert matrix["D_random_frame_null"]["null_deficiency"] > 0


def test_quotient_classes_match_expected_family_structure():
    module = load_module()
    payload = module.build_payload(run_julia=False)
    quotients = payload["quotient_structures"]

    assert quotients["committed_pauli_xyz"]["class_count"] == 6
    assert quotients["A_sic_tetrahedron"]["class_count"] == 6
    assert quotients["B_mub_xyz"]["class_count"] == 6
    assert quotients["C_single_axis_z"]["classes"] == {
        "-1/2": [["0", "0", "-1/2"]],
        "0": [["-1/2", "0", "0"], ["0", "-1/2", "0"], ["0", "1/2", "0"], ["1/2", "0", "0"]],
        "1/2": [["0", "0", "1/2"]],
    }
    assert payload["structural_answer"]["committed_pattern_unique_or_shared"] == "shared_on_IC_rank_and_separation_unique_on_z_quotient_coarsening"
    assert sorted(payload["structural_answer"]["ic_co_survivors"]) == ["A_sic_tetrahedron", "B_mub_xyz", "committed_pauli_xyz"]


def test_smt_erased_flip_and_controls_are_load_bearing():
    module = load_module()
    payload = module.build_payload(run_julia=False)
    proofs = payload["crossover_proofs"]

    for solver in ("z3", "cvc5"):
        assert proofs[solver]["ran"] is True
        assert proofs[solver]["verdict"] == "sat"
        assert proofs[solver]["erased_verdict"] == "unsat"
        assert proofs[solver]["erased_flip_detected"] is True
        assert proofs[solver]["asserted_precomputed_boolean"] is False

    assert payload["controls"]["single_axis_fails_separation"]["fires"] is True
    assert payload["controls"]["rank_checks_exact"]["pass"] is True
    assert payload["build_gates"]["one_to_one_tool_calls"] is True
