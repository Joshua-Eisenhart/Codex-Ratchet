#!/usr/bin/env python3
"""Classical baseline: monotone convergence theorem on a classical filtration.

For an increasing sequence of sigma-algebras F_n and E[|X|] < inf, the
conditional expectations E[X | F_n] form an L^1 martingale that converges to
E[X | F_inf]. We instantiate this on finite partitions.
"""
import json
import os

import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical filtrations are nested sigma-algebras of commuting events. "
    "Quantum filtrations are nested von Neumann subalgebras with "
    "noncommuting projections; conditional expectation is replaced by "
    "operator-valued projection. This baseline drops the noncommutativity."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "partition refinement and means"},
    "scipy": {"tried": False, "used": False, "reason": "not required"},
    "pytorch": {
        "tried": _torch_ok,
        "used": _torch_ok,
        "reason": "supportive import only",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT claim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "supportive" if _torch_ok else None,
    "scipy": None,
    "z3": None,
}


def cond_exp_on_partition(X, weights, partition):
    """Compute E[X | partition]: piecewise-constant on each atom."""
    X = np.asarray(X, float)
    w = np.asarray(weights, float)
    w = w / w.sum()
    out = np.zeros_like(X)
    for atom in partition:
        idx = np.asarray(list(atom), dtype=int)
        mass = w[idx].sum()
        if mass > 0:
            mean = float(np.sum(X[idx] * w[idx]) / mass)
        else:
            mean = 0.0
        out[idx] = mean
    return out


def is_refinement(coarse, fine):
    """Check every atom of fine is contained in some atom of coarse."""
    for f_atom in fine:
        f_set = set(f_atom)
        if not any(f_set.issubset(set(c_atom)) for c_atom in coarse):
            return False
    return True


def build_filtration(N, n_levels, seed=0):
    """Increasing sequence of partitions via dyadic refinement."""
    rng = np.random.default_rng(seed)
    levels = []
    # Start with trivial partition
    current = [list(range(N))]
    levels.append(current)
    for _ in range(n_levels):
        new_level = []
        for atom in current:
            if len(atom) <= 1:
                new_level.append(atom)
                continue
            perm = list(atom)
            rng.shuffle(perm)
            mid = len(perm) // 2
            new_level.append(perm[:mid])
            new_level.append(perm[mid:])
        current = new_level
        levels.append(current)
    return levels


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(11)
    N = 64
    X = rng.normal(size=N)
    w = rng.dirichlet(np.ones(N))

    levels = build_filtration(N, n_levels=6, seed=3)
    # All nested
    r["filtration_nested"] = bool(
        all(is_refinement(levels[i], levels[i + 1]) for i in range(len(levels) - 1))
    )

    # Final partition = singletons => conditional expectation = X itself
    final = levels[-1]
    CE_final = cond_exp_on_partition(X, w, final)
    # (only atoms of size 1 reproduce X; with n_levels large enough most atoms are)
    singleton_mask = np.zeros(N, dtype=bool)
    for atom in final:
        if len(atom) == 1:
            singleton_mask[atom[0]] = True
    r["refined_tends_to_X"] = bool(np.allclose(CE_final[singleton_mask], X[singleton_mask]))

    # L2 distance (orthogonal-projection geometry) is monotone non-increasing
    # under refinement: ||X - E[X|F_{n+1}]||_2 <= ||X - E[X|F_n]||_2.
    d_prev = float(np.sum(w * (X - cond_exp_on_partition(X, w, levels[0])) ** 2))
    monotone = True
    for lev in levels[1:]:
        d = float(np.sum(w * (X - cond_exp_on_partition(X, w, lev)) ** 2))
        if d > d_prev + 1e-9:
            monotone = False
            break
        d_prev = d
    r["L2_distance_monotone_nonincreasing"] = monotone

    # Tower property: E[ E[X|F_n] ] = E[X] for every n
    mean_X = float(np.sum(w * X))
    tower_ok = True
    for lev in levels:
        ce = cond_exp_on_partition(X, w, lev)
        if not np.isclose(float(np.sum(w * ce)), mean_X, atol=1e-9):
            tower_ok = False
            break
    r["tower_property"] = tower_ok
    return r


def run_negative_tests():
    r = {}
    # Non-nested sequence should NOT satisfy refinement test
    p1 = [[0, 1], [2, 3]]
    p2 = [[0, 2], [1, 3]]
    r["nonnested_fails_refinement"] = bool(not is_refinement(p1, p2))

    # Coarser conditional expectation is not pointwise equal to finer generically
    X = np.array([1.0, 2.0, 3.0, 4.0])
    w = np.ones(4) / 4
    coarse = [[0, 1, 2, 3]]
    fine = [[0, 1], [2, 3]]
    ce_c = cond_exp_on_partition(X, w, coarse)
    ce_f = cond_exp_on_partition(X, w, fine)
    r["coarse_differs_from_fine"] = bool(not np.allclose(ce_c, ce_f))
    return r


def run_boundary_tests():
    r = {}
    # Constant X: conditional expectation equals X at every level
    N = 8
    X = np.ones(N) * 3.14
    w = np.ones(N) / N
    levels = build_filtration(N, n_levels=3, seed=5)
    ok = all(np.allclose(cond_exp_on_partition(X, w, lev), X) for lev in levels)
    r["constant_CE_is_identity"] = ok

    # Trivial partition: CE is mean
    X2 = np.array([0.0, 1.0, 2.0, 3.0])
    w2 = np.ones(4) / 4
    r["trivial_CE_is_mean"] = bool(
        np.allclose(cond_exp_on_partition(X2, w2, [[0, 1, 2, 3]]), np.full(4, 1.5))
    )
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "monotone_filtration_convergence_classical_results.json")
    payload = {
        "name": "monotone_filtration_convergence_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": bool(all_pass),
        "summary": {"all_pass": bool(all_pass)},
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Results written to {out_path} all_pass={all_pass}")
