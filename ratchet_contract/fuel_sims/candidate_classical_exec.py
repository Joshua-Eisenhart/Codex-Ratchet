#!/usr/bin/env python3
"""
candidate_classical_exec.py -- the classical relational RIVAL
(system_v8/candidates/candidate_classical_bottomup.md) as an EXECUTABLE
bridge candidate implementing ratchet_contract/bridge_validation/
bridge_interface.py's CandidateBridgeInterface (step_C). Answers the SAME
18-action deck as candidate_spinor_qit_exec.py (see ACTIONS below -- checked
literally-equal at runtime by practice_run.py, never just assumed).

SCOPE (binding, matches bridge_validation/README.md's own ceiling): PRACTICE
+ fuel development. Not an admission, not a scientific claim.
promotion_allowed=false; formal_admission_allowed=false.

CARRIER: per the md doc's Layer 0/1/2 ladder -- "a finite relation over a
finite atom set... never a density matrix or spinor." Opaque state here is
`(weights, edges)`:
  - `weights`: a 4-tuple of NONNEGATIVE INTEGERS over a fixed finite atom
    universe {0,1,2,3} standing in for the finite labels "00","01","10","11"
    (a shared finite label space of size 4 is the minimum ANY carrier over a
    2-slot binary probe needs to be comparable at all -- using the same 4
    labels is not smuggled quantum structure; nothing here requires the
    weights to FACTOR as a bit0-marginal times a bit1-marginal, which a
    tensor-product carrier would require and this one deliberately does
    not). Total weight is conserved at TOTAL_WEIGHT=4 by every rewrite
    below, by construction -- no positivity-of-a-matrix, no unit-trace, no
    complex amplitude, no tensor-factorization commitment.
  - `edges`: a finite frozenset of atom-pairs, the relation's declared
    correlations -- genuinely relational, not a bookkeeping accident.

DECLARED_PRIMITIVES: () -- empty. This carrier installs no probability
model (weights are plain nonnegative integers, not a normalized measure
until the very last step of read_outcome_z, which is output-formatting, not
carrier structure), no continuous time (delay is a discrete step count, not
a qutip-style dt), no metric, no frame. This is the carrier's own claimed
minimality, tested honestly rather than asserted: read_outcome_x below is a
genuine, structural point where this carrier admits it cannot do what the
richer rival can (see below).

ORDER-SENSITIVITY, verified by hand before this file was trusted (not just
claimed): starting from root_00 = (4,0,0,0), applying rewrite H0 then
CNOT01 reaches (2,0,0,2); applying CNOT01 then H0 reaches (2,0,2,0) --
different final weight vectors, confirming ordered_compose is genuinely
order-sensitive on this carrier, for the same reason it is on the spinor
carrier (H0-flavoured "spread" and CNOT01-flavoured "conditional swap" do
not commute as operations on the weight vector).

BRACKET_COMPOSE, same honest structural finding as the spinor file: applying
a SEQUENCE of rewrite functions in a fixed temporal order is function
composition, which is associative regardless of parenthesization. Both
"left" and "right" bracket tokens apply the same three named rewrites in
the same order and must produce byte-identical results here too -- an
expected, cross-candidate-consistent negative, not a defect specific to
either carrier family.

READ_OUTCOME_X -- NOT a coherence readout (this carrier installs no
superposition structure, so a genuine X-basis probe is inapplicable), but
also deliberately NOT a flat refusal: an earlier draft made it a constant
sentinel regardless of state, which was caught, before this file was ever
run, as a real design gap rather than an honest weakness -- couple_inner_
outer / couple_neighbor_neighbor are the only two actions that write to
`edges`, and a constant read_outcome_x meant NOTHING in the declared 18-
action deck ever read `edges` back out, making those two actions dead
writes for this carrier specifically (not a shared QM artifact -- see the
next paragraph). Fixed: read_outcome_x reports the carrier's own honest
analog of "what's in the off-diagonal/relational part of your state" --
the current edge-relation content (a canonical sorted tuple of atom-pairs,
or an explicit "edges_empty" token) -- genuinely different information from
read_outcome_z's weight/population readout, and genuinely different in
KIND from the spinor carrier's coherence-basis measurement, honestly
labelled as such rather than smuggled in as if it were the same thing.

A general QM fact, verified by hand and worth naming so it is not mistaken
for a classical-carrier-only gap: applying a purely-diagonal (relative-
phase) gate such as CZ to a computational-basis state (no superposition
present) has ZERO observable effect in ANY measurement basis -- phase only
becomes visible through interference with an existing superposition. So
`couple_inner_outer` applied directly to `root_00` is expected to be
invisible to read_outcome_z AND read_outcome_x on the SPINOR carrier too,
from that specific starting point; the practice demand deck deliberately
also probes couple_inner_outer / couple_neighbor_neighbor from states that
already carry superposition (e.g. root_plus0), where a phase effect has
something to interfere with and a difference becomes checkable.

BOOKKEEPING DISCIPLINE: identical convention to the spinor file -- every
non-read transform action returns the constant Outcome.deterministic("ack");
only read_outcome_z/x and extend_under_constraint's admitted/rejected
predicate carry real information.

No qutip / numpy dependency (deliberately -- pure Python integer
arithmetic only), so this file can be imported and run under a plain
python3, independent of the sim-stack interpreter the spinor file needs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Sequence

_FUEL_SIMS_DIR = Path(__file__).resolve().parent
_RATCHET_CONTRACT_DIR = _FUEL_SIMS_DIR.parent
_BRIDGE_VALIDATION_DIR = _RATCHET_CONTRACT_DIR / "bridge_validation"
for _p in (_FUEL_SIMS_DIR, _RATCHET_CONTRACT_DIR, _BRIDGE_VALIDATION_DIR):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from bridge_interface import (  # noqa: E402
    Action,
    CandidateBridgeInterface,
    NestContext,
    Outcome,
)

# ---------------------------------------------------------------------------
# Shared constants -- MUST stay literally in sync with
# candidate_spinor_qit_exec.py's ACTIONS/SHOT_BUDGET/ROOTS. practice_run.py
# asserts this equality at runtime rather than trusting it by inspection.
# ---------------------------------------------------------------------------
SHOT_BUDGET = 1000
TOTAL_WEIGHT = 4  # this carrier's own small internal integer budget (not shared with the spinor file)
ROOTS: tuple[str, ...] = ("root_00", "root_bell", "root_plus0", "root_mixed")

ACTIONS: tuple[Action, ...] = (
    "prepare_00",
    "prepare_bell",
    "prepare_plus0",
    "restrict_trace_out_qubit1",
    ("ordered_compose", ("H0", "CNOT01")),
    ("ordered_compose", ("CNOT01", "H0")),
    ("bracket_compose", ("left", ("H0", "X1", "CNOT01"))),
    ("bracket_compose", ("right", ("H0", "X1", "CNOT01"))),
    "perturb_small_rx0",
    "delay_short",
    "delay_long",
    "couple_inner_outer",
    "couple_neighbor_neighbor",
    "renest_swap01",
    ("extend_under_constraint", "trace_preserving"),
    ("extend_under_constraint", "require_purity"),
    "read_outcome_z",
    "read_outcome_x",
)

_ACTION_CATEGORY: dict[Action, str] = {
    "prepare_00": "prepare_restrict",
    "prepare_bell": "prepare_restrict",
    "prepare_plus0": "prepare_restrict",
    "restrict_trace_out_qubit1": "prepare_restrict",
    ("ordered_compose", ("H0", "CNOT01")): "ordered_compose",
    ("ordered_compose", ("CNOT01", "H0")): "ordered_compose",
    ("bracket_compose", ("left", ("H0", "X1", "CNOT01"))): "bracket_compose",
    ("bracket_compose", ("right", ("H0", "X1", "CNOT01"))): "bracket_compose",
    "perturb_small_rx0": "perturb",
    "delay_short": "delay_retain_history",
    "delay_long": "delay_retain_history",
    "couple_inner_outer": "couple_inner_outer",
    "couple_neighbor_neighbor": "couple_neighbor_neighbor",
    "renest_swap01": "renest",
    ("extend_under_constraint", "trace_preserving"): "extend_under_constraint",
    ("extend_under_constraint", "require_purity"): "extend_under_constraint",
    "read_outcome_z": "read_outcome",
    "read_outcome_x": "read_outcome",
}
assert set(_ACTION_CATEGORY) == set(ACTIONS)

DELAY_STEPS_LONG = 5


# ---------------------------------------------------------------------------
# Deterministic integer rounding (mirrors the spinor file's largest-remainder
# helper -- duplicated rather than shared-imported, so each exec file stays
# independently self-contained and readable).
# ---------------------------------------------------------------------------
def _largest_remainder_round(fractions: Sequence[float], total: int) -> list[int]:
    fracs = [max(0.0, float(f)) for f in fractions]
    s = sum(fracs)
    if s <= 0:
        base = [0] * len(fracs)
        base[0] = total
        return base
    scaled = [f / s * total for f in fracs]
    floors = [int(x) for x in scaled]  # floor for nonnegative floats
    remainder = total - sum(floors)
    order = sorted(range(len(scaled)), key=lambda i: (-(scaled[i] - floors[i]), i))
    for i in range(remainder):
        floors[order[i]] += 1
    return floors


State = tuple[tuple[int, int, int, int], frozenset]


def _initial_state(root: str) -> State:
    if root == "root_00":
        return (4, 0, 0, 0), frozenset()
    if root == "root_bell":
        return (2, 0, 0, 2), frozenset({(0, 3)})
    if root == "root_plus0":
        return (2, 2, 0, 0), frozenset()
    if root == "root_mixed":
        return (1, 1, 1, 1), frozenset()
    raise ValueError(f"unknown root {root!r}")


def _flip0(i: int) -> int:
    return i ^ 0b10


def _flip1(i: int) -> int:
    return i ^ 0b01


def _bit_reverse(i: int) -> int:
    b0 = (i >> 1) & 1
    b1 = i & 1
    return (b1 << 1) | b0


# -- named rewrites, each a pure function (weights, edges) -> (weights, edges) --
def _rewrite_H0(weights, edges):
    w = list(weights)
    new_w = [w[i] + w[_flip0(i)] for i in range(4)]
    return tuple(_largest_remainder_round(new_w, TOTAL_WEIGHT)), edges


def _rewrite_X1(weights, edges):
    w = list(weights)
    new_w = [0, 0, 0, 0]
    for i in range(4):
        new_w[_flip1(i)] = w[i]
    return tuple(new_w), edges  # pure permutation -- exact, no rounding needed


def _rewrite_CNOT01(weights, edges):
    w = list(weights)
    w[2], w[3] = w[3], w[2]  # controlled swap: bit0=1 branch only (atoms 2,3); bit0=0 branch fixed
    return tuple(w), edges


_REWRITES = {"H0": _rewrite_H0, "X1": _rewrite_X1, "CNOT01": _rewrite_CNOT01}


def _restrict(weights, edges) -> State:
    w = weights
    pair0 = (w[0] + w[1]) / 2.0
    pair1 = (w[2] + w[3]) / 2.0
    new_w = _largest_remainder_round([pair0, pair0, pair1, pair1], TOTAL_WEIGHT)
    return tuple(new_w), frozenset()  # marginalizing erases correlations that referenced the traced coordinate


def _perturb(weights, edges) -> State:
    w = list(weights)
    if w[0] > 0:
        w[0] -= 1
        w[2] += 1
    return tuple(w), edges  # bounded single-unit nudge; a no-op once atom0 is empty (honest edge case)


def _delay_step(weights, edges) -> State:
    w = list(weights)
    moved = 0
    for i in (1, 2, 3):
        take = w[i] // 2
        w[i] -= take
        moved += take
    w[0] += moved
    new_edges = edges if moved == 0 else frozenset()  # relaxation also erases correlation once it moves anything
    return tuple(w), new_edges


def _argmax_atom(weights) -> int:
    return max(range(4), key=lambda i: weights[i])


def _couple_inner_outer(weights, edges) -> State:
    i = _argmax_atom(weights)
    j = 3 - i  # opposite corner: both bits flipped
    return weights, edges | {tuple(sorted((i, j)))}


def _couple_neighbor_neighbor(weights, edges) -> State:
    i = _argmax_atom(weights)
    j = i ^ 0b01  # adjacent: second bit flipped only -- structurally different topology from couple_inner_outer
    return weights, edges | {tuple(sorted((i, j)))}


def _renest(weights, edges) -> State:
    new_w = [0, 0, 0, 0]
    for i in range(4):
        new_w[_bit_reverse(i)] = weights[i]
    new_edges = frozenset(tuple(sorted((_bit_reverse(a), _bit_reverse(b)))) for (a, b) in edges)
    return tuple(new_w), new_edges


def _purity_classical(weights) -> bool:
    return sum(1 for x in weights if x > 0) == 1


def _extend_under_constraint(weights, edges, constraint: str) -> tuple[State, bool]:
    if constraint == "trace_preserving":
        return (weights, edges), True  # total conserved by construction under every rewrite -- always admitted
    if constraint == "require_purity":
        return (weights, edges), _purity_classical(weights)  # state never mutated by the attempt either way
    raise ValueError(f"unknown constraint {constraint!r}")


def _read_outcome_z(weights) -> Outcome:
    counts = _largest_remainder_round(list(weights), SHOT_BUDGET)
    labels = ("00", "01", "10", "11")
    return Outcome.table({labels[i]: counts[i] for i in range(4) if counts[i] > 0})


def _read_outcome_x(weights, edges) -> Outcome:
    # Reports the relation's own edge content -- see module docstring for why
    # this replaced an earlier constant-refusal draft (a real dead-write gap,
    # not an honest weakness: nothing else in the deck ever reads `edges`).
    if not edges:
        return Outcome.table({"edges_empty": SHOT_BUDGET})
    token = f"edges:{tuple(sorted(tuple(sorted(e)) for e in edges))}"
    return Outcome.table({token: SHOT_BUDGET})


class ClassicalRelationalExecCandidate(CandidateBridgeInterface):
    """Finite-relation rival: opaque state = (weights, edges), a nonnegative
    integer multiplicity vector over 4 atoms plus a finite correlation
    relation. Answers the exact same 18-action deck as
    SpinorQitExecCandidate; see module docstring for where and why the two
    carriers' answers genuinely diverge (read_outcome_x) versus where they
    happen to agree for the same structural reason (bracket_compose)."""

    name = "classical_relational_exec"

    def action_alphabet(self) -> Sequence[Action]:
        return ACTIONS

    def action_category(self, action: Action) -> str:
        return _ACTION_CATEGORY[action]

    def initial_state(self, root):
        return _initial_state(root)

    def step_C(self, state, action, nest_context: Optional[NestContext] = None):
        weights, edges = state
        if action == "prepare_00":
            return _initial_state("root_00"), Outcome.deterministic("ack")
        if action == "prepare_bell":
            return _initial_state("root_bell"), Outcome.deterministic("ack")
        if action == "prepare_plus0":
            return _initial_state("root_plus0"), Outcome.deterministic("ack")
        if action == "restrict_trace_out_qubit1":
            return _restrict(weights, edges), Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "ordered_compose":
            names = action[1]
            w, e = weights, edges
            for nm in names:
                w, e = _REWRITES[nm](w, e)
            return (w, e), Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "bracket_compose":
            _bracket, names = action[1]
            w, e = weights, edges
            for nm in names:
                w, e = _REWRITES[nm](w, e)
            return (w, e), Outcome.deterministic("ack")
        if action == "perturb_small_rx0":
            return _perturb(weights, edges), Outcome.deterministic("ack")
        if action == "delay_short":
            return _delay_step(weights, edges), Outcome.deterministic("ack")
        if action == "delay_long":
            w, e = weights, edges
            for _ in range(DELAY_STEPS_LONG):
                w, e = _delay_step(w, e)
            return (w, e), Outcome.deterministic("ack")
        if action == "couple_inner_outer":
            return _couple_inner_outer(weights, edges), Outcome.deterministic("ack")
        if action == "couple_neighbor_neighbor":
            return _couple_neighbor_neighbor(weights, edges), Outcome.deterministic("ack")
        if action == "renest_swap01":
            return _renest(weights, edges), Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "extend_under_constraint":
            constraint = action[1]
            (w, e), admitted = _extend_under_constraint(weights, edges, constraint)
            return (w, e), Outcome.deterministic("admitted" if admitted else "rejected")
        if action == "read_outcome_z":
            return (weights, edges), _read_outcome_z(weights)
        if action == "read_outcome_x":
            return (weights, edges), _read_outcome_x(weights, edges)
        raise ValueError(f"unknown action {action!r}")

    # Extra, non-ABC informational method -- see candidate_spinor_qit_exec.py's
    # matching docstring note on why this exists outside CandidateBridgeInterface.
    def declared_primitives(self) -> tuple[str, ...]:
        return ()


if __name__ == "__main__":
    c = ClassicalRelationalExecCandidate()
    s = c.initial_state("root_00")
    s, _ = c.step_C(s, ("ordered_compose", ("H0", "CNOT01")))
    s, o2 = c.step_C(s, "read_outcome_z")
    print("root_00 -> H0,CNOT01 -> read_outcome_z:", o2)
    s3 = c.initial_state("root_00")
    s3, _ = c.step_C(s3, ("ordered_compose", ("CNOT01", "H0")))
    s3, o3 = c.step_C(s3, "read_outcome_z")
    print("root_00 -> CNOT01,H0 -> read_outcome_z:", o3)
    print("order-sensitive:", o2 != o3)
