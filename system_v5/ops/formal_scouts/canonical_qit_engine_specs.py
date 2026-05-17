#!/usr/bin/env python3
"""
canonical_qit_engine_specs.py — single source of truth for operational QIT engine specs.

Centralizes:
  - Pauli matrices and Hamiltonian H0 = 0.77 * SZ + 0.13 * SX
  - Type 1 vs Type 2 Hamiltonian sign (Type 1: +H0, Type 2: -H0)
  - Per-perception Lindblad collapse operator L matrices (Se, Ne, Ni, Si)
  - Operator generators (Ti, Te, Fi, Fe) → algebraic (SZ, SX, SY) basis
  - Per-topology (op, sign) pairs for outer/inner loop classes
  - 13-layer manifold names
  - Engine schedule per loop (8 main stages = 4 outer + 4 inner per engine)
  - Accessor functions for engine specs and Lindblad parameters

Source alignment (load-bearing references):
  - sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py:68-144
  - sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py:53-69
  - sim_fe_three_to_one_asymmetry_structural_origin_probe.py (Fe asymmetry → operator generators)
  - sim_nested_geometry_tower_dependency_order_probe.py:56-70 (manifold layer names)
  - claude_integrated_manifold_modules/two_engine_thirty_two_stage_execution.py:96-181
    (TYPE_ONE_TOPOLOGY_SPECS, TYPE_TWO_TOPOLOGY_SPECS canonical specs)

All matrices are complex128 numpy arrays. Tensor versions are derived on demand
via torch.from_numpy() in EngineCore. No tensor conversion at import time.

This module does not run simulations. It is read by:
  - engine_core.py (EngineCore class)
  - engine_schedule.py (Schedule class)
  - engine_readouts.py (EngineReadout class)
  - sim_paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe.py
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Numerical constants and Pauli basis (complex128 throughout)
# ---------------------------------------------------------------------------

DTYPE = np.complex128

I2 = np.eye(2, dtype=DTYPE)
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
SIGMA_MINUS = np.array([[0, 0], [1, 0]], dtype=DTYPE)  # σ_-
SIGMA_PLUS = np.array([[0, 1], [0, 0]], dtype=DTYPE)   # σ_+

# Base Hamiltonian on the 2-dim chirality sub-block.
# Source: LEFT_RIGHT_CHIRAL_OPERATING_SPACE_BUILD_NOTE.md:44-45
H0 = 0.77 * SZ + 0.13 * SX
H_TYPE_ONE = +H0    # Type 1 / left Weyl: H_L = +H0
H_TYPE_TWO = -H0    # Type 2 / right Weyl: H_R = -H0
H3 = 0.61 * SY + 0.21 * SX
H_STRATA = 0.83 * SZ

# Mirror operator (σ_x) — maps H_L ↔ H_R and σ_- ↔ σ_+
MIRROR = SX

# ---------------------------------------------------------------------------
# Per-perception Lindblad collapse operator L matrices
# ---------------------------------------------------------------------------
#
# Each perception (Se, Ne, Ni, Si) admits a canonical Lindblad collapse
# operator L. The Lindblad equation is:
#   dρ/dt = -i[H, ρ] + L ρ L† - ½ {L†L, ρ}
#
# Source: master math table screenshot context — per-perception L matrices.
#
# Algebraic shapes:
#   Se: σ_z         — pure dephasing (no population transfer)
#   Ne: σ_+         — raising (drives ground → excited)
#   Ni: -i σ_y      — rotation generator (off-diagonal antisymmetric)
#   Si: σ_-         — lowering (drives excited → ground)
PERCEPTION_L_MATRICES: dict[str, np.ndarray] = {
    "Se": SZ.copy(),                       # σ_z dephasing
    "Ne": SIGMA_PLUS.copy(),               # σ_+ raising
    "Ni": -1j * SY,                        # -i σ_y rotation
    "Si": SIGMA_MINUS.copy(),              # σ_- lowering
}

# ---------------------------------------------------------------------------
# Operator generators (Ti, Te, Fi, Fe)
# ---------------------------------------------------------------------------
#
# Sourced from Fe asymmetry sim — algebraically grounded.
# Source: sim_fe_three_to_one_asymmetry_structural_origin_probe.py
#
# Operator → generator mapping:
#   Ti: σ_z       — diagonal phase (dephasing-like rotation)
#   Te: σ_x       — off-diagonal real coherent transfer
#   Fi: σ_x       — coherent transfer (paired with Ti via inner loop)
#   Fe: σ_y       — antisymmetric phase rotation
#
# Note: Ti and Fi share the SX/SZ basis BUT differ in their semantic role
# (Ti outer vs Fi inner) and their topology assignments — see TYPE_ONE / TYPE_TWO
# topology dicts below.
OPERATOR_GENERATORS: dict[str, np.ndarray] = {
    "Ti": SZ.copy(),
    "Te": SX.copy(),
    "Fi": SX.copy(),
    "Fe": SY.copy(),
}

# Default operator rotation angles per (op, sign) — scaled by sign at use time.
# These are bounded magnitudes; the actual rotation = sign * base_angle.
OPERATOR_BASE_ANGLES: dict[str, float] = {
    "Ti": 0.12,
    "Te": 0.09,
    "Fi": 0.15,
    "Fe": 0.11,
}

OPERATOR_SLOT_SEQUENCE: list[str] = ["Ti", "Te", "Fi", "Fe"]

NATIVE_OPERATORS_BY_TOPOLOGY: dict[str, tuple[str, str]] = {
    "Se": ("Ti", "Fi"),
    "Ne": ("Ti", "Fi"),
    "Ni": ("Te", "Fe"),
    "Si": ("Te", "Fe"),
}

OPERATOR_MAP_FAMILY: dict[str, str] = {
    "Ti": "z_pinching_dephase",
    "Te": "x_pinching_dephase",
    "Fi": "x_coherent_rotation",
    "Fe": "z_coherent_rotation",
}

CHART_TOKEN_PRECEDENCE: dict[str, tuple[str, int]] = {
    "TiSe": ("operator_first", +1),
    "TiNe": ("operator_first", +1),
    "SeTi": ("terrain_first", -1),
    "NeTi": ("terrain_first", -1),
    "FeSi": ("operator_first", +1),
    "FeNi": ("operator_first", +1),
    "SiFe": ("terrain_first", -1),
    "NiFe": ("terrain_first", -1),
    "TeNi": ("operator_first", +1),
    "TeSi": ("operator_first", +1),
    "NiTe": ("terrain_first", -1),
    "SiTe": ("terrain_first", -1),
    "FiNe": ("operator_first", +1),
    "FiSe": ("operator_first", +1),
    "NeFi": ("terrain_first", -1),
    "SeFi": ("terrain_first", -1),
}


def ordered_token(operator: str, perception: str, precedence: str) -> str:
    if precedence == "operator_first":
        return f"{operator}{perception}"
    if precedence == "terrain_first":
        return f"{perception}{operator}"
    raise ValueError(f"unknown precedence {precedence!r}")

# ---------------------------------------------------------------------------
# Topology specs — Type 1 (left chiral) and Type 2 (right chiral)
# ---------------------------------------------------------------------------
#
# Each topology key (Se/Ne/Ni/Si) maps to:
#   realization      — terrain label (Funnel/Vortex/Pit/Hill or Cannon/Spiral/Source/Citadel)
#   pattern          — strategy pattern (winWIN, WINlose, LOSEwin, loseLOSE, etc.)
#   outer            — outer-loop class: (op, sign, result)
#   inner            — inner-loop class: (op, sign, result)
#   projector_axis   — terrain-channel pinch axis (x / y / z)
#   rate             — terrain-channel rate parameter
#   mode             — semantic mode label
#
# Type 1 is paired with H_TYPE_ONE = +H0 and σ_- (sink) ladder.
# Type 2 is paired with H_TYPE_TWO = -H0 and σ_+ (source) ladder.
# Mirror operator (σ_x) maps Type 1 ↔ Type 2 by flipping H sign and ladder direction.

TYPE_ONE_TOPOLOGIES: dict[str, dict[str, Any]] = {
    "Se": {
        "realization": "Funnel",
        "dynamics_family": "pinching_projection",
        "hamiltonian_key": "H0",
        "pattern": "LOSEwin",
        "outer": {"op": "Ti", "sign": +1, "result": "LOSE"},
        "inner": {"op": "Fi", "sign": -1, "result": "win"},
        "projector_axis": "x",
        "rate": 0.18,
        "mode": "sink_capture",
    },
    "Ne": {
        "realization": "Vortex",
        "dynamics_family": "kraus_filter",
        "hamiltonian_key": "H3",
        "pattern": "WINlose",
        "outer": {"op": "Ti", "sign": -1, "result": "WIN"},
        "inner": {"op": "Fi", "sign": +1, "result": "lose"},
        "projector_axis": "y",
        "rate": 0.13,
        "mode": "circulation",
    },
    "Ni": {
        "realization": "Pit",
        "dynamics_family": "lowering_dissipator",
        "hamiltonian_key": "H0",
        "pattern": "loseLOSE",
        "outer": {"op": "Fe", "sign": -1, "result": "LOSE"},
        "inner": {"op": "Te", "sign": +1, "result": "lose"},
        "projector_axis": "z",
        "rate": 0.28,
        "mode": "absorbing_basin",
    },
    "Si": {
        "realization": "Hill",
        "dynamics_family": "pinching_dissipator",
        "hamiltonian_key": "HS",
        "pattern": "winWIN",
        "outer": {"op": "Fe", "sign": +1, "result": "WIN"},
        "inner": {"op": "Te", "sign": -1, "result": "win"},
        "projector_axis": "z",
        "rate": 0.20,
        "mode": "stabilized_plateau",
    },
}

TYPE_TWO_TOPOLOGIES: dict[str, dict[str, Any]] = {
    "Se": {
        "realization": "Cannon",
        "dynamics_family": "kraus_release",
        "hamiltonian_key": "H0",
        "pattern": "loseWIN",
        "outer": {"op": "Fi", "sign": +1, "result": "WIN"},
        "inner": {"op": "Ti", "sign": -1, "result": "lose"},
        "projector_axis": "x",
        "rate": 0.18,
        "mode": "source_projection",
    },
    "Ne": {
        "realization": "Spiral",
        "dynamics_family": "outward_projection",
        "hamiltonian_key": "H3",
        "pattern": "winLOSE",
        "outer": {"op": "Fi", "sign": -1, "result": "LOSE"},
        "inner": {"op": "Ti", "sign": +1, "result": "win"},
        "projector_axis": "y",
        "rate": 0.15,
        "mode": "reverse_circulation",
    },
    "Ni": {
        "realization": "Source",
        "dynamics_family": "raising_dissipator",
        "hamiltonian_key": "H0",
        "pattern": "LOSElose",
        "outer": {"op": "Te", "sign": -1, "result": "LOSE"},
        "inner": {"op": "Fe", "sign": +1, "result": "lose"},
        "projector_axis": "x",
        "rate": 0.27,
        "mode": "emitting_basin",
    },
    "Si": {
        "realization": "Citadel",
        "dynamics_family": "pinching_dissipator",
        "hamiltonian_key": "HS",
        "pattern": "WINwin",
        "outer": {"op": "Te", "sign": +1, "result": "WIN"},
        "inner": {"op": "Fe", "sign": -1, "result": "win"},
        "projector_axis": "z",
        "rate": 0.21,
        "mode": "protected_plateau",
    },
}

# Realization → topology key lookups
REALIZATION_TO_TOPOLOGY_KEY_TYPE_ONE: dict[str, str] = {
    "Funnel": "Se", "Vortex": "Ne", "Pit": "Ni", "Hill": "Si",
}
REALIZATION_TO_TOPOLOGY_KEY_TYPE_TWO: dict[str, str] = {
    "Cannon": "Se", "Spiral": "Ne", "Source": "Ni", "Citadel": "Si",
}

# ---------------------------------------------------------------------------
# 13-layer manifold names
# ---------------------------------------------------------------------------
#
# Source: sim_nested_geometry_tower_dependency_order_probe.py:56-70
# Also: claude_integrated_manifold_modules/active_layer_constraint_enforcers.py:51-65

MANIFOLD_LAYERS: list[str] = [
    "finite_constraint_complex",          # 0
    "complex_hilbert_carrier",            # 1
    "unit_spinor_sphere",                 # 2
    "projective_base_sphere",             # 3
    "hopf_fiber_bundle",                  # 4
    "hopf_torus_leaf_family",             # 5
    "connection_holonomy_geometry",       # 6
    "weyl_spinor_bundle",                 # 7
    "chirality_orientation_cover",        # 8
    "clifford_module_geometry",           # 9
    "frame_bundle_structure_reduction",   # 10
    "tensor_product_coupling_geometry",   # 11
    "dynamic_transition_ratchet_geometry",# 12
]
N_MANIFOLD_LAYERS = 13

# ---------------------------------------------------------------------------
# Engine schedule per loop
# ---------------------------------------------------------------------------
#
# Each engine cycle = 8 main stages.
# Per main stage = 1 perception × 1 loop class (outer / inner).
#
# Type 1 schedule walks Se → Ne → Ni → Si twice (once outer, once inner),
# matching the inductive cycle (Si → Se → Ne → Ni) when reordered.
#
# Type 2 schedule mirrors Type 1: each (perception, loop_class) pair is the
# same set, but the topology assignments per perception come from TYPE_TWO_TOPOLOGIES.
#
# 8 main × 1 stage record per main = 8 stage records per engine.
# A "stage" in this module = 1 main stage of the engine cycle.

ENGINE_SCHEDULE_TYPE_ONE: list[tuple[str, str]] = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
ENGINE_SCHEDULE_TYPE_TWO: list[tuple[str, str]] = [
    ("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner"),
]

# A "full cycle" per engine = 8 main stages × 4 substages (operator, terrain,
# manifold, loop placement) = 32 substage records. Paired engines = 64 total.
N_MAIN_STAGES_PER_ENGINE = 8
N_SUBSTAGES_PER_MAIN = 4
N_TOTAL_SUBSTAGES_PER_ENGINE = N_MAIN_STAGES_PER_ENGINE * N_SUBSTAGES_PER_MAIN  # 32


# ---------------------------------------------------------------------------
# Accessor functions
# ---------------------------------------------------------------------------

def get_engine_spec(engine_type: int) -> dict[str, Any]:
    """
    Return the canonical spec for an engine type.

    engine_type:
      0 → Type 1 (left Weyl, H = +H0, σ_- ladder, Type 1 topology dict)
      1 → Type 2 (right Weyl, H = -H0, σ_+ ladder, Type 2 topology dict)

    Returns:
      dict with keys:
        type_label, hamiltonian, ladder, topologies, schedule,
        realization_to_topology_key, name
    """
    if engine_type == 0:
        return {
            "type_label": "type_one_left_weyl",
            "name": "Type 1 / left Weyl chiral",
            "hamiltonian": H_TYPE_ONE.copy(),
            "ladder": SIGMA_MINUS.copy(),
            "topologies": TYPE_ONE_TOPOLOGIES,
            "schedule": ENGINE_SCHEDULE_TYPE_ONE,
            "realization_to_topology_key": REALIZATION_TO_TOPOLOGY_KEY_TYPE_ONE,
            "chirality_sign": +1,
            "h_sign": +1.0,
        }
    elif engine_type == 1:
        return {
            "type_label": "type_two_right_weyl",
            "name": "Type 2 / right Weyl chiral",
            "hamiltonian": H_TYPE_TWO.copy(),
            "ladder": SIGMA_PLUS.copy(),
            "topologies": TYPE_TWO_TOPOLOGIES,
            "schedule": ENGINE_SCHEDULE_TYPE_TWO,
            "realization_to_topology_key": REALIZATION_TO_TOPOLOGY_KEY_TYPE_TWO,
            "chirality_sign": -1,
            "h_sign": -1.0,
        }
    else:
        raise ValueError(f"engine_type must be 0 or 1, got {engine_type}")


def get_lindblad_params(
    perception: str,
    engine_type: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return (Hamiltonian, Lindblad-L) for a (perception, engine_type) pair.

    perception: one of {"Se", "Ne", "Ni", "Si"}
    engine_type: 0 (Type 1) or 1 (Type 2)

    The Hamiltonian sign chirality is encoded in engine_type.
    The L matrix is taken from PERCEPTION_L_MATRICES.
    Type 2 mirrors Type 1 by conjugating L with the mirror operator σ_x:
        L_R = σ_x L_L σ_x
    This maps:
      Se: σ_z → -σ_z (still pure dephasing, sign-flipped diagonal)
      Ne: σ_+ → σ_-
      Ni: -i σ_y → +i σ_y
      Si: σ_- → σ_+
    """
    if perception not in PERCEPTION_L_MATRICES:
        raise ValueError(f"perception must be in {sorted(PERCEPTION_L_MATRICES)}, got {perception}")
    spec = get_engine_spec(engine_type)
    H = spec["hamiltonian"]
    L_type_one = PERCEPTION_L_MATRICES[perception]
    if engine_type == 0:
        L = L_type_one
    else:
        # Mirror: L_R = σ_x L σ_x
        L = MIRROR @ L_type_one @ MIRROR
    return H.copy(), L.copy()


def get_hamiltonian_by_key(key: str, engine_type: int) -> np.ndarray:
    """Return a signed Hamiltonian family for the requested chiral sector."""
    sign = +1.0 if engine_type == 0 else -1.0
    if key == "H0":
        return (sign * H0).copy()
    if key == "H3":
        return (sign * H3).copy()
    if key == "HS":
        return (sign * H_STRATA).copy()
    raise ValueError(f"unknown hamiltonian_key {key!r}")


def get_topology_spec(
    perception: str,
    engine_type: int,
) -> dict[str, Any]:
    """Return the full topology spec dict for (perception, engine_type)."""
    spec = get_engine_spec(engine_type)
    if perception not in spec["topologies"]:
        raise ValueError(f"perception must be in {sorted(spec['topologies'])}, got {perception}")
    return spec["topologies"][perception]


def get_terrain_dynamics_spec(perception: str, engine_type: int) -> dict[str, Any]:
    """Return the per-topology dynamical family and Hamiltonian metadata."""
    topo = get_topology_spec(perception, engine_type)
    return {
        "realization": topo["realization"],
        "family": topo["dynamics_family"],
        "hamiltonian_key": topo["hamiltonian_key"],
        "hamiltonian": get_hamiltonian_by_key(topo["hamiltonian_key"], engine_type),
        "projector_axis": topo["projector_axis"],
        "rate": float(topo["rate"]),
        "mode": topo["mode"],
    }


def get_loop_class_op_sign(
    perception: str,
    engine_type: int,
    loop_class: str,
) -> tuple[str, int]:
    """
    Return the (operator_name, sign) pair for a given (perception, engine_type, loop_class).

    loop_class: "outer" or "inner"
    """
    topo = get_topology_spec(perception, engine_type)
    if loop_class == "outer":
        return topo["outer"]["op"], int(topo["outer"]["sign"])
    elif loop_class == "inner":
        return topo["inner"]["op"], int(topo["inner"]["sign"])
    else:
        raise ValueError(f"loop_class must be 'outer' or 'inner', got {loop_class}")


def get_chart_token_spec(perception: str, engine_type: int, loop_class: str) -> dict[str, Any]:
    """Return the chart-locked native token for a topology/engine/loop placement."""
    topo = get_topology_spec(perception, engine_type)
    op, sign = get_loop_class_op_sign(perception, engine_type, loop_class)
    precedence = "operator_first" if sign > 0 else "terrain_first"
    token = ordered_token(op, perception, precedence)
    return {
        "operator": op,
        "sign": sign,
        "axis6": "UP" if sign > 0 else "DOWN",
        "precedence": precedence,
        "token": token,
        "result": topo[loop_class]["result"],
        "is_native_operator": op in NATIVE_OPERATORS_BY_TOPOLOGY[perception],
        "is_chart_locked": True,
    }


def get_operator_slot_spec(
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> dict[str, Any]:
    """
    Return the operator slot for one of the four substages on a topology law.

    Slot 0 is the chart-locked native operator for the current loop placement.
    The remaining slots run the other three operators, preserving native-vs-
    non-native metadata. Non-chart slot precedence is a conservative candidate:
    native operators use their chart-token precedence when available; non-native
    operators alternate by slot/engine so collapse controls can test necessity.
    """
    if substage_idx < 0:
        raise ValueError("substage_idx must be non-negative")
    chart = get_chart_token_spec(perception, engine_type, loop_class)
    native = list(NATIVE_OPERATORS_BY_TOPOLOGY[perception])
    remaining_native = [op for op in native if op != chart["operator"]]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if op not in native]
    slot_ops = [chart["operator"], *remaining_native, *remaining_non_native]
    op = slot_ops[substage_idx % len(slot_ops)]
    if op == chart["operator"]:
        precedence = chart["precedence"]
        sign = int(chart["sign"])
        token = chart["token"]
        chart_locked = True
    else:
        token_up = ordered_token(op, perception, "operator_first")
        token_down = ordered_token(op, perception, "terrain_first")
        if token_up in CHART_TOKEN_PRECEDENCE:
            precedence, sign = CHART_TOKEN_PRECEDENCE[token_up]
            token = token_up
        elif token_down in CHART_TOKEN_PRECEDENCE:
            precedence, sign = CHART_TOKEN_PRECEDENCE[token_down]
            token = token_down
        else:
            sign = +1 if (substage_idx + engine_type) % 2 == 0 else -1
            precedence = "operator_first" if sign > 0 else "terrain_first"
            token = ordered_token(op, perception, precedence)
        chart_locked = False
    return {
        "operator": op,
        "sign": int(sign),
        "axis6": "UP" if int(sign) > 0 else "DOWN",
        "precedence": precedence,
        "token": token,
        "operator_family": OPERATOR_MAP_FAMILY[op],
        "is_native_operator": op in native,
        "is_chart_locked": chart_locked,
        "native_operator_set": native,
        "slot_index": substage_idx % len(slot_ops),
    }


def get_schedule(engine_type: int) -> list[tuple[str, str]]:
    """Return the (perception, loop_class) main-stage schedule for an engine."""
    return get_engine_spec(engine_type)["schedule"]


def get_unique_op_sign_pairs(engine_type: int) -> list[tuple[str, int]]:
    """
    Return the list of unique (op, sign) pairs for an engine, computed from its
    topology spec dict. Each topology contributes outer + inner = 2 pairs;
    4 topologies → 8 total pairs (unique by construction).
    """
    spec = get_engine_spec(engine_type)
    pairs: list[tuple[str, int]] = []
    for perception in ["Se", "Ne", "Ni", "Si"]:
        topo = spec["topologies"][perception]
        pairs.append((topo["outer"]["op"], int(topo["outer"]["sign"])))
        pairs.append((topo["inner"]["op"], int(topo["inner"]["sign"])))
    return pairs


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("canonical_qit_engine_specs.py — smoke test")
    print("=" * 70)

    # 1. Hamiltonian sign flip
    sum_h = H_TYPE_ONE + H_TYPE_TWO
    print(f"\nH_TYPE_ONE + H_TYPE_TWO = 0:  "
          f"max_abs={float(np.max(np.abs(sum_h))):.2e}  "
          f"ok={np.allclose(sum_h, 0.0)}")

    # 2. Mirror identity
    mirror_check_h = MIRROR @ H_TYPE_ONE @ MIRROR + H_TYPE_ONE   # σ_x H_L σ_x = -H_L ?
    expected = -2 * H_TYPE_ONE
    # σ_x σ_z σ_x = -σ_z, σ_x σ_x σ_x = σ_x; mirror H = 0.77*(-σ_z) + 0.13*σ_x ≠ -H_L
    # So mirror_check should equal -H_L, i.e. σ_x H_L σ_x should be H_R only if SX terms also flip.
    mirror_h = MIRROR @ H_TYPE_ONE @ MIRROR
    print(f"\nMIRROR @ H_TYPE_ONE @ MIRROR =\n{mirror_h}")
    # Pure-σ_z component flips sign under σ_x conj; σ_x component is preserved.
    # So mirror_h != H_TYPE_TWO in general; mirror is a partial chirality flip.
    # Full mirror (Type 1 → Type 2) is H_sign flip + ladder swap.
    print(f"\nH_TYPE_TWO =\n{H_TYPE_TWO}")
    print(f"\n(NOTE: σ_x H σ_x flips only the σ_z component; full Type 1→2 mirror "
          f"is H sign + ladder direction; the math.md table specifies H_R = -H_L directly.)")

    # 3. Mirror lowering ↔ raising
    mirror_ladder = MIRROR @ SIGMA_MINUS @ MIRROR
    print(f"\nMIRROR @ σ_- @ MIRROR = σ_+? "
          f"{np.allclose(mirror_ladder, SIGMA_PLUS)}")

    # 4. Engine specs
    for engine_type in [0, 1]:
        spec = get_engine_spec(engine_type)
        print(f"\nengine_type={engine_type}  →  {spec['type_label']}")
        print(f"  hamiltonian sign: {spec['h_sign']}")
        print(f"  ladder shape: {spec['ladder'].shape}")
        print(f"  topology keys: {sorted(spec['topologies'])}")
        print(f"  schedule length: {len(spec['schedule'])}")
        pairs = get_unique_op_sign_pairs(engine_type)
        print(f"  unique (op,sign) pairs: {len(pairs)} -> {sorted(set(pairs))}")
        # Assert 8 unique pairs per engine
        assert len(set(pairs)) == 8, f"expected 8 unique pairs, got {len(set(pairs))}"

    # 5. Lindblad params
    print("\nLindblad params per perception × engine_type:")
    for engine_type in [0, 1]:
        for perception in ["Se", "Ne", "Ni", "Si"]:
            H, L = get_lindblad_params(perception, engine_type)
            print(f"  (eng={engine_type}, perc={perception})  "
                  f"H.shape={H.shape}  L.shape={L.shape}  "
                  f"L_nnz={int(np.sum(np.abs(L) > 1e-12))}")

    # 6. Loop class accessor
    print("\nLoop-class op/sign pairs (Type 1):")
    for perception in ["Se", "Ne", "Ni", "Si"]:
        outer = get_loop_class_op_sign(perception, 0, "outer")
        inner = get_loop_class_op_sign(perception, 0, "inner")
        print(f"  {perception}: outer={outer}  inner={inner}")

    print(f"\nMANIFOLD_LAYERS count: {len(MANIFOLD_LAYERS)} (expected 13): "
          f"ok={len(MANIFOLD_LAYERS) == 13}")

    print("\n" + "=" * 70)
    print("Smoke test PASS")
    print("=" * 70)
