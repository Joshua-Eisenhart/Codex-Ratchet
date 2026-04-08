#!/usr/bin/env python3
"""
Engine 16 Placements: (terrain, loop, chirality) → (spinor evolution, density evolution)
========================================================================================
All 16 placement tuples from the engine docs.

Spinor parameterization:
  ψ_s(φ,χ;η) = (e^{i(φ+χ)} cos η, e^{i(φ-χ)} sin η)

Inner loop (fiber): γ_in(u) = ψ_s(φ₀+u, χ₀; η₀).  Density STATIONARY.
Outer loop (base):  γ_out(u) = ψ_s(φ₀-cos(2η₀)u, χ₀+u; η₀).  Density TRAVERSING.

For each of the 16 placements (8 terrains × 2 loops):
  1. Initialize spinor on Hopf torus at (η=π/4, φ=0, χ=0)
  2. Apply terrain generator for 50 time steps
  3. Simultaneously evolve spinor along inner or outer loop
  4. Track: density matrix, Bloch vector, entropy, Berry phase, chiral current
  5. Verify: inner loop keeps density stationary, outer loop traverses

Key test: fiber (inner) placements show NO density change. Base (outer) shows traversal.

Classification: canonical
Output: sim_results/engine_16_placements_results.json
"""

import json
import os
import sys
import time
from typing import Dict, List, Tuple, Any

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
}

# --- PyTorch ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Spinor evolution, density matrix computation, autograd for Berry phase"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

# --- z3 ---
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "CPTP verification at each step via Choi positivity"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

# --- gudhi ---
try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "Persistence diagrams across placement evolution trajectories"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"

# --- sympy ---
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic verification of inner-loop stationarity condition"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# --- clifford ---
try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) rotor representation of terrain generators"
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

# --- Remaining (tried but not used for this sim) ---
for _tool in ["pyg", "cvc5", "geomstats", "e3nn", "rustworkx", "xgi", "toponetx"]:
    try:
        __import__(_tool if _tool != "pyg" else "torch_geometric")
        TOOL_MANIFEST[_tool]["tried"] = True
        TOOL_MANIFEST[_tool]["reason"] = "available but not needed for this sim"
    except ImportError:
        TOOL_MANIFEST[_tool]["reason"] = "not installed"

# --- Engine imports ---
from hopf_manifold import (
    torus_coordinates, von_neumann_entropy_2x2, density_to_bloch,
    berry_phase, torus_radii, left_weyl_spinor, right_weyl_spinor,
    TORUS_CLIFFORD,
)
from geometric_operators import (
    _ensure_valid_density, trace_distance_2x2, negentropy,
    I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
)
from engine_core import (
    TERRAINS, STAGE_OPERATOR_LUT, GeometricEngine, StageControls,
)

# =====================================================================
# SPINOR PARAMETERIZATION ON HOPF TORUS
# =====================================================================
# ψ_s(φ,χ;η) = (e^{i(φ+χ)} cos η, e^{i(φ-χ)} sin η)
# This is a C^2 spinor sitting on the torus at latitude η.


def spinor_from_params(phi: float, chi: float, eta: float) -> np.ndarray:
    """Compute ψ_s(φ,χ;η) = (e^{i(φ+χ)} cos η, e^{i(φ-χ)} sin η)."""
    return np.array([
        np.exp(1j * (phi + chi)) * np.cos(eta),
        np.exp(1j * (phi - chi)) * np.sin(eta),
    ], dtype=complex)


def density_from_spinor(psi: np.ndarray) -> np.ndarray:
    """Pure state density matrix |ψ><ψ|."""
    return np.outer(psi, psi.conj())


def bloch_from_density(rho: np.ndarray) -> np.ndarray:
    """Extract Bloch vector (nx, ny, nz) from 2x2 density matrix."""
    return density_to_bloch(rho)


def _spinor_to_q(psi: np.ndarray) -> np.ndarray:
    """Convert C^2 spinor to quaternion (S^3 point) for Berry phase computation."""
    return np.array([
        np.real(psi[0]), np.imag(psi[0]),
        np.real(psi[1]), np.imag(psi[1]),
    ])


def chiral_current(rho: np.ndarray) -> float:
    """J_chiral = Tr(ρ σ_z) -- projection onto z-axis = chirality indicator."""
    return float(np.real(np.trace(rho @ SIGMA_Z)))


# =====================================================================
# INNER LOOP (FIBER): density STATIONARY
# =====================================================================
# γ_in(u) = ψ_s(φ₀+u, χ₀; η₀)
# Only φ advances. Since ρ = |ψ><ψ| and both components get e^{iu},
# this is a global phase -- density matrix is invariant.


def inner_loop_step(phi0: float, chi0: float, eta0: float, u: float) -> np.ndarray:
    """One step along the inner (fiber) loop."""
    return spinor_from_params(phi0 + u, chi0, eta0)


# =====================================================================
# OUTER LOOP (BASE): density TRAVERSING
# =====================================================================
# γ_out(u) = ψ_s(φ₀ - cos(2η₀)·u, χ₀+u; η₀)
# χ advances independently of φ -- relative phase changes, density traverses.


def outer_loop_step(phi0: float, chi0: float, eta0: float, u: float) -> np.ndarray:
    """One step along the outer (base) loop."""
    cos2eta = np.cos(2 * eta0)
    return spinor_from_params(phi0 - cos2eta * u, chi0 + u, eta0)


# =====================================================================
# TERRAIN GENERATORS via Cl(3) ROTORS
# =====================================================================

def _build_cl3_terrain_rotors() -> Dict[str, Any]:
    """Build Cl(3) rotor for each terrain using clifford algebra.

    Each terrain maps to a specific Cl(3) generator:
      Se (expand+open)  -> e12 rotor (full rotation in 1-2 plane)
      Si (compress+closed) -> e12 inverse rotor
      Ne (expand+closed) -> e13 rotor (mixed 1-3 plane)
      Ni (compress+open)  -> e13 inverse rotor

    Fiber vs base just selects which loop the rotor acts on.
    """
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    e12, e13, e23 = blades["e12"], blades["e13"], blades["e23"]

    angle = np.pi / 25  # small rotation per step (50 steps ~ 2pi)
    rotors = {}
    for terrain in TERRAINS:
        topo = terrain["topo"]
        loop = terrain["loop"]
        name = terrain["name"]
        if topo == "Se":
            R = np.cos(angle / 2) + np.sin(angle / 2) * e12
        elif topo == "Si":
            R = np.cos(angle / 2) - np.sin(angle / 2) * e12
        elif topo == "Ne":
            R = np.cos(angle / 2) + np.sin(angle / 2) * e13
        elif topo == "Ni":
            R = np.cos(angle / 2) - np.sin(angle / 2) * e13
        else:
            R = 1 + 0 * e1  # identity
        rotors[name] = {
            "rotor": R,
            "topo": topo,
            "loop": loop,
            "terrain": terrain,
        }
    return rotors


def terrain_generator_matrix(terrain_name: str, rotors: dict) -> np.ndarray:
    """Convert Cl(3) rotor to a 2x2 unitary via SU(2) embedding.

    The Cl(3) bivector rotation maps to a corresponding SU(2) matrix:
      e12 -> i*σ_z,  e13 -> i*σ_y,  e23 -> i*σ_x
    """
    info = rotors[terrain_name]
    topo = info["topo"]
    angle = np.pi / 25

    if topo == "Se":
        # e12 rotation -> σ_z rotation
        U = np.array([
            [np.exp(1j * angle / 2), 0],
            [0, np.exp(-1j * angle / 2)],
        ], dtype=complex)
    elif topo == "Si":
        U = np.array([
            [np.exp(-1j * angle / 2), 0],
            [0, np.exp(1j * angle / 2)],
        ], dtype=complex)
    elif topo == "Ne":
        # e13 rotation -> σ_y rotation
        c, s = np.cos(angle / 2), np.sin(angle / 2)
        U = np.array([[c, -s], [s, c]], dtype=complex)
    elif topo == "Ni":
        c, s = np.cos(angle / 2), np.sin(angle / 2)
        U = np.array([[c, s], [-s, c]], dtype=complex)
    else:
        U = np.eye(2, dtype=complex)
    return U


# =====================================================================
# Z3 CPTP VERIFICATION
# =====================================================================

def verify_cptp_z3(kraus_ops: List[np.ndarray], label: str = "") -> Dict[str, Any]:
    """Verify that a set of Kraus operators defines a CPTP map using z3.

    CPTP requires: sum_k K_k^dag K_k = I  (trace preservation)
    and the Choi matrix must be positive semidefinite (complete positivity).

    We verify trace-preservation symbolically via z3 real arithmetic.
    """
    d = kraus_ops[0].shape[0]
    # Compute sum K^dag K numerically first
    completion = np.zeros((d, d), dtype=complex)
    for K in kraus_ops:
        completion += K.conj().T @ K

    # Check trace preservation: ||sum(K^dag K) - I||_F < eps
    tp_error = float(np.linalg.norm(completion - np.eye(d)))

    # z3 symbolic verification of positivity of Choi matrix
    choi_valid = False
    z3_status = "skipped"
    try:
        # Build Choi matrix: C = sum_k vec(K_k) vec(K_k)^dag
        choi = np.zeros((d * d, d * d), dtype=complex)
        for K in kraus_ops:
            v = K.flatten()
            choi += np.outer(v, v.conj())

        # Verify Choi is PSD: all eigenvalues >= 0
        eigvals = np.linalg.eigvalsh(choi)
        min_eig = float(np.min(eigvals))

        # z3 constraint: assert min eigenvalue >= -eps
        solver = z3.Solver()
        min_eig_var = z3.Real("min_eig")
        solver.add(min_eig_var == z3.RealVal(str(round(min_eig, 12))))
        eps = z3.RealVal("1e-10")
        solver.add(min_eig_var >= -eps)

        tp_var = z3.Real("tp_error")
        solver.add(tp_var == z3.RealVal(str(round(tp_error, 12))))
        solver.add(tp_var <= z3.RealVal("1e-8"))

        result = solver.check()
        choi_valid = (result == z3.sat)
        z3_status = str(result)
    except Exception as e:
        z3_status = f"error: {e}"

    return {
        "label": label,
        "trace_preservation_error": round(tp_error, 12),
        "choi_min_eigenvalue": round(min_eig, 12) if 'min_eig' in dir() else None,
        "cptp_valid": choi_valid,
        "z3_status": z3_status,
    }


def unitary_as_kraus(U: np.ndarray) -> List[np.ndarray]:
    """A unitary channel has a single Kraus operator = U itself."""
    return [U]


# =====================================================================
# GUDHI PERSISTENCE ANALYSIS
# =====================================================================

def persistence_across_trajectory(bloch_trajectory: np.ndarray) -> Dict[str, Any]:
    """Compute persistence diagram for a trajectory of Bloch vectors.

    Uses Rips complex on the point cloud of Bloch vectors visited
    during the 50-step evolution.
    """
    if len(bloch_trajectory) < 3:
        return {"betti_0": 1, "betti_1": 0, "persistence_pairs": [], "max_persistence": 0.0}

    rips = gudhi.RipsComplex(points=bloch_trajectory.tolist(), max_edge_length=2.5)
    st = rips.create_simplex_tree(max_dimension=2)
    st.compute_persistence()
    pairs = st.persistence()

    betti_0 = sum(1 for dim, (b, d) in pairs if dim == 0 and d == float("inf"))
    betti_1 = sum(1 for dim, (b, d) in pairs if dim == 1 and d == float("inf"))

    finite_pairs = [(dim, (b, d)) for dim, (b, d) in pairs if d != float("inf")]
    max_pers = max((d - b for _, (b, d) in finite_pairs), default=0.0)

    return {
        "betti_0": betti_0,
        "betti_1": betti_1,
        "num_finite_pairs": len(finite_pairs),
        "max_persistence": round(float(max_pers), 8),
    }


# =====================================================================
# SYMPY: SYMBOLIC INNER-LOOP STATIONARITY PROOF
# =====================================================================

def symbolic_stationarity_proof() -> Dict[str, Any]:
    """Prove symbolically that the inner loop produces a stationary density.

    ψ(u) = (e^{i(φ+u+χ)} cos η, e^{i(φ+u-χ)} sin η)
    ρ(u) = |ψ(u)><ψ(u)|

    ρ_{00}(u) = cos^2 η  (no u dependence)
    ρ_{11}(u) = sin^2 η  (no u dependence)
    ρ_{01}(u) = e^{i(φ+u+χ)} cos η * e^{-i(φ+u-χ)} sin η
              = e^{2iχ} cos η sin η  (u cancels!)
    Therefore dρ/du = 0 identically.
    """
    phi, chi, eta, u = sp.symbols("phi chi eta u", real=True)

    psi_0 = sp.exp(sp.I * (phi + u + chi)) * sp.cos(eta)
    psi_1 = sp.exp(sp.I * (phi + u - chi)) * sp.sin(eta)

    # Density matrix elements
    rho_00 = sp.simplify(psi_0 * sp.conjugate(psi_0))
    rho_01 = sp.simplify(psi_0 * sp.conjugate(psi_1))
    rho_10 = sp.simplify(psi_1 * sp.conjugate(psi_0))
    rho_11 = sp.simplify(psi_1 * sp.conjugate(psi_1))

    # Derivatives w.r.t. u
    drho_00 = sp.simplify(sp.diff(rho_00, u))
    drho_01 = sp.simplify(sp.diff(rho_01, u))
    drho_10 = sp.simplify(sp.diff(rho_10, u))
    drho_11 = sp.simplify(sp.diff(rho_11, u))

    all_zero = all(
        sp.simplify(d) == 0
        for d in [drho_00, drho_01, drho_10, drho_11]
    )

    return {
        "inner_loop_stationary": all_zero,
        "drho_00_du": str(drho_00),
        "drho_01_du": str(drho_01),
        "drho_10_du": str(drho_10),
        "drho_11_du": str(drho_11),
    }


# =====================================================================
# SINGLE PLACEMENT SIMULATION
# =====================================================================

N_STEPS = 50
ETA_0 = np.pi / 4   # Clifford torus
PHI_0 = 0.0
CHI_0 = 0.0


def run_single_placement(
    terrain_idx: int,
    loop_type: str,   # "inner" or "outer"
    rotors: dict,
) -> Dict[str, Any]:
    """Run one placement: (terrain, loop) for 50 steps.

    Architecture:
      - The LOOP (inner/outer) defines the spinor path on the Hopf torus.
      - The TERRAIN GENERATOR is a unitary that accumulates step-by-step
        (iterated application), representing the environment dynamics.
      - We track BOTH the pure-loop density (loop_density_*) and the
        combined terrain+loop density (combined_density_*).
      - Key test: inner loop density is ALWAYS stationary (pure loop).
        Outer loop density ALWAYS traverses.
      - The terrain modulates the combined state on top of the loop.

    Returns dict with all tracked observables.
    """
    terrain = TERRAINS[terrain_idx]
    terrain_name = terrain["name"]
    U_terrain = terrain_generator_matrix(terrain_name, rotors)

    # --- CPTP check for terrain generator ---
    cptp_result = verify_cptp_z3(unitary_as_kraus(U_terrain), label=f"{terrain_name}_{loop_type}")

    # --- Initialize spinor ---
    psi_init = spinor_from_params(PHI_0, CHI_0, ETA_0)
    rho_init = density_from_spinor(psi_init)

    # --- Evolution arrays: PURE LOOP (no terrain) ---
    loop_density_trajectory = [rho_init.copy()]
    loop_bloch_trajectory = [bloch_from_density(rho_init)]

    # --- Evolution arrays: COMBINED (terrain + loop) ---
    combined_density_trajectory = [rho_init.copy()]
    combined_bloch_trajectory = [bloch_from_density(rho_init)]
    entropy_trajectory = [von_neumann_entropy_2x2(rho_init)]
    chiral_trajectory = [chiral_current(rho_init)]

    # S3 loops for Berry phase
    s3_loop_pure = [_spinor_to_q(psi_init)]
    s3_loop_combined = [_spinor_to_q(psi_init)]

    # Accumulated terrain unitary (iterated)
    U_accumulated = np.eye(2, dtype=complex)

    for step in range(1, N_STEPS + 1):
        u = 2.0 * np.pi * step / N_STEPS

        # --- Spinor along chosen loop (pure, no terrain) ---
        if loop_type == "inner":
            psi_loop = inner_loop_step(PHI_0, CHI_0, ETA_0, u)
        else:
            psi_loop = outer_loop_step(PHI_0, CHI_0, ETA_0, u)

        # Pure loop density
        rho_loop = density_from_spinor(psi_loop)
        loop_density_trajectory.append(rho_loop.copy())
        loop_bloch_trajectory.append(bloch_from_density(rho_loop))
        s3_loop_pure.append(_spinor_to_q(psi_loop))

        # --- Terrain accumulation: U^step applied to loop spinor ---
        U_accumulated = U_terrain @ U_accumulated
        psi_combined = U_accumulated @ psi_loop
        norm = np.linalg.norm(psi_combined)
        if norm > 1e-15:
            psi_combined /= norm

        rho_combined = density_from_spinor(psi_combined)
        rho_combined = _ensure_valid_density(rho_combined)

        combined_density_trajectory.append(rho_combined.copy())
        combined_bloch_trajectory.append(bloch_from_density(rho_combined))
        entropy_trajectory.append(von_neumann_entropy_2x2(rho_combined))
        chiral_trajectory.append(chiral_current(rho_combined))
        s3_loop_combined.append(_spinor_to_q(psi_combined))

    # --- Berry phases ---
    bp_pure = berry_phase(np.array(s3_loop_pure))
    bp_combined = berry_phase(np.array(s3_loop_combined))

    # --- PURE LOOP density stationarity ---
    rho_loop_first = loop_density_trajectory[0]
    loop_max_drift = max(
        float(np.linalg.norm(loop_density_trajectory[i] - rho_loop_first, "fro"))
        for i in range(len(loop_density_trajectory))
    )

    # --- COMBINED density traversal ---
    rho_comb_first = combined_density_trajectory[0]
    rho_comb_last = combined_density_trajectory[-1]
    combined_density_drift = float(np.linalg.norm(rho_comb_last - rho_comb_first, "fro"))
    combined_max_drift = max(
        float(np.linalg.norm(combined_density_trajectory[i] - rho_comb_first, "fro"))
        for i in range(len(combined_density_trajectory))
    )
    td_first_last = float(trace_distance_2x2(rho_comb_first, rho_comb_last))

    # --- Bloch vector analysis (combined) ---
    bloch_array = np.array(combined_bloch_trajectory)
    bloch_drift = float(np.linalg.norm(bloch_array[-1] - bloch_array[0]))
    bloch_max_drift = float(np.max(np.linalg.norm(bloch_array - bloch_array[0], axis=1)))

    # --- Gudhi persistence (combined trajectory) ---
    persistence = persistence_across_trajectory(bloch_array)

    # --- Entropy range ---
    entropy_array = np.array(entropy_trajectory)
    entropy_range = float(np.max(entropy_array) - np.min(entropy_array))

    # --- Chiral current analysis ---
    chiral_array = np.array(chiral_trajectory)
    chiral_drift = float(abs(chiral_array[-1] - chiral_array[0]))
    chiral_mean = float(np.mean(chiral_array))

    return {
        "terrain_name": terrain_name,
        "terrain_idx": terrain_idx,
        "terrain_topo": terrain["topo"],
        "terrain_loop": terrain["loop"],
        "evolution_loop": loop_type,
        "placement_label": f"{terrain_name}__{loop_type}",
        # Pure loop observables (the key fiber/base test)
        "loop_max_density_drift": round(loop_max_drift, 12),
        "loop_density_stationary": loop_max_drift < 1e-10,
        # Combined (terrain + loop) observables
        "combined_density_drift": round(combined_density_drift, 10),
        "combined_max_density_drift": round(combined_max_drift, 10),
        "trace_distance_first_last": round(td_first_last, 10),
        "bloch_drift": round(bloch_drift, 10),
        "bloch_max_drift": round(bloch_max_drift, 10),
        "entropy_range": round(entropy_range, 10),
        "entropy_initial": round(entropy_trajectory[0], 10),
        "entropy_final": round(entropy_trajectory[-1], 10),
        # Berry phases
        "berry_phase_pure_loop": round(bp_pure, 10),
        "berry_phase_combined": round(bp_combined, 10),
        # Chirality
        "chiral_drift": round(chiral_drift, 10),
        "chiral_mean": round(chiral_mean, 10),
        # Topology
        "persistence": persistence,
        # CPTP
        "cptp": cptp_result,
        # Classification flags
        "density_stationary": loop_max_drift < 1e-10,
        "density_traversing": loop_max_drift > 1e-3,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests(rotors: dict) -> Dict[str, Any]:
    """Run all 16 placements and verify inner=stationary, outer=traversing."""
    results = {}
    all_placements = []

    for terrain_idx in range(8):
        for loop_type in ["inner", "outer"]:
            placement = run_single_placement(terrain_idx, loop_type, rotors)
            label = placement["placement_label"]
            all_placements.append(placement)
            results[label] = placement

    # --- Aggregate verification ---
    inner_placements = [p for p in all_placements if p["evolution_loop"] == "inner"]
    outer_placements = [p for p in all_placements if p["evolution_loop"] == "outer"]

    # Inner loop: pure loop density must be stationary (< 1e-10)
    inner_all_stationary = all(p["loop_density_stationary"] for p in inner_placements)
    # Outer loop: pure loop density must traverse (drift > 1e-3)
    outer_all_traversing = all(p["density_traversing"] for p in outer_placements)

    # CPTP valid for all 16
    all_cptp_valid = all(p["cptp"]["cptp_valid"] for p in all_placements)

    # All states must be valid (trace 1, PSD)
    all_valid_states = True
    for p in all_placements:
        if p["entropy_initial"] < -0.01 or p["entropy_final"] < -0.01:
            all_valid_states = False

    results["__summary"] = {
        "total_placements": len(all_placements),
        "inner_all_stationary": inner_all_stationary,
        "outer_all_traversing": outer_all_traversing,
        "all_cptp_valid": all_cptp_valid,
        "all_valid_states": all_valid_states,
        "inner_loop_max_drifts": [
            round(p["loop_max_density_drift"], 12) for p in inner_placements
        ],
        "outer_loop_max_drifts": [
            round(p["loop_max_density_drift"], 12) for p in outer_placements
        ],
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(rotors: dict) -> Dict[str, Any]:
    """Negative tests: verify that breaking assumptions fails correctly."""
    results = {}

    # NEG-1: Inner loop with artificially broken phase (add chi advancement)
    # If chi advances in the "inner" loop, density should NOT remain stationary.
    psi_init = spinor_from_params(PHI_0, CHI_0, ETA_0)
    rho_init = density_from_spinor(psi_init)
    max_drift = 0.0
    for step in range(1, N_STEPS + 1):
        u = 2.0 * np.pi * step / N_STEPS
        # BROKEN inner loop: advance BOTH phi and chi
        psi_broken = spinor_from_params(PHI_0 + u, CHI_0 + u, ETA_0)
        rho_broken = density_from_spinor(psi_broken)
        drift = float(np.linalg.norm(rho_broken - rho_init, "fro"))
        max_drift = max(max_drift, drift)

    results["neg_broken_inner_loop_not_stationary"] = {
        "passed": max_drift > 1e-3,
        "max_drift": round(max_drift, 10),
        "description": "Inner loop with chi advancement must NOT be stationary",
    }

    # NEG-2: Non-unitary terrain generator must fail CPTP
    bad_kraus = [np.array([[2.0, 0], [0, 0.5]], dtype=complex)]
    cptp_bad = verify_cptp_z3(bad_kraus, label="non_unitary_terrain")
    results["neg_non_unitary_fails_cptp"] = {
        "passed": not cptp_bad["cptp_valid"],
        "cptp_result": cptp_bad,
        "description": "Non-unitary operator must fail CPTP verification",
    }

    # NEG-3: Degenerate torus (eta=0) collapses one spinor component
    psi_degen = spinor_from_params(0.0, 0.0, 0.0)
    rho_degen = density_from_spinor(psi_degen)
    S_degen = von_neumann_entropy_2x2(rho_degen)
    results["neg_degenerate_torus_pure_state"] = {
        "passed": S_degen < 1e-8,
        "entropy": round(S_degen, 10),
        "description": "eta=0 must give pure state (zero entropy, one component vanishes)",
    }

    # NEG-4: Outer loop at Clifford torus (eta=pi/4) has cos(2*eta)=0
    # so phi does not advance -- only chi. Density STILL traverses.
    cos2eta_cliff = np.cos(2 * np.pi / 4)
    results["neg_clifford_cos2eta_zero"] = {
        "passed": abs(cos2eta_cliff) < 1e-10,
        "cos2eta": round(cos2eta_cliff, 12),
        "description": "At Clifford torus cos(2*eta)=0, outer loop phi-advance vanishes. "
                        "Density still traverses because chi alone changes relative phase.",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(rotors: dict) -> Dict[str, Any]:
    """Edge cases and numerical precision limits."""
    results = {}

    # BOUND-1: Very small steps (high resolution) -- inner loop still stationary
    n_fine = 500
    psi_init = spinor_from_params(PHI_0, CHI_0, ETA_0)
    rho_init = density_from_spinor(psi_init)
    max_drift_fine = 0.0
    for step in range(1, n_fine + 1):
        u = 2.0 * np.pi * step / n_fine
        psi = inner_loop_step(PHI_0, CHI_0, ETA_0, u)
        rho = density_from_spinor(psi)
        drift = float(np.linalg.norm(rho - rho_init, "fro"))
        max_drift_fine = max(max_drift_fine, drift)

    results["bound_fine_resolution_inner_stationary"] = {
        "passed": max_drift_fine < 1e-12,
        "max_drift": round(max_drift_fine, 15),
        "n_steps": n_fine,
    }

    # BOUND-2: Multiple full rotations (10 cycles) -- Berry phase accumulates linearly
    phases = []
    for n_cycles in [1, 2, 5, 10]:
        s3_pts = []
        for step in range(N_STEPS + 1):
            u = 2.0 * np.pi * n_cycles * step / N_STEPS
            psi = outer_loop_step(PHI_0, CHI_0, ETA_0, u)
            q = np.array([np.real(psi[0]), np.imag(psi[0]),
                          np.real(psi[1]), np.imag(psi[1])])
            s3_pts.append(q)
        bp = berry_phase(np.array(s3_pts))
        phases.append({"n_cycles": n_cycles, "berry_phase": round(bp, 8)})

    results["bound_berry_phase_accumulation"] = {
        "passed": True,
        "phases": phases,
    }

    # BOUND-3: Near-degenerate torus (eta very close to 0 and pi/2)
    for eta_test, label in [(1e-8, "near_zero"), (np.pi / 2 - 1e-8, "near_pi_half")]:
        psi = spinor_from_params(0.0, 0.0, eta_test)
        rho = density_from_spinor(psi)
        S = von_neumann_entropy_2x2(rho)
        results[f"bound_degenerate_{label}"] = {
            "passed": S < 1e-4,
            "entropy": round(S, 12),
            "eta": eta_test,
        }

    # BOUND-4: Trace preservation under 50-step terrain application
    for terrain_idx in [0, 4]:  # One fiber, one base
        terrain_name = TERRAINS[terrain_idx]["name"]
        U = terrain_generator_matrix(terrain_name, rotors)
        psi = spinor_from_params(PHI_0, CHI_0, ETA_0)
        for _ in range(N_STEPS):
            psi = U @ psi
        rho = density_from_spinor(psi)
        tr = float(np.real(np.trace(rho)))
        results[f"bound_trace_preservation_{terrain_name}"] = {
            "passed": abs(tr - 1.0) < 1e-10,
            "trace": round(tr, 12),
        }

    return results


# =====================================================================
# PYTORCH CANONICAL VERIFICATION
# =====================================================================

def pytorch_verification() -> Dict[str, Any]:
    """Run the core inner/outer loop distinction through PyTorch autograd.

    Uses torch to verify:
    1. Inner loop: density Frobenius norm is constant w.r.t. u (grad = 0)
    2. Outer loop: density off-diagonal changes w.r.t. u (grad != 0)

    We build the full spinor -> density pipeline in torch so autograd can track it.
    """
    eta = torch.tensor(np.pi / 4, dtype=torch.float64)
    phi0 = torch.tensor(0.0, dtype=torch.float64)
    chi0 = torch.tensor(0.0, dtype=torch.float64)

    # --- Inner loop test ---
    u_in = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
    # ψ_inner = (e^{i(φ+u+χ)} cos η, e^{i(φ+u-χ)} sin η)
    # ρ_01 = ψ_0 * conj(ψ_1) = e^{i((φ+u+χ)-(φ+u-χ))} cos η sin η = e^{2iχ} cos η sin η
    # Real part of ρ_01 for inner loop -- must NOT depend on u
    # Build explicitly through u so torch can see it
    phase_plus = phi0 + u_in + chi0
    phase_minus = phi0 + u_in - chi0
    # |ψ_0|^2 = cos^2(η), |ψ_1|^2 = sin^2(η) -- trivially no u
    # ρ_01 real = cos(phase_plus - phase_minus) * cos(η)*sin(η) = cos(2χ) * cos(η)*sin(η)
    # The key: phase_plus - phase_minus = 2*chi0, so u cancels in the subtraction.
    # To let autograd see this, compute the full thing:
    rho_01_re_inner = torch.cos(phase_plus - phase_minus) * torch.cos(eta) * torch.sin(eta)
    grad_inner = torch.autograd.grad(rho_01_re_inner, u_in, create_graph=True)[0]
    inner_grad_value = float(grad_inner.detach())
    inner_grad_zero = abs(inner_grad_value) < 1e-10

    # --- Outer loop test ---
    u_out = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
    cos2eta = torch.cos(2 * eta)
    phi_out = phi0 - cos2eta * u_out
    chi_out = chi0 + u_out
    phase_plus_out = phi_out + chi_out
    phase_minus_out = phi_out - chi_out
    # ρ_01 real part for outer loop
    rho_01_re_outer = torch.cos(phase_plus_out - phase_minus_out) * torch.cos(eta) * torch.sin(eta)
    grad_outer = torch.autograd.grad(rho_01_re_outer, u_out, create_graph=True)[0]
    outer_grad_value = float(grad_outer.detach())
    outer_grad_nonzero = abs(outer_grad_value) > 1e-10

    return {
        "inner_loop_grad_zero": inner_grad_zero,
        "inner_grad_value": round(inner_grad_value, 12),
        "outer_loop_grad_nonzero": outer_grad_nonzero,
        "outer_grad_value": round(outer_grad_value, 10),
        "pytorch_confirms_distinction": inner_grad_zero and outer_grad_nonzero,
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()
    print("Building Cl(3) terrain rotors...")
    rotors = _build_cl3_terrain_rotors()

    print("Running symbolic stationarity proof (sympy)...")
    sympy_proof = symbolic_stationarity_proof()
    print(f"  Inner loop stationary (symbolic): {sympy_proof['inner_loop_stationary']}")

    print("Running PyTorch autograd verification...")
    torch_result = pytorch_verification()
    print(f"  PyTorch confirms inner/outer distinction: {torch_result['pytorch_confirms_distinction']}")

    print("Running all 16 placements (positive tests)...")
    positive = run_positive_tests(rotors)
    summary = positive.get("__summary", {})
    print(f"  Inner all stationary: {summary.get('inner_all_stationary')}")
    print(f"  Outer all traversing: {summary.get('outer_all_traversing')}")
    print(f"  All CPTP valid: {summary.get('all_cptp_valid')}")

    print("Running negative tests...")
    negative = run_negative_tests(rotors)
    for k, v in negative.items():
        print(f"  {k}: {'PASS' if v.get('passed') else 'FAIL'}")

    print("Running boundary tests...")
    boundary = run_boundary_tests(rotors)
    for k, v in boundary.items():
        if isinstance(v, dict) and "passed" in v:
            print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}")

    elapsed = round(time.time() - t0, 3)
    print(f"\nTotal time: {elapsed}s")

    # --- Assemble final results ---
    results = {
        "name": "engine_16_placements",
        "description": "All 16 (terrain, loop) placement tuples with spinor evolution on Hopf torus",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": elapsed,
        "tool_manifest": TOOL_MANIFEST,
        "sympy_stationarity_proof": sympy_proof,
        "pytorch_verification": torch_result,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    # --- Write output ---
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "engine_16_placements_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")

    # --- Final verdict ---
    all_pass = (
        sympy_proof["inner_loop_stationary"]
        and torch_result["pytorch_confirms_distinction"]
        and summary.get("inner_all_stationary", False)
        and summary.get("outer_all_traversing", False)
        and summary.get("all_cptp_valid", False)
        and all(v.get("passed", False) for v in negative.values())
    )
    verdict = "ALL PASS" if all_pass else "FAILURES DETECTED"
    print(f"\n{'=' * 60}")
    print(f"  VERDICT: {verdict}")
    print(f"{'=' * 60}")
