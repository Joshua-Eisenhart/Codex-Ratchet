#!/usr/bin/env python3
"""Tests for the JAX twistor-incidence substrate falsifier."""

from __future__ import annotations


def test_twistor_incidence_probe_falsifies_canonical_promotion():
    import jax_twistor_incidence_substrate_probe as probe

    result = probe.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_twistor_incidence_substrate_probe"
    assert result["ran_jax"] is True
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"
    assert result["promotion_allowed"] is False
    assert result["formal_layer_admission_allowed"] is False

    checks = result["checks"]
    assert checks["incidence_relation_present"]
    assert checks["blockdiag_control_near_floor"]
    assert checks["x0_incidence_control_near_floor"]
    assert checks["twistor_incidence_nonzero"]
    assert checks["twistor_distinct_from_blockdiag"]
    assert checks["random_offdiag_control_blocks_promotion"]
    assert checks["twistor_no_better_than_generic_offdiag"]
    assert checks["negative_probe_pass"]

    verdict = result["verdict"]
    assert verdict["overall"] == "twistor_no_better_than_blockdiag"
    assert verdict["promotion_allowed"] is False

    summary = result["summary"]
    assert summary["tw_vs_block_gap"] > 0.02
    assert summary["best_random_offdiag_gap_over_twistor"] >= 0.0
