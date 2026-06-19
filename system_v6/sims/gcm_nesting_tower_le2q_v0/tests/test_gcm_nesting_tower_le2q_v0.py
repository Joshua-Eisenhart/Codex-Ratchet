#!/usr/bin/env python3
"""Regression checks for gcm_nesting_tower_le2q_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import gcm_nesting_tower_le2q_v0_common as common  # noqa: E402


def result_payload() -> dict:
    return json.loads(common.RESULT_PATH.read_text(encoding="utf-8"))


def test_rebuilt_packet_passes_and_matches_written_result() -> None:
    rebuilt = common.build_packet(write=False)
    written = result_payload()
    for payload in (rebuilt, written):
        assert payload["all_pass"] is True
        assert payload["classification"] == "scratch_diagnostic"
        assert payload["promotion_allowed"] is False
        assert payload["formal_admission_allowed"] is False
        assert payload["axis_declaration"] == {"axis": "nesting/tower", "object": "inverse-limit", "rung": "<=2Q"}
    for key in ("counts", "fiber_summary", "entangled_16_fiber_membership", "exact_vs_probe_equivalence_adjudication"):
        assert rebuilt[key] == written[key]


def test_tower_cardinalities_and_exact_probe_split() -> None:
    counts = result_payload()["counts"]
    assert counts["one_q_survivor_count"] == 16
    assert counts["two_q_survivor_count"] == 544
    assert counts["exact_compatible_2q_count"] == 256
    assert counts["exact_compatible_family_triple_count"] == 256
    assert counts["exact_orphan_2q_count"] == 288
    assert counts["probe_compatible_2q_count"] == 464
    assert counts["probe_compatible_family_triple_count"] == 1856
    assert counts["probe_orphan_2q_count"] == 80
    assert counts["probe_rescued_exact_orphan_2q_count"] == 208
    assert counts["quotient_multiplicity_added_family_triples"] == 1600


def test_fibers_products_and_entanglement_place() -> None:
    payload = result_payload()
    fibers = payload["fiber_summary"]
    assert fibers["fiber_size_distribution"]["exact_A"] == {"34": 16}
    assert fibers["fiber_size_distribution"]["exact_B"] == {"16": 16}
    assert fibers["fiber_size_distribution"]["probe_A"] == {"68": 16}
    assert fibers["fiber_size_distribution"]["probe_B"] == {"48": 8, "64": 6, "80": 2}
    assert fibers["cover_partition_checks"]["exact_A_partitions_all_2q_survivors"] is True
    assert fibers["cover_partition_checks"]["exact_B_partitions_exact_compatible_2q_survivors"] is True

    controls = payload["controls"]
    product = controls["product_only_subtower"]
    assert product["exact_product_subtower_count"] == 256
    assert product["pinned_product_embedding_row_count"] == 16
    assert product["pinned_product_embedding_all_survive"] is True

    entangled = payload["entangled_16_fiber_membership"]
    assert entangled["entangled_2q_count"] == 16
    assert entangled["exact_compatible_count"] == 0
    assert entangled["probe_compatible_count"] == 16
    assert entangled["verdict"] == "entangled_16_are_exact_B_orphans_but_probe_compatible_fiber_members"


def test_controls_and_envelope_shape() -> None:
    payload = result_payload()
    controls = payload["controls"]
    assert controls["substrate_positive_1q"]["ok"] is True
    assert controls["substrate_positive_2q"]["ok"] is True
    assert controls["substrate_lineage_free_negative_1q"]["ok"] is False
    assert controls["substrate_lineage_free_negative_2q"]["ok"] is False
    assert controls["scrambled_pairing_tower"]["all_probe_compatibility_destroyed"] is True
    assert payload["bidirectional_check"]["all_round_trips_pass"] is True

    envelope = common.build_envelope(write=False)
    assert envelope["all_pass"] is True
    assert envelope["mode"] == common.ENGINE_MODE
    assert set(envelope["engine_lanes"]) == {"julia", "jax", "pytorch"}
    assert envelope["engine_consensus"]["all_engine_lanes_pass"] is True
    assert envelope["divergence"]["max_divergence"] == 0
