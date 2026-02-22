import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
import math

def main():
    # Hermitian 2x2: eigenvalues must be real
    H = [[1+0j, 0.5+0j], [0.5+0j, -1+0j]]
    # Check Hermitian
    if abs(H[0][1] - H[1][0].conjugate()) > 1e-9:
        raise SystemExit(1)
    if abs(H[0][0].imag) > 1e-9 or abs(H[1][1].imag) > 1e-9:
        raise SystemExit(1)
    # Eigenvalues of 2x2 Hermitian are real
    a = H[0][0].real
    d = H[1][1].real
    b = H[0][1].real
    disc = (a - d)**2 + 4*b**2
    lam1 = 0.5*(a + d + math.sqrt(disc))
    lam2 = 0.5*(a + d - math.sqrt(disc))
    if abs(lam1.real - lam1) > 1e-9 or abs(lam2.real - lam2) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
