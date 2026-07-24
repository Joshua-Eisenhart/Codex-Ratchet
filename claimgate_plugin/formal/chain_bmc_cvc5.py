#!/usr/bin/env python3
"""Independent cvc5 encoding of the ClaimGate chain — hand-built, not a z3 round trip.

Deliberately NOT translated from the z3 goal. The transition system is
re-expressed against cvc5's own TermManager API, so agreement with
chain_bmc_z3.py is two encodings of one spec rather than one encoding checked
twice. That is still solver/encoding reproduction, not independent semantics —
the .tla module remains the single source both are transcribed from, and a
transcription error common to both would survive. Recorded as such.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cvc5
from cvc5 import Kind

STAGES = ["intake", "tier0", "seal", "verify", "floor", "done"]
S = {n: i for i, n in enumerate(STAGES)}
DISP = {"none": 0, "ADMIT": 1, "PARK": 2, "BLOCK": 3}
N = len(STAGES)


def check(prop: str, erase: str | None) -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LIA")
    I, B = tm.getIntegerSort(), tm.getBooleanSort()

    def i(n):
        return tm.mkInteger(n)

    st = [tm.mkConst(I, f"stage_{k}") for k in range(N + 1)]
    ino = [tm.mkConst(B, f"intakeOk_{k}") for k in range(N + 1)]
    t0 = [tm.mkConst(B, f"tier0Ok_{k}") for k in range(N + 1)]
    sl = [tm.mkConst(B, f"sealOk_{k}") for k in range(N + 1)]
    vc = [tm.mkConst(I, f"verifyCode_{k}") for k in range(N + 1)]
    dp = [tm.mkConst(I, f"disp_{k}") for k in range(N + 1)]

    A = slv.assertFormula
    EQ, AND, OR, NOT, IMP, ITE = (Kind.EQUAL, Kind.AND, Kind.OR, Kind.NOT,
                                  Kind.IMPLIES, Kind.ITE)
    T = tm.mkTerm

    def eq(a, b):
        return T(EQ, a, b)

    for k in range(N + 1):
        A(T(Kind.GEQ, st[k], i(0)))
        A(T(Kind.LT, st[k], i(len(STAGES))))
        A(T(Kind.GEQ, vc[k], i(0)))
        A(T(Kind.LEQ, vc[k], i(3)))
        A(T(Kind.GEQ, dp[k], i(0)))
        A(T(Kind.LEQ, dp[k], i(3)))

    A(eq(st[0], i(S["intake"])))
    A(T(NOT, ino[0]))
    A(T(NOT, t0[0]))
    A(T(NOT, sl[0]))
    A(eq(vc[0], i(0)))
    A(eq(dp[0], i(DISP["none"])))

    for k in range(N):
        def step(cur, guard, nxt, keep):
            adv = T(AND, eq(st[k + 1], i(S[nxt])), eq(dp[k + 1], i(DISP["none"])))
            blk = T(AND, eq(st[k + 1], i(S["done"])), eq(dp[k + 1], i(DISP["BLOCK"])))
            body = [T(ITE, guard, adv, blk)] + keep
            A(T(IMP, eq(st[k], i(S[cur])), T(AND, *body) if len(body) > 1 else body[0]))

        keep_i = [eq(t0[k + 1], t0[k]), eq(sl[k + 1], sl[k]), eq(vc[k + 1], vc[k])]
        g = ino[k + 1] if erase != "intake" else tm.mkTrue()
        step("intake", g, "tier0", keep_i)

        keep_t = [eq(ino[k + 1], ino[k]), eq(sl[k + 1], sl[k]), eq(vc[k + 1], vc[k])]
        g = t0[k + 1] if erase != "tier0" else tm.mkTrue()
        step("tier0", g, "seal", keep_t)

        keep_s = [eq(ino[k + 1], ino[k]), eq(t0[k + 1], t0[k]), eq(vc[k + 1], vc[k])]
        g = sl[k + 1] if erase != "seal" else tm.mkTrue()
        step("seal", g, "verify", keep_s)

        keep_v = [eq(ino[k + 1], ino[k]), eq(t0[k + 1], t0[k]), eq(sl[k + 1], sl[k])]
        g = (tm.mkTrue() if erase == "verify"
             else T(OR, eq(vc[k + 1], i(0)), eq(vc[k + 1], i(3))))
        step("verify", g, "floor", keep_v)

        # floor: depth-pending parks, else admits
        A(T(IMP, eq(st[k], i(S["floor"])),
            T(AND, eq(ino[k + 1], ino[k]), eq(t0[k + 1], t0[k]), eq(sl[k + 1], sl[k]),
              eq(vc[k + 1], vc[k]), eq(st[k + 1], i(S["done"])),
              T(ITE, eq(vc[k], i(3)), eq(dp[k + 1], i(DISP["PARK"])),
                eq(dp[k + 1], i(DISP["ADMIT"]))))))
        # done absorbs
        A(T(IMP, eq(st[k], i(S["done"])),
            T(AND, eq(st[k + 1], st[k]), eq(ino[k + 1], ino[k]), eq(t0[k + 1], t0[k]),
              eq(sl[k + 1], sl[k]), eq(vc[k + 1], vc[k]), eq(dp[k + 1], dp[k]))))

    k = N
    if prop == "NoAdmitWithoutAllChecks":
        A(T(AND, eq(dp[k], i(DISP["ADMIT"])),
            T(NOT, T(AND, ino[k], t0[k], sl[k], eq(vc[k], i(0))))))
    elif prop == "DepthPendingNeverAdmits":
        A(T(AND, eq(vc[k], i(3)), eq(dp[k], i(DISP["ADMIT"]))))
    elif prop == "SealFailsClosed":
        A(T(AND, T(NOT, sl[k]), eq(st[k], i(S["done"])), eq(dp[k], i(DISP["ADMIT"]))))
    elif prop == "NoSilentExit":
        A(T(AND, eq(st[k], i(S["done"])), eq(dp[k], i(DISP["none"]))))
    else:
        raise ValueError(prop)

    r = slv.checkSat()
    return "unsat" if r.isUnsat() else ("sat" if r.isSat() else "unknown")


PROPERTIES = ["NoAdmitWithoutAllChecks", "DepthPendingNeverAdmits",
              "SealFailsClosed", "NoSilentExit"]
GUARDS = ["intake", "tier0", "seal", "verify"]


def main():
    rows = []
    for p in PROPERTIES:
        rows.append({
            "property": p,
            "cvc5_real": check(p, None),
            "erasure_results": {g: check(p, g) for g in GUARDS},
        })
        rows[-1]["guards_proven_load_bearing"] = [
            g for g, v in rows[-1]["erasure_results"].items() if v == "sat"]
    out = {
        "checker": "claimgate_chain_bmc_cvc5_v0",
        "encoding": "independent hand-built cvc5 TermManager encoding (NOT a z3 round trip)",
        "independence_ceiling": ("two encodings of ONE .tla spec; a transcription error "
                                 "common to both would survive. Not independent semantics."),
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "unroll_depth": N,
        "properties": rows,
    }
    d = Path(__file__).parent / "results"
    d.mkdir(exist_ok=True)
    (d / "chain_bmc_cvc5_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
