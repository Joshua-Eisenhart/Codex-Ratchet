"""
runtime_state.py — Nonclassical Runtime State Model

Per the nonclassical runtime design doc, this module provides the shared
kernel types that all operators (B, SIM, A1, graveyard) work over.

Two root constraints:
  1. Finitude — bounded state, bounded iteration, pruned search
  2. Non-commutation — transform order matters, A∘B ≠ B∘A

Core types:
  RuntimeState — region, phase, loop scale, boundaries, invariants, dof
  Probe        — observe structured state, emit Observation
  Transform    — ordered state transition
  Witness      — positive/negative/counterexample evidence trace
  StepEvent    — append-only record of a single state transition

Key commitments:
  1. State is structured (not flat)
  2. Transform order matters (ordered composition)
  3. Equivalence is probe-relative (not primitive equality)
  4. Evidence is explicit and replayable (witness traces)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set


# ═══════════════════════════════════════════════════════════
# Loop Scale & Boundary Tags
# ═══════════════════════════════════════════════════════════

LOOP_SCALES = ("micro", "meso", "macro")

BOUNDARY_TAGS = (
    "stable",       # no active pressure
    "frontier",     # at the edge of known structure
    "blocked",      # cannot proceed without intervention
    "unstable",     # recent evidence contradicts expectations
    "degenerate",   # collapsed into trivial/uninformative state
    "admissible",   # meets all guards for promotion
)


# ═══════════════════════════════════════════════════════════
# RuntimeState
# ═══════════════════════════════════════════════════════════

@dataclass
class RuntimeState:
    """
    Structured runtime state per the nonclassical design doc.

    This is NOT flat key-value state. It encodes:
      - region: location in structured space
      - phase_index / phase_period: local phase position
      - loop_scale: micro/meso/macro
      - boundaries: active boundary relations
      - invariants: currently surviving structure
      - dof: active degrees of freedom
      - context: structured local context
    """
    region: str = "INIT"
    phase_index: int = 0
    phase_period: int = 8
    loop_scale: str = "micro"           # micro | meso | macro
    boundaries: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    dof: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def normalized_phase(self) -> int:
        """Phase mod period, always in [0, period)."""
        return ((self.phase_index % self.phase_period) +
                self.phase_period) % self.phase_period

    def phase_band(self, bands: int = 8) -> int:
        """Discretize phase into bands."""
        if self.phase_period == 0:
            return 0
        return int((self.phase_index / self.phase_period) * bands)

    def state_hash(self) -> str:
        """SHA256 of canonical JSON encoding."""
        canonical = json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'RuntimeState':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ═══════════════════════════════════════════════════════════
# Observation & Probe
# ═══════════════════════════════════════════════════════════

@dataclass
class Observation:
    """Result of a probe observing runtime state."""
    probe_id: str
    features: Dict[str, Any] = field(default_factory=dict)


class Probe:
    """
    A probe observes structured state and emits an Observation.

    Probes define the equivalence surface: two states are equivalent
    if and only if ALL probes produce identical observations.
    """
    def __init__(self, probe_id: str, observe_fn=None):
        self.id = probe_id
        self._observe_fn = observe_fn

    def observe(self, state: RuntimeState) -> Observation:
        if self._observe_fn:
            features = self._observe_fn(state)
        else:
            # Default: observe region, phase band, boundary class
            features = {
                "region": state.region,
                "phase_band": state.phase_band(),
                "boundary_class": _boundary_class(state),
                "loop_scale": state.loop_scale,
            }
        return Observation(probe_id=self.id, features=features)


def _boundary_class(state: RuntimeState) -> str:
    """Coarse boundary classification."""
    if "blocked" in state.boundaries:
        return "blocked"
    if "frontier" in state.boundaries:
        return "frontier"
    if "unstable" in state.boundaries:
        return "unstable"
    return "stable"


# ═══════════════════════════════════════════════════════════
# Probe-Relative Equivalence
# ═══════════════════════════════════════════════════════════

def equivalent_under(a: RuntimeState, b: RuntimeState,
                     probes: List[Probe]) -> bool:
    """Two states are equivalent iff all probes see the same features."""
    for p in probes:
        oa = p.observe(a)
        ob = p.observe(b)
        if oa.features != ob.features:
            return False
    return True


def distinguishability(a: RuntimeState, b: RuntimeState,
                       probes: List[Probe]) -> int:
    """Count how many probes distinguish two states."""
    diff = 0
    for p in probes:
        oa = p.observe(a)
        ob = p.observe(b)
        if oa.features != ob.features:
            diff += 1
    return diff


# ═══════════════════════════════════════════════════════════
# Transform (ordered state transition)
# ═══════════════════════════════════════════════════════════

class Transform:
    """
    An ordered transform on RuntimeState.

    Composition is NOT commutative: compose(A, B) ≠ compose(B, A)
    """
    def __init__(self, transform_id: str, apply_fn=None):
        self.id = transform_id
        self._apply_fn = apply_fn

    def apply(self, state: RuntimeState) -> RuntimeState:
        if self._apply_fn:
            return self._apply_fn(state)
        return state    # identity if no fn


def compose(left: Transform, right: Transform) -> Transform:
    """Ordered composition: left ∘ right. Applies right first, then left."""
    def composed_fn(state: RuntimeState) -> RuntimeState:
        intermediate = right.apply(state)
        return left.apply(intermediate)
    return Transform(
        transform_id=f"{left.id}∘{right.id}",
        apply_fn=composed_fn,
    )


def compare_orders(state: RuntimeState,
                   a: Transform, b: Transform,
                   probes: List[Probe]) -> bool:
    """Check if A∘B and B∘A produce equivalent states under probes."""
    ab = compose(a, b).apply(state)
    ba = compose(b, a).apply(state)
    return equivalent_under(ab, ba, probes)


# ═══════════════════════════════════════════════════════════
# StepEvent (append-only trace element)
# ═══════════════════════════════════════════════════════════

@dataclass
class StepEvent:
    """Single transition in an append-only execution trace."""
    timestamp_utc: str
    operator_id: str
    before_hash: str
    after_hash: str
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════
# Witness (evidence trace)
# ═══════════════════════════════════════════════════════════

@dataclass
class Witness:
    """
    Evidence record: positive, negative, or counterexample.

    Per the doc: "Evidence is explicit and replayable."
    Every witness has a trace of StepEvents that produced it.
    """
    kind: str                    # "positive" | "negative" | "counterexample"
    passed: bool
    target_id: str = ""
    sim_id: str = ""
    violations: List[str] = field(default_factory=list)
    touched_boundaries: List[str] = field(default_factory=list)
    trace: List[StepEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ═══════════════════════════════════════════════════════════
# Phase / Loop-Scale Operations
# ═══════════════════════════════════════════════════════════

def advance_phase(state: RuntimeState, steps: int = 1) -> RuntimeState:
    """Advance local phase by `steps`."""
    new_index = ((state.phase_index + steps) % state.phase_period +
                 state.phase_period) % state.phase_period
    return RuntimeState(
        region=state.region,
        phase_index=new_index,
        phase_period=state.phase_period,
        loop_scale=state.loop_scale,
        boundaries=list(state.boundaries),
        invariants=list(state.invariants),
        dof=dict(state.dof),
        context=dict(state.context),
    )


SCALE_ORDER = {"micro": 0, "meso": 1, "macro": 2}
SCALE_NEXT = {"micro": "meso", "meso": "macro", "macro": "macro"}
SCALE_PREV = {"micro": "micro", "meso": "micro", "macro": "meso"}


def escalate_scale(state: RuntimeState) -> RuntimeState:
    """Move to next loop scale, reset phase."""
    return RuntimeState(
        region=state.region,
        phase_index=0,
        phase_period=state.phase_period,
        loop_scale=SCALE_NEXT.get(state.loop_scale, "macro"),
        boundaries=list(set(state.boundaries + ["frontier"])),
        invariants=list(state.invariants),
        dof=dict(state.dof),
        context=dict(state.context),
    )


def should_escalate(state: RuntimeState) -> bool:
    """Escalate if micro loop reaches high phase band."""
    return state.loop_scale == "micro" and state.phase_band() >= 6


# ═══════════════════════════════════════════════════════════
# Coarse State (Abstract Interpretation pre-filter)
# ═══════════════════════════════════════════════════════════

@dataclass
class CoarseState:
    """
    Coarse-grained abstract state for cheap pre-filtering.
    Preserves region, phase band, and boundary class.
    """
    region: str
    phase_band: int
    boundary_class: str     # stable | frontier | blocked

    @classmethod
    def from_runtime(cls, state: RuntimeState,
                     bands: int = 4) -> 'CoarseState':
        return cls(
            region=state.region,
            phase_band=state.phase_band(bands),
            boundary_class=_boundary_class(state),
        )


def coarse_equivalent(a: CoarseState, b: CoarseState) -> bool:
    """Two coarse states are equivalent if all fields match."""
    return (a.region == b.region and
            a.phase_band == b.phase_band and
            a.boundary_class == b.boundary_class)


# ═══════════════════════════════════════════════════════════
# Guard Transitions
# ═══════════════════════════════════════════════════════════

def guard_transition(before: RuntimeState,
                     after: RuntimeState) -> List[str]:
    """Check for illegal state transitions. Returns violation list."""
    violations = []

    # Cannot cross regions if blocked
    if "blocked" in before.boundaries and before.region != after.region:
        violations.append("ILLEGAL_BOUNDARY_CROSSING")

    # Phase period must stay positive
    if after.phase_period <= 0:
        violations.append("BAD_PHASE_PERIOD")

    # Cannot lose all invariants in one step
    if before.invariants and not after.invariants:
        violations.append("INVARIANT_WIPEOUT")

    # Degenerate transitions
    if "degenerate" in after.boundaries and "degenerate" not in before.boundaries:
        # New degeneracy — mark but don't block
        pass

    return violations


# ═══════════════════════════════════════════════════════════
# Standard Probes (built-in probe library)
# ═══════════════════════════════════════════════════════════

# Structural probe: region + phase + boundaries
STRUCTURAL_PROBE = Probe("STRUCTURAL", lambda s: {
    "region": s.region,
    "phase_band": s.phase_band(),
    "boundary_class": _boundary_class(s),
    "loop_scale": s.loop_scale,
    "invariant_count": len(s.invariants),
})

# Token probe: dof keys (what degrees of freedom are active)
TOKEN_PROBE = Probe("TOKEN", lambda s: {
    "dof_keys": sorted(s.dof.keys()) if s.dof else [],
    "context_keys": sorted(s.context.keys()) if s.context else [],
})

# Phase probe: precise phase info
PHASE_PROBE = Probe("PHASE", lambda s: {
    "phase_index": s.normalized_phase(),
    "phase_period": s.phase_period,
    "loop_scale": s.loop_scale,
})

# Boundary probe: full boundary set
BOUNDARY_PROBE = Probe("BOUNDARY", lambda s: {
    "boundaries": sorted(s.boundaries),
    "has_frontier": "frontier" in s.boundaries,
    "has_blocked": "blocked" in s.boundaries,
})

# Standard probe set
STANDARD_PROBES = [STRUCTURAL_PROBE, TOKEN_PROBE, PHASE_PROBE, BOUNDARY_PROBE]
