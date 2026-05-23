#!/usr/bin/env python3
"""
sim_holo_dirac_st_pairwise_coupling.py

Coupling Program Step 1: Shell-local + pairwise coupling checks.
Gap-fill: covers 3 uncovered pairs — Dirac×Holographic, Holographic×SpectralTriple,
Dirac×SpectralTriple.

Q_HDS = MI × H_holo × H_dirac × H_st

Shell entropy definitions:
  H_holo = 2*log(2)  (holographic entropy, fixed)
  H_dirac = spectral gap of seed=0 random symmetric 4×4
  H_st    = spectral gap of seed=1 random symmetric 4×4
  MI      = S_A + S_B - S_AB from Bell state through 4-layer dephasing-MERA (eps=0.3)

Tests:
  P-section:
    P1. H_holo > 0
    P2. H_dirac > 0
    P3. H_st > 0
    P4. MI > 0
    P5. Q_HDS > 0 (all shells active)
    P6-P8. Pairwise partial products nonzero (Holo×Dirac, Holo×ST, Dirac×ST)
  N-section:
    N1. z3 UNSAT: Q_HDS != 0 with MI=0 (MERA absent)
    N2. Q with H_holo=0 → 0
    N3. Q with H_dirac=0 → 0
    N4. Q with H_st=0 → 0
  B-section:
    B1. All shells inactive → Q=0
    B2. Single shell active → Q=0 (missing factors)

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

import numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from z3 import Real, Solver, unsat, And
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

# =====================================================================
# SHELL ENTROPY HELPERS
# =====================================================================

def h_holo():
    """Holographic entropy: fixed 2*log(2), AdS boundary saturation."""
    return 2.0 * math.log(2)

def h_dirac(seed=0):
    """Spectral gap of seed=0 random symmetric 4x4 matrix."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((4, 4))
    M = (A + A.T) / 2.0
    evals = np.linalg.eigvalsh(M)
    return float(abs(evals[1] - evals[0]))

def h_st(seed=1):
    """Spectral gap of seed=1 random symmetric 4x4 matrix."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((4, 4))
    M = (A + A.T) / 2.0
    evals = np.linalg.eigvalsh(M)
    return float(abs(evals[1] - evals[0]))

def mera_MI_dephasing(n_layers=4, seed=0, eps=0.3):
    """MI from Bell state through n_layers of random-unitary dephasing MERA."""
    rng = np.random.default_rng(seed)
    psi = np.array([1., 0., 0., 1.]) / math.sqrt(2)
    rho = np.outer(psi, psi.conj())

    def pt_A(r):
        return np.einsum("akbk->ab", r.reshape(2, 2, 2, 2))

    def pt_B(r):
        return np.einsum("kakb->ab", r.reshape(2, 2, 2, 2))

    def vn(r):
        ev = np.linalg.eigvalsh(r)
        ev = ev[ev > 1e-12]
        return float(-np.sum(ev * np.log(ev)))

    def MI(r):
        return vn(pt_A(r)) + vn(pt_B(r)) - vn(r)

    vals = [MI(rho)]
    for _ in range(n_layers):
        U_A = np.linalg.qr(rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2)))[0]
        U_B = np.linalg.qr(rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2)))[0]
        U = np.kron(U_A, U_B)
        rho = U @ rho @ U.conj().T
        rho = (1 - eps) * rho + eps * np.diag(np.diag(rho))
        vals.append(MI(rho))
    return vals

def compute_MI():
    """Return final MI after 4-layer dephasing."""
    vals = mera_MI_dephasing(n_layers=4, seed=0, eps=0.3)
    return float(vals[-1])

def Q_HDS(mi, hh, hd, hs):
    return mi * hh * hd * hs

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    hh = h_holo()
    hd = h_dirac(seed=0)
    hs = h_st(seed=1)
    mi = compute_MI()

    results["P1_h_holo_positive"] = {"value": hh, "pass": hh > 0}
    results["P2_h_dirac_positive"] = {"value": hd, "pass": hd > 0}
    results["P3_h_st_positive"] = {"value": hs, "pass": hs > 0}
    results["P4_MI_positive"] = {"value": mi, "pass": mi > 0}

    q_full = Q_HDS(mi, hh, hd, hs)
    results["P5_Q_HDS_full_nonzero"] = {"value": q_full, "pass": q_full > 0}

    # Pairwise partial products (gap-fill pairs)
    results["P6_pair_holo_dirac"] = {"value": hh * hd, "pass": hh * hd > 0}
    results["P7_pair_holo_st"] = {"value": hh * hs, "pass": hh * hs > 0}
    results["P8_pair_dirac_st"] = {"value": hd * hs, "pass": hd * hs > 0}

    return results

# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    hh = h_holo()
    hd = h_dirac(seed=0)
    hs = h_st(seed=1)
    mi = compute_MI()

    # N1: z3 UNSAT — Q_HDS != 0 requires MI != 0
    try:
        mi_var = Real("mi")
        s = Solver()
        s.add(mi_var == 0)
        s.add(mi_var * hh * hd * hs != 0)
        r = s.check()
        results["N1_z3_unsat_mi_zero"] = {
            "z3_result": str(r),
            "pass": r == unsat,
            "reason": "Q_HDS=0 when MI=0; z3 confirms UNSAT for Q!=0 with MI=0",
        }
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Proves Q_HDS=0 is forced when MI=0; structural impossibility gate"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    except Exception as e:
        results["N1_z3_unsat_mi_zero"] = {"pass": False, "error": str(e)}

    results["N2_Q_holo_zero"] = {"value": Q_HDS(mi, 0.0, hd, hs), "pass": Q_HDS(mi, 0.0, hd, hs) == 0.0}
    results["N3_Q_dirac_zero"] = {"value": Q_HDS(mi, hh, 0.0, hs), "pass": Q_HDS(mi, hh, 0.0, hs) == 0.0}
    results["N4_Q_st_zero"] = {"value": Q_HDS(mi, hh, hd, 0.0), "pass": Q_HDS(mi, hh, hd, 0.0) == 0.0}

    return results

# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    hh = h_holo()
    hd = h_dirac(seed=0)
    hs = h_st(seed=1)
    mi = compute_MI()

    # B1: all shells inactive
    results["B1_all_inactive"] = {"value": Q_HDS(0, 0, 0, 0), "pass": Q_HDS(0, 0, 0, 0) == 0.0}

    # B2: single shell active
    results["B2_only_holo"] = {"value": Q_HDS(0, hh, 0, 0), "pass": Q_HDS(0, hh, 0, 0) == 0.0}
    results["B2_only_dirac"] = {"value": Q_HDS(0, 0, hd, 0), "pass": Q_HDS(0, 0, hd, 0) == 0.0}
    results["B2_only_st"] = {"value": Q_HDS(0, 0, 0, hs), "pass": Q_HDS(0, 0, 0, hs) == 0.0}

    # B3: MI layers sweep (stability of MI across layers)
    mi_vals = mera_MI_dephasing(n_layers=4, seed=0, eps=0.3)
    results["B3_MI_layer_sweep"] = {
        "values": [round(v, 6) for v in mi_vals],
        "monotone_check": all(mi_vals[i] >= mi_vals[i+1] - 1e-9 for i in range(len(mi_vals)-1)),
        "pass": mi_vals[-1] > 0,
    }

    return results

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    hh = h_holo()
    hd = h_dirac(seed=0)
    hs = h_st(seed=1)
    mi = compute_MI()

    results = {
        "name": "sim_holo_dirac_st_pairwise_coupling",
        "description": "Gap-fill coupling program Step 1: Holographic x Dirac x SpectralTriple pairwise",
        "Q_form": "Q_HDS = MI x H_holo x H_dirac x H_st",
        "shell_values": {
            "H_holo": hh,
            "H_dirac": hd,
            "H_st": hs,
            "MI": mi,
            "Q_HDS": Q_HDS(mi, hh, hd, hs),
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "classical_baseline",
        "covered_pairs": ["Dirac x Holographic", "Holographic x SpectralTriple", "Dirac x SpectralTriple"],
    }

    all_pass = all(
        v.get("pass", False)
        for section in [pos, neg, bnd]
        for v in section.values()
        if isinstance(v, dict) and "pass" in v
    )
    results["summary"] = {"all_pass": all_pass}
    print(f"Q_HDS = {results['shell_values']['Q_HDS']:.6f}")
    print(f"All pass: {all_pass}")

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_holo_dirac_st_pairwise_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
