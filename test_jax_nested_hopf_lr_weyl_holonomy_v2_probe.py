#!/usr/bin/env python3
"""Tests for the JAX v2 nested-Hopf/LR-Weyl holonomy probe."""

from __future__ import annotations


def test_holonomy_v2_runs_as_bounded_diagnostic_not_admission():
    import jax_nested_hopf_lr_weyl_holonomy_v2_probe as probe

    result = probe.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_nested_hopf_lr_weyl_holonomy_v2"
    assert result["ran_jax"] is True
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"
    assert result["promotion_allowed"] is False
    assert result["formal_layer_admission_allowed"] is False
    assert result["one_layer_done_right_candidate"] is False
    assert result["all_pass"] is False

    checks = result["checks"]
    assert checks["scale_8_16_32_64"]
    assert checks["clifford_gamma_anticommutation"]
    assert checks["mixed_cocycle_signature_present"]
    assert checks["mixed_cocycle_magnitude_pass"] is False
    assert checks["mixed_cocycle_wrong_structure_control"]
    assert checks["holonomy_cos2eta_law"]
    assert checks["carrier_perturbation_holonomy_survives"]
    assert checks["equal_error_eta_erased_control_rejected"]
    assert checks["holonomy_gamma5_odd"]
    assert checks["chirality_flip_control"]
    assert checks["grok_deflation_control_run"]
    assert checks["singlebase_reproduces_holonomy_law"]
    assert checks["singlebase_does_not_reproduce_mixed_cocycle"]
    assert checks["grok_deflation_split_captured"]
    assert checks["order_dag_score_nonzero"]
    assert checks["bounded_v2_diagnostic_pass"]
    assert checks["bounded_v2_candidate_pass"] is False

    summary = result["summary"]
    assert summary["min_holonomy_r2"] > 0.999
    assert summary["max_holonomy_residual"] < 1.0e-10
    assert summary["min_perturbed_holonomy_r2"] > 0.995
    assert summary["max_equal_error_control_r2"] < 0.9
    assert summary["mixed_cocycle_nested_mag_min_LR"] > 0.3
    assert summary["mixed_cocycle_nested_mag_min_LR"] < 0.5
    assert summary["mixed_cocycle_winding_L"] == -summary["mixed_cocycle_winding_R"]
    assert summary["singlebase_holonomy_r2"] > 0.999
    assert summary["singlebase_reproduces_A_mixed_cocycle"] is False
    assert summary["singlebase_reproduces_B_holonomy_law"] is True
    assert summary["max_gamma_anticommutation_residual"] < 1.0e-10

    assert result["pre_registered_thresholds"]["holonomy_r2_min"] == 0.999
    assert result["pre_registered_thresholds"]["mixed_cocycle_mag_min"] == 0.5
    assert result["grok_deflation_control"]["grok_deflation_verdict"] == "mixed_single_base_reproduces_B_only"
    reauth = result["dependency_receipts"]["julia_cocycle_reauthor_readonly"]
    assert reauth["exists"] is True
    assert reauth["classification"] == "cocycle_reauthor_poc"
    assert reauth["verdict"] == "cocycle_genuine_signature"
    assert "Axis0" in result["blocked_consumers"]
    assert "final_manifold_admission" in result["blocked_consumers"]
