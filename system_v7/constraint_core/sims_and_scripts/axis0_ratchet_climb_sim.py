#!/usr/bin/env python3
"""axis0_ratchet_climb -- the A0_raw vector RATCHETS: each Axis-0 readout component earned one forced tooth
at a time, not measured all at once.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False.

WHY THIS EXISTS: axis0_shell_polarity_docfaithful measures the A0_raw vector and classifies two faces, but it
does NOT ratchet -- it reads all components at once. The owner: "it actually has to ratchet things." So this
fuses the proven climb mechanism (ratchet_climb_engine_v0: forced teeth, MSS batch-jump refusal, strict
refinement) with the A0_raw readout ladder (AXIS0_PHYSICS_MODEL_CORE section 24) as the RUNGS. Each component
of A0_raw is admitted ONLY when a lost distinction forces it; components that add no forced distinction land on
the FRONTIER -- which is how the "honest remainder" (order_gap did not separate the faces) becomes a RATCHET
STATEMENT instead of a footnote.

THE LADDER (A0_raw components, weakest readout -> strongest), section 24 order:
  L0_trivial -> L1_S (global entropy) -> L2_S_B (boundary) -> L3_H_Om (future-fuzz) -> L4_I_c (coherent info)
  -> L5_order_gap (N01 order witness)
CLIMB RULE (identical to ratchet_climb_engine_v0): admit level k+1 iff its readout partition on the finite
process pool STRICTLY REFINES level k's (forces >=1 new distinction). No strict refinement -> FRONTIER (does
not ratchet at this baseline). MSS: never admit a stronger level when a weaker one already forced the tooth.

TWO RESULTS:
  (1) GENERIC POOL: the ladder RATCHETS -- multiple A0_raw components each force a tooth (strict refinement),
      and at least ONE component lands on the FRONTIER: by the time the earlier teeth are placed, every process
      is already distinct, so that component carries no FORCED new distinction. WHICH component lands on the
      frontier depends on the pool and the readout quantization (measured at runtime, NOT asserted) -- what is
      structural is that the ratchet REFUSES an unforced admission. This is the "honest remainder" (a component
      that did not separate the faces in the polarity sim) derived as a ratchet frontier, not footnoted.
  (2) N01 DEMAND: order_gap is FORCED off the frontier by a demand only it can meet -- a pair the whole entropy
      sector (S,S_B,H_Om,I_c) reads as IDENTICAL yet order tells apart. Constructed exactly via two Kraus
      decompositions of the SAME channel (identical rho -> S,S_B,I_c identical to machine precision; H_Om
      matched within readout quantization) with different individual Kraus commutators. Under this demand the
      entropy sector gives 1 class and admitting order_gap gives 2 -> the tooth is forced. So order_gap RATCHETS
      iff the N01 demand is live; at the generic baseline it does not. Either way the answer is the ratchet's.
"""
import json, sys
import numpy as np

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)

def S(rho):
    w = np.linalg.eigvalsh((rho + rho.conj().T) / 2); w = w[w > 1e-12]
    return float(-(w * np.log2(w)).sum())

def ptB(rho):
    r = rho.reshape(2, 2, 2, 2); return np.einsum('ijik->jk', r)

def runit(rng):
    z = (rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))) / np.sqrt(2)
    q, r = np.linalg.qr(z); d = np.diagonal(r); return q * (d / np.abs(d))

def readouts(rho0, Ks, th):
    KsB = [np.kron(I2, K) for K in Ks]
    br = [k @ rho0 @ k.conj().T for k in KsB]
    wn = np.array([np.real(np.trace(b)) for b in br]); w = wn / wn.sum()
    rho = sum(br) / wn.sum()
    H = np.kron(SX, SX) + np.kron(SZ, SZ); ev, V = np.linalg.eigh(H)
    U = V @ np.diag(np.exp(-1j * th * ev)) @ V.conj().T
    rho = U @ rho @ U.conj().T; rho = (rho + rho.conj().T) / 2; rho = rho / np.real(np.trace(rho))
    if len(KsB) >= 2:
        ab = KsB[1] @ KsB[0] @ rho0 @ KsB[0].conj().T @ KsB[1].conj().T
        ba = KsB[0] @ KsB[1] @ rho0 @ KsB[1].conj().T @ KsB[0].conj().T
        og = float(np.linalg.norm(ab - ba))
    else:
        og = 0.0
    return {"S": S(rho), "S_B": S(ptB(rho)), "H_Om": float(-(w * np.log2(w + 1e-15)).sum()),
            "I_c": S(ptB(rho)) - S(rho), "order_gap": og}

LADDER = ["L0_trivial", "L1_S", "L2_S_B", "L3_H_Om", "L4_I_c", "L5_order_gap"]

def readvec(level, ro, q=0.02):
    Q = lambda x: int(round(x / q))
    cols = {"L0_trivial": [], "L1_S": ["S"], "L2_S_B": ["S", "S_B"],
            "L3_H_Om": ["S", "S_B", "H_Om"], "L4_I_c": ["S", "S_B", "H_Om", "I_c"],
            "L5_order_gap": ["S", "S_B", "H_Om", "I_c", "order_gap"]}
    return tuple(Q(ro[c]) for c in cols[level])

def partition(level, pool):
    cls = {}
    for i, ro in enumerate(pool):
        cls.setdefault(readvec(level, ro), []).append(i)
    return sorted(tuple(sorted(v)) for v in cls.values())

def climb(pool):
    prev = 1; admitted = []; frontier = []; ledger = []
    for L in LADDER:
        sz = len(partition(L, pool))
        if sz > prev:
            admitted.append(L); ledger.append({"level": L, "event": "TOOTH_FORCED", "classes": sz, "new": sz - prev}); prev = sz
        elif L != "L0_trivial":
            frontier.append(L); ledger.append({"level": L, "event": "FRONTIER", "classes": sz})
    return admitted, frontier, ledger

def build_generic_pool():
    pool = []
    for c in np.linspace(0.1, 0.9, 6):
        for sd in range(4):
            r = np.random.default_rng(100 + sd)
            rho0 = np.kron(0.5 * (I2 + 0.5 * SX), 0.5 * (I2 + 0.3 * SZ))
            wts = np.exp(3 * c * r.normal(size=3)); wts /= wts.sum()
            Ks = [np.sqrt(p) * runit(r) for p in wts]
            pool.append(readouts(rho0, Ks, 0.9 * c))
    return pool

def n01_demand_pair():
    """Two Kraus decompositions of the SAME channel -> S,S_B,I_c identical to machine precision, H_Om within
    quantization, order_gap DIFFERENT. The pure N01 demand only order_gap can meet."""
    rho0 = np.kron(0.5 * (I2 + 0.5 * SX), 0.5 * (I2 + 0.3 * SZ))
    base = [runit(np.random.default_rng(k)) for k in (1, 2, 3)]
    G = sum(K.conj().T @ K for K in base); Gi = np.linalg.inv(np.linalg.cholesky(G).conj().T)
    base = [K @ Gi for K in base]
    def mix(a, b):
        R1 = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        R2 = np.array([[np.cos(b), 0, -np.sin(b)], [0, 1, 0], [np.sin(b), 0, np.cos(b)]])
        U = R1 @ R2
        return [sum(U[i, j] * base[j] for j in range(3)) for i in range(3)]
    grid = []
    for a in np.linspace(0, 1.4, 12):
        for b in np.linspace(0, 1.4, 12):
            d = readouts(rho0, mix(a, b), 0.6); grid.append((d["H_Om"], d["order_gap"], a, b))
    best = None
    for i in range(len(grid)):
        for j in range(i + 1, len(grid)):
            if abs(grid[i][0] - grid[j][0]) < 1e-3 and abs(grid[i][1] - grid[j][1]) > 0.01:
                g = abs(grid[i][1] - grid[j][1])
                if best is None or g > best[0]: best = (g, i, j)
    _, i, j = best
    A = readouts(rho0, mix(grid[i][2], grid[i][3]), 0.6)
    B = readouts(rho0, mix(grid[j][2], grid[j][3]), 0.6)
    return A, B

def main():
    pool = build_generic_pool()
    admitted, frontier, ledger = climb(pool)

    A, B = n01_demand_pair()
    ent_exact = all(abs(A[k] - B[k]) < 1e-6 for k in ["S", "S_B", "I_c"])
    ent_sector_classes = len(partition("L4_I_c", [A, B]))
    order_classes = len(partition("L5_order_gap", [A, B]))
    order_forced = (ent_sector_classes == 1) and (order_classes == 2)

    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "generic_pool_size": len(pool),
           "forced_teeth": [a.split("_", 1)[1] for a in admitted],
           "frontier": [f.split("_", 1)[1] for f in frontier],
           "climb_ledger": ledger,
           "n01_demand": {"S_SB_Ic_identical_to_1e-6": bool(ent_exact),
                          "A_order_gap": round(A["order_gap"], 5), "B_order_gap": round(B["order_gap"], 5),
                          "entropy_sector_classes": ent_sector_classes, "with_order_gap_classes": order_classes,
                          "order_gap_forced_off_frontier": bool(order_forced)},
           "verdict_basis": "numpy_partition_measurement_on_CPTP_constructed_data (NOT solver-gated; the "
                            "refinement is a partition count, and an SMT encoding over the readouts would be a "
                            "pinned-constant tautology -- no free-variable theorem exists here, so no solver "
                            "gate is claimed. Ceiling scratch_diagnostic accordingly.)"}
    path = __file__.replace(".py", "_results.json"); json.dump(out, open(path, "w"), indent=1)

    print("THE A0_raw VECTOR RATCHETS -- each Axis-0 component earned one forced tooth at a time:")
    for e in ledger:
        tag = "TOOTH FORCED" if e["event"] == "TOOTH_FORCED" else "frontier    "
        extra = f"(+{e['new']} new distinctions)" if e["event"] == "TOOTH_FORCED" else "(no forced distinction here)"
        print(f"   {tag}  {e['level']:14s} classes={e['classes']:<3} {extra}")
    print(f"  forced teeth: {out['forced_teeth']}")
    print(f"  frontier (unforced at generic baseline): {out['frontier']}")
    print()
    print("N01 DEMAND -- can order_gap be FORCED off the frontier?")
    print(f"  entropy-identical pair (two Kraus decomps of one channel): S,S_B,I_c identical to 1e-6: {ent_exact}")
    print(f"  order_gap differs: A={A['order_gap']:.4f} vs B={B['order_gap']:.4f}")
    print(f"  entropy sector L4 classes: {ent_sector_classes} (cannot separate) -> admit order_gap L5: {order_classes}")
    print(f"  ORDER_GAP FORCED OFF FRONTIER BY N01 DEMAND: {order_forced}")
    # Gate tests the RATCHET MECHANISM, not a memorized component identity (which depends on pool + quantization):
    #  (1) the climb forces multiple teeth (the A0_raw ladder genuinely ratchets, not one batch jump),
    #  (2) at least one component lands on the FRONTIER (the ratchet refuses an unforced admission = honest remainder),
    #  (3) the N01 demand FORCES order_gap off the frontier (a pair the entropy sector cannot separate).
    n_forced = len(out["forced_teeth"]); n_frontier = len(out["frontier"])
    ratchets = n_forced >= 3
    has_frontier = n_frontier >= 1
    ok = ratchets and has_frontier and order_forced and ent_exact
    print(f"  MECHANISM: teeth forced={n_forced} (ratchets={ratchets}); frontier components={n_frontier} (honest remainder={has_frontier})")
    print(f"  VERDICT BASIS: numpy partition measurement on CPTP-constructed data (scratch_diagnostic). NOT")
    print(f"    solver-gated -- an SMT encoding over the readouts would pin every variable to a constant, a")
    print(f"    tautology, not a theorem; so no dual-solver claim is made here (three-engine contract not met).")
    if ok:
        print("PASS axis0_ratchet_climb")
    print("ALL_GATES:", "PASS" if ok else "FAIL", "->", path)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
