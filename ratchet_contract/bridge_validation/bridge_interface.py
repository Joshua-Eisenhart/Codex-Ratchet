#!/usr/bin/env python3
"""
bridge_interface.py -- the CORRECTED candidate interface for BRIDGE_VALIDATION.

Scope (binding, see README.md): this module, and everything under
bridge_validation/, tests whether a proposed trace->partition bridge honestly
lets the FIXED ratchet (ratchet_contract/gates.py, mss.py) see competing
candidates. It does NOT ratchet the axioms and does NOT admit any real
carrier. `promotion_allowed: false` everywhere in this package.

CORRECTED CONTRACT (owner corrections, 2026-07-20 -- these override
system_v8/bridge_designs/design_action_predictive_quotient.md and
design_smt_relational.md wherever the two disagree):

  input   = a finite ORDERED PROBE WORD (a sequence of public actions).
            NOT primitive time, NOT a causal state machine -- just an
            ordered finite history. A `HistoryPoint` = (root, prefix) is
            the SYNTACTIC address of one such history: candidate-independent,
            never a carrier state, never hashed/compared as an identity
            claim by any bridge in this package.

  output  = a finite OUTCOME RECORD (`Outcome`, a multiplicity table over a
            finite OutcomeToken alphabet) + an OPAQUE continuation state.
            NO continuous/primitive probabilities anywhere on the shared
            surface -- multiplicities are positive ints (counts / relative
            weights / instrument-branch weights), never floats.

  candidate interface: step_C(s, a, nest_context) -> (s', o). `s` is
            OPAQUE: no bridge in this package ever compares, hashes, or
            exposes an OpaqueState to a partition decision. Bridges only
            ever compare Outcome records produced by replaying probe words
            from the SYNTACTIC (root, prefix) address (see `replay` below).

  public action vocabulary = MANIFOLD-NATIVE ops (MANIFOLD_ACTION_CATEGORIES
            below), never POVM/membership/eigenprojector tokens.

  predictive quotient: h ~_C h' iff, for every action word u with
            |u| <= horizon H, replaying u from h and from h' produces
            identical Outcome traces. Deterministic equality over finite
            outcome records -- no primitive probability anywhere in the
            comparison.

BOOKKEEPING vs ILLICIT IDENTITY (the rule every control in controls.py and
every self-test in bridge_self_tests.py is built to exercise): code MAY use
raw IDs/indices/hashes/equality for implementation bookkeeping (a memo
dict keyed by (root, prefix), a dict lookup keyed by a raw action-token
string whose VALUE is the declared meaning) -- that is not forbidden A=A.
The violation is ONLY when a handle ALTERS THE SEMANTIC RESULT without an
allowed probe/history exposing the difference (see controls.py C2 and
bridge_self_tests.py's hidden-lookup-table self-test for the positive and
negative demonstrations).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Hashable, Optional, Sequence

# ---------------------------------------------------------------------------
# Type aliases. Structurally open (Hashable), matching contract.py's own
# convention -- nothing here presumes a shape beyond "usable as a dict key".
# ---------------------------------------------------------------------------
Root = Hashable
Action = Hashable
OutcomeToken = Hashable
OpaqueState = Hashable
HistoryPointT = tuple  # (Root, tuple[Action, ...]) -- see history_point() below


def history_point(root: Root, prefix: Sequence[Action] = ()) -> tuple:
    """Build a syntactic (root, prefix) address. This is the unit BOTH
    bridges induce a partition over -- never an OpaqueState."""
    return (root, tuple(prefix))


def extend_history(x: tuple, action: Action) -> tuple:
    root, prefix = x
    return (root, prefix + (action,))


def hp_json(x: tuple) -> dict:
    """JSON-safe rendering of a HistoryPoint for receipts."""
    root, prefix = x
    return {"root": repr(root), "prefix": [repr(a) for a in prefix]}


# ---------------------------------------------------------------------------
# The manifold-native public action vocabulary (owner-corrected -- replaces
# the POVM/membership-flavoured vocabulary sketched in the earlier design
# docs). A concrete Action token may be a bare string drawn from one of
# these categories, or a parameterized tuple such as
# ("ordered_compose", ("write_a", "write_b")) -- action_category() below is
# how a candidate declares which bucket a given token belongs to.
# ---------------------------------------------------------------------------
MANIFOLD_ACTION_CATEGORIES: tuple[str, ...] = (
    "prepare_restrict",
    "ordered_compose",
    "bracket_compose",
    "perturb",
    "delay_retain_history",
    "couple_inner_outer",
    "couple_neighbor_neighbor",
    "renest",
    "extend_under_constraint",
    "read_outcome",
)

# Mechanical scan target (used by run_bridge_validation.py, which excludes
# THIS file from the scan since the forbidden vocabulary necessarily has to
# be spelled out here to be documented at all). Chosen as API-call-shaped or
# otherwise unlikely-in-ordinary-prose substrings, mirroring
# run_contract_selfcheck.py's own token choices ("requests.", "os.system(")
# rather than bare English words that would false-positive on discussion
# prose in docstrings/comments.
FORBIDDEN_SURFACE_TOKENS: tuple[str, ...] = (
    "povm",
    "eigenprojector",
    "membership(",
    "basis_index",
    "raw_state_id",
    "time.time(",
    "datetime.now(",
    "perf_counter(",
    "causal_state_machine",
)


# ---------------------------------------------------------------------------
# Outcome -- the finite multiplicity table. This is what "no continuous
# probability" cashes out to: a candidate reporting a stochastic/quantum
# instrument exposes finitely many outcome tokens and their integer
# multiplicities (counts / relative weights), never a float chance.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Outcome:
    entries: tuple[tuple[OutcomeToken, int], ...]

    def __post_init__(self) -> None:
        normalized = tuple(sorted(self.entries, key=lambda kv: repr(kv[0])))
        object.__setattr__(self, "entries", normalized)
        seen = set()
        for tok, mult in normalized:
            if not isinstance(mult, int) or mult <= 0:
                raise ValueError(
                    f"Outcome multiplicity must be a positive int, got {mult!r} for token {tok!r} "
                    "-- multiplicities are counts/weights, never primitive probabilities"
                )
            if tok in seen:
                raise ValueError(f"Outcome token {tok!r} repeated -- pre-merge multiplicities before constructing")
            seen.add(tok)

    @staticmethod
    def deterministic(token: OutcomeToken) -> "Outcome":
        return Outcome(((token, 1),))

    @staticmethod
    def table(mapping: dict) -> "Outcome":
        return Outcome(tuple(mapping.items()))

    def tokens(self) -> tuple[OutcomeToken, ...]:
        return tuple(tok for tok, _ in self.entries)


@dataclass(frozen=True)
class NestContext:
    """Optional coupling context for couple_inner_outer / couple_neighbor_neighbor
    / renest actions. NOTE (honest scope limit): neither bridge in this
    package threads a non-None NestContext through step_C -- every replay
    call passes nest_context=None. Exercising couple_*/renest actions here
    is done via each toy candidate's OWN self-contained internal behaviour,
    never via real cross-candidate wiring. Real multi-shell coupling is out
    of scope (owner: 'adapting real carriers (NOT done here)'). The field
    still exists because step_C's signature must accept it."""

    inner: Optional[OpaqueState] = None
    outer: Optional[OpaqueState] = None
    neighbors: tuple[OpaqueState, ...] = ()


# ---------------------------------------------------------------------------
# The corrected candidate interface.
# ---------------------------------------------------------------------------
class CandidateBridgeInterface(ABC):
    """Every candidate/deck in controls.py and bridge_self_tests.py
    implements this. `step_C` is the ONLY way any bridge may advance a
    candidate -- fixed argument order (state, action, nest_context)."""

    name: str = "unnamed_bridge_candidate"

    @abstractmethod
    def action_alphabet(self) -> Sequence[Action]:
        """Finite public action alphabet this candidate accepts."""

    @abstractmethod
    def action_category(self, action: Action) -> str:
        """Which MANIFOLD_ACTION_CATEGORIES bucket `action` belongs to."""

    @abstractmethod
    def initial_state(self, root: Root) -> OpaqueState:
        """Opaque starting continuation handle for one public root."""

    @abstractmethod
    def step_C(
        self, state: OpaqueState, action: Action, nest_context: Optional[NestContext] = None
    ) -> tuple[OpaqueState, "Outcome"]:
        """(s, a, nest_context) -> (s', o). Pure/deterministic: the same
        (s, a, nest_context) always returns the same (s', o) -- no
        unrecorded randomness at call time (design_action_predictive_quotient.md
        section 3, point 1). `o` is a finite Outcome, never a primitive
        float probability. `s'` is a new OPAQUE state."""


# ---------------------------------------------------------------------------
# Shared plumbing: deterministic replay, addressed SYNTACTICALLY by
# (root, prefix), never by opaque-state identity. `memo`, when supplied, is
# BOOKKEEPING ONLY (a cache keyed by the syntactic address) -- see the
# module docstring's bookkeeping-vs-illicit-identity rule.
# ---------------------------------------------------------------------------
def replay(
    candidate: CandidateBridgeInterface,
    root: Root,
    prefix: Sequence[Action],
    *,
    memo: Optional[dict] = None,
) -> OpaqueState:
    prefix = tuple(prefix)
    key = (root, prefix)
    if memo is not None and key in memo:
        return memo[key]
    if not prefix:
        state = candidate.initial_state(root)
    else:
        parent_state = replay(candidate, root, prefix[:-1], memo=memo)
        state, _outcome = candidate.step_C(parent_state, prefix[-1], None)
    if memo is not None:
        memo[key] = state
    return state


def step_outcome(
    candidate: CandidateBridgeInterface,
    root: Root,
    prefix: Sequence[Action],
    action: Action,
    *,
    memo: Optional[dict] = None,
) -> Outcome:
    state = replay(candidate, root, prefix, memo=memo)
    _next_state, outcome = candidate.step_C(state, action, None)
    return outcome


def run_word(
    candidate: CandidateBridgeInterface,
    root: Root,
    word: Sequence[Action],
    *,
    memo: Optional[dict] = None,
) -> tuple[OpaqueState, tuple[Outcome, ...]]:
    """Full outcome trace for one ordered probe word from `root`. Returns
    (final_state, outcome_trace)."""
    state = replay(candidate, root, (), memo=memo)
    trace: list[Outcome] = []
    prefix: tuple[Action, ...] = ()
    for a in word:
        state, o = candidate.step_C(state, a, None)
        trace.append(o)
        prefix = prefix + (a,)
        if memo is not None:
            memo[(root, prefix)] = state
    return state, tuple(trace)


def probe_outcomes(
    candidate: CandidateBridgeInterface,
    root: Root,
    prefixes: Sequence[Sequence[Action]],
    final_action: Action,
    *,
    memo: Optional[dict] = None,
) -> dict:
    """For each prefix, replay it from root then apply `final_action` once
    more; return {prefix_tuple: repr(outcome)}. Shared convenience for
    relabeling/encoding-invariance checks and canary probes (controls.py C2,
    C7; bridge_self_tests.py)."""
    memo = {} if memo is None else memo
    out = {}
    for prefix in prefixes:
        prefix = tuple(prefix)
        out[prefix] = repr(step_outcome(candidate, root, prefix, final_action, memo=memo))
    return out


# ---------------------------------------------------------------------------
# Shared receipt shape -- mirrors gates.py's GateResult (verdict + reasons
# dict, nothing decided from prose).
# ---------------------------------------------------------------------------
class CheckLabel(str, Enum):
    """Generic bucket a control's specific finding is classified into, for
    the roll-up confirmations in run_bridge_validation.py. The SPECIFIC
    finding always also has a free-text `label` on BridgeCheckResult."""

    PASS = "PASS"
    FAIL = "FAIL"
    HOLD = "HOLD"
    DETECTED = "DETECTED"
    DEAD_END = "DEAD_END"


@dataclass(frozen=True)
class BridgeCheckResult:
    check: str
    label: str
    expected_label: str
    fired_as_expected: bool
    reasons: dict

    def to_json(self) -> dict:
        return {
            "check": self.check,
            "label": self.label,
            "expected_label": self.expected_label,
            "fired_as_expected": self.fired_as_expected,
            "reasons": self.reasons,
        }
