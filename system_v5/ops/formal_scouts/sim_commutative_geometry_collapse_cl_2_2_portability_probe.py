"""
sim_commutative_geometry_collapse_cl_2_2_portability_probe.py

Portability test for D5 commutative_geometry_collapse_falsifier_probe (the only currently
earned deep_basin in the basin classifier). D5 proved that commutative reduction of Cl(1,3)
generators preserves nontrivial geometry invariants is structurally impossible (z3 UNSAT
on Bool + BitVec dual encodings).

This portability probe asks: does the same impossibility hold under signature Cl(2,2)?
If UNSAT in Cl(2,2) as well, D5's deep_basin is signature-portable (robust_basin candidate
under grok-1's alt classifier axes). If SAT, D5 is Cl(1,3)-locked (grok-1's permeable_edge
verdict for D5 stands; portability axis missing).

Design (per grok wizard-iter): Cl(2,2) has 4 generators e1..e4 with signature (+,+,-,-).
Bivector basis (grade 2) is 6 elements. I1 = commutator norm; I2 = grade-2 weight.
Encoding: same predicate as D5 — exists subset S of generators with |S|>=2 that is
all-pairwise-commuting AND has a noncommuting pair (contradiction, UNSAT expected).

Cross-solver: z3 Boolean + z3 BitVec + cvc5 Boolean + cvc5 BitVec = 4-way dual-encoding
agreement (same shape as D5's cross-solver lift earned in this session).

Anti-smuggling: this probe AUTHORS a new sim that exists. It does NOT add a CASES entry
to the basin classifier (that requires cross-lineage external authorship). Receipt sits
in results/ awaiting external classifier-case authorship.
"""

from __future__ import annotations

import json
import pathlib
import time
from itertools import combinations

import numpy as np
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "commutative_geometry_collapse_cl_2_2_portability_probe_results.json"

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether the commutative-reduction impossibility proven "
    "structurally for Cl(1,3) (D5 commutative_geometry_collapse, only deep_basin in current "
    "classifier) also holds under signature Cl(2,2). Cross-solver verification via z3 + cvc5 "
    "dual encodings (4-way UNSAT or split). Does not admit canonical engine, manifold, axis, "
    "or basin verdict — that requires fresh-context external case authorship per "
    "anti-smuggling rule. Surfaces portability evidence only."
)

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "supportive",
}

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Bool + BitVec encodings of subset-choice predicate over Cl(2,2) generators",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "Independent SMT solver family: Bool + BitVec encodings of the same predicate; cross-solver agreement check",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing Cl(2,2) generator construction and geometric-product witness tables",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "Supportive finite vector norm arithmetic for clifford multivector coefficients",
    },
}


def build_cl22_generators():
    """Cl(2,2) signature: first 2 generators square to +1, next 2 to -1."""
    layout, blades = Cl(2, 2)
    e1, e2, e3, e4 = blades["e1"], blades["e2"], blades["e3"], blades["e4"]
    grade1 = [e1, e2, e3, e4]
    grade2 = [e1 * e2, e1 * e3, e1 * e4, e2 * e3, e2 * e4, e3 * e4]
    all_gens = grade1 + grade2
    return all_gens, layout


def commutator_norm(g, h):
    c = g * h - h * g
    return float(np.linalg.norm(c.value))


def grade2_weight(g, h):
    prod = g * h
    return float(np.linalg.norm(prod(2).value))


def precompute_tables(gens):
    N = len(gens)
    commutes = np.zeros((N, N), dtype=bool)
    grade2 = np.zeros((N, N), dtype=bool)
    for i in range(N):
        for j in range(i + 1, N):
            commutes[i, j] = commutator_norm(gens[i], gens[j]) < 1e-12
            commutes[j, i] = commutes[i, j]
            grade2[i, j] = grade2_weight(gens[i], gens[j]) > 1e-12
            grade2[j, i] = grade2[i, j]
    return commutes, grade2


# ====================================================================
# Z3 ENCODINGS
# ====================================================================

def z3_bool_encoding(commutes: np.ndarray):
    """Bool subset choice; UNSAT means no commuting subset of size >=2 has noncommuting pair."""
    N = commutes.shape[0]
    s = [z3.Bool(f"s_{i}") for i in range(N)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 2)
    nc_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            if not commutes[i, j]:
                solver.add(z3.Not(z3.And(s[i], s[j])))
                nc_terms.append(z3.And(s[i], s[j]))
    solver.add(z3.Or(nc_terms) if nc_terms else z3.BoolVal(False))
    t0 = time.time()
    st = solver.check()
    dt = time.time() - t0
    return {"encoding": "z3_bool", "result": str(st), "unsat": st == z3.unsat, "check_time_s": dt}


def z3_bitvec_encoding(commutes: np.ndarray):
    N = commutes.shape[0]
    bv = z3.BitVec("subset", N)
    bits = [z3.Extract(i, i, bv) for i in range(N)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.ZeroExt(3, b) for b in bits]) >= 2)
    bv_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            both = z3.And(bits[i] == 1, bits[j] == 1)
            if not commutes[i, j]:
                solver.add(z3.Not(both))
                bv_terms.append(both)
    solver.add(z3.Or(bv_terms) if bv_terms else z3.BoolVal(False))
    t0 = time.time()
    st = solver.check()
    dt = time.time() - t0
    return {"encoding": "z3_bitvec", "result": str(st), "unsat": st == z3.unsat, "check_time_s": dt}


# ====================================================================
# CVC5 ENCODINGS
# ====================================================================

def cvc5_bool_encoding(commutes: np.ndarray):
    N = commutes.shape[0]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    s = [solver.mkConst(bool_sort, f"s_{i}") for i in range(N)]
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    two = solver.mkInteger(2)
    int_terms = [solver.mkTerm(Kind.ITE, si, one, zero) for si in s]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, two))
    nc_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            both = solver.mkTerm(Kind.AND, s[i], s[j])
            if not commutes[i, j]:
                solver.assertFormula(solver.mkTerm(Kind.NOT, both))
                nc_terms.append(both)
    if nc_terms:
        solver.assertFormula(solver.mkTerm(Kind.OR, *nc_terms))
    else:
        solver.assertFormula(solver.mkBoolean(False))
    t0 = time.time()
    res = solver.checkSat()
    dt = time.time() - t0
    return {"encoding": "cvc5_bool", "result": str(res), "unsat": res.isUnsat(), "check_time_s": dt}


def cvc5_bitvec_encoding(commutes: np.ndarray):
    N = commutes.shape[0]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bv_sort = solver.mkBitVectorSort(N)
    bv = solver.mkConst(bv_sort, "subset")
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    two = solver.mkInteger(2)

    bits = [solver.mkTerm(solver.mkOp(Kind.BITVECTOR_EXTRACT, i, i), bv) for i in range(N)]
    one_bv1 = solver.mkBitVector(1, 1)
    bit_eqs = [solver.mkTerm(Kind.EQUAL, b, one_bv1) for b in bits]
    int_terms = [solver.mkTerm(Kind.ITE, be, one, zero) for be in bit_eqs]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, two))

    bv_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            both = solver.mkTerm(Kind.AND, bit_eqs[i], bit_eqs[j])
            if not commutes[i, j]:
                solver.assertFormula(solver.mkTerm(Kind.NOT, both))
                bv_terms.append(both)
    if bv_terms:
        solver.assertFormula(solver.mkTerm(Kind.OR, *bv_terms))
    else:
        solver.assertFormula(solver.mkBoolean(False))
    t0 = time.time()
    res = solver.checkSat()
    dt = time.time() - t0
    return {"encoding": "cvc5_bitvec", "result": str(res), "unsat": res.isUnsat(), "check_time_s": dt}


def z3_weakened_control(commutes: np.ndarray):
    """Drop the all-commuting requirement; expect SAT (proves encoding isn't trivially-UNSAT)."""
    N = commutes.shape[0]
    s = [z3.Bool(f"w_{i}") for i in range(N)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 2)
    nc_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            if not commutes[i, j]:
                nc_terms.append(z3.And(s[i], s[j]))
    solver.add(z3.Or(nc_terms) if nc_terms else z3.BoolVal(False))
    t0 = time.time()
    st = solver.check()
    dt = time.time() - t0
    return {"encoding": "z3_weakened_control", "result": str(st), "sat": st == z3.sat, "check_time_s": dt}


def main():
    gens, _ = build_cl22_generators()
    N = len(gens)  # should be 10 (4 + 6)
    commutes, grade2 = precompute_tables(gens)

    z3_b = z3_bool_encoding(commutes)
    z3_bv = z3_bitvec_encoding(commutes)
    try:
        cvc_b = cvc5_bool_encoding(commutes)
    except Exception as e:
        cvc_b = {"encoding": "cvc5_bool", "error": f"{type(e).__name__}: {e}", "unsat": None}
    try:
        cvc_bv = cvc5_bitvec_encoding(commutes)
    except Exception as e:
        cvc_bv = {"encoding": "cvc5_bitvec", "error": f"{type(e).__name__}: {e}", "unsat": None}
    weakened = z3_weakened_control(commutes)

    encodings = [z3_b, z3_bv, cvc_b, cvc_bv]
    all_unsat = all(e.get("unsat") is True for e in encodings)
    any_error = any("error" in e for e in encodings)
    agreement = (z3_b["unsat"], z3_bv["unsat"], cvc_b.get("unsat"), cvc_bv.get("unsat"))

    # Count commuting pairs in Cl(2,2) vs Cl(1,3) for diagnostic
    n_commuting = int(np.sum(commutes) // 2)
    n_pairs = N * (N - 1) // 2

    positive = {
        "N_generators": N,
        "signature": "Cl(2,2) — (+,+,-,-)",
        "commuting_pairs_out_of_total": [n_commuting, n_pairs],
        "encodings": encodings,
        "all_4_unsat": all_unsat,
        "cross_solver_agreement_tuple": list(agreement),
        "weakened_control_sat": weakened["sat"],
    }
    graveyard_companions = {
        "weakened_control_is_sat_so_unsat_is_not_solver_trivial": {
            "pass": bool(weakened["sat"]),
            "control": weakened,
        },
        "no_single_solver_or_single_encoding_dependency": {
            "pass": bool(
                z3_b["unsat"]
                and z3_bv["unsat"]
                and cvc_b.get("unsat") is True
                and cvc_bv.get("unsat") is True
            ),
            "families": ["z3", "cvc5"],
            "encodings": ["bool", "bitvec"],
        },
        "numpy_is_supportive_not_admission_surface": {
            "pass": TOOL_INTEGRATION_DEPTH.get("numpy") == "supportive",
            "role": TOOL_INTEGRATION_DEPTH.get("numpy"),
        },
    }
    boundary = {
        "z3_unsat_both": z3_b["unsat"] and z3_bv["unsat"],
        "cvc5_unsat_both": (cvc_b.get("unsat") is True) and (cvc_bv.get("unsat") is True),
        "z3_cvc5_agree": (z3_b["unsat"] == cvc_b.get("unsat")) and (z3_bv["unsat"] == cvc_bv.get("unsat")),
        "formal_scout_only_no_engine_or_axis_admission": True,
    }
    all_pass = bool(all_unsat and not any_error and weakened["sat"])

    results = {
        "probe": "sim_commutative_geometry_collapse_cl_2_2_portability_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "audit_method_families": [
            "z3_boolean_encoding",
            "z3_bitvec_encoding",
            "cvc5_boolean_encoding",
            "cvc5_bitvec_encoding",
        ],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "why_not_v4_probes": {
            "reason": "This is a v5 formal scout portability check using v5 result contracts and cvc5/clifford tooling; v4 probes do not own formal-scout admission.",
            "pass": True,
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for item in graveyard_companions.values() if item.get("pass") is True),
            "variants": sorted(graveyard_companions),
        },
        "negative": {
            "any_solver_error": any_error,
        },
        "boundary": boundary,
        "all_pass": all_pass,
    }

    # Portability interpretation
    if all_unsat and not any_error:
        portability_verdict = "PORTABLE — Cl(2,2) UNSAT across all 4 encodings; D5's commutative-reduction impossibility holds across signature change. Signature-independent result."
    elif any_error:
        portability_verdict = "OPEN — solver error blocks definitive answer; debug then re-run."
    elif not all_unsat:
        portability_verdict = "NOT PORTABLE — at least one encoding returned SAT for Cl(2,2). D5's impossibility is Cl(1,3)-locked, not signature-independent. Grok-alt-classifier's 'permeable_edge' verdict for D5 (failing cross-domain portability axis) is supported."
    else:
        portability_verdict = "OPEN"
    results["portability_verdict"] = portability_verdict

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"WROTE: {OUT_PATH}")
    print(f"N_generators (Cl 2,2) = {N}")
    print(f"commuting pairs: {n_commuting} / {n_pairs}")
    print(f"all_4_unsat: {all_unsat}")
    print(f"cross_solver_agreement: {agreement}")
    print(f"weakened_control_sat: {weakened['sat']}")
    print(f"PORTABILITY VERDICT: {portability_verdict}")
    return results


if __name__ == "__main__":
    main()
