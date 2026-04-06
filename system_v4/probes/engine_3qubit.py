#!/usr/bin/env python3
"""
engine_3qubit.py
================

3-Qubit Geometric Engine extension for Axis 0 I_c breakthrough.

Wraps the 2-qubit GeometricEngine, extending its operator algebra to an
8x8 (d=8) Hilbert space.  The key structural innovation: Fi acts across
the 1|23 partition (X on qubit 1, Z on qubit 3), which is an entangling
gate that can earn I_c > 0 from separable initial states -- impossible
in the 2-qubit engine where all operators act within the same partition.

Operator Algebra (8x8):
  Ti_3q : Z x Z x I   dephasing   (acts on q1,q2; q3 untouched)
  Fe_3q : X x X x I   rotation    (acts on q1,q2; q3 untouched)
  Te_3q : Y x Y x I   dephasing   (acts on q1,q2; q3 untouched)
  Fi_3q : X x I x Z   rotation    (crosses 1|23 partition -- THE KEY)

Dephasing ops (Ti, Te): projector-based CPTP channels
Rotation ops  (Fe, Fi): unitary U = cos(t/2)I - i sin(t/2) H_int
"""

import sys
import os
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, TERRAINS, STAGE_OPERATOR_LUT,
    LOOP_STAGE_ORDER, LOOP_GRAMMAR,
)
from geometric_operators import SIGMA_X, SIGMA_Y, SIGMA_Z, I2
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER, torus_radii


# =====================================================================
# PARTIAL TRACE (proven implementation from sim_3qubit_bridge_prototype)
# =====================================================================

def partial_trace_keep(rho: np.ndarray, keep: list, dims: list) -> np.ndarray:
    """Partial trace: keep subsystems in 'keep', trace out the rest.

    dims = list of subsystem dimensions, e.g. [2,2,2] for 3 qubits.
    Uses the reshape-and-trace approach.
    """
    n = len(dims)
    rho_r = rho.reshape(dims + dims)
    trace_out = sorted([i for i in range(n) if i not in keep], reverse=True)
    current_n = n
    for i in trace_out:
        rho_r = np.trace(rho_r, axis1=i, axis2=i + current_n)
        current_n -= 1
    d_keep = int(np.prod([dims[i] for i in keep]))
    return rho_r.reshape(d_keep, d_keep)


def von_neumann_entropy(rho: np.ndarray) -> float:
    """Von Neumann entropy S(rho) = -Tr(rho log2 rho), in bits."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))


def ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    """Force Hermiticity, positivity, trace=1."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho /= tr
    else:
        d = rho.shape[0]
        rho = np.eye(d, dtype=complex) / d
    return rho


# =====================================================================
# 3-QUBIT OPERATORS (8x8)
# =====================================================================

def build_3q_Ti(strength: float = 1.0):
    """Ti: Z x Z x I dephasing (Luders projection on q1,q2, q3 untouched)."""
    ZZ_I = np.kron(np.kron(SIGMA_Z, SIGMA_Z), I2)
    P0 = (np.eye(8, dtype=complex) + ZZ_I) / 2
    P1 = (np.eye(8, dtype=complex) - ZZ_I) / 2

    def apply(rho, polarity_up=True):
        mix = strength if polarity_up else 0.3 * strength
        rho_proj = P0 @ rho @ P0 + P1 @ rho @ P1
        return ensure_valid_density(mix * rho_proj + (1 - mix) * rho)
    return apply


def build_3q_Fe(strength: float = 1.0, phi: float = 0.4):
    """Fe: X x X x I rotation (unitary on q1,q2, q3 untouched)."""
    H_int = np.kron(np.kron(SIGMA_X, SIGMA_X), I2)

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * phi * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        return ensure_valid_density(U @ rho @ U.conj().T)
    return apply


def build_3q_Te(strength: float = 1.0, q: float = 0.7):
    """Te: Y x Y x I dephasing (Luders projection on q1,q2, q3 untouched)."""
    YY_I = np.kron(np.kron(SIGMA_Y, SIGMA_Y), I2)
    P_plus = (np.eye(8, dtype=complex) + YY_I) / 2
    P_minus = (np.eye(8, dtype=complex) - YY_I) / 2

    def apply(rho, polarity_up=True):
        mix = min(strength * (q if polarity_up else 0.3 * q), 1.0)
        rho_proj = P_plus @ rho @ P_plus + P_minus @ rho @ P_minus
        return ensure_valid_density((1 - mix) * rho + mix * rho_proj)
    return apply


def build_3q_Fi(strength: float = 1.0, theta: float = 0.4):
    """Fi: X x I x Z rotation -- CROSSES the 1|23 partition.

    H_int = sigma_X(q1) tensor I(q2) tensor sigma_Z(q3).
    This is the entangling gate that earns I_c > 0 from separable states.
    """
    H_int = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * theta * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        return ensure_valid_density(U @ rho @ U.conj().T)
    return apply


def build_3q_XX23(strength: float = 1.0, theta: float = 0.4):
    """XX_23: I x X x X rotation -- bridges cut2 (12|3) via XX on q2,q3.

    H_int = I(q1) tensor sigma_X(q2) tensor sigma_X(q3).
    This is the auxiliary relay operator that makes all 3 bipartition
    cuts simultaneously positive: base-aligned, relays base->environment.
    Strength scaled by R_major (base-aligned like Fi).
    """
    H_int = np.kron(I2, np.kron(SIGMA_X, SIGMA_X))

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * theta * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        return ensure_valid_density(U @ rho @ U.conj().T)
    return apply


# Operator builder registry, keyed by 2q operator name
_3Q_BUILDER = {
    "Ti": build_3q_Ti,
    "Fe": build_3q_Fe,
    "XX23": build_3q_XX23,
    "Te": build_3q_Te,
    "Fi": build_3q_Fi,
}


# =====================================================================
# BIPARTITIONS
# =====================================================================

BIPARTITIONS_3Q = {
    "1vs23": {"A": [0], "B": [1, 2], "label": "q1 | q2q3"},
    "12vs3": {"A": [0, 1], "B": [2], "label": "q1q2 | q3"},
    "13vs2": {"A": [0, 2], "B": [1], "label": "q1q3 | q2"},
}


# =====================================================================
# ENGINE STATE (3-qubit)
# =====================================================================

@dataclass
class EngineState3Q:
    """Complete state of the 3-qubit engine."""
    rho_ABC: np.ndarray        # 8x8 joint density matrix (3 qubits)
    eta: float                 # current torus latitude
    theta1: float              # angle on first circle
    theta2: float              # angle on second circle
    stage_idx: int = 0
    engine_type: int = 1
    history: list = field(default_factory=list)


# =====================================================================
# 3-QUBIT GEOMETRIC ENGINE
# =====================================================================

class GeometricEngine3Q:
    """3-qubit extension of the GeometricEngine.

    Wraps the 2-qubit engine's loop grammar and stage ordering, but
    applies 8x8 operators that include cross-partition Fi.

    Each cycle follows LOOP_STAGE_ORDER for the engine type.
    After each stage, I_c is computed for the 1vs23 cut and stored
    in the state history.
    """

    def __init__(self, engine_type: int = 1,
                 dephasing_strength: float = 0.05,
                 fi_theta: float = 0.4,
                 eta: float = None):
        assert engine_type in (1, 2), "engine_type must be 1 or 2"
        self.engine_type = engine_type
        self.dephasing_strength = dephasing_strength
        self.fi_theta = fi_theta
        self.loop_grammar = LOOP_GRAMMAR[engine_type]

        # Build operators scaled by torus radii at eta
        self._build_ops(eta)

    def _build_ops(self, eta: float = None):
        """Build operators with strengths modulated by torus radii at eta.

        R_major = cos(eta) controls base-loop operators (Te, Fi).
        R_minor = sin(eta) controls fiber-loop operators (Ti, Fe).

        At Clifford (eta=pi/4): R_major = R_minor = 1/sqrt(2) -> balanced.
        At inner   (eta=pi/8): R_minor < R_major -> fiber ops weaker.
        At outer   (eta=3pi/8): R_minor > R_major -> fiber ops stronger.
        """
        if eta is None:
            eta = TORUS_CLIFFORD
        self._current_eta = eta

        R_major, R_minor = torus_radii(eta)

        # Ti: fiber-aligned dephasing -> scale by R_minor
        # Fe: fiber-aligned rotation  -> scale by R_minor
        # Te: base-aligned dephasing  -> scale by R_major
        # Fi: base-aligned rotation   -> scale by R_major
        self._ops = {
            "Ti": build_3q_Ti(strength=self.dephasing_strength * R_minor),
            "Fe": build_3q_Fe(strength=R_minor, phi=0.4),
            "XX23": build_3q_XX23(strength=R_major, theta=0.4),
            "Te": build_3q_Te(strength=self.dephasing_strength * R_major, q=0.7),
            "Fi": build_3q_Fi(strength=R_major, theta=self.fi_theta),
        }

    def init_state(self, eta: float = TORUS_CLIFFORD,
                   theta1: float = 0.0, theta2: float = 0.0) -> EngineState3Q:
        """Initialize to |000> (fully separable product state).

        Also rebuilds operators scaled to this eta so dynamics reflect
        the torus latitude.
        """
        self._build_ops(eta)
        rho = np.zeros((8, 8), dtype=complex)
        rho[0, 0] = 1.0  # |000><000|
        return EngineState3Q(
            rho_ABC=rho,
            eta=eta, theta1=theta1, theta2=theta2,
            stage_idx=0,
            engine_type=self.engine_type,
            history=[],
        )

    def _apply_stage(self, state: EngineState3Q, terrain_idx: int) -> EngineState3Q:
        """Apply one macro-stage (single operator) from the LUT."""
        terrain = TERRAINS[terrain_idx]
        op_name, polarity_up = STAGE_OPERATOR_LUT[
            (self.engine_type, terrain["loop"], terrain["topo"])
        ]

        op_fn = self._ops[op_name]
        rho_new = op_fn(state.rho_ABC, polarity_up=polarity_up)

        # Compute I_c for the primary cut (1vs23)
        ic_1vs23 = self.compute_I_c(rho_new, cut="1vs23")

        new_history = list(state.history)
        new_history.append({
            "stage_idx": terrain_idx,
            "terrain": terrain["name"],
            "op": op_name,
            "polarity_up": polarity_up,
            "I_c_1vs23": round(ic_1vs23, 10),
        })

        return EngineState3Q(
            rho_ABC=rho_new,
            eta=state.eta,
            theta1=state.theta1,
            theta2=state.theta2,
            stage_idx=terrain_idx,
            engine_type=state.engine_type,
            history=new_history,
        )

    def run_cycle(self, state: EngineState3Q) -> EngineState3Q:
        """Run a full 8-stage cycle following LOOP_STAGE_ORDER."""
        stage_order = LOOP_STAGE_ORDER[self.engine_type]
        for terrain_idx in stage_order:
            state = self._apply_stage(state, terrain_idx)
        return state

    # -----------------------------------------------------------------
    # Analysis methods
    # -----------------------------------------------------------------

    def run_full_operator_cycle(self, state: EngineState3Q) -> EngineState3Q:
        """Run a full Ti->Fe->XX23->Te->Fi operator block (5-op cycle).

        Unlike run_cycle() which follows the LUT (one operator per terrain),
        this applies ALL five operators in sequence each cycle.  XX23
        (I x X x X) is the auxiliary relay bridging cut2 (12|3) that makes
        all 3 bipartition cuts simultaneously positive.
        """
        rho = state.rho_ABC.copy()
        ops_order = [("Ti", True), ("Fe", True), ("XX23", True),
                     ("Te", True), ("Fi", True)]

        new_history = list(state.history)
        for op_name, pol in ops_order:
            rho = self._ops[op_name](rho, polarity_up=pol)

        ic = self.compute_I_c(rho, cut="1vs23")
        new_history.append({
            "stage_idx": -1,
            "terrain": "full_block",
            "op": "Ti->Fe->XX23->Te->Fi",
            "polarity_up": True,
            "I_c_1vs23": round(ic, 10),
        })

        return EngineState3Q(
            rho_ABC=rho,
            eta=state.eta,
            theta1=state.theta1,
            theta2=state.theta2,
            stage_idx=state.stage_idx,
            engine_type=state.engine_type,
            history=new_history,
        )

    def run_full_operator_cycle_no_xx23(self, state: EngineState3Q) -> EngineState3Q:
        """Run the legacy 4-op Ti->Fe->Te->Fi cycle (without XX23).

        Preserved for comparison: this is the old cycle that cannot
        achieve all 3 bipartition cuts positive simultaneously.
        """
        rho = state.rho_ABC.copy()
        ops_order = [("Ti", True), ("Fe", True), ("Te", True), ("Fi", True)]

        new_history = list(state.history)
        for op_name, pol in ops_order:
            rho = self._ops[op_name](rho, polarity_up=pol)

        ic = self.compute_I_c(rho, cut="1vs23")
        new_history.append({
            "stage_idx": -1,
            "terrain": "full_block",
            "op": "Ti->Fe->Te->Fi",
            "polarity_up": True,
            "I_c_1vs23": round(ic, 10),
        })

        return EngineState3Q(
            rho_ABC=rho,
            eta=state.eta,
            theta1=state.theta1,
            theta2=state.theta2,
            stage_idx=state.stage_idx,
            engine_type=state.engine_type,
            history=new_history,
        )

    # -----------------------------------------------------------------
    # Analysis methods
    # -----------------------------------------------------------------

    def compute_I_c(self, rho_or_state, cut: str = "1vs23") -> float:
        """Coherent information I_c = S(B) - S(AB) for a given bipartition.

        Args:
            rho_or_state: 8x8 density matrix or EngineState3Q
            cut: one of "1vs23", "12vs3", "13vs2"
        """
        if isinstance(rho_or_state, EngineState3Q):
            rho = rho_or_state.rho_ABC
        else:
            rho = rho_or_state
        dims = [2, 2, 2]
        bp = BIPARTITIONS_3Q[cut]
        rho_B = partial_trace_keep(rho, bp["B"], dims)
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho)
        return S_B - S_AB

    def compute_all_cuts(self, rho_or_state) -> Dict[str, float]:
        """Compute I_c for all 3 bipartitions."""
        results = {}
        for cut_name in BIPARTITIONS_3Q:
            results[cut_name] = self.compute_I_c(rho_or_state, cut=cut_name)
        return results

    def compute_full_info(self, rho_or_state) -> Dict[str, dict]:
        """Full information measures (I_c, mutual info) for all cuts."""
        if isinstance(rho_or_state, EngineState3Q):
            rho = rho_or_state.rho_ABC
        else:
            rho = rho_or_state
        dims = [2, 2, 2]
        S_AB = von_neumann_entropy(rho)
        results = {}
        for name, bp in BIPARTITIONS_3Q.items():
            rho_A = partial_trace_keep(rho, bp["A"], dims)
            rho_B = partial_trace_keep(rho, bp["B"], dims)
            S_A = von_neumann_entropy(rho_A)
            S_B = von_neumann_entropy(rho_B)
            I_c = S_B - S_AB
            I_AB = S_A + S_B - S_AB
            results[name] = {
                "label": bp["label"],
                "S_A": round(S_A, 8),
                "S_B": round(S_B, 8),
                "S_AB": round(S_AB, 8),
                "I_c": round(I_c, 8),
                "I_AB": round(I_AB, 8),
                "I_c_positive": bool(I_c > 1e-10),
            }
        return results

    # -----------------------------------------------------------------
    # Eta-dependent run
    # -----------------------------------------------------------------

    def run_at_eta(self, eta: float, n_cycles: int,
                   dephasing: float = 0.05,
                   fi_theta: float = np.pi) -> Dict[str, list]:
        """Run engine at a specific torus latitude and return I_c trajectories.

        Rebuilds operators scaled to the given eta, runs n_cycles using
        run_full_operator_cycle (Ti->Fe->Te->Fi block), and returns
        I_c trajectories for all 3 bipartition cuts.

        Args:
            eta: Torus latitude in [0, pi/2].
            n_cycles: Number of full operator cycles to run.
            dephasing: Dephasing strength (applied to Ti, Te).
            fi_theta: Rotation angle for Fi operator.

        Returns:
            Dict with keys '1vs23', '12vs3', '13vs2', each mapping to
            a list of I_c values (length n_cycles + 1, starting from init).
        """
        # Reconfigure engine with new parameters and eta
        self.dephasing_strength = dephasing
        self.fi_theta = fi_theta
        state = self.init_state(eta=eta)

        trajectories = {cut: [] for cut in BIPARTITIONS_3Q}
        # Record initial I_c (should be 0 for separable |000>)
        for cut in BIPARTITIONS_3Q:
            trajectories[cut].append(self.compute_I_c(state, cut=cut))

        for _ in range(n_cycles):
            state = self.run_full_operator_cycle(state)
            for cut in BIPARTITIONS_3Q:
                trajectories[cut].append(self.compute_I_c(state, cut=cut))

        return trajectories


# =====================================================================
# MAIN -- verification block
# =====================================================================

def _run_single_config(etype, dephasing, fi_theta, n_cycles, label="", eta=None):
    """Run one engine configuration and return summary dict."""
    engine = GeometricEngine3Q(
        engine_type=etype,
        dephasing_strength=dephasing,
        fi_theta=fi_theta,
        eta=eta,
    )
    init_eta = eta if eta is not None else TORUS_CLIFFORD
    state = engine.init_state(eta=init_eta)

    ic_trajectory = []
    first_positive_cycle = None
    max_ic = -999.0
    max_ic_cycle = 0
    sustained_count = 0

    ic_init = engine.compute_I_c(state, cut="1vs23")
    ic_trajectory.append(("init", round(ic_init, 8)))

    for cycle in range(1, n_cycles + 1):
        state = engine.run_cycle(state)
        ic = engine.compute_I_c(state, cut="1vs23")
        ic_trajectory.append((f"cycle_{cycle}", round(ic, 8)))

        if ic > max_ic:
            max_ic = ic
            max_ic_cycle = cycle
        if ic > 1e-10:
            sustained_count += 1
            if first_positive_cycle is None:
                first_positive_cycle = cycle

    all_cuts = engine.compute_all_cuts(state)

    return {
        "label": label,
        "engine_type": etype,
        "dephasing": dephasing,
        "fi_theta": fi_theta,
        "trajectory": ic_trajectory,
        "max_ic": max_ic,
        "max_ic_cycle": max_ic_cycle,
        "first_positive_cycle": first_positive_cycle,
        "sustained_count": sustained_count,
        "n_cycles": n_cycles,
        "all_cuts_final": all_cuts,
        "state": state,
    }


def main():
    print("=" * 72)
    print("  ENGINE 3-QUBIT -- XX_23 Relay Operator Verification")
    print("  5-op (Ti->Fe->XX23->Te->Fi) vs 4-op (Ti->Fe->Te->Fi)")
    print("=" * 72)

    n_cycles = 20
    dephasing = 0.05
    fi_theta = np.pi
    eta = TORUS_CLIFFORD

    # ---- Run both cycles ----
    engine = GeometricEngine3Q(engine_type=1, dephasing_strength=dephasing,
                               fi_theta=fi_theta, eta=eta)

    state_5op = engine.init_state(eta=eta)
    state_4op = engine.init_state(eta=eta)

    traj_5op = {cut: [engine.compute_I_c(state_5op, cut=cut)]
                for cut in BIPARTITIONS_3Q}
    traj_4op = {cut: [engine.compute_I_c(state_4op, cut=cut)]
                for cut in BIPARTITIONS_3Q}

    for _ in range(n_cycles):
        state_5op = engine.run_full_operator_cycle(state_5op)
        state_4op = engine.run_full_operator_cycle_no_xx23(state_4op)
        for cut in BIPARTITIONS_3Q:
            traj_5op[cut].append(engine.compute_I_c(state_5op, cut=cut))
            traj_4op[cut].append(engine.compute_I_c(state_4op, cut=cut))

    # ---- Display 5-op trajectory ----
    print(f"\n{'='*72}")
    print("  5-OP CYCLE: Ti -> Fe -> XX23 -> Te -> Fi")
    print(f"{'='*72}")
    print(f"  {'Cycle':<8s}  {'1vs23':>12s}  {'12vs3':>12s}  {'13vs2':>12s}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*12}  {'-'*12}")
    for cyc in range(n_cycles + 1):
        lbl = "init" if cyc == 0 else f"  {cyc}"
        v1 = traj_5op["1vs23"][cyc]
        v2 = traj_5op["12vs3"][cyc]
        v3 = traj_5op["13vs2"][cyc]
        print(f"  {lbl:<8s}  {v1:>+12.8f}  {v2:>+12.8f}  {v3:>+12.8f}")

    # ---- Display 4-op trajectory ----
    print(f"\n{'='*72}")
    print("  4-OP CYCLE: Ti -> Fe -> Te -> Fi  (legacy, no XX23)")
    print(f"{'='*72}")
    print(f"  {'Cycle':<8s}  {'1vs23':>12s}  {'12vs3':>12s}  {'13vs2':>12s}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*12}  {'-'*12}")
    for cyc in range(n_cycles + 1):
        lbl = "init" if cyc == 0 else f"  {cyc}"
        v1 = traj_4op["1vs23"][cyc]
        v2 = traj_4op["12vs3"][cyc]
        v3 = traj_4op["13vs2"][cyc]
        print(f"  {lbl:<8s}  {v1:>+12.8f}  {v2:>+12.8f}  {v3:>+12.8f}")

    # ---- Per-cycle all-positive check ----
    print(f"\n{'='*72}")
    print("  ALL-3-CUTS-POSITIVE SCAN (per cycle)")
    print(f"{'='*72}")
    print(f"  {'Cycle':<8s}  {'5-op all+':>10s}  {'4-op all+':>10s}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*10}")

    cycles_5op_allpos = []
    cycles_4op_allpos = []
    for cyc in range(n_cycles + 1):
        ap5 = all(traj_5op[c][cyc] > 1e-10 for c in BIPARTITIONS_3Q)
        ap4 = all(traj_4op[c][cyc] > 1e-10 for c in BIPARTITIONS_3Q)
        tag5 = "YES" if ap5 else "no"
        tag4 = "YES" if ap4 else "no"
        lbl = "init" if cyc == 0 else f"  {cyc}"
        print(f"  {lbl:<8s}  {tag5:>10s}  {tag4:>10s}")
        if ap5:
            cycles_5op_allpos.append(cyc)
        if ap4:
            cycles_4op_allpos.append(cyc)

    # ---- Verdict ----
    print(f"\n{'='*72}")
    print("  VERDICT")
    print(f"{'='*72}")

    print(f"  5-op cycles with all 3 cuts positive: {cycles_5op_allpos if cycles_5op_allpos else 'NONE'}")
    print(f"  4-op cycles with all 3 cuts positive: {cycles_4op_allpos if cycles_4op_allpos else 'NONE'}")

    if cycles_5op_allpos and not cycles_4op_allpos:
        print(f"\n  RESULT: XX_23 RELAY PROVEN")
        print(f"  5-op achieves all 3 cuts positive at cycles {cycles_5op_allpos}")
        print(f"  4-op NEVER achieves all 3 cuts positive.")
        print(f"  XX_23 (I x X x X) is the canonical relay bridging cut2 (12|3).")
    elif cycles_5op_allpos and cycles_4op_allpos:
        print(f"\n  RESULT: Both achieve all-positive, but 5-op has more: "
              f"{len(cycles_5op_allpos)} vs {len(cycles_4op_allpos)} cycles")
    else:
        print(f"\n  RESULT: Further tuning needed")

    print(f"{'='*72}")


if __name__ == "__main__":
    main()
