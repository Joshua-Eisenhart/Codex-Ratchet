#!/usr/bin/env python3
"""Tests for the JAX runner over Julia-reference geometric constraint layers."""

from __future__ import annotations


def test_julia_reference_layer_runner_covers_all_reference_layers_without_promotion():
    import jax_julia_reference_geometric_constraint_layer_runner as runner

    result = runner.run_probe(write=False)

    assert result["AUDIT_PASS"] is True
    assert result["classification"] == "diagnostic_jax_julia_reference_geometric_constraint_layer_runner"
    assert result["promotion_allowed"] is False
    assert result["formal_admission_allowed"] is False
    assert result["ran_julia"] is False
    assert result["julia_reference_mode"] == "read_only"

    reference_names = set(result["julia_reference_layers"])
    row_names = {row["julia_reference_result"] for row in result["rows"]}
    assert reference_names == row_names
    assert len(result["rows"]) >= 20
    assert all(row["pass"] is True for row in result["rows"])
    assert all(row["promotion_allowed"] is False for row in result["rows"])

    checks = result["checks"]
    assert checks["all_reference_layers_have_jax_rows"]
    assert checks["all_rows_pass"]
    assert checks["no_julia_execution"]
    assert checks["promotion_blocked"]
