#!/usr/bin/env python3
"""Tests for the JAX nested Hopf shell branch/prune QIT probe."""

from __future__ import annotations


def test_nested_hopf_shell_probe_is_jax_only_and_constraint_bounded():
    import jax_nested_hopf_shell_branch_prune_qit_probe as probe

    result = probe.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_nested_hopf_shell_branch_prune_qit"
    assert result["promotion_allowed"] is False
    assert result["executed_track"] == "jax"
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"

    checks = result["checks"]
    assert checks["baseline_reaches_all_basins"]
    assert checks["chirality_prune_kills_forbidden_basins"]
    assert checks["allowed_basins_preserved_after_prune"]
    assert checks["trivial_control_matches_baseline"]
    assert checks["real_prune_fired"]
    assert checks["bookkeeping_consistent"]
    assert checks["spinor_norm_retraction_works"]
    assert checks["hopf_map_stays_on_s2"]
    assert checks["quaternion_order_witness_present"]
    assert checks["qit_link_controls_pass"]
    assert checks["capacity_budget_finite_and_respected"]

    runs = result["runs"]
    assert runs["A_no_prune"]["populated_basins"] == [1, 2, 3, 4]
    assert set(runs["B_chirality_prune"]["populated_basins"]) <= {1, 2}
    assert runs["C_trivial_control"]["populated_basins"] == runs["A_no_prune"]["populated_basins"]
    assert runs["C_trivial_control"]["pruned"] == 0
    assert runs["B_chirality_prune"]["pruned"] > 0

    qit = result["qit_link_controls"]
    assert qit["linked_logneg"] > 0.99
    assert qit["dephased_logneg"] < 1.0e-9
    assert qit["dephased_cmi_shadow"] > 0.99
