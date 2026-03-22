"""
bounded_improve_operator.py

Karpathy-style bounded improvement loop:
  mutate → evaluate → keep/discard → repeat

Design doc: §Karpathy Design Philosophy + §autoresearch.
Small core, visible loop, bounded mutation, explicit evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, Generic

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Witness, WitnessKind, StepEvent, utc_iso,
)

T = TypeVar("T")


@dataclass
class MutationDecision:
    """Record of a single mutation decision."""
    round_index: int
    kept: bool
    score_before: float
    score_after: float
    rationale: str = ""


@dataclass
class BoundedImproveResult:
    """Outcome of a bounded improvement loop."""
    rounds: int
    decisions: list[MutationDecision] = field(default_factory=list)
    final_score: float = 0.0
    improved: bool = False


def bounded_improve(
    artifact: RuntimeState,
    mutate: Callable[[RuntimeState], RuntimeState],
    eval_fn: Callable[[RuntimeState], float],
    rounds: int = 5,
) -> tuple[RuntimeState, BoundedImproveResult]:
    """Karpathy-style bounded improvement.  Returns (best, result)."""
    current = artifact
    current_score = eval_fn(current)
    decisions: list[MutationDecision] = []

    for i in range(rounds):
        try:
            candidate = mutate(current)
        except Exception:
            decisions.append(MutationDecision(
                round_index=i, kept=False,
                score_before=current_score, score_after=current_score,
                rationale="mutation_exception",
            ))
            continue

        score = eval_fn(candidate)
        if score > current_score:
            decisions.append(MutationDecision(
                round_index=i, kept=True,
                score_before=current_score, score_after=score,
                rationale="improvement",
            ))
            current = candidate
            current_score = score
        else:
            decisions.append(MutationDecision(
                round_index=i, kept=False,
                score_before=current_score, score_after=score,
                rationale="no_improvement",
            ))

    return current, BoundedImproveResult(
        rounds=rounds,
        decisions=decisions,
        final_score=current_score,
        improved=current_score > eval_fn(artifact),
    )


def mutate_and_evaluate(
    current: RuntimeState,
    mutate: Callable[[RuntimeState], RuntimeState],
    score_fn: Callable[[RuntimeState], float],
) -> MutationDecision:
    """Single mutation + evaluation step from §autoresearch."""
    after = mutate(current)
    sb = score_fn(current)
    sa = score_fn(after)
    return MutationDecision(
        round_index=0, kept=sa > sb,
        score_before=sb, score_after=sa,
        rationale="bounded_mutation",
    )


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from system_v4.skills.runtime_state_kernel import BoundaryTag

    seed = RuntimeState(region="test", phase_index=0, phase_period=8)

    # Each mutation advances phase; score = phase_index
    best, result = bounded_improve(
        seed,
        mutate=lambda s: s.advance_phase(1),
        eval_fn=lambda s: float(s.phase_index),
        rounds=5,
    )
    assert result.improved
    assert best.phase_index > seed.phase_index
    assert result.final_score > 0

    # No improvement possible
    perfect = RuntimeState(region="max", phase_index=7, phase_period=8)
    _, r2 = bounded_improve(
        perfect,
        mutate=lambda s: s.advance_phase(1),  # wraps to 0
        eval_fn=lambda s: float(s.phase_index),
        rounds=3,
    )
    assert not r2.improved

    print(f"PASS: bounded_improve_operator self-test (score {seed.phase_index}→{best.phase_index})")
