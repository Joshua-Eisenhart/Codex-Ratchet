"""
runtime_state_kernel.py

Shared nonclassical runtime kernel.  Every other operator skill imports its
core types from here.  Derived from the design doc
`core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
§Core Types (lines 376–472).

Design commitments:
  1. state is structured  (RuntimeState)
  2. transform order matters  (compose is left ∘ right)
  3. equivalence is probe-relative  (equivalent_under)
  4. evidence is explicit and replayable  (Witness / StepEvent)
  5. intent is first-class  (WitnessKind.INTENT)
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Protocol


# ── Enums ────────────────────────────────────────────────────────────────

class LoopScale(str, Enum):
    MICRO = "micro"
    MESO  = "meso"
    MACRO = "macro"


class BoundaryTag(str, Enum):
    STABLE      = "stable"
    FRONTIER    = "frontier"
    BLOCKED     = "blocked"
    UNSTABLE    = "unstable"
    DEGENERATE  = "degenerate"
    ADMISSIBLE  = "admissible"


class WitnessKind(str, Enum):
    POSITIVE       = "positive"
    NEGATIVE       = "negative"
    COUNTEREXAMPLE = "counterexample"
    INTENT         = "intent"           # maker / system intent — first-class
    CONTEXT        = "context"          # persistent context preservation


# ── Core Types ───────────────────────────────────────────────────────────

@dataclass
class RuntimeState:
    """Structured nonclassical state carried through the runtime."""
    region: str
    phase_index: int       = 0
    phase_period: int      = 8
    loop_scale: LoopScale  = LoopScale.MICRO
    boundaries: list[BoundaryTag] = field(default_factory=list)
    invariants: list[str]  = field(default_factory=list)
    dof: dict[str, Any]    = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    # ── helpers ──────────────────────────────────────────────────
    def hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    def normalized_phase(self) -> int:
        return ((self.phase_index % self.phase_period)
                + self.phase_period) % self.phase_period

    def phase_band(self, bands: int = 8) -> int:
        if self.phase_period == 0:
            return 0
        return int((self.phase_index / self.phase_period) * bands)

    def has_boundary(self, tag: BoundaryTag) -> bool:
        return tag in self.boundaries

    def add_boundary(self, tag: BoundaryTag) -> "RuntimeState":
        if tag not in self.boundaries:
            return RuntimeState(**{**asdict(self),
                                   "boundaries": [*self.boundaries, tag]})
        return self

    def advance_phase(self, steps: int = 1) -> "RuntimeState":
        d = asdict(self)
        d["phase_index"] = (
            (self.phase_index + steps) % self.phase_period
            + self.phase_period
        ) % self.phase_period
        return RuntimeState(**d)


@dataclass
class Observation:
    """Probe output: a named set of scalar features."""
    probe_id: str
    features: dict[str, Any] = field(default_factory=dict)


class Probe(Protocol):
    """Protocol for anything that can observe a RuntimeState."""
    probe_id: str
    def observe(self, state: RuntimeState) -> Observation: ...


@dataclass
class StepEvent:
    """Single entry in an append-only witness trace."""
    at: str
    op: str
    before_hash: str
    after_hash: str
    notes: list[str] = field(default_factory=list)


@dataclass
class Witness:
    """Explicit evidence record: positive, negative, counterexample, or intent.

    Intent witnesses are first-class: they capture the maker's goals,
    design decisions, constraints, and priorities.  They persist across
    sessions and are the highest-priority content for A2/A1 refinement.
    """
    kind: WitnessKind
    passed: bool
    violations: list[str]   = field(default_factory=list)
    touched_boundaries: list[BoundaryTag] = field(default_factory=list)
    trace: list[StepEvent]  = field(default_factory=list)


# ── Transform protocol ──────────────────────────────────────────────────

class Transform(Protocol):
    transform_id: str
    def apply(self, state: RuntimeState, input_data: Any = None) -> RuntimeState: ...


@dataclass
class FnTransform:
    """Concrete transform wrapping a plain function."""
    transform_id: str
    _fn: Callable[[RuntimeState], RuntimeState]

    def apply(self, state: RuntimeState, input_data: Any = None) -> RuntimeState:
        return self._fn(state)


# ── Composition ──────────────────────────────────────────────────────────

def compose(left: Transform, right: Transform) -> FnTransform:
    """Ordered composition: left ∘ right.  Apply right first, then left."""
    return FnTransform(
        transform_id=f"{left.transform_id}∘{right.transform_id}",
        _fn=lambda s: left.apply(right.apply(s)),
    )


def transform_sequence(state: RuntimeState, transforms: list[Transform]) -> RuntimeState:
    """Apply transforms in order (left to right)."""
    for t in transforms:
        state = t.apply(state)
    return state


# ── Probe-relative equivalence ───────────────────────────────────────────

def equivalent_under(a: RuntimeState, b: RuntimeState, probes: list[Probe]) -> bool:
    """Two states are equivalent iff all probes produce identical observations."""
    for p in probes:
        oa = p.observe(a)
        ob = p.observe(b)
        keys = sorted(set(oa.features) | set(ob.features))
        if any(oa.features.get(k) != ob.features.get(k) for k in keys):
            return False
    return True


def compare_orders(
    state: RuntimeState, a: Transform, b: Transform, probes: list[Probe]
) -> bool:
    """Check whether A∘B == B∘A under given probes (detects non-commutation)."""
    ab = compose(a, b).apply(state)
    ba = compose(b, a).apply(state)
    return equivalent_under(ab, ba, probes)


# ── Guard logic ──────────────────────────────────────────────────────────

def guard_transition(before: RuntimeState, after: RuntimeState) -> list[str]:
    """Return violation reasons if the transition is illegal."""
    violations: list[str] = []
    if after.phase_period <= 0:
        violations.append("BAD_PHASE_PERIOD")
    if (BoundaryTag.BLOCKED in before.boundaries
            and before.region != after.region):
        violations.append("ILLEGAL_BOUNDARY_CROSSING")
    return violations


# ── Phase / Loop-Scale helpers ───────────────────────────────────────────

LOOP_ESCALATION = {
    LoopScale.MICRO: LoopScale.MESO,
    LoopScale.MESO:  LoopScale.MACRO,
    LoopScale.MACRO: LoopScale.MACRO,
}

def should_escalate(state: RuntimeState) -> bool:
    return state.loop_scale == LoopScale.MICRO and state.phase_band(8) >= 6

def escalate_loop_scale(state: RuntimeState) -> RuntimeState:
    d = asdict(state)
    d["loop_scale"] = LOOP_ESCALATION[state.loop_scale]
    d["phase_index"] = 0
    if BoundaryTag.FRONTIER not in d["boundaries"]:
        d["boundaries"] = [*d["boundaries"], BoundaryTag.FRONTIER]
    return RuntimeState(**d)


# ── Utility ──────────────────────────────────────────────────────────────

def utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def make_step_event(op: str, before: RuntimeState, after: RuntimeState,
                    notes: list[str] | None = None) -> StepEvent:
    return StepEvent(
        at=utc_iso(), op=op,
        before_hash=before.hash(), after_hash=after.hash(),
        notes=notes or [],
    )


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    s = RuntimeState(region="test", phase_index=0, phase_period=8)
    assert s.hash(), "hash should be non-empty"
    assert s.normalized_phase() == 0
    assert s.phase_band(8) == 0

    s2 = s.advance_phase(3)
    assert s2.phase_index == 3
    assert s2.region == "test"

    s3 = s.add_boundary(BoundaryTag.FRONTIER)
    assert BoundaryTag.FRONTIER in s3.boundaries

    t1 = FnTransform("advance", lambda st: st.advance_phase(1))
    t2 = FnTransform("frontier", lambda st: st.add_boundary(BoundaryTag.FRONTIER))
    seq = transform_sequence(s, [t1, t2])
    assert seq.phase_index == 1
    assert BoundaryTag.FRONTIER in seq.boundaries

    comp = compose(t2, t1)
    res = comp.apply(s)
    assert res.phase_index == 1 and BoundaryTag.FRONTIER in res.boundaries

    violations = guard_transition(
        s.add_boundary(BoundaryTag.BLOCKED),
        RuntimeState(region="other"),
    )
    assert "ILLEGAL_BOUNDARY_CROSSING" in violations

    evt = make_step_event("test_op", s, s2)
    assert evt.op == "test_op"

    w = Witness(
        kind=WitnessKind.POSITIVE, passed=True,
        violations=[], touched_boundaries=[],
        trace=[evt],
    )
    assert w.passed

    print("PASS: runtime_state_kernel self-test")
"""
Skill registration metadata (for skill_registry_v1.json):
  skill_id: runtime-state-kernel
  skill_type: bridge
  applicable_trust_zones: [INDEX]
  capabilities: {is_phase_runner: false}
  source_path: system_v4/skills/runtime_state_kernel.py
  adapters: {shell: system_v4/skills/runtime_state_kernel.py}
"""
