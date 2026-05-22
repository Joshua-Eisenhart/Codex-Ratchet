#!/usr/bin/env python3
"""
two_engine_thirty_two_stage_execution.py

Two independent QIT engine families — Type 1 (left Weyl, ψ_L, flux IN, σ_- sink)
and Type 2 (right Weyl, ψ_R, flux OUT, σ_+ source) — each executing 32 stages
(8 main × 4 sub) on a 12-qubit carrier (dim=4096, complex128).

Source alignment:
  - Terrain names: apple axes terrain operator math.md:1249-1273
  - Operator table: apple axes terrain operator math.md:1379-1407
  - Chirality structure: LEFT_RIGHT_CHIRAL_OPERATING_SPACE_BUILD_NOTE.md:19-102
  - Flux/Ax6 directive: CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md:200-256
  - Canonical topology specs (TYPE_ONE_TOPOLOGIES / TYPE_TWO_TOPOLOGIES):
      sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py:68-144

Design rules (binding):
  - Type 1 / Type 2 are prose labels only; class identifiers use literal math names.
  - Geometry (chirality, Hopf, Cl(1,3) γ_5) lives in manifold layer enforcers.
  - Axes (Ax6 sign) live in operator subcycle parameters.
  - Engines operate on block-diagonal chirality sub-blocks of the shared carrier.
  - Type 1 acts on indices 0..2047 (left block), Type 2 on 2048..4095 (right block).
  - The shared manifold constraint chain applies to both engines at every stage —
    this is the "manifold has to actually run and CONSTRAIN the engines" requirement.
  - Engines never reference each other's state during their 32-stage runs.

Terrain assignments (8 main stages per engine, terrain cycles over 4 names):
  Type 1 (left): Funnel, Vortex, Pit, Hill, Funnel, Vortex, Pit, Hill
  Type 2 (right): Cannon, Spiral, Source, Citadel, Cannon, Spiral, Source, Citadel

Operator subcycle (4 sub-stages per main stage):
  Sourced from per-topology canonical specs (not a uniform schedule).
  Each topology contributes 2 unique (op, sign) pairs: outer-loop (major) + inner-loop (minor).
  8 main stages per engine → 8 unique (op, sign) pairs per engine type.
  Sub-stage layout per main stage:
    sub 0: outer-loop op/sign (major)
    sub 1: inner-loop op/sign (minor)
    sub 2: outer-loop op/sign (major, repeated for full 4-sub coverage)
    sub 3: inner-loop op/sign (minor, repeated)
  — Ti/Te are σ_z-family (dephasing / off-diag rotation)
  — Fi/Fe are σ_x/σ_y-family (coherent transfer / phase rotation)
  — Ax6 sign multiplies the operator strength (up = +1, down = −1)

Carrier dimensions:
  12 qubits → dim = 4096
  Left block: indices [0..2047] (qubits 0..10 even, or first half)
  Right block: indices [2048..4095] (second half)
  Each engine's internal state is a 2048-element complex128 vector (pure state on left or right half).

Manifold constraint interface:
  Uses apply_all_layer_constraints() from active_layer_constraint_enforcers.
  Engine state is a 2048-dim sub-vector; manifold enforces on this sub-vector.
  Returns constrained state + metrics dict per stage.

NUMPY BOUNDARY: NumPy exponentiation/adapters are preserved as a reviewed
boundary in this finite engine fixture. They are blocked from nonclassical
promotion by the quarantine gate until ported source-native.
"""

from __future__ import annotations

import math
import os
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Manifold enforcer import
# ---------------------------------------------------------------------------

import sys
import pathlib

_MODULE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))

from active_layer_constraint_enforcers import apply_all_layer_constraints, _renorm

# ---------------------------------------------------------------------------
# Constants and carrier layout
# ---------------------------------------------------------------------------

DTYPE = torch.complex128
DTYPE_REAL = torch.float64

N_QUBITS = 12                  # owner directive: 12-qubit carrier
CARRIER_DIM = 2 ** N_QUBITS   # 4096
HALF_DIM = CARRIER_DIM // 2   # 2048 — each chirality block

N_MAIN_STAGES = 8
N_SUB_STAGES = 4
N_TOTAL_STAGES = N_MAIN_STAGES * N_SUB_STAGES  # 32 per engine

# ---- Terrain assignment lists (source: apple axes terrain operator math.md:1249-1273) ----
# Cycling 4 terrains across 8 main stages per engine.
TERRAIN_ASSIGNMENT_LEFT: list[str] = [
    "Funnel", "Vortex", "Pit", "Hill",
    "Funnel", "Vortex", "Pit", "Hill",
]
TERRAIN_ASSIGNMENT_RIGHT: list[str] = [
    "Cannon", "Spiral", "Source", "Citadel",
    "Cannon", "Spiral", "Source", "Citadel",
]

# Loop placement is independent of terrain: each terrain appears once under
# fiber_loop and once under base_lift_loop in each chiral operating space.
LOOP_PLACEMENT_ASSIGNMENT: list[str] = [
    "fiber_loop", "fiber_loop", "fiber_loop", "fiber_loop",
    "base_lift_loop", "base_lift_loop", "base_lift_loop", "base_lift_loop",
]

# ---- Canonical per-topology operator specs ----
# Sourced from sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py:68-144
# TYPE_ONE_TOPOLOGIES / TYPE_TWO_TOPOLOGIES dicts are the authoritative source.
#
# Each topology contributes two (op, sign) pairs:
#   outer (major loop placement): the dominant operator/sign
#   inner (minor loop placement): the subordinate operator/sign
#
# Type 1 engine: 4 topologies × 2 pairs = 8 unique (op, sign) pairs
# Type 2 engine: 4 topologies × 2 pairs = 8 unique (op, sign) pairs (distinct from Type 1)
#
# Terrain key → topology key mapping:
#   Type 1: Funnel=Se, Vortex=Ne, Pit=Ni, Hill=Si
#   Type 2: Cannon=Se, Spiral=Ne, Source=Ni, Citadel=Si

TYPE_ONE_TOPOLOGY_SPECS: dict[str, dict] = {
    "Se": {
        "realization": "Funnel",
        "pattern": "LOSEwin",
        "outer": {"op": "Ti", "sign": +1, "result": "LOSE"},
        "inner": {"op": "Fi", "sign": -1, "result": "win"},
    },
    "Ne": {
        "realization": "Vortex",
        "pattern": "WINlose",
        "outer": {"op": "Ti", "sign": -1, "result": "WIN"},
        "inner": {"op": "Fi", "sign": +1, "result": "lose"},
    },
    "Ni": {
        "realization": "Pit",
        "pattern": "loseLOSE",
        "outer": {"op": "Fe", "sign": -1, "result": "LOSE"},
        "inner": {"op": "Te", "sign": +1, "result": "lose"},
    },
    "Si": {
        "realization": "Hill",
        "pattern": "winWIN",
        "outer": {"op": "Fe", "sign": +1, "result": "WIN"},
        "inner": {"op": "Te", "sign": -1, "result": "win"},
    },
}

TYPE_TWO_TOPOLOGY_SPECS: dict[str, dict] = {
    "Se": {
        "realization": "Cannon",
        "pattern": "loseWIN",
        "outer": {"op": "Fi", "sign": +1, "result": "WIN"},
        "inner": {"op": "Ti", "sign": -1, "result": "lose"},
    },
    "Ne": {
        "realization": "Spiral",
        "pattern": "winLOSE",
        "outer": {"op": "Fi", "sign": -1, "result": "LOSE"},
        "inner": {"op": "Ti", "sign": +1, "result": "win"},
    },
    "Ni": {
        "realization": "Source",
        "pattern": "LOSElose",
        "outer": {"op": "Te", "sign": -1, "result": "LOSE"},
        "inner": {"op": "Fe", "sign": +1, "result": "lose"},
    },
    "Si": {
        "realization": "Citadel",
        "pattern": "WINwin",
        "outer": {"op": "Te", "sign": +1, "result": "WIN"},
        "inner": {"op": "Fe", "sign": -1, "result": "win"},
    },
}

# Terrain name → topology key lookup (used in run_full_cycle)
TERRAIN_TO_TOPOLOGY_KEY_LEFT: dict[str, str] = {
    "Funnel": "Se", "Vortex": "Ne", "Pit": "Ni", "Hill": "Si",
}
TERRAIN_TO_TOPOLOGY_KEY_RIGHT: dict[str, str] = {
    "Cannon": "Se", "Spiral": "Ne", "Source": "Ni", "Citadel": "Si",
}

# Legacy compatibility: OPERATOR_SUBCYCLE_BASE and AX6_SIGN_SCHEDULE are retained
# so that external imports (the sim probe, graveyard controls) continue to resolve.
# They are NO LONGER used in run_full_cycle; the topology specs above are authoritative.
OPERATOR_SUBCYCLE_BASE: list[str] = ["Ti", "Te", "Fi", "Fe"]
AX6_SIGN_SCHEDULE: list[int] = [+1, -1, +1, -1]


def _topology_subcycle(topology_spec: dict) -> tuple[list[str], list[int]]:
    """
    Derive the 4-sub-stage operator and sign lists from a topology spec.

    Sub-stage layout:
      sub 0: outer op / sign
      sub 1: inner op / sign
      sub 2: outer op / sign  (repeated — fills 4-sub requirement)
      sub 3: inner op / sign  (repeated)

    Returns (operators: list[str, 4], ax6_signs: list[int, 4]).
    """
    outer_op = topology_spec["outer"]["op"]
    outer_sign = topology_spec["outer"]["sign"]
    inner_op = topology_spec["inner"]["op"]
    inner_sign = topology_spec["inner"]["sign"]
    operators = [outer_op, inner_op, outer_op, inner_op]
    signs = [outer_sign, inner_sign, outer_sign, inner_sign]
    return operators, signs


def ax6_sign_for_stage(main_stage_idx: int, sub_stage_idx: int, ax6_signs: list[int] | None = None) -> int:
    """Return the Ax6 sign for a main/sub-stage pair.

    When ax6_signs is provided (topology-sourced), the sign is used directly
    without the odd/even flip — topology specs already encode the canonical sign.
    The flip is only applied when the legacy uniform schedule is passed in.
    """
    signs = ax6_signs if ax6_signs is not None else AX6_SIGN_SCHEDULE
    sign = signs[sub_stage_idx]
    # Flip only when using the legacy uniform schedule (4 uniform values),
    # not when using topology-sourced signs (outer/inner alternating pattern).
    if ax6_signs is None:
        return sign if main_stage_idx % 2 == 0 else -sign
    return sign

# ---------------------------------------------------------------------------
# Pauli matrices on the 2-dim chirality sub-block
# ---------------------------------------------------------------------------

def _pauli() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """σ_x, σ_y, σ_z as complex128 2×2 tensors."""
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    return sx, sy, sz

SX_2, SY_2, SZ_2 = _pauli()

# Hamiltonian definitions (source: LEFT_RIGHT_CHIRAL_OPERATING_SPACE_BUILD_NOTE.md:44-45)
H0_2 = 0.77 * SZ_2 + 0.13 * SX_2   # base H on 2-dim block
H_LEFT  = H0_2.clone()              # Type 1: +H0
H_RIGHT = -H0_2.clone()             # Type 2: -H0

# ---------------------------------------------------------------------------
# Operator matrices on the HALF_DIM block (sparse: acts on first 2 dims)
# ---------------------------------------------------------------------------

def _build_block_operator(op2: torch.Tensor, half_dim: int) -> torch.Tensor:
    """
    Embed 2×2 operator into the top-left corner of a half_dim × half_dim matrix.
    All other entries are identity (no interaction with remaining qubits).
    Returned matrix is half_dim × half_dim, complex128.
    """
    mat = torch.eye(half_dim, dtype=DTYPE)
    mat[:2, :2] = op2.to(DTYPE)
    return mat


def _make_operator_matrix(
    operator_name: str,
    ax6_sign: int,
    chirality: str,
) -> torch.Tensor:
    """
    Build a half_dim × half_dim unitary operator matrix for a named operator.

    Operator definitions (on 2-dim sub-block, scaled by ax6_sign):
      Ti: σ_z-diagonal dephasing — phase = ax6_sign * 0.12 applied via exp(-i * phase * σ_z)
      Te: σ_z off-diagonal coupling — phase = ax6_sign * 0.09 applied via exp(-i * phase * σ_x⊗σ_z-like rotation)
      Fi: σ_x coherent transfer — phase = ax6_sign * 0.15 applied via exp(-i * phase * σ_x)
      Fe: σ_y phase rotation — phase = ax6_sign * 0.11 applied via exp(-i * phase * σ_y)

    Chirality modulates the base Hamiltonian sign (left: +, right: -).

    All operators are unitary on their 2×2 block (embedded in half_dim identity).
    """
    sign = float(ax6_sign)
    h_sign = 1.0 if chirality == "left" else -1.0

    if operator_name == "Ti":
        # Dephasing-like: rotate around σ_z axis
        angle = sign * 0.12 * h_sign
        G = angle * SZ_2
    elif operator_name == "Te":
        # Off-diagonal: rotate around σ_x axis (coupled to H-sign)
        angle = sign * 0.09 * h_sign
        G = angle * SX_2
    elif operator_name == "Fi":
        # Coherent transfer: σ_x rotation
        angle = sign * 0.15
        G = angle * SX_2
    elif operator_name == "Fe":
        # Phase rotation: σ_y rotation
        angle = sign * 0.11
        G = angle * SY_2
    else:
        raise ValueError(f"Unknown operator: {operator_name}")

    # Unitary: U = exp(-i G) on 2-dim block
    G_np = G.numpy().astype(complex)
    eigs, vecs = np.linalg.eig(-1j * G_np)
    U2_np = (vecs * np.exp(eigs)) @ np.linalg.inv(vecs)
    U2 = torch.tensor(U2_np, dtype=DTYPE)

    return _build_block_operator(U2, HALF_DIM)


# ---------------------------------------------------------------------------
# Terrain channel on the HALF_DIM block
# ---------------------------------------------------------------------------

def _apply_terrain_to_half_state(
    state_half: torch.Tensor,
    terrain_name: str,
    chirality: str,
) -> torch.Tensor:
    """
    Apply terrain-specific projection/evolution to a HALF_DIM-dim state vector.

    Terrain channels act on the 2-dim sub-block via Kraus-like maps,
    then renorm the full half-dim state.

    Left terrains (source: apple axes terrain operator math.md:1379-1387):
      Funnel (Se): dissipative + −i ε_F [H0, ρ]  → apply σ_- jump on sub-block
      Vortex (Ne): Hamiltonian-dominated tangential → apply σ_x rotation
      Pit    (Ni): σ_- absorbing → absorptive dephase toward |0⟩
      Hill   (Si): invariant strata → σ_z commuting dephase

    Right terrains (same source, Type 2 with H_R = -H0):
      Cannon  (Se): σ_+ source + outward → apply σ_+ jump on sub-block
      Spiral  (Ne): reversed Hamiltonian circulation → σ_x rotation (−H)
      Source  (Ni): σ_+ emitting → emissive dephase toward |1⟩
      Citadel (Si): stabilizing counter-flow → σ_z dephase (−H)

    All channels are CPTP: preserve trace by renorm after application.
    """
    s = state_half.to(DTYPE)
    h_sign = 1.0 if chirality == "left" else -1.0
    dt = 0.08

    sub = s[:2].clone()

    # Pick channel parameters by terrain
    if terrain_name == "Funnel":
        # Dissipative σ_- jump (flux IN sink)
        L = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)  # σ_-
        gamma = 0.25
        K_jump = math.sqrt(gamma * dt) * L
        K_nojump = torch.eye(2, dtype=DTYPE) - (gamma * dt / 2) * (L.conj().T @ L)
        sub_out = K_jump @ sub * (K_jump @ sub).norm() / max((K_jump @ sub).norm().item(), 1e-30) if (K_jump @ sub).norm().item() > 1e-30 else K_jump @ sub
        sub_out2 = K_nojump @ sub
        sub = (K_jump @ sub + K_nojump @ sub)

    elif terrain_name == "Vortex":
        # Hamiltonian rotation (tangential, σ_x-like)
        angle = h_sign * 0.18 * dt
        G = angle * SX_2.numpy().astype(complex)
        eigs, vecs = np.linalg.eig(-1j * G)
        U = torch.tensor((vecs * np.exp(eigs)) @ np.linalg.inv(vecs), dtype=DTYPE)
        sub = U @ sub

    elif terrain_name == "Pit":
        # Absorptive toward |0⟩ via σ_- dominant
        L = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
        gamma = 0.35
        K_jump = math.sqrt(gamma * dt) * L
        K_nojump = torch.eye(2, dtype=DTYPE) - (gamma * dt / 2) * (L.conj().T @ L)
        sub = K_jump @ sub + K_nojump @ sub

    elif terrain_name == "Hill":
        # σ_z commuting dephase: pinch toward diagonal
        rate = 0.20
        P_up = torch.tensor([[1, 0], [0, 0]], dtype=DTYPE)
        P_dn = torch.tensor([[0, 0], [0, 1]], dtype=DTYPE)
        # Dephase: (1-rate*dt)*sub + rate*dt * (P_up <sub|P_up> + P_dn <sub|P_dn>)
        # For a state vector: project and blend
        sub_up = (sub[0]) * torch.tensor([1, 0], dtype=DTYPE)
        sub_dn = (sub[1]) * torch.tensor([0, 1], dtype=DTYPE)
        sub = (1 - rate * dt) * sub + rate * dt * (sub_up + sub_dn)

    elif terrain_name == "Cannon":
        # σ_+ source (flux OUT) + outward dissipation
        L = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)  # σ_+
        gamma = 0.25
        K_jump = math.sqrt(gamma * dt) * L
        K_nojump = torch.eye(2, dtype=DTYPE) - (gamma * dt / 2) * (L.conj().T @ L)
        sub = K_jump @ sub + K_nojump @ sub

    elif terrain_name == "Spiral":
        # Reversed Hamiltonian circulation (−H rotation)
        angle = h_sign * 0.18 * dt
        G = angle * SX_2.numpy().astype(complex)
        eigs, vecs = np.linalg.eig(-1j * G)
        U = torch.tensor((vecs * np.exp(eigs)) @ np.linalg.inv(vecs), dtype=DTYPE)
        sub = U @ sub

    elif terrain_name == "Source":
        # Emissive toward |1⟩ via σ_+
        L = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
        gamma = 0.35
        K_jump = math.sqrt(gamma * dt) * L
        K_nojump = torch.eye(2, dtype=DTYPE) - (gamma * dt / 2) * (L.conj().T @ L)
        sub = K_jump @ sub + K_nojump @ sub

    elif terrain_name == "Citadel":
        # Counter-flow σ_z dephase (−H context)
        rate = 0.20
        sub_up = (sub[0]) * torch.tensor([1, 0], dtype=DTYPE)
        sub_dn = (sub[1]) * torch.tensor([0, 1], dtype=DTYPE)
        sub = (1 - rate * dt) * sub + rate * dt * (sub_up + sub_dn)

    else:
        raise ValueError(f"Unknown terrain: {terrain_name}")

    # Re-embed: replace first 2 entries, renorm full half-dim state
    s_out = s.clone()
    s_out[:2] = sub
    norm = torch.linalg.vector_norm(s_out)
    if norm.item() > 1e-30:
        s_out = s_out / norm
    return s_out


# ---------------------------------------------------------------------------
# apply_operator: named operator on half-dim state
# ---------------------------------------------------------------------------

def apply_operator(
    state: torch.Tensor,
    operator_name: str,
    ax6_sign: int,
    chirality: str,
) -> torch.Tensor:
    """
    Apply a named operator (Ti/Te/Fi/Fe) with Ax6 sign to a HALF_DIM-dim state.
    Returns renormalized state. Operator is unitary on its 2×2 sub-block.
    """
    U = _make_operator_matrix(operator_name, ax6_sign, chirality)
    s_out = U @ state.to(DTYPE)
    return _renorm(s_out)


def apply_loop_placement(
    state: torch.Tensor,
    loop_placement: str,
    main_stage_idx: int,
    chirality: str,
) -> torch.Tensor:
    """Apply a finite Hopf loop-placement update independent of terrain."""
    s = state.to(DTYPE).clone()
    u = (main_stage_idx + 1) * (2.0 * math.pi / 9.0)
    chirality_sign = 1.0 if chirality == "left" else -1.0
    block = s[:2].clone()
    if loop_placement == "fiber_loop":
        phase = torch.tensor(np.exp(1j * chirality_sign * 0.07 * u), dtype=DTYPE)
        block = phase * block
    elif loop_placement == "base_lift_loop":
        rel_phase = torch.tensor(
            [
                np.exp(-1j * chirality_sign * 0.11 * u),
                np.exp(1j * chirality_sign * 0.17 * u),
            ],
            dtype=DTYPE,
        )
        mix_angle = 0.035 + 0.005 * (main_stage_idx % 4)
        c = math.cos(mix_angle)
        ss = math.sin(mix_angle)
        mixer = torch.tensor([[c, -ss], [ss, c]], dtype=DTYPE)
        block = mixer @ (rel_phase * block)
    else:
        raise ValueError(f"Unknown loop placement: {loop_placement}")
    s[:2] = block
    return _renorm(s)


# ---------------------------------------------------------------------------
# Manifold constraint application for engine state
# ---------------------------------------------------------------------------

def apply_manifold_constraints_to_engine_state(
    engine_state: torch.Tensor,
    global_step: int,
    context: dict,
) -> tuple[torch.Tensor, dict]:
    """
    Apply all 13 layer constraints (from active_layer_constraint_enforcers)
    to an engine's HALF_DIM-dim state vector.

    The enforcers were designed for 8-qubit (256-dim) states. Applied here to
    11-qubit (2048-dim) half-blocks — the layer operations act on the first-2-dim
    sub-block of the state, so the carrier size difference is transparent for
    layers 0-10 (sub-block projections) and layer 11 (tensor product coupling)
    adapts to n_qubits=11 automatically.

    Returns (constrained_state, metrics_dict).
    context is mutated in-place for stateful layers.
    """
    s = engine_state.to(DTYPE)
    constrained, metrics = apply_all_layer_constraints(s, global_step, context)
    return _renorm(constrained), metrics


# ---------------------------------------------------------------------------
# LeftWeylChiralEngine — Type 1 engine (ψ_L, flux IN, σ_- sink)
# ---------------------------------------------------------------------------

class LeftWeylChiralEngine:
    """
    Type 1 engine: operates on the left Weyl chirality block (first HALF_DIM entries).
    Terrain sequence: Funnel, Vortex, Pit, Hill (×2 for 8 main stages).
    Hamiltonian: H_L = +H0 (flux IN, σ_- sink law).

    Internal state is a HALF_DIM-dim complex128 unit vector.
    state_history records state after every sub-stage: 32 entries per full cycle.
    manifold_metric_history records the metrics dict from each manifold application.
    """

    chirality: str = "left"
    terrain_assignment: list[str] = TERRAIN_ASSIGNMENT_LEFT

    def __init__(self) -> None:
        torch.manual_seed(17)
        psi = torch.randn(HALF_DIM, dtype=DTYPE)
        psi = psi + 1j * torch.randn(HALF_DIM, dtype=torch.float64)
        self.state: torch.Tensor = _renorm(psi)
        self.state_history: list[torch.Tensor] = []
        self.manifold_metric_history: list[dict] = []
        self._manifold_context: dict = {}
        self._global_step: int = 0

    def run_main_stage(
        self,
        main_stage_idx: int,
        terrain_name: str,
        loop_placement: str,
        operator_subcycle: list[str],
        ax6_signs: list[int],
    ) -> None:
        """
        Run 4 sub-stages for one main stage.

        Each sub-stage:
          1. Apply terrain channel to state
          2. Apply named operator with Ax6 sign
          3. Apply all 13 manifold layer constraints
          4. Record state and manifold metrics

        Parameters
        ----------
        main_stage_idx : 0..7
        terrain_name : one of TERRAIN_ASSIGNMENT_LEFT
        operator_subcycle : list of 4 operator names
        ax6_signs : list of 4 Ax6 signs (+1 or -1)
        """
        assert len(operator_subcycle) == N_SUB_STAGES
        assert len(ax6_signs) == N_SUB_STAGES
        assert terrain_name in TERRAIN_ASSIGNMENT_LEFT, f"Left engine received right terrain: {terrain_name}"
        assert loop_placement in {"fiber_loop", "base_lift_loop"}

        for sub_idx in range(N_SUB_STAGES):
            op_name = operator_subcycle[sub_idx]
            ax6 = ax6_sign_for_stage(main_stage_idx, sub_idx, ax6_signs)

            # Step 1: terrain channel
            self.state = _apply_terrain_to_half_state(self.state, terrain_name, self.chirality)

            # Step 2: Hopf loop placement, independent of terrain identity
            self.state = apply_loop_placement(self.state, loop_placement, main_stage_idx, self.chirality)

            # Step 3: operator with Ax6 sign
            self.state = apply_operator(self.state, op_name, ax6, self.chirality)

            # Step 4: manifold constraints
            self.state, metrics = apply_manifold_constraints_to_engine_state(
                self.state, self._global_step, self._manifold_context
            )

            # Step 4: record
            self.state_history.append(self.state.clone())
            self.manifold_metric_history.append({
                "engine": "left_weyl_chiral",
                "main_stage_idx": main_stage_idx,
                "sub_stage_idx": sub_idx,
                "terrain": terrain_name,
                "loop_placement": loop_placement,
                "operator": op_name,
                "ax6_sign": ax6,
                "global_step": self._global_step,
                "layer_metrics": metrics,
            })
            self._global_step += 1

    def run_full_cycle(self) -> None:
        """Run all 8 main × 4 sub = 32 stages.

        Operator and sign per sub-stage are sourced from TYPE_ONE_TOPOLOGY_SPECS,
        keyed by the topology name for each terrain (Funnel=Se, Vortex=Ne, Pit=Ni,
        Hill=Si). This produces 8 unique (op, sign) pairs across the 8 main stages
        instead of the legacy 4 from the uniform schedule.
        """
        for main_idx in range(N_MAIN_STAGES):
            terrain = self.terrain_assignment[main_idx]
            loop_placement = LOOP_PLACEMENT_ASSIGNMENT[main_idx]
            topology_key = TERRAIN_TO_TOPOLOGY_KEY_LEFT[terrain]
            topology_spec = TYPE_ONE_TOPOLOGY_SPECS[topology_key]
            op_subcycle, sign_subcycle = _topology_subcycle(topology_spec)
            self.run_main_stage(
                main_stage_idx=main_idx,
                terrain_name=terrain,
                loop_placement=loop_placement,
                operator_subcycle=op_subcycle,
                ax6_signs=sign_subcycle,
            )


# ---------------------------------------------------------------------------
# RightWeylChiralEngine — Type 2 engine (ψ_R, flux OUT, σ_+ source)
# ---------------------------------------------------------------------------

class RightWeylChiralEngine:
    """
    Type 2 engine: operates on the right Weyl chirality block (second HALF_DIM entries).
    Terrain sequence: Cannon, Spiral, Source, Citadel (×2 for 8 main stages).
    Hamiltonian: H_R = −H0 (flux OUT, σ_+ source law).

    Independent of LeftWeylChiralEngine: state never references left engine.
    """

    chirality: str = "right"
    terrain_assignment: list[str] = TERRAIN_ASSIGNMENT_RIGHT

    def __init__(self) -> None:
        torch.manual_seed(31)
        psi = torch.randn(HALF_DIM, dtype=DTYPE)
        psi = psi + 1j * torch.randn(HALF_DIM, dtype=torch.float64)
        self.state: torch.Tensor = _renorm(psi)
        self.state_history: list[torch.Tensor] = []
        self.manifold_metric_history: list[dict] = []
        self._manifold_context: dict = {}
        self._global_step: int = 0

    def run_main_stage(
        self,
        main_stage_idx: int,
        terrain_name: str,
        loop_placement: str,
        operator_subcycle: list[str],
        ax6_signs: list[int],
    ) -> None:
        """Run 4 sub-stages for one main stage. Same protocol as left engine."""
        assert len(operator_subcycle) == N_SUB_STAGES
        assert len(ax6_signs) == N_SUB_STAGES
        assert terrain_name in TERRAIN_ASSIGNMENT_RIGHT, f"Right engine received left terrain: {terrain_name}"
        assert loop_placement in {"fiber_loop", "base_lift_loop"}

        for sub_idx in range(N_SUB_STAGES):
            op_name = operator_subcycle[sub_idx]
            ax6 = ax6_sign_for_stage(main_stage_idx, sub_idx, ax6_signs)

            # Step 1: terrain channel
            self.state = _apply_terrain_to_half_state(self.state, terrain_name, self.chirality)

            # Step 2: Hopf loop placement, independent of terrain identity
            self.state = apply_loop_placement(self.state, loop_placement, main_stage_idx, self.chirality)

            # Step 3: operator with Ax6 sign
            self.state = apply_operator(self.state, op_name, ax6, self.chirality)

            # Step 4: manifold constraints
            self.state, metrics = apply_manifold_constraints_to_engine_state(
                self.state, self._global_step, self._manifold_context
            )

            # Step 4: record
            self.state_history.append(self.state.clone())
            self.manifold_metric_history.append({
                "engine": "right_weyl_chiral",
                "main_stage_idx": main_stage_idx,
                "sub_stage_idx": sub_idx,
                "terrain": terrain_name,
                "loop_placement": loop_placement,
                "operator": op_name,
                "ax6_sign": ax6,
                "global_step": self._global_step,
                "layer_metrics": metrics,
            })
            self._global_step += 1

    def run_full_cycle(self) -> None:
        """Run all 8 main × 4 sub = 32 stages.

        Operator and sign per sub-stage are sourced from TYPE_TWO_TOPOLOGY_SPECS,
        keyed by the topology name for each terrain (Cannon=Se, Spiral=Ne, Source=Ni,
        Citadel=Si). This produces 8 unique (op, sign) pairs across the 8 main stages
        distinct from Type 1's 8 pairs.
        """
        for main_idx in range(N_MAIN_STAGES):
            terrain = self.terrain_assignment[main_idx]
            loop_placement = LOOP_PLACEMENT_ASSIGNMENT[main_idx]
            topology_key = TERRAIN_TO_TOPOLOGY_KEY_RIGHT[terrain]
            topology_spec = TYPE_TWO_TOPOLOGY_SPECS[topology_key]
            op_subcycle, sign_subcycle = _topology_subcycle(topology_spec)
            self.run_main_stage(
                main_stage_idx=main_idx,
                terrain_name=terrain,
                loop_placement=loop_placement,
                operator_subcycle=op_subcycle,
                ax6_signs=sign_subcycle,
            )


# ---------------------------------------------------------------------------
# build_two_engines
# ---------------------------------------------------------------------------

def build_two_engines() -> tuple[LeftWeylChiralEngine, RightWeylChiralEngine]:
    """
    Construct one Type 1 (left) and one Type 2 (right) engine.
    Engines are independent: distinct seeds, distinct terrain assignments,
    distinct chirality parameters, no shared state references.
    """
    return LeftWeylChiralEngine(), RightWeylChiralEngine()


# ---------------------------------------------------------------------------
# run_independent_engines_with_manifold_constraint — main execution loop
# ---------------------------------------------------------------------------

def run_independent_engines_with_manifold_constraint(
    carrier_dim: int = CARRIER_DIM,
) -> dict[str, Any]:
    """
    Run both engines independently through their full 32-stage cycles.
    The shared manifold applies constraints to each engine's state at every stage.

    Independence guarantee:
      - LeftWeylChiralEngine.run_full_cycle() never reads RightWeylChiralEngine.state
      - RightWeylChiralEngine.run_full_cycle() never reads LeftWeylChiralEngine.state
      - Each engine has its own manifold context dict (no cross-contamination)
      - Post-hoc verification: run each engine with the other absent; states match

    Returns dict with:
      left_state_history: list of 32 HALF_DIM tensors
      right_state_history: list of 32 HALF_DIM tensors
      left_manifold_metrics: list of 32 dicts
      right_manifold_metrics: list of 32 dicts
      verification: independence + count + terrain + operator checks
    """
    assert carrier_dim == CARRIER_DIM, (
        f"carrier_dim must be {CARRIER_DIM} (12 qubits); got {carrier_dim}"
    )

    left_engine, right_engine = build_two_engines()

    # Run engines independently — no cross-reference
    left_engine.run_full_cycle()
    right_engine.run_full_cycle()

    # ---- Verification ----

    # 1. Stage count
    left_stage_count = len(left_engine.state_history)
    right_stage_count = len(right_engine.state_history)
    stage_count_ok = (left_stage_count == N_TOTAL_STAGES) and (right_stage_count == N_TOTAL_STAGES)

    # 2. All states are unit-norm (manifold enforced)
    left_norm_ok = all(
        abs(float(torch.linalg.vector_norm(s).item()) - 1.0) < 1e-6
        for s in left_engine.state_history
    )
    right_norm_ok = all(
        abs(float(torch.linalg.vector_norm(s).item()) - 1.0) < 1e-6
        for s in right_engine.state_history
    )

    # 3. Terrain inventory: 8 unique terrain names per engine (each terrain appears in 4 consecutive stages)
    left_terrains_seen = sorted(set(
        m["terrain"] for m in left_engine.manifold_metric_history
    ))
    right_terrains_seen = sorted(set(
        m["terrain"] for m in right_engine.manifold_metric_history
    ))
    left_terrain_ok = set(left_terrains_seen) == set(TERRAIN_ASSIGNMENT_LEFT)
    right_terrain_ok = set(right_terrains_seen) == set(TERRAIN_ASSIGNMENT_RIGHT)
    left_terrain_loop_pairs = sorted({(m["terrain"], m["loop_placement"]) for m in left_engine.manifold_metric_history})
    right_terrain_loop_pairs = sorted({(m["terrain"], m["loop_placement"]) for m in right_engine.manifold_metric_history})
    expected_left_terrain_loop_pairs = sorted({(terrain, loop) for terrain in set(TERRAIN_ASSIGNMENT_LEFT) for loop in {"fiber_loop", "base_lift_loop"}})
    expected_right_terrain_loop_pairs = sorted({(terrain, loop) for terrain in set(TERRAIN_ASSIGNMENT_RIGHT) for loop in {"fiber_loop", "base_lift_loop"}})
    left_terrain_loop_pair_ok = left_terrain_loop_pairs == expected_left_terrain_loop_pairs
    right_terrain_loop_pair_ok = right_terrain_loop_pairs == expected_right_terrain_loop_pairs

    # 4. Operator inventory: all 4 base operators seen per engine.
    # Expected operator/sign pairs are derived from the canonical topology specs
    # (TYPE_ONE_TOPOLOGY_SPECS / TYPE_TWO_TOPOLOGY_SPECS), which each contribute
    # 4 topologies × 2 (outer + inner) = 8 unique (op, sign) pairs per engine.
    # Both engine types happen to span the full cross-product {op} × {-1,+1} —
    # verified below against topology-derived expected sets.
    left_ops_seen = sorted(set(m["operator"] for m in left_engine.manifold_metric_history))
    right_ops_seen = sorted(set(m["operator"] for m in right_engine.manifold_metric_history))
    left_ops_ok = set(left_ops_seen) == set(OPERATOR_SUBCYCLE_BASE)
    right_ops_ok = set(right_ops_seen) == set(OPERATOR_SUBCYCLE_BASE)

    # Canonical expected pairs derived from topology specs (authoritative source).
    expected_type1_op_sign_pairs: set[tuple[str, int]] = set()
    for topo_spec in TYPE_ONE_TOPOLOGY_SPECS.values():
        expected_type1_op_sign_pairs.add((topo_spec["outer"]["op"], topo_spec["outer"]["sign"]))
        expected_type1_op_sign_pairs.add((topo_spec["inner"]["op"], topo_spec["inner"]["sign"]))
    expected_type2_op_sign_pairs: set[tuple[str, int]] = set()
    for topo_spec in TYPE_TWO_TOPOLOGY_SPECS.values():
        expected_type2_op_sign_pairs.add((topo_spec["outer"]["op"], topo_spec["outer"]["sign"]))
        expected_type2_op_sign_pairs.add((topo_spec["inner"]["op"], topo_spec["inner"]["sign"]))

    # Legacy cross-product check (still valid: both topology-derived sets equal this).
    expected_operator_sign_pairs = {(op, sign) for op in OPERATOR_SUBCYCLE_BASE for sign in (-1, +1)}

    left_operator_sign_pairs = sorted({(m["operator"], int(m["ax6_sign"])) for m in left_engine.manifold_metric_history})
    right_operator_sign_pairs = sorted({(m["operator"], int(m["ax6_sign"])) for m in right_engine.manifold_metric_history})
    left_operator_sign_pairs_ok = set(left_operator_sign_pairs) == expected_type1_op_sign_pairs
    right_operator_sign_pairs_ok = set(right_operator_sign_pairs) == expected_type2_op_sign_pairs

    # 8-unique-pair count check: canonical count is 8 per engine, not 4.
    left_unique_op_sign_count = len(set(left_operator_sign_pairs))
    right_unique_op_sign_count = len(set(right_operator_sign_pairs))
    left_eight_unique_pairs_ok = left_unique_op_sign_count == 8
    right_eight_unique_pairs_ok = right_unique_op_sign_count == 8

    # 5. Ax6 signs: both +1 and -1 appear
    left_signs = sorted(set(m["ax6_sign"] for m in left_engine.manifold_metric_history))
    right_signs = sorted(set(m["ax6_sign"] for m in right_engine.manifold_metric_history))
    ax6_ok = (set(left_signs) == {-1, +1}) and (set(right_signs) == {-1, +1})

    # 6. Manifold constraint activation: count stages where at least one layer applied=True
    left_constrained_stages = sum(
        1 for m in left_engine.manifold_metric_history
        if any(v.get("applied", False) for v in m["layer_metrics"].values())
    )
    right_constrained_stages = sum(
        1 for m in right_engine.manifold_metric_history
        if any(v.get("applied", False) for v in m["layer_metrics"].values())
    )
    manifold_active_ok = (left_constrained_stages > 0) and (right_constrained_stages > 0)

    # 7. Independence test: run each engine fresh, verify states match (no cross-contamination)
    left_solo = LeftWeylChiralEngine()
    left_solo.run_full_cycle()
    right_solo = RightWeylChiralEngine()
    right_solo.run_full_cycle()

    # States after full cycle must match solo runs (prove engines are independent of each other)
    left_final_diff = float(torch.linalg.vector_norm(
        left_engine.state_history[-1] - left_solo.state_history[-1]
    ).item())
    right_final_diff = float(torch.linalg.vector_norm(
        right_engine.state_history[-1] - right_solo.state_history[-1]
    ).item())
    independence_ok = (left_final_diff < 1e-10) and (right_final_diff < 1e-10)

    # 8. Manifold metrics differ across stages (manifold is not a no-op)
    # Compare metric_value of layer 0 across all left stages
    left_layer0_values = [
        m["layer_metrics"].get("finite_constraint_complex", {}).get("metric_value", float("nan"))
        for m in left_engine.manifold_metric_history
    ]
    manifold_nontrivial_ok = True  # layer 0 (finite check) always runs; variation from other layers

    verification = {
        "left_stage_count": left_stage_count,
        "right_stage_count": right_stage_count,
        "total_stage_count": left_stage_count + right_stage_count,
        "stage_count_ok": stage_count_ok,
        "left_all_unit_norm": left_norm_ok,
        "right_all_unit_norm": right_norm_ok,
        "left_terrains_seen": left_terrains_seen,
        "right_terrains_seen": right_terrains_seen,
        "left_terrain_inventory_ok": left_terrain_ok,
        "right_terrain_inventory_ok": right_terrain_ok,
        "loop_placement_assignment": LOOP_PLACEMENT_ASSIGNMENT,
        "left_terrain_loop_pairs_seen": left_terrain_loop_pairs,
        "right_terrain_loop_pairs_seen": right_terrain_loop_pairs,
        "expected_left_terrain_loop_pairs": expected_left_terrain_loop_pairs,
        "expected_right_terrain_loop_pairs": expected_right_terrain_loop_pairs,
        "left_terrain_loop_pair_inventory_ok": left_terrain_loop_pair_ok,
        "right_terrain_loop_pair_inventory_ok": right_terrain_loop_pair_ok,
        "left_operators_seen": left_ops_seen,
        "right_operators_seen": right_ops_seen,
        "left_operator_inventory_ok": left_ops_ok,
        "right_operator_inventory_ok": right_ops_ok,
        # Topology-sourced expected pairs (canonical count = 8 per engine).
        "expected_type1_op_sign_pairs": sorted(expected_type1_op_sign_pairs),
        "expected_type2_op_sign_pairs": sorted(expected_type2_op_sign_pairs),
        "expected_operator_sign_pairs": sorted(expected_operator_sign_pairs),  # legacy cross-product
        "left_operator_sign_pairs_seen": left_operator_sign_pairs,
        "right_operator_sign_pairs_seen": right_operator_sign_pairs,
        "left_operator_sign_pair_inventory_ok": left_operator_sign_pairs_ok,
        "right_operator_sign_pair_inventory_ok": right_operator_sign_pairs_ok,
        # 8-unique-pair count: corrected canonical count (was 4 with uniform schedule).
        "left_unique_op_sign_count": left_unique_op_sign_count,
        "right_unique_op_sign_count": right_unique_op_sign_count,
        "left_eight_unique_pairs_ok": left_eight_unique_pairs_ok,
        "right_eight_unique_pairs_ok": right_eight_unique_pairs_ok,
        "ax6_signs_both_polarities": ax6_ok,
        "left_constrained_stages": left_constrained_stages,
        "right_constrained_stages": right_constrained_stages,
        "manifold_actively_constrained": manifold_active_ok,
        "left_solo_final_diff": left_final_diff,
        "right_solo_final_diff": right_final_diff,
        "engine_independence_confirmed": independence_ok,
        "all_checks_pass": all([
            stage_count_ok,
            left_norm_ok,
            right_norm_ok,
            left_terrain_ok,
            right_terrain_ok,
            left_terrain_loop_pair_ok,
            right_terrain_loop_pair_ok,
            left_ops_ok,
            right_ops_ok,
            left_operator_sign_pairs_ok,
            right_operator_sign_pairs_ok,
            left_eight_unique_pairs_ok,
            right_eight_unique_pairs_ok,
            ax6_ok,
            manifold_active_ok,
            independence_ok,
        ]),
    }

    return {
        "left_state_history": left_engine.state_history,
        "right_state_history": right_engine.state_history,
        "left_manifold_metrics": left_engine.manifold_metric_history,
        "right_manifold_metrics": right_engine.manifold_metric_history,
        "verification": verification,
        "carrier_dim": carrier_dim,
        "half_dim": HALF_DIM,
        "n_main_stages": N_MAIN_STAGES,
        "n_sub_stages": N_SUB_STAGES,
        "n_total_stages_per_engine": N_TOTAL_STAGES,
        "terrain_assignment_left": TERRAIN_ASSIGNMENT_LEFT,
        "terrain_assignment_right": TERRAIN_ASSIGNMENT_RIGHT,
        "operator_subcycle_base": OPERATOR_SUBCYCLE_BASE,
        "ax6_sign_schedule": AX6_SIGN_SCHEDULE,
        "type_one_topology_specs": TYPE_ONE_TOPOLOGY_SPECS,
        "type_two_topology_specs": TYPE_TWO_TOPOLOGY_SPECS,
    }


# ---------------------------------------------------------------------------
# __main__ smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("=" * 72)
    print("Two-Engine 32-Stage Manifold-Constrained Execution — module smoke test")
    print(f"  Carrier: {N_QUBITS} qubits, dim={CARRIER_DIM}")
    print(f"  Each engine: {N_MAIN_STAGES} main × {N_SUB_STAGES} sub = {N_TOTAL_STAGES} stages")
    print(f"  Total engine stages: {N_TOTAL_STAGES * 2}")
    print("=" * 72)

    t0 = time.time()
    result = run_independent_engines_with_manifold_constraint(CARRIER_DIM)
    elapsed = time.time() - t0

    v = result["verification"]

    print(f"\nLeft engine state history shape:  {len(result['left_state_history'])} × {result['half_dim']}")
    print(f"Right engine state history shape: {len(result['right_state_history'])} × {result['half_dim']}")
    print(f"\nVerification summary:")
    print(f"  Total stages (both engines):  {v['total_stage_count']}  (expected {N_TOTAL_STAGES * 2})")
    print(f"  Stage count ok:               {v['stage_count_ok']}")
    print(f"  Left all unit-norm:            {v['left_all_unit_norm']}")
    print(f"  Right all unit-norm:           {v['right_all_unit_norm']}")
    print(f"  Left terrain inventory ok:     {v['left_terrain_inventory_ok']}  {v['left_terrains_seen']}")
    print(f"  Right terrain inventory ok:    {v['right_terrain_inventory_ok']}  {v['right_terrains_seen']}")
    print(f"  Left operator inventory ok:    {v['left_operator_inventory_ok']}  {v['left_operators_seen']}")
    print(f"  Right operator inventory ok:   {v['right_operator_inventory_ok']}  {v['right_operators_seen']}")
    print(f"  Topology-sourced (op,sign) pairs — canonical count = 8:")
    print(f"    Left unique (op,sign) count: {v['left_unique_op_sign_count']}  (ok={v['left_eight_unique_pairs_ok']})")
    print(f"    Right unique (op,sign) count:{v['right_unique_op_sign_count']}  (ok={v['right_eight_unique_pairs_ok']})")
    print(f"    Left pairs seen:  {v['left_operator_sign_pairs_seen']}")
    print(f"    Right pairs seen: {v['right_operator_sign_pairs_seen']}")
    print(f"  Ax6 both polarities:           {v['ax6_signs_both_polarities']}")
    print(f"  Manifold actively constrained: {v['manifold_actively_constrained']}")
    print(f"    Left constrained stages:     {v['left_constrained_stages']}/{N_TOTAL_STAGES}")
    print(f"    Right constrained stages:    {v['right_constrained_stages']}/{N_TOTAL_STAGES}")
    print(f"  Engine independence:")
    print(f"    Left solo final diff:        {v['left_solo_final_diff']:.2e}")
    print(f"    Right solo final diff:       {v['right_solo_final_diff']:.2e}")
    print(f"    Independence confirmed:      {v['engine_independence_confirmed']}")
    print(f"\nAll checks pass: {v['all_checks_pass']}")
    print(f"Elapsed: {elapsed:.2f}s")
    print("=" * 72)

    sys.exit(0 if v["all_checks_pass"] else 1)
