#!/usr/bin/env python3
"""NEGATIVE: fidelity with a non-PSD matrix is NOT bounded in [0,1].
Proves: F(rho, sigma) requires both inputs to be valid density matrices.
Exit 0 = confirmed bad inputs break fidelity. Exit 1 = looked valid (bad)."""


def main():
    p0 = [[1.0, 0.0], [0.0, 0.0]]

    # Not-a-density-matrix (trace >> 1, not PSD)
    bad = [[5.0, 0.0], [0.0, -4.0]]
    f = _trace_product(p0, bad)
    if 0 <= f <= 1:
        raise SystemExit(1)  # bounded like real fidelity = BAD

    # Not trace-1
    big = [[3.0, 0.0], [0.0, 3.0]]
    f2 = _trace_product(p0, big)
    if abs(f2) <= 1.0:
        raise SystemExit(1)  # bounded = BAD


def _trace_product(rho, sigma):
    s = 0.0
    for i in range(2):
        for j in range(2):
            s += rho[i][j] * sigma[j][i]
    return abs(s)


if __name__ == "__main__":
    main()
