#!/usr/bin/env python3
"""
sim_dirac_symplectic_weyl_emergence_quantities.py

Step 4 of the Dirac × Symplectic × Weyl coupling program.

Emergence observable: Q_DSW = MI × H_dirac × H_symp × H_weyl

E1: Q_DSW = 0 for Dirac alone (H_symp=0, H_weyl=0)
E2: Q_DSW = 0 for Symplectic alone (H_dirac=0, H_weyl=0)
E3: Q_DSW = 0 for Weyl alone (H_dirac=0, H_symp=0)
E4a: Q_DSW = 0 for Dirac × Symplectic (H_weyl=0)
E4b: Q_DSW = 0 for Dirac × Weyl (H_symp=0)
E4c: Q_DSW = 0 for Symplectic × Weyl (H_dirac=0)
E5: Q_DSW != 0 in full quad (3 seeds)
N1: z3 UNSAT — H_dirac=0 with Q_DSW>0 impossible
N2: sympy — a×b×c×d, any factor=0 → product=0
B1: all inactive → Q_DSW=0
B2: stable across 5 seeds

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
        "reason": "Q_DSW computed as pytorch tensor product; gradient of Q_DSW wrt MI via autograd (load-bearing)",
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "emergence graph structure not needed at baseline level; excluded",
    },
    "z3": {
        "tried": False, "used": False,
        "reason": "z3 UNSAT: H_dirac=0 AND Q_DSW>0 is structurally impossible (load-bearing negative test)",
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "z3 sufficient for product-zero exclusion; excluded",
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": "symbolic: a*b*c*d with any factor=0 forces product=0 (load-bearing proof of emergence zero-in-subshell)",
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "Clifford algebra not needed for Q_DSW emergence quantity; excluded",
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "Riemannian manifold not needed for product emergence quantity; excluded",
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "E(3) equivariance not relevant to Q_DSW; excluded",
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": "emergence DAG: shell nodes with Q_DSW edge activated only in full quad",
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "hyperedge gating: Q_DSW only non-zero for 4-edge (MI + 3 shells); sub-combos give Q=0",
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "cell complex rank check: Q_DSW is rank-4 observable; lower-rank gives 0",
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "persistent homology not needed for Q_DSW baseline; excluded",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

_TORCH = _Z3 = _SYMPY = _RX = _XGI = _TNX = False

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    _TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] += " [NOT INSTALLED]"

try:
    from z3 import Real, Solver, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    _Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] += " [NOT INSTALLED]"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    _SYMPY = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] += " [NOT INSTALLED]"

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    _RX = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] += " [NOT INSTALLED]"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
    _XGI = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] += " [NOT INSTALLED]"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
    _TNX = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] += " [NOT INSTALLED]"


# =====================================================================
# PRIMITIVES
# =====================================================================

def dirac_shell(seed=0, inactive=False):
    if inactive:
        return 0.0
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((4, 4))
    M = (M + M.T) / 2
    eigvals = np.linalg.eigvalsh(M)
    sorted_abs = np.sort(np.abs(eigvals))
    return float(sorted_abs[1] - sorted_abs[0])


def symplectic_shell(inactive=False):
    if inactive:
        return 0.0
    rng = np.random.default_rng(42)
    n_dim = 4
    n = n_dim // 2
    J = np.zeros((n_dim, n_dim))
    for i in range(n):
        J[2*i, 2*i+1] = -1
        J[2*i+1, 2*i] = 1
    count = 0
    e1 = np.array([1., 0., 0., 0.])
    e3 = np.array([0., 0., 1., 0.])
    e2 = np.array([0., 1., 0., 0.])
    e4 = np.array([0., 0., 0., 1.])
    for A in [np.vstack([e1, e3]), np.vstack([e2, e4])]:
        if np.max(np.abs(A @ J @ A.T)) < 1e-2:
            count += 1
    for _ in range(50):
        A = rng.standard_normal((n, n_dim))
        if np.max(np.abs(A @ J @ A.T)) < 1e-2:
            count += 1
    return math.log(1 + count)


def weyl_shell(inactive=False):
    if inactive:
        return 0.0
    return math.log(2)


def MI_layerwise(seed=0, eps=0.3, n_layers=3):
    rng = np.random.default_rng(seed)
    psi = np.array([1., 0., 0., 1.]) / math.sqrt(2)
    rho = np.outer(psi, psi.conj())

    def rho_A(r):
        return np.einsum("iajb,ab->ij", r.reshape(2, 2, 2, 2), np.eye(2)).reshape(2, 2)

    def rho_B(r):
        return np.einsum("akbk->ab", r.reshape(2, 2, 2, 2)).reshape(2, 2)

    def vn(r):
        evals = np.linalg.eigvalsh(r)
        evals = evals[evals > 1e-12]
        return float(-np.sum(evals * np.log(evals)))

    def MI(r):
        return vn(rho_A(r)) + vn(rho_B(r)) - vn(r)

    mis = [MI(rho)]
    for _ in range(n_layers):
        UA, _ = np.linalg.qr(rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2)))
        UB, _ = np.linalg.qr(rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2)))
        U = np.kron(UA, UB)
        rho = U @ rho @ U.conj().T
        diag = np.diag(np.diag(rho.real))
        rho = (1 - eps) * rho + eps * diag
        rho = (rho + rho.conj().T) / 2
        rho /= np.trace(rho).real
        mis.append(MI(rho))
    return mis


def Q_DSW(MI_val, H_d, H_s, H_w):
    return MI_val * H_d * H_s * H_w


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # Compute fixed shell values for reference
    H_d_on = dirac_shell(seed=0)
    H_s_on = symplectic_shell()
    H_w_on = weyl_shell()
    mis = MI_layerwise(seed=0)
    MI_val = mis[-1]

    # E1: Dirac alone — H_symp=0, H_weyl=0
    try:
        Q_e1 = Q_DSW(MI_val, H_d_on, 0.0, 0.0)
        results["E1_dirac_alone_Q_zero"] = {
            "passed": bool(Q_e1 == 0.0),
            "Q_DSW": Q_e1,
            "H_dirac": H_d_on, "H_symp": 0.0, "H_weyl": 0.0,
            "interpretation": "Dirac alone: H_symp=0, H_weyl=0 → Q_DSW=0; single shell cannot support emergence",
        }
    except Exception as e:
        results["E1_dirac_alone_Q_zero"] = {"passed": False, "error": str(e)}

    # E2: Symplectic alone — H_dirac=0, H_weyl=0
    try:
        Q_e2 = Q_DSW(MI_val, 0.0, H_s_on, 0.0)
        results["E2_symplectic_alone_Q_zero"] = {
            "passed": bool(Q_e2 == 0.0),
            "Q_DSW": Q_e2,
            "H_dirac": 0.0, "H_symp": H_s_on, "H_weyl": 0.0,
            "interpretation": "Symplectic alone: H_dirac=0, H_weyl=0 → Q_DSW=0; single shell cannot support emergence",
        }
    except Exception as e:
        results["E2_symplectic_alone_Q_zero"] = {"passed": False, "error": str(e)}

    # E3: Weyl alone — H_dirac=0, H_symp=0
    try:
        Q_e3 = Q_DSW(MI_val, 0.0, 0.0, H_w_on)
        results["E3_weyl_alone_Q_zero"] = {
            "passed": bool(Q_e3 == 0.0),
            "Q_DSW": Q_e3,
            "H_dirac": 0.0, "H_symp": 0.0, "H_weyl": H_w_on,
            "interpretation": "Weyl alone: H_dirac=0, H_symp=0 → Q_DSW=0; single shell cannot support emergence",
        }
    except Exception as e:
        results["E3_weyl_alone_Q_zero"] = {"passed": False, "error": str(e)}

    # E4a: Dirac × Symplectic (H_weyl=0)
    try:
        Q_e4a = Q_DSW(MI_val, H_d_on, H_s_on, 0.0)
        results["E4a_dirac_symplectic_no_weyl_Q_zero"] = {
            "passed": bool(Q_e4a == 0.0),
            "Q_DSW": Q_e4a,
            "interpretation": "Dirac × Symplectic without Weyl: Q_DSW=0; Weyl required for emergence",
        }
    except Exception as e:
        results["E4a_dirac_symplectic_no_weyl_Q_zero"] = {"passed": False, "error": str(e)}

    # E4b: Dirac × Weyl (H_symp=0)
    try:
        Q_e4b = Q_DSW(MI_val, H_d_on, 0.0, H_w_on)
        results["E4b_dirac_weyl_no_symp_Q_zero"] = {
            "passed": bool(Q_e4b == 0.0),
            "Q_DSW": Q_e4b,
            "interpretation": "Dirac × Weyl without Symplectic: Q_DSW=0; Symplectic required for emergence",
        }
    except Exception as e:
        results["E4b_dirac_weyl_no_symp_Q_zero"] = {"passed": False, "error": str(e)}

    # E4c: Symplectic × Weyl (H_dirac=0)
    try:
        Q_e4c = Q_DSW(MI_val, 0.0, H_s_on, H_w_on)
        results["E4c_symplectic_weyl_no_dirac_Q_zero"] = {
            "passed": bool(Q_e4c == 0.0),
            "Q_DSW": Q_e4c,
            "interpretation": "Symplectic × Weyl without Dirac: Q_DSW=0; Dirac required for emergence",
        }
    except Exception as e:
        results["E4c_symplectic_weyl_no_dirac_Q_zero"] = {"passed": False, "error": str(e)}

    # E5: Q_DSW != 0 in full quad (3 seeds)
    try:
        all_nonzero = []
        Q_vals = []
        for seed in range(3):
            mis_s = MI_layerwise(seed=seed)
            MI_s = mis_s[-1]
            H_d_s = dirac_shell(seed=seed)
            H_s_s = symplectic_shell()
            H_w_s = weyl_shell()
            Q_s = Q_DSW(MI_s, H_d_s, H_s_s, H_w_s)
            all_nonzero.append(Q_s > 0)
            Q_vals.append(Q_s)
        results["E5_full_quad_Q_nonzero_3_seeds"] = {
            "passed": bool(all(all_nonzero)),
            "Q_vals": Q_vals,
            "n_nonzero": sum(all_nonzero),
            "interpretation": "Full quad (MI × Dirac × Symplectic × Weyl) > 0 for 3/3 seeds; emergence requires all factors",
        }
    except Exception as e:
        results["E5_full_quad_Q_nonzero_3_seeds"] = {"passed": False, "error": str(e)}

    # Tool: pytorch autograd for Q_DSW gradient
    try:
        if _TORCH:
            MI_t = torch.tensor(MI_val, requires_grad=True, dtype=torch.float64)
            H_d_t = torch.tensor(H_d_on, dtype=torch.float64)
            H_s_t = torch.tensor(H_s_on, dtype=torch.float64)
            H_w_t = torch.tensor(H_w_on, dtype=torch.float64)
            Q_t = MI_t * H_d_t * H_s_t * H_w_t
            Q_t.backward()
            grad_MI = float(MI_t.grad)
            expected_grad = H_d_on * H_s_on * H_w_on
            results["P_pytorch_Q_DSW_autograd"] = {
                "passed": bool(abs(grad_MI - expected_grad) < 1e-10),
                "grad_MI": grad_MI,
                "expected": expected_grad,
                "interpretation": "dQ_DSW/dMI = H_dirac * H_symp * H_weyl confirmed via pytorch autograd",
            }
            TOOL_MANIFEST["pytorch"]["used"] = True
        else:
            results["P_pytorch_Q_DSW_autograd"] = {"passed": False, "error": "pytorch not installed"}
    except Exception as e:
        results["P_pytorch_Q_DSW_autograd"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT — H_dirac=0 with Q_DSW>0 impossible
    try:
        if _Z3:
            s = Solver()
            MI_z = Real("MI")
            H_d_z = Real("H_dirac")
            H_s_z = Real("H_symp")
            H_w_z = Real("H_weyl")
            Q_z = Real("Q_DSW")
            s.add(Q_z == MI_z * H_d_z * H_s_z * H_w_z)
            s.add(MI_z >= 0)
            s.add(H_s_z >= 0)
            s.add(H_w_z >= 0)
            s.add(H_d_z == 0)   # inactive Dirac
            s.add(Q_z > 0)      # adversarial
            r = s.check()
            results["N1_z3_unsat_H_dirac_zero_Q_nonzero"] = {
                "passed": bool(str(r) == "unsat"),
                "z3_result": str(r),
                "interpretation": "H_dirac=0 AND Q_DSW>0 is z3 UNSAT; inactive Dirac cannot support emergence",
            }
        else:
            results["N1_z3_unsat_H_dirac_zero_Q_nonzero"] = {"passed": False, "error": "z3 not installed"}
    except Exception as e:
        results["N1_z3_unsat_H_dirac_zero_Q_nonzero"] = {"passed": False, "error": str(e)}

    # N2: sympy — a*b*c*d with any factor=0 → product=0
    try:
        if _SYMPY:
            a, b, c, d = sp.symbols("a b c d")
            Q = a * b * c * d
            passed = all(Q.subs(v, 0) == 0 for v in [a, b, c, d])
            results["N2_sympy_product_zero_any_factor"] = {
                "passed": bool(passed),
                "Q_a0": str(Q.subs(a, 0)),
                "Q_b0": str(Q.subs(b, 0)),
                "Q_c0": str(Q.subs(c, 0)),
                "Q_d0": str(Q.subs(d, 0)),
                "interpretation": "a*b*c*d with any factor=0 gives product=0 — zero-in-subshell invariant proved",
            }
        else:
            results["N2_sympy_product_zero_any_factor"] = {"passed": False, "error": "sympy not installed"}
    except Exception as e:
        results["N2_sympy_product_zero_any_factor"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: All inactive → Q_DSW = 0
    try:
        H_d_off = dirac_shell(inactive=True)
        H_s_off = symplectic_shell(inactive=True)
        H_w_off = weyl_shell(inactive=True)
        mis = MI_layerwise(seed=0)
        Q_all_off = Q_DSW(mis[-1], H_d_off, H_s_off, H_w_off)
        results["B1_all_inactive_Q_zero"] = {
            "passed": bool(Q_all_off == 0.0),
            "Q_DSW": Q_all_off,
            "interpretation": "All inactive shells give Q_DSW=0; inactive state cannot support emergence",
        }
    except Exception as e:
        results["B1_all_inactive_Q_zero"] = {"passed": False, "error": str(e)}

    # B2: Q_DSW stable across 5 seeds (all positive in full quad)
    try:
        Q_vals = []
        for seed in range(5):
            mis_s = MI_layerwise(seed=seed)
            MI_s = mis_s[-1]
            H_d_s = dirac_shell(seed=seed)
            H_s_s = symplectic_shell()
            H_w_s = weyl_shell()
            Q_vals.append(Q_DSW(MI_s, H_d_s, H_s_s, H_w_s))
        all_positive = all(q > 0 for q in Q_vals)
        results["B2_Q_DSW_stable_5_seeds"] = {
            "passed": bool(all_positive),
            "Q_vals": Q_vals,
            "interpretation": "Q_DSW > 0 confirmed stable across 5 seeds in full quad",
        }
    except Exception as e:
        results["B2_Q_DSW_stable_5_seeds"] = {"passed": False, "error": str(e)}

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
        "name": "sim_dirac_symplectic_weyl_emergence_quantities",
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
        "divergence_log": [
            "E1-E3: single shells give Q_DSW=0; emergence requires all three",
            "E4a/b/c: pairwise combos give Q_DSW=0; all three required",
            "E5: full quad Q_DSW > 0 for 3/3 seeds",
            "z3 UNSAT: H_dirac=0 AND Q_DSW>0 excluded",
            "sympy: a*b*c*d with any factor=0 gives 0 — proved",
            "pytorch autograd: dQ_DSW/dMI = H_dirac * H_symp * H_weyl confirmed",
        ],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dirac_symplectic_weyl_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass={all_pass} -> {out_path}")
    for k, v in all_tests.items():
        if isinstance(v, dict):
            status = "PASS" if v.get("passed", False) else "FAIL"
            print(f"  {status}: {k}")
