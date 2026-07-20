#!/usr/bin/env python3
"""
contract.py -- the typed CandidatePackage interface (Ratchet Execution Contract v0).

This is fuel-adjacent INFRASTRUCTURE, not the ratchet itself. It defines the
code-level shape an executable candidate must have so that gates.py and
mss.py can compare candidates with ZERO LLM judgment. See
ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md and
system_v7/constraint_core/RATCHET_SPEC.md (esp. section 3, the entropy-geometry
coface, and section 6, packet-relative MSS) for the process this contract
implements in code.

Boundary (binding, see system_v8/candidates/RANKING_VOID_llm_did_ratchets_job.md):
LLMs / councils PRODUCE and VET fuel (candidates, demand sets D, weakness
proposals). LLMs DO NOT compute relative MSS, presumption, distinguishability,
or any tooth. That is the ratchet -- CODE, run on executable finite
structures. Nothing in this module, gates.py, or mss.py ever asks a model to
judge a candidate.

carrier/states/probes/apply are the executable substrate. reidentify is the
single function every downstream operator (IDENTITY_GATE, persistence_gate,
evolvability_gate, extension_gate, pairwise_mss) uses to induce a candidate's
partition of a shared observation surface X -- pi_C : X -> Q_pi, "the
candidate's presentation as a probe-relative quotient S/~_M"
(HOW_THE_ENGINES_RUN_THE_RATCHET.md Part A.2). persist/evolve/nest_interface
are CONTINUATIONS: gates.py pushes the shared demand set D through them to
build the demand-thickened comparison (RATCHET_SPEC.md section 3's L_D, now
evaluated on multi-layer traces, not one-step probes alone).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Hashable, Optional, Sequence

# ---------------------------------------------------------------------------
# Type aliases -- v0 keeps these structurally open (Any/Hashable). Every toy
# candidate in toy_candidates.py commits to a concrete, hashable, opaque
# representation. Nothing in the contract itself presumes a shape beyond
# "hashable enough to be a dict key / union-find element."
# ---------------------------------------------------------------------------
State = Hashable
Op = Hashable
Probe = Hashable
Record = Hashable

# The owner's converged primitive vocabulary (RANKING_VOID_llm_did_ratchets_job.md,
# ROOT_CARD.md item 7). declared_primitives() is not restricted to only these
# values, but anything drawn from this set is a DIRECT, load-bearing
# commitment IDENTITY_GATE treats as an admission of installed presumption.
PRIMITIVE_VOCABULARY: tuple[str, ...] = (
    "identity",
    "equality",
    "time",
    "metric",
    "probability",
    "frame",
)


def is_recognized_primitive(name: str) -> bool:
    return name in PRIMITIVE_VOCABULARY


# ---------------------------------------------------------------------------
# Small typed value objects the contract's members traffic in.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Carrier:
    """Finite state representation + allowed ops. `allowed_ops` is the
    finite set of transformation tokens valid as the `op` argument to
    apply() for state-transforming (non-probe) calls; probes() is a
    separate finite family, also valid as `op` to apply()."""

    description: str
    allowed_ops: tuple[Op, ...]


@dataclass(frozen=True)
class NestRef:
    """One end of a nest_interface() connection. `recompute_digest`, when
    present, is the candidate's OWN claim about what a fresh recompute of
    its induced partition should hash to -- extension_gate checks this
    claim against an actual fresh recompute; it never trusts the claim
    unchecked."""

    recompute_digest: Optional[str] = None
    note: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        # dict-like convenience so callers can write `ref.get("recompute_digest")`
        # uniformly whether ref is a NestRef or a plain dict.
        return getattr(self, key, default)


@dataclass(frozen=True)
class NestInterface:
    """inner/outer/neighbor connection. All three default to "not
    declared" (None / empty tuple) -- a shell-local candidate that makes no
    nesting claim declares nothing, and extension_gate treats that as
    HOLD/vacuous, never as a failure."""

    inner: Optional[NestRef] = None
    outer: Optional[NestRef] = None
    neighbors: tuple[NestRef, ...] = ()


@dataclass(frozen=True)
class ControlCase:
    """One control pair. `expected_distinguishable=True` marks a positive
    control (D must separate state_a from state_b) -- checked by
    gates.py's probe_validity_gate, which HOLDs if D fails to separate it.
    False marks a negative control (an ablation/alias pair that must NOT
    be falsely separated) -- also checked by probe_validity_gate, which
    FAILs if D separates it anyway (a leakage-fence violation: D exposes a
    distinction the candidate declares must not exist)."""

    label: str
    state_a: State
    state_b: State
    expected_distinguishable: bool


@dataclass(frozen=True)
class ControlSet:
    positive: tuple[ControlCase, ...] = ()
    negative: tuple[ControlCase, ...] = ()


# ---------------------------------------------------------------------------
# The contract itself.
# ---------------------------------------------------------------------------
class CandidatePackage(ABC):
    """Required members (owner's converged contract, RATCHET EXECUTION
    CONTRACT v0 build card). Every method is a hard requirement -- a
    subclass that omits one cannot be instantiated (Python's ABC machinery
    enforces this at construction time, which is itself the first, free
    layer of buildability_gate's job).

    Argument order on apply(op, state) is fixed and never swapped: which
    argument comes first is itself an ordering commitment this contract
    does not treat as neutral (RATCHET_SPEC.md's N01 -- order can be
    load-bearing)."""

    # -- identity / reporting -------------------------------------------------
    @property
    def name(self) -> str:
        return type(self).__name__

    # -- carrier ---------------------------------------------------------------
    @property
    @abstractmethod
    def carrier(self) -> Carrier:
        """Finite state representation + allowed ops."""

    # -- finite substrate --------------------------------------------------
    @abstractmethod
    def states(self) -> Sequence[State]:
        """Finite state population. Must be non-empty for buildability_gate
        to pass."""

    @abstractmethod
    def probes(self) -> Sequence[Probe]:
        """Finite probe/instrument family -- the read-only observation
        tokens valid as `op` to apply(). Must be non-empty for
        buildability_gate to pass."""

    # -- application: explicit order and bracketing -------------------------
    @abstractmethod
    def apply(self, op: Op, state: State) -> Any:
        """Apply ONE op (a carrier.allowed_ops transform token OR a
        probes() instrument token -- the candidate dispatches on which)
        to ONE state. Returns a new State (for a transform) or an
        Observation value (for a probe). Argument order is (op, state),
        fixed."""

    def apply_sequence(
        self, ops: Sequence[Op], state: State, bracketing: str = "left"
    ) -> Any:
        """Explicit-bracketing fold over apply(). Provided once here (not
        abstract) so every candidate gets the same composition semantics;
        only the atomic apply() is candidate-specific.

        bracketing="left"  : (((state . op1) . op2) . op3) ... -- ops applied
                              in the given order, each result feeding the next.
        bracketing="right" : (((state . opN) . op(N-1)) ...) . op1 -- ops
                              applied in REVERSE order.

        The root composition floor is association-unspecified
        (RATCHET_SPEC.md section 3): "left" and "right" may legitimately
        give different results, and this method never collapses that
        difference by assuming associativity -- callers that care about
        order-sensitivity call both and compare.
        """
        if not ops:
            return state
        if bracketing == "left":
            acc = state
            for op in ops:
                acc = self.apply(op, acc)
            return acc
        if bracketing == "right":
            acc = state
            for op in reversed(ops):
                acc = self.apply(op, acc)
            return acc
        raise ValueError(f"unknown bracketing {bracketing!r}; expected 'left' or 'right'")

    # -- re-identification: the nominalist core hook -------------------------
    @abstractmethod
    def reidentify(self, record: Record, current_state: State) -> bool:
        """Is `record` the same entity as `current_state`? THE function
        every downstream operator (IDENTITY_GATE, persistence_gate,
        evolvability_gate, extension_gate, pairwise_mss/frontier in mss.py)
        uses to induce this candidate's partition of a shared observation
        surface X: pi_C(x) = pi_C(y) iff reidentify(x,y) and
        reidentify(y,x). A candidate earns identity only if this function's
        answers are exactly reproduced by the probe-induced partition
        (a=a iff a~b); IDENTITY_GATE is the executable form of that check.
        Must be callable on ANY two hashable values in the candidate's
        state vocabulary, not merely ones drawn from this instance's own
        states() -- gates.py evaluates it over an externally supplied X."""

    # -- continuations: demand-thickening hooks -------------------------------
    @abstractmethod
    def persist(
        self,
        state: State,
        *,
        perturbation: Any = None,
        delay: int = 0,
        partial_access: Any = None,
        relabeled: bool = False,
    ) -> State:
        """Return this candidate's OWN account of what `state` looks like
        after the declared continuation (perturbation / delay /
        partial_access / relabeling). Returns a State, never a
        self-reported viability verdict -- gates.py (persistence_gate)
        mechanically decides viability by re-running reidentify/the
        partition kernel on the returned continuation, never by trusting
        the candidate's say-so. A candidate that "forgets" returns a
        degraded/constant State that the partition kernel will then show
        collapsing previously-live distinctions."""

    @abstractmethod
    def evolve(self, new_constraint: Any) -> Optional["CandidatePackage"]:
        """Return an extended CandidatePackage that additionally
        accommodates `new_constraint`, or None if no admissible extension
        exists. gates.py (evolvability_gate) checks the returned extension
        against the SAME demand set the original candidate had to
        preserve, and checks declared_primitives() gained nothing new
        (no ad-hoc primitive smuggled in during evolution)."""

    # -- nesting --------------------------------------------------------------
    @abstractmethod
    def nest_interface(self) -> NestInterface:
        """Inner/outer/neighbor connection. A shell-local candidate that
        makes no nesting claim returns NestInterface() (all fields empty/
        None) -- extension_gate treats that as HOLD, not FAIL. A candidate
        that DOES claim a nest connection should set inner.recompute_digest
        to what it honestly computes its own induced-partition digest to
        be; extension_gate independently recomputes and compares."""

    # -- primitive commitments --------------------------------------------
    @abstractmethod
    def declared_primitives(self) -> tuple[str, ...]:
        """Explicit list of primitive commitments this candidate installs
        (drawn from PRIMITIVE_VOCABULARY when possible: identity, equality,
        time, metric, probability, frame). Empty tuple = declares nothing
        as primitive -- every distinction must be earned via probes."""

    # -- controls -------------------------------------------------------------
    @abstractmethod
    def controls(self) -> ControlSet:
        """Positive controls (pairs D must separate) and negative controls
        (pairs D must NOT falsely separate -- ablation/alias pairs). Both
        are enforced by gates.py's probe_validity_gate: positive controls
        gate a HOLD ("D has not demonstrated discrimination power"),
        negative controls gate a FAIL ("D leaks a distinction the candidate
        declares must not exist")."""


# ---------------------------------------------------------------------------
# Engine-adapter interface -- v0 stubs only. Concrete engine wiring (actually
# compiling a CandidatePackage's states()/probes()/apply() onto Julia canon,
# JAX batched sweeps, or PyTorch learned components) is a LATER increment.
# See HOW_THE_ENGINES_RUN_THE_RATCHET.md Part B/C: the engines produce the
# BEHAVIORS that induce partitions; this adapter shape is what lets gates.py
# and mss.py be written today against a stable interface that a real engine
# will satisfy later without changing the gate/mss code.
# ---------------------------------------------------------------------------
class EngineAdapter(ABC):
    """Every method raises NotImplementedError in v0. Docstrings describe
    the contract each engine will have to satisfy once wired -- never a
    silent fallback to the Python reference implementation in this module."""

    engine_name: str = "unset"

    @abstractmethod
    def compile_candidate(self, candidate: "CandidatePackage") -> Any:
        """Compile a CandidatePackage's states()/probes()/carrier.allowed_ops
        onto this engine's native representation. Returns an opaque
        engine-specific handle. Must raise if the engine cannot represent
        the candidate -- never silently approximate."""
        raise NotImplementedError(
            f"{self.engine_name} adapter: compile_candidate is a later increment (v0 is contract-only)"
        )

    @abstractmethod
    def run_apply(self, handle: Any, op: Any, state: Any) -> Any:
        """Engine-native equivalent of CandidatePackage.apply(op, state).
        Must preserve the (op, state) argument order and must not assume
        associativity when called as part of a sequence."""
        raise NotImplementedError(
            f"{self.engine_name} adapter: run_apply is a later increment (v0 is contract-only)"
        )

    @abstractmethod
    def run_probe_family(self, handle: Any, probes: Sequence[Any], states: Sequence[Any]) -> Any:
        """Engine-native batched observation table -- the engine-side
        source of the partition pi: X -> Q_pi (RATCHET_SPEC.md section 3).
        Must return something reducible to the same observation-table
        shape gates.py's partition kernel already consumes, so a real
        engine run can replace the Python reference path without changing
        gates.py or mss.py."""
        raise NotImplementedError(
            f"{self.engine_name} adapter: run_probe_family is a later increment (v0 is contract-only)"
        )


class JuliaEngineAdapter(EngineAdapter):
    """Julia canon: authoritative/deep-claim substrate (exceptional algebra
    conventions, high-precision GKSL, octonion/Albert). Per
    HOW_THE_ENGINES_RUN_THE_RATCHET.md Part B, this is the reference engine
    when engines disagree. v0: stub only."""

    engine_name = "julia_canon"


class JaxEngineAdapter(EngineAdapter):
    """JAX: batched/mass-behavior workhorse -- candidates over large
    probe/parameter populations, partitions at scale (the 32,400 -> 3,147
    alias-collapse pattern, HOW_THE_ENGINES_RUN_THE_RATCHET.md Part A.8).
    v0: stub only."""

    engine_name = "jax_workhorse"


class PyTorchEngineAdapter(EngineAdapter):
    """PyTorch: learned-component behavior (JEPA / holodeck candidates) --
    graph/network/autograd machinery, first-class but never the semantic
    arbiter over Julia canon. v0: stub only."""

    engine_name = "pytorch_learned"
