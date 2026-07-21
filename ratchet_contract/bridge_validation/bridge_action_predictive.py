#!/usr/bin/env python3
"""
bridge_action_predictive.py -- the predictive-quotient bridge (BRIDGE_VALIDATION).

Adapts system_v8/bridge_designs/design_action_predictive_quotient.md
section 5's bounded backward color-refinement recursion (kappa_t) to the
OWNER's corrected contract (bridge_interface.py): outcomes are exact finite
multiplicity tables (`Outcome`), compared by structural equality. There is
no quantizer step (design doc section 3.1's Q_epsilon) because there is
nothing continuous left to quantize -- the single biggest simplification
the correction buys.

h ~_C h' iff, for every action word u with |u| <= horizon, replaying u from
h and from h' produces identical Outcome traces. The recursion below is an
efficient (memoized, bottom-up) encoding of exactly that
universally-quantified-over-u statement -- provably the same relation as
brute-force enumeration of every u (see separating_witness, which DOES
brute-force enumerate, for the reference/debugging path and for producing a
human-readable separating witness).

`induce_action_predictive_partition` NEVER calls `==` or `hash()` on an
OpaqueState. It only ever compares Outcome records reached via `replay()`,
addressed by the SYNTACTIC (root, prefix) pair -- see bridge_interface.py's
module docstring for the bookkeeping-vs-illicit-identity rule this
discipline is required by.
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path
from typing import Any, Optional, Sequence

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from gates import normalise_partition  # noqa: E402 -- reused, not reimplemented

from bridge_interface import (  # noqa: E402
    Action,
    CandidateBridgeInterface,
    HistoryPointT,
    Outcome,
    Root,
    replay,
)

_BASE_SIGNATURE = ("HORIZON_EXHAUSTED",)


def _outcome_after(
    candidate: CandidateBridgeInterface, root: Root, prefix: tuple[Action, ...], action: Action, memo: dict
) -> Outcome:
    state = replay(candidate, root, prefix, memo=memo)
    _next_state, outcome = candidate.step_C(state, action, None)
    return outcome


def _signature(
    candidate: CandidateBridgeInterface,
    root: Root,
    prefix: tuple[Action, ...],
    depth: int,
    alphabet: Sequence[Action],
    memo: dict,
    sig_cache: dict,
) -> Any:
    key = (root, prefix, depth)
    if key in sig_cache:
        return sig_cache[key]
    if depth == 0:
        sig_cache[key] = _BASE_SIGNATURE
        return _BASE_SIGNATURE
    parts = []
    for a in alphabet:
        outcome = _outcome_after(candidate, root, prefix, a, memo)
        sub_sig = _signature(candidate, root, prefix + (a,), depth - 1, alphabet, memo, sig_cache)
        parts.append((a, outcome, sub_sig))
    sig = tuple(parts)
    sig_cache[key] = sig
    return sig


def induce_action_predictive_partition(
    candidate: CandidateBridgeInterface,
    X: Sequence[HistoryPointT],
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> tuple[int, ...]:
    """pi_C over X, via the bounded backward recursion. X entries are
    (root, prefix) HistoryPoints -- syntactic addresses, never opaque
    states. Reuses gates.py's normalise_partition (canonical block-label
    encoding) rather than reimplementing it."""
    if not X:
        return ()
    if action_alphabet is None:
        action_alphabet = candidate.action_alphabet()
    alphabet = tuple(action_alphabet)
    if not alphabet:
        raise ValueError("action_alphabet is empty -- nothing to induce a partition with")
    memo: dict = {}
    sig_cache: dict = {}
    signatures = []
    for (root, prefix) in X:
        prefix = tuple(prefix)
        signatures.append(_signature(candidate, root, prefix, horizon, alphabet, memo, sig_cache))
    return normalise_partition(signatures)


def separating_witness(
    candidate: CandidateBridgeInterface,
    x: HistoryPointT,
    y: HistoryPointT,
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> Optional[tuple[Action, ...]]:
    """Shortest continuation word u (|u| <= horizon) whose outcome trace
    differs between x=(root,prefix) and y=(root',prefix'). Returns None if
    no such word exists within horizon (x, y indistinguishable at this
    horizon -- consistent with induce_action_predictive_partition placing
    them in the same block). Brute-force BFS over word length: this is the
    definitional check (design doc section 5's 'for all u'), used here to
    cross-validate the recursive signature above and to produce a
    human-readable witness for receipts -- deliberately not the scalable
    path (fine for this campaign's tiny toy decks, not meant to scale)."""
    if action_alphabet is None:
        action_alphabet = candidate.action_alphabet()
    alphabet = tuple(action_alphabet)
    memo: dict = {}
    root_x, prefix_x = x
    root_y, prefix_y = y
    prefix_x, prefix_y = tuple(prefix_x), tuple(prefix_y)

    for length in range(0, horizon + 1):
        for u in product(alphabet, repeat=length):
            px, py = prefix_x, prefix_y
            trace_x = []
            trace_y = []
            for a in u:
                trace_x.append(_outcome_after(candidate, root_x, px, a, memo))
                trace_y.append(_outcome_after(candidate, root_y, py, a, memo))
                px = px + (a,)
                py = py + (a,)
            if tuple(trace_x) != tuple(trace_y):
                return u
    return None
