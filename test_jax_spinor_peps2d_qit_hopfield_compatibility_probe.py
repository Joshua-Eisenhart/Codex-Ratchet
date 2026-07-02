#!/usr/bin/env python3
"""Receipt tests for the JAX spinor/PEPS2D/QIT-Hopfield probe."""

from __future__ import annotations

import json
from pathlib import Path


def test_spinor_peps2d_qit_hopfield_receipt_keeps_spinor_ontology():
    result_path = Path("jax_spinor_peps2d_qit_hopfield_compatibility_probe_results.json")
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_spinor_peps2d_qit_hopfield_compatibility"
    assert result["promotion_allowed"] is False
    assert result["formal_layer_admission_allowed"] is False
    assert result["ran_jax"] is True
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"

    checks = result["checks"]
    assert checks["finite_scale_sweep_8_16_32_64"]
    assert checks["spinor_physical_leg_roundtrip"]
    assert checks["density_trace_psd_rank_one"]
    assert checks["hopf_map_unit_s2"]
    assert checks["peps2d_virtual_bonds_load_bearing"]
    assert checks["tensor_only_control_rejected"]
    assert checks["inter_shell_g0_control"]
    assert checks["shuffled_shell_order_control"]
    assert checks["noncommuting_quaternion_order_witness"]
    assert checks["qit_entangling_readout_survives"]
    assert checks["qit_product_and_dephased_controls_collapse"]
    assert checks["geometric_hopfield_energy_decreases"]
    assert checks["geometric_hopfield_recall_improves"]
    assert checks["classical_dot_hopfield_control_not_equivalent"]

    assert result["scales"] == [8, 16, 32, 64]
    assert result["bond_dims"] == [2, 4]
    assert result["summary"]["max_spinor_roundtrip_error"] < 1.0e-10
    assert result["summary"]["min_peps2d_virtual_gap"] > 1.0e-3
    assert result["summary"]["min_tensor_only_rejection_gap"] > 1.0e-2
    assert result["summary"]["min_geometric_recall_gain"] > 0.05
    assert result["summary"]["min_classical_control_gap"] > 0.02

    assert result["blocked_consumers"]
    assert "Axis0" in result["blocked_consumers"]
    assert "final_manifold_admission" in result["blocked_consumers"]
