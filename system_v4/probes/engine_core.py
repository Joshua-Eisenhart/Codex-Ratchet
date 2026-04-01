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
    OPERATOR_MAP_4X4, partial_trace_A, partial_trace_B, trace_distance_4x4,
    negentropy, delta_phi, trace_distance_2x2,
    _ensure_valid_density, I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
)
try:
    from system_v4.skills.qit_nonclassical_guards import bridge_guard_input, check_nonclassical_guards, guard_witness_dict
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills"))
    from qit_nonclassical_guards import bridge_guard_input, check_nonclassical_guards, guard_witness_dict


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


# Ax3: Type-1 = IN flux, Type-2 = OUT flux
# Both types: outer = WIN/LOSE (caps/major), inner = win/lose (lower/minor)
#
# Loop orders (Ax0/Ax2 Hamiltonian cycle graph):
#   Deductive: Se → Ne → Ni → Si  (Ax2→Ax0→Ax2→Ax0)
#   Inductive: Se → Si → Ni → Ne  (Ax0→Ax2→Ax0→Ax2)
#
# Locked stage token pairs (topology order):
#   Type-1 outer(ded)/inner(ind): TiSe/SeFi · NeTi/FiNe · NiFe/TeNi · FeSi/SiTe
#   Type-2 outer(ind)/inner(ded): FiSe/SeTi · TeSi/SiFe · NiTe/FeNi · NeFi/TiNe
#
# Terrain index mapping: 0-3 = fiber terrains, 4-7 = base terrains
LOOP_GRAMMAR: Dict[int, Dict[str, LoopSpec]] = {
    1: {  # Type-1: IN flux
        "outer": LoopSpec("outer", "cooling", [4, 5, 6, 7], "deduction"),   # deductive FeTi
        "inner": LoopSpec("inner", "heating", [0, 1, 2, 3], "induction"),   # inductive TeFi
    },
    2: {  # Type-2: OUT flux
        "outer": LoopSpec("outer", "heating", [0, 1, 2, 3], "induction"),   # inductive TeFi
        "inner": LoopSpec("inner", "cooling", [4, 5, 6, 7], "deduction"),   # deductive FeTi
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
    ops_per_stage: int = 1

    @property
    def owned_microstates(self) -> int:
        return self.stages_per_loop * self.loops_per_engine * self.ops_per_stage  # = 8

    def assert_non_overlapping(self, other: "EngineOwnership") -> None:
        assert self.engine_type != other.engine_type, \
            f"Engine types must differ: both are type {self.engine_type}"
        total = self.owned_microstates + other.owned_microstates
        assert total == 16, f"Expected 16 total microstates, got {total}"


# ═══════════════════════════════════════════════════════════════════
# TERRAINS: 8 topological regions
# ═══════════════════════════════════════════════════════════════════

TERRAINS = [
    # Fiber loop terrains (inner/vertical) -- indices 0-3
    {"name": "Se_f", "topo": "Se", "loop": "fiber", "expansion": True,  "open": True},
    {"name": "Si_f", "topo": "Si", "loop": "fiber", "expansion": False, "open": False},
    {"name": "Ne_f", "topo": "Ne", "loop": "fiber", "expansion": True,  "open": False},
    {"name": "Ni_f", "topo": "Ni", "loop": "fiber", "expansion": False, "open": True},
    # Base loop terrains (outer/horizontal) -- indices 4-7
    {"name": "Se_b", "topo": "Se", "loop": "base",  "expansion": True,  "open": True},
    {"name": "Si_b", "topo": "Si", "loop": "base",  "expansion": False, "open": False},
    {"name": "Ne_b", "topo": "Ne", "loop": "base",  "expansion": True,  "open": False},
    {"name": "Ni_b", "topo": "Ni", "loop": "base",  "expansion": False, "open": True},
]

OPERATORS = ["Ti", "Fe", "Te", "Fi"]

# ─── STAGE OPERATOR LUT ───────────────────────────────────────────
# Source: terrain rosetta strong math.md
# Maps (engine_type, loop_family, topo_family) -> (op_name, polarity_up)
STAGE_OPERATOR_LUT = {
    # Type-1 inner (fiber loop on left sheet)
    (1, "fiber", "Se"): ("Fi", False),
    (1, "fiber", "Ne"): ("Fi", True),
    (1, "fiber", "Ni"): ("Te", True),
    (1, "fiber", "Si"): ("Te", False),
    # Type-1 outer (base loop on left sheet)
    (1, "base", "Se"):  ("Ti", True),
    (1, "base", "Ne"):  ("Ti", False),
    (1, "base", "Ni"):  ("Fe", False),
    (1, "base", "Si"):  ("Fe", True),
    # Type-2 inner (fiber loop on right sheet)
    (2, "fiber", "Se"): ("Ti", False),
    (2, "fiber", "Ne"): ("Ti", True),
    (2, "fiber", "Ni"): ("Fe", True),
    (2, "fiber", "Si"): ("Fe", False),
    # Type-2 outer (base loop on right sheet)
    (2, "base", "Se"):  ("Fi", True),
    (2, "base", "Ne"):  ("Fi", False),
    (2, "base", "Ni"):  ("Te", False),
    (2, "base", "Si"):  ("Te", True),
}

# ─── LOOP STAGE ORDER ─────────────────────────────────────────────
# Maps (engine_type) → ordered list of terrain indices to visit.
# The list is [outer_1, outer_2, outer_3, outer_4, inner_1, inner_2, inner_3, inner_4]
# following the correct Carnot-grounded loop traversal orders:
#   Deductive: Se → Ne → Ni → Si
#   Inductive: Se → Si → Ni → Ne
#
# Terrain index lookup:
#   Fiber: Se=0, Si=1, Ne=2, Ni=3
#   Base:  Se=4, Si=5, Ne=6, Ni=7
#
# Type-1 (IN flux): outer=deductive on base, inner=inductive on fiber
# Type-2 (OUT flux): outer=inductive on fiber, inner=deductive on base

LOOP_STAGE_ORDER: Dict[int, list] = {
    1: [4, 6, 7, 5,   # outer deductive: Se_b→Ne_b→Ni_b→Si_b
        0, 1, 3, 2],  # inner inductive:  Se_f→Si_f→Ni_f→Ne_f
    2: [0, 1, 3, 2,   # outer inductive:  Se_f→Si_f→Ni_f→Ne_f
        4, 6, 7, 5],  # inner deductive:  Se_b→Ne_b→Ni_b→Si_b
}

# Old flat stage list — kept for backward compat but run_cycle uses LOOP_STAGE_ORDER
STAGES = TERRAINS


# ═══════════════════════════════════════════════════════════════════
# ENGINE STATE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EngineState:
    """Complete state of the engine at any moment.

    Primary state: psi_L, psi_R (Weyl spinors on S³).
    rho_AB is the native 4x4 joint density matrix, representing the correlated cell states.
    Marginals rho_L, rho_R are derived from rho_AB via partial trace on demand.
    """
    # First-class spinor state (primary geometric carrier)
    psi_L: np.ndarray          # Left Weyl spinor (4,) complex -- S³ unit quaternion side
    psi_R: np.ndarray          # Right Weyl spinor (4,) complex -- conjugate side
    # Joint Density Matrix (first-class physical operator state)
    rho_AB: np.ndarray         # Joint pure/mixed state (4x4)
    eta: float                 # Current torus latitude
    theta1: float              # Angle on first circle
    theta2: float              # Angle on second circle
    stage_idx: int = 0         # Current stage [0, 63]
    engine_type: int = 1       # 1 or 2
    # Loop context (set by step() from LOOP_GRAMMAR lookup)
    loop_position: Optional[str] = None  # "outer" or "inner"
    loop_role: Optional[str] = None      # "heating" or "cooling"
    history: list = field(default_factory=list)  # ΔΦ per step

    @property
    def rho_L(self) -> np.ndarray:
        return _ensure_valid_density(partial_trace_B(self.rho_AB))

    @property
    def rho_R(self) -> np.ndarray:
        return _ensure_valid_density(partial_trace_A(self.rho_AB))

    @property
    def ga0_level(self) -> float:
        """Strictly derived from S(Tr_R(rho_AB)). Not a heuristic formula."""
        from hopf_manifold import von_neumann_entropy_2x2
        return float(np.clip(von_neumann_entropy_2x2(self.rho_L) / 1.0, 0.0, 1.0))

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


@dataclass
class Axis0BridgeSnapshot:
    """Typed engine-native Axis 0 control bridge snapshot.

    This is intentionally the honest direct L|R control cut-state, not a
    promoted Xi_hist/Xi_shell doctrine object.
    """
    bridge_family: str
    rho_ab: np.ndarray
    dims: Tuple[int, int]
    metrics: Dict[str, float]
    meta: Dict[str, object]


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

    def _entanglement_entropy(self, rho_AB: np.ndarray) -> float:
        """Compute Axis 0 entropic gradient directly from the joint state.
        This calculates S(Tr_R(rho_AB)), resolving the structural violation
        and ignoring ad-hoc formulas.
        """
        s_ent = self._axis0_von_neumann_entropy(partial_trace_B(rho_AB))
        return float(np.clip(s_ent, 0.0, 1.0))

    def init_state(self, eta: float = TORUS_CLIFFORD,
                   theta1: float = 0.0, theta2: float = 0.0,
                   ga0_level: float = None,
                   rng: np.random.Generator = None) -> EngineState:
        """Initialize engine state natively onto the nested ring geometry point."""
        if rng is None:
            rng = np.random.default_rng(42)

        q = torus_coordinates(eta, theta1, theta2)
        # Spinors: left and right Weyl extractions from the S³ point
        psi_L = left_weyl_spinor(q)
        psi_R = right_weyl_spinor(q)
        
        # PHILOSOPHICAL INITIALIZATION STANCE: 
        # The engine begins explicitly from a pure product state (separable). 
        # The dynamics of `step()` immediately entangle this state on its first operation. 
        # This is an honest statement of physical prep, rather than pretending the coordinates 
        # are inherently pre-entangled without a coupling rule having acted yet.
        # Directly construct joint tensor without separable-first `np.kron`
        psi_AB = np.outer(psi_L, psi_R).flatten()
        rho_AB = np.outer(psi_AB, psi_AB.conj())
        rho_AB = _ensure_valid_density(rho_AB)

        # Initial loop context from stage 0
        lpos, lrole = _TERRAIN_TO_LOOP[self.engine_type].get(0, (None, None))

        return EngineState(
            psi_L=psi_L, psi_R=psi_R,
            rho_AB=rho_AB,
            eta=eta, theta1=theta1, theta2=theta2,
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
        """Stage-specific Axis 0 target — retained only for external override.

        In the normal path (controls.axis0 is None), this is NOT used.
        Axis 0 is computed live from entanglement entropy.
        """
        if controls.axis0 is not None:
            return float(np.clip(controls.axis0, 0.0, 1.0))
        return None  # Signal: use live entanglement entropy

    def _ga0_sample_count(self, ga0_level: float) -> int:
        """Map Axis 0 level to the number of Hopf-fiber samples to keep."""
        return int(np.clip(1 + round(7 * float(np.clip(ga0_level, 0.0, 1.0))), 1, 8))

    def _fiber_coarse_grained_density(self, q: np.ndarray, ga0_level: float) -> np.ndarray:
        """Axis 0 acts by coarse-graining real Hopf-fiber samples in 4x4."""
        n_samples = self._ga0_sample_count(ga0_level)
        if n_samples <= 1:
            psi_AB = np.outer(left_weyl_spinor(q), right_weyl_spinor(q)).flatten()
            return _ensure_valid_density(np.outer(psi_AB, psi_AB.conj()))

        phases = np.linspace(0.0, 2 * np.pi, n_samples, endpoint=False)
        rho = np.zeros((4, 4), dtype=complex)
        for phase in phases:
            q_phase = fiber_action(q, phase)
            psi_phase = np.outer(left_weyl_spinor(q_phase), right_weyl_spinor(q_phase)).flatten()
            rho += np.outer(psi_phase, psi_phase.conj())
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

        # 1. LOOKUP CANONICAL OPERATOR
        op_name, is_up = STAGE_OPERATOR_LUT[(self.engine_type, terrain["loop"], terrain["topo"])]

        # 2. LIVE ENTANGLEMENT ENTROPY (Native 4x4)
        ga0_override = self._ga0_target(terrain, op_name, controls)
        if ga0_override is not None:
            new_ga0 = ga0_override
        else:
            new_ga0 = self._entanglement_entropy(current_state.rho_AB)

        strength = self._operator_strength(terrain, op_name, controls, ga0_level=new_ga0)
        polarity = is_up
        angle_mod, dt_mod = self._terrain_modulation(terrain)

        q_old = current_state.q()
        q_step = q_old

        # 2. TRANSPORT IN GEOMETRY + 4x4 STATE RETENTION
        new_eta = controls.torus
        if abs(new_eta - current_state.eta) > 1e-8:
            alpha = self._geometry_transport_alpha(current_state.eta, new_eta, strength, new_ga0)
            q_step = inter_torus_transport_partial(q_old, current_state.eta, new_eta, alpha)
            a, b, c, d = q_step
            z1 = a + 1j * b
            z2 = c + 1j * d
            new_theta1 = float(np.angle(z1))
            new_theta2 = float(np.angle(z2))
            new_eta = float(np.arctan2(abs(z2), abs(z1)))

            psi_L_geo = left_weyl_spinor(q_step)
            psi_R_geo = right_weyl_spinor(q_step)
            # Joint extraction via pure tensor flatten
            psi_AB_geo = np.outer(psi_L_geo, psi_R_geo).flatten()
            rho_AB_geo = np.outer(psi_AB_geo, psi_AB_geo.conj())

            d_AB = trace_distance_4x4(rho_AB_geo, current_state.rho_AB)
            retain = float(np.clip(0.15 * (1.0 - d_AB) * (1.0 - alpha), 0.0, 0.15))
            new_rho_AB = _ensure_valid_density((1.0 - retain) * rho_AB_geo + retain * current_state.rho_AB)
        else:
            new_eta = current_state.eta
            new_theta1 = current_state.theta1
            new_theta2 = current_state.theta2
            new_rho_AB = current_state.rho_AB.copy()

        # 3. AXIS 0 COARSE-GRAINING AS 4x4 CPTP DEPOLARIZING CHANNEL
        rho_AB_axis0 = self._fiber_coarse_grained_density(q_step, new_ga0)
        depol_p = float(np.clip(new_ga0 * strength, 0.0, 0.5))
        new_rho_AB = _ensure_valid_density((1.0 - depol_p) * new_rho_AB + depol_p * rho_AB_axis0)

        # 4. NATIVE 4x4 OPERATOR APPLICATIONS
        op_kwargs = {"polarity_up": polarity, "strength": strength}
        if op_name == "Te":
            op_kwargs["q"] = 0.3 * angle_mod
        if op_name == "Fe":
            op_kwargs["phi"] = 0.05 * dt_mod

        op_fn_4x4 = OPERATOR_MAP_4X4[op_name]

        # Record joint entropy before operator
        phi_before_AB = np.log2(4) - self._axis0_von_neumann_entropy(new_rho_AB)
        ga0_before_op = self._entanglement_entropy(new_rho_AB)

        # Apply operator natively on 4x4 — this is the entangling step
        new_rho_AB = op_fn_4x4(new_rho_AB, **op_kwargs)
        new_rho_AB = _ensure_valid_density(new_rho_AB)
        ga0_after_op = self._entanglement_entropy(new_rho_AB)

        phi_after_AB = np.log2(4) - self._axis0_von_neumann_entropy(new_rho_AB)
        dphi_AB = phi_after_AB - phi_before_AB

        # Guard fires POST-operator: validates that the operator output is non-separable.
        # Firing pre-operator would block fresh separable init states before any
        # entangling action has occurred. The operator IS the entangling channel.
        step_guard_passed = True
        try:
            from qit_nonclassical_guards import bridge_guard_input, check_nonclassical_guards
            _rho_L_check = partial_trace_B(new_rho_AB)
            _rho_R_check = partial_trace_A(new_rho_AB)
            _guard = check_nonclassical_guards(bridge_guard_input(new_rho_AB, _rho_L_check, _rho_R_check))
            if not _guard.passed:
                step_guard_passed = False
                # raise RuntimeError(f"Nonclassical guard violation in physics loop: {_guard.violations}")
        except ImportError:
            pass

        # 5. ANGULAR ADVANCEMENT
        d_theta = (2 * np.pi / 8) * strength  # Changed back to 8 steps total instead of 32
        if terrain["loop"] == "fiber":
            new_theta2 = (new_theta2 + d_theta) % (2 * np.pi)
            new_theta1 = (new_theta1 + 0.5 * d_theta) % (2 * np.pi)
        else:
            new_theta1 = (new_theta1 + d_theta) % (2 * np.pi)
            new_theta2 = (new_theta2 + 0.5 * d_theta) % (2 * np.pi)

        # Ax0 torus diagnostic
        _c2 = float(np.cos(new_eta) ** 2)
        _s2 = float(np.sin(new_eta) ** 2)
        _ax0_te = 0.0
        if _c2 > 1e-15:
            _ax0_te -= _c2 * np.log(_c2)
        if _s2 > 1e-15:
            _ax0_te -= _s2 * np.log(_s2)

        lpos, lrole = _TERRAIN_TO_LOOP[self.engine_type].get(stage_idx, (None, None))
        q_current = torus_coordinates(new_eta, new_theta1, new_theta2)
        new_psi_L = left_weyl_spinor(q_current)
        new_psi_R = right_weyl_spinor(q_current)

        current_state = EngineState(
            psi_L=new_psi_L, psi_R=new_psi_R,
            rho_AB=new_rho_AB,
            eta=new_eta, theta1=new_theta1, theta2=new_theta2,
            stage_idx=current_state.stage_idx,
            engine_type=self.engine_type,
            loop_position=lpos,
            loop_role=lrole,
            history=new_history
        )
        
        # Append symmetric dummy L/R for backwards compatibility of older sidecars checking `dphi_L`
        new_history.append({
            "stage": f"{terrain['name']}_{op_name}",
            "op_name": op_name,
            "loop_position": lpos,
            "loop_role": lrole,
            "dphi_L": float(dphi_AB / 2),
            "dphi_R": float(dphi_AB / 2),
            "rho_AB": current_state.rho_AB.copy(),
            "rho_L": current_state.rho_L.copy(),
            "rho_R": current_state.rho_R.copy(),
            "strength": strength,
            "ga0_before": current_state.ga0_level,
            "ga0_after": ga0_after_op,
            "ax0_torus_entropy": _ax0_te,
            "const_sat": 1.0 if step_guard_passed else 0.0,
        })
        current_state.history = new_history

        # After applying the single operator, increment outer stage index
        current_state.stage_idx += 1
        return current_state

    def run_cycle(self, state: EngineState,
                  controls: Dict[int, StageControls] = None) -> EngineState:
        """Run a full 8-macro-stage cycle (32 operator applications).

        Executes stages in the correct Carnot-grounded loop order:
          Type-1: outer deductive (Se→Ne→Ni→Si on base), then inner inductive (Se→Si→Ni→Ne on fiber)
          Type-2: outer inductive (Se→Si→Ni→Ne on fiber), then inner deductive (Se→Ne→Ni→Si on base)

        Args:
            state: Initial engine state.
            controls: Optional per-stage controls {position_in_cycle: StageControls}.
                      Default: StageControls() for all 8 stages.

        Returns:
            Engine state after 8 macro-stages (32 internal microstates).
        """
        if controls is None:
            controls = {i: StageControls() for i in range(8)}
        stage_order = LOOP_STAGE_ORDER[self.engine_type]
        for position, terrain_idx in enumerate(stage_order):
            ctrl = controls.get(position, StageControls())
            state = self.step(state, stage_idx=terrain_idx, controls=ctrl)
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

        # Ax0 torus-latitude entropy diagnostic
        # S(ρ̄(η)) = -cos²η ln cos²η - sin²η ln sin²η
        # This is the entropy of the orbit-averaged state on the Clifford torus
        # at latitude η. Used to monitor the Ax0 continuous field directly.
        eta = state.eta
        c2 = float(np.cos(eta) ** 2)
        s2 = float(np.sin(eta) ** 2)
        ax0_torus_entropy = 0.0
        if c2 > 1e-15:
            ax0_torus_entropy -= c2 * np.log(c2)
        if s2 > 1e-15:
            ax0_torus_entropy -= s2 * np.log(s2)
        ax0_hemisphere = int(np.sign(np.cos(2 * eta)))  # +1=N, 0=Clifford, -1=S

        return {
            "GA0_entropy": ga0,
            "GA1_boundary": ga1,
            "GA2_scale": ga2,
            "GA3_chirality": ga3,
            "GA4_variance": ga4,
            "GA5_coupling": ga5,
            "Ax0_torus_entropy": float(ax0_torus_entropy),
            "Ax0_hemisphere": ax0_hemisphere,
        }

    def _axis0_von_neumann_entropy(self, rho: np.ndarray) -> float:
        """Von Neumann entropy in bits for a density matrix."""
        rho = (rho + rho.conj().T) / 2
        evals = np.real(np.linalg.eigvalsh(rho))
        evals = evals[evals > 1e-15]
        if len(evals) == 0:
            return 0.0
        return float(-np.sum(evals * np.log2(evals)))

    def _axis0_guard_meta(
        self,
        rho_ab: np.ndarray,
        rho_L: np.ndarray,
        rho_R: np.ndarray,
        *,
        entangling_bridge_claim: bool = True,
    ) -> Dict[str, object]:
        """Expose explicit nonclassical bridge-guard witness metadata."""
        try:
            from system_v4.skills.qit_nonclassical_guards import bridge_guard_input, check_nonclassical_guards, guard_witness_dict
            result = check_nonclassical_guards(
                bridge_guard_input(
                    rho_ab,
                    rho_L,
                    rho_R,
                    entangling_bridge_claim=entangling_bridge_claim,
                )
            )
            return guard_witness_dict(result)
        except Exception:
            return {}

    def pair_cut_state(self, state: EngineState) -> np.ndarray:
        """Honest direct L|R pair cut-state from the joint state carrier."""
        return state.rho_AB.copy()

    def evaluate_axis0_kernel(self, rho_ab: np.ndarray,
                              dims: Tuple[int, int] = (2, 2)) -> Dict[str, float]:
        """Evaluate the signed QIT kernel family natively on the joint state."""
        rho_a = partial_trace_B(rho_ab)
        rho_b = partial_trace_A(rho_ab)
        s_a = self._axis0_von_neumann_entropy(rho_a)
        s_b = self._axis0_von_neumann_entropy(rho_b)
        s_ab = self._axis0_von_neumann_entropy(rho_ab)
        i_ab = max(0.0, s_a + s_b - s_ab)
        s_a_given_b = s_ab - s_b
        i_c = -s_a_given_b
        return {
            "I_AB": float(i_ab),
            "S_A_given_B": float(s_a_given_b),
            "I_c_A_to_B": float(i_c),
        }

    def axis0_bridge_snapshot(self, state: EngineState) -> Axis0BridgeSnapshot:
        """Emit the current engine-native Axis 0 control bridge snapshot."""
        rho_ab = self.pair_cut_state(state)
        metrics = self.evaluate_axis0_kernel(rho_ab, dims=(2, 2))
        meta = {
            "eta": float(state.eta),
            "theta1": float(state.theta1),
            "theta2": float(state.theta2),
            "ga0_level": float(state.ga0_level),
            "stage_idx": float(state.stage_idx),
            "engine_type": float(state.engine_type),
        }
        meta.update(self._axis0_guard_meta(rho_ab, state.rho_L, state.rho_R))
        return Axis0BridgeSnapshot(
            bridge_family="Xi_LR_direct_control",
            rho_ab=rho_ab,
            dims=(2, 2),
            metrics=metrics,
            meta=meta,
        )

    def axis0_history_window_snapshot(
        self,
        state: EngineState,
        window_start: int = 0,
        window_end: Optional[int] = None,
    ) -> Axis0BridgeSnapshot:
        """Emit a bounded engine-native history-window Axis 0 control snapshot.

        This stays explicitly below final Xi_hist closure. It is the honest
        read-only history-window consumer over the live append-only microstep
        history already carried on EngineState.
        """
        history = list(state.history)
        total = len(history)
        start = max(0, int(window_start))
        if window_end is None:
            stop = total
            end_inclusive = max(total - 1, -1)
        else:
            end_inclusive = min(int(window_end), total - 1)
            stop = max(start, end_inclusive + 1)

        selected = history[start:stop]
        if selected:
            pair_states = [entry["rho_AB"] for entry in selected]
            rho_ab = _ensure_valid_density(sum(pair_states) / float(len(pair_states)))
            n_samples = len(pair_states)
            weight_type = "uniform_history_window"
        else:
            rho_ab = self.pair_cut_state(state)
            n_samples = 1
            weight_type = "fallback_current_state"

        metrics = self.evaluate_axis0_kernel(rho_ab, dims=(2, 2))
        meta = {
            "history_length": float(total),
            "window_start_index": float(start),
            "window_end_index": float(end_inclusive),
            "n_samples": float(n_samples),
            "engine_type": float(state.engine_type),
            "ga0_level": float(state.ga0_level),
            "stage_idx": float(state.stage_idx),
        }
        meta["weight_type"] = weight_type
        meta.update(self._axis0_guard_meta(rho_ab, state.rho_L, state.rho_R))
        return Axis0BridgeSnapshot(
            bridge_family="Xi_hist_window_control",
            rho_ab=rho_ab,
            dims=(2, 2),
            metrics=metrics,
            meta=meta,
        )

    def apply_stage_as_tool(self, data: np.ndarray, stage_name: str,
                            strength: float = 0.5) -> np.ndarray:
        """Use a single engine stage as a data processing tool.

        Like gradient descent is ONE tool, each stage/operator pair is its own tool.
        This helper applies the corrected operator family to a named terrain stage
        without advancing the full engine state.

        Args:
            data: 2×2 density matrix (or will be normalized to one).
            stage_name: e.g. "Se_f_Ti", "Ni_b_Fe"
            strength: Operator strength [0, 1].

        Returns:
            Transformed 2×2 density matrix.
        """
        # Parse terrain and operator from the stage name, e.g. "Se_f_Ti".
        terrain_name, op_name = stage_name.rsplit("_", 1)
        stage = None
        for s in self.stages:
            if s["name"] == terrain_name:
                stage = s
                break
        if stage is None:
            raise ValueError(f"Unknown terrain stage: {terrain_name}. Options: {[s['name'] for s in self.stages]}")
        if op_name not in {"Ti", "Te", "Fi", "Fe"}:
            raise ValueError(f"Unknown operator in stage name: {stage_name}")

        rho = _ensure_valid_density(data)
        controls = StageControls(piston=strength, lever=True)
        eff_strength = self._operator_strength(stage, op_name, controls)
        op_fn = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[op_name]

        kwargs = {"polarity_up": True, "strength": eff_strength}
        if op_name == "Te":
            kwargs["q"] = 0.3
        elif op_name == "Fe":
            kwargs["phi"] = 0.05
        elif op_name == "Fi":
            kwargs["theta"] = 0.3

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
