#!/usr/bin/env python3
"""
Positive + negative + boundary tests for rpf_outward_record_memory_v0.

Run:  <sim-stack python3> tests/test_rpf_outward_record_memory_v0.py
Exit 0 iff every assertion holds.
"""
from __future__ import annotations

import math
import os
import sys

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SIM_DIR)

import rpf_outward_record_memory_v0 as rpf  # noqa: E402


def test_positive_irreversibility_pair_earned() -> None:
    t = rpf.irreversibility_pair_test(rpf.DOMAIN_EVENTS)
    assert t["irreversibility_pair_earned"] is True
    # inward measured many-to-one with positive loss
    assert t["measure_inward"]["max_fiber"] == 3
    assert t["measure_inward"]["bits_lost"] == math.log2(8) - math.log2(3)
    assert t["measure_inward"]["bits_lost"] > 0
    # outward measured injective with zero loss
    assert t["measure_outward"]["injective"] is True
    assert t["measure_outward"]["bits_lost"] == 0
    # opposite orientation derived from measurement
    assert t["derived_orientation_inward"] == "INWARD"
    assert t["derived_orientation_outward"] == "OUTWARD"
    assert t["opposite_orientation_by_measurement"] is True
    # the record is the structural inverse-direction of phi's loss
    assert t["record_is_structural_inverse_direction"] is True


def test_positive_both_control_flips_fire() -> None:
    flip1 = rpf.lossy_record_control(rpf.DOMAIN_EVENTS)
    flip2 = rpf.reversible_compression_control(rpf.DOMAIN_EVENTS)
    assert flip1["lossy_record_kills_memory"] is True
    assert flip2["reversible_compression_kills_positive_entropy"] is True


def test_negative_lossy_record_breaks_memory() -> None:
    """Collapsing the record many-to-one must break EVERY measured memory property."""
    flip1 = rpf.lossy_record_control(rpf.DOMAIN_EVENTS)
    assert flip1["no_longer_injective"] is True
    assert flip1["memory_leaks_bits_lost_gt_0"] is True
    assert flip1["reconstruction_fails"] is True
    assert flip1["derived_orientation_lossy_record"] != "OUTWARD"


def test_negative_reversible_compression_breaks_positive_entropy() -> None:
    """Making phi injective must break EVERY measured positive-entropy property."""
    flip2 = rpf.reversible_compression_control(rpf.DOMAIN_EVENTS)
    assert flip2["no_longer_many_to_one"] is True
    assert flip2["max_fiber_is_one"] is True
    assert flip2["no_information_lost_bits_lost_eq_0"] is True
    assert flip2["derived_orientation_reversible_compression"] != "INWARD"
    assert flip2["record_now_redundant_phi_reconstructs_domain"] is True


def test_negative_substituting_lossy_outward_unearns() -> None:
    """If the outward map is replaced by a lossy one, the pair must NOT be earned
    (the acceptance test is not vacuous)."""
    orig = rpf.outward_record_map
    try:
        rpf.outward_record_map = lambda d: {
            eid: ev["coarse_class"] for eid, ev in sorted(d.items())
        }
        t = rpf.irreversibility_pair_test(rpf.DOMAIN_EVENTS)
        assert t["irreversibility_pair_earned"] is False
    finally:
        rpf.outward_record_map = orig


def test_boundary_non_injective_record_fails_fiber_recovery() -> None:
    """A record that collides distinct events (fine-tag only) cannot recover the fibers."""
    phi = rpf.inward_compression_map(rpf.DOMAIN_EVENTS)
    fine_only = {eid: str(ev["fine_tag"]) for eid, ev in sorted(rpf.DOMAIN_EVENTS.items())}
    m = rpf.measure_map(fine_only)
    assert m["injective"] is False
    assert rpf.fibers_recovered_from_record(phi, fine_only)["all_inward_fibers_recovered"] is False


def test_boundary_single_event_map_orientation_none_or_outward() -> None:
    """A one-element map is injective (OUTWARD) and an empty map derives None."""
    assert rpf.derive_orientation(rpf.measure_map({})) is None
    assert rpf.derive_orientation(rpf.measure_map({"x": "y"})) == "OUTWARD"


def test_boundary_carrier_uncontaminated_after_flips() -> None:
    canonical = {
        "e0": {"coarse_class": "C0", "fine_tag": 0},
        "e1": {"coarse_class": "C0", "fine_tag": 1},
        "e2": {"coarse_class": "C0", "fine_tag": 2},
        "e3": {"coarse_class": "C1", "fine_tag": 0},
        "e4": {"coarse_class": "C1", "fine_tag": 1},
        "e5": {"coarse_class": "C1", "fine_tag": 2},
        "e6": {"coarse_class": "C2", "fine_tag": 0},
        "e7": {"coarse_class": "C2", "fine_tag": 1},
    }
    rpf.lossy_record_control(rpf.DOMAIN_EVENTS)
    rpf.reversible_compression_control(rpf.DOMAIN_EVENTS)
    assert rpf.DOMAIN_EVENTS == canonical


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\nALL {len(tests)} TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
