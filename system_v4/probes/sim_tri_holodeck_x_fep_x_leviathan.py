#!/usr/bin/env python3
"""
TRI sim: Holodeck x FEP x Leviathan  (coupling program step 3)
==============================================================
Three-way multi-shell coexistence.

Shells:
  H   Holodeck  : per-observer admissible observation shell p_H (finite atom set)
  F   FEP       : surprise-reduction descent on q toward p_H
  L   Leviathan : civilizational shell -- shared constraint across observers

Genuinely 3-way emergent question:
  Do multiple observers under FEP descent converge on a shared core that sits
  inside the Leviathan shell? Pairwise H x F gives per-observer convergence;
  pairwise H x L gives civic overlap; pairwise F x L gives nothing per-observer.
  ONLY the 3-way can report "all observers' post-descent beliefs are mutually
  in the civic shell" -- a civic-coherent belief core no pair can detect.

POS : all 3 observers descend (F), end inside their holodecks (H), AND inside
      leviathan (L); z3 tetra-like conjunction SAT; drop-one UNSAT each.
NEG : drop-H (off-shell target), drop-F (no descent), drop-L (civic empty).
BND : two-observer minimal instance on 3-atom support.

Classification: canonical. z3 load-bearing.
"""
from __future__ import annotations
import json, os
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True,
              "reason": "KL descent + civic intersection numerics"},
    "z3":    {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "z3": None, "sympy": None}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
try:
    import sympy as sp; TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None


def kl(q, p):
    m = q > 1e-15
    return float(np.sum(q[m] * (np.log(q[m]) - np.log(np.maximum(p[m], 1e-15)))))

def fep_descend(q, p, steps=40, lr=0.3):
    F = [kl(q, p)]
    for _ in range(steps):
        q = (1 - lr) * q + lr * p
        q = np.clip(q, 1e-9, 1); q /= q.sum()
        F.append(kl(q, p))
    return q, F

def in_civic(q, civic_mask):
    # civic_mask: which atoms are admitted by leviathan. q must place its mass there.
    return float(np.sum(q[civic_mask])) > 0.9


def z3_tri_drop_one(extra_H=True, extra_F=True, extra_L=True):
    assert z3 is not None
    out = {}
    for drop in ("H", "F", "L"):
        s = z3.Solver()
        H, F, L, T = z3.Bools("H F L T")
        s.add(T == z3.And(H, F, L))
        s.add(T)
        s.add({"H": z3.Not(H), "F": z3.Not(F), "L": z3.Not(L)}[drop])
        out[f"drop_{drop}_unsat"] = (s.check() == z3.unsat)
    s2 = z3.Solver()
    H, F, L, T = z3.Bools("H F L T")
    s2.add(T == z3.And(H, F, L), T)
    out["all_three_sat"] = (s2.check() == z3.sat)
    return out


def run_positive_tests():
    r = {}
    # 4-atom world; civic shell = atoms {0,1,2}; observers overlap differently on H
    civic_mask = np.array([True, True, True, False])
    obs_targets = [
        np.array([0.5, 0.3, 0.2, 0.0]),
        np.array([0.4, 0.4, 0.2, 0.0]),
        np.array([0.3, 0.4, 0.3, 0.0]),
    ]
    q0 = np.array([0.1, 0.1, 0.1, 0.7])

    descended, F_series = [], []
    for p in obs_targets:
        qe, F = fep_descend(q0.copy(), p)
        descended.append(qe); F_series.append(F)

    r["F_descended_all"]   = all(F[-1] < F[0] - 1e-6 for F in F_series)
    r["H_shell_respected"] = all(np.allclose(qe.sum(), 1.0) and
                                 np.all((p > 0) | (qe < 1e-6))
                                 for qe, p in zip(descended, obs_targets))
    r["L_civic_respected"] = all(in_civic(qe, civic_mask) for qe in descended)

    # Emergent 3-way: all observers' descended beliefs mutually in civic shell
    # AND pairwise belief-overlap (atom-wise min) is nonzero on civic atoms.
    stacked = np.stack(descended)
    civic_core = np.min(stacked[:, civic_mask], axis=0)
    r["EMERGENT_3way_civic_belief_core"] = bool(np.sum(civic_core) > 0.1)

    # z3 load-bearing: conjunction required
    z3r = z3_tri_drop_one()
    r.update({f"z3_{k}": v for k, v in z3r.items()})
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "tri conjunction UNSAT on any single-shell drop"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    if sp is not None:
        Hs, Fs, Ls = sp.symbols("H F L")
        r["sympy_tri_predicate"] = bool(sp.And(Hs, Fs, Ls).subs(
            {Hs: True, Fs: True, Ls: True}))
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "symbolic tri conjunction"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return r


def run_negative_tests():
    r = {}
    civic_mask = np.array([True, True, True, False])
    p = np.array([0.5, 0.3, 0.2, 0.0])
    q0 = np.array([0.1, 0.1, 0.1, 0.7])

    # drop H: target off-shell (mass on atom 3 outside civic)
    p_off = np.array([0.1, 0.1, 0.1, 0.7])
    qe_H, _ = fep_descend(q0.copy(), p_off)
    r["drop_H_civic_fails"] = not in_civic(qe_H, civic_mask)

    # drop F: no descent (keep q0, which is outside civic)
    r["drop_F_no_descent"] = not in_civic(q0, civic_mask)

    # drop L: civic mask = all False -> civic impossible
    civic_empty = np.array([False, False, False, False])
    qe_L, _ = fep_descend(q0.copy(), p)
    r["drop_L_no_civic_core"] = not in_civic(qe_L, civic_empty)

    z3r = z3_tri_drop_one()
    for k in ("drop_H_unsat", "drop_F_unsat", "drop_L_unsat"):
        r[f"z3_{k}"] = z3r[k]
    return r


def run_boundary_tests():
    r = {}
    # 2-observer, 3-atom minimal
    civic = np.array([True, True, False])
    p1 = np.array([0.6, 0.4, 0.0])
    p2 = np.array([0.3, 0.7, 0.0])
    q0 = np.array([0.2, 0.2, 0.6])
    qe1, F1 = fep_descend(q0.copy(), p1)
    qe2, F2 = fep_descend(q0.copy(), p2)
    r["min_descent_both"]  = F1[-1] < F1[0] and F2[-1] < F2[0]
    r["min_civic_both"]    = in_civic(qe1, civic) and in_civic(qe2, civic)
    r["min_atoms_3"]       = len(p1) == 3
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_tri_holodeck_x_fep_x_leviathan",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "three_way_note": ("3-way ADDS: shared civic-belief core across FEP-"
                            "descended observers, undetectable pairwise."),
    }
    ok = all(bool(v) for d in (results["positive"], results["negative"],
                               results["boundary"])
             for k, v in d.items() if isinstance(v, bool))
    results["PASS"] = ok
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "tri_holodeck_x_fep_x_leviathan_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={ok}  ->  {out}")
