#!/usr/bin/env python3
"""
rpf_outward_record_memory_v0 -- the OUTWARD RECORD as a genuine injective MEMORY map
that is the structural inverse-direction of the many-to-one INWARD compression.

WHAT THIS SIM ATTACKS (distinct from rpf_v1/v2/v3):
  rpf_v3 earned a GLOBAL-vs-GREEDY survivor-selection separation. It did NOT make the
  outward_record do real work: its record was the trivial id->id map (each compressed-
  away event preserved as literally itself), which is injective but VACUOUSLY so -- it
  carries no relation to what the compression actually forgot. This sim does NOT
  re-litigate survivor selection. It builds the ONE thing the owner model says the
  outward record IS, and makes it MEASURED, not labeled.

THE OWNER-MODEL ANCHOR (object source, kept as excavation not admission;
system_v5/docs/session_20260606_physics_excavation/01_OWNER_PHYSICS_MODEL.md):
  > "Dark energy is positive entropy and dark matter is negative entropy."
  > "dark matter is information, literally information itself being preserved"
  The OUTWARD record = the dark-matter face = NEGATIVE entropy / PRESERVED information /
  inherited memory. The INWARD compression = the dark-energy/time face = POSITIVE
  entropy / many-to-one collapse. The two are an IRREVERSIBILITY / TIME-REVERSAL PAIR:
  one direction forgets (many-to-one, lossy), the opposite direction remembers
  (one-to-one, the memory that exactly compensates what was forgotten).

THE STRUCTURAL CLAIM (what "structural inverse-direction" MEANS here, operationally):
  Let the inward compression be a map  phi : D -> I  on a finite carrier D.
    - phi is MANY-TO-ONE: some image i in I has |phi^{-1}(i)| > 1. From phi(d) alone you
      CANNOT recover d. Information is LOST. (positive entropy: many configurations
      collapse to one summary.)
  Let the outward record be a map  rho : D -> R.
    - rho is INJECTIVE: distinct d map to distinct r. From rho(d) you CAN recover d.
      Information is PRESERVED. (negative entropy: each event kept as its own image.)
  The record is the STRUCTURAL INVERSE-DIRECTION of the compression iff the PAIR
  (phi, rho) is JOINTLY reversible: the combined map d |-> (phi(d), rho(d)) is
  injective AND the record alone suffices to reconstruct D (and hence to invert phi's
  collapse: given an image i and the record, the full fiber phi^{-1}(i) is recovered).
  This is the precise sense in which rho remembers EXACTLY what phi forgot. It is a
  measured right-section property, not a stipulated label.

THE IRREVERSIBILITY-PAIR TEST (HARD ACCEPTANCE, first-class in result JSON):
  We MEASURE both directions on the SAME carrier D and assert OPPOSITE orientation BY
  MEASUREMENT (never by a stored "INWARD"/"OUTWARD" string):
    (A) inward fiber cardinality: measure max_fiber(phi). many_to_one (max_fiber>1)
        => information LOST => positive-entropy / INWARD face. We also report the
        measured information loss bits_lost(phi) = log2|D| - log2|image(phi)| > 0.
    (B) outward record injectivity: measure injective(rho). one-to-one
        => information PRESERVED => negative-entropy / OUTWARD face. bits_lost(rho)=0.
    (C) reconstruction (the inverse-direction proof): rho reconstructs D exactly
        (record_reconstructs_domain), and the pair (phi,rho) recovers every inward
        fiber (fibers_recovered_from_record). So rho is phi's structural inverse-
        direction: it stores precisely the distinction phi destroyed.
    (D) opposite-orientation-by-measurement: derive_orientation(measure_phi)==INWARD
        and derive_orientation(measure_rho)==OUTWARD, and they are NOT EQUAL --
        established from the measured cardinalities, with NO stored orientation string.

  irreversibility_pair_earned == (A) and (B) and (C) and (D).

THE TWO DISCRIMINATING CONTROL FLIPS (HARD ACCEPTANCE, first-class):
  FLIP 1 -- LOSSY RECORD: make rho non-injective (collapse it many-to-one). Then the
    negative-entropy / memory property MUST FAIL:
      - rho no longer injective; bits_lost(rho) > 0 (memory leaks);
      - reconstruction FAILS (record no longer recovers D / the inward fibers);
      - derived orientation of rho is no longer OUTWARD.
    If any of these still passed, "memory / negative entropy" would be a label, not a
    measured property. We assert lossy_record_kills_memory.
  FLIP 2 -- REVERSIBLE COMPRESSION: make phi injective (one-to-one). Then the
    positive-entropy property MUST FAIL:
      - phi no longer many-to-one; max_fiber(phi)==1; bits_lost(phi)==0;
      - derived orientation of phi is no longer INWARD (no collapse to summarize);
      - the record becomes redundant (phi alone already reconstructs D) -- the pair is
        no longer an irreversibility pair (both directions reversible).
    We assert reversible_compression_kills_positive_entropy.

  Both flips are run by MUTATING the map and RE-MEASURING (deepcopy carrier; no
  contamination of the serialized canonical object), then asserting the measured
  property changed in the demanded direction. The flips are the discriminator: the
  irreversibility pair is earned ONLY because breaking either direction breaks exactly
  the entropy face that direction carries.

HONEST CEILING:
  - classification = scratch_diagnostic ; promotion_allowed=false ;
    formal_admission_allowed=false.
  - claim_ceiling: this EARNS that, on a trivial finite carrier, an injective record
    map and a many-to-one compression map are MEASURED-opposite irreversibility faces
    (positive vs negative information change), and the record is the measured structural
    inverse-direction (right-section) of the compression's loss, with two control flips
    that break exactly the entropy face whose direction is broken. This is a
    finite-set INFORMATION-BOOKKEEPING separation. It is NOT physics, NOT dark
    matter/energy, NOT a temporal arrow, NOT thermodynamic entropy, NOT Axis0, NOT a
    manifold, NOT canonical. "negative entropy / inherited memory" is EARNED only as
    "an injective right-section that recovers what a measured many-to-one map
    destroyed", on integers.

Probe family M: (i) fiber-cardinality readout measure_map(f) over a finite map
  {domain_id -> image_id}; (ii) the injectivity / many-to-one / bits_lost readouts
  derived from it; (iii) the reconstruction readout (does rho recover D and the inward
  fibers); (iv) the derived-orientation readout from measured cardinality.
Constraint / structure: a finite carrier D of distinct events; an inward compression
  phi:D->I many-to-one; an outward record rho:D->R injective and a right-section of phi.
"""

from __future__ import annotations

import copy
import json
import math
import os
from typing import Any

# =====================================================================
# TOOL MANIFEST
# =====================================================================
# This is a finite-set INFORMATION-BOOKKEEPING receipt. Its load-bearing claim is a
# MEASURED irreversibility pair: a many-to-one compression (positive information change)
# and an injective record (negative information change) that is the compression's
# structural inverse-direction (right-section). It deliberately uses NO QIT / density /
# heavy-numeric tooling -- the maps are tiny finite dicts and the entropy bookkeeping is
# exact log2 arithmetic, so the separation stays auditable line by line. A numeric
# substrate would re-enter the proxy basin.

TOOL_MANIFEST = {
    "math": {
        "tried": True,
        "used": True,
        "reason": "math.log2 computes the exact information change bits_lost(f) = "
        "log2|domain| - log2|image| for each map. This is the load-bearing measured "
        "quantity that separates the positive-entropy (lossy, bits_lost>0) inward face "
        "from the negative-entropy (preserving, bits_lost==0) outward face. Without it "
        "the entropy orientation would be a label, not a measurement.",
    },
    "copy": {
        "tried": True,
        "used": True,
        "reason": "copy.deepcopy isolates the carrier maps before the control flips "
        "MUTATE them (lossy-record / reversible-compression), so the serialized "
        "canonical object is never contaminated. Load-bearing for the flip controls' "
        "honesty (no mutation leaks into the result JSON).",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "result-JSON serialization; supportive (serialization, not the claim).",
    },
    "numpy": {
        "tried": True,
        "used": False,
        "reason": "available but deliberately NOT used: the carrier is a tiny finite "
        "set of integer events and the entropy bookkeeping is exact log2 over integer "
        "fiber counts; pure Python keeps the irreversibility-pair measurement auditable. "
        "A numeric substrate would be decorative and re-enter the proxy basin.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is a measured information-bookkeeping separation by "
        "direct fiber counting and reconstruction, not a structural-impossibility "
        "(UNSAT) proof. No formal admission is claimed.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed: no density matrix / network / autograd carrier.",
    },
    "jax": {
        "tried": False,
        "used": False,
        "reason": "not needed: trivial finite carrier; no batched/exhaustive sweep.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Canon algebra artifact is consumed.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "math": "load_bearing",   # exact bits_lost separating the two entropy faces
    "copy": "load_bearing",   # uncontaminated control-flip mutation
    "json": "supportive",
    "numpy": None,
    "z3": None,
    "pytorch": None,
    "jax": None,
    "julia": None,
}


# =====================================================================
# THE FINITE CARRIER D -- distinct future-possibility events.
# Each event carries a (summary) coarse class and a (detail) fine tag. The INWARD
# compression keeps only the coarse class (many futures collapse to one summary =
# information lost). The OUTWARD record keeps the full distinct event (each preserved
# as itself = information preserved). The detail is exactly the distinction the
# compression discards, so the record is the structural inverse-direction of the loss.
# =====================================================================

# 8 distinct events grouped into 3 coarse classes. The class sizes (3,3,2) make the
# compression genuinely many-to-one (max_fiber = 3 > 1), so bits_lost > 0.
DOMAIN_EVENTS: dict[str, dict[str, Any]] = {
    "e0": {"coarse_class": "C0", "fine_tag": 0},
    "e1": {"coarse_class": "C0", "fine_tag": 1},
    "e2": {"coarse_class": "C0", "fine_tag": 2},
    "e3": {"coarse_class": "C1", "fine_tag": 0},
    "e4": {"coarse_class": "C1", "fine_tag": 1},
    "e5": {"coarse_class": "C1", "fine_tag": 2},
    "e6": {"coarse_class": "C2", "fine_tag": 0},
    "e7": {"coarse_class": "C2", "fine_tag": 1},
}


# =====================================================================
# The two directed maps on the SAME carrier D.
# =====================================================================

def inward_compression_map(domain_events: dict[str, dict[str, Any]]) -> dict[str, str]:
    """phi : D -> I. The INWARD (positive-entropy / dark-energy face) map: each event is
    compressed to its COARSE CLASS only. Many events share a class => many-to-one =>
    the fine detail is DESTROYED. From the image (a coarse class) you cannot tell which
    event produced it. This is the measured information-LOSING direction."""
    return {eid: ev["coarse_class"] for eid, ev in sorted(domain_events.items())}


def outward_record_map(domain_events: dict[str, dict[str, Any]]) -> dict[str, str]:
    """rho : D -> R. The OUTWARD (negative-entropy / dark-matter face) map: each event is
    preserved as its OWN distinct record image, qualified by BOTH the coarse class and
    the fine tag -- i.e. the full distinct identity of the event. Distinct events get
    distinct records => INJECTIVE => no information lost. This is the memory that keeps
    EXACTLY the distinction (the fine tag) the compression destroyed: it is therefore
    the structural inverse-direction of phi's collapse, not a vacuous id->id relabel."""
    return {
        eid: f"{ev['coarse_class']}#{ev['fine_tag']}"
        for eid, ev in sorted(domain_events.items())
    }


# =====================================================================
# THE MEASUREMENT (probe family M): fiber cardinality + exact information change.
# Nothing here reads an orientation label; the asymmetry is purely measured.
# =====================================================================

def measure_map(stratum_map: dict[str, str]) -> dict[str, Any]:
    """
    Measure a finite map {domain_id -> image_id}:
      domain_size     = |distinct domain ids|
      distinct_images = |distinct image ids|
      max_fiber       = largest preimage count (how many ids share one image)
      injective       = (distinct_images == domain_size) and domain_size >= 1
      many_to_one     = max_fiber > 1
      bits_lost       = log2(domain_size) - log2(distinct_images)  (>= 0; the EXACT
                        information change of the map: >0 iff lossy/positive-entropy,
                        ==0 iff injective/negative-entropy-preserving)
    """
    domain = list(stratum_map.keys())
    images = list(stratum_map.values())
    domain_size = len(set(domain))
    distinct_images = len(set(images))
    fibers: dict[str, int] = {}
    for img in images:
        fibers[img] = fibers.get(img, 0) + 1
    max_fiber = max(fibers.values()) if fibers else 0
    injective = (distinct_images == domain_size) and (domain_size >= 1)
    many_to_one = max_fiber > 1
    if domain_size >= 1 and distinct_images >= 1:
        bits_lost = math.log2(domain_size) - math.log2(distinct_images)
    else:
        bits_lost = 0.0
    # numerical hygiene: snap tiny negative round-off to 0; loss is non-negative.
    if -1e-12 < bits_lost < 0:
        bits_lost = 0.0
    return {
        "domain_size": domain_size,
        "distinct_images": distinct_images,
        "max_fiber": max_fiber,
        "injective": injective,
        "many_to_one": many_to_one,
        "fiber_counts": dict(sorted(fibers.items())),
        "bits_lost": bits_lost,
    }


def derive_orientation(measure: dict[str, Any]) -> str | None:
    """
    DERIVE orientation from the measured fiber cardinality (the ONLY place a string is
    produced, and solely from the measurement):
      INWARD  iff many_to_one (max_fiber > 1): the positive-entropy / compression face.
      OUTWARD iff injective: the negative-entropy / memory face.
    Returns None for the degenerate empty / neither case.
    """
    if measure["domain_size"] == 0:
        return None
    if measure["many_to_one"]:
        return "INWARD"
    if measure["injective"]:
        return "OUTWARD"
    return None


# =====================================================================
# THE RECONSTRUCTION (the inverse-direction proof): does the record recover what the
# compression forgot?
# =====================================================================

def reconstruct_from_record(record_map: dict[str, str]) -> dict[str, Any]:
    """Invert rho. A record is the structural inverse-direction of the loss iff it is
    invertible on the domain: rho^{-1} recovers each distinct domain id from its record
    image. record_reconstructs_domain is True iff every domain id is uniquely recovered
    (i.e. rho is injective, so the inverse is well-defined and total on the image)."""
    image_to_ids: dict[str, list[str]] = {}
    for eid, img in record_map.items():
        image_to_ids.setdefault(img, []).append(eid)
    # well-defined inverse iff every image has exactly one preimage
    well_defined = all(len(ids) == 1 for ids in image_to_ids.values())
    if well_defined:
        recovered = {img: ids[0] for img, ids in image_to_ids.items()}
        recovered_domain = set(recovered.values())
    else:
        recovered = {}
        recovered_domain = set()
    return {
        "record_inverse_well_defined": well_defined,
        "recovered_domain": sorted(recovered_domain),
        "record_reconstructs_domain": well_defined
        and recovered_domain == set(record_map.keys()),
    }


def fibers_recovered_from_record(
    compression_map: dict[str, str],
    record_map: dict[str, str],
) -> dict[str, Any]:
    """The PAIR test: given a compression image (a coarse class) and the record, can we
    recover the exact fiber phi^{-1}(image) -- i.e. the set of events that collapsed to
    that image? This is the operational statement that the record is phi's structural
    inverse-direction: it restores precisely the distinction phi destroyed.

    Procedure: invert the record to map each record image back to its unique domain id;
    then for each compression image, the recovered fiber = the domain ids (via the
    record) whose compression image equals it. Compare to the TRUE fiber.
    """
    rec = reconstruct_from_record(record_map)
    if not rec["record_inverse_well_defined"]:
        return {
            "all_inward_fibers_recovered": False,
            "reason": "record not invertible (rho not injective) -> cannot recover fibers",
        }
    # invert rho: record_image -> domain id
    rho_inv = {img: eid for eid, img in record_map.items()}
    # true fibers of phi
    true_fibers: dict[str, set[str]] = {}
    for eid, img in compression_map.items():
        true_fibers.setdefault(img, set()).add(eid)
    # recovered fibers: walk the record images, map back to domain ids via rho_inv,
    # then re-apply phi to bucket them -- the record alone re-identifies every event,
    # so re-bucketing under phi must reproduce the true fibers exactly.
    recovered_fibers: dict[str, set[str]] = {}
    for img_record, eid in rho_inv.items():
        comp_img = compression_map[eid]
        recovered_fibers.setdefault(comp_img, set()).add(eid)
    all_match = true_fibers == recovered_fibers
    return {
        "true_inward_fibers": {k: sorted(v) for k, v in sorted(true_fibers.items())},
        "recovered_inward_fibers": {k: sorted(v) for k, v in sorted(recovered_fibers.items())},
        "all_inward_fibers_recovered": all_match,
    }


def joint_pair_injective(
    compression_map: dict[str, str],
    record_map: dict[str, str],
) -> dict[str, Any]:
    """Is d |-> (phi(d), rho(d)) injective? (i.e. is the PAIR reversible). For a genuine
    irreversibility pair the record alone already makes it injective; we report the joint
    map's measured injectivity as an independent corroboration."""
    domain = sorted(set(compression_map.keys()) | set(record_map.keys()))
    pairs = {d: (compression_map.get(d), record_map.get(d)) for d in domain}
    distinct = len(set(pairs.values()))
    return {
        "joint_pair_injective": distinct == len(domain) and len(domain) >= 1,
        "joint_distinct_images": distinct,
        "joint_domain_size": len(domain),
    }


# =====================================================================
# THE IRREVERSIBILITY-PAIR TEST (HARD ACCEPTANCE, first-class).
# =====================================================================

def irreversibility_pair_test(domain_events: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Measure BOTH directions on the SAME carrier and assert they are opposite-
    orientation BY MEASUREMENT, with the record proven to be phi's structural inverse-
    direction. Returns a fully measured receipt; irreversibility_pair_earned is the
    conjunction of (A) inward many-to-one, (B) outward injective, (C) record
    reconstructs D and recovers every inward fiber, (D) opposite derived orientation."""
    phi = inward_compression_map(domain_events)
    rho = outward_record_map(domain_events)

    measure_phi = measure_map(phi)
    measure_rho = measure_map(rho)
    orient_phi = derive_orientation(measure_phi)
    orient_rho = derive_orientation(measure_rho)

    # (A) inward = many-to-one => information LOST => positive entropy
    inward_lossy = measure_phi["many_to_one"] and measure_phi["bits_lost"] > 0
    # (B) outward = injective => information PRESERVED => negative-entropy/memory
    outward_preserving = measure_rho["injective"] and measure_phi["bits_lost"] >= 0 and measure_rho["bits_lost"] == 0
    # (C) record is the structural inverse-direction of phi's loss
    recon = reconstruct_from_record(rho)
    fibers = fibers_recovered_from_record(phi, rho)
    joint = joint_pair_injective(phi, rho)
    record_is_inverse_direction = (
        recon["record_reconstructs_domain"]
        and fibers["all_inward_fibers_recovered"]
        and joint["joint_pair_injective"]
    )
    # (D) opposite orientation by measurement (no stored label)
    opposite_by_measurement = (
        orient_phi == "INWARD" and orient_rho == "OUTWARD" and orient_phi != orient_rho
    )

    earned = inward_lossy and outward_preserving and record_is_inverse_direction and opposite_by_measurement

    return {
        "inward_compression_map": phi,
        "outward_record_map": rho,
        "measure_inward": measure_phi,
        "measure_outward": measure_rho,
        "derived_orientation_inward": orient_phi,
        "derived_orientation_outward": orient_rho,
        # (A)
        "inward_many_to_one": bool(measure_phi["many_to_one"]),
        "inward_max_fiber": measure_phi["max_fiber"],
        "inward_bits_lost": measure_phi["bits_lost"],
        "inward_is_positive_entropy_lossy": bool(inward_lossy),
        # (B)
        "outward_injective": bool(measure_rho["injective"]),
        "outward_bits_lost": measure_rho["bits_lost"],
        "outward_is_negative_entropy_preserving": bool(outward_preserving),
        # (C)
        "record_reconstructs_domain": bool(recon["record_reconstructs_domain"]),
        "all_inward_fibers_recovered": bool(fibers["all_inward_fibers_recovered"]),
        "joint_pair_injective": bool(joint["joint_pair_injective"]),
        "record_is_structural_inverse_direction": bool(record_is_inverse_direction),
        "reconstruction_detail": recon,
        "fibers_detail": fibers,
        "joint_detail": joint,
        # (D)
        "opposite_orientation_by_measurement": bool(opposite_by_measurement),
        # verdict
        "irreversibility_pair_earned": bool(earned),
        "honest_message": (
            "EARNED: the outward record is a MEASURED injective memory (bits_lost==0) "
            "that reconstructs the domain and every fiber the MEASURED many-to-one "
            "inward compression (bits_lost>0) destroyed; opposite orientation is "
            "derived from the measured cardinalities, not labeled"
            if earned
            else "NOT EARNED: the irreversibility pair failed a measured clause "
            "(inward not lossy / outward not preserving / record not an inverse / "
            "orientations not opposite by measurement)"
        ),
    }


# =====================================================================
# CONTROL FLIP 1 -- LOSSY RECORD: collapse rho many-to-one. The negative-entropy /
# memory property MUST FAIL.
# =====================================================================

def lossy_record_control(domain_events: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Mutate the record so distinct events share an image (collapse to the COARSE class
    only -- the same lossy summary the compression already keeps). Re-measure: the record
    must NO LONGER be injective, bits_lost(rho)>0, reconstruction must FAIL, and the
    derived orientation must no longer be OUTWARD. lossy_record_kills_memory is True iff
    the memory property broke in EVERY one of those measured senses."""
    safe = copy.deepcopy(domain_events)  # never touch the canonical carrier
    phi = inward_compression_map(safe)
    # lossy record: keep only the coarse class -> many-to-one (identical to phi here)
    rho_lossy = {eid: ev["coarse_class"] for eid, ev in sorted(safe.items())}

    measure_lossy = measure_map(rho_lossy)
    orient_lossy = derive_orientation(measure_lossy)
    recon = reconstruct_from_record(rho_lossy)
    fibers = fibers_recovered_from_record(phi, rho_lossy)

    no_longer_injective = not measure_lossy["injective"]
    memory_leaks = measure_lossy["bits_lost"] > 0
    reconstruction_fails = not (
        recon["record_reconstructs_domain"] and fibers["all_inward_fibers_recovered"]
    )
    orientation_not_outward = orient_lossy != "OUTWARD"

    killed = no_longer_injective and memory_leaks and reconstruction_fails and orientation_not_outward
    return {
        "mechanism": "collapse the record to the coarse class only (many-to-one lossy record)",
        "lossy_record_map": rho_lossy,
        "measure_lossy_record": measure_lossy,
        "derived_orientation_lossy_record": orient_lossy,
        "no_longer_injective": bool(no_longer_injective),
        "memory_leaks_bits_lost_gt_0": bool(memory_leaks),
        "reconstruction_fails": bool(reconstruction_fails),
        "derived_orientation_not_outward": bool(orientation_not_outward),
        "lossy_record_kills_memory": bool(killed),
    }


# =====================================================================
# CONTROL FLIP 2 -- REVERSIBLE COMPRESSION: make phi injective. The positive-entropy
# property MUST FAIL.
# =====================================================================

def reversible_compression_control(domain_events: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Mutate the compression so each event maps to a DISTINCT image (one-to-one,
    reversible -- it now keeps the fine tag too, so nothing collapses). Re-measure: phi
    must NO LONGER be many-to-one, max_fiber==1, bits_lost(phi)==0, the derived
    orientation must no longer be INWARD, and the record becomes redundant (phi alone
    reconstructs the domain) -- so the PAIR is no longer an irreversibility pair.
    reversible_compression_kills_positive_entropy is True iff the positive-entropy face
    broke in every measured sense."""
    safe = copy.deepcopy(domain_events)
    # reversible compression: keep coarse class AND fine tag -> injective
    phi_rev = {
        eid: f"{ev['coarse_class']}@{ev['fine_tag']}"
        for eid, ev in sorted(safe.items())
    }

    measure_rev = measure_map(phi_rev)
    orient_rev = derive_orientation(measure_rev)
    recon_via_phi = reconstruct_from_record(phi_rev)  # phi now invertible itself

    no_longer_many_to_one = not measure_rev["many_to_one"]
    max_fiber_one = measure_rev["max_fiber"] == 1
    no_information_lost = measure_rev["bits_lost"] == 0
    orientation_not_inward = orient_rev != "INWARD"
    record_now_redundant = recon_via_phi["record_reconstructs_domain"]  # phi reconstructs D itself

    killed = (
        no_longer_many_to_one
        and max_fiber_one
        and no_information_lost
        and orientation_not_inward
        and record_now_redundant
    )
    return {
        "mechanism": "make compression keep the fine tag too (injective / reversible compression)",
        "reversible_compression_map": phi_rev,
        "measure_reversible_compression": measure_rev,
        "derived_orientation_reversible_compression": orient_rev,
        "no_longer_many_to_one": bool(no_longer_many_to_one),
        "max_fiber_is_one": bool(max_fiber_one),
        "no_information_lost_bits_lost_eq_0": bool(no_information_lost),
        "derived_orientation_not_inward": bool(orientation_not_inward),
        "record_now_redundant_phi_reconstructs_domain": bool(record_now_redundant),
        "reversible_compression_kills_positive_entropy": bool(killed),
    }


# =====================================================================
# NEGATIVE / TRAP controls retained for hygiene.
# =====================================================================

def carrier_uncontaminated_after_controls() -> dict[str, Any]:
    """Both control flips deepcopy the carrier; confirm the module global DOMAIN_EVENTS
    is byte-identical to the canonical carrier after running both flips (no contamination
    leaks into the serialized object -- the v1 b3.a=6 class of bug)."""
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
    _ = lossy_record_control(DOMAIN_EVENTS)
    _ = reversible_compression_control(DOMAIN_EVENTS)
    return {
        "module_carrier_uncontaminated": DOMAIN_EVENTS == canonical,
    }


# =====================================================================
# INVARIANTS
# =====================================================================

def check_invariants(test: dict[str, Any]) -> dict[str, Any]:
    """Named invariant -> bool. The validator re-derives and asserts these."""
    return {
        # the carrier maps exist and are over the same finite domain
        "maps_share_domain": (
            set(test["inward_compression_map"].keys())
            == set(test["outward_record_map"].keys())
        ),
        # the two maps are genuinely different maps (not the same dict)
        "inward_and_outward_are_distinct_maps": (
            test["inward_compression_map"] != test["outward_record_map"]
        ),
        # (A) inward face MEASURED lossy / positive-entropy
        "INWARD_is_many_to_one_measured": test["inward_many_to_one"],
        "INWARD_max_fiber_gt_1": test["inward_max_fiber"] > 1,
        "INWARD_bits_lost_gt_0": test["inward_bits_lost"] > 0,
        # (B) outward face MEASURED injective / negative-entropy
        "OUTWARD_is_injective_measured": test["outward_injective"],
        "OUTWARD_bits_lost_eq_0": test["outward_bits_lost"] == 0,
        # (C) record is the structural inverse-direction of the loss
        "record_reconstructs_domain": test["record_reconstructs_domain"],
        "record_recovers_every_inward_fiber": test["all_inward_fibers_recovered"],
        "joint_pair_injective": test["joint_pair_injective"],
        "record_is_structural_inverse_direction": test["record_is_structural_inverse_direction"],
        # (D) opposite orientation derived from measurement (no stored label)
        "orientations_opposite_by_measurement": test["opposite_orientation_by_measurement"],
        # the verdict
        "IRREVERSIBILITY_PAIR_EARNED": test["irreversibility_pair_earned"],
    }


# =====================================================================
# BUILD RESULT
# =====================================================================

def build_result() -> dict[str, Any]:
    test = irreversibility_pair_test(DOMAIN_EVENTS)
    invariants = check_invariants(test)
    all_invariants_hold = all(invariants.values())

    flip1 = lossy_record_control(DOMAIN_EVENTS)
    flip2 = reversible_compression_control(DOMAIN_EVENTS)
    contamination = carrier_uncontaminated_after_controls()

    lossy_kills = flip1["lossy_record_kills_memory"]
    reversible_kills = flip2["reversible_compression_kills_positive_entropy"]
    both_flips_discriminate = lossy_kills and reversible_kills

    all_pass = (
        all_invariants_hold
        and test["irreversibility_pair_earned"]
        and both_flips_discriminate
        and contamination["module_carrier_uncontaminated"]
    )

    result = {
        "name": "rpf_outward_record_memory_v0",
        "object_name": "OutwardRecordMemory_IrreversibilityPair",
        "probe_family": "M_fiber_cardinality_plus_bits_lost_plus_reconstruction_plus_derived_orientation",
        "structure": (
            "finite carrier D of distinct events; inward compression phi:D->coarse_class "
            "(many-to-one, lossy); outward record rho:D->full_event_identity (injective, "
            "the structural inverse-direction / right-section recovering phi's loss)"
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,

        # ---- the carrier ----
        "domain_events": copy.deepcopy(DOMAIN_EVENTS),
        "domain_size": len(DOMAIN_EVENTS),

        # ---- THE IRREVERSIBILITY-PAIR TEST (HARD ACCEPTANCE) ----
        "IRREVERSIBILITY_PAIR_TEST": {
            "inward_compression_map": test["inward_compression_map"],
            "outward_record_map": test["outward_record_map"],
            "measure_inward": test["measure_inward"],
            "measure_outward": test["measure_outward"],
            "derived_orientation_inward": test["derived_orientation_inward"],
            "derived_orientation_outward": test["derived_orientation_outward"],
            # the measured fiber cardinalities BOTH directions (the demand):
            "inward_max_fiber": test["inward_max_fiber"],
            "inward_bits_lost": test["inward_bits_lost"],
            "outward_max_fiber": test["measure_outward"]["max_fiber"],
            "outward_bits_lost": test["outward_bits_lost"],
            # the measured properties:
            "inward_is_positive_entropy_lossy": test["inward_is_positive_entropy_lossy"],
            "outward_is_negative_entropy_preserving": test["outward_is_negative_entropy_preserving"],
            "record_is_structural_inverse_direction": test["record_is_structural_inverse_direction"],
            "opposite_orientation_by_measurement": test["opposite_orientation_by_measurement"],
            "irreversibility_pair_earned": test["irreversibility_pair_earned"],
            "honest_message": test["honest_message"],
            "reconstruction_detail": test["reconstruction_detail"],
            "fibers_detail": test["fibers_detail"],
            "joint_detail": test["joint_detail"],
        },
        "irreversibility_pair_earned": test["irreversibility_pair_earned"],

        # ---- HONEST CAVEAT on what the reconstruction/fiber test certifies ----
        # The fiber-recovery test certifies that the record is AN injective right-section
        # of phi (any injective record, including a vacuous id->id one, re-identifies each
        # event and hence re-buckets phi's true fibers). It does NOT, by itself, certify
        # that THIS record's specific class#fine_tag encoding is privileged over the
        # vacuous id->id record rpf_v3 used: both are injective. What makes this an
        # irreversibility PAIR -- and the load-bearing improvement over v3 -- is that the
        # record is MEASURED opposite to a MEASURED many-to-one information-LOSS map phi
        # on the SAME carrier (v3 had no complementary measured-loss map for its record to
        # be the inverse-direction OF), and that the TWO CONTROL FLIPS each break exactly
        # the entropy face whose direction is broken. The carried distinction (fine_tag)
        # is exactly what phi destroys, so the record content is non-vacuous AS A PAIR
        # with phi; but the injectivity, not the encoding, is the certified property.
        "honest_caveat_reconstruction_certifies_injectivity_not_encoding": (
            "the record_is_structural_inverse_direction test certifies the record is an "
            "injective right-section of phi (a vacuous id->id record would also pass it); "
            "the load-bearing object is the MEASURED pair (lossy phi + injective rho on "
            "one carrier) and the two control flips, not the specific record encoding"
        ),

        # ---- THE TWO DISCRIMINATING CONTROL FLIPS (HARD ACCEPTANCE) ----
        "CONTROL_FLIP_1_lossy_record": flip1,
        "CONTROL_FLIP_2_reversible_compression": flip2,
        "lossy_record_kills_memory": lossy_kills,
        "reversible_compression_kills_positive_entropy": reversible_kills,
        "both_flips_discriminate": both_flips_discriminate,

        # ---- contamination hygiene ----
        "carrier_uncontaminated_after_controls": contamination["module_carrier_uncontaminated"],

        "invariants": invariants,
        "all_invariants_hold": all_invariants_hold,

        # ---- honest self-assessment ----
        "honest_self_assessment": (
            "EARNED on this carrier, in a PRECISE and LIMITED sense: 'inherited memory / "
            "negative entropy' is earned only as 'an injective right-section rho that "
            "MEASURABLY recovers the domain and every fiber that a MEASURED many-to-one "
            "compression phi destroyed (inward bits_lost=%s>0, outward bits_lost=%s==0), "
            "with opposite orientation DERIVED from the measured fiber cardinalities, "
            "and with both discriminating flips firing (collapsing rho kills the memory "
            "property; making phi injective kills the positive-entropy property).' This "
            "is finite-set information bookkeeping. It is NOT thermodynamic entropy, NOT "
            "physical dark matter/energy, NOT a temporal arrow, NOT a demonstration that "
            "this carrier IS the owner model's dark sector. The owner-model words "
            "(negative entropy, preserved information, inherited memory, irreversibility "
            "pair) are the OBJECT SOURCE, held as target/excavation, not admitted physics."
        ) % (test["inward_bits_lost"], test["outward_bits_lost"]),

        # ---- honest ceiling ----
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "EARNS only a finite-set INFORMATION-BOOKKEEPING irreversibility pair: a "
            "measured many-to-one compression (positive bits_lost) and a measured "
            "injective record (zero bits_lost) that is the structural inverse-direction "
            "(right-section) recovering the compression's destroyed fibers, with two "
            "control flips that each break exactly the entropy face whose direction is "
            "broken. NOT physics, NOT dark matter/energy, NOT thermodynamic entropy, NOT "
            "a temporal arrow, NOT Axis0, NOT a manifold, NOT canonical."
        ),
        "blocked_downstream_consumers": [
            "Axis0 claim",
            "flux claim",
            "physics / dark-sector claim",
            "thermodynamic entropy claim",
            "temporal-arrow claim",
            "formal manifold admission",
            "claim that this trivial carrier IS the owner model's outward record / dark matter",
            "claim that bits_lost is physical entropy",
        ],
        "all_pass": all_pass,
        "criteria_checked": sorted(invariants.keys()),
    }
    return result


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(SIM_DIR, "results", "rpf_outward_record_memory_v0_results.json")


def main() -> int:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "ok": result["all_pass"],
        "irreversibility_pair_earned": result["irreversibility_pair_earned"],
        "inward_max_fiber": result["IRREVERSIBILITY_PAIR_TEST"]["inward_max_fiber"],
        "inward_bits_lost": result["IRREVERSIBILITY_PAIR_TEST"]["inward_bits_lost"],
        "outward_max_fiber": result["IRREVERSIBILITY_PAIR_TEST"]["outward_max_fiber"],
        "outward_bits_lost": result["IRREVERSIBILITY_PAIR_TEST"]["outward_bits_lost"],
        "opposite_orientation_by_measurement": result["IRREVERSIBILITY_PAIR_TEST"]["opposite_orientation_by_measurement"],
        "record_is_structural_inverse_direction": result["IRREVERSIBILITY_PAIR_TEST"]["record_is_structural_inverse_direction"],
        "lossy_record_kills_memory": result["lossy_record_kills_memory"],
        "reversible_compression_kills_positive_entropy": result["reversible_compression_kills_positive_entropy"],
        "all_invariants_hold": result["all_invariants_hold"],
        "result_path": RESULT_PATH,
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
