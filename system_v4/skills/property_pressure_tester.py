"""
property_pressure_tester.py

Generate structured perturbations against structural invariants
and produce witnesses.

Design doc: §Property-Based Testing — invariant pressure over
structured state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Witness, WitnessKind, BoundaryTag, StepEvent, utc_iso,
    LoopScale,
)

Invariant = Callable[[RuntimeState], bool]
Perturbation = Callable[[RuntimeState], RuntimeState]


@dataclass
class PressureResult:
    """Outcome of a property-pressure pass."""
    seed_hash: str
    total: int
    passed: int
    failed: int
    witnesses: list[Witness] = field(default_factory=list)


def property_pressure(
    seed: RuntimeState,
    perturbations: list[Perturbation],
    invariant: Invariant,
    invariant_name: str = "unnamed",
) -> PressureResult:
    """Apply each perturbation and check the invariant.  Emit witnesses."""
    witnesses: list[Witness] = []
    passed = 0
    failed = 0

    for i, p in enumerate(perturbations):
        try:
            next_state = p(seed)
        except Exception as exc:
            witnesses.append(Witness(
                kind=WitnessKind.NEGATIVE, passed=False,
                violations=[f"PERTURBATION_{i}_EXCEPTION:{exc}"],
                touched_boundaries=list(seed.boundaries),
                trace=[],
            ))
            failed += 1
            continue

        ok = invariant(next_state)
        w = Witness(
            kind=WitnessKind.POSITIVE if ok else WitnessKind.NEGATIVE,
            passed=ok,
            violations=[] if ok else [f"INVARIANT_BREAK_{invariant_name}_{i}"],
            touched_boundaries=list(next_state.boundaries),
            trace=[StepEvent(
                at=utc_iso(), op=f"perturbation_{i}",
                before_hash=seed.hash(), after_hash=next_state.hash(),
            )],
        )
        witnesses.append(w)
        if ok:
            passed += 1
        else:
            failed += 1

    return PressureResult(
        seed_hash=seed.hash(),
        total=len(perturbations),
        passed=passed, failed=failed,
        witnesses=witnesses,
    )


# ── Standard perturbation families ───────────────────────────────────────

def standard_perturbations() -> list[Perturbation]:
    """Perturbations that exercise phase, boundaries, regions, and scale."""
    return [
        # Phase jumps
        lambda s: s.advance_phase(1),
        lambda s: s.advance_phase(5),
        lambda s: s.advance_phase(s.phase_period - 1),
        # Boundary additions
        lambda s: s.add_boundary(BoundaryTag.BLOCKED),
        lambda s: s.add_boundary(BoundaryTag.DEGENERATE),
        lambda s: s.add_boundary(BoundaryTag.FRONTIER),
        lambda s: s.add_boundary(BoundaryTag.UNSTABLE),
        # Region mutation
        lambda s: RuntimeState(**{**s.__dict__, "region": f"{s.region}:mutant"}),
        lambda s: RuntimeState(**{**s.__dict__, "region": ""}),
        # Loop scale changes
        lambda s: RuntimeState(**{**s.__dict__, "loop_scale": LoopScale.MESO}),
        lambda s: RuntimeState(**{**s.__dict__, "loop_scale": LoopScale.MACRO}),
        # Combined
        lambda s: s.advance_phase(3).add_boundary(BoundaryTag.UNSTABLE),
    ]


def standard_invariants() -> dict[str, Invariant]:
    """Invariants that should hold across perturbations."""
    return {
        "region_nonempty": lambda s: bool(s.region),
        "phase_period_positive": lambda s: s.phase_period > 0,
        "no_blocked_admissible": lambda s: not (
            BoundaryTag.BLOCKED in s.boundaries
            and BoundaryTag.ADMISSIBLE in s.boundaries
        ),
    }


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    s = RuntimeState(region="test", phase_index=0, phase_period=8)

    # Phase period should survive all perturbations
    r = property_pressure(
        s, standard_perturbations(),
        lambda st: st.phase_period > 0,
        invariant_name="phase_positive",
    )
    assert r.total == 12
    assert r.passed >= 11  # region="" might still have positive phase period

    # Region nonempty will fail on the empty-region perturbation
    r2 = property_pressure(
        s, standard_perturbations(),
        lambda st: bool(st.region),
        invariant_name="region_nonempty",
    )
    assert r2.failed >= 1

    print(f"PASS: property_pressure_tester self-test ({r.total} perturbations)")
