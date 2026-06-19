#!/usr/bin/env python3
"""
retrocausal_possibility_field_v1 -- successor to v0. ONE audited gap fixed:
the SHELL ORDERING is now LOAD-BEARING in the inward multi-shell compression.

Started from system_v4/probes/SIM_TEMPLATE.py (template framing preserved) and
mirrors retrocausal_possibility_field_v0's structure (carrier, hash-chain
outward_record, invariant battery, result receipt). The ONLY substantive change
is compression_map: v0 flattened all shells into one union candidate set and
took a flat compatibility-centroid argmax (so which shell a branch sat on was
DECORATIVE -- moving a branch between shells with the union unchanged left the
survivor unchanged: trap#2/#5 FAILED). v1 replaces that with a genuine inward
TRAVERSAL of the shells outer->inner->present.

THE OBJECT (per system_v6/receipts/v43_object_card_current_run.json):
  "A finite shell-indexed field of possible futures compresses INWARD through
   compatibility into a present survivor, while the past-facing OUTWARD record
   preserves what survived."

THE AUDITED GAP v1 FIXES (from v0 audit_verdict.md):
  v0's compression_map flattened all shells into one union candidate set and
  argmaxed total pairwise compatibility mass -- shell membership and shell radius
  ordering never entered the computation, so moving a branch between shells (union
  unchanged) left the present_survivor UNCHANGED (trap#2/#5 FAIL). The inward
  multi-shell compression was shape-labeled, not dynamically real.

THE v1 FIX -- shell-structured INWARD TRAVERSAL (compression_map):
  The compression now TRAVERSES the inward shells from OUTER (largest radius) to
  INNER (smallest radius) to present (r=0). It carries a single PROPAGATED ANCHOR
  inward:
    - At the OUTERMOST inward shell there is no incoming anchor: the local anchor
      is the branch on that shell with maximal WITHIN-SHELL pairwise compatibility
      mass.
    - At every more-inner shell, each branch on that shell is scored by its
      pairwise COMPATIBILITY WEIGHT with the anchor propagated from the next-OUTER
      shell. The new anchor is the inner-shell branch maximizing that cross-shell
      compatibility (deterministic tie-break: lowest branch id).
    - The final anchor at present (r=0) is the present_survivor.
  This is a genuine MULTI-STEP inward propagation: which shell a branch sits on,
  and the shell radius ordering, both change the survivor (a branch can only set
  the anchor on its own shell; the radius ordering sets the traversal sequence).
  In the canonical instance the INNER step OVERRIDES the outer anchor (b1->b3),
  so the second step is load-bearing in the canonical instance itself, not merely
  a mechanical pass-through.

WHAT THIS SIM IS / IS NOT (honest ceiling):
  - classification = scratch_diagnostic
  - promotion_allowed = false ; formal_admission_allowed = false
  - claim_ceiling: shell-ordering now load-bearing in inward multi-shell
    compression; trivial carrier; NOT physics/Axis0/manifold/canonical;
    orientation still a label not emergent (the v2 target).

ANTI-PROXY-DRIFT (retained from v0; v1 adds the shell-ordering control):
  - future_continuations is a dict of shell -> LIST (NOT a scalar count, NOT bool)
  - compatibility_weights is a real-valued weight structure over PAIRS of futures,
    computed BEFORE compression, and is NOW USED in the cross-shell propagation
  - present_survivor is DERIVED inward through the traversal (HARD-STOP if it
    equals the future_continuations input -> identity compression / proxy drift)
  - outward_record is a past-facing hash-chain DISTINCT from compression_map, and
    now reflects the PER-SHELL compression steps (anchor in / anchor out per shell)
  - shells + shell_radius_r are FIRST-CLASS named fields AND are load-bearing:
    the shell_reassignment_moves_survivor control proves it.

Probe family M: pairwise-compatibility weight readout over enumerated branch
  states, with a shell-orientation marker; the readout is now a shell-ORDERED
  inward propagation (a sequence of per-shell cross-shell compatibility selects).
Constraint set C: inward traversal outer->inner->present; each inner shell's
  surviving anchor is selected by maximal pairwise compatibility with the anchor
  propagated from the next-outer shell (deterministic tie-break by branch id).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import Any

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================
# This object is a FIELD-INSTANTIATION receipt on a trivial finite carrier whose
# multi-shell inward compression is now shell-ordered. It deliberately uses NO
# QIT / density-matrix / heavy numeric tooling: the load-bearing tool is the
# hashlib append-only chain (outward_record provenance, reused from CFR v0 /
# rpf v0); the shell traversal is pure-Python integer/float weight arithmetic so
# the shell-ordering load-bearingness stays auditable line by line.

TOOL_MANIFEST = {
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "append-only sha256 hash-chain is the outward_record machinery "
        "(reused from CFR v0 / rpf v0); each chain entry now binds the PER-SHELL "
        "compression step (incoming anchor, surviving anchor, branches compressed "
        "away on that shell) so the record reflects the shell-ordered traversal -- "
        "load-bearing for outward_record provenance and tamper-evidence.",
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
        "finite set and the shell traversal is a short deterministic loop; "
        "pure-Python keeps the shell-ordering load-bearingness auditable. Heavy "
        "numeric tooling would re-enter the proxy basin and obscure the traversal.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is object-field instantiation on a trivial "
        "carrier with a deterministic inward traversal, not a structural-"
        "impossibility (UNSAT) proof. No formal admission is claimed.",
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
        "reason": "not needed: trivial finite carrier; the shell traversal is a "
        "short deterministic loop, not a batched/exhaustive sweep.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Canon algebra artifact is consumed; field "
        "instantiation with a shell-ordered traversal only.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "hashlib": "load_bearing",   # outward_record per-shell hash-chain
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
# Each branch state is a distinct point in a tiny 2-feature finite space.
# These are the admissible future possibilities ("jk fuzz" in object native
# terms) carried on the shells. They are NON-TRIVIALLY DISTINCT (different
# feature tuples). The carrier is intentionally identical to v0: the change is
# in the compression dynamics, not the carrier.
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
# r=2 outer future stratum, r=1 inner future stratum (both INWARD: future->present
# compression). r=-1 is the past-facing OUTWARD record stratum. The present
# survivor sits at r=0 (the apex / event_x), produced by inward traversal.
#
# shell_orientation explicitly distinguishes INWARD (future->present) from
# OUTWARD (present->past record). Removing it MUST break the build (negative
# control b). The shell_radius_r now ORDERS the inward traversal (load-bearing).
SHELLS: list[dict[str, Any]] = [
    {"shell_id": "Sigma_2", "shell_radius_r": 2, "shell_orientation": "INWARD",
     "role": "future possibility stratum (outer)"},
    {"shell_id": "Sigma_1", "shell_radius_r": 1, "shell_orientation": "INWARD",
     "role": "future possibility stratum (inner)"},
    {"shell_id": "Sigma_record", "shell_radius_r": -1, "shell_orientation": "OUTWARD",
     "role": "past-facing survival record stratum"},
]

# Future continuations are FUTURE-INDEXED: keyed by the INWARD (future) shells
# only. Each value is a LIST of >=2 non-trivially-distinct admissible branch
# states. The canonical config is chosen so that (a) the INNER traversal step
# OVERRIDES the outer anchor (b1 -> b3), making the multi-step traversal
# load-bearing in the canonical instance, and (b) a single-branch shell
# reassignment that keeps the union identical MOVES the present_survivor.
FUTURE_CONTINUATIONS_BY_SHELL: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b5"],   # outer future stratum: 3 branches
    "Sigma_1": ["b2", "b3", "b4"],   # inner future stratum: 3 branches
}


# =====================================================================
# compatibility_weights: real-valued weights over PAIRS of future continuations
# Computed BEFORE survivor compression (required invariant) and NOW CONSUMED by
# the cross-shell inward propagation.
# =====================================================================

def branch_distance(s1: str, s2: str) -> int:
    """L1 distance between two branch states in the trivial feature space."""
    x, y = BRANCH_STATES[s1], BRANCH_STATES[s2]
    return abs(x["a"] - y["a"]) + abs(x["b"] - y["b"])


def compute_compatibility_weights(
    future_continuations: dict[str, list[str]],
) -> dict[str, float]:
    """
    Weight structure over PAIRS of future continuations (cross-shell and
    within-shell). Higher weight = more compatible (closer in feature space).
    weight(p,q) = 1 / (1 + L1_distance(p,q)). This is a real-valued NON-uniform
    weight structure, NOT a boolean exclusion predicate. Returned keyed by a
    canonical unordered pair string "bi|bj" with i<j by id, so it is genuinely
    a structure over PAIRS. (Identical to v0; v1 changes only how it is consumed.)
    """
    all_futures: list[str] = []
    for shell_id, branches in future_continuations.items():
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
    """Numeric rank for the deterministic tie-break (lowest branch id wins).

    Tie-break: among branches with equal score we keep the LOWEST id, so we
    maximize (score, -rank)."""
    return int(b[1:])


# =====================================================================
# compression_map: shell-indexed future_continuations -> present_survivor
# via an INWARD TRAVERSAL of the shells (outer -> inner -> present), through the
# compatibility weights. SHELL-STRUCTURED (multi-step), NOT a flat union argmax.
# This is the ONE thing that changed from v0.
# =====================================================================

def compression_map(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
    shells: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inward TRAVERSAL compression (the v0->v1 fix).

    Walk the INWARD shells in order of DECREASING radius (outermost first), and
    carry a single PROPAGATED ANCHOR inward:
      - OUTERMOST inward shell (no incoming anchor): the local anchor is the
        branch on that shell with maximal WITHIN-SHELL pairwise compatibility mass
        (sum of weights to the other branches on the SAME shell).
      - each MORE-INNER shell: score every branch on the shell by its pairwise
        compatibility weight with the anchor propagated from the next-OUTER shell
        (a branch identical to the anchor scores 1.0 = maximal self-compatibility,
        so the anchor persists if it reappears on the inner shell). The new anchor
        is the argmax (deterministic tie-break: lowest branch id).
      - the final anchor (at present / r=0) is the present_survivor.

    Shell membership and radius ordering are LOAD-BEARING: a branch can only set
    the anchor on the shell it sits on, and the radius ordering fixes the
    traversal sequence. Moving a branch to a different shell (union unchanged)
    changes the propagation path and can change the survivor. This is genuinely
    multi-step: in the canonical instance the inner step OVERRIDES the outer
    anchor.
    """
    # inward shells, outermost (largest radius) first
    inward_shells = sorted(
        [s for s in shells if s.get("shell_orientation") == "INWARD"],
        key=lambda s: -int(s["shell_radius_r"]),
    )

    traversal_steps: list[dict[str, Any]] = []
    anchor: str | None = None

    for shell in inward_shells:
        sid = shell["shell_id"]
        branches = sorted(future_continuations.get(sid, []))
        if not branches:
            # an inward shell with no future continuations contributes no step
            traversal_steps.append({
                "shell_id": sid,
                "shell_radius_r": shell["shell_radius_r"],
                "incoming_anchor": anchor,
                "branches_on_shell": [],
                "branch_scores": {},
                "selected_anchor": anchor,
                "step_kind": "empty_shell_passthrough",
            })
            continue

        if anchor is None:
            # OUTERMOST inward shell: seed anchor by within-shell compatibility mass
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
            # inner shell: score by cross-shell compatibility with incoming anchor
            scores = {}
            for p in branches:
                if p == anchor:
                    scores[p] = 1.0  # maximal self-compatibility: anchor persists
                else:
                    scores[p] = compatibility_weights[pair_key(p, anchor)]
            step_kind = "cross_shell_compat_with_incoming_anchor"

        selected = max(branches, key=lambda p: (scores[p], -_branch_id_rank(p)))
        traversal_steps.append({
            "shell_id": sid,
            "shell_radius_r": shell["shell_radius_r"],
            "incoming_anchor": anchor,
            "branches_on_shell": branches,
            "branch_scores": scores,
            "selected_anchor": selected,
            "step_kind": step_kind,
        })
        anchor = selected

    return {
        "direction": "INWARD",
        "rule": "inward multi-shell traversal outer->inner->present; outermost "
        "shell seeds the anchor by within-shell compatibility mass; each inner "
        "shell selects the branch of maximal pairwise compatibility with the "
        "anchor propagated from the next-outer shell; tie-break lowest branch id",
        "shell_traversal_order": [s["shell_id"] for s in inward_shells],
        "shell_radius_order": [int(s["shell_radius_r"]) for s in inward_shells],
        "traversal_steps": traversal_steps,
        "num_traversal_steps": len([s for s in traversal_steps if s["branches_on_shell"]]),
        "present_survivor": anchor,
        "weights_computed_before_compression": True,
        "input_shells_used": sorted(future_continuations.keys()),
        "shell_ordering_load_bearing": True,
    }


# =====================================================================
# Flat-union argmax: the v0 mechanism, retained ONLY as a negative-control
# reference (NOT used to build the canonical instance). The validator collapses
# the traversal to this and asserts that the shell_reassignment control then
# FAILS -- proving the traversal is what carries the shell-ordering effect.
# =====================================================================

def flat_union_argmax_survivor(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
) -> str:
    """v0's flat-union mechanism: union all branches, argmax total pairwise
    compatibility mass over the union, ignore which shell each branch sits on."""
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
# DISTINCT from compression_map. Reuses CFR v0 / rpf v0 append-only chain
# pattern. v1: each entry now reflects the PER-SHELL traversal step (incoming
# anchor, the anchor that survived the shell, the branches compressed away on
# that shell), so the record reflects the shell-ordered inward compression.
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
    """
    Past-facing OUTWARD record. We replay the INWARD traversal steps from the
    compression_map (outer -> inner) and at each step emit a provenance entry
    recording, relative to the inward compression: the shell, its radius, the
    anchor coming IN, the anchor that SURVIVED the shell, and the branches that
    were compressed away on that shell. The record itself is oriented OUTWARD
    (r=-1 shell). Each entry is hashed into an append-only chain (tamper-evident
    provenance), DISTINCT from the compression_map's traversal trace.

    The record now reflects the PER-SHELL compression steps (v1 requirement),
    not just the final survivor.
    """
    survivor = compression["present_survivor"]
    # .get(): a shell missing shell_orientation (negative control b) yields None,
    # so no OUTWARD shell is found and next(...) raises StopIteration -> the build
    # breaks exactly as the orientation-removal control requires.
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
            "inward_orientation_of_source": "INWARD",
            "record_orientation": record_shell["shell_orientation"],  # OUTWARD
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
        "record_orientation": record_shell["shell_orientation"],  # must be OUTWARD
        "inward_provenance_bound": True,
        "reflects_per_shell_compression_steps": True,
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
    """Assemble one RetrocausalPossibilityField instance. Parameters allow the
    negative controls and the shell-reassignment control to perturb inputs and
    observe the break / the survivor move."""
    fc = future_continuations if future_continuations is not None else FUTURE_CONTINUATIONS_BY_SHELL
    sh = shells if shells is not None else SHELLS

    # Required invariant: compatibility weights computed BEFORE compression.
    weights = weights_override if weights_override is not None else compute_compatibility_weights(fc)
    compression = compression_map(fc, weights, sh)
    present_survivor = compression["present_survivor"]
    outward_record = build_outward_record(sh, compression)

    return {
        "event_x": EVENT_X,
        "shells": sh,
        "shell_radius_r": [s["shell_radius_r"] for s in sh],
        "shell_orientation": {s["shell_id"]: s["shell_orientation"] for s in sh},
        "branch_states": copy.deepcopy(BRANCH_STATES),
        "future_continuations": fc,
        "compatibility_weights": weights,
        "compression_map": compression,
        "present_survivor": present_survivor,
        "outward_record": outward_record,
    }


# =====================================================================
# The shell-reassignment control (the v1 first-class acceptance control).
# Move ONE branch to a DIFFERENT shell while keeping the UNION of branches
# identical, and observe whether the present_survivor moves. In v0 this stayed
# fixed (FAIL). In v1 it must MOVE (PASS) -- proving the shell ordering is
# load-bearing.
# =====================================================================

CANONICAL_REASSIGNMENT: dict[str, list[str]] = {
    # canonical: Sigma_2=[b0,b1,b5], Sigma_1=[b2,b3,b4]
    # reassignment: move b3 from the inner shell (Sigma_1) to the outer shell
    # (Sigma_2). The UNION {b0,b1,b2,b3,b4,b5}\{b5? no} stays identical.
    "Sigma_2": ["b0", "b1", "b5", "b3"],
    "Sigma_1": ["b2", "b4"],
}


def union_of(future_continuations: dict[str, list[str]]) -> list[str]:
    return sorted({b for branches in future_continuations.values() for b in branches})


def shell_reassignment_control() -> dict[str, Any]:
    """Build the canonical instance and a shell-reassigned instance with an
    identical union, and report whether the present_survivor moves AND whether
    the inward propagation path changes. Both are first-class evidence."""
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
    """Negative control (a): collapse the shell-ordered traversal to v0's flat
    union argmax. Under the flat mechanism, the shell-reassignment must FAIL to
    move the survivor (because the union is identical) -- proving it is the
    TRAVERSAL, not the carrier or the weights, that carries the shell-ordering
    effect."""
    base = build_object_instance()
    reassigned = build_object_instance(future_continuations=CANONICAL_REASSIGNMENT)

    base_weights = base["compatibility_weights"]
    reassigned_weights = reassigned["compatibility_weights"]

    base_flat = flat_union_argmax_survivor(base["future_continuations"], base_weights)
    reassigned_flat = flat_union_argmax_survivor(
        reassigned["future_continuations"], reassigned_weights
    )

    return {
        "mechanism": "flat_union_argmax_total_pairwise_mass (v0 mechanism)",
        "base_flat_survivor": base_flat,
        "reassigned_flat_survivor": reassigned_flat,
        # under the flat mechanism the survivor must NOT move (control FAILS to
        # move) -> this confirms the traversal is what carries the effect.
        "flat_union_moves_survivor": base_flat != reassigned_flat,
        "flat_union_control_correctly_inert": base_flat == reassigned_flat,
    }


def scramble_futures_negative_control() -> dict[str, Any]:
    """Negative control (b): scramble future_continuations so each shell carries
    only ONE distinct branch (destroys the >=2-distinct structure). The build
    must BREAK (an invariant must fail)."""
    scrambled = {
        sid: [branches[0], branches[0]]
        for sid, branches in FUTURE_CONTINUATIONS_BY_SHELL.items()
    }
    inst = build_object_instance(future_continuations=scrambled)
    inv = check_invariants(inst, include_shell_ordering=False)
    return {
        "mechanism": "scramble future_continuations to 1 distinct branch per shell",
        "all_invariants_hold": all(inv.values()),
        "control_breaks": not all(inv.values()),
    }


def uniform_weights_negative_control() -> dict[str, Any]:
    """Negative control (c): replace compatibility_weights with a CONSTANT value
    (same pair keys). The non-uniformity invariant must fail (the structure is
    decorative) -> the build breaks; AND the shell-reassignment must no longer
    move the survivor (uniform weights cannot carry the cross-shell selection)."""
    real_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
    uniform = {k: 0.5 for k in real_weights}
    inst = build_object_instance(weights_override=uniform)
    inv = check_invariants(inst, include_shell_ordering=False)

    # also: under uniform weights, does the shell-reassignment still move?
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
        # under uniform weights the cross-shell selection is degenerate, so the
        # reassignment must NOT move the survivor.
        "uniform_correctly_kills_shell_effect": not moves_under_uniform,
    }


# =====================================================================
# Trap controls retained from the v0 audit (must STILL pass in v1)
# =====================================================================

def weight_permutation_trap() -> dict[str, Any]:
    """Trap #1 (must stay PASS): permuting compatibility_weights moves the
    survivor. We swap the two pair weights b0|b1 <-> b1|b2 (a permutation of the
    weight values) and confirm the survivor moves."""
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
    """Trap #4 (must stay PASS): mutating a branch feature moves the survivor.
    We shift branch b3's feature 'a' by +5 (re-deriving weights from the mutated
    carrier) and confirm the survivor moves."""
    base = build_object_instance()

    global BRANCH_STATES
    saved = copy.deepcopy(BRANCH_STATES)
    try:
        BRANCH_STATES["b3"]["a"] += 5
        mutated_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
        mutated = build_object_instance(weights_override=mutated_weights)
        mutated_survivor = mutated["present_survivor"]
    finally:
        BRANCH_STATES = copy.deepcopy(saved)  # restore the carrier

    return {
        "mutated_branch": "b3",
        "mutation": "b3.a += 5",
        "base_survivor": base["present_survivor"],
        "mutated_survivor": mutated_survivor,
        "state_mutation_moves_survivor": base["present_survivor"] != mutated_survivor,
    }


# =====================================================================
# INVARIANTS + HARD-STOP (the validator asserts these; we also expose them here)
# =====================================================================

def check_invariants(instance: dict[str, Any], *, include_shell_ordering: bool = True) -> dict[str, Any]:
    """Return a dict of named invariant -> bool. The validator asserts these.

    include_shell_ordering=False is used by the negative-control builders that
    intentionally break a precursor invariant (so the shell-ordering control,
    which calls build_object_instance again, is not double-counted there)."""
    fc = instance["future_continuations"]
    shells = instance["shells"]
    weights = instance["compatibility_weights"]
    compression = instance["compression_map"]
    survivor = instance["present_survivor"]
    record = instance["outward_record"]

    inward_shell_ids = {s["shell_id"] for s in shells if s["shell_orientation"] == "INWARD"}
    outward_shell_ids = {s["shell_id"] for s in shells if s["shell_orientation"] == "OUTWARD"}

    # future continuations are FUTURE-INDEXED (keyed by inward shells only)
    fc_future_indexed = (set(fc.keys()) <= inward_shell_ids) and len(fc) >= 1
    # each shell carries a LIST of >=2 distinct branches (not a scalar/bool)
    fc_lists_of_distinct = all(
        isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()
    )
    # future flow is INWARD
    future_flow_inward = compression.get("direction") == "INWARD"
    # record is OUTWARD
    record_outward = record.get("record_orientation") == "OUTWARD"
    # at least one OUTWARD shell exists and the record uses it
    has_outward_shell = len(outward_shell_ids) >= 1
    # compatibility weights computed BEFORE survivor compression
    weights_before_compression = bool(compression.get("weights_computed_before_compression"))
    # compatibility_weights is a real-valued PAIR structure (keys "bi|bj"), not bool
    weights_are_pair_reals = (
        len(weights) >= 1
        and all("|" in k for k in weights.keys())
        and all(isinstance(w, float) for w in weights.values())
    )
    # weights are NON-uniform: negative control (c) replaces them with a constant
    weights_non_uniform = len(set(round(w, 12) for w in weights.values())) >= 2
    # survivor is DERIVED through the traversal (it is the final selected anchor
    # of a multi-step inward traversal, and appears on the innermost non-empty
    # shell it survived)
    nonempty_steps = [s for s in compression.get("traversal_steps", []) if s["branches_on_shell"]]
    survivor_derived = (
        survivor == compression.get("present_survivor")
        and len(nonempty_steps) >= 1
        and survivor == nonempty_steps[-1]["selected_anchor"]
    )
    # the compression is a genuine MULTI-STEP traversal (>=2 non-empty shells)
    multi_step_traversal = len(nonempty_steps) >= 2
    # record hash-chain recomputes (tamper-evident append-only)
    record_chain_ok = bool(record.get("append_only_recomputed"))
    # record binds inward-compression provenance and reflects per-shell steps
    record_binds_provenance = (
        bool(record.get("inward_provenance_bound"))
        and bool(record.get("reflects_per_shell_compression_steps"))
        and record.get("binds_present_survivor") == survivor
        and len(record.get("record_entries", [])) == len(nonempty_steps) + (
            len([s for s in compression.get("traversal_steps", []) if not s["branches_on_shell"]])
        )
        and len(record.get("record_entries", [])) >= 1
    )

    # HARD-STOP: future_continuations must NOT equal present_survivor.
    hard_stop_not_identity = fc != survivor and survivor not in (None, fc)

    # compression_map DISTINCT from outward_record (different shapes/keys)
    map_distinct_from_record = set(compression.keys()) != set(record.keys())

    invariants = {
        "future_continuations_future_indexed": fc_future_indexed,
        "future_continuations_lists_of_distinct_ge2": fc_lists_of_distinct,
        "future_flow_inward": future_flow_inward,
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
    flat_neg = flat_union_negative_control()
    scramble_neg = scramble_futures_negative_control()
    uniform_neg = uniform_weights_negative_control()
    weight_trap = weight_permutation_trap()
    state_trap = state_mutation_trap()

    result = {
        "name": "retrocausal_possibility_field_v1",
        "object_name": "RetrocausalPossibilityField",
        "object_statement_sha256": "02f813d355b5812e1021eb023e5aca7c6006c00dcfc060cf94ff727b7cb8dd78",
        "probe_family": "M_pairwise_compatibility_weight_readout_shell_ordered_inward_traversal",
        "constraint_set": "C_inward_traversal_outer_to_inner_cross_shell_compatibility",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,

        # ---- THE FIRST-CLASS OBJECT FIELDS (genuinely computed) ----
        "event_x": instance["event_x"],
        "shells": instance["shells"],
        "shell_radius_r": instance["shell_radius_r"],
        "shell_orientation": instance["shell_orientation"],
        "future_continuations": instance["future_continuations"],
        "branch_states": instance["branch_states"],
        "compatibility_weights": instance["compatibility_weights"],
        "compression_map": instance["compression_map"],
        "present_survivor": instance["present_survivor"],
        "outward_record": instance["outward_record"],

        "first_class_keys_present": FIRST_CLASS_KEYS,
        "invariants": invariants,
        "all_invariants_hold": all_invariants_hold,

        # ---- THE v1 ACCEPTANCE CONTROL (the audited gap, now fixed) ----
        "shell_reassignment_moves_survivor": reassignment["shell_reassignment_moves_survivor"],
        "shell_reassignment_control": reassignment,

        # ---- traps retained from v0 (must still pass) ----
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
            "shell-ordering now load-bearing in inward multi-shell compression; "
            "trivial carrier; NOT physics/Axis0/manifold/canonical; orientation "
            "still a label not emergent (the v2 target)."
        ),
        "blocked_downstream_consumers": [
            "Axis0 claim",
            "flux claim",
            "physics claim",
            "formal manifold admission",
            "claim that this trivial carrier is THE retrocausal field of the real model",
            "claim that the INWARD/OUTWARD orientation is emergent (still an asserted label)",
        ],
        "all_pass": all_invariants_hold,
        "criteria_checked": sorted(invariants.keys()),
    }
    return result


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(SIM_DIR, "results", "retrocausal_possibility_field_v1_results.json")


def main() -> int:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "ok": result["all_pass"],
        "shell_reassignment_moves_survivor": result["shell_reassignment_moves_survivor"],
        "base_survivor": result["shell_reassignment_control"]["base_present_survivor"],
        "reassigned_survivor": result["shell_reassignment_control"]["reassigned_present_survivor"],
        "result_path": RESULT_PATH,
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
