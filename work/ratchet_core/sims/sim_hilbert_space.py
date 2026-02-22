#!/usr/bin/env python3
import math


def inner(u, v):
    return sum(uc.conjugate()*vc for uc, vc in zip(u, v))


def main():
    v = [complex(1, 0), complex(0, 1)]
    n = math.sqrt(inner(v, v).real)
    if abs(n - math.sqrt(2)) > 1e-9:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
