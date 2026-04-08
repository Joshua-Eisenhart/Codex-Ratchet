#!/usr/bin/env python3
"""
sim_lego_flux_candidates.py -- 7 flux candidates as independent legos.

Setup: L/R Weyl spinors on nested Hopf torus at eta=pi/4 (Clifford torus).
Each candidate computed under 5 evolution types + 3 negative tests.
Pure math. No jargon. No terrain labels.

Classification: canonical (torch-native).
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "All density matrix ops, Lindblad, unitaries, entropy, coherent info"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# CONSTANTS
# =====================================================================

DTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-12
DT = 0.1  # evolution step size

# Pauli matrices
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
S_MINUS = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)  # |1><0| = lowering


# =====================================================================
# MATH PRIMITIVES
# =====================================================================

def hopf_torus_spinor(eta, theta1, theta2):
    """
    Point on S^3 parametrised by Hopf torus coordinates.
    psi = (cos(eta) * e^{i theta1}, sin(eta) * e^{i theta2})
    At eta=pi/4 this is the Clifford torus.
    Returns: (2,) complex tensor, normalized.
    """
    psi = torch.tensor([
        np.cos(eta) * np.exp(1j * theta1),
        np.sin(eta) * np.exp(1j * theta2),
    ], dtype=DTYPE)
    return psi / torch.linalg.norm(psi)


def weyl_split(psi):
    """
    Split a 2-spinor into L/R chiral components.
    Convention: psi_L = P_L psi, psi_R = P_R psi
    where P_L = (I - sigma_z)/2, P_R = (I + sigma_z)/2.
    These are the chiral projectors in the Weyl basis.
    """
    P_L = (I2 - SZ) / 2.0
    P_R = (I2 + SZ) / 2.0
    psi_L = P_L @ psi
    psi_R = P_R @ psi
    return psi_L, psi_R


def spinor_to_density(psi):
    """Pure state |psi><psi|."""
    return torch.outer(psi, psi.conj())


def bloch_vector(rho):
    """Extract Bloch vector (r_x, r_y, r_z) from 2x2 density matrix."""
    rx = torch.trace(rho @ SX).real
    ry = torch.trace(rho @ SY).real
    rz = torch.trace(rho @ SZ).real
    return torch.tensor([rx, ry, rz], dtype=FDTYPE)


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho). Uses eigenvalues."""
    evals = torch.linalg.eigvalsh(rho.real if rho.is_complex() else rho)
    evals = evals.real.clamp(min=EPS)
    return -torch.sum(evals * torch.log2(evals)).item()


def trace_distance(rho, sigma):
    """D(rho, sigma) = 0.5 * Tr|rho - sigma|."""
    diff = rho - sigma
    evals = torch.linalg.eigvalsh(diff @ diff.conj().T).real.clamp(min=0)
    return 0.5 * torch.sum(torch.sqrt(evals)).item()


def partial_trace_B(rho_AB):
    """Trace out qubit B from a 4x4 density matrix. Returns 2x2."""
    rho_A = torch.zeros(2, 2, dtype=DTYPE)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                rho_A[i, j] += rho_AB[2 * i + k, 2 * j + k]
    return rho_A


def partial_trace_A(rho_AB):
    """Trace out qubit A from a 4x4 density matrix. Returns 2x2."""
    rho_B = torch.zeros(2, 2, dtype=DTYPE)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                rho_B[i, j] += rho_AB[2 * k + i, 2 * k + j]
    return rho_B


def coherent_information(rho_AB):
    """I_c(A>B) = S(B) - S(AB)."""
    rho_B = partial_trace_A(rho_AB)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    return S_B - S_AB


def torus_coords_from_spinor(psi):
    """
    Extract (eta, theta1, theta2) from a spinor on S^3.
    eta = arctan(|psi[1]|/|psi[0]|)
    theta1 = arg(psi[0]), theta2 = arg(psi[1])
    """
    a0 = torch.abs(psi[0]).item()
    a1 = torch.abs(psi[1]).item()
    eta = np.arctan2(a1, a0)
    theta1 = np.angle(psi[0].item())
    theta2 = np.angle(psi[1].item())
    return eta, theta1, theta2


# =====================================================================
# EVOLUTION OPERATORS
# =====================================================================

def lindblad_step(rho, L, dt=DT):
    """
    One Lindblad dissipator step: rho -> rho + dt * D[L](rho)
    D[L](rho) = L rho L^dag - 0.5 {L^dag L, rho}
    """
    LdL = L.conj().T @ L
    drho = L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
    rho_new = rho + dt * drho
    # Renormalize trace
    rho_new = rho_new / torch.trace(rho_new)
    return rho_new


def unitary_step(rho, H, dt=DT):
    """
    One unitary step: rho -> U rho U^dag
    U = exp(-i H dt)
    """
    U = torch.matrix_exp(-1j * H * dt)
    return U @ rho @ U.conj().T


def lindblad_step_bipartite(rho_AB, L_local, qubit='A', dt=DT):
    """
    Apply Lindblad dissipator on one qubit of a 2-qubit state.
    L_full = L_local (x) I  (if qubit='A')
    L_full = I (x) L_local  (if qubit='B')
    """
    if qubit == 'A':
        L_full = torch.kron(L_local, I2)
    else:
        L_full = torch.kron(I2, L_local)
    return lindblad_step(rho_AB, L_full, dt)


def unitary_step_bipartite(rho_AB, H_local, qubit='A', dt=DT):
    """Apply unitary on one qubit of a 2-qubit state."""
    if qubit == 'A':
        H_full = torch.kron(H_local, I2)
    else:
        H_full = torch.kron(I2, H_local)
    return unitary_step(rho_AB, H_full, dt)


# =====================================================================
# EVOLUTION CATALOG
# =====================================================================

EVOLUTIONS = {
    "D[sigma_z]": {"type": "lindblad", "L": SZ},
    "D[sigma_x]": {"type": "lindblad", "L": SX},
    "D[sigma_-]": {"type": "lindblad", "L": S_MINUS},
    "exp(-i*sigma_x*t/2)": {"type": "unitary", "H": SX / 2.0},
    "exp(-i*sigma_z*t/2)": {"type": "unitary", "H": SZ / 2.0},
}


def evolve_single(rho, evo_spec, dt=DT):
    """Evolve a single-qubit density matrix by one step."""
    if evo_spec["type"] == "lindblad":
        return lindblad_step(rho, evo_spec["L"], dt)
    else:
        return unitary_step(rho, evo_spec["H"], dt)


def evolve_bipartite(rho_AB, evo_spec, dt=DT):
    """Evolve both qubits of a bipartite state by one step each."""
    if evo_spec["type"] == "lindblad":
        rho_AB = lindblad_step_bipartite(rho_AB, evo_spec["L"], 'A', dt)
        rho_AB = lindblad_step_bipartite(rho_AB, evo_spec["L"], 'B', dt)
    else:
        rho_AB = unitary_step_bipartite(rho_AB, evo_spec["H"], 'A', dt)
        rho_AB = unitary_step_bipartite(rho_AB, evo_spec["H"], 'B', dt)
    return rho_AB


def evolve_spinor(psi, evo_spec, dt=DT):
    """Evolve a pure spinor (for geometric flux). Only unitary supported."""
    if evo_spec["type"] == "unitary":
        U = torch.matrix_exp(-1j * evo_spec["H"] * dt)
        psi_new = U @ psi
        return psi_new / torch.linalg.norm(psi_new)
    else:
        # For Lindblad, go through density matrix, extract dominant eigenvector
        rho = spinor_to_density(psi)
        rho_new = lindblad_step(rho, evo_spec["L"], dt)
        evals, evecs = torch.linalg.eigh(rho_new)
        return evecs[:, -1]  # largest eigenvalue eigenvector


# =====================================================================
# INITIAL STATES
# =====================================================================

def make_initial_states():
    """
    Build initial L/R Weyl spinors on Clifford torus (eta=pi/4).
    theta1=0, theta2=pi/3 gives a generic chiral split.
    """
    eta = np.pi / 4
    theta1 = 0.0
    theta2 = np.pi / 3

    psi = hopf_torus_spinor(eta, theta1, theta2)
    psi_L, psi_R = weyl_split(psi)

    # Normalize each chirality (they won't be unit norm individually)
    norm_L = torch.linalg.norm(psi_L)
    norm_R = torch.linalg.norm(psi_R)

    # Density matrices from chiral components (unnormalized -> mixed)
    rho_L = spinor_to_density(psi_L) / (norm_L ** 2 + EPS) if norm_L > EPS else spinor_to_density(psi_L)
    rho_R = spinor_to_density(psi_R) / (norm_R ** 2 + EPS) if norm_R > EPS else spinor_to_density(psi_R)

    # Bipartite state: entangled L-R pair
    # Use a partially entangled state built from the chiral components
    # |Psi_AB> = cos(eta)|psi_L>|0> + sin(eta)|psi_R>|1> (Bell-like)
    psi_L_norm = psi_L / (norm_L + EPS) if norm_L > EPS else psi_L
    psi_R_norm = psi_R / (norm_R + EPS) if norm_R > EPS else psi_R

    psi_AB = (np.cos(eta) * torch.kron(psi_L_norm, torch.tensor([1, 0], dtype=DTYPE))
              + np.sin(eta) * torch.kron(psi_R_norm, torch.tensor([0, 1], dtype=DTYPE)))
    psi_AB = psi_AB / torch.linalg.norm(psi_AB)
    rho_AB = torch.outer(psi_AB, psi_AB.conj())

    return {
        "psi": psi,
        "psi_L": psi_L,
        "psi_R": psi_R,
        "rho_L": rho_L,
        "rho_R": rho_R,
        "rho_AB": rho_AB,
        "eta": eta,
        "theta1": theta1,
        "theta2": theta2,
    }


# =====================================================================
# 7 FLUX CANDIDATES -- each is a pure function
# =====================================================================

def flux_1_geometric(psi_before, psi_after):
    """
    J_geom = (Delta_eta, Delta_theta1, Delta_theta2).
    Changes in torus coordinates after evolution. Pure geometry.
    Returns 3-vector.
    """
    eta0, th1_0, th2_0 = torus_coords_from_spinor(psi_before)
    eta1, th1_1, th2_1 = torus_coords_from_spinor(psi_after)
    return [eta1 - eta0, th1_1 - th1_0, th2_1 - th2_0]


def flux_2_chirality_separation(rho_L_after, rho_R_after):
    """
    J_chi = d(rho_L, rho_R). Trace distance. Scalar.
    """
    return trace_distance(rho_L_after, rho_R_after)


def flux_3_differential_bloch(rho_L_before, rho_R_before, rho_L_after, rho_R_after):
    """
    J_Bloch = Delta_r_L - Delta_r_R. 3-vector.
    """
    r_L0 = bloch_vector(rho_L_before)
    r_R0 = bloch_vector(rho_R_before)
    r_L1 = bloch_vector(rho_L_after)
    r_R1 = bloch_vector(rho_R_after)
    delta_L = r_L1 - r_L0
    delta_R = r_R1 - r_R0
    return (delta_L - delta_R).tolist()


def flux_4_entropic_asymmetry(rho_L_before, rho_R_before, rho_L_after, rho_R_after):
    """
    J_ent = Delta_S(rho_L) - Delta_S(rho_R). Scalar. Signed.
    """
    dS_L = von_neumann_entropy(rho_L_after) - von_neumann_entropy(rho_L_before)
    dS_R = von_neumann_entropy(rho_R_after) - von_neumann_entropy(rho_R_before)
    return dS_L - dS_R


def flux_5_joint_state(rho_AB_before, rho_AB_after):
    """
    J_cut = Delta I_c(A>B). Change in coherent information. Scalar.
    """
    Ic_before = coherent_information(rho_AB_before)
    Ic_after = coherent_information(rho_AB_after)
    return Ic_after - Ic_before


def flux_6_phase_winding(psi_L_before, psi_R_before, psi_L_after, psi_R_after):
    """
    J_theta = Delta_theta_L - Delta_theta_R.
    Phase = arg(<psi_before|psi_after>) for each chirality.
    Related to Berry phase difference. Scalar.
    """
    overlap_L = torch.dot(psi_L_before.conj(), psi_L_after)
    overlap_R = torch.dot(psi_R_before.conj(), psi_R_after)
    phase_L = np.angle(overlap_L.item())
    phase_R = np.angle(overlap_R.item())
    return phase_L - phase_R


def flux_7_cross_axis(J_chi, J_ent):
    """
    J_cross = correlation proxy between chirality separation and entropic asymmetry.
    Simple product: J_chi * J_ent. If they co-vary, this is nonzero.
    """
    return J_chi * J_ent


# =====================================================================
# RUN ONE EVOLUTION + COMPUTE ALL 7 CANDIDATES
# =====================================================================

def run_one_evolution(states, evo_name, evo_spec):
    """Evolve initial states by one step, compute all 7 flux candidates."""
    psi = states["psi"]
    rho_L = states["rho_L"]
    rho_R = states["rho_R"]
    rho_AB = states["rho_AB"]
    psi_L = states["psi_L"]
    psi_R = states["psi_R"]

    # Evolve
    psi_after = evolve_spinor(psi, evo_spec)
    rho_L_after = evolve_single(rho_L, evo_spec)
    rho_R_after = evolve_single(rho_R, evo_spec)
    rho_AB_after = evolve_bipartite(rho_AB, evo_spec)

    # Evolved chiral spinors (from evolved full spinor)
    psi_L_after, psi_R_after = weyl_split(psi_after)

    # Compute all 7
    j1 = flux_1_geometric(psi, psi_after)
    j2 = flux_2_chirality_separation(rho_L_after, rho_R_after)
    j3 = flux_3_differential_bloch(rho_L, rho_R, rho_L_after, rho_R_after)
    j4 = flux_4_entropic_asymmetry(rho_L, rho_R, rho_L_after, rho_R_after)
    j5 = flux_5_joint_state(rho_AB, rho_AB_after)
    j6 = flux_6_phase_winding(psi_L, psi_R, psi_L_after, psi_R_after)
    j7 = flux_7_cross_axis(j2, j4)

    def is_nonzero_scalar(v):
        return abs(v) > EPS

    def is_nonzero_vec(v):
        return any(abs(x) > EPS for x in v)

    return {
        "J1_geometric": {"value": j1, "nonzero": is_nonzero_vec(j1)},
        "J2_chirality_separation": {"value": j2, "nonzero": is_nonzero_scalar(j2)},
        "J3_differential_bloch": {"value": j3, "nonzero": is_nonzero_vec(j3)},
        "J4_entropic_asymmetry": {"value": j4, "nonzero": is_nonzero_scalar(j4)},
        "J5_joint_state_flux": {"value": j5, "nonzero": is_nonzero_scalar(j5)},
        "J6_phase_winding": {"value": j6, "nonzero": is_nonzero_scalar(j6)},
        "J7_cross_axis": {"value": j7, "nonzero": is_nonzero_scalar(j7)},
    }


# =====================================================================
# POSITIVE TESTS -- 5 evolution types x 7 candidates
# =====================================================================

def run_positive_tests():
    results = {}
    states = make_initial_states()

    for evo_name, evo_spec in EVOLUTIONS.items():
        results[evo_name] = run_one_evolution(states, evo_name, evo_spec)

    # Summary table: which candidates are nonzero under which evolution
    summary = {}
    for evo_name in EVOLUTIONS:
        summary[evo_name] = {}
        for jname in ["J1_geometric", "J2_chirality_separation",
                       "J3_differential_bloch", "J4_entropic_asymmetry",
                       "J5_joint_state_flux", "J6_phase_winding",
                       "J7_cross_axis"]:
            summary[evo_name][jname] = results[evo_name][jname]["nonzero"]

    results["sensitivity_matrix"] = summary
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Use a representative evolution for negatives: amplitude damping
    evo_spec = EVOLUTIONS["D[sigma_-]"]

    # --- NEG 1: Remove chirality (set rho_L = rho_R) ---
    states = make_initial_states()
    # Force both chiralities to the same state (average)
    rho_avg = (states["rho_L"] + states["rho_R"]) / 2.0
    rho_avg = rho_avg / torch.trace(rho_avg)
    states_no_chiral = dict(states)
    states_no_chiral["rho_L"] = rho_avg.clone()
    states_no_chiral["rho_R"] = rho_avg.clone()
    # Also make psi_L = psi_R (equal projection)
    psi_sym = hopf_torus_spinor(np.pi / 4, 0.0, 0.0)  # symmetric: theta1=theta2
    psi_L_sym, psi_R_sym = weyl_split(psi_sym)
    states_no_chiral["psi"] = psi_sym
    states_no_chiral["psi_L"] = psi_L_sym
    states_no_chiral["psi_R"] = psi_R_sym
    # Bipartite: product state (no entanglement)
    rho_AB_product = torch.kron(rho_avg, rho_avg)
    states_no_chiral["rho_AB"] = rho_AB_product

    neg1_results = {}
    for evo_name, evo_spec_i in EVOLUTIONS.items():
        r = run_one_evolution(states_no_chiral, evo_name, evo_spec_i)
        neg1_results[evo_name] = {
            k: {"nonzero": v["nonzero"], "value": v["value"]}
            for k, v in r.items()
        }

    # Check: which candidates collapse to zero when chirality removed?
    neg1_collapse = {}
    for jname in ["J1_geometric", "J2_chirality_separation",
                   "J3_differential_bloch", "J4_entropic_asymmetry",
                   "J5_joint_state_flux", "J6_phase_winding",
                   "J7_cross_axis"]:
        # Collapses if nonzero becomes zero for ALL evolutions
        collapsed_all = all(
            not neg1_results[evo][jname]["nonzero"]
            for evo in EVOLUTIONS
        )
        collapsed_any = any(
            not neg1_results[evo][jname]["nonzero"]
            for evo in EVOLUTIONS
        )
        neg1_collapse[jname] = {
            "collapsed_all_evolutions": collapsed_all,
            "collapsed_some_evolutions": collapsed_any,
        }

    results["neg1_remove_chirality"] = {
        "description": "Set rho_L = rho_R (no chiral split). Does each J collapse?",
        "per_evolution": neg1_results,
        "collapse_summary": neg1_collapse,
    }

    # --- NEG 2: Swap loop law (fiber <-> base) ---
    # Implemented as: swap theta1 <-> theta2 in the initial state
    states_swapped = make_initial_states()
    eta_orig = states_swapped["eta"]
    theta1_orig = states_swapped["theta1"]
    theta2_orig = states_swapped["theta2"]
    psi_swapped = hopf_torus_spinor(eta_orig, theta2_orig, theta1_orig)  # swap
    psi_L_sw, psi_R_sw = weyl_split(psi_swapped)
    norm_L_sw = torch.linalg.norm(psi_L_sw)
    norm_R_sw = torch.linalg.norm(psi_R_sw)
    states_swapped["psi"] = psi_swapped
    states_swapped["psi_L"] = psi_L_sw
    states_swapped["psi_R"] = psi_R_sw
    states_swapped["rho_L"] = spinor_to_density(psi_L_sw) / (norm_L_sw ** 2 + EPS)
    states_swapped["rho_R"] = spinor_to_density(psi_R_sw) / (norm_R_sw ** 2 + EPS)
    states_swapped["theta1"] = theta2_orig
    states_swapped["theta2"] = theta1_orig

    # Rebuild bipartite
    psi_L_sw_n = psi_L_sw / (norm_L_sw + EPS)
    psi_R_sw_n = psi_R_sw / (norm_R_sw + EPS)
    psi_AB_sw = (np.cos(eta_orig) * torch.kron(psi_L_sw_n, torch.tensor([1, 0], dtype=DTYPE))
                 + np.sin(eta_orig) * torch.kron(psi_R_sw_n, torch.tensor([0, 1], dtype=DTYPE)))
    psi_AB_sw = psi_AB_sw / torch.linalg.norm(psi_AB_sw)
    states_swapped["rho_AB"] = torch.outer(psi_AB_sw, psi_AB_sw.conj())

    # Run original and swapped, compare
    states_orig = make_initial_states()
    neg2_results = {}
    for evo_name, evo_spec_i in EVOLUTIONS.items():
        r_orig = run_one_evolution(states_orig, evo_name, evo_spec_i)
        r_swap = run_one_evolution(states_swapped, evo_name, evo_spec_i)
        neg2_results[evo_name] = {}
        for jname in ["J1_geometric", "J2_chirality_separation",
                       "J3_differential_bloch", "J4_entropic_asymmetry",
                       "J5_joint_state_flux", "J6_phase_winding",
                       "J7_cross_axis"]:
            v_orig = r_orig[jname]["value"]
            v_swap = r_swap[jname]["value"]
            # Check if values are the same or different
            if isinstance(v_orig, list):
                diff = max(abs(a - b) for a, b in zip(v_orig, v_swap))
            else:
                diff = abs(v_orig - v_swap)
            survived = diff > EPS
            neg2_results[evo_name][jname] = {
                "original": v_orig,
                "swapped": v_swap,
                "difference": diff,
                "survived_swap": survived,
            }

    # Summary: does each J survive the swap?
    neg2_survival = {}
    for jname in ["J1_geometric", "J2_chirality_separation",
                   "J3_differential_bloch", "J4_entropic_asymmetry",
                   "J5_joint_state_flux", "J6_phase_winding",
                   "J7_cross_axis"]:
        survived_any = any(
            neg2_results[evo][jname]["survived_swap"]
            for evo in EVOLUTIONS
        )
        survived_all = all(
            neg2_results[evo][jname]["survived_swap"]
            for evo in EVOLUTIONS
        )
        neg2_survival[jname] = {
            "survived_all_evolutions": survived_all,
            "survived_some_evolutions": survived_any,
        }

    results["neg2_swap_loop_law"] = {
        "description": "Swap fiber <-> base (theta1 <-> theta2). Does each J survive?",
        "per_evolution": neg2_results,
        "survival_summary": neg2_survival,
    }

    # --- NEG 3: Flatten transport (zero all deltas) ---
    # Evolve with dt=0 (no evolution). All deltas should be zero.
    states_flat = make_initial_states()
    neg3_results = {}
    for evo_name, evo_spec_i in EVOLUTIONS.items():
        # Override: evolve with dt=0
        psi = states_flat["psi"]
        rho_L = states_flat["rho_L"]
        rho_R = states_flat["rho_R"]
        rho_AB = states_flat["rho_AB"]
        psi_L = states_flat["psi_L"]
        psi_R = states_flat["psi_R"]

        # "After" = same as before (dt=0)
        psi_after = psi.clone()
        rho_L_after = rho_L.clone()
        rho_R_after = rho_R.clone()
        rho_AB_after = rho_AB.clone()
        psi_L_after = psi_L.clone()
        psi_R_after = psi_R.clone()

        j1 = flux_1_geometric(psi, psi_after)
        j2 = flux_2_chirality_separation(rho_L_after, rho_R_after)
        j3 = flux_3_differential_bloch(rho_L, rho_R, rho_L_after, rho_R_after)
        j4 = flux_4_entropic_asymmetry(rho_L, rho_R, rho_L_after, rho_R_after)
        j5 = flux_5_joint_state(rho_AB, rho_AB_after)
        j6 = flux_6_phase_winding(psi_L, psi_R, psi_L_after, psi_R_after)
        j7 = flux_7_cross_axis(j2, j4)

        def is_nz_s(v):
            return abs(v) > EPS

        def is_nz_v(v):
            return any(abs(x) > EPS for x in v)

        neg3_results[evo_name] = {
            "J1_geometric": {"value": j1, "persisted": is_nz_v(j1)},
            "J2_chirality_separation": {"value": j2, "persisted": is_nz_s(j2)},
            "J3_differential_bloch": {"value": j3, "persisted": is_nz_v(j3)},
            "J4_entropic_asymmetry": {"value": j4, "persisted": is_nz_s(j4)},
            "J5_joint_state_flux": {"value": j5, "persisted": is_nz_s(j5)},
            "J6_phase_winding": {"value": j6, "persisted": is_nz_s(j6)},
            "J7_cross_axis": {"value": j7, "persisted": is_nz_s(j7)},
        }

    # Note: J2 (chirality separation) is a static measure, not a delta.
    # It may be nonzero even with zero transport (it measures distance, not change).
    neg3_persistence = {}
    for jname in ["J1_geometric", "J2_chirality_separation",
                   "J3_differential_bloch", "J4_entropic_asymmetry",
                   "J5_joint_state_flux", "J6_phase_winding",
                   "J7_cross_axis"]:
        persisted_any = any(
            neg3_results[evo][jname]["persisted"]
            for evo in EVOLUTIONS
        )
        neg3_persistence[jname] = {
            "persisted_with_zero_transport": persisted_any,
            "note": "J2 is static distance, expected nonzero even without transport"
                    if jname == "J2_chirality_separation" else "",
        }

    results["neg3_flatten_transport"] = {
        "description": "Zero all deltas (dt=0). Does each J persist? (Should not, except static measures.)",
        "per_evolution": neg3_results,
        "persistence_summary": neg3_persistence,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary 1: eta -> 0 (one chirality dominates completely)
    eta_small = 0.01
    psi_edge = hopf_torus_spinor(eta_small, 0.0, np.pi / 3)
    psi_L_e, psi_R_e = weyl_split(psi_edge)
    norm_L = torch.linalg.norm(psi_L_e).item()
    norm_R = torch.linalg.norm(psi_R_e).item()
    results["eta_near_zero"] = {
        "description": "eta~0: one chirality dominates",
        "norm_L": norm_L,
        "norm_R": norm_R,
        "ratio": norm_L / (norm_R + EPS),
    }

    # Boundary 2: eta -> pi/2 (other chirality dominates)
    eta_large = np.pi / 2 - 0.01
    psi_edge2 = hopf_torus_spinor(eta_large, 0.0, np.pi / 3)
    psi_L_e2, psi_R_e2 = weyl_split(psi_edge2)
    norm_L2 = torch.linalg.norm(psi_L_e2).item()
    norm_R2 = torch.linalg.norm(psi_R_e2).item()
    results["eta_near_pi_over_2"] = {
        "description": "eta~pi/2: other chirality dominates",
        "norm_L": norm_L2,
        "norm_R": norm_R2,
        "ratio": norm_R2 / (norm_L2 + EPS),
    }

    # Boundary 3: large dt (strong dissipation / large rotation)
    states = make_initial_states()
    large_dt_results = {}
    for evo_name, evo_spec in EVOLUTIONS.items():
        # dt=1.0 (10x normal)
        psi_after = evolve_spinor(states["psi"], evo_spec, dt=1.0)
        rho_L_after = evolve_single(states["rho_L"], evo_spec, dt=1.0)
        rho_R_after = evolve_single(states["rho_R"], evo_spec, dt=1.0)

        j1 = flux_1_geometric(states["psi"], psi_after)
        j2 = flux_2_chirality_separation(rho_L_after, rho_R_after)
        j4 = flux_4_entropic_asymmetry(
            states["rho_L"], states["rho_R"], rho_L_after, rho_R_after
        )
        large_dt_results[evo_name] = {
            "J1_geometric": j1,
            "J2_chirality_separation": j2,
            "J4_entropic_asymmetry": j4,
        }
    results["large_dt"] = {
        "description": "dt=1.0 (10x). Check numerical stability.",
        "per_evolution": large_dt_results,
    }

    # Boundary 4: maximally mixed initial state
    rho_mixed = I2 / 2.0
    states_mixed = make_initial_states()
    states_mixed["rho_L"] = rho_mixed.clone()
    states_mixed["rho_R"] = rho_mixed.clone()
    mixed_results = {}
    for evo_name, evo_spec in EVOLUTIONS.items():
        rho_L_after = evolve_single(rho_mixed.clone(), evo_spec)
        rho_R_after = evolve_single(rho_mixed.clone(), evo_spec)
        j2 = flux_2_chirality_separation(rho_L_after, rho_R_after)
        j3 = flux_3_differential_bloch(rho_mixed, rho_mixed, rho_L_after, rho_R_after)
        j4 = flux_4_entropic_asymmetry(rho_mixed, rho_mixed, rho_L_after, rho_R_after)
        mixed_results[evo_name] = {
            "J2": j2,
            "J3": j3,
            "J4": j4,
            "note": "From maximally mixed: L=R, so J3 and J4 should be zero",
        }
    results["maximally_mixed"] = mixed_results

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running 7 flux candidates as independent legos...")
    print("Setup: L/R Weyl spinors on Clifford torus (eta=pi/4)")
    print("=" * 60)

    positive = run_positive_tests()
    print("\n[POSITIVE] Sensitivity matrix:")
    for evo_name, jmap in positive["sensitivity_matrix"].items():
        nonzero_list = [k for k, v in jmap.items() if v]
        print(f"  {evo_name}: {len(nonzero_list)}/7 nonzero -> {nonzero_list}")

    negative = run_negative_tests()
    print("\n[NEGATIVE 1] Remove chirality -- collapse summary:")
    for jname, info in negative["neg1_remove_chirality"]["collapse_summary"].items():
        print(f"  {jname}: collapsed_all={info['collapsed_all_evolutions']}, "
              f"collapsed_some={info['collapsed_some_evolutions']}")

    print("\n[NEGATIVE 2] Swap loop law -- survival summary:")
    for jname, info in negative["neg2_swap_loop_law"]["survival_summary"].items():
        print(f"  {jname}: survived_all={info['survived_all_evolutions']}, "
              f"survived_some={info['survived_some_evolutions']}")

    print("\n[NEGATIVE 3] Flatten transport -- persistence summary:")
    for jname, info in negative["neg3_flatten_transport"]["persistence_summary"].items():
        persisted = info["persisted_with_zero_transport"]
        note = info.get("note", "")
        print(f"  {jname}: persisted={persisted} {note}")

    boundary = run_boundary_tests()
    print("\n[BOUNDARY] eta near 0:", boundary["eta_near_zero"])
    print("[BOUNDARY] eta near pi/2:", boundary["eta_near_pi_over_2"])

    results = {
        "name": "lego_flux_candidates -- 7 independent flux candidates",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_flux_candidates_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
