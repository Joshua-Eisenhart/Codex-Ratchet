"""
model_checker.py

Bounded DFS path exploration over structured state with guard
transitions.  Extracts explicit failure traces (counterexamples).

Design doc: §Model Checking — witness path extraction over
structured state and transforms.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Transform, FnTransform, Witness, WitnessKind,
    BoundaryTag, StepEvent, utc_iso, guard_transition,
)


@dataclass
class ExplorationResult:
    """Outcome of a model-checking exploration."""
    states_visited: int
    counterexamples: list[Witness] = field(default_factory=list)
    max_depth_reached: int = 0


def explore(
    seed: RuntimeState,
    ops: list[Transform],
    depth: int = 4,
    budget: int = 200,
) -> ExplorationResult:
    """Bounded DFS exploration.  Returns counterexamples found."""
    counterexamples: list[Witness] = []
    visited = 0
    max_depth = 0
    seen: set[str] = set()

    def dfs(state: RuntimeState, trace: list[StepEvent], d: int):
        nonlocal visited, max_depth, budget

        if d == 0 or budget <= 0:
            return

        state_key = state.hash()
        if state_key in seen:
            return
        seen.add(state_key)

        for op in ops:
            budget -= 1
            if budget <= 0:
                return

            try:
                next_state = op.apply(state)
            except Exception:
                continue

            visited += 1
            current_depth = len(trace) + 1
            if current_depth > max_depth:
                max_depth = current_depth

            event = StepEvent(
                at=utc_iso(), op=op.transform_id,
                before_hash=state.hash(), after_hash=next_state.hash(),
            )

            violations = guard_transition(state, next_state)
            if violations:
                counterexamples.append(Witness(
                    kind=WitnessKind.COUNTEREXAMPLE,
                    passed=False,
                    violations=violations,
                    touched_boundaries=list(next_state.boundaries),
                    trace=[*trace, event],
                ))
                continue

            dfs(next_state, [*trace, event], d - 1)

    dfs(seed, [], depth)

    return ExplorationResult(
        states_visited=visited,
        counterexamples=counterexamples,
        max_depth_reached=max_depth,
    )


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed = RuntimeState(region="start", phase_index=0, phase_period=8)

    ops = [
        FnTransform("advance", lambda s: s.advance_phase(1)),
        FnTransform("add_blocked", lambda s: s.add_boundary(BoundaryTag.BLOCKED)),
        FnTransform("cross_region", lambda s: RuntimeState(
            **{**s.__dict__, "region": "other"})),
    ]

    r = explore(seed, ops, depth=3, budget=100)
    assert r.states_visited > 0

    # Should find counterexample: add_blocked then cross_region
    assert len(r.counterexamples) >= 1
    cex = r.counterexamples[0]
    assert "ILLEGAL_BOUNDARY_CROSSING" in cex.violations

    print(f"PASS: model_checker self-test ({r.states_visited} states, "
          f"{len(r.counterexamples)} counterexamples, depth={r.max_depth_reached})")
