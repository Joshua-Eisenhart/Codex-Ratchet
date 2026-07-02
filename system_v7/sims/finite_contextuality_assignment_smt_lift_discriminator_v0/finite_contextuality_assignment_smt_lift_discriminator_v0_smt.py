#!/usr/bin/env python3
"""Executable density-rho control for the Ratchet Runbook (ledger caveat #2:
controls must be executable, not narrative).

Question: when is a quantum/operator (rho) carrier FORCED over a classical
measure on the bare quotient X/~_P? Answer (standard, finite, decidable): when
the finite measurement statistics are CONTEXTUAL -- i.e. admit NO single
{-1,+1} value assignment consistent across all measurement contexts (no
noncontextual hidden-variable model, hence no classical probability measure on
a quotient reproduces them). This is a load-bearing z3+cvc5 UNSAT, the system's
primary proof form -- NOT a definitional restatement.

The flip (proves it is not by-construction):
  * CONTEXTUAL case  = the Peres-Mermin 3x3 square. Each of the 6 contexts (3
    rows, 3 cols) is a set of mutually commuting +-1 observables whose product
    is forced: all rows -> +1, two cols -> +1, one col -> -1. Multiplying all 9
    observables row-wise gives +1, column-wise gives -1: a parity contradiction.
    -> NO consistent {-1,+1} assignment -> UNSAT -> noncontextual model
    IMPOSSIBLE -> the quantum/rho carrier is FORCED.
  * NONCONTEXTUAL CONTROL = the SAME 9 observables and 6 contexts, but with the
    frustrating col product flipped to +1 (all 6 contexts -> +1). A global
    assignment now exists (e.g. all +1) -> SAT -> a classical measure on the
    quotient suffices -> the rho lift is REJECTED.

Both z3 and cvc5 must agree on each. The flip (UNSAT for contextual, SAT for the
control) is the load-bearing structural fact.
"""

import json
import os
import hashlib
from datetime import datetime, timezone

import z3
import cvc5
from cvc5 import Kind

SIM_ID = "finite_contextuality_assignment_smt_lift_discriminator_v0"
HERE = os.path.dirname(os.path.abspath(__file__))

# Peres-Mermin 3x3 grid of observables a..i:
#   a b c        rows: R1=abc  R2=def  R3=ghi
#   d e f        cols: C1=adg  C2=beh  C3=cfi
#   g h i
CELLS = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
CONTEXTS = {
    "R1": ["a", "b", "c"], "R2": ["d", "e", "f"], "R3": ["g", "h", "i"],
    "C1": ["a", "d", "g"], "C2": ["b", "e", "h"], "C3": ["c", "f", "i"],
}
# Peres-Mermin signs: all rows = +1, two cols = +1, one col = -1 -> parity contradiction.
PM_SIGNS = {"R1": 1, "R2": 1, "R3": 1, "C1": 1, "C2": 1, "C3": -1}
# Noncontextual control: flip the frustrating col to +1 -> globally satisfiable.
CTRL_SIGNS = {"R1": 1, "R2": 1, "R3": 1, "C1": 1, "C2": 1, "C3": 1}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def z3_check(signs):
    s = z3.Solver()
    v = {c: z3.Int(c) for c in CELLS}
    for c in CELLS:
        s.add(z3.Or(v[c] == 1, v[c] == -1))
    for ctx, cells in CONTEXTS.items():
        s.add(v[cells[0]] * v[cells[1]] * v[cells[2]] == signs[ctx])
    return str(s.check())  # 'sat' or 'unsat'


def cvc5_check(signs):
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NIA")
    slv.setOption("produce-models", "true")
    one = tm.mkInteger(1)
    negone = tm.mkInteger(-1)
    v = {c: tm.mkConst(tm.getIntegerSort(), c) for c in CELLS}
    for c in CELLS:
        slv.assertFormula(tm.mkTerm(Kind.OR,
                                    tm.mkTerm(Kind.EQUAL, v[c], one),
                                    tm.mkTerm(Kind.EQUAL, v[c], negone)))
    for ctx, cells in CONTEXTS.items():
        prod = tm.mkTerm(Kind.MULT, v[cells[0]], v[cells[1]], v[cells[2]])
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, prod, tm.mkInteger(signs[ctx])))
    return str(slv.checkSat())  # 'sat' or 'unsat'


def main():
    pm_z3, pm_cvc5 = z3_check(PM_SIGNS), cvc5_check(PM_SIGNS)
    ct_z3, ct_cvc5 = z3_check(CTRL_SIGNS), cvc5_check(CTRL_SIGNS)

    contextual_unsat = pm_z3 == "unsat" and pm_cvc5 == "unsat"
    control_sat = ct_z3 == "sat" and ct_cvc5 == "sat"
    flip_confirmed = contextual_unsat and control_sat
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "smt",
        "computation_style": "noncontextual_assignment_smt_feasibility_z3_cvc5",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": timestamp,
        "written_at": timestamp,
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_smt_results.json",
        "smt_flip": {
            "question": "does a single noncontextual {-1,+1} assignment satisfy all 6 measurement-context product constraints?",
            "contextual_peres_mermin": {"z3": pm_z3, "cvc5": pm_cvc5, "expected": "unsat"},
            "noncontextual_control": {"z3": ct_z3, "cvc5": ct_cvc5, "expected": "sat"},
            "contextual_is_unsat": contextual_unsat,
            "control_is_sat": control_sat,
            "real_vs_control_flip_confirmed": flip_confirmed,
            "interpretation": (
                "Contextual statistics (Peres-Mermin) admit NO noncontextual assignment -> UNSAT -> no classical "
                "measure on a quotient reproduces them -> the quantum/rho carrier is FORCED. The control (frustrating "
                "sign removed) is SAT -> a classical measure on the quotient suffices -> the rho lift is REJECTED. "
                "The UNSAT/SAT FLIP is the load-bearing structural fact; it is not a definitional restatement."
            ),
        },
        "positive_tests": {
            "contextual_peres_mermin_unsat": contextual_unsat,
            "real_vs_control_flip_confirmed": flip_confirmed,
        },
        "negative_tests": {
            "noncontextual_control_is_sat": control_sat,
            "frustrating_sign_removed_rejects_rho_lift": control_sat,
        },
        "facts": {
            "contextual_peres_mermin": {"z3": pm_z3, "cvc5": pm_cvc5},
            "noncontextual_control": {"z3": ct_z3, "cvc5": ct_cvc5},
        },
        "claims": {
            "rho_forced_when_contextual": contextual_unsat,
            "rho_rejected_when_noncontextual": control_sat,
            "load_bearing_smt_flip": flip_confirmed,
        },
        "honest_scope": {
            "earns": "an executable, flip-able z3+cvc5 control for the density_rho projection: a quantum/rho carrier is forced exactly when the finite probe statistics are CONTEXTUAL (UNSAT), rejected when noncontextual (SAT). Makes the runbook density Control executable (ledger caveat #2).",
            "does_not_earn": "no claim that any PARTICULAR finite probe set is contextual -- only that IF it is, rho is forced; this is the discriminator, not a survey. scratch_diagnostic.",
        },
        "packages_used": ["z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": {
            "z3": {"tried": True, "used": True, "reason": "load-bearing UNSAT (contextual) vs SAT (control) noncontextual-assignment flip"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent second solver confirming the same flip"},
        },
        "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing", "cvc5": "load_bearing"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_smt_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")
    print(f"  Peres-Mermin (contextual): z3={pm_z3} cvc5={pm_cvc5}  (expect unsat -> rho FORCED)")
    print(f"  noncontextual control:     z3={ct_z3} cvc5={ct_cvc5}  (expect sat   -> rho REJECTED)")
    print(f"  load-bearing flip confirmed = {flip_confirmed}")


if __name__ == "__main__":
    main()
