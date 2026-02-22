import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3


def matmul(a, b):
    return [
        [a[0][0]*b[0][0] + a[0][1]*b[1][0], a[0][0]*b[0][1] + a[0][1]*b[1][1]],
        [a[1][0]*b[0][0] + a[1][1]*b[1][0], a[1][0]*b[0][1] + a[1][1]*b[1][1]],
    ]


def sub(a, b):
    return [
        [a[0][0]-b[0][0], a[0][1]-b[0][1]],
        [a[1][0]-b[1][0], a[1][1]-b[1][1]],
    ]


def dagger(a):
    return [
        [a[0][0].conjugate(), a[1][0].conjugate()],
        [a[0][1].conjugate(), a[1][1].conjugate()],
    ]


def main():
    # Hermitian H and rho
    H = [[1+0j, 0.2+0j], [0.2+0j, -1+0j]]
    rho = [[0.6+0j, 0.1+0.1j], [0.1-0.1j, 0.4+0j]]
    comm = sub(matmul(H, rho), matmul(rho, H))
    # Commutator should be anti-Hermitian: comm^† = -comm
    comm_d = dagger(comm)
    if abs(comm_d[0][0] + comm[0][0]) > 1e-9:
        raise SystemExit(1)
    if abs(comm_d[1][1] + comm[1][1]) > 1e-9:
        raise SystemExit(1)
    if abs(comm_d[0][1] + comm[0][1]) > 1e-9:
        raise SystemExit(1)
    if abs(comm_d[1][0] + comm[1][0]) > 1e-9:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
