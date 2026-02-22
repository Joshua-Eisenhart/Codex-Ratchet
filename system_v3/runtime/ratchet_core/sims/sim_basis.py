import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""Orthonormal basis: <e_i|e_j> = delta_ij, sum |e_i><e_i| = I."""


def main():
    # Standard basis for C^2
    e0 = [1+0j, 0+0j]
    e1 = [0+0j, 1+0j]

    # Orthonormality
    if abs(_inner(e0, e0) - 1.0) > 1e-9:
        raise SystemExit(1)
    if abs(_inner(e1, e1) - 1.0) > 1e-9:
        raise SystemExit(1)
    if abs(_inner(e0, e1)) > 1e-9:
        raise SystemExit(1)

    # Completeness: |e0><e0| + |e1><e1| = I
    proj = [[0+0j, 0+0j], [0+0j, 0+0j]]
    for e in [e0, e1]:
        for i in range(2):
            for j in range(2):
                proj[i][j] += e[i] * e[j].conjugate()
    if abs(proj[0][0] - 1) > 1e-9 or abs(proj[1][1] - 1) > 1e-9:
        raise SystemExit(1)
    if abs(proj[0][1]) > 1e-9 or abs(proj[1][0]) > 1e-9:
        raise SystemExit(1)


def _inner(a, b):
    return sum(x.conjugate() * y for x, y in zip(a, b))


if __name__ == "__main__":
    main()
