"""
z3_cegis_refiner.py

Counter-Example Guided Inductive Synthesis (CEGIS) loop.
Candidate → check → counterexample → refine → retry.

Design doc: §CEGIS — structured learning from failure.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Transform, FnTransform, Witness, WitnessKind,
    BoundaryTag, StepEvent, utc_iso, transform_sequence, guard_transition,
)


@dataclass
class Candidate:
    """A proposed solution: a sequence of transforms + claimed invariants."""
    candidate_id: str
    family: str
    transforms: list[Transform]
    claimed_invariants: list[str] = field(default_factory=list)


@dataclass
class CEGISRound:
    """One CEGIS refinement round."""
    round_index: int
    candidate_id: str
    witness: Witness
    refined: bool = False


def check_candidate(
    seed: RuntimeState,
    candidate: Candidate,
) -> Witness:
    """Apply candidate transforms and check for degenerate end state."""
    end_state = transform_sequence(seed, candidate.transforms)
    violations = guard_transition(seed, end_state)
    if BoundaryTag.DEGENERATE in end_state.boundaries:
        violations.append("DEGENERATE_END_STATE")

    return Witness(
        kind=WitnessKind.COUNTEREXAMPLE if violations else WitnessKind.POSITIVE,
        passed=len(violations) == 0,
        violations=violations,
        touched_boundaries=list(end_state.boundaries),
        trace=[StepEvent(
            at=utc_iso(), op=f"cegis_check:{candidate.candidate_id}",
            before_hash=seed.hash(), after_hash=end_state.hash(),
        )],
    )


def cegis_loop(
    seed: RuntimeState,
    initial_candidate: Candidate,
    refine_fn: Callable[[Candidate, Witness], Candidate],
    max_rounds: int = 5,
) -> tuple[Candidate | None, list[CEGISRound]]:
    """Run the CEGIS loop.  Returns (winning candidate or None, history)."""
    history: list[CEGISRound] = []
    candidate = initial_candidate

    for i in range(max_rounds):
        witness = check_candidate(seed, candidate)
        rnd = CEGISRound(
            round_index=i,
            candidate_id=candidate.candidate_id,
            witness=witness,
        )

        if witness.passed:
            history.append(rnd)
            return candidate, history

        # Refine
        candidate = refine_fn(candidate, witness)
        rnd.refined = True
        history.append(rnd)

    return None, history


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed = RuntimeState(region="start", phase_index=0, phase_period=8)

    # Initial bad candidate: adds degenerate boundary
    bad_t = FnTransform("add_degen", lambda s: s.add_boundary(BoundaryTag.DEGENERATE))
    good_t = FnTransform("advance", lambda s: s.advance_phase(1))

    initial = Candidate(
        candidate_id="v0", family="test",
        transforms=[bad_t],
        claimed_invariants=["no_degenerate"],
    )

    def refine(c: Candidate, w: Witness) -> Candidate:
        """Replace degenerate transform with advance."""
        return Candidate(
            candidate_id=f"v{int(c.candidate_id[1:]) + 1}",
            family=c.family,
            transforms=[good_t],
            claimed_invariants=c.claimed_invariants,
        )

    winner, history = cegis_loop(seed, initial, refine, max_rounds=3)
    assert winner is not None
    assert winner.candidate_id == "v1"
    assert len(history) == 2
    assert not history[0].witness.passed  # first was bad
    assert history[1].witness.passed      # second was good

    print("PASS: z3_cegis_refiner self-test")
