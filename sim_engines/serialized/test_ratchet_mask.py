#!/usr/bin/env python3
"""Phase 2 acceptance test — verifies the Julia-generated Ratchet mask.

Reads the Arrow artifact and asserts, from the bytes on disk (not from the
producer's claims):
  1. shape 16x16, entries strictly in {0.0, 1.0}, float64
  2. symmetric (undirected)
  3. zero diagonal (no self-loops)
  4. degree exactly 4 per node (2D torus: up/down/left/right)
  5. periodic wraparound: every (r,c) connects to (r,c±1 mod 4) and (r±1,c mod 4),
     and to NOTHING else (no diagonal smuggling edges)
  6. bipartite under the checkerboard coloring (r+c) mod 2

Usage: test_ratchet_mask.py <mask.arrow>
Exit: 0 all assertions hold, 1 any failure.
"""
import sys

import pyarrow.feather as feather

GRID = 4
N = GRID * GRID


def idx(r, c):
    return (r % GRID) * GRID + (c % GRID)  # 0-based


def main(path):
    table = feather.read_feather(path)
    a = [[float(table[f"dim_{j + 1}"][i]) for j in range(N)] for i in range(N)]
    checks = []

    # 1. shape + binary entries + dtype
    checks.append(("float64 columns", all(str(table[c].dtype) == "float64" for c in table.columns)))
    checks.append(("16x16", len(a) == N and all(len(row) == N for row in a)))
    checks.append(("entries in {0,1}", all(v in (0.0, 1.0) for row in a for v in row)))
    # 2. symmetric
    checks.append(("symmetric", all(a[i][j] == a[j][i] for i in range(N) for j in range(N))))
    # 3. zero diagonal
    checks.append(("zero diagonal", all(a[i][i] == 0.0 for i in range(N))))
    # 4. degree exactly 4
    checks.append(("degree 4 per node", all(sum(row) == 4.0 for row in a)))
    # 5. periodic wraparound + nothing else
    ok_ring = True
    for r in range(GRID):
        for c in range(GRID):
            i = idx(r, c)
            expected = {idx(r, c + 1), idx(r, c - 1), idx(r + 1, c), idx(r - 1, c)}
            actual = {j for j in range(N) if a[i][j] == 1.0}
            if actual != expected:
                ok_ring = False
    checks.append(("torus neighbours exactly {N,S,E,W} (no diagonals)", ok_ring))
    # 6. bipartite under checkerboard coloring
    color = [((i // GRID) + (i % GRID)) % 2 for i in range(N)]
    checks.append(("bipartite (checkerboard 2-coloring)",
                   all(color[i] != color[j] for i in range(N) for j in range(N) if a[i][j] == 1.0)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"[!] mask REJECTED: {failed}")
        return 1
    print(f"[*] mask VERIFIED: all {len(checks)} structural assertions hold ({path})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: test_ratchet_mask.py <mask.arrow>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
