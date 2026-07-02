#!/usr/bin/env python3
"""Tests for the JAX terrain Choi holonomy ladder diagnostic."""

from __future__ import annotations


def test_terrain_choi_holonomy_ladder_is_bounded_diagnostic():
    import jax_terrain_choi_holonomy_ladder_probe as probe

    result = probe.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_terrain_choi_holonomy_ladder"
    assert result["promotion_allowed"] is False
    assert result["formal_layer_admission_allowed"] is False
    assert result["terrain_admission_allowed"] is False
    assert result["ran_julia"] is False
    assert result["ran_pytorch"] is False

    checks = result["checks"]
    assert checks["dependency_receipts_present"]
    assert checks["terrain_choi_rows_64x4"]
    assert checks["choi_channels_finite"]
    assert checks["choi_hermitian_psd"]
    assert checks["trace_preserving_channels"]
    assert checks["noncommuting_order_gap_preserved"]
    assert checks["holonomy_cos2eta_law_recorded"]
    assert checks["fixed_base_spin_lift_deflates_holonomy"]
    assert checks["mixed_cocycle_signature_present"]
    assert checks["mixed_cocycle_magnitude_not_promoted"]
    assert checks["terrain_erased_control_rejected"]
    assert checks["chirality_erased_control_rejected"]
    assert checks["loop_erased_control_rejected"]
    assert checks["operator_order_erased_control_rejected"]
    assert checks["promotion_blocked"]
    assert checks["bounded_diagnostic_pass"]

    summary = result["summary"]
    assert summary["choi_row_count"] == 256
    assert summary["microstep_count"] == 64
    assert summary["eta_count"] == 4
    assert summary["max_choi_hermitian_gap"] < 1.0e-10
    assert summary["min_choi_eigenvalue"] > -1.0e-10
    assert summary["max_trace_preserving_gap"] < 1.0e-10
    assert summary["min_row_holonomy_r2"] > 0.999
    assert summary["fixed_base_spin_lift_holonomy_r2"] > 0.999
    assert summary["mean_choi_order_gap"] > 1.0e-5
    assert summary["terrain_erased_gap"] > 1.0e-5
    assert summary["operator_order_erased_gap"] > 1.0e-5

    assert result["grok_deflation_split"]["singlebase_reproduces_B_holonomy_law"] is True
    assert result["grok_deflation_split"]["singlebase_reproduces_A_mixed_cocycle"] is False
    assert "Axis0" in result["blocked_consumers"]
    assert "final_manifold_admission" in result["blocked_consumers"]
