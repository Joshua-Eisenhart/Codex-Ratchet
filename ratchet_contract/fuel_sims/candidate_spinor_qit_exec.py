#!/usr/bin/env python3
"""
candidate_spinor_qit_exec.py -- the owner's PROPOSED MODEL
(system_v8/candidates/candidate_spinor_qit.md) as an EXECUTABLE bridge
candidate implementing ratchet_contract/bridge_validation/bridge_interface.py's
CandidateBridgeInterface (step_C).

SCOPE (binding, matches bridge_validation/README.md's own ceiling): this is
PRACTICE + fuel development -- exercising the ratchet pipeline machinery
end-to-end on a real, small, finite QIT carrier. It does NOT admit this
carrier, does NOT compute a scientific/MSS claim about the owner's manifold,
and is NOT the 9-layer candidate_spinor_qit.md schedule executed in full --
it is a SMALL, TRACTABLE 2-qubit slice exercising the manifold-native action
vocabulary genuinely (real qutip density matrices, real GKSL/mesolve
evolution, real projective-measurement statistics), not a string-typed
simulacrum. promotion_allowed=false; formal_admission_allowed=false.

CARRIER: a 2-qubit (4x4) density matrix (qutip.Qobj, dims=[[2,2],[2,2]]).
Opaque state = the Qobj itself. Per bridge_interface.py's contract, no
bridge in this package ever compares, hashes, or exposes this state to a
partition decision (and Qobj is in fact NOT hashable in this qutip version,
confirmed empirically -- attempting to use it as a dict key would raise
TypeError, which is a structural guarantee this file never leaks the state
into an identity comparison, not merely a stated intention).

DECLARED_PRIMITIVES (what this carrier genuinely installs, drawn from
contract.py's PRIMITIVE_VOCABULARY): "probability" (read_outcome_* reports
Born-rule statistics -- even though rendered as finite integer multiplicities
per the corrected bridge contract, the underlying commitment is a probability
model) and "time" (the delay_retain_history actions use qutip.mesolve with a
genuine continuous-time parameter dt). NOT declared: "identity"/"equality"
(state is opaque, never compared for raw identity -- earning distinctions
only through declared read actions is the whole point); "metric" (no
geometric-distance commitment is used by any action); "frame" (the
computational-Z and Hadamard-X measurement bases are DECLARED, examinable
action tokens on the public alphabet, not a smuggled ambient default).

OUTCOME DESIGN (ensemble-read semantics, a documented choice, not a
shortcut): step_C must be pure/deterministic -- "no unrecorded randomness at
call time" (bridge_interface.py). A real single-shot projective measurement
would collapse the state stochastically, which the corrected contract
forbids. Instead, read_outcome_z / read_outcome_x treat the density matrix
as describing an ensemble/preparation procedure: they report the EXACT Born
probabilities, deterministically rounded (largest-remainder / Hamilton
apportionment, never plain floor/round-half-up, so counts always sum exactly
to SHOT_BUDGET) to integer counts over a fixed SHOT_BUDGET, and leave the
running state UNCHANGED (s'=s) so later actions in the same history continue
from the pre-read state. This matches every read_outcome-style action in
ratchet_contract/bridge_validation/controls.py (state unchanged on read).

BOOKKEEPING DISCIPLINE (bridge_interface.py's illicit-identity rule): every
non-read (transform) action returns the SAME constant acknowledgement token
Outcome.deterministic("ack"), carrying NO information about which specific
action or parameters were used -- exactly controls.py's own convention
(C1/C3/C4/C5/C6 all use "ack"/"composed" uniformly regardless of which
branch fired). Only read_outcome_z/x (genuine Born statistics) and
extend_under_constraint (a genuinely computed admitted/rejected predicate)
carry real information. This was a deliberate fix during design: an earlier
draft tagged bracket_compose's acknowledgement with "composed_left" /
"composed_right", which would have let the BRACKET LABEL leak into the
immediate Outcome regardless of physics -- exactly the kind of illicit,
bookkeeping-driven semantic leak controls.py's C2 is built to catch. Fixed
before this file was ever run.

HONEST STRUCTURAL FINDING, stated up front rather than discovered by
surprise later: bracket_compose is mathematically INERT on this carrier.
Composing a sequence of unitary conjugations (rho -> U_n...U_1 rho
U_1^dag...U_n^dag) is function composition, which is associative regardless
of how you group/parenthesize the sequence -- both "left" and "right"
bracket tokens below apply the SAME three named gates in the SAME temporal
order and must produce byte-identical final states. This is a fact about
linear-map composition, not a modeling shortcut, and the practice run
reports it as an honest negative rather than hiding it. ordered_compose,
by contrast, IS genuinely order-sensitive (verified by hand and confirmed
by qutip: H0-then-CNOT01 from |00> reaches the Bell state; CNOT01-then-H0
from |00> reaches the product state |+0> -- the two orders are physically
different final states).

MEMORY GATE: per the build task's binding instruction, available-memory
headroom is checked BEFORE qutip is imported (qutip pulls in a sizeable
native/BLAS stack). Uses psutil when available; falls back to parsing
macOS `vm_stat` otherwise. Raises MemoryError (fail loud) if headroom is
below the floor -- this file will not silently proceed under memory
pressure. The receipt is exposed as MEMORY_GATE_RECEIPT for the orchestrator
(practice_run.py) to embed in its own report.

Run under the sim-stack interpreter (qutip 5.2.3 confirmed installed there):
    /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
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
# Memory gate -- MUST run before `import qutip`.
# ---------------------------------------------------------------------------
def _memory_gate_check(min_available_fraction: float = 0.25) -> dict:
    """Real, mechanical memory-headroom check. Returns a receipt dict.
    Raises MemoryError (fail loud, never silent) if the floor is not met."""
    import shutil
    import subprocess

    available_fraction: Optional[float] = None
    source = "unresolved"

    try:
        import psutil  # local, deferred import -- lightweight compared to qutip

        vm = psutil.virtual_memory()
        available_fraction = vm.available / vm.total
        source = "psutil.virtual_memory"
    except ImportError:
        if shutil.which("vm_stat"):
            try:
                out = subprocess.run(
                    ["vm_stat"], capture_output=True, text=True, timeout=5, check=True
                ).stdout
                stats = {}
                for line in out.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        stats[k.strip()] = v.strip().rstrip(".")
                free = int(stats.get("Pages free", 0))
                inactive = int(stats.get("Pages inactive", 0))
                speculative = int(stats.get("Pages speculative", 0))
                wired = int(stats.get("Pages wired down", 0))
                active = int(stats.get("Pages active", 0))
                total_pages = free + inactive + speculative + wired + active
                available_pages = free + inactive + speculative
                if total_pages > 0:
                    available_fraction = available_pages / total_pages
                    source = "vm_stat_fallback"
            except Exception as e:  # noqa: BLE001 -- report the parse failure, do not crash the gate on it
                source = f"vm_stat_fallback_failed:{e!r}"

    receipt = {
        "min_available_fraction_required": min_available_fraction,
        "available_fraction_observed": available_fraction,
        "source": source,
    }
    if available_fraction is None:
        receipt["gate_verdict"] = "UNRESOLVED_no_memory_reading_available"
        print(f"MEMORY GATE: {receipt} -- proceeding without a hard block (no reading available)", file=sys.stderr)
        return receipt
    if available_fraction < min_available_fraction:
        receipt["gate_verdict"] = "BLOCKED_below_floor"
        raise MemoryError(
            f"memory gate: only {available_fraction:.1%} available memory, below the required "
            f"{min_available_fraction:.0%} floor -- refusing to import qutip. receipt={receipt}"
        )
    receipt["gate_verdict"] = "PASS"
    print(f"MEMORY GATE: PASS -- {available_fraction:.1%} available (>= {min_available_fraction:.0%} floor)", file=sys.stderr)
    return receipt


MEMORY_GATE_RECEIPT = _memory_gate_check()

import numpy as np  # noqa: E402
import qutip as qt  # noqa: E402

# ---------------------------------------------------------------------------
# Shared constants (must stay literally in sync with candidate_classical_exec.py
# -- practice_run.py asserts this equality at runtime rather than trusting it).
# ---------------------------------------------------------------------------
SHOT_BUDGET = 1000
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

THETA_SMALL = 0.05       # perturb_small_rx0's rotation angle (radians)
GAMMA = 0.8              # amplitude-damping rate for delay_retain_history
DELAY_SHORT_DT = 0.2
DELAY_LONG_DT = 3.0
PURITY_FLOOR = 1 - 1e-6  # require_purity's admissibility threshold

# ---------------------------------------------------------------------------
# Gate library -- constructed manually (qutip 5.x dropped the top-level
# qt.cnot()/qt.swap() gate helpers; verified empirically before writing this
# file, see the build session's qutip_smoke.py). All checked for unitarity
# at import time below (a cheap, real self-check, not asserted in prose).
# ---------------------------------------------------------------------------
_I2 = qt.qeye(2)
_SX = qt.sigmax()
_SP = qt.sigmap()  # verified empirically: maps basis(2,1) -> basis(2,0), i.e. decays "1"-> "0"
_H1 = qt.Qobj([[1, 1], [1, -1]]) / np.sqrt(2)

_CNOT01 = qt.Qobj(
    np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex),
    dims=[[2, 2], [2, 2]],
)
_SWAP = qt.Qobj(
    np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex),
    dims=[[2, 2], [2, 2]],
)
_CZ = qt.Qobj(
    np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dtype=complex),
    dims=[[2, 2], [2, 2]],
)
_ISWAP = qt.Qobj(
    np.array([[1, 0, 0, 0], [0, 0, 1j, 0], [0, 1j, 0, 0], [0, 0, 0, 1]], dtype=complex),
    dims=[[2, 2], [2, 2]],
)


def _u1(op: "qt.Qobj", qubit: int) -> "qt.Qobj":
    return qt.tensor(op, _I2) if qubit == 0 else qt.tensor(_I2, op)


_GATES: dict[str, "qt.Qobj"] = {
    "H0": _u1(_H1, 0),
    "X1": _u1(_SX, 1),
    "CNOT01": _CNOT01,
}

for _name, _U in list(_GATES.items()) + [("SWAP", _SWAP), ("CZ", _CZ), ("ISWAP", _ISWAP)]:
    _dev = (_U * _U.dag() - qt.qeye([2, 2])).norm()
    assert _dev < 1e-9, f"gate {_name!r} failed unitarity self-check, deviation={_dev}"


def _apply_u(rho: "qt.Qobj", U: "qt.Qobj") -> "qt.Qobj":
    return U * rho * U.dag()


def _dm(ket: "qt.Qobj") -> "qt.Qobj":
    return ket * ket.dag()


def _initial_dm(root: str) -> "qt.Qobj":
    if root == "root_00":
        return _dm(qt.tensor(qt.basis(2, 0), qt.basis(2, 0)))
    if root == "root_bell":
        psi = (qt.tensor(qt.basis(2, 0), qt.basis(2, 0)) + qt.tensor(qt.basis(2, 1), qt.basis(2, 1))).unit()
        return _dm(psi)
    if root == "root_plus0":
        plus = (qt.basis(2, 0) + qt.basis(2, 1)).unit()
        return _dm(qt.tensor(plus, qt.basis(2, 0)))
    if root == "root_mixed":
        return qt.tensor(qt.qeye(2), qt.qeye(2)) / 4
    raise ValueError(f"unknown root {root!r}")


def _restrict_trace_out_qubit1(rho: "qt.Qobj") -> "qt.Qobj":
    rho0 = rho.ptrace(0)
    return qt.tensor(rho0, qt.qeye(2) / 2)


def _rx(theta: float) -> "qt.Qobj":
    return (-1j * theta / 2 * _SX).expm()


def _perturb(rho: "qt.Qobj") -> "qt.Qobj":
    return _apply_u(rho, _u1(_rx(THETA_SMALL), 0))


def _delay(rho: "qt.Qobj", dt: float) -> "qt.Qobj":
    H = qt.Qobj(np.zeros((4, 4)), dims=[[2, 2], [2, 2]])
    c_ops = [np.sqrt(GAMMA) * _u1(_SP, 0), np.sqrt(GAMMA) * _u1(_SP, 1)]
    result = qt.mesolve(H, rho, [0, dt], c_ops=c_ops)
    return result.states[-1]


def _purity(rho: "qt.Qobj") -> float:
    return (rho * rho).tr().real


def _extend_under_constraint(rho: "qt.Qobj", constraint: str) -> tuple["qt.Qobj", bool]:
    if constraint == "trace_preserving":
        return rho, True  # conserved by construction under every action here -- always admitted
    if constraint == "require_purity":
        return rho, _purity(rho) > PURITY_FLOOR  # state never mutated by the attempt either way
    raise ValueError(f"unknown constraint {constraint!r}")


def _largest_remainder_round(fractions: Sequence[float], total: int) -> list[int]:
    """Deterministic (Hamilton/largest-remainder) rounding: counts always
    sum EXACTLY to `total`, tie-broken by index for full determinism -- no
    unrecorded randomness, matching step_C's purity requirement."""
    fracs = [max(0.0, float(f)) for f in fractions]
    s = sum(fracs)
    if s <= 0:
        base = [0] * len(fracs)
        base[0] = total
        return base
    scaled = [f / s * total for f in fracs]
    floors = [int(np.floor(x)) for x in scaled]
    remainder = total - sum(floors)
    order = sorted(range(len(scaled)), key=lambda i: (-(scaled[i] - floors[i]), i))
    for i in range(remainder):
        floors[order[i]] += 1
    return floors


def _read_outcome_z(rho: "qt.Qobj") -> Outcome:
    diag = np.real(rho.full().diagonal())
    counts = _largest_remainder_round(diag, SHOT_BUDGET)
    labels = ("00", "01", "10", "11")
    return Outcome.table({labels[i]: counts[i] for i in range(4) if counts[i] > 0})


def _read_outcome_x(rho: "qt.Qobj") -> Outcome:
    Hboth = qt.tensor(_H1, _H1)
    rho_x = Hboth * rho * Hboth.dag()  # H1 is Hermitian (H1.dag()==H1) -- order is immaterial here
    diag = np.real(rho_x.full().diagonal())
    counts = _largest_remainder_round(diag, SHOT_BUDGET)
    labels = ("++", "+-", "-+", "--")
    return Outcome.table({labels[i]: counts[i] for i in range(4) if counts[i] > 0})


class SpinorQitExecCandidate(CandidateBridgeInterface):
    """Owner's proposed density-matrix / spinor-flavoured carrier, executed
    on a 2-qubit register. `couple_inner_outer` / `couple_neighbor_neighbor`
    are two structurally different 2-qubit unitaries (CZ vs iSWAP) on the
    SAME fixed register -- real 2-qubit coupling exercised, not a stub;
    genuine cross-shell wiring (a second candidate's state entering THIS
    candidate's nest_context) remains explicitly out of scope, per
    bridge_interface.py's own NestContext docstring."""

    name = "spinor_qit_exec"

    def action_alphabet(self) -> Sequence[Action]:
        return ACTIONS

    def action_category(self, action: Action) -> str:
        return _ACTION_CATEGORY[action]

    def initial_state(self, root):
        return _initial_dm(root)

    def step_C(self, state, action, nest_context: Optional[NestContext] = None):
        rho = state
        if action == "prepare_00":
            return _initial_dm("root_00"), Outcome.deterministic("ack")
        if action == "prepare_bell":
            return _initial_dm("root_bell"), Outcome.deterministic("ack")
        if action == "prepare_plus0":
            return _initial_dm("root_plus0"), Outcome.deterministic("ack")
        if action == "restrict_trace_out_qubit1":
            return _restrict_trace_out_qubit1(rho), Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "ordered_compose":
            names = action[1]
            new_rho = rho
            for nm in names:
                new_rho = _apply_u(new_rho, _GATES[nm])
            return new_rho, Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "bracket_compose":
            _bracket, names = action[1]
            new_rho = rho
            for nm in names:
                new_rho = _apply_u(new_rho, _GATES[nm])
            return new_rho, Outcome.deterministic("ack")
        if action == "perturb_small_rx0":
            return _perturb(rho), Outcome.deterministic("ack")
        if action == "delay_short":
            return _delay(rho, DELAY_SHORT_DT), Outcome.deterministic("ack")
        if action == "delay_long":
            return _delay(rho, DELAY_LONG_DT), Outcome.deterministic("ack")
        if action == "couple_inner_outer":
            return _apply_u(rho, _CZ), Outcome.deterministic("ack")
        if action == "couple_neighbor_neighbor":
            return _apply_u(rho, _ISWAP), Outcome.deterministic("ack")
        if action == "renest_swap01":
            return _apply_u(rho, _SWAP), Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "extend_under_constraint":
            constraint = action[1]
            new_rho, admitted = _extend_under_constraint(rho, constraint)
            return new_rho, Outcome.deterministic("admitted" if admitted else "rejected")
        if action == "read_outcome_z":
            return rho, _read_outcome_z(rho)
        if action == "read_outcome_x":
            return rho, _read_outcome_x(rho)
        raise ValueError(f"unknown action {action!r}")

    # Extra, non-ABC informational method -- see contract.py's PRIMITIVE_VOCABULARY.
    # bridge_interface.CandidateBridgeInterface has no declared_primitives() slot
    # of its own; this is added so practice_run.py's CandidatePackage adapter
    # (which DOES require it) can report an honest, non-fabricated value.
    def declared_primitives(self) -> tuple[str, ...]:
        return ("probability", "time")


if __name__ == "__main__":
    # Small standalone smoke test -- not the practice pipeline itself.
    c = SpinorQitExecCandidate()
    s = c.initial_state("root_bell")
    s, o = c.step_C(s, "read_outcome_z")
    print("root_bell read_outcome_z:", o)
    s2 = c.initial_state("root_00")
    s2, _ = c.step_C(s2, ("ordered_compose", ("H0", "CNOT01")))
    s2, o2 = c.step_C(s2, "read_outcome_z")
    print("root_00 -> H0,CNOT01 -> read_outcome_z:", o2)
    s3 = c.initial_state("root_00")
    s3, _ = c.step_C(s3, ("ordered_compose", ("CNOT01", "H0")))
    s3, o3 = c.step_C(s3, "read_outcome_z")
    print("root_00 -> CNOT01,H0 -> read_outcome_z:", o3)
    print("order-sensitive:", o2 != o3)
