import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""NEGATIVE: purity of a non-Hermitian matrix is NOT in [0,1].
Proves: Tr(A^2) for arbitrary A is not bounded like Tr(rho^2).
Exit 0 = confirmed non-Hermitian purity is wrong. Exit 1 = it looked valid (bad)."""


def main():
    # Non-Hermitian, non-PSD matrix: "purity" can exceed 1
    A = [[2+0j, 3+0j], [0+0j, 4+0j]]
    p = _fake_purity(A)
    if 0 <= p <= 1:
        raise SystemExit(1)  # bounded like real purity = BAD

    # Non-trace-1 matrix: "purity" is not meaningful
    B = [[5+0j, 0j], [0j, 5+0j]]
    p2 = _fake_purity(B)
    if abs(p2 - 1.0) < 1e-9:
        raise SystemExit(1)  # looks like pure state = BAD


def _fake_purity(A):
    A2 = _matmul(A, A)
    return (A2[0][0] + A2[1][1]).real


def _matmul(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]


if __name__ == "__main__":
    main()
