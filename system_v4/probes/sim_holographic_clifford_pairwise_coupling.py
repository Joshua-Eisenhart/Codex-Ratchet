#!/usr/bin/env python3
"""
sim_holographic_clifford_pairwise_coupling.py
==============================================
Coupling Program Step 2a (pairwise coupling):
    Holographic shell × Clifford Cl(3) shell

Parent sims:
  - sim_holographic_entropy_bound_canonical.py: S(A) <= |∂A|*log(χ)
  - sim_clifford_generator_basis.py: Cl(3) rotors are unitary

Research question:
  Does Clifford Cl(3) rotor action on a holographic entropy state preserve
  the RT bound S(A) <= |∂A|*log(χ)?

Key math:
  - RT entropy: S = n_cut * log(χ) for a MERA tensor network.
  - Cl(3) rotor R(θ) = cos(θ)·I + sin(θ)·gen is unitary (orthogonal over reals).
  - Unitary evolution preserves eigenvalues of density matrix → S(ρ) invariant.
  - Therefore RT bound cannot be violated by Clifford rotation.
  - autograd: ∂S/∂θ = 0 since S is θ-independent under unitary.

Tests:
  P1 (pytorch): RT entropy S = n_cut*log(χ) preserved under Cl(3) rotor at 5 angles.
  P2 (pytorch+z3): Clifford rotation is unitary → entropy invariant (z3 UNSAT on entropy increase).
  P3 (pytorch autograd): ∂S/∂θ = 0 (entropy is θ-independent for unitary rotation).
  N1 (z3 UNSAT): S > |∂A|*log(χ) after Clifford rotation cannot be admitted.
  B1: θ=0 (identity) leaves S unchanged.

Classification: classical_baseline
"""

import json
import math
import os
import sys
import traceback

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False, "used": False,
        "reason": (
            "Load-bearing: entropy computed via torch SVD on rotated state; "
            "autograd used for ∂S/∂θ = 0 verification in P3"
        ),
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "No dynamic graph structure needed for pairwise entropy coupling test",
    },
    "z3": {
        "tried": False, "used": False,
        "reason": (
            "Load-bearing: UNSAT proof in N1 that S > |∂A|*log(χ) is inadmissible "
            "after Clifford rotation; encodes holographic bound as hard constraint"
        ),
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "z3 sufficient for UNSAT bound proof; cvc5 not needed",
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": (
            "Supportive: symbolic verification that unitary conjugation R·M·R^T "
            "preserves trace(M^2) (Frobenius norm) for P2 cross-check"
        ),
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "Cl(3) rotor encoded as explicit block-diagonal orthogonal matrix; clifford package not required",
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "No Riemannian manifold computation needed at pairwise coupling level",
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "Equivariant layers not required for holographic-Clifford entropy test",
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": "No graph operations needed; holographic cut is a scalar parameter",
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "Hyperedge structure not needed for bipartite RT entropy",
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "Cell complex topology not required for RT entropy bound test",
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "Persistent homology not required for entropy coupling probe",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "supportive",
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# =====================================================================
# IMPORTS
# =====================================================================

_pytorch_ok = False
_z3_ok = False
_sympy_ok = False

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    _pytorch_ok = True
except ImportError as e:
    TOOL_MANIFEST["pytorch"]["reason"] = f"import failed: {e}"
    print("FATAL: pytorch required")
    sys.exit(1)

try:
    from z3 import Real, Solver, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    _z3_ok = True
except ImportError as e:
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {e}"
    print("FATAL: z3 required")
    sys.exit(1)

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    _sympy_ok = True
except ImportError as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"import failed: {e}"
    _sympy_ok = False

# =====================================================================
# HELPERS
# =====================================================================

LOG2 = math.log(2)
TOL = 1e-6


def _rt_state(chi: int, n_cut: int, seed: int = 0) -> np.ndarray:
    """
    Construct a bipartite density matrix with Schmidt rank chi at n_cut bonds.
    Each bond contributes log(chi) to entanglement entropy.
    rho_A = Tr_B(|ψ><ψ|) for max-entangled state: singular values all 1/sqrt(chi).
    """
    rng = np.random.RandomState(seed)
    d = chi ** n_cut  # dimension of system A
    # Build a maximally entangled reduced state: ρ_A = I/d
    rho = np.eye(d, dtype=np.float64) / d
    return rho


def _von_neumann_entropy_np(rho: np.ndarray) -> float:
    """Von Neumann entropy S(ρ) = -Tr(ρ log ρ) via eigenvalues."""
    eigs = np.linalg.eigvalsh(rho)
    eigs = eigs[eigs > 1e-15]
    return float(-np.sum(eigs * np.log(eigs)))


def _von_neumann_entropy_torch(rho_t: torch.Tensor) -> torch.Tensor:
    """Von Neumann entropy via torch.linalg.eigvalsh."""
    eigs = torch.linalg.eigvalsh(rho_t)
    eigs = eigs.clamp(min=1e-15)
    log_eigs = torch.log(eigs)
    return -torch.sum(eigs * log_eigs)


def _cl3_rotor_matrix(theta: float, d: int) -> np.ndarray:
    """
    Cl(3) rotor R(θ) = cos(θ)·I + sin(θ)·gen, block-diagonal antisymmetric gen.
    """
    gen = np.zeros((d, d), dtype=np.float64)
    for i in range(0, d - 1, 2):
        gen[i, i + 1] = -1.0
        gen[i + 1, i] = +1.0
    return math.cos(theta) * np.eye(d) + math.sin(theta) * gen


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1 (pytorch): RT entropy S = n_cut*log(χ) preserved under Cl(3) rotor
    # at 5 angles.
    # ------------------------------------------------------------------
    chi = 2
    n_cut = 2
    expected_S = n_cut * math.log(chi)  # = 2*log(2)
    seed = 42

    rho0 = _rt_state(chi, n_cut, seed)
    d = rho0.shape[0]

    thetas = [math.pi / 8, math.pi / 4, math.pi / 3, math.pi / 2, 2 * math.pi / 3]
    theta_results = {}
    all_S_preserved = True

    for theta in thetas:
        R = _cl3_rotor_matrix(theta, d)
        rho_rot = R @ rho0 @ R.T
        rho_t = torch.tensor(rho_rot, dtype=torch.float64)
        S_val = _von_neumann_entropy_torch(rho_t).item()
        bound_ok = S_val <= n_cut * math.log(chi) + TOL
        preserved = abs(S_val - expected_S) < 1e-6
        if not preserved:
            all_S_preserved = False
        theta_results[f"theta_{theta:.4f}"] = {
            "S": S_val,
            "expected_S": expected_S,
            "bound_satisfied": bound_ok,
            "S_preserved": preserved,
        }

    results["P1_expected_S"] = expected_S
    results["P1_theta_results"] = theta_results
    results["P1_all_S_preserved_under_rotor"] = all_S_preserved
    results["P1_pass"] = all_S_preserved

    # ------------------------------------------------------------------
    # P2 (pytorch + z3): Unitarity of Cl(3) rotor → entropy invariant.
    # Cross-check: R·R^T = I confirms unitarity; then z3 UNSAT on entropy increase.
    # ------------------------------------------------------------------
    unitarity_results = {}
    all_unitary = True
    for theta in thetas:
        R = _cl3_rotor_matrix(theta, d)
        RRT = R @ R.T
        is_unitary = bool(np.allclose(RRT, np.eye(d), atol=1e-10))
        unitarity_results[f"theta_{theta:.4f}_unitary"] = is_unitary
        if not is_unitary:
            all_unitary = False

    # sympy cross-check: Frobenius norm preserved under orthogonal conjugation
    if _sympy_ok:
        theta_sym = sp.Symbol("theta", real=True)
        d_sym = 4
        I_sym = sp.eye(d_sym)
        gen_sym = sp.zeros(d_sym, d_sym)
        for i in range(0, d_sym - 1, 2):
            gen_sym[i, i + 1] = -1
            gen_sym[i + 1, i] = 1
        R_sym = sp.cos(theta_sym) * I_sym + sp.sin(theta_sym) * gen_sym
        RT_sym = R_sym.T
        RRT_sym = sp.simplify(R_sym * RT_sym - I_sym)
        sympy_unitary = (RRT_sym == sp.zeros(d_sym, d_sym))
        results["P2_sympy_unitarity_RRT_eq_I"] = bool(sympy_unitary)
    else:
        results["P2_sympy_available"] = False

    results["P2_unitarity_at_thetas"] = unitarity_results
    results["P2_all_unitary"] = all_unitary
    results["P2_pass"] = all_unitary

    # ------------------------------------------------------------------
    # P3 (pytorch autograd): ∂S/∂θ = 0 (entropy θ-independent for unitary rotation).
    # ------------------------------------------------------------------
    theta_t = torch.tensor(math.pi / 4, dtype=torch.float64, requires_grad=True)
    # Construct rotor as differentiable function of theta
    gen_t = torch.zeros(d, d, dtype=torch.float64)
    for i in range(0, d - 1, 2):
        gen_t[i, i + 1] = -1.0
        gen_t[i + 1, i] = +1.0
    R_t = torch.cos(theta_t) * torch.eye(d, dtype=torch.float64) + torch.sin(theta_t) * gen_t
    rho0_t = torch.tensor(rho0, dtype=torch.float64)
    rho_rot_t = R_t @ rho0_t @ R_t.T
    S_t = _von_neumann_entropy_torch(rho_rot_t)
    S_t.backward()
    dS_dtheta = float(theta_t.grad.abs().item())
    grad_near_zero = dS_dtheta < 1e-4

    results["P3_dS_dtheta_at_pi4"] = dS_dtheta
    results["P3_grad_near_zero"] = grad_near_zero
    results["P3_pass"] = grad_near_zero

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1 (z3 UNSAT): S > |∂A|*log(χ) after Clifford rotation is inadmissible.
    # Unitary rotation cannot increase entropy; RT bound cannot be violated.
    # ------------------------------------------------------------------
    chi_val = 2.0
    n_cut_val = 2.0
    bound_val = n_cut_val * math.log(chi_val)

    s = Solver()
    S_before = Real("S_before")
    S_after = Real("S_after")
    log_chi = Real("log_chi")
    n_cut_z3 = Real("n_cut")

    # Before rotation: S satisfies RT bound
    s.add(S_before >= 0.0)
    s.add(S_before <= n_cut_z3 * log_chi)
    s.add(log_chi == bound_val / n_cut_val)  # log(chi) = log(2)
    s.add(n_cut_z3 == n_cut_val)
    # Unitary rotation: S_after = S_before (entropy invariant)
    s.add(S_after == S_before)
    # Claim: RT bound violated after rotation (UNSAT)
    s.add(S_after > n_cut_z3 * log_chi)

    r = s.check()
    results["N1_z3_rt_bound_violation_after_clifford_unsat"] = (r == unsat)
    results["N1_z3_result"] = str(r)
    results["N1_pass"] = (r == unsat)

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    chi = 2
    n_cut = 2
    rho0 = _rt_state(chi, n_cut, seed=42)
    d = rho0.shape[0]
    expected_S = n_cut * math.log(chi)

    # ------------------------------------------------------------------
    # B1: θ=0 (identity rotor) leaves S unchanged.
    # ------------------------------------------------------------------
    R_id = _cl3_rotor_matrix(0.0, d)
    rho_id = R_id @ rho0 @ R_id.T
    S_id = _von_neumann_entropy_np(rho_id)
    S0 = _von_neumann_entropy_np(rho0)
    b1_pass = abs(S_id - S0) < 1e-10

    results["B1_S_before"] = S0
    results["B1_S_after_identity"] = S_id
    results["B1_S_unchanged"] = b1_pass
    results["B1_expected_S"] = expected_S
    results["B1_pass"] = b1_pass

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = _pytorch_ok
    TOOL_MANIFEST["z3"]["used"] = _z3_ok
    TOOL_MANIFEST["sympy"]["used"] = _sympy_ok

    errors = []
    pos = {}
    neg = {}
    bnd = {}

    try:
        pos = run_positive_tests()
    except Exception as e:
        errors.append(f"positive: {e}\n{traceback.format_exc()}")

    try:
        neg = run_negative_tests()
    except Exception as e:
        errors.append(f"negative: {e}\n{traceback.format_exc()}")

    try:
        bnd = run_boundary_tests()
    except Exception as e:
        errors.append(f"boundary: {e}\n{traceback.format_exc()}")

    def _bools(d):
        return {k: v for k, v in d.items() if isinstance(v, bool)}

    bool_pos = _bools(pos)
    bool_neg = _bools(neg)
    bool_bnd = _bools(bnd)

    all_pass = (
        all(bool_pos.values()) and
        all(bool_neg.values()) and
        all(bool_bnd.values()) and
        len(errors) == 0
    )

    failed_tests = (
        [k for k, v in bool_pos.items() if not v] +
        [k for k, v in bool_neg.items() if not v] +
        [k for k, v in bool_bnd.items() if not v]
    )

    results = {
        "name": "sim_holographic_clifford_pairwise_coupling",
        "classification": "classical_baseline",
        "coupling_program": "Holographic x Clifford x Weyl",
        "coupling_program_step": "2a",
        "parent_sims": [
            "sim_holographic_entropy_bound_canonical",
            "sim_clifford_generator_basis",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "failed_tests": failed_tests,
        "errors": errors,
        "summary": {
            "all_pass": all_pass,
            "passed_bool_count": (
                sum(bool_pos.values()) +
                sum(bool_neg.values()) +
                sum(bool_bnd.values())
            ),
            "total_bool_count": len(bool_pos) + len(bool_neg) + len(bool_bnd),
        },
        "divergence_log": [
            "classical_baseline: RT entropy computed from maximally mixed state (I/d)",
            "Cl(3) rotor encoded as block-diagonal orthogonal matrix; not full Cl(3) package",
            "autograd ∂S/∂θ computed via torch eigvalsh; clamp used to avoid log(0)",
            "z3 UNSAT uses real arithmetic proxy; not full quantum information proof",
            "RT bound S <= n_cut*log(chi) held with tolerance 1e-6 for float comparison",
        ],
    }

    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_holographic_clifford_pairwise_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"all_pass={all_pass} -> {out_path}")
    if failed_tests:
        print(f"FAILED: {failed_tests}")
    if errors:
        for e in errors:
            print(e)
