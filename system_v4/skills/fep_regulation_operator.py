"""
fep_regulation_operator.py

Free Energy Principle / Active Inference loop:
  predict → observe → mismatch → regulate → repeat

Design doc: §FEP/Active Inference — adaptive correction over
structured state.  Also incorporates §Bayesian Updating for the
evidence-driven revision sub-step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Observation, BoundaryTag, StepEvent, utc_iso,
)


@dataclass
class RegulationStep:
    """One predict → observe → regulate cycle."""
    step_index: int
    predicted: Observation
    actual: Observation
    divergence: int
    regulated: bool


@dataclass
class RegulationResult:
    """Outcome of an FEP regulation pass."""
    steps: list[RegulationStep] = field(default_factory=list)
    total_divergence: int = 0
    corrections_applied: int = 0


def predict(state: RuntimeState) -> Observation:
    """Generate a prediction observation from current state."""
    return Observation(
        probe_id="predict",
        features={
            "region": state.region,
            "phase_band": state.phase_band(8),
            "boundary_count": len(state.boundaries),
            "loop_scale": state.loop_scale.value,
        },
    )


def divergence(pred: Observation, actual: Observation) -> int:
    """Count feature-level mismatches between prediction and observation."""
    keys = set(pred.features) | set(actual.features)
    return sum(1 for k in keys if pred.features.get(k) != actual.features.get(k))


def mismatch_score(expected: Observation, observed: Observation) -> float:
    """Normalized mismatch (0.0–1.0) from §Bayesian Updating."""
    keys = list(set(expected.features) | set(observed.features))
    if not keys:
        return 0.0
    mismatches = sum(1 for k in keys
                     if expected.features.get(k) != observed.features.get(k))
    return mismatches / len(keys)


def regulate(state: RuntimeState, actual: Observation) -> RuntimeState:
    """Apply regulation: if divergent, correct state."""
    pred = predict(state)
    d = divergence(pred, actual)

    if d == 0:
        return state

    # Correct: advance phase, mark unstable
    corrected = state.advance_phase(2)
    corrected = corrected.add_boundary(BoundaryTag.UNSTABLE)
    d2 = corrected.__dict__.copy()
    d2["region"] = f"{state.region}:corrected"
    return RuntimeState(**d2)


def revise_state(
    state: RuntimeState,
    observed: Observation,
    threshold: float = 0.7,
) -> RuntimeState:
    """Bayesian-style state revision based on mismatch score."""
    pred = predict(state)
    mm = mismatch_score(pred, observed)

    if mm > threshold:
        corrected = state.advance_phase(1).add_boundary(BoundaryTag.FRONTIER)
        d = corrected.__dict__.copy()
        d["region"] = f"{state.region}:updated"
        return RuntimeState(**d)

    # Low mismatch: remove frontier if present
    d = state.__dict__.copy()
    d["boundaries"] = [b for b in state.boundaries if b != BoundaryTag.FRONTIER]
    return RuntimeState(**d)


def regulation_loop(
    state: RuntimeState,
    observe_fn: Callable[[RuntimeState], Observation],
    max_steps: int = 5,
) -> tuple[RuntimeState, RegulationResult]:
    """Multi-step regulation loop."""
    steps: list[RegulationStep] = []
    current = state
    total_div = 0
    corrections = 0

    for i in range(max_steps):
        pred = predict(current)
        actual = observe_fn(current)
        d = divergence(pred, actual)
        total_div += d

        regulated = d > 0
        if regulated:
            current = regulate(current, actual)
            corrections += 1

        steps.append(RegulationStep(
            step_index=i, predicted=pred, actual=actual,
            divergence=d, regulated=regulated,
        ))

        if d == 0:
            break

    return current, RegulationResult(
        steps=steps, total_divergence=total_div,
        corrections_applied=corrections,
    )


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed = RuntimeState(region="test", phase_index=0, phase_period=8)

    # Observation that disagrees with prediction
    divergent = Observation(
        probe_id="actual",
        features={"region": "other", "phase_band": 5,
                  "boundary_count": 3, "loop_scale": "macro"},
    )

    s2 = regulate(seed, divergent)
    assert "corrected" in s2.region
    assert BoundaryTag.UNSTABLE in s2.boundaries

    # Matching observation — no correction
    matching = predict(seed)
    s3 = regulate(seed, matching)
    assert s3.region == seed.region

    # Regulation loop
    correction_count = [0]
    def observe_fn(s: RuntimeState) -> Observation:
        correction_count[0] += 1
        if correction_count[0] <= 2:
            return divergent
        return predict(s)  # converges

    final, result = regulation_loop(seed, observe_fn, max_steps=5)
    assert result.corrections_applied >= 1
    assert len(result.steps) >= 2

    # Bayesian revision
    high_mm_obs = Observation(
        probe_id="bayesian",
        features={"region": "xxx", "phase_band": 99,
                  "boundary_count": 10, "loop_scale": "???"},
    )
    revised = revise_state(seed, high_mm_obs, threshold=0.5)
    assert "updated" in revised.region

    print(f"PASS: fep_regulation_operator self-test "
          f"({result.corrections_applied} corrections in {len(result.steps)} steps)")
