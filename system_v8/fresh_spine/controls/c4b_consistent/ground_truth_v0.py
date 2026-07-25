#!/usr/bin/env python3
"""ANALYTIC CONTROL for the fresh-spine n=4 fixtures.

Computes every quantity in the output contract by EXHAUSTIVE ENUMERATION in plain
Python. No jax, no torch, no julia, no numpy. Matrix rank is exact: Gaussian
elimination over Fraction, so there is no floating-point rank threshold anywhere.

This is what tells us whether three agreeing engines are three right answers or
three wrong ones. It is deliberately dumb and complete: |J| = 16, so everything
below enumerates the whole space rather than sampling or reasoning about it.

The lane re-derives the three presentation edge lists from their spec definitions
and asserts they match fixture_v0.json. If the fixture is edited, this lane fails
rather than silently agreeing with a corrupted input.
"""

import hashlib
import json
import math
import pathlib
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = HERE / "fixture_v0.json"
OUT = HERE / "ground_truth_v0.json"


def popcount(x: int) -> int:
    return bin(x).count("1")


def canon(edges) -> list:
    s = {(min(a, b), max(a, b)) for (a, b) in edges}
    return [list(e) for e in sorted(s)]


def exact_det(mat: list) -> Fraction:
    """Determinant over the rationals by exact elimination. Independent of exact_rank."""
    rows = [[Fraction(v) for v in row] for row in mat]
    n = len(rows)
    det = Fraction(1)
    for col in range(n):
        pivot = None
        for r in range(col, n):
            if rows[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            det = -det
        det *= rows[col][col]
        pv = rows[col][col]
        for r in range(col + 1, n):
            if rows[r][col] != 0:
                f = rows[r][col] / pv
                rows[r] = [a - f * b for a, b in zip(rows[r], rows[col])]
    return det


def exact_rank(mat: list) -> int:
    """Rank over the rationals by exact Gaussian elimination on Fractions."""
    rows = [[Fraction(v) for v in row] for row in mat]
    nrows = len(rows)
    ncols = len(rows[0]) if nrows else 0
    rank = 0
    for col in range(ncols):
        pivot = None
        for r in range(rank, nrows):
            if rows[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        pv = rows[rank][col]
        rows[rank] = [v / pv for v in rows[rank]]
        for r in range(nrows):
            if r != rank and rows[r][col] != 0:
                f = rows[r][col]
                rows[r] = [a - f * b for a, b in zip(rows[r], rows[rank])]
        rank += 1
        if rank == nrows:
            break
    return rank


def components(vertices, edges) -> int:
    """Connected-component count by explicit BFS over the enumerated vertex set."""
    adj = {v: set() for v in vertices}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen = set()
    count = 0
    for v in vertices:
        if v in seen:
            continue
        count += 1
        stack = [v]
        seen.add(v)
        while stack:
            u = stack.pop()
            for w in adj[u]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
    return count


def degree_sequence(vertices, edges) -> list:
    deg = {v: 0 for v in vertices}
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    return sorted(deg[v] for v in vertices)


def independent_cycles(vertices, edges) -> int:
    """edges - vertices + components, as the fixture spec declares."""
    return len(edges) - len(vertices) + components(vertices, edges)


# ---------------------------------------------------------------- fixture load
fixture = json.loads(FIXTURE.read_text())
fixture_sha = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

N = fixture["n"]
J = fixture["J"]
assert N == 4, N
assert J == list(range(16)), "J must be the 16 integers 0..15"
assert len(J) == 16

# Re-derive the presentations from their definitions and cross-check the fixture.
checker_edges = canon((j, k) for j in J for k in J if popcount(j ^ k) == 1)
gray_order = [i ^ (i >> 1) for i in J]
ring_edges = canon(
    (gray_order[i], gray_order[(i + 1) % 16]) for i in range(16)
)
sigma = [(3 * v + 7) % 16 for v in J]
spun_edges = canon((sigma[a], sigma[b]) for (a, b) in ring_edges)

crosscheck = {
    "checker_edges_match_fixture": checker_edges == fixture["presentations"]["checker"]["edges"],
    "ring_edges_match_fixture": ring_edges == fixture["presentations"]["ring"]["edges"],
    "spun_edges_match_fixture": spun_edges == fixture["presentations"]["spun"]["edges"],
    "gray_order_match_fixture": gray_order == fixture["presentations"]["ring"]["gray_code_order"],
    "sigma_match_fixture": sigma == fixture["presentations"]["spun"]["relabelling"],
    "sigma_is_bijection": sorted(sigma) == J,
}
for k, v in crosscheck.items():
    assert v, f"fixture cross-check excluded: {k}"

# ------------------------------------------------------------------- F0 fields
diag = [[1 if j == k else 0 for k in J] for j in J]
coh = [[1 if popcount(j ^ k) <= 1 else 0 for k in J] for j in J]

# Pair support counted over ORDERED pairs (j,k) in J x J, per the fixture spec's
# own derivation 16 + 16*4/2*2 = 80 for COHERENT.
diag_support_ordered = sum(1 for j in J for k in J if diag[j][k] != 0)
coh_support_ordered = sum(1 for j in J for k in J if coh[j][k] != 0)
# Recorded alongside so an implementation that chose UNORDERED can be diagnosed
# rather than mistaken for a wrong answer.
diag_support_unordered = sum(1 for j in J for k in J if j <= k and diag[j][k] != 0)
coh_support_unordered = sum(1 for j in J for k in J if j <= k and coh[j][k] != 0)

f0 = {
    "diag_a0": math.log2(len(J)),
    "diag_a1": math.log2(diag_support_ordered),
    "diag_a2": exact_rank(diag),
    "coh_a0": math.log2(len(J)),
    "coh_a1": math.log2(coh_support_ordered),
    "coh_a2": exact_rank(coh),
}

# A2 is the one quantity where an engine can plausibly go wrong (a floating-point
# rank threshold reports the wrong integer). Second, independent derivation:
# the Q4 adjacency spectrum is {4-2i} with multiplicity C(4,i), so COHERENT = I+A(Q4)
# has spectrum {5-2i}, and its determinant is the product of those. Full rank iff
# the determinant is non-zero. This path never runs elimination for the prediction.
coh_det_by_elimination = exact_det(coh)
coh_det_by_spectrum = 1
for i in range(N + 1):
    coh_det_by_spectrum *= (5 - 2 * i) ** math.comb(N, i)
diag_det_by_elimination = exact_det(diag)

a2_second_path = {
    "coh_det_by_elimination": int(coh_det_by_elimination),
    "coh_det_by_q4_spectrum": coh_det_by_spectrum,
    "coh_det_paths_agree": int(coh_det_by_elimination) == coh_det_by_spectrum,
    "coh_det_nonzero_so_full_rank": coh_det_by_spectrum != 0,
    "diag_det_by_elimination": int(diag_det_by_elimination),
    "reading": "Two independent paths agree that COHERENT is full rank: exact Fraction elimination, and the Q4 spectrum shifted by 1, whose eigenvalues {5,3,1,-1,-3} contain no zero. A2 therefore does NOT separate DIAG from COHERENT.",
}

# ------------------------------------------------------------------- F1 fibres
def fibres(mapping, codomain):
    return {y: sorted(j for j in J if mapping(j) == y) for y in codomain}


q_fibres = fibres(popcount, [0, 1, 2, 3, 4])
q2_fibres = fibres(lambda j: j % 5, [0, 1, 2, 3, 4])

f1_fibre_sizes = [len(q_fibres[y]) for y in [0, 1, 2, 3, 4]]
# Release_q(y) returns the fibre descriptor itself. No division, no arithmetic on
# an empty fibre: kappa is only defined where the fibre is non-empty, and where it
# is empty the descriptor is returned instead of a number.
f1_kappa = [
    math.log2(len(q_fibres[y])) if len(q_fibres[y]) > 0 else None
    for y in [0, 1, 2, 3, 4]
]
f1_release_descriptors = {
    str(y): {"fibre": q_fibres[y], "size": len(q_fibres[y]), "empty": len(q_fibres[y]) == 0}
    for y in [0, 1, 2, 3, 4]
}
f1_q2_fibre_sizes = [len(q2_fibres[y]) for y in [0, 1, 2, 3, 4]]

# --------------------------------------------------------- F2 presentations
def profile(vertices, edges):
    return {
        "vertices": len(vertices),
        "edges": len(edges),
        "degree_sequence": degree_sequence(vertices, edges),
        "components": components(vertices, edges),
        "independent_cycles": independent_cycles(vertices, edges),
    }


checker_profile = profile(J, [tuple(e) for e in checker_edges])
ring_profile = profile(J, [tuple(e) for e in ring_edges])
spun_profile = profile(J, [tuple(e) for e in spun_edges])

# N1 SEAM-BROKEN RING: delete one ring edge. The cut edge is declared, not chosen
# at random, so the control is reproducible.
n1_cut_edge = ring_edges[0]
n1_edges = [tuple(e) for e in ring_edges if e != n1_cut_edge]
n1_profile = profile(J, n1_edges)

# N2 BAD ADJACENCY: add an edge at Hamming distance 3 in CHECKER.
n2_added_edge = [0b0000, 0b0111]
assert popcount(n2_added_edge[0] ^ n2_added_edge[1]) == 3
n2_edges = [tuple(e) for e in canon([tuple(e) for e in checker_edges] + [tuple(n2_added_edge)])]
n2_profile = profile(J, n2_edges)
n2_degree_changed = n2_profile["degree_sequence"] != checker_profile["degree_sequence"]

# N3 NO-MAP CLAIM: assert CHECKER and RING are the same object with no transition
# map supplied. Not established -- the edge counts differ.
n3_edge_counts_differ = checker_profile["edges"] != ring_profile["edges"]

# ---------------------------------------------- F3 seam obligation and rewrites
def r(j: int) -> int:
    return j & 0b11


r_fibres = {y: sorted(j for j in J if r(j) == y) for y in range(4)}


def seam_ok(a: int, b: int) -> bool:
    return r(a) == r(b) or popcount(r(a) ^ r(b)) == 1


seam_total = len(checker_edges)
seam_satisfied = sum(1 for a, b in checker_edges if seam_ok(a, b))
seam_violations = [[a, b] for a, b in checker_edges if not seam_ok(a, b)]

# R1 CONTRACT: identify vertices sharing the same r image.
r1_quotient_vertices = sorted({r(j) for j in J})
r1_quotient_simple_edges = canon(
    (r(a), r(b)) for a, b in checker_edges if r(a) != r(b)
)
r1_selfloop_classes = sorted({r(a) for a, b in checker_edges if r(a) == r(b)})
r1_edges_becoming_selfloops = sum(1 for a, b in checker_edges if r(a) == r(b))
r1_edges_between_classes = sum(1 for a, b in checker_edges if r(a) != r(b))

# R2 OBSTRUCT: add edge (0b0000, 0b0111) then re-check the seam obligation.
# NO-REPAIR policy: nothing is adjusted to make the check pass. It stays BLOCKED.
r2_added_edge = [0b0000, 0b0111]
r2_edges = canon([tuple(e) for e in checker_edges] + [tuple(r2_added_edge)])
r2_violations = [[a, b] for a, b in r2_edges if not seam_ok(a, b)]
r2_blocked = len(r2_violations) > 0

ground_truth = {
    "ground_truth_id": "fresh_spine_ground_truth_v0",
    "method": "exhaustive enumeration over J (|J|=16) in plain Python; matrix rank exact over Fraction",
    "engines_used": [],
    "fixture_path": str(FIXTURE),
    "fixture_sha256": fixture_sha,
    "fixture_crosscheck": crosscheck,
    "python_version": sys.version.split()[0],
    "contract": {
        "f0_diag_a0": f0["diag_a0"],
        "f0_diag_a1": f0["diag_a1"],
        "f0_diag_a2": f0["diag_a2"],
        "f0_coh_a0": f0["coh_a0"],
        "f0_coh_a1": f0["coh_a1"],
        "f0_coh_a2": f0["coh_a2"],
        "f1_fibre_sizes": f1_fibre_sizes,
        "f1_kappa": f1_kappa,
        "f1_q2_fibre_sizes": f1_q2_fibre_sizes,
        "f2_checker_edges": checker_profile["edges"],
        "f2_ring_edges": ring_profile["edges"],
        "f2_checker_cycles": checker_profile["independent_cycles"],
        "f2_ring_cycles": ring_profile["independent_cycles"],
        "f2_n1_ring_cycles_after_cut": n1_profile["independent_cycles"],
        "f2_n2_degree_changed": n2_degree_changed,
        "f2_n3_edge_counts_differ": n3_edge_counts_differ,
        "f3_seam_satisfied_edges": seam_satisfied,
        "f3_seam_total_edges": seam_total,
        "f3_r1_quotient_vertices": len(r1_quotient_vertices),
        "f3_r2_violating_edges": len(r2_violations),
        "f3_r2_blocked": r2_blocked,
    },
    "exact_integer_forms": {
        "note": "integer counts the log2 values are taken of; engines can be compared exactly here rather than on floats",
        "address_space_size": len(J),
        "diag_pair_support_ordered": diag_support_ordered,
        "coh_pair_support_ordered": coh_support_ordered,
        "diag_pair_support_unordered": diag_support_unordered,
        "coh_pair_support_unordered": coh_support_unordered,
        "f1_fibre_sizes": f1_fibre_sizes,
    },
    "f0_discrimination": {
        "a0_separates": f0["diag_a0"] != f0["coh_a0"],
        "a1_separates": f0["diag_a1"] != f0["coh_a1"],
        "a2_separates": f0["diag_a2"] != f0["coh_a2"],
        "reading": "A0 is identical by construction (same J, same addresses). A2 is identical by computation, not by construction: I and I+A(Q4) are both full rank because the Q4 spectrum {4,2,0,-2,-4} shifted by 1 has no zero. Only A1 separates DIAG from COHERENT.",
        "a2_second_path": a2_second_path,
    },
    "f1_detail": {
        "q_fibres": {str(y): q_fibres[y] for y in q_fibres},
        "q2_fibres": {str(y): q2_fibres[y] for y in q2_fibres},
        "release_q_descriptors": f1_release_descriptors,
        "q_fibre_size_multiset": sorted(f1_fibre_sizes),
        "q2_fibre_size_multiset": sorted(f1_q2_fibre_sizes),
        "multisets_differ": sorted(f1_fibre_sizes) != sorted(f1_q2_fibre_sizes),
        "q_image_size": len({popcount(j) for j in J}),
        "q2_image_size": len({j % 5 for j in J}),
        "image_sizes_equal": len({popcount(j) for j in J}) == len({j % 5 for j in J}),
        "any_empty_fibre": any(s == 0 for s in f1_fibre_sizes + f1_q2_fibre_sizes),
        "reading": "q and q2 have the same image size, so |Q| does not separate them. The fibre-size multiset does.",
    },
    "f2_detail": {
        "checker": checker_profile,
        "ring": ring_profile,
        "spun": spun_profile,
        "spun_edges_differ_from_ring": spun_edges != ring_edges,
        "ring_edges_subset_of_checker": set(map(tuple, ring_edges)).issubset(set(map(tuple, checker_edges))),
        "n1_cut_edge": n1_cut_edge,
        "n1_profile": n1_profile,
        "n1_cycles_dropped": n1_profile["independent_cycles"] < ring_profile["independent_cycles"],
        "n2_added_edge": n2_added_edge,
        "n2_profile": n2_profile,
        "n2_degree_sequence_before": checker_profile["degree_sequence"],
        "n2_degree_sequence_after": n2_profile["degree_sequence"],
        "n3_reading": "CHECKER and RING have different edge counts, so the no-map identity claim is not established. A topology tool may measure a supplied complex; without the transition map it cannot declare two presentations globally identical.",
    },
    "f3_detail": {
        "r_definition": "r(j) = j & 0b11 (low two bits)",
        "r_fibres": {str(y): r_fibres[y] for y in r_fibres},
        "seam_total_edges": seam_total,
        "seam_satisfied_edges": seam_satisfied,
        "seam_violating_edges": seam_violations,
        "r1_quotient_vertex_labels": r1_quotient_vertices,
        "r1_quotient_simple_edges": r1_quotient_simple_edges,
        "r1_selfloop_classes": r1_selfloop_classes,
        "r1_edges_becoming_selfloops": r1_edges_becoming_selfloops,
        "r1_edges_between_classes": r1_edges_between_classes,
        "r1_verdict": "R1 survives the seam obligation: the contraction is applied as declared and no value is adjusted.",
        "r2_added_edge": r2_added_edge,
        "r2_total_edges_after": len(r2_edges),
        "r2_violating_edges": r2_violations,
        "r2_blocked": r2_blocked,
        "r2_verdict": "R2 is BLOCKED under the NO-REPAIR policy. The added edge (0,7) has r(0)=0b00 and r(7)=0b11, Hamming distance 2 in the base, so it is neither equal nor one bit apart. Nothing is adjusted to make it pass.",
    },
}

OUT.write_text(json.dumps(ground_truth, indent=2, sort_keys=True) + "\n")
print(json.dumps(ground_truth["contract"], indent=2, sort_keys=True))
print(f"\nfixture_sha256 {fixture_sha}")
print(f"wrote {OUT}")
