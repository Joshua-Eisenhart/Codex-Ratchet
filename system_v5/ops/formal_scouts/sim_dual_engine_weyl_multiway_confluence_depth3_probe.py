"""
sim_dual_engine_weyl_multiway_confluence_depth3_probe.py

DEPTH-3 multiway / confluence deepening of the verified order-proof sim.
Builds on sim_dual_engine_weyl_layer_composition_order_proof_probe (verified
twice-clean). For every triple {A,B,C} of the 5 layer operators, applies all
3!=6 orderings to the Weyl-spinor carrier and asks: do the 6 final states
COLLAPSE to one (confluent / "causal-invariant" at depth 3) or fan out to
several distinct states (non-confluent)? This tests the parked question:
does pairwise non-commutativity force depth-3 non-confluence, or can orders
re-converge?

n_distinct(triple) = number of clusters of the 6 final states under trace
distance < EPS. confluence_gap = max pairwise trace distance over the 6.

Dual-engine (torch primary / jax parity). Proof (z3+cvc5) load-bearing by
mutation: "all 6 orderings collapse to 1 state" is UNSAT for a non-confluent
triple given the measured pairwise gaps, and flips to SAT under gap-erasure.

NOTE: confluence here is STATE-LEVEL (all orderings reach the same density
matrix), the strongest form of Wolfram-style causal invariance restricted to
this bounded depth-3 rule budget; it is NOT the full causal-graph-isomorphism
notion. classification="diagnostic_only"; promotion_allowed=False.
"""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402

import json  # noqa: E402
import math  # noqa: E402
import pathlib  # noqa: E402
import itertools  # noqa: E402
from fractions import Fraction  # noqa: E402
import functools  # noqa: E402
import torch  # noqa: E402
import z3  # noqa: E402
try:
    import cvc5
    from cvc5 import Kind
    HAVE_CVC5 = True
except Exception:
    HAVE_CVC5 = False

# Reuse the VERIFIED building blocks (carrier, operators, channel application,
# trace distance, reduced entropy) from the twice-clean order-proof sim.
from sim_dual_engine_weyl_layer_composition_order_proof_probe import (  # noqa: E402
    OP_NAMES, EPS,
    carrier_t, kraus_t, apply_t, trace_dist_t, reduced0_t, vn_entropy_t,
    carrier_j, kraus_j, apply_j, trace_dist_j,
)

SIM_ID = "dual_engine_weyl_multiway_confluence_depth3_probe"
TRIPLES = list(itertools.combinations(OP_NAMES, 3))  # C(5,3)=10

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "primary complex128 multiway composition substrate"},
    "jax": {"tried": True, "used": True, "reason": "second-engine parity (x64) recompute of confluence gaps"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: 'all 6 orderings collapse to 1' UNSAT for non-confluent triples; flips under erasure"},
    "cvc5": {"tried": True, "used": HAVE_CVC5, "reason": "second SMT family cross-check of confluence verdict"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "jax": "load_bearing", "z3": "load_bearing",
                          "cvc5": ("load_bearing" if HAVE_CVC5 else None)}


def compose_seq_t(names, rho):
    return functools.reduce(lambda r, n: apply_t(kraus_t(n), r), names, rho)


def compose_seq_j(names, rho):
    return functools.reduce(lambda r, n: apply_j(kraus_j(n), r), names, rho)


def cluster_count(states, dist_fn, eps=EPS):
    """Union states whose pairwise distance < eps; return (n_clusters, max_pairwise_dist)."""
    n = len(states)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    maxd = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            d = float(dist_fn(states[i], states[j]))
            maxd = max(maxd, d)
            if d < eps:
                parent[find(i)] = find(j)
    return len({find(i) for i in range(n)}), maxd


def run_torch():
    rho = carrier_t()
    rows = []
    for tri in TRIPLES:
        perms = list(itertools.permutations(tri))
        states = [compose_seq_t(list(p), rho) for p in perms]
        n_dist, maxd = cluster_count(states, trace_dist_t)
        ent_spread = max(vn_entropy_t(reduced0_t(s)) for s in states) - min(vn_entropy_t(reduced0_t(s)) for s in states)
        rows.append({"triple": "|".join(tri), "n_distinct": n_dist, "confluence_gap": maxd,
                     "confluent": bool(n_dist == 1), "has_Rsu2": "Rsu2" in tri,
                     "entropy_spread": ent_spread})
    return rows


def run_jax():
    rho = carrier_j()
    rows = {}
    for tri in TRIPLES:
        perms = list(itertools.permutations(tri))
        states = [compose_seq_j(list(p), rho) for p in perms]
        n_dist, maxd = cluster_count(states, trace_dist_j)
        rows["|".join(tri)] = {"n_distinct": n_dist, "confluence_gap": maxd}
    return rows


def z3_confluence(rows, erase=False):
    """For each triple, assert confluence_gap == measured and gap <= eps
    ('triple is confluent: all orderings collapse'). A non-confluent triple
    (measured gap > eps) makes this UNSAT. Erase to 0 -> SAT. The flip proves
    the solver consumed the measured confluence gaps."""
    s = z3.Solver()
    for r in rows:
        v = z3.Real("cg_" + r["triple"].replace("|", "_"))
        s.add(v == z3.RealVal(repr(0.0 if erase else float(r["confluence_gap"]))))
        s.add(v <= z3.RealVal(repr(EPS)))
    return str(s.check())


def cvc5_confluence(rows, erase=False):
    if not HAVE_CVC5:
        return "n/a"
    sv = cvc5.Solver(); sv.setLogic("QF_LRA")
    R = sv.getRealSort()

    def rv(x):
        fr = Fraction(float(x)).limit_denominator(10 ** 15)
        return sv.mkReal(fr.numerator, fr.denominator)

    for r in rows:
        v = sv.mkConst(R, "cg_" + r["triple"].replace("|", "_"))
        sv.assertFormula(sv.mkTerm(Kind.EQUAL, v, rv(0.0 if erase else r["confluence_gap"])))
        sv.assertFormula(sv.mkTerm(Kind.LEQ, v, rv(EPS)))
    return str(sv.checkSat())


def main():
    t_rows = run_torch()
    j_rows = run_jax()

    max_gap_delta = max(abs(r["confluence_gap"] - j_rows[r["triple"]]["confluence_gap"]) for r in t_rows)
    same_ndistinct = all(r["n_distinct"] == j_rows[r["triple"]]["n_distinct"] for r in t_rows)

    z3_real, z3_erased = z3_confluence(t_rows, False), z3_confluence(t_rows, True)
    cvc5_real, cvc5_erased = cvc5_confluence(t_rows, False), cvc5_confluence(t_rows, True)
    proof_load_bearing = bool(z3_real == "unsat" and z3_erased == "sat"
                              and (not HAVE_CVC5 or (cvc5_real == "unsat" and cvc5_erased == "sat")))

    confluent_triples = [r["triple"] for r in t_rows if r["confluent"]]
    nonconfluent = [r for r in t_rows if not r["confluent"]]
    # KEY QUESTION: among non-confluent triples (all contain Rsu2?), how many distinct states?
    rsu2_triples = [r for r in t_rows if r["has_Rsu2"]]
    nonrsu2_triples = [r for r in t_rows if not r["has_Rsu2"]]

    known_value_checks = [
        {"invariant": "all Rsu2-free triples are CONFLUENT (n_distinct==1)",
         "computed": str([r["n_distinct"] for r in nonrsu2_triples]), "known": "all 1",
         "match": all(r["confluent"] for r in nonrsu2_triples)},
        {"invariant": "all Rsu2-containing triples are NON-confluent (n_distinct>1)",
         "computed": str([r["n_distinct"] for r in rsu2_triples]), "known": "all >1",
         "match": all(not r["confluent"] for r in rsu2_triples)},
        {"invariant": "z3 confluence UNSAT on real data (some triple non-confluent)",
         "computed": z3_real, "known": "unsat", "match": z3_real == "unsat"},
        {"invariant": "z3 flips to SAT under gap-erasure (load-bearing)",
         "computed": z3_erased, "known": "sat", "match": z3_erased == "sat"},
        {"invariant": "cvc5 confluence UNSAT on real data",
         "computed": cvc5_real, "known": "unsat", "match": (cvc5_real == "unsat") or not HAVE_CVC5},
        {"invariant": "dual-engine max confluence-gap delta < 1e-9",
         "computed": f"{max_gap_delta:.2e}", "known": "<1e-9", "match": bool(max_gap_delta < 1e-9)},
        {"invariant": "dual-engine same n_distinct per triple", "computed": str(same_ndistinct),
         "known": "True", "match": same_ndistinct},
    ]
    all_pass = bool(all(c["match"] for c in known_value_checks) and proof_load_bearing)

    out = {
        "sim_id": SIM_ID, "classification": "diagnostic_only", "promotion_allowed": False,
        "claim_ceiling": "Depth-3 STATE-LEVEL confluence diagnostic on a bounded 3-rule budget; not full causal-graph-isomorphism causal invariance.",
        "triples": t_rows,
        "confluent_triples": confluent_triples,
        "nonconfluent_summary": [{"triple": r["triple"], "n_distinct": r["n_distinct"], "confluence_gap": r["confluence_gap"]} for r in nonconfluent],
        "finding": "Rsu2 (sole basis-rotating op) controls depth-3 confluence: triples without it collapse all 6 orderings to 1 state; triples with it fan out." if (all(r["confluent"] for r in nonrsu2_triples) and all(not r["confluent"] for r in rsu2_triples)) else "mixed - see triples",
        "max_n_distinct": max(r["n_distinct"] for r in t_rows),
        "dual_engine_max_gap_delta": max_gap_delta, "dual_engine_same_ndistinct": same_ndistinct,
        "proof_real_verdict": {"z3": z3_real, "cvc5": cvc5_real},
        "proof_erased_verdict": {"z3": z3_erased, "cvc5": cvc5_erased},
        "proof_load_bearing": proof_load_bearing,
        "known_value_checks": known_value_checks, "all_pass": all_pass,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "blockers": [],
    }
    outdir = pathlib.Path(__file__).parent / "results"
    outdir.mkdir(exist_ok=True)
    (outdir / f"{SIM_ID}_results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"triples": [(r["triple"], r["n_distinct"], round(r["confluence_gap"], 4)) for r in t_rows],
                      "max_n_distinct": out["max_n_distinct"], "proof_load_bearing": proof_load_bearing,
                      "proof_real": out["proof_real_verdict"], "proof_erased": out["proof_erased_verdict"],
                      "dual_engine_same_ndistinct": same_ndistinct, "all_pass": all_pass,
                      "finding": out["finding"]}, indent=2))
    return out


if __name__ == "__main__":
    main()
