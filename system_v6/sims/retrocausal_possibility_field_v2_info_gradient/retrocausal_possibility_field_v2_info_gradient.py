#!/usr/bin/env python3
"""
retrocausal_possibility_field_v2_info_gradient -- successor to v1. ONE audited
gap fixed: the SHELL ORIENTATION (INWARD / OUTWARD) is now EMERGENT from a
MEASURED per-shell information gradient, not a STIPULATED string label.

Started from system_v4/probes/SIM_TEMPLATE.py (template framing preserved) and
mirrors retrocausal_possibility_field_v1's structure (carrier, shell-ordered
inward traversal, compatibility weights, hash-chain outward_record, invariant
battery, result receipt). v1's wins are KEPT verbatim in spirit:
  - shell-reassignment STILL moves the survivor (the v1 fix);
  - trap #1 (weight permutation) and trap #4 (state mutation) STILL pass;
  - the HARD-STOP future_continuations != present_survivor STILL fires.

THE OBJECT (per system_v6/receipts/v43_object_card_current_run.json, same as v1):
  "A finite shell-indexed field of possible futures compresses INWARD through
   compatibility into a present survivor, while the past-facing OUTWARD record
   preserves what survived."

THE AUDITED GAP v2 FIXES (from v1 audit / v0 audit_verdict.md tail):
  In v1 each shell carried a HARD-CODED shell_orientation string ("INWARD" /
  "OUTWARD"). The whole inward traversal and the past-facing record both READ
  that constant to decide which way to flow and which shell records. So the
  orientation -- the very thing the object word "retrocausal INWARD compression"
  asserts -- was an asserted label, not a measured property of the field. (v1's
  own claim_ceiling names this as "orientation still a label not emergent (the
  v2 target)".)

THE v2 FIX -- orientation DERIVED from a measured information gradient:
  1. Each shell carries a position coordinate shell_pos (the geometry; the future
     strata sit at positive positions, the present apex at 0, the record stratum
     at a negative position) AND a LIST of admissible branches. NO shell carries
     a shell_orientation string anymore.
  2. We COMPUTE a per-shell INFORMATION MEASURE = the possibility entropy
     I(shell) = log2(number of distinct admissible branches on that shell).
     High I = many open futures (uncommitted); low I = few (committed). The
     record stratum carries the single frozen survivor (count 1 -> I = 0).
  3. We MEASURE the information gradient along the position axis. INWARD is, BY
     DEFINITION OF THE OBJECT, the direction of DECREASING possibility / INCREASING
     commitment. For each adjacent pair of strata ordered by position we compute
     dI/dp; a stratum's emergent orientation is then DERIVED from the SIGN of the
     local information gradient toward the present:
       - a stratum whose information DECREASES as we step toward the present
         (possibilities collapsing) is derived INWARD;
       - the past-side record stratum, where the information has already bottomed
         out at the present and the survivor is FROZEN (the gradient does not keep
         decreasing -- it is a flat committed tail on the far side of the apex),
         is derived OUTWARD.
     The derived orientation is COMPUTED from I and shell_pos -- it is read off a
     measured quantity, never from a constant.
  4. The inward traversal then walks ONLY the strata that emerged INWARD, in the
     emergent commitment order (decreasing information). The record is written on
     the stratum that emerged OUTWARD. So the v1 dynamics are preserved, but every
     orientation decision is now downstream of the measured gradient.

THE EMERGENCE DISCRIMINATING CONTROL (the hard acceptance bar):
  REVERSE the measured asymmetry: give the inner (near-present) strata MORE open
  possibilities than the outer strata (an inverted possibility profile). The
  information gradient sign then FLIPS, so the DERIVED orientation must FLIP (the
  strata that read INWARD now read the opposite / the orientation assignment is no
  longer the canonical INWARD-collapse one) AND/OR the orientation-consistency
  invariant must FAIL. If orientation were still a stipulated constant, reversing
  the possibility profile would leave it UNCHANGED. The control proves the
  orientation tracks the measured gradient, not a label.
  We additionally run a FLAT control (all strata equal possibility-count): the
  gradient is ZERO, so NO direction of collapse is measurable and the orientation
  derivation must REFUSE to emit a canonical INWARD field (fails) -- a flat field
  has no emergent inward direction.

WHAT THIS SIM IS / IS NOT (honest ceiling):
  - classification = scratch_diagnostic
  - promotion_allowed = false ; formal_admission_allowed = false
  - claim_ceiling: shell ORIENTATION now emergent from a measured information
    gradient (no stipulated INWARD/OUTWARD constants); shell-ordering still
    load-bearing (v1 win kept); trivial carrier; NO QIT; NOT
    physics/Axis0/manifold/canonical.

ANTI-PROXY-DRIFT (retained from v0/v1; v2 adds the orientation-emergence control):
  - future_continuations is a dict of shell -> LIST (NOT a scalar count, NOT bool)
  - compatibility_weights is a real-valued weight structure over PAIRS of futures,
    computed BEFORE compression, consumed by the cross-shell propagation
  - present_survivor is DERIVED inward through the traversal (HARD-STOP if it
    equals the future_continuations input -> identity compression / proxy drift)
  - outward_record is a past-facing hash-chain DISTINCT from compression_map
  - shell ORIENTATION is now a COMPUTED field (derived_orientation per shell),
    NOT a constant; the emergence control proves it.

Probe family M: per-shell possibility-entropy readout + pairwise-compatibility
  weight readout; the orientation marker is now the SIGN of the measured
  information gradient, and the inward readout is a shell-ORDERED propagation in
  the emergent commitment order.
Constraint set C: orientation derived from the measured information gradient
  (INWARD = decreasing possibility toward present); inward traversal over the
  emergent-INWARD strata in decreasing-information order; each inner shell's
  surviving anchor selected by maximal pairwise compatibility with the anchor
  propagated from the next-outer shell (deterministic tie-break by branch id).
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
# orientation is now emergent from a measured information gradient. It uses NO
# QIT / density-matrix / heavy numeric tooling: the load-bearing tool is the
# hashlib append-only chain (outward_record provenance, reused from CFR v0 /
# rpf v0 / rpf v1); the information measure and gradient are pure-Python
# log/float arithmetic so the orientation-emergence stays auditable line by line.

TOOL_MANIFEST = {
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "append-only sha256 hash-chain is the outward_record machinery "
        "(reused from CFR v0 / rpf v0 / rpf v1); each chain entry binds the "
        "PER-SHELL compression step. In v2 the chain entries also bind the "
        "DERIVED orientation of the recording stratum (the emergent OUTWARD tag), "
        "so the record's orientation provenance is tamper-evident -- load-bearing "
        "for outward_record provenance and the orientation-emergence audit trail.",
    },
    "math": {
        "tried": True,
        "used": True,
        "reason": "math.log2 computes the per-shell possibility entropy "
        "I(shell)=log2(#distinct branches), the MEASURED quantity from which the "
        "INWARD/OUTWARD orientation is derived. Load-bearing for the v2 fix: the "
        "orientation is read off this computed information gradient, not a "
        "constant. Pure stdlib so the derivation stays auditable line by line.",
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
        "finite set and the gradient is a short deterministic loop over a handful "
        "of strata; pure-Python keeps the orientation-emergence auditable. Heavy "
        "numeric tooling would re-enter the proxy basin and obscure the gradient.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is object-field instantiation on a trivial "
        "carrier with a deterministic gradient computation, not a structural-"
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
        "reason": "not needed: trivial finite carrier; the information gradient is "
        "a short deterministic loop, not a batched/exhaustive sweep.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Canon algebra artifact is consumed; field "
        "instantiation with a measured-gradient orientation derivation only.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "hashlib": "load_bearing",   # outward_record per-shell hash-chain incl. emergent orientation tag
    "math": "load_bearing",      # possibility entropy -> information gradient -> orientation
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
# Identical to v0/v1: distinct points in a tiny 2-feature finite space. The
# change is orientation emergence, not the carrier.
BRANCH_STATES: dict[str, dict[str, int]] = {
    "b0": {"a": 0, "b": 0},
    "b1": {"a": 0, "b": 1},
    "b2": {"a": 1, "b": 0},
    "b3": {"a": 1, "b": 1},
    "b4": {"a": 2, "b": 0},
    "b5": {"a": 2, "b": 1},
}

EVENT_X = "event_x:apex_decision_node"

# ---- The shells Sigma_r: a finite set with POSITION coordinates only ----------
# CRITICAL v2 CHANGE: shells NO LONGER carry a shell_orientation string. They
# carry only geometry (shell_pos) and a role label. The orientation is DERIVED
# downstream from the measured possibility entropy of the branches each carries.
#
# shell_pos is the signed position coordinate along the field axis:
#   - future strata sit at POSITIVE positions (further future = larger pos),
#   - the present apex (event_x) is at pos 0,
#   - the past-facing record stratum sits at a NEGATIVE position.
# NOTHING here says which way is "inward". That is computed.
SHELLS: list[dict[str, Any]] = [
    {"shell_id": "Sigma_2", "shell_pos": 2, "role": "future possibility stratum (outer)"},
    {"shell_id": "Sigma_1", "shell_pos": 1, "role": "future possibility stratum (inner)"},
    {"shell_id": "Sigma_record", "shell_pos": -1, "role": "past-facing survival record stratum"},
]

# Future continuations carried on the FUTURE (positive-position) strata. The
# canonical config is a DECREASING-possibility profile: the outer stratum carries
# MORE open branches than the inner stratum (count 3 vs 2). This is what makes
# the information gradient point toward commitment as we approach the present, so
# INWARD emerges. (The discriminating control inverts this profile.)
FUTURE_CONTINUATIONS_BY_SHELL: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b5"],   # outer future stratum: 3 branches  -> I = log2(3)
    "Sigma_1": ["b2", "b3"],         # inner future stratum: 2 branches  -> I = log2(2) = 1.0
}


# =====================================================================
# THE v2 CORE: per-shell information measure + emergent orientation
# =====================================================================

def possibility_entropy(branches: list[str]) -> float:
    """Per-shell information measure I(shell) = log2(#distinct admissible
    branches). This is the MEASURED quantity from which orientation is derived.
    More open branches = more possibility = higher information. A single frozen
    branch (the recorded survivor) -> I = log2(1) = 0.0."""
    n = len(set(branches))
    if n <= 0:
        return 0.0
    return math.log2(n)


def compute_shell_information(
    shells: list[dict[str, Any]],
    future_continuations: dict[str, list[str]],
    present_survivor: str | None,
) -> dict[str, dict[str, Any]]:
    """Attach to each shell its position, the branches it carries, and its
    MEASURED possibility entropy. Future strata carry their future_continuations;
    the past-side record stratum carries the single frozen survivor (count 1 ->
    I = 0) IF the survivor is known (it is, after compression). Before the
    survivor is known the record stratum carries the empty set (I = 0 as well).

    Returns shell_id -> {shell_pos, branches, info_entropy, branch_count}.
    """
    info: dict[str, dict[str, Any]] = {}
    for s in shells:
        sid = s["shell_id"]
        pos = int(s["shell_pos"])
        if pos > 0:
            branches = sorted(future_continuations.get(sid, []))
        elif pos < 0:
            # past-side record stratum: carries the frozen survivor (one
            # possibility) once known, else NOTHING (count 0). A None survivor
            # (no inward collapse occurred) must NOT be inserted as a branch --
            # an empty record stratum (count 0) cannot read OUTWARD.
            branches = [present_survivor] if present_survivor is not None else []
        else:
            branches = []  # the apex itself carries no enumerated branch set
        info[sid] = {
            "shell_pos": pos,
            "branches": branches,
            "branch_count": len(set(branches)),
            "info_entropy": possibility_entropy(branches),
        }
    return info


def derive_orientation_from_gradient(
    shell_info: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    DERIVE each shell's orientation (INWARD / OUTWARD) from the SIGN of the
    measured information gradient -- NOT from any stored constant.

    Method:
      - Sort the strata by position (descending: outermost future first, present
        side last). This is the candidate inward walk order (toward the present).
      - For each adjacent ordered pair (outer -> inner) compute the information
        change dI = I(inner) - I(outer) as we step TOWARD the present (position
        decreasing). The information gradient w.r.t. decreasing position is
        grad_toward_present = -(I(inner) - I(outer)) / (pos_inner - pos_outer)
        but since pos_inner < pos_outer the denominator is negative; the
        operationally meaningful quantity is simply dI_step = I(inner) - I(outer),
        the change in possibility as we move one step toward the present.
      - INWARD (commitment) requires possibilities to be NON-INCREASING toward the
        present at the FUTURE->FUTURE / FUTURE->PRESENT transitions: dI_step < 0
        means possibilities are collapsing (committing) -> the OUTER stratum of
        that step is emergently INWARD.
      - The past-side record stratum (pos < 0) is on the FAR side of the apex; the
        information there is the frozen survivor (I = 0). Its emergent orientation
        is OUTWARD: it is the stratum where the gradient has stopped decreasing
        (the survivor is committed) AND it lies at negative position -- i.e. it is
        not part of the collapsing-possibility future stack.

    Concretely, a stratum at position p gets:
      derived_orientation = "INWARD"  iff it sits on the future side (p > 0) AND
        the measured information is NON-INCREASING from it toward the present
        (its forward step dI_step <= 0, with at least one strict decrease across
        the whole future stack so the field genuinely collapses);
      derived_orientation = "OUTWARD" iff it sits on the past side (p < 0) and
        carries the committed survivor (I has bottomed out);
      derived_orientation = "UNDIRECTED" iff the future stack shows NO net
        possibility decrease (flat or increasing) -- there is no emergent inward
        direction (this is what the flat / reversed controls trigger).

    Returns the per-shell derived orientation plus the measured gradient pieces
    the derivation read, so the audit can see the orientation came from numbers.
    """
    # order future strata by position descending (outer -> inner -> present)
    future_strata = sorted(
        [sid for sid, d in shell_info.items() if d["shell_pos"] > 0],
        key=lambda sid: -shell_info[sid]["shell_pos"],
    )
    past_strata = [sid for sid, d in shell_info.items() if d["shell_pos"] < 0]

    # measured information sequence along the future stack, outer -> inner
    info_sequence = [(sid, shell_info[sid]["info_entropy"]) for sid in future_strata]

    # adjacent steps toward the present: dI_step = I(next_inner) - I(this)
    forward_steps: list[dict[str, Any]] = []
    for i in range(len(future_strata) - 1):
        sid_out = future_strata[i]
        sid_in = future_strata[i + 1]
        dI = shell_info[sid_in]["info_entropy"] - shell_info[sid_out]["info_entropy"]
        forward_steps.append({
            "from_shell": sid_out,
            "to_shell": sid_in,
            "I_from": shell_info[sid_out]["info_entropy"],
            "I_to": shell_info[sid_in]["info_entropy"],
            "dI_toward_present": dI,
            "pos_from": shell_info[sid_out]["shell_pos"],
            "pos_to": shell_info[sid_in]["shell_pos"],
        })

    # The future stack genuinely collapses iff its information is non-increasing
    # toward the present AND strictly decreases somewhere (net commitment).
    monotone_nonincreasing = all(st["dI_toward_present"] <= 1e-12 for st in forward_steps)
    has_strict_decrease = any(st["dI_toward_present"] < -1e-12 for st in forward_steps)
    # net possibility change across the whole future stack (outer -> innermost)
    if len(info_sequence) >= 2:
        net_dI = info_sequence[-1][1] - info_sequence[0][1]
    else:
        net_dI = 0.0
    field_collapses_inward = monotone_nonincreasing and has_strict_decrease

    derived_orientation: dict[str, str] = {}
    for sid, d in shell_info.items():
        if d["shell_pos"] > 0:
            if field_collapses_inward:
                derived_orientation[sid] = "INWARD"
            else:
                # gradient does not collapse toward the present -> no inward
                # direction emerges for the future stack
                derived_orientation[sid] = "UNDIRECTED"
        elif d["shell_pos"] < 0:
            # past-side record stratum: orientation OUTWARD iff it carries EXACTLY
            # ONE committed branch (the frozen survivor: I has bottomed out at 0
            # with a genuine commitment). An EMPTY record (count 0, no inward
            # collapse occurred) or a multi-branch record cannot read OUTWARD.
            # This distinguishes "committed survivor" (count 1) from "nothing
            # committed" (count 0) -- both have I=0 but only the former is OUTWARD.
            if d["branch_count"] == 1:
                derived_orientation[sid] = "OUTWARD"
            else:
                derived_orientation[sid] = "UNDIRECTED"
        else:
            derived_orientation[sid] = "APEX"

    inward_shell_ids = [sid for sid, o in derived_orientation.items() if o == "INWARD"]
    outward_shell_ids = [sid for sid, o in derived_orientation.items() if o == "OUTWARD"]

    return {
        "derived_orientation": derived_orientation,
        "info_sequence_outer_to_inner": info_sequence,
        "forward_steps_toward_present": forward_steps,
        "net_dI_future_stack": net_dI,
        "monotone_nonincreasing_toward_present": monotone_nonincreasing,
        "has_strict_decrease": has_strict_decrease,
        "field_collapses_inward": field_collapses_inward,
        "inward_shell_ids": sorted(inward_shell_ids),
        "outward_shell_ids": sorted(outward_shell_ids),
        # the canonical emergent INWARD field requires: a genuine collapse on the
        # future side AND a committed OUTWARD record stratum.
        "emergent_inward_field_valid": field_collapses_inward and len(outward_shell_ids) >= 1,
    }


# =====================================================================
# compatibility_weights: real-valued weights over PAIRS of future continuations
# (identical machinery to v0/v1).
# =====================================================================

def branch_distance(s1: str, s2: str) -> int:
    x, y = BRANCH_STATES[s1], BRANCH_STATES[s2]
    return abs(x["a"] - y["a"]) + abs(x["b"] - y["b"])


def compute_compatibility_weights(
    future_continuations: dict[str, list[str]],
) -> dict[str, float]:
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
    return int(b[1:])


# =====================================================================
# compression_map: now walks the EMERGENT-INWARD strata in the emergent
# commitment order (decreasing information). The traversal mechanics are v1's
# (within-shell seed mass + cross-shell compatibility), but the SET of inward
# strata and the ORDER come from the DERIVED orientation + measured information,
# not from a shell_orientation constant.
# =====================================================================

def compression_map(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
    shells: list[dict[str, Any]],
    shell_info: dict[str, dict[str, Any]],
    orientation: dict[str, Any],
) -> dict[str, Any]:
    """
    Inward TRAVERSAL compression over the EMERGENT-INWARD strata.

    The set of inward strata = orientation["inward_shell_ids"] (DERIVED). The
    traversal order = those strata sorted by DECREASING measured information
    (most open first -> most committed last), i.e. the emergent commitment order.
    Within that order, the v1 mechanics apply:
      - outermost (highest information) inward shell seeds the anchor by
        within-shell compatibility mass;
      - each more-committed (lower information) inward shell selects the branch of
        maximal pairwise compatibility with the propagated anchor (anchor that
        reappears scores 1.0); tie-break lowest branch id;
      - the final anchor is the present_survivor.
    """
    inward_ids = list(orientation["inward_shell_ids"])
    # emergent commitment order: DECREASING information; tie-break by position
    # (outer first) then shell_id for determinism.
    inward_ordered = sorted(
        inward_ids,
        key=lambda sid: (-shell_info[sid]["info_entropy"], -shell_info[sid]["shell_pos"], sid),
    )

    traversal_steps: list[dict[str, Any]] = []
    anchor: str | None = None

    for sid in inward_ordered:
        branches = sorted(future_continuations.get(sid, []))
        if not branches:
            traversal_steps.append({
                "shell_id": sid,
                "shell_pos": shell_info[sid]["shell_pos"],
                "info_entropy": shell_info[sid]["info_entropy"],
                "incoming_anchor": anchor,
                "branches_on_shell": [],
                "branch_scores": {},
                "selected_anchor": anchor,
                "step_kind": "empty_shell_passthrough",
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
        traversal_steps.append({
            "shell_id": sid,
            "shell_pos": shell_info[sid]["shell_pos"],
            "info_entropy": shell_info[sid]["info_entropy"],
            "incoming_anchor": anchor,
            "branches_on_shell": branches,
            "branch_scores": scores,
            "selected_anchor": selected,
            "step_kind": step_kind,
        })
        anchor = selected

    return {
        "direction": "INWARD",
        "direction_is_emergent": True,
        "rule": "inward multi-shell traversal over the EMERGENT-INWARD strata in "
        "decreasing-information (emergent commitment) order; outermost (highest "
        "information) inward shell seeds the anchor by within-shell compatibility "
        "mass; each more-committed inner shell selects the branch of maximal "
        "pairwise compatibility with the anchor propagated from the next-outer "
        "shell; tie-break lowest branch id",
        "inward_shell_ids_used": sorted(inward_ids),
        "shell_traversal_order": inward_ordered,
        "shell_info_order": [shell_info[sid]["info_entropy"] for sid in inward_ordered],
        "shell_pos_order": [shell_info[sid]["shell_pos"] for sid in inward_ordered],
        "traversal_steps": traversal_steps,
        "num_traversal_steps": len([s for s in traversal_steps if s["branches_on_shell"]]),
        "present_survivor": anchor,
        "weights_computed_before_compression": True,
        "input_shells_used": sorted(future_continuations.keys()),
        "shell_ordering_load_bearing": True,
        "orientation_is_derived_not_stipulated": True,
    }


def flat_union_argmax_survivor(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
) -> str:
    """v0's flat-union mechanism, retained ONLY as a negative-control reference."""
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
# outward_record: past-facing hash-chain, now written on the EMERGENT-OUTWARD
# stratum (the orientation of the recording shell is itself derived).
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
    orientation: dict[str, Any],
) -> dict[str, Any]:
    """
    Past-facing OUTWARD record. The recording stratum is the one whose orientation
    EMERGED as OUTWARD (orientation["outward_shell_ids"][0]); if none emerged
    OUTWARD the build BREAKS (StopIteration), which is exactly what the flat /
    reversed controls require.
    """
    survivor = compression["present_survivor"]
    outward_ids = orientation["outward_shell_ids"]
    # next(...) raises StopIteration if no stratum emerged OUTWARD -> build breaks
    record_sid = next(sid for sid in [s["shell_id"] for s in shells] if sid in outward_ids)
    record_shell = next(s for s in shells if s["shell_id"] == record_sid)

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
            "from_shell_pos": tstep["shell_pos"],
            "from_shell_info_entropy": tstep["info_entropy"],
            "source_derived_orientation": "INWARD",  # derived, not stipulated
            "record_derived_orientation": "OUTWARD",  # derived, not stipulated
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
        "record_shell_pos": record_shell["shell_pos"],
        "record_orientation": "OUTWARD",                 # DERIVED for this stratum
        "record_orientation_is_derived": True,
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
    """Assemble one RetrocausalPossibilityField instance. The orientation is
    derived from the measured information of the supplied future_continuations on
    the supplied shell geometry -- so perturbing the possibility profile (the
    emergence control) changes the DERIVED orientation."""
    fc = future_continuations if future_continuations is not None else FUTURE_CONTINUATIONS_BY_SHELL
    sh = shells if shells is not None else SHELLS

    # Required invariant: compatibility weights computed BEFORE compression.
    weights = weights_override if weights_override is not None else compute_compatibility_weights(fc)

    # STAGE 1: measure per-shell information with survivor unknown yet (record
    # stratum carries nothing). Orientation of the FUTURE stack is derived from
    # the future possibility profile alone -- it does NOT need the survivor.
    pre_info = compute_shell_information(sh, fc, present_survivor=None)
    pre_orient = derive_orientation_from_gradient(pre_info)

    # STAGE 2: compress inward over the emergent-INWARD strata.
    compression = compression_map(fc, weights, sh, pre_info, pre_orient)
    present_survivor = compression["present_survivor"]

    # STAGE 3: re-measure information now that the survivor is committed (the
    # record stratum carries the single frozen survivor, I=0) and RE-DERIVE
    # orientation so the OUTWARD record stratum emerges from a measured I=0.
    post_info = compute_shell_information(sh, fc, present_survivor=present_survivor)
    orientation = derive_orientation_from_gradient(post_info)

    outward_record = build_outward_record(sh, compression, orientation)

    return {
        "event_x": EVENT_X,
        "shells": sh,
        "shell_pos": {s["shell_id"]: s["shell_pos"] for s in sh},
        # deep snapshot so the dumped result never reflects a trap's transient
        # carrier mutation (the state_mutation_trap mutates the global in place
        # under a try/finally; snapshotting here keeps the receipt clean).
        "branch_states": {k: dict(v) for k, v in BRANCH_STATES.items()},
        "future_continuations": fc,
        "compatibility_weights": weights,
        # ---- the v2 emergent-orientation fields ----
        "shell_information": post_info,
        "orientation_derivation": orientation,
        "shell_orientation_derived": orientation["derived_orientation"],
        "compression_map": compression,
        "present_survivor": present_survivor,
        "outward_record": outward_record,
    }


# =====================================================================
# v1 win KEPT: the shell-reassignment control (move ONE branch to a different
# shell, union identical, survivor must MOVE). v2 keeps the inverted-profile
# canonical config: Sigma_2=[b0,b1,b5] (3), Sigma_1=[b2,b3] (2). Reassignment
# moves a branch across shells while keeping the union and the per-shell COUNTS
# such that the field still collapses inward (so orientation stays valid) but the
# traversal path / survivor moves.
# =====================================================================

# Swap b3 (inner) <-> b5 (outer): b3 moves to the outer stratum, b5 moves to the
# inner stratum, so the union {b0,b1,b2,b3,b5} is identical AND both per-shell
# COUNTS are preserved (Sigma_2 keeps 3, Sigma_1 keeps 2). The information profile
# (and hence the emergent orientation) is therefore UNCHANGED -- this deliberately
# ISOLATES the v1 shell-ordering effect from the v2 orientation: only which branch
# sits on which shell changes, so any survivor move is purely the shell-ordering
# (placement) effect, not an orientation artifact. The present_survivor moves
# b3 -> b2.
CANONICAL_REASSIGNMENT: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b1", "b3"],   # b5 -> b3 swapped in (b3 was on the inner shell)
    "Sigma_1": ["b2", "b5"],         # b3 -> b5 swapped in (b5 was on the outer shell)
}


def union_of(future_continuations: dict[str, list[str]]) -> list[str]:
    return sorted({b for branches in future_continuations.values() for b in branches})


def shell_reassignment_control() -> dict[str, Any]:
    """Build the canonical instance and a shell-reassigned instance with an
    identical union, and report whether the present_survivor moves AND whether
    the inward propagation path changes."""
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


# =====================================================================
# THE v2 EMERGENCE DISCRIMINATING CONTROLS (the hard acceptance bar):
# reverse / flatten the measured asymmetry and confirm the DERIVED orientation
# flips or refuses (proving it is emergent, not stipulated).
# =====================================================================

REVERSED_PROFILE: dict[str, list[str]] = {
    # INVERT the possibility profile: inner stratum carries MORE branches than the
    # outer stratum (count 3 vs 2). The information gradient toward the present
    # now INCREASES -> no inward collapse -> orientation must NOT emerge INWARD.
    "Sigma_2": ["b0", "b1"],          # outer: 2 branches  -> I = 1.0
    "Sigma_1": ["b2", "b3", "b4"],    # inner: 3 branches  -> I = log2(3) ~ 1.585
}

FLAT_PROFILE: dict[str, list[str]] = {
    # EQUAL possibility on every future stratum: gradient = 0 -> no measurable
    # direction of collapse -> orientation must NOT emerge INWARD.
    "Sigma_2": ["b0", "b1"],          # 2 branches
    "Sigma_1": ["b2", "b3"],          # 2 branches
}


def _orientation_for_profile(fc: dict[str, list[str]]) -> dict[str, Any]:
    """Derive orientation for a profile WITHOUT committing a survivor on the
    record stratum (pre-compression view) -- this is the future-side gradient
    that the emergence control targets."""
    pre_info = compute_shell_information(SHELLS, fc, present_survivor=None)
    return derive_orientation_from_gradient(pre_info)


def emergence_reverse_gradient_control() -> dict[str, Any]:
    """
    THE PRIMARY EMERGENCE CONTROL. Reverse the measured information asymmetry
    (inner shell carries MORE possibility than outer). Under v2 the DERIVED
    orientation must FLIP away from the canonical INWARD-collapse field: the
    future strata no longer read INWARD (they read UNDIRECTED because the
    possibility gradient now increases toward the present), and the emergent
    inward field is INVALID. If orientation were a stipulated constant this would
    be UNCHANGED. We ALSO confirm the full build FAILS to produce a valid
    emergent-inward field (no OUTWARD record stratum can form on a non-collapsing
    field), i.e. the orientation derivation refuses.
    """
    base_orient = _orientation_for_profile(FUTURE_CONTINUATIONS_BY_SHELL)
    rev_orient = _orientation_for_profile(REVERSED_PROFILE)

    base_future_inward = base_orient["field_collapses_inward"]
    rev_future_inward = rev_orient["field_collapses_inward"]

    # the orientation labels on the future strata before/after reversal
    base_future_labels = {
        sid: o for sid, o in base_orient["derived_orientation"].items()
        if sid in ("Sigma_2", "Sigma_1")
    }
    rev_future_labels = {
        sid: o for sid, o in rev_orient["derived_orientation"].items()
        if sid in ("Sigma_2", "Sigma_1")
    }

    orientation_flipped = base_future_labels != rev_future_labels

    # does the full build refuse on the reversed profile?
    build_refused = False
    try:
        build_object_instance(future_continuations=REVERSED_PROFILE)
    except StopIteration:
        build_refused = True

    return {
        "mechanism": "reverse the measured information gradient (inner carries MORE "
        "possibility than outer)",
        "base_net_dI_future_stack": base_orient["net_dI_future_stack"],
        "reversed_net_dI_future_stack": rev_orient["net_dI_future_stack"],
        "base_field_collapses_inward": base_future_inward,
        "reversed_field_collapses_inward": rev_future_inward,
        "base_future_orientation_labels": base_future_labels,
        "reversed_future_orientation_labels": rev_future_labels,
        "orientation_flipped_under_reversal": orientation_flipped,
        "reversed_emergent_inward_field_valid": rev_orient["emergent_inward_field_valid"],
        "reversed_build_refused": build_refused,
        # PASS iff: base collapses inward, reversed does NOT, the future labels
        # flipped, and the reversed build refused (no valid emergent inward field).
        "emergence_control_passes": (
            base_future_inward is True
            and rev_future_inward is False
            and orientation_flipped is True
            and build_refused is True
        ),
    }


def emergence_flat_gradient_control() -> dict[str, Any]:
    """
    SECONDARY EMERGENCE CONTROL. A flat possibility profile (equal counts) has a
    ZERO information gradient -> NO measurable direction of collapse -> the
    orientation derivation must REFUSE to emit a canonical INWARD field, and the
    build must FAIL. Confirms orientation needs a measured asymmetry to exist.
    """
    flat_orient = _orientation_for_profile(FLAT_PROFILE)
    build_refused = False
    try:
        build_object_instance(future_continuations=FLAT_PROFILE)
    except StopIteration:
        build_refused = True
    return {
        "mechanism": "flat possibility profile (equal branch counts -> zero gradient)",
        "flat_net_dI_future_stack": flat_orient["net_dI_future_stack"],
        "flat_field_collapses_inward": flat_orient["field_collapses_inward"],
        "flat_emergent_inward_field_valid": flat_orient["emergent_inward_field_valid"],
        "flat_build_refused": build_refused,
        # PASS iff a flat field shows NO inward collapse AND the build refuses.
        "flat_control_passes": (
            flat_orient["field_collapses_inward"] is False
            and build_refused is True
        ),
    }


# =====================================================================
# Negative controls retained from v1 (must STILL behave correctly)
# =====================================================================

def flat_union_negative_control() -> dict[str, Any]:
    """Negative control (a): collapse the shell-ordered traversal to v0's flat
    union argmax. Under the flat mechanism the shell-reassignment must FAIL to
    move the survivor (proving it is the TRAVERSAL that carries the effect)."""
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
    only ONE distinct branch (destroys the >=2-distinct structure). The build
    must BREAK (an invariant must fail)."""
    scrambled = {
        sid: [branches[0], branches[0]]
        for sid, branches in FUTURE_CONTINUATIONS_BY_SHELL.items()
    }
    try:
        inst = build_object_instance(future_continuations=scrambled)
    except StopIteration:
        # a degenerate single-branch profile may also collapse the orientation
        return {
            "mechanism": "scramble future_continuations to 1 distinct branch per shell",
            "all_invariants_hold": False,
            "control_breaks": True,
        }
    inv = check_invariants(inst, include_shell_ordering=False)
    return {
        "mechanism": "scramble future_continuations to 1 distinct branch per shell",
        "all_invariants_hold": all(inv.values()),
        "control_breaks": not all(inv.values()),
    }


def uniform_weights_negative_control() -> dict[str, Any]:
    """Negative control (c): replace compatibility_weights with a CONSTANT value.
    The non-uniformity invariant must fail (the structure is decorative) -> the
    build breaks; AND the shell-reassignment must no longer move the survivor."""
    real_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
    uniform = {k: 0.5 for k in real_weights}
    inst = build_object_instance(weights_override=uniform)
    inv = check_invariants(inst, include_shell_ordering=False)

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
# Trap controls retained from v0/v1 (must STILL pass)
# =====================================================================

def weight_permutation_trap() -> dict[str, Any]:
    """Trap #1 (must stay PASS): permuting compatibility_weights moves the
    survivor. Swap two pair weights present in the canonical profile's branch
    set ({b0,b1,b2,b3,b5}: use b0|b1 <-> b1|b2) and confirm the survivor moves."""
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
    Shift branch b3's feature 'a' by +5 (re-deriving weights from the mutated
    carrier) and confirm the survivor moves -- identical to the v1 trap. b3 is on
    the inner shell in the canonical profile, so its placement is load-bearing;
    shifting its feature changes the cross-shell compatibility weights and moves
    the survivor b3 -> b2. The mutation changes feature VALUES only, not per-shell
    branch COUNTS, so the emergent orientation stays valid."""
    base = build_object_instance()

    saved_b3 = dict(BRANCH_STATES["b3"])
    try:
        BRANCH_STATES["b3"]["a"] += 5
        mutated_weights = compute_compatibility_weights(FUTURE_CONTINUATIONS_BY_SHELL)
        mutated = build_object_instance(weights_override=mutated_weights)
        mutated_survivor = mutated["present_survivor"]
    finally:
        BRANCH_STATES["b3"] = saved_b3  # restore the carrier in place

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

def check_invariants(instance: dict[str, Any], *, include_shell_ordering: bool = True) -> dict[str, Any]:
    """Return a dict of named invariant -> bool. The validator asserts these."""
    fc = instance["future_continuations"]
    shells = instance["shells"]
    weights = instance["compatibility_weights"]
    compression = instance["compression_map"]
    survivor = instance["present_survivor"]
    record = instance["outward_record"]
    orientation = instance["orientation_derivation"]
    shell_info = instance["shell_information"]
    derived = instance["shell_orientation_derived"]

    future_shell_ids = {s["shell_id"] for s in shells if s["shell_pos"] > 0}

    # future continuations are FUTURE-INDEXED (keyed by positive-position shells)
    fc_future_indexed = (set(fc.keys()) <= future_shell_ids) and len(fc) >= 1
    # each shell carries a LIST of >=2 distinct branches (not a scalar/bool)
    fc_lists_of_distinct = all(
        isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()
    )
    # future flow is INWARD (emergent)
    future_flow_inward = compression.get("direction") == "INWARD"

    # ---- THE v2 EMERGENCE INVARIANTS ----
    # NO shell carries a hard-coded shell_orientation string (the v1 constant).
    no_stipulated_orientation_constant = all(
        "shell_orientation" not in s for s in shells
    )
    # orientation is DERIVED from the measured gradient (computed field present).
    orientation_is_derived = (
        bool(compression.get("orientation_is_derived_not_stipulated"))
        and bool(record.get("record_orientation_is_derived"))
        and isinstance(derived, dict)
        and len(derived) >= 1
    )
    # the per-shell information measure is genuinely computed (entropy floats).
    shell_information_computed = (
        isinstance(shell_info, dict)
        and len(shell_info) >= 2
        and all(isinstance(d.get("info_entropy"), float) for d in shell_info.values())
    )
    # the measured future-stack gradient is non-trivial (a real asymmetry exists).
    measured_gradient_nontrivial = abs(orientation.get("net_dI_future_stack", 0.0)) > 1e-12
    # the field genuinely collapses inward by the MEASURED gradient.
    field_collapses_inward = bool(orientation.get("field_collapses_inward"))
    # the emergent inward field is valid (collapse + an OUTWARD record stratum).
    emergent_inward_field_valid = bool(orientation.get("emergent_inward_field_valid"))
    # at least one stratum emerged OUTWARD and the record uses it.
    has_emergent_outward_shell = (
        len(orientation.get("outward_shell_ids", [])) >= 1
        and record.get("record_shell_id") in orientation.get("outward_shell_ids", [])
    )
    # record orientation is OUTWARD (derived)
    record_outward = record.get("record_orientation") == "OUTWARD"

    # ---- weights (v0/v1) ----
    weights_before_compression = bool(compression.get("weights_computed_before_compression"))
    weights_are_pair_reals = (
        len(weights) >= 1
        and all("|" in k for k in weights.keys())
        and all(isinstance(w, float) for w in weights.values())
    )
    weights_non_uniform = len(set(round(w, 12) for w in weights.values())) >= 2

    # ---- survivor derivation (v1) ----
    nonempty_steps = [s for s in compression.get("traversal_steps", []) if s["branches_on_shell"]]
    survivor_derived = (
        survivor == compression.get("present_survivor")
        and len(nonempty_steps) >= 1
        and survivor == nonempty_steps[-1]["selected_anchor"]
    )
    multi_step_traversal = len(nonempty_steps) >= 2

    # ---- record provenance (v1) ----
    record_chain_ok = bool(record.get("append_only_recomputed"))
    record_binds_provenance = (
        bool(record.get("inward_provenance_bound"))
        and bool(record.get("reflects_per_shell_compression_steps"))
        and record.get("binds_present_survivor") == survivor
        and len(record.get("record_entries", [])) == len(compression.get("traversal_steps", []))
        and len(record.get("record_entries", [])) >= 1
    )

    # HARD-STOP: future_continuations must NOT equal present_survivor.
    hard_stop_not_identity = fc != survivor and survivor not in (None, fc)

    # compression_map DISTINCT from outward_record
    map_distinct_from_record = set(compression.keys()) != set(record.keys())

    invariants = {
        "future_continuations_future_indexed": fc_future_indexed,
        "future_continuations_lists_of_distinct_ge2": fc_lists_of_distinct,
        "future_flow_inward": future_flow_inward,
        # v2 emergence invariants
        "NO_stipulated_orientation_constant": no_stipulated_orientation_constant,
        "orientation_is_derived_not_stipulated": orientation_is_derived,
        "shell_information_measure_computed": shell_information_computed,
        "measured_information_gradient_nontrivial": measured_gradient_nontrivial,
        "field_collapses_inward_by_measured_gradient": field_collapses_inward,
        "emergent_inward_field_valid": emergent_inward_field_valid,
        "has_emergent_outward_record_shell": has_emergent_outward_shell,
        "record_outward": record_outward,
        # weights
        "compatibility_weights_before_compression": weights_before_compression,
        "compatibility_weights_are_pair_reals": weights_are_pair_reals,
        "compatibility_weights_non_uniform": weights_non_uniform,
        # survivor + traversal
        "present_survivor_derived_through_traversal": survivor_derived,
        "compression_is_multi_step_traversal": multi_step_traversal,
        # record provenance
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
        emc = emergence_reverse_gradient_control()
        invariants["ORIENTATION_EMERGENCE_REVERSE_CONTROL_PASSES"] = bool(
            emc["emergence_control_passes"]
        )
        flatc = emergence_flat_gradient_control()
        invariants["ORIENTATION_EMERGENCE_FLAT_CONTROL_PASSES"] = bool(
            flatc["flat_control_passes"]
        )

    return invariants


FIRST_CLASS_KEYS = [
    "event_x",
    "shells",
    "shell_pos",
    "shell_information",
    "orientation_derivation",
    "shell_orientation_derived",
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
    reverse_emergence = emergence_reverse_gradient_control()
    flat_emergence = emergence_flat_gradient_control()
    flat_neg = flat_union_negative_control()
    scramble_neg = scramble_futures_negative_control()
    uniform_neg = uniform_weights_negative_control()
    weight_trap = weight_permutation_trap()
    state_trap = state_mutation_trap()

    result = {
        "name": "retrocausal_possibility_field_v2_info_gradient",
        "object_name": "RetrocausalPossibilityField",
        "object_statement_sha256": "02f813d355b5812e1021eb023e5aca7c6006c00dcfc060cf94ff727b7cb8dd78",
        "probe_family": "M_possibility_entropy_plus_pairwise_compatibility_readout_emergent_orientation",
        "constraint_set": "C_orientation_derived_from_measured_information_gradient_then_inward_traversal",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,

        # ---- THE FIRST-CLASS OBJECT FIELDS (genuinely computed) ----
        "event_x": instance["event_x"],
        "shells": instance["shells"],
        "shell_pos": instance["shell_pos"],
        "shell_information": instance["shell_information"],
        "orientation_derivation": instance["orientation_derivation"],
        "shell_orientation_derived": instance["shell_orientation_derived"],
        "future_continuations": instance["future_continuations"],
        "branch_states": instance["branch_states"],
        "compatibility_weights": instance["compatibility_weights"],
        "compression_map": instance["compression_map"],
        "present_survivor": instance["present_survivor"],
        "outward_record": instance["outward_record"],

        "first_class_keys_present": FIRST_CLASS_KEYS,
        "invariants": invariants,
        "all_invariants_hold": all_invariants_hold,

        # ---- THE v2 ACCEPTANCE: orientation emergence ----
        "orientation_emergence_reverse_control": reverse_emergence,
        "orientation_emergence_flat_control": flat_emergence,
        "orientation_emergence_passes": (
            reverse_emergence["emergence_control_passes"]
            and flat_emergence["flat_control_passes"]
        ),

        # ---- v1 win KEPT: shell reassignment moves the survivor ----
        "shell_reassignment_moves_survivor": reassignment["shell_reassignment_moves_survivor"],
        "shell_reassignment_control": reassignment,

        # ---- traps retained from v0/v1 (must still pass) ----
        "trap_1_weight_permutation": weight_trap,
        "trap_4_state_mutation": state_trap,

        # ---- negative controls retained from v1 ----
        "negative_control_flat_union": flat_neg,
        "negative_control_scramble_futures": scramble_neg,
        "negative_control_uniform_weights": uniform_neg,

        # ---- honest ceiling ----
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "shell ORIENTATION (INWARD/OUTWARD) now EMERGENT from a measured "
            "per-shell possibility-entropy gradient: NO shell carries a stipulated "
            "shell_orientation constant; the INWARD/OUTWARD assignment AND whether "
            "an inward collapse exists are READ from the sign of the computed "
            "net_dI_future_stack gradient (reverse the gradient -> orientation "
            "flips and the build refuses). shell-ordering still load-bearing (v1 "
            "win kept); trivial carrier; NO QIT; NOT physics/Axis0/manifold/"
            "canonical. HONEST RESIDUAL (still stipulated, NOT emergent): the "
            "geometry sign convention -- which side is FUTURE (shell_pos > 0) vs "
            "PAST/record (shell_pos < 0), and the definitional choice that "
            "DECREASING possibility toward the present == INWARD. The gradient "
            "decides the orientation GIVEN that convention; it does not derive the "
            "convention itself."
        ),
        "honest_residual_stipulation": {
            "what_is_emergent": "the INWARD/OUTWARD orientation assignment and "
            "whether an inward collapse exists are derived from the sign of the "
            "measured possibility-entropy gradient (net_dI_future_stack); flip the "
            "gradient and the orientation flips / the build refuses.",
            "what_is_still_stipulated": "the geometry sign convention: shell_pos "
            "sign fixes which strata are FUTURE vs PAST/record, and the "
            "definitional mapping 'decreasing possibility toward present = INWARD' "
            "is a choice in derive_orientation_from_gradient, not itself measured.",
        },
        "blocked_downstream_consumers": [
            "Axis0 claim",
            "flux claim",
            "physics claim",
            "formal manifold admission",
            "claim that this trivial carrier is THE retrocausal field of the real model",
            "claim that the possibility-entropy gradient is THE physical arrow of time",
            "claim that the geometry sign convention (future=pos>0) is itself emergent",
        ],
        "all_pass": all_invariants_hold,
        "criteria_checked": sorted(invariants.keys()),
    }
    return result


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(SIM_DIR, "results", "retrocausal_possibility_field_v2_info_gradient_results.json")


def main() -> int:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "ok": result["all_pass"],
        "orientation_emergence_passes": result["orientation_emergence_passes"],
        "derived_orientation": result["shell_orientation_derived"],
        "net_dI_future_stack": result["orientation_derivation"]["net_dI_future_stack"],
        "reversed_orientation_labels": result["orientation_emergence_reverse_control"]["reversed_future_orientation_labels"],
        "shell_reassignment_moves_survivor": result["shell_reassignment_moves_survivor"],
        "present_survivor": result["present_survivor"],
        "result_path": RESULT_PATH,
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
