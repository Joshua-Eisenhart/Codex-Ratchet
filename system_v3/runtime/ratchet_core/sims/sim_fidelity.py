import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""Fidelity: F(rho, sigma) in [0,1], F(rho, rho) = 1 for pure states."""
import math


def main():
    # F(|0><0|, |0><0|) = 1
    p0 = [[1.0, 0.0], [0.0, 0.0]]
    if abs(_fidelity_pure(p0, p0) - 1.0) > 1e-9:
        raise SystemExit(1)

    # F(|0><0|, |1><1|) = 0
    p1 = [[0.0, 0.0], [0.0, 1.0]]
    if abs(_fidelity_pure(p0, p1)) > 1e-9:
        raise SystemExit(1)

    # F(|0><0|, |+><+|) = 0.5
    pp = [[0.5, 0.5], [0.5, 0.5]]
    f = _fidelity_pure(p0, pp)
    if abs(f - 0.5) > 1e-9:
        raise SystemExit(1)

    # F must be in [0,1]
    if f < -1e-9 or f > 1.0 + 1e-9:
        raise SystemExit(1)


def _fidelity_pure(rho, sigma):
    """For rank-1 projectors: F = Tr(rho sigma)."""
    s = 0.0
    for i in range(2):
        for j in range(2):
            s += rho[i][j] * sigma[j][i]
    return abs(s)


if __name__ == "__main__":
    main()
