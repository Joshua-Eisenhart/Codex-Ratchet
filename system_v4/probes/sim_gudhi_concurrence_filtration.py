#!/usr/bin/env python3
"""
sim_gudhi_concurrence_filtration.py

Filtration by concurrence C in [0,1].
20 states from separable (C=0) to maximally entangled (C=1).
Tests whether C=0 boundary creates a persistent H0 gap.
Compares concurrence filtration vs I_c filtration.
"""

import json
import os
import numpy as np

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
    "pytorch": "supportive",
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
    "gudhi": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Density matrix construction, partial traces, concurrence and I_c computation"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "Simplex tree filtration (by concurrence and I_c) -- primary topological analysis"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

def von_neumann_entropy(rho: "torch.Tensor") -> float:
    import torch
    eigvals = torch.linalg.eigvalsh(rho).real.clamp(min=1e-12)
    return float(-torch.sum(eigvals * torch.log2(eigvals)))


def partial_trace_system(rho_AB: "torch.Tensor", keep: str, dimA: int, dimB: int) -> "torch.Tensor":
    import torch
    rho = rho_AB.reshape(dimA, dimB, dimA, dimB)
    if keep == "A":
        return torch.einsum("ibjb->ij", rho)
    else:
        return torch.einsum("iajb->ab", rho.permute(1, 0, 3, 2))


def concurrence_from_state(alpha: float) -> float:
    """
    For the family cos(alpha)|00> + sin(alpha)|11>, concurrence = sin(2*alpha).
    alpha in [0, pi/4] gives C in [0, 1].
    """
    return float(np.sin(2 * alpha))


def build_concurrence_family(n_states: int = 20):
    """
    Build n_states parameterized by C in [0,1].
    State: cos(alpha)|00> + sin(alpha)|11>, where C = sin(2*alpha).
    alpha in [0, pi/4].
    Returns list of dicts with rho, C, MI, cond_S, I_c.
    """
    import torch

    alphas = np.linspace(0, np.pi / 4, n_states)
    states = []

    for alpha in alphas:
        c = float(np.cos(alpha))
        s = float(np.sin(alpha))
        psi = torch.tensor([c, 0.0, 0.0, s], dtype=torch.complex128)
        rho = torch.outer(psi, psi.conj())

        rho_A = partial_trace_system(rho, "A", 2, 2)
        rho_B = partial_trace_system(rho, "B", 2, 2)

        S_AB = von_neumann_entropy(rho)
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)

        MI = S_A + S_B - S_AB
        cond_S = S_AB - S_A
        I_c = S_B - S_AB
        C = concurrence_from_state(alpha)

        states.append({
            "alpha": float(alpha),
            "C": C,
            "MI": float(MI),
            "cond_S": float(cond_S),
            "I_c": float(I_c),
            "S_A": float(S_A),
            "S_B": float(S_B),
            "S_AB": float(S_AB),
        })

    return states


def build_simplex_tree_from_filtration(states: list, filtration_key: str):
    """
    Build a GUDHI simplex tree with explicit filtration values.
    States are added as 0-simplices in order of increasing filtration_key.
    Edges added between consecutive states (1-simplices) with filtration value
    = max of the two endpoint filtration values.
    """
    st = gudhi.SimplexTree()
    n = len(states)
    fvals = [s[filtration_key] for s in states]

    # Add 0-simplices
    for i, fv in enumerate(fvals):
        st.insert([i], filtration=fv)

    # Add 1-simplices (edges between consecutive states)
    for i in range(n - 1):
        edge_fval = max(fvals[i], fvals[i + 1])
        st.insert([i, i + 1], filtration=edge_fval)

    # Also add edges between geometrically close states (using kernel distance)
    # This ensures we capture topology beyond just the chain
    points = np.array([[s["MI"], s["cond_S"], s["I_c"]] for s in states])
    for i in range(n):
        for j in range(i + 2, n):  # skip already-added consecutive edges
            dist = float(np.linalg.norm(points[i] - points[j]))
            if dist < 0.3:  # only add short edges
                edge_fval_2 = max(fvals[i], fvals[j])
                st.insert([i, j], filtration=edge_fval_2)

    st.make_filtration_non_decreasing()
    st.compute_persistence()
    return st


def homology_summary(st, dim: int) -> dict:
    pairs = st.persistence_intervals_in_dimension(dim)
    pairs_list = [(float(b), float(d)) for b, d in pairs]
    finite = [(b, d) for b, d in pairs_list if d != float("inf") and d - b > 1e-9]
    infinite = [(b, d) for b, d in pairs_list if d == float("inf")]
    return {
        "finite_bars": len(finite),
        "infinite_bars": len(infinite),
        "total": len(pairs_list),
        "max_persistence": float(max((d - b for b, d in finite), default=0.0)),
        "pairs": pairs_list[:10],
    }


def rips_homology_summary(points: list, max_edge: float = 3.0) -> dict:
    try:
        rc = gudhi.RipsComplex(points=points, max_edge_length=max_edge)
        st = rc.create_simplex_tree(max_dimension=3)
        st.compute_persistence()
        return {
            "H0": homology_summary(st, 0),
            "H1": homology_summary(st, 1),
            "H2": homology_summary(st, 2),
        }
    except Exception as e:
        return {"error": str(e)}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    states = build_concurrence_family(20)
    results["n_states"] = len(states)
    results["state_sample"] = states[:3] + states[-2:]

    # Kernel point cloud
    points = [[s["MI"], s["cond_S"], s["I_c"]] for s in states]
    results["kernel_range"] = {
        "C_min": float(min(s["C"] for s in states)),
        "C_max": float(max(s["C"] for s in states)),
        "MI_range": [float(min(s["MI"] for s in states)), float(max(s["MI"] for s in states))],
        "I_c_range": [float(min(s["I_c"] for s in states)), float(max(s["I_c"] for s in states))],
    }

    # --- Concurrence filtration ---
    try:
        st_conc = build_simplex_tree_from_filtration(states, "C")
        results["concurrence_filtration"] = {
            "H0": homology_summary(st_conc, 0),
            "H1": homology_summary(st_conc, 1),
        }
    except Exception as e:
        results["concurrence_filtration"] = {"error": str(e)}

    # --- I_c filtration ---
    try:
        st_ic = build_simplex_tree_from_filtration(states, "I_c")
        results["I_c_filtration"] = {
            "H0": homology_summary(st_ic, 0),
            "H1": homology_summary(st_ic, 1),
        }
    except Exception as e:
        results["I_c_filtration"] = {"error": str(e)}

    # --- Rips on kernel point cloud ---
    results["rips_kernel"] = rips_homology_summary(points, max_edge=3.0)

    return results


# =====================================================================
# NEGATIVE TESTS -- all separable (C=0)
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative: all states at C=0 (alpha=0, product states)
    # All 20 states are the same point -- should give H0=1, H1=0, trivial
    import torch

    sep_states = []
    for _ in range(20):
        psi = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.complex128)
        rho = torch.outer(psi, psi.conj())
        rho_A = partial_trace_system(rho, "A", 2, 2)
        rho_B = partial_trace_system(rho, "B", 2, 2)
        S_AB = von_neumann_entropy(rho)
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)
        sep_states.append({
            "C": 0.0,
            "MI": float(S_A + S_B - S_AB),
            "cond_S": float(S_AB - S_A),
            "I_c": float(S_B - S_AB),
        })

    points_sep = [[s["MI"], s["cond_S"], s["I_c"]] for s in sep_states]
    results["all_separable_rips"] = rips_homology_summary(points_sep, max_edge=3.0)
    results["all_separable_degenerate"] = bool(np.allclose(points_sep, points_sep[0], atol=1e-9))

    # Negative: test that no H1 appears in a purely 1D (monotone) family
    # I_c is monotone in alpha, so there should be no loop
    states_mono = build_concurrence_family(20)
    ic_vals = [s["I_c"] for s in states_mono]
    results["I_c_monotone"] = bool(all(ic_vals[i] <= ic_vals[i + 1] + 1e-9 for i in range(len(ic_vals) - 1)))
    results["note"] = "Monotone I_c family: no loop expected, H1 should be 0 in Rips"

    return results


# =====================================================================
# BOUNDARY TESTS -- C=0 gap detection
# =====================================================================

def run_boundary_tests():
    results = {}
    states = build_concurrence_family(20)

    # Separate into C=0 cluster and C>0 cluster
    sep_states = [s for s in states if s["C"] < 1e-9]
    ent_states = [s for s in states if s["C"] >= 1e-9]
    results["n_separable"] = len(sep_states)
    results["n_entangled"] = len(ent_states)

    # Concurrence filtration: at what filtration value does H0 reduce from 2 to 1?
    # (i.e. when do the two clusters merge?)
    try:
        st_conc = build_simplex_tree_from_filtration(states, "C")
        h0_pairs = st_conc.persistence_intervals_in_dimension(0)
        h0_pairs_list = [(float(b), float(d)) for b, d in h0_pairs]
        finite_h0 = [(b, d) for b, d in h0_pairs_list if d != float("inf") and d - b > 1e-9]
        results["concurrence_H0_gap"] = {
            "finite_bars": finite_h0,
            "persistent_H0_at_C0_boundary": any(d < 0.1 for b, d in finite_h0 if b < 1e-9),
            "gap_bars": [bar for bar in finite_h0 if bar[0] < 1e-9 and bar[1] > 0.05],
        }
    except Exception as e:
        results["concurrence_H0_gap"] = {"error": str(e)}

    # I_c filtration H0 gap
    try:
        st_ic = build_simplex_tree_from_filtration(states, "I_c")
        h0_ic = st_ic.persistence_intervals_in_dimension(0)
        h0_ic_list = [(float(b), float(d)) for b, d in h0_ic]
        finite_h0_ic = [(b, d) for b, d in h0_ic_list if d != float("inf") and d - b > 1e-9]
        results["I_c_H0_gap"] = {
            "finite_bars": finite_h0_ic,
            "max_persistence": float(max((d - b for b, d in finite_h0_ic), default=0.0)),
        }
    except Exception as e:
        results["I_c_H0_gap"] = {"error": str(e)}

    # Verdict: do the two filtrations differ in gap structure?
    c_max_pers = 0.0
    ic_max_pers = 0.0
    try:
        c_h0 = results.get("concurrence_H0_gap", {})
        ic_h0 = results.get("I_c_H0_gap", {})
        if isinstance(c_h0.get("finite_bars"), list) and c_h0["finite_bars"]:
            c_max_pers = max(d - b for b, d in c_h0["finite_bars"])
        if isinstance(ic_h0.get("finite_bars"), list) and ic_h0["finite_bars"]:
            ic_max_pers = max(d - b for b, d in ic_h0["finite_bars"])
    except Exception:
        pass

    results["filtration_comparison"] = {
        "concurrence_H0_max_persistence": float(c_max_pers),
        "I_c_H0_max_persistence": float(ic_max_pers),
        "filtrations_produce_different_diagrams": abs(c_max_pers - ic_max_pers) > 0.01,
        "interpretation": (
            "Concurrence and I_c filtrations agree on H0 structure"
            if abs(c_max_pers - ic_max_pers) <= 0.01
            else "Concurrence and I_c filtrations produce different persistence diagrams -- they probe different structure"
        ),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Extract key results for summary
    conc_filt = pos.get("concurrence_filtration", {})
    ic_filt = pos.get("I_c_filtration", {})
    rips_k = pos.get("rips_kernel", {})

    results = {
        "name": "gudhi_concurrence_filtration",
        "description": (
            "Filtration by concurrence C in [0,1] on 20 two-qubit states. "
            "Tests for persistent H0 gap at C=0 boundary. "
            "Compares concurrence filtration vs I_c filtration persistence diagrams."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "topology_verdict": {
            "concurrence_filtration_H0": conc_filt.get("H0"),
            "concurrence_filtration_H1": conc_filt.get("H1"),
            "I_c_filtration_H0": ic_filt.get("H0"),
            "I_c_filtration_H1": ic_filt.get("H1"),
            "rips_kernel_H0": rips_k.get("H0"),
            "rips_kernel_H1": rips_k.get("H1"),
            "C0_gap_detected": bnd.get("concurrence_H0_gap", {}).get("persistent_H0_at_C0_boundary", False),
            "filtrations_differ": bnd.get("filtration_comparison", {}).get("filtrations_produce_different_diagrams", False),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_concurrence_filtration_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
