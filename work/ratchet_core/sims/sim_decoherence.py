#!/usr/bin/env python3
"""Decoherence: dephasing channel kills off-diagonals, preserves diagonals."""


def main():
    rho = [[0.6+0j, 0.3+0.2j], [0.3-0.2j, 0.4+0j]]

    # Full dephasing
    decohered = _dephase(rho, gamma=1.0)
    if abs(decohered[0][1]) > 1e-9 or abs(decohered[1][0]) > 1e-9:
        raise SystemExit(1)
    if abs(decohered[0][0] - rho[0][0]) > 1e-9:
        raise SystemExit(1)
    if abs(decohered[1][1] - rho[1][1]) > 1e-9:
        raise SystemExit(1)

    # Partial dephasing: off-diagonals shrink
    partial = _dephase(rho, gamma=0.5)
    if abs(partial[0][1]) > abs(rho[0][1]) + 1e-9:
        raise SystemExit(1)

    # No dephasing: unchanged
    nodeph = _dephase(rho, gamma=0.0)
    for i in range(2):
        for j in range(2):
            if abs(nodeph[i][j] - rho[i][j]) > 1e-9:
                raise SystemExit(1)


def _dephase(rho, gamma):
    out = [[rho[i][j] for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            if i != j:
                out[i][j] *= (1 - gamma)
    return out


if __name__ == "__main__":
    main()
