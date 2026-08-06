#!/usr/bin/env python3
"""Probe lane 2 — PyTorch leg. R0, R1, R2, R3, C1-C3 on the root strata, n = 4.

usage: lane_torch.py {float32|float64}

Deliberately NOT a transcription of the JAX leg:
  popcount   : bit-shift-and-sum, not a population_count primitive
  R3          : one einsum contraction over all 81 cells, not a vmap
Engine-op evidence comes from TorchDispatchMode, so the recorded op names are the
aten ops the dispatcher actually saw, not a list this file keeps by hand.

This lane reads NO other lane's output. `jax` absence at exit is measured.
"""
import json
import os
import sys
import time

MODE = sys.argv[1] if len(sys.argv) > 1 else "float32"
if MODE not in ("float32", "float64"):
    print(json.dumps({"why": f"unknown float mode {MODE!r}"}))
    sys.exit(2)

import torch                                                      # noqa: E402
from torch.utils._python_dispatch import TorchDispatchMode         # noqa: E402

N = 4
SIZE = 2 ** N
FDT = torch.float64 if MODE == "float64" else torch.float32
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", f"lane_torch_{MODE}.json")

LOG2_CALLS = [0]
OPS = {}


class OpLedger(TorchDispatchMode):
    """Records every aten op the dispatcher routes while active."""
    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        name = str(func)
        OPS[name] = OPS.get(name, 0) + 1
        return func(*args, **(kwargs or {}))


def tlog2(x):
    LOG2_CALLS[0] += 1
    return float(torch.log2(torch.tensor(x, dtype=FDT)))


def bits_of(J):
    shifts = torch.arange(N, dtype=torch.int64)
    return torch.bitwise_and(torch.bitwise_right_shift(J.unsqueeze(1), shifts.unsqueeze(0)),
                             torch.tensor(1, dtype=torch.int64))


def popcount_matrix(J):
    """popcount(j XOR k) by shift-and-sum. No population_count primitive used."""
    x = torch.bitwise_xor(J.unsqueeze(1), J.unsqueeze(0))
    acc = torch.zeros_like(x)
    for i in range(2 * N):
        acc = acc + torch.bitwise_and(torch.bitwise_right_shift(x, i),
                                      torch.tensor(1, dtype=torch.int64))
    return acc


def popcount_vec(J):
    acc = torch.zeros_like(J)
    for i in range(2 * N):
        acc = acc + torch.bitwise_and(torch.bitwise_right_shift(J, i),
                                      torch.tensor(1, dtype=torch.int64))
    return acc


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
        d["kappa_ext_bits"] = tlog2(len(members))
    return d


def main():
    t0 = time.time()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    dtypes = {}

    with OpLedger():
        J = torch.arange(SIZE, dtype=torch.int64)
        # ---- R0
        r0 = {"index_set": "J_4 = {0,1}^4 as int64 0..15", "alphabet": "binary",
              "n_bits": N, "cardinality": int(J.shape[0]),
              "distinct_addresses_measured": int(torch.unique(J).shape[0]),
              "bits_matrix_row_sums": [int(v) for v in bits_of(J).sum(dim=1)]}
        r0["H0_addr_bits"] = tlog2(r0["cardinality"])

        # ---- R1
        pc = popcount_matrix(J)
        F_diag = torch.eq(J.unsqueeze(1), J.unsqueeze(0)).to(torch.int64)
        F_coh = torch.le(pc, torch.tensor(1, dtype=torch.int64)).to(torch.int64)
        r1 = {}
        for kind, F in (("DIAG", F_diag), ("COHERENT", F_coh)):
            Ff = F.to(FDT)
            supp = int(torch.sum(F))
            rank = int(torch.linalg.matrix_rank(Ff))
            det = float(torch.linalg.det(Ff))
            sign, logabs = torch.linalg.slogdet(Ff)
            eig = torch.linalg.eigvalsh(Ff)
            dtypes[kind] = {"F": str(F.dtype), "F_float": str(Ff.dtype),
                            "eigvals": str(eig.dtype)}
            r1[kind] = {"index_set_ref": "R0.J_4",
                        "omega_cardinality": int(F.numel()),
                        "support_cardinality": supp,
                        "H0_pair_bits": tlog2(supp),
                        "integer_matrix_rank": rank,
                        "determinant_from_torch_linalg_det": det,
                        "determinant_from_slogdet": float(sign) * float(torch.exp(logabs)),
                        "slogdet_sign": float(sign),
                        "slogdet_logabsdet": float(logabs),
                        "trace": float(torch.trace(Ff)),
                        "eigenvalues_sorted": [float(v) for v in eig]}
        r1["discrimination"] = {
            k: {"DIAG": r1["DIAG"][k], "COHERENT": r1["COHERENT"][k],
                "separates": r1["DIAG"][k] != r1["COHERENT"][k]}
            for k in ("support_cardinality", "H0_pair_bits", "integer_matrix_rank",
                      "determinant_from_torch_linalg_det", "trace")}
        r1["discrimination"]["H0_addr_bits"] = {"DIAG": r0["H0_addr_bits"],
                                                "COHERENT": r0["H0_addr_bits"],
                                                "separates": False}
        r1["discrimination"]["log2_integer_matrix_rank"] = {
            "DIAG": tlog2(r1["DIAG"]["integer_matrix_rank"]),
            "COHERENT": tlog2(r1["COHERENT"]["integer_matrix_rank"]),
            "separates": r1["DIAG"]["integer_matrix_rank"] != r1["COHERENT"]["integer_matrix_rank"]}

        # ---- R2 boundary composition through torch.matmul
        by_dim, mats = boundary_matrices()
        tm = {d: torch.tensor(m, dtype=torch.int64) for d, m in mats.items()}
        comp = {}
        for d in range(2, N + 1):
            P = torch.matmul(tm[d - 1], tm[d])
            comp[f"d{d-1}_o_d{d}"] = {"shape": list(P.shape),
                                      "max_abs_entry": int(torch.max(torch.abs(P))),
                                      "dtype": str(P.dtype)}
        r2 = {"cell_counts_by_dim": {str(d): len(v) for d, v in by_dim.items()},
              "total_cells": sum(len(v) for v in by_dim.values()),
              "boundary_matrix_shapes": {f"d{d}": list(tm[d].shape) for d in tm},
              "boundary_composition": comp}

        # ---- R3 : one einsum contraction over all 81 cells
        K = [c for d in sorted(by_dim) for c in by_dim[d]]
        mask = torch.tensor([[0 if s == "*" else 1 for s in c] for c in K],
                            dtype=torch.int64)
        val = torch.tensor([[0 if s == "*" else int(s) for s in c] for c in K],
                           dtype=torch.int64)
        mb = bits_of(J)                                     # (16, 4)
        agree = torch.logical_or(mask.unsqueeze(1) == 0, mb.unsqueeze(0) == val.unsqueeze(1))
        inside = torch.all(agree, dim=2).to(torch.int64)     # (81, 16)
        pc_ok = torch.le(pc, torch.tensor(1, dtype=torch.int64)).to(torch.int64)
        rest = torch.einsum("cj,jk,ck->c", inside, pc_ok, inside)
        ones = torch.ones((SIZE, SIZE), dtype=torch.int64)
        full = torch.einsum("cj,jk,ck->c", torch.ones_like(inside), ones,
                            torch.ones_like(inside))
        insize = inside.sum(dim=1)
        per_full, per_rest, per_in = {}, {}, {}
        for c, fv, rv, iv in zip(K, [int(x) for x in full], [int(x) for x in rest],
                                 [int(x) for x in insize]):
            per_full.setdefault(str(dim(c)), set()).add(fv)
            per_rest.setdefault(str(dim(c)), set()).add(rv)
            per_in.setdefault(str(dim(c)), set()).add(iv)
        def fold(m):
            out = {}
            for k in sorted(m):
                if len(m[k]) != 1:
                    raise SystemExit(f"non-uniform |R_c| within dim {k}: {sorted(m[k])}")
                card = next(iter(m[k]))
                out[k] = {"relation_cardinality": card, "kappa_bits": tlog2(card)}
            return out
        r3 = {"projection_ref": "pi : E -> K, cell label over {0,1,*}^4",
              "subcube_sizes_by_dim": {k: sorted(v) for k, v in per_in.items()},
              "FULL_FIELD": {"per_dim": fold(per_full),
                             "E_cardinality": int(full.sum())},
              "RESTRICTED": {"per_dim": fold(per_rest),
                             "E_cardinality": int(rest.sum())}}

        # ---- C1-C3
        q = popcount_vec(J)
        us = torch.arange(N + 2, dtype=torch.int64)
        counts = [int(x) for x in torch.eq(q.unsqueeze(0), us.unsqueeze(1)).to(
            torch.int64).sum(dim=1)]
        qh = [int(x) for x in q]
        members = {u: [j for j in range(SIZE) if qh[j] == u] for u in range(N + 2)}

    before = LOG2_CALLS[0]
    rel = {str(u): release(u, members[u]) for u in range(N + 1)}
    empty = release(5, members[5])
    after = LOG2_CALLS[0]
    c123 = {"quotient": "q(j) = shift-and-sum popcount(j), Q = {0,1,2,3,4}",
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

    rec = {"lane": f"torch_{MODE}", "engine": "pytorch",
           "torch_version": torch.__version__,
           "device": str(torch.empty(0).device),
           "default_dtype": str(torch.get_default_dtype()),
           "requested_float_mode": MODE,
           "measured_float_dtypes": dtypes,
           "measured_log2_output_dtype": str(torch.log2(
               torch.tensor(80, dtype=FDT)).dtype),
           "interpreter": sys.executable,
           "engine_ops_from_torch_dispatch": dict(sorted(OPS.items())),
           "engine_op_count_distinct": len(OPS),
           "engine_op_invocations_total": sum(OPS.values()),
           "other_engine_modules_at_exit": {m: (m in sys.modules)
                                            for m in ("jax", "jaxlib")},
           "n": N, "R0": r0, "R1": r1, "R2": r2, "R3": r3, "C1_C3": c123,
           "log2_calls_total": LOG2_CALLS[0],
           "wallclock_s": round(time.time() - t0, 3)}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1)
    leaked = [m for m, p in rec["other_engine_modules_at_exit"].items() if p]
    print(json.dumps({"wrote": OUT, "mode": MODE,
                      "log2_dtype": rec["measured_log2_output_dtype"],
                      "distinct_aten_ops": len(OPS),
                      "aten_invocations": sum(OPS.values()),
                      "other_engines_loaded": leaked,
                      "wallclock_s": rec["wallclock_s"]}, indent=1))
    return 1 if leaked else 0


if __name__ == "__main__":
    sys.exit(main())
