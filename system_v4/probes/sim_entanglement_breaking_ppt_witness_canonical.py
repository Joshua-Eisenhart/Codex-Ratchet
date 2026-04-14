#!/usr/bin/env python3
"""Entanglement-breaking witness via PPT on the Choi state of a single-qubit
depolarizing channel E_p(rho) = (1-p) rho + p I/2.

The Choi state J(E_p) is entanglement-breaking iff its partial transpose is PSD.
Threshold: EB iff p >= 2/3. Gap metric: minimum PPT eigenvalue.
  - p = 0.3: NOT EB (min eig < 0)
  - p = 0.8: EB (min eig >= 0)
Load-bearing: pytorch (eigvalsh on Choi + partial transpose).
"""

import json
import os

classification = "canonical"

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

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Builds Choi matrix of depolarizing channel, computes partial "
        "transpose, and uses torch.linalg.eigvalsh to decide PPT/EB; "
        "load-bearing for the gap-across-threshold claim."
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    raise


def choi_depolarizing(p):
    """Choi J = sum_{ij} |i><j| (x) E(|i><j|), qubit depolarizing."""
    I2 = torch.eye(2, dtype=torch.complex128)
    # Maximally entangled (unnormalized) |Phi+><Phi+|
    phi = torch.zeros(4, dtype=torch.complex128)
    phi[0] = 1.0
    phi[3] = 1.0
    phi = phi / (2 ** 0.5)
    Phi = torch.outer(phi, phi.conj())
    # Apply E on system B: J = (I (x) E)(|Phi+><Phi+|)
    # For depolarizing: J = (1-p) Phi + p * (I/2 (x) I/2) ... but we want (I (x) E)
    # (I (x) E)(|Phi+><Phi+|) = (1-p) Phi + p * (rho_A (x) I/2)
    # where rho_A = Tr_B(Phi) = I/2.
    maximally_mixed_joint = torch.kron(I2 / 2, I2 / 2)
    J = (1 - p) * Phi + p * maximally_mixed_joint
    return J


def partial_transpose_B(rho, dA=2, dB=2):
    R = rho.reshape(dA, dB, dA, dB)
    R = R.permute(0, 3, 2, 1).contiguous()  # transpose on B index pair
    return R.reshape(dA * dB, dA * dB)


def min_pt_eig(p):
    J = choi_depolarizing(p)
    JT = partial_transpose_B(J)
    JT_h = 0.5 * (JT + JT.conj().T)
    eigs = torch.linalg.eigvalsh(JT_h)
    return eigs.min().item()


def run_positive_tests():
    # p = 0.8 -> EB, min eig >= 0
    m = min_pt_eig(0.8)
    return {
        "p_0p8_min_pt_eig": m,
        "p_0p8_is_EB": m >= -1e-9,
    }


def run_negative_tests():
    # p = 0.3 -> NOT EB, min eig < 0
    m = min_pt_eig(0.3)
    return {
        "p_0p3_min_pt_eig": m,
        "p_0p3_is_not_EB": m < -1e-6,
    }


def run_boundary_tests():
    # Threshold p = 2/3: min eig ~ 0
    m_thresh = min_pt_eig(2 / 3)
    # Identity channel (p=0): strongly entangled, min eig = -1/2
    m_id = min_pt_eig(0.0)
    # Fully depolarizing (p=1): maximally mixed, min eig = 1/4
    m_full = min_pt_eig(1.0)
    return {
        "p_threshold_min_eig": m_thresh,
        "p_threshold_near_zero": abs(m_thresh) < 1e-6,
        "p_0_min_eig": m_id,
        "p_0_strongly_entangled": m_id < -0.4,
        "p_1_min_eig": m_full,
        "p_1_separable": m_full > 0.2,
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        bool(pos["p_0p8_is_EB"])
        and bool(neg["p_0p3_is_not_EB"])
        and bool(bnd["p_threshold_near_zero"])
        and bool(bnd["p_0_strongly_entangled"])
        and bool(bnd["p_1_separable"])
    )
    results = {
        "name": "entanglement_breaking_ppt_witness_canonical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "quantum_classical_gap": {
            "metric": "min eigenvalue of partial transpose of Choi state",
            "p_0p3_min_eig": neg["p_0p3_min_pt_eig"],
            "p_0p8_min_eig": pos["p_0p8_min_pt_eig"],
            "sign_change_gap": pos["p_0p8_min_pt_eig"] - neg["p_0p3_min_pt_eig"],
        },
        "summary": {"all_pass": bool(all_pass)},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entanglement_breaking_ppt_witness_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
