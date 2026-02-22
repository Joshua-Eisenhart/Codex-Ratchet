import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""Purity: Tr(rho^2) in [0,1], = 1 for pure states, = 1/d for maximally mixed."""


def main():
    # Pure state: purity = 1
    rho_pure = [[1.0+0j, 0j], [0j, 0j]]
    if abs(_purity(rho_pure) - 1.0) > 1e-9:
        raise SystemExit(1)

    # Maximally mixed: purity = 1/d = 0.5
    rho_mixed = [[0.5+0j, 0j], [0j, 0.5+0j]]
    if abs(_purity(rho_mixed) - 0.5) > 1e-9:
        raise SystemExit(1)

    # General state: 1/d <= purity <= 1
    rho = [[0.7+0j, 0.2+0.1j], [0.2-0.1j, 0.3+0j]]
    p = _purity(rho)
    if p < 0.5 - 1e-9 or p > 1.0 + 1e-9:
        raise SystemExit(1)


def _purity(rho):
    rho2 = _matmul(rho, rho)
    return (rho2[0][0] + rho2[1][1]).real


def _matmul(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]


if __name__ == "__main__":
    main()
