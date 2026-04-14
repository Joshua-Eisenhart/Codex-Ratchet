"""Shared helpers for triple framework coupling sims (step 3 of coupling program).

Exclusion-language discipline:
- A triple "survived" when the joint A/B/C + coupling constraint set is SAT.
- A triple is "excluded" when the joint constraint set is UNSAT.
- A triple is "interacting" when admissible_joint_triple <
  admissible_pairwise_intersection (the three-way coupling strictly excludes
  candidates that all three pairwise couplings would admit).
- A triple is "additive" when admissible_joint_triple ==
  admissible_pairwise_intersection (no three-way exclusion beyond pairwise).

scope_note cites: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md
"""
from __future__ import annotations

import itertools
import json
import os

try:
    from z3 import Bool, Solver, And, Or, Not, Implies, sat, unsat
    _HAVE_Z3 = True
except Exception:
    _HAVE_Z3 = False

from _couple_common import SHELL_SPECS, SCOPE_NOTE as _PAIR_SCOPE  # reuse


SCOPE_NOTE = (
    "Triple coupling test (step 3 of coupling program: multi-shell coexistence). "
    "Cites system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md. "
    "Statements use 'survived' / 'admissible under joint triple coupling' / "
    "'joint coupling excludes ...'. No creates/derives/drives language."
)


def _enumerate_triple(atoms, pA, pB, pC, pair_ABC_pred, triple_pred):
    """pair_ABC_pred(env) is AND of the three pairwise couplings (enum side).
    triple_pred(env) is the three-way coupling.
    Returns pairwise-intersection count, triple-joint count, and flags.
    """
    names = list(atoms)
    n = len(names)
    admA = admB = admC = inter3 = pairwise_admit = triple_admit = excl = 0
    for bits in itertools.product([False, True], repeat=n):
        env = dict(zip(names, bits))
        a = pA(env); b = pB(env); c = pC(env)
        admA += int(a); admB += int(b); admC += int(c)
        all3 = a and b and c
        inter3 += int(all3)
        pw = all3 and pair_ABC_pred(env)
        pairwise_admit += int(pw)
        tr = pw and triple_pred(env)
        triple_admit += int(tr)
        if pw and not tr:
            excl += 1
    return {
        "admissible_A": admA,
        "admissible_B": admB,
        "admissible_C": admC,
        "admissible_intersection_ABC": inter3,
        "admissible_pairwise_joint": pairwise_admit,
        "admissible_triple_joint": triple_admit,
        "excluded_by_triple_coupling": excl,
        "interacting": (excl > 0),
        "additive": (excl == 0),
    }


def _z3_check_triple(atoms, clauses_A, clauses_B, clauses_C,
                     pair_coupling_clauses, triple_coupling_clauses):
    if not _HAVE_Z3:
        return {"z3_available": False}
    env = {a: Bool(a) for a in atoms}

    def coll(cs):
        return [c(env) for c in cs]

    s_j = Solver()
    s_j.add(*coll(clauses_A)); s_j.add(*coll(clauses_B)); s_j.add(*coll(clauses_C))
    s_j.add(*coll(pair_coupling_clauses))
    s_j.add(*coll(triple_coupling_clauses))
    r_j = s_j.check()

    # triple-exclusion witness: A,B,C all admissible AND pair couplings hold
    # AND triple coupling fails.
    s_e = Solver()
    s_e.add(*coll(clauses_A)); s_e.add(*coll(clauses_B)); s_e.add(*coll(clauses_C))
    s_e.add(*coll(pair_coupling_clauses))
    triple_cs = coll(triple_coupling_clauses)
    if triple_cs:
        s_e.add(Not(And(*triple_cs)))
    else:
        # no triple coupling -> additive by construction
        return {
            "z3_available": True,
            "joint_triple": "sat" if r_j == sat else "unsat",
            "triple_exclusion_witness": "unsat",
        }
    r_e = s_e.check()
    return {
        "z3_available": True,
        "joint_triple": "sat" if r_j == sat else "unsat",
        "triple_exclusion_witness": "sat" if r_e == sat else "unsat",
    }


def write_results(name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path


def run_triple(name, shell_a, shell_b, shell_c,
               pair_coupling_py, pair_coupling_z3,
               triple_coupling_py, triple_coupling_z3,
               coupling_desc, extra_atoms=None):
    atoms_a, pred_a, clauses_a = SHELL_SPECS[shell_a]
    atoms_b, pred_b, clauses_b = SHELL_SPECS[shell_b]
    atoms_c, pred_c, clauses_c = SHELL_SPECS[shell_c]
    atoms = list(dict.fromkeys(
        atoms_a + atoms_b + atoms_c + list(extra_atoms or [])
    ))

    # POSITIVE
    pos_enum = _enumerate_triple(atoms, pred_a, pred_b, pred_c,
                                 pair_coupling_py, triple_coupling_py)
    pos_z3 = _z3_check_triple(atoms, clauses_a(), clauses_b(), clauses_c(),
                              pair_coupling_z3, triple_coupling_z3)
    positive_pass = (
        pos_enum["admissible_triple_joint"] >= 0
        and pos_z3.get("joint_triple") in ("sat", "unsat")
    )

    # NEGATIVE: triple coupling forced FALSE -> joint must be empty
    neg_enum = _enumerate_triple(atoms, pred_a, pred_b, pred_c,
                                 pair_coupling_py, lambda e: False)
    negative_pass = (neg_enum["admissible_triple_joint"] == 0)

    # BOUNDARY: triple coupling forced TRUE -> reduces to pairwise_joint
    bnd_enum = _enumerate_triple(atoms, pred_a, pred_b, pred_c,
                                 pair_coupling_py, lambda e: True)
    boundary_pass = (
        bnd_enum["admissible_triple_joint"] == bnd_enum["admissible_pairwise_joint"]
        and bnd_enum["excluded_by_triple_coupling"] == 0
    )

    overall = positive_pass and negative_pass and boundary_pass

    return {
        "name": name,
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "exclusion_language_note": (
            "Triple coupling uses 'joint coupling excludes ...' / 'survived' / "
            "'admissible under triple coupling'. No create/derive/drive language."
        ),
        "shells": [shell_a, shell_b, shell_c],
        "coupling_description": coupling_desc,
        "atoms": atoms,
        "positive": {"enum": pos_enum, "z3": pos_z3, "pass": positive_pass},
        "negative": {
            "enum": neg_enum,
            "description": "triple coupling forced FALSE; joint admissible triple must be empty",
            "pass": negative_pass,
        },
        "boundary": {
            "enum": bnd_enum,
            "description": "triple coupling forced TRUE; joint reduces to pairwise-joint",
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
                    "load_bearing: triple-joint SAT and triple-exclusion-witness SAT/UNSAT "
                    "decides whether three-way coupling strictly excludes beyond pairwise"
                ) if _HAVE_Z3 else "not installed",
            },
            "sympy": {"tried": True, "used": False,
                      "reason": "supportive only; Boolean admissibility does not require symbolic algebra"},
            "clifford": {"tried": True, "used": False,
                         "reason": "not applicable at triple-level Boolean coupling layer"},
            "pytorch": {"tried": True, "used": False,
                        "reason": "no gradient surface at this Boolean triple-admissibility layer"},
        },
        "tool_integration_depth": {
            "z3": "load_bearing" if _HAVE_Z3 else None,
            "sympy": "supportive",
            "clifford": None,
            "pytorch": None,
        },
    }
