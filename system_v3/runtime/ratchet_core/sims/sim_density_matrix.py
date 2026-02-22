import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
import math


def matmul(a, b):
    return [
        [a[0][0]*b[0][0] + a[0][1]*b[1][0], a[0][0]*b[0][1] + a[0][1]*b[1][1]],
        [a[1][0]*b[0][0] + a[1][1]*b[1][0], a[1][0]*b[0][1] + a[1][1]*b[1][1]],
    ]


def trace(a):
    return a[0][0] + a[1][1]


def main():
    # 2x2 density matrix: Hermitian, trace 1, PSD (eigenvalues >= 0)
    rho = [[0.7+0j, 0.2+0.1j], [0.2-0.1j, 0.3+0j]]
    if abs(trace(rho).real - 1.0) > 1e-9:
        raise SystemExit(1)
    if abs(rho[0][1] - rho[1][0].conjugate()) > 1e-9:
        raise SystemExit(1)
    # PSD check via eigenvalues of 2x2 Hermitian
    a = rho[0][0].real
    d = rho[1][1].real
    b = rho[0][1]
    tr = a + d
    det = a*d - (b.real*b.real + b.imag*b.imag)
    disc = tr*tr - 4*det
    if disc < -1e-12:
        raise SystemExit(1)
    lam1 = 0.5*(tr + math.sqrt(max(disc, 0.0)))
    lam2 = 0.5*(tr - math.sqrt(max(disc, 0.0)))
    if lam1 < -1e-9 or lam2 < -1e-9:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
