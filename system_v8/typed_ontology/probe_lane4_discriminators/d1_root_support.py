#!/usr/bin/env python3
"""D1 ROOT SUPPORT discriminator, n = 4.

Rival A: diagonal-only field  F[j][k] = d_j * delta_{jk}
Rival B: pair field retaining j != k, built on the SAME diagonal data d,
         plus the Hamming-1 off-diagonal terms.

The discriminator is run at three choices of the SAME diagonal data so that a
separation cannot be an artifact of one convenient d. Every observable is exact
integer / rational arithmetic (sympy over ZZ). No floats decide anything.

Absence rule honoured: H0_pair is log2 of a support cardinality. When the
support is empty the key is NOT PRESENT (no null, no 0, no NaN).
"""
import json
import math
import os
import sys

import sympy

N = 4
J = list(range(2 ** N))


def popcount(x):
    return bin(x).count("1")


def build(diag_data, keep_offdiag):
    """16x16 exact integer matrix. keep_offdiag=False deletes every j != k term."""
    rows = []
    for j in J:
        row = []
        for k in J:
            if j == k:
                row.append(diag_data[j])
            elif keep_offdiag and popcount(j ^ k) == 1:
                row.append(1)
            else:
                row.append(0)
        rows.append(row)
    return sympy.Matrix(rows)


def observe(M):
    """Every observable computed from the matrix, exactly."""
    support = [(j, k) for j in J for k in J if M[j, k] != 0]
    diag_support = [(j, k) for (j, k) in support if j == k]
    ham1_support = [(j, k) for (j, k) in support if popcount(j ^ k) == 1]
    lam = sympy.Symbol("lam")
    charpoly = sympy.Poly(M.charpoly(lam).as_expr(), lam).all_coeffs()
    out = {
        "support_cardinality": len(support),
        "diagonal_support_cardinality": len(diag_support),
        "hamming1_offdiagonal_support_cardinality": len(ham1_support),
        "exact_rank": int(M.rank()),
        "exact_determinant": int(M.det()),
        "charpoly_coeffs_exact": [int(c) for c in charpoly],
        "nullspace_dimension": int(2 ** N - M.rank()),
        "row_sum_multiset": sorted(int(sum(M.row(j))) for j in J),
    }
    # TYPED ABSENCE: no support -> the H0_pair key is not present at all.
    if len(support) > 0:
        out["H0_pair_bits"] = math.log2(len(support))
    return out


def z3_capacity_ceiling():
    """Structural claim, solver-decided, not asserted:
    a DIAGONAL support over J_4 x J_4 cannot exceed 2^n = 16 cells,
    so H0_pair of a diagonal field cannot exceed n.  Control: drop the
    diagonality constraint and the same cardinality bound becomes satisfiable.
    """
    import z3

    def run(diagonal_constraint, threshold):
        s = z3.Solver()
        sel = [[z3.Bool(f"s_{j}_{k}") for k in J] for j in J]
        if diagonal_constraint:
            for j in J:
                for k in J:
                    if j != k:
                        s.add(z3.Not(sel[j][k]))
        flat = [sel[j][k] for j in J for k in J]
        s.add(z3.Sum([z3.If(b, 1, 0) for b in flat]) > threshold)
        return str(s.check())

    return {
        "z3_version": ".".join(str(v) for v in z3.get_version()[:3]),
        "diagonal_support_gt_16_status": run(True, 2 ** N),
        "pair_support_gt_16_status_control": run(False, 2 ** N),
        "diagonal_support_gt_15_status_control": run(True, 2 ** N - 1),
        "threshold_2_to_the_n": 2 ** N,
    }


def main():
    variants = {
        "all_ones": {j: 1 for j in J},
        "even_parity_only": {j: (1 if popcount(j) % 2 == 0 else 0) for j in J},
        "all_zeros": {j: 0 for j in J},
    }
    result = {
        "discriminator": "D1_root_support_diagonal_vs_pair_field",
        "n": N,
        "address_cardinality": 2 ** N,
        "ordered_pair_cardinality": 4 ** N,
        "H0_addr_bits": float(N),
        "max_H0_pair_bits_reachable_by_a_diagonal_field": float(N),
        "max_H0_pair_bits_reachable_by_a_full_pair_field": float(2 * N),
        "diagonal_data_variants": {},
    }
    for name, d in variants.items():
        A = observe(build(d, keep_offdiag=False))
        B = observe(build(d, keep_offdiag=True))
        keys = sorted(set(A) | set(B))
        separating, non_separating, absent_asym = [], [], []
        for key in keys:
            if key not in A or key not in B:
                absent_asym.append(key)
            elif A[key] != B[key]:
                separating.append(key)
            else:
                non_separating.append(key)
        result["diagonal_data_variants"][name] = {
            "diagonal_data": [d[j] for j in J],
            "rival_A_diagonal_only": A,
            "rival_B_pair_field": B,
            "observables_that_separate": separating,
            "observables_that_do_not_separate": non_separating,
            "keys_present_in_one_rival_only": absent_asym,
        }
    result["solver_leg"] = z3_capacity_ceiling()
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results", "d1_root_support.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps(result, indent=1, sort_keys=True))
    print(f"WROTE {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
