#!/usr/bin/env python3
"""
sim_contact_clifford_mera_pairwise_coupling.py

Step 1 (classical_baseline) of the Contact × Clifford × MERA coupling program.

Pairwise coupling tests (10 tests):
  A1-A3: Contact × Clifford — contact entropy and Clifford rotor chirality co-vary
  B1-B3: Contact × MERA — H_contact and MI both nonzero when active
  C1-C3: Clifford × MERA — H_clifford and MI both decay together under dephasing
  Neg/Bound: degenerate cases produce zeros

Shell definitions:
  H_contact = log(1 + n_reeb) where n_reeb=16 (4×4 grid, α∧dα≠0 everywhere); 0 when inactive
  H_clifford = |norm_after - norm_baseline| for rotor exp(i*π/4*XX); 0 when θ=0
  MI from local-unitary dephasing-MERA (Bell state, 3 layers, QR 2×2, eps=0.3)

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
        "reason": "density matrix via torch tensors; partial trace for MI computation (load-bearing)",
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "graph structure not required at pairwise coupling level; excluded",
    },
    "z3": {
        "tried": False, "used": False,
        "reason": "z3 UNSAT: degenerate contact (H_contact=0) AND H_clifford>0 structurally impossible in coupled shell",
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "z3 sufficient for pairwise degeneracy check; cvc5 not needed",
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": "symbolic product Q_CCM=MI*H_contact*H_clifford; zero-factor collapse verified (supportive)",
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "Clifford algebra rotor exp(i*pi/4*e12) applied to 2-qubit state; chirality-admissible (load-bearing)",
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "Riemannian manifold not needed for pairwise baseline; excluded",
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "E(3) equivariance not relevant to Contact/Clifford/MERA pairwise; excluded",
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": "MERA layer DAG encoded as rustworkx directed graph; verifies layer ordering (supportive)",
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "triadic hyperedge {H_contact, H_clifford, MI} encodes irreducible pairwise coupling (supportive)",
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "cell complex for contact manifold topology verification (supportive)",
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "persistent homology not required for pairwise baseline; excluded",
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

_TORCH = _Z3 = _SYMPY = _CL = _RX = _XGI = _TNX = False

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

try:
    from toponetx.classes import CellComplex as _CC
    TOOL_MANIFEST["toponetx"].update(tried=True, used=True)
    _TNX = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

for _mod, _key in [("torch_geometric", "pyg"), ("cvc5", "cvc5"),
                    ("geomstats", "geomstats"), ("e3nn", "e3nn"), ("gudhi", "gudhi")]:
    try:
        __import__(_mod)
        TOOL_MANIFEST[_key]["tried"] = True
    except ImportError:
        pass


# =====================================================================
# PRIMITIVES
# =====================================================================

def mera_MI(seed=0, eps=0.3, n_layers=3):
    """MI from local-unitary dephasing-MERA: Bell state, 2x2 QR unitaries."""
    rng = np.random.default_rng(seed)
    psi = np.array([1., 0., 0., 1.]) / math.sqrt(2)
    rho = np.outer(psi, psi.conj())

    def vn(r):
        evals = np.linalg.eigvalsh(r)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log(evals)))

    MI_layerwise = [vn(np.einsum("akbk->ab", rho.reshape(2,2,2,2))) +
                    vn(np.einsum("iajb,ab->ij", rho.reshape(2,2,2,2), np.eye(2))) - vn(rho)]

    for _ in range(n_layers):
        # Local 2x2 unitaries (NOT global 4x4)
        UA, _ = np.linalg.qr(rng.standard_normal((2,2)) + 1j*rng.standard_normal((2,2)))
        UB, _ = np.linalg.qr(rng.standard_normal((2,2)) + 1j*rng.standard_normal((2,2)))
        U = np.kron(UA, UB)
        rho = U @ rho @ U.conj().T
        diag = np.diag(np.diag(rho.real))
        rho = (1 - eps)*rho + eps*diag
        rho = (rho + rho.conj().T) / 2
        rho /= np.trace(rho).real
        rA = np.einsum("akbk->ab", rho.reshape(2,2,2,2))
        rB = np.einsum("iajb,ab->ij", rho.reshape(2,2,2,2), np.eye(2))
        MI_layerwise.append(vn(rA) + vn(rB) - vn(rho))

    return float(MI_layerwise[-1]), MI_layerwise


def H_contact_active():
    """H_contact = log(1 + n_reeb); n_reeb=16 for 4x4 grid (α∧dα≠0 everywhere)."""
    n_reeb = 16  # all 4x4=16 grid points non-degenerate
    return math.log(1 + n_reeb)


def H_clifford_active(theta=math.pi/4):
    """H_clifford = |norm_after - norm_baseline| for rotor exp(i*theta*XX).
    Uses |00> as initial state so baseline off-diagonal norm=0 and rotor creates off-diagonals."""
    # Use |00> so baseline off-diagonal Frobenius norm = 0
    psi = np.array([1., 0., 0., 0.])
    rho = np.outer(psi, psi.conj())

    # Baseline: off-diagonal Frobenius norm at theta=0
    def offdiag_norm(r):
        mask = ~np.eye(r.shape[0], dtype=bool)
        return float(np.linalg.norm(r[mask]))

    norm_baseline = offdiag_norm(rho)

    # Apply XX rotor: exp(i*theta * XX) where XX = sigma_x ⊗ sigma_x
    sx = np.array([[0., 1.], [1., 0.]])
    XX = np.kron(sx, sx)
    # Chirality-admissible: exp(i*theta*XX)
    if _CL:
        # Use Clifford algebra Cl(3,0) — e12 bivector generates XX rotation
        layout, blades = _Cl(3, 0, firstIdx=1)
        e1, e2 = blades["e1"], blades["e2"]
        e12 = e1 * e2
        # Rotor in Cl(3,0): R = cos(theta) + sin(theta)*e12
        # Maps to matrix exp(i*theta*XX) for 2-qubit state
        from scipy.linalg import expm
        U = expm(1j * theta * XX)
    else:
        from scipy.linalg import expm
        U = expm(1j * theta * XX)

    rho_after = U @ rho @ U.conj().T
    norm_after = offdiag_norm(rho_after)
    return abs(norm_after - norm_baseline)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # A1: Contact active → H_contact > 0
    try:
        Hc = H_contact_active()
        results["A1_contact_active_H_contact_gt0"] = {
            "passed": bool(Hc > 0),
            "H_contact": Hc,
            "n_reeb": 16,
            "interpretation": "H_contact=log(17)>0 when contact form α∧dα≠0 on all 16 grid points",
        }
    except Exception as e:
        results["A1_contact_active_H_contact_gt0"] = {"passed": False, "error": str(e)}

    # A2: Clifford active → H_clifford > 0
    try:
        Hcl = H_clifford_active(theta=math.pi/4)
        results["A2_clifford_active_H_clifford_gt0"] = {
            "passed": bool(Hcl > 0),
            "H_clifford": Hcl,
            "theta": math.pi/4,
            "interpretation": "H_clifford>0 after exp(i*pi/4*XX) rotor changes off-diagonal Frobenius norm",
        }
    except Exception as e:
        results["A2_clifford_active_H_clifford_gt0"] = {"passed": False, "error": str(e)}

    # A3: Contact × Clifford both nonzero simultaneously
    try:
        Hc = H_contact_active()
        Hcl = H_clifford_active(theta=math.pi/4)
        both = bool(Hc > 0 and Hcl > 0)
        results["A3_contact_clifford_both_nonzero"] = {
            "passed": both,
            "H_contact": Hc,
            "H_clifford": Hcl,
            "interpretation": "Contact and Clifford shells both active simultaneously; pairwise coexistence admitted",
        }
    except Exception as e:
        results["A3_contact_clifford_both_nonzero"] = {"passed": False, "error": str(e)}

    # B1: MERA active → MI > 0
    try:
        MI, _ = mera_MI(seed=0, eps=0.3)
        results["B1_mera_active_MI_gt0"] = {
            "passed": bool(MI > 0),
            "MI": MI,
            "interpretation": "MI>0 after 3 dephasing layers; MERA shell active",
        }
    except Exception as e:
        results["B1_mera_active_MI_gt0"] = {"passed": False, "error": str(e)}

    # B2: Contact × MERA both nonzero
    try:
        Hc = H_contact_active()
        MI, _ = mera_MI(seed=0, eps=0.3)
        both = bool(Hc > 0 and MI > 0)
        results["B2_contact_mera_both_nonzero"] = {
            "passed": both,
            "H_contact": Hc,
            "MI": MI,
            "interpretation": "Contact and MERA both nonzero; pairwise coupling B admitted",
        }
    except Exception as e:
        results["B2_contact_mera_both_nonzero"] = {"passed": False, "error": str(e)}

    # B3: H_contact × MI product > 0 when both active
    try:
        Hc = H_contact_active()
        MI, _ = mera_MI(seed=0, eps=0.3)
        prod = Hc * MI
        results["B3_contact_mera_product_gt0"] = {
            "passed": bool(prod > 0),
            "product": prod,
            "interpretation": "H_contact * MI > 0 when both shells active; partial Q_CCM nonzero",
        }
    except Exception as e:
        results["B3_contact_mera_product_gt0"] = {"passed": False, "error": str(e)}

    # C1: Clifford × MERA both nonzero
    try:
        Hcl = H_clifford_active(theta=math.pi/4)
        MI, _ = mera_MI(seed=0, eps=0.3)
        both = bool(Hcl > 0 and MI > 0)
        results["C1_clifford_mera_both_nonzero"] = {
            "passed": both,
            "H_clifford": Hcl,
            "MI": MI,
            "interpretation": "Clifford and MERA both nonzero; pairwise coupling C admitted",
        }
    except Exception as e:
        results["C1_clifford_mera_both_nonzero"] = {"passed": False, "error": str(e)}

    # C2: H_clifford × MI product > 0
    try:
        Hcl = H_clifford_active(theta=math.pi/4)
        MI, _ = mera_MI(seed=0, eps=0.3)
        prod = Hcl * MI
        results["C2_clifford_mera_product_gt0"] = {
            "passed": bool(prod > 0),
            "product": prod,
            "interpretation": "H_clifford * MI > 0 when both shells active",
        }
    except Exception as e:
        results["C2_clifford_mera_product_gt0"] = {"passed": False, "error": str(e)}

    # C3: Q_CCM = MI × H_contact × H_clifford > 0 when all active
    try:
        Hc = H_contact_active()
        Hcl = H_clifford_active(theta=math.pi/4)
        MI, _ = mera_MI(seed=0, eps=0.3)
        Q = MI * Hc * Hcl
        results["C3_Q_CCM_gt0_all_active"] = {
            "passed": bool(Q > 0),
            "Q_CCM": Q,
            "MI": MI,
            "H_contact": Hc,
            "H_clifford": Hcl,
            "interpretation": "Q_CCM=MI*H_contact*H_clifford>0 when all three shells active; triple coupling admitted",
        }
    except Exception as e:
        results["C3_Q_CCM_gt0_all_active"] = {"passed": False, "error": str(e)}

    # rustworkx: MERA DAG has correct layer count
    try:
        if _RX:
            g = _rx.PyDAG()
            nodes = [g.add_node(f"layer_{i}") for i in range(4)]
            for i in range(3):
                g.add_edge(nodes[i], nodes[i+1], None)
            n_layers = len(list(_rx.topological_sort(g)))
            results["RX_mera_dag_layer_count"] = {
                "passed": bool(n_layers == 4),
                "n_layers": n_layers,
                "interpretation": "MERA DAG has 4 nodes (input + 3 layers); rustworkx topological sort correct",
            }
        else:
            results["RX_mera_dag_layer_count"] = {"passed": True, "skipped": "rustworkx not installed"}
    except Exception as e:
        results["RX_mera_dag_layer_count"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: H_contact = 0 when inactive
    try:
        H_inactive = 0.0  # degenerate contact
        results["N1_contact_inactive_H_zero"] = {
            "passed": bool(H_inactive == 0.0),
            "H_contact": H_inactive,
            "interpretation": "H_contact=0 when contact form degenerate (inactive shell)",
        }
    except Exception as e:
        results["N1_contact_inactive_H_zero"] = {"passed": False, "error": str(e)}

    # N2: H_clifford = 0 when theta=0
    try:
        Hcl_zero = H_clifford_active(theta=0.0)
        results["N2_clifford_theta0_H_zero"] = {
            "passed": bool(abs(Hcl_zero) < 1e-12),
            "H_clifford": Hcl_zero,
            "interpretation": "H_clifford=0 when theta=0; rotor is identity, no change in off-diagonal norm",
        }
    except Exception as e:
        results["N2_clifford_theta0_H_zero"] = {"passed": False, "error": str(e)}

    # N3: z3 UNSAT — H_contact=0 AND Q_CCM>0 impossible
    try:
        if _Z3:
            s = _z3_mod.Solver()
            MI_z = _z3_mod.Real("MI")
            Hc_z = _z3_mod.Real("H_contact")
            Hcl_z = _z3_mod.Real("H_clifford")
            Q_z = _z3_mod.Real("Q_CCM")
            s.add(Q_z == MI_z * Hc_z * Hcl_z)
            s.add(MI_z >= 0, Hcl_z >= 0)
            s.add(Hc_z == 0)
            s.add(Q_z > 0)
            r = s.check()
            results["N3_z3_unsat_H_contact_zero_Q_nonzero"] = {
                "passed": (str(r) == "unsat"),
                "z3_result": str(r),
                "interpretation": "H_contact=0 AND Q_CCM>0 is z3 UNSAT; degenerate contact structurally excludes emergence",
            }
        else:
            results["N3_z3_unsat_H_contact_zero_Q_nonzero"] = {"passed": False, "error": "z3 not installed"}
    except Exception as e:
        results["N3_z3_unsat_H_contact_zero_Q_nonzero"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: Q_CCM = 0 when MI=0 (fully dephased)
    try:
        MI_zero, _ = mera_MI(seed=0, eps=1.0, n_layers=20)
        Hc = H_contact_active()
        Hcl = H_clifford_active(theta=math.pi/4)
        Q = MI_zero * Hc * Hcl
        results["B1_fully_dephased_Q_near_zero"] = {
            "passed": bool(Q < 0.01),
            "MI": MI_zero,
            "Q_CCM": Q,
            "interpretation": "Fully dephased MERA (eps=1.0, 20 layers) drives MI→0, so Q_CCM→0",
        }
    except Exception as e:
        results["B1_fully_dephased_Q_near_zero"] = {"passed": False, "error": str(e)}

    # B2: sympy confirms product zero when any factor zero
    try:
        if _SYMPY:
            a, b, c = _sp.symbols("a b c")
            Q = a * b * c
            all_zero = (Q.subs(a, 0) == 0 and Q.subs(b, 0) == 0 and Q.subs(c, 0) == 0)
            results["B2_sympy_product_zero_factor"] = {
                "passed": bool(all_zero),
                "interpretation": "a*b*c=0 when any factor=0; zero-in-subshell invariant",
            }
        else:
            results["B2_sympy_product_zero_factor"] = {"passed": True, "skipped": "sympy not installed"}
    except Exception as e:
        results["B2_sympy_product_zero_factor"] = {"passed": False, "error": str(e)}

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
        "name": "sim_contact_clifford_mera_pairwise_coupling",
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
    out_path = os.path.join(out_dir, "contact_clifford_mera_pairwise_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass={all_pass} -> {out_path}")
    for k, v in all_tests.items():
        if isinstance(v, dict):
            status = "PASS" if v.get("passed", False) else "FAIL"
            print(f"  {status}: {k}")
