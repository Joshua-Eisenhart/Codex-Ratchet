#!/usr/bin/env python3
"""
sim_z3_negative_quasiprob_exclusion.py

Canonical z3-deep sim: proves that a quasi-distribution reconstruction
(Wigner-like) reproducing marginals of a nonclassical state cannot have
all nonnegative weights -- i.e. negativity is UNSAT-excludable only for
classical-compatible marginals.

Encoding: 4-cell quasi-distribution q_1..q_4 with sum=1, reproducing two
pairs of marginals m_A = (q_1+q_2, q_3+q_4) and m_B = (q_1+q_3, q_2+q_4),
plus a 'third marginal' m_C = (q_1+q_4, q_2+q_3) from a complementary
context. For a nonclassical (Bell-like) marginal triple, asserting
q_i >= 0 for all i is UNSAT.

z3 is load_bearing: reconstruction is a linear-arithmetic feasibility
problem; numpy lstsq returns a *solution* but cannot prove *no* nonneg
solution exists. z3 returns an UNSAT certificate over Q (decidable).
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "no learning"},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "reserved cross-check"},
    "sympy": {"tried": False, "used": False, "reason": "rational marginal assignments"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from z3 import Real, Solver, And, Not, Sum, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "LRA UNSAT over nonneg q_i reconstructing nonclassical marginals"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    HAVE_Z3 = True
except ImportError:
    HAVE_Z3 = False


def reconstruction_unsat(E00, E01, E10, E11, nonneg=True):
    """Fine's theorem encoding. Joint quasi-distribution q(a0,a1,b0,b1)
    over {-1,+1}^4, 16 cells, reproducing CHSH correlations
    <A_i B_j> = E_ij. If nonneg required and CHSH sum > 2 -> UNSAT.
    """
    s = Solver()
    from itertools import product as _p
    cells = list(_p([-1, 1], repeat=4))  # (a0,a1,b0,b1)
    q = [Real(f"q_{i}") for i in range(16)]
    if nonneg:
        for i in range(16):
            s.add(q[i] >= 0)
    s.add(Sum(q) == 1)
    # Marginals: <A_i B_j>
    def corr(i, j, target):
        e = 0
        for k, (a0, a1, b0, b1) in enumerate(cells):
            avec = (a0, a1)
            bvec = (b0, b1)
            e = e + avec[i] * bvec[j] * q[k]
        s.add(e == target)
    corr(0, 0, E00)
    corr(0, 1, E01)
    corr(1, 0, E10)
    corr(1, 1, E11)
    return str(s.check())


# CHSH-violating correlations: S = E00+E01+E10-E11 = 4 > 2
NC_E = (1, 1, 1, -1)
# Classical correlations (reachable by product joint): all zero
CL_E = (0, 0, 0, 0)


def run_positive_tests():
    results = {}
    r = reconstruction_unsat(*NC_E, nonneg=True)
    results["nonclassical_nonneg_reconstruction_unsat"] = {
        "z3_result": r, "expected": "unsat", "pass": r == "unsat"
    }
    r2 = reconstruction_unsat(*NC_E, nonneg=False)
    results["nonclassical_signed_reconstruction_sat"] = {
        "z3_result": r2, "expected": "sat", "pass": r2 == "sat"
    }
    return results


def run_negative_tests():
    results = {}
    r = reconstruction_unsat(*CL_E, nonneg=True)
    results["classical_nonneg_reconstruction_sat"] = {
        "z3_result": r, "expected": "sat", "pass": r == "sat"
    }
    # Out-of-range correlations |E|>1 => UNSAT even signed with normalization
    # and per-cell bounded? With unbounded signed weights these are still SAT;
    # instead assert a direct contradiction: all four E = +2 is infeasible
    # since each E_ij must lie in [-1,1] under sum(q)=1 when q>=0.
    bad = reconstruction_unsat(2, 0, 0, 0, nonneg=True)
    results["out_of_range_corr_unsat"] = {
        "z3_result": bad, "expected": "unsat", "pass": bad == "unsat"
    }
    return results


def run_boundary_tests():
    results = {}
    # Interpolate from classical (S=0) to PR-box (S=4). Transition at S=2.
    last_sat_t = None
    first_unsat_t = None
    for k in range(0, 11):
        t = k / 10.0
        # E_ij = t * NC_E + (1-t)*0
        E = tuple(t * e for e in NC_E)
        r = reconstruction_unsat(*E, nonneg=True)
        if r == "sat":
            last_sat_t = t
        elif r == "unsat" and first_unsat_t is None:
            first_unsat_t = t
    results["interpolation"] = {
        "last_sat_t": last_sat_t,
        "first_unsat_t": first_unsat_t,
        "pass": (last_sat_t is not None) and (first_unsat_t is not None) and (last_sat_t < first_unsat_t),
    }
    return results


def run_ablation():
    # numpy lstsq: build 5x16 system (4 corr + normalization) and solve.
    from itertools import product as _p
    cells = list(_p([-1, 1], repeat=4))
    A = np.zeros((5, 16))
    for k, (a0, a1, b0, b1) in enumerate(cells):
        A[0, k] = a0 * b0
        A[1, k] = a0 * b1
        A[2, k] = a1 * b0
        A[3, k] = a1 * b1
        A[4, k] = 1.0
    b = np.array([NC_E[0], NC_E[1], NC_E[2], NC_E[3], 1.0])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    nonneg = bool(np.all(sol >= -1e-9))
    residual = float(np.linalg.norm(A @ sol - b))
    return {
        "numpy_lstsq_min_entry": float(sol.min()),
        "numpy_nonneg": nonneg,
        "residual": residual,
        "note": "lstsq returns a signed solution; cannot certify NO nonneg sol exists. z3 closes with UNSAT via LRA.",
        "certifies_structural_impossibility": False,
    }


if __name__ == "__main__":
    results = {
        "name": "z3-proves-exclusion-of-negative-probabilities-in-quasi-distribution-reconstruction",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "ablation_numpy_substitute": run_ablation(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "z3_negative_quasiprob_exclusion_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
