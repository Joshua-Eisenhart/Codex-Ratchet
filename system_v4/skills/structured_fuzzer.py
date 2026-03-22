"""
structured_fuzzer.py

Structured adversarial perturbation over region, boundary, phase,
and transform inputs.

Design doc: §Fuzzing — fuzz regions, boundaries, phases to find
hidden assumptions and unstable neighborhoods.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Callable

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Witness, WitnessKind, BoundaryTag, StepEvent, utc_iso,
    LoopScale, guard_transition,
)


@dataclass
class FuzzResult:
    """Outcome of a structured fuzz pass."""
    seed_hash: str
    total_variants: int
    violations_found: int
    witnesses: list[Witness] = field(default_factory=list)


def fuzz_state(state: RuntimeState) -> list[RuntimeState]:
    """Generate structured mutants of a RuntimeState."""
    mutants: list[RuntimeState] = []
    d = state.__dict__.copy()

    # Phase jumps
    for delta in [1, 3, 5, -1, state.phase_period - 1]:
        mutants.append(state.advance_phase(delta))

    # Region mutations
    mutants.append(RuntimeState(**{**d, "region": f"{state.region}:mutant"}))
    mutants.append(RuntimeState(**{**d, "region": ""}))
    mutants.append(RuntimeState(**{**d, "region": state.region * 3}))

    # Boundary injections
    for tag in BoundaryTag:
        mutants.append(state.add_boundary(tag))

    # Combined: blocked + region change (should trigger guard)
    blocked = state.add_boundary(BoundaryTag.BLOCKED)
    mutants.append(RuntimeState(**{**blocked.__dict__, "region": "fuzz_target"}))

    # Loop scale changes
    for scale in LoopScale:
        mutants.append(RuntimeState(**{**d, "loop_scale": scale}))

    # Zero/negative phase period
    mutants.append(RuntimeState(**{**d, "phase_period": 0}))
    mutants.append(RuntimeState(**{**d, "phase_period": -1}))

    return mutants


def fuzz_and_check(
    seed: RuntimeState,
    check_fn: Callable[[RuntimeState, RuntimeState], list[str]] | None = None,
) -> FuzzResult:
    """Fuzz a seed state and collect violation witnesses."""
    if check_fn is None:
        check_fn = guard_transition

    mutants = fuzz_state(seed)
    witnesses: list[Witness] = []
    violations_found = 0

    for i, mutant in enumerate(mutants):
        violations = check_fn(seed, mutant)
        if violations:
            violations_found += 1
            witnesses.append(Witness(
                kind=WitnessKind.NEGATIVE,
                passed=False,
                violations=violations,
                touched_boundaries=list(mutant.boundaries),
                trace=[StepEvent(
                    at=utc_iso(), op=f"fuzz_{i}",
                    before_hash=seed.hash(), after_hash=mutant.hash(),
                )],
            ))

    return FuzzResult(
        seed_hash=seed.hash(),
        total_variants=len(mutants),
        violations_found=violations_found,
        witnesses=witnesses,
    )


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    s = RuntimeState(region="test", phase_index=0, phase_period=8)
    r = fuzz_and_check(s)

    assert r.total_variants >= 15
    # Should find at least the blocked+region-change violation
    assert r.violations_found >= 1
    assert len(r.witnesses) >= 1

    # With stricter check: reject any phase_period <= 0
    def strict_check(before: RuntimeState, after: RuntimeState) -> list[str]:
        v = guard_transition(before, after)
        if after.phase_period <= 0:
            v.append("BAD_PHASE_PERIOD")
        if not after.region:
            v.append("EMPTY_REGION")
        return v

    r2 = fuzz_and_check(s, strict_check)
    assert r2.violations_found >= 3  # blocked crossing + phase=0 + phase=-1 + empty region

    print(f"PASS: structured_fuzzer self-test ({r.total_variants} variants, {r.violations_found} violations)")
