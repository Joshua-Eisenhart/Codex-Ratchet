#!/usr/bin/env python3
"""Focused tests for the classical ring-checkerboard automaton packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PACKET = Path(__file__).resolve().parents[1]
RESULT = PACKET / "results" / "ring_checkerboard_automaton_v0_envelope_results.json"
sys.path.insert(0, str(PACKET))

import ring_checkerboard_automaton_v0_common as common


def test_support_counts_are_owner_named_sizes() -> None:
    rows = [common.support_counts(n) for n in (4, 8, 16)]
    assert [row["steps_per_ring"] for row in rows] == [4, 8, 16]
    for row in rows:
        n = row["steps_per_ring"]
        assert row["support_cell_count"] == n * (n + 1)
        assert row["single_active_readout_probe_microstates"] == 16 * n * (n + 1)
        assert row["phase_test_microstates_per_directed_order"] == 8 * n * (n + 1)
        assert row["full_binary_configuration_enumerated"] is False


def test_phase_orders_are_preserved_and_distinguished() -> None:
    packet = common.build_packet()
    phase = packet["phase_test"]
    assert phase["alternating_order"]["preserved"] is True
    assert phase["paired_order"]["preserved"] is True
    assert phase["terminal_structure_distinguishable"] is True
    assert phase["orbit_structure_distinguishable"] is True
    assert phase["order_shuffle_changes_dynamics"] is True
    assert phase["verdict"] == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR"


def test_required_controls_fire_and_label_permutation_is_invariant() -> None:
    controls = common.build_packet()["controls"]
    for key in [
        "similarity_only_cluster",
        "non_partitioned_scramble",
        "order_shuffle",
        "ring_off",
        "checkerboard_off",
        "nesting_off",
        "frozen_phase",
    ]:
        assert controls[key]["fired"] is True
    assert controls["label_permutation"]["counts_invariant"] is True


def test_basin_rows_have_terminal_absent_exit_proofs() -> None:
    packet = common.build_packet()
    for name in ["alternating", "paired", "intrinsic"]:
        row = packet["basin_partition_tables"][name]
        assert row["terminal_classes"]
        assert row["basin_map"]
        for terminal in row["terminal_classes"]:
            assert terminal["absent_exit_proof"]["no_exit"] is True
            assert terminal["absent_exit_proof"]["outgoing_edge_count"] == 0
        assert "exists_for_pinned_rules" in row["monotone_exclusion_observable"]


def test_smt_phase_separation_has_unsat_and_flip_sat() -> None:
    proofs = common.build_packet()["crossover_proofs"]
    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["z3"]["computed_perturbation_flip_verdict"] == "sat"
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["cvc5"]["computed_perturbation_flip_verdict"] == "sat"


def test_envelope_boundary_if_generated() -> None:
    if not RESULT.exists():
        return
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["builder_gates"]["no_builder_audit_verdict"] is True
    assert payload["no_builder_audit_verdict"] is True
    assert payload["object"]["qca_index"] == "v1_or_later_not_here"
