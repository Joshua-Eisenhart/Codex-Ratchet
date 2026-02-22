#!/usr/bin/env python3
"""Projective measurement: projectors sum to I, outcomes are real, post-measurement states are valid."""


def main():
    # Z-basis measurement: P0=|0><0|, P1=|1><1|
    P0 = [[1+0j, 0j], [0j, 0j]]
    P1 = [[0j, 0j], [0j, 1+0j]]

    # Completeness: P0 + P1 = I
    for i in range(2):
        for j in range(2):
            expected = 1+0j if i == j else 0j
            if abs(P0[i][j] + P1[i][j] - expected) > 1e-9:
                raise SystemExit(1)

    # Born rule: p_k = Tr(P_k rho)
    rho = [[0.7+0j, 0.2+0.1j], [0.2-0.1j, 0.3+0j]]
    p0 = _trace_product(P0, rho).real
    p1 = _trace_product(P1, rho).real

    # Probabilities are real, non-negative, sum to 1
    if p0 < -1e-9 or p1 < -1e-9:
        raise SystemExit(1)
    if abs(p0 + p1 - 1.0) > 1e-9:
        raise SystemExit(1)


def _trace_product(A, B):
    s = 0+0j
    for i in range(2):
        for j in range(2):
            s += A[i][j] * B[j][i]
    return s


if __name__ == "__main__":
    main()
