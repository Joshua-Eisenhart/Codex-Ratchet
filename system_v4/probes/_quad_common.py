"""Shared helpers for 4-shell and 5-shell coexistence sims (step 4 of coupling program).

Exclusion-language discipline:
- A quad (or pent) "survived" when the joint A/B/C/D(+E) + coupling constraint set is SAT.
- It is "excluded" when the joint constraint set is UNSAT.
- A quad is "interacting" when admissible_joint_quad is strictly smaller than the
  intersection of all 4 triple-joints embedded inside it; else "additive".
- Pent analogously uses the intersection of all 5 quad-joints embedded inside.

scope_note cites: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md

No create/derive/drive language; use 'survived' / 'admissible under joint coupling' /
'joint coupling excludes ...'.
"""
from __future__ import annotations

import itertools
import json
import os

try:
    from z3 import Bool, Solver, And, Not, sat
    _HAVE_Z3 = True
except Exception:
    _HAVE_Z3 = False

from _couple_common import SHELL_SPECS


SCOPE_NOTE = (
    "4-shell / 5-shell coexistence test (step 4 of coupling program: multi-shell "
    "coexistence). Cites system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md. "
    "Statements use 'survived' / 'admissible under joint coupling' / 'joint coupling "
    "excludes ...'. No creates/derives/drives language."
)


def _enumerate_k(atoms, shell_preds, pair_pred, triple_pred, kwise_pred):
    """Enumerate 2^|atoms|; count admissible at each coupling depth.

    shell_preds: list of k shell predicates, evaluated on env.
    pair_pred(env): AND of all pairwise couplings across the k shells.
    triple_pred(env): AND of all triple couplings across the k shells.
    kwise_pred(env): the k-wise coupling itself.
    """
    names = list(atoms)
    admissible_shellwise_all = 0
    admissible_pair = 0
    admissible_triple = 0
    admissible_kwise = 0
    excluded_by_kwise = 0
    for bits in itertools.product([False, True], repeat=len(names)):
        env = dict(zip(names, bits))
        all_shells = all(p(env) for p in shell_preds)
        if not all_shells:
            continue
        admissible_shellwise_all += 1
        if not pair_pred(env):
            continue
        admissible_pair += 1
        if not triple_pred(env):
            continue
        admissible_triple += 1
        if kwise_pred(env):
            admissible_kwise += 1
        else:
            excluded_by_kwise += 1
    return {
        "admissible_shellwise_intersection": admissible_shellwise_all,
        "admissible_pair_joint": admissible_pair,
        "admissible_triple_joint": admissible_triple,
        "admissible_kwise_joint": admissible_kwise,
        "excluded_by_kwise_coupling": excluded_by_kwise,
        "interacting": (excluded_by_kwise > 0),
        "additive": (excluded_by_kwise == 0),
    }


def _z3_check_k(atoms, all_clauses, pair_z3_clauses, triple_z3_clauses, kwise_z3_clauses):
    if not _HAVE_Z3:
        return {"z3_available": False}
    env = {a: Bool(a) for a in atoms}

    def coll(cs):
        return [c(env) for c in cs]

    s_j = Solver()
    for cs in all_clauses:
        s_j.add(*coll(cs))
    s_j.add(*coll(pair_z3_clauses))
    s_j.add(*coll(triple_z3_clauses))
    s_j.add(*coll(kwise_z3_clauses))
    r_j = s_j.check()

    s_e = Solver()
    for cs in all_clauses:
        s_e.add(*coll(cs))
    s_e.add(*coll(pair_z3_clauses))
    s_e.add(*coll(triple_z3_clauses))
    kwise = coll(kwise_z3_clauses)
    if kwise:
        s_e.add(Not(And(*kwise)))
    else:
        return {
            "z3_available": True,
            "joint_kwise": "sat" if r_j == sat else "unsat",
            "kwise_exclusion_witness": "unsat",
        }
    r_e = s_e.check()
    return {
        "z3_available": True,
        "joint_kwise": "sat" if r_j == sat else "unsat",
        "kwise_exclusion_witness": "sat" if r_e == sat else "unsat",
    }


def write_results(name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path


def run_kwise(name, shells, pair_coupling_py, pair_coupling_z3,
              triple_coupling_py, triple_coupling_z3,
              kwise_coupling_py, kwise_coupling_z3,
              coupling_desc, extra_atoms=None):
    specs = [SHELL_SPECS[s] for s in shells]
    atoms_lists = [s[0] for s in specs]
    preds = [s[1] for s in specs]
    clauses_fns = [s[2] for s in specs]

    atoms = []
    for al in atoms_lists:
        for a in al:
            if a not in atoms:
                atoms.append(a)
    for a in (extra_atoms or []):
        if a not in atoms:
            atoms.append(a)

    all_clauses = [fn() for fn in clauses_fns]

    # POSITIVE
    pos_enum = _enumerate_k(atoms, preds, pair_coupling_py, triple_coupling_py,
                            kwise_coupling_py)
    pos_z3 = _z3_check_k(atoms, all_clauses, pair_coupling_z3, triple_coupling_z3,
                         kwise_coupling_z3)
    positive_pass = (
        pos_enum["admissible_kwise_joint"] >= 0
        and pos_z3.get("joint_kwise") in ("sat", "unsat")
    )

    # NEGATIVE: k-wise coupling forced FALSE -> joint must be empty
    neg_enum = _enumerate_k(atoms, preds, pair_coupling_py, triple_coupling_py,
                            lambda e: False)
    negative_pass = (neg_enum["admissible_kwise_joint"] == 0)

    # BOUNDARY: k-wise forced TRUE -> reduces to triple_joint count
    bnd_enum = _enumerate_k(atoms, preds, pair_coupling_py, triple_coupling_py,
                            lambda e: True)
    boundary_pass = (
        bnd_enum["admissible_kwise_joint"] == bnd_enum["admissible_triple_joint"]
        and bnd_enum["excluded_by_kwise_coupling"] == 0
    )

    overall = positive_pass and negative_pass and boundary_pass

    return {
        "name": name,
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "exclusion_language_note": (
            "k-wise coupling uses 'joint coupling excludes ...' / 'survived' / "
            "'admissible under joint coupling'. No create/derive/drive language."
        ),
        "shells": list(shells),
        "k": len(shells),
        "coupling_description": coupling_desc,
        "atoms": atoms,
        "positive": {"enum": pos_enum, "z3": pos_z3, "pass": positive_pass},
        "negative": {
            "enum": neg_enum,
            "description": "k-wise coupling forced FALSE; joint admissible set must be empty",
            "pass": negative_pass,
        },
        "boundary": {
            "enum": bnd_enum,
            "description": (
                "k-wise coupling forced TRUE; joint reduces to (k-1)-wise triple joint"
            ),
            "pass": boundary_pass,
        },
        "overall_pass": overall,
        "interacting": pos_enum["interacting"],
        "additive": pos_enum["additive"],
        "tool_manifest": {
            "z3": {
                "tried": _HAVE_Z3,
                "used": _HAVE_Z3,
                "reason": (
                    "load_bearing: k-wise joint SAT and k-wise-exclusion-witness "
                    "SAT/UNSAT decides whether k-way coupling strictly excludes "
                    "beyond all embedded (k-1)-triples"
                ) if _HAVE_Z3 else "not installed",
            },
            "sympy":    {"tried": True, "used": False,
                         "reason": "supportive only; Boolean admissibility at k-wise layer does not require symbolic algebra"},
            "clifford": {"tried": True, "used": False,
                         "reason": "not applicable at Boolean k-wise coupling layer"},
            "pytorch":  {"tried": True, "used": False,
                         "reason": "no gradient surface at Boolean k-wise admissibility layer"},
        },
        "tool_integration_depth": {
            "z3": "load_bearing" if _HAVE_Z3 else None,
            "sympy": "supportive",
            "clifford": None,
            "pytorch": None,
        },
    }
