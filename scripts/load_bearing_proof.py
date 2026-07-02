#!/usr/bin/env python3
"""
load_bearing_proof.py -- correct-by-construction helpers so a sim's SMT proof and
tool ablation are GENUINELY load-bearing, not decorative. Authored separately from
the sims (like the gate) so individual sims cannot lower their own bar.

The 2026-05-29 adversarial audit found the recurring fabrication:
  - z3 'load_bearing' = a tautology: assert b==True (a pre-computed Python bool),
    then Not(b) is trivially UNSAT. z3 never touches the real numeric observable.
  - ablation 'outcome_delta' = a hardcoded float or a count, not a remove-and-recompute.

These helpers fix both by construction:

  smt_load_bearing(claim, real_measured, control_measured, claim_builder)
     Binds z3 (and cvc5 best-effort) REAL variables to the actual NUMERIC observables.
     Asserts the SAME structural claim once under the REAL carrier's measured values and
     once under the negative-CONTROL carrier's measured values. The proof is load-bearing
     IFF the verdict FLIPS (real holds -> sat; control breaks it -> unsat). A tautology or
     a claim decoupled from the numbers cannot flip. Returns the exact contract fields
     (real_claim_verdict, negated_claim_verdict, differ, bound_to_measured).

  tool_ablation(observable, baseline_value, ablated_value)
     Records BOTH the with-tool and without-tool observable; delta = baseline - ablated.
     The sim must actually compute both (run the observable with the tool/structure, then
     with it removed). A bare/hardcoded delta cannot be produced this way.

Honesty is still not automatic: the sim must feed the REAL observables and a REAL control.
But it can no longer satisfy the contract with a tautology or a hardcoded number, and the
fed values are exactly what a fresh-context audit re-checks.
"""
from fractions import Fraction

import z3


def _q(x, max_den=10**9):
    return Fraction(float(x)).limit_denominator(max_den)


def _z3_verdict(measured, claim_builder):
    """measured: {name: float}. claim_builder({name: z3.Real}) -> z3.BoolRef.
    Bind each var to its measured rational value, assert the claim, return sat/unsat."""
    s = z3.Solver()
    s.set("timeout", 15000)
    vs = {k: z3.Real(k) for k in measured}
    for k, v in measured.items():
        s.add(vs[k] == _q(v))
    s.add(claim_builder(vs))
    r = s.check()
    if r == z3.sat:
        return "sat"
    if r == z3.unsat:
        return "unsat"
    return "unknown"


def _cvc5_verdict(measured, claim_pairs):
    """Best-effort cvc5 cross-check. claim_pairs: list of (lhs_name_or_const, op, rhs).
    Kept simple/optional; returns 'sat'/'unsat'/'skip'. Not required for the gate."""
    try:
        import cvc5
        from cvc5 import Kind
        slv = cvc5.Solver()
        slv.setOption("produce-models", "true")
        slv.setLogic("QF_LRA")
        R = slv.getRealSort()
        vs = {k: slv.mkConst(R, k) for k in measured}
        for k, v in measured.items():
            q = _q(v)
            val = slv.mkReal(q.numerator, q.denominator)
            slv.assertFormula(slv.mkTerm(Kind.EQUAL, vs[k], val))
        for lhs, op, rhs in claim_pairs:
            lt = vs[lhs] if lhs in vs else slv.mkReal(_q(lhs).numerator, _q(lhs).denominator)
            rt = vs[rhs] if rhs in vs else slv.mkReal(_q(rhs).numerator, _q(rhs).denominator)
            kind = {"==": Kind.EQUAL, "<": Kind.LT, "<=": Kind.LEQ,
                    ">": Kind.GT, ">=": Kind.GEQ}[op]
            slv.assertFormula(slv.mkTerm(kind, lt, rt))
        return "sat" if slv.checkSat().isSat() else "unsat"
    except Exception:
        return "skip"


def smt_load_bearing(claim, real_measured, control_measured, claim_builder, cvc5_claim_pairs=None):
    """Load-bearing iff the SAME claim flips verdict between the real carrier's measured
    values and the negative-control carrier's measured values.

    claim_builder: fn({name: z3.Real}) -> z3.BoolRef -- the structural claim about the
                   ACTUAL numeric observables (e.g. norm==1, fs_distance==pi/2, anticommutator==0).
    real_measured / control_measured: {name: float} measured on the real vs control carrier.
    """
    real_v = _z3_verdict(real_measured, claim_builder)
    ctrl_v = _z3_verdict(control_measured, claim_builder)
    out = {
        "claim": claim,
        "engine": "z3",
        "real_claim_verdict": real_v,
        "negated_claim_verdict": ctrl_v,  # claim re-checked under the erased/control values
        "differ": real_v != ctrl_v,
        "load_bearing": real_v != ctrl_v,
        "bound_to_measured": True,
        "real_measured": {k: float(v) for k, v in real_measured.items()},
        "control_measured": {k: float(v) for k, v in control_measured.items()},
    }
    if cvc5_claim_pairs is not None:
        out["cvc5_real_verdict"] = _cvc5_verdict(real_measured, cvc5_claim_pairs)
        out["cvc5_control_verdict"] = _cvc5_verdict(control_measured, cvc5_claim_pairs)
    return out


def tool_ablation(observable, baseline_value, ablated_value, tool=None):
    """Record a genuine remove-and-recompute ablation. The sim must pass the observable
    computed WITH the tool/structure (baseline) and WITHOUT it (ablated)."""
    b, a = float(baseline_value), float(ablated_value)
    return {
        "observable": observable,
        "tool": tool,
        "baseline_value": b,
        "ablated_value": a,
        "outcome_delta": b - a,
    }


if __name__ == "__main__":
    # self-test: a real claim (norm==1) flips under a control where norm=0.5
    import z3 as _z3
    real = {"norm": 1.0}
    ctrl = {"norm": 0.5}
    pr = smt_load_bearing(
        "carrier_norm_is_one",
        real, ctrl,
        lambda v: _z3.And(v["norm"] <= _q(1.0) + _q(1e-9), v["norm"] >= _q(1.0) - _q(1e-9)),
        cvc5_claim_pairs=[("norm", "<=", 1.0 + 1e-9), ("norm", ">=", 1.0 - 1e-9)],
    )
    abl = tool_ablation("half_chain_entropy", baseline_value=2.08, ablated_value=0.0, tool="clifford")
    print("smt_load_bearing:", {k: pr[k] for k in ("real_claim_verdict", "negated_claim_verdict", "differ", "cvc5_real_verdict", "cvc5_control_verdict")})
    print("tool_ablation:", abl)
    assert pr["differ"] is True, "real claim must flip vs control"
    assert abs(abl["outcome_delta"] - 2.08) < 1e-9
    print("SELF-TEST PASS")
