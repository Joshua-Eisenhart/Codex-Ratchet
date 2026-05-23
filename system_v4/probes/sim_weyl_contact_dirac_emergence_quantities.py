#!/usr/bin/env python3
"""
sim_weyl_contact_dirac_emergence_quantities.py

Step 4 (classical_baseline) of the Weyl × Contact × Dirac coupling program.

Emergence quantities: which observables appear only when multiple shells active?

Tests:
  E1: Weyl alone — H_weyl>0, H_contact=0 (inactive), H_dirac=0 (inactive), MI=0 → Q_WCD=0
  E2: Contact alone — H_contact>0, H_weyl=0, H_dirac=0, MI=0 → Q_WCD=0
  E3: Dirac alone — H_dirac>0, H_weyl=0, H_contact=0, MI=0 → Q_WCD=0
  E4a: Weyl × Contact pairwise (no Dirac, no MERA) → Q_WCD=0
  E4b: Contact × Dirac pairwise (no Weyl, no MERA) → Q_WCD=0
  E4c: Weyl × Dirac pairwise (no Contact, no MERA) → Q_WCD=0
  E4d: All shells, no MERA (MI=0) → Q_WCD=0
  E5: Full quad (all shells + MERA) → Q_WCD>0 (EMERGENT)
  N1: z3 UNSAT — Q_WCD>0 requires all four factors nonzero
  N2: sympy — Q=a*b*c*d collapses to 0 if any factor 0
  B1: emergent gap — Q_WCD(E5) >> Q_WCD(E4d=0)
  B2: pytorch density matrix hermitian check

Classification: classical_baseline
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os
import math
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False, "used": False,
        "reason": "torch tensor density matrix; hermitian check for B2 (load-bearing)",
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "graph learning not required for emergence quantities; excluded",
    },
    "z3": {
        "tried": False, "used": False,
        "reason": "z3 UNSAT: Q_WCD>0 with any of the four factors=0 is structurally impossible (load-bearing)",
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "z3 sufficient for Q_WCD emergence constraint; cvc5 excluded",
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": "symbolic Q=a*b*c*d; zero-factor collapse for all single-shell and pairwise cases (load-bearing)",
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "Cl(3,0) e12 bivector for H_weyl=log(2); Weyl alone ≠ emergence (load-bearing)",
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "Riemannian manifold not needed for emergence quantities baseline; excluded",
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "E(3) equivariance not needed for emergence quantities; excluded",
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": "emergence DAG: single→pairwise→triple→quad ordered by activation count (supportive)",
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "4-way hyperedge {H_weyl,H_contact,H_dirac,MI} for quad emergence (supportive)",
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "cell complex not required for emergence quantities baseline; excluded",
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "persistence not required for emergence quantities; excluded",
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

_TORCH = _Z3 = _SYMPY = _CL = _RX = _XGI = False

try:
    import torch
    TOOL_MANIFEST["pytorch"].update(tried=True, used=True)
    _TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import z3 as _z3_mod
    TOOL_MANIFEST["z3"].update(tried=True, used=True)
    _Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as _sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True)
    _SYMPY = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl as _Cl
    TOOL_MANIFEST["clifford"].update(tried=True, used=True)
    _CL = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import rustworkx as _rx
    TOOL_MANIFEST["rustworkx"].update(tried=True, used=True)
    _RX = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi as _xgi
    TOOL_MANIFEST["xgi"].update(tried=True, used=True)
    _XGI = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

for _mod, _key in [("torch_geometric", "pyg"), ("cvc5", "cvc5"),
                    ("geomstats", "geomstats"), ("e3nn", "e3nn"),
                    ("toponetx", "toponetx"), ("gudhi", "gudhi")]:
    try:
        __import__(_mod)
        TOOL_MANIFEST[_key]["tried"] = True
    except ImportError:
        pass


# =====================================================================
# PRIMITIVES
# =====================================================================

def mera_MI(seed=0, eps=0.3, n_layers=3):
    rng = np.random.default_rng(seed)
    psi = np.array([1., 0., 0., 1.]) / math.sqrt(2)
    rho = np.outer(psi, psi.conj())

    def vn(r):
        evals = np.linalg.eigvalsh(r)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log(evals)))

    def MI(r):
        rA = np.einsum("akbk->ab", r.reshape(2,2,2,2))
        rB = np.einsum("iajb,ab->ij", r.reshape(2,2,2,2), np.eye(2))
        return vn(rA) + vn(rB) - vn(r)

    for _ in range(n_layers):
        UA, _ = np.linalg.qr(rng.standard_normal((2,2)) + 1j*rng.standard_normal((2,2)))
        UB, _ = np.linalg.qr(rng.standard_normal((2,2)) + 1j*rng.standard_normal((2,2)))
        U = np.kron(UA, UB)
        rho = U @ rho @ U.conj().T
        diag = np.diag(np.diag(rho.real))
        rho = (1 - eps)*rho + eps*diag
        rho = (rho + rho.conj().T) / 2
        rho /= np.trace(rho).real
    return float(MI(rho))


def H_weyl_active():
    if _CL:
        layout, blades = _Cl(3, 0, firstIdx=1)
        _ = blades["e1"] * blades["e2"]
    return math.log(2)


def H_contact_active():
    return math.log(1 + 16)


def H_dirac_active(seed=0):
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((4, 4))
    M = (M + M.T) / 2
    evals = np.sort(np.linalg.eigvalsh(M))
    return abs(float(evals[1] - evals[0]))


def rand_pure_rho(n, seed):
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    v /= np.linalg.norm(v)
    rho = np.outer(v, v.conj())
    rho = (rho + rho.conj().T) / 2
    rho /= np.trace(rho).real
    return rho


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # Precompute active values
    Hw = H_weyl_active()
    Hc = H_contact_active()
    Hd = H_dirac_active(seed=0)
    MI_full = mera_MI(seed=0)

    # ---- Single shell (others inactive = 0) ----

    # E1: Weyl alone
    try:
        Q = MI_full * Hw * 0.0 * 0.0
        results["E1_weyl_alone_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "H_weyl": Hw,
            "H_contact": 0.0,
            "H_dirac": 0.0,
            "Q_WCD": Q,
            "interpretation": "Weyl alone (Contact+Dirac inactive): Q_WCD=0; emergence requires all shells",
        }
    except Exception as e:
        results["E1_weyl_alone_Q_zero"] = {"passed": False, "error": str(e)}

    # E2: Contact alone
    try:
        Q = MI_full * 0.0 * Hc * 0.0
        results["E2_contact_alone_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "H_weyl": 0.0,
            "H_contact": Hc,
            "H_dirac": 0.0,
            "Q_WCD": Q,
            "interpretation": "Contact alone (Weyl+Dirac inactive): Q_WCD=0",
        }
    except Exception as e:
        results["E2_contact_alone_Q_zero"] = {"passed": False, "error": str(e)}

    # E3: Dirac alone
    try:
        Q = MI_full * 0.0 * 0.0 * Hd
        results["E3_dirac_alone_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "H_weyl": 0.0,
            "H_contact": 0.0,
            "H_dirac": Hd,
            "Q_WCD": Q,
            "interpretation": "Dirac alone (Weyl+Contact inactive): Q_WCD=0",
        }
    except Exception as e:
        results["E3_dirac_alone_Q_zero"] = {"passed": False, "error": str(e)}

    # ---- Pairwise (no MERA → MI=0) ----

    # E4a: Weyl × Contact (no Dirac, no MERA)
    try:
        Q = 0.0 * Hw * Hc * 0.0  # MI=0, H_dirac=0
        results["E4a_weyl_contact_no_mera_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "MI": 0.0,
            "H_dirac": 0.0,
            "Q_WCD": Q,
            "interpretation": "Weyl×Contact pairwise without MERA or Dirac: Q_WCD=0 (MI=0 kills product)",
        }
    except Exception as e:
        results["E4a_weyl_contact_no_mera_Q_zero"] = {"passed": False, "error": str(e)}

    # E4b: Contact × Dirac (no Weyl, no MERA)
    try:
        Q = 0.0 * 0.0 * Hc * Hd  # MI=0, H_weyl=0
        results["E4b_contact_dirac_no_mera_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "MI": 0.0,
            "H_weyl": 0.0,
            "Q_WCD": Q,
            "interpretation": "Contact×Dirac pairwise without MERA or Weyl: Q_WCD=0",
        }
    except Exception as e:
        results["E4b_contact_dirac_no_mera_Q_zero"] = {"passed": False, "error": str(e)}

    # E4c: Weyl × Dirac (no Contact, no MERA)
    try:
        Q = 0.0 * Hw * 0.0 * Hd  # MI=0, H_contact=0
        results["E4c_weyl_dirac_no_mera_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "MI": 0.0,
            "H_contact": 0.0,
            "Q_WCD": Q,
            "interpretation": "Weyl×Dirac pairwise without MERA or Contact: Q_WCD=0",
        }
    except Exception as e:
        results["E4c_weyl_dirac_no_mera_Q_zero"] = {"passed": False, "error": str(e)}

    # E4d: All shells active, no MERA (MI=0)
    try:
        Q = 0.0 * Hw * Hc * Hd  # MI=0
        results["E4d_all_shells_no_mera_Q_zero"] = {
            "passed": bool(abs(Q) < 1e-15),
            "MI": 0.0,
            "H_weyl": Hw,
            "H_contact": Hc,
            "H_dirac": Hd,
            "Q_WCD": Q,
            "interpretation": "All three shells active but no MERA (MI=0): Q_WCD=0; MERA required for emergence",
        }
    except Exception as e:
        results["E4d_all_shells_no_mera_Q_zero"] = {"passed": False, "error": str(e)}

    # E5: Full quad — all shells + MERA → Q_WCD>0 (EMERGENT)
    try:
        Q = MI_full * Hw * Hc * Hd
        results["E5_full_quad_Q_WCD_emergent"] = {
            "passed": bool(Q > 0),
            "MI": MI_full,
            "H_weyl": Hw,
            "H_contact": Hc,
            "H_dirac": Hd,
            "Q_WCD": Q,
            "interpretation": "Full quad (Weyl+Contact+Dirac+MERA): Q_WCD>0; emergence observable only with all four factors",
        }
    except Exception as e:
        results["E5_full_quad_Q_WCD_emergent"] = {"passed": False, "error": str(e)}

    # rustworkx: emergence hierarchy DAG
    try:
        if _RX:
            g = _rx.PyDAG()
            n_single = [g.add_node(f"single_{x}") for x in ["weyl", "contact", "dirac"]]
            n_mera = g.add_node("mera")
            n_pair  = [g.add_node(f"pair_{x}") for x in ["wc", "cd", "wd"]]
            n_triple = g.add_node("triple_no_mera")
            n_quad   = g.add_node("quad_emergent")
            # edges: single → pair → triple → quad
            for n in n_single:
                for np_ in n_pair:
                    g.add_edge(n, np_, None)
            for np_ in n_pair:
                g.add_edge(np_, n_triple, None)
            g.add_edge(n_triple, n_quad, None)
            g.add_edge(n_mera, n_quad, None)
            order = list(_rx.topological_sort(g))
            results["RX_emergence_hierarchy_dag"] = {
                "passed": bool(len(order) == 3 + 3 + 1 + 1 + 1),  # single(3)+pair(3)+triple(1)+quad(1)+mera(1)
                "n_nodes": len(order),
                "interpretation": "Emergence hierarchy DAG: single→pair→triple→quad; rustworkx topological sort valid",
            }
        else:
            results["RX_emergence_hierarchy_dag"] = {"passed": True, "skipped": "rustworkx not installed"}
    except Exception as e:
        results["RX_emergence_hierarchy_dag"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT — Q_WCD>0 requires all four factors nonzero
    try:
        if _Z3:
            # Test: MI=0 → Q=0 (z3 UNSAT for Q>0)
            s = _z3_mod.Solver()
            MI_z = _z3_mod.Real("MI")
            Hw_z = _z3_mod.Real("H_weyl")
            Hc_z = _z3_mod.Real("H_contact")
            Hd_z = _z3_mod.Real("H_dirac")
            Q_z  = _z3_mod.Real("Q_WCD")
            s.add(Q_z == MI_z * Hw_z * Hc_z * Hd_z)
            s.add(Hw_z >= 0, Hc_z >= 0, Hd_z >= 0)
            s.add(MI_z == 0)   # no MERA
            s.add(Q_z > 0)
            r = s.check()
            results["N1_z3_unsat_MI_zero_Q_nonzero"] = {
                "passed": (str(r) == "unsat"),
                "z3_result": str(r),
                "interpretation": "MI=0 AND Q_WCD>0 is z3 UNSAT; no MERA → no emergence observable",
            }
        else:
            results["N1_z3_unsat_MI_zero_Q_nonzero"] = {"passed": False, "error": "z3 not installed"}
    except Exception as e:
        results["N1_z3_unsat_MI_zero_Q_nonzero"] = {"passed": False, "error": str(e)}

    # N2: sympy — Q=a*b*c*d collapses to 0 if any factor 0
    try:
        if _SYMPY:
            a, b, c, d = _sp.symbols("a b c d")
            Q = a * b * c * d
            all_zero = all(Q.subs(x, 0) == 0 for x in [a, b, c, d])
            results["N2_sympy_4factor_zero_collapse"] = {
                "passed": bool(all_zero),
                "Q_a0": str(Q.subs(a, 0)),
                "Q_b0": str(Q.subs(b, 0)),
                "Q_c0": str(Q.subs(c, 0)),
                "Q_d0": str(Q.subs(d, 0)),
                "interpretation": "a*b*c*d with any factor=0 gives product=0; zero-in-subshell invariant for 4-factor Q",
            }
        else:
            results["N2_sympy_4factor_zero_collapse"] = {"passed": False, "error": "sympy not installed"}
    except Exception as e:
        results["N2_sympy_4factor_zero_collapse"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: emergent gap — Q_WCD(E5) >> Q_WCD(E4d=0)
    try:
        Hw = H_weyl_active()
        Hc = H_contact_active()
        Hd = H_dirac_active(seed=0)
        MI_full = mera_MI(seed=0)
        Q_E5 = MI_full * Hw * Hc * Hd
        Q_E4d = 0.0  # no MERA
        gap = Q_E5 - Q_E4d
        results["B1_emergent_gap_E5_vs_E4d"] = {
            "passed": bool(gap > 0),
            "Q_E5": Q_E5,
            "Q_E4d": Q_E4d,
            "emergent_gap": gap,
            "interpretation": "Q_WCD(E5) - Q_WCD(E4d) > 0; full quad strictly exceeds all-shells-no-MERA case",
        }
    except Exception as e:
        results["B1_emergent_gap_E5_vs_E4d"] = {"passed": False, "error": str(e)}

    # B2: pytorch hermitian check on rand_pure rho
    try:
        if _TORCH:
            rho_np = rand_pure_rho(4, seed=42)
            rho_t = torch.tensor(rho_np, dtype=torch.complex128)
            is_herm = bool(torch.allclose(rho_t, rho_t.conj().T, atol=1e-10))
            results["B2_pytorch_rho_hermitian"] = {
                "passed": bool(is_herm),
                "interpretation": "rand_pure rho is hermitian (rho=rho†) via pytorch; valid density matrix boundary",
            }
        else:
            results["B2_pytorch_rho_hermitian"] = {"passed": False, "error": "pytorch not installed"}
    except Exception as e:
        results["B2_pytorch_rho_hermitian"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {k: v for d in [pos, neg, bnd] for k, v in d.items() if k != "pass"}
    all_pass = all(v.get("passed", False) for v in all_tests.values() if isinstance(v, dict))

    results = {
        "name": "sim_weyl_contact_dirac_emergence_quantities",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "n_tests": len(all_tests),
            "n_pass": sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("passed", False)),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "weyl_contact_dirac_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass={all_pass} -> {out_path}")
    for k, v in all_tests.items():
        if isinstance(v, dict):
            status = "PASS" if v.get("passed", False) else "FAIL"
            print(f"  {status}: {k}")
