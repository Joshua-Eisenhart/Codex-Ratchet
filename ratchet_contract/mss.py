#!/usr/bin/env python3
"""
mss.py -- the MSS operator. ONE judge: partition coarseness on a probe-honest,
demand-thickened partition. No score, no weighted sum, no machinery count.

Owner correction (binding, applied here): MSS = PARTITION COARSENESS, full
stop. Mirrors system_v7/constraint_core/ratchet/ratchet_engine.py's
`_partition_coarser` and `compute_frontier_cache`: survivors have L_D=0; the
frontier is the coarsest survivors; antichain, never a single winner.
pairwise_mss(A,B,D) compares induced partitions pi_A, pi_B by coarsening
ONLY.

Three-stage pipeline, every stage code-computed, nothing scored or summed:

  STAGE 1 -- ELIGIBILITY. IDENTITY_GATE(A), IDENTITY_GATE(B) must both PASS.
    A candidate whose reidentify() does not exactly reproduce its own
    probe-induced partition has a partition that cannot be trusted --
    INELIGIBLE for comparison (HOLD), not scored down.

  STAGE 2 -- DEMAND-THICKENED SURVIVORSHIP. persistence_gate / evolvability_gate
    / extension_gate (gates.py) each ENLARGE D by pushing it through a
    continuation (persist / evolve / nest-recompute) and re-checking
    survivorship with the SAME kernel. Each layer is opt-in per call
    (thicken_persistence / thicken_evolvability / thicken_wholenest) --
    when requested, failing it makes the candidate INELIGIBLE for THIS
    comparison (HOLD), exactly like stage 1, not a separate score.

  STAGE 3 -- COARSENESS. Only reached if both candidates cleared stages 1-2.
    Compare pi_A, pi_B (both induced over the same base X) via
    partition_coarser. A_WEAKER / B_WEAKER / INCOMPARABLE, computed, never
    LLM judgment.

frontier(candidates, X, D) partitions the pool into PURGATORY (candidates
that failed stage 1 or 2, with the exact failure and a re-entry condition),
BRANCHES (survivors grouped by identical induced partition -- re-merge), and
the ANTICHAIN of nondominated branches (a branch is dominated only when some
other surviving branch is a STRICT coarsening of it). Never a single winner.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Sequence

from contract import CandidatePackage, State
from gates import (
    GateResult,
    Verdict,
    IDENTITY_GATE,
    persistence_gate,
    evolvability_gate,
    extension_gate,
    induced_partition,
    partition_coarser,
    partition_digest,
    collapsed_demand_edges,
)


class MssVerdict(str, Enum):
    A_WEAKER = "A_WEAKER"
    B_WEAKER = "B_WEAKER"
    INCOMPARABLE = "INCOMPARABLE"
    HOLD = "HOLD"


@dataclass(frozen=True)
class MssResult:
    candidate_a: str
    candidate_b: str
    verdict: MssVerdict
    reasons: dict

    def to_json(self) -> dict:
        return {
            "candidate_a": self.candidate_a,
            "candidate_b": self.candidate_b,
            "verdict": self.verdict.value,
            "reasons": self.reasons,
        }


_RE_ENTRY_CONDITIONS = {
    "eligibility_identity_honesty": (
        "reidentify() must agree exactly with the probe-induced partition over X "
        "(no distinction reidentify makes that no probe exposes)"
    ),
    "persistence_demand": (
        "persist() must produce continuations whose reidentify-relation still "
        "separates every base-demanded pair (no collapse under delay/"
        "perturbation/relabeling/partial-access)"
    ),
    "evolvability_demand": (
        "evolve() must return a non-None extension whose reidentify-relation "
        "still separates every base-demanded pair, without adding a new "
        "declared primitive"
    ),
    "wholenest_demand": (
        "the declared nest-interface recompute_digest must match a fresh "
        "recompute of the induced partition"
    ),
}


def _thickened_layers(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    thicken_persistence: bool,
    persistence_kwargs: Optional[dict],
    thicken_evolvability: bool,
    new_constraint: Any,
    thicken_wholenest: bool,
) -> list[tuple[str, GateResult]]:
    """Run whichever demand-thickening layers were requested; return the
    (layer_label, GateResult) pairs that did NOT pass (HOLD counts as
    passing for extension_gate specifically -- a shell-local candidate with
    no nest claim is not penalized for declaring none)."""
    failures: list[tuple[str, GateResult]] = []
    if thicken_persistence:
        r = persistence_gate(candidate, X, D, **(persistence_kwargs or {}))
        if r.verdict != Verdict.PASS:
            failures.append(("persistence_demand", r))
    if thicken_evolvability:
        r = evolvability_gate(candidate, X, D, new_constraint=new_constraint)
        if r.verdict != Verdict.PASS:
            failures.append(("evolvability_demand", r))
    if thicken_wholenest:
        r = extension_gate(candidate, X, D)
        if r.verdict not in (Verdict.PASS, Verdict.HOLD):
            failures.append(("wholenest_demand", r))
    return failures


def pairwise_mss(
    A: CandidatePackage,
    B: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    thicken_persistence: bool = False,
    persistence_kwargs: Optional[dict] = None,
    thicken_evolvability: bool = False,
    new_constraint: Any = "probe_generic_extension",
    thicken_wholenest: bool = False,
) -> MssResult:
    # STAGE 1 -- eligibility (identity-honesty control).
    id_a, id_b = IDENTITY_GATE(A, X), IDENTITY_GATE(B, X)
    if id_a.verdict != Verdict.PASS or id_b.verdict != Verdict.PASS:
        return MssResult(A.name, B.name, MssVerdict.HOLD, {
            "stage": "eligibility",
            "reason": (
                "a candidate whose partition is not probe-honest is ineligible "
                "for the coarseness comparison -- its partition cannot be trusted"
            ),
            "identity_A": id_a.to_json(), "identity_B": id_b.to_json(),
        })

    # STAGE 2 -- demand-thickened survivorship (opt-in layers).
    fail_a = _thickened_layers(A, X, D, thicken_persistence=thicken_persistence,
                                persistence_kwargs=persistence_kwargs,
                                thicken_evolvability=thicken_evolvability,
                                new_constraint=new_constraint, thicken_wholenest=thicken_wholenest)
    fail_b = _thickened_layers(B, X, D, thicken_persistence=thicken_persistence,
                                persistence_kwargs=persistence_kwargs,
                                thicken_evolvability=thicken_evolvability,
                                new_constraint=new_constraint, thicken_wholenest=thicken_wholenest)
    if fail_a or fail_b:
        return MssResult(A.name, B.name, MssVerdict.HOLD, {
            "stage": "demand_thickened_survivorship",
            "reason": "does not survive the demand-thickened comparison",
            "failures_A": [{"layer": lbl, "verdict": r.verdict.value, "detail": r.reasons} for lbl, r in fail_a],
            "failures_B": [{"layer": lbl, "verdict": r.verdict.value, "detail": r.reasons} for lbl, r in fail_b],
        })

    # STAGE 3 -- coarseness, over the base (X, D) only.
    pi_a = induced_partition(A, X)
    pi_b = induced_partition(B, X)
    index = {x: i for i, x in enumerate(X)}
    collapsed_a = collapsed_demand_edges(pi_a, index, D)
    collapsed_b = collapsed_demand_edges(pi_b, index, D)
    if collapsed_a or collapsed_b:
        return MssResult(A.name, B.name, MssVerdict.HOLD, {
            "stage": "base_survivorship",
            "reason": "does not preserve every demanded distinction in the base demand set D",
            "collapsed_edges_A": [[repr(x), repr(y)] for x, y in collapsed_a],
            "collapsed_edges_B": [[repr(x), repr(y)] for x, y in collapsed_b],
        })

    a_coarser = partition_coarser(pi_a, pi_b)
    b_coarser = partition_coarser(pi_b, pi_a)
    equal = pi_a == pi_b

    detail = {
        "stage": "coarseness",
        "pi_A": list(pi_a), "pi_B": list(pi_b),
        "cells_A": len(set(pi_a)), "cells_B": len(set(pi_b)),
        "partition_digest_A": partition_digest(pi_a), "partition_digest_B": partition_digest(pi_b),
    }

    if equal:
        detail["reason"] = "identical induced partitions over the base surface -- re-mergeable, no strict order"
        return MssResult(A.name, B.name, MssVerdict.INCOMPARABLE, detail)
    if a_coarser and not b_coarser:
        detail["reason"] = (
            "A's partition is a strict coarsening of B's -- A preserves every demanded "
            "distinction B preserves using fewer distinctions overall (more MSS)"
        )
        return MssResult(A.name, B.name, MssVerdict.A_WEAKER, detail)
    if b_coarser and not a_coarser:
        detail["reason"] = (
            "B's partition is a strict coarsening of A's -- B preserves every demanded "
            "distinction A preserves using fewer distinctions overall (more MSS)"
        )
        return MssResult(A.name, B.name, MssVerdict.B_WEAKER, detail)
    detail["reason"] = "neither partition is a coarsening of the other -- genuinely incomparable"
    return MssResult(A.name, B.name, MssVerdict.INCOMPARABLE, detail)


def frontier(
    candidates: Sequence[CandidatePackage],
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    thicken_persistence: bool = False,
    persistence_kwargs: Optional[dict] = None,
    thicken_evolvability: bool = False,
    new_constraint: Any = "probe_generic_extension",
    thicken_wholenest: bool = False,
) -> dict:
    """Returns the nondominated antichain -- NEVER a single winner. Also
    reports PURGATORY (candidates that dead-end at eligibility or a
    demand-thickened layer, with the exact failure and a re-entry
    condition) and BRANCHES (survivors grouped by identical induced
    partition -- two branches inducing the same partition re-merge into
    one)."""
    purgatory: list[dict] = []
    survivors: list[CandidatePackage] = []

    for C in candidates:
        idg = IDENTITY_GATE(C, X)
        if idg.verdict != Verdict.PASS:
            purgatory.append({
                "candidate": C.name,
                "failed_at": "eligibility_identity_honesty",
                "reason": idg.reasons,
                "re_entry_condition": _RE_ENTRY_CONDITIONS["eligibility_identity_honesty"],
            })
            continue

        layer_failures = _thickened_layers(
            C, X, D, thicken_persistence=thicken_persistence, persistence_kwargs=persistence_kwargs,
            thicken_evolvability=thicken_evolvability, new_constraint=new_constraint,
            thicken_wholenest=thicken_wholenest,
        )
        if layer_failures:
            label, r = layer_failures[0]
            purgatory.append({
                "candidate": C.name,
                "failed_at": label,
                "reason": r.reasons,
                "re_entry_condition": _RE_ENTRY_CONDITIONS[label],
                "all_failed_layers": [lbl for lbl, _ in layer_failures],
            })
            continue

        pi_c = induced_partition(C, X)
        index = {x: i for i, x in enumerate(X)}
        collapsed = collapsed_demand_edges(pi_c, index, D)
        if collapsed:
            purgatory.append({
                "candidate": C.name,
                "failed_at": "base_survivorship",
                "reason": {"collapsed_edges": [[repr(x), repr(y)] for x, y in collapsed]},
                "re_entry_condition": "the candidate's own induced partition must not collapse any pair in D",
            })
            continue

        survivors.append(C)

    # Branches: group survivors by identical induced-partition digest (re-merge).
    partitions = {c.name: induced_partition(c, X) for c in survivors}
    digests = {name: partition_digest(p) for name, p in partitions.items()}
    branch_map: dict[str, list[str]] = {}
    for c in survivors:
        branch_map.setdefault(digests[c.name], []).append(c.name)
    branches = [
        {"partition_digest": dg, "members": sorted(members), "cells": len(set(partitions[members[0]]))}
        for dg, members in branch_map.items()
    ]

    # Pairwise coarseness among survivors -> dominance.
    pairwise: dict[str, dict] = {}
    dominated: set[str] = set()
    for A, B in itertools.combinations(survivors, 2):
        r = pairwise_mss(
            A, B, X, D, thicken_persistence=thicken_persistence, persistence_kwargs=persistence_kwargs,
            thicken_evolvability=thicken_evolvability, new_constraint=new_constraint,
            thicken_wholenest=thicken_wholenest,
        )
        pairwise[f"{A.name}__vs__{B.name}"] = r.to_json()
        if r.verdict == MssVerdict.A_WEAKER:
            dominated.add(B.name)
        elif r.verdict == MssVerdict.B_WEAKER:
            dominated.add(A.name)

    antichain_branches = [b for b in branches if not any(m in dominated for m in b["members"])]
    antichain = sorted(b["members"][0] for b in antichain_branches)

    return {
        "purgatory": purgatory,
        "survivors": [c.name for c in survivors],
        "branches": branches,
        "dominated": sorted(dominated),
        "antichain": antichain,
        "pairwise": pairwise,
    }
