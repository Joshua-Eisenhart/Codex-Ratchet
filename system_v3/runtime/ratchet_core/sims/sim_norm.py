import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""Operator norm: ||A|| >= 0, ||cA|| = |c|·||A||, ||I|| = 1. Uses Frobenius norm."""
import math


def main():
    A = [[1+2j, 3+4j], [5+6j, 7+8j]]

    n = _frobenius(A)
    if n < -1e-9:
        raise SystemExit(1)

    # ||cA|| = |c| * ||A||
    c = 3 + 4j
    cA = [[c * A[i][j] for j in range(2)] for i in range(2)]
    if abs(_frobenius(cA) - abs(c) * n) > 1e-9:
        raise SystemExit(1)

    # ||0|| = 0
    Z = [[0j, 0j], [0j, 0j]]
    if abs(_frobenius(Z)) > 1e-9:
        raise SystemExit(1)

    # ||I|| = sqrt(2) for Frobenius
    I = [[1+0j, 0j], [0j, 1+0j]]
    if abs(_frobenius(I) - math.sqrt(2)) > 1e-9:
        raise SystemExit(1)


def _frobenius(m):
    s = 0.0
    for row in m:
        for x in row:
            s += x.real**2 + x.imag**2
    return math.sqrt(s)


if __name__ == "__main__":
    main()
