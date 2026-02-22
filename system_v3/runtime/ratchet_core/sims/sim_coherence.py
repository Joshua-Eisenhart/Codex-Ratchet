import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""Coherence: l1-norm of off-diagonals >= 0, = 0 for diagonal (incoherent) states."""


def main():
    # Diagonal state: zero coherence
    rho_diag = [[0.7+0j, 0j], [0j, 0.3+0j]]
    if abs(_l1_coherence(rho_diag)) > 1e-9:
        raise SystemExit(1)

    # |+><+| state: maximal coherence for qubit = 1.0
    rho_plus = [[0.5+0j, 0.5+0j], [0.5+0j, 0.5+0j]]
    c = _l1_coherence(rho_plus)
    if abs(c - 1.0) > 1e-9:
        raise SystemExit(1)

    # General state: coherence >= 0
    rho = [[0.6+0j, 0.2+0.1j], [0.2-0.1j, 0.4+0j]]
    if _l1_coherence(rho) < -1e-9:
        raise SystemExit(1)


def _l1_coherence(rho):
    s = 0.0
    for i in range(2):
        for j in range(2):
            if i != j:
                s += abs(rho[i][j])
    return s


if __name__ == "__main__":
    main()
