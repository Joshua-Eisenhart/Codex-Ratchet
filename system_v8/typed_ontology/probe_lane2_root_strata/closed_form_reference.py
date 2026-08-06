#!/usr/bin/env python3
"""Probe lane 2 second referee: CLOSED-FORM combinatorics only.

Builds no matrix, enumerates no pair. Everything comes from n, math.comb and the
hypercube spectrum theorem (eig A(Q_n) = n - 2k with multiplicity C(n,k)).
Its job is to catch the worst outcome named in the task card: every engine and the
enumerator agreeing on a WRONG number because they share a construction.

Exit 0 always if it computes; it asserts nothing about other lanes.
"""
import json
import math
import os
import sys

N = 4
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "closed_form_reference.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    card = 2 ** N
    diag_supp = 2 ** N
    coh_supp = (2 ** N) * (1 + N)

    # I + A(Q_N): eig = 1 + (N - 2k), multiplicity C(N,k)
    coh_eigs = {}
    det = 1
    trace = 0
    for k in range(N + 1):
        lam = 1 + (N - 2 * k)
        mult = math.comb(N, k)
        coh_eigs[str(lam)] = mult
        det *= lam ** mult
        trace += lam * mult
    coh_rank = card - coh_eigs.get("0", 0)

    cell_counts = {str(d): math.comb(N, d) * 2 ** (N - d) for d in range(N + 1)}
    rest_card = {str(d): 2 ** d * (1 + d) for d in range(N + 1)}
    e_rest = sum(math.comb(N, d) * 2 ** (N - d) * 2 ** d * (1 + d) for d in range(N + 1))

    rec = {
        "lane": "closed_form_reference",
        "engine": "none (math.comb + hypercube spectrum theorem)",
        "interpreter": sys.executable,
        "n": N,
        "R0": {"cardinality": card, "H0_addr_bits": float(N)},
        "R1": {
            "DIAG": {"support_cardinality": diag_supp,
                     "H0_pair_bits": math.log2(diag_supp),
                     "integer_matrix_rank": card, "integer_determinant": 1, "trace": card,
                     "eigenvalue_multiplicities": {"1": card}},
            "COHERENT": {"support_cardinality": coh_supp,
                         "H0_pair_bits": math.log2(coh_supp),
                         "integer_matrix_rank": coh_rank, "integer_determinant": det,
                         "trace": trace,
                         "eigenvalue_multiplicities": coh_eigs},
            "why_coherent_support": "each j has 1 + N partners within Hamming distance 1, "
                                    "so |supp F| = 2^N (1+N) with no matrix built",
        },
        "R2": {"cell_counts_by_dim": cell_counts, "total_cells": 3 ** N,
               "boundary_composition_max_abs_entry_expected": 0,
               "why": "cubical chain complex identity d o d = 0"},
        "R3": {"FULL_FIELD": {"kappa_bits": float(2 * N),
                              "relation_cardinality": 4 ** N,
                              "E_cardinality": 3 ** N * 4 ** N},
               "RESTRICTED": {"relation_cardinality_by_dim": rest_card,
                              "kappa_bits_by_dim": {d: math.log2(v)
                                                    for d, v in rest_card.items()},
                              "E_cardinality": e_rest}},
        "C1_C3": {"fibre_cardinalities": {str(u): math.comb(N, u) for u in range(N + 1)},
                  "fibre_cardinality_sum": 2 ** N,
                  "kappa_ext_bits": {str(u): math.log2(math.comb(N, u))
                                     for u in range(N + 1)},
                  "empty_fibre_quotient_value": 5,
                  "empty_fibre_cardinality": 0},
    }
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps({"wrote": OUT, "coherent_det": det, "coherent_trace": trace,
                      "coherent_rank": coh_rank, "E_restricted": e_rest}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
