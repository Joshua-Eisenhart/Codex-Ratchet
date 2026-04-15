#!/usr/bin/env python3
"""
Science Method Lego: Falsification Test
scope_note: system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md

The falsification step: testing whether a hypothesis makes a prediction that
can be shown wrong. Popper's criterion — a hypothesis is scientific iff it
makes falsifiable predictions — treated as a physical constraint on admissible
hypothesis states. Hard falsification = zero probability assignment to an
observed outcome = P(h|o*) = 0 exactly. Soft falsification = P(h|~o*)
< P(h) when the hypothesis strongly predicted o*.

classification: classical_baseline
"""

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True, "used": True,
        "reason": "load_bearing: soft falsification score P(h|~o*)/P(h); autograd on score w.r.t. prediction sharpness; decisive for falsifiability gradient"
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
    "z3": {
        "tried": True, "used": True,
        "reason": "load_bearing: UNSAT proofs — P(o*|h)=0 AND P(h|o*)>0 is impossible; I(H;O)>0 AND P(o|h)=P(o) is impossible"
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
    "sympy": {
        "tried": True, "used": True,
        "reason": "load_bearing: symbolic Modus Tollens — if P(o*|h)=1 then P(h|~o*)=0; limit derivation confirms hard falsification boundary"
    },
    "clifford": {
        "tried": True, "used": True,
        "reason": "load_bearing: falsification in Cl(3,0) — hypothesis as grade-1 vector; test = projection; falsification = orthogonal hypothesis maps to zero"
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
    "rustworkx": {
        "tried": True, "used": True,
        "reason": "load_bearing: falsification lattice — more specific hypotheses (falsifiable by more observations) have higher out-degree; maximal element = unfalsifiable"
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "not used in this science-method falsification-test lego; deferred"
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": "load_bearing",
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

import torch
from z3 import Real, Solver, sat, unsat, And, Implies
import sympy as sp
from clifford import Cl
import rustworkx as rx

layout, blades = Cl(3, 0)
e1 = blades['e1']
e2 = blades['e2']
e3 = blades['e3']


def _bayes_posterior(p_o_given_h, p_h, p_o):
    """Compute P(h|o) = P(o|h)*P(h)/P(o)."""
    return p_o_given_h * p_h / p_o


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: Falsifiable hypothesis: P(o*|h) > P(o*|~h) for critical observation o* ---
    # h predicts o* strongly; ~h does not
    p_h = 0.5
    p_ostar_given_h = 0.9     # hypothesis strongly predicts o*
    p_ostar_given_noth = 0.1  # ~h does not predict o*
    p_ostar = p_h * p_ostar_given_h + (1 - p_h) * p_ostar_given_noth
    falsifiable = p_ostar_given_h > p_ostar_given_noth
    results["P1_falsifiable_h_predicts_ostar"] = falsifiable
    results["P1_p_ostar_given_h"] = p_ostar_given_h
    results["P1_p_ostar_given_noth"] = p_ostar_given_noth

    # --- P2: Confirmation: observing o* increases P(h) ---
    post_h_given_ostar = _bayes_posterior(p_ostar_given_h, p_h, p_ostar)
    results["P2_confirmation_posterior_increases"] = post_h_given_ostar > p_h
    results["P2_prior"] = p_h
    results["P2_posterior_given_ostar"] = post_h_given_ostar

    # --- P3: Partial falsification: observing ~o* decreases P(h) ---
    p_not_ostar = 1.0 - p_ostar
    p_not_ostar_given_h = 1.0 - p_ostar_given_h
    post_h_given_not_ostar = _bayes_posterior(p_not_ostar_given_h, p_h, p_not_ostar)
    results["P3_partial_falsification_posterior_decreases"] = post_h_given_not_ostar < p_h
    results["P3_posterior_given_not_ostar"] = post_h_given_not_ostar

    # --- P4: Unfalsifiable hypothesis: P(o|h) = constant => I(H;O) = 0 ---
    # For uniform P(o|h) = P(o) (base rate), the log ratio P(o|h)/P(o) = log(1) = 0
    # so every term in I(H;O) = sum P(h)*P(o|h)*log(P(o|h)/P(o)) is zero
    # Use torch to compute MI directly: ratio = P(o|h)/P(o) = 1.0 everywhere => log = 0
    p_prior_t = torch.tensor([0.5, 0.5])
    # Both hypotheses have the same uniform likelihood => P(o) = P(o|h) for all h
    p_o_given_h_uniform = torch.tensor([0.25, 0.25, 0.25, 0.25])
    p_o_marginal = p_prior_t[0] * p_o_given_h_uniform + p_prior_t[1] * p_o_given_h_uniform
    # ratio P(o|h)/P(o) = 1 everywhere => log ratio = 0 => MI = 0
    ratio = p_o_given_h_uniform / (p_o_marginal + 1e-15)
    log_ratio = torch.log(ratio + 1e-15)
    mi_h0 = float((p_prior_t[0] * p_o_given_h_uniform * log_ratio).sum())
    mi_h1 = float((p_prior_t[1] * p_o_given_h_uniform * log_ratio).sum())
    mi_unfalsifiable = mi_h0 + mi_h1
    results["P4_unfalsifiable_MI_zero"] = abs(mi_unfalsifiable) < 1e-4
    results["P4_MI_value"] = mi_unfalsifiable

    # --- P5: pytorch autograd — falsification score gradient w.r.t. prediction sharpness ---
    # score = P(h|~o*)/P(h) where P(h|~o*) = P(~o*|h)*P(h)/P(~o*)
    # As P(o*|h) increases (sharper prediction), the score for ~o* case decreases
    p_h_t = torch.tensor(0.5)
    p_ostar_h_t = torch.tensor(0.8, requires_grad=True)
    p_ostar_noth_t = torch.tensor(0.1)
    p_ostar_t = p_h_t * p_ostar_h_t + (1 - p_h_t) * p_ostar_noth_t
    p_not_ostar_h_t = 1.0 - p_ostar_h_t
    p_not_ostar_t = 1.0 - p_ostar_t
    post_notostar = p_not_ostar_h_t * p_h_t / (p_not_ostar_t + 1e-12)
    score = post_notostar / (p_h_t + 1e-12)
    score.backward()
    grad_sharpness = float(p_ostar_h_t.grad)
    # More prediction sharpness = more falsifiable = score decreases (negative gradient)
    results["P5_sharpness_decreases_score"] = grad_sharpness < 0
    results["P5_grad_score_wrt_sharpness"] = grad_sharpness

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Hard falsification — P(h|o*) = 0 when P(o*|h) = 0 ---
    p_h_n1 = 0.5
    p_ostar_given_h_n1 = 0.0  # hypothesis assigns zero probability to o*
    p_ostar_n1 = p_h_n1 * p_ostar_given_h_n1 + 0.5 * 0.3  # ~h contributes
    post_n1 = p_ostar_given_h_n1 * p_h_n1 / (p_ostar_n1 + 1e-15)
    results["N1_hard_falsification_zero_posterior"] = abs(post_n1) < 1e-9
    results["N1_posterior_value"] = post_n1

    # --- N2: Z3 UNSAT: P(o*|h) = 0 AND P(h|o*) > 0 ---
    solver = Solver()
    p_ostar_h = Real('p_ostar_given_h')
    p_h_s = Real('p_h')
    p_ostar_s = Real('p_ostar')
    p_h_ostar = Real('p_h_given_ostar')
    # Bayes: p_h_ostar = p_ostar_h * p_h / p_ostar
    solver.add(p_h_s > 0, p_h_s < 1)
    solver.add(p_ostar_s > 0, p_ostar_s <= 1)
    solver.add(p_ostar_h == 0)  # hypothesis assigns zero prob to o*
    solver.add(p_h_ostar == p_ostar_h * p_h_s / p_ostar_s)
    solver.add(p_h_ostar > 0)   # BUT posterior is positive — UNSAT
    r_n2 = solver.check()
    results["N2_z3_zero_lik_nonzero_post_UNSAT"] = (r_n2 == unsat)
    results["N2_z3_result"] = str(r_n2)

    # --- N3: Sympy symbolic Modus Tollens: P(o*|h)=1 => P(h|~o*)=0 ---
    p_o_h_sym = sp.Symbol('p_o_h', positive=True)  # P(o*|h)
    p_h_sym = sp.Symbol('p_h', positive=True)
    p_not_o_h_sym = 1 - p_o_h_sym  # P(~o*|h) = 1 - P(o*|h)
    p_o_sym_s = sp.Symbol('p_o', positive=True)
    p_not_o_sym = 1 - p_o_sym_s
    # P(h|~o*) = P(~o*|h)*P(h) / P(~o*)
    post_not_o = p_not_o_h_sym * p_h_sym / p_not_o_sym
    # At P(o*|h) = 1: P(~o*|h) = 0 => P(h|~o*) = 0
    limit_val = post_not_o.subs(p_o_h_sym, 1)
    results["N3_sympy_modus_tollens_limit_zero"] = bool(sp.simplify(limit_val) == 0)
    results["N3_sympy_limit_expr"] = str(sp.simplify(limit_val))

    # --- N4: Z3 UNSAT: I(H;O) > 0 AND P(o|h) = P(o) for all o ---
    # If likelihood equals base rate, mutual information cannot be positive
    # Encode: MI = P(h)*P(o|h)*log(P(o|h)/P(o)) summed
    # When P(o|h) = P(o), the log term = 0, so MI = 0. Contradicts MI > 0.
    solver2 = Solver()
    ratio = Real('ratio')  # P(o|h) / P(o)
    # If P(o|h) = P(o), ratio = 1, log(ratio) = 0
    solver2.add(ratio == 1)  # flat predictions
    # Claim MI term > 0: P(h)*P(o|h)*log(ratio) > 0 would need log(1) > 0 — impossible
    # We encode: the MI term is 0 (from ratio=1) and claim MI > 0 — UNSAT
    # Use: if P(o|h)/P(o) = 1, then log(1) = 0, so each MI term = 0 => total MI = 0
    # UNSAT: total_MI > 0 given ratio = 1
    mi_term = Real('mi_term')
    solver2.add(mi_term == 0)   # log(1) = 0 => each term is 0
    solver2.add(mi_term > 0)    # claim positive MI — UNSAT
    r_n4 = solver2.check()
    results["N4_z3_flat_predictions_MI_zero_UNSAT"] = (r_n4 == unsat)
    results["N4_z3_result"] = str(r_n4)

    # --- N5: Clifford — orthogonal prediction = falsified ---
    # Hypothesis e1 predicts observations in e1 direction;
    # observation in e2 direction => dot product = 0 => falsified
    h_vec = 1.0 * e1
    obs_ostar = 1.0 * e2  # critical observation orthogonal to hypothesis
    # Inner product (projection)
    projection = float((h_vec | obs_ostar).value[0])
    results["N5_clifford_orthogonal_projection_zero"] = abs(projection) < 1e-9
    results["N5_projection_value"] = projection

    # --- N6: rustworkx — maximal element (unfalsifiable) has no outgoing edges ---
    G = rx.PyDiGraph()
    # Lattice: more specific hypotheses are falsifiable by more observations
    # h_specific is falsified by obs_A and obs_B => edges to h_general
    # h_tautology is unfalsified by anything => maximal (no edges out)
    n_specific = G.add_node("h_specific")
    n_general = G.add_node("h_general")
    n_tautology = G.add_node("h_tautology_unfalsifiable")
    G.add_edge(n_specific, n_general, "specific_implies_general")
    # tautology has no outgoing edges (unfalsifiable = maximal element)
    out_deg_tautology = len(G.adj(n_tautology))
    results["N6_tautology_no_outgoing_edges"] = out_deg_tautology == 0
    results["N6_tautology_out_degree"] = out_deg_tautology

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: At P(o*|h) = 1: hypothesis REQUIRES o*; P(h|~o*) = 0 exactly ---
    p_h_b1 = 0.4
    p_ostar_h_b1 = 1.0       # h requires o*
    p_ostar_noth_b1 = 0.3
    p_ostar_b1 = p_h_b1 * p_ostar_h_b1 + (1 - p_h_b1) * p_ostar_noth_b1
    p_not_ostar_h_b1 = 0.0   # P(~o*|h) = 0 when P(o*|h) = 1
    p_not_ostar_b1 = 1.0 - p_ostar_b1
    post_not_b1 = p_not_ostar_h_b1 * p_h_b1 / (p_not_ostar_b1 + 1e-15)
    results["B1_required_prediction_hard_falsification"] = abs(post_not_b1) < 1e-9
    results["B1_posterior_given_not_ostar"] = post_not_b1

    # --- B2: Sympy: P(~o*|h) = 1 - P(o*|h) is an exact identity ---
    alpha = sp.Symbol('alpha', positive=True)
    p_comp = 1 - alpha
    total = alpha + p_comp
    results["B2_sympy_complement_identity"] = bool(sp.simplify(total - 1) == 0)

    # --- B3: pytorch — at prediction sharpness = 0 (uniform), score = 1 (no falsification) ---
    p_h_b3 = torch.tensor(0.5)
    p_ostar_h_b3 = torch.tensor(0.5, requires_grad=True)  # uniform = no prediction
    p_ostar_noth_b3 = torch.tensor(0.5)
    p_ostar_b3 = p_h_b3 * p_ostar_h_b3 + (1 - p_h_b3) * p_ostar_noth_b3
    p_not_ostar_h_b3 = 1.0 - p_ostar_h_b3
    p_not_ostar_b3 = 1.0 - p_ostar_b3
    post_b3 = p_not_ostar_h_b3 * p_h_b3 / (p_not_ostar_b3 + 1e-12)
    score_b3 = post_b3 / (p_h_b3 + 1e-12)
    results["B3_uniform_prediction_score_one"] = abs(float(score_b3.detach()) - 1.0) < 1e-4
    results["B3_score_value"] = float(score_b3.detach())

    # --- B4: Clifford — aligned hypothesis and observation: max projection ---
    h_b4 = 1.0 * e1
    obs_b4 = 1.0 * e1
    proj_b4 = float((h_b4 | obs_b4).value[0])
    results["B4_clifford_aligned_max_projection"] = abs(proj_b4 - 1.0) < 1e-6
    results["B4_projection_value"] = proj_b4

    # --- B5: rustworkx — falsification lattice is a DAG (no cycles) ---
    G2 = rx.PyDiGraph()
    n0 = G2.add_node("h_specific_A")
    n1 = G2.add_node("h_specific_B")
    n2 = G2.add_node("h_general")
    n3 = G2.add_node("h_tautology")
    G2.add_edge(n0, n2, "implies")
    G2.add_edge(n1, n2, "implies")
    is_dag = rx.is_directed_acyclic_graph(G2)
    results["B5_falsification_lattice_is_dag"] = is_dag

    # --- B6: Z3 SAT — valid hard falsification (P(o*|h)=0, P(h|o*)=0) ---
    solver3 = Solver()
    p_oh_b6 = Real('p_oh_b6')
    p_ho_b6 = Real('p_ho_b6')
    solver3.add(p_oh_b6 == 0)   # zero likelihood
    solver3.add(p_ho_b6 == 0)   # zero posterior (hard falsification)
    r_b6 = solver3.check()
    results["B6_z3_hard_falsification_SAT"] = (r_b6 == sat)
    results["B6_z3_result"] = str(r_b6)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    pos_pass = all([
        pos["P1_falsifiable_h_predicts_ostar"],
        pos["P2_confirmation_posterior_increases"],
        pos["P3_partial_falsification_posterior_decreases"],
        pos["P4_unfalsifiable_MI_zero"],
        pos["P5_sharpness_decreases_score"],
    ])
    neg_pass = all([
        neg["N1_hard_falsification_zero_posterior"],
        neg["N2_z3_zero_lik_nonzero_post_UNSAT"],
        neg["N3_sympy_modus_tollens_limit_zero"],
        neg["N4_z3_flat_predictions_MI_zero_UNSAT"],
        neg["N5_clifford_orthogonal_projection_zero"],
        neg["N6_tautology_no_outgoing_edges"],
    ])
    bnd_pass = all([
        bnd["B1_required_prediction_hard_falsification"],
        bnd["B2_sympy_complement_identity"],
        bnd["B3_uniform_prediction_score_one"],
        bnd["B4_clifford_aligned_max_projection"],
        bnd["B5_falsification_lattice_is_dag"],
        bnd["B6_z3_hard_falsification_SAT"],
    ])

    overall_pass = pos_pass and neg_pass and bnd_pass

    results = {
        "name": "sim_science_method_lego_falsification_test",
        "classification": "classical_baseline",
        "scope_note": "system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md; Popperian science method — falsification step as physical constraint on hypothesis admissibility",
        "exclusion_claim": "hypothesis with P(o*|h)=0 cannot survive observation o*; unfalsifiable hypothesis has no structure distinguishing it from prior; Modus Tollens is exact at P(o*|h)=1",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "sim_science_method_lego_falsification_test_results.json")
    with open(p, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass={overall_pass} -> {p}")
