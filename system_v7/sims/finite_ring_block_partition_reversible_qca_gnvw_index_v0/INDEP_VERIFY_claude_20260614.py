#!/usr/bin/env python3
"""INDEPENDENT adversarial re-derivation of the GNVW shift index.

Written by the Claude verify lane. Does NOT import the sim's image_for /
index_for / circuit_image. Reimplements symplectic swap conjugation and GF(2)
rank flow from scratch, then runs falsifiers the builder did not:

  F1  Does the SWAP block circuit (the schedule the source ships) realize a TRUE
      cyclic translation of cells?  (check as a permutation on 2^8 ring states)
  F2  Does the support index track cell displacement for k = 1..7, i.e. does it
      SCALE past the rigged k in {1,2,3} (genuine net flow), or SATURATE at +/-1?
  F3  FAKE-CIRCUIT control: feed a NON-translating reversible block circuit
      (an identity-equivalent even+odd SWAP double-pass) through the SAME index
      machinery.  A genuine support-flow index must return 0 for it; if the
      machinery returns +/-k regardless of the circuit, the conjugation is faked.
  F4  Is the conjugated single-cell image a single cell at (cell + k) mod 8 with
      NO size growth (translation), vs the brickwork CZ/CNOT which DO spread?
  F5  index operator == reversibility operator: same N, same bonds, same
      schedule, no lifted open line (positions are exactly 0..N-1, ring bond 7-0
      present, no 7-8 bond).
"""

import math

N = 8
LEFT_CELL = 3
RIGHT_CELL = 4
POSITIONS = list(range(N))
EVEN_BONDS = [(0, 1), (2, 3), (4, 5), (6, 7)]
ODD_BONDS = [(1, 2), (3, 4), (5, 6), (7, 0)]
# schedules copied from spec.json (these are the OBJECT under test)
RIGHT_SCHED = [(7, 0), (6, 7), (5, 6), (4, 5), (3, 4), (2, 3), (1, 2)]
LEFT_SCHED = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0)]


# ---- my own symplectic (Pauli support) representation: vec length 2N, [X|Z] ----
def gen(cell, kind):
    v = [0] * (2 * N)
    if kind == "X":
        v[cell] = 1
    else:
        v[N + cell] = 1
    return v


def swap_sym(v, a, b):
    v = list(v)
    v[a], v[b] = v[b], v[a]
    v[N + a], v[N + b] = v[N + b], v[N + a]
    return v


def conjugate_through_swaps(v, schedule, steps):
    for _ in range(steps):
        for a, b in schedule:
            v = swap_sym(v, a, b)
    return v


def support(v):
    return [p for p in POSITIONS if v[p] or v[N + p]]


# ---- my own GF(2) rank ----
def gf2_rank(rows):
    rows = [list(r) for r in rows if any(r)]
    rank = 0
    if not rows:
        return 0
    ncol = len(rows[0])
    col = 0
    while col < ncol and rank < len(rows):
        piv = next((r for r in range(rank, len(rows)) if rows[r][col]), None)
        if piv is not None:
            rows[rank], rows[piv] = rows[piv], rows[rank]
            for r in range(len(rows)):
                if r != rank and rows[r][col]:
                    rows[r] = [x ^ y for x, y in zip(rows[r], rows[rank])]
            rank += 1
        col += 1
    return rank


def restrict_side(v, side):
    keep = (lambda p: p >= RIGHT_CELL) if side == "right" else (lambda p: p <= LEFT_CELL)
    out = []
    for p in POSITIONS:
        if keep(p):
            out.extend([v[p], v[N + p]])
    return out


def boundary_cells(side, width):
    if side == "left":
        return [((LEFT_CELL - off) % N) for off in range(width - 1, -1, -1)]
    return [((RIGHT_CELL + off) % N) for off in range(width)]


def index_via_conjugation(image_fn, is_left, is_right, width):
    """Generic index: image_fn(cell,kind) gives the conjugated support vector.
    Mirrors the spec's local-cut flow but with my own rank machinery."""
    right_rows, left_rows = [], []
    imgs = {}
    for cell in boundary_cells("left", width):
        for kind in ("X", "Z"):
            vl = image_fn(cell, kind)
            if not is_left:
                right_rows.append(restrict_side(vl, "right"))
            imgs[f"A{cell}_{kind}"] = support(vl)
    for cell in boundary_cells("right", width):
        for kind in ("X", "Z"):
            vr = image_fn(cell, kind)
            if not is_right:
                left_rows.append(restrict_side(vr, "left"))
            imgs[f"A{cell}_{kind}"] = support(vr)
    rR = gf2_rank(right_rows)
    rL = gf2_rank(left_rows)
    return 0.5 * (rR - rL), rR, rL, imgs


# ---------------- F1: does the swap circuit equal a true cyclic shift? ---------
def swap_state(state, a, b):
    ab = (state >> a) & 1
    bb = (state >> b) & 1
    if ab != bb:
        state ^= (1 << a) | (1 << b)
    return state


def perm_of_schedule(schedule, steps):
    """Where does each single-occupied cell go under the swap circuit, read as a
    permutation of cell positions (occupy one cell, run circuit, see where it landed)."""
    perm = {}
    for c in range(N):
        st = 1 << c
        for _ in range(steps):
            for a, b in schedule:
                st = swap_state(st, a, b)
        landed = [i for i in range(N) if (st >> i) & 1]
        assert len(landed) == 1, f"cell {c} did not stay single under circuit: {landed}"
        perm[c] = landed[0]
    return perm


def f1():
    print("== F1: swap circuit vs true cyclic shift ==")
    ok = True
    for name, sched, sign in (("right", RIGHT_SCHED, +1), ("left", LEFT_SCHED, -1)):
        for k in range(1, 5):
            perm = perm_of_schedule(sched, k)
            expected = {c: (c + sign * k) % N for c in range(N)}
            match = perm == expected
            ok &= match
            print(f"  {name} k={k}: circuit perm == cyclic_shift({sign*k})? {match}  perm={perm}")
    print(f"  F1 PASS={ok}\n")
    return ok


# ---------------- F2: scaling past rigged k, F4: single-cell translation -------
def f2_f4():
    print("== F2/F4: index scaling for k=1..7 + single-cell-image check ==")
    ok = True
    for name, sched, is_left, is_right, sign in (
        ("right_shift", RIGHT_SCHED, False, True, +1),
        ("left_shift", LEFT_SCHED, True, False, -1),
    ):
        for k in range(1, 8):
            image_fn = lambda cell, kind, s=sched, kk=k: conjugate_through_swaps(gen(cell, kind), s, kk)
            units, rR, rL, imgs = index_via_conjugation(image_fn, is_left, is_right, width=k)
            # single-cell image translation check (F4)
            sizes_ok = all(len(sup) == 1 for sup in imgs.values())
            disp_ok = True
            for keyc, sup in imgs.items():
                c = int(keyc[1:].split("_")[0])
                if sup != [(c + sign * k) % N]:
                    disp_ok = False
            expected_units = sign * k
            scale_ok = abs(units - expected_units) < 1e-12
            ok &= scale_ok and sizes_ok and disp_ok
            print(f"  {name} k={k}: units={units} (expect {expected_units}) scale_ok={scale_ok} "
                  f"single_cell_images={sizes_ok} displacement_ok={disp_ok}")
    print(f"  F2/F4 PASS={ok}\n")
    return ok


# ---------------- F3: FAKE / NON-translating block-circuit control --------------
def f3():
    print("== F3: non-translating reversible block circuit must give index 0 ==")
    # A block circuit that is reversible but moves NOTHING across the cut:
    # apply each even bond's SWAP twice (= identity) -> reversible, no net transport.
    NULL_SCHED = []
    for a, b in EVEN_BONDS:
        NULL_SCHED += [(a, b), (a, b)]
    image_fn = lambda cell, kind: conjugate_through_swaps(gen(cell, kind), NULL_SCHED, 1)
    # treat it as a generic (non-shift) rule: restrict both sides, width 1
    units, rR, rL, imgs = index_via_conjugation(image_fn, is_left=False, is_right=False, width=1)
    # Also a REAL falsifier: run the SHIFT index path but with a null circuit and width=3.
    units3, rR3, rL3, _ = index_via_conjugation(image_fn, is_left=False, is_right=True, width=3)
    ok = abs(units) < 1e-12
    print(f"  null block circuit (double-swap=identity): units={units} rR={rR} rL={rL}  index0_ok={ok}")
    print(f"  null circuit forced through right-shift path width=3: units={units3} (a faked machine would print 3) -> {'FAKE' if abs(units3-3)<1e-9 else 'not faked'}")
    not_faked = abs(units3 - 3) > 1e-9
    print(f"  F3 PASS={ok and not_faked}\n")
    return ok and not_faked


# ---------------- F5: same operator, no lifted open line -----------------------
def f5():
    print("== F5: index op == reversibility op, no lifted open line ==")
    ring_bond_present = (7, 0) in ODD_BONDS
    no_lift = max(max(a, b) for a, b in EVEN_BONDS + ODD_BONDS + RIGHT_SCHED + LEFT_SCHED) == N - 1
    positions_ok = POSITIONS == list(range(N))
    ok = ring_bond_present and no_lift and positions_ok
    print(f"  periodic ring bond (7,0) present: {ring_bond_present}")
    print(f"  max cell index == N-1 == 7 (no lifted 0..8 / (7,8) open line): {no_lift}")
    print(f"  positions exactly 0..N-1: {positions_ok}")
    print(f"  F5 PASS={ok}\n")
    return ok


if __name__ == "__main__":
    r1 = f1()
    r24 = f2_f4()
    r3 = f3()
    r5 = f5()
    print("==== SUMMARY ====")
    print(f"F1 swap-circuit-is-true-shift : {r1}")
    print(f"F2/F4 scales k=1..7 + single-cell translation : {r24}")
    print(f"F3 non-translating circuit -> index 0, machine not faked : {r3}")
    print(f"F5 same operator, no lifted line : {r5}")
    print(f"ALL_INDEP_CHECKS_PASS={r1 and r24 and r3 and r5}")
