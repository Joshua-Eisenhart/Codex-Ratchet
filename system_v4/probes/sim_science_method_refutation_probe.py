#!/usr/bin/env python3
"""sim_science_method_refutation_probe

Load-bearing z3 sim. UNSAT IS refutation.

Carrier: a claim encoded as a z3 formula phi(x).
Structure: counter-candidate psi(x) = NOT phi(x) AND observable-consistency.
Reduction: search for x satisfying psi.
Admissibility: claim survives iff no counterexample found (UNSAT of psi).
Distinguishability probe: z3.check() returns sat/unsat/unknown.
Chirality: refutation is asymmetric — one counterexample kills the claim;
          no amount of confirmation proves it.
Coupling stub: consumes candidate list from conjecture_generation format.
"""
import os
import sys
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT = refutation proof; load-bearing"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False
    TOOL_MANIFEST["z3"]["reason"] = "not installed — sim cannot be load-bearing"


def refutes(claim_builder):
    """Given a function that builds (solver, negated_claim), return 'refuted'
    if a counterexample exists, 'survives' if UNSAT, 'unknown' otherwise."""
    if not HAS_Z3:
        return "no_z3"
    s = z3.Solver()
    claim_builder(s)
    r = s.check()
    if r == z3.sat:
        return "refuted"
    if r == z3.unsat:
        return "survives"
    return "unknown"


def run_positive_tests():
    # Claim: "for all int x, x*x >= 0". Negation SAT? No -> survives.
    def build(s):
        x = z3.Int("x")
        s.add(x * x < 0)
    r = refutes(build)
    return {"square_nonneg_survives": {"pass": r == "survives", "result": r}}


def run_negative_tests():
    # Claim: "for all int x, x > 0". Counterexample x=0 exists -> refuted.
    def build(s):
        x = z3.Int("x")
        s.add(z3.Not(x > 0))
    r = refutes(build)
    return {"positivity_refuted": {"pass": r == "refuted", "result": r}}


def run_boundary_tests():
    # Vacuous claim over empty domain: forall x in {}: anything. Survives trivially.
    def build(s):
        x = z3.Int("x")
        # domain empty: 1==2; negation: domain && NOT claim -> unsat
        s.add(z3.And(z3.BoolVal(False), x == x))
    r = refutes(build)
    return {"vacuous_survives": {"pass": r == "survives", "result": r}}


if __name__ == "__main__":
    if not HAS_Z3:
        results = {
            "name": "science_method_refutation_probe",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": {}, "negative": {}, "boundary": {},
            "classification": "classical_baseline",
            "status": "fail",
            "note": "z3 missing — refutation probe requires z3",
        }
        write_results("sim_science_method_refutation_probe", results)
        print("[fail] z3 not installed")
        sys.exit(1)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_refutation_probe",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical",  # z3 load-bearing
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_refutation_probe", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)
