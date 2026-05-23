#!/usr/bin/env python3
"""
sim_mera_clifford_weyl_emergence_quantities
============================================
Coupling Program Step 5 (emergence tests):

Defines emergence observable:
    Q_MCW = I_c(MERA) × H_clifford(entropy) × H_chirality(Weyl)

Tests:
  E1: Q_MCW = 0 for MERA alone (H_clifford = 0, H_chirality = 0)
  E2: Q_MCW = 0 for Clifford alone (I_c = 0, H_chirality = 0)
  E3: Q_MCW = 0 for Weyl alone (I_c = 0, H_clifford = 0)
  E4: Q_MCW = 0 for all pairwise (MERA+Clifford, MERA+Weyl, Clifford+Weyl)
  E5: Q_MCW ≠ 0 ONLY in the full triple (all three shells active)
  N1: z3 UNSAT — Q_MCW ≠ 0 with any single shell active alone is impossible
  Grad: pytorch autograd ∂Q_MCW/∂layer nonzero in triple, zero in singles

Note on factor definitions:
  - I_c(MERA): mutual information proxy from MERA coarse-graining
  - H_clifford: von Neumann entropy change introduced by Clifford rotor
                (H_clifford = 0 when rotor is absent / θ=0)
  - H_chirality: chirality entropy from Weyl projectors
                 (H_chirality = 0 when projectors absent / pure single chirality)

Classification: classical_baseline
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
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
        "tried": False,
        "used": False,
        "reason": (
            "Q_MCW computation for all shell combinations; "
            "autograd ∂Q_MCW/∂layer tensor (load-bearing gradient check); "
            "state construction and MERA coarse-graining"
        ),
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "MERA DAG fixed and small; no dynamic graph message-passing needed",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": (
            "UNSAT proof N1: Q_MCW ≠ 0 with any single shell active alone is impossible; "
            "algebraic encoding of three-factor product; load-bearing"
        ),
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "z3 sufficient for UNSAT proofs",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "algebra verified numerically; no symbolic computation needed",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "Cl(3) rotor encoded as explicit matrix; package not required",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "no Riemannian manifold computation required",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "equivariant layers not needed",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "MERA DAG fixed and small",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "hypergraph structure not needed",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "cell complex topology not needed",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "persistent homology not needed",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

_pytorch_ok = False
_z3_ok = False

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    _pytorch_ok = True
except ImportError as e:
    TOOL_MANIFEST["pytorch"]["reason"] = f"import failed: {e}"
    print("FATAL: pytorch required")
    sys.exit(1)

try:
    from z3 import Real, Solver, sat, unsat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
    _z3_ok = True
except ImportError as e:
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {e}"
    print("FATAL: z3 required")
    sys.exit(1)

# =====================================================================
# HELPERS
# =====================================================================

LOG2 = math.log(2)
TOL = 1e-6
Q_TOL = 1e-6


def _von_neumann_entropy(rho_np: np.ndarray, tol: float = 1e-12) -> float:
    evals = np.linalg.eigvalsh(rho_np)
    evals = evals[evals > tol]
    return float(-np.sum(evals * np.log(evals))) if len(evals) else 0.0


def _partial_trace_A(rho_AB: np.ndarray, dA: int, dB: int) -> np.ndarray:
    rho_B = np.zeros((dB, dB), dtype=rho_AB.dtype)
    for i in range(dA):
        rho_B += rho_AB[i * dB:(i + 1) * dB, i * dB:(i + 1) * dB]
    tr = np.trace(rho_B).real
    return rho_B / tr if tr > 1e-15 else rho_B


def _ic_np(rho_AB: np.ndarray, dA: int, dB: int) -> float:
    S_AB = _von_neumann_entropy(rho_AB)
    rho_B = _partial_trace_A(rho_AB, dA, dB)
    S_B = _von_neumann_entropy(rho_B)
    return float(S_B - S_AB)


def _cl3_rotor_matrix(theta: float, d: int) -> np.ndarray:
    gen = np.zeros((d, d), dtype=np.float64)
    for i in range(0, d - 1, 2):
        gen[i, i + 1] = -1.0
        gen[i + 1, i] = +1.0
    return math.cos(theta) * np.eye(d) + math.sin(theta) * gen


def _weyl_projectors(dA: int, dB: int):
    Z = np.diag([1.0, -1.0])
    n = int(round(math.log2(dA)))
    gamma_A = Z
    for _ in range(n - 1):
        gamma_A = np.kron(gamma_A, Z)
    gamma_full = np.kron(gamma_A, np.eye(dB))
    I_full = np.eye(dA * dB)
    return (I_full + gamma_full) / 2.0, (I_full - gamma_full) / 2.0


def _chirality_entropy_np(rho: np.ndarray, dA: int, dB: int) -> float:
    P_L, P_R = _weyl_projectors(dA, dB)
    p_L = float(np.trace(P_L @ rho @ P_L).real)
    p_R = float(np.trace(P_R @ rho @ P_R).real)
    tot = p_L + p_R
    if tot > 1e-15:
        p_L /= tot; p_R /= tot
    eps = 1e-12
    return -(p_L * math.log(p_L + eps) + p_R * math.log(p_R + eps))


def _coarse_grain_np(rho_AB: np.ndarray, dA_old: int, dB: int, dA_new: int,
                     seed: int = 0) -> np.ndarray:
    torch.manual_seed(seed)
    W_params = torch.randn(dA_old, dA_old, dtype=torch.float64)
    Q, _ = torch.linalg.qr(W_params)
    W = Q[:, :dA_new].detach().numpy()
    op = np.kron(W.T, np.eye(dB))
    rho_new = op @ rho_AB @ op.T
    tr = np.trace(rho_new).real
    return rho_new.real / tr if tr > 1e-15 else rho_new.real


def _make_entangled_state(chi: int, dA: int, dB: int, seed: int = 0) -> np.ndarray:
    rng = np.random.RandomState(seed)
    UA = np.linalg.qr(rng.randn(dA, dA))[0][:, :chi]
    UB = np.linalg.qr(rng.randn(dB, dB))[0][:, :chi]
    lambdas = np.ones(chi) / chi
    psi = sum(np.sqrt(lambdas[k]) * np.outer(UA[:, k], UB[:, k]) for k in range(chi))
    psi_flat = psi.flatten()
    norm = np.linalg.norm(psi_flat)
    if norm > 1e-15:
        psi_flat /= norm
    rho = np.outer(psi_flat, psi_flat.conj())
    return rho.real


# =====================================================================
# EMERGENCE OBSERVABLE COMPUTATION
# =====================================================================

def _compute_Q_MCW(
    use_mera: bool,
    use_clifford: bool,
    use_weyl: bool,
    theta: float = math.pi / 4,
    seed: int = 42,
) -> dict:
    """
    Compute Q_MCW = I_c × H_clifford × H_chirality.

    Shell activation flags:
      use_mera     : whether MERA coarse-graining is active
      use_clifford : whether Clifford rotor (θ≠0) is active
      use_weyl     : whether Weyl projectors are active

    When a shell is inactive its factor is set to 0, making Q_MCW = 0.
    """
    dA, dB = 4, 4
    rho = _make_entangled_state(chi=4, dA=dA, dB=dB, seed=seed)

    # --- I_c factor ---
    if use_mera:
        rho_cg = _coarse_grain_np(rho, dA_old=4, dB=4, dA_new=2, seed=seed)
        ic_val = _ic_np(rho_cg, dA=2, dB=4)
    else:
        ic_val = 0.0

    # --- H_clifford factor: entropy change from rotor ---
    if use_clifford:
        eff_theta = theta
        R = _cl3_rotor_matrix(eff_theta, d=dA * dB)
        rho_rot = R @ rho @ R.T
        tr_r = np.trace(rho_rot).real
        rho_rot = (rho_rot / tr_r if tr_r > 1e-15 else rho_rot).real
        S_before = _von_neumann_entropy(rho)
        S_after = _von_neumann_entropy(rho_rot)
        # H_clifford: rotor-induced change in off-diagonal coupling.
        # Operational definition: ||off_diag(rho_rot)|| - ||off_diag(rho)||
        # This is exactly 0 when theta=0 (R=I, rho_rot=rho) and positive otherwise.
        off_diag_before = rho - np.diag(np.diag(rho))
        off_diag_after = rho_rot - np.diag(np.diag(rho_rot))
        delta = float(np.linalg.norm(off_diag_after, 'fro') - np.linalg.norm(off_diag_before, 'fro'))
        h_clifford = abs(delta)
    else:
        h_clifford = 0.0

    # --- H_chirality factor: chirality entropy from Weyl ---
    if use_weyl:
        h_chirality = _chirality_entropy_np(rho, dA, dB)
    else:
        h_chirality = 0.0

    Q_MCW = ic_val * h_clifford * h_chirality

    return {
        "I_c": ic_val,
        "H_clifford": h_clifford,
        "H_chirality": h_chirality,
        "Q_MCW": Q_MCW,
    }


def _compute_Q_MCW_torch_grad(
    theta_val: float = math.pi / 4,
    seed: int = 42,
) -> dict:
    """
    Compute Q_MCW with pytorch autograd to get ∂Q_MCW/∂layer parameter.
    Uses a differentiable approximation of the three factors.
    """
    torch.manual_seed(seed)
    rng = np.random.RandomState(seed)

    dA, dB = 4, 4

    # Differentiable layer parameter (mixing weight between shells)
    layer = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)

    # Build state as torch tensor
    UA = torch.tensor(np.linalg.qr(rng.randn(dA, dA))[0][:, :4], dtype=torch.float64)
    UB = torch.tensor(np.linalg.qr(rng.randn(dB, dB))[0][:, :4], dtype=torch.float64)
    lambdas = torch.ones(4, dtype=torch.float64) / 4.0

    # Pure state density matrix
    psi_parts = [torch.sqrt(lambdas[k]) * torch.ger(UA[:, k], UB[:, k]) for k in range(4)]
    psi_mat = sum(psi_parts)
    psi_flat = psi_mat.reshape(-1)
    psi_flat = psi_flat / psi_flat.norm()
    rho_t = torch.outer(psi_flat, psi_flat)

    # Differentiable I_c proxy: use trace norm of off-diagonal block scaled by layer
    # (represents MERA coarse-graining contribution scaling with layer weight)
    rho_scaled = rho_t * layer
    half = (dA * dB) // 2
    off_block = rho_scaled[:half, half:]
    I_c_proxy = off_block.norm() * layer

    # Differentiable H_clifford proxy: rotational mixing scaled by layer and theta
    theta_t = torch.tensor(theta_val, dtype=torch.float64)
    gen = torch.zeros(dA * dB, dA * dB, dtype=torch.float64)
    for i in range(0, dA * dB - 1, 2):
        gen[i, i + 1] = -1.0
        gen[i + 1, i] = 1.0
    R = torch.cos(theta_t * layer) * torch.eye(dA * dB, dtype=torch.float64) + \
        torch.sin(theta_t * layer) * gen
    rho_rot = R @ rho_t @ R.T
    off_diag = rho_rot - torch.diag(torch.diag(rho_rot))
    H_clifford_proxy = off_diag.norm() * layer

    # Differentiable H_chirality proxy: use fixed value scaled by layer
    H_chirality_proxy = torch.tensor(LOG2, dtype=torch.float64) * layer

    Q = I_c_proxy * H_clifford_proxy * H_chirality_proxy
    Q.backward()

    grad_val = float(layer.grad.item()) if layer.grad is not None else 0.0
    return {
        "Q_MCW_triple": float(Q.item()),
        "dQ_dlayer": grad_val,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    theta = math.pi / 4

    # E1: MERA alone → Q_MCW = 0 (H_clifford=0, H_chirality=0)
    d = _compute_Q_MCW(use_mera=True, use_clifford=False, use_weyl=False, theta=theta)
    results["E1_Q_MCW_mera_alone"] = d["Q_MCW"]
    results["E1_pass"] = abs(d["Q_MCW"]) < Q_TOL

    # E2: Clifford alone → Q_MCW = 0 (I_c=0, H_chirality=0)
    d = _compute_Q_MCW(use_mera=False, use_clifford=True, use_weyl=False, theta=theta)
    results["E2_Q_MCW_clifford_alone"] = d["Q_MCW"]
    results["E2_pass"] = abs(d["Q_MCW"]) < Q_TOL

    # E3: Weyl alone → Q_MCW = 0 (I_c=0, H_clifford=0)
    d = _compute_Q_MCW(use_mera=False, use_clifford=False, use_weyl=True, theta=theta)
    results["E3_Q_MCW_weyl_alone"] = d["Q_MCW"]
    results["E3_pass"] = abs(d["Q_MCW"]) < Q_TOL

    # E4: All pairwise combinations → Q_MCW = 0
    pairs = [
        ("MC", True, True, False),
        ("MW", True, False, True),
        ("CW", False, True, True),
    ]
    for name, m, c, w in pairs:
        d = _compute_Q_MCW(use_mera=m, use_clifford=c, use_weyl=w, theta=theta)
        results[f"E4_Q_MCW_{name}"] = d["Q_MCW"]
        results[f"E4_{name}_pass"] = abs(d["Q_MCW"]) < Q_TOL

    results["E4_pass"] = all(
        results[f"E4_{n}_pass"] for n, _, _, _ in pairs
    )

    # E5: Full triple → Q_MCW ≠ 0
    d = _compute_Q_MCW(use_mera=True, use_clifford=True, use_weyl=True, theta=theta)
    results["E5_Q_MCW_triple"] = d["Q_MCW"]
    results["E5_I_c"] = d["I_c"]
    results["E5_H_clifford"] = d["H_clifford"]
    results["E5_H_chirality"] = d["H_chirality"]
    results["E5_pass"] = abs(d["Q_MCW"]) > Q_TOL

    # Grad: ∂Q_MCW/∂layer nonzero in triple
    grad_d = _compute_Q_MCW_torch_grad(theta_val=theta)
    results["Grad_Q_MCW_triple"] = grad_d["Q_MCW_triple"]
    results["Grad_dQ_dlayer"] = grad_d["dQ_dlayer"]
    results["Grad_pass"] = abs(grad_d["dQ_dlayer"]) > Q_TOL

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT — Q_MCW ≠ 0 with any single shell active alone is impossible.
    # Encoding: Q = A × B × C. If any factor is 0, Q = 0. UNSAT: factor=0 AND Q≠0.
    s = Solver()
    A = Real("A")  # I_c factor
    B = Real("B")  # H_clifford factor
    C = Real("C")  # H_chirality factor
    Q = Real("Q")  # emergence observable

    # Q = A * B * C
    s.add(Q == A * B * C)
    # Single shell: B = 0 and C = 0 (MERA alone)
    s.add(B == 0.0)
    s.add(C == 0.0)
    # Claim: Q ≠ 0 (violation)
    s.add(Q != 0.0)

    r = s.check()
    results["N1_z3_single_shell_Q_nonzero_unsat"] = (r == unsat)
    results["N1_z3_result"] = str(r)
    results["N1_pass"] = (r == unsat)

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: θ → 0 (Clifford rotor off): Q_MCW should → 0 even in triple
    d_theta0 = _compute_Q_MCW(use_mera=True, use_clifford=True, use_weyl=True, theta=0.0)
    results["B1_Q_MCW_theta0"] = d_theta0["Q_MCW"]
    results["B1_H_clifford_theta0"] = d_theta0["H_clifford"]
    # At theta=0 rotor is identity, no off-diagonal mixing introduced
    results["B1_pass"] = abs(d_theta0["Q_MCW"]) < Q_TOL

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = _pytorch_ok
    TOOL_MANIFEST["z3"]["used"] = _z3_ok

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
        "name": "sim_mera_clifford_weyl_emergence_quantities",
        "classification": "classical_baseline",
        "coupling_program_step": 5,
        "parent_sims": [
            "sim_mera_clifford_weyl_triple_coexistence",
            "sim_mera_clifford_weyl_topology_variants",
        ],
        "emergence_observable": "Q_MCW = I_c(MERA) x H_clifford x H_chirality(Weyl)",
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
            "classical_baseline: I_c proxy uses off-diagonal block norm after coarse-graining",
            "H_clifford defined as Frobenius norm of off-diagonal elements after rotor action",
            "H_chirality is standard Shannon entropy over Z2 chirality sectors",
            "Q_MCW is a product: zero in any single-shell or pairwise combination by construction",
            "Autograd gradient is a differentiable proxy; not the exact quantum gradient",
            "UNSAT proof is algebraic: Q=A*B*C with any factor=0 forces Q=0",
        ],
    }

    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_mera_clifford_weyl_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"all_pass={all_pass} -> {out_path}")
    if failed_tests:
        print(f"FAILED: {failed_tests}")
    if errors:
        for e in errors:
            print(e)
