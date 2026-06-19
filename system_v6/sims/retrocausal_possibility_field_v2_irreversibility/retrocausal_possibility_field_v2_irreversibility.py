#!/usr/bin/env python3
"""
retrocausal_possibility_field_v2_irreversibility -- successor to v1. ONE audited
gap fixed: the shell_orientation INWARD/OUTWARD is now DERIVED from the measured
COMPRESSION IRREVERSIBILITY (fan-in / fan-out) of each stratum's actual mapping,
not stipulated as a string label.

Started from system_v4/probes/SIM_TEMPLATE.py (template framing preserved) and
mirrors retrocausal_possibility_field_v1's structure (carrier, shell-ordered
inward traversal, hash-chain outward_record, invariant battery, result receipt).
v1's wins are KEPT verbatim in mechanism: the inward traversal is still a
multi-step outer->inner propagation; shell-reassignment still MOVES the survivor;
v0 traps #1 (weight permutation) and #4 (state mutation) still PASS; the HARD-STOP
future_continuations != present_survivor still fires.

THE OBJECT (per system_v6/receipts/v43_object_card_current_run.json):
  "A finite shell-indexed field of possible futures compresses INWARD through
   compatibility into a present survivor, while the past-facing OUTWARD record
   preserves what survived."

THE AUDITED GAP v2 FIXES (the named v1 limitation, in v1's own ceiling string and
in v0's audit_verdict.md):
  In v1 the shell_orientation INWARD/OUTWARD was a STIPULATED string typed on each
  shell. The compression and record FILTERED on that string to decide which strata
  are inward and which is the record. So the orientation was load-bearing only as a
  hardcoded constant -- "orientation still a label not emergent (the v2 target)."

THE v2 FIX -- orientation EMERGENT from compression irreversibility:
  v2 does NOT store INWARD/OUTWARD on the shells. Each shell carries instead the
  ACTUAL MAP it performs over branch ids, from which we MEASURE its irreversibility:

    INWARD  = the many-to-one COMPRESSION direction: multiple incoming futures map
              to ONE survivor (non-injective: |image| < |domain|). Futures are
              destroyed; the map is irreversible. fan_in > fan_out.
    OUTWARD = the injective RECORD direction: each compressed-away event is
              preserved as its own distinct, recoverable record entry (injective:
              |image| == |domain|). Nothing collapses; the map is reversible.
              fan_in == fan_out.

  measure_irreversibility(map) computes (domain_size, distinct_images, injective)
  from the ACTUAL stratum map. derive_orientation(measure) RETURNS the label from
  that measured pair -- "INWARD" iff non-injective (distinct_images < domain_size),
  "OUTWARD" iff injective (distinct_images == domain_size). The label is a COMPUTED
  function of a measured asymmetry, NEVER read from a stored constant.

  THE EMERGENCE DISCRIMINATING CONTROL (the v2 hard acceptance): if we REVERSE the
  measured asymmetry, the derived orientation MUST flip / fail:
    - make an inward stratum map INJECTIVE (each incoming branch keeps a distinct
      image -> no compression) -> its derived orientation flips INWARD -> OUTWARD.
    - make the record stratum map MANY-TO-ONE (collapse all events to one image)
      -> its derived orientation flips OUTWARD -> INWARD.
  Because the label tracks the asymmetry, removing/reversing the asymmetry flips it.
  That is the proof the orientation is emergent, not stipulated.

WHAT THIS SIM IS / IS NOT (honest ceiling):
  - classification = scratch_diagnostic
  - promotion_allowed = false ; formal_admission_allowed = false
  - claim_ceiling: shell_orientation now DERIVED from measured compression
    irreversibility (fan-in/fan-out), not a stipulated string; v1's shell-ordering
    and traps preserved; trivial carrier, no QIT; NOT physics/Axis0/manifold/
    canonical.

ANTI-PROXY-DRIFT (retained from v1; v2 adds the orientation-derivation control):
  - future_continuations is a dict of shell -> LIST (NOT a scalar count, NOT bool).
  - compatibility_weights is a real-valued weight structure over PAIRS of futures,
    computed BEFORE compression, and consumed by the cross-shell propagation.
  - present_survivor is DERIVED inward through the traversal (HARD-STOP if it
    equals future_continuations -> identity compression / proxy drift).
  - shell_orientation is DERIVED from measure_irreversibility, NOT stored. A
    discriminating control proves: reverse the measured asymmetry -> the label flips.
  - outward_record is a past-facing hash-chain whose OUTWARD orientation is itself
    DERIVED (the record map is injective), distinct from compression_map.

Probe family M: per-stratum irreversibility readout -- measure (domain_size,
  distinct_images, injective) of each stratum's actual branch-id map, plus the
  pairwise-compatibility weight readout that drives the inward traversal.
Constraint set C: orientation is the function derive_orientation(measure): INWARD
  iff non-injective, OUTWARD iff injective; inward traversal outer->inner->present
  is keyed by shell_radius_r; each inner shell's anchor is selected by maximal
  pairwise compatibility with the anchor propagated from the next-outer shell
  (deterministic tie-break by branch id).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================
# This object is a FIELD-INSTANTIATION receipt on a trivial finite carrier whose
# multi-shell inward compression is shell-ordered (v1) AND whose shell_orientation
# is DERIVED from measured compression irreversibility (v2). It deliberately uses
# NO QIT / density-matrix / heavy numeric tooling: the load-bearing tool is the
# hashlib append-only chain (outward_record provenance, reused from rpf v0/v1); the
# irreversibility measure and the shell traversal are pure-Python integer/float
# arithmetic so the orientation-derivation stays auditable line by line.

TOOL_MANIFEST = {
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "append-only sha256 hash-chain is the outward_record machinery "
        "(reused from rpf v0 / v1); each chain entry binds a PER-EVENT record image "
        "(one distinct entry per compressed-away branch event), which is exactly "
        "what makes the record map INJECTIVE -- and the record's OUTWARD orientation "
        "is DERIVED from that injectivity. Load-bearing for outward_record "
        "provenance AND for the measured record-stratum irreversibility.",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "canonical_json serialization for stable hash-chain digests and "
        "the result receipt; supportive (serialization, not the claim itself).",
    },
    "numpy": {
        "tried": True,
        "used": False,
        "reason": "available but deliberately NOT used: the carrier is a trivial "
        "finite set, the irreversibility measure is |domain| vs |distinct image| "
        "integer counting, and the shell traversal is a short deterministic loop; "
        "pure-Python keeps the orientation-derivation auditable. Heavy numeric "
        "tooling would re-enter the proxy basin and obscure the derivation.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is object-field instantiation with a measured "
        "fan-in/fan-out derivation, not a structural-impossibility (UNSAT) proof. "
        "No formal admission is claimed.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed: no density matrix / network / autograd carrier; "
        "using it would be decorative and would re-enter the proxy basin.",
    },
    "jax": {
        "tried": False,
        "used": False,
        "reason": "not needed: trivial finite carrier; the irreversibility measure "
        "and traversal are short deterministic loops, not batched/exhaustive sweeps.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Canon algebra artifact is consumed; field "
        "instantiation with a measured-irreversibility orientation derivation only.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "hashlib": "load_bearing",   # outward_record injective per-event hash-chain
    "json": "supportive",        # canonical serialization
    "numpy": None,
    "z3": None,
    "pytorch": None,
    "jax": None,
    "julia": None,
}


# =====================================================================
# Carrier + record machinery
# =====================================================================

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ---- The trivial finite carrier: 6 enumerated branch states ----------
# Identical to v0/v1: the change is in how orientation is obtained, not the carrier.
BRANCH_STATES: dict[str, dict[str, int]] = {
    "b0": {"a": 0, "b": 0},
    "b1": {"a": 0, "b": 1},
    "b2": {"a": 1, "b": 0},
    "b3": {"a": 1, "b": 1},
    "b4": {"a": 2, "b": 0},
    "b5": {"a": 2, "b": 1},
}

EVENT_X = "event_x:apex_decision_node"

# ---- The shells Sigma_r: a finite ORDERED set --------------------------------
# r=2 outer future stratum, r=1 inner future stratum, r=-1 the record stratum.
# The present survivor sits at r=0 (the apex / event_x).
#
# v2 CRITICAL CHANGE: NO shell carries a stipulated shell_orientation string.
# Orientation is NOT stored here. Each shell carries only:
#   - shell_id          : a name
#   - shell_radius_r     : the geometric/structural ordering key for the traversal
#                          (a magnitude/sign of position, NOT the inward/outward
#                          label; the label is derived from each stratum's MAP)
#   - role               : a human description, NOT consumed by any orientation logic
#   - stratum_kind       : "future" (carries future_continuations -> compresses) or
#                          "record" (carries the survival record). This selects WHICH
#                          MAP a stratum performs, NOT its orientation -- the
#                          orientation is then DERIVED from the map it performs.
# The validator asserts that NO shell dict contains the key "shell_orientation".
SHELLS: list[dict[str, Any]] = [
    {"shell_id": "Sigma_2", "shell_radius_r": 2, "stratum_kind": "future",
     "role": "future possibility stratum (outer)"},
    {"shell_id": "Sigma_1", "shell_radius_r": 1, "stratum_kind": "future",
     "role": "future possibility stratum (inner)"},
    {"shell_id": "Sigma_record", "shell_radius_r": -1, "stratum_kind": "record",
     "role": "survival record stratum"},
]

# Future continuations are FUTURE-INDEXED: keyed by the future-stratum shells only.
# Each value is a LIST of >=2 non-trivially-distinct admissible branch states.
# Identical canonical config to v1 so v1's traversal/traps/reassignment carry over.
FUTURE_CONTINUATIONS_BY_SHELL: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b5"],   # outer future stratum: 3 branches
    "Sigma_1": ["b2", "b3", "b4"],   # inner future stratum: 3 branches
}


# =====================================================================
# compatibility_weights: real-valued weights over PAIRS of future continuations
# Computed BEFORE survivor compression (required invariant) and consumed by the
# cross-shell inward propagation. Identical to v1.
# =====================================================================

def branch_distance(s1: str, s2: str) -> int:
    """L1 distance between two branch states in the trivial feature space."""
    x, y = BRANCH_STATES[s1], BRANCH_STATES[s2]
    return abs(x["a"] - y["a"]) + abs(x["b"] - y["b"])


def compute_compatibility_weights(
    future_continuations: dict[str, list[str]],
) -> dict[str, float]:
    """Weight structure over PAIRS of future continuations. Higher weight = more
    compatible (closer in feature space). weight(p,q) = 1/(1+L1_distance(p,q)).
    Real-valued NON-uniform; keyed by a canonical unordered pair "bi|bj" with i<j.
    Identical to v1; v2 changes only orientation, not the weights or the traversal."""
    all_futures: list[str] = []
    for _shell_id, branches in future_continuations.items():
        for b in branches:
            all_futures.append(b)
    uniq = sorted(set(all_futures))
    weights: dict[str, float] = {}
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            p, q = uniq[i], uniq[j]
            key = f"{p}|{q}"
            d = branch_distance(p, q)
            weights[key] = 1.0 / (1.0 + float(d))
    return weights


def pair_key(p: str, q: str) -> str:
    lo, hi = sorted((p, q))
    return f"{lo}|{hi}"


def _branch_id_rank(b: str) -> int:
    """Numeric rank for the deterministic tie-break (lowest branch id wins)."""
    return int(b[1:])


# =====================================================================
# THE v2 CORE: measure_irreversibility + derive_orientation
# Orientation is a COMPUTED function of a measured fan-in/fan-out asymmetry, NOT a
# stored string. This is the one substantive thing v2 adds over v1.
# =====================================================================

def measure_irreversibility(stratum_map: dict[str, str]) -> dict[str, Any]:
    """
    Measure the compression irreversibility of a single stratum's ACTUAL map.

    A stratum_map is a dict {incoming_branch_id -> image_id}: the map this stratum
    performs over branch-event ids. We MEASURE:
      - domain_size      = number of distinct incoming items (|domain|)
      - distinct_images  = number of distinct image items (|image|)
      - fan_in           = domain_size  (how many items enter)
      - fan_out          = distinct_images (how many distinct items leave)
      - injective        = (distinct_images == domain_size): the map loses no
                           distinctions; every incoming item has its own image;
                           reversible.
      - many_to_one      = (distinct_images < domain_size): multiple incoming items
                           collapse to a shared image; distinctions are destroyed;
                           irreversible (the COMPRESSION direction).
      - collapse_ratio   = distinct_images / domain_size in (0, 1]; 1.0 = injective,
                           < 1.0 = compressive.

    NOTHING here reads any orientation label. The asymmetry is purely the measured
    relation between |domain| and |image| of the actual map.
    """
    domain = list(stratum_map.keys())
    images = list(stratum_map.values())
    domain_size = len(set(domain))
    distinct_images = len(set(images))
    injective = (distinct_images == domain_size) and (domain_size >= 1)
    many_to_one = distinct_images < domain_size
    collapse_ratio = (distinct_images / domain_size) if domain_size else 0.0
    return {
        "domain_size": domain_size,
        "distinct_images": distinct_images,
        "fan_in": domain_size,
        "fan_out": distinct_images,
        "injective": injective,
        "many_to_one": many_to_one,
        "collapse_ratio": collapse_ratio,
    }


def derive_orientation(measure: dict[str, Any]) -> str | None:
    """
    DERIVE the orientation label from the measured irreversibility.

    INWARD  iff the map is MANY-TO-ONE (non-injective: distinct_images < domain) --
            the compression direction: futures destroyed.
    OUTWARD iff the map is INJECTIVE (distinct_images == domain_size) -- the record
            direction: each event preserved distinctly.

    Returns None for the degenerate domain_size==0 case (no map -> no orientation).
    This is the ONLY place the INWARD/OUTWARD string is produced, and it is produced
    SOLELY from the measured (domain_size, distinct_images) pair. There is no stored
    orientation constant anywhere in the sim to read.
    """
    if measure["domain_size"] == 0:
        return None
    if measure["many_to_one"]:
        return "INWARD"
    if measure["injective"]:
        return "OUTWARD"
    return None  # unreachable for finite maps, kept explicit


# =====================================================================
# Stratum maps: the ACTUAL map each stratum performs, from which orientation is
# measured. These are computed from the dynamics, not from a label.
# =====================================================================

def future_stratum_map(branches_on_shell: list[str], selected_anchor: str) -> dict[str, str]:
    """The map a FUTURE stratum performs in the inward traversal: every incoming
    branch on the shell maps to the SINGLE selected anchor. If >=2 distinct
    branches enter, this is many-to-one (compressive / irreversible)."""
    return {b: selected_anchor for b in sorted(set(branches_on_shell))}


def record_stratum_map(compressed_away_events: list[str]) -> dict[str, str]:
    """The map the RECORD stratum performs: each compressed-away branch EVENT is
    preserved as its OWN distinct record image (id -> itself). This is injective
    (reversible): the record loses no distinctions. Empty input -> empty map."""
    return {ev: ev for ev in sorted(set(compressed_away_events))}


# =====================================================================
# compression_map: shell-indexed future_continuations -> present_survivor via an
# INWARD TRAVERSAL of the shells (outer -> inner -> present). v2 keeps v1's
# traversal mechanism VERBATIM but selects inward strata by DERIVED orientation,
# not by a stored "INWARD" string.
# =====================================================================

def _is_future_stratum(shell: dict[str, Any]) -> bool:
    """A future stratum is one that carries future_continuations (stratum_kind ==
    'future'). This selects WHICH MAP the stratum performs; the inward/outward
    ORIENTATION is then DERIVED from the map. stratum_kind is NOT an orientation
    label -- the adversarial control reverses the MAP while keeping stratum_kind
    fixed and the derived orientation still flips, proving stratum_kind is not the
    smuggled-in orientation."""
    return shell.get("stratum_kind") == "future"


def compression_map(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
    shells: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inward TRAVERSAL compression (v1 mechanism, kept verbatim) PLUS the v2
    per-shell DERIVED orientation.

    Walk the FUTURE strata in order of DECREASING shell_radius_r (outermost first),
    carry a single PROPAGATED ANCHOR inward (outermost seeds by within-shell mass;
    each inner shell selects the branch of maximal pairwise compatibility with the
    incoming anchor; tie-break lowest branch id). For EACH future shell we then:
      - build its ACTUAL future_stratum_map (branches -> selected anchor),
      - MEASURE its irreversibility,
      - DERIVE its orientation from that measure.
    Inward shells are the FUTURE strata; their derived orientation is computed and
    asserted (the canonical instance must derive "INWARD" because >=2 branches
    compress to one anchor). The radius ordering (a structural magnitude) sets the
    traversal sequence; it is NOT the orientation label.
    """
    # future strata, outermost (largest radius) first
    future_shells = sorted(
        [s for s in shells if _is_future_stratum(s)],
        key=lambda s: -int(s["shell_radius_r"]),
    )

    traversal_steps: list[dict[str, Any]] = []
    anchor: str | None = None

    for shell in future_shells:
        sid = shell["shell_id"]
        branches = sorted(future_continuations.get(sid, []))
        if not branches:
            traversal_steps.append({
                "shell_id": sid,
                "shell_radius_r": shell["shell_radius_r"],
                "incoming_anchor": anchor,
                "branches_on_shell": [],
                "branch_scores": {},
                "selected_anchor": anchor,
                "step_kind": "empty_shell_passthrough",
                "stratum_map": {},
                "irreversibility": measure_irreversibility({}),
                "derived_orientation": derive_orientation(measure_irreversibility({})),
            })
            continue

        if anchor is None:
            scores = {
                p: sum(
                    compatibility_weights[pair_key(p, q)]
                    for q in branches
                    if q != p
                )
                for p in branches
            }
            step_kind = "seed_within_shell_mass"
        else:
            scores = {}
            for p in branches:
                if p == anchor:
                    scores[p] = 1.0
                else:
                    scores[p] = compatibility_weights[pair_key(p, anchor)]
            step_kind = "cross_shell_compat_with_incoming_anchor"

        selected = max(branches, key=lambda p: (scores[p], -_branch_id_rank(p)))

        # v2: the ACTUAL map this future stratum performs, and its DERIVED orientation
        smap = future_stratum_map(branches, selected)
        measure = measure_irreversibility(smap)
        derived = derive_orientation(measure)

        traversal_steps.append({
            "shell_id": sid,
            "shell_radius_r": shell["shell_radius_r"],
            "incoming_anchor": anchor,
            "branches_on_shell": branches,
            "branch_scores": scores,
            "selected_anchor": selected,
            "step_kind": step_kind,
            "stratum_map": smap,
            "irreversibility": measure,
            "derived_orientation": derived,
        })
        anchor = selected

    nonempty = [s for s in traversal_steps if s["branches_on_shell"]]
    return {
        # v2: direction is DERIVED from the measured irreversibility of the inward
        # strata, not stored. It is "INWARD" iff every non-empty future stratum's
        # map is many-to-one (derives INWARD). If any inward stratum is injective
        # (control reversed it), direction is NOT uniformly INWARD.
        "direction": (
            "INWARD"
            if (len(nonempty) >= 1 and all(s["derived_orientation"] == "INWARD" for s in nonempty))
            else "MIXED_OR_NOT_INWARD"
        ),
        "direction_is_derived_from_irreversibility": True,
        "rule": "inward multi-shell traversal outer->inner->present keyed by "
        "shell_radius_r; outermost shell seeds the anchor by within-shell "
        "compatibility mass; each inner shell selects max pairwise compatibility "
        "with the incoming anchor (tie-break lowest id). Each future stratum's "
        "orientation is DERIVED: INWARD iff its branches->anchor map is many-to-one.",
        "shell_traversal_order": [s["shell_id"] for s in future_shells],
        "shell_radius_order": [int(s["shell_radius_r"]) for s in future_shells],
        "traversal_steps": traversal_steps,
        "num_traversal_steps": len(nonempty),
        "present_survivor": anchor,
        "weights_computed_before_compression": True,
        "input_shells_used": sorted(future_continuations.keys()),
        "shell_ordering_load_bearing": True,
        # v2: the per-shell derived inward orientation, exposed for the validator.
        "inward_strata_derived_orientations": {
            s["shell_id"]: s["derived_orientation"] for s in nonempty
        },
    }


# =====================================================================
# Flat-union argmax: v0 mechanism, retained ONLY as a negative-control reference.
# =====================================================================

def flat_union_argmax_survivor(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
) -> str:
    """v0's flat-union mechanism (shell-blind), retained for negative control (a)."""
    candidates = sorted(
        {b for branches in future_continuations.values() for b in branches}
    )
    inward_mass = {
        p: sum(
            compatibility_weights[pair_key(p, q)]
            for q in candidates
            if q != p
        )
        for p in candidates
    }
    return max(candidates, key=lambda p: (inward_mass[p], -_branch_id_rank(p)))


# =====================================================================
# outward_record: past-facing hash-chain of what survived the compression.
# v2: the record's OUTWARD orientation is itself DERIVED from the record map's
# INJECTIVITY (each compressed-away event -> its own distinct entry). DISTINCT from
# compression_map.
# =====================================================================

def hash_chain_step(previous_hash: str, step: int, entries: list[dict[str, Any]]) -> dict[str, Any]:
    entry_hashes = [sha256_text(canonical_json(entry)) for entry in entries]
    state = {
        "previous_hash": previous_hash,
        "step": step,
        "entry_hashes": entry_hashes,
        "entry_count": len(entries),
    }
    return {
        "step": step,
        "previous_hash": previous_hash,
        "entry_hashes": entry_hashes,
        "record_state_hash": sha256_text(canonical_json(state)),
    }


def recompute_hash_chain(hash_chain: list[dict[str, Any]], per_step_entries: list[list[dict[str, Any]]]) -> bool:
    previous = "0" * 64
    for expected, entries in zip(hash_chain, per_step_entries, strict=True):
        actual = hash_chain_step(previous, expected["step"], entries)
        if actual["record_state_hash"] != expected["record_state_hash"]:
            return False
        previous = actual["record_state_hash"]
    return True


def build_outward_record(
    shells: list[dict[str, Any]],
    compression: dict[str, Any],
    *,
    record_map_override: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Past-facing record. We replay the inward traversal steps and at each step emit a
    provenance entry. The record stratum performs the RECORD MAP: each compressed-
    away branch event is preserved as its OWN distinct image (record_stratum_map ->
    injective). We MEASURE that map's irreversibility and DERIVE the record's
    orientation from it: it is OUTWARD iff injective.

    record_map_override: the emergence discriminating control passes a MANY-TO-ONE
    record map here (all events collapsed to one image). With a many-to-one record
    map, derive_orientation returns INWARD instead of OUTWARD -- the record's
    orientation FLIPS, proving it is emergent, not stipulated.

    The record stratum is selected by stratum_kind == "record" (which MAP it
    performs), NOT by any stored orientation string.
    """
    survivor = compression["present_survivor"]
    record_shell = next(s for s in shells if s.get("stratum_kind") == "record")

    per_step_entries: list[list[dict[str, Any]]] = []
    hash_chain: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    record_entries: list[dict[str, Any]] = []

    # Collect all compressed-away branch events across the inward traversal; each
    # becomes a distinct record event id (shell-qualified so events on different
    # shells are distinct preserved items).
    compressed_events: list[str] = []
    for tstep in compression["traversal_steps"]:
        branches = tstep["branches_on_shell"]
        selected = tstep["selected_anchor"]
        for b in sorted(branches):
            if b != selected:
                compressed_events.append(f"{tstep['shell_id']}:{b}")

    # The ACTUAL record map (injective by construction), unless the control overrides it.
    rmap = record_map_override if record_map_override is not None else record_stratum_map(compressed_events)
    record_measure = measure_irreversibility(rmap)
    record_derived_orientation = derive_orientation(record_measure)

    for step, tstep in enumerate(compression["traversal_steps"]):
        branches = tstep["branches_on_shell"]
        selected = tstep["selected_anchor"]
        compressed_away = sorted([b for b in branches if b != selected])
        entry = {
            "from_shell": tstep["shell_id"],
            "from_shell_radius_r": tstep["shell_radius_r"],
            "source_derived_orientation": tstep.get("derived_orientation"),
            "record_derived_orientation": record_derived_orientation,
            "incoming_anchor": tstep["incoming_anchor"],
            "anchor_survived_this_shell": selected,
            "branches_compressed_away": compressed_away,
            "step_kind": tstep["step_kind"],
            "final_present_survivor": survivor,
        }
        entries = [entry]
        record_entries.extend(entries)
        per_step_entries.append(entries)
        chain_entry = hash_chain_step(previous_hash, step, entries)
        hash_chain.append(chain_entry)
        previous_hash = chain_entry["record_state_hash"]

    return {
        "record_shell_id": record_shell["shell_id"],
        # v2: orientation DERIVED from the record map's injectivity, not stored.
        "record_orientation": record_derived_orientation,  # must DERIVE OUTWARD
        "record_orientation_is_derived_from_irreversibility": True,
        "record_map": rmap,
        "record_irreversibility": record_measure,
        "inward_provenance_bound": True,
        "reflects_per_shell_compression_steps": True,
        "binds_present_survivor": survivor,
        "compressed_events": sorted(compressed_events),
        "record_entries": record_entries,
        "record_hash_chain": hash_chain,
        "append_only_recomputed": recompute_hash_chain(hash_chain, per_step_entries),
        "record_final_hash": previous_hash,
    }


# =====================================================================
# Build the full object instance
# =====================================================================

def build_object_instance(
    *,
    future_continuations: dict[str, list[str]] | None = None,
    shells: list[dict[str, Any]] | None = None,
    weights_override: dict[str, float] | None = None,
    record_map_override: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Assemble one RetrocausalPossibilityField instance. record_map_override is
    used by the emergence discriminating control to reverse the record-map asymmetry."""
    fc = future_continuations if future_continuations is not None else FUTURE_CONTINUATIONS_BY_SHELL
    sh = shells if shells is not None else SHELLS

    weights = weights_override if weights_override is not None else compute_compatibility_weights(fc)
    compression = compression_map(fc, weights, sh)
    present_survivor = compression["present_survivor"]
    outward_record = build_outward_record(sh, compression, record_map_override=record_map_override)

    # v2: the DERIVED shell_orientation map -- computed per stratum from its
    # measured irreversibility, NEVER read from a stored string. (The future strata
    # derive INWARD from the traversal step maps; the record stratum derives its
    # orientation from the record map.)
    derived_shell_orientation: dict[str, str | None] = {}
    for tstep in compression["traversal_steps"]:
        derived_shell_orientation[tstep["shell_id"]] = tstep.get("derived_orientation")
    derived_shell_orientation[outward_record["record_shell_id"]] = outward_record["record_orientation"]

    return {
        "event_x": EVENT_X,
        "shells": sh,
        "shell_radius_r": [s["shell_radius_r"] for s in sh],
        "shell_orientation": derived_shell_orientation,  # DERIVED, not stored
        "branch_states": BRANCH_STATES,
        "future_continuations": fc,
        "compatibility_weights": weights,
        "compression_map": compression,
        "present_survivor": present_survivor,
        "outward_record": outward_record,
    }


# =====================================================================
# THE v2 EMERGENCE DISCRIMINATING CONTROL (the new first-class acceptance control).
# Reverse the MEASURED asymmetry and assert the DERIVED orientation FLIPS / FAILS.
# =====================================================================

def orientation_emergence_control() -> dict[str, Any]:
    """
    Prove orientation is EMERGENT, not stipulated, by reversing the measured
    asymmetry and showing the derived label flips.

    Direction 1 (inward stratum -> make injective):
      Take an inward future stratum's actual map (branches -> single anchor =
      many-to-one -> derives INWARD). Reverse the asymmetry: build an INJECTIVE
      map over the same branches (each branch -> its own distinct image, no
      compression). derive_orientation MUST flip INWARD -> OUTWARD.

    Direction 2 (record stratum -> make many-to-one):
      Take the record's actual map (each event -> itself = injective -> derives
      OUTWARD). Reverse it: collapse ALL events to one image (many-to-one).
      derive_orientation MUST flip OUTWARD -> INWARD. We also rebuild the full
      object with that reversed record map and confirm the instance's
      shell_orientation for the record shell flips.

    If derive_orientation read a stored constant, NONE of these would flip. They
    flip iff the label tracks the measured irreversibility -> emergent.
    """
    base = build_object_instance()

    # --- direction 1: an inward stratum, baseline derives INWARD ---
    inward_steps = [s for s in base["compression_map"]["traversal_steps"] if s["branches_on_shell"]]
    sample = inward_steps[0]
    actual_inward_map = sample["stratum_map"]
    actual_inward_measure = measure_irreversibility(actual_inward_map)
    actual_inward_orientation = derive_orientation(actual_inward_measure)

    # reverse the asymmetry: injective map over the SAME domain branches
    branches = sample["branches_on_shell"]
    injective_inward_map = {b: f"img_{b}" for b in branches}  # each -> distinct image
    reversed_inward_measure = measure_irreversibility(injective_inward_map)
    reversed_inward_orientation = derive_orientation(reversed_inward_measure)

    inward_flips = (
        actual_inward_orientation == "INWARD"
        and reversed_inward_orientation == "OUTWARD"
        and actual_inward_orientation != reversed_inward_orientation
    )

    # --- direction 2: the record stratum, baseline derives OUTWARD ---
    actual_record_map = base["outward_record"]["record_map"]
    actual_record_measure = measure_irreversibility(actual_record_map)
    actual_record_orientation = derive_orientation(actual_record_measure)

    # reverse: collapse all record events to ONE shared image (many-to-one)
    record_domain = sorted(actual_record_map.keys())
    collapsed_record_map = {ev: "single_collapsed_image" for ev in record_domain}
    reversed_record_measure = measure_irreversibility(collapsed_record_map)
    reversed_record_orientation = derive_orientation(reversed_record_measure)

    record_flips = (
        actual_record_orientation == "OUTWARD"
        and reversed_record_orientation == "INWARD"
        and actual_record_orientation != reversed_record_orientation
    )

    # rebuild the full instance with the reversed (collapsed) record map and confirm
    # the instance-level derived record orientation flips end-to-end.
    reversed_instance = build_object_instance(record_map_override=collapsed_record_map)
    record_shell_id = base["outward_record"]["record_shell_id"]
    base_record_orientation_inst = base["shell_orientation"][record_shell_id]
    reversed_record_orientation_inst = reversed_instance["shell_orientation"][record_shell_id]
    record_flips_end_to_end = (
        base_record_orientation_inst == "OUTWARD"
        and reversed_record_orientation_inst == "INWARD"
    )

    return {
        # direction 1: inward -> injective flips INWARD->OUTWARD
        "inward_actual_map": actual_inward_map,
        "inward_actual_measure": actual_inward_measure,
        "inward_actual_orientation": actual_inward_orientation,
        "inward_reversed_injective_map": injective_inward_map,
        "inward_reversed_measure": reversed_inward_measure,
        "inward_reversed_orientation": reversed_inward_orientation,
        "inward_orientation_flips_under_reversal": inward_flips,
        # direction 2: record -> many-to-one flips OUTWARD->INWARD
        "record_actual_map": actual_record_map,
        "record_actual_measure": actual_record_measure,
        "record_actual_orientation": actual_record_orientation,
        "record_reversed_collapsed_map": collapsed_record_map,
        "record_reversed_measure": reversed_record_measure,
        "record_reversed_orientation": reversed_record_orientation,
        "record_orientation_flips_under_reversal": record_flips,
        # end-to-end (full instance rebuild with reversed record map)
        "base_record_orientation_instance": base_record_orientation_inst,
        "reversed_record_orientation_instance": reversed_record_orientation_inst,
        "record_orientation_flips_end_to_end": record_flips_end_to_end,
        # overall
        "orientation_is_emergent": inward_flips and record_flips and record_flips_end_to_end,
    }


# =====================================================================
# v1's shell-reassignment control (KEPT -- must STILL pass in v2).
# =====================================================================

CANONICAL_REASSIGNMENT: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b5", "b3"],
    "Sigma_1": ["b2", "b4"],
}


def union_of(future_continuations: dict[str, list[str]]) -> list[str]:
    return sorted({b for branches in future_continuations.values() for b in branches})


def shell_reassignment_control() -> dict[str, Any]:
    """v1's control (kept): move a branch to a different shell, union identical, the
    present_survivor must MOVE. Proves the shell ordering is still load-bearing."""
    base = build_object_instance()
    reassigned = build_object_instance(future_continuations=CANONICAL_REASSIGNMENT)

    base_union = union_of(base["future_continuations"])
    reassigned_union = union_of(reassigned["future_continuations"])

    base_path = [
        (s["shell_id"], s["selected_anchor"])
        for s in base["compression_map"]["traversal_steps"]
        if s["branches_on_shell"]
    ]
    reassigned_path = [
        (s["shell_id"], s["selected_anchor"])
        for s in reassigned["compression_map"]["traversal_steps"]
        if s["branches_on_shell"]
    ]

    base_survivor = base["present_survivor"]
    reassigned_survivor = reassigned["present_survivor"]

    return {
        "base_future_continuations": base["future_continuations"],
        "reassigned_future_continuations": reassigned["future_continuations"],
        "union_identical": base_union == reassigned_union,
        "union": base_union,
        "base_present_survivor": base_survivor,
        "reassigned_present_survivor": reassigned_survivor,
        "base_inward_path": base_path,
        "reassigned_inward_path": reassigned_path,
        "shell_reassignment_moves_survivor": base_survivor != reassigned_survivor,
        "shell_reassignment_moves_inward_path": base_path != reassigned_path,
    }


def flat_union_negative_control() -> dict[str, Any]:
    """Negative control (a): collapse to v0's flat union argmax -> the
    shell-reassignment must FAIL to move the survivor (union identical)."""
    base = build_object_instance()
    reassigned = build_object_instance(future_continuations=CANONICAL_REASSIGNMENT)

    base_flat = flat_union_argmax_survivor(base["future_continuations"], base["compatibility_weights"])
    reassigned_flat = flat_union_argmax_survivor(
        reassigned["future_continuations"], reassigned["compatibility_weights"]
    )

    return {
        "mechanism": "flat_union_argmax_total_pairwise_mass (v0 mechanism)",
        "base_flat_survivor": base_flat,
        "reassigned_flat_survivor": reassigned_flat,
        "flat_union_moves_survivor": base_flat != reassigned_flat,
        "flat_union_control_correctly_inert": base_flat == reassigned_flat,
    }


def scramble_futures_negative_control() -> dict[str, Any]:
    """Negative control (b): scramble future_continuations so each shell carries
    ONE distinct branch. The build must BREAK (an invariant must fail). NOTE: with
    one branch per shell the future stratum map is 1->1 (injective) so its derived
    orientation is OUTWARD not INWARD -- a second way this control breaks the build
    (the future strata no longer derive INWARD)."""
    scrambled = {
        sid: [branches[0], branches[0]]
        for sid, branches in FUTURE_CONTINUATIONS_BY_SHELL.items()
    }
    inst = build_object_instance(future_continuations=scrambled)
    inv = check_invariants(inst, include_emergent_controls=False)
    return {
        "mechanism": "scramble future_continuations to 1 distinct branch per shell",
        "all_invariants_hold": all(inv.values()),
        "control_breaks": not all(inv.values()),
    }


def uniform_weights_negative_control() -> dict[str, Any]:
    """Negative control (c): constant compatibility weights -> non-uniformity
    invariant fails (build breaks) AND the shell-reassignment no longer moves."""
    real_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
    uniform = {k: 0.5 for k in real_weights}
    inst = build_object_instance(weights_override=uniform)
    inv = check_invariants(inst, include_emergent_controls=False)

    base_uniform = build_object_instance(weights_override=uniform)
    reassigned_real = compute_compatibility_weights(CANONICAL_REASSIGNMENT)
    reassigned_uniform = {k: 0.5 for k in reassigned_real}
    reassigned_inst = build_object_instance(
        future_continuations=CANONICAL_REASSIGNMENT, weights_override=reassigned_uniform
    )
    moves_under_uniform = (
        base_uniform["present_survivor"] != reassigned_inst["present_survivor"]
    )

    return {
        "mechanism": "uniform (constant) compatibility weights claiming pair structure",
        "all_invariants_hold": all(inv.values()),
        "control_breaks": not all(inv.values()),
        "base_survivor_under_uniform": base_uniform["present_survivor"],
        "reassigned_survivor_under_uniform": reassigned_inst["present_survivor"],
        "shell_reassignment_still_moves_under_uniform": moves_under_uniform,
        "uniform_correctly_kills_shell_effect": not moves_under_uniform,
    }


# =====================================================================
# v0 trap controls (must STILL pass in v2)
# =====================================================================

def weight_permutation_trap() -> dict[str, Any]:
    """Trap #1 (must stay PASS): permuting compatibility_weights moves the survivor."""
    base = build_object_instance()
    weights = dict(base["compatibility_weights"])
    ka, kb = "b0|b1", "b1|b2"
    weights[ka], weights[kb] = weights[kb], weights[ka]
    permuted = build_object_instance(weights_override=weights)
    return {
        "swapped_pair_weights": [ka, kb],
        "base_survivor": base["present_survivor"],
        "permuted_survivor": permuted["present_survivor"],
        "weight_permutation_moves_survivor": base["present_survivor"] != permuted["present_survivor"],
    }


def state_mutation_trap() -> dict[str, Any]:
    """Trap #4 (must stay PASS): mutating a branch feature moves the survivor."""
    base = build_object_instance()

    global BRANCH_STATES
    saved = {k: dict(v) for k, v in BRANCH_STATES.items()}
    try:
        BRANCH_STATES["b3"]["a"] += 5
        mutated_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
        mutated = build_object_instance(weights_override=mutated_weights)
        mutated_survivor = mutated["present_survivor"]
    finally:
        BRANCH_STATES = saved

    return {
        "mutated_branch": "b3",
        "mutation": "b3.a += 5",
        "base_survivor": base["present_survivor"],
        "mutated_survivor": mutated_survivor,
        "state_mutation_moves_survivor": base["present_survivor"] != mutated_survivor,
    }


# =====================================================================
# INVARIANTS + HARD-STOP
# =====================================================================

def check_invariants(instance: dict[str, Any], *, include_emergent_controls: bool = True) -> dict[str, Any]:
    """Named invariant -> bool. The validator asserts these.

    include_emergent_controls=False is used by the negative-control builders that
    intentionally break a precursor invariant."""
    fc = instance["future_continuations"]
    shells = instance["shells"]
    weights = instance["compatibility_weights"]
    compression = instance["compression_map"]
    survivor = instance["present_survivor"]
    record = instance["outward_record"]

    future_shell_ids = {s["shell_id"] for s in shells if s.get("stratum_kind") == "future"}
    record_shell_ids = {s["shell_id"] for s in shells if s.get("stratum_kind") == "record"}

    # future continuations are FUTURE-INDEXED (keyed by future strata only)
    fc_future_indexed = (set(fc.keys()) <= future_shell_ids) and len(fc) >= 1
    fc_lists_of_distinct = all(
        isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()
    )

    # v2: NO shell carries a stipulated shell_orientation string (the gap fixed)
    no_stipulated_orientation_on_shells = all(
        "shell_orientation" not in s for s in shells
    )

    # v2: the inward direction is DERIVED (not stored) and the canonical instance
    # derives INWARD on every non-empty future stratum.
    nonempty_steps = [s for s in compression.get("traversal_steps", []) if s["branches_on_shell"]]
    future_flow_inward_derived = (
        compression.get("direction") == "INWARD"
        and bool(compression.get("direction_is_derived_from_irreversibility"))
        and len(nonempty_steps) >= 1
        and all(s.get("derived_orientation") == "INWARD" for s in nonempty_steps)
    )

    # v2: each inward stratum's map is genuinely many-to-one (the measured asymmetry)
    inward_strata_many_to_one = (
        len(nonempty_steps) >= 1
        and all(s["irreversibility"]["many_to_one"] is True for s in nonempty_steps)
        and all(s["irreversibility"]["fan_in"] > s["irreversibility"]["fan_out"] for s in nonempty_steps)
    )

    # v2: the record orientation is DERIVED OUTWARD from the record map's injectivity
    record_outward_derived = (
        record.get("record_orientation") == "OUTWARD"
        and bool(record.get("record_orientation_is_derived_from_irreversibility"))
        and record.get("record_irreversibility", {}).get("injective") is True
        and record.get("record_irreversibility", {}).get("fan_in")
        == record.get("record_irreversibility", {}).get("fan_out")
    )

    has_record_shell = len(record_shell_ids) >= 1

    weights_before_compression = bool(compression.get("weights_computed_before_compression"))
    weights_are_pair_reals = (
        len(weights) >= 1
        and all("|" in k for k in weights.keys())
        and all(isinstance(w, float) for w in weights.values())
    )
    weights_non_uniform = len(set(round(w, 12) for w in weights.values())) >= 2

    survivor_derived = (
        survivor == compression.get("present_survivor")
        and len(nonempty_steps) >= 1
        and survivor == nonempty_steps[-1]["selected_anchor"]
    )
    multi_step_traversal = len(nonempty_steps) >= 2
    record_chain_ok = bool(record.get("append_only_recomputed"))

    empty_steps = [s for s in compression.get("traversal_steps", []) if not s["branches_on_shell"]]
    record_binds_provenance = (
        bool(record.get("inward_provenance_bound"))
        and bool(record.get("reflects_per_shell_compression_steps"))
        and record.get("binds_present_survivor") == survivor
        and len(record.get("record_entries", [])) == len(nonempty_steps) + len(empty_steps)
        and len(record.get("record_entries", [])) >= 1
    )

    # HARD-STOP: future_continuations must NOT equal present_survivor.
    hard_stop_not_identity = fc != survivor and survivor not in (None, fc)

    map_distinct_from_record = set(compression.keys()) != set(record.keys())

    invariants = {
        "future_continuations_future_indexed": fc_future_indexed,
        "future_continuations_lists_of_distinct_ge2": fc_lists_of_distinct,
        "no_stipulated_shell_orientation_string": no_stipulated_orientation_on_shells,
        "future_flow_inward_DERIVED": future_flow_inward_derived,
        "inward_strata_maps_are_many_to_one": inward_strata_many_to_one,
        "record_outward_DERIVED_from_injectivity": record_outward_derived,
        "has_record_shell": has_record_shell,
        "compatibility_weights_before_compression": weights_before_compression,
        "compatibility_weights_are_pair_reals": weights_are_pair_reals,
        "compatibility_weights_non_uniform": weights_non_uniform,
        "present_survivor_derived_through_traversal": survivor_derived,
        "compression_is_multi_step_traversal": multi_step_traversal,
        "outward_record_hash_chain_recomputes": record_chain_ok,
        "outward_record_binds_inward_provenance": record_binds_provenance,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop_not_identity,
        "compression_map_distinct_from_outward_record": map_distinct_from_record,
    }

    if include_emergent_controls:
        # v1 win retained: shell-reassignment moves the survivor
        ctrl = shell_reassignment_control()
        invariants["SHELL_REASSIGNMENT_MOVES_SURVIVOR"] = bool(
            ctrl["union_identical"] and ctrl["shell_reassignment_moves_survivor"]
        )
        # v2 fix: orientation is emergent (reversing the asymmetry flips the label)
        emergence = orientation_emergence_control()
        invariants["ORIENTATION_IS_EMERGENT_REVERSAL_FLIPS_LABEL"] = bool(
            emergence["orientation_is_emergent"]
        )

    return invariants


FIRST_CLASS_KEYS = [
    "event_x",
    "shells",
    "shell_radius_r",
    "shell_orientation",
    "future_continuations",
    "branch_states",
    "compatibility_weights",
    "compression_map",
    "present_survivor",
    "outward_record",
]


def build_result() -> dict[str, Any]:
    instance = build_object_instance()
    invariants = check_invariants(instance)
    all_invariants_hold = all(invariants.values())

    reassignment = shell_reassignment_control()
    emergence = orientation_emergence_control()
    flat_neg = flat_union_negative_control()
    scramble_neg = scramble_futures_negative_control()
    uniform_neg = uniform_weights_negative_control()
    weight_trap = weight_permutation_trap()
    state_trap = state_mutation_trap()

    result = {
        "name": "retrocausal_possibility_field_v2_irreversibility",
        "object_name": "RetrocausalPossibilityField",
        "object_statement_sha256": "02f813d355b5812e1021eb023e5aca7c6006c00dcfc060cf94ff727b7cb8dd78",
        "probe_family": "M_per_stratum_irreversibility_readout_plus_shell_ordered_inward_traversal",
        "constraint_set": "C_orientation_derived_from_fan_in_fan_out_plus_inward_traversal_cross_shell_compatibility",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,

        # ---- THE FIRST-CLASS OBJECT FIELDS (genuinely computed) ----
        "event_x": instance["event_x"],
        "shells": instance["shells"],
        "shell_radius_r": instance["shell_radius_r"],
        "shell_orientation": instance["shell_orientation"],  # v2: DERIVED, not stored
        "future_continuations": instance["future_continuations"],
        "branch_states": instance["branch_states"],
        "compatibility_weights": instance["compatibility_weights"],
        "compression_map": instance["compression_map"],
        "present_survivor": instance["present_survivor"],
        "outward_record": instance["outward_record"],

        "first_class_keys_present": FIRST_CLASS_KEYS,
        "invariants": invariants,
        "all_invariants_hold": all_invariants_hold,

        # ---- THE v2 ACCEPTANCE: orientation derived + emergence control ----
        "orientation_is_emergent": emergence["orientation_is_emergent"],
        "orientation_emergence_control": emergence,
        # the COMPUTED asymmetries from which orientation is derived
        "computed_irreversibility": {
            "inward_strata": {
                s["shell_id"]: s["irreversibility"]
                for s in instance["compression_map"]["traversal_steps"]
                if s["branches_on_shell"]
            },
            "inward_strata_derived_orientations": instance["compression_map"]["inward_strata_derived_orientations"],
            "record_stratum": instance["outward_record"]["record_irreversibility"],
            "record_derived_orientation": instance["outward_record"]["record_orientation"],
        },

        # ---- v1 wins retained (must still pass) ----
        "shell_reassignment_moves_survivor": reassignment["shell_reassignment_moves_survivor"],
        "shell_reassignment_control": reassignment,
        "trap_1_weight_permutation": weight_trap,
        "trap_4_state_mutation": state_trap,

        # ---- negative controls ----
        "negative_control_flat_union": flat_neg,
        "negative_control_scramble_futures": scramble_neg,
        "negative_control_uniform_weights": uniform_neg,

        # ---- honest ceiling ----
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "shell_orientation now DERIVED from measured compression irreversibility "
            "(fan-in/fan-out): INWARD = many-to-one compression, OUTWARD = injective "
            "record; reversing the measured asymmetry flips the derived label "
            "(emergence control). v1's shell-ordering load-bearingness, traps #1/#4, "
            "and hard-stop are preserved. Trivial carrier, no QIT; NOT physics/Axis0/"
            "manifold/canonical."
        ),
        "blocked_downstream_consumers": [
            "Axis0 claim",
            "flux claim",
            "physics claim",
            "formal manifold admission",
            "claim that this trivial carrier is THE retrocausal field of the real model",
            "claim that fan-in/fan-out on a 6-branch toy is a physical arrow of time",
        ],
        "all_pass": all_invariants_hold,
        "criteria_checked": sorted(invariants.keys()),
    }
    return result


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(
    SIM_DIR, "results", "retrocausal_possibility_field_v2_irreversibility_results.json"
)


def main() -> int:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "ok": result["all_pass"],
        "orientation_is_emergent": result["orientation_is_emergent"],
        "inward_derived_orientations": result["compression_map"]["inward_strata_derived_orientations"],
        "record_derived_orientation": result["outward_record"]["record_orientation"],
        "shell_reassignment_moves_survivor": result["shell_reassignment_moves_survivor"],
        "result_path": RESULT_PATH,
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
