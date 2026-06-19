#!/usr/bin/env python3
"""
Validator for rpf_outward_record_memory_v0.

Written to the HARD ACCEPTANCE bar: the controller re-runs this fresh. It RE-DERIVES
the load-bearing facts from the sim module rather than trusting the stored result
booleans, and asserts (and reports):

  1. The carrier maps share a finite domain and are genuinely distinct maps.

  THE IRREVERSIBILITY-PAIR TEST (re-measured from scratch):
  2. INWARD compression phi is MEASURED many-to-one: max_fiber>1 and bits_lost>0
     (information LOST / positive-entropy face). Re-computed by independent fiber
     counting, NOT read from the result.
  3. OUTWARD record rho is MEASURED injective: max_fiber==1 and bits_lost==0
     (information PRESERVED / negative-entropy face). Re-computed independently.
  4. The record is the structural INVERSE-DIRECTION of the loss: rho reconstructs the
     domain AND, paired with phi, recovers every inward fiber phi^{-1}(image), AND the
     joint map d|->(phi(d),rho(d)) is injective. Re-derived independently (the
     validator re-inverts rho and re-buckets under phi, comparing to the true fibers).
  5. The two orientations are OPPOSITE BY MEASUREMENT: derive_orientation(measure phi)
     == INWARD and derive_orientation(measure rho) == OUTWARD, with NO stored orientation
     string anywhere in the carrier.

  THE TWO DISCRIMINATING CONTROL FLIPS (re-run fresh):
  6. LOSSY RECORD: collapsing rho many-to-one MUST kill the memory property in EVERY
     measured sense (no longer injective, bits_lost>0, reconstruction fails, orientation
     no longer OUTWARD).
  7. REVERSIBLE COMPRESSION: making phi injective MUST kill the positive-entropy
     property in EVERY measured sense (no longer many-to-one, max_fiber==1, bits_lost==0,
     orientation no longer INWARD, phi alone reconstructs the domain).

  CONTAMINATION:
  8. After running both flips the module carrier DOMAIN_EVENTS is byte-identical to the
     canonical carrier (no mutation leaked into the serialized object).

Exits 0 (green) only if ALL of the above hold AND result["all_pass"] is True.

Run:  <sim-stack python3> validate_rpf_outward_record_memory_v0.py
"""

from __future__ import annotations

import json
import math
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import rpf_outward_record_memory_v0 as rpf  # noqa: E402


CANONICAL_CARRIER = {
    "e0": {"coarse_class": "C0", "fine_tag": 0},
    "e1": {"coarse_class": "C0", "fine_tag": 1},
    "e2": {"coarse_class": "C0", "fine_tag": 2},
    "e3": {"coarse_class": "C1", "fine_tag": 0},
    "e4": {"coarse_class": "C1", "fine_tag": 1},
    "e5": {"coarse_class": "C1", "fine_tag": 2},
    "e6": {"coarse_class": "C2", "fine_tag": 0},
    "e7": {"coarse_class": "C2", "fine_tag": 1},
}


def independent_measure(m: dict) -> dict:
    """Re-implement the fiber-cardinality + bits_lost measurement from scratch (do NOT
    call rpf.measure_map) so the validator does not merely echo the sim's measurement."""
    domain = set(m.keys())
    images = list(m.values())
    distinct_images = set(images)
    fibers: dict[str, int] = {}
    for img in images:
        fibers[img] = fibers.get(img, 0) + 1
    max_fiber = max(fibers.values()) if fibers else 0
    injective = (len(distinct_images) == len(domain)) and len(domain) >= 1
    bits_lost = (math.log2(len(domain)) - math.log2(len(distinct_images))) if (domain and distinct_images) else 0.0
    if -1e-12 < bits_lost < 0:
        bits_lost = 0.0
    return {
        "domain_size": len(domain),
        "distinct_images": len(distinct_images),
        "max_fiber": max_fiber,
        "injective": injective,
        "many_to_one": max_fiber > 1,
        "bits_lost": bits_lost,
    }


def independent_fiber_recovery(phi: dict, rho: dict) -> bool:
    """Re-derive (NOT via rpf.fibers_recovered_from_record) whether the record recovers
    every inward fiber: invert rho (must be injective), re-bucket the recovered ids
    under phi, compare to the true fibers of phi."""
    # rho must be injective for a well-defined inverse
    if len(set(rho.values())) != len(rho):
        return False
    rho_inv = {img: eid for eid, img in rho.items()}
    true_fibers: dict[str, set] = {}
    for eid, img in phi.items():
        true_fibers.setdefault(img, set()).add(eid)
    recovered: dict[str, set] = {}
    for _img, eid in rho_inv.items():
        recovered.setdefault(phi[eid], set()).add(eid)
    return true_fibers == recovered


def main() -> int:
    result = rpf.build_result()

    checks: dict[str, bool] = {}
    values: dict[str, object] = {}

    # 1. carrier maps share domain and are distinct
    phi = rpf.inward_compression_map(rpf.DOMAIN_EVENTS)
    rho = rpf.outward_record_map(rpf.DOMAIN_EVENTS)
    checks["maps_share_finite_domain"] = set(phi.keys()) == set(rho.keys()) and len(phi) >= 2
    checks["inward_and_outward_are_distinct_maps"] = phi != rho

    # 2. INWARD measured many-to-one / positive entropy (independent re-measurement)
    mphi = independent_measure(phi)
    values["independent_measure_inward"] = mphi
    checks["INWARD_many_to_one_remeasured"] = mphi["many_to_one"] and mphi["max_fiber"] > 1
    checks["INWARD_bits_lost_gt_0_remeasured"] = mphi["bits_lost"] > 0

    # 3. OUTWARD measured injective / negative entropy (independent re-measurement)
    mrho = independent_measure(rho)
    values["independent_measure_outward"] = mrho
    checks["OUTWARD_injective_remeasured"] = mrho["injective"] and mrho["max_fiber"] == 1
    checks["OUTWARD_bits_lost_eq_0_remeasured"] = mrho["bits_lost"] == 0

    # 4. record is the structural inverse-direction (independent re-derivation)
    rho_injective = len(set(rho.values())) == len(rho)
    record_reconstructs_domain = rho_injective and set(rho.keys()) == set(
        {img: eid for eid, img in rho.items()}.values()
    )
    fibers_recovered = independent_fiber_recovery(phi, rho)
    joint_pairs = {d: (phi[d], rho[d]) for d in phi}
    joint_injective = len(set(joint_pairs.values())) == len(joint_pairs) and len(joint_pairs) >= 1
    checks["record_reconstructs_domain_remeasured"] = record_reconstructs_domain
    checks["record_recovers_every_inward_fiber_remeasured"] = fibers_recovered
    checks["joint_pair_injective_remeasured"] = joint_injective
    checks["record_is_structural_inverse_direction"] = (
        record_reconstructs_domain and fibers_recovered and joint_injective
    )

    # 5. opposite orientation by measurement, no stored orientation string
    orient_phi = rpf.derive_orientation(mphi)
    orient_rho = rpf.derive_orientation(mrho)
    values["derived_orientation_inward"] = orient_phi
    values["derived_orientation_outward"] = orient_rho
    checks["orientation_inward_derived_INWARD"] = orient_phi == "INWARD"
    checks["orientation_outward_derived_OUTWARD"] = orient_rho == "OUTWARD"
    checks["orientations_opposite_by_measurement"] = (
        orient_phi == "INWARD" and orient_rho == "OUTWARD" and orient_phi != orient_rho
    )
    # no stored orientation string anywhere in the carrier rows
    checks["no_stored_orientation_string_in_carrier"] = all(
        "orientation" not in str(k).lower()
        for ev in rpf.DOMAIN_EVENTS.values() for k in ev.keys()
    )

    # 6. LOSSY RECORD flip kills memory (re-run fresh)
    flip1 = rpf.lossy_record_control(rpf.DOMAIN_EVENTS)
    # independent re-measurement of the lossy record map
    m_lossy = independent_measure(flip1["lossy_record_map"])
    lossy_remeasured_kills = (
        (not m_lossy["injective"])
        and m_lossy["bits_lost"] > 0
        and rpf.derive_orientation(m_lossy) != "OUTWARD"
    )
    checks["lossy_record_kills_memory_reported"] = bool(flip1["lossy_record_kills_memory"])
    checks["lossy_record_kills_memory_remeasured"] = lossy_remeasured_kills
    values["lossy_record_measure"] = m_lossy

    # 7. REVERSIBLE COMPRESSION flip kills positive entropy (re-run fresh)
    flip2 = rpf.reversible_compression_control(rpf.DOMAIN_EVENTS)
    m_rev = independent_measure(flip2["reversible_compression_map"])
    rev_reconstructs = (len(set(flip2["reversible_compression_map"].values()))
                        == len(flip2["reversible_compression_map"]))
    rev_remeasured_kills = (
        (not m_rev["many_to_one"])
        and m_rev["max_fiber"] == 1
        and m_rev["bits_lost"] == 0
        and rpf.derive_orientation(m_rev) != "INWARD"
        and rev_reconstructs
    )
    checks["reversible_compression_kills_positive_entropy_reported"] = bool(
        flip2["reversible_compression_kills_positive_entropy"]
    )
    checks["reversible_compression_kills_positive_entropy_remeasured"] = rev_remeasured_kills
    values["reversible_compression_measure"] = m_rev

    # 8. contamination: carrier byte-identical after both flips
    checks["module_carrier_uncontaminated_after_flips"] = rpf.DOMAIN_EVENTS == CANONICAL_CARRIER

    # the sim's own verdict must also be green
    checks["sim_all_pass"] = bool(result["all_pass"])
    checks["sim_irreversibility_pair_earned"] = bool(result["irreversibility_pair_earned"])

    green = all(checks.values())

    report = {
        "validator": "validate_rpf_outward_record_memory_v0",
        "checks": checks,
        "remeasured_values": values,
        "GREEN": green,
        "classification": result["classification"],
        "promotion_allowed": result["promotion_allowed"],
        "formal_admission_allowed": result["formal_admission_allowed"],
        "claim_ceiling": result["claim_ceiling"],
        "honest_self_assessment": result["honest_self_assessment"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
