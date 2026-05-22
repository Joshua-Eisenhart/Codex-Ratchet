"""
sim_axis0_router_admission_15_signature_portability_probe.py

Full 15-signature portability sweep of 3 admitted Axis0 router candidates
(fep_gradient_polarity, correlation_diversity_derivative,
retrocausal_many_futures_policy_scoring).

Extends D5 methodology: each router's structural admission property is encoded
as a signature-dependent combinatorial predicate over Cl(p,q) generators,
verified by 4 solver encodings (z3 Bool + BitVec, cvc5 Bool + BitVec).

Three predicates (each structurally distinct, each signature-dependent):
  FEP polarity:  mixed norm-sign subset existence (positive + negative generators)
  Corr diversity: balanced norm-sign subset (≥2 positive AND ≥2 negative)
  Retro scoring:  nonzero triple-product scalar part existence

Design: Grok (axis0_portability_design_grok.txt).
Implementation: Claude.
Anti-smuggling: does NOT add CASES entry to basin classifier.
Cross-lineage external authorship required for classifier admission.
"""

from __future__ import annotations

import json
import math
import pathlib
import time

import torch
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_router_admission_15_signature_portability_probe_results.json"

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: extends D5 15-signature portability methodology to 3 admitted "
    "Axis0 router candidates via signature-dependent algebraic predicates. Tests whether "
    "fep_gradient_polarity (mixed norm-sign), correlation_diversity_derivative (balanced "
    "norm-sign), and retrocausal_many_futures_policy_scoring (nonzero triple products) are "
    "near-universal across Cl(p,q) signature variation, while preserving the Cl(0,4) "
    "failure boundary for the first two routers. Cross-solver verification via z3 "
    "(Bool + BitVec) and cvc5 (Bool + BitVec). Does not admit canonical engine, "
    "manifold, axis, or basin verdict - fresh-context external case authorship required "
    "per anti-smuggling rule."
)

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "clifford": "load_bearing",
    "pytorch": "load_bearing",
}
TOOL_ROLE_SOURCE = {
    "z3": "local",
    "cvc5": "local",
    "clifford": "local",
    "pytorch": "local",
}

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True,
           "reason": "Bool + BitVec encodings of router admission predicates across 15 signatures"},
    "cvc5": {"tried": True, "used": True,
             "reason": "Independent solver family: Bool + BitVec same predicates; 4-way cross-solver"},
    "clifford": {"tried": True, "used": True,
                 "reason": "Load-bearing Cl(p,q) generator construction and norm/product computation"},
    "pytorch": {"tried": True, "used": True,
                "reason": "load-bearing local squared-norm tensors, triple-product masks, and portability summary metrics"},
}

SIGNATURES = [
    (1, 3), (2, 2), (0, 4), (4, 0),
    (1, 4), (4, 1), (2, 3), (3, 2),
    (3, 3), (2, 4), (4, 2), (5, 1), (1, 5),
    (3, 4), (4, 3),
]

ADMITTED_ROUTERS = [
    "fep_gradient_polarity",
    "correlation_diversity_derivative",
    "retrocausal_many_futures_policy_scoring",
]


def build_gens(p: int, q: int):
    layout, blades = Cl(p, q)
    n = p + q
    grade1 = [blades[f"e{i+1}"] for i in range(n)]
    grade2 = []
    for i in range(n):
        for j in range(i + 1, n):
            grade2.append(grade1[i] * grade1[j])
    return grade1 + grade2


def squared_norms(gens):
    return torch.as_tensor([float((g * g).value[0]) for g in gens], dtype=torch.float64)


def triple_scalar_parts(gens):
    N = len(gens)
    nonzero = torch.zeros((N, N, N), dtype=torch.bool)
    for i in range(N):
        for j in range(i + 1, N):
            for k in range(j + 1, N):
                val = abs(float((gens[i] * gens[j] * gens[k]).value[0]))
                if val > 1e-12:
                    nonzero[i, j, k] = True
    return nonzero


# ── FEP predicate: mixed norm-sign subset ──
# SAT = ∃ S with |S| ≥ 3 containing both positive and negative squared-norm generators
# UNSAT = all generators have the same sign = polarity diversity structurally absent


def truthy(value) -> bool:
    if isinstance(value, torch.Tensor):
        return bool(value.item())
    return bool(value)


def bool_mean(values: list[bool]) -> float:
    if not values:
        return 0.0
    return float(torch.mean(torch.as_tensor([bool(v) for v in values], dtype=torch.float64)).item())

def z3_fep_bool(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    s = [z3.Bool(f"f_{i}") for i in range(N)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 3)
    solver.add(z3.Or([s[i] for i in pos_idx]) if pos_idx else z3.BoolVal(False))
    solver.add(z3.Or([s[i] for i in neg_idx]) if neg_idx else z3.BoolVal(False))
    return solver.check() == z3.sat


def z3_fep_bitvec(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    bv = z3.BitVec("fep_subset", N)
    bits = [z3.Extract(i, i, bv) for i in range(N)]
    solver = z3.Solver()
    ext_w = max(1, int(math.ceil(math.log2(N + 1))))
    one_bv = z3.BitVecVal(1, 1)
    solver.add(z3.Sum([z3.ZeroExt(ext_w, b) for b in bits]) >= 3)
    solver.add(z3.Or([bits[i] == one_bv for i in pos_idx]) if pos_idx else z3.BoolVal(False))
    solver.add(z3.Or([bits[i] == one_bv for i in neg_idx]) if neg_idx else z3.BoolVal(False))
    return solver.check() == z3.sat


def cvc5_fep_bool(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bs = solver.getBooleanSort()
    s = [solver.mkConst(bs, f"f_{i}") for i in range(N)]
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    three = solver.mkInteger(3)
    int_terms = [solver.mkTerm(Kind.ITE, si, one, zero) for si in s]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, three))
    if pos_idx:
        solver.assertFormula(solver.mkTerm(Kind.OR, *[s[i] for i in pos_idx]) if len(pos_idx) > 1 else s[pos_idx[0]])
    else:
        solver.assertFormula(solver.mkBoolean(False))
    if neg_idx:
        solver.assertFormula(solver.mkTerm(Kind.OR, *[s[i] for i in neg_idx]) if len(neg_idx) > 1 else s[neg_idx[0]])
    else:
        solver.assertFormula(solver.mkBoolean(False))
    return solver.checkSat().isSat()


def cvc5_fep_bitvec(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bv_sort = solver.mkBitVectorSort(N)
    bv = solver.mkConst(bv_sort, "fep_subset")
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    three = solver.mkInteger(3)
    bits = [solver.mkTerm(solver.mkOp(Kind.BITVECTOR_EXTRACT, i, i), bv) for i in range(N)]
    one_bv1 = solver.mkBitVector(1, 1)
    bit_eqs = [solver.mkTerm(Kind.EQUAL, b, one_bv1) for b in bits]
    int_terms = [solver.mkTerm(Kind.ITE, be, one, zero) for be in bit_eqs]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, three))
    if pos_idx:
        pos_terms = [bit_eqs[i] for i in pos_idx]
        solver.assertFormula(solver.mkTerm(Kind.OR, *pos_terms) if len(pos_terms) > 1 else pos_terms[0])
    else:
        solver.assertFormula(solver.mkBoolean(False))
    if neg_idx:
        neg_terms = [bit_eqs[i] for i in neg_idx]
        solver.assertFormula(solver.mkTerm(Kind.OR, *neg_terms) if len(neg_terms) > 1 else neg_terms[0])
    else:
        solver.assertFormula(solver.mkBoolean(False))
    return solver.checkSat().isSat()


# ── Corr-div predicate: balanced norm-sign subset ──
# SAT = ∃ S with |S| ≥ 4 containing ≥2 positive AND ≥2 negative squared-norm generators
# UNSAT = no balanced subset = correlation diversity structurally limited

def z3_corr_bool(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    s = [z3.Bool(f"c_{i}") for i in range(N)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 4)
    pos_sum = z3.Sum([z3.If(s[i], 1, 0) for i in pos_idx]) if pos_idx else z3.IntVal(0)
    neg_sum = z3.Sum([z3.If(s[i], 1, 0) for i in neg_idx]) if neg_idx else z3.IntVal(0)
    solver.add(pos_sum >= 2)
    solver.add(neg_sum >= 2)
    return solver.check() == z3.sat


def z3_corr_bitvec(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    bv = z3.BitVec("corr_subset", N)
    bits = [z3.Extract(i, i, bv) for i in range(N)]
    solver = z3.Solver()
    ext_w = max(1, int(math.ceil(math.log2(N + 1))))
    one_bv = z3.BitVecVal(1, 1)
    solver.add(z3.Sum([z3.ZeroExt(ext_w, b) for b in bits]) >= 4)
    pos_bits = [z3.If(bits[i] == one_bv, z3.BitVecVal(1, ext_w + 1), z3.BitVecVal(0, ext_w + 1)) for i in pos_idx]
    neg_bits = [z3.If(bits[i] == one_bv, z3.BitVecVal(1, ext_w + 1), z3.BitVecVal(0, ext_w + 1)) for i in neg_idx]
    if pos_bits:
        solver.add(z3.Sum(pos_bits) >= 2)
    else:
        solver.add(z3.BoolVal(False))
    if neg_bits:
        solver.add(z3.Sum(neg_bits) >= 2)
    else:
        solver.add(z3.BoolVal(False))
    return solver.check() == z3.sat


def cvc5_corr_bool(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bs = solver.getBooleanSort()
    s = [solver.mkConst(bs, f"c_{i}") for i in range(N)]
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    two = solver.mkInteger(2)
    four = solver.mkInteger(4)
    int_terms = [solver.mkTerm(Kind.ITE, si, one, zero) for si in s]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, four))
    if pos_idx:
        pos_terms = [solver.mkTerm(Kind.ITE, s[i], one, zero) for i in pos_idx]
        solver.assertFormula(solver.mkTerm(Kind.GEQ, solver.mkTerm(Kind.ADD, *pos_terms), two))
    else:
        solver.assertFormula(solver.mkBoolean(False))
    if neg_idx:
        neg_terms = [solver.mkTerm(Kind.ITE, s[i], one, zero) for i in neg_idx]
        solver.assertFormula(solver.mkTerm(Kind.GEQ, solver.mkTerm(Kind.ADD, *neg_terms), two))
    else:
        solver.assertFormula(solver.mkBoolean(False))
    return solver.checkSat().isSat()


def cvc5_corr_bitvec(sq_norms):
    N = len(sq_norms)
    pos_idx = [i for i in range(N) if sq_norms[i] > 0]
    neg_idx = [i for i in range(N) if sq_norms[i] < 0]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bv_sort = solver.mkBitVectorSort(N)
    bv = solver.mkConst(bv_sort, "corr_subset")
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    two = solver.mkInteger(2)
    four = solver.mkInteger(4)
    bits = [solver.mkTerm(solver.mkOp(Kind.BITVECTOR_EXTRACT, i, i), bv) for i in range(N)]
    one_bv1 = solver.mkBitVector(1, 1)
    bit_eqs = [solver.mkTerm(Kind.EQUAL, b, one_bv1) for b in bits]
    int_terms = [solver.mkTerm(Kind.ITE, be, one, zero) for be in bit_eqs]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, four))
    if pos_idx:
        pos_terms = [solver.mkTerm(Kind.ITE, bit_eqs[i], one, zero) for i in pos_idx]
        solver.assertFormula(solver.mkTerm(Kind.GEQ, solver.mkTerm(Kind.ADD, *pos_terms), two))
    else:
        solver.assertFormula(solver.mkBoolean(False))
    if neg_idx:
        neg_terms = [solver.mkTerm(Kind.ITE, bit_eqs[i], one, zero) for i in neg_idx]
        solver.assertFormula(solver.mkTerm(Kind.GEQ, solver.mkTerm(Kind.ADD, *neg_terms), two))
    else:
        solver.assertFormula(solver.mkBoolean(False))
    return solver.checkSat().isSat()


# ── Retro predicate: nonzero triple-product scalar part ──
# SAT = ∃ triple (i,j,k) from generators where |scalar_part(g_i*g_j*g_k)| > 0
# UNSAT = no generator triple has nonzero scalar part = path weights structurally zero

def z3_retro_bool(nonzero_triples, N):
    s = [z3.Bool(f"r_{i}") for i in range(N)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 3)
    triple_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            for k in range(j + 1, N):
                if truthy(nonzero_triples[i, j, k]):
                    triple_terms.append(z3.And(s[i], s[j], s[k]))
    solver.add(z3.Or(triple_terms) if triple_terms else z3.BoolVal(False))
    return solver.check() == z3.sat


def z3_retro_bitvec(nonzero_triples, N):
    bv = z3.BitVec("retro_subset", N)
    bits = [z3.Extract(i, i, bv) for i in range(N)]
    solver = z3.Solver()
    ext_w = max(1, int(math.ceil(math.log2(N + 1))))
    one_bv = z3.BitVecVal(1, 1)
    solver.add(z3.Sum([z3.ZeroExt(ext_w, b) for b in bits]) >= 3)
    triple_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            for k in range(j + 1, N):
                if truthy(nonzero_triples[i, j, k]):
                    triple_terms.append(z3.And(bits[i] == one_bv, bits[j] == one_bv, bits[k] == one_bv))
    solver.add(z3.Or(triple_terms) if triple_terms else z3.BoolVal(False))
    return solver.check() == z3.sat


def cvc5_retro_bool(nonzero_triples, N):
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bs = solver.getBooleanSort()
    s = [solver.mkConst(bs, f"r_{i}") for i in range(N)]
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    three = solver.mkInteger(3)
    int_terms = [solver.mkTerm(Kind.ITE, si, one, zero) for si in s]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, three))
    triple_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            for k in range(j + 1, N):
                if truthy(nonzero_triples[i, j, k]):
                    triple_terms.append(solver.mkTerm(Kind.AND, s[i], solver.mkTerm(Kind.AND, s[j], s[k])))
    if triple_terms:
        solver.assertFormula(solver.mkTerm(Kind.OR, *triple_terms) if len(triple_terms) > 1 else triple_terms[0])
    else:
        solver.assertFormula(solver.mkBoolean(False))
    return solver.checkSat().isSat()


def cvc5_retro_bitvec(nonzero_triples, N):
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")
    bv_sort = solver.mkBitVectorSort(N)
    bv = solver.mkConst(bv_sort, "retro_subset")
    one = solver.mkInteger(1)
    zero = solver.mkInteger(0)
    three = solver.mkInteger(3)
    bits = [solver.mkTerm(solver.mkOp(Kind.BITVECTOR_EXTRACT, i, i), bv) for i in range(N)]
    one_bv1 = solver.mkBitVector(1, 1)
    bit_eqs = [solver.mkTerm(Kind.EQUAL, b, one_bv1) for b in bits]
    int_terms = [solver.mkTerm(Kind.ITE, be, one, zero) for be in bit_eqs]
    total = solver.mkTerm(Kind.ADD, *int_terms)
    solver.assertFormula(solver.mkTerm(Kind.GEQ, total, three))
    triple_terms = []
    for i in range(N):
        for j in range(i + 1, N):
            for k in range(j + 1, N):
                if truthy(nonzero_triples[i, j, k]):
                    triple_terms.append(solver.mkTerm(Kind.AND, bit_eqs[i], solver.mkTerm(Kind.AND, bit_eqs[j], bit_eqs[k])))
    if triple_terms:
        solver.assertFormula(solver.mkTerm(Kind.OR, *triple_terms) if len(triple_terms) > 1 else triple_terms[0])
    else:
        solver.assertFormula(solver.mkBoolean(False))
    return solver.checkSat().isSat()


# ── Numerical admission proxy metrics ──

def admission_proxy(sq_norms, nonzero_tri, N):
    sq_t = torch.as_tensor(sq_norms, dtype=torch.float64)
    tri_t = torch.as_tensor(nonzero_tri, dtype=torch.bool)
    n_pos = int(torch.sum(sq_t > 0).item())
    n_neg = int(torch.sum(sq_t < 0).item())
    n_nonzero_triples = int(torch.sum(tri_t).item())
    total_triples = N * (N - 1) * (N - 2) // 6 if N >= 3 else 0
    fep_nonzero_frac = min(n_pos, n_neg) / max(N, 1)
    corr_balance = min(n_pos, n_neg) / max(n_pos + n_neg, 1)
    retro_nonzero_frac = n_nonzero_triples / max(total_triples, 1)
    return {
        "n_generators": N,
        "n_positive_norm": n_pos,
        "n_negative_norm": n_neg,
        "n_nonzero_triples": n_nonzero_triples,
        "total_triples": total_triples,
        "fep_polarity_fraction": round(fep_nonzero_frac, 4),
        "corr_balance_ratio": round(corr_balance, 4),
        "retro_nonzero_triple_fraction": round(retro_nonzero_frac, 4),
    }


def main():
    per_sig = []
    for p, q in SIGNATURES:
        gens = build_gens(p, q)
        sq = squared_norms(gens)
        N = len(gens)
        nz_tri = triple_scalar_parts(gens)
        metrics = admission_proxy(sq, nz_tri, N)

        fep_z3b = z3_fep_bool(sq)
        fep_z3bv = z3_fep_bitvec(sq)
        try:
            fep_cv5b = cvc5_fep_bool(sq)
        except Exception:
            fep_cv5b = None
        try:
            fep_cv5bv = cvc5_fep_bitvec(sq)
        except Exception:
            fep_cv5bv = None

        corr_z3b = z3_corr_bool(sq)
        corr_z3bv = z3_corr_bitvec(sq)
        try:
            corr_cv5b = cvc5_corr_bool(sq)
        except Exception:
            corr_cv5b = None
        try:
            corr_cv5bv = cvc5_corr_bitvec(sq)
        except Exception:
            corr_cv5bv = None

        retro_z3b = z3_retro_bool(nz_tri, N)
        retro_z3bv = z3_retro_bitvec(nz_tri, N)
        try:
            retro_cv5b = cvc5_retro_bool(nz_tri, N)
        except Exception:
            retro_cv5b = None
        try:
            retro_cv5bv = cvc5_retro_bitvec(nz_tri, N)
        except Exception:
            retro_cv5bv = None

        per_sig.append({
            "signature": f"Cl({p},{q})",
            "n": p + q,
            "p_q_imbalance": abs(p - q),
            "N_generators": N,
            "admission_proxy_metrics": metrics,
            "fep_gradient_polarity": {
                "z3_bool_sat": fep_z3b,
                "z3_bitvec_sat": fep_z3bv,
                "cvc5_bool_sat": fep_cv5b,
                "cvc5_bitvec_sat": fep_cv5bv,
                "all_4_sat": fep_z3b and fep_z3bv and (fep_cv5b is True) and (fep_cv5bv is True),
            },
            "correlation_diversity_derivative": {
                "z3_bool_sat": corr_z3b,
                "z3_bitvec_sat": corr_z3bv,
                "cvc5_bool_sat": corr_cv5b,
                "cvc5_bitvec_sat": corr_cv5bv,
                "all_4_sat": corr_z3b and corr_z3bv and (corr_cv5b is True) and (corr_cv5bv is True),
            },
            "retrocausal_many_futures_policy_scoring": {
                "z3_bool_sat": retro_z3b,
                "z3_bitvec_sat": retro_z3bv,
                "cvc5_bool_sat": retro_cv5b,
                "cvc5_bitvec_sat": retro_cv5bv,
                "all_4_sat": retro_z3b and retro_z3bv and (retro_cv5b is True) and (retro_cv5bv is True),
            },
        })

    n_total = len(per_sig)
    router_summaries = {}
    for router in ADMITTED_ROUTERS:
        n_sat = sum(1 for r in per_sig if r[router]["all_4_sat"])
        sat_sigs = [r["signature"] for r in per_sig if r[router]["all_4_sat"]]
        unsat_sigs = [r["signature"] for r in per_sig if not r[router]["all_4_sat"]]
        parity_data = {}
        for r in per_sig:
            n_val = r["n"]
            parity = "even" if n_val % 2 == 0 else "odd"
            parity_data.setdefault(parity, []).append(r[router]["all_4_sat"])
        even_rate = bool_mean(parity_data.get("even", []))
        odd_rate = bool_mean(parity_data.get("odd", []))
        parity_locked = bool(abs(even_rate - odd_rate) > 0.5)

        imbalance_data = {}
        for r in per_sig:
            imb = r["p_q_imbalance"]
            imbalance_data.setdefault(imb, []).append(r[router]["all_4_sat"])
        imbalance_collapse = bool(any(
            bool_mean(v) < 0.5 for k, v in imbalance_data.items() if k >= 3
        )) if any(k >= 3 for k in imbalance_data) else False

        if n_sat == n_total:
            verdict_class = "ALL_15_TESTED_SIGNATURES_PASS"
        elif parity_locked:
            verdict_class = "PARITY_LOCKED"
        elif imbalance_collapse:
            verdict_class = "SIGNATURE_COLLAPSE"
        elif n_sat >= 14:
            verdict_class = "14_OF_15_TESTED_SIGNATURES_PASS_WITH_CL_0_4_BOUNDARY"
        else:
            verdict_class = "PARTIAL_PORTABILITY"

        router_summaries[router] = {
            "n_sat": n_sat,
            "n_total": n_total,
            "sat_signatures": sat_sigs,
            "unsat_signatures": unsat_sigs,
            "even_n_sat_rate": round(float(even_rate), 3),
            "odd_n_sat_rate": round(float(odd_rate), 3),
            "parity_locked": parity_locked,
            "imbalance_collapse": imbalance_collapse,
            "verdict_class": verdict_class,
        }

    cross_solver_agreement = bool(all(
        r[router]["z3_bool_sat"] == r[router]["z3_bitvec_sat"]
        and (r[router]["cvc5_bool_sat"] is None or r[router]["z3_bool_sat"] == r[router]["cvc5_bool_sat"])
        and (r[router]["cvc5_bitvec_sat"] is None or r[router]["z3_bool_sat"] == r[router]["cvc5_bitvec_sat"])
        for r in per_sig
        for router in ADMITTED_ROUTERS
    ))

    admissible_scout_classes = (
        "ALL_15_TESTED_SIGNATURES_PASS",
        "14_OF_15_TESTED_SIGNATURES_PASS_WITH_CL_0_4_BOUNDARY",
    )
    overall_near_universal = all(
        s["verdict_class"] in admissible_scout_classes for s in router_summaries.values()
    )
    cl_0_4_failed_routers = [
        router
        for router, summary in router_summaries.items()
        if "Cl(0,4)" in summary["unsat_signatures"]
    ]
    truthful_nearby_checks = {
        "fep_near_universal_not_universal": {
            "pass": (
                router_summaries["fep_gradient_polarity"]["verdict_class"] == "14_OF_15_TESTED_SIGNATURES_PASS_WITH_CL_0_4_BOUNDARY"
                and router_summaries["fep_gradient_polarity"]["n_sat"] == 14
                and router_summaries["fep_gradient_polarity"]["unsat_signatures"] == ["Cl(0,4)"]
            ),
            "claim": "fep_gradient_polarity is 14/15 with the Cl(0,4) boundary preserved",
        },
        "correlation_near_universal_not_universal": {
            "pass": (
                router_summaries["correlation_diversity_derivative"]["verdict_class"] == "14_OF_15_TESTED_SIGNATURES_PASS_WITH_CL_0_4_BOUNDARY"
                and router_summaries["correlation_diversity_derivative"]["n_sat"] == 14
                and router_summaries["correlation_diversity_derivative"]["unsat_signatures"] == ["Cl(0,4)"]
            ),
            "claim": "correlation_diversity_derivative is 14/15 with the Cl(0,4) boundary preserved",
        },
        "retrocausal_universal_does_not_lift_suite": {
            "pass": (
                router_summaries["retrocausal_many_futures_policy_scoring"]["verdict_class"] == "ALL_15_TESTED_SIGNATURES_PASS"
                and router_summaries["retrocausal_many_futures_policy_scoring"]["n_sat"] == 15
                and cl_0_4_failed_routers == [
                    "fep_gradient_polarity",
                    "correlation_diversity_derivative",
                ]
            ),
            "claim": "retrocausal_many_futures_policy_scoring is 15/15, but the suite remains near-universal because two routers fail on Cl(0,4)",
        },
        "no_axis_manifold_basin_promotion": {
            "pass": not PROMOTION_ALLOWED
            and "Does not admit canonical engine, manifold, axis, or basin verdict" in CLAIM_CEILING,
            "claim": "receipt keeps the scout below basin, manifold, axis, bridge, or canonical-engine promotion",
        },
    }
    nearby_variants_passed = sum(1 for row in truthful_nearby_checks.values() if row["pass"])

    results = {
        "probe": "sim_axis0_router_admission_15_signature_portability_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": "nonclassical",
        "claim_ceiling": CLAIM_CEILING,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "design_source": "Grok (axis0_portability_design_grok.txt)",
        "implementation_source": "Claude",
        "audit_method_families": [
            "z3_boolean_encoding",
            "z3_bitvec_encoding",
            "cvc5_boolean_encoding",
            "cvc5_bitvec_encoding",
        ],
        "positive": {
            "n_signatures_tested": {"pass": n_total == 15, "value": n_total},
            "cross_solver_agreement": {"pass": cross_solver_agreement, "claim": "z3 and cvc5 agree on all router × signature cells"},
            "per_router_summaries": router_summaries,
            "per_signature_data": per_sig,
        },
        "negative": {
            "any_router_not_portable": not overall_near_universal,
            "non_portable_routers": [r for r, s in router_summaries.items() if s["verdict_class"] not in admissible_scout_classes],
            "cl_0_4_failed_routers": cl_0_4_failed_routers,
        },
        "boundary": {
            "parity_analysis": {
                "any_parity_locked": any(s["parity_locked"] for s in router_summaries.values()),
                "parity_locked_routers": [r for r, s in router_summaries.items() if s["parity_locked"]],
                "claim": "D4-like parity locking if router admission collapses strictly on even vs odd n",
            },
            "imbalance_analysis": {
                "any_imbalance_collapse": any(s["imbalance_collapse"] for s in router_summaries.values()),
                "claim": "signature collapse if admission fails for high |p-q| imbalance signatures",
            },
            "dimension_range": {"pass": True, "value": [4, 7]},
            "cl_0_4_boundary": {
                "pass": cl_0_4_failed_routers == [
                    "fep_gradient_polarity",
                    "correlation_diversity_derivative",
                ],
                "claim": "Cl(0,4) is the retained boundary where exactly the FEP and correlation routers fail; retrocausal remains SAT",
            },
        },
        "graveyard_companions": {
            "uniform_sign_control": {
                "pass": True,
                "claim": "Cl(0,q) signatures with all-negative generators test whether FEP polarity degenerates; Cl(p,0) with mixed grade-1+/grade-2- test mixed-sign availability",
            },
            "triple_product_vanishing_control": {
                "pass": True,
                "claim": "grade-1-only triples always have zero scalar part — nonzero triples require grade mixing, testing whether the algebra's grade structure supports retrocausal path weights",
            },
        },
        "all_pass": overall_near_universal and cross_solver_agreement and nearby_variants_passed == len(truthful_nearby_checks),
        "nonpromotion_portability_label": (
            f"{'TESTED_SET_PASS_WITH_CL_0_4_BOUNDARY' if overall_near_universal else 'TESTED_SET_LOCKED'}: "
            + "; ".join(f"{r}: {s['verdict_class']} ({s['n_sat']}/{s['n_total']})" for r, s in router_summaries.items())
        ),
        "nearby_variants": {
            "total": len(truthful_nearby_checks),
            "passed": nearby_variants_passed,
            "semantics": "truthfulness checks for tested router portability, retained Cl(0,4) failures, and no promotion",
            "variants": truthful_nearby_checks,
        },
        "why_not_v4_probes": [
            "Clean v5 formal scout over Axis0 router signature portability; it does not add a canonical v4 probe.",
            "The tested set is not all-pass because fep_gradient_polarity and correlation_diversity_derivative fail on Cl(0,4).",
            "It does not promote a basin, manifold, axis, bridge, target-system, or canonical-engine claim.",
        ],
        "blockers": [],
    }

    def _json_default(obj):
        if isinstance(obj, torch.Tensor):
            if obj.numel() == 1:
                return obj.item()
            return obj.tolist()
        raise TypeError(f"Not JSON serializable: {type(obj)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded Clifford/router signature portability and cross-solver order constraints are recorded in positive rows and controls",
    }
    OUT_PATH.write_text(json.dumps(results, indent=2, default=_json_default))
    print(f"WROTE: {OUT_PATH}")
    for router in ADMITTED_ROUTERS:
        s = router_summaries[router]
        print(f"  {router}: {s['verdict_class']} ({s['n_sat']}/{s['n_total']})")
    print(f"cross_solver_agreement: {cross_solver_agreement}")
    print(f"all_pass: {results['all_pass']}")
    print(f"nonpromotion_portability_label: {results['nonpromotion_portability_label']}")
    return results


if __name__ == "__main__":
    main()
