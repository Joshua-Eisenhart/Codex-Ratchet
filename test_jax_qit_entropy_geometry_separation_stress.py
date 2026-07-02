#!/usr/bin/env python3
"""Tests for the JAX QIT entropy/geometry separation stress probe."""

from __future__ import annotations


def test_qit_entropy_geometry_separation_is_jax_only_and_no_promotion():
    import jax_qit_entropy_geometry_separation_stress as probe

    result = probe.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_qit_entropy_geometry_separation_stress"
    assert result["promotion_allowed"] is False
    assert result["executed_track"] == "jax"
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"

    checks = result["checks"]
    assert checks["linked_has_logneg_and_cmi"]
    assert checks["matched_trivial_preserves_local_entropy_budget"]
    assert checks["matched_trivial_kills_ac_entanglement_and_cmi"]
    assert checks["dephasing_kills_logneg_but_not_classical_cmi_shadow"]
    assert checks["product_kills_all_readouts"]
    assert checks["noncommuting_order_gap_present"]
    assert checks["capacity_budget_finite_and_respected"]

    linked = result["cases"]["linked_ac_er_bridge"]
    trivial = result["cases"]["matched_trivial_chain"]
    dephased = result["cases"]["dephased_linked_classical_shadow"]
    product = result["cases"]["product"]

    assert linked["LN_AC"] > 0.99
    assert linked["I_c_A_to_C"] > 0.99
    assert linked["CMI_A_C_given_B"] > 1.99
    assert trivial["LN_AC"] < 1.0e-9
    assert trivial["CMI_A_C_given_B"] < 1.0e-9
    assert abs(linked["single_site_entropy_sum"] - trivial["single_site_entropy_sum"]) < 1.0e-9
    assert dephased["LN_AC"] < 1.0e-9
    assert dephased["CMI_A_C_given_B"] > 0.99
    assert product["LN_AC"] < 1.0e-9
    assert product["CMI_A_C_given_B"] < 1.0e-9
