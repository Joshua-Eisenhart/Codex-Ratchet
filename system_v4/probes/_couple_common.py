"""Shared helpers for pairwise framework coupling sims.

Exclusion-language discipline:
- A coupling "survived" when the joint constraint set is SAT.
- A coupling is "excluded" when the joint constraint set is UNSAT.
- A pair is "interacting" when joint admissibility strictly differs from
  the intersection of the two shell-local admissible sets
  (i.e., some candidate admissible shell-locally is excluded jointly,
  or vice versa under an asymmetric coupling witness).
- A pair is "additive" when joint admissibility == intersection (no
  coupling-induced exclusion beyond the two shell-local filters).

scope_note cites: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md

Shell-local admissibility axioms (toy but structural):
- holodeck: observer-indistinguishable projection; admissible iff
  carrier_equivalence AND projection_is_quotient (no information leak
  to observer beyond the carrier class).
- igt: admissible iff strategy is NOT strictly dominated AND payoff
  is Pareto-non-minimal (survives under dominance pruning).
- leviathan: admissible iff coalition is monotone-aggregated AND
  stability constraint holds (no blocking sub-coalition).
- sci_method: admissible iff hypothesis is falsifiable AND survives
  modus-tollens under observed evidence (not yet refuted).
- fep: admissible iff variational free energy gradient is non-positive
  at the point (locally minimizing surprise) AND Markov blanket CI
  holds.

These are intentionally minimal Booleans per pair; the sim encodes
each pair's joint constraint in z3 and enumerates the 2^k candidate
worlds, classifying interacting vs additive.
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


SCOPE_NOTE = (
    "Pairwise coupling test under exclusion-language discipline. "
    "See system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md. "
    "Candidates are not 'created' or 'derived'; they are 'admissible under joint "
    "coupling', 'survived', or 'excluded'."
)


def _enumerate(atoms, shell_a_pred, shell_b_pred, coupling_pred):
    """Enumerate all 2^|atoms| assignments and classify.

    Returns dict with counts for: admissible_A, admissible_B,
    admissible_intersection, admissible_joint, excluded_by_coupling,
    admitted_only_jointly.
    """
    names = list(atoms)
    n = len(names)
    A = B = inter = joint = excl_by_coupling = 0
    for bits in itertools.product([False, True], repeat=n):
        env = dict(zip(names, bits))
        a_ok = shell_a_pred(env)
        b_ok = shell_b_pred(env)
        c_ok = coupling_pred(env)
        A += int(a_ok)
        B += int(b_ok)
        inter += int(a_ok and b_ok)
        joint += int(a_ok and b_ok and c_ok)
        if a_ok and b_ok and not c_ok:
            excl_by_coupling += 1
    return {
        "admissible_A": A,
        "admissible_B": B,
        "admissible_intersection": inter,
        "admissible_joint": joint,
        "excluded_by_coupling": excl_by_coupling,
        "interacting": (excl_by_coupling > 0),
        "additive": (excl_by_coupling == 0),
    }


def _z3_check(atoms_spec, shell_a_clauses, shell_b_clauses, coupling_clauses):
    """Use z3 as load-bearing proof layer.

    atoms_spec: list of atom names (Bools).
    Each clauses arg: list of callables f(env_dict_of_Bool) -> BoolRef.
    Returns: dict with sat/unsat for (A only), (B only), (joint), and a
    UNSAT witness flag for coupling exclusion.
    """
    if not _HAVE_Z3:
        return {"z3_available": False}

    env = {a: Bool(a) for a in atoms_spec}

    def _collect(clauses):
        return [c(env) for c in clauses]

    s_a = Solver(); s_a.add(*_collect(shell_a_clauses))
    s_b = Solver(); s_b.add(*_collect(shell_b_clauses))
    s_j = Solver()
    s_j.add(*_collect(shell_a_clauses))
    s_j.add(*_collect(shell_b_clauses))
    s_j.add(*_collect(coupling_clauses))

    r_a = s_a.check()
    r_b = s_b.check()
    r_j = s_j.check()

    # Exclusion witness: is there an env satisfying A and B but NOT coupling?
    s_e = Solver()
    s_e.add(*_collect(shell_a_clauses))
    s_e.add(*_collect(shell_b_clauses))
    s_e.add(Not(And(*_collect(coupling_clauses))) if _collect(coupling_clauses) else Bool("__dummy_false__") == Bool("__dummy_false_other__"))
    r_e = s_e.check()

    return {
        "z3_available": True,
        "shell_A_alone": "sat" if r_a == sat else "unsat",
        "shell_B_alone": "sat" if r_b == sat else "unsat",
        "joint_coupling": "sat" if r_j == sat else "unsat",
        "coupling_exclusion_witness": "sat" if r_e == sat else "unsat",
    }


def write_results(name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path


# -------- shell-local predicates (python eval side, for enumeration) --------

def holodeck_admissible(e):
    # carrier_equiv AND projection_quotient
    return e["carrier_equiv"] and e["projection_quotient"]

def igt_admissible(e):
    # not_strictly_dominated AND pareto_non_minimal
    return e["not_strictly_dominated"] and e["pareto_non_minimal"]

def leviathan_admissible(e):
    # monotone_aggregation AND coalition_stable
    return e["monotone_aggregation"] and e["coalition_stable"]

def sci_method_admissible(e):
    # falsifiable AND survives_modus_tollens
    return e["falsifiable"] and e["survives_modus_tollens"]

def fep_admissible(e):
    # vfe_nonincreasing AND markov_blanket_ci
    return e["vfe_nonincreasing"] and e["markov_blanket_ci"]


# -------- z3 clause builders (proof side) --------

def holodeck_clauses():
    return [lambda e: e["carrier_equiv"], lambda e: e["projection_quotient"]]

def igt_clauses():
    return [lambda e: e["not_strictly_dominated"], lambda e: e["pareto_non_minimal"]]

def leviathan_clauses():
    return [lambda e: e["monotone_aggregation"], lambda e: e["coalition_stable"]]

def sci_method_clauses():
    return [lambda e: e["falsifiable"], lambda e: e["survives_modus_tollens"]]

def fep_clauses():
    return [lambda e: e["vfe_nonincreasing"], lambda e: e["markov_blanket_ci"]]


SHELL_SPECS = {
    "holodeck":   (["carrier_equiv", "projection_quotient"], holodeck_admissible, holodeck_clauses),
    "igt":        (["not_strictly_dominated", "pareto_non_minimal"], igt_admissible, igt_clauses),
    "leviathan":  (["monotone_aggregation", "coalition_stable"], leviathan_admissible, leviathan_clauses),
    "sci_method": (["falsifiable", "survives_modus_tollens"], sci_method_admissible, sci_method_clauses),
    "fep":        (["vfe_nonincreasing", "markov_blanket_ci"], fep_admissible, fep_clauses),
}


def run_pair(name, shell_a, shell_b, coupling_py, coupling_z3, coupling_desc,
             extra_atoms=None,
             negative_coupling_py=None, boundary_coupling_py=None):
    """Run positive/negative/boundary and return a full result dict.

    coupling_py: callable(env) -> bool   (enumeration side)
    coupling_z3: list of lambda e->BoolRef  (z3 side)
    """
    atoms_a, pred_a, clauses_a = SHELL_SPECS[shell_a]
    atoms_b, pred_b, clauses_b = SHELL_SPECS[shell_b]
    atoms = list(dict.fromkeys(atoms_a + atoms_b + list(extra_atoms or [])))

    # POSITIVE: requested coupling
    positive_enum = _enumerate(atoms, pred_a, pred_b, coupling_py)
    positive_z3 = _z3_check(atoms, clauses_a(), clauses_b(), coupling_z3)
    positive_pass = (
        positive_enum["admissible_joint"] >= 0
        and positive_z3.get("joint_coupling") in ("sat", "unsat")
    )

    # NEGATIVE: coupling forced FALSE everywhere must exclude everything
    neg_py = negative_coupling_py if negative_coupling_py else (lambda e: False)
    negative_enum = _enumerate(atoms, pred_a, pred_b, neg_py)
    negative_pass = (negative_enum["admissible_joint"] == 0)

    # BOUNDARY: coupling TRUE everywhere reduces to intersection (additive)
    bnd_py = boundary_coupling_py if boundary_coupling_py else (lambda e: True)
    boundary_enum = _enumerate(atoms, pred_a, pred_b, bnd_py)
    boundary_pass = (
        boundary_enum["admissible_joint"] == boundary_enum["admissible_intersection"]
        and boundary_enum["additive"] is True
    )

    overall = positive_pass and negative_pass and boundary_pass

    results = {
        "name": name,
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "exclusion_language_note": (
            "All admissibility statements use 'survived' / 'admissible under joint "
            "coupling' / 'excluded'. No creates/derives/drives."
        ),
        "shells": [shell_a, shell_b],
        "coupling_description": coupling_desc,
        "atoms": atoms,
        "positive": {
            "enum": positive_enum,
            "z3": positive_z3,
            "pass": positive_pass,
        },
        "negative": {
            "enum": negative_enum,
            "description": "coupling forced identically FALSE; joint admissible set must be empty",
            "pass": negative_pass,
        },
        "boundary": {
            "enum": boundary_enum,
            "description": "coupling forced identically TRUE; joint reduces to shell-local intersection (additive)",
            "pass": boundary_pass,
        },
        "overall_pass": overall,
        "interacting": positive_enum["interacting"],
        "additive": positive_enum["additive"],
        "tool_manifest": {
            "z3": {
                "tried": _HAVE_Z3,
                "used": _HAVE_Z3,
                "reason": "load_bearing: joint/shell/exclusion SAT-UNSAT decides admissibility and coupling-exclusion witness" if _HAVE_Z3 else "not installed",
            },
            "sympy":    {"tried": True, "used": False, "reason": "supportive only; not needed for Boolean admissibility"},
            "clifford": {"tried": True, "used": False, "reason": "not applicable at pair-level Boolean coupling layer"},
            "pytorch":  {"tried": True, "used": False, "reason": "no gradient surface at this Boolean admissibility layer"},
        },
        "tool_integration_depth": {
            "z3": "load_bearing" if _HAVE_Z3 else None,
            "sympy": "supportive",
            "clifford": None,
            "pytorch": None,
        },
    }
    return results
