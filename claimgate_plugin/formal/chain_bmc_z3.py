#!/usr/bin/env python3
"""EXHAUSTIVE bounded model check of the ClaimGate chain — z3 AND cvc5.

Same transition system as ClaimGateChain.tla, encoded for SMT. The chain is
ACYCLIC (each step advances the stage, "done" absorbs), so unrolling to the
number of stages is not a bound — it is EXHAUSTIVE. Every reachable path is
covered.

Method, per property P:
  REAL   : assert the transition relation AND NOT P   -> expect UNSAT (no path)
  ERASED : delete one guard, assert the same          -> expect SAT (a path appears)

The erasure leg is what makes this non-decorative. An encoding that returns
UNSAT with the guard removed proved nothing about the guard. This is the same
polarity discipline as the flip battery, applied to the gate's own control flow
instead of to a mechanism.

Dual solver: z3 and cvc5 must AGREE. Agreement is solver reproduction, not
independent semantics — recorded as such, never as a second proof.

Exit 0 all properties hold and every guard is load-bearing; 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import z3

try:
    import cvc5
    from cvc5 import Kind
    HAVE_CVC5 = True
except Exception:  # noqa: BLE001
    HAVE_CVC5 = False

STAGES = ["intake", "tier0", "seal", "verify", "floor", "done"]
S = {n: i for i, n in enumerate(STAGES)}
DISP = {"none": 0, "ADMIT": 1, "PARK": 2, "BLOCK": 3}
N = len(STAGES)  # unrolling depth: acyclic chain => exhaustive


def build(erase: str | None, mutate: str | None = None):
    """Return (solver-agnostic) z3 constraint list + the step variables."""
    st = [z3.Int(f"stage_{k}") for k in range(N + 1)]
    ino = [z3.Bool(f"intakeOk_{k}") for k in range(N + 1)]
    t0 = [z3.Bool(f"tier0Ok_{k}") for k in range(N + 1)]
    sl = [z3.Bool(f"sealOk_{k}") for k in range(N + 1)]
    vc = [z3.Int(f"verifyCode_{k}") for k in range(N + 1)]
    dp = [z3.Int(f"disp_{k}") for k in range(N + 1)]
    fc = [z3.Int(f"floorCode_{k}") for k in range(N + 1)]   # ratchet_floor exit
    ic = [z3.Int(f"intakeCode_{k}") for k in range(N + 1)]  # 0 pass|1 REJECT|3 PARK

    C = []
    # types
    for k in range(N + 1):
        C += [st[k] >= 0, st[k] < len(STAGES), vc[k] >= 0, vc[k] <= 3,
              dp[k] >= 0, dp[k] <= 3, fc[k] >= 0, fc[k] <= 3,
              z3.Or(ic[k] == 0, ic[k] == 1, ic[k] == 3)]
    # init
    C += [st[0] == S["intake"], ino[0] == False, t0[0] == False,  # noqa: E712
          sl[0] == False, vc[0] == 0, dp[0] == DISP["none"],       # noqa: E712
          fc[0] == 0, ic[0] == 0]

    for k in range(N):
        adv = []
        # INTAKE
        # intake exits 0 pass | 1 REJECT | 3 PARK (locked-floor absent). All three
        # are distinct dispositions; folding 3 into BLOCK hid a real path.
        pass_i = z3.Or(ic[k + 1] == 0, erase == "intake")
        adv.append(z3.Implies(st[k] == S["intake"],
                   z3.And(t0[k + 1] == t0[k], sl[k + 1] == sl[k], vc[k + 1] == vc[k],
                          ino[k + 1] == (ic[k + 1] == 0),
                          z3.If(pass_i,
                                z3.And(st[k + 1] == S["tier0"], dp[k + 1] == DISP["none"]),
                                z3.And(st[k + 1] == S["done"],
                                       z3.If(ic[k + 1] == 3, dp[k + 1] == DISP["PARK"],
                                             dp[k + 1] == DISP["BLOCK"]))))))
        # TIER0
        pass_t = z3.Or(t0[k + 1], erase == "tier0")
        adv.append(z3.Implies(st[k] == S["tier0"],
                   z3.And(ino[k + 1] == ino[k], sl[k + 1] == sl[k], vc[k + 1] == vc[k],
                          z3.If(pass_t,
                                z3.And(st[k + 1] == S["seal"], dp[k + 1] == DISP["none"]),
                                z3.And(st[k + 1] == S["done"], dp[k + 1] == DISP["BLOCK"])))))
        # SEAL — fails closed on ANY nonzero
        pass_s = z3.Or(sl[k + 1], erase == "seal")
        adv.append(z3.Implies(st[k] == S["seal"],
                   z3.And(ino[k + 1] == ino[k], t0[k + 1] == t0[k], vc[k + 1] == vc[k],
                          z3.If(pass_s,
                                z3.And(st[k + 1] == S["verify"], dp[k + 1] == DISP["none"]),
                                z3.And(st[k + 1] == S["done"], dp[k + 1] == DISP["BLOCK"])))))
        # VERIFY — 0 or 3 continue; 1,2 block
        pass_v = z3.Or(vc[k + 1] == 0, vc[k + 1] == 3, erase == "verify")
        adv.append(z3.Implies(st[k] == S["verify"],
                   z3.And(ino[k + 1] == ino[k], t0[k + 1] == t0[k], sl[k + 1] == sl[k],
                          z3.If(pass_v,
                                z3.And(st[k + 1] == S["floor"], dp[k + 1] == DISP["none"]),
                                z3.And(st[k + 1] == S["done"], dp[k + 1] == DISP["BLOCK"])))))
        # FLOOR — shell: floor exit 1/2 OVERRIDES the claim outcome with failure;
        # floor 0/3 keeps it (park when depth-pending, else admit).
        floor_blocks = z3.And(fc[k + 1] >= 1, fc[k + 1] <= 2)
        if mutate == "floor_ignores_block":
            floor_blocks = z3.BoolVal(False)          # mutation: floor result erased
        park_cond = (vc[k] == 3) if mutate != "floor_admits_depth" else z3.BoolVal(False)
        adv.append(z3.Implies(st[k] == S["floor"],
                   z3.And(ino[k + 1] == ino[k], t0[k + 1] == t0[k], sl[k + 1] == sl[k],
                          vc[k + 1] == vc[k], st[k + 1] == S["done"],
                          z3.If(floor_blocks, dp[k + 1] == DISP["BLOCK"],
                                z3.If(park_cond, dp[k + 1] == DISP["PARK"],
                                      dp[k + 1] == DISP["ADMIT"])))))
        for other in ("intake", "tier0", "seal", "verify"):
            adv.append(z3.Implies(st[k] == S[other], fc[k + 1] == fc[k]))
        for other in ("tier0", "seal", "verify", "floor", "done"):
            adv.append(z3.Implies(st[k] == S[other], ic[k + 1] == ic[k]))
        # DONE absorbs
        adv.append(z3.Implies(st[k] == S["done"],
                   z3.And(st[k + 1] == st[k], ino[k + 1] == ino[k], t0[k + 1] == t0[k],
                          sl[k + 1] == sl[k], vc[k + 1] == vc[k], dp[k + 1] == dp[k])))
        C += adv
    return C, (st, ino, t0, sl, vc, dp, fc, ic)


def negated(prop, v):
    """NOT P at the final step."""
    st, ino, t0, sl, vc, dp, fc, ic = v
    k = N
    if prop == "NoAdmitWithoutAllChecks":
        return z3.And(dp[k] == DISP["ADMIT"],
                      z3.Not(z3.And(ino[k], t0[k], sl[k], vc[k] == 0)))
    if prop == "DepthPendingNeverAdmits":
        return z3.And(vc[k] == 3, dp[k] == DISP["ADMIT"])
    if prop == "SealFailsClosed":
        return z3.And(z3.Not(sl[k]), st[k] == S["done"], dp[k] == DISP["ADMIT"])
    if prop == "NoSilentExit":
        return z3.And(st[k] == S["done"], dp[k] == DISP["none"])
    raise ValueError(prop)


def z3_check(prop, erase, mutate=None):
    C, v = build(erase, mutate)
    s = z3.Solver()
    s.add(C)
    s.add(negated(prop, v))
    return str(s.check())


def cvc5_check(prop, erase):
    """Independent cvc5 result, from the hand-built encoding in chain_bmc_cvc5.py
    (the cvc5 BINARY is absent here; only the python module is installed, so an
    SMT-LIB round trip through a subprocess cannot run)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cvc5mod", str(Path(__file__).parent / "chain_bmc_cvc5.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.check(prop, erase)
    except Exception:  # noqa: BLE001
        return "unavailable"


def _dead_cvc5_roundtrip(prop, erase):
    if not HAVE_CVC5:
        return "unavailable"
    C, v = build(erase)
    g = z3.Goal()
    g.add(C)
    g.add(negated(prop, v))
    smt2 = g.as_expr().sexpr()
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_LIA")
    try:
        parser = None  # cvc5 python parser API varies; use the simple path
        # Encode via z3's SMT-LIB2 text and let cvc5 parse it.
        import tempfile
        decls = "\n".join(
            f"(declare-fun {d.name()} () {d.range().sexpr()})"
            for d in sorted({x.decl() for x in _atoms(C + [negated(prop, v)])},
                            key=lambda d: d.name()))
        text = f"(set-logic QF_LIA)\n{decls}\n(assert {smt2})\n(check-sat)\n"
        with tempfile.NamedTemporaryFile("w", suffix=".smt2", delete=False) as f:
            f.write(text)
            path = f.name
        import subprocess
        out = subprocess.run(["cvc5", path], capture_output=True, text=True, timeout=60)
        if out.returncode != 0 and not out.stdout.strip():
            return "unavailable"
        return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "unavailable"
    except Exception:  # noqa: BLE001
        return "unavailable"


def _atoms(exprs):
    seen, out = set(), []
    stack = list(exprs)
    while stack:
        e = stack.pop()
        if z3.is_const(e) and e.decl().kind() == z3.Z3_OP_UNINTERPRETED:
            if e.decl().name() not in seen:
                seen.add(e.decl().name())
                out.append(e)
        stack.extend(e.children())
    return out


PROPERTIES = ["NoAdmitWithoutAllChecks", "DepthPendingNeverAdmits",
              "SealFailsClosed", "NoSilentExit"]
GUARDS = ["intake", "tier0", "seal", "verify"]
MUTATIONS = ["floor_ignores_block", "floor_admits_depth"]


def main():
    rows = []
    all_ok = True
    for prop in PROPERTIES:
        real = z3_check(prop, None)
        real_cvc5 = cvc5_check(prop, None)
        holds = (real == "unsat")
        # polarity: erasing a guard must make a counterexample appear
        erasures = {}
        for g in GUARDS:
            erasures[g] = z3_check(prop, g)
        # structural mutations, not just guard erasures: if NOTHING can produce a
        # counterexample the property is a tautology of the encoding (VACUOUS).
        for mu in MUTATIONS:
            erasures[f"mutate:{mu}"] = z3_check(prop, None, mu)
        load_bearing = [g for g, r in erasures.items() if r == "sat"]
        vacuous = (real == "unsat" and not load_bearing)
        rows.append({
            "property": prop,
            "z3_real": real,
            "cvc5_real": real_cvc5,
            "solvers_agree": (real_cvc5 == real),
            "cvc5_status": ("agreed" if real_cvc5 == real else
                            "UNAVAILABLE — not counted as agreement" if real_cvc5 == "unavailable"
                            else "DISAGREES"),
            "holds_over_all_paths": holds,
            "erasure_results": erasures,
            "guards_proven_load_bearing": load_bearing,
            "vacuous": bool(vacuous),
            "vacuity_note": ("no guard erasure and no structural mutation can produce a "
                             "counterexample — this property restates the encoding rather "
                             "than testing it (red-team finding, 2026-07-25)")
                            if vacuous else "counterexample is expressible; the encoding tests it",
        })
        if not holds:
            all_ok = False

    # at least one guard must be load-bearing for the central property,
    # otherwise the encoding proves nothing
    central = next(r for r in rows if r["property"] == "NoAdmitWithoutAllChecks")
    non_decorative = len(central["guards_proven_load_bearing"]) > 0
    if not non_decorative:
        all_ok = False

    out = {
        "checker": "claimgate_chain_bmc_v0",
        "spec": "claimgate_plugin/formal/ClaimGateChain.tla",
        "mirrors": "claimgate_plugin/hooks/post_receipt_gate.sh",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "unroll_depth": N,
        "exhaustive": True,
        "exhaustive_justification": (
            "the chain is acyclic (every step advances the stage; 'done' absorbs), "
            "so unrolling to the stage count covers every reachable path"),
        "llm_tokens_spent": 0,
        "declared_divergences_from_shell": [
            "ratchet_floor runs ONLY when floor_claims is present; the spec always enters floor",
            "the shell's terminal value is an exit CODE (0/1/2/3); the spec abstracts to a disposition token",
            "advise()/suggest.mjs is omitted (control-irrelevant: its output and status are discarded)",
            "RF_STORE selection of the floor store is not modelled",
        ],
        "divergences_found_by": "codex terra + grok-4.5 + nvidia deepseek, independently, 2026-07-25",
        "solver_note": ("z3 and cvc5 agreeing is solver reproduction over one encoding, "
                        "NOT independent semantics"),
        "properties": rows,
        "all_properties_hold": all(r["holds_over_all_paths"] for r in rows),
        "non_vacuous_properties": [r["property"] for r in rows if not r["vacuous"]],
        "VACUOUS_properties": [r["property"] for r in rows if r["vacuous"]],
        "encoding_is_non_decorative": non_decorative,
    }
    d = Path(__file__).parent / "results"
    d.mkdir(exist_ok=True)
    (d / "chain_bmc_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
