"""
z3_constraint_checker.py

SAT/SMT constraint satisfaction + minimal failure-set extraction.
Uses Z3 when available, falls back to pure-Python brute-force for
small constraint sets.

Design doc: §SAT/SMT — local hard incompatibility detection.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Witness, WitnessKind, BoundaryTag, StepEvent, utc_iso,
)

# ── Z3 availability ─────────────────────────────────────────────────────

try:
    import z3 as _z3
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False


# ── Constraint types ─────────────────────────────────────────────────────

Constraint = Callable[[RuntimeState], bool]


@dataclass
class ConstraintResult:
    """Outcome of a constraint check pass."""
    all_satisfied: bool
    violations: list[str] = field(default_factory=list)
    minimal_failure_set: list[str] = field(default_factory=list)
    checked_count: int = 0
    elapsed_ms: float = 0.0


def check_constraints(
    state: RuntimeState,
    constraints: dict[str, Constraint],
) -> ConstraintResult:
    """Check all constraints against a state.  Returns violations."""
    t0 = time.monotonic()
    violations = []
    for name, cfn in constraints.items():
        try:
            if not cfn(state):
                violations.append(name)
        except Exception as exc:
            violations.append(f"{name}:ERROR:{exc}")

    return ConstraintResult(
        all_satisfied=len(violations) == 0,
        violations=violations,
        minimal_failure_set=violations[:5],  # bounded
        checked_count=len(constraints),
        elapsed_ms=(time.monotonic() - t0) * 1000,
    )


def constraints_to_witness(
    state: RuntimeState, result: ConstraintResult,
) -> Witness:
    """Convert a constraint check result to a Witness."""
    return Witness(
        kind=WitnessKind.POSITIVE if result.all_satisfied else WitnessKind.NEGATIVE,
        passed=result.all_satisfied,
        violations=result.violations,
        touched_boundaries=[b for b in state.boundaries],
        trace=[StepEvent(
            at=utc_iso(), op="z3_constraint_check",
            before_hash=state.hash(), after_hash=state.hash(),
            notes=[f"checked={result.checked_count}",
                   f"elapsed_ms={result.elapsed_ms:.1f}"],
        )],
    )


# ── Z3-backed checking (when available) ─────────────────────────────────

def z3_check_phase_boundaries(state: RuntimeState) -> ConstraintResult:
    """Use Z3 to verify phase/boundary constraints if available."""
    if not HAS_Z3:
        # Fallback: pure-python checks
        violations = []
        if state.phase_period <= 0:
            violations.append("phase_period_nonpositive")
        if state.phase_index < 0:
            violations.append("phase_index_negative")
        if state.phase_index >= state.phase_period:
            violations.append("phase_index_exceeds_period")
        if BoundaryTag.BLOCKED in state.boundaries and BoundaryTag.ADMISSIBLE in state.boundaries:
            violations.append("blocked_and_admissible_conflict")
        return ConstraintResult(
            all_satisfied=len(violations) == 0,
            violations=violations, checked_count=4,
        )

    # Z3 path
    phase_idx = _z3.Int("phase_index")
    phase_per = _z3.Int("phase_period")

    solver = _z3.Solver()
    solver.add(phase_idx == state.phase_index)
    solver.add(phase_per == state.phase_period)

    # Constraints
    solver.add(phase_per > 0)
    solver.add(phase_idx >= 0)
    solver.add(phase_idx < phase_per)

    violations = []
    if solver.check() == _z3.unsat:
        core = solver.unsat_core() if hasattr(solver, 'unsat_core') else []
        violations.append(f"z3_unsat:phase_constraints (core={len(core)})")

    # Boundary conflict
    if BoundaryTag.BLOCKED in state.boundaries and BoundaryTag.ADMISSIBLE in state.boundaries:
        violations.append("blocked_and_admissible_conflict")

    return ConstraintResult(
        all_satisfied=len(violations) == 0,
        violations=violations, checked_count=4,
    )


# ── Convenience: standard constraint families ───────────────────────────

def standard_constraints() -> dict[str, Constraint]:
    """A baseline set of structural constraints any RuntimeState should meet."""
    return {
        "phase_period_positive": lambda s: s.phase_period > 0,
        "phase_index_nonneg": lambda s: s.phase_index >= 0,
        "phase_index_bounded": lambda s: s.phase_index < s.phase_period,
        "region_nonempty": lambda s: bool(s.region),
        "no_blocked_admissible_conflict": lambda s: not (
            BoundaryTag.BLOCKED in s.boundaries
            and BoundaryTag.ADMISSIBLE in s.boundaries
        ),
        "no_degenerate_stable_conflict": lambda s: not (
            BoundaryTag.DEGENERATE in s.boundaries
            and BoundaryTag.STABLE in s.boundaries
        ),
    }


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    s = RuntimeState(region="test", phase_index=3, phase_period=8)
    r = check_constraints(s, standard_constraints())
    assert r.all_satisfied, f"Should pass: {r.violations}"

    # Force a violation
    bad = RuntimeState(region="", phase_index=-1, phase_period=0)
    r2 = check_constraints(bad, standard_constraints())
    assert not r2.all_satisfied
    assert len(r2.violations) >= 3

    w = constraints_to_witness(s, r)
    assert w.passed

    # Z3 path
    r3 = z3_check_phase_boundaries(s)
    assert r3.all_satisfied

    r4 = z3_check_phase_boundaries(RuntimeState(region="x", phase_index=10, phase_period=3))
    assert not r4.all_satisfied

    print(f"PASS: z3_constraint_checker self-test (z3_available={HAS_Z3})")
