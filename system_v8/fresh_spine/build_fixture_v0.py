#!/usr/bin/env python3
"""Write the RAW fixture for the fresh-spine n=4 finite fixtures.

CONTRACT: this file writes ONLY raw finite data -- n, the enumeration of J, and
the three presentation edge lists (plus the two declarations that define RING and
SPUN: the Gray-code order and the SPUN relabelling table). It writes NO results,
NO capacities, NO counts, NO expected answers. Counts are results and live in
ground_truth_v0.json, which is produced by a separate lane.

Plain Python only. No jax, no torch, no julia, no numpy.
"""

import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "fixture_v0.json"

N = 4
J = list(range(1 << N))


def popcount(x: int) -> int:
    return bin(x).count("1")


def canon(edges) -> list:
    """Undirected edges, each stored once as [min, max], sorted lexicographically."""
    s = {(min(a, b), max(a, b)) for (a, b) in edges}
    return [list(e) for e in sorted(s)]


# CHECKER: the 4-cube graph Q4. Edge (j,k) iff popcount(j XOR k) == 1.
checker_edges = canon(
    (j, k) for j in J for k in J if popcount(j ^ k) == 1
)

# RING: the 16-cycle in standard reflected binary Gray-code order.
# g(i) = i XOR (i >> 1) is the standard reflected binary Gray code.
gray_order = [i ^ (i >> 1) for i in J]
ring_edges = canon(
    (gray_order[i], gray_order[(i + 1) % len(gray_order)]) for i in range(len(gray_order))
)

# SPUN: RING under an explicitly declared vertex relabelling.
# sigma(v) = (3*v + 7) mod 16.  gcd(3,16) == 1, so sigma is a bijection on J.
# The full table is written into the fixture so no reader has to re-derive it.
spun_relabelling = [(3 * v + 7) % 16 for v in J]
spun_edges = canon(
    (spun_relabelling[a], spun_relabelling[b]) for (a, b) in ring_edges
)

fixture = {
    "fixture_id": "fresh_spine_fixture_v0",
    "n": N,
    "J": J,
    "presentations": {
        "checker": {
            "definition": "edge (j,k) iff popcount(j XOR k) == 1",
            "edges": checker_edges,
        },
        "ring": {
            "definition": "16-cycle over gray_code_order, consecutive plus wrap",
            "gray_code_order": gray_order,
            "edges": ring_edges,
        },
        "spun": {
            "definition": "image of ring edges under relabelling sigma(v) = (3*v + 7) mod 16",
            "relabelling": spun_relabelling,
            "edges": spun_edges,
        },
    },
    "edge_convention": "undirected; each edge stored once as [min, max]; list sorted lexicographically",
}

text = json.dumps(fixture, indent=2, sort_keys=True) + "\n"
OUT.write_text(text)
digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
print(f"wrote {OUT}")
print(f"bytes {OUT.stat().st_size}")
print(f"sha256 {digest}")
