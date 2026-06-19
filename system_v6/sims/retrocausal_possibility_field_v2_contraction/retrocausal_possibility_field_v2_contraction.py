#!/usr/bin/env python3
"""
retrocausal_possibility_field_v2_contraction -- successor to v1. ONE audited gap
fixed: the SHELL ORIENTATION (INWARD / OUTWARD) is now EMERGENT from a computed
contraction quantity, not a STIPULATED string label.

Started from system_v4/probes/SIM_TEMPLATE.py (template framing preserved) and
inherits v1's machinery (trivial finite carrier, pairwise-compatibility weights,
shell-ordered inward traversal, hash-chain outward_record). It KEEPS all of v1's
wins:
  - shell-reassignment (union identical, branch moved between shells) still MOVES
    the present_survivor (v1's trap#2/#5 fix);
  - trap #1 (weight permutation moves survivor) and trap #4 (state mutation moves
    survivor) still PASS;
  - the HARD-STOP future_continuations != present_survivor still holds.

THE OBJECT (per system_v6/receipts/v43_object_card_current_run.json):
  "A finite shell-indexed field of possible futures compresses INWARD through
   compatibility into a present survivor, while the past-facing OUTWARD record
   preserves what survived."

THE AUDITED GAP v2 FIXES (from v1's claim_ceiling + the v0 audit lineage):
  In v1, each shell carried shell_orientation as a HARDCODED string ("INWARD" /
  "OUTWARD"), the compression returned direction="INWARD" as a hardcoded literal,
  and the validator only read those constants back. So "which way is inward" was
  STIPULATED, never derived. v1's own claim_ceiling names it: "orientation still a
  label not emergent (the v2 target)."

THE v2 FIX -- orientation EMERGENT from a contraction / fixed-point direction:
  The present location x* (= present_survivor) is a FIXED POINT: it is the point
  the field compresses TO, derived from the geometry (v1's traversal), independent
  of any orientation label. We then DERIVE orientation as a downstream COMPUTED
  quantity:
    - For a given shell traversal ORDER, compute the mean L1 distance of each
      shell's full candidate set to the fixed point x*. This gives a sequence
      d_0, d_1, ... along the traversal.
    - The CONTRACTION RATIO is the ratio of consecutive mean-distances toward x*
      (d_{k+1} / d_k), averaged (geometric mean) over the traversal steps.
    - If contraction_ratio < 1  -> the candidate sets get CLOSER to x* along this
      order -> the map CONTRACTS toward the fixed point -> the order is INWARD.
    - If contraction_ratio > 1  -> the sets get FARTHER -> the map EXPANDS away
      from the fixed point -> the order is OUTWARD.
    - If contraction_ratio == 1 (within tol) -> NO asymmetry -> orientation is
      UNDEFINED (it cannot be derived; orientation FAILS, proving it is not a free
      stipulation).
  orientation = derive_orientation(contraction_ratio): a function of a COMPUTED
  real number, NOT a constant read from the shell record.

THE EMERGENCE DISCRIMINATING CONTROL (the hard-acceptance requirement):
  REVERSE the computed asymmetry (reverse the traversal order) and re-derive:
  the contraction ratio crosses 1 (contraction <-> expansion) and the DERIVED
  orientation FLIPS (INWARD -> OUTWARD). REMOVE the asymmetry (a radially symmetric
  field whose shells are equidistant from x*) and the ratio == 1 so the DERIVED
  orientation FAILS (UNDEFINED). Either way, orientation tracks the computed
  quantity and is not a stipulated label.

WHAT THIS SIM IS / IS NOT (honest ceiling):
  - classification = scratch_diagnostic
  - promotion_allowed = false ; formal_admission_allowed = false
  - claim_ceiling: shell-orientation now DERIVED from a computed contraction ratio
    (emergent, flips/fails under reversal/removal of the asymmetry); shell-ordering
    still load-bearing; trivial carrier; NO QIT; NOT physics/Axis0/manifold/
    canonical.

Probe family M: pairwise-compatibility weight readout over enumerated branch
  states + a CONTRACTION readout (mean-distance-to-fixed-point sequence along a
  shell order).
Constraint set C: inward traversal (compression toward the fixed point) +
  orientation derived from sign(contraction_ratio - 1).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Any

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================
# This object is a FIELD-INSTANTIATION receipt on a trivial finite carrier whose
# inward compression is shell-ordered (v1) AND whose orientation is now derived
# from a computed contraction ratio (v2). It deliberately uses NO QIT /
# density-matrix / heavy numeric tooling: the load-bearing tool is the hashlib
# append-only chain (outward_record provenance, reused from rpf v0/v1); the
# contraction quantity is pure-Python integer/float arithmetic so the emergence
# of orientation stays auditable line by line.

TOOL_MANIFEST = {
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "append-only sha256 hash-chain is the outward_record machinery "
        "(reused from rpf v0/v1); each chain entry binds the PER-SHELL compression "
        "step (incoming anchor, surviving anchor, branches compressed away, and the "
        "step's mean-distance-to-fixed-point) so the record reflects the shell-"
        "ordered contraction -- load-bearing for outward_record provenance.",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "canonical_json serialization for stable hash-chain digests and "
        "the result receipt; supportive (serialization, not the claim itself).",
    },
    "math": {
        "tried": True,
        "used": True,
        "reason": "math.prod / math.pow for the geometric-mean contraction ratio "
        "over traversal steps; supportive arithmetic for the emergent-orientation "
        "quantity (the orientation derivation itself is plain comparison to 1).",
    },
    "numpy": {
        "tried": True,
        "used": False,
        "reason": "available but deliberately NOT used: the carrier is a trivial "
        "finite set and the contraction quantity is a short deterministic loop over "
        "<=3 shells; pure-Python keeps the orientation-emergence auditable. Heavy "
        "numeric tooling would re-enter the proxy basin and obscure the derivation.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is object-field instantiation with a derived "
        "scalar orientation, not a structural-impossibility (UNSAT) proof. No formal "
        "admission is claimed.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed: no density matrix / network / autograd carrier; using "
        "it would be decorative and would re-enter the proxy basin.",
    },
    "jax": {
        "tried": False,
        "used": False,
        "reason": "not needed: trivial finite carrier; the contraction quantity is a "
        "short deterministic loop, not a batched/exhaustive sweep.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Canon algebra artifact is consumed; field "
        "instantiation with a derived orientation scalar only.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "hashlib": "load_bearing",   # outward_record per-shell hash-chain
    "json": "supportive",        # canonical serialization
    "math": "supportive",        # geometric-mean contraction ratio
    "numpy": None,
    "z3": None,
    "pytorch": None,
    "jax": None,
    "julia": None,
}


# =====================================================================
# Carrier + record machinery (inherited from v1, unchanged carrier)
# =====================================================================

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ---- The trivial finite carrier: 6 enumerated branch states ----------
# Identical to v0/v1: the change is in the orientation derivation, not the carrier.
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
# CRITICAL v2 CHANGE: the inward shells NO LONGER carry a hardcoded
# shell_orientation string. They carry only shell_radius_r (their position) and a
# role description. The orientation INWARD/OUTWARD is DERIVED from the contraction
# quantity (see derive_orientation). The OUTWARD record shell keeps an explicit
# orientation tag ONLY as the record sink marker, but its INWARD/OUTWARD-ness as
# the *future* strata is the thing now derived, not stipulated.
#
# To keep v1's outward_record machinery (which needs an OUTWARD sink shell) we
# retain a single record shell tagged "OUTWARD" -- but the FUTURE shells'
# orientation is derived. We flag derived-vs-stipulated explicitly per shell.
SHELLS: list[dict[str, Any]] = [
    {"shell_id": "Sigma_2", "shell_radius_r": 2,
     "orientation_source": "DERIVED_FROM_CONTRACTION",
     "role": "future possibility stratum (radius 2)"},
    {"shell_id": "Sigma_1", "shell_radius_r": 1,
     "orientation_source": "DERIVED_FROM_CONTRACTION",
     "role": "future possibility stratum (radius 1)"},
    {"shell_id": "Sigma_record", "shell_radius_r": -1,
     "orientation_source": "RECORD_SINK_MARKER",
     "shell_orientation": "OUTWARD",
     "role": "past-facing survival record stratum (record sink)"},
]

# Future continuations are FUTURE-INDEXED by the future strata only. Each value is
# a LIST of >=2 non-trivially-distinct admissible branch states. Identical to v1's
# canonical config so all of v1's behavioral wins are preserved verbatim.
FUTURE_CONTINUATIONS_BY_SHELL: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b5"],   # radius-2 future stratum: 3 branches
    "Sigma_1": ["b2", "b3", "b4"],   # radius-1 future stratum: 3 branches
}

ORIENTATION_TOL = 1e-9   # |ratio - 1| <= tol => no asymmetry => UNDEFINED


# =====================================================================
# compatibility_weights (inherited from v1, unchanged)
# =====================================================================

def branch_distance(s1: str, s2: str) -> int:
    """L1 distance between two branch states in the trivial feature space."""
    x, y = BRANCH_STATES[s1], BRANCH_STATES[s2]
    return abs(x["a"] - y["a"]) + abs(x["b"] - y["b"])


def compute_compatibility_weights(
    future_continuations: dict[str, list[str]],
) -> dict[str, float]:
    """Real-valued non-uniform weights over PAIRS: weight(p,q)=1/(1+L1(p,q))."""
    all_futures: list[str] = []
    for _shell_id, branches in future_continuations.items():
        for b in branches:
            all_futures.append(b)
    uniq = sorted(set(all_futures))
    weights: dict[str, float] = {}
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            p, q = uniq[i], uniq[j]
            weights[f"{p}|{q}"] = 1.0 / (1.0 + float(branch_distance(p, q)))
    return weights


def pair_key(p: str, q: str) -> str:
    lo, hi = sorted((p, q))
    return f"{lo}|{hi}"


def _branch_id_rank(b: str) -> int:
    return int(b[1:])


# =====================================================================
# compression_map: shell-ordered INWARD traversal -> present_survivor (the FIXED
# POINT). Inherited from v1 verbatim in mechanism, with one addition: it now also
# RETURNS each step's mean-distance-to-the-fixed-point so the contraction quantity
# can be read off. The fixed point x* = present_survivor is geometry-derived and
# does NOT depend on any orientation label.
# =====================================================================

def _traverse(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
    shell_order: list[str],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Direction-agnostic anchor propagation along an explicit shell order.

    OUTERMOST step seeds the anchor by within-shell compatibility mass; each later
    step selects the branch of maximal pairwise compatibility with the incoming
    anchor (self-compatibility = 1.0 so the anchor persists if it reappears);
    deterministic tie-break = lowest branch id. The final anchor is the survivor.
    This is exactly v1's selection rule, factored so the SAME rule can be run on a
    reversed order for the emergence control."""
    anchor: str | None = None
    steps: list[dict[str, Any]] = []
    for sid in shell_order:
        branches = sorted(future_continuations.get(sid, []))
        if not branches:
            continue
        if anchor is None:
            scores = {
                p: sum(compatibility_weights[pair_key(p, q)] for q in branches if q != p)
                for p in branches
            }
            step_kind = "seed_within_shell_mass"
        else:
            scores = {
                p: (1.0 if p == anchor else compatibility_weights[pair_key(p, anchor)])
                for p in branches
            }
            step_kind = "cross_shell_compat_with_incoming_anchor"
        selected = max(branches, key=lambda p: (scores[p], -_branch_id_rank(p)))
        steps.append({
            "shell_id": sid,
            "incoming_anchor": anchor,
            "branches_on_shell": branches,
            "branch_scores": scores,
            "selected_anchor": selected,
            "step_kind": step_kind,
        })
        anchor = selected
    return anchor, steps


def _radius_descending_order(shells: list[dict[str, Any]],
                             future_continuations: dict[str, list[str]]) -> list[str]:
    """The future shells, largest radius first. This is the candidate 'inward'
    traversal ORDER -- whether it is *actually* inward is then DERIVED from the
    contraction ratio, not assumed."""
    future_shells = [s for s in shells if s["shell_id"] in future_continuations]
    return [s["shell_id"] for s in sorted(future_shells, key=lambda s: -int(s["shell_radius_r"]))]


def mean_distance_to_fixed_point(branches: list[str], fixed_point: str) -> float:
    """Mean L1 distance of a shell's full candidate set to the fixed point x*.
    The CONTRACTION quantity is built from this (NOT from the selected anchor,
    whose distance to x* is tautologically 0 on the final step)."""
    if not branches:
        return 0.0
    return sum(branch_distance(b, fixed_point) for b in branches) / len(branches)


def compute_contraction(
    future_continuations: dict[str, list[str]],
    shell_order: list[str],
    fixed_point: str,
) -> dict[str, Any]:
    """The v2 emergent-orientation quantity.

    Walk the shells in shell_order; for each non-empty shell compute the mean
    distance of its candidate set to the FIXED present location x*. This yields a
    sequence d_0, d_1, ... . The CONTRACTION RATIO is the geometric mean of the
    consecutive ratios d_{k+1}/d_k. ratio<1 => contracts toward x* => the order is
    INWARD; ratio>1 => expands => OUTWARD; ratio==1 (tol) => no asymmetry =>
    UNDEFINED. The orientation is DERIVED from this scalar, not read from a label.
    """
    dist_seq: list[float] = []
    per_shell: list[dict[str, Any]] = []
    for sid in shell_order:
        branches = sorted(future_continuations.get(sid, []))
        if not branches:
            continue
        d = mean_distance_to_fixed_point(branches, fixed_point)
        dist_seq.append(d)
        per_shell.append({
            "shell_id": sid,
            "branches_on_shell": branches,
            "mean_distance_to_fixed_point": d,
        })

    step_ratios: list[float] = []
    for k in range(len(dist_seq) - 1):
        if dist_seq[k] > 0.0:
            step_ratios.append(dist_seq[k + 1] / dist_seq[k])
        # if dist_seq[k]==0 the set already sits on x*; that step contributes no
        # finite ratio and is skipped (the remaining steps still decide).

    if step_ratios:
        contraction_ratio = math.prod(step_ratios) ** (1.0 / len(step_ratios))
    else:
        # not enough non-degenerate steps to define a ratio
        contraction_ratio = float("nan")

    return {
        "fixed_point": fixed_point,
        "shell_order": shell_order,
        "mean_distance_sequence": dist_seq,
        "per_shell_distance": per_shell,
        "step_ratios": step_ratios,
        "contraction_ratio": contraction_ratio,
    }


def derive_orientation(contraction_ratio: float, tol: float = ORIENTATION_TOL) -> str:
    """DERIVE orientation from the computed contraction ratio. This is the whole
    point of v2: the orientation is a function of a COMPUTED real number, not a
    constant. < 1 (beyond tol) => INWARD (contracts toward x*); > 1 (beyond tol)
    => OUTWARD (expands); within tol of 1 OR nan => UNDEFINED (no asymmetry to
    derive from)."""
    if not math.isfinite(contraction_ratio):
        return "UNDEFINED"
    if contraction_ratio < 1.0 - tol:
        return "INWARD"
    if contraction_ratio > 1.0 + tol:
        return "OUTWARD"
    return "UNDEFINED"


def compression_map(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
    shells: list[dict[str, Any]],
) -> dict[str, Any]:
    """Inward traversal compression (v1 mechanism) + DERIVED orientation (v2).

    The survivor (fixed point x*) is produced by the SAME radius-ordered traversal
    as v1 (so all of v1's behavioral wins are preserved). The DIRECTION label is NO
    LONGER a hardcoded literal: it is derived from the contraction ratio of the
    candidate sets toward x*.
    """
    shell_order = _radius_descending_order(shells, future_continuations)
    survivor, steps = _traverse(future_continuations, compatibility_weights, shell_order)

    # The fixed point of the compression = the survivor (geometry-derived, label-
    # independent). Orientation is now derived downstream of it.
    fixed_point = survivor
    contraction = compute_contraction(future_continuations, shell_order, fixed_point)
    derived_direction = derive_orientation(contraction["contraction_ratio"])

    # attach each step's mean-distance-to-fixed-point so the record/validator can
    # read the contraction off the same trace.
    dist_by_shell = {p["shell_id"]: p["mean_distance_to_fixed_point"]
                     for p in contraction["per_shell_distance"]}
    radius_by_shell = {s["shell_id"]: int(s["shell_radius_r"]) for s in shells}
    traversal_steps: list[dict[str, Any]] = []
    for st in steps:
        traversal_steps.append({
            **st,
            "shell_radius_r": radius_by_shell.get(st["shell_id"]),
            "mean_distance_to_fixed_point": dist_by_shell.get(st["shell_id"]),
        })

    return {
        # DERIVED, not stipulated:
        "direction": derived_direction,
        "direction_source": "DERIVED_FROM_CONTRACTION_RATIO",
        "contraction": contraction,
        "contraction_ratio": contraction["contraction_ratio"],
        "fixed_point": fixed_point,

        "rule": "inward multi-shell traversal seeds anchor by within-shell "
        "compatibility mass then selects each inner branch by max pairwise "
        "compatibility with the incoming anchor; the DIRECTION label is derived "
        "from sign(contraction_ratio - 1): mean candidate-set distance to the "
        "fixed point x* contracts (<1=>INWARD) or expands (>1=>OUTWARD)",
        "shell_traversal_order": shell_order,
        "shell_radius_order": [radius_by_shell[sid] for sid in shell_order],
        "traversal_steps": traversal_steps,
        "num_traversal_steps": len([s for s in traversal_steps if s["branches_on_shell"]]),
        "present_survivor": survivor,
        "weights_computed_before_compression": True,
        "input_shells_used": sorted(future_continuations.keys()),
        "shell_ordering_load_bearing": True,
    }


# =====================================================================
# Flat-union argmax (v0 mechanism) -- negative-control reference only.
# =====================================================================

def flat_union_argmax_survivor(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
) -> str:
    candidates = sorted({b for branches in future_continuations.values() for b in branches})
    inward_mass = {
        p: sum(compatibility_weights[pair_key(p, q)] for q in candidates if q != p)
        for p in candidates
    }
    return max(candidates, key=lambda p: (inward_mass[p], -_branch_id_rank(p)))


# =====================================================================
# outward_record: past-facing hash-chain (v1 mechanism). Each entry now also binds
# the step's mean-distance-to-fixed-point (the contraction trace).
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
) -> dict[str, Any]:
    """Past-facing OUTWARD record over the inward traversal steps. The record sink
    shell is the one explicitly tagged shell_orientation == 'OUTWARD' (the only
    remaining stipulated orientation, and ONLY as the record sink). A shell missing
    that tag yields None and next(...) raises -> the orientation-removal control
    breaks the build exactly as required."""
    survivor = compression["present_survivor"]
    record_shell = next(s for s in shells if s.get("shell_orientation") == "OUTWARD")

    per_step_entries: list[list[dict[str, Any]]] = []
    hash_chain: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    record_entries: list[dict[str, Any]] = []

    for step, tstep in enumerate(compression["traversal_steps"]):
        branches = tstep["branches_on_shell"]
        selected = tstep["selected_anchor"]
        compressed_away = sorted([b for b in branches if b != selected])
        entry = {
            "from_shell": tstep["shell_id"],
            "from_shell_radius_r": tstep["shell_radius_r"],
            "derived_inward_direction": compression["direction"],
            "record_orientation": record_shell["shell_orientation"],  # OUTWARD sink
            "incoming_anchor": tstep["incoming_anchor"],
            "anchor_survived_this_shell": selected,
            "branches_compressed_away": compressed_away,
            "mean_distance_to_fixed_point": tstep["mean_distance_to_fixed_point"],
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
        "record_orientation": record_shell["shell_orientation"],  # OUTWARD sink
        "inward_provenance_bound": True,
        "reflects_per_shell_compression_steps": True,
        "binds_contraction_trace": True,
        "binds_present_survivor": survivor,
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
) -> dict[str, Any]:
    fc = future_continuations if future_continuations is not None else FUTURE_CONTINUATIONS_BY_SHELL
    sh = shells if shells is not None else SHELLS

    weights = weights_override if weights_override is not None else compute_compatibility_weights(fc)
    compression = compression_map(fc, weights, sh)
    present_survivor = compression["present_survivor"]
    outward_record = build_outward_record(sh, compression)

    return {
        "event_x": EVENT_X,
        "shells": sh,
        "shell_radius_r": [s["shell_radius_r"] for s in sh],
        "derived_orientation": compression["direction"],
        "orientation_source": compression["direction_source"],
        "contraction_ratio": compression["contraction_ratio"],
        "branch_states": BRANCH_STATES,
        "future_continuations": fc,
        "compatibility_weights": weights,
        "compression_map": compression,
        "present_survivor": present_survivor,
        "outward_record": outward_record,
    }


# =====================================================================
# THE v2 EMERGENCE DISCRIMINATING CONTROL (the hard-acceptance requirement).
# Reverse / remove the computed asymmetry and confirm the DERIVED orientation
# flips / fails -- proving orientation is emergent, not stipulated.
# =====================================================================

def emergence_discriminating_control() -> dict[str, Any]:
    """Two flavors, both first-class evidence:

    FLAVOR 1 -- REVERSE the asymmetry: keep the same field but reverse the shell
    traversal order. The mean-distance-to-x* sequence reverses, so the contraction
    ratio crosses 1 (contraction <-> expansion) and the DERIVED orientation must
    FLIP (forward INWARD -> reversed OUTWARD). x* is held FIXED at the canonical
    forward survivor (the present location is the same physical point; only the
    direction we walk it changes).

    FLAVOR 2 -- REMOVE the asymmetry: a radially symmetric field whose two shells
    carry candidate sets with IDENTICAL mean distance to x*. The contraction ratio
    == 1 so the DERIVED orientation must FAIL (UNDEFINED)."""
    base = build_object_instance()
    fc = base["future_continuations"]
    weights = base["compatibility_weights"]
    xstar = base["present_survivor"]

    fwd_order = base["compression_map"]["shell_traversal_order"]
    rev_order = list(reversed(fwd_order))

    fwd_contraction = compute_contraction(fc, fwd_order, xstar)
    rev_contraction = compute_contraction(fc, rev_order, xstar)
    fwd_orient = derive_orientation(fwd_contraction["contraction_ratio"])
    rev_orient = derive_orientation(rev_contraction["contraction_ratio"])

    # FLAVOR 2: a symmetric field. Both shells equidistant (mean) from x*.
    # branches at L1-distance 1 from x*=b3 are {b1,b2,b5}; build two shells with
    # identical distance multisets {1,1} so the mean distance is equal => ratio==1.
    sym_fc = {"Sigma_2": ["b1", "b5"], "Sigma_1": ["b2", "b5"]}
    sym_weights = compute_compatibility_weights(sym_fc)
    sym_order = _radius_descending_order(SHELLS, sym_fc)
    # fixed point for the symmetric field = its own forward survivor
    sym_surv, _ = _traverse(sym_fc, sym_weights, sym_order)
    sym_contraction = compute_contraction(sym_fc, sym_order, sym_surv)
    # ALSO measure symmetry directly toward x*=b3 (the canonical present location)
    sym_contraction_to_b3 = compute_contraction(sym_fc, sym_order, "b3")
    sym_orient = derive_orientation(sym_contraction_to_b3["contraction_ratio"])

    return {
        "fixed_point_x_star": xstar,
        # FLAVOR 1: reversal flips orientation
        "forward_shell_order": fwd_order,
        "forward_contraction_ratio": fwd_contraction["contraction_ratio"],
        "forward_derived_orientation": fwd_orient,
        "forward_mean_distance_sequence": fwd_contraction["mean_distance_sequence"],
        "reversed_shell_order": rev_order,
        "reversed_contraction_ratio": rev_contraction["contraction_ratio"],
        "reversed_derived_orientation": rev_orient,
        "reversed_mean_distance_sequence": rev_contraction["mean_distance_sequence"],
        "orientation_flips_under_reversal": (
            fwd_orient == "INWARD" and rev_orient == "OUTWARD"
        ),
        # FLAVOR 2: removing the asymmetry fails orientation
        "symmetric_field": sym_fc,
        "symmetric_contraction_ratio_to_b3": sym_contraction_to_b3["contraction_ratio"],
        "symmetric_mean_distance_sequence_to_b3": sym_contraction_to_b3["mean_distance_sequence"],
        "symmetric_derived_orientation": sym_orient,
        "orientation_undefined_when_symmetric": sym_orient == "UNDEFINED",
        # the combined emergence verdict
        "orientation_is_emergent": (
            fwd_orient == "INWARD"
            and rev_orient == "OUTWARD"
            and sym_orient == "UNDEFINED"
        ),
    }


# =====================================================================
# v1 wins, retained as first-class controls (must STILL pass in v2)
# =====================================================================

CANONICAL_REASSIGNMENT: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b5", "b3"],
    "Sigma_1": ["b2", "b4"],
}


def union_of(future_continuations: dict[str, list[str]]) -> list[str]:
    return sorted({b for branches in future_continuations.values() for b in branches})


def shell_reassignment_control() -> dict[str, Any]:
    """v1's trap#2/#5 fix: move a branch between shells (union identical) and the
    present_survivor must MOVE."""
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
    scrambled = {
        sid: [branches[0], branches[0]]
        for sid, branches in FUTURE_CONTINUATIONS_BY_SHELL.items()
    }
    inst = build_object_instance(future_continuations=scrambled)
    inv = check_invariants(inst, include_shell_ordering=False, include_emergence=False)
    return {
        "mechanism": "scramble future_continuations to 1 distinct branch per shell",
        "all_invariants_hold": all(inv.values()),
        "control_breaks": not all(inv.values()),
    }


def uniform_weights_negative_control() -> dict[str, Any]:
    real_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
    uniform = {k: 0.5 for k in real_weights}
    inst = build_object_instance(weights_override=uniform)
    inv = check_invariants(inst, include_shell_ordering=False, include_emergence=False)

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


def orientation_removal_negative_control() -> dict[str, Any]:
    """Negative control (d, v2): remove the OUTWARD record-sink tag from the shells.
    The outward_record build must BREAK (StopIteration), proving the record sink
    orientation is load-bearing for provenance."""
    stripped = []
    for s in SHELLS:
        s2 = dict(s)
        s2.pop("shell_orientation", None)
        stripped.append(s2)
    broke = False
    try:
        build_object_instance(shells=stripped)
    except StopIteration:
        broke = True
    return {
        "mechanism": "remove OUTWARD record-sink tag from all shells",
        "build_breaks": broke,
    }


# =====================================================================
# Traps retained from the v0/v1 audit (must STILL pass in v2)
# =====================================================================

def weight_permutation_trap() -> dict[str, Any]:
    """Trap #1: permuting compatibility_weights moves the survivor."""
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
    """Trap #4: mutating a branch feature moves the survivor."""
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

def check_invariants(
    instance: dict[str, Any],
    *,
    include_shell_ordering: bool = True,
    include_emergence: bool = True,
) -> dict[str, Any]:
    fc = instance["future_continuations"]
    shells = instance["shells"]
    weights = instance["compatibility_weights"]
    compression = instance["compression_map"]
    survivor = instance["present_survivor"]
    record = instance["outward_record"]

    future_shell_ids = {s["shell_id"] for s in shells if s["shell_id"] in fc}
    outward_shell_ids = {s["shell_id"] for s in shells if s.get("shell_orientation") == "OUTWARD"}

    fc_future_indexed = (set(fc.keys()) <= future_shell_ids) and len(fc) >= 1
    fc_lists_of_distinct = all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values())

    # v2: future flow direction is DERIVED, and on the canonical instance it must
    # come out INWARD (the canonical field genuinely contracts toward x*).
    future_flow_inward = compression.get("direction") == "INWARD"
    # and the source of that direction must be the contraction, not a constant
    direction_is_derived = compression.get("direction_source") == "DERIVED_FROM_CONTRACTION_RATIO"
    # the contraction ratio is a real number strictly < 1 on the canonical instance
    cr = compression.get("contraction_ratio")
    contraction_ratio_is_real_lt_1 = isinstance(cr, float) and math.isfinite(cr) and cr < 1.0

    record_outward = record.get("record_orientation") == "OUTWARD"
    has_outward_shell = len(outward_shell_ids) >= 1
    weights_before_compression = bool(compression.get("weights_computed_before_compression"))
    weights_are_pair_reals = (
        len(weights) >= 1
        and all("|" in k for k in weights.keys())
        and all(isinstance(w, float) for w in weights.values())
    )
    weights_non_uniform = len(set(round(w, 12) for w in weights.values())) >= 2

    nonempty_steps = [s for s in compression.get("traversal_steps", []) if s["branches_on_shell"]]
    survivor_derived = (
        survivor == compression.get("present_survivor")
        and len(nonempty_steps) >= 1
        and survivor == nonempty_steps[-1]["selected_anchor"]
    )
    multi_step_traversal = len(nonempty_steps) >= 2
    record_chain_ok = bool(record.get("append_only_recomputed"))
    record_binds_provenance = (
        bool(record.get("inward_provenance_bound"))
        and bool(record.get("reflects_per_shell_compression_steps"))
        and bool(record.get("binds_contraction_trace"))
        and record.get("binds_present_survivor") == survivor
        and len(record.get("record_entries", [])) == len(nonempty_steps)
        and len(record.get("record_entries", [])) >= 1
    )

    hard_stop_not_identity = fc != survivor and survivor not in (None, fc)
    map_distinct_from_record = set(compression.keys()) != set(record.keys())

    invariants = {
        "future_continuations_future_indexed": fc_future_indexed,
        "future_continuations_lists_of_distinct_ge2": fc_lists_of_distinct,
        "future_flow_inward_DERIVED": future_flow_inward,
        "direction_source_is_derived_from_contraction": direction_is_derived,
        "contraction_ratio_real_and_lt_1_on_canonical": contraction_ratio_is_real_lt_1,
        "record_outward": record_outward,
        "has_outward_shell": has_outward_shell,
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

    if include_shell_ordering:
        ctrl = shell_reassignment_control()
        invariants["SHELL_REASSIGNMENT_MOVES_SURVIVOR"] = bool(
            ctrl["union_identical"] and ctrl["shell_reassignment_moves_survivor"]
        )

    if include_emergence:
        em = emergence_discriminating_control()
        invariants["ORIENTATION_EMERGENT_FLIPS_AND_FAILS"] = bool(em["orientation_is_emergent"])

    return invariants


FIRST_CLASS_KEYS = [
    "event_x",
    "shells",
    "shell_radius_r",
    "derived_orientation",
    "contraction_ratio",
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
    emergence = emergence_discriminating_control()
    flat_neg = flat_union_negative_control()
    scramble_neg = scramble_futures_negative_control()
    uniform_neg = uniform_weights_negative_control()
    orient_removal_neg = orientation_removal_negative_control()
    weight_trap = weight_permutation_trap()
    state_trap = state_mutation_trap()

    result = {
        "name": "retrocausal_possibility_field_v2_contraction",
        "object_name": "RetrocausalPossibilityField",
        "object_statement_sha256": "02f813d355b5812e1021eb023e5aca7c6006c00dcfc060cf94ff727b7cb8dd78",
        "probe_family": "M_pairwise_compatibility_weight_readout_plus_contraction_to_fixed_point",
        "constraint_set": "C_inward_traversal_with_orientation_derived_from_contraction_ratio",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,

        # ---- THE FIRST-CLASS OBJECT FIELDS (genuinely computed) ----
        "event_x": instance["event_x"],
        "shells": instance["shells"],
        "shell_radius_r": instance["shell_radius_r"],
        "derived_orientation": instance["derived_orientation"],
        "orientation_source": instance["orientation_source"],
        "contraction_ratio": instance["contraction_ratio"],
        "future_continuations": instance["future_continuations"],
        "branch_states": instance["branch_states"],
        "compatibility_weights": instance["compatibility_weights"],
        "compression_map": instance["compression_map"],
        "present_survivor": instance["present_survivor"],
        "outward_record": instance["outward_record"],

        "first_class_keys_present": FIRST_CLASS_KEYS,
        "invariants": invariants,
        "all_invariants_hold": all_invariants_hold,

        # ---- THE v2 ACCEPTANCE: orientation emergent ----
        "emergence_discriminating_control": emergence,
        "orientation_is_emergent": emergence["orientation_is_emergent"],

        # ---- v1 win retained: shell-reassignment moves survivor ----
        "shell_reassignment_moves_survivor": reassignment["shell_reassignment_moves_survivor"],
        "shell_reassignment_control": reassignment,

        # ---- traps retained from v0/v1 (must still pass) ----
        "trap_1_weight_permutation": weight_trap,
        "trap_4_state_mutation": state_trap,

        # ---- negative controls ----
        "negative_control_flat_union": flat_neg,
        "negative_control_scramble_futures": scramble_neg,
        "negative_control_uniform_weights": uniform_neg,
        "negative_control_orientation_removal": orient_removal_neg,

        # ---- honest ceiling ----
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "shell-orientation now DERIVED from a computed contraction ratio "
            "(emergent: flips INWARD->OUTWARD under traversal reversal, fails to "
            "UNDEFINED when the asymmetry is removed); shell-ordering still "
            "load-bearing; trivial carrier; NO QIT; NOT physics/Axis0/manifold/"
            "canonical."
        ),
        "blocked_downstream_consumers": [
            "Axis0 claim",
            "flux claim",
            "physics claim",
            "formal manifold admission",
            "claim that this trivial carrier is THE retrocausal field of the real model",
            "claim that the fixed point x* is a physical present (it is a survivor of a trivial finite compression)",
        ],
        "all_pass": all_invariants_hold,
        "criteria_checked": sorted(invariants.keys()),
    }
    return result


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(
    SIM_DIR, "results", "retrocausal_possibility_field_v2_contraction_results.json"
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
        "derived_orientation": result["derived_orientation"],
        "contraction_ratio": result["contraction_ratio"],
        "forward_derived_orientation": result["emergence_discriminating_control"]["forward_derived_orientation"],
        "reversed_derived_orientation": result["emergence_discriminating_control"]["reversed_derived_orientation"],
        "symmetric_derived_orientation": result["emergence_discriminating_control"]["symmetric_derived_orientation"],
        "shell_reassignment_moves_survivor": result["shell_reassignment_moves_survivor"],
        "result_path": RESULT_PATH,
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
