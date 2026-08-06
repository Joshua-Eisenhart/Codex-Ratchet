#!/usr/bin/env python3
"""D5 ALGEBRA discriminator: [A,B] != 0 is NOT [a,b,c]_star != 0.

Rival A: associative operations suffice.
Rival B: an explicit bracketed nonassociative product is required.

Four explicit finite algebras, exact integer / rational arithmetic:
  M2(Z)        associative, noncommutative    -> commutator NONZERO, associator ZERO
  quaternions  associative, noncommutative    -> commutator NONZERO, associator ZERO
  octonions    nonassociative, noncommutative -> BOTH nonzero
  Jordan 2x2   commutative, nonassociative    -> commutator ZERO, associator NONZERO
The last row is the converse witness: nonassociativity does not require
noncommutation either. The separation runs in both directions.
"""
import json
import os
import sys
from itertools import product

import sympy

# ---- Cayley-Dickson tables, built by doubling. Exact integer structure constants.
def cayley_dickson(table):
    """table[i][j] = (sign, index). Double it: (a,b)(c,d) = (ac - d*b, da + b c*)."""
    n = len(table)
    conj = lambda i: (1 if i == 0 else -1, i)
    new = [[None] * (2 * n) for _ in range(2 * n)]
    def mul(i, j):
        return table[i][j]
    def cmul(i, j, ci=False, cj=False):
        s, k = mul(i, j)
        if ci:
            s *= conj(i)[0]
        if cj:
            s *= conj(j)[0]
        return s, k
    for a in range(n):
        for c in range(n):           # (a,0)(c,0) = (ac, 0)
            s, k = mul(a, c)
            new[a][c] = (s, k)
        for d in range(n):           # (a,0)(0,d) = (0, d a)
            s, k = mul(d, a)
            new[a][n + d] = (s, n + k)
    for b in range(n):
        for c in range(n):           # (0,b)(c,0) = (0, b c*)
            s, k = cmul(b, c, cj=True)
            new[n + b][c] = (s, n + k)
        for d in range(n):           # (0,b)(0,d) = (-d* b, 0)
            s, k = cmul(d, b, ci=True)
            new[n + b][n + d] = (-s, k)
    return new


COMPLEX = [[(1, 0), (1, 1)], [(1, 1), (-1, 0)]]
QUAT = cayley_dickson(COMPLEX)
OCT = cayley_dickson(QUAT)


def basis_algebra(table, name):
    dim = len(table)

    def mul(x, y):
        out = [0] * dim
        for i in range(dim):
            if x[i] == 0:
                continue
            for j in range(dim):
                if y[j] == 0:
                    continue
                s, k = table[i][j]
                out[k] += s * x[i] * y[j]
        return out

    def unit(i):
        v = [0] * dim
        v[i] = 1
        return v

    zero = [0] * dim
    sub = lambda x, y: [a - b for a, b in zip(x, y)]
    comm_witnesses, assoc_witnesses = [], []
    for i, j in product(range(dim), repeat=2):
        c = sub(mul(unit(i), unit(j)), mul(unit(j), unit(i)))
        if c != zero:
            comm_witnesses.append({"a": i, "b": j, "commutator": c})
    for i, j, k in product(range(dim), repeat=3):
        a = sub(mul(mul(unit(i), unit(j)), unit(k)), mul(unit(i), mul(unit(j), unit(k))))
        if a != zero:
            assoc_witnesses.append({"a": i, "b": j, "c": k, "associator": a})
    return {
        "algebra": name,
        "dimension": dim,
        "basis_triples_tested_for_associativity": dim ** 3,
        "basis_pairs_tested_for_commutativity": dim ** 2,
        "nonzero_commutator_witness_count": len(comm_witnesses),
        "nonzero_associator_witness_count": len(assoc_witnesses),
        "first_nonzero_commutator": comm_witnesses[0] if comm_witnesses else None,
        "first_nonzero_associator": assoc_witnesses[0] if assoc_witnesses else None,
        "commutator_vanishes_on_every_basis_pair": len(comm_witnesses) == 0,
        "associator_vanishes_on_every_basis_triple": len(assoc_witnesses) == 0,
    }


def matrix_algebra():
    """M2(Z): associative by construction, noncommutative. Exhaustive over an
    explicit finite basis-plus-sample set, with the associator computed, not assumed."""
    E = {f"e{i}{j}": sympy.Matrix(2, 2, lambda r, c: 1 if (r, c) == (i, j) else 0)
         for i in range(2) for j in range(2)}
    names = sorted(E)
    Z = sympy.zeros(2, 2)
    comm, assoc = [], []
    for a, b in product(names, repeat=2):
        c = E[a] * E[b] - E[b] * E[a]
        if c != Z:
            comm.append({"a": a, "b": b, "commutator": [int(x) for x in c]})
    for a, b, c in product(names, repeat=3):
        d = (E[a] * E[b]) * E[c] - E[a] * (E[b] * E[c])
        if d != Z:
            assoc.append({"a": a, "b": b, "c": c, "associator": [int(x) for x in d]})
    return {
        "algebra": "M2(Z) matrix units under matrix product",
        "dimension": 4,
        "basis_triples_tested_for_associativity": len(names) ** 3,
        "basis_pairs_tested_for_commutativity": len(names) ** 2,
        "nonzero_commutator_witness_count": len(comm),
        "nonzero_associator_witness_count": len(assoc),
        "first_nonzero_commutator": comm[0] if comm else None,
        "first_nonzero_associator": assoc[0] if assoc else None,
        "commutator_vanishes_on_every_basis_pair": len(comm) == 0,
        "associator_vanishes_on_every_basis_triple": len(assoc) == 0,
    }


def jordan_algebra():
    """Symmetric 2x2 rationals under A o B = (AB + BA)/2: COMMUTATIVE, and the
    associator is computed to see whether it vanishes."""
    S = {
        "s11": sympy.Matrix([[1, 0], [0, 0]]),
        "s22": sympy.Matrix([[0, 0], [0, 1]]),
        "s12": sympy.Matrix([[0, 1], [1, 0]]),
    }
    names = sorted(S)
    Z = sympy.zeros(2, 2)
    jm = lambda A, B: (A * B + B * A) / 2
    comm, assoc = [], []
    for a, b in product(names, repeat=2):
        c = jm(S[a], S[b]) - jm(S[b], S[a])
        if c != Z:
            comm.append({"a": a, "b": b})
    for a, b, c in product(names, repeat=3):
        d = jm(jm(S[a], S[b]), S[c]) - jm(S[a], jm(S[b], S[c]))
        if d != Z:
            assoc.append({"a": a, "b": b, "c": c,
                          "associator": [str(sympy.nsimplify(x)) for x in d]})
    return {
        "algebra": "symmetric 2x2 rationals under the Jordan product (AB+BA)/2",
        "dimension": 3,
        "basis_triples_tested_for_associativity": len(names) ** 3,
        "basis_pairs_tested_for_commutativity": len(names) ** 2,
        "nonzero_commutator_witness_count": len(comm),
        "nonzero_associator_witness_count": len(assoc),
        "first_nonzero_commutator": comm[0] if comm else None,
        "first_nonzero_associator": assoc[0] if assoc else None,
        "commutator_vanishes_on_every_basis_pair": len(comm) == 0,
        "associator_vanishes_on_every_basis_triple": len(assoc) == 0,
    }


def main():
    rows = [
        matrix_algebra(),
        basis_algebra(QUAT, "quaternions over Z, Cayley-Dickson basis"),
        basis_algebra(OCT, "octonions over Z, Cayley-Dickson basis"),
        jordan_algebra(),
    ]
    quadrant = {}
    for r in rows:
        nc = not r["commutator_vanishes_on_every_basis_pair"]
        na = not r["associator_vanishes_on_every_basis_triple"]
        quadrant[r["algebra"]] = {"noncommutative": nc, "nonassociative": na}
    occupied = sorted({(v["noncommutative"], v["nonassociative"]) for v in quadrant.values()})
    result = {
        "discriminator": "D5_algebra_associative_vs_bracketed_nonassociative",
        "algebras": rows,
        "quadrant_by_algebra": quadrant,
        "noncommutative_and_nonassociative_quadrants_occupied":
            [{"noncommutative": a, "nonassociative": b} for a, b in occupied],
        "a_noncommutative_algebra_with_a_vanishing_associator_exists":
            any(v["noncommutative"] and not v["nonassociative"] for v in quadrant.values()),
        "a_commutative_algebra_with_a_nonvanishing_associator_exists":
            any(not v["noncommutative"] and v["nonassociative"] for v in quadrant.values()),
    }
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results", "d5_algebra.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps(result, indent=1, sort_keys=True))
    print(f"WROTE {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
