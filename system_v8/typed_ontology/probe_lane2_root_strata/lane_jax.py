#!/usr/bin/env python3
"""Probe lane 2 — JAX leg. R0, R1, R2, R3, C1-C3 on the root strata, n = 4.

usage: lane_jax.py {float32|float64}

The float mode is a CONTROL, not a preference: it is the same code path with
jax_enable_x64 flipped, so the two runs discriminate engine-default precision from
arithmetic. Actual array dtypes are MEASURED and recorded, because a float64 request
under x64-disabled JAX is silently downgraded.

Engine-op evidence is taken from the JAXPR (primitive names jax itself emitted) and
from the lowered StableHLO module, not from a hand-kept list.

This lane reads NO other lane's output. `torch` absence at exit is measured.
"""
import json
import os
import sys
import time

MODE = sys.argv[1] if len(sys.argv) > 1 else "float32"
if MODE not in ("float32", "float64"):
    print(json.dumps({"why": f"unknown float mode {MODE!r}"}))
    sys.exit(2)

import jax                                                       # noqa: E402
if MODE == "float64":
    jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp                                           # noqa: E402
from jax import lax                                               # noqa: E402

N = 4
SIZE = 2 ** N
FDT = jnp.float64 if MODE == "float64" else jnp.float32
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", f"lane_jax_{MODE}.json")

LOG2_CALLS = [0]


def jlog2(x):
    """Every log2 in this lane goes through here, so the counter is a measurement."""
    LOG2_CALLS[0] += 1
    return float(jnp.log2(jnp.asarray(x, dtype=FDT)))


# ----------------------------------------------------------------- core jax fns
def bits_of(J):
    shifts = jnp.arange(N, dtype=jnp.uint32)
    return jnp.bitwise_and(lax.shift_right_logical(J[:, None], shifts[None, :]),
                           jnp.uint32(1))


def pair_popcount(J):
    return lax.population_count(jnp.bitwise_xor(J[:, None], J[None, :]))


def field_diag(J):
    return jnp.equal(J[:, None], J[None, :]).astype(jnp.int32)


def field_coherent(J):
    return jnp.less_equal(pair_popcount(J), jnp.uint32(1)).astype(jnp.int32)


def support_count(F):
    return jnp.sum(F)


def cell_relation_counts(mask, val, member_bits, pc_ok):
    """|R_c| for one cell, both the full-field and the subcube-restricted relation."""
    agree = jnp.logical_or(mask[None, :] == 0, member_bits == val[None, :])
    inside = jnp.all(agree, axis=1)
    full = jnp.sum(jnp.ones((SIZE, SIZE), dtype=jnp.int32))
    rest = jnp.sum((inside[:, None] & inside[None, :] & pc_ok).astype(jnp.int32))
    return full, rest, jnp.sum(inside.astype(jnp.int32))


def fibre_counts(q, us):
    return jnp.sum(jnp.equal(q[None, :], us[:, None]).astype(jnp.int32), axis=1)


# ----------------------------------------------------------------- R2 structure
def cells():
    out = []
    def rec(pref):
        if len(pref) == N:
            out.append(tuple(pref))
            return
        for s in (0, 1, "*"):
            rec(pref + [s])
    rec([])
    return out


def dim(c):
    return sum(1 for s in c if s == "*")


def boundary_matrices():
    K = cells()
    by_dim = {d: [c for c in K if dim(c) == d] for d in range(N + 1)}
    index = {d: {c: i for i, c in enumerate(by_dim[d])} for d in by_dim}
    mats = {}
    for d in range(1, N + 1):
        M = [[0] * len(by_dim[d]) for _ in range(len(by_dim[d - 1]))]
        for jc, c in enumerate(by_dim[d]):
            free = [i for i, s in enumerate(c) if s == "*"]
            for m, i in enumerate(free, start=1):
                sgn = -1 if m % 2 else 1
                for v, vs in ((1, 1), (0, -1)):
                    face = list(c)
                    face[i] = v
                    M[index[d - 1][tuple(face)]][jc] += sgn * vs
        mats[d] = M
    return by_dim, mats


def release(u, members):
    d = {"quotient_class_id": int(u), "probe_family": ["p_popcount"],
         "constraint_set_ref": "C0 = identity constraint (E_C = E)",
         "fibre_cardinality": len(members), "fibre_members": [int(x) for x in members]}
    if len(members) >= 1:
        d["kappa_ext_bits"] = jlog2(len(members))
    return d


def main():
    t0 = time.time()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    J = jnp.arange(SIZE, dtype=jnp.uint32)

    # ---- engine-op evidence: what primitives did JAX itself emit?
    jaxprs = {}
    for name, fn, args in (
        ("field_coherent", field_coherent, (J,)),
        ("field_diag", field_diag, (J,)),
        ("support_count", support_count, (field_coherent(J),)),
        ("fibre_counts", fibre_counts, (lax.population_count(J),
                                        jnp.arange(N + 2, dtype=jnp.uint32))),
        ("matrix_rank", jnp.linalg.matrix_rank, (field_coherent(J).astype(FDT),)),
        ("det", jnp.linalg.det, (field_coherent(J).astype(FDT),)),
        ("slogdet", jnp.linalg.slogdet, (field_coherent(J).astype(FDT),)),
        ("eigvalsh", jnp.linalg.eigvalsh, (field_coherent(J).astype(FDT),)),
        ("matmul_int", jnp.matmul, (jnp.zeros((3, 4), jnp.int32),
                                    jnp.zeros((4, 5), jnp.int32))),
        ("log2", jnp.log2, (jnp.asarray(80, dtype=FDT),)),
    ):
        jx = jax.make_jaxpr(fn)(*args)
        prims = {}
        for eqn in jx.jaxpr.eqns:
            prims[eqn.primitive.name] = prims.get(eqn.primitive.name, 0) + 1
        jaxprs[name] = prims
    lowered = jax.jit(field_coherent).lower(J).as_text()
    hlo_ops = sorted({tok.split("(")[0].strip()
                      for line in lowered.splitlines()
                      for tok in [line.strip()]
                      if tok.startswith("%") and "= " in tok
                      for tok in [tok.split("= ", 1)[1]]})

    # ---- R0
    r0 = {"index_set": "J_4 = {0,1}^4 as uint32 0..15", "alphabet": "binary",
          "n_bits": N, "cardinality": int(J.shape[0]),
          "distinct_addresses_measured": int(jnp.unique(J).shape[0]),
          "H0_addr_bits": jlog2(int(J.shape[0])),
          "bits_matrix_row_sums": [int(v) for v in jnp.sum(bits_of(J), axis=1)]}

    # ---- R1
    jf = jax.jit(field_diag), jax.jit(field_coherent)
    r1 = {}
    dtypes = {}
    for kind, f in (("DIAG", jf[0]), ("COHERENT", jf[1])):
        F = f(J)
        Ff = F.astype(FDT)
        supp = int(jax.jit(support_count)(F))
        rank = int(jnp.linalg.matrix_rank(Ff))
        det = float(jnp.linalg.det(Ff))
        sign, logabs = jnp.linalg.slogdet(Ff)
        eig = jnp.linalg.eigvalsh(Ff)
        dtypes[kind] = {"F": str(F.dtype), "F_float": str(Ff.dtype),
                        "eigvals": str(eig.dtype)}
        r1[kind] = {
            "index_set_ref": "R0.J_4", "omega_cardinality": int(F.size),
            "support_cardinality": supp, "H0_pair_bits": jlog2(supp),
            "integer_matrix_rank": rank,
            "determinant_from_jnp_linalg_det": det,
            "determinant_from_slogdet": float(sign) * float(jnp.exp(logabs)),
            "slogdet_sign": float(sign), "slogdet_logabsdet": float(logabs),
            "trace": float(jnp.trace(Ff)),
            "eigenvalues_sorted": [float(v) for v in eig],
        }
    r1["discrimination"] = {
        k: {"DIAG": r1["DIAG"][k], "COHERENT": r1["COHERENT"][k],
            "separates": r1["DIAG"][k] != r1["COHERENT"][k]}
        for k in ("support_cardinality", "H0_pair_bits", "integer_matrix_rank",
                  "determinant_from_jnp_linalg_det", "trace")
    }
    r1["discrimination"]["H0_addr_bits"] = {
        "DIAG": r0["H0_addr_bits"], "COHERENT": r0["H0_addr_bits"], "separates": False}
    r1["discrimination"]["log2_integer_matrix_rank"] = {
        "DIAG": jlog2(r1["DIAG"]["integer_matrix_rank"]),
        "COHERENT": jlog2(r1["COHERENT"]["integer_matrix_rank"]),
        "separates": r1["DIAG"]["integer_matrix_rank"] != r1["COHERENT"]["integer_matrix_rank"]}

    # ---- R2 : boundary composition through jnp.matmul
    by_dim, mats = boundary_matrices()
    jm = {d: jnp.asarray(m, dtype=jnp.int32) for d, m in mats.items()}
    comp = {}
    for d in range(2, N + 1):
        P = jnp.matmul(jm[d - 1], jm[d])
        comp[f"d{d-1}_o_d{d}"] = {"shape": [int(x) for x in P.shape],
                                  "max_abs_entry": int(jnp.max(jnp.abs(P))),
                                  "dtype": str(P.dtype)}
    r2 = {"cell_counts_by_dim": {str(d): len(v) for d, v in by_dim.items()},
          "total_cells": sum(len(v) for v in by_dim.values()),
          "boundary_matrix_shapes": {f"d{d}": [int(jm[d].shape[0]), int(jm[d].shape[1])]
                                     for d in jm},
          "boundary_composition": comp}

    # ---- R3 : vmap over all 81 cells at once
    K = [c for d in sorted(by_dim) for c in by_dim[d]]
    mask = jnp.asarray([[0 if s == "*" else 1 for s in c] for c in K], dtype=jnp.uint32)
    val = jnp.asarray([[0 if s == "*" else int(s) for s in c] for c in K], dtype=jnp.uint32)
    mb = bits_of(J)
    pc_ok = jnp.less_equal(pair_popcount(J), jnp.uint32(1))
    vf = jax.jit(jax.vmap(lambda m, v: cell_relation_counts(m, v, mb, pc_ok)))
    full, rest, insize = vf(mask, val)
    full = [int(x) for x in full]
    rest = [int(x) for x in rest]
    insize = [int(x) for x in insize]
    per_full, per_rest, per_in = {}, {}, {}
    for c, fv, rv, iv in zip(K, full, rest, insize):
        per_full.setdefault(str(dim(c)), set()).add(fv)
        per_rest.setdefault(str(dim(c)), set()).add(rv)
        per_in.setdefault(str(dim(c)), set()).add(iv)
    def fold(m):
        out = {}
        for k in sorted(m):
            if len(m[k]) != 1:
                raise SystemExit(f"non-uniform |R_c| within dim {k}: {sorted(m[k])}")
            card = next(iter(m[k]))
            out[k] = {"relation_cardinality": card, "kappa_bits": jlog2(card)}
        return out
    r3 = {"projection_ref": "pi : E -> K, cell label over {0,1,*}^4",
          "subcube_sizes_by_dim": {k: sorted(v) for k, v in per_in.items()},
          "FULL_FIELD": {"per_dim": fold(per_full), "E_cardinality": sum(full)},
          "RESTRICTED": {"per_dim": fold(per_rest), "E_cardinality": sum(rest)}}

    # ---- C1-C3
    q = lax.population_count(J)
    us = jnp.arange(N + 2, dtype=jnp.uint32)         # includes u = 5, which is empty
    counts = [int(x) for x in jax.jit(fibre_counts)(q, us)]
    members = {u: [int(j) for j in range(SIZE) if int(q[j]) == u] for u in range(N + 2)}
    before = LOG2_CALLS[0]
    rel = {str(u): release(u, members[u]) for u in range(N + 1)}
    empty = release(5, members[5])
    after = LOG2_CALLS[0]
    c123 = {"quotient": "q(j) = lax.population_count(j), Q = {0,1,2,3,4}",
            "probe_family": ["p_popcount"],
            "fibre_cardinalities": {str(u): counts[u] for u in range(N + 1)},
            "fibre_cardinality_sum": sum(counts[:N + 1]),
            "kappa_ext_bits": {str(u): rel[str(u)]["kappa_ext_bits"] for u in range(N + 1)},
            "releases": rel,
            "empty_fibre_case": {"quotient_value_probed": 5,
                                 "engine_measured_count": counts[5],
                                 "descriptor": empty,
                                 "descriptor_keys": sorted(empty.keys()),
                                 "kappa_key_present": "kappa_ext_bits" in empty},
            "log2_calls_across_5_nonempty_and_1_empty_release": after - before}

    rec = {"lane": f"jax_{MODE}", "engine": "jax",
           "jax_version": jax.__version__,
           "jax_devices": [str(d) for d in jax.devices()],
           "x64_enabled": bool(jax.config.read("jax_enable_x64")),
           "requested_float_mode": MODE,
           "measured_float_dtypes": dtypes,
           "measured_log2_output_dtype": str(jnp.log2(jnp.asarray(80, dtype=FDT)).dtype),
           "interpreter": sys.executable,
           "engine_ops_from_jaxpr": jaxprs,
           "engine_ops_from_lowered_stablehlo": hlo_ops,
           "other_engine_modules_at_exit": {m: (m in sys.modules)
                                            for m in ("torch", "julia")},
           "n": N, "R0": r0, "R1": r1, "R2": r2, "R3": r3, "C1_C3": c123,
           "log2_calls_total": LOG2_CALLS[0],
           "wallclock_s": round(time.time() - t0, 3)}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1)
    leaked = [m for m, p in rec["other_engine_modules_at_exit"].items() if p]
    print(json.dumps({"wrote": OUT, "mode": MODE,
                      "x64_enabled": rec["x64_enabled"],
                      "log2_dtype": rec["measured_log2_output_dtype"],
                      "primitives_seen": sorted({p for v in jaxprs.values() for p in v}),
                      "other_engines_loaded": leaked,
                      "wallclock_s": rec["wallclock_s"]}, indent=1))
    return 1 if leaked else 0


if __name__ == "__main__":
    sys.exit(main())
