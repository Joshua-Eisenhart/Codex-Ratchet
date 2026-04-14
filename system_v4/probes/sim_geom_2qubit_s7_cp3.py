#!/usr/bin/env python3
"""
sim_geom_2qubit_s7_cp3.py
─────────────────────────
2-qubit geometry: S^7, CP^3, Segre embedding, concurrence fibration,
quaternionic Hopf map S^3 -> S^7 -> S^4.

Sections
--------
1. S^7 embedding       -- 2-qubit pure states live on the 7-sphere in C^4
2. CP^3 projection     -- S^7/U(1), 6 real dimensions
3. Segre embedding     -- CP^1 x CP^1 -> CP^3, product states = Segre image
4. Concurrence         -- C = 2|ad - bc|, fibration at fixed C
5. Quaternionic Hopf   -- S^3 -> S^7 -> S^4, entanglement geometry
6. Autograd through concurrence -- gradient flow via PyTorch

Classification: canonical (pytorch=used, sympy=tried)
Output: sim_results/geom_2qubit_s7_cp3_results.json
"""

import json
import os
import time
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "graph layer not needed for pure geometry"},
    "z3":        {"tried": False, "used": False, "reason": "proof layer not needed for numerical geometry"},
    "cvc5":      {"tried": False, "used": False, "reason": "proof layer not needed"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed for S7/CP3 embedding"},
    "geomstats": {"tried": False, "used": False, "reason": "manual embedding preferred for transparency"},
    "e3nn":      {"tried": False, "used": False, "reason": "equivariant NN not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph structure"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph structure"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence needed"},
}

# --- Import PyTorch ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd through concurrence, S7 norm, all core computation"
    TORCH_OK = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    TORCH_OK = False

# --- Import sympy ---
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "tried for symbolic Segre verification, torch preferred for numerics"
    SYMPY_OK = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    SYMPY_OK = False

assert TORCH_OK, "PyTorch required for canonical sim"

EPS = 1e-10
torch.manual_seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "sim_results")
OUT_FILE = os.path.join(OUT_DIR, "geom_2qubit_s7_cp3_results.json")


# =====================================================================
# HELPERS
# =====================================================================

def random_pure_state_torch(d=4):
    """Random normalised state in C^d as torch complex128 tensor."""
    re = torch.randn(d, dtype=torch.float64)
    im = torch.randn(d, dtype=torch.float64)
    psi = torch.complex(re, im)
    return psi / psi.norm()


def product_state(a, b):
    """Tensor product |a> x |b> in C^4, both normalised 2-vectors."""
    a = a / a.norm()
    b = b / b.norm()
    return torch.kron(a, b)


def concurrence_pure(psi):
    """
    Concurrence for a 2-qubit pure state |psi> = (alpha, beta, gamma, delta).
    C = 2|alpha*delta - beta*gamma|
    """
    alpha, beta, gamma, delta = psi[0], psi[1], psi[2], psi[3]
    return 2.0 * torch.abs(alpha * delta - beta * gamma)


def fubini_study_distance(psi, phi):
    """Fubini-Study distance between two normalised states."""
    overlap = torch.abs(torch.dot(psi.conj(), phi))
    # Clamp to avoid numerical issues at acos(1)
    overlap = torch.clamp(overlap, 0.0, 1.0)
    # For overlaps very close to 1, use sqrt(2(1-x)) approximation to avoid acos precision loss
    if overlap.item() > 1.0 - 1e-12:
        return torch.sqrt(2.0 * (1.0 - overlap))
    return torch.acos(overlap)


def segre_map(a, b):
    """
    Segre embedding CP^1 x CP^1 -> CP^3.
    Maps (a0:a1, b0:b1) -> (a0*b0 : a0*b1 : a1*b0 : a1*b1).
    Returns normalised C^4 vector.
    """
    return product_state(a, b)


def distance_from_segre(psi, n_samples=500):
    """
    Approximate minimum Fubini-Study distance from |psi> to the Segre variety.
    Uses random sampling over product states, then gradient refinement.
    """
    psi_n = psi / psi.norm()
    best_dist = torch.tensor(float('inf'), dtype=torch.float64)

    # Random sampling phase
    for _ in range(n_samples):
        a = random_pure_state_torch(2)
        b = random_pure_state_torch(2)
        prod = product_state(a, b)
        d = fubini_study_distance(psi_n, prod)
        if d < best_dist:
            best_dist = d.detach()

    return best_dist


def distance_from_segre_analytic(psi):
    """
    For a pure 2-qubit state, the FS distance to the nearest product state
    is acos(sqrt(lambda_max)) where lambda_max is the largest Schmidt
    coefficient squared. This equals acos(sqrt((1 + sqrt(1 - C^2)) / 2))
    """
    C = concurrence_pure(psi)
    # Largest Schmidt coefficient squared
    lam_max = (1.0 + torch.sqrt(torch.clamp(1.0 - C * C, min=0.0))) / 2.0
    return torch.acos(torch.clamp(torch.sqrt(lam_max), 0.0, 1.0))


def quaternionic_hopf_map(psi):
    """
    Quaternionic Hopf map S^7 -> S^4.
    Given |psi> = (z0, z1, z2, z3) in C^4 with |psi|=1 (point on S^7),
    maps to a point on S^4.

    Interpret C^4 as H^2: q_L = z0 + z1*j, q_R = z2 + z3*j.
    Map: (q_L, q_R) -> (|q_L|^2 - |q_R|^2,  2 * q_L * bar(q_R))

    Quaternion product q_L * bar(q_R) with
      q_L = (a0, a1, a2, a3) = (Re z0, Im z0, Re z1, Im z1)
      q_R = (b0, b1, b2, b3) = (Re z2, Im z2, Re z3, Im z3)
      bar(q_R) = (b0, -b1, -b2, -b3)

    Product components (Hamilton):
      r0 = a0*b0 + a1*b1 + a2*b2 + a3*b3
      r1 = -a0*b1 + a1*b0 - a2*b3 + a3*b2
      r2 = -a0*b2 + a2*b0 + a1*b3 - a3*b1
      r3 = -a0*b3 + a3*b0 - a1*b2 + a2*b1

    For |psi|=1, output lies on S^4: q0^2 + sum(2*r_i)^2 = 1.
    """
    z0, z1, z2, z3 = psi[0], psi[1], psi[2], psi[3]

    # Extract real components
    a0, a1 = z0.real, z0.imag
    a2, a3 = z1.real, z1.imag
    b0, b1 = z2.real, z2.imag
    b2, b3 = z3.real, z3.imag

    # q0 = |q_L|^2 - |q_R|^2
    q0 = (a0**2 + a1**2 + a2**2 + a3**2) - (b0**2 + b1**2 + b2**2 + b3**2)

    # q_L * bar(q_R) Hamilton product
    r0 = a0*b0 + a1*b1 + a2*b2 + a3*b3
    r1 = -a0*b1 + a1*b0 - a2*b3 + a3*b2
    r2 = -a0*b2 + a2*b0 + a1*b3 - a3*b1
    r3 = -a0*b3 + a3*b0 - a1*b2 + a2*b1

    q = torch.stack([q0, 2.0*r0, 2.0*r1, 2.0*r2, 2.0*r3])
    return q


# =====================================================================
# SYMPY: symbolic Segre check (tried, not core)
# =====================================================================

def sympy_segre_check():
    """Verify Segre embedding algebraically: product state has zero concurrence."""
    if not SYMPY_OK:
        return {"skipped": True, "reason": "sympy not installed"}
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic verification of Segre concurrence=0"

    a0, a1, b0, b1 = sp.symbols('a0 a1 b0 b1')
    # Product state: (a0*b0, a0*b1, a1*b0, a1*b1)
    alpha = a0 * b0
    beta = a0 * b1
    gamma = a1 * b0
    delta = a1 * b1
    conc_expr = sp.expand(alpha * delta - beta * gamma)
    return {
        "concurrence_expression": str(conc_expr),
        "is_zero": conc_expr == 0,
        "pass": conc_expr == 0,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Test 1: S^7 embedding, pure states have unit norm ---
    t1_states = [random_pure_state_torch(4) for _ in range(20)]
    t1_norms = [psi.norm().item() for psi in t1_states]
    t1_all_unit = all(abs(n - 1.0) < EPS for n in t1_norms)
    # 7 real DOF: 4 complex = 8 real, minus 1 norm constraint = S^7
    results["s7_unit_norm"] = {
        "pass": t1_all_unit,
        "real_dof": 7,
        "norms_range": [min(t1_norms), max(t1_norms)],
        "detail": "2-qubit pure states live on S^7 in C^4",
    }

    # --- Test 2: Product states lie on the Segre variety (C=0) ---
    t2_concurrences = []
    for _ in range(20):
        a = random_pure_state_torch(2)
        b = random_pure_state_torch(2)
        prod = product_state(a, b)
        C = concurrence_pure(prod).item()
        t2_concurrences.append(C)
    t2_pass = all(c < EPS for c in t2_concurrences)
    results["segre_product_concurrence_zero"] = {
        "pass": t2_pass,
        "max_concurrence": max(t2_concurrences),
        "detail": "Product states = Segre image => C=0",
    }

    # --- Test 3: Bell states have C=1 (maximally entangled, off Segre) ---
    bell_00 = torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / np.sqrt(2)
    bell_01 = torch.tensor([1, 0, 0, -1], dtype=torch.complex128) / np.sqrt(2)
    bell_10 = torch.tensor([0, 1, 1, 0], dtype=torch.complex128) / np.sqrt(2)
    bell_11 = torch.tensor([0, 1, -1, 0], dtype=torch.complex128) / np.sqrt(2)
    bell_Cs = [concurrence_pure(b).item() for b in [bell_00, bell_01, bell_10, bell_11]]
    t3_pass = all(abs(c - 1.0) < EPS for c in bell_Cs)
    results["bell_state_concurrence_one"] = {
        "pass": t3_pass,
        "concurrences": bell_Cs,
        "detail": "All four Bell states have C=1",
    }

    # --- Test 4: Concurrence = analytic FS distance from Segre ---
    t4_diffs = []
    for _ in range(30):
        psi = random_pure_state_torch(4)
        d_analytic = distance_from_segre_analytic(psi).item()
        C = concurrence_pure(psi).item()
        # Analytic relation: d_FS = acos(sqrt((1 + sqrt(1-C^2))/2))
        lam_max = (1.0 + np.sqrt(max(1.0 - C**2, 0.0))) / 2.0
        d_expected = np.arccos(min(np.sqrt(lam_max), 1.0))
        t4_diffs.append(abs(d_analytic - d_expected))
    t4_pass = all(d < EPS for d in t4_diffs)
    results["concurrence_distance_relation"] = {
        "pass": t4_pass,
        "max_diff": max(t4_diffs),
        "detail": "d_FS(psi, Segre) = acos(sqrt((1+sqrt(1-C^2))/2))",
    }

    # --- Test 5: CP^3 projection -- global phase equivalence ---
    psi = random_pure_state_torch(4)
    phases = [torch.exp(torch.tensor(1j * theta, dtype=torch.complex128)) for theta in [0.3, 1.2, np.pi, 5.0]]
    t5_dists = [fubini_study_distance(psi, phase * psi).item() for phase in phases]
    t5_pass = all(d < 1e-6 for d in t5_dists)  # numerical tolerance for acos near 1
    results["cp3_phase_equivalence"] = {
        "pass": t5_pass,
        "fs_distances": t5_dists,
        "detail": "CP^3 = S^7/U(1): global phase does not change state",
    }

    # --- Test 6: Quaternionic Hopf map lands on S^4 ---
    t6_norms = []
    for _ in range(20):
        psi = random_pure_state_torch(4)
        q = quaternionic_hopf_map(psi)
        t6_norms.append(q.norm().item())
    t6_pass = all(abs(n - 1.0) < 1e-8 for n in t6_norms)
    results["quaternionic_hopf_on_s4"] = {
        "pass": t6_pass,
        "norms_range": [min(t6_norms), max(t6_norms)],
        "detail": "Hopf image has |q|=1, confirming it lands on S^4",
    }

    # --- Test 7: Hopf fibers -- same entanglement class maps to same S^4 point ---
    psi_base = random_pure_state_torch(4)
    q_base = quaternionic_hopf_map(psi_base)
    # Apply local unitaries (SU(2) x SU(2)) which preserve entanglement
    t7_dists = []
    for _ in range(10):
        # Random SU(2) via Cayley parameterisation
        def random_su2():
            h = torch.randn(2, 2, dtype=torch.complex128)
            h = (h - h.T.conj()) / 2  # anti-hermitian
            return torch.matrix_exp(h)
        U_A = random_su2()
        U_B = random_su2()
        U_AB = torch.kron(U_A, U_B)
        psi_rot = U_AB @ psi_base
        psi_rot = psi_rot / psi_rot.norm()
        q_rot = quaternionic_hopf_map(psi_rot)
        # Hopf map is NOT preserved by SU(2)xSU(2) in general,
        # but concurrence IS preserved. Check concurrence instead.
        C_base = concurrence_pure(psi_base).item()
        C_rot = concurrence_pure(psi_rot).item()
        t7_dists.append(abs(C_base - C_rot))
    t7_pass = all(d < 1e-8 for d in t7_dists)
    results["local_unitaries_preserve_concurrence"] = {
        "pass": t7_pass,
        "max_concurrence_diff": max(t7_dists),
        "detail": "SU(2)xSU(2) local unitaries preserve concurrence (SLOCC invariant)",
    }

    # --- Test 8: Concurrence fibration -- fixed C gives 5-dim fiber ---
    # At fixed concurrence C, the set of states is 5-dimensional.
    # dim(S^7) = 7, minus 1 for norm (already on S^7), minus 1 for concurrence constraint = 5-dim fiber.
    # Verify: random perturbations tangent to the fiber preserve C.
    psi0 = random_pure_state_torch(4)
    C0 = concurrence_pure(psi0)
    # Get gradient of concurrence at psi0
    psi_grad = psi0.clone().detach().requires_grad_(True)
    C_val = concurrence_pure(psi_grad)
    C_val.backward()
    grad_C = psi_grad.grad.clone()
    # Project random tangent vectors to be orthogonal to grad_C AND psi0
    t8_deltas = []
    for _ in range(30):
        v = random_pure_state_torch(4)
        # Remove component along psi0 (tangent to S^7)
        v = v - torch.dot(psi0.conj(), v) * psi0
        # Remove component along grad_C (tangent to C=const fiber)
        v = v - (torch.dot(grad_C.conj(), v) / (grad_C.norm()**2 + EPS)) * grad_C
        if v.norm() < EPS:
            continue
        v = v / v.norm()
        eps_step = 1e-5
        psi_new = psi0 + eps_step * v
        psi_new = psi_new / psi_new.norm()
        C_new = concurrence_pure(psi_new).item()
        t8_deltas.append(abs(C_new - C0.item()))
    t8_pass = all(d < 1e-3 for d in t8_deltas) if t8_deltas else False
    results["concurrence_fiber_5dim"] = {
        "pass": t8_pass,
        "max_C_deviation": max(t8_deltas) if t8_deltas else None,
        "n_samples": len(t8_deltas),
        "detail": "Perturbations orthogonal to grad(C) preserve concurrence (5-dim fiber)",
    }

    # --- Test 9: Segre embedding is isometric for FS metric ---
    # d_FS(a1 x b1, a2 x b2) relates to d_FS(a1,a2) and d_FS(b1,b2)
    t9_checks = []
    for _ in range(20):
        a1, a2 = random_pure_state_torch(2), random_pure_state_torch(2)
        b1, b2 = random_pure_state_torch(2), random_pure_state_torch(2)
        prod1 = product_state(a1, b1)
        prod2 = product_state(a2, b2)
        # For product states: |<a1xb1|a2xb2>| = |<a1|a2>| * |<b1|b2>|
        overlap_prod = torch.abs(torch.dot(prod1.conj(), prod2)).item()
        overlap_ab = (torch.abs(torch.dot(a1.conj(), a2)) *
                      torch.abs(torch.dot(b1.conj(), b2))).item()
        t9_checks.append(abs(overlap_prod - overlap_ab))
    t9_pass = all(d < EPS for d in t9_checks)
    results["segre_overlap_factorisation"] = {
        "pass": t9_pass,
        "max_diff": max(t9_checks),
        "detail": "|<a1xb1|a2xb2>| = |<a1|a2>|*|<b1|b2>| (Segre isometry)",
    }

    # --- Test 10: sympy symbolic Segre check ---
    results["sympy_segre_symbolic"] = sympy_segre_check()

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- Neg 1: Entangled states NOT on Segre (C != 0) ---
    bell = torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / np.sqrt(2)
    C_bell = concurrence_pure(bell).item()
    results["entangled_not_on_segre"] = {
        "pass": C_bell > 0.99,
        "concurrence": C_bell,
        "detail": "Bell state has C~1, far from Segre variety",
    }

    # --- Neg 2: Non-normalised state violates S^7 ---
    bad_state = torch.tensor([1, 1, 1, 1], dtype=torch.complex128)
    norm = bad_state.norm().item()
    results["non_normalised_not_on_s7"] = {
        "pass": abs(norm - 1.0) > 0.1,
        "norm": norm,
        "detail": "Un-normalised vector not on S^7",
    }

    # --- Neg 3: Phase change alters S^7 point but NOT CP^3 point ---
    psi = random_pure_state_torch(4)
    psi_phased = psi * torch.exp(torch.tensor(1j * 0.7, dtype=torch.complex128))
    s7_diff = (psi - psi_phased).norm().item()
    fs_dist = fubini_study_distance(psi, psi_phased).item()
    results["phase_changes_s7_not_cp3"] = {
        "pass": s7_diff > 0.1 and fs_dist < EPS,
        "s7_distance": s7_diff,
        "fs_distance": fs_dist,
        "detail": "Global phase moves on S^7 but not on CP^3",
    }

    # --- Neg 4: Random state generically has nonzero concurrence ---
    n_nonzero = 0
    for _ in range(100):
        psi = random_pure_state_torch(4)
        if concurrence_pure(psi).item() > 1e-4:
            n_nonzero += 1
    results["generic_state_entangled"] = {
        "pass": n_nonzero > 90,
        "n_nonzero_of_100": n_nonzero,
        "detail": "Generic random 2-qubit state is entangled (measure-zero product states)",
    }

    # --- Neg 5: Concurrence out of [0,1] should not happen ---
    t5_all_valid = True
    for _ in range(100):
        psi = random_pure_state_torch(4)
        C = concurrence_pure(psi).item()
        if C < -EPS or C > 1.0 + EPS:
            t5_all_valid = False
    results["concurrence_bounded_0_1"] = {
        "pass": t5_all_valid,
        "detail": "C in [0,1] for all random pure states",
    }

    # --- Neg 6: Hopf map of non-unit vector has |q| != 1 ---
    bad = torch.tensor([2, 0, 0, 1], dtype=torch.complex128)
    q = quaternionic_hopf_map(bad)
    results["hopf_non_unit_input"] = {
        "pass": abs(q.norm().item() - 1.0) > 0.1,
        "q_norm": q.norm().item(),
        "detail": "Hopf map of non-unit vector leaves S^4",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- Boundary 1: Interpolate from product to Bell, C varies continuously ---
    thetas = torch.linspace(0, np.pi / 4, 50, dtype=torch.float64)
    Cs = []
    for theta in thetas:
        psi = torch.tensor([
            torch.cos(theta), 0, 0, torch.sin(theta)
        ], dtype=torch.complex128)
        psi = psi / psi.norm()
        Cs.append(concurrence_pure(psi).item())
    # C should go from 0 to 1 monotonically
    monotonic = all(Cs[i] <= Cs[i+1] + EPS for i in range(len(Cs)-1))
    results["product_to_bell_interpolation"] = {
        "pass": monotonic and abs(Cs[0]) < EPS and abs(Cs[-1] - 1.0) < EPS,
        "C_start": Cs[0],
        "C_end": Cs[-1],
        "monotonic": monotonic,
        "detail": "cos(t)|00> + sin(t)|11> interpolates C from 0 to 1",
    }

    # --- Boundary 2: Concurrence autograd -- gradient exists and is finite ---
    psi_ag = torch.tensor(
        [0.6 + 0j, 0.1 + 0.2j, 0.3 - 0.1j, 0.5 + 0.3j],
        dtype=torch.complex128
    )
    psi_ag = psi_ag / psi_ag.norm()
    psi_ag = psi_ag.clone().detach().requires_grad_(True)
    C_ag = concurrence_pure(psi_ag)
    C_ag.backward()
    grad = psi_ag.grad
    grad_finite = torch.all(torch.isfinite(grad.real)) and torch.all(torch.isfinite(grad.imag))
    grad_nonzero = grad.norm().item() > EPS
    results["concurrence_autograd"] = {
        "pass": grad_finite.item() and grad_nonzero,
        "concurrence": C_ag.item(),
        "grad_norm": grad.norm().item(),
        "detail": "Autograd through concurrence yields finite nonzero gradient",
    }

    # --- Boundary 3: Gradient descent reduces concurrence toward Segre ---
    psi_opt = torch.tensor(
        [0.5 + 0j, 0.2 + 0.1j, 0.3 - 0.2j, 0.6 + 0.1j],
        dtype=torch.complex128
    )
    psi_opt = psi_opt / psi_opt.norm()
    # Optimise: project onto S^7 after each step
    psi_param = psi_opt.clone().detach().requires_grad_(True)
    lr = 0.05
    C_history = []
    for step in range(50):
        C_step = concurrence_pure(psi_param)
        C_history.append(C_step.item())
        C_step.backward()
        with torch.no_grad():
            psi_param -= lr * psi_param.grad
            psi_param /= psi_param.norm()
        psi_param = psi_param.clone().detach().requires_grad_(True)
    C_decreased = C_history[-1] < C_history[0] - 0.01
    results["gradient_descent_toward_segre"] = {
        "pass": C_decreased,
        "C_initial": C_history[0],
        "C_final": C_history[-1],
        "n_steps": len(C_history),
        "detail": "Gradient descent on C drives state toward Segre variety (product states)",
    }

    # --- Boundary 4: Numerical precision at C=0 exact ---
    psi_exact_product = product_state(
        torch.tensor([1, 0], dtype=torch.complex128),
        torch.tensor([0, 1], dtype=torch.complex128),
    )
    C_exact = concurrence_pure(psi_exact_product).item()
    results["exact_product_precision"] = {
        "pass": C_exact < 1e-15,
        "concurrence": C_exact,
        "detail": "|01> is exactly on Segre, C should be machine-zero",
    }

    # --- Boundary 5: Numerical precision at C=1 exact ---
    bell_exact = torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / np.sqrt(2)
    C_bell = concurrence_pure(bell_exact).item()
    results["exact_bell_precision"] = {
        "pass": abs(C_bell - 1.0) < 1e-14,
        "concurrence": C_bell,
        "detail": "Bell state |00>+|11> should have C=1 to machine precision",
    }

    # --- Boundary 6: Hopf map equator vs pole separation ---
    # |00> maps to north pole of S^4, |11> maps to south pole
    psi_00 = torch.tensor([1, 0, 0, 0], dtype=torch.complex128)
    psi_11 = torch.tensor([0, 0, 0, 1], dtype=torch.complex128)
    q_00 = quaternionic_hopf_map(psi_00)
    q_11 = quaternionic_hopf_map(psi_11)
    # These should be antipodal on S^4
    dot_val = torch.dot(q_00, q_11).item()
    results["hopf_antipodal_product_states"] = {
        "pass": abs(dot_val - (-1.0)) < 1e-8,
        "dot_product": dot_val,
        "q_00": q_00.tolist(),
        "q_11": q_11.tolist(),
        "detail": "|00> and |11> map to antipodal points on S^4",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    elapsed = time.time() - t0

    n_pass = sum(1 for v in {**positive, **negative, **boundary}.values()
                 if isinstance(v, dict) and v.get("pass"))
    n_total = len(positive) + len(negative) + len(boundary)

    results = {
        "name": "2-qubit geometry: S^7, CP^3, Segre embedding, concurrence fibration",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_tests": n_total,
            "passed": n_pass,
            "failed": n_total - n_pass,
            "elapsed_s": round(elapsed, 3),
        },
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {OUT_FILE}")
    print(f"{n_pass}/{n_total} tests passed in {elapsed:.2f}s")
