#!/usr/bin/env python3
"""
bridge_smt_relational.py -- the SMT-relational bridge (BRIDGE_VALIDATION).

Adapts system_v8/bridge_designs/design_smt_relational.md sections 3-5
(shared responds/next vocabulary, z3+cvc5 decide distinguishability,
SAT=distinct/UNSAT=same-block) to the OWNER's corrected contract
(bridge_interface.py). `responds(Observation, Action, Outcome)` collapses
to a direct step_C replay (there is no separate carrier-specific
compilation step to smuggle a native quantum-instrument or set-membership token through); `next` is the
syntactic (root, prefix) -> (root, prefix+(a,)) advance, never an opaque
state comparison.

WHAT IS AND IS NOT DELEGATED TO THE SOLVER (stated honestly, not oversold):
the GROUND FACTS (what step_C actually returns for a given (root, prefix,
action)) can only come from replaying the candidate in Python -- no solver
can call an arbitrary Python object's step_C. What genuinely IS delegated
to z3/cvc5 is the RECURSIVE COMBINATION of those ground facts into a
same/different verdict at depth H: `same_v` for each suffix v is asserted
as a fresh Bool variable via a hard iff-constraint referencing the
PREVIOUSLY DEFINED variable at depth-1 (never a Python-precomputed literal
substituted in), so the solver's own constraint propagation is what decides
the top-level query, via `s.add(Not(same_H)); s.check()`:
UNSAT => same_H is forced True (same block); SAT => a model exists with
same_H False, meaning the ground facts already force it False (distinct).
This is Route B ("explicit distinguishability queries") from the design
doc's section 5, with the private-axiom layer removed (nothing here is
underdetermined -- step_C is a pure function, so there is no genuine
existential search beyond depth-bounded constraint chaining).

z3 and cvc5 encode and decide the SAME recursive definition via two
INDEPENDENTLY WRITTEN builders (`_decide_same_z3`, `_decide_same_cvc5`),
each doing its own ground-fact gathering and solver-formula construction --
not two renderers of one shared AST -- so a bug in either builder is
genuinely catchable by disagreement with the other, and with the pure-
Python `_reference_same` (no solver at all), which is provably the same
relation by structural induction on depth. All three are compared per pair;
disagreement is a real, reportable finding (see SmtDecision.agree), never
silently resolved by picking one.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from gates import normalise_partition  # noqa: E402

from bridge_interface import (  # noqa: E402
    Action,
    CandidateBridgeInterface,
    HistoryPointT,
    Outcome,
    Root,
    replay,
)

import z3  # noqa: E402
import cvc5  # noqa: E402
from cvc5 import Kind as Cvc5Kind  # noqa: E402


def _outcome_after(
    candidate: CandidateBridgeInterface, root: Root, prefix: tuple[Action, ...], action: Action, memo: dict
) -> Outcome:
    state = replay(candidate, root, prefix, memo=memo)
    _next_state, outcome = candidate.step_C(state, action, None)
    return outcome


# ---------------------------------------------------------------------------
# Reference decision -- pure Python, no solver. Provably the same relation
# as induce_action_predictive_partition's signature equality (structural
# induction on depth: sig(x,d)==sig(y,d) iff, for all a, outcome match AND
# sig(succ_x,d-1)==sig(succ_y,d-1), which unfolds to exactly this).
# ---------------------------------------------------------------------------
def _reference_same(
    candidate: CandidateBridgeInterface,
    root_x: Root, prefix_x: tuple[Action, ...],
    root_y: Root, prefix_y: tuple[Action, ...],
    depth: int, alphabet: Sequence[Action], memo: dict,
) -> bool:
    if depth == 0:
        return True
    for a in alphabet:
        if _outcome_after(candidate, root_x, prefix_x, a, memo) != _outcome_after(candidate, root_y, prefix_y, a, memo):
            return False
        if not _reference_same(candidate, root_x, prefix_x + (a,), root_y, prefix_y + (a,), depth - 1, alphabet, memo):
            return False
    return True


# ---------------------------------------------------------------------------
# z3 builder.
# ---------------------------------------------------------------------------
def _decide_same_z3(
    candidate: CandidateBridgeInterface,
    root_x: Root, prefix_x: tuple[Action, ...],
    root_y: Root, prefix_y: tuple[Action, ...],
    horizon: int, alphabet: Sequence[Action], memo: dict,
) -> tuple[str, bool]:
    solver = z3.Solver()
    var_cache: dict = {}
    counter = [0]

    def var(px: tuple, py: tuple, depth: int):
        key = (px, py, depth)
        if key in var_cache:
            return var_cache[key]
        counter[0] += 1
        v = z3.Bool(f"same__{depth}__{counter[0]}")
        var_cache[key] = v
        if depth == 0:
            solver.add(v == z3.BoolVal(True))
        else:
            terms = []
            for a in alphabet:
                ox = _outcome_after(candidate, root_x, px, a, memo)
                oy = _outcome_after(candidate, root_y, py, a, memo)
                eq_outcome = z3.BoolVal(ox == oy)
                sub = var(px + (a,), py + (a,), depth - 1)
                terms.append(z3.And(eq_outcome, sub))
            rhs = z3.And(*terms) if terms else z3.BoolVal(True)
            solver.add(v == rhs)
        return v

    top = var(prefix_x, prefix_y, horizon)
    solver.push()
    solver.add(z3.Not(top))
    result = solver.check()
    solver.pop()
    same = result == z3.unsat
    return str(result), same


# ---------------------------------------------------------------------------
# cvc5 builder -- independently written (own ground-fact gathering, own
# term construction), not a renderer of the z3 builder's structure.
# ---------------------------------------------------------------------------
def _decide_same_cvc5(
    candidate: CandidateBridgeInterface,
    root_x: Root, prefix_x: tuple[Action, ...],
    root_y: Root, prefix_y: tuple[Action, ...],
    horizon: int, alphabet: Sequence[Action], memo: dict,
) -> tuple[str, bool]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_UF")
    solver.setOption("incremental", "true")
    bool_sort = tm.getBooleanSort()
    var_cache: dict = {}
    counter = [0]

    def var(px: tuple, py: tuple, depth: int):
        key = (px, py, depth)
        if key in var_cache:
            return var_cache[key]
        counter[0] += 1
        v = tm.mkConst(bool_sort, f"same__{depth}__{counter[0]}")
        var_cache[key] = v
        if depth == 0:
            solver.assertFormula(tm.mkTerm(Cvc5Kind.EQUAL, v, tm.mkTrue()))
        else:
            conj = []
            for a in alphabet:
                ox = _outcome_after(candidate, root_x, px, a, memo)
                oy = _outcome_after(candidate, root_y, py, a, memo)
                eq_outcome = tm.mkTrue() if ox == oy else tm.mkFalse()
                sub = var(px + (a,), py + (a,), depth - 1)
                conj.append(tm.mkTerm(Cvc5Kind.AND, eq_outcome, sub))
            if not conj:
                rhs = tm.mkTrue()
            elif len(conj) == 1:
                rhs = conj[0]
            else:
                rhs = tm.mkTerm(Cvc5Kind.AND, *conj)
            solver.assertFormula(tm.mkTerm(Cvc5Kind.EQUAL, v, rhs))
        return v

    top = var(prefix_x, prefix_y, horizon)
    solver.push()
    solver.assertFormula(tm.mkTerm(Cvc5Kind.NOT, top))
    result = solver.checkSat()
    solver.pop()
    same = result.isUnsat()
    return str(result), same


@dataclass(frozen=True)
class SmtDecision:
    x: HistoryPointT
    y: HistoryPointT
    horizon: int
    reference_same: bool
    z3_verdict: str
    cvc5_verdict: str
    z3_same: bool
    cvc5_same: bool
    agree: bool

    def to_json(self) -> dict:
        rx, px = self.x
        ry, py = self.y
        return {
            "x": {"root": repr(rx), "prefix": [repr(a) for a in px]},
            "y": {"root": repr(ry), "prefix": [repr(a) for a in py]},
            "horizon": self.horizon,
            "reference_same": self.reference_same,
            "z3_verdict": self.z3_verdict,
            "cvc5_verdict": self.cvc5_verdict,
            "z3_same": self.z3_same,
            "cvc5_same": self.cvc5_same,
            "agree": self.agree,
        }


def smt_same(
    candidate: CandidateBridgeInterface,
    x: HistoryPointT,
    y: HistoryPointT,
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
    memo: Optional[dict] = None,
) -> SmtDecision:
    if action_alphabet is None:
        action_alphabet = candidate.action_alphabet()
    alphabet = tuple(action_alphabet)
    memo = {} if memo is None else memo
    root_x, prefix_x = x[0], tuple(x[1])
    root_y, prefix_y = y[0], tuple(y[1])

    ref = _reference_same(candidate, root_x, prefix_x, root_y, prefix_y, horizon, alphabet, memo)
    z3_verdict, z3_same = _decide_same_z3(candidate, root_x, prefix_x, root_y, prefix_y, horizon, alphabet, memo)
    cvc5_verdict, cvc5_same = _decide_same_cvc5(candidate, root_x, prefix_x, root_y, prefix_y, horizon, alphabet, memo)
    agree = (ref == z3_same == cvc5_same)
    return SmtDecision(
        x=(root_x, prefix_x), y=(root_y, prefix_y), horizon=horizon,
        reference_same=ref, z3_verdict=z3_verdict, cvc5_verdict=cvc5_verdict,
        z3_same=z3_same, cvc5_same=cvc5_same, agree=agree,
    )


@dataclass(frozen=True)
class SmtPartitionResult:
    partition: tuple[int, ...]
    pairwise: dict = field(default_factory=dict)
    disagreements: tuple = ()
    all_agree: bool = True


def induce_smt_relational_partition(
    candidate: CandidateBridgeInterface,
    X: Sequence[HistoryPointT],
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> SmtPartitionResult:
    """pi_C over X, decided pairwise by z3+cvc5 (SAT=distinct, UNSAT=same-
    block), unioned via the SAME union-find pattern gates.py's
    induced_partition uses (the oracle here is 'z3 and cvc5 both agree
    UNSAT' instead of candidate.reidentify). Any z3/cvc5/reference
    disagreement on a pair is recorded and that pair is NOT unioned (an
    honest HOLD on that edge rather than a silently-picked answer)."""
    if not X:
        return SmtPartitionResult(partition=())
    if action_alphabet is None:
        action_alphabet = candidate.action_alphabet()
    alphabet = tuple(action_alphabet)
    if not alphabet:
        raise ValueError("action_alphabet is empty -- nothing to decide distinguishability with")

    memo: dict = {}
    n = len(X)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    pairwise: dict = {}
    disagreements: list = []
    for i in range(n):
        for j in range(i + 1, n):
            decision = smt_same(candidate, X[i], X[j], horizon=horizon, action_alphabet=alphabet, memo=memo)
            pairwise[f"{i}__{j}"] = decision.to_json()
            if not decision.agree:
                disagreements.append(decision.to_json())
            elif decision.reference_same:
                union(i, j)

    labels = [find(i) for i in range(n)]
    partition = normalise_partition(labels)
    return SmtPartitionResult(
        partition=partition, pairwise=pairwise, disagreements=tuple(disagreements),
        all_agree=(len(disagreements) == 0),
    )
