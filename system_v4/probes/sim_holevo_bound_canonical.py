#!/usr/bin/env python3
"""Canonical: Holevo chi on noncommuting ensembles.

chi = S(sum p_i rho_i) - sum p_i S(rho_i)
Classical (commuting rho_i) => chi collapses to Jensen mixing entropy equality.
Quantum (noncommuting rho_i) => chi > I_acc typically, and chi can be less than
H(priors) for nonorthogonal states — a gap invisible to the classical baseline.

Pairs with sim_holevo_bound_classical.py.

load_bearing: pytorch (complex density ops + eigvalsh for S(rho)).
"""
import json, os, math
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "numpy":   {"tried": True, "used": True,  "reason": "scalar arithmetic"},
    "pytorch": {"tried": False,"used": False, "reason": ""},
    "sympy":   {"tried": False,"used": False, "reason": "not required for this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy":   "supportive",
    "pytorch": "load_bearing",
    "sympy":   None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "complex density matrix mix + eigvalsh for von Neumann entropy"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def _cdtype():
    return torch.complex128


def _S_vn(rho):
    rho_h = 0.5 * (rho + rho.conj().T)
    w = torch.linalg.eigvalsh(rho_h).real
    w = torch.clamp(w, min=0.0)
    s = w.sum()
    if s > 0:
        w = w / s
    mask = w > 1e-15
    w_safe = w[mask]
    return float(-(w_safe * torch.log2(w_safe)).sum().item())


def holevo_chi(priors, rhos):
    """chi = S(sum p_i rho_i) - sum p_i S(rho_i)."""
    mix = torch.zeros_like(rhos[0])
    avg_S = 0.0
    for p, r in zip(priors, rhos):
        mix = mix + p * r
        avg_S += p * _S_vn(r)
    return _S_vn(mix) - avg_S


def _H(p):
    p = np.asarray(p, float); p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


# ---- standard ensembles --------------------------------------------------

def _ket_theta(theta):
    """|theta> = cos(theta/2)|0> + sin(theta/2)|1>."""
    c = math.cos(theta / 2); s = math.sin(theta / 2)
    v = torch.tensor([[c + 0j], [s + 0j]], dtype=_cdtype())
    return v @ v.conj().T


def _bb84_like_ensemble():
    """|0>, |1>, |+>, |->, uniform priors — classic nonorthogonal ensemble."""
    rho0 = torch.tensor([[1, 0], [0, 0]], dtype=_cdtype())
    rho1 = torch.tensor([[0, 0], [0, 1]], dtype=_cdtype())
    plus = torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=_cdtype())
    minus = torch.tensor([[0.5, -0.5], [-0.5, 0.5]], dtype=_cdtype())
    return [0.25, 0.25, 0.25, 0.25], [rho0, rho1, plus, minus]


# ---- I_accessible lower bound via fixed measurement (qubit POVM sweep) --

def _povm_measurement_info(priors, rhos, n_angles=40):
    """Return max over 2-outcome projective measurements of I(X:Y).

    For qubit ensemble, sweep measurement |v><v| over Bloch sphere.
    """
    d = rhos[0].shape[0]
    assert d == 2, "only 2d for this sweep"
    best = 0.0
    thetas = np.linspace(0, math.pi, n_angles)
    phis = np.linspace(0, 2 * math.pi, n_angles, endpoint=False)
    for th in thetas:
        c = math.cos(th / 2); s = math.sin(th / 2)
        for ph in phis:
            eph = complex(math.cos(ph), math.sin(ph))
            v = torch.tensor([[c + 0j], [s * eph]], dtype=_cdtype())
            Pi0 = v @ v.conj().T
            Pi1 = torch.eye(2, dtype=_cdtype()) - Pi0
            # joint p(x,y) = p_x * Tr(Pi_y rho_x)
            n_x = len(priors)
            pxy = np.zeros((n_x, 2))
            for ix, (p, r) in enumerate(zip(priors, rhos)):
                p0 = float(torch.trace(Pi0 @ r).real.item())
                p1 = float(torch.trace(Pi1 @ r).real.item())
                pxy[ix, 0] = p * max(p0, 0.0)
                pxy[ix, 1] = p * max(p1, 0.0)
            pxy = pxy / pxy.sum()
            px = pxy.sum(axis=1); py = pxy.sum(axis=0)
            I = _H(px) + _H(py) - _H(pxy.ravel())
            if I > best:
                best = I
    return best


# ---- tests --------------------------------------------------------------

def run_positive_tests():
    # Nonorthogonal qubit ensemble: |0>, |theta> with theta=pi/3
    rho0 = _ket_theta(0.0)
    rho1 = _ket_theta(math.pi / 3)
    priors = [0.5, 0.5]
    chi = holevo_chi(priors, [rho0, rho1])
    # Orthogonal (|0>,|1>): chi should equal 1
    chi_ortho = holevo_chi([0.5, 0.5], [_ket_theta(0.0), _ket_theta(math.pi)])
    # BB84-like
    bpriors, brhos = _bb84_like_ensemble()
    chi_bb = holevo_chi(bpriors, brhos)
    # I_acc gap: chi > I_accessible lower bound (via best projective measurement)
    I_acc = _povm_measurement_info(priors, [rho0, rho1], n_angles=32)
    gap = chi - I_acc
    return {
        "nonortho_chi_less_than_1": chi < 1.0 - 1e-6,
        "nonortho_chi_val": chi,
        "ortho_chi_equals_1": abs(chi_ortho - 1.0) < 1e-6,
        "ortho_chi_val": chi_ortho,
        "bb84_chi_val": chi_bb,
        "bb84_chi_less_than_log_d": chi_bb < math.log2(2) + 1e-9,
        "chi_geq_I_acc": gap >= -1e-6,
        "holevo_gap_chi_minus_Iacc": gap,
        "I_acc_lower_bound": I_acc,
    }


def run_negative_tests():
    # Identical rho_i -> chi = 0
    rho = _ket_theta(0.4)
    chi_same = holevo_chi([0.5, 0.5], [rho, rho])
    # Classical (commuting diagonal) ensemble: chi collapses to classical mixing entropy
    r1 = torch.diag(torch.tensor([0.7, 0.3], dtype=_cdtype()))
    r2 = torch.diag(torch.tensor([0.2, 0.8], dtype=_cdtype()))
    chi_commut = holevo_chi([0.5, 0.5], [r1, r2])
    # Compare to classical formula H(mix) - sum p_i H(rho_i)
    mix_p = np.array([0.5 * 0.7 + 0.5 * 0.2, 0.5 * 0.3 + 0.5 * 0.8])
    expected = _H(mix_p) - (0.5 * _H([0.7, 0.3]) + 0.5 * _H([0.2, 0.8]))
    return {
        "identical_states_chi_zero": abs(chi_same) < 1e-9,
        "identical_chi_val": chi_same,
        "commuting_matches_classical_formula": abs(chi_commut - expected) < 1e-9,
        "commuting_chi_val": chi_commut,
        "classical_formula_val": expected,
    }


def run_boundary_tests():
    # Degenerate prior -> chi = 0
    rho0 = _ket_theta(0.0); rho1 = _ket_theta(math.pi / 2)
    chi_deg = holevo_chi([1.0, 0.0], [rho0, rho1])
    # chi <= log2(d): hold for a mixed ensemble of 4 states in d=2
    priors, rhos = _bb84_like_ensemble()
    chi = holevo_chi(priors, rhos)
    # chi >= 0 always
    return {
        "degenerate_prior_chi_zero": abs(chi_deg) < 1e-9,
        "degen_chi_val": chi_deg,
        "chi_bounded_by_log2_d": chi <= math.log2(2) + 1e-9,
        "chi_nonnegative": chi >= -1e-9,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def _bool_ok(d):
        for k, v in d.items():
            if isinstance(v, bool) and not v:
                return False
        return True
    all_pass = _bool_ok(pos) and _bool_ok(neg) and _bool_ok(bnd)
    # chi for nonorthogonal pi/3 pair should be ~ 0.55 bits < 1 bit prior entropy
    gap = {
        "classical_chi_equals_mixing_entropy_with_equality": "chi = H(mix) - sum p_i H(rho_i) on commuting rho_i",
        "canonical_nonortho_chi": pos["nonortho_chi_val"],
        "classical_prior_H_bound": 1.0,  # H([0.5,0.5]) = 1
        "holevo_bound_gap_nonortho": 1.0 - pos["nonortho_chi_val"],
        "chi_minus_I_acc": pos["holevo_gap_chi_minus_Iacc"],
        "I_acc_best_projective": pos["I_acc_lower_bound"],
        "classical_baseline_admits_no_nonortho_ensemble": True,
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "holevo_bound_canonical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "holevo_bound_canonical",
            "classification": classification,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass,
            "summary": {"all_pass": all_pass, "gap": gap},
            "pairs_with": "sim_holevo_bound_classical.py",
            "divergence_log": [
                "canonical chi on nonorthogonal |0>,|theta=pi/3> ensemble is strictly "
                "less than prior entropy (1 bit) — classical baseline cannot see this",
                "chi > I_accessible (best projective measurement) exhibits the Holevo gap",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} chi_nonortho={pos['nonortho_chi_val']:.4f} "
          f"chi_minus_Iacc={pos['holevo_gap_chi_minus_Iacc']:.4f} -> {out}")
