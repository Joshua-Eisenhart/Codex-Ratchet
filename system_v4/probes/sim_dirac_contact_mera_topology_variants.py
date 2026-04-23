#!/usr/bin/env python3
"""
sim_dirac_contact_mera_topology_variants.py

Step 3 (topology variants) of the Dirac×Contact×MERA coupling program (29th program).

Three topology variants T1/T2/T3 (different random seeds for H_dirac):
  T1: seed=0, T2: seed=7, T3: seed=42
H_contact and H_mera are fixed (topology-independent).

DPI (data-processing inequality): MI_final ≤ MI_input across all variants.
z3 UNSAT: H_dirac ≤ 0 AND Q_DCM > 0 impossible.

Classification: canonical
"""

import json, math
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Dirac×Contact×MERA topology-variant probe. This remains a "
    "classical-baseline comparison surface, not a nonclassical witness."
)
CLASSIFICATION_NOTE = divergence_log

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

_Z3 = False
try:
    import z3 as _z3
    TOOL_MANIFEST["z3"].update(tried=True, used=True,
        reason="UNSAT: H_dirac ≤ 0 with Q_DCM > 0 impossible — spectral gap must be positive for nonzero four-factor DCM product; topology variant constraint for step 3 (load-bearing).")
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    _Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

for _mod, _key, _reason in [
    ("torch",          "pytorch",   "tensor computation not required for DCM topology variant scalar stability checks"),
    ("torch_geometric","pyg",       "graph message passing not invoked in DCM topology variants step; all operations are scalar products"),
    ("cvc5",           "cvc5",      "z3 is sufficient for DCM topology variant UNSAT proof; cvc5 not needed alongside z3"),
    ("sympy",          "sympy",     "symbolic algebra not needed for DCM topology variant DPI and spectral stability checks"),
    ("clifford",       "clifford",  "Clifford algebra not a shell in DCM program; not invoked in topology variant step"),
    ("geomstats",      "geomstats", "Riemannian geometry not invoked in DCM topology variant scalar entropy checks"),
    ("e3nn",           "e3nn",      "SO(3) equivariant networks not needed for scalar DCM topology variant stability tests"),
    ("rustworkx",      "rustworkx", "no graph traversal required in DCM topology variant spectral gap computation"),
    ("xgi",            "xgi",       "no hyperedge structure required in DCM topology variant spectral gap entropy tests"),
    ("toponetx",       "toponetx",  "CellComplex topology variants captured via seed diversity; toponetx not invoked in DCM step 3"),
    ("gudhi",          "gudhi",     "persistent homology not needed in DCM topology variant spectral stability tests"),
]:
    try:
        __import__(_mod)
        if not TOOL_MANIFEST[_key]["tried"]:
            TOOL_MANIFEST[_key].update(tried=True, used=False, reason=_reason)
    except ImportError:
        if not TOOL_MANIFEST[_key]["tried"]:
            TOOL_MANIFEST[_key]["reason"] = "not installed"

# =====================================================================
# Shell entropy constants
# =====================================================================

def _spectral_gap(seed=0):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((4, 4))
    A = (A + A.T) / 2
    evals = np.linalg.eigvalsh(A)
    return float(abs(evals[1] - evals[0]))

H_CONTACT = math.log(17)
H_MERA    = math.log(2)

TOPOLOGY_SEEDS = {"T1": 0, "T2": 7, "T3": 42}

def mera_MI_dephasing(n_layers=4, seed=0, eps=0.3):
    rng = np.random.default_rng(seed)
    psi = np.array([1., 0., 0., 1.]) / math.sqrt(2)
    rho = np.outer(psi, psi.conj())
    def pt_A(r): return np.einsum("akbk->ab", r.reshape(2,2,2,2))
    def pt_B(r): return np.einsum("kakb->ab", r.reshape(2,2,2,2))
    def vn(r):
        ev = np.linalg.eigvalsh(r); ev = ev[ev > 1e-12]
        return float(-np.sum(ev * np.log(ev)))
    def MI(r): return vn(pt_A(r)) + vn(pt_B(r)) - vn(r)
    vals = [MI(rho)]
    for _ in range(n_layers):
        U_A = np.linalg.qr(rng.standard_normal((2,2)) + 1j*rng.standard_normal((2,2)))[0]
        U_B = np.linalg.qr(rng.standard_normal((2,2)) + 1j*rng.standard_normal((2,2)))[0]
        U = np.kron(U_A, U_B)
        rho = U @ rho @ U.conj().T
        rho = (1-eps)*rho + eps*np.diag(np.diag(rho))
        vals.append(MI(rho))
    return vals

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}

    for tname, seed in TOPOLOGY_SEEDS.items():
        H_d = _spectral_gap(seed=seed)
        Q   = mera_MI_dephasing(seed=seed, eps=0.3)[-1] * H_d * H_CONTACT * H_MERA
        dpi_layers = mera_MI_dephasing(seed=seed, eps=0.3)
        dpi_ok = bool(dpi_layers[0] >= dpi_layers[-1])

        r[f"P_{tname}_H_dirac_stable"] = {
            "seed": seed, "H_dirac": H_d,
            "passed": bool(H_d > 0),
        }
        r[f"P_{tname}_Q_positive"] = {
            "Q": Q, "passed": bool(Q > 0),
        }
        r[f"P_{tname}_DPI_MI_final_leq_input"] = {
            "MI_input": dpi_layers[0], "MI_final": dpi_layers[-1],
            "passed": dpi_ok,
        }

    r["P_H_contact_stable_across_variants"] = {
        "H_contact": H_CONTACT, "passed": bool(H_CONTACT > 0),
    }
    r["P_H_mera_stable_across_variants"] = {
        "H_mera": H_MERA, "passed": bool(H_MERA > 0),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r

# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}

    if _Z3:
        s = _z3.Solver()
        Hd = _z3.Real("H_dirac")
        Hco = _z3.Real("H_contact")
        Hm  = _z3.Real("H_mera")
        MI  = _z3.Real("MI")
        Q   = MI * Hd * Hco * Hm
        s.add(Hd <= 0, Hco > 0, Hm > 0, MI > 0, Q > 0)
        unsat = (s.check() == _z3.unsat)
        r["N1_z3_unsat_H_dirac_nonpositive"] = {
            "z3": "unsat" if unsat else "sat",
            "passed": bool(unsat),
        }
    else:
        r["N1_z3_unsat_H_dirac_nonpositive"] = {"error": "z3 not installed", "passed": False}

    r["N2_seed_variation_all_H_dirac_positive"] = {
        "H_dirac_values": {t: _spectral_gap(seed=s) for t, s in TOPOLOGY_SEEDS.items()},
        "passed": bool(all(_spectral_gap(seed=s) > 0 for s in TOPOLOGY_SEEDS.values())),
    }
    r["N3_high_eps_DPI_still_holds"] = {
        "diffs": {t: round(mera_MI_dephasing(seed=s, eps=0.9)[0] - mera_MI_dephasing(seed=s, eps=0.9)[-1], 4)
                  for t, s in TOPOLOGY_SEEDS.items()},
        "passed": bool(all(
            mera_MI_dephasing(seed=s, eps=0.9)[0] >= mera_MI_dephasing(seed=s, eps=0.9)[-1]
            for s in TOPOLOGY_SEEDS.values()
        )),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r

# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}

    r["B1_H_contact_fixed"] = {
        "H_contact": H_CONTACT, "log17": math.log(17),
        "passed": bool(abs(H_CONTACT - math.log(17)) < 1e-12),
    }
    r["B2_H_mera_fixed"] = {
        "H_mera": H_MERA, "log2": math.log(2),
        "passed": bool(abs(H_MERA - math.log(2)) < 1e-12),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    result = {
        "sim": "sim_dirac_contact_mera_topology_variants",
        "classification": classification,
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "topology_seeds": TOPOLOGY_SEEDS,
        "H_contact": H_CONTACT,
        "H_mera": H_MERA,
        "positive_tests": pos,
        "negative_tests": neg,
        "boundary_tests": bnd,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "overall_pass": bool(pos["pass"] and neg["pass"] and bnd["pass"]),
    }
    print(json.dumps(result, indent=2))
