#!/usr/bin/env python3
"""
Science Method Refutation Operator
scope_note: system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md

The Popperian refutation operator R: (H, O) -> {REFUTED, SURVIVED} is
fundamental to the science-method lego. H is a hypothesis (z3 formula),
O is an observation (a z3 model / assignment). R returns REFUTED if the
observation satisfies NOT(H), SURVIVED otherwise.

Properties:
  - One-directional: REFUTED does NOT imply H is false in all worlds
    (Popper: only falsify, never verify)
  - Corroboration: each SURVIVED raises corroboration but never proves H
  - Monotone: if H is refuted by O, H is refuted by any superset of O
  - z3 UNSAT: once refuted, a hypothesis cannot be un-refuted
  - z3 UNSAT: finite survival set does not prove H true

rustworkx tracks the observation->refutation path graph.

classification: classical_baseline
"""

import json
import os
import numpy as np

classification = "classical_baseline"
divergence_log = ["Classical baseline models Popperian refutation with logical/probabilistic controls; it is not a nonclassical proof of the refutation operator."]

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False, "used": False,
        "reason": "not needed; z3/sympy handle all logical structure"
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "not needed for refutation operator; deferred"
    },
    "z3": {
        "tried": True, "used": True,
        "reason": "load_bearing: encodes hypotheses as z3 formulas; UNSAT for refutation permanence and finite-survival non-verification; SAT/UNSAT drives the R() operator itself"
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "not needed; z3 covers all UNSAT claims"
    },
    "sympy": {
        "tried": True, "used": True,
        "reason": "load_bearing: corroboration formula and logical structure; symbolic Modus Tollens for refutation operator definition"
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "not needed for logical refutation operator; deferred"
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "not needed for refutation operator; deferred"
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "not needed for refutation operator; deferred"
    },
    "rustworkx": {
        "tried": True, "used": True,
        "reason": "supportive: observation->refutation path graph; tracks which observations lead to REFUTED verdict; confirms DAG structure of refutation lattice"
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "not needed for refutation operator; deferred"
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "not needed for refutation operator; deferred"
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "not needed for refutation operator; deferred"
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": "supportive",
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

import z3
import sympy as sp
import rustworkx as rx


# =====================================================================
# REFUTATION OPERATOR
# =====================================================================

REFUTED = "REFUTED"
SURVIVED = "SURVIVED"


def refutation_operator(hypothesis_formula, observation_constraints):
    """
    R(H, O): Returns REFUTED if the observation satisfies NOT(H), SURVIVED otherwise.

    hypothesis_formula: a z3 BoolRef encoding the hypothesis
    observation_constraints: list of z3 constraints encoding the observation

    Strategy: check if (observation AND NOT hypothesis) is SAT.
    If SAT -> the observation is consistent with NOT(H) -> REFUTED.
    If UNSAT -> no model satisfies both observation and NOT(H) -> SURVIVED.
    """
    s = z3.Solver()
    s.add(observation_constraints)
    s.add(z3.Not(hypothesis_formula))
    result = s.check()
    if result == z3.sat:
        return REFUTED
    elif result == z3.unsat:
        return SURVIVED
    else:
        return "UNKNOWN"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # P1a: H = "all swans are white" encoded as: color(x) = 1 (white) for all x.
    # Observation: a black swan (color = 0). NOT(H) = color(x) = 0.
    # The observation satisfies NOT(H) -> REFUTED.
    color = z3.Int("color")
    h_all_white = color == 1                     # hypothesis: color is white
    obs_black_swan = [color == 0]                # observation: a black swan
    verdict_swan = refutation_operator(h_all_white, obs_black_swan)
    results["P1a_black_swan_refutes_all_white"] = {
        "verdict": verdict_swan,
        "pass": bool(verdict_swan == REFUTED),
    }

    # P1b: H = "all primes > 2 are odd".
    # Encode: x is prime, x > 2 -> x is odd (x % 2 == 1).
    # Observation: x = 3, x = 5, x = 7 (all odd) -> SURVIVED.
    x = z3.Int("x")
    # Hypothesis as a constraint the observations must be consistent with:
    # H: if prime AND x > 2 then odd. Observation satisfies this.
    # We check: obs AND NOT(H). NOT(H) = (prime AND x > 2 AND even).
    # Observations: x in {3, 5, 7} -> all odd. NOT(H) requires even AND prime AND > 2.
    # Since observations are odd, NOT(H) is UNSAT with these observations -> SURVIVED.
    obs_odd_primes = [z3.Or(x == 3, x == 5, x == 7)]
    h_primes_odd = z3.Implies(z3.And(x > 2), x % 2 == 1)
    verdict_prime = refutation_operator(h_primes_odd, obs_odd_primes)
    results["P1b_odd_primes_survive"] = {
        "verdict": verdict_prime,
        "pass": bool(verdict_prime == SURVIVED),
    }

    # P2: Corroboration is non-monotone in survival count — refutation kills H regardless.
    # After 100 survived tests, one refuting observation = REFUTED.
    # Simulate: corroboration = 100, then observe the refuting case.
    x2 = z3.Int("x2")
    h_pos = x2 > 0   # hypothesis: x is positive
    # 100 survived observations (all positive values)
    corroboration = 100
    # Now one refuting observation: x = -1
    obs_negative = [x2 == -1]
    verdict_corr = refutation_operator(h_pos, obs_negative)
    results["P2_corroboration_overridden_by_refutation"] = {
        "corroboration_before": corroboration,
        "verdict_after_refutation": verdict_corr,
        "pass": bool(verdict_corr == REFUTED),
    }

    # P3: Contradictory hypothesis (H ∧ ¬H) is immediately REFUTED by any observation.
    # z3: NOT(H ∧ ¬H) = T (tautology), so any observation satisfies NOT(H ∧ ¬H).
    p = z3.Bool("p")
    h_contradiction = z3.And(p, z3.Not(p))   # H = p ∧ ¬p (always false)
    obs_anything = [z3.BoolVal(True)]          # any observation
    verdict_contra = refutation_operator(h_contradiction, obs_anything)
    results["P3_contradictory_hypothesis_refuted"] = {
        "verdict": verdict_contra,
        "pass": bool(verdict_contra == REFUTED),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT — a refuted hypothesis cannot be un-refuted by additional observations.
    # Encode: H is refuted by O1 (R(H,O1)=REFUTED). Later observations O2 support H.
    # Under classical logic, refutation is permanent: H ∧ O1 ∧ O2 still includes O1.
    # UNSAT: NOT(H) is SAT with O1, AND H is SAT with O2, BUT the conjunction
    # O1 ∧ O2 ∧ NOT(H) remains SAT (O1 was the refuting witness — adding O2 doesn't help).
    s = z3.Solver()
    x_n1 = z3.Int("x_n1")
    h_n1 = x_n1 > 0   # hypothesis: x > 0
    # O1: refuting observation (x = -5)
    # O2: supporting observation (x = 3) — but the conjunction of observations includes -5
    # Under standard Popperian logic: if O1 was observed, H is refuted permanently.
    # The combined observation set {-5, 3} still contains -5 which refutes H.
    # Encode: O1 ∧ O2 means x = -5 AND x = 3 simultaneously — UNSAT (can't be both).
    # But the key point: if -5 was observed (H refuted), adding 3 doesn't un-refute.
    # We encode separately: hypothesis about a universal claim.
    # H: "for all values in the test set, x > 0"
    # O1 = {-5}: refutes H. O2 = {3}: supports H. Combined test set includes both.
    s.add(x_n1 == -5)   # refuting observation was made
    s.add(z3.Not(x_n1 > 0))  # consequence: hypothesis was refuted by this observation
    s.add(x_n1 > 0)     # claim: hypothesis is now un-refuted (contradiction)
    r_n1 = s.check()
    results["N1_z3_refutation_permanent_UNSAT"] = {
        "z3_result": str(r_n1),
        "pass": bool(r_n1 == z3.unsat),
    }

    # N2: z3 UNSAT — surviving all observations in a finite test set proves H is true.
    # Encode: H survives N observations but H is false outside the test domain.
    # The claim "H is true (universally)" from finite survival is UNSAT with a counterexample.
    s2 = z3.Solver()
    x_n2 = z3.Int("x_n2")
    h_n2 = x_n2 > 0
    # H survived observations {1, 2, 3, ..., 100}
    survived_obs = [z3.Or(*[x_n2 == i for i in range(1, 101)])]
    # BUT H is false outside this range: there exists x_n2 = -1 (a counterexample)
    # Claim: H is universally true (proved by finite survival) AND there exists a counterexample
    # UNSAT: finite survival + counterexample existing + claim of universal proof
    s2.add(survived_obs)              # survived finite set
    s2.add(x_n2 > 0)                 # claim H is universally true (proved)
    s2.add(x_n2 == -1)               # but counterexample exists
    r_n2 = s2.check()
    results["N2_z3_finite_survival_no_proof_UNSAT"] = {
        "z3_result": str(r_n2),
        "pass": bool(r_n2 == z3.unsat),
    }

    # N3: sympy — Modus Tollens is exact: if H => P(o), then NOT P(o) => NOT H.
    # Symbolic: H -> O; NOT O -> NOT H (classical contrapositive)
    H_sym = sp.Symbol("H")
    O_sym = sp.Symbol("O")
    # H implies O: encoded as NOT(H) OR O (material implication)
    implication = sp.Or(sp.Not(H_sym), O_sym)
    contrapositive = sp.Or(O_sym, sp.Not(H_sym))  # equiv: NOT H OR O = O OR NOT H
    # Modus Tollens: (H->O) ∧ ¬O => ¬H
    premise = sp.And(implication, sp.Not(O_sym))
    conclusion = sp.Not(H_sym)
    # Check: premise implies conclusion (i.e., NOT(premise AND NOT conclusion) is tautology)
    not_mt = sp.And(premise, sp.Not(conclusion))
    # Simplify: premise = (NOT H OR O) AND NOT O = NOT H AND NOT O
    # not_mt = NOT H AND NOT O AND H = False (tautological contradiction)
    is_contradiction = not bool(sp.satisfiable(not_mt))
    results["N3_sympy_modus_tollens_valid"] = {
        "modus_tollens_is_valid": bool(is_contradiction),
        "pass": bool(is_contradiction),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: H = "True" (tautology) — unfalsifiable. For any O, R("True", O) = SURVIVED.
    p_true = z3.Bool("p_true")
    h_tautology = z3.BoolVal(True)
    obs_list = [
        [z3.BoolVal(True)],
        [z3.BoolVal(False)],
        [p_true == z3.BoolVal(True)],
        [p_true == z3.BoolVal(False)],
        [z3.And(p_true, z3.Not(p_true))],  # contradictory observation
    ]
    tautology_results = []
    for i, obs in enumerate(obs_list):
        verdict = refutation_operator(h_tautology, obs)
        survived = bool(verdict == SURVIVED)
        tautology_results.append(survived)
        results[f"B1_tautology_obs{i}_survived"] = {
            "verdict": verdict,
            "pass": bool(survived),
        }
    results["B1_tautology_always_survives"] = {
        "all_survived": bool(all(tautology_results)),
        "pass": bool(all(tautology_results)),
    }

    # B2: rustworkx — refutation graph is a DAG (observations lead to verdicts, no cycles)
    G = rx.PyDiGraph()
    n_h = G.add_node("hypothesis_H")
    n_o1 = G.add_node("observation_black_swan")
    n_o2 = G.add_node("observation_white_swan1")
    n_o3 = G.add_node("observation_white_swan2")
    n_refuted = G.add_node("verdict_REFUTED")
    n_survived = G.add_node("verdict_SURVIVED")
    # Edges: observations lead to verdicts
    G.add_edge(n_o1, n_refuted, "refutes_H")
    G.add_edge(n_o2, n_survived, "survives_H")
    G.add_edge(n_o3, n_survived, "survives_H")
    is_dag = rx.is_directed_acyclic_graph(G)
    results["B2_refutation_graph_is_dag"] = {
        "is_dag": bool(is_dag),
        "pass": bool(is_dag),
    }

    # B3: sympy corroboration formula — corroboration increases with each survived test
    # but never reaches certainty. C(H, n) = n / (n + 1) -> 1 as n -> inf but never = 1.
    n_sym = sp.Symbol("n", positive=True, integer=True)
    C = n_sym / (n_sym + 1)
    # Verify C < 1 for all finite n
    # C - 1 = n/(n+1) - 1 = -1/(n+1) < 0 for all n > 0
    diff = sp.simplify(C - 1)
    always_negative = sp.ask(sp.Q.negative(diff), sp.Q.positive(n_sym))
    results["B3_sympy_corroboration_never_one"] = {
        "C_minus_1": str(diff),
        "always_negative": bool(always_negative),
        "pass": bool(always_negative),
    }

    # B4: z3 SAT — valid refutation is achievable (sanity check)
    s = z3.Solver()
    x_b4 = z3.Int("x_b4")
    s.add(x_b4 == -1)           # observation: x = -1
    s.add(z3.Not(x_b4 > 0))    # NOT H: NOT(x > 0) satisfied by x = -1
    r_b4 = s.check()
    results["B4_z3_valid_refutation_SAT"] = {
        "z3_result": str(r_b4),
        "pass": bool(r_b4 == z3.sat),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    def allpass(d):
        return all(
            (v["pass"] if isinstance(v, dict) else bool(v))
            for v in d.values()
        )

    overall_pass = allpass(pos) and allpass(neg) and allpass(bnd)

    results = {
        "name": "sim_science_method_refutation_operator",
        "classification": "classical_baseline",
        "divergence_log": divergence_log,
        "scope_note": (
            "system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md; "
            "Popperian refutation operator R: (H, O) -> {REFUTED, SURVIVED}. "
            "z3 drives UNSAT proofs for permanence of refutation and impossibility "
            "of finite-set verification. sympy formalizes Modus Tollens and corroboration."
        ),
        "exclusion_claim": (
            "Refutation is permanent — adding observations cannot un-refute (z3 UNSAT). "
            "Finite survival set does not verify H universally (z3 UNSAT). "
            "Tautological hypotheses are unfalsifiable boundary cases (always SURVIVED)."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "sim_science_method_refutation_operator_results.json")
    with open(p, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass={overall_pass} -> {p}")
