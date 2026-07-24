#!/usr/bin/env python3
"""THE BRIDGE: a QIT engine loop presented to the ratchet as a CandidatePackage.

HOW_THE_ENGINES_RUN_THE_RATCHET.md Part C names this as the key missing
engineering: "engine behavior -> partition -> ratchet input". This file builds
exactly that, and nothing more.

  engine loop  ->  behaviour over a probe family  ->  induced partition pi
               ->  ratchet compares pi's by COARSENING  ->  antichain / purgatory

Two partitions are produced per candidate, deliberately kept separate:
  pi_probe : one-step probe-indistinguishability   (a = a iff a ~ b, one tick)
  pi_basin : same-attractor-in-the-limit           (what the loop converges on)

The basin partition is the ANTI-TELEOLOGICAL readout: the attractor is whatever
survives iteration, never a target the engine aims at.

Math is the doc math, not invented:
  terrains  -- "terrain math.md" Eight Terrain Generators (Type-1 s=+1):
      Se  X = lam*sum_{j=x,y,z} D[sig_j](rho) - i*eps*[H0,rho]      (depolarizing)
      Ne  X = -i[H0,rho]                                            (PURE Hamiltonian)
      Ni  X = gam*D[sig_-](rho) - i*eps*[H0,rho]                    (sink)
      Si  X = -i[w*sig_z,rho] + kap*(P0 rho P0 + P1 rho P1 - rho)   (strata)
    Type-2 flips s -> -1 (so -i[H0,.] -> +i[H0,.]) and sig_- -> sig_+.
  operators -- "operator math explicit.md" the only four:
      Ti  (1-q1)rho + q1(P0 rho P0 + P1 rho P1)      z-dephasing
      Te  (1-q2)rho + q2(Q+ rho Q+ + Q- rho Q-)      x-dephasing
      Fi  U_x(theta) rho U_x(theta)^dag              x-rotation
      Fe  U_z(phi)   rho U_z(phi)^dag                z-rotation
  Axis-6 -- UP = operator first (Phi_T o O); DOWN = terrain first (O o Phi_T).

STATUS: tool_lego_fit_probe. promotion_allowed=false. Loop ORDER is OD-11 OPEN --
this file runs rival orders side by side and never selects one. Rough sim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm

_RC = Path(__file__).resolve().parents[2] / "ratchet_contract"
sys.path.insert(0, str(_RC))
from contract import CandidatePackage, Carrier, NestInterface, NestRef, ControlSet, ControlCase  # noqa: E402

# ---------------------------------------------------------------- fixed matrices
I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
SM = jnp.array([[0, 0], [1, 0]], dtype=jnp.complex128)   # sigma_-
SP = jnp.array([[0, 1], [0, 0]], dtype=jnp.complex128)   # sigma_+
P0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
P1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
QP = 0.5 * (I2 + SX)
QM = 0.5 * (I2 - SX)

NVEC = (0.6, 0.0, 0.8)
H0 = NVEC[0] * SX + NVEC[1] * SY + NVEC[2] * SZ

# declared rates (free parameters of the doc generators)
LAM_SE, EPS_SE = 0.6, 0.9
EPS_NE = 1.0
GAM_NI, EPS_NI = 0.6, 0.9
W_SI, KAP_SI = 0.8, 0.6
TAU = 0.5
Q_TI, Q_TE = 0.5, 0.5
THETA_FI, PHI_FE = 0.7, 0.7

# ------------------------------------------------------- exact Liouvillian flow
def _sup_H(H):
    return -1j * (jnp.kron(H, I2) - jnp.kron(I2, H.T))


def _sup_D(L):
    Ld = L.conj().T
    LdL = Ld @ L
    return jnp.kron(L, L.conj()) - 0.5 * jnp.kron(LdL, I2) - 0.5 * jnp.kron(I2, LdL.T)


def _flow(H_eff, jumps, rho, tau=TAU):
    Ls = _sup_H(H_eff)
    for L in jumps:
        Ls = Ls + _sup_D(L)
    out = (expm(Ls * tau) @ rho.reshape(-1)).reshape(2, 2)
    out = 0.5 * (out + out.conj().T)
    return out / jnp.trace(out).real


def terrain(name, s):
    """Return (H_eff, jumps) for a terrain on sheet sign s (+1 Type-1, -1 Type-2)."""
    if name == "Se":
        j = jnp.sqrt(LAM_SE)
        return s * EPS_SE * H0, [j * SX, j * SY, j * SZ]
    if name == "Ne":
        return s * EPS_NE * H0, []                       # pure Hamiltonian
    if name == "Ni":
        return s * EPS_NI * H0, [jnp.sqrt(GAM_NI) * (SM if s > 0 else SP)]
    if name == "Si":
        return s * W_SI * SZ, [jnp.sqrt(KAP_SI) * P0, jnp.sqrt(KAP_SI) * P1]
    raise ValueError(name)


def operator(name, rho):
    if name == "Ti":
        return (1 - Q_TI) * rho + Q_TI * (P0 @ rho @ P0 + P1 @ rho @ P1)
    if name == "Te":
        return (1 - Q_TE) * rho + Q_TE * (QP @ rho @ QP + QM @ rho @ QM)
    if name == "Fi":
        U = expm(-1j * THETA_FI * SX / 2)
        return U @ rho @ U.conj().T
    if name == "Fe":
        U = expm(-1j * PHI_FE * SZ / 2)
        return U @ rho @ U.conj().T
    if name == "Id":
        return rho
    raise ValueError(name)


def stage(rho, terr, op, arrow, s):
    """Axis-6: UP = operator first (Phi_T o O); DOWN = terrain first (O o Phi_T)."""
    H_eff, jumps = terrain(terr, s)
    if arrow == "UP":
        return _flow(H_eff, jumps, operator(op, rho))
    return operator(op, _flow(H_eff, jumps, rho))


# ------------------------------------------------------------------ state coding
def rho_of(state):
    x, y, z = state
    return 0.5 * (I2 + x * SX + y * SY + z * SZ)


def state_of(rho, res=3):
    x = float(jnp.trace(rho @ SX).real)
    y = float(jnp.trace(rho @ SY).real)
    z = float(jnp.trace(rho @ SZ).real)
    return (round(x, res), round(y, res), round(z, res))


def vn(rho):
    w = jnp.clip(jnp.linalg.eigvalsh(rho).real, 1e-12, 1.0)
    return float(-jnp.sum(w * jnp.log(w)))


def rank0(rho, tol=1e-6):
    """Hartley / Renyi-0 : log2 rank(rho). Support only -- no weights."""
    w = jnp.linalg.eigvalsh(rho).real
    r = int(jnp.sum(w > tol))
    return float(jnp.log2(max(r, 1)))


# -------------------------------------------------------------- the candidate
class EngineCandidate(CandidatePackage):
    """One engine configuration presented to the ratchet.

    schedule : tuple of (terrain, operator, arrow) in visit order
    s        : +1 Type-1 (left Weyl), -1 Type-2 (right Weyl)
    """

    def __init__(self, label, schedule, s=+1, probe_res=2, declared=()):
        self._label = label
        self._schedule = tuple(schedule)
        self._s = s
        self._res = probe_res
        self._declared = tuple(declared)

    @property
    def name(self):
        return self._label

    @property
    def carrier(self):
        return Carrier(
            description="qubit density operator, Bloch-coded finite grid",
            allowed_ops=tuple(f"{t}{o}" for t, o, _ in self._schedule) + ("LOOP",),
        )

    def states(self):
        return tuple(_GRID)

    def probes(self):
        return ("ex", "ey", "ez", "purity", "S1", "S0")

    # ---- dynamics
    def _loop_once(self, rho):
        for terr, op, arrow in self._schedule:
            rho = stage(rho, terr, op, arrow, self._s)
        return rho

    def apply(self, op, state):
        rho = rho_of(state)
        if op == "LOOP":
            return state_of(self._loop_once(rho))
        if op in self.probes():
            return self._probe(op, rho)
        for terr, o, arrow in self._schedule:
            if op == f"{terr}{o}":
                return state_of(stage(rho, terr, o, arrow, self._s))
        raise ValueError(f"unknown op {op}")

    def _probe(self, p, rho):
        if p == "ex":
            return round(float(jnp.trace(rho @ SX).real), self._res)
        if p == "ey":
            return round(float(jnp.trace(rho @ SY).real), self._res)
        if p == "ez":
            return round(float(jnp.trace(rho @ SZ).real), self._res)
        if p == "purity":
            return round(float(jnp.trace(rho @ rho).real), self._res)
        if p == "S1":
            return round(vn(rho), self._res)
        if p == "S0":
            return round(rank0(rho), self._res)
        raise ValueError(p)

    # ---- THE nominalist hook: a = a iff a ~ b, under this candidate's probes,
    #      read AFTER one engine loop (behaviour, not label).
    def reidentify(self, record, current_state):
        try:
            ra = self._loop_once(rho_of(record))
            rb = self._loop_once(rho_of(current_state))
        except Exception:
            return record == current_state
        return all(self._probe(p, ra) == self._probe(p, rb) for p in self.probes())

    # ---- basin: iterate the loop to its fixed point (anti-teleological readout)
    def attractor(self, state, iters=60, tol=1e-9):
        rho = rho_of(state)
        prev = None
        for _ in range(iters):
            rho = self._loop_once(rho)
            cur = state_of(rho, res=6)
            if prev is not None and max(abs(a - b) for a, b in zip(cur, prev)) < tol:
                break
            prev = cur
        return state_of(rho, res=4)

    # ---- continuations
    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        rho = rho_of(state)
        for _ in range(max(delay, 1)):
            rho = self._loop_once(rho)
        return state_of(rho)

    def evolve(self, new_constraint):
        return EngineCandidate(self._label + "+ev", self._schedule, self._s,
                               probe_res=self._res + 1, declared=self._declared)

    def nest_interface(self):
        return NestInterface(inner=NestRef(note="stage-level"), outer=NestRef(note="loop-level"))

    def declared_primitives(self):
        return self._declared

    def controls(self):
        return ControlSet(
            positive=(ControlCase("pure_vs_mixed", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), True),),
            negative=(ControlCase("self_alias", (0.5, 0.0, 0.3), (0.5, 0.0, 0.3), False),),
        )

    # contract extras (unused by the partition path, required by ABC)
    def compile_candidate(self, candidate):
        return candidate

    def run_apply(self, handle, op, state):
        return self.apply(op, state)

    def run_probe_family(self, handle, probes, states):
        return [[self.apply(p, s) for p in probes] for s in states]


# ------------------------------------------------------- observation surface X
def _make_grid():
    pts = []
    for x in (-0.6, -0.2, 0.2, 0.6):
        for z in (-0.6, -0.2, 0.2, 0.6):
            if x * x + z * z <= 1.0:
                pts.append((x, 0.0, z))
    return tuple(pts)


_GRID = _make_grid()
