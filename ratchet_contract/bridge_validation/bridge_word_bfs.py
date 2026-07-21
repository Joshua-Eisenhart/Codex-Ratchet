#!/usr/bin/env python3
"""
bridge_word_bfs.py -- the FORWARD WORD-ENUMERATION rival bridge
(BRIDGE_VALIDATION).

Decides the SAME target relation as bridge_action_predictive.py and
bridge_smt_relational.py (bridge_interface.py's predictive quotient):

    h ~_C h' iff, for every action word u with |u| <= horizon, replaying u
    from h and from h' produces identical Outcome traces.

...but by a STRUCTURALLY DIFFERENT derivation path: genuine FORWARD
breadth-first enumeration of action words, level by level, comparing the
replayed Outcome multiplicity table at every prefix as it is produced.
There is no backward recursion here (contrast bridge_action_predictive.py's
`_signature`, which recurses from depth=`horizon` down to depth=0) and no
memoized per-history "signature" object standing in for the
universally-quantified statement -- only outcome traces, compared directly
as the word frontier is grown one action at a time. A live frontier of
(word, state_x, state_y) triples is extended action-by-action; the moment
any extension's immediate Outcome differs between the x-branch and the
y-branch, that extension word is the (shortest, by BFS construction)
separating witness, exactly mirroring bridge_action_predictive.py's own
`separating_witness` brute-force reference path, but used here as the
PRIMARY partition-induction algorithm rather than a secondary
cross-validation check.

Because the derivation differs end to end -- forward word enumeration vs
backward color-refinement recursion (bridge_action_predictive.py) vs SMT
encoding (bridge_smt_relational.py) -- agreement between this bridge and
either of the other two is a REAL cross-check: the three do not share a
computation, only a target relation.

Imports ONLY from bridge_interface and stdlib. In particular, gates.py's
`normalise_partition` is deliberately NOT reused here (contrast
bridge_action_predictive.py, which reuses it) -- the union-find + canonical
block-label encoding below is reimplemented locally so this bridge's
partition-induction path is independent of the other bridges end to end,
not just at the pairwise-relation step.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from bridge_interface import (
    Action,
    CandidateBridgeInterface,
    HistoryPointT,
    Outcome,
    Root,
    replay,
)


def _normalise_partition(labels: Sequence[Any]) -> tuple[int, ...]:
    """Canonical block-label encoding, first-seen-gets-lowest-label -- the
    same convention as gates.py's `normalise_partition`, reimplemented
    locally (not imported) per the module docstring's independence rule."""
    seen: dict[Any, int] = {}
    out: list[int] = []
    for v in labels:
        if v not in seen:
            seen[v] = len(seen)
        out.append(seen[v])
    return tuple(out)


def separating_word_bfs(
    candidate: CandidateBridgeInterface,
    x: HistoryPointT,
    y: HistoryPointT,
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> Optional[tuple[Action, ...]]:
    """Shortest action word u (|u| <= horizon) whose outcome trace differs
    between x=(root,prefix) and y=(root',prefix'), found by genuine forward
    breadth-first enumeration. The frontier holds one live (word, state_x,
    state_y) triple per surviving word of the current length; each level
    extends every surviving word by one action, comparing the immediate
    Outcome produced by that single step -- a mismatch at ANY prefix along
    the way is caught the level it first occurs, since that prefix IS the
    word at that BFS depth. Returns None if no word separates within
    horizon (x, y indistinguishable at this horizon)."""
    if action_alphabet is None:
        action_alphabet = candidate.action_alphabet()
    alphabet = tuple(action_alphabet)
    root_x, prefix_x = x
    root_y, prefix_y = y
    prefix_x, prefix_y = tuple(prefix_x), tuple(prefix_y)

    # ONE replay call per side to reach the starting (root, prefix) address
    # -- shared bridge_interface.py plumbing, not part of the word-search
    # algorithm itself (see bridge_interface.py's replay() docstring: this
    # is the SYNTACTIC address lookup every bridge in this package shares).
    state_x = replay(candidate, root_x, prefix_x)
    state_y = replay(candidate, root_y, prefix_y)

    frontier: list[tuple[tuple[Action, ...], Any, Any]] = [((), state_x, state_y)]
    for _depth in range(1, horizon + 1):
        next_frontier: list[tuple[tuple[Action, ...], Any, Any]] = []
        for word, sx, sy in frontier:
            for a in alphabet:
                sx2, ox = candidate.step_C(sx, a, None)
                sy2, oy = candidate.step_C(sy, a, None)
                new_word = word + (a,)
                if ox != oy:
                    return new_word
                next_frontier.append((new_word, sx2, sy2))
        frontier = next_frontier
    return None


def indistinguishable_word_bfs(
    candidate: CandidateBridgeInterface,
    x: HistoryPointT,
    y: HistoryPointT,
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> bool:
    """h ~_C h' at this horizon iff no separating word exists."""
    return separating_word_bfs(candidate, x, y, horizon=horizon, action_alphabet=action_alphabet) is None


def induce_word_bfs_partition(
    candidate: CandidateBridgeInterface,
    X: Sequence[HistoryPointT],
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> tuple[int, ...]:
    """pi_C over X: for every pair (x, y) in X, decide indistinguishability
    by forward word-BFS (separating_word_bfs), then induce the partition
    from that pairwise relation via union-find + transitive closure --
    mirroring gates.py's `induced_partition` shape (generalized from a
    `reidentify` oracle to `indistinguishable_word_bfs`), but reimplemented
    locally per the module docstring's independence rule."""
    n = len(X)
    if n == 0:
        return ()
    if action_alphabet is None:
        action_alphabet = candidate.action_alphabet()
    alphabet = tuple(action_alphabet)
    if not alphabet:
        raise ValueError("action_alphabet is empty -- nothing to enumerate words with")

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

    for i in range(n):
        for j in range(i + 1, n):
            if indistinguishable_word_bfs(candidate, X[i], X[j], horizon=horizon, action_alphabet=alphabet):
                union(i, j)

    return _normalise_partition([find(i) for i in range(n)])
