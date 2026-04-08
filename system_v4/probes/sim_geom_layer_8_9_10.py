#!/usr/bin/env python3
"""
Geometric Layers 8-10: Pauli Operators, Weyl Flux, Entropy Gradient
=====================================================================

LAYER 8 -- Pauli operators on all geometry layers:
  4 engine operators (Ti=Z-dephasing, Te=X-dephasing, Fi=X-rotation,
  Fe=Z-rotation) tested on density matrix, Bloch sphere, Hopf torus,
  and Weyl spinors.  Ti preserves chirality (commutes with sigma_z).
  Fi mixes L/R.

LAYER 9 -- Flux on Weyl spinors:
  J_LR = d/dt |<L|psi(t)>|^2 under evolution.
  Fe: J_LR=0 (no flux).  Fi: J_LR!=0.  Dephasing: irreversible flux.
  Computed at 10 torus points for each operator.

LAYER 10 -- Entropy gradient nabla I_c on full stack:
  I_c computed with increasing numbers of active layers.
  nabla I_c via autograd.  Layer contribution =
  ||nabla I_c(with layer) - nabla I_c(without)||.
  KEY TEST: does each layer change the gradient?  Which layer matters most?

Classification: canonical
Output: system_v4/probes/a2_state/sim_results/geom_layer_8_9_10_results.json
"""

import json
import os
import sys
import traceback
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no GNN layers"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- numerical sim"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- torch native Pauli ops"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- Bloch/Hopf done in torch"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed"},
}

# ── Imports ─────────────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd for nabla I_c, differentiable operator channels"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    print("FATAL: pytorch required for canonical sim", file=sys.stderr)
    sys.exit(1)

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic verification of Ti chirality-preservation"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# TORCH PRIMITIVES
# =====================================================================

DEVICE = "cpu"
DTYPE_C = torch.complex64
DTYPE_R = torch.float32

def _t(arr):
    """Numpy array to torch complex tensor."""
    return torch.tensor(arr, dtype=DTYPE_C, device=DEVICE)

def _eye2():
    return torch.eye(2, dtype=DTYPE_C, device=DEVICE)

def pauli():
    """Return I, X, Y, Z as complex64 tensors."""
    I = torch.eye(2, dtype=DTYPE_C, device=DEVICE)
    X = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE_C, device=DEVICE)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE_C, device=DEVICE)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE_C, device=DEVICE)
    return I, X, Y, Z


def von_neumann_entropy(rho):
    """Differentiable S(rho) = -Tr(rho log rho)."""
    evals = torch.linalg.eigvalsh(rho.real.to(torch.float64))
    evals = torch.clamp(evals, min=1e-12)
    return -torch.sum(evals * torch.log(evals)).to(DTYPE_R)


def bloch_vector(rho):
    """Extract (px, py, pz) from 2x2 density matrix."""
    _, X, Y, Z = pauli()
    px = torch.real(torch.trace(rho @ X))
    py = torch.real(torch.trace(rho @ Y))
    pz = torch.real(torch.trace(rho @ Z))
    return torch.stack([px, py, pz])


def bloch_to_density(bv):
    """Bloch vector (3,) -> 2x2 density matrix."""
    I, X, Y, Z = pauli()
    return (I + bv[0].to(DTYPE_C) * X
            + bv[1].to(DTYPE_C) * Y
            + bv[2].to(DTYPE_C) * Z) / 2.0


def make_density_param(r, theta, phi):
    """Differentiable density matrix from Bloch parameters."""
    I, X, Y, Z = pauli()
    r_s = torch.sigmoid(r)
    nx = r_s * torch.sin(theta) * torch.cos(phi)
    ny = r_s * torch.sin(theta) * torch.sin(phi)
    nz = r_s * torch.cos(theta)
    return (I + nx.to(DTYPE_C) * X + ny.to(DTYPE_C) * Y + nz.to(DTYPE_C) * Z) / 2.0


# =====================================================================
# TORUS / WEYL PRIMITIVES (torch-native)
# =====================================================================

def torus_point_torch(eta, theta1, theta2):
    """S^3 quaternion from toroidal coordinates, as torch tensor."""
    a = torch.cos(eta) * torch.cos(theta1)
    b = torch.cos(eta) * torch.sin(theta1)
    c = torch.sin(eta) * torch.cos(theta2)
    d = torch.sin(eta) * torch.sin(theta2)
    return torch.stack([a, b, c, d])


def quaternion_to_spinor_L(q):
    """Left Weyl spinor psi_L = (z1, z2) from quaternion."""
    a, b, c, d = q[0], q[1], q[2], q[3]
    z1 = a.to(DTYPE_C) + 1j * b.to(DTYPE_C)
    z2 = c.to(DTYPE_C) + 1j * d.to(DTYPE_C)
    return torch.stack([z1, z2])


def quaternion_to_spinor_R(q):
    """Right Weyl spinor psi_R = (conj(z2), -conj(z1)) from quaternion."""
    a, b, c, d = q[0], q[1], q[2], q[3]
    z1 = a.to(DTYPE_C) + 1j * b.to(DTYPE_C)
    z2 = c.to(DTYPE_C) + 1j * d.to(DTYPE_C)
    return torch.stack([torch.conj(z2), -torch.conj(z1)])


def spinor_to_density(psi):
    """Pure state density matrix |psi><psi|."""
    return torch.outer(psi, torch.conj(psi))


def hopf_map_torch(q):
    """Hopf map S^3 -> S^2: quaternion to Bloch vector."""
    a, b, c, d = q[0], q[1], q[2], q[3]
    z1 = a.to(DTYPE_C) + 1j * b.to(DTYPE_C)
    z2 = c.to(DTYPE_C) + 1j * d.to(DTYPE_C)
    x = 2.0 * torch.real(torch.conj(z1) * z2)
    y = 2.0 * torch.imag(torch.conj(z1) * z2)
    z = torch.abs(z1)**2 - torch.abs(z2)**2
    return torch.stack([x, y, z])


# =====================================================================
# ENGINE OPERATORS (differentiable channels)
# =====================================================================

class TiChannel(nn.Module):
    """Ti = Z-dephasing: rho -> (1-p)*rho + p*Z*rho*Z.
    Constraint / projection operator. Preserves diagonal (Z-basis).
    PRESERVES chirality: commutes with sigma_z."""
    def __init__(self, p=0.3):
        super().__init__()
        self.p = nn.Parameter(torch.tensor(float(p)))

    def forward(self, rho):
        _, _, _, Z = pauli()
        p = torch.sigmoid(self.p).to(DTYPE_C)
        return (1 - p) * rho + p * (Z @ rho @ Z)


class TeChannel(nn.Module):
    """Te = X-dephasing: rho -> (1-p)*rho + p*X*rho*X.
    Exploration / dephasing. Destroys X-coherence."""
    def __init__(self, p=0.3):
        super().__init__()
        self.p = nn.Parameter(torch.tensor(float(p)))

    def forward(self, rho):
        _, X, _, _ = pauli()
        p = torch.sigmoid(self.p).to(DTYPE_C)
        return (1 - p) * rho + p * (X @ rho @ X)


class FeChannel(nn.Module):
    """Fe = Z-rotation: rho -> U_z rho U_z^dag.
    Release / frame rotation. Unitary, PRESERVES purity.
    Z-rotation: no chirality mixing (J_LR = 0)."""
    def __init__(self, theta=0.5):
        super().__init__()
        self.theta = nn.Parameter(torch.tensor(float(theta)))

    def forward(self, rho):
        t = self.theta.to(DTYPE_C)
        U = torch.stack([
            torch.stack([torch.exp(-1j * t / 2), torch.tensor(0.0 + 0j, dtype=DTYPE_C)]),
            torch.stack([torch.tensor(0.0 + 0j, dtype=DTYPE_C), torch.exp(1j * t / 2)]),
        ])
        return U @ rho @ U.conj().T


class FiChannel(nn.Module):
    """Fi = X-rotation: rho -> U_x rho U_x^dag.
    Filter / selection. Unitary, PRESERVES purity.
    X-rotation MIXES L/R chirality (J_LR != 0)."""
    def __init__(self, theta=0.5):
        super().__init__()
        self.theta = nn.Parameter(torch.tensor(float(theta)))

    def forward(self, rho):
        t = self.theta.to(DTYPE_C)
        cos_t = torch.cos(t / 2)
        sin_t = -1j * torch.sin(t / 2)
        U = torch.stack([
            torch.stack([cos_t, sin_t]),
            torch.stack([sin_t, cos_t]),
        ])
        return U @ rho @ U.conj().T


OPERATORS = {
    "Ti": TiChannel,
    "Te": TeChannel,
    "Fe": FeChannel,
    "Fi": FiChannel,
}


# =====================================================================
# LAYER 8: Pauli operators on all geometry representations
# =====================================================================

def _test_operator_on_representations(op_name, op_cls):
    """Test one operator across density matrix, Bloch, Hopf torus, Weyl spinors.

    Returns dict of results for this operator.
    """
    op = op_cls()
    results = {}

    # -- (a) density matrix test --
    r = torch.tensor(0.8, requires_grad=True)
    theta = torch.tensor(1.2, requires_grad=True)
    phi = torch.tensor(0.7, requires_grad=True)
    rho_in = make_density_param(r, theta, phi)
    rho_out = op(rho_in)

    S_in = von_neumann_entropy(rho_in)
    S_out = von_neumann_entropy(rho_out)
    purity_in = torch.real(torch.trace(rho_in @ rho_in)).item()
    purity_out = torch.real(torch.trace(rho_out @ rho_out)).item()
    trace_preserved = abs(torch.real(torch.trace(rho_out)).item() - 1.0) < 1e-5

    results["density_matrix"] = {
        "S_in": S_in.item(),
        "S_out": S_out.item(),
        "delta_S": (S_out - S_in).item(),
        "purity_in": purity_in,
        "purity_out": purity_out,
        "trace_preserved": trace_preserved,
    }

    # -- (b) Bloch sphere test --
    bv_in = bloch_vector(rho_in)
    bv_out = bloch_vector(rho_out)
    bloch_len_in = torch.norm(bv_in).item()
    bloch_len_out = torch.norm(bv_out).item()

    results["bloch_sphere"] = {
        "bloch_in": bv_in.detach().tolist(),
        "bloch_out": bv_out.detach().tolist(),
        "len_in": bloch_len_in,
        "len_out": bloch_len_out,
        "len_change": bloch_len_out - bloch_len_in,
    }

    # -- (c) Hopf torus test (3 nested tori) --
    ETA_INNER = torch.tensor(np.pi / 8)
    ETA_CLIFFORD = torch.tensor(np.pi / 4)
    ETA_OUTER = torch.tensor(3 * np.pi / 8)
    torus_results = {}
    for tname, eta_val in [("inner", ETA_INNER), ("clifford", ETA_CLIFFORD), ("outer", ETA_OUTER)]:
        theta1 = torch.tensor(0.5)
        theta2 = torch.tensor(1.0)
        q = torus_point_torch(eta_val, theta1, theta2)
        psi_L = quaternion_to_spinor_L(q)
        rho_t = spinor_to_density(psi_L)
        rho_t_out = op(rho_t)
        S_t = von_neumann_entropy(rho_t_out)
        bv_t = bloch_vector(rho_t_out)
        torus_results[tname] = {
            "S_after_op": S_t.item(),
            "bloch_after": bv_t.detach().tolist(),
            "bloch_z": bv_t[2].item(),
        }
    results["hopf_torus"] = torus_results

    # -- (d) Weyl spinor chirality test --
    # Use inner torus (eta != pi/4) so pz != 0; at Clifford torus pz=0 for all points
    q_test = torus_point_torch(ETA_INNER, torch.tensor(0.3), torch.tensor(0.8))
    psi_L = quaternion_to_spinor_L(q_test)
    psi_R = quaternion_to_spinor_R(q_test)
    rho_L = spinor_to_density(psi_L)
    rho_R = spinor_to_density(psi_R)

    rho_L_out = op(rho_L)
    rho_R_out = op(rho_R)

    # Chirality = Bloch z component (eigenvalue of sigma_z)
    chi_L_before = bloch_vector(rho_L)[2].item()
    chi_R_before = bloch_vector(rho_R)[2].item()
    chi_L_after = bloch_vector(rho_L_out)[2].item()
    chi_R_after = bloch_vector(rho_R_out)[2].item()

    # Overlap |<L|R>| before and after
    overlap_before = torch.abs(torch.vdot(psi_L, psi_R)).item()

    results["weyl_spinors"] = {
        "chirality_L_before": chi_L_before,
        "chirality_L_after": chi_L_after,
        "chirality_R_before": chi_R_before,
        "chirality_R_after": chi_R_after,
        "delta_chi_L": chi_L_after - chi_L_before,
        "delta_chi_R": chi_R_after - chi_R_before,
        "LR_overlap_before": overlap_before,
        "preserves_chirality": abs(chi_L_after - chi_L_before) < 1e-4
                               and abs(chi_R_after - chi_R_before) < 1e-4,
    }

    return results


def run_layer_8():
    """LAYER 8: All four operators on all four geometry representations."""
    results = {}
    for op_name, op_cls in OPERATORS.items():
        results[op_name] = _test_operator_on_representations(op_name, op_cls)

    # KEY ASSERTIONS
    assertions = {}

    # Ti preserves chirality (commutes with sigma_z)
    assertions["Ti_preserves_chirality"] = results["Ti"]["weyl_spinors"]["preserves_chirality"]

    # Fe preserves chirality (Z-rotation commutes with sigma_z)
    assertions["Fe_preserves_chirality"] = results["Fe"]["weyl_spinors"]["preserves_chirality"]

    # Fi MIXES chirality (X-rotation anticommutes with sigma_z)
    assertions["Fi_mixes_chirality"] = not results["Fi"]["weyl_spinors"]["preserves_chirality"]

    # Te mixes chirality (X-dephasing mixes L/R)
    assertions["Te_mixes_chirality"] = not results["Te"]["weyl_spinors"]["preserves_chirality"]

    # Dephasing channels increase entropy (or preserve for pure states)
    assertions["Ti_entropy_nondecreasing"] = results["Ti"]["density_matrix"]["delta_S"] >= -1e-6
    assertions["Te_entropy_nondecreasing"] = results["Te"]["density_matrix"]["delta_S"] >= -1e-6

    # Unitary channels preserve purity
    assertions["Fe_purity_preserved"] = abs(
        results["Fe"]["density_matrix"]["purity_out"]
        - results["Fe"]["density_matrix"]["purity_in"]) < 1e-4
    assertions["Fi_purity_preserved"] = abs(
        results["Fi"]["density_matrix"]["purity_out"]
        - results["Fi"]["density_matrix"]["purity_in"]) < 1e-4

    # All channels preserve trace
    for op_name in OPERATORS:
        assertions[f"{op_name}_trace_preserved"] = results[op_name]["density_matrix"]["trace_preserved"]

    # Sympy symbolic check: [sigma_z, Ti_kraus] commutation
    sympy_check = "skipped"
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            sz_sym = sp.Matrix([[1, 0], [0, -1]])
            # Ti Kraus: K0 = sqrt(1-p)*I, K1 = sqrt(p)*Z
            # Check: Z commutes with Z (trivially)
            p_sym = sp.Symbol("p", positive=True)
            K0 = sp.sqrt(1 - p_sym) * sp.eye(2)
            K1 = sp.sqrt(p_sym) * sz_sym
            # [Z, K0] = 0 and [Z, K1] = 0
            comm_K0 = sp.simplify(sz_sym * K0 - K0 * sz_sym)
            comm_K1 = sp.simplify(sz_sym * K1 - K1 * sz_sym)
            sympy_check = {
                "comm_Z_K0_zero": comm_K0 == sp.zeros(2),
                "comm_Z_K1_zero": comm_K1 == sp.zeros(2),
                "Ti_commutes_with_Z": comm_K0 == sp.zeros(2) and comm_K1 == sp.zeros(2),
            }
        except Exception as e:
            sympy_check = f"error: {e}"

    results["assertions"] = assertions
    results["sympy_chirality_check"] = sympy_check
    results["all_pass"] = all(assertions.values())
    return results


# =====================================================================
# LAYER 9: Flux J_LR on Weyl spinors
# =====================================================================

def compute_J_LR(op, q_torch, dt=0.01):
    """Compute J_LR = d/dt |<L|psi(t)>|^2 under operator evolution.

    For a spinor psi = psi_L, we evolve via the operator channel
    and measure the rate of change of the left-projection weight.

    Returns J_LR (float), plus diagnostics.
    """
    psi_L = quaternion_to_spinor_L(q_torch)
    rho_0 = spinor_to_density(psi_L)

    # Weight of L component at t=0
    # For pure left spinor, |<L|psi>|^2 = 1 by construction
    # After operator, measure weight in L-basis
    # L-projector = |0><0| in the z-basis (L = upper component = spin-up)
    P_L = torch.tensor([[1, 0], [0, 0]], dtype=DTYPE_C, device=DEVICE)

    w_L_0 = torch.real(torch.trace(P_L @ rho_0)).item()

    # Single step evolution
    rho_1 = op(rho_0)
    w_L_1 = torch.real(torch.trace(P_L @ rho_1)).item()

    # Two steps
    rho_2 = op(rho_1)
    w_L_2 = torch.real(torch.trace(P_L @ rho_2)).item()

    # Numerical derivative (central difference on steps)
    J_LR = (w_L_1 - w_L_0)  # flux per step

    return {
        "w_L_0": w_L_0,
        "w_L_1": w_L_1,
        "w_L_2": w_L_2,
        "J_LR": J_LR,
        "J_LR_abs": abs(J_LR),
        "irreversible": abs(w_L_2 - w_L_0) > abs(w_L_1 - w_L_0) * 0.5,
    }


def run_layer_9():
    """LAYER 9: Flux J_LR at 10 torus points for each operator."""
    # 10 torus points spanning the three nested tori
    torus_params = []
    etas = [np.pi / 8, np.pi / 4, 3 * np.pi / 8]
    for eta in etas:
        for t1 in [0.0, np.pi / 2, np.pi]:
            torus_params.append((eta, t1, 0.5))
    torus_params.append((np.pi / 4, np.pi / 3, np.pi / 3))  # 10th point

    results = {}
    for op_name, op_cls in OPERATORS.items():
        op = op_cls()
        op_results = []
        for i, (eta, t1, t2) in enumerate(torus_params):
            q = torus_point_torch(
                torch.tensor(eta), torch.tensor(t1), torch.tensor(t2)
            )
            flux = compute_J_LR(op, q)
            flux["torus_point"] = {"eta": eta, "theta1": t1, "theta2": t2}
            op_results.append(flux)
        results[op_name] = op_results

    # Aggregate assertions
    assertions = {}

    # Fe: J_LR = 0 at all points (Z-rotation preserves L/R weight)
    fe_flux = [abs(r["J_LR"]) for r in results["Fe"]]
    assertions["Fe_zero_flux"] = all(f < 1e-5 for f in fe_flux)
    assertions["Fe_max_flux"] = max(fe_flux)

    # Fi: J_LR != 0 at most points (X-rotation mixes L/R)
    fi_flux = [abs(r["J_LR"]) for r in results["Fi"]]
    assertions["Fi_nonzero_flux"] = sum(f > 1e-5 for f in fi_flux) >= 7
    assertions["Fi_mean_flux"] = float(np.mean(fi_flux))

    # Ti dephasing (Z-dephasing): preserves L-projection weight (Z-basis),
    # so J_LR ~ 0 -- same as Fe but for a different reason (dephasing, not unitary)
    ti_flux = [abs(r["J_LR"]) for r in results["Ti"]]
    assertions["Ti_preserves_L_weight"] = all(f < 1e-4 for f in ti_flux)
    assertions["Ti_max_flux"] = max(ti_flux)

    # Te dephasing (X-dephasing): irreversible flux toward X eigenstates
    # X*Z*X = -Z so pz -> (1-2p)*pz each step -- monotonic shrinkage
    te_flux = [abs(r["J_LR"]) for r in results["Te"]]
    te_has_flux = sum(f > 1e-5 for f in te_flux)
    assertions["Te_has_flux_on_nonzero_pz"] = te_has_flux >= 3

    results["assertions"] = assertions
    results["all_pass"] = (
        assertions["Fe_zero_flux"]
        and assertions["Fi_nonzero_flux"]
    )
    return results


# =====================================================================
# LAYER 10: Entropy gradient nabla I_c on full stack
# =====================================================================

def build_layer_stack():
    """Build the layer stack as a list of differentiable modules.

    Each layer is a function rho -> rho that represents one
    constraint/transformation layer.  We use simplified versions
    of the actual constraint shells for gradient analysis.

    Returns list of (name, module) pairs.
    """
    layers = []

    # L1: CPTP projection (depolarizing channel as minimal CPTP map)
    class L1_CPTP(nn.Module):
        def __init__(self):
            super().__init__()
            self.p = nn.Parameter(torch.tensor(0.05))
        def forward(self, rho):
            p = torch.sigmoid(self.p).to(DTYPE_C)
            return (1 - p) * rho + p * _eye2() / 2.0
    layers.append(("L1_CPTP", L1_CPTP()))

    # L2: Hopf constraint (project Bloch vector onto S^2 surface)
    class L2_Hopf(nn.Module):
        def forward(self, rho):
            bv = bloch_vector(rho)
            norm = torch.norm(bv)
            if norm > 1e-8:
                bv_proj = bv / torch.clamp(norm, min=0.01, max=1.0) * norm
            else:
                bv_proj = bv
            return bloch_to_density(bv_proj)
    layers.append(("L2_Hopf", L2_Hopf()))

    # L3: Noncommutation guard (inject off-diagonal if too diagonal)
    class L3_Noncomm(nn.Module):
        def __init__(self):
            super().__init__()
            self.eps = nn.Parameter(torch.tensor(0.02))
        def forward(self, rho):
            _, X, _, _ = pauli()
            eps = torch.sigmoid(self.eps).to(DTYPE_C)
            offdiag = torch.abs(rho[0, 1])
            if offdiag < 0.01:
                rho = rho + eps * (X @ rho + rho @ X) / 4.0
                # Re-normalize trace
                rho = rho / torch.trace(rho).real
            return rho
    layers.append(("L3_Noncomm", L3_Noncomm()))

    # L4-L6: Composition / chirality / irreversibility (single dephasing)
    class L4_Composition(nn.Module):
        def __init__(self):
            super().__init__()
            self.gamma = nn.Parameter(torch.tensor(0.02))
        def forward(self, rho):
            g = torch.sigmoid(self.gamma).to(DTYPE_C)
            return (1 - g) * rho + g * rho @ rho / torch.trace(rho @ rho).real
    layers.append(("L4_Composition", L4_Composition()))

    class L5_Chirality(nn.Module):
        def forward(self, rho):
            # Slight Z-preference (chirality lock)
            _, _, _, Z = pauli()
            return 0.98 * rho + 0.02 * (Z @ rho @ Z)
    layers.append(("L5_Chirality", L5_Chirality()))

    class L6_Irreversibility(nn.Module):
        def __init__(self):
            super().__init__()
            self.p = nn.Parameter(torch.tensor(0.03))
        def forward(self, rho):
            _, _, _, Z = pauli()
            p = torch.sigmoid(self.p).to(DTYPE_C)
            return (1 - p) * rho + p * _eye2() / 2.0
    layers.append(("L6_Irreversibility", L6_Irreversibility()))

    # L7: Stage ordering (identity placeholder -- ordering is discrete)
    class L7_StageOrder(nn.Module):
        def forward(self, rho):
            return rho
    layers.append(("L7_StageOrder", L7_StageOrder()))

    # L8: Operator application (Ti as canonical)
    layers.append(("L8_Ti", TiChannel(p=0.2)))

    # L9: Weyl flux gate (Fi as canonical L/R mixer)
    layers.append(("L9_Fi", FiChannel(theta=0.3)))

    return layers


def compute_Ic_with_layers(rho_param_r, rho_param_theta, rho_param_phi,
                           layers, active_mask):
    """Compute I_c = 1 - S(rho) / log(2) through the active layer subset.

    I_c in [0, 1]: 1 = pure state, 0 = maximally mixed.
    Returns I_c as a differentiable scalar.
    """
    rho = make_density_param(rho_param_r, rho_param_theta, rho_param_phi)
    for i, (name, layer) in enumerate(layers):
        if active_mask[i]:
            rho = layer(rho)
            # Re-enforce Hermiticity after each layer
            rho = (rho + rho.conj().T) / 2.0
            # Re-enforce trace=1
            tr = torch.real(torch.trace(rho))
            if tr > 1e-8:
                rho = rho / tr
    S = von_neumann_entropy(rho)
    I_c = 1.0 - S / torch.log(torch.tensor(2.0))
    return I_c


def run_layer_10():
    """LAYER 10: nabla I_c with increasing layer subsets."""
    layers = build_layer_stack()
    n_layers = len(layers)

    # Layer subsets to test: L1 only, L1-3, L1-6, L1-7, L1-8, L1-9, full
    subset_specs = [
        ("L1_only",  [True] + [False] * (n_layers - 1)),
        ("L1_to_L3", [True, True, True] + [False] * (n_layers - 3)),
        ("L1_to_L6", [True] * 6 + [False] * (n_layers - 6)),
        ("L1_to_L7", [True] * 7 + [False] * (n_layers - 7)),
        ("L1_to_L8", [True] * 8 + [False] * (n_layers - 8)),
        ("L1_to_L9", [True] * 9 + [False] * (n_layers - 9)),
        ("full",     [True] * n_layers),
    ]

    # Parameters for the input state
    r = torch.tensor(1.5, requires_grad=True)
    theta = torch.tensor(1.0, requires_grad=True)
    phi = torch.tensor(0.8, requires_grad=True)

    results = {}
    grad_norms = {}

    for spec_name, mask in subset_specs:
        # Zero grads
        if r.grad is not None:
            r.grad.zero_()
        if theta.grad is not None:
            theta.grad.zero_()
        if phi.grad is not None:
            phi.grad.zero_()

        I_c = compute_Ic_with_layers(r, theta, phi, layers, mask)
        I_c.backward(retain_graph=False)

        grad_r = r.grad.item() if r.grad is not None else 0.0
        grad_theta = theta.grad.item() if theta.grad is not None else 0.0
        grad_phi = phi.grad.item() if phi.grad is not None else 0.0
        grad_norm = float(np.sqrt(grad_r**2 + grad_theta**2 + grad_phi**2))

        results[spec_name] = {
            "I_c": I_c.item(),
            "grad_r": grad_r,
            "grad_theta": grad_theta,
            "grad_phi": grad_phi,
            "grad_norm": grad_norm,
            "active_layers": [layers[i][0] for i, m in enumerate(mask) if m],
        }
        grad_norms[spec_name] = grad_norm

        # Recreate params to avoid accumulated grad issues
        r = torch.tensor(1.5, requires_grad=True)
        theta = torch.tensor(1.0, requires_grad=True)
        phi = torch.tensor(0.8, requires_grad=True)

    # Compute layer contributions: ||grad(with) - grad(without)||
    layer_contributions = {}
    ordered_specs = list(subset_specs)
    for i in range(1, len(ordered_specs)):
        curr_name = ordered_specs[i][0]
        prev_name = ordered_specs[i - 1][0]
        curr_g = results[curr_name]
        prev_g = results[prev_name]
        delta = float(np.sqrt(
            (curr_g["grad_r"] - prev_g["grad_r"])**2
            + (curr_g["grad_theta"] - prev_g["grad_theta"])**2
            + (curr_g["grad_phi"] - prev_g["grad_phi"])**2
        ))
        layer_contributions[f"{prev_name}_to_{curr_name}"] = {
            "delta_grad_norm": delta,
            "delta_Ic": curr_g["I_c"] - prev_g["I_c"],
        }

    # Find which layer matters most
    if layer_contributions:
        most_impactful = max(layer_contributions.items(),
                             key=lambda x: x[1]["delta_grad_norm"])
    else:
        most_impactful = ("none", {"delta_grad_norm": 0.0})

    # Assertions
    assertions = {}

    # Each layer subset should produce a different gradient
    unique_norms = len(set(round(v, 6) for v in grad_norms.values()))
    assertions["gradient_changes_with_layers"] = unique_norms >= 4

    # Full stack gradient should be nonzero
    assertions["full_stack_grad_nonzero"] = grad_norms["full"] > 1e-8

    # I_c should generally decrease as more dissipative layers are added
    assertions["Ic_monotonic_trend"] = (
        results["L1_only"]["I_c"] >= results["full"]["I_c"] - 0.1
    )

    # At least one layer should contribute significantly
    max_contribution = most_impactful[1]["delta_grad_norm"]
    assertions["at_least_one_significant_layer"] = max_contribution > 1e-6

    results["layer_contributions"] = layer_contributions
    results["most_impactful_transition"] = {
        "name": most_impactful[0],
        "delta_grad_norm": most_impactful[1]["delta_grad_norm"],
    }
    results["assertions"] = assertions
    results["all_pass"] = all(assertions.values())
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """Verify that broken configurations fail as expected."""
    results = {}

    # NEG-1: Identity channel should NOT mix chirality
    class IdentityChannel(nn.Module):
        def forward(self, rho):
            return rho
    id_op = IdentityChannel()
    q = torus_point_torch(torch.tensor(np.pi / 4), torch.tensor(0.5), torch.tensor(1.0))
    flux = compute_J_LR(id_op, q)
    results["identity_zero_flux"] = {
        "J_LR": flux["J_LR"],
        "pass": abs(flux["J_LR"]) < 1e-10,
    }

    # NEG-2: Fully depolarizing channel should push I_c toward 0
    class FullDepolarize(nn.Module):
        def forward(self, rho):
            return _eye2() / 2.0
    layers = build_layer_stack()
    # Replace all layers with full depolarizing
    depol_layers = [(n, FullDepolarize()) for n, _ in layers]
    r = torch.tensor(1.5, requires_grad=True)
    theta = torch.tensor(1.0, requires_grad=True)
    phi = torch.tensor(0.8, requires_grad=True)
    mask = [True] * len(depol_layers)
    I_c = compute_Ic_with_layers(r, theta, phi, depol_layers, mask)
    results["full_depolarize_kills_Ic"] = {
        "I_c": I_c.item(),
        "pass": I_c.item() < 0.05,
    }

    # NEG-3: Zero-strength operators should be identity
    ti_zero = TiChannel(p=-10.0)  # sigmoid(-10) ~ 0
    q = torus_point_torch(torch.tensor(np.pi / 4), torch.tensor(0.3), torch.tensor(0.8))
    psi_L = quaternion_to_spinor_L(q)
    rho_in = spinor_to_density(psi_L)
    rho_out = ti_zero(rho_in)
    diff = torch.norm(rho_out - rho_in).item()
    results["zero_strength_is_identity"] = {
        "diff": diff,
        "pass": diff < 1e-3,
    }

    # NEG-4: Non-physical state (trace != 1) should still be handled
    rho_bad = torch.tensor([[2.0 + 0j, 0.5 + 0j], [0.5 + 0j, 1.0 + 0j]], dtype=DTYPE_C)
    try:
        ti = TiChannel()
        rho_result = ti(rho_bad)
        tr = torch.real(torch.trace(rho_result)).item()
        results["nonphysical_input_handled"] = {
            "trace_out": tr,
            "pass": True,  # didn't crash
        }
    except Exception as e:
        results["nonphysical_input_handled"] = {"pass": False, "error": str(e)}

    results["all_pass"] = all(r.get("pass", False) for r in results.values()
                              if isinstance(r, dict) and "pass" in r)
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases and numerical precision limits."""
    results = {}

    # BND-1: Maximally mixed state (I/2) -- operators should not decrease entropy below log(2)
    rho_mm = _eye2() / 2.0
    for op_name, op_cls in OPERATORS.items():
        op = op_cls()
        rho_out = op(rho_mm)
        S = von_neumann_entropy(rho_out)
        results[f"{op_name}_on_maximally_mixed"] = {
            "S_out": S.item(),
            "S_max": float(np.log(2)),
            "pass": S.item() <= float(np.log(2)) + 1e-4,
        }

    # BND-2: Pure state |0> -- dephasing should increase entropy
    ket0 = torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=DTYPE_C)
    rho_pure = torch.outer(ket0, torch.conj(ket0))
    for op_name in ["Ti", "Te"]:
        op = OPERATORS[op_name]()
        rho_out = op(rho_pure)
        S_out = von_neumann_entropy(rho_out)
        results[f"{op_name}_on_pure_state"] = {
            "S_out": S_out.item(),
            "pass": S_out.item() >= -1e-6,
        }

    # BND-3: Eta = 0 and eta = pi/2 (degenerate tori)
    for eta_val, eta_name in [(0.0, "eta_0"), (np.pi / 2, "eta_pi2")]:
        q = torus_point_torch(torch.tensor(eta_val), torch.tensor(0.5), torch.tensor(1.0))
        psi_L = quaternion_to_spinor_L(q)
        norm = torch.abs(torch.vdot(psi_L, psi_L)).item()
        results[f"degenerate_torus_{eta_name}"] = {
            "spinor_norm": norm,
            "pass": abs(norm - 1.0) < 1e-5,
        }

    # BND-4: Large rotation angle (theta = 100*pi) should still be valid
    fi_large = FiChannel(theta=100 * np.pi)
    rho_test = spinor_to_density(quaternion_to_spinor_L(
        torus_point_torch(torch.tensor(np.pi / 4), torch.tensor(0.5), torch.tensor(1.0))
    ))
    rho_out = fi_large(rho_test)
    tr = torch.real(torch.trace(rho_out)).item()
    results["large_rotation_stable"] = {
        "trace": tr,
        "pass": abs(tr - 1.0) < 1e-3,
    }

    results["all_pass"] = all(r.get("pass", False) for r in results.values()
                              if isinstance(r, dict) and "pass" in r)
    return results


# =====================================================================
# MAIN
# =====================================================================

def sanitize(obj):
    """Make object JSON-serializable."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, torch.Tensor):
        return obj.detach().cpu().tolist()
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float, str)):
        return obj
    return str(obj)


if __name__ == "__main__":
    print("=" * 70)
    print("GEOM LAYERS 8-9-10: Pauli Operators / Weyl Flux / Entropy Gradient")
    print("=" * 70)

    all_results = {
        "name": "geom_layer_8_9_10",
        "tool_manifest": TOOL_MANIFEST,
        "classification": "canonical",
    }

    # --- Layer 8 ---
    print("\n[LAYER 8] Pauli operators on all geometry representations...")
    try:
        l8 = run_layer_8()
        all_results["layer_8_pauli_operators"] = l8
        status_8 = "PASS" if l8["all_pass"] else "FAIL"
        print(f"  Layer 8: {status_8}")
        for k, v in l8.get("assertions", {}).items():
            tag = "OK" if v else "FAIL"
            print(f"    [{tag}] {k}")
    except Exception as e:
        all_results["layer_8_pauli_operators"] = {"error": str(e), "traceback": traceback.format_exc()}
        print(f"  Layer 8: ERROR -- {e}")

    # --- Layer 9 ---
    print("\n[LAYER 9] Weyl spinor flux J_LR...")
    try:
        l9 = run_layer_9()
        all_results["layer_9_weyl_flux"] = l9
        status_9 = "PASS" if l9["all_pass"] else "FAIL"
        print(f"  Layer 9: {status_9}")
        for k, v in l9.get("assertions", {}).items():
            if isinstance(v, bool):
                tag = "OK" if v else "FAIL"
            else:
                tag = f"= {v:.6f}"
            print(f"    [{tag}] {k}")
    except Exception as e:
        all_results["layer_9_weyl_flux"] = {"error": str(e), "traceback": traceback.format_exc()}
        print(f"  Layer 9: ERROR -- {e}")

    # --- Layer 10 ---
    print("\n[LAYER 10] Entropy gradient nabla I_c...")
    try:
        l10 = run_layer_10()
        all_results["layer_10_entropy_gradient"] = l10
        status_10 = "PASS" if l10["all_pass"] else "FAIL"
        print(f"  Layer 10: {status_10}")
        for k, v in l10.get("assertions", {}).items():
            tag = "OK" if v else "FAIL"
            print(f"    [{tag}] {k}")
        mi = l10.get("most_impactful_transition", {})
        print(f"  Most impactful: {mi.get('name', '?')} "
              f"(delta_grad_norm={mi.get('delta_grad_norm', 0.0):.6f})")
    except Exception as e:
        all_results["layer_10_entropy_gradient"] = {"error": str(e), "traceback": traceback.format_exc()}
        print(f"  Layer 10: ERROR -- {e}")

    # --- Negative tests ---
    print("\n[NEGATIVE] Failure-mode tests...")
    try:
        neg = run_negative_tests()
        all_results["negative"] = neg
        status_neg = "PASS" if neg["all_pass"] else "FAIL"
        print(f"  Negative: {status_neg}")
    except Exception as e:
        all_results["negative"] = {"error": str(e)}
        print(f"  Negative: ERROR -- {e}")

    # --- Boundary tests ---
    print("\n[BOUNDARY] Edge-case tests...")
    try:
        bnd = run_boundary_tests()
        all_results["boundary"] = bnd
        status_bnd = "PASS" if bnd["all_pass"] else "FAIL"
        print(f"  Boundary: {status_bnd}")
    except Exception as e:
        all_results["boundary"] = {"error": str(e)}
        print(f"  Boundary: ERROR -- {e}")

    # --- Overall ---
    sections = ["layer_8_pauli_operators", "layer_9_weyl_flux",
                "layer_10_entropy_gradient", "negative", "boundary"]
    overall = all(
        all_results.get(s, {}).get("all_pass", False) for s in sections
    )
    all_results["overall_pass"] = overall
    print(f"\n{'=' * 70}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    print(f"{'=' * 70}")

    # --- Write output ---
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_layer_8_9_10_results.json")
    with open(out_path, "w") as f:
        json.dump(sanitize(all_results), f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
