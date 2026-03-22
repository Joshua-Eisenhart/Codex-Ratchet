"""
differential_tester.py

Run multiple variants on the same surface and compare outputs.
Disagreement = structured signal.

Design doc: §Differential Testing — probe-relative comparison
of final states.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Transform, FnTransform, Witness, WitnessKind,
    StepEvent, utc_iso, transform_sequence, equivalent_under, Probe,
    Observation,
)
from system_v4.skills.z3_cegis_refiner import Candidate


@dataclass
class Disagreement:
    """A pair of variants that produce different observations."""
    left_id: str
    right_id: str
    differing_probes: list[str] = field(default_factory=list)


@dataclass
class DiffTestResult:
    """Outcome of a differential test."""
    variant_count: int
    disagreements: list[Disagreement] = field(default_factory=list)
    all_agree: bool = True


def differential_test(
    seed: RuntimeState,
    variants: list[Candidate],
    probes: list[Probe],
) -> DiffTestResult:
    """Fan-out variants, compare outputs under probes."""
    outputs = []
    for v in variants:
        end = transform_sequence(seed, v.transforms)
        outputs.append((v.candidate_id, end))

    disagreements: list[Disagreement] = []
    for i, (id_a, state_a) in enumerate(outputs):
        for j, (id_b, state_b) in enumerate(outputs[i + 1:], i + 1):
            if not equivalent_under(state_a, state_b, probes):
                diff_probes = []
                for p in probes:
                    oa = p.observe(state_a)
                    ob = p.observe(state_b)
                    if oa.features != ob.features:
                        diff_probes.append(p.probe_id)
                disagreements.append(Disagreement(
                    left_id=id_a, right_id=id_b,
                    differing_probes=diff_probes,
                ))

    return DiffTestResult(
        variant_count=len(variants),
        disagreements=disagreements,
        all_agree=len(disagreements) == 0,
    )


# ── Built-in probes ─────────────────────────────────────────────────────

@dataclass
class RegionProbe:
    probe_id: str = "region"
    def observe(self, state: RuntimeState) -> Observation:
        return Observation(probe_id=self.probe_id, features={"region": state.region})


@dataclass
class PhaseProbe:
    probe_id: str = "phase"
    def observe(self, state: RuntimeState) -> Observation:
        return Observation(probe_id=self.probe_id, features={
            "phase_index": state.phase_index,
            "phase_band": state.phase_band(8),
        })


@dataclass
class BoundaryProbe:
    probe_id: str = "boundary"
    def observe(self, state: RuntimeState) -> Observation:
        return Observation(probe_id=self.probe_id, features={
            "boundary_count": len(state.boundaries),
            "boundaries": ",".join(sorted(b.value for b in state.boundaries)),
        })


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from system_v4.skills.runtime_state_kernel import BoundaryTag

    seed = RuntimeState(region="test", phase_index=0, phase_period=8)

    v1 = Candidate("v1", "test", [FnTransform("a1", lambda s: s.advance_phase(1))])
    v2 = Candidate("v2", "test", [FnTransform("a3", lambda s: s.advance_phase(3))])
    v3 = Candidate("v3", "test", [FnTransform("a1_dup", lambda s: s.advance_phase(1))])

    probes = [RegionProbe(), PhaseProbe(), BoundaryProbe()]
    r = differential_test(seed, [v1, v2, v3], probes)

    assert r.variant_count == 3
    # v1 and v3 agree, but v2 disagrees with both
    assert len(r.disagreements) == 2
    assert not r.all_agree

    # All same
    r2 = differential_test(seed, [v1, v3], probes)
    assert r2.all_agree

    print(f"PASS: differential_tester self-test ({len(r.disagreements)} disagreements)")
