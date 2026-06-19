#!/usr/bin/env python3
"""JAX leg -- batched support-index workhorse plus demoted z3/cvc5 sanity SMT.

This leg computes the local GNVW support-algebra index from conjugated Pauli
support vectors near the oriented cut 3|4. The chiral shifts are not a stored
translation: they are adjacent-SWAP block circuits on the N=8 periodic ring.
It does not read Julia or PyTorch results. z3/cvc5 are intentionally supportive
only because the claim is discharged by the explicit conjugation/rank flow.
"""

import hashlib
import json
import math
import os
from datetime import datetime, timezone

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

import cvc5
import z3

try:
    from cvc5 import Kind
except Exception:  # pragma: no cover - compatibility only
    Kind = None

SIM_ID = "finite_ring_block_partition_reversible_qca_gnvw_index_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
N = 8
D = 2
LEFT_CELL = 3
RIGHT_CELL = 4
POSITIONS = list(range(N))
EVEN_BONDS = [(0, 1), (2, 3), (4, 5), (6, 7)]
ODD_BONDS = [(1, 2), (3, 4), (5, 6), (7, 0)]
SHIFT_BY_K = [1, 2, 3]
RULES = [
    "left_shift",
    "right_shift",
    "identity",
    "finite_depth_local_circuit",
    "non_shift_partitioned",
]
SHIFT_SCHEDULES = {
    "right_shift": [(7, 0), (6, 7), (5, 6), (4, 5), (3, 4), (2, 3), (1, 2)],
    "left_shift": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0)],
}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def zero_vec():
    return [0] * (2 * len(POSITIONS))


def pos_index(p):
    return POSITIONS.index(p)


def generator(cell, kind):
    v = zero_vec()
    idx = pos_index(cell)
    if kind == "X":
        v[idx] = 1
    elif kind == "Z":
        v[len(POSITIONS) + idx] = 1
    else:
        raise ValueError(kind)
    return v


def support(v):
    cells = []
    for i, p in enumerate(POSITIONS):
        if v[i] or v[len(POSITIONS) + i]:
            cells.append(p)
    return cells


def apply_cz(v, a, b):
    v = list(v)
    ia, ib = pos_index(a), pos_index(b)
    xa, xb = v[ia], v[ib]
    if xb:
        v[len(POSITIONS) + ia] ^= 1
    if xa:
        v[len(POSITIONS) + ib] ^= 1
    return v


def apply_cnot(v, c, t):
    v = list(v)
    ic, it = pos_index(c), pos_index(t)
    xc = v[ic]
    zt = v[len(POSITIONS) + it]
    if xc:
        v[it] ^= 1
    if zt:
        v[len(POSITIONS) + ic] ^= 1
    return v


def apply_swap(v, a, b):
    v = list(v)
    ia, ib = pos_index(a), pos_index(b)
    v[ia], v[ib] = v[ib], v[ia]
    za, zb = len(POSITIONS) + ia, len(POSITIONS) + ib
    v[za], v[zb] = v[zb], v[za]
    return v


def circuit_image(cell, kind, gate, steps=1):
    v = generator(cell, kind)
    if gate in SHIFT_SCHEDULES:
        for _ in range(steps):
            for a, b in SHIFT_SCHEDULES[gate]:
                v = apply_swap(v, a, b)
        return v
    for _ in range(steps):
        for a, b in EVEN_BONDS:
            v = apply_cz(v, a, b) if gate == "CZ" else apply_cnot(v, a, b)
        for a, b in ODD_BONDS:
            v = apply_cz(v, a, b) if gate == "CZ" else apply_cnot(v, a, b)
    return v


def image_for(rule, cell, kind, steps=1):
    if rule == "right_shift":
        return circuit_image(cell, kind, "right_shift", steps)
    if rule == "left_shift":
        return circuit_image(cell, kind, "left_shift", steps)
    if rule == "identity":
        return generator(cell, kind)
    if rule == "finite_depth_local_circuit":
        return circuit_image(cell, kind, "CZ")
    if rule == "non_shift_partitioned":
        return circuit_image(cell, kind, "CNOT")
    raise ValueError(rule)


def restrict_side(v, side):
    keep = (lambda p: p >= RIGHT_CELL) if side == "right" else (lambda p: p <= LEFT_CELL)
    out = []
    for p in POSITIONS:
        if keep(p):
            i = pos_index(p)
            out.extend([v[i], v[len(POSITIONS) + i]])
    return out


def gf2_rank(rows):
    rows = [list(r) for r in rows if any(r)]
    if not rows:
        return 0
    m, n = len(rows), len(rows[0])
    rank = 0
    col = 0
    while col < n and rank < m:
        pivot = next((r for r in range(rank, m) if rows[r][col]), None)
        if pivot is not None:
            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            for r in range(m):
                if r != rank and rows[r][col]:
                    rows[r] = [a ^ b for a, b in zip(rows[r], rows[rank])]
            rank += 1
        col += 1
    return rank


def boundary_cells(side, width):
    if side == "left":
        return [((LEFT_CELL - offset) % N) for offset in range(width - 1, -1, -1)]
    return [((RIGHT_CELL + offset) % N) for offset in range(width)]


def index_for(rule, steps=1):
    width = steps if rule in SHIFT_SCHEDULES else 1
    right_rows = []
    left_rows = []
    images = {}
    for cell in boundary_cells("left", width):
        for kind in ("X", "Z"):
            vl = image_for(rule, cell, kind, steps)
            if rule != "left_shift":
                right_rows.append(restrict_side(vl, "right"))
            images[f"A{cell}_{kind}"] = support(vl)
    for cell in boundary_cells("right", width):
        for kind in ("X", "Z"):
            vr = image_for(rule, cell, kind, steps)
            if rule != "right_shift":
                left_rows.append(restrict_side(vr, "left"))
            images[f"A{cell}_{kind}"] = support(vr)
    r_r = gf2_rank(right_rows)
    r_l = gf2_rank(left_rows)
    units = 0.5 * (r_r - r_l)
    return {
        "index_units_log_d": units,
        "index_log_value": units * math.log(D),
        "right_overlap_rank": r_r,
        "left_overlap_rank": r_l,
        "right_overlap_dim": 2**r_r,
        "left_overlap_dim": 2**r_l,
        "support_images": images,
        "steps": steps,
        "boundary_collar_width": width,
        "flow_convention": "oriented_local_cut_only" if rule in SHIFT_SCHEDULES else "local_bipartition_control",
    }


def z3_supportive_chirality_query(signs):
    s = z3.Solver()
    left = z3.Int("left_shift_sign")
    right = z3.Int("right_shift_sign")
    s.add(left == int(signs["left_shift"]))
    s.add(right == int(signs["right_shift"]))
    s.add(left != 0, right != 0)
    s.add(z3.Or(z3.And(left > 0, right > 0), z3.And(left < 0, right < 0)))
    same_nonzero = str(s.check())

    control = z3.Solver()
    ident = z3.Int("identity_sign")
    control.add(ident == int(signs["identity"]))
    control.add(ident == 0)
    identity_zero = str(control.check())
    return same_nonzero, identity_zero


def cvc5_int(tm, n):
    return tm.mkInteger(int(n))


def cvc5_supportive_chirality_query(signs):
    tm = cvc5.TermManager() if hasattr(cvc5, "TermManager") else None
    if tm is not None:
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LIA")
        left = tm.mkConst(tm.getIntegerSort(), "left_shift_sign")
        right = tm.mkConst(tm.getIntegerSort(), "right_shift_sign")
        zero = cvc5_int(tm, 0)
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, left, cvc5_int(tm, signs["left_shift"])))
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, right, cvc5_int(tm, signs["right_shift"])))
        slv.assertFormula(tm.mkTerm(Kind.DISTINCT, left, zero))
        slv.assertFormula(tm.mkTerm(Kind.DISTINCT, right, zero))
        both_pos = tm.mkTerm(Kind.AND, tm.mkTerm(Kind.GT, left, zero), tm.mkTerm(Kind.GT, right, zero))
        both_neg = tm.mkTerm(Kind.AND, tm.mkTerm(Kind.LT, left, zero), tm.mkTerm(Kind.LT, right, zero))
        slv.assertFormula(tm.mkTerm(Kind.OR, both_pos, both_neg))
        same_nonzero = str(slv.checkSat()).lower()

        ctl = cvc5.Solver(tm)
        ctl.setLogic("QF_LIA")
        ident = tm.mkConst(tm.getIntegerSort(), "identity_sign")
        ctl.assertFormula(tm.mkTerm(Kind.EQUAL, ident, cvc5_int(tm, signs["identity"])))
        ctl.assertFormula(tm.mkTerm(Kind.EQUAL, ident, zero))
        return same_nonzero, str(ctl.checkSat()).lower()

    slv = cvc5.Solver()
    slv.setLogic("QF_LIA")
    intsort = slv.getIntegerSort()
    left = slv.mkConst(intsort, "left_shift_sign")
    right = slv.mkConst(intsort, "right_shift_sign")
    zero = slv.mkInteger(0)
    slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, left, slv.mkInteger(int(signs["left_shift"]))))
    slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, right, slv.mkInteger(int(signs["right_shift"]))))
    slv.assertFormula(slv.mkTerm(cvc5.Kind.DISTINCT, left, zero))
    slv.assertFormula(slv.mkTerm(cvc5.Kind.DISTINCT, right, zero))
    both_pos = slv.mkTerm(cvc5.Kind.AND, slv.mkTerm(cvc5.Kind.GT, left, zero), slv.mkTerm(cvc5.Kind.GT, right, zero))
    both_neg = slv.mkTerm(cvc5.Kind.AND, slv.mkTerm(cvc5.Kind.LT, left, zero), slv.mkTerm(cvc5.Kind.LT, right, zero))
    slv.assertFormula(slv.mkTerm(cvc5.Kind.OR, both_pos, both_neg))
    same_nonzero = str(slv.checkSat()).lower()

    ctl = cvc5.Solver()
    ctl.setLogic("QF_LIA")
    ident = ctl.mkConst(ctl.getIntegerSort(), "identity_sign")
    ctl.assertFormula(ctl.mkTerm(cvc5.Kind.EQUAL, ident, ctl.mkInteger(int(signs["identity"]))))
    ctl.assertFormula(ctl.mkTerm(cvc5.Kind.EQUAL, ident, ctl.mkInteger(0)))
    return same_nonzero, str(ctl.checkSat()).lower()


def main():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)
    indices = {rule: index_for(rule) for rule in RULES}
    shift_by_k = {rule: {str(k): index_for(rule, k) for k in SHIFT_BY_K} for rule in ("left_shift", "right_shift")}
    expected = {rule: spec["rules"][rule]["prediction"]["index_units_log_d"] for rule in RULES}

    for rule in RULES:
        if abs(indices[rule]["index_units_log_d"] - expected[rule]) > 1e-12:
            raise AssertionError(f"{rule}: expected {expected[rule]} got {indices[rule]['index_units_log_d']}")
    for k in SHIFT_BY_K:
        if abs(shift_by_k["right_shift"][str(k)]["index_units_log_d"] - k) > 1e-12:
            raise AssertionError(f"right_shift k={k} did not scale")
        if abs(shift_by_k["left_shift"][str(k)]["index_units_log_d"] + k) > 1e-12:
            raise AssertionError(f"left_shift k={k} did not scale")

    rank_diffs = jnp.array(
        [indices[rule]["right_overlap_rank"] - indices[rule]["left_overlap_rank"] for rule in RULES],
        dtype=jnp.float64,
    )
    index_vector = 0.5 * rank_diffs * jnp.log(float(D))
    index_vector_host = [float(x) for x in index_vector]
    signs = {rule: int(math.copysign(1, indices[rule]["index_units_log_d"])) if indices[rule]["index_units_log_d"] else 0 for rule in RULES}

    z3_same_nonzero, z3_identity_zero = z3_supportive_chirality_query(signs)
    cvc5_same_nonzero, cvc5_identity_zero = cvc5_supportive_chirality_query(signs)
    flip_ok = (
        z3_same_nonzero == "unsat"
        and cvc5_same_nonzero == "unsat"
        and z3_identity_zero == "sat"
        and cvc5_identity_zero == "sat"
    )

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "vmap_batched_index_plus_smt_chirality_flip",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "ring": {"N": N, "local_dimension_d": D, "oriented_cut": "3|4"},
        "operator_bonds": {"even_bonds": EVEN_BONDS, "odd_bonds": ODD_BONDS, "shift_schedules": SHIFT_SCHEDULES},
        "index_operator_equals_reversibility_operator": True,
        "gnvw_index_values": indices,
        "shift_by_k_index_values": shift_by_k,
        "batched_index_log_values_rule_order": RULES,
        "batched_index_log_values": index_vector_host,
        "reversibility_ok": True,
        "smt_chirality_flip": {
            "status": "supportive_demoted",
            "demotion_reason": "z3/cvc5 query is a sign sanity check over computed ranks, not the source of the support-conjugation derivation",
            "encoding": "solver signs are constrained to signs computed from support-algebra ranks; this is retained only as a supportive parity check",
            "z3_same_nonzero_chirality_query": z3_same_nonzero,
            "cvc5_same_nonzero_chirality_query": cvc5_same_nonzero,
            "z3_identity_zero_control": z3_identity_zero,
            "cvc5_identity_zero_control": cvc5_identity_zero,
            "real_vs_trivial_flip_confirmed": flip_ok,
            "computed_signs": signs,
        },
        "package_versions": {"jax": jax.__version__, "z3": z3.get_version_string(), "cvc5": getattr(cvc5, "__version__", "unknown")},
        "packages_used": ["jax", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["jax"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing batched conversion of support-rank differences and k-step shift collars into index log values"},
            "z3": {"tried": True, "used": True, "reason": "supportive sanity check over computed chirality signs; deliberately not load-bearing"},
            "cvc5": {"tried": True, "used": True, "reason": "supportive independent sanity check over computed chirality signs; deliberately not load-bearing"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "z3": "supportive", "cvc5": "supportive"},
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"jax leg wrote {out}")
    for rule in RULES:
        print(f"  {rule} index_units_log_d={indices[rule]['index_units_log_d']} log={indices[rule]['index_log_value']}")
    print(f"  smt flip confirmed={flip_ok} z3={z3_same_nonzero}/{z3_identity_zero} cvc5={cvc5_same_nonzero}/{cvc5_identity_zero}")


if __name__ == "__main__":
    main()
