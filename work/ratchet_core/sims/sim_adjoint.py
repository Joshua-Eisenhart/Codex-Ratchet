#!/usr/bin/env python3
"""Adjoint: (AB)† = B†A†, (A†)† = A, for 2x2 complex matrices."""


def main():
    A = [[1+2j, 3+4j], [5+6j, 7+8j]]
    B = [[0.5-1j, 2+0.5j], [1-3j, 4+2j]]

    # (A†)† = A
    Ad = _dag(A)
    Add = _dag(Ad)
    for i in range(2):
        for j in range(2):
            if abs(Add[i][j] - A[i][j]) > 1e-9:
                raise SystemExit(1)

    # (AB)† = B†A†
    AB = _matmul(A, B)
    AB_dag = _dag(AB)
    BdAd = _matmul(_dag(B), _dag(A))
    for i in range(2):
        for j in range(2):
            if abs(AB_dag[i][j] - BdAd[i][j]) > 1e-9:
                raise SystemExit(1)


def _dag(m):
    return [[m[j][i].conjugate() for j in range(2)] for i in range(2)]


def _matmul(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]


if __name__ == "__main__":
    main()
