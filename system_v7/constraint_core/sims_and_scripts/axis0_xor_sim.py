"""
axis0_xor_sim.py  —  PURE MATH, NO JARGON.

Structural identity only. No terrain names, no Jungian labels. Labels live in the rosetta layer.

OBJECTS (pure):
  Each object is a pair of binary charges (a1, a2) in {0,1}^2:
    a1 = dynamics bit  (0 = spectrum-contracting / dephasing, 1 = spectrum-preserving / unitary)
    a2 = frame bit     (0 = identity frame, 1 = conjugated frame)
  A third derived bit is the parity  p = a1 XOR a2.

RESULT (deterministic algebra):
  The 2x2 lattice of (a1,a2) has a well-defined parity bit p = a1 XOR a2.
  p partitions the four objects into two classes:
      p = 0 : (0,0) and (1,1)   [charges agree]
      p = 1 : (1,0) and (0,1)   [charges disagree]
  XOR is not linearly separable in (a1,a2): no single linear functional of the two charges
  reproduces p. Reading p requires BOTH charges combined nonlinearly (a product of signs).

This file asserts nothing about what a1, a2, p "mean". That mapping (a1<->dynamics split,
a2<->frame split, p<->the third observed split, and all named-system overlays) is in the rosetta
layer, applied only after the structure is earned.

scratch_diagnostic; promotion_allowed=false.
"""
import itertools

def parity_lattice():
    rows = []
    for a1, a2 in itertools.product((0,1), repeat=2):
        rows.append((a1, a2, a1 ^ a2))
    return rows

def xor_not_linearly_separable():
    # brute force: does ANY linear rule sign(w1*a1 + w2*a2 - t) reproduce p for all 4 points?
    import numpy as np
    pts = parity_lattice()
    grid = np.linspace(-2, 2, 41)
    for w1 in grid:
        for w2 in grid:
            for t in grid:
                ok = all((1 if (w1*a1 + w2*a2 - t) > 0 else 0) == p for a1, a2, p in pts)
                if ok:
                    return False  # a separating line exists -> would be linearly separable
    return True  # no linear rule works

if __name__ == "__main__":
    print("a1 a2 | p=a1 XOR a2")
    for a1, a2, p in parity_lattice():
        print(f" {a1}  {a2} |     {p}")
    print(f"\nparity is NOT linearly separable in (a1,a2): {xor_not_linearly_separable()}")
    print("=> the parity bit requires both charges combined nonlinearly (product of two signs).")
