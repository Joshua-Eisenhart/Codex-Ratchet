#!/usr/bin/env python3
"""
Engine Core — Full 64-Step Geometric Engine on Nested Hopf Tori
===============================================================
The actual running engine. 8 macro-stages per type × 4 fixed operator
subcycles per macro-stage × 2 types = 64 operator applications.

Architecture:
  8 terrains = 8 macro-stages per engine type
  each macro-stage runs all 4 operators in fixed order
  
  Terrains (from L2 topology):
    Fiber loop:  Se_f (expand+open), Si_f (compress+closed),
                 Ne_f (expand+closed), Ni_f (compress+open)
    Base loop:   Se_b, Si_b, Ne_b, Ni_b

  Operators per terrain (applied in sequence):
    Ti (constrain) → Fe (release) → Te (explore) → Fi (filter)

  Engine types (from L4 chirality):
    Type 1 (Left Weyl): Fe/Ti dominant on base, Te/Fi on fiber
    Type 2 (Right Weyl): Te/Fi dominant on base, Fe/Ti on fiber

  4 controls per stage:
    1. Piston   = operator strength [0, 1]
    2. Lever    = polarity (up/down)
    3. Torus    = which nested torus (inner/Clifford/outer)
    4. Spinor   = act on left, right, or both Weyl spinors

State:
  ρ_L  = left Weyl spinor density matrix (2×2)
  ρ_R  = right Weyl spinor density matrix (2×2)
  eta  = current torus latitude
  θ₁   = angle on first circle
  θ₂   = angle on second circle
  stage = current macro-stage index [0, 7]

Usage:
  engine = GeometricEngine(engine_type=1)
  state = engine.init_state()
  state = engine.step(state, stage_idx=0)
  trajectory = engine.run_cycle(state)
  axes = engine.read_axes(state)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import copy

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    torus_coordinates, random_s3_point, hopf_map,
    left_weyl_spinor, right_weyl_spinor,
    left_density, right_density,
    rotate_left, rotate_right,
    fiber_phase_left, fiber_phase_right, fiber_action,
    inter_torus_transport, inter_torus_transport_partial,
    torus_transport_fraction, density_to_bloch,
    von_neumann_entropy_2x2, berry_phase,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, NESTED_TORI,
    torus_radii,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, delta_phi, trace_distance_2x2,
    _ensure_valid_density, I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
)


# ═══════════════════════════════════════════════════════════════════
# LOOP GRAMMAR: dual-loop structure per engine type
# ═══════════════════════════════════════════════════════════════════

@dataclass
class LoopSpec:
    """One of the two loops per engine type.

    Owner grammar (ENGINE_GRAMMAR_DISCRETE.md):
      - Each engine type has exactly 2 loops: outer (major) and inner (minor)
      - Each loop owns 4 terrain slots (one per perceiving topology)
      - Loop-role (heating/cooling) inverts across the two engine families
      - Topology traversal ORDER within each loop is DISPUTED --
        recorded from spec but flagged; correct order is a simulation target.
    """
    name: str                   # "outer" or "inner"
    role: str                   # "heating" or "cooling"
    terrain_indices: List[int]  # Which 4 of the 8 terrain slots this loop owns
    topology_order: str         # "deduction" or "induction" (Ax4 -- DISPUTED)


# Ax3 distinguishes the two engine types by FLUX DIRECTION (IN vs OUT), not by casing.
# Both types have WIN/LOSE (caps) on the outer loop and win/lose (lower) on the inner loop.
# Type-1 = IN flux. Type-2 = OUT flux.
#
# Locked stage token pairs (Apple Notes dump — authoritative):
#   Type-1 outer/inner: NeTi/FiNe · FeSi/SiTe · TiSe/SeFi · NiFe/TeNi
#   Type-2 outer/inner: NeFi/TiNe · TeSi/SiFe · FiSe/SeTi · NiTe/FeNi
#
# Terrain index mapping: 0-3 = fiber terrains, 4-7 = base terrains
LOOP_GRAMMAR: Dict[int, Dict[str, LoopSpec]] = {
    1: {  # Type-1: IN flux
        "outer": LoopSpec("outer", "cooling", [4, 5, 6, 7], "deduction"),   # base terrains
        "inner": LoopSpec("inner", "heating", [0, 1, 2, 3], "induction"),   # fiber terrains
    },
    2: {  # Type-2: OUT flux [role inverted vs Type-1]
        "outer": LoopSpec("outer", "heating", [0, 1, 2, 3], "induction"),   # fiber terrains
        "inner": LoopSpec("inner", "cooling", [4, 5, 6, 7], "deduction"),   # base terrains
    },
}

# Reverse map: terrain index -> (loop_name, loop_role) per engine type
_TERRAIN_TO_LOOP: Dict[int, Dict[int, Tuple[str, str]]] = {}
for _et, _loops in LOOP_GRAMMAR.items():
    _TERRAIN_TO_LOOP[_et] = {}
    for _lspec in _loops.values():
        for _ti in _lspec.terrain_indices:
            _TERRAIN_TO_LOOP[_et][_ti] = (_lspec.name, _lspec.role)


@dataclass
class EngineOwnership:
    """Declares what each engine type owns. Enforces 32/32 non-sharing.

    Runtime truth (ENGINE_OWNERSHIP_GRAMMAR_32_32_64.md):
      - Each engine type owns 32 microsteps (8 stages x 4 ops)
      - Two engine types together = 64, non-overlapping
      - This is runtime truth, not proof of structural 8x8 closure
    """
    engine_type: int
    stages_per_loop: int = 4
    loops_per_engine: int = 2
    ops_per_stage: int = 4

    @property
    def owned_microstates(self) -> int:
        return self.stages_per_loop * self.loops_per_engine * self.ops_per_stage  # = 32

    def assert_non_overlapping(self, other: "EngineOwnership") -> None:
        assert self.engine_type != other.engine_type, \
            f"Engine types must differ: both are type {self.engine_type}"
        total = self.owned_microstates + other.owned_microstates
        assert total == 64, f"Expected 64 total microstates, got {total}"


# ═══════════════════════════════════════════════════════════════════
# TERRAINS: 8 topological regions
# ═══════════════════════════════════════════════════════════════════

TERRAINS = [
    # Fiber loop terrains (inner/vertical) -- indices 0-3
    {"name": "Se_f", "loop": "fiber", "expansion": True,  "open": True},
    {"name": "Si_f", "loop": "fiber", "expansion": False, "open": False},
    {"name": "Ne_f", "loop": "fiber", "expansion": True,  "open": False},
    {"name": "Ni_f", "loop": "fiber", "expansion": False, "open": True},
    # Base loop terrains (outer/horizontal) -- indices 4-7
    {"name": "Se_b", "loop": "base",  "expansion": True,  "open": True},
    {"name": "Si_b", "loop": "base",  "expansion": False, "open": False},
    {"name": "Ne_b", "loop": "base",  "expansion": True,  "open": False},
    {"name": "Ni_b", "loop": "base",  "expansion": False, "open": True},
]

OPERATORS = ["Ti", "Fe", "Te", "Fi"]

# 8 stages = 8 terrains (each macro-stage runs all 4 operators internally)
STAGES = TERRAINS


# ═══════════════════════════════════════════════════════════════════
# ENGINE STATE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EngineState:
    """Complete state of the engine at any moment.

    Primary state: psi_L, psi_R (Weyl spinors on S³).
    Density matrices rho_L, rho_R are DERIVED from the spinor via the
    current S³ point q -- they are carried for convenience but the spinor
    is the first-class geometric object.
    """
    # First-class spinor state (primary geometric carrier)
    psi_L: np.ndarray          # Left Weyl spinor (4,) complex -- S³ unit quaternion side
    psi_R: np.ndarray          # Right Weyl spinor (4,) complex -- conjugate side
    # Density matrices (derived from spinor; kept alongside for operator application)
    rho_L: np.ndarray          # Left Weyl density matrix (2×2)
    rho_R: np.ndarray          # Right Weyl density matrix (2×2)
    eta: float                 # Current torus latitude
    theta1: float              # Angle on first circle
    theta2: float              # Angle on second circle
    ga0_level: float = 0.5     # Correlation entropy level (Ax0 -- can be negative in principle)
    stage_idx: int = 0         # Current stage [0, 63]
    engine_type: int = 1       # 1 or 2
    # Loop context (set by step() from LOOP_GRAMMAR lookup)
    loop_position: Optional[str] = None  # "outer" or "inner"
    loop_role: Optional[str] = None      # "heating" or "cooling"
    history: list = field(default_factory=list)  # ΔΦ per step

    def q(self) -> np.ndarray:
        """Current S³ point as quaternion."""
        return torus_coordinates(self.eta, self.theta1, self.theta2)

    def bloch_L(self) -> np.ndarray:
        """Left spinor Bloch vector."""
        return density_to_bloch(self.rho_L)

    def bloch_R(self) -> np.ndarray:
        """Right spinor Bloch vector."""
        return density_to_bloch(self.rho_R)


@dataclass
class StageControls:
    """4 controls per stage."""
    piston: float = 0.5        # Operator strength [0, 1]
    lever: bool = True         # Polarity: True = up, False = down
    torus: float = TORUS_CLIFFORD  # Which nested torus (η value)
    spinor: str = "both"       # "left", "right", or "both"
    axis0: Optional[float] = None  # Target coarse-graining / entropy ceiling [0, 1]


# ═══════════════════════════════════════════════════════════════════
# GEOMETRIC ENGINE
# ═══════════════════════════════════════════════════════════════════

class GeometricEngine:
    """Dual-loop geometric engine on nested Hopf tori with Weyl spinors.

    Each engine type has 2 loops (outer/inner) with inverted heating/cooling
    roles across the two engine families. Each loop owns 4 terrain stages.
    32 microsteps per engine type; 64 total across both types.
    """

    def __init__(self, engine_type: int = 1):
        """
        Args:
            engine_type: 1 = Left Weyl (outer=cooling, inner=heating)
                         2 = Right Weyl (outer=heating, inner=cooling) [role inverted]
        """
        assert engine_type in (1, 2), "engine_type must be 1 or 2"
        self.engine_type = engine_type
        self.stages = STAGES  # 8 terrains
        self.loop_grammar = LOOP_GRAMMAR[engine_type]
        self.ownership = EngineOwnership(engine_type=engine_type)

    def init_state(self, eta: float = TORUS_CLIFFORD,
                   theta1: float = 0.0, theta2: float = 0.0,
                   ga0_level: float = None,
                   rng: np.random.Generator = None) -> EngineState:
        """Initialize engine state on a torus point."""
        if rng is None:
            rng = np.random.default_rng(42)

        q = torus_coordinates(eta, theta1, theta2)
        rho_L = left_density(q)
        rho_R = right_density(q)
        # Spinors: left and right Weyl extractions from the S³ point
        psi_L = left_weyl_spinor(q)
        psi_R = right_weyl_spinor(q)
        if ga0_level is None:
            R_major, R_minor = torus_radii(eta)
            ga0_level = float(np.clip(2.0 * R_major * R_minor, 0.0, 1.0))

        # Initial loop context from stage 0
        lpos, lrole = _TERRAIN_TO_LOOP[self.engine_type].get(0, (None, None))

        return EngineState(
            psi_L=psi_L, psi_R=psi_R,
            rho_L=rho_L, rho_R=rho_R,
            eta=eta, theta1=theta1, theta2=theta2,
            ga0_level=ga0_level,
            stage_idx=0, engine_type=self.engine_type,
            loop_position=lpos, loop_role=lrole,
        )

    def _operator_strength(self, terrain: dict, op_name: str, controls: StageControls,
                           ga0_level: float = None) -> float:
        """Compute effective operator strength based on engine type and terrain.

        Type 1: Fe/Ti stronger on base, Te/Fi stronger on fiber
        Type 2: Te/Fi stronger on base, Fe/Ti stronger on fiber
        """
        loop = terrain["loop"]
        base_piston = controls.piston

        if self.engine_type == 1:
            # Left Weyl: Fe/Ti dominant on base
            if loop == "base" and op_name in ("Fe", "Ti"):
                strength = base_piston * 1.0  # Full strength
            elif loop == "fiber" and op_name in ("Te", "Fi"):
                strength = base_piston * 1.0
            else:
                strength = base_piston * 0.3  # Suppressed
        else:
            # Right Weyl: Te/Fi dominant on base
            if loop == "base" and op_name in ("Te", "Fi"):
                strength = base_piston * 1.0
            elif loop == "fiber" and op_name in ("Fe", "Ti"):
                strength = base_piston * 1.0
            else:
                strength = base_piston * 0.3

        if ga0_level is not None:
            if op_name in ("Te", "Fe"):
                strength *= 0.7 + 0.6 * ga0_level
            else:
                strength *= 1.3 - 0.6 * ga0_level

        return float(np.clip(strength, 0.0, 1.0))

    def _terrain_modulation(self, terrain: dict) -> Tuple[float, float]:
        """Terrain modulates operator behavior:
        - expansion: broadens effect (larger angle/dt)
        - open: allows more mixing (higher damping)
        Returns (angle_mod, dt_mod).
        """
        angle_mod = 1.2 if terrain["expansion"] else 0.8
        dt_mod = 1.2 if terrain["open"] else 0.8
        return angle_mod, dt_mod

    def _ga0_target(self, terrain: dict, op_name: str, controls: StageControls) -> float:
        """Stage-specific Axis 0 target as a real engine control signal."""
        if controls.axis0 is not None:
            return float(np.clip(controls.axis0, 0.0, 1.0))

        target = 0.35 if terrain["loop"] == "fiber" else 0.55
        target += 0.15 if terrain["expansion"] else -0.10
        target += 0.10 if terrain["open"] else -0.05
        target += {"Ti": -0.25, "Fe": 0.05, "Te": 0.20, "Fi": -0.10}[op_name]

        if self.engine_type == 1:
            if terrain["loop"] == "fiber" and op_name in ("Te", "Fi"):
                target += 0.05
            elif terrain["loop"] == "base" and op_name in ("Fe", "Ti"):
                target -= 0.05
        else:
            if terrain["loop"] == "base" and op_name in ("Te", "Fi"):
                target += 0.05
            elif terrain["loop"] == "fiber" and op_name in ("Fe", "Ti"):
                target -= 0.05

        return float(np.clip(target, 0.05, 0.95))

    def _ga0_sample_count(self, ga0_level: float) -> int:
        """Map Axis 0 level to the number of Hopf-fiber samples to keep."""
        return int(np.clip(1 + round(7 * float(np.clip(ga0_level, 0.0, 1.0))), 1, 8))

    def _fiber_coarse_grained_density(self, q: np.ndarray, ga0_level: float,
                                      spinor: str) -> np.ndarray:
        """Axis 0 acts by coarse-graining real Hopf-fiber samples."""
        n_samples = self._ga0_sample_count(ga0_level)
        if n_samples <= 1:
            return left_density(q) if spinor == "left" else right_density(q)

        phases = np.linspace(0.0, 2 * np.pi, n_samples, endpoint=False)
        rho = np.zeros((2, 2), dtype=complex)
        for phase in phases:
            q_phase = fiber_action(q, phase)
            rho += left_density(q_phase) if spinor == "left" else right_density(q_phase)
        rho /= n_samples
        return _ensure_valid_density(rho)

    def _geometry_transport_alpha(self, eta_from: float, eta_to: float,
                                  strength: float, ga0_level: float) -> float:
        """Transport gain derived from torus separation, not a fixed blend."""
        eta_frac = torus_transport_fraction(eta_from, eta_to)
        if eta_frac < 1e-12 or strength <= 1e-12:
            return 0.0

        R0_major, R0_minor = torus_radii(eta_from)
        R1_major, R1_minor = torus_radii(eta_to)
        radius_delta = 0.5 * (abs(R1_major - R0_major) + abs(R1_minor - R0_minor))
        radius_frac = min(radius_delta / (np.sqrt(2) / 2), 1.0)
        geom_frac = min(0.5 * eta_frac + 0.5 * radius_frac, 1.0)
        return float(np.clip(geom_frac * strength * (0.45 + 0.45 * ga0_level), 0.0, 1.0))

    def step(self, state: EngineState, stage_idx: int = None,
             controls: StageControls = None) -> EngineState:
        """Execute one macro-stage.

        Args:
            state: Current engine state.
            stage_idx: Which of 8 macro-stages to execute (default: state.stage_idx % 8).
            controls: 4 control parameters. Default: StageControls().

        Returns:
            New engine state after all 4 internal operator subcycles.
        """
        if controls is None:
            controls = StageControls()
        if stage_idx is None:
            stage_idx = state.stage_idx % 8

        terrain = self.stages[stage_idx]
        current_state = state
        new_history = list(state.history)

        for op_name in OPERATORS:
            ga0_target = self._ga0_target(terrain, op_name, controls)
            ga0_alpha = min(1.0, 0.10 + 0.45 * controls.piston + (0.10 if terrain["open"] else 0.0))
            new_ga0 = float(np.clip((1.0 - ga0_alpha) * current_state.ga0_level + ga0_alpha * ga0_target, 0.0, 1.0))

            # Get effective strength from engine type and current Axis 0 regime
            strength = self._operator_strength(terrain, op_name, controls, ga0_level=new_ga0)
            polarity = controls.lever
            angle_mod, dt_mod = self._terrain_modulation(terrain)

            q_old = current_state.q()
            q_step = q_old

            # Transport on S^3 rather than blending directly in density space.
            new_eta = controls.torus
            if abs(new_eta - current_state.eta) > 1e-8:
                alpha = self._geometry_transport_alpha(current_state.eta, new_eta, strength, new_ga0)
                q_step = inter_torus_transport_partial(q_old, current_state.eta, new_eta, alpha)
                # Update angles from transported point
                a, b, c, d = q_step
                z1 = a + 1j * b
                z2 = c + 1j * d
                new_theta1 = float(np.angle(z1))
                new_theta2 = float(np.angle(z2))
                new_eta = float(np.arctan2(abs(z2), abs(z1)))

                rho_L_geo = left_density(q_step)
                rho_R_geo = right_density(q_step)
                memory = 0.10 * (1.0 - alpha)
                new_rho_L = _ensure_valid_density((1.0 - memory) * rho_L_geo + memory * current_state.rho_L)
                new_rho_R = _ensure_valid_density((1.0 - memory) * rho_R_geo + memory * current_state.rho_R)
            else:
                new_eta = current_state.eta
                new_theta1 = current_state.theta1
                new_theta2 = current_state.theta2
                # No transport — start from current state
                new_rho_L = current_state.rho_L.copy()
                new_rho_R = current_state.rho_R.copy()

            # Axis 0 now acts causally through real Hopf-fiber coarse-graining.
            rho_L_axis0 = self._fiber_coarse_grained_density(q_step, new_ga0, "left")
            rho_R_axis0 = self._fiber_coarse_grained_density(q_step, new_ga0, "right")
            axis0_blend = min(0.45, strength * (0.05 + 0.30 * new_ga0))
            new_rho_L = _ensure_valid_density((1.0 - axis0_blend) * new_rho_L + axis0_blend * rho_L_axis0)
            new_rho_R = _ensure_valid_density((1.0 - axis0_blend) * new_rho_R + axis0_blend * rho_R_axis0)

            op_kwargs = {"polarity_up": polarity, "strength": strength}
            if op_name == "Te":
                op_kwargs["angle"] = 0.3 * angle_mod
            if op_name == "Fe":
                op_kwargs["dt"] = 0.05 * dt_mod

            op_fn = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[op_name]

            if controls.spinor in ("left", "both"):
                phi_before = negentropy(new_rho_L)
                new_rho_L = op_fn(new_rho_L, **op_kwargs)
                phi_after = negentropy(new_rho_L)

            if controls.spinor in ("right", "both"):
                phi_before_R = negentropy(new_rho_R)
                # Right Weyl spinor: CONJUGATE dynamics for ALL operators.
                # ψ_R transforms under U* not U, so every operator acts
                # in the conjugate representation.
                right_kwargs = dict(op_kwargs)
                applied_op = op_name
                if applied_op == "Te":
                    # Conjugate unitary = reversed rotation
                    right_kwargs["polarity_up"] = not polarity
                elif applied_op == "Ti":
                    # Right-spinor Ti dephases in a rotated geometry-dependent basis.
                    phase = new_theta2 - new_theta1
                    basis = np.array(
                        [[1.0, np.exp(1j * phase)],
                         [1.0, -np.exp(1j * phase)]],
                        dtype=complex,
                    ) / np.sqrt(2.0)
                    rho_conj = basis @ new_rho_R @ basis.conj().T
                    rho_conj = op_fn(rho_conj, **right_kwargs)
                    new_rho_R = basis.conj().T @ rho_conj @ basis
                    new_rho_R = _ensure_valid_density(new_rho_R)
                    applied_op = None  # Already applied
                elif applied_op == "Fe":
                    # Conjugate damping: toward |1⟩ instead of |0⟩
                    # Flip basis, damp, flip back
                    sx = SIGMA_X
                    rho_conj = sx @ new_rho_R @ sx
                    rho_conj = op_fn(rho_conj, **right_kwargs)
                    new_rho_R = sx @ rho_conj @ sx
                    new_rho_R = _ensure_valid_density(new_rho_R)
                    applied_op = None
                elif applied_op == "Fi":
                    # Conjugate filter: amplify |1⟩ instead of |0⟩
                    sx = SIGMA_X
                    rho_conj = sx @ new_rho_R @ sx
                    rho_conj = op_fn(rho_conj, **right_kwargs)
                    new_rho_R = sx @ rho_conj @ sx
                    new_rho_R = _ensure_valid_density(new_rho_R)
                    applied_op = None
                if applied_op is not None:
                    new_rho_R = op_fn(new_rho_R, **right_kwargs)

            # Advance torus angles proportional to effective strength and loop type.
            # At piston=0 the engine must be identity — no angular drift.
            d_theta = (2 * np.pi / 32) * strength
            if terrain["loop"] == "fiber":
                new_theta2 = (new_theta2 + d_theta) % (2 * np.pi)
                new_theta1 = (new_theta1 + 0.5 * d_theta) % (2 * np.pi)
            else:
                new_theta1 = (new_theta1 + d_theta) % (2 * np.pi)
                new_theta2 = (new_theta2 + 0.5 * d_theta) % (2 * np.pi)

            # Record step (1 of 32 total operator actions)
            dphi_L = negentropy(new_rho_L) - negentropy(current_state.rho_L)
            dphi_R = negentropy(new_rho_R) - negentropy(current_state.rho_R)

            new_history.append({
                "stage": f"{terrain['name']}_{op_name}",
                "op_name": op_name,
                "loop_position": _TERRAIN_TO_LOOP[self.engine_type].get(stage_idx, (None, None))[0],
                "loop_role": _TERRAIN_TO_LOOP[self.engine_type].get(stage_idx, (None, None))[1],
                "dphi_L": dphi_L,
                "dphi_R": dphi_R,
                "rho_L": new_rho_L.copy(),
                "rho_R": new_rho_R.copy(),
                "strength": strength,
                "ga0_before": current_state.ga0_level,
                "ga0_after": new_ga0
            })

            lpos, lrole = _TERRAIN_TO_LOOP[self.engine_type].get(stage_idx, (None, None))
            # Update spinors from current S³ point (first-class state update)
            q_current = torus_coordinates(new_eta, new_theta1, new_theta2)
            new_psi_L = left_weyl_spinor(q_current)
            new_psi_R = right_weyl_spinor(q_current)

            current_state = EngineState(
                psi_L=new_psi_L, psi_R=new_psi_R,
                rho_L=new_rho_L, rho_R=new_rho_R,
                eta=new_eta, theta1=new_theta1, theta2=new_theta2,
                ga0_level=new_ga0,
                stage_idx=current_state.stage_idx,
                engine_type=self.engine_type,
                loop_position=lpos,
                loop_role=lrole,
                history=new_history
            )

        # After applying all 4 operators, increment outer stage index
        current_state.stage_idx += 1
        return current_state

    def run_cycle(self, state: EngineState,
                  controls: Dict[int, StageControls] = None) -> EngineState:
        """Run a full 8-macro-stage cycle (32 operator applications).

        Args:
            state: Initial engine state.
            controls: Optional per-stage controls {stage_idx: StageControls}.
                      Default: StageControls() for all 8 stages.

        Returns:
            Engine state after 8 macro-stages (32 internal microstates).
        """
        if controls is None:
            controls = {i: StageControls() for i in range(8)}
        for i in range(8):
            ctrl = controls.get(i, StageControls())
            state = self.step(state, stage_idx=i, controls=ctrl)
        return state

    def read_axes(self, state: EngineState) -> Dict[str, float]:
        """Read all 6 geometric axis coordinates from current state."""
        rho_L = state.rho_L
        rho_R = state.rho_R
        b_L = state.bloch_L()
        b_R = state.bloch_R()

        # GA0: Entropic gradient (entropy of combined L+R)
        rho_avg = (rho_L + rho_R) / 2
        rho_avg = _ensure_valid_density(rho_avg)
        ga0 = von_neumann_entropy_2x2(rho_avg)

        # GA1: Boundary (off-diagonal coherence = openness)
        ga1 = float(abs(rho_L[0, 1]) + abs(rho_R[0, 1])) / 2

        # GA2: Scale (torus radius = distance from pole)
        R_major, R_minor = torus_radii(state.eta)
        ga2 = R_major * R_minor  # Area of torus cross-section

        # GA3: Chirality (L/R asymmetry)
        ga3 = trace_distance_2x2(rho_L, rho_R)

        # GA4: Variance (Bloch displacement angle between L and R)
        dot = np.clip(np.dot(b_L, b_R) / (np.linalg.norm(b_L) * np.linalg.norm(b_R) + 1e-12), -1, 1)
        ga4 = float(np.arccos(abs(dot)))

        # GA5: Coupling (avg negentropy)
        ga5 = (negentropy(rho_L) + negentropy(rho_R)) / 2

        return {
            "GA0_entropy": ga0,
            "GA1_boundary": ga1,
            "GA2_scale": ga2,
            "GA3_chirality": ga3,
            "GA4_variance": ga4,
            "GA5_coupling": ga5,
        }

    def apply_stage_as_tool(self, data: np.ndarray, stage_name: str,
                            strength: float = 0.5) -> np.ndarray:
        """Use a single engine stage as a data processing tool.

        Like gradient descent is ONE tool, each of the 32 stages is its own tool.
        The engine provides 8 qualitatively different information-processing modes:
          1. Ti on fiber = constrain/project along fiber (like regularization)
          2. Fe on fiber = dissipate along fiber (like dropout)
          3. Te on fiber = explore within fiber (like momentum)
          4. Fi on fiber = filter on fiber (like attention)
          5. Ti on base = constrain across base (like batch norm)
          6. Fe on base = dissipate across base (like learning rate decay)
          7. Te on base = explore across base (like random search)
          8. Fi on base = filter across base (like feature selection)

        Args:
            data: 2×2 density matrix (or will be normalized to one).
            stage_name: e.g. "Se_f_Ti", "Ni_b_Fe"
            strength: Operator strength [0, 1].

        Returns:
            Transformed 2×2 density matrix.
        """
        # Find stage
        stage = None
        for s in self.stages:
            if s["name"] == stage_name:
                stage = s
                break
        if stage is None:
            raise ValueError(f"Unknown stage: {stage_name}. Options: {[s['name'] for s in self.stages]}")

        rho = _ensure_valid_density(data)
        controls = StageControls(piston=strength, lever=True)
        eff_strength = self._operator_strength(stage, controls)
        op_fn = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[stage["operator"]]

        kwargs = {"polarity_up": True, "strength": eff_strength}
        if stage["operator"] == "Te":
            kwargs["angle"] = 0.3
        if stage["operator"] == "Fe":
            kwargs["dt"] = 0.05

        return op_fn(rho, **kwargs)


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE
# ═══════════════════════════════════════════════════════════════════

def full_64_stage_run(rng: np.random.Generator = None) -> Dict:
    """Run both Type 1 and Type 2 engines = 64 total stages.

    Returns summary with axis trajectories and total ΔΦ.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    results = {}
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        state = engine.init_state(rng=rng)
        axes_before = engine.read_axes(state)
        state = engine.run_cycle(state)
        axes_after = engine.read_axes(state)

        total_dphi_L = sum(h["dphi_L"] for h in state.history)
        total_dphi_R = sum(h["dphi_R"] for h in state.history)

        results[f"type_{engine_type}"] = {
            "stages_run": len(state.history),
            "total_dphi_L": total_dphi_L,
            "total_dphi_R": total_dphi_R,
            "axes_before": axes_before,
            "axes_after": axes_after,
            "axis_deltas": {k: axes_after[k] - axes_before[k] for k in axes_before},
        }

    return results


if __name__ == "__main__":
    print("=" * 72)
    print("FULL 64-STAGE GEOMETRIC ENGINE")
    print("=" * 72)

    results = full_64_stage_run()

    for tp, data in results.items():
        print(f"\n  {tp.upper()}: {data['stages_run']} stages")
        print(f"    Total ΔΦ_L: {data['total_dphi_L']:+.6f}")
        print(f"    Total ΔΦ_R: {data['total_dphi_R']:+.6f}")
        print(f"    Axis deltas:")
        for ax, delta in data["axis_deltas"].items():
            print(f"      {ax}: {delta:+.4f}")

    print(f"\n  TOTAL STAGES: {sum(d['stages_run'] for d in results.values())}")
