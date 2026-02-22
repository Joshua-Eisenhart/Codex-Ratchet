#!/usr/bin/env python3

def matmul(a, b):
    return [
        [a[0][0]*b[0][0] + a[0][1]*b[1][0], a[0][0]*b[0][1] + a[0][1]*b[1][1]],
        [a[1][0]*b[0][0] + a[1][1]*b[1][0], a[1][0]*b[0][1] + a[1][1]*b[1][1]],
    ]


def dagger(a):
    return [
        [a[0][0].conjugate(), a[1][0].conjugate()],
        [a[0][1].conjugate(), a[1][1].conjugate()],
    ]


def main():
    # Hadamard gate (unitary)
    s = 1.0 / (2 ** 0.5)
    U = [[s+0j, s+0j], [s+0j, -s+0j]]
    UdagU = matmul(dagger(U), U)
    if abs(UdagU[0][0].real - 1.0) > 1e-9 or abs(UdagU[1][1].real - 1.0) > 1e-9:
        raise SystemExit(1)
    if abs(UdagU[0][1]) > 1e-9 or abs(UdagU[1][0]) > 1e-9:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
