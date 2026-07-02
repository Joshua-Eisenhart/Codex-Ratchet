#!/usr/bin/env python3
"""Tests for the independent JAX physics recompute oracle."""

from __future__ import annotations


def test_high_risk_rows_are_independently_recomputed_without_promotion_or_julia():
    import jax_independent_physics_recompute_oracle as oracle

    result = oracle.run_audit(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["promotion_allowed"] is False
    assert result["executed_track"] == "jax"
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"
    assert result["rows_checked"] == 7
    assert result["rows_recomputed_pass"] == 7
    assert result["max_abs_metric_delta"] < 1.0e-8

    expected = {
        "boundary_environment_cut",
        "nested_hopf_shells",
        "weyl_gamma5_chirality",
        "qit_entropy_information",
        "conditional_mutual_information_readout",
        "spectral_triple_dirac",
        "survivor_quotient_branch_prune",
    }
    assert {row["layer_id"] for row in result["results"]} == expected
    assert all(row["recompute_pass"] for row in result["results"])
