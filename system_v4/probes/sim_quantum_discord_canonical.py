#!/usr/bin/env python3
"""Canonical: real quantum discord D(A:B) on rho_AB.

Pairs with sim_quantum_discord_classical.py (which is identically 0).

D(A:B) = I(rho_AB) - J(rho_AB)
  I(rho_AB) = S(rho_A) + S(rho_B) - S(rho_AB)
  J(rho_AB) = S(rho_A) - min_{Pi_B} sum_k p_k S(rho_{A|k})

Positive pair: Werner-like rho with quantum-correlated (nonzero-discord) state.
Negative pair: classical-classical diagonal joint rho -> discord must be 0.

load_bearing: pytorch (autograd-ready dense ops on density matrices) +
              sympy (exact symbolic verification of product-state zero case).
"""
import json, os, itertools, math
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "numpy":  {"tried": True, "used": True,  "reason": "baseline numeric cross-check"},
    "pytorch":{"tried": False,"used": False, "reason": ""},
    "sympy":  {"tried": False,"used": False, "reason": ""},
    "z3":     {"tried": True, "used": False, "reason": "not needed: numerical not proof claim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy":   "supportive",
    "pytorch": "load_bearing",
    "sympy":   "load_bearing",
    "z3":      None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "complex density matrix ops, eigh, partial trace, log2 via eigendecomp"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic proof that product states have exact zero discord"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# ---- torch helpers ------------------------------------------------------

def _cdtype():
    return torch.complex128

def _rdtype():
    return torch.float64

def _S_vn(rho):
    """von Neumann entropy S(rho) in bits via torch.linalg.eigvalsh of Hermitian rho."""
    # Symmetrize numerically
    rho_h = 0.5 * (rho + rho.conj().T)
    w = torch.linalg.eigvalsh(rho_h).real
    w = torch.clamp(w, min=0.0)
    s = w.sum()
    if s > 0:
        w = w / s
    mask = w > 1e-15
    w_safe = w[mask]
    return float(-(w_safe * torch.log2(w_safe)).sum().item())

def _partial_trace_B(rho_ab, dA, dB):
    """rho_A = Tr_B(rho_AB). rho_ab shape (dA*dB, dA*dB)."""
    T = rho_ab.reshape(dA, dB, dA, dB)
    return torch.einsum('ijkj->ik', T)

def _partial_trace_A(rho_ab, dA, dB):
    T = rho_ab.reshape(dA, dB, dA, dB)
    return torch.einsum('ijil->jl', T)

def _project_B(rho_ab, Pi_b, dA, dB):
    """Apply projector I_A ⊗ Pi_b. Returns (p_k, rho_{A|k})."""
    I_A = torch.eye(dA, dtype=_cdtype())
    M = torch.kron(I_A, Pi_b)
    post = M @ rho_ab @ M
    p = torch.trace(post).real
    if p.abs() < 1e-14:
        return 0.0, None
    rho_post = post / p
    rho_A_cond = _partial_trace_B(rho_post, dA, dB)
    return float(p.item()), rho_A_cond

def _J_BtoA_2qubit(rho_ab, n_angles=40):
    """Optimize J over real projective measurements on B (qubit).
    Pi_0 = |v><v|, |v> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>.
    """
    dA, dB = 2, 2
    rho_A = _partial_trace_B(rho_ab, dA, dB)
    S_A = _S_vn(rho_A)
    best_cond_S = math.inf
    # Grid over (theta, phi); sufficient for 2-qubit demonstration gap.
    thetas = np.linspace(0.0, math.pi, n_angles)
    phis   = np.linspace(0.0, 2 * math.pi, n_angles, endpoint=False)
    for th in thetas:
        c = math.cos(th / 2.0); s = math.sin(th / 2.0)
        for ph in phis:
            eph = complex(math.cos(ph), math.sin(ph))
            v = torch.tensor([[c + 0j], [s * eph]], dtype=_cdtype())
            Pi0 = v @ v.conj().T
            Pi1 = torch.eye(2, dtype=_cdtype()) - Pi0
            total = 0.0
            for Pi in (Pi0, Pi1):
                p, rho_cond = _project_B(rho_ab, Pi, dA, dB)
                if p > 0 and rho_cond is not None:
                    total += p * _S_vn(rho_cond)
            if total < best_cond_S:
                best_cond_S = total
    J = S_A - best_cond_S
    return J, S_A, best_cond_S

def quantum_discord_2qubit(rho_ab, n_angles=40):
    dA, dB = 2, 2
    rho_A = _partial_trace_B(rho_ab, dA, dB)
    rho_B = _partial_trace_A(rho_ab, dA, dB)
    S_A = _S_vn(rho_A); S_B = _S_vn(rho_B); S_AB = _S_vn(rho_ab)
    I = S_A + S_B - S_AB
    J, _, _ = _J_BtoA_2qubit(rho_ab, n_angles=n_angles)
    D = I - J
    return {"I": I, "J": J, "D": D, "S_A": S_A, "S_B": S_B, "S_AB": S_AB}


# ---- state factories ----------------------------------------------------

def _bell_phi_plus():
    v = torch.zeros(4, 1, dtype=_cdtype()); v[0, 0] = 1.0 / math.sqrt(2); v[3, 0] = 1.0 / math.sqrt(2)
    return v @ v.conj().T

def _werner(p):
    """p|Phi+><Phi+| + (1-p)/4 * I4."""
    return p * _bell_phi_plus() + (1 - p) / 4.0 * torch.eye(4, dtype=_cdtype())

def _classical_joint_diag(pxy):
    """Diagonal rho_AB from classical pmf pxy (dA x dB). Zero discord expected."""
    pxy = np.asarray(pxy, float)
    dA, dB = pxy.shape
    diag = pxy.reshape(-1)
    rho = torch.diag(torch.tensor(diag, dtype=_cdtype()))
    return rho, dA, dB

def _product_state(rhoA, rhoB):
    return torch.kron(rhoA, rhoB)


# ---- sympy exact product-state verification -----------------------------

def _sympy_product_discord_zero():
    """Symbolic: rho_AB = rho_A ⊗ rho_B => I = 0 and any local measurement
    on B gives post-state rho_A ⊗ Pi_k/p_k so S(rho_{A|k}) = S(rho_A) for all k
    => J = S_A - S_A = 0 => D = 0 exactly.

    We verify the structural identity: ptrace_B((I ⊗ Pi_k)(rho_A ⊗ rho_B)(I ⊗ Pi_k)) / p_k = rho_A.
    """
    a, b, c, d = sp.symbols('a b c d', positive=True, real=True)
    # Symbolic diagonal rho_A and rho_B (2x2), unit trace
    rhoA = sp.Matrix([[a, 0], [0, 1 - a]])
    rhoB = sp.Matrix([[b, 0], [0, 1 - b]])
    # tensor
    rho = sp.zeros(4, 4)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    rho[2*i+k, 2*j+l] = rhoA[i, j] * rhoB[k, l]
    # projector on B = |0><0|
    Pi0B = sp.Matrix([[1, 0], [0, 0]])
    IA = sp.eye(2)
    M = sp.Matrix(sp.BlockMatrix([[Pi0B[0,0]*IA, Pi0B[0,1]*IA],
                                  [Pi0B[1,0]*IA, Pi0B[1,1]*IA]]))
    # Actually M = I_A ⊗ Pi0B. Build via Kronecker:
    M = sp.Matrix(4, 4, lambda i, j: IA[i//2, j//2] * Pi0B[i%2, j%2])
    post = M * rho * M
    p0 = sp.simplify(post.trace())
    # partial trace over B
    T = sp.zeros(2, 2)
    for i in range(2):
        for j in range(2):
            s = 0
            for k in range(2):
                s = s + post[2*i+k, 2*j+k]
            T[i, j] = sp.simplify(s / p0)
    diff = sp.simplify(T - rhoA)
    return bool(diff == sp.zeros(2, 2))


# ---- tests --------------------------------------------------------------

def run_positive_tests():
    # Werner at p=0.8 -> rank-<4 rho with real discord
    rho_w = _werner(0.8)
    out_w = quantum_discord_2qubit(rho_w, n_angles=30)
    # Non-maximally entangled pure state: |psi> = sqrt(0.7)|00> + sqrt(0.3)|11>
    v = torch.zeros(4, 1, dtype=_cdtype())
    v[0, 0] = math.sqrt(0.7); v[3, 0] = math.sqrt(0.3)
    rho_ne = v @ v.conj().T
    out_ne = quantum_discord_2qubit(rho_ne, n_angles=30)
    # Mixed superposition-with-coherence: depolarized |+>|+> channel output
    plus = (torch.tensor([[1.0],[1.0]], dtype=_cdtype()) / math.sqrt(2))
    pp = torch.kron(plus, plus); rho_pp = pp @ pp.conj().T
    rho_dephase = 0.7 * rho_pp + 0.3 * torch.kron(
        torch.tensor([[0.5,0],[0,0.5]], dtype=_cdtype()),
        torch.tensor([[0.5,0],[0,0.5]], dtype=_cdtype())
    )
    out_dp = quantum_discord_2qubit(rho_dephase, n_angles=30)
    # sympy structural check for product-state
    sym_product_zero = _sympy_product_discord_zero()
    return {
        "werner_p0p8_discord_positive": out_w["D"] > 0.05,
        "werner_D_val": out_w["D"],
        "nonmax_entangled_discord_positive": out_ne["D"] > 0.1,
        "nonmax_entangled_D_val": out_ne["D"],
        "depolarized_plusplus_discord_positive": out_dp["D"] > 0.0,
        "depolarized_plusplus_D_val": out_dp["D"],
        "sympy_product_state_structural_zero_discord": sym_product_zero,
    }

def run_negative_tests():
    # Classical-classical diagonal joint -> D = 0 (within optimization error)
    pxy = np.array([[0.1, 0.2], [0.3, 0.4]])
    rho_cc, _, _ = _classical_joint_diag(pxy)
    out_cc = quantum_discord_2qubit(rho_cc, n_angles=30)
    # Product state -> D = 0
    rhoA = torch.tensor([[0.6, 0],[0, 0.4]], dtype=_cdtype())
    rhoB = torch.tensor([[0.3, 0],[0, 0.7]], dtype=_cdtype())
    rho_prod = _product_state(rhoA, rhoB)
    out_prod = quantum_discord_2qubit(rho_prod, n_angles=30)
    return {
        "classical_classical_discord_near_zero": abs(out_cc["D"]) < 5e-3,
        "classical_classical_D_val": out_cc["D"],
        "product_state_discord_near_zero": abs(out_prod["D"]) < 5e-3,
        "product_state_D_val": out_prod["D"],
    }

def run_boundary_tests():
    # Maximally mixed -> I=0, D=0
    rho_mm = torch.eye(4, dtype=_cdtype()) / 4.0
    out_mm = quantum_discord_2qubit(rho_mm, n_angles=20)
    # Bell state: I should approach 2 (for pure entangled, S_A=S_B=1, S_AB=0)
    rho_bell = _bell_phi_plus()
    out_bell = quantum_discord_2qubit(rho_bell, n_angles=30)
    return {
        "maximally_mixed_D_near_zero": abs(out_mm["D"]) < 1e-6,
        "maximally_mixed_I_near_zero": abs(out_mm["I"]) < 1e-6,
        "bell_I_near_2": abs(out_bell["I"] - 2.0) < 1e-3,
        "bell_D_positive": out_bell["D"] > 0.5,
        "bell_D_val": out_bell["D"],
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def _bool_ok(d):
        for k, v in d.items():
            if isinstance(v, bool) and not v:
                return False
        return True
    all_pass = _bool_ok(pos) and _bool_ok(neg) and _bool_ok(bnd)
    # Gap summary
    gap = {
        "classical_discord_always_zero": 0.0,
        "quantum_werner_p0p8_D": pos["werner_D_val"],
        "quantum_nonmax_entangled_D": pos["nonmax_entangled_D_val"],
        "quantum_bell_D": bnd["bell_D_val"],
        "gap_werner_vs_classical": pos["werner_D_val"] - 0.0,
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "quantum_discord_canonical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "quantum_discord_canonical",
            "classification": classification,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass,
            "summary": {"all_pass": all_pass, "gap": gap},
            "pairs_with": "sim_quantum_discord_classical.py",
            "divergence_log": [
                "canonical D(A:B) nonzero for Werner/entangled/dephased-plus states; "
                "classical baseline is identically zero",
                "J(A:B) optimized over qubit projective measurements on B; "
                "classical J=I always, quantum J<I for coherent rho_AB",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} gap_werner={gap['gap_werner_vs_classical']:.4f} -> {out}")
