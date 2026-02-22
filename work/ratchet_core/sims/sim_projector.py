#!/usr/bin/env python3
"""Projector: P^2 = P, P† = P, rank = Tr(P)."""


def main():
    # |0><0| projector
    P = [[1+0j, 0j], [0j, 0j]]

    # P^2 = P
    P2 = _matmul(P, P)
    for i in range(2):
        for j in range(2):
            if abs(P2[i][j] - P[i][j]) > 1e-9:
                raise SystemExit(1)

    # P† = P (Hermitian)
    for i in range(2):
        for j in range(2):
            if abs(P[i][j] - P[j][i].conjugate()) > 1e-9:
                raise SystemExit(1)

    # rank = Tr(P) = 1
    if abs((P[0][0] + P[1][1]).real - 1.0) > 1e-9:
        raise SystemExit(1)

    # |+><+| projector
    Q = [[0.5+0j, 0.5+0j], [0.5+0j, 0.5+0j]]
    Q2 = _matmul(Q, Q)
    for i in range(2):
        for j in range(2):
            if abs(Q2[i][j] - Q[i][j]) > 1e-9:
                raise SystemExit(1)


def _matmul(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]


if __name__ == "__main__":
    main()
