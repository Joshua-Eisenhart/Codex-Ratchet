#!/usr/bin/env python3
"""
toy_candidates.py -- 4 TOY candidates implementing contract.py, built so the
gates DISCRIMINATE (self-verification). Each toy isolates exactly ONE
failure mode so the discrimination matrix in run_contract_selfcheck.py shows
every gate PASSing on the right toy and FAILing/HOLDing on the right toy:

  toy_raw_label            -- reidentify() keyed on raw_id, not on anything
                               a probe exposes. FAILS IDENTITY_GATE.
  toy_quotient_respecting  -- reidentify() keyed on exactly what probes()
                               exposes (value), at the FINEST honest
                               granularity. PASSES every gate.
  toy_frozen               -- reidentify() keyed on probe-visible content,
                               but at a COARSER granularity (warm/cool
                               category, not exact value) -- still
                               probe-honest, so PASSES IDENTITY_GATE, and
                               its coarser partition is what lets it beat
                               toy_quotient_respecting on a base (untickened)
                               coarseness comparison. evolve() always
                               returns None -> FAILS the evolvability
                               demand. Its declared nest digest is a fixed,
                               stale literal -> FAILS the whole-nest demand
                               (extension_gate).
  toy_amnesiac             -- reidentify() at the SAME exact-value
                               granularity as toy_quotient_respecting
                               (so a base coarseness comparison between the
                               two is a genuine tie / re-merge). persist()
                               wipes value to a constant "forgotten" marker
                               under any declared continuation, so
                               previously-distinct states collapse together
                               afterward -> FAILS the persistence demand.

All four share one canonical observation surface X_BASE and one thin base
demand set D_BASE (a single required distinction: red vs blue), matching
RATCHET_SPEC.md's own convention that X and D are pre-registered/external,
never derived privately from a single candidate.
"""

from __future__ import annotations

from typing import Sequence

from contract import (
    CandidatePackage,
    Carrier,
    ControlCase,
    ControlSet,
    NestInterface,
    NestRef,
    State,
)
from gates import induced_partition, partition_digest

# ---------------------------------------------------------------------------
# Shared observation surface and base demand set.
# ---------------------------------------------------------------------------
X_BASE: tuple[State, ...] = ((0, "red"), (1, "blue"), (2, "red"), (3, "green"), (4, "yellow"))

# Deliberately THIN: only one demanded distinction (red vs blue). This is
# the point -- RATCHET_SPEC.md section 6's MSS is always relative to what D
# actually demands, not to every distinction a finer candidate happens to
# make. A candidate that separates red/yellow or blue/green too is not
# rewarded for it; D never asked for that.
D_BASE: tuple[tuple[State, State], ...] = (
    ((0, "red"), (1, "blue")),
)

_WARM = {"red", "yellow"}


def _category(value: str) -> str:
    return "warm" if value in _WARM else "cool"


# ---------------------------------------------------------------------------
# toy_raw_label
# ---------------------------------------------------------------------------
class ToyRawLabel(CandidatePackage):
    def __init__(self, states: Sequence[State] = X_BASE):
        self._states = tuple(states)

    @property
    def name(self) -> str:
        return "toy_raw_label"

    @property
    def carrier(self) -> Carrier:
        return Carrier(
            description="raw (raw_id,value) pairs; probes read value only; identity keyed on raw_id",
            allowed_ops=("noop",),
        )

    def states(self):
        return self._states

    def probes(self):
        return ("read_value",)

    def apply(self, op, state):
        raw_id, value = state
        if op == "read_value":
            return value
        if op == "noop":
            return state
        if op == "constant_probe":
            return "K"
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        # UNEARNED: raw_id equality, not probe-visible value. This is the
        # defect IDENTITY_GATE must catch.
        return record[0] == current_state[0]

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return (state[0], state[1])

    def evolve(self, new_constraint):
        extra = (len(self._states) + 100, f"ext_{new_constraint}")
        return ToyRawLabel(self._states + (extra,))

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return ("identity",)

    def controls(self):
        pos = (ControlCase("red_vs_blue", (0, "red"), (1, "blue"), True),)
        neg = (ControlCase("red_vs_red_alias", (0, "red"), (2, "red"), False),)
        return ControlSet(positive=pos, negative=neg)


# ---------------------------------------------------------------------------
# toy_quotient_respecting
# ---------------------------------------------------------------------------
class ToyQuotientRespecting(CandidatePackage):
    def __init__(self, states: Sequence[State] = X_BASE):
        self._states = tuple(states)

    @property
    def name(self) -> str:
        return "toy_quotient_respecting"

    @property
    def carrier(self) -> Carrier:
        return Carrier(
            description="raw (raw_id,value) pairs; identity earned via probes only, exact-value granularity",
            allowed_ops=("noop",),
        )

    def states(self):
        return self._states

    def probes(self):
        return ("read_value",)

    def apply(self, op, state):
        raw_id, value = state
        if op == "read_value":
            return value
        if op == "noop":
            return state
        if op == "constant_probe":
            return "K"
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        # EARNED: compares only what probes can see (value), never raw_id.
        return record[1] == current_state[1]

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return (state[0], state[1])

    def evolve(self, new_constraint):
        extra = (len(self._states) + 100, f"ext_{new_constraint}")
        return ToyQuotientRespecting(self._states + (extra,))

    def nest_interface(self):
        # Honest self-recompute: whatever a fresh induced_partition(self, X_BASE)
        # digests to, right now -- extension_gate independently reproduces
        # this and compares; nothing here is trusted unchecked.
        digest = partition_digest(induced_partition(self, X_BASE))
        return NestInterface(inner=NestRef(recompute_digest=digest, note="honest self-recompute"))

    def declared_primitives(self):
        return ()

    def controls(self):
        pos = (ControlCase("red_vs_blue", (0, "red"), (1, "blue"), True),)
        neg = (ControlCase("red_vs_red_alias", (0, "red"), (2, "red"), False),)
        return ControlSet(positive=pos, negative=neg)


# ---------------------------------------------------------------------------
# toy_frozen
# ---------------------------------------------------------------------------
class ToyFrozen(CandidatePackage):
    def __init__(self, states: Sequence[State] = X_BASE):
        self._states = tuple(states)

    @property
    def name(self) -> str:
        return "toy_frozen"

    @property
    def carrier(self) -> Carrier:
        return Carrier(
            description="raw (raw_id,value) pairs; identity earned via probes at warm/cool "
                        "category granularity (coarser than exact value); frozen, cannot evolve",
            allowed_ops=("noop",),
        )

    def states(self):
        return self._states

    def probes(self):
        return ("read_category",)

    def apply(self, op, state):
        raw_id, value = state
        if op == "read_category":
            return _category(value)
        if op == "noop":
            return state
        if op == "constant_probe":
            return "K"
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        # EARNED, but at a coarser granularity than toy_quotient_respecting:
        # category(value), not value itself. Still exactly what its own
        # probe family (read_category) exposes -- probe-honest.
        return _category(record[1]) == _category(current_state[1])

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return (state[0], state[1])

    def evolve(self, new_constraint):
        return None  # the point of this toy: no admissible extension, ever

    def nest_interface(self):
        # Deliberately STALE: recorded once, never kept in sync with
        # reality -- "frozen". extension_gate must catch the mismatch.
        return NestInterface(
            inner=NestRef(recompute_digest="stale-digest-0000-recorded-once",
                           note="recorded once at authoring time, never refreshed")
        )

    def declared_primitives(self):
        return ()

    def controls(self):
        pos = (ControlCase("green_vs_yellow", (3, "green"), (4, "yellow"), True),)
        neg = ()
        return ControlSet(positive=pos, negative=neg)


# ---------------------------------------------------------------------------
# toy_amnesiac
# ---------------------------------------------------------------------------
class ToyIntransitiveReidentify(CandidatePackage):
    """Probe-coarse partition matches transitive closure, but raw answers do not.

    The old IDENTITY_GATE check would PASS this candidate; the widened check
    correctly FAILs because 0~1 and 1~2 merge a block while 0~2 is denied.
    """

    def __init__(self, states: Sequence[State] = X_BASE):
        self._states = tuple(states)

    @property
    def name(self) -> str:
        return "toy_intransitive_reidentify"

    @property
    def carrier(self) -> Carrier:
        return Carrier(description="constant probe with deliberately non-transitive reidentify", allowed_ops=("noop",))

    def states(self):
        return self._states

    def probes(self):
        return ("constant_probe",)

    def apply(self, op, state):
        if op == "constant_probe":
            return "same"
        if op == "noop":
            return state
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        return abs(record[0] - current_state[0]) <= 1

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return state

    def evolve(self, new_constraint):
        return self

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return ()

    def controls(self):
        return ControlSet()


# ---------------------------------------------------------------------------
class ToyAmnesiac(CandidatePackage):
    def __init__(self, states: Sequence[State] = X_BASE):
        self._states = tuple(states)

    @property
    def name(self) -> str:
        return "toy_amnesiac"

    @property
    def carrier(self) -> Carrier:
        return Carrier(
            description="raw (raw_id,value) pairs; identity earned via probes, exact-value "
                        "granularity; cannot hold a record through any continuation",
            allowed_ops=("noop",),
        )

    def states(self):
        return self._states

    def probes(self):
        return ("read_value",)

    def apply(self, op, state):
        raw_id, value = state
        if op == "read_value":
            return value
        if op == "noop":
            return state
        if op == "constant_probe":
            return "K"
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        return record[1] == current_state[1]

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        # Amnesia: ANY declared continuation wipes value to a constant
        # marker, so previously-distinct states become probe-indistinguishable
        # afterward. This is what the persistence demand must catch.
        return (state[0], "forgotten")

    def evolve(self, new_constraint):
        extra = (len(self._states) + 100, f"ext_{new_constraint}")
        return ToyAmnesiac(self._states + (extra,))

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return ()

    def controls(self):
        pos = (ControlCase("red_vs_blue", (0, "red"), (1, "blue"), True),)
        neg = ()
        return ControlSet(positive=pos, negative=neg)


def all_toys() -> tuple[CandidatePackage, ...]:
    return (ToyRawLabel(), ToyQuotientRespecting(), ToyFrozen(), ToyAmnesiac(), ToyIntransitiveReidentify())
