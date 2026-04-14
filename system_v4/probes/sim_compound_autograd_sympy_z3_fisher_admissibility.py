#!/usr/bin/env python3
"""Compound triple-tool sim: torch.autograd + sympy + z3 -- Fisher information
positive-definiteness admissibility for a Bernoulli(p) family on p in (0,1).

Claim: the closed-form Fisher I(p) = 1/(p(1-p)) is admissible as a metric
(strictly positive) on the open interval; the boundary p in {0,1} is excluded.
Three irreducible tools:
 - sympy: derives I(p) symbolically from d^2/dp^2 of the negative log-likelihood;
   neither autograd (numeric) nor z3 (no calculus) can produce the closed form.
 - torch.autograd: computes the numeric Hessian at sample points and must agree
   with sympy's closed form; neither sympy nor z3 provides numeric Hessians over
   torch tensors.
 - z3: discharges the admissibility predicate forall p in (0,1) -> I(p)>0 as
   UNSAT of its negation over rational p; neither sympy nor autograd emits
   symbolic SAT/UNSAT certificates.
Ablate any one and the admissibility chain collapses.
"""
import json, os, numpy as np
import torch
import sympy as sp
import z3

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "autograd Hessian; irreducible numeric derivative"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT of negation over rationals; irreducible proof"},
    "cvc5": {"tried": False, "used": False, "reason": "z3 suffices"},
    "sympy": {"tried": True, "used": True, "reason": "closed-form Fisher derivation; irreducible symbolic layer"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
for k in ("pytorch", "sympy", "z3"):
    TOOL_INTEGRATION_DEPTH[k] = "load_bearing"


def sympy_fisher():
    p, x = sp.symbols('p x', positive=True)
    # log-likelihood for single Bernoulli draw
    ll = x * sp.log(p) + (1 - x) * sp.log(1 - p)
    d2 = sp.diff(ll, p, 2)
    # Fisher = -E_x[d2 ll] where E[x]=p
    I = sp.simplify(-d2.subs(x, p))
    return sp.simplify(I)  # expect 1/(p(1-p))


def autograd_hessian(p_val):
    # Fisher = -E_x[d2/dp2 log L]; expectation has x replaced by p after derivative.
    # Compute d2/dp2 of ll(x=1)=log p and d2/dp2 of ll(x=0)=log(1-p), weight by p and (1-p).
    p = torch.tensor(p_val, dtype=torch.float64, requires_grad=True)
    ll1 = torch.log(p)
    ll0 = torch.log(1 - p)
    d1_1 = torch.autograd.grad(ll1, p, create_graph=True)[0]
    d2_1 = torch.autograd.grad(d1_1, p, create_graph=True)[0]
    d1_0 = torch.autograd.grad(ll0, p, create_graph=True)[0]
    d2_0 = torch.autograd.grad(d1_0, p)[0]
    fisher = -(p_val * float(d2_1) + (1 - p_val) * float(d2_0))
    return fisher


def z3_positive_on_rationals():
    # Check: for a dense sample of rational p in (0,1), 1/(p(1-p)) > 0 is SAT and
    # negation (exists p in (0,1) with 1/(p(1-p)) <= 0) is UNSAT.
    s = z3.Solver()
    p = z3.Real('p')
    # admissibility predicate negation
    s.add(p > 0, p < 1)
    # rewrite 1/(p*(1-p)) > 0 via p*(1-p) > 0 (since p in (0,1) -> denom>0)
    s.add(p * (1 - p) <= 0)
    return s.check() == z3.unsat


def run_positive_tests():
    I_sym = sympy_fisher()
    p_sym = sp.Symbol('p', positive=True)
    target = 1 / (p_sym * (1 - p_sym))
    sym_ok = sp.simplify(I_sym - target) == 0
    # numeric cross-check at several p
    pts = [0.25, 0.5, 0.75]
    diffs = []
    for pv in pts:
        num = autograd_hessian(pv)
        closed = 1.0 / (pv * (1 - pv))
        diffs.append(abs(num - closed))
    num_ok = max(diffs) < 1e-6
    z3_ok = z3_positive_on_rationals()
    return {"sympy_closed_form_ok": bool(sym_ok), "autograd_matches": bool(num_ok),
            "max_diff": max(diffs), "z3_admissible_unsat_of_negation": bool(z3_ok),
            "pass": bool(sym_ok and num_ok and z3_ok)}


def run_negative_tests():
    # Wrong closed form: claim I(p) = 1/p. sympy must disagree, autograd must disagree,
    # and z3 must find SAT (counterexample exists in (0,1)).
    wrong = 1 / sp.Symbol('p')
    correct = sympy_fisher()
    disagree_sym = sp.simplify(wrong - correct) != 0
    num_diff = abs(autograd_hessian(0.25) - (1 / 0.25))
    # z3: exists p in (0,1) with 1/p != 1/(p(1-p))? that's p*(1-p) != p -> always for p!=0
    s = z3.Solver(); p = z3.Real('p')
    s.add(p > 0, p < 1, p * (1 - p) == p)  # requires p=0 which is excluded
    z3_excluded = s.check() == z3.unsat
    return {"sympy_disagrees": bool(disagree_sym), "autograd_diff_nonzero": num_diff > 1e-3,
            "z3_excludes_wrong_form": bool(z3_excluded),
            "pass": bool(disagree_sym and num_diff > 1e-3 and z3_excluded)}


def run_boundary_tests():
    # p -> 0+ : Fisher diverges; z3 checks that 1/(p(1-p)) is unbounded as p->0.
    # Use a witness: for any M>0, exists p in (0,1) with 1/(p(1-p)) > M.
    s = z3.Solver(); p = z3.Real('p'); M = z3.RealVal(1_000_000)
    s.add(p > 0, p < 1, 1 > M * p * (1 - p))
    witness_sat = s.check() == z3.sat
    # autograd near boundary: large value
    near = autograd_hessian(1e-4)
    return {"z3_unbounded_witness_sat": bool(witness_sat), "autograd_near_zero_large": near > 1e3,
            "pass": bool(witness_sat and near > 1e3)}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_compound_autograd_sympy_z3_fisher_admissibility",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_compound_autograd_sympy_z3_fisher_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
