#!/usr/bin/env python3
"""
candidate_ablation_exec.py -- the flattened ablation control applied to the
concrete ClassicalRelationalExecCandidate carrier.

Composition/nesting is severed to identity-on-later-steps: ordered_compose
and bracket_compose apply only their first named rewrite and ignore the rest.
Everything else in the classical `(weights, edges)` carrier is intact,
including its named rewrites, readouts, delays, couplings, renest, prepares,
and constraint extension. This adapts candidate_ablation_flattened.md's
ablation concept to this executable concrete carrier.

SCOPE (binding): practice/fuel development only. This is a control, not an
admission or a scientific claim.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Sequence

_FUEL_SIMS_DIR = Path(__file__).resolve().parent
_RATCHET_CONTRACT_DIR = _FUEL_SIMS_DIR.parent
_BRIDGE_VALIDATION_DIR = _RATCHET_CONTRACT_DIR / "bridge_validation"
for _p in (_FUEL_SIMS_DIR, _RATCHET_CONTRACT_DIR, _BRIDGE_VALIDATION_DIR):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from bridge_interface import Action, NestContext  # noqa: E402
from candidate_classical_exec import (  # noqa: E402
    ACTIONS,
    ROOTS,
    _ACTION_CATEGORY,
    _REWRITES,
    ClassicalRelationalExecCandidate,
)


class AblationFlattenedExecCandidate(ClassicalRelationalExecCandidate):
    """Classical carrier with only multi-step composition flattened."""

    name = "ablation_flattened_exec"

    def action_alphabet(self) -> Sequence[Action]:
        return ACTIONS

    def action_category(self, action: Action) -> str:
        return _ACTION_CATEGORY[action]

    def step_C(self, state, action, nest_context: Optional[NestContext] = None):
        if isinstance(action, tuple) and action[0] == "ordered_compose":
            weights, edges = state
            first_name = action[1][0]
            weights, edges = _REWRITES[first_name](weights, edges)
            return (weights, edges), self._ack()
        if isinstance(action, tuple) and action[0] == "bracket_compose":
            weights, edges = state
            first_name = action[1][1][0]
            weights, edges = _REWRITES[first_name](weights, edges)
            return (weights, edges), self._ack()
        return super().step_C(state, action, nest_context)

    @staticmethod
    def _ack():
        from bridge_interface import Outcome

        return Outcome.deterministic("ack")


if __name__ == "__main__":
    c = AblationFlattenedExecCandidate()
    s = c.initial_state("root_00")
    s, _ = c.step_C(s, ("ordered_compose", ("H0", "CNOT01")))
    _s, outcome = c.step_C(s, "read_outcome_z")
    print("ablation root_00 -> H0,CNOT01(first only) -> read_outcome_z:", outcome)
