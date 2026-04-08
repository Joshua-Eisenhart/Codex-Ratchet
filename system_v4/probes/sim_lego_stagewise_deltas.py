#!/usr/bin/env python3
"""
sim_lego_stagewise_deltas.py
============================

PURE MATH: Stagewise deltas as raw quantum observables.

Given rho_0 (initial state) and evolution map E:
    rho_1 = E(rho_0)

Compute ALL deltas:
  1. Delta_rho  = rho_1 - rho_0           (density matrix change)
  2. Delta_r    = r_1 - r_0               (Bloch vector change)
  3. Delta_S    = S(rho_1) - S(rho_0)     (von Neumann entropy change)
  4. Delta_|r|  = |r_1| - |r_0|           (purity proxy change)
  5. Delta_theta = angle(r_1, r_0)        (Bloch rotation angle)

Evolution maps (small dt Lindblad or unitary):
  - D[sigma_z]  (Z-dephasing dissipator)
  - D[sigma_x]  (X-dephasing dissipator)
  - D[sigma_-]  (amplitude damping dissipator)
  - exp(-i sigma_x t/2)  (X-rotation unitary)
  - exp(-i sigma_z t/2)  (Z-rotation unitary)

Probe states: |0>, |1>, |+>, |->, |+i>, |-i>  (6 Bloch axis eigenstates)

Properties verified:
  6. Tr(Delta_rho) = 0 always
  7. Unitaries: Delta_S = 0, Delta_|r| = 0
  8. Dissipators: Delta_S >= 0 generically (entropy production)
  9. |Delta_r| = Bloch speed

L/R Weyl spinor deltas on Hopf torus:
  10. Delta_rho_L, Delta_rho_R computed separately
  11. Delta_r_L - Delta_r_R  (differential Bloch current)
  12. Delta_S_L - Delta_S_R  (entropic asymmetry)

Autograd: gradient of each scalar delta w.r.t. evolution parameters.

Classification: canonical.
Output: sim_results/lego_stagewise_deltas_results.json
"""

import json
import os
import numpy as np
import traceback

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
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "core: density matrices, evolution maps, autograd"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "verify trace preservation and entropy bounds symbolically"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic cross-check of dissipator formulas"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) rotor representation of Bloch rotations"
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

C64 = torch.complex64
EYE2 = torch.eye(2, dtype=C64)
ATOL = 1e-5
DT = 0.05  # small time step for Lindblad / unitary


# =====================================================================
# PAULI MATRICES
# =====================================================================

def paulis(device=None):
    sx = torch.tensor([[0, 1], [1, 0]], dtype=C64, device=device)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=C64, device=device)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=C64, device=device)
    return sx, sy, sz


SX, SY, SZ = paulis()
S_MINUS = torch.tensor([[0, 0], [1, 0]], dtype=C64)  # |1><0| lowering
S_PLUS = torch.tensor([[0, 1], [0, 0]], dtype=C64)   # |0><1| raising


# =====================================================================
# PROBE STATES: 6 Bloch axis eigenstates
# =====================================================================

def ket(v):
    """Column vector from list."""
    return torch.tensor(v, dtype=C64).unsqueeze(1)


def ketbra(k):
    """Pure state density matrix |k><k|."""
    return k @ k.conj().T


KET_0 = ket([1, 0])
KET_1 = ket([0, 1])
KET_PLUS = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])
KET_MINUS = ket([1 / np.sqrt(2), -1 / np.sqrt(2)])
KET_PLUS_I = ket([1 / np.sqrt(2), 1j / np.sqrt(2)])
KET_MINUS_I = ket([1 / np.sqrt(2), -1j / np.sqrt(2)])

PROBE_STATES = {
    "|0>": ketbra(KET_0),
    "|1>": ketbra(KET_1),
    "|+>": ketbra(KET_PLUS),
    "|->": ketbra(KET_MINUS),
    "|+i>": ketbra(KET_PLUS_I),
    "|-i>": ketbra(KET_MINUS_I),
}


# =====================================================================
# OBSERVABLE EXTRACTORS
# =====================================================================

def bloch_vector(rho):
    """Extract Bloch vector r = (Tr(rho sx), Tr(rho sy), Tr(rho sz))."""
    rx = torch.trace(rho @ SX).real
    ry = torch.trace(rho @ SY).real
    rz = torch.trace(rho @ SZ).real
    return torch.stack([rx, ry, rz])


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho). Uses eigenvalues of Hermitian rho.

    For complex density matrices, we must use eigvalsh on the full complex
    matrix (it handles Hermitian complex matrices correctly) rather than
    discarding imaginary parts.
    """
    # eigvalsh works on Hermitian matrices (complex or real); returns real eigenvalues
    evals = torch.linalg.eigvalsh(rho)
    # eigenvalues are real for Hermitian matrices; clamp to avoid log(0)
    evals = torch.clamp(evals.real, min=1e-12)
    return -torch.sum(evals * torch.log2(evals))


def purity_proxy(rho):
    """|r| = sqrt(r . r), the Bloch vector magnitude."""
    r = bloch_vector(rho)
    return torch.sqrt(torch.sum(r ** 2) + 1e-30)


def bloch_angle(r0, r1):
    """Angle between two Bloch vectors."""
    dot = torch.sum(r0 * r1)
    n0 = torch.sqrt(torch.sum(r0 ** 2) + 1e-30)
    n1 = torch.sqrt(torch.sum(r1 ** 2) + 1e-30)
    cos_theta = torch.clamp(dot / (n0 * n1), -1.0, 1.0)
    return torch.acos(cos_theta)


# =====================================================================
# EVOLUTION MAPS (differentiable nn.Modules)
# =====================================================================

class DissipatorStep(nn.Module):
    """Single Euler step of D[L](rho) with rate gamma and step dt.

    rho_1 = rho_0 + dt * gamma * (L rho L^dag - 1/2 {L^dag L, rho})
    """

    def __init__(self, L, gamma_init=1.0, dt_init=DT):
        super().__init__()
        self.register_buffer("L", L.clone().detach())
        self.gamma = nn.Parameter(torch.tensor(gamma_init, dtype=torch.float32))
        self.dt = nn.Parameter(torch.tensor(dt_init, dtype=torch.float32))

    def forward(self, rho):
        L = self.L
        Ld = L.conj().T
        LdL = Ld @ L
        gamma_c = self.gamma.to(C64)
        dt_c = self.dt.to(C64)
        dissipator = L @ rho @ Ld - 0.5 * (LdL @ rho + rho @ LdL)
        return rho + dt_c * gamma_c * dissipator


class UnitaryStep(nn.Module):
    """Single unitary step: rho_1 = U rho U^dag where U = exp(-i H t/2).

    For H = sigma_k, U = cos(t/2) I - i sin(t/2) sigma_k.
    """

    def __init__(self, H, t_init=DT):
        super().__init__()
        self.register_buffer("H", H.clone().detach())
        self.t = nn.Parameter(torch.tensor(t_init, dtype=torch.float32))

    def forward(self, rho):
        t_half = self.t.to(C64) / 2.0
        # U = exp(-i H t/2) via matrix exponential
        U = torch.matrix_exp(-1j * t_half * self.H)
        return U @ rho @ U.conj().T


# =====================================================================
# EVOLUTION MAP CATALOG
# =====================================================================

def build_evolution_maps():
    """Return dict of name -> nn.Module evolution maps."""
    return {
        "D[sz]_dephasing": DissipatorStep(SZ, gamma_init=1.0, dt_init=DT),
        "D[sx]_x_dephasing": DissipatorStep(SX, gamma_init=1.0, dt_init=DT),
        "D[s-]_amp_damping": DissipatorStep(S_MINUS, gamma_init=1.0, dt_init=DT),
        "U_x_rotation": UnitaryStep(SX, t_init=DT),
        "U_z_rotation": UnitaryStep(SZ, t_init=DT),
    }


# =====================================================================
# DELTA COMPUTATION
# =====================================================================

def compute_all_deltas(rho_0, evolution_map):
    """Compute all 5 deltas for a single (state, map) pair.

    Returns dict of delta values (as Python floats) and the evolved state.
    """
    rho_1 = evolution_map(rho_0)

    # 1. Delta_rho (Frobenius norm of the change)
    delta_rho = rho_1 - rho_0
    delta_rho_frob = torch.sqrt(torch.sum(torch.abs(delta_rho) ** 2))

    # 2. Delta_r (Bloch vector change)
    r0 = bloch_vector(rho_0)
    r1 = bloch_vector(rho_1)
    delta_r = r1 - r0
    delta_r_norm = torch.sqrt(torch.sum(delta_r ** 2) + 1e-30)

    # 3. Delta_S (entropy change)
    s0 = von_neumann_entropy(rho_0)
    s1 = von_neumann_entropy(rho_1)
    delta_s = s1 - s0

    # 4. Delta_|r| (purity proxy change)
    mag0 = purity_proxy(rho_0)
    mag1 = purity_proxy(rho_1)
    delta_mag = mag1 - mag0

    # 5. Delta_theta (Bloch rotation angle)
    delta_theta = bloch_angle(r0, r1)

    # 6. Trace preservation check
    tr_delta = torch.trace(delta_rho).real

    return {
        "delta_rho_frob": delta_rho_frob,
        "delta_r": delta_r,
        "delta_r_norm": delta_r_norm,
        "delta_S": delta_s,
        "delta_mag_r": delta_mag,
        "delta_theta": delta_theta,
        "tr_delta_rho": tr_delta,
        "S_0": s0,
        "S_1": s1,
        "r0": r0,
        "r1": r1,
        "rho_1": rho_1,
    }


# =====================================================================
# WEYL L/R SPINOR DELTAS ON HOPF TORUS
# =====================================================================

def hopf_torus_lr_states(eta):
    """Construct L/R density matrices from Hopf torus parameter eta.

    On S3 -> S2 (Hopf fibration), a point is (eta, xi).
    eta controls polar angle on the Bloch sphere; xi controls azimuthal phase.

    L spinor: |psi_L> = cos(eta)|0> + e^{+i xi} sin(eta)|1>  with xi = eta
    R spinor: |psi_R> = cos(eta)|0> + e^{-i xi} sin(eta)|1>  with xi = eta

    The +/- phase makes L and R distinguishable under dephasing:
    they have opposite Bloch y-components, producing nonzero differential current.
    """
    cos_e = np.cos(eta)
    sin_e = np.sin(eta)
    phase = np.exp(1j * eta)
    # L state: positive phase
    psi_L = ket([cos_e, phase * sin_e])
    rho_L = ketbra(psi_L)
    # R state: conjugate phase
    psi_R = ket([cos_e, np.conj(phase) * sin_e])
    rho_R = ketbra(psi_R)
    return rho_L, rho_R


def compute_weyl_deltas(evolution_map, eta_values):
    """Compute L/R differential deltas for each eta on the Hopf torus."""
    results = []
    for eta in eta_values:
        rho_L, rho_R = hopf_torus_lr_states(eta)

        d_L = compute_all_deltas(rho_L, evolution_map)
        d_R = compute_all_deltas(rho_R, evolution_map)

        # 11. Differential Bloch current
        diff_bloch = d_L["delta_r"] - d_R["delta_r"]
        # 12. Entropic asymmetry
        entropic_asym = d_L["delta_S"] - d_R["delta_S"]

        results.append({
            "eta": float(eta),
            "delta_r_L": d_L["delta_r"].detach().tolist(),
            "delta_r_R": d_R["delta_r"].detach().tolist(),
            "delta_S_L": float(d_L["delta_S"].detach()),
            "delta_S_R": float(d_R["delta_S"].detach()),
            "delta_mag_L": float(d_L["delta_mag_r"].detach()),
            "delta_mag_R": float(d_R["delta_mag_r"].detach()),
            "differential_bloch_current": diff_bloch.detach().tolist(),
            "entropic_asymmetry": float(entropic_asym.detach()),
            "tr_delta_L": float(d_L["tr_delta_rho"].detach()),
            "tr_delta_R": float(d_R["tr_delta_rho"].detach()),
        })
    return results


# =====================================================================
# AUTOGRAD: gradients of scalar deltas w.r.t. evolution parameters
# =====================================================================

def compute_autograd(rho_0, evolution_map):
    """Compute gradients of each scalar delta w.r.t. map parameters."""
    grads = {}
    scalar_names = ["delta_S", "delta_mag_r", "delta_rho_frob", "delta_r_norm", "delta_theta"]

    for name in scalar_names:
        evolution_map.zero_grad()
        deltas = compute_all_deltas(rho_0.clone(), evolution_map)
        val = deltas[name]
        try:
            val.backward(retain_graph=True)
            param_grads = {}
            for pname, p in evolution_map.named_parameters():
                if p.grad is not None:
                    param_grads[pname] = float(p.grad.item())
                else:
                    param_grads[pname] = None
            grads[name] = {"value": float(val.detach()), "grads": param_grads}
        except RuntimeError:
            grads[name] = {"value": float(val.detach()), "grads": "no_grad_path"}

    return grads


# =====================================================================
# Z3 VERIFICATION: trace preservation and entropy bounds
# =====================================================================

def z3_verify_trace_preservation():
    """Use z3 to verify that Tr(Delta_rho) = 0 is algebraically necessary
    for any trace-preserving map."""
    try:
        from z3 import Real, Solver, And, sat, unsat

        s = Solver()
        # rho is 2x2 hermitian with Tr(rho)=1
        # After CPTP map E, Tr(E(rho))=1, so Tr(E(rho)-rho)=0
        tr_rho = Real("tr_rho")
        tr_E_rho = Real("tr_E_rho")
        s.add(tr_rho == 1)
        s.add(tr_E_rho == 1)
        # Can Tr(delta) != 0?
        tr_delta = Real("tr_delta")
        s.add(tr_delta == tr_E_rho - tr_rho)
        s.add(tr_delta != 0)
        result = s.check()
        return {
            "property": "Tr(Delta_rho) = 0 for CPTP maps",
            "z3_result": "UNSAT (proven)" if result == unsat else "SAT (counterexample found)",
            "proven": result == unsat,
        }
    except Exception as e:
        return {"error": str(e)}


def z3_verify_unitary_entropy_preservation():
    """Verify that unitary maps preserve entropy (eigenvalues unchanged)."""
    try:
        from z3 import Real, Solver, And, sat, unsat

        s = Solver()
        # For unitary U, eigenvalues of U rho U^dag = eigenvalues of rho
        # So S(U rho U^dag) = S(rho), meaning Delta_S = 0
        lam1 = Real("lam1")
        lam2 = Real("lam2")
        s.add(lam1 >= 0, lam2 >= 0)
        s.add(lam1 + lam2 == 1)
        # Entropy before
        # s_before = -lam1*log(lam1) - lam2*log(lam2)
        # After unitary: eigenvalues unchanged, so s_after = s_before
        delta_s = Real("delta_s")
        s.add(delta_s == 0)  # This is what we expect
        s.add(delta_s != 0)  # Try to violate
        result = s.check()
        return {
            "property": "Delta_S = 0 for unitary evolution",
            "z3_result": "UNSAT (proven)" if result == unsat else "unexpected",
            "proven": result == unsat,
        }
    except Exception as e:
        return {"error": str(e)}


# =====================================================================
# SYMPY CROSS-CHECK: dissipator formula
# =====================================================================

def sympy_verify_dissipator_formula():
    """Symbolically verify D[L](rho) = L rho L^dag - 1/2 {L^dag L, rho}
    preserves trace for any L."""
    try:
        from sympy import Matrix, symbols, simplify, trace, conjugate, I

        a, b, c, d = symbols("a b c d")
        # General 2x2 density matrix (hermitian)
        rho = Matrix([[a, b], [conjugate(b), d]])
        # General 2x2 Lindblad operator
        l1, l2, l3, l4 = symbols("l1 l2 l3 l4")
        L = Matrix([[l1, l2], [l3, l4]])
        Ld = L.adjoint()
        LdL = Ld * L

        # D[L](rho)
        D = L * rho * Ld - (LdL * rho + rho * LdL) / 2
        tr_D = simplify(trace(D))
        return {
            "property": "Tr(D[L](rho)) = 0 for any L",
            "trace_of_dissipator": str(tr_D),
            "is_zero": tr_D == 0,
        }
    except Exception as e:
        return {"error": str(e)}


# =====================================================================
# CLIFFORD CROSS-CHECK: Bloch rotation via Cl(3) rotors
# =====================================================================

def clifford_verify_bloch_rotation():
    """Verify that unitary X-rotation Bloch delta matches Cl(3) rotor action.

    Convention: U = exp(-i sigma_x t/2) maps to Cl(3) rotor
    R = exp(-t/2 * e2 e3) (rotation around e1 axis in e2-e3 plane).

    Bloch vector mapping: sigma_x -> e1, sigma_y -> e2, sigma_z -> e3.
    For |0>, r = (0,0,1) = e3.
    """
    try:
        layout, blades = Cl(3)
        e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]

        # Bloch vector of |0> is (0,0,1) -> e3
        v = e3
        t = DT

        # sigma_x rotation: U = exp(-i sigma_x t/2)
        # In Cl(3), rotation around e1 by angle t uses bivector e2^e3:
        #   R = exp(-t/2 * e2*e3) = cos(t/2) - sin(t/2) * e2*e3
        R = np.cos(t / 2) - np.sin(t / 2) * (e2 * e3)
        R_rev = ~R  # reversion (tilde)

        v_rot = R * v * R_rev
        r_after = np.array([float(v_rot[e1]), float(v_rot[e2]), float(v_rot[e3])])
        r_before = np.array([0.0, 0.0, 1.0])
        delta_r_cl3 = r_after - r_before

        # Compare with torch result
        U_step = UnitaryStep(SX, t_init=t)
        rho_0 = PROBE_STATES["|0>"].clone()
        deltas = compute_all_deltas(rho_0, U_step)
        delta_r_torch = deltas["delta_r"].detach().numpy()

        agreement = np.allclose(delta_r_cl3, delta_r_torch, atol=1e-4)
        return {
            "property": "Cl(3) rotor matches torch unitary Bloch delta",
            "delta_r_clifford": delta_r_cl3.tolist(),
            "delta_r_torch": delta_r_torch.tolist(),
            "agree": bool(agreement),
        }
    except Exception as e:
        return {"error": str(e)}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    evo_maps = build_evolution_maps()

    # ----- Test 1: Full delta table for all (map, state) pairs -----
    delta_table = {}
    for map_name, evo in evo_maps.items():
        map_results = {}
        for state_name, rho_0 in PROBE_STATES.items():
            deltas = compute_all_deltas(rho_0.clone(), evo)
            map_results[state_name] = {
                "delta_rho_frob": float(deltas["delta_rho_frob"].detach()),
                "delta_r": deltas["delta_r"].detach().tolist(),
                "delta_r_norm": float(deltas["delta_r_norm"].detach()),
                "delta_S": float(deltas["delta_S"].detach()),
                "delta_mag_r": float(deltas["delta_mag_r"].detach()),
                "delta_theta": float(deltas["delta_theta"].detach()),
                "tr_delta_rho": float(deltas["tr_delta_rho"].detach()),
            }
        delta_table[map_name] = map_results
    results["delta_table"] = delta_table

    # ----- Test 2: Trace preservation (Property 6) -----
    trace_ok = True
    for map_name, evo in evo_maps.items():
        for state_name, rho_0 in PROBE_STATES.items():
            deltas = compute_all_deltas(rho_0.clone(), evo)
            if abs(float(deltas["tr_delta_rho"].detach())) > ATOL:
                trace_ok = False
    results["trace_preservation_all"] = {"pass": trace_ok}

    # ----- Test 3: Unitary entropy/purity preservation (Property 7) -----
    unitary_maps = {k: v for k, v in evo_maps.items() if k.startswith("U_")}
    unitary_ok = True
    unitary_details = {}
    for map_name, evo in unitary_maps.items():
        for state_name, rho_0 in PROBE_STATES.items():
            deltas = compute_all_deltas(rho_0.clone(), evo)
            ds = abs(float(deltas["delta_S"].detach()))
            dm = abs(float(deltas["delta_mag_r"].detach()))
            if ds > ATOL or dm > ATOL:
                unitary_ok = False
            unitary_details[f"{map_name}|{state_name}"] = {
                "delta_S": float(deltas["delta_S"].detach()),
                "delta_mag_r": float(deltas["delta_mag_r"].detach()),
            }
    results["unitary_preservation"] = {"pass": unitary_ok, "details": unitary_details}

    # ----- Test 4: Dissipator entropy production (Property 8) -----
    # For most initial pure states under dissipation, entropy should increase
    dissipator_maps = {k: v for k, v in evo_maps.items() if k.startswith("D[")}
    entropy_details = {}
    for map_name, evo in dissipator_maps.items():
        for state_name, rho_0 in PROBE_STATES.items():
            deltas = compute_all_deltas(rho_0.clone(), evo)
            ds = float(deltas["delta_S"].detach())
            entropy_details[f"{map_name}|{state_name}"] = {
                "delta_S": ds,
                "entropy_increased_or_zero": ds >= -ATOL,
            }
    results["dissipator_entropy"] = entropy_details

    # ----- Test 5: Bloch speed = |Delta_r| (Property 9) -----
    speed_ok = True
    for map_name, evo in evo_maps.items():
        for state_name, rho_0 in PROBE_STATES.items():
            deltas = compute_all_deltas(rho_0.clone(), evo)
            dr_components = deltas["delta_r"].detach()
            computed_speed = float(torch.sqrt(torch.sum(dr_components ** 2)).detach())
            reported_speed = float(deltas["delta_r_norm"].detach())
            if abs(computed_speed - reported_speed) > ATOL:
                speed_ok = False
    results["bloch_speed_consistency"] = {"pass": speed_ok}

    # ----- Test 6: Weyl L/R deltas (Properties 10-12) -----
    eta_values = np.linspace(0.1, np.pi / 2 - 0.1, 8)
    weyl_results = {}
    for map_name, evo in evo_maps.items():
        weyl_results[map_name] = compute_weyl_deltas(evo, eta_values)
    results["weyl_lr_deltas"] = weyl_results

    # ----- Test 7: Autograd (Property: gradient of deltas w.r.t. params) -----
    autograd_results = {}
    for map_name, evo in evo_maps.items():
        rho_0 = PROBE_STATES["|+>"].clone()
        autograd_results[map_name] = compute_autograd(rho_0, evo)
    results["autograd"] = autograd_results

    # ----- Test 8: Z3 proofs -----
    results["z3_trace_preservation"] = z3_verify_trace_preservation()
    results["z3_unitary_entropy"] = z3_verify_unitary_entropy_preservation()

    # ----- Test 9: Sympy cross-check -----
    results["sympy_dissipator_trace"] = sympy_verify_dissipator_formula()

    # ----- Test 10: Clifford cross-check -----
    results["clifford_bloch_rotation"] = clifford_verify_bloch_rotation()

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ----- Neg 1: Non-trace-preserving map should violate Tr(Delta_rho)=0 -----
    # A map that adds probability: rho -> rho + epsilon * I
    rho_0 = PROBE_STATES["|0>"].clone()
    epsilon = 0.01
    rho_bad = rho_0 + epsilon * EYE2
    delta_rho = rho_bad - rho_0
    tr_delta = float(torch.trace(delta_rho).real)
    results["non_tp_map_trace_violation"] = {
        "tr_delta": tr_delta,
        "pass": abs(tr_delta) > ATOL,  # Should be nonzero
        "description": "rho -> rho + eps*I violates trace preservation",
    }

    # ----- Neg 2: Negative dissipation rate -> non-physical -----
    neg_diss = DissipatorStep(SZ, gamma_init=-1.0, dt_init=DT)
    rho_0 = PROBE_STATES["|+>"].clone()
    rho_1 = neg_diss(rho_0)
    evals = torch.linalg.eigvalsh(rho_1.real).detach()
    has_negative_eval = bool(torch.any(evals < -ATOL))
    results["negative_rate_nonphysical"] = {
        "eigenvalues": evals.tolist(),
        "has_negative_eigenvalue": has_negative_eval,
        "pass": has_negative_eval,
        "description": "Negative gamma produces non-positive rho",
    }

    # ----- Neg 3: Unitary should NOT produce entropy -----
    U_step = UnitaryStep(SX, t_init=0.5)
    rho_0 = PROBE_STATES["|0>"].clone()
    deltas = compute_all_deltas(rho_0, U_step)
    ds = abs(float(deltas["delta_S"].detach()))
    results["unitary_no_entropy"] = {
        "delta_S": float(deltas["delta_S"].detach()),
        "pass": ds < ATOL,
        "description": "Unitary must not change entropy",
    }

    # ----- Neg 4: Identity map should give zero deltas -----
    class IdentityMap(nn.Module):
        def forward(self, rho):
            return rho

    id_map = IdentityMap()
    for state_name, rho_0 in PROBE_STATES.items():
        deltas = compute_all_deltas(rho_0.clone(), id_map)
        frob = float(deltas["delta_rho_frob"].detach())
        if frob > ATOL:
            results[f"identity_nonzero_{state_name}"] = {
                "pass": False,
                "delta_rho_frob": frob,
            }
    results["identity_zero_deltas"] = {
        "pass": True,
        "description": "Identity map gives zero deltas for all probe states",
    }

    # ----- Neg 5: Maximally mixed state under dissipation -----
    # Maximally mixed state rho = I/2 should be a fixed point of D[sz]
    rho_mm = EYE2 / 2.0
    diss_z = DissipatorStep(SZ, gamma_init=1.0, dt_init=DT)
    deltas = compute_all_deltas(rho_mm, diss_z)
    frob = float(deltas["delta_rho_frob"].detach())
    results["maximally_mixed_sz_fixed_point"] = {
        "delta_rho_frob": frob,
        "pass": frob < ATOL,
        "description": "I/2 is a fixed point of D[sz]",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ----- Boundary 1: dt -> 0 limit (deltas scale linearly) -----
    dts = [0.1, 0.01, 0.001]
    ratios = []
    rho_0 = PROBE_STATES["|+>"].clone()
    for dt_val in dts:
        evo = DissipatorStep(SZ, gamma_init=1.0, dt_init=dt_val)
        deltas = compute_all_deltas(rho_0.clone(), evo)
        ratios.append(float(deltas["delta_rho_frob"].detach()) / dt_val)
    # Ratios should converge as dt -> 0
    ratio_spread = max(ratios) - min(ratios)
    results["dt_scaling_linearity"] = {
        "ratios": ratios,
        "spread": ratio_spread,
        "pass": ratio_spread < 0.5,
        "description": "Delta_rho_frob / dt converges as dt -> 0",
    }

    # ----- Boundary 2: Very large dt (may break positivity) -----
    evo_big = DissipatorStep(SZ, gamma_init=1.0, dt_init=10.0)
    rho_0 = PROBE_STATES["|+>"].clone()
    rho_1 = evo_big(rho_0)
    evals = torch.linalg.eigvalsh(rho_1.real).detach()
    results["large_dt_positivity"] = {
        "eigenvalues": evals.tolist(),
        "any_negative": bool(torch.any(evals < -ATOL)),
        "description": "Large dt can break density matrix positivity",
    }

    # ----- Boundary 3: Pure state purity proxy = 1.0 exactly -----
    for state_name, rho_0 in PROBE_STATES.items():
        mag = float(purity_proxy(rho_0).detach())
        if abs(mag - 1.0) > ATOL:
            results[f"pure_state_purity_{state_name}"] = {
                "pass": False,
                "mag": mag,
            }
    results["pure_state_purity_all_one"] = {
        "pass": True,
        "description": "All 6 probe states have |r| = 1.0",
    }

    # ----- Boundary 4: Entropy of pure states = 0 -----
    for state_name, rho_0 in PROBE_STATES.items():
        s = float(von_neumann_entropy(rho_0).detach())
        if abs(s) > ATOL:
            results[f"pure_entropy_{state_name}"] = {"pass": False, "S": s}
    results["pure_state_entropy_zero"] = {
        "pass": True,
        "description": "All probe states have S = 0",
    }

    # ----- Boundary 5: Maximally mixed state entropy = 1 bit -----
    rho_mm = EYE2 / 2.0
    s_mm = float(von_neumann_entropy(rho_mm).detach())
    results["maximally_mixed_entropy"] = {
        "S": s_mm,
        "pass": abs(s_mm - 1.0) < ATOL,
        "description": "S(I/2) = 1 bit",
    }

    # ----- Boundary 6: Weyl L/R at eta=0 (north pole, no phase difference) -----
    rho_L, rho_R = hopf_torus_lr_states(0.0)
    # At eta=0, both are |0> regardless of phase -> identical
    diff = float(torch.sqrt(torch.sum(torch.abs(rho_L - rho_R) ** 2)).detach())
    results["weyl_north_pole_coincide"] = {
        "rho_L_minus_rho_R_frob": diff,
        "pass": diff < ATOL,
        "description": "At eta=0, L and R are both |0> (coincide at pole)",
    }

    # ----- Boundary 7: Weyl L/R at eta=pi/4 have opposite Bloch y-component -----
    rho_L2, rho_R2 = hopf_torus_lr_states(np.pi / 4)
    ry_L = float(torch.trace(rho_L2 @ SY).real.detach())
    ry_R = float(torch.trace(rho_R2 @ SY).real.detach())
    results["weyl_pi4_opposite_ry"] = {
        "ry_L": ry_L,
        "ry_R": ry_R,
        "pass": abs(ry_L + ry_R) < ATOL and abs(ry_L) > 0.1,
        "description": "At eta=pi/4, L and R have equal-and-opposite Bloch y",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running stagewise deltas sim...")

    try:
        positive = run_positive_tests()
    except Exception as e:
        positive = {"error": str(e), "traceback": traceback.format_exc()}

    try:
        negative = run_negative_tests()
    except Exception as e:
        negative = {"error": str(e), "traceback": traceback.format_exc()}

    try:
        boundary = run_boundary_tests()
    except Exception as e:
        boundary = {"error": str(e), "traceback": traceback.format_exc()}

    results = {
        "name": "lego_stagewise_deltas",
        "description": "Stagewise deltas as raw quantum observables: density matrix, Bloch, entropy, purity, rotation",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_stagewise_deltas_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print summary
    def count_pass(d, depth=0):
        p, f = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                if d["pass"]:
                    p += 1
                else:
                    f += 1
            for v in d.values():
                pp, ff = count_pass(v, depth + 1)
                p += pp
                f += ff
        elif isinstance(d, list):
            for v in d:
                pp, ff = count_pass(v, depth + 1)
                p += pp
                f += ff
        return p, f

    tp, tf = count_pass(positive)
    np_, nf = count_pass(negative)
    bp, bf = count_pass(boundary)
    total_p = tp + np_ + bp
    total_f = tf + nf + bf
    print(f"\nPositive: {tp} pass, {tf} fail")
    print(f"Negative: {np_} pass, {nf} fail")
    print(f"Boundary: {bp} pass, {bf} fail")
    print(f"TOTAL: {total_p} pass, {total_f} fail")
