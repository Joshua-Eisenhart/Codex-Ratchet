#!/usr/bin/env python3
"""Tests for the JAX nested-Hopf/LR-Weyl first-layer candidate receipt."""

from __future__ import annotations


def test_nested_hopf_lr_weyl_first_layer_candidate_runs_but_does_not_admit():
    import jax_nested_hopf_lr_weyl_first_layer_candidate as probe

    result = probe.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["all_pass"] is True
    assert result["classification"] == "diagnostic_jax_nested_hopf_lr_weyl_first_layer_candidate"
    assert result["ran_jax"] is True
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"
    assert result["promotion_allowed"] is False
    assert result["formal_layer_admission_allowed"] is False

    checks = result["checks"]
    assert checks["scale_8_16_32_64"]
    assert checks["bond_dim_D_2_4"]
    assert checks["nested_hopf_tori_two_shells_present"]
    assert checks["left_right_weyl_sheets_present"]
    assert checks["gamma5_chirality_signs"]
    assert checks["spinor_density_valid"]
    assert checks["hopf_map_unit_s2"]
    assert checks["peps2d_shell_virtual_bonds_load_bearing"]
    assert checks["tensor_only_control_rejected"]
    assert checks["inter_shell_g0_control"]
    assert checks["shuffled_shell_order_control"]
    assert checks["lr_weyl_g0_control"]
    assert checks["lr_weyl_chirality_flip_control"]
    assert checks["qit_product_and_dephased_controls_collapse"]
    assert checks["noncommuting_quaternion_order_witness"]
    assert checks["hopfield_attractor_control"]
    assert checks["exact_mps_style_spinor_crosscheck"]
    assert checks["five_non_vacuous_ablations"]
    assert checks["candidate_first_layer_working_target_pass"]

    summary = result["summary"]
    assert summary["min_peps2d_virtual_gap"] > 1.0e-3
    assert summary["min_tensor_only_rejection_gap"] > 1.0e-2
    assert summary["min_lr_log_negativity"] > 1.0e-6
    assert summary["min_nested_order_gap"] > 1.0e-4
    assert summary["min_exact_mps_entropy"] > 1.0e-6
    assert summary["max_exact_mps_entropy_disagreement"] < 1.0e-10
    assert summary["ablation_pass_count"] >= 5

    assert result["carrier_crosscheck"]["mode"] == "exact_schmidt_vs_partial_trace"
    assert result["carrier_crosscheck"]["uses_ctmrg"] is False
    assert result["carrier_crosscheck"]["uses_peps2d_optimization"] is False

    assert "Axis0" in result["blocked_consumers"]
    assert "final_manifold_admission" in result["blocked_consumers"]
