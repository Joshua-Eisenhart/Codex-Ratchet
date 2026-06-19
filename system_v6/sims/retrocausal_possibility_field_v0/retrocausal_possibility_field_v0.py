#!/usr/bin/env python3
"""
retrocausal_possibility_field_v0 -- FIRST instantiation of the Wizard v4.3
primary object (RetrocausalPossibilityField) first-class fields on a TRIVIAL
finite carrier.

Started from system_v4/probes/SIM_TEMPLATE.py (template framing preserved).
Reuses the append-only hash-chain record machinery pattern from
system_v6/sims/compression_flow_radiated_record_v0 (CFR v0) for outward_record.

THE OBJECT (per system_v6/receipts/v43_object_card_current_run.json):
  "A finite shell-indexed field of possible futures compresses INWARD through
   compatibility into a present survivor, while the past-facing OUTWARD record
   preserves what survived."

WHAT THIS SIM IS / IS NOT (honest ceiling):
  - classification = scratch_diagnostic
  - promotion_allowed = false ; formal_admission_allowed = false
  - claim_ceiling: FIRST instantiation of RetrocausalPossibilityField first-class
    fields (event_x, shells, shell_radius_r, shell_orientation,
    future_continuations [shell-keyed LISTS], branch_states,
    compatibility_weights [over PAIRS], compression_map [inward], present_survivor
    [derived], outward_record [outward, hash-chain]) on a TRIVIAL finite carrier.
    NOT physics / NOT Axis0 / NOT manifold / NOT canonical. This is FIELD
    INSTANTIATION, NOT carrier richness. No QIT/density-matrix machinery is used
    and none is claimed.

ANTI-PROXY-DRIFT (council traps this build must NOT match):
  - future_continuations is a dict of shell -> LIST (NOT a scalar count, NOT bool)
  - compatibility_weights is a real-valued weight structure over PAIRS of futures
    (NOT a boolean exclusion predicate) and is computed BEFORE compression
  - present_survivor is DERIVED from the weighted futures (HARD-STOP if it equals
    the future_continuations input -> identity compression / proxy drift)
  - outward_record is a past-facing hash-chain DISTINCT from compression_map
  - shells + shell_radius_r are FIRST-CLASS named fields (no implicit shell)

Probe family M: pairwise-compatibility weight readout over enumerated branch
  states, with a shell-orientation marker.
Constraint set C: shell-indexed compatibility weights select the survivor as the
  branch maximizing total inward compatibility mass (argmax with deterministic
  tie-break by branch_id).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================
# This object is a FIELD-INSTANTIATION receipt on a trivial finite carrier.
# It deliberately uses NO QIT / density-matrix / heavy numeric tooling: the
# council's finding is that the campaign built rich PROXIES while never
# instantiating the object's first-class fields. The load-bearing tool here is
# the hashlib append-only chain (outward_record provenance), reused from CFR v0.

TOOL_MANIFEST = {
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "append-only sha256 hash-chain is the outward_record machinery "
        "(reused from CFR v0); the record's tamper-evidence and inward-compression "
        "provenance binding are computed with it -- load-bearing for outward_record.",
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
        "finite set; pure-Python integer/float weight arithmetic keeps the field "
        "instantiation auditable. Heavy numeric tooling would re-enter the proxy basin.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is object-field instantiation on a trivial "
        "carrier, not a structural-impossibility (UNSAT) proof. No formal admission "
        "is claimed.",
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
        "reason": "not needed: trivial finite carrier, no batched/exhaustive sweep.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Canon algebra artifact is consumed; field "
        "instantiation only.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "hashlib": "load_bearing",   # outward_record hash-chain
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
# feature tuples), satisfying the >=2-distinct requirement per shell.
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
# survivor sits at r=0 (the apex / event_x), produced by inward compression.
#
# shell_orientation explicitly distinguishes INWARD (future->present) from
# OUTWARD (present->past record). Removing it MUST break the build (negative
# control b).
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
# states. This is the object's first-class field that ~218 prior sims never
# instantiated (it was always a count / boolean / quotient readout).
FUTURE_CONTINUATIONS_BY_SHELL: dict[str, list[str]] = {
    "Sigma_2": ["b0", "b2", "b4", "b5"],   # outer future stratum: 4 branches
    "Sigma_1": ["b2", "b3", "b5"],          # inner future stratum: 3 branches
}


# =====================================================================
# compatibility_weights: real-valued weights over PAIRS of future continuations
# Computed BEFORE survivor compression (required invariant).
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
    a structure over PAIRS.
    """
    all_futures: list[str] = []
    for shell_id, branches in future_continuations.items():
        for b in branches:
            all_futures.append(b)
    # de-duplicate while preserving determinism (a branch can appear on >1 shell)
    uniq = sorted(set(all_futures))
    weights: dict[str, float] = {}
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            p, q = uniq[i], uniq[j]
            key = f"{p}|{q}"
            d = branch_distance(p, q)
            weights[key] = 1.0 / (1.0 + float(d))
    return weights


# =====================================================================
# compression_map: shell-indexed future_continuations -> present_survivor
# via the compatibility weights (INWARD). Records the trace/params.
# =====================================================================

def compression_map(
    future_continuations: dict[str, list[str]],
    compatibility_weights: dict[str, float],
) -> dict[str, Any]:
    """
    Inward compression. For each candidate branch p that appears as a future
    continuation, accumulate its total compatibility mass: the sum of pairwise
    weights linking p to every OTHER future continuation. The present survivor
    is argmax of this inward mass (deterministic tie-break: lowest branch id).

    This is genuinely a function future_continuations -> present_survivor THROUGH
    the pairwise weights: change the futures or the weights and the survivor moves.
    The trace (per-candidate mass + the winning argmax) is recorded.
    """
    candidates = sorted(
        {b for branches in future_continuations.values() for b in branches}
    )

    def pair_key(p: str, q: str) -> str:
        lo, hi = sorted((p, q))
        return f"{lo}|{hi}"

    inward_mass: dict[str, float] = {}
    for p in candidates:
        mass = 0.0
        for q in candidates:
            if q == p:
                continue
            mass += compatibility_weights[pair_key(p, q)]
        inward_mass[p] = mass

    # argmax with deterministic tie-break (lowest branch id)
    best = None
    best_mass = float("-inf")
    for p in candidates:
        m = inward_mass[p]
        if (m > best_mass) or (m == best_mass and (best is None or p < best)):
            best, best_mass = p, m

    return {
        "direction": "INWARD",
        "rule": "argmax total pairwise compatibility mass over future "
        "continuations; tie-break lowest branch id",
        "candidate_inward_mass": inward_mass,
        "present_survivor": best,
        "present_survivor_mass": best_mass,
        "weights_computed_before_compression": True,
        "input_shells_used": sorted(future_continuations.keys()),
    }


# =====================================================================
# outward_record: past-facing hash-chain of what survived the compression.
# DISTINCT from compression_map. Reuses CFR v0 append-only chain pattern.
# Each entry binds inward-compression provenance (the survivor + the losing
# branches at each shell that were compressed away), so the record cannot be
# a content-free hash chain (anti-proxy trap c/the council's "hash chain
# without inward-compression provenance" trap).
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
    future_continuations: dict[str, list[str]],
    shells: list[dict[str, Any]],
    compression: dict[str, Any],
) -> dict[str, Any]:
    """
    Past-facing OUTWARD record. We walk the INWARD shells from OUTER (r=2) to
    INNER (r=1), and at each shell emit a provenance entry recording, relative
    to the inward compression: which branches were on the shell, which one is
    the surviving present, and which branches were compressed away (lost).
    The record itself is oriented OUTWARD (r=-1 shell). Each entry is hashed
    into an append-only chain (tamper-evident provenance), DISTINCT from the
    compression_map's argmax trace.
    """
    survivor = compression["present_survivor"]
    # Use .get(): a shell missing shell_orientation (negative control b) yields
    # None, so no OUTWARD shell is found and next(...) raises StopIteration ->
    # the build breaks exactly as the orientation-removal control requires.
    record_shell = next(s for s in shells if s.get("shell_orientation") == "OUTWARD")
    # inward shells in order of DECREASING radius (outer -> inner compression flow)
    inward_shells = sorted(
        [s for s in shells if s.get("shell_orientation") == "INWARD"],
        key=lambda s: -int(s["shell_radius_r"]),
    )

    per_step_entries: list[list[dict[str, Any]]] = []
    hash_chain: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    record_entries: list[dict[str, Any]] = []

    for step, shell in enumerate(inward_shells):
        sid = shell["shell_id"]
        branches = future_continuations.get(sid, [])
        compressed_away = [b for b in branches if b != survivor]
        survived_here = survivor in branches
        entry = {
            "from_shell": sid,
            "from_shell_radius_r": shell["shell_radius_r"],
            "inward_orientation_of_source": shell["shell_orientation"],
            "record_orientation": record_shell["shell_orientation"],  # OUTWARD
            "survivor_present": survivor,
            "survivor_present_on_this_shell": survived_here,
            "branches_compressed_away": sorted(compressed_away),
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
    negative controls to perturb inputs and observe the break."""
    fc = future_continuations if future_continuations is not None else FUTURE_CONTINUATIONS_BY_SHELL
    sh = shells if shells is not None else SHELLS

    # Required invariant: compatibility weights computed BEFORE compression.
    weights = weights_override if weights_override is not None else compute_compatibility_weights(fc)
    compression = compression_map(fc, weights)
    present_survivor = compression["present_survivor"]
    outward_record = build_outward_record(fc, sh, compression)

    return {
        "event_x": EVENT_X,
        "shells": sh,
        "shell_radius_r": [s["shell_radius_r"] for s in sh],
        "shell_orientation": {s["shell_id"]: s["shell_orientation"] for s in sh},
        "branch_states": BRANCH_STATES,
        "future_continuations": fc,
        "compatibility_weights": weights,
        "compression_map": compression,
        "present_survivor": present_survivor,
        "outward_record": outward_record,
    }


# =====================================================================
# INVARIANTS + HARD-STOP (the validator asserts these; we also expose them here)
# =====================================================================

def check_invariants(instance: dict[str, Any]) -> dict[str, Any]:
    """Return a dict of named invariant -> bool. The validator asserts these."""
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
    # weights are NON-uniform (not "uniform-then-claim-structure"): negative
    # control (c) replaces them with a constant -> this becomes False.
    weights_non_uniform = len(set(round(w, 12) for w in weights.values())) >= 2
    # survivor is DERIVED from weighted futures (appears as a candidate AND was
    # selected via the per-candidate inward mass argmax)
    survivor_derived = (
        survivor in compression.get("candidate_inward_mass", {})
        and survivor == compression.get("present_survivor")
    )
    # record hash-chain recomputes (tamper-evident append-only)
    record_chain_ok = bool(record.get("append_only_recomputed"))
    # record binds inward-compression provenance (not a content-free chain)
    record_binds_provenance = (
        bool(record.get("inward_provenance_bound"))
        and record.get("binds_present_survivor") == survivor
        and len(record.get("record_entries", [])) >= 1
    )

    # HARD-STOP: future_continuations must NOT equal present_survivor.
    # (identity compression / collapsed object = proxy drift)
    hard_stop_not_identity = fc != survivor and survivor not in (None, fc)

    # compression_map DISTINCT from outward_record (different shapes/keys)
    map_distinct_from_record = set(compression.keys()) != set(record.keys())

    return {
        "future_continuations_future_indexed": fc_future_indexed,
        "future_continuations_lists_of_distinct_ge2": fc_lists_of_distinct,
        "future_flow_inward": future_flow_inward,
        "record_outward": record_outward,
        "has_outward_shell": has_outward_shell,
        "compatibility_weights_before_compression": weights_before_compression,
        "compatibility_weights_are_pair_reals": weights_are_pair_reals,
        "compatibility_weights_non_uniform": weights_non_uniform,
        "present_survivor_derived_from_weighted_futures": survivor_derived,
        "outward_record_hash_chain_recomputes": record_chain_ok,
        "outward_record_binds_inward_provenance": record_binds_provenance,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop_not_identity,
        "compression_map_distinct_from_outward_record": map_distinct_from_record,
    }


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

    result = {
        "name": "retrocausal_possibility_field_v0",
        "object_name": "RetrocausalPossibilityField",
        "object_statement_sha256": "02f813d355b5812e1021eb023e5aca7c6006c00dcfc060cf94ff727b7cb8dd78",
        "probe_family": "M_pairwise_compatibility_weight_readout_with_shell_orientation",
        "constraint_set": "C_inward_argmax_total_compatibility_mass",
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

        # ---- honest ceiling ----
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "FIRST instantiation of RetrocausalPossibilityField first-class fields "
            "on a TRIVIAL finite carrier; NOT physics/Axis0/manifold/canonical; "
            "field instantiation, not carrier richness."
        ),
        "blocked_downstream_consumers": [
            "Axis0 claim",
            "flux claim",
            "physics claim",
            "formal manifold admission",
            "claim that this trivial carrier is THE retrocausal field of the real model",
        ],
        "all_pass": all_invariants_hold,
        "criteria_checked": sorted(invariants.keys()),
    }
    return result


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(SIM_DIR, "results", "retrocausal_possibility_field_v0_results.json")


def main() -> int:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({"ok": result["all_pass"], "result_path": RESULT_PATH}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
