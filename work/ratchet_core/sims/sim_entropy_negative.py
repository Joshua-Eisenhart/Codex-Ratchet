#!/usr/bin/env python3
"""NEGATIVE: entropy WITHOUT the minus sign gives wrong results.
Proves: S(rho) = Tr(rho log rho) (no minus) is NOT a valid entropy.
Exit 0 = confirmed the wrong formula is wrong. Exit 1 = the wrong formula worked (bad)."""
import math


def main():
    # Maximally mixed state: correct entropy = log(2) ≈ 0.693
    # Wrong entropy (no minus sign) = -log(2) ≈ -0.693
    rho_mixed = [[0.5, 0.0], [0.0, 0.5]]
    wrong_entropy = _wrong_entropy(rho_mixed)

    # Wrong entropy should be NEGATIVE (real entropy is non-negative)
    if wrong_entropy >= 0:
        raise SystemExit(1)  # wrong formula gave non-negative = BAD

    # Pure state: wrong entropy = 0 (happens to be correct here)
    rho_pure = [[1.0, 0.0], [0.0, 0.0]]
    if abs(_wrong_entropy(rho_pure)) > 1e-9:
        raise SystemExit(1)

    # General state: wrong entropy should be negative
    rho = [[0.7, 0.0], [0.0, 0.3]]
    if _wrong_entropy(rho) >= 0:
        raise SystemExit(1)


def _wrong_entropy(rho):
    """Entropy WITHOUT minus sign: Tr(rho log rho). Should be <= 0."""
    a, d = rho[0][0], rho[1][1]
    s = 0.0
    for lam in [a, d]:
        if lam > 1e-15:
            s += lam * math.log(lam)
    return s


if __name__ == "__main__":
    main()
