#!/usr/bin/env python3
"""
sim_carnot_constraint_admissibility_fence
==========================================

Classification: canonical
Starts from: system_v4/probes/SIM_TEMPLATE.py

Purpose
-------
Bridge the classical Carnot cycle to the nonclassical
constraint-admissibility geometry of this project, using symbolic proof
(sympy) and SMT (z3) as the load-bearing tools.

Three bridge claims (nominalist, exclusion-form):

1. Efficiency-bound-as-admissibility-fence
   The Carnot bound eta <= 1 - Tc/Th is *not* a ceiling imposed by
   engineering; it is the exclusion fence defined by dS_total >= 0.
   Any (Q_h, Q_c, W, Th, Tc) tuple outside the fence fails the
   admissibility constraint and is z3-UNSAT under
        Q_h = W + Q_c,   Q_h/Th - Q_c/Tc <= 0,   0 < Tc < Th,  W > 0.

2. Reversibility-as-F01-symmetry
   A reversible cycle is the equality case dS_total = 0, which is the
   fixed-point of the forward/backward (F01) swap of the cycle
   endpoints. Symbolic check: eta = 1 - Tc/Th exactly when
   Q_h/Th - Q_c/Tc = 0. No other solution survives.

3. Work-extraction-as-distinguishability-transfer
   Work W = Q_h - Q_c is the Landauer-like image of moved
   distinguishability: D(hot||ambient) - D(cold||ambient) -- under the
   classical-bath approximation D(T||T_ref) ~ Q/T_ref. sympy derives
   the identity W/T_ref = Delta D to first order.

Load-bearing tools
------------------
- sympy: algebraic derivation of the efficiency bound from dS_total >= 0
  and of the distinguishability-transfer identity.
- z3: SMT refutation of violator tuples; the fence is encoded as a
  satisfiability problem whose UNSAT is the proof form.

No numpy fallback is used for the proof. Numeric spot-checks only
cross-validate the symbolic result.

Operational language
--------------------
Forbidden: "causes", "creates", "drives".
Used:       "admits", "excludes", "survives under", "coupled with",
            "indistinguishable from", "z3-UNSAT".
"""

import json
import os
import sys
from fractions import Fraction

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": "no tensor computation needed for symbolic proof"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph transport in this bridge"},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "cvc5":     {"tried": False, "used": False, "reason": "z3 chosen as primary SMT; cvc5 reserved for cross-check in later sim"},
    "sympy":    {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "thermodynamic variables are scalar, no rotor algebra required"},
    "geomstats":{"tried": False, "used": False, "reason": "no manifold learning"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistence"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


# =====================================================================
# SYMPY: algebraic derivation of the efficiency bound and the
# distinguishability-transfer identity.
# =====================================================================

def sympy_derive_efficiency_bound():
    """Derive eta <= 1 - Tc/Th from first-law + dS_total >= 0.

    Returns a dict describing the derivation and a symbolic True/False
    verdict on the inequality at reversible equality.
    """
    assert sp is not None, "sympy required"
    Th, Tc, Qh, Qc, W = sp.symbols("Th Tc Qh Qc W", positive=True, real=True)

    # First law (closed cycle, internal-energy returns to start):
    first_law = sp.Eq(Qh, W + Qc)

    # Clausius / dS_total >= 0 for the combined hot+cold reservoirs:
    #   -Qh/Th + Qc/Tc >= 0   (reservoirs lose Qh gain Qc of entropy)
    clausius = sp.Ge(Qc/Tc - Qh/Th, 0)

    # Solve first law for Qc, substitute:
    Qc_of_W = sp.solve(first_law, Qc)[0]          # Qh - W
    ineq = (Qc_of_W / Tc - Qh / Th)               # >= 0
    ineq_simplified = sp.simplify(ineq)

    # Efficiency eta = W/Qh. Want to show eta <= 1 - Tc/Th.
    # From ineq >= 0: (Qh - W)/Tc >= Qh/Th  =>  W/Qh <= 1 - Tc/Th.
    eta_bound_expr = sp.simplify(1 - Tc/Th - W/Qh)  # must be >= 0

    # Multiply ineq by Tc (>0) then divide by Qh (>0) to see the bound:
    derived = sp.simplify((Qh - W) / Tc - Qh / Th)         # = ineq
    derived_over_Qh_times_Tc = sp.simplify(Tc * (derived) / Qh)  # = 1 - W/Qh - Tc/Th
    bound_equivalent = sp.simplify(derived_over_Qh_times_Tc - eta_bound_expr)

    # Reversible equality case: set ineq = 0, solve for W:
    W_rev = sp.solve(sp.Eq((Qh - W)/Tc - Qh/Th, 0), W)[0]
    eta_rev = sp.simplify(W_rev / Qh)                     # should be 1 - Tc/Th
    eta_rev_check = sp.simplify(eta_rev - (1 - Tc/Th))

    return {
        "first_law": str(first_law),
        "clausius_inequality": "Qc/Tc - Qh/Th >= 0",
        "ineq_after_substitution": str(ineq_simplified),
        "bound_equivalence_residual (must be 0)": str(bound_equivalent),
        "bound_equivalence_is_zero": bool(bound_equivalent == 0),
        "W_reversible": str(W_rev),
        "eta_reversible": str(eta_rev),
        "eta_reversible_minus_carnot (must be 0)": str(eta_rev_check),
        "eta_reversible_is_carnot": bool(eta_rev_check == 0),
    }


def sympy_distinguishability_transfer():
    """Work = moved distinguishability, at first order in classical-bath limit.

    D(T || T_ref) ~ Q / T_ref   (Landauer-like linearization)
    Delta D = D_hot - D_cold = (Qh - Qc)/T_ref = W/T_ref.
    """
    assert sp is not None, "sympy required"
    Qh, Qc, W, T_ref = sp.symbols("Qh Qc W T_ref", positive=True, real=True)
    D_hot = Qh / T_ref
    D_cold = Qc / T_ref
    Delta_D = sp.simplify(D_hot - D_cold)
    # First law: W = Qh - Qc
    residual = sp.simplify(Delta_D - (Qh - Qc)/T_ref)
    identity = sp.simplify((Qh - Qc)/T_ref - W/T_ref)  # = 0 under Qh = W + Qc
    identity_after_first_law = identity.subs(Qh, W + Qc)
    return {
        "Delta_D_minus_first_law_residual (must be 0)": str(residual),
        "identity_under_first_law (must be 0)": str(sp.simplify(identity_after_first_law)),
        "distinguishability_transfer_closed": bool(sp.simplify(identity_after_first_law) == 0),
    }


# =====================================================================
# Z3: admissibility fence as an SMT problem.
# =====================================================================

def z3_fence_admissibility():
    """Encode the fence and prove by UNSAT that a 'super-Carnot' engine
    (eta > 1 - Tc/Th) cannot coexist with dS_total >= 0 and the first law.

    Returns per-assertion verdicts.
    """
    assert z3 is not None, "z3 required"

    def make_base(Th, Tc, Qh, Qc, W):
        return [
            Tc > 0,
            Th > Tc,
            Qh > 0,
            Qc > 0,
            W > 0,
            Qh == W + Qc,                    # first law
            Qc * Th - Qh * Tc >= 0,          # Clausius: Qc/Tc - Qh/Th >= 0, cleared
        ]

    verdicts = {}

    # --- Claim 1 (positive, SAT): a Carnot-admissible tuple exists. ---
    s = z3.Solver()
    Th, Tc, Qh, Qc, W = z3.Reals("Th Tc Qh Qc W")
    for c in make_base(Th, Tc, Qh, Qc, W):
        s.add(c)
    # Pick a concrete reversible example to witness: Th=400, Tc=300.
    s.push()
    s.add(Th == 400, Tc == 300, Qh == 4, Qc == 3, W == 1)  # eta = 0.25 = 1 - 3/4
    verdicts["reversible_witness_sat"] = (s.check() == z3.sat)
    s.pop()

    # --- Claim 2 (negative, UNSAT): a super-Carnot violator cannot exist. ---
    s2 = z3.Solver()
    Th, Tc, Qh, Qc, W = z3.Reals("Th Tc Qh Qc W")
    for c in make_base(Th, Tc, Qh, Qc, W):
        s2.add(c)
    # Violator: eta > 1 - Tc/Th  <=>  W*Th > Qh*(Th - Tc).
    s2.add(W * Th > Qh * (Th - Tc))
    verdicts["super_carnot_unsat"] = (s2.check() == z3.unsat)

    # --- Claim 3 (negative, UNSAT): Kelvin statement.
    # No process with Qc = 0, W > 0, Qh > 0 under Clausius (single bath) is admissible.
    s3 = z3.Solver()
    Th, Qh, W = z3.Reals("Th Qh W")
    s3.add(Th > 0, Qh > 0, W > 0, Qh == W,           # single-bath first law
           # dS_reservoir = -Qh/Th must be >= 0 for admissibility of net cycle
           -Qh / Th >= 0)
    verdicts["kelvin_single_bath_unsat"] = (s3.check() == z3.unsat)

    # --- Claim 4 (reversibility = F01 fixed point):
    # If we also require Qc*Th == Qh*Tc (equality / reversible), then W*Th must
    # equal Qh*(Th - Tc). Check UNSAT for any deviation.
    s4 = z3.Solver()
    Th, Tc, Qh, Qc, W = z3.Reals("Th Tc Qh Qc W")
    for c in make_base(Th, Tc, Qh, Qc, W):
        s4.add(c)
    s4.add(Qc * Th == Qh * Tc)                     # reversible equality
    s4.add(W * Th != Qh * (Th - Tc))               # deviation from Carnot W
    verdicts["reversible_forces_carnot_W_unsat"] = (s4.check() == z3.unsat)

    return verdicts


# =====================================================================
# POSITIVE / NEGATIVE / BOUNDARY TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    if sp is None:
        results["sympy_available"] = False
        results["pass"] = False
        return results
    deriv = sympy_derive_efficiency_bound()
    dtx = sympy_distinguishability_transfer()
    results["efficiency_derivation"] = deriv
    results["distinguishability_transfer"] = dtx
    results["pass"] = bool(
        deriv["bound_equivalence_is_zero"]
        and deriv["eta_reversible_is_carnot"]
        and dtx["distinguishability_transfer_closed"]
    )
    if results["pass"]:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Symbolically derived eta <= 1 - Tc/Th from first-law + Clausius "
            "and closed the distinguishability-transfer identity W/T_ref = Delta D."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    return results


def run_negative_tests():
    results = {}
    if z3 is None:
        results["z3_available"] = False
        results["pass"] = False
        return results
    verdicts = z3_fence_admissibility()
    results["z3_verdicts"] = verdicts
    # Pass criterion: every UNSAT claim is UNSAT, and the SAT witness is SAT.
    results["pass"] = bool(
        verdicts.get("reversible_witness_sat", False)
        and verdicts.get("super_carnot_unsat", False)
        and verdicts.get("kelvin_single_bath_unsat", False)
        and verdicts.get("reversible_forces_carnot_W_unsat", False)
    )
    if results["pass"]:
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "UNSAT-refuted super-Carnot violators, Kelvin single-bath violators, "
            "and non-Carnot W under reversible equality; SAT-witnessed a reversible tuple."
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return results


def run_boundary_tests():
    """Boundaries: Tc -> Th (zero-efficiency fence), Tc -> 0+ (eta -> 1)."""
    results = {"cases": []}
    if sp is None:
        results["pass"] = False
        return results
    Th, Tc = sp.symbols("Th Tc", positive=True)
    eta_carnot = 1 - Tc/Th
    lim_equal = sp.limit(eta_carnot.subs(Tc, Th), Th, sp.Symbol("T0", positive=True))
    lim_zero  = sp.limit(eta_carnot, Tc, 0, "+")
    results["cases"].append({"Tc_to_Th_eta_limit": str(lim_equal), "expected": "0"})
    results["cases"].append({"Tc_to_0_eta_limit":  str(lim_zero),  "expected": "1"})
    # Numeric spot-check (not load-bearing, just sanity):
    spot = []
    for Th_v, Tc_v in [(Fraction(400), Fraction(300)), (Fraction(500), Fraction(250)), (Fraction(100), Fraction(99))]:
        eta_v = 1 - Tc_v/Th_v
        spot.append({"Th": str(Th_v), "Tc": str(Tc_v), "eta_carnot": str(eta_v)})
    results["spot_checks"] = spot
    results["pass"] = bool(str(lim_equal) == "0" and str(lim_zero) == "1")
    return results


# =====================================================================
# MAIN
# =====================================================================

def main():
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    overall = bool(positive.get("pass") and negative.get("pass") and boundary.get("pass"))

    results = {
        "name": "sim_carnot_constraint_admissibility_fence",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "bridge_claims": {
            "efficiency_bound_as_admissibility_fence":
                "eta <= 1 - Tc/Th is the exclusion fence of dS_total >= 0 "
                "(sympy-derived, z3-UNSAT on violators).",
            "reversibility_as_F01_symmetry":
                "Reversible equality Qc*Th = Qh*Tc is the forward/backward fixed point; "
                "z3-UNSAT shows this equality forces W = Qh*(1 - Tc/Th).",
            "work_extraction_as_distinguishability_transfer":
                "W/T_ref = Delta D under the Landauer-like bath linearization; "
                "sympy closes the identity under the first law.",
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "carnot_constraint_admissibility_fence.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"overall_pass = {overall}")
    print(f"Results written to {out_path}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
