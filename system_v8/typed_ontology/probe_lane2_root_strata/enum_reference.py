#!/usr/bin/env python3
"""Probe lane 2 referee: exhaustive enumeration in plain python, no array engine.

Exact integer arithmetic throughout (Fraction for rank, Bareiss for determinant).
Writes results/enum_reference.json. Exit 0 only if every internal exactness
assertion held; exit 1 otherwise.

This lane reads NO other lane's output.
"""
import json
import math
import os
import sys
import time
from fractions import Fraction

N = 4
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "enum_reference.json")

LOG2_CALLS = [0]


def log2_counted(x):
    LOG2_CALLS[0] += 1
    return math.log2(x)


# ------------------------------------------------------------------ exact linalg
def exact_rank(M):
    """Fraction-free-in-spirit Gaussian elimination over Q. Exact."""
    A = [[Fraction(v) for v in row] for row in M]
    rows, cols = len(A), len(A[0])
    r = 0
    for c in range(cols):
        piv = None
        for i in range(r, rows):
            if A[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        A[r], A[piv] = A[piv], A[r]
        pv = A[r][c]
        for i in range(r + 1, rows):
            if A[i][c] != 0:
                f = A[i][c] / pv
                for j in range(c, cols):
                    A[i][j] -= f * A[r][j]
        r += 1
        if r == rows:
            break
    return r


def bareiss_det(M):
    """Integer-preserving determinant. Exact for integer input."""
    A = [list(row) for row in M]
    n = len(A)
    sign = 1
    prev = 1
    for k in range(n - 1):
        if A[k][k] == 0:
            sw = None
            for i in range(k + 1, n):
                if A[i][k] != 0:
                    sw = i
                    break
            if sw is None:
                return 0
            A[k], A[sw] = A[sw], A[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                num = A[i][j] * A[k][k] - A[i][k] * A[k][j]
                assert num % prev == 0, "Bareiss divisibility broke: input not integral"
                A[i][j] = num // prev
        prev = A[k][k]
    return sign * A[n - 1][n - 1]


# ------------------------------------------------------------------ R0
def r0():
    J = []
    for j in range(2 ** N):
        bits = tuple((j >> i) & 1 for i in range(N))
        assert all(b in (0, 1) for b in bits)
        J.append(j)
    assert len(set(J)) == len(J)
    return {
        "index_set": "J_4 = {0,1}^4 as integers 0..15",
        "alphabet": "binary",
        "n_bits": N,
        "cardinality": len(J),
        "H0_addr_bits": log2_counted(len(J)),
        "distinct_bitstrings_enumerated": len({tuple((j >> i) & 1 for i in range(N)) for j in J}),
    }


# ------------------------------------------------------------------ R1
def popcount(x):
    c = 0
    while x:
        c += x & 1
        x >>= 1
    return c


def pair_field(kind):
    size = 2 ** N
    F = [[0] * size for _ in range(size)]
    for j in range(size):
        for k in range(size):
            if kind == "DIAG":
                F[j][k] = 1 if j == k else 0
            elif kind == "COHERENT":
                F[j][k] = 1 if popcount(j ^ k) <= 1 else 0
            else:
                raise ValueError(kind)
    return F


def spectrum_multiplicities(F, lambdas):
    """Exact: multiplicity of lambda = nullity of (F - lambda I) over Q."""
    size = len(F)
    out = {}
    for lam in lambdas:
        M = [[F[i][j] - (lam if i == j else 0) for j in range(size)] for i in range(size)]
        out[str(lam)] = size - exact_rank(M)
    return out


def r1(addr_card):
    fields = {}
    for kind in ("DIAG", "COHERENT"):
        F = pair_field(kind)
        supp = sum(sum(row) for row in F)
        trace = sum(F[i][i] for i in range(len(F)))
        cand = [5, 3, 1, -1, -3] if kind == "COHERENT" else [1, 0]
        fields[kind] = {
            "index_set_ref": "R0.J_4",
            "omega_cardinality": (2 ** N) ** 2,
            "support_cardinality": supp,
            "H0_pair_bits": log2_counted(supp),
            "integer_matrix_rank": exact_rank(F),
            "integer_determinant": bareiss_det(F),
            "trace": trace,
            "eigenvalue_multiplicities_by_exact_nullity": spectrum_multiplicities(F, cand),
        }
    d, c = fields["DIAG"], fields["COHERENT"]
    sep = {}
    for name, a, b in (
        ("H0_addr_bits", addr_card, addr_card),
        ("support_cardinality", d["support_cardinality"], c["support_cardinality"]),
        ("H0_pair_bits", d["H0_pair_bits"], c["H0_pair_bits"]),
        ("integer_matrix_rank", d["integer_matrix_rank"], c["integer_matrix_rank"]),
        ("log2_integer_matrix_rank", log2_counted(d["integer_matrix_rank"]),
         log2_counted(c["integer_matrix_rank"])),
        ("integer_determinant", d["integer_determinant"], c["integer_determinant"]),
        ("trace", d["trace"], c["trace"]),
        ("eigenvalue_multiplicities", str(d["eigenvalue_multiplicities_by_exact_nullity"]),
         str(c["eigenvalue_multiplicities_by_exact_nullity"])),
    ):
        sep[name] = {"DIAG": a, "COHERENT": b, "separates": a != b}
    return {"fields": fields, "discrimination": sep}


# ------------------------------------------------------------------ R2
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


def boundary_matrix(d, by_dim, index):
    """d_k : C_k -> C_{k-1} as a list-of-lists integer matrix."""
    src = by_dim[d]
    dst = by_dim[d - 1]
    M = [[0] * len(src) for _ in range(len(dst))]
    for jc, c in enumerate(src):
        free = [i for i, s in enumerate(c) if s == "*"]
        for m, i in enumerate(free, start=1):
            sgn = -1 if m % 2 else 1
            for val, vs in ((1, 1), (0, -1)):
                face = list(c)
                face[i] = val
                M[index[d - 1][tuple(face)]][jc] += sgn * vs
    return M


def matmul_int(A, B):
    n, k, m = len(A), len(B), len(B[0])
    assert len(A[0]) == k
    C = [[0] * m for _ in range(n)]
    for i in range(n):
        Ai = A[i]
        Ci = C[i]
        for t in range(k):
            a = Ai[t]
            if a:
                Bt = B[t]
                for j in range(m):
                    Ci[j] += a * Bt[j]
    return C


def r2():
    K = cells()
    by_dim = {d: [c for c in K if dim(c) == d] for d in range(N + 1)}
    index = {d: {c: i for i, c in enumerate(by_dim[d])} for d in by_dim}
    counts = {str(d): len(by_dim[d]) for d in by_dim}
    bnd = {d: boundary_matrix(d, by_dim, index) for d in range(1, N + 1)}
    comps = {}
    for d in range(2, N + 1):
        P = matmul_int(bnd[d - 1], bnd[d])
        comps[f"d{d-1}_o_d{d}"] = {
            "shape": [len(P), len(P[0])],
            "max_abs_entry": max(abs(v) for row in P for v in row),
        }
    return {
        "cell_counts_by_dim": counts,
        "total_cells": sum(len(v) for v in by_dim.values()),
        "boundary_matrix_shapes": {f"d{d}": [len(bnd[d]), len(bnd[d][0])] for d in bnd},
        "boundary_composition": comps,
    }, by_dim


# ------------------------------------------------------------------ R3
def subcube_members(c):
    out = []
    for j in range(2 ** N):
        ok = True
        for i, s in enumerate(c):
            if s != "*" and ((j >> i) & 1) != s:
                ok = False
                break
        if ok:
            out.append(j)
    return out


def r3(by_dim, h0_pair_coherent):
    K = [c for d in sorted(by_dim) for c in by_dim[d]]
    full, restricted = {}, {}
    e_full = e_rest = 0
    for c in K:
        d = dim(c)
        mem = subcube_members(c)
        assert len(mem) == 2 ** d
        n_full = (2 ** N) ** 2
        n_rest = sum(1 for j in mem for k in mem if popcount(j ^ k) <= 1)
        e_full += n_full
        e_rest += n_rest
        full.setdefault(str(d), set()).add(n_full)
        restricted.setdefault(str(d), set()).add(n_rest)
    def fold(m):
        out = {}
        for k, v in sorted(m.items()):
            assert len(v) == 1, f"non-uniform |R_c| within dim {k}: {sorted(v)}"
            card = next(iter(v))
            out[k] = {"relation_cardinality": card, "kappa_bits": log2_counted(card)}
        return out
    return {
        "projection_ref": "pi : E -> K, cell label over {0,1,*}^4",
        "FULL_FIELD": {"per_dim": fold(full), "E_cardinality": e_full,
                       "kappa_equals_2n": all(next(iter(v)) == (2 ** N) ** 2
                                              for v in full.values())},
        "RESTRICTED": {"per_dim": fold(restricted), "E_cardinality": e_rest},
        "top_cell_restricted_kappa_vs_H0_pair_coherent": {
            "kappa_top": log2_counted(next(iter(restricted[str(N)]))),
            "H0_pair_coherent": h0_pair_coherent,
        },
    }


# ------------------------------------------------------------------ C1-C3
def release(u, fibre):
    """TYPED RELEASE. Descriptor only. No kappa key when the fibre is empty."""
    desc = {
        "quotient_class_id": u,
        "probe_family": ["p_popcount"],
        "constraint_set_ref": "C0 = identity constraint (E_C = E) for this probe lane",
        "fibre_cardinality": len(fibre),
        "fibre_members": sorted(fibre),
    }
    if len(fibre) >= 1:
        desc["kappa_ext_bits"] = log2_counted(len(fibre))
    return desc


def c123():
    fib = {}
    for j in range(2 ** N):
        fib.setdefault(popcount(j), []).append(j)
    before = LOG2_CALLS[0]
    rel = {str(u): release(u, fib.get(u, [])) for u in range(N + 1)}
    empty = release(5, fib.get(5, []))
    after = LOG2_CALLS[0]
    return {
        "quotient": "q(j) = popcount(j), Q = {0,1,2,3,4}",
        "fibre_cardinalities": {str(u): len(fib.get(u, [])) for u in range(N + 1)},
        "fibre_cardinality_sum": sum(len(v) for v in fib.values()),
        "kappa_ext_bits": {str(u): rel[str(u)]["kappa_ext_bits"] for u in range(N + 1)},
        "releases": rel,
        "empty_fibre_case": {
            "quotient_value_probed": 5,
            "descriptor": empty,
            "descriptor_keys": sorted(empty.keys()),
            "kappa_key_present": "kappa_ext_bits" in empty,
        },
        "log2_calls_across_5_nonempty_and_1_empty_release": after - before,
    }


def main():
    t0 = time.time()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    a = r0()
    b = r1(a["H0_addr_bits"])
    c, by_dim = r2()
    d = r3(by_dim, b["fields"]["COHERENT"]["H0_pair_bits"])
    e = c123()
    rec = {
        "lane": "enum_reference_plain_python",
        "engine": "none (pure python integers + math.log2)",
        "interpreter": sys.executable,
        "python_version": sys.version.split()[0],
        "n": N,
        "engine_modules_in_sys_modules_at_exit": {
            m: (m in sys.modules) for m in ("numpy", "jax", "jaxlib", "torch")
        },
        "R0": a, "R1": b, "R2": c, "R3": d, "C1_C3": e,
        "log2_calls_total": LOG2_CALLS[0],
        "wallclock_s": round(time.time() - t0, 3),
    }
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=False)
    contaminated = [m for m, p in rec["engine_modules_in_sys_modules_at_exit"].items() if p]
    print(json.dumps({"wrote": OUT, "wallclock_s": rec["wallclock_s"],
                      "engine_modules_present": contaminated}, indent=1))
    return 1 if contaminated else 0


if __name__ == "__main__":
    sys.exit(main())
