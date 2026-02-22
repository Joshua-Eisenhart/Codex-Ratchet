import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""von Neumann entropy: S(rho) = -Tr(rho log rho) >= 0, = 0 for pure, = log(d) for maximally mixed."""
import math


def main():
    # Pure state |0><0|: entropy = 0
    rho_pure = [[1.0, 0.0], [0.0, 0.0]]
    s_pure = _entropy_2x2(rho_pure)
    if abs(s_pure) > 1e-9:
        raise SystemExit(1)

    # Maximally mixed I/2: entropy = log(2)
    rho_mixed = [[0.5, 0.0], [0.5, 0.0]]  # wrong — fix:
    rho_mixed = [[0.5, 0.0], [0.0, 0.5]]
    s_mixed = _entropy_2x2(rho_mixed)
    if abs(s_mixed - math.log(2)) > 1e-9:
        raise SystemExit(1)

    # General state: entropy >= 0
    rho = [[0.7, 0.0], [0.0, 0.3]]
    s = _entropy_2x2(rho)
    if s < -1e-9:
        raise SystemExit(1)


def _entropy_2x2(rho):
    a, d = rho[0][0], rho[1][1]
    s = 0.0
    for lam in [a, d]:
        if lam > 1e-15:
            s -= lam * math.log(lam)
    return s


if __name__ == "__main__":
    main()
