#!/usr/bin/env python3
"""Build the C3 (wrong carrier) and C4 (wrong order) control fixtures.

Same construction rules as build_fixture_v0.py, only the declared parameters
move. Raw finite data only: no capacities, no counts, no expected answers.

  c3_n3/fixture_v0.json      n = 3, so J = 0..7 : a 3-cube instead of a 4-cube
  c4a_inconsistent/...       n = 4, RING edges taken in PLAIN BINARY order while
                             the declared gray_code_order field still holds the
                             true Gray code -- the fixture contradicts itself
  c4b_consistent/...         n = 4, RING edges in plain binary order AND the
                             order field re-declared to match -- self-consistent
                             but no longer a Gray-code ring
"""

import hashlib
import json
import pathlib

C = pathlib.Path(__file__).resolve().parent


def popcount(x):
    return bin(x).count("1")


def canon(edges):
    s = {(min(a, b), max(a, b)) for (a, b) in edges}
    return [list(e) for e in sorted(s)]


def build(n, ring_order, declared_order, sigma_mod):
    J = list(range(1 << n))
    nj = len(J)
    checker = canon((j, k) for j in J for k in J if popcount(j ^ k) == 1)
    ring = canon(
        (ring_order[i], ring_order[(i + 1) % nj]) for i in range(nj)
    )
    sigma = [(3 * v + 7) % sigma_mod for v in J]
    spun = canon((sigma[a], sigma[b]) for (a, b) in ring)
    return {
        "fixture_id": "fresh_spine_fixture_v0",
        "n": n,
        "J": J,
        "presentations": {
            "checker": {
                "definition": "edge (j,k) iff popcount(j XOR k) == 1",
                "edges": checker,
            },
            "ring": {
                "definition": "16-cycle over gray_code_order, consecutive plus wrap",
                "gray_code_order": declared_order,
                "edges": ring,
            },
            "spun": {
                "definition": "image of ring edges under relabelling sigma(v) = (3*v + 7) mod 16",
                "relabelling": sigma,
                "edges": spun,
            },
        },
        "edge_convention": "undirected; each edge stored once as [min, max]; list sorted lexicographically",
    }


def write(subdir, fixture):
    d = C / subdir
    d.mkdir(parents=True, exist_ok=True)
    p = d / "fixture_v0.json"
    p.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    print("%-22s n=%d |J|=%2d checker=%2d ring=%2d spun=%2d  sha256=%s"
          % (subdir, fixture["n"], len(fixture["J"]),
             len(fixture["presentations"]["checker"]["edges"]),
             len(fixture["presentations"]["ring"]["edges"]),
             len(fixture["presentations"]["spun"]["edges"]), sha))
    return sha


# C3 : 3-cube. Gray code over 8 addresses; sigma modulus follows the carrier.
gray3 = [i ^ (i >> 1) for i in range(8)]
write("c3_n3", build(3, gray3, gray3, 8))

# C4 : 4-cube carrier kept; only the RING ORDER moves.
gray4 = [i ^ (i >> 1) for i in range(16)]
binary4 = list(range(16))
write("c4a_inconsistent", build(4, binary4, gray4, 16))
write("c4b_consistent", build(4, binary4, binary4, 16))

# reference: rebuild the real fixture's ring under the true Gray code so the two
# edge sets can be compared directly in the report
ring_gray = canon((gray4[i], gray4[(i + 1) % 16]) for i in range(16))
ring_bin = canon((binary4[i], binary4[(i + 1) % 16]) for i in range(16))
shared = sorted(set(map(tuple, ring_gray)) & set(map(tuple, ring_bin)))
print("\nRING edge sets: gray=%d edges, binary=%d edges, shared=%d edges"
      % (len(ring_gray), len(ring_bin), len(shared)))
print("shared edges:", [list(e) for e in shared])
checker4 = set(map(tuple, canon((j, k) for j in range(16) for k in range(16)
                                if popcount(j ^ k) == 1)))
print("gray ring is a subgraph of CHECKER :",
      set(map(tuple, ring_gray)).issubset(checker4))
print("binary ring is a subgraph of CHECKER :",
      set(map(tuple, ring_bin)).issubset(checker4))
