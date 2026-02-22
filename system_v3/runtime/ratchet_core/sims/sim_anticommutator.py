import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3

def mm(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]

def add(a, b):
    return [[a[i][j]+b[i][j] for j in range(2)] for i in range(2)]

def main():
    # {H, rho} = H rho + rho H
    # If H and rho are Hermitian, {H,rho} is Hermitian
    H = [[1+0j, 0.3+0j], [0.3+0j, -1+0j]]
    rho = [[0.6+0j, 0.1+0.2j], [0.1-0.2j, 0.4+0j]]
    anti = add(mm(H, rho), mm(rho, H))
    # Check Hermitian: anti[i][j] = anti[j][i].conj
    if abs(anti[0][1] - anti[1][0].conjugate()) > 1e-9:
        raise SystemExit(1)
    if abs(anti[0][0].imag) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
