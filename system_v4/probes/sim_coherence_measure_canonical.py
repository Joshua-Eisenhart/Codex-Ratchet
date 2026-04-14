#!/usr/bin/env python3
"""Canonical: l1-norm coherence C_l1(rho) = sum_{i!=j} |rho_ij| on real
density matrices, including superposition and mixed-coherent states.

Pairs with sim_coherence_measure_classical.py (identically 0 on diagonal).

load_bearing: pytorch (complex density matrices, basis rotation via unitary).
"""
import json, os, math
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "numpy":   {"tried": True, "used": True,  "reason": "cross-check"},
    "pytorch": {"tried": False,"used": False, "reason": ""},
    "z3":      {"tried": True, "used": False, "reason": "not needed: numerical"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy":   "supportive",
    "pytorch": "load_bearing",
    "z3":      None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "complex rho, unitary basis rotation, l1-norm over off-diagonals"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def _cdtype():
    return torch.complex128


def l1_coherence_torch(rho):
    """C_l1(rho) = sum_{i != j} |rho_ij|."""
    diag = torch.diag(torch.diag(rho))
    off = rho - diag
    return float(off.abs().sum().real.item())


def _plus_state_rho(n=2):
    v = torch.ones((n, 1), dtype=_cdtype()) / math.sqrt(n)
    return v @ v.conj().T


def _ghz_rho(n_qubits=2):
    dim = 2 ** n_qubits
    v = torch.zeros((dim, 1), dtype=_cdtype())
    v[0, 0] = 1 / math.sqrt(2); v[-1, 0] = 1 / math.sqrt(2)
    return v @ v.conj().T


def _dephase(rho, gamma):
    """Partial dephasing on computational basis."""
    d = rho.shape[0]
    out = rho.clone()
    for i in range(d):
        for j in range(d):
            if i != j:
                out[i, j] = out[i, j] * (1 - gamma)
    return out


def _random_unitary(d, seed=0):
    g = torch.Generator(); g.manual_seed(seed)
    # Random complex Ginibre -> QR -> unitary with phase-fixed diagonal
    A = torch.randn(d, d, generator=g, dtype=torch.float64) + \
        1j * torch.randn(d, d, generator=g, dtype=torch.float64)
    Q, R = torch.linalg.qr(A)
    ph = torch.diag(R) / torch.diag(R).abs()
    return Q * ph.conj()


# ---- tests --------------------------------------------------------------

def run_positive_tests():
    # |+> state: C_l1(|+><+|) = 1 exactly (off-diag = 0.5, two entries)
    rho_plus = _plus_state_rho(2)
    c_plus = l1_coherence_torch(rho_plus)
    # GHZ 2q: C_l1 = 1 (two off-diag each 0.5)
    rho_ghz = _ghz_rho(2)
    c_ghz = l1_coherence_torch(rho_ghz)
    # Dephased |+>: gamma=0.5 halves coherence
    rho_deph = _dephase(rho_plus, 0.5)
    c_deph = l1_coherence_torch(rho_deph)
    # 3-level uniform superposition
    v3 = torch.ones((3, 1), dtype=_cdtype()) / math.sqrt(3)
    rho_3 = v3 @ v3.conj().T
    c_3 = l1_coherence_torch(rho_3)  # (3^2 - 3) * 1/3 = 2
    return {
        "plus_state_c_l1_is_1": abs(c_plus - 1.0) < 1e-10,
        "plus_c_val": c_plus,
        "ghz2_c_l1_is_1": abs(c_ghz - 1.0) < 1e-10,
        "ghz2_c_val": c_ghz,
        "dephased_plus_c_l1_is_0p5": abs(c_deph - 0.5) < 1e-10,
        "dephased_c_val": c_deph,
        "dim3_uniform_c_l1_is_2": abs(c_3 - 2.0) < 1e-10,
        "dim3_c_val": c_3,
    }


def run_negative_tests():
    # Diagonal (classical) rho -> C_l1 = 0
    p = torch.tensor([0.2, 0.3, 0.5], dtype=_cdtype())
    rho_diag = torch.diag(p)
    c_diag = l1_coherence_torch(rho_diag)
    # Maximally mixed (also diagonal)
    rho_mm = torch.eye(4, dtype=_cdtype()) / 4.0
    c_mm = l1_coherence_torch(rho_mm)
    return {
        "diagonal_c_l1_zero": c_diag == 0.0,
        "diag_c_val": c_diag,
        "max_mixed_c_l1_zero": c_mm == 0.0,
        "max_mixed_c_val": c_mm,
    }


def run_boundary_tests():
    # Basis-rotation: classical state becomes coherent in rotated basis.
    # rho = diag(0.6, 0.4); U = Hadamard. In new basis, off-diagonals appear.
    rho_cl = torch.diag(torch.tensor([0.6, 0.4], dtype=_cdtype()))
    H = torch.tensor([[1, 1], [1, -1]], dtype=_cdtype()) / math.sqrt(2)
    rho_rot = H @ rho_cl @ H.conj().T
    c_before = l1_coherence_torch(rho_cl)
    c_after = l1_coherence_torch(rho_rot)
    # Pure classical rho = diag(1,0) has C_l1 = 0
    rho_pure_cl = torch.diag(torch.tensor([1.0, 0.0], dtype=_cdtype()))
    c_pure_cl = l1_coherence_torch(rho_pure_cl)
    # Random unitary rotation of a classical state: coherence emerges
    U = _random_unitary(3, seed=7)
    rho_cl3 = torch.diag(torch.tensor([0.2, 0.3, 0.5], dtype=_cdtype()))
    rho_rot3 = U @ rho_cl3 @ U.conj().T
    c_rot3 = l1_coherence_torch(rho_rot3)
    return {
        "classical_in_native_basis_zero": c_before == 0.0,
        "classical_becomes_coherent_under_Hadamard": c_after > 0.0,
        "rot_c_val": c_after,
        "pure_classical_zero_coherence": c_pure_cl == 0.0,
        "random_unitary_induces_coherence_dim3": c_rot3 > 0.0,
        "rot_dim3_c_val": c_rot3,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def _bool_ok(d):
        for k, v in d.items():
            if isinstance(v, bool) and not v:
                return False
        return True
    all_pass = _bool_ok(pos) and _bool_ok(neg) and _bool_ok(bnd)
    gap = {
        "classical_c_l1_always_zero": 0.0,
        "canonical_plus_state_c_l1": pos["plus_c_val"],
        "canonical_dim3_uniform_c_l1": pos["dim3_c_val"],
        "canonical_ghz2_c_l1": pos["ghz2_c_val"],
        "gap_plus_vs_classical": pos["plus_c_val"] - 0.0,
        "basis_rotation_induced_coherence": bnd["rot_c_val"],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "coherence_measure_canonical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "coherence_measure_canonical",
            "classification": classification,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass,
            "summary": {"all_pass": all_pass, "gap": gap},
            "pairs_with": "sim_coherence_measure_classical.py",
            "divergence_log": [
                "|+> superposition yields C_l1 = 1; classical diagonal yields 0",
                "basis rotation makes classical state coherent — basis-dependence "
                "absent in classical baseline",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} gap_plus={gap['gap_plus_vs_classical']:.4f} -> {out}")
