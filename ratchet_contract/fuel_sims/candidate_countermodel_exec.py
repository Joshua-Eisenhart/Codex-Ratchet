#!/usr/bin/env python3
"""
candidate_countermodel_exec.py -- the countermodel lookup/replay carrier for
the bridge-validation fuel campaign.

This candidate reproduces ClassicalRelationalExecCandidate's outcome tables
without a relational composition mechanism of its own. It has no index set,
no step relation, no closure, and no relational mechanism: its only semantic
surface is a flat, precomputed replayed lookup table over bounded syntactic
addresses. The continuation state is just `(root, prefix)`.

SCOPE (binding): practice/fuel development only. This is a countermodel, not
an admission or a scientific claim.
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path
from typing import Optional, Sequence

_FUEL_SIMS_DIR = Path(__file__).resolve().parent
_RATCHET_CONTRACT_DIR = _FUEL_SIMS_DIR.parent
_BRIDGE_VALIDATION_DIR = _RATCHET_CONTRACT_DIR / "bridge_validation"
for _p in (_FUEL_SIMS_DIR, _RATCHET_CONTRACT_DIR, _BRIDGE_VALIDATION_DIR):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from bridge_interface import (  # noqa: E402
    Action,
    CandidateBridgeInterface,
    NestContext,
    Outcome,
    replay,
)
from candidate_classical_exec import (  # noqa: E402
    ACTIONS,
    ROOTS,
    _ACTION_CATEGORY,
    ClassicalRelationalExecCandidate,
)


def _build_lookup() -> dict[tuple[str, tuple[Action, ...], Action], Outcome]:
    classical = ClassicalRelationalExecCandidate()
    table = {}
    memo: dict = {}
    for root in ROOTS:
        for length in (0, 1):
            for prefix in product(ACTIONS, repeat=length):
                prefix = tuple(prefix)
                state = replay(classical, root, prefix, memo=memo)
                for action in ACTIONS:
                    _next_state, outcome = classical.step_C(state, action, None)
                    table[(root, prefix, action)] = outcome
    return table


_LOOKUP: dict[tuple[str, tuple[Action, ...], Action], Outcome] = _build_lookup()


class CountermodelLookupReplayExecCandidate(CandidateBridgeInterface):
    """Flat countermodel whose semantics are only replayed table lookups."""

    name = "countermodel_lookup_replay_exec"

    def action_alphabet(self) -> Sequence[Action]:
        return ACTIONS

    def action_category(self, action: Action) -> str:
        return _ACTION_CATEGORY[action]

    def initial_state(self, root):
        return (root, ())

    def step_C(self, state, action, nest_context: Optional[NestContext] = None):
        root, prefix = state
        prefix = tuple(prefix)
        key = (root, prefix, action)
        try:
            outcome = _LOOKUP[key]
        except KeyError as exc:
            raise ValueError(f"countermodel lookup missing bounded key {key!r}") from exc
        return (root, prefix + (action,)), outcome


if __name__ == "__main__":
    c = CountermodelLookupReplayExecCandidate()
    s = c.initial_state("root_00")
    s, _ = c.step_C(s, ("ordered_compose", ("H0", "CNOT01")))
    _s, outcome = c.step_C(s, "read_outcome_z")
    print("countermodel root_00 -> H0,CNOT01 -> read_outcome_z:", outcome)
