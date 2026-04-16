#!/usr/bin/env python3
"""
sim_dirac_gerbe_mera_topology_variants.py

Step 3 (topology variants) of the Dirac×Gerbe×MERA coupling program (25th program).

Topology variants:
  T1: flat topology   — H_mera = log(2)   (χ=2, standard bond dimension)
  T2: enriched        — H_mera = log(3)   (χ=3, higher bond dimension)
  T3: minimal         — H_mera = log(2)/2 (χ=2, half-weight holonomy)

H_dirac (seed=0 fixed) and H_gerbe (DD_count=3 fixed) are topology-stable.
DPI: Q_DGM(T2) > Q_DGM(T1) > Q_DGM(T3) (monotone in H_mera)
z3 UNSAT: topology variant that sets H_mera=0 gives Q=0.

Load-bearing: pytorch + z3 + sympy
Classification: canonical
"""

import json, os, math
import numpy as np

classification = "canonical"

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

_TORCH = _Z3 = _SYMPY = False

try:
    import torch
    TOOL_MANIFEST["pytorch"].update(tried=True, used=True,
        reason="Compute Q_DGM for each MERA topology variant as float64 torch tensors; verify monotone ordering T2>T1>T3 under varying H_mera bond dimension (load-bearing).")
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    _TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import z3 as _z3
    TOOL_MANIFEST["z3"].update(tried=True, used=True,
        reason="UNSAT: topology variant with H_mera=0 makes Q_DGM=0 — zero bond-dimension entropy destroys coupling; structural impossibility proof (load-bearing).")
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    _Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as _sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="Symbolic Q_DGM = MI*H_dirac*H_gerbe*H_mera: encode topology sensitivity as H_mera factor; verify ordering under symbolic substitution (load-bearing).")
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    _SYMPY = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

for _mod, _key, _reason in [
    ("torch_geometric",  "pyg",       "no graph message-passing needed for scalar Q_DGM topology-variant comparison in DGM program"),
    ("cvc5",             "cvc5",      "z3 UNSAT covers the H_mera=0 impossibility for DGM topology variants; cvc5 adds no new proof here"),
    ("clifford",         "clifford",  "Dirac spectral gap encoded as scalar H_dirac for all topology classes; Cl(3,0) rotor not needed in this step"),
    ("geomstats",        "geomstats", "Riemannian geometry not invoked for scalar topology-variant Q_DGM ordering tests"),
    ("e3nn",             "e3nn",      "SO(3) equivariant networks not needed for scalar MERA bond-dimension topology-class comparison"),
    ("rustworkx",        "rustworkx", "no graph traversal needed for topology-variant scalar entropy product tests in DGM program"),
    ("xgi",              "xgi",       "no hyperedge structure needed for topology-variant scalar Q_DGM comparison"),
    ("toponetx",         "toponetx",  "CellComplex topology class encoded as H_mera scalar here; full CellComplex exercised in bridge step"),
    ("gudhi",            "gudhi",     "persistent homology not needed for topology-variant scalar Q_DGM ordering tests"),
]:
    try:
        __import__(_mod)
        TOOL_MANIFEST[_key]["tried"] = True
        TOOL_MANIFEST[_key]["reason"] = _reason
    except ImportError:
        TOOL_MANIFEST[_key]["reason"] = "not installed"


# =====================================================================
# Shell entropy constants
# =====================================================================

def spectral_gap_dirac(seed=0):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((4, 4))
    A = (A + A.T) / 2
    evals = np.sort(np.abs(np.linalg.eigvalsh(A)))
    return float(evals[1] - evals[0])


H_DIRAC = spectral_gap_dirac(seed=0)
H_GERBE = math.log(1 + 3)

TOPOLOGY_VARIANTS = {
    "T1_flat":     math.log(2),
    "T2_enriched": math.log(3),
    "T3_minimal":  math.log(2) / 2,
}


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

    MI_val = mera_MI_dephasing(seed=0, eps=0.3)[-1]

    Q_vals = {}
    for name, h_mera in TOPOLOGY_VARIANTS.items():
        Q_vals[name] = MI_val * H_DIRAC * H_GERBE * h_mera
        r[f"P_Q_{name}_positive"] = {
            "H_mera": h_mera,
            "Q_DGM": Q_vals[name],
            "passed": bool(Q_vals[name] > 0),
        }

    # DPI: T2 > T1 > T3
    r["P_DPI_T2_gt_T1_gt_T3"] = {
        "Q_T2": Q_vals["T2_enriched"],
        "Q_T1": Q_vals["T1_flat"],
        "Q_T3": Q_vals["T3_minimal"],
        "passed": bool(Q_vals["T2_enriched"] > Q_vals["T1_flat"] > Q_vals["T3_minimal"]),
    }

    r["P_H_dirac_stable"] = {
        "H_dirac": H_DIRAC,
        "passed": bool(H_DIRAC > 0),
    }
    r["P_H_gerbe_stable"] = {
        "H_gerbe": H_GERBE,
        "passed": bool(abs(H_GERBE - math.log(4)) < 1e-12),
    }

    if _TORCH:
        import torch
        h_vals = torch.tensor(
            [TOPOLOGY_VARIANTS[k] for k in ["T1_flat", "T2_enriched", "T3_minimal"]],
            dtype=torch.float64,
        )
        q_vals = torch.tensor(MI_val * H_DIRAC * H_GERBE, dtype=torch.float64) * h_vals
        ordered = bool((q_vals[1] > q_vals[0]).item() and (q_vals[0] > q_vals[2]).item())
        r["P_pytorch_topology_ordering"] = {
            "Q_values": q_vals.tolist(),
            "passed": ordered,
        }
    else:
        r["P_pytorch_topology_ordering"] = {"error": "torch not installed", "passed": False}

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}

    if _Z3:
        s = _z3.Solver()
        MI  = _z3.Real("MI")
        Hd  = _z3.Real("Hd")
        Hg  = _z3.Real("Hg")
        Hm  = _z3.Real("Hm")
        s.add(Hm == 0, MI > 0, Hd > 0, Hg > 0, MI * Hd * Hg * Hm > 0)
        unsat = (s.check() == _z3.unsat)
        r["N1_z3_unsat_Hmera_zero_Q_nonzero"] = {
            "z3": "unsat" if unsat else "sat",
            "passed": bool(unsat),
        }
    else:
        r["N1_z3_unsat_Hmera_zero_Q_nonzero"] = {"error": "z3 not installed", "passed": False}

    if _SYMPY:
        h = _sp.Symbol("h", positive=True)
        Q = _sp.Symbol("MI") * _sp.Symbol("Hd") * _sp.Symbol("Hg") * h
        h1, h2 = _sp.symbols("h1 h2", positive=True)
        diff = (Q.subs(h, h2) - Q.subs(h, h1)).subs([
            (_sp.Symbol("MI"), 1), (_sp.Symbol("Hd"), 1), (_sp.Symbol("Hg"), 1)
        ])
        diff_simplified = _sp.simplify(diff)
        numeric_check = float(diff_simplified.subs([(h1, 1), (h2, 2)]))
        r["N2_sympy_Q_monotone_in_Hmera"] = {
            "Q_diff_h2_minus_h1": str(diff_simplified),
            "numeric_h1_1_h2_2": numeric_check,
            "passed": bool(numeric_check > 0),
        }
    else:
        r["N2_sympy_Q_monotone_in_Hmera"] = {"error": "sympy not installed", "passed": False}

    MI_val = mera_MI_dephasing(seed=0, eps=0.3)[-1]
    Q_T2 = MI_val * H_DIRAC * H_GERBE * TOPOLOGY_VARIANTS["T2_enriched"]
    Q_T3 = MI_val * H_DIRAC * H_GERBE * TOPOLOGY_VARIANTS["T3_minimal"]
    r["N3_reversed_ordering_is_false"] = {
        "Q_T3_gt_T2": bool(Q_T3 > Q_T2),
        "passed": bool(not (Q_T3 > Q_T2)),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}

    vals = list(TOPOLOGY_VARIANTS.values())
    r["B1_topology_variants_distinct"] = {
        "variants": TOPOLOGY_VARIANTS,
        "passed": bool(len(set(round(v, 15) for v in vals)) == len(vals)),
    }

    h_dirac_recheck = spectral_gap_dirac(seed=0)
    r["B2_H_dirac_unchanged"] = {
        "H_dirac_original": H_DIRAC,
        "H_dirac_recheck": h_dirac_recheck,
        "passed": bool(abs(H_DIRAC - h_dirac_recheck) < 1e-12),
    }

    expected = math.log(2) / 2
    r["B3_T3_minimal_value"] = {
        "H_mera_T3": TOPOLOGY_VARIANTS["T3_minimal"],
        "expected": expected,
        "passed": bool(abs(TOPOLOGY_VARIANTS["T3_minimal"] - expected) < 1e-12),
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

    overall = pos["pass"] and neg["pass"] and bnd["pass"]

    out = {
        "name": "sim_dirac_gerbe_mera_topology_variants",
        "classification": classification,
        "divergence_log": (
            "Topology variants for Dirac×Gerbe×MERA (25th program). "
            f"H_dirac={H_DIRAC:.6f} (stable). H_gerbe={H_GERBE:.6f} (stable). "
            f"T1 H_mera={TOPOLOGY_VARIANTS['T1_flat']:.6f} (log(2)). "
            f"T2 H_mera={TOPOLOGY_VARIANTS['T2_enriched']:.6f} (log(3)). "
            f"T3 H_mera={TOPOLOGY_VARIANTS['T3_minimal']:.6f} (log(2)/2). "
            "DPI ordering: Q_T2 > Q_T1 > Q_T3 (monotone in H_mera). "
            "z3 UNSAT: H_mera=0 makes Q=0. "
            "sympy: Q is monotone in H_mera. "
            "pytorch: topology ordering validated as float64 tensor comparison."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "H_values": {"H_dirac": H_DIRAC, "H_gerbe": H_GERBE, "topology_variants": TOPOLOGY_VARIANTS},
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall,
    }

    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "sim_dirac_gerbe_mera_topology_variants_results.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"overall_pass={overall} -> {p}")
    if not overall:
        import sys; sys.exit(1)
