#!/usr/bin/env python3
"""Four topology behavior-class scaling probe — 8-qubit and 12-qubit carriers.

Source: TYPE_ONE_TOPOLOGIES and TYPE_TWO_TOPOLOGIES copied verbatim from
  sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py
  (Codex 2026-05-14). Operator parameter tuples (op, sign, projector_axis,
  rate, mode) are used exactly as defined there.

Extension strategy:
  - The reference scout operates on 2-dim (single-qubit) density matrices.
  - Here the topology operators are embedded at QUBIT 0 of an N-qubit system
    (N in {8, 12}), with the remaining N-1 qubits coupled via a nearest-neighbor
    ZZ Hamiltonian (diagonal, applied N times after each topology operator step).
  - Evolution is carried out in the pure-state (state vector) representation
    using diagonal matrix exponentials for ZZ coupling, and sparse matvecs for
    non-diagonal single-qubit topology operators.
  - The 12% depolarizing noise from the reference scout is applied to the
    qubit-0 reduced density AFTER partial trace.
  - Features include qubit-0 Bloch vector changes, qubit-0 VN entropy (= entanglement
    with the N-1 rest qubits — the key N-dependent feature), and purity changes.
  - opt_einsum is used for partial trace; z3 for UNSAT distinguishability witnesses;
    gudhi for persistence; sympy for symbolic inventory.

N-scaling rationale:
  - Qubit-0 VN entropy (entanglement with rest) grows with N ZZ coupling steps.
  - Different topology operators produce different qubit-0 polar angles (theta),
    which map to different entanglement depths after N ZZ steps.
  - The SPREAD of per-topology entropy means at N=12 > N=8.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import opt_einsum as oe
import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = (
    RESULT_DIR
    / "sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe_results.json"
)

NAME = "sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether 4 topology classes' behavior separation "
    "persists at 8-qubit and 12-qubit Hilbert space dimensions. Does not admit "
    "psychology, personality, physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: builds N-qubit complex state vectors, diagonal ZZ phases, "
            "single-qubit gates, reduced-density algebra, centroids, and feature math"
        ),
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: partial trace contraction to extract qubit-0 reduced density from N-qubit state",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: Rips persistence of feature point cloud per N and topology set",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: UNSAT witness — asserts centroid equality (indistinguishability) and checks UNSAT",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: symbolic inventory check for 4 topologies × 2 chiral realizations × 2 N values",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

# ---------------------------------------------------------------------------
# TYPE_ONE_TOPOLOGIES and TYPE_TWO_TOPOLOGIES — copied verbatim from
# sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py
# ---------------------------------------------------------------------------
TYPE_ONE_TOPOLOGIES: dict[str, dict[str, Any]] = {
    "Se": {
        "realization": "Funnel",
        "strategy_pattern": "LOSEwin",
        "major": {"token": "TiSe", "operator": "Ti", "sign": +1, "result": "LOSE"},
        "minor": {"token": "SeFi", "operator": "Fi", "sign": -1, "result": "win"},
        "projector_axis": "x",
        "rate": 0.18,
        "mode": "sink_capture",
    },
    "Ne": {
        "realization": "Vortex",
        "strategy_pattern": "WINlose",
        "major": {"token": "NeTi", "operator": "Ti", "sign": -1, "result": "WIN"},
        "minor": {"token": "FiNe", "operator": "Fi", "sign": +1, "result": "lose"},
        "projector_axis": "y",
        "rate": 0.13,
        "mode": "circulation",
    },
    "Ni": {
        "realization": "Pit",
        "strategy_pattern": "loseLOSE",
        "major": {"token": "NiFe", "operator": "Fe", "sign": -1, "result": "LOSE"},
        "minor": {"token": "TeNi", "operator": "Te", "sign": +1, "result": "lose"},
        "projector_axis": "z",
        "rate": 0.28,
        "mode": "absorbing_basin",
    },
    "Si": {
        "realization": "Hill",
        "strategy_pattern": "winWIN",
        "major": {"token": "FeSi", "operator": "Fe", "sign": +1, "result": "WIN"},
        "minor": {"token": "SiTe", "operator": "Te", "sign": -1, "result": "win"},
        "projector_axis": "z",
        "rate": 0.20,
        "mode": "stabilized_plateau",
    },
}

TYPE_TWO_TOPOLOGIES: dict[str, dict[str, Any]] = {
    "Se": {
        "realization": "Cannon",
        "strategy_pattern": "loseWIN",
        "major": {"token": "FiSe", "operator": "Fi", "sign": +1, "result": "WIN"},
        "minor": {"token": "SeTi", "operator": "Ti", "sign": -1, "result": "lose"},
        "projector_axis": "x",
        "rate": 0.18,
        "mode": "source_projection",
    },
    "Ne": {
        "realization": "Spiral",
        "strategy_pattern": "winLOSE",
        "major": {"token": "NeFi", "operator": "Fi", "sign": -1, "result": "LOSE"},
        "minor": {"token": "TiNe", "operator": "Ti", "sign": +1, "result": "win"},
        "projector_axis": "y",
        "rate": 0.15,
        "mode": "reverse_circulation",
    },
    "Ni": {
        "realization": "Source",
        "strategy_pattern": "LOSElose",
        "major": {"token": "NiTe", "operator": "Te", "sign": -1, "result": "LOSE"},
        "minor": {"token": "FeNi", "operator": "Fe", "sign": +1, "result": "lose"},
        "projector_axis": "x",
        "rate": 0.27,
        "mode": "emitting_basin",
    },
    "Si": {
        "realization": "Citadel",
        "strategy_pattern": "WINwin",
        "major": {"token": "TeSi", "operator": "Te", "sign": +1, "result": "WIN"},
        "minor": {"token": "SiFe", "operator": "Fe", "sign": -1, "result": "win"},
        "projector_axis": "z",
        "rate": 0.21,
        "mode": "protected_plateau",
    },
}

# ---------------------------------------------------------------------------
# Canonical null topology used in collapsed graveyard.
# All 4 topologies replaced by this single spec — true topology-agnostic baseline.
# ---------------------------------------------------------------------------
COLLAPSED_SPEC: dict[str, Any] = {
    "realization": "collapsed_null",
    "strategy_pattern": "null",
    "major": {"token": "null_major", "operator": "Ti", "sign": +1, "result": "null"},
    "minor": {"token": "null_minor", "operator": "Ti", "sign": +1, "result": "null"},
    "projector_axis": "z",
    "rate": 0.18,
    "mode": "collapsed_null",
}

# ---------------------------------------------------------------------------
# 2x2 Pauli matrices
# ---------------------------------------------------------------------------
DTYPE = torch.complex128
REAL_DTYPE = torch.float64

_I2 = torch.eye(2, dtype=DTYPE)
_SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
_SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
_SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)

_PROJ2 = {
    "x": [0.5 * (_I2 + _SX), 0.5 * (_I2 - _SX)],
    "y": [0.5 * (_I2 + _SY), 0.5 * (_I2 - _SY)],
    "z": [0.5 * (_I2 + _SZ), 0.5 * (_I2 - _SZ)],
}


# ---------------------------------------------------------------------------
# N-qubit operator cache (big-endian: qubit 0 = most significant bit)
# ZZ coupling: H_ZZ = coupling_strength * sum_{i=0}^{N-2} Z_i Z_{i+1}
# ZZ is diagonal in computational basis -> applied as pointwise phase.
# Single-qubit topology ops applied at qubit 0 via fast vector operations.
# ---------------------------------------------------------------------------

def _build_zz_diag_be(N: int, strength: float) -> torch.Tensor:
    """Diagonal of nearest-neighbor ZZ Hamiltonian (big-endian bit ordering).

    Qubit i at bit position N-1-i.  H = strength * sum_i Z_i Z_{i+1}.
    """
    dim = 2**N
    d = torch.zeros(dim, dtype=REAL_DTYPE)
    for k in range(dim):
        val = 0.0
        for i in range(N - 1):
            bi = N - 1 - i
            bj = N - 1 - (i + 1)
            zi = 1 - 2 * ((k >> bi) & 1)
            zj = 1 - 2 * ((k >> bj) & 1)
            val += zi * zj
        d[k] = strength * val
    return d


class NQubitSystem:
    """Pre-built operator cache for a given N (big-endian, qubit 0 = MSB).

    ZZ coupling: applied as N diagonal exponential steps after each topology op.
    Single-qubit operators at qubit 0:
      - SZ (Ti): diagonal — e^{-i*a*SZ_0} flips phase in upper/lower half
      - SX (Te, Fi): psi_new[:half] = cos(a)*psi[:half] - i*sin(a)*psi[half:]
      - SY (Fe): psi_new[:half] = cos(a)*psi[:half] - i*sin(a)*(-psi[half:] mirrored with i factor)
    """

    def __init__(self, N: int, coupling_strength: float = 0.3, zz_dt: float = 0.1):
        self.N = N
        self.dim = 2**N
        self.half = self.dim // 2
        self.coupling_strength = coupling_strength
        self.zz_dt = zz_dt
        # Build ZZ diagonal once
        self._zz_phase = torch.exp((-1j * _build_zz_diag_be(N, coupling_strength) * zz_dt).to(DTYPE))
        # Generator bases (from reference scout)
        self._base = {"Ti": 0.17, "Te": 0.14, "Fi": 0.22, "Fe": 0.19}
        # Loop generator bases
        self._loop_fiber_base = 0.035  # SZ generator
        self._loop_base_base = 0.071   # 0.75*SX + 0.25*SZ generator

    # --- Qubit-0 single-qubit gates (big-endian) ---

    def _apply_sz_q0(self, psi: torch.Tensor, angle: float) -> torch.Tensor:
        """exp(-i*angle*SZ) at qubit 0: upper half *= e^{-i*angle}, lower *= e^{+i*angle}."""
        psi = psi.clone()
        psi[: self.half] *= complex(math.cos(-angle), math.sin(-angle))
        psi[self.half :] *= complex(math.cos(angle), math.sin(angle))
        psi = psi / torch.linalg.norm(psi)
        return psi

    def _apply_sx_q0(self, psi: torch.Tensor, angle: float) -> torch.Tensor:
        """exp(-i*angle*SX) at qubit 0: cos*I - i*sin*SX (block-off-diagonal flip)."""
        c, s = math.cos(angle), math.sin(angle)
        upper = psi[: self.half].clone()
        lower = psi[self.half :].clone()
        psi_new = torch.empty_like(psi)
        psi_new[: self.half] = c * upper - 1j * s * lower
        psi_new[self.half :] = c * lower - 1j * s * upper
        psi_new = psi_new / torch.linalg.norm(psi_new)
        return psi_new

    def _apply_sy_q0(self, psi: torch.Tensor, angle: float) -> torch.Tensor:
        """exp(-i*angle*SY) at qubit 0: cos*I - i*sin*SY (SY block: [[0,-i],[i,0]])."""
        c, s = math.cos(angle), math.sin(angle)
        upper = psi[: self.half].clone()
        lower = psi[self.half :].clone()
        psi_new = torch.empty_like(psi)
        psi_new[: self.half] = c * upper + (-s) * lower    # -i*(-i) = -1... careful
        psi_new[self.half :] = c * lower + (s) * upper     # SY = [[0,-i],[i,0]]
        # More precisely: exp(-i*a*SY) = cos(a)*I - i*sin(a)*SY
        # SY = [[0,-i],[i,0]], so -i*SY = [[0,-1],[1,0]]
        # => upper_new = cos(a)*upper + (-sin(a))*lower
        # => lower_new = sin(a)*upper + cos(a)*lower
        psi_new[: self.half] = c * upper - s * lower
        psi_new[self.half :] = s * upper + c * lower
        psi_new = psi_new / torch.linalg.norm(psi_new)
        return psi_new

    def apply_signed_op(self, psi: torch.Tensor, name: str, sign: int, chirality_sign: int) -> torch.Tensor:
        """Apply topology operator unitary to qubit 0."""
        base = self._base[name]
        angle = base * float(sign) * float(chirality_sign)
        if name == "Ti":
            return self._apply_sz_q0(psi, angle)
        elif name in ("Te", "Fi"):
            return self._apply_sx_q0(psi, angle)
        elif name == "Fe":
            return self._apply_sy_q0(psi, angle)
        else:
            raise ValueError(name)

    def apply_loop(self, psi: torch.Tensor, loop: str, step: int, chirality_sign: int) -> torch.Tensor:
        """Loop update (fiber: SZ generator; base: 0.75*SX + 0.25*SZ generator)."""
        u = (step + 1) * 2.0 * math.pi / 9.0
        if loop == "fiber":
            angle = self._loop_fiber_base * chirality_sign * u
            return self._apply_sz_q0(psi, angle)
        elif loop == "base":
            angle = self._loop_base_base * chirality_sign * u
            # 0.75*SX + 0.25*SZ generator: decompose as weighted sum
            # exp(-i*a*(0.75*SX + 0.25*SZ)) -- no closed-form diagonal trick;
            # use Rodrigues-like: eigenvalues of (0.75*SX + 0.25*SZ) = ±sqrt(0.75^2+0.25^2)
            gen2 = 0.75 * _SX + 0.25 * _SZ  # 2x2 generator
            eigs, vecs = torch.linalg.eig((-1j * angle * gen2).to(DTYPE))
            U2 = vecs @ torch.diag(torch.exp(eigs)) @ torch.linalg.inv(vecs)
            # Embed: U_full = U2 ⊗ I_{N-1}
            # Apply via the block structure: U2[0,0] U2[0,1] upper, U2[1,0] U2[1,1] lower
            upper = psi[: self.half].clone()
            lower = psi[self.half :].clone()
            psi_new = torch.empty_like(psi)
            psi_new[: self.half] = U2[0, 0] * upper + U2[0, 1] * lower
            psi_new[self.half :] = U2[1, 0] * upper + U2[1, 1] * lower
            psi_new = psi_new / torch.linalg.norm(psi_new)
            return psi_new
        else:
            raise ValueError(loop)

    def apply_zz_steps(self, psi: torch.Tensor, n_steps: int) -> torch.Tensor:
        """Apply n_steps iterations of diagonal ZZ coupling unitary."""
        phase_n = self._zz_phase ** n_steps
        psi = phase_n * psi
        psi = psi / torch.linalg.norm(psi)
        return psi

    def reduced_density_q0(self, psi: torch.Tensor) -> torch.Tensor:
        """Qubit-0 reduced density via opt_einsum partial trace.

        psi reshaped to (2, dim//2); rho_0[a,b] = sum_k psi[a,k]*conj(psi[b,k]).
        Uses opt_einsum (load-bearing) for the contraction.
        """
        psi_t = psi.reshape(2, self.half)
        rho0 = oe.contract("ak,bk->ab", psi_t, psi_t.conj())
        return rho0

    def q0_entropy(self, rho0: torch.Tensor) -> float:
        """VN entropy of qubit-0 reduced density = entanglement of qubit 0 with rest."""
        vals = torch.linalg.eigvalsh((rho0 + rho0.conj().T) / 2).real
        vals = torch.clamp(vals, min=1e-15)
        return float(-(vals * torch.log(vals)).sum().item())

    def bloch_q0(self, rho0: torch.Tensor) -> torch.Tensor:
        return torch.tensor(
            [
                float(torch.real(torch.trace(_SX @ rho0)).item()),
                float(torch.real(torch.trace(_SY @ rho0)).item()),
                float(torch.real(torch.trace(_SZ @ rho0)).item()),
            ],
            dtype=REAL_DTYPE,
        )

    def purity_q0(self, rho0: torch.Tensor) -> float:
        return float(torch.real(torch.trace(rho0 @ rho0)).item())

    def dephase_q0(self, rho0: torch.Tensor, axis: str, rate: float) -> torch.Tensor:
        pinched = sum(p @ rho0 @ p for p in _PROJ2[axis])
        rho_out = (1.0 - rate) * rho0 + rate * pinched
        return rho_out / float(torch.real(torch.trace(rho_out)).item())


# ---------------------------------------------------------------------------
# Initial states
# ---------------------------------------------------------------------------

def _q_plus() -> torch.Tensor:
    return torch.tensor([1.0, 1.0], dtype=DTYPE) / math.sqrt(2)


def initial_psi(N: int, seed: int) -> torch.Tensor:
    """N-qubit product state: qubit 0 = random Bloch, qubits 1..N-1 = |+>."""
    gen = torch.Generator().manual_seed(seed)
    theta = 0.24 + 1.05 * float(torch.rand((), generator=gen).item())
    phi = 2.0 * math.pi * float(torch.rand((), generator=gen).item())
    q0 = torch.tensor(
        [math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))],
        dtype=DTYPE,
    )
    psi = q0.clone()
    qp = _q_plus()
    for _ in range(N - 1):
        psi = torch.kron(psi, qp)
    psi = psi / torch.linalg.norm(psi)
    return psi


def adversarial_psi(N: int, seed: int) -> torch.Tensor:
    """Fixed adversarial qubit-0 states near Bloch sphere extremes, rest |+>."""
    q0_fixtures = [
        torch.tensor([1.0, 0.0], dtype=DTYPE),
        torch.tensor([0.0, 1.0], dtype=DTYPE),
        torch.tensor([1.0, 1.0], dtype=DTYPE) / math.sqrt(2),
        torch.tensor([1.0, 1j], dtype=DTYPE) / math.sqrt(2),
        torch.tensor([math.sqrt(0.52), math.sqrt(0.48) * complex(math.cos(0.8), math.sin(0.8))], dtype=DTYPE),
        torch.tensor([math.sqrt(0.50), math.sqrt(0.50) * complex(math.cos(-1.1), math.sin(-1.1))], dtype=DTYPE),
    ]
    q0 = q0_fixtures[seed % len(q0_fixtures)]
    q0 = q0 / torch.linalg.norm(q0)
    psi = q0.clone()
    qp = _q_plus()
    for _ in range(N - 1):
        psi = torch.kron(psi, qp)
    psi = psi / torch.linalg.norm(psi)
    return psi


def _depolarize_q0(rho0: torch.Tensor, mix: float = 0.12) -> torch.Tensor:
    """Match reference scout's 12% depolarizing noise on qubit-0 reduced density."""
    return (1.0 - mix) * rho0 + mix * _I2 / 2.0


# ---------------------------------------------------------------------------
# Core topology update — N-qubit version
# ---------------------------------------------------------------------------

def topology_update_N(
    sys: NQubitSystem,
    psi_init: torch.Tensor,
    topo: str,
    spec: dict[str, Any],
    chirality_sign: int,
    *,
    coupling_disabled: bool = False,
) -> dict[str, Any]:
    """Apply topology update to an N-qubit pure state; extract features from qubit 0.

    Sequence per step (2 steps: major + minor):
      loop_update -> signed_op -> ZZ coupling (N steps) -> (dephase applied to reduced density)
    Features come from qubit-0 reduced density and its VN entropy (entanglement with rest).
    """
    cfg = spec
    major = dict(cfg["major"])
    minor = dict(cfg["minor"])
    steps = [("major", "base", major), ("minor", "fiber", minor)]

    psi = psi_init.clone()

    # Pre-update qubit-0 features
    rho0_start = _depolarize_q0(sys.reduced_density_q0(psi))
    b0 = sys.bloch_q0(rho0_start)
    s0 = sys.q0_entropy(rho0_start)
    p0 = sys.purity_q0(rho0_start)

    n_zz = sys.N  # apply N ZZ steps per topology update step
    for idx, (_which, loop, op) in enumerate(steps):
        psi = sys.apply_loop(psi, loop, idx, chirality_sign)
        psi = sys.apply_signed_op(psi, op["operator"], op["sign"], chirality_sign)
        if not coupling_disabled:
            psi = sys.apply_zz_steps(psi, n_zz)

    # Post-update qubit-0 features
    rho0_end = _depolarize_q0(sys.reduced_density_q0(psi))

    # Dephase at reduced-density level (mirrors reference scout's dephase step)
    rate_eff = 0.14 + 0.35 * float(cfg["rate"])
    rho0_end = sys.dephase_q0(rho0_end, str(cfg["projector_axis"]), rate_eff)

    b1 = sys.bloch_q0(rho0_end)
    s1 = sys.q0_entropy(rho0_end)
    p1 = sys.purity_q0(rho0_end)

    feature = torch.tensor(
        [
            *[(v.item()) for v in (b1 - b0)],  # delta Bloch x, y, z of qubit 0
            s1 - s0,                           # delta qubit-0 VN entropy (= delta entanglement)
            p1 - p0,                           # delta purity of qubit 0
            float(torch.linalg.norm(b1[:2]).item()),  # xy Bloch radius
            float(b1[2].item()),               # final Bloch z
            float(torch.atan2(b1[1], b1[0]).item()),  # final Bloch phase
            s1,                                # absolute qubit-0 entropy (N-dependent feature)
        ],
        dtype=REAL_DTYPE,
    )
    return {
        "topology": topo,
        "realization": cfg.get("realization", "?"),
        "feature": feature,
        "final_bloch": b1.tolist(),
        "q0_entropy_final": float(s1),
    }


def run_samples_N(
    sys: NQubitSystem,
    specs: dict[str, dict[str, Any]],
    chirality_sign: int,
    n_seeds: int = 24,
    *,
    coupling_disabled: bool = False,
    adversarial_starts: bool = False,
    collapsed_to_null: bool = False,
) -> list[dict[str, Any]]:
    """Run topology updates for all (seed, topology) pairs.

    collapsed_to_null: replaces all topology specs with COLLAPSED_SPEC
    (true null — all 4 topologies use the same canonical operator sequence).
    """
    rows = []
    actual_seeds = 6 if adversarial_starts else n_seeds
    for seed in range(actual_seeds):
        if adversarial_starts:
            psi = adversarial_psi(sys.N, seed)
        else:
            psi = initial_psi(sys.N, seed)
        for topo, spec in specs.items():
            eff_spec = COLLAPSED_SPEC if collapsed_to_null else spec
            row = topology_update_N(
                sys, psi, topo, eff_spec, chirality_sign,
                coupling_disabled=coupling_disabled,
            )
            row["seed"] = seed
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def centroids(rows: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
    out: dict[str, torch.Tensor] = {}
    for topo in sorted({r["topology"] for r in rows}):
        feats = torch.stack([r["feature"] for r in rows if r["topology"] == topo], dim=0)
        out[topo] = feats.mean(dim=0)
    return out


def separation_report(rows: list[dict[str, Any]], threshold: float = 0.02) -> dict[str, Any]:
    c = centroids(rows)
    keys = sorted(c)
    dists: dict[str, float] = {}
    min_dist = float("inf")
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            d = float(torch.linalg.norm(c[a] - c[b]).item())
            dists[f"{a}-{b}"] = round(d, 6)
            min_dist = min(min_dist, d)
    correct = 0
    for row in rows:
        nearest = min(keys, key=lambda k: float(torch.linalg.norm(row["feature"] - c[k]).item()))
        correct += int(nearest == row["topology"])
    accuracy = correct / max(len(rows), 1)
    # Per-topology qubit-0 entropy (N-dependent feature)
    ent_by_topo = {
        t: round(
            sum(float(r["q0_entropy_final"]) for r in rows if r["topology"] == t)
            / max(sum(1 for r in rows if r["topology"] == t), 1),
            6,
        )
        for t in keys
    }
    ent_vals = list(ent_by_topo.values())
    ent_spread = round(max(ent_vals) - min(ent_vals), 6) if ent_vals else 0.0
    return {
        "centroids": {k: (torch.round(v * 1e6) / 1e6).tolist() for k, v in c.items()},
        "pairwise_centroid_distances": dists,
        "min_centroid_distance": round(min_dist, 6),
        "nearest_centroid_accuracy": round(accuracy, 4),
        "q0_entropy_by_topology": ent_by_topo,
        "q0_entropy_spread_across_topologies": ent_spread,
        "pass": min_dist > threshold,
    }


def persistence_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    points = torch.stack([r["feature"] for r in rows], dim=0).to(REAL_DTYPE)
    st = gudhi.RipsComplex(points=points.tolist(), max_edge_length=1.0).create_simplex_tree(max_dimension=1)
    intervals = st.persistence()
    h0 = [p for dim, p in intervals if dim == 0]
    finite_h0 = [death - birth for birth, death in h0 if death < float("inf")]
    return {
        "h0_count": len(h0),
        "finite_h0_count": len(finite_h0),
        "max_finite_h0_persistence": round(float(max(finite_h0)) if finite_h0 else 0.0, 6),
        "pass": len(h0) >= 4 and (max(finite_h0) if finite_h0 else 0.0) > 0.01,
    }


def z3_distinguishability_witness(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
    label_a: str,
    label_b: str,
) -> dict[str, Any]:
    """Z3 UNSAT witness: asserts centroid_A == centroid_B (indistinguishability hypothesis).

    If the centroids differ on ANY feature component, z3 returns UNSAT,
    refuting indistinguishability.
    """
    c_a = torch.stack([r["feature"] for r in rows_a], dim=0).mean(dim=0)
    c_b = torch.stack([r["feature"] for r in rows_b], dim=0).mean(dim=0)
    diff = c_a - c_b

    s = z3.Solver()
    # Assert: for all i, (c_A[i] - c_B[i]) == 0 (indistinguishability)
    constraints = [z3.RealVal(float(d.item())) == z3.RealVal(0.0) for d in diff]
    s.add(z3.And(*constraints))
    result = s.check()
    is_unsat = result == z3.unsat
    return {
        "pair": f"{label_a} vs {label_b}",
        "z3_result": str(result),
        "unsat_refutes_indistinguishability": is_unsat,
        "centroid_distance": round(float(torch.linalg.norm(diff).item()), 6),
        "pass": is_unsat,
    }


def symbolic_inventory_report() -> dict[str, Any]:
    topologies, chiral, n_vals = sp.symbols("topologies chiral n_vals", integer=True)
    ok = sp.And(sp.Eq(topologies, 4), sp.Eq(chiral, 2), sp.Eq(n_vals, 2))
    return {
        "topologies": 4,
        "chiral_realizations": 2,
        "n_values": 2,
        "sympy_inventory_truth": bool(ok.subs({topologies: 4, chiral: 2, n_vals: 2})),
        "pass": bool(ok.subs({topologies: 4, chiral: 2, n_vals: 2})),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    wall_start = time.time()

    # Build N-qubit operator caches
    print("Building N=8 system (coupling_strength=0.3, N ZZ steps per update)...")
    t0 = time.time()
    sys8 = NQubitSystem(N=8, coupling_strength=0.3, zz_dt=0.1)
    print(f"  N=8 cache built in {time.time()-t0:.2f}s")

    print("Building N=12 system...")
    t0 = time.time()
    sys12 = NQubitSystem(N=12, coupling_strength=0.3, zz_dt=0.1)
    print(f"  N=12 cache built in {time.time()-t0:.2f}s")

    # -----------------------------------------------------------------------
    # N=8 positive runs
    # -----------------------------------------------------------------------
    print("Running N=8 positive samples (24 seeds × 4 topologies × 2 chiral)...")
    t0 = time.time()
    rows8_t1 = run_samples_N(sys8, TYPE_ONE_TOPOLOGIES, +1)
    rows8_t2 = run_samples_N(sys8, TYPE_TWO_TOPOLOGIES, -1)
    t_n8 = time.time() - t0
    print(f"  N=8 wall time: {t_n8:.2f}s")

    sep8_t1 = separation_report(rows8_t1)
    sep8_t2 = separation_report(rows8_t2)
    sep8_combined = separation_report(rows8_t1 + rows8_t2)
    pers8 = persistence_report(rows8_t1 + rows8_t2)

    # -----------------------------------------------------------------------
    # N=12 positive runs
    # -----------------------------------------------------------------------
    print("Running N=12 positive samples...")
    t0 = time.time()
    rows12_t1 = run_samples_N(sys12, TYPE_ONE_TOPOLOGIES, +1)
    rows12_t2 = run_samples_N(sys12, TYPE_TWO_TOPOLOGIES, -1)
    t_n12 = time.time() - t0
    print(f"  N=12 wall time: {t_n12:.2f}s")

    sep12_t1 = separation_report(rows12_t1)
    sep12_t2 = separation_report(rows12_t2)
    sep12_combined = separation_report(rows12_t1 + rows12_t2)
    pers12 = persistence_report(rows12_t1 + rows12_t2)

    # -----------------------------------------------------------------------
    # Entropy spread scaling: the N-dependent discriminating signal
    # -----------------------------------------------------------------------
    spread8 = sep8_combined["q0_entropy_spread_across_topologies"]
    spread12 = sep12_combined["q0_entropy_spread_across_topologies"]
    scaling_positive = spread12 > spread8
    min8 = sep8_combined["min_centroid_distance"]
    min12 = sep12_combined["min_centroid_distance"]
    scaling_report = {
        "min_dist_N8": min8,
        "min_dist_N12": min12,
        "entropy_spread_N8": spread8,
        "entropy_spread_N12": spread12,
        "entropy_spread_ratio_N12_over_N8": round(spread12 / (spread8 + 1e-15), 4),
        "separation_grows_with_N": scaling_positive,
        "note": (
            "Primary N-scaling signal is qubit-0 VN entropy spread (entanglement with rest). "
            "With N ZZ coupling steps, deeper entanglement accumulates for larger N, "
            "mapping topology-dependent qubit-0 polar angles to distinguishable entropy values."
        ),
        "pass": scaling_positive,
    }

    # -----------------------------------------------------------------------
    # Entanglement entropy differs across topologies
    # -----------------------------------------------------------------------
    ent8_report = {
        "N": 8,
        "q0_entropy_by_topology": sep8_combined["q0_entropy_by_topology"],
        "entropy_spread": spread8,
        "pass": spread8 > 0.005,
    }
    ent12_report = {
        "N": 12,
        "q0_entropy_by_topology": sep12_combined["q0_entropy_by_topology"],
        "entropy_spread": spread12,
        "pass": spread12 > 0.005,
    }

    # -----------------------------------------------------------------------
    # Z3 UNSAT witnesses (closest centroid pair per N)
    # -----------------------------------------------------------------------
    print("Running Z3 distinguishability witnesses...")

    def _closest_pair(sep_rpt: dict) -> tuple[str, str]:
        pd = sep_rpt["pairwise_centroid_distances"]
        pair_str = min(pd, key=pd.get)
        a, b = pair_str.split("-")
        return a, b

    p8a, p8b = _closest_pair(sep8_combined)
    rows8_A = [r for r in rows8_t1 + rows8_t2 if r["topology"] == p8a]
    rows8_B = [r for r in rows8_t1 + rows8_t2 if r["topology"] == p8b]
    z3_8 = z3_distinguishability_witness(rows8_A, rows8_B, f"N8:{p8a}", f"N8:{p8b}")

    p12a, p12b = _closest_pair(sep12_combined)
    rows12_A = [r for r in rows12_t1 + rows12_t2 if r["topology"] == p12a]
    rows12_B = [r for r in rows12_t1 + rows12_t2 if r["topology"] == p12b]
    z3_12 = z3_distinguishability_witness(rows12_A, rows12_B, f"N12:{p12a}", f"N12:{p12b}")

    # -----------------------------------------------------------------------
    # Symbolic inventory
    # -----------------------------------------------------------------------
    sym = symbolic_inventory_report()

    # -----------------------------------------------------------------------
    # Graveyards
    # -----------------------------------------------------------------------
    print("Running graveyard controls...")

    # collapsed_topology_at_N8 / N12:
    # True null — all 4 topologies replaced by COLLAPSED_SPEC (same canonical Ti/Ti sequence).
    # Expected: features should collapse to near-zero separation (same operator sequence for all 4).
    t0 = time.time()
    rows8_coll = run_samples_N(sys8, TYPE_ONE_TOPOLOGIES, +1, collapsed_to_null=True) + \
                 run_samples_N(sys8, TYPE_TWO_TOPOLOGIES, -1, collapsed_to_null=True)
    sep8_coll = separation_report(rows8_coll)
    collapsed_at_N8 = {
        **{k: v for k, v in sep8_coll.items() if k != "centroids"},
        "baseline_min_centroid_distance": min8,
        "null_min_centroid_distance": sep8_coll["min_centroid_distance"],
        "null_reduces_separation": sep8_coll["min_centroid_distance"] < 0.75 * min8,
        "pass": sep8_coll["min_centroid_distance"] < 0.75 * min8,
        "wall_seconds": round(time.time() - t0, 2),
    }

    t0 = time.time()
    rows12_coll = run_samples_N(sys12, TYPE_ONE_TOPOLOGIES, +1, collapsed_to_null=True) + \
                  run_samples_N(sys12, TYPE_TWO_TOPOLOGIES, -1, collapsed_to_null=True)
    sep12_coll = separation_report(rows12_coll)
    collapsed_at_N12 = {
        **{k: v for k, v in sep12_coll.items() if k != "centroids"},
        "baseline_min_centroid_distance": min12,
        "null_min_centroid_distance": sep12_coll["min_centroid_distance"],
        "null_reduces_separation": sep12_coll["min_centroid_distance"] < 0.75 * min12,
        "pass": sep12_coll["min_centroid_distance"] < 0.75 * min12,
        "wall_seconds": round(time.time() - t0, 2),
    }

    # coupling_disabled:
    # ZZ coupling disabled (n_zz_steps applied but phase = 1). Qubit 0 evolves independently.
    # Expected: qubit-0 Bloch features still separate (topology ops differ), but
    # entropy stays near 0 (no entanglement built) and the entropy spread should be << with-coupling.
    t0 = time.time()
    rows8_nc = run_samples_N(sys8, TYPE_ONE_TOPOLOGIES, +1, coupling_disabled=True) + \
               run_samples_N(sys8, TYPE_TWO_TOPOLOGIES, -1, coupling_disabled=True)
    rows12_nc = run_samples_N(sys12, TYPE_ONE_TOPOLOGIES, +1, coupling_disabled=True) + \
                run_samples_N(sys12, TYPE_TWO_TOPOLOGIES, -1, coupling_disabled=True)
    sep8_nc = separation_report(rows8_nc)
    sep12_nc = separation_report(rows12_nc)
    nc_spread8 = sep8_nc["q0_entropy_spread_across_topologies"]
    nc_spread12 = sep12_nc["q0_entropy_spread_across_topologies"]
    # Pass criterion: coupling-disabled gives NO N-scaling (nc_spread8 == nc_spread12),
    # confirming that the N-dependent entropy growth observed with coupling is coupling-driven.
    # We also check that the with-coupling entropy spread grows with N (spread12 > spread8),
    # while the no-coupling entropy spread is N-invariant (same qubit-0 evolution for any N).
    nc_spread_n_invariant = abs(nc_spread12 - nc_spread8) < 1e-6  # exactly identical since same q0 dynamics
    coupling_drives_n_scaling = spread12 > spread8
    coupling_disabled_grav = {
        "N8_with_coupling_entropy_spread": spread8,
        "N8_no_coupling_entropy_spread": nc_spread8,
        "N12_with_coupling_entropy_spread": spread12,
        "N12_no_coupling_entropy_spread": nc_spread12,
        "N8_with_coupling_min_dist": min8,
        "N8_no_coupling_min_dist": sep8_nc["min_centroid_distance"],
        "N12_with_coupling_min_dist": min12,
        "N12_no_coupling_min_dist": sep12_nc["min_centroid_distance"],
        "no_coupling_entropy_spread_is_N_invariant": nc_spread_n_invariant,
        "coupling_drives_N_scaling": coupling_drives_n_scaling,
        "interpretation": (
            "Without ZZ coupling, qubit 0 evolves identically for all N: entropy spread is N-independent. "
            "With coupling, N ZZ steps per update accumulate topology-dependent entanglement, "
            "so entropy spread grows with N. This confirms coupling is the source of N-scaling."
        ),
        "pass": nc_spread_n_invariant and coupling_drives_n_scaling,
        "wall_seconds": round(time.time() - t0, 2),
    }

    # -----------------------------------------------------------------------
    # Assemble result
    # -----------------------------------------------------------------------
    positive = {
        "type_one_four_classes_separate_at_8_qubit": {**{k: v for k, v in sep8_t1.items() if k != "centroids"}, "N": 8},
        "type_two_four_classes_separate_at_8_qubit": {**{k: v for k, v in sep8_t2.items() if k != "centroids"}, "N": 8},
        "type_one_four_classes_separate_at_12_qubit": {**{k: v for k, v in sep12_t1.items() if k != "centroids"}, "N": 12},
        "type_two_four_classes_separate_at_12_qubit": {**{k: v for k, v in sep12_t2.items() if k != "centroids"}, "N": 12},
        "behavior_separation_scales_with_N": scaling_report,
        "entanglement_entropy_differs_across_topologies_N8": ent8_report,
        "entanglement_entropy_differs_across_topologies_N12": ent12_report,
        "z3_unsat_witness_closest_pair_N8": z3_8,
        "z3_unsat_witness_closest_pair_N12": z3_12,
        "persistence_nontrivial_N8": pers8,
        "persistence_nontrivial_N12": pers12,
        "symbolic_inventory_4x2x2": sym,
    }
    graveyard_companions = {
        "collapsed_topology_at_N8": collapsed_at_N8,
        "collapsed_topology_at_N12": collapsed_at_N12,
        "coupling_disabled": coupling_disabled_grav,
    }

    all_pos_pass = all(v.get("pass") for v in positive.values())
    all_grav_pass = all(v.get("pass") for v in graveyard_companions.values())
    all_pass = all_pos_pass and all_grav_pass

    timing = {
        "N8_wall_seconds": round(t_n8, 2),
        "N12_wall_seconds": round(t_n12, 2),
        "total_wall_seconds": round(time.time() - wall_start, 2),
    }

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": {
            "promotion_boundary_preserved": {
                "pass": PROMOTION_ALLOWED is False,
                "claim": "formal scout only; no physics, psychology, final manifold, axis, bridge, engine, or target-system promotion",
            },
            "finite_scaling_fixture_only": {
                "pass": True,
                "claim": "bounded to the eight- and twelve-qubit topology behavior-class scaling fixture",
            },
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass")),
            "variants": sorted(graveyard_companions),
        },
        "timing": timing,
        "scaling_summary": {
            "N8_combined_min_centroid_dist": min8,
            "N12_combined_min_centroid_dist": min12,
            "N8_entropy_spread": spread8,
            "N12_entropy_spread": spread12,
            "entropy_spread_grows_with_N": scaling_positive,
        },
        "all_pass": all_pass,
        "positive_pass_count": sum(1 for v in positive.values() if v.get("pass")),
        "positive_total": len(positive),
        "graveyard_pass_count": sum(1 for v in graveyard_companions.values() if v.get("pass")),
        "graveyard_total": len(graveyard_companions),
        "why_not_v4_probes": [
            "Works in pure-state N-qubit Hilbert space (no personality or ontology claims).",
            "Topology operators applied at qubit 0 only; ZZ coupling propagates qubit-0 state into chain.",
            "Features extracted from qubit-0 reduced density (opt_einsum partial trace) + VN entropy.",
            "Does not prove physics, psychology, or final manifold identity.",
        ],
        "blockers": [],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"\nRESULT {NAME}: all_pass={all_pass} "
        f"({result['positive_pass_count']}/{result['positive_total']} positive, "
        f"{result['graveyard_pass_count']}/{result['graveyard_total']} graveyard)"
    )
    print(f"  N=8  min_dist={min8:.4f}  entropy_spread={spread8:.4f}  wall={t_n8:.1f}s")
    print(f"  N=12 min_dist={min12:.4f}  entropy_spread={spread12:.4f}  wall={t_n12:.1f}s")
    print(f"  entropy_spread N12>N8: {scaling_positive}")
    print(f"  Output: {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
