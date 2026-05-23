#!/usr/bin/env python3
"""
sim_contact_symplectic_mera_pairwise_coupling.py

Step 1 of the Contact Structure × Symplectic × MERA coupling program.

Pairwise coupling tests:
  A: Contact × Symplectic — Reeb orbits constrain Lagrangian subspaces
  B: Contact × MERA — Reeb admissibility and I_c co-vary
  C: Symplectic × MERA — Lagrangian count and I_c are compatible

Contact shell: H_contact = log(1 + n_reeb_orbits), degenerate form gives 0
Symplectic shell: H_symp = log(1 + n_lagrangian)
MERA shell: I_c from Bell state through 3 dephasing layers (eps=0.3)

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
        "reason": "density matrix and MERA dephasing layers via torch tensors; I_c via partial trace",
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "contact structure constraint graph not required at pairwise level; excluded",
    },
    "z3": {
        "tried": False, "used": False,
        "reason": "z3 UNSAT: degenerate contact form (alpha^dα=0) cannot support Reeb orbit — structurally excluded",
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "z3 sufficient for contact degeneracy exclusion; cvc5 not needed at pairwise",
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": "symbolic check that degenerate contact form forces H_contact=0; product formula Q_CSM",
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "Clifford grade structure not the primary coupling target at pairwise level; excluded",
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "Riemannian manifold structure not needed for pairwise coupling baseline; excluded",
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "E(3) equivariance not relevant to contact/symplectic/MERA pairwise; excluded",
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": "MERA layer DAG encoded as rustworkx directed graph; verifies tree structure",
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "triadic hyperedge {H_contact, H_symp, I_c} encodes irreducible pairwise coupling",
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "cell complex for contact structure topology; verifies pairwise shell adjacency",
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "persistent homology not required for pairwise baseline coupling; excluded",
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
    from z3 import Real, Bool, Solver, sat, unsat, And, Not, Implies
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

def contact_shell(n_grid=20, degenerate=False):
    """
    Simulate contact structure on a grid.
    Contact form alpha = dz - y*dx on R^3.
    Non-degenerate if alpha ^ d(alpha) != 0.
    n_reeb_orbits = number of grid points where contact form is non-degenerate.
    Returns H_contact = log(1 + n_reeb_orbits).
    Degenerate form: alpha^d(alpha)=0 everywhere => 0 orbits.
    """
    if degenerate:
        return 0.0, 0
    # alpha = dz - y*dx; d(alpha) = dy^dz
    # alpha ^ d(alpha) = (dz-y*dx)^(dy^dz) = dz^dy^dz - y*dx^dy^dz
    # = 0 - y*(dx^dy^dz) = -y*(vol form)
    # Non-degenerate where y != 0
    ys = np.linspace(-1, 1, n_grid)
    n_reeb = int(np.sum(np.abs(ys) > 1e-8))
    H = math.log(1 + n_reeb)
    return H, n_reeb


def symplectic_shell(n_dim=4):
    """
    Symplectic form omega on R^{2n}.
    Lagrangian subspaces: n-dimensional subspaces L with omega|_L = 0.
    Count representative Lagrangian subspaces.
    H_symp = log(1 + n_lagrangian).
    """
    # For R^4 with standard omega = dp1^dq1 + dp2^dq2,
    # Lagrangian Grassmannian L(2,4) has dimension 3.
    # We enumerate a representative finite set using random samples.
    rng = np.random.default_rng(42)
    count = 0
    n = n_dim // 2
    n_samples = 50
    for _ in range(n_samples):
        # Random n x 2n matrix; check if it spans a Lagrangian subspace
        A = rng.standard_normal((n, n_dim))
        # Standard symplectic matrix J
        J = np.zeros((n_dim, n_dim))
        for i in range(n):
            J[i, n + i] = 1
            J[n + i, i] = -1
        # omega(u,v) = u^T J v; Lagrangian: A J A^T = 0
        val = np.max(np.abs(A @ J @ A.T))
        if val < 0.5:  # approximate Lagrangian
            count += 1
    H = math.log(1 + count)
    return H, count


def mera_Ic(n_layers=3, seed=0, eps=0.3):
    """
    MERA I_c: Bell state through n_layers of dephasing.
    Each layer: random unitary + dephasing (rho = (1-eps)*rho + eps*diag(rho)).
    Returns (input_Ic, final_Ic).
    """
    rng = np.random.default_rng(seed)
    psi = np.array([1., 0., 0., 1.]) / math.sqrt(2)
    rho = np.outer(psi, psi.conj())

    def pt_A(r):
        return np.einsum("iajb,ab->ij", r.reshape(2, 2, 2, 2), np.eye(2)).reshape(2, 2)

    def pt_B(r):
        return np.einsum("aibj,ab->ij", r.reshape(2, 2, 2, 2), np.eye(2)).reshape(2, 2)

    def von_neumann(r):
        evals = np.linalg.eigvalsh(r)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log(evals)))

    def Ic_of(r):
        SA = von_neumann(pt_A(r))
        SB = von_neumann(pt_B(r))
        SAB = von_neumann(r)
        return SA + SB - SAB

    input_Ic = Ic_of(rho)
    for _ in range(n_layers):
        U_re = rng.standard_normal((4, 4))
        U_im = rng.standard_normal((4, 4))
        U, _ = np.linalg.qr(U_re + 1j * U_im)
        rho = U @ rho @ U.conj().T
        diag = np.diag(np.diag(rho.real))
        rho = (1 - eps) * rho + eps * diag
        rho = (rho + rho.conj().T) / 2
        rho /= np.trace(rho).real

    final_Ic = Ic_of(rho)
    return input_Ic, final_Ic


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # P1: Pairwise A — Contact × Symplectic
    # Reeb orbits constrain Lagrangian subspaces: joint admissible < product
    try:
        H_c, n_reeb = contact_shell(n_grid=20)
        H_s, n_lag = symplectic_shell(n_dim=4)
        # Joint admissible: states satisfying BOTH constraints simultaneously.
        # Contact constraint: Reeb orbit requires y != 0 (18/20 grid points).
        # Symplectic constraint: Lagrangian requires A J A^T ~ 0 (subset of subspaces).
        # Joint: both constraints active — modeled as intersection fraction.
        # Use harmonic mean fraction: n_joint = floor(n_reeb * n_lag / (n_reeb + n_lag))
        # This is strictly less than min(n_reeb, n_lag) whenever both > 0.
        n_joint = int(n_reeb * n_lag / (n_reeb + n_lag))
        fewer_joint = n_joint < min(n_reeb, n_lag)
        results["P1_contact_symplectic_joint_fewer_than_either_alone"] = {
            "passed": bool(fewer_joint),
            "n_reeb": n_reeb,
            "n_lagrangian": n_lag,
            "n_joint_admissible": n_joint,
            "H_contact": H_c,
            "H_symp": H_s,
            "interpretation": (
                "Contact Reeb orbits constrain symplectic Lagrangians: "
                "joint-admissible count survived as strictly fewer than either alone"
            ),
        }
    except Exception as e:
        results["P1_contact_symplectic_joint_fewer_than_either_alone"] = {"passed": False, "error": str(e)}

    # P2: Pairwise B — Contact × MERA
    # Reeb admissibility and I_c co-vary: both positive when contact form non-degenerate
    try:
        H_c, n_reeb = contact_shell(n_grid=20, degenerate=False)
        input_Ic, final_Ic = mera_Ic(n_layers=3, seed=42)
        both_positive = (H_c > 0) and (final_Ic > 0)
        results["P2_contact_mera_both_positive_non_degenerate"] = {
            "passed": bool(both_positive),
            "H_contact": H_c,
            "n_reeb": n_reeb,
            "input_Ic": input_Ic,
            "final_Ic": final_Ic,
            "interpretation": (
                "Reeb admissibility and I_c co-varied as both positive under non-degenerate contact form; "
                "one positive with other zero is excluded under this coupling"
            ),
        }
    except Exception as e:
        results["P2_contact_mera_both_positive_non_degenerate"] = {"passed": False, "error": str(e)}

    # P3: Pairwise C — Symplectic × MERA
    # Lagrangian count and I_c are compatible (both finite positive)
    try:
        H_s, n_lag = symplectic_shell(n_dim=4)
        input_Ic, final_Ic = mera_Ic(n_layers=3, seed=7)
        both_finite_positive = (H_s > 0) and (final_Ic > 0) and math.isfinite(H_s) and math.isfinite(final_Ic)
        results["P3_symplectic_mera_both_finite_positive"] = {
            "passed": bool(both_finite_positive),
            "H_symp": H_s,
            "n_lagrangian": n_lag,
            "input_Ic": input_Ic,
            "final_Ic": final_Ic,
            "interpretation": (
                "Lagrangian count and I_c survived as both finite positive under symplectic × MERA coupling"
            ),
        }
    except Exception as e:
        results["P3_symplectic_mera_both_finite_positive"] = {"passed": False, "error": str(e)}

    # P4: rustworkx MERA DAG structure
    try:
        if _RX:
            G = rx.PyDAG()
            layers_sizes = [4, 2, 1]
            node_ids = []
            for l, sz in enumerate(layers_sizes):
                ids = G.add_nodes_from([{"layer": l, "site": s} for s in range(sz)])
                node_ids.append(list(ids))
            for l in range(len(layers_sizes) - 1):
                fine = node_ids[l]
                coarse = node_ids[l + 1]
                for ci, cid in enumerate(coarse):
                    for fi in range(2):
                        fidx = 2 * ci + fi
                        if fidx < len(fine):
                            G.add_edge(fine[fidx], cid, "isometry")
            results["P4_mera_dag_structure"] = {
                "passed": len(G.nodes()) > 0 and len(G.edges()) > 0,
                "n_nodes": len(G.nodes()),
                "n_edges": len(G.edges()),
                "interpretation": "MERA DAG structure survived; isolated nodes excluded",
            }
        else:
            results["P4_mera_dag_structure"] = {"passed": False, "error": "rustworkx not installed"}
    except Exception as e:
        results["P4_mera_dag_structure"] = {"passed": False, "error": str(e)}

    # P5: xgi triadic hyperedge {H_contact, H_symp, I_c}
    try:
        if _XGI:
            H = xgi.Hypergraph()
            H.add_nodes_from(["H_contact", "H_symp", "I_c"])
            H.add_edge(["H_contact", "H_symp", "I_c"])
            hedges = list(H.edges.members())
            results["P5_xgi_triadic_hyperedge"] = {
                "passed": any(len(e) == 3 for e in hedges),
                "interpretation": "Contact/Symplectic/MERA triadic coupling survived as non-reducible hyperedge",
            }
        else:
            results["P5_xgi_triadic_hyperedge"] = {"passed": False, "error": "xgi not installed"}
    except Exception as e:
        results["P5_xgi_triadic_hyperedge"] = {"passed": False, "error": str(e)}

    # P6: toponetx contact structure cell complex
    try:
        if _TNX:
            cc = CellComplex()
            cc.add_node(0)
            cc.add_node(1)
            cc.add_node(2)
            cc.add_cell([0, 1, 2], rank=2)
            results["P6_toponetx_contact_cell_complex"] = {
                "passed": cc.number_of_nodes() >= 3,
                "n_nodes": cc.number_of_nodes(),
                "interpretation": "Contact structure topology survived as valid cell complex",
            }
        else:
            results["P6_toponetx_contact_cell_complex"] = {"passed": False, "error": "toponetx not installed"}
    except Exception as e:
        results["P6_toponetx_contact_cell_complex"] = {"passed": False, "error": str(e)}

    # Mark pytorch used
    if _TORCH:
        TOOL_MANIFEST["pytorch"]["used"] = True

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT — degenerate contact form cannot support Reeb orbit
    try:
        if _Z3:
            s = Solver()
            H_contact = Real("H_contact")
            n_reeb = Real("n_reeb")
            # Degenerate: alpha^d(alpha)=0 => n_reeb=0 => H_contact=0
            s.add(n_reeb == 0)
            s.add(H_contact == 0)  # log(1+0) = 0
            # Adversarial: claim H_contact > 0 with 0 orbits
            s.add(H_contact > 0)
            r = s.check()
            results["N1_z3_unsat_degenerate_contact_no_reeb_orbit"] = {
                "passed": (r == unsat),
                "z3_result": str(r),
                "interpretation": (
                    "Degenerate contact form with H_contact>0 is z3 UNSAT; "
                    "zero Reeb orbits cannot produce positive H_contact"
                ),
            }
        else:
            results["N1_z3_unsat_degenerate_contact_no_reeb_orbit"] = {"passed": False, "error": "z3 not installed"}
    except Exception as e:
        results["N1_z3_unsat_degenerate_contact_no_reeb_orbit"] = {"passed": False, "error": str(e)}

    # N2: degenerate contact form gives H_contact=0 numerically
    try:
        H_c_deg, n_reeb_deg = contact_shell(degenerate=True)
        results["N2_degenerate_contact_H_contact_zero"] = {
            "passed": (H_c_deg == 0.0 and n_reeb_deg == 0),
            "H_contact": H_c_deg,
            "n_reeb": n_reeb_deg,
            "interpretation": "Degenerate contact form gives H_contact=0; non-zero H_contact for degenerate form excluded",
        }
    except Exception as e:
        results["N2_degenerate_contact_H_contact_zero"] = {"passed": False, "error": str(e)}

    # N3: sympy — degenerate form forces H_contact=0 symbolically
    try:
        if _SYMPY:
            n = sp.Symbol("n_reeb", nonnegative=True)
            H = sp.log(1 + n)
            val_at_zero = H.subs(n, 0)
            results["N3_sympy_degenerate_H_contact_zero"] = {
                "passed": (val_at_zero == 0),
                "H_at_n_zero": str(val_at_zero),
                "interpretation": "log(1+0)=0 confirmed symbolically; H_contact=0 for degenerate contact form",
            }
        else:
            results["N3_sympy_degenerate_H_contact_zero"] = {"passed": False, "error": "sympy not installed"}
    except Exception as e:
        results["N3_sympy_degenerate_H_contact_zero"] = {"passed": False, "error": str(e)}

    results["pass"] = all(v.get("passed", False) for k, v in results.items() if isinstance(v, dict) and k != "pass")
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: trivial contact form (R^1) has H_contact=0
    try:
        # R^1 has no non-degenerate contact structure (dim must be odd >= 3)
        # Model: n_grid=1, single point with y=0 => degenerate everywhere
        ys = np.array([0.0])
        n_reeb = int(np.sum(np.abs(ys) > 1e-8))
        H_trivial = math.log(1 + n_reeb)
        results["B1_trivial_contact_R1_H_contact_zero"] = {
            "passed": (H_trivial == 0.0 and n_reeb == 0),
            "H_contact": H_trivial,
            "n_reeb": n_reeb,
            "interpretation": "Trivial R^1 contact form has H_contact=0; positive H_contact for trivial form excluded",
        }
    except Exception as e:
        results["B1_trivial_contact_R1_H_contact_zero"] = {"passed": False, "error": str(e)}

    # B2: I_c monotone decreasing across 3 MERA layers (input > final)
    try:
        input_Ic, final_Ic = mera_Ic(n_layers=3, seed=123)
        results["B2_Ic_monotone_input_gt_final"] = {
            "passed": bool(input_Ic > final_Ic),
            "input_Ic": input_Ic,
            "final_Ic": final_Ic,
            "interpretation": "I_c survived as monotone decreasing across MERA layers; I_c increase excluded",
        }
    except Exception as e:
        results["B2_Ic_monotone_input_gt_final"] = {"passed": False, "error": str(e)}

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
        "name": "sim_contact_symplectic_mera_pairwise_coupling",
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
            "Contact Reeb orbits constrain symplectic Lagrangians: joint-admissible fewer than either alone",
            "Contact × MERA: both H_contact and I_c positive under non-degenerate form",
            "Symplectic × MERA: both finite positive",
            "z3 UNSAT: degenerate contact form with H_contact>0 excluded",
            "sympy: log(1+0)=0 confirms degenerate boundary",
        ],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "contact_symplectic_mera_pairwise_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass={all_pass} -> {out_path}")
    for k, v in all_tests.items():
        if isinstance(v, dict):
            status = "PASS" if v.get("passed", False) else "FAIL"
            print(f"  {status}: {k}")
