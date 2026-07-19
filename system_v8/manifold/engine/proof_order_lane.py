#!/usr/bin/env python3
"""Dual-solver (z3 AND cvc5) proof lane for the welded v8 manifold.

Supplies the multi-engine proof leg the inherited pack admitted it never ran.
Encodings are SYMBOLIC (integer/boolean constants constrained to the archived
receipt values) so the solvers, not Python, decide every verdict. Every proof
carries an erasure control whose verdict must FLIP — a proof that cannot flip
is decorative and fails this lane.

P1 frontier incomparability — symbolic vectors a, b constrained to the
   archived presumption vectors of finite_relation / finite_automaton;
   Pareto domination formula must be UNSAT in both directions on both
   solvers. Erasure: overwrite automaton's winning component with
   relation's value -> domination SAT.
P2 nesting expansion — archived admissible triple sets (baseline 11,
   expanded 13) encoded as 9-bit codes; subset violation must be UNSAT;
   a strictly added configuration must be SAT with a model. Erasure:
   expanded replaced by baseline -> added-configuration claim UNSAT.
P3 real-packet exclusion — from the real contextuality packet's
   deterministic contexts: the finite_partition over-admission ({0,1}
   everywhere) matching observation somewhere must be UNSAT. Erasure:
   drop the exclusions (observation admits both) -> SAT.

Claim ceiling: packet-relative structural proofs over archived receipt
values; no scientific, physical, or canonical claim. promotion_allowed=false.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))
from common import digest, write_json  # noqa: E402

import z3  # noqa: E402
import cvc5  # noqa: E402
from cvc5 import Kind  # noqa: E402

MANIFOLD = ENGINE.parent
RESULTS = MANIFOLD / "results"


def both(name, zv, cv, expected):
    agree = zv == cv
    return {"proof": name, "z3": zv, "cvc5": cv, "expected": expected,
            "solvers_agree": agree, "pass": agree and zv == expected}


# --------------------------------------------------------------- cvc5 utils
class C5:
    def __init__(self):
        self.tm = cvc5.TermManager()
        self.slv = cvc5.Solver(self.tm)

    def int_const(self, name, value):
        c = self.tm.mkConst(self.tm.getIntegerSort(), name)
        self.slv.assertFormula(self.tm.mkTerm(
            Kind.EQUAL, c, self.tm.mkInteger(value)))
        return c

    def check(self):
        return str(self.slv.checkSat())


# --------------------------------------------------------------------- P1
def p1(vectors, order):
    va = [vectors["finite_relation"][k] for k in order]
    vb = [vectors["finite_automaton"][k] for k in order]

    def domination(x_vals, y_vals, label, expected):
        # z3: symbolic ints pinned to receipt values
        xs = [z3.Int(f"x{i}") for i in range(len(x_vals))]
        ys = [z3.Int(f"y{i}") for i in range(len(y_vals))]
        pins = [c == v for c, v in zip(xs, x_vals)] + \
               [c == v for c, v in zip(ys, y_vals)]
        dom = z3.And(z3.And([a <= b for a, b in zip(xs, ys)]),
                     z3.Or([a < b for a, b in zip(xs, ys)]))
        s = z3.Solver()
        s.add(*pins, dom)
        zv = str(s.check())
        # cvc5 mirror
        c = C5()
        cx = [c.int_const(f"x{i}", v) for i, v in enumerate(x_vals)]
        cy = [c.int_const(f"y{i}", v) for i, v in enumerate(y_vals)]
        leqs = [c.tm.mkTerm(Kind.LEQ, a, b) for a, b in zip(cx, cy)]
        lts = [c.tm.mkTerm(Kind.LT, a, b) for a, b in zip(cx, cy)]
        c.slv.assertFormula(c.tm.mkTerm(
            Kind.AND,
            c.tm.mkTerm(Kind.AND, *leqs) if len(leqs) > 1 else leqs[0],
            c.tm.mkTerm(Kind.OR, *lts) if len(lts) > 1 else lts[0]))
        cv = c.check()
        return both(label, zv, cv, expected)

    rows = [
        domination(va, vb, "P1a_relation_dominates_automaton", "unsat"),
        domination(vb, va, "P1b_automaton_dominates_relation", "unsat"),
    ]
    vb_erased = list(vb)
    vb_erased[0] = va[0]  # erase automaton's carrier-atom advantage
    rows.append(domination(va, vb_erased,
                           "P1c_erasure_control_domination", "sat"))
    return rows


# --------------------------------------------------------------------- P2
def triple_code(triple):
    code = 0
    for layer, (j, k, zbit) in enumerate(triple):
        code |= (j << 0 | k << 1 | zbit << 2) << (3 * layer)
    return code


def p2(nesting_packets):
    baseline = {triple_code([tuple(s) for s in t])
                for t in nesting_packets[0]["admissible_triples"]}
    expanded = {triple_code([tuple(s) for s in t])
                for t in nesting_packets[1]["admissible_triples"]}

    def member(x, codes):
        return z3.Or([x == c for c in sorted(codes)])

    def c5_member(c, var, codes):
        terms = [c.tm.mkTerm(Kind.EQUAL, var, c.tm.mkInteger(v))
                 for v in sorted(codes)]
        return c.tm.mkTerm(Kind.OR, *terms) if len(terms) > 1 else terms[0]

    def claim(codes_a, codes_b, label, expected):
        # exists x in A and not in B
        x = z3.Int("x")
        s = z3.Solver()
        s.add(member(x, codes_a), z3.Not(member(x, codes_b)))
        zv = str(s.check())
        c = C5()
        var = c.tm.mkConst(c.tm.getIntegerSort(), "x")
        c.slv.assertFormula(c5_member(c, var, codes_a))
        c.slv.assertFormula(c.tm.mkTerm(Kind.NOT, c5_member(c, var, codes_b)))
        cv = c.check()
        return both(label, zv, cv, expected)

    return [
        claim(baseline, expanded, "P2a_subset_violation", "unsat"),
        claim(expanded, baseline, "P2b_expansion_adds_configuration", "sat"),
        claim(baseline, baseline, "P2c_erasure_control_same_set", "unsat"),
    ], {"baseline_count": len(baseline), "expanded_count": len(expanded)}


# --------------------------------------------------------------------- P3
def p3(source):
    pkt = next(p for p in source["base_packets"]
               if p["packet_id"] == "v7_contextuality_heldout_relation")
    words = [tuple(int(c) for c in w) for w in pkt["accepted_words"]]
    contexts = {}
    for w in words:
        contexts.setdefault(w[:3], set()).add(w[3])
    det = {ctx: next(iter(o)) for ctx, o in sorted(contexts.items())
           if len(o) == 1}
    assert det, "need at least one deterministic context"

    def run(drop_exclusions, label, expected):
        # booleans obs[i][o]: observation admits outcome o at context i;
        # partition admits both. Claim: exists i with set equality.
        idx = list(det)
        z_obs = {(i, o): z3.Bool(f"obs_{i}_{o}")
                 for i in range(len(idx)) for o in (0, 1)}
        pins = []
        for i, ctx in enumerate(idx):
            for o in (0, 1):
                val = True if drop_exclusions else (o == det[ctx])
                pins.append(z_obs[(i, o)] == val)
        match = z3.Or([z3.And(z_obs[(i, 0)] == True,  # noqa: E712
                              z_obs[(i, 1)] == True)  # noqa: E712
                       for i in range(len(idx))])
        s = z3.Solver()
        s.add(*pins, match)
        zv = str(s.check())
        c = C5()
        obs = {}
        for i, ctx in enumerate(idx):
            for o in (0, 1):
                b = c.tm.mkConst(c.tm.getBooleanSort(), f"obs_{i}_{o}")
                val = True if drop_exclusions else (o == det[ctx])
                c.slv.assertFormula(
                    c.tm.mkTerm(Kind.EQUAL, b, c.tm.mkBoolean(val)))
                obs[(i, o)] = b
        ands = [c.tm.mkTerm(Kind.AND, obs[(i, 0)], obs[(i, 1)])
                for i in range(len(idx))]
        c.slv.assertFormula(c.tm.mkTerm(Kind.OR, *ands)
                            if len(ands) > 1 else ands[0])
        cv = c.check()
        return both(label, zv, cv, expected)

    return [
        run(False, "P3a_partition_matches_observation_somewhere", "unsat"),
        run(True, "P3b_erasure_control_exclusions_dropped", "sat"),
    ], {"deterministic_context_count": len(det)}


def main() -> int:
    source = json.loads((RESULTS / "source_packets.json").read_text())
    base = json.loads((RESULTS / "base_mss.json").read_text())
    order = base["candidate_evaluations"]["finite_relation"][
        "presumption_vector_order"]
    vectors = {n: base["candidate_evaluations"][n]["presumption_vector"]
               for n in ("finite_relation", "finite_automaton")}

    rows = p1(vectors, order)
    p2_rows, p2_meta = p2(source["nesting_packets"])
    rows += p2_rows
    p3_rows, p3_meta = p3(source)
    rows += p3_rows

    checks = {r["proof"]: r["pass"] for r in rows}
    flips = {
        "P1_flip": checks["P1a_relation_dominates_automaton"]
        and checks["P1c_erasure_control_domination"],
        "P2_flip": checks["P2b_expansion_adds_configuration"]
        and checks["P2c_erasure_control_same_set"],
        "P3_flip": checks["P3a_partition_matches_observation_somewhere"]
        and checks["P3b_erasure_control_exclusions_dropped"],
    }
    result = {
        "schema": "ratchet.v8.proof-order-lane.v2",
        "proofs": rows,
        "computed_inputs": {
            "presumption_vectors": vectors,
            "vector_order": order,
            **p2_meta, **p3_meta,
        },
        "verdict_flips": flips,
        "checks": checks,
        "all_pass": all(checks.values()) and all(flips.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("dual-solver structural proofs over archived "
                          "receipt values; packet-relative only"),
    }
    result["result_digest"] = digest(result)
    write_json(RESULTS / "proof_order_lane.json", result)
    print(json.dumps({"all_pass": result["all_pass"], "checks": checks,
                      "flips": flips}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
