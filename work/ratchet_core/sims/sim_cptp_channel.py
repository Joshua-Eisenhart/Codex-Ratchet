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
    # Simple bit-flip channel with p=0.1
    p = 0.1
    K0 = [[(1-p) ** 0.5 + 0j, 0j], [0j, (1-p) ** 0.5 + 0j]]
    K1 = [[0j, (p) ** 0.5 + 0j], [(p) ** 0.5 + 0j, 0j]]
    K0dK0 = matmul(dagger(K0), K0)
    K1dK1 = matmul(dagger(K1), K1)
    # Sum should be identity
    s00 = K0dK0[0][0] + K1dK1[0][0]
    s11 = K0dK0[1][1] + K1dK1[1][1]
    s01 = K0dK0[0][1] + K1dK1[0][1]
    s10 = K0dK0[1][0] + K1dK1[1][0]
    if abs(s00.real - 1.0) > 1e-9 or abs(s11.real - 1.0) > 1e-9:
        raise SystemExit(1)
    if abs(s01) > 1e-9 or abs(s10) > 1e-9:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
