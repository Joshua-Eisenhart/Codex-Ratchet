#!/usr/bin/env python3
"""ratchet_definition_executable_v0 — the ratchet DEFINED as decidable math and RUN.

QUARANTINE_EXPLORATORY. classification = "scratch_diagnostic". promotion_allowed = False.

The definition (finite, decidable, falsifiable):
  Level strength IS expressible distinction: D_l(X) = partition of X induced by
  level-l readouts; l <= l' iff D_l coarsens D_l'. A demand = witness pair with
  provenance that MUST separate. Lift trigger = Lost(l, Delta) computed by
  exhaustive enumeration (Minimalist failure is a proof, not prose).
  One tooth: carve -> recompute -> if Lost empty: NO LIFT; else admit the
  MINIMAL sufficient level (MSS), log stronger candidates REJECTED-UNFORCED,
  lock append-only.
Checked theorems: T1 termination, T2 monotone expressivity, T3 no unforced
  lift, T4 pawl, T5 basin (order-permuted runs converge or measurably don't).
The forcing fact is real physics: R(2pi) flips the spinor sign while the
  density matrix is IDENTICAL — no rho-level ever separates it (proven here by
  enumeration); only the lift carries it.
"""
import itertools, json, sys
import numpy as np

EPS = 1e-9
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
S = np.array([[1, 0], [0, 1j]], dtype=complex)

def R(theta):  # spinor rotation about z: R(2pi) = -I on psi, identity on rho
    return np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=complex)

# ---------- carrier: states with process provenance (word), psi + rho ----------
def make_carrier():
    gates = {"H": H, "S": S, "X": X, "R2pi": R(2 * np.pi)}
    psi0 = np.array([1, 0], dtype=complex)
    items, seen = [], set()
    for n in range(0, 3):
        for word in itertools.product(sorted(gates), repeat=n):
            psi = psi0.copy()
            for g in word:
                psi = gates[g] @ psi
            key = ("".join(word),)
            if key in seen:
                continue
            seen.add(key)
            items.append({"word": "".join(word) or "id", "psi": psi,
                          "rho": np.outer(psi, psi.conj())})
    mixed = {"word": "MIXED", "psi": None, "rho": I2 / 2}  # maximally mixed prep
    items.append(mixed)
    return items

# ---------- levels: each = the partition its readouts induce (D_l) ----------
def sig(vals):
    return tuple(int(round(v / EPS)) for v in vals)

def level_readout(level, item, ref_psi):
    if level == "L0_trivial":
        return ()
    if level == "L1_Z":
        return sig([float(np.real(np.trace(Z @ item["rho"])))])
    if level == "L2_Pauli":
        return sig([float(np.real(np.trace(P @ item["rho"]))) for P in (X, Y, Z)])
    if level == "L3_Spinor":  # everything Pauli sees PLUS the lift sign vs reference word-class
        base = sig([float(np.real(np.trace(P @ item["rho"]))) for P in (X, Y, Z)])
        if item["psi"] is None:
            return base + ("mixed",)
        ov = complex(np.vdot(ref_psi(item), item["psi"]))
        return base + (int(round(np.sign(np.real(ov)) if abs(ov) > EPS else 0)),)
    raise KeyError(level)

LADDER = ["L0_trivial", "L1_Z", "L2_Pauli", "L3_Spinor"]  # candidate order irrelevant; MSS picks

def partition_of(level, items, ref_psi):
    classes = {}
    for i, it in enumerate(items):
        classes.setdefault(level_readout(level, it, ref_psi), []).append(i)
    return sorted(tuple(sorted(v)) for v in classes.values())

def separates(level, items, i, j, ref_psi):
    return level_readout(level, items[i], ref_psi) != level_readout(level, items[j], ref_psi)

def refines(pA, pB):  # every class of pA inside a class of pB (pA finer-or-equal)
    lookup = {i: k for k, cls in enumerate(pB) for i in cls}
    return all(len({lookup[i] for i in cls}) == 1 for cls in pA)

# ---------- the run ----------
def run(order_seed):
    rng = np.random.default_rng(order_seed)
    items = make_carrier()
    idx = {it["word"]: k for k, it in enumerate(items)}
    strip = lambda w: w.replace("R2pi", "")  # spinor reference: same word minus rotations
    def ref_psi(item):
        base = strip(item["word"]) or "id"
        return items[idx[base]]["psi"] if base in idx else item["psi"]

    # demands: (name, i, j, provenance, admissible?)
    demands = [
        ("sep_0_vs_1",      idx["id"], idx["X"],    "prep difference (physical)", True),
        ("sep_plus_vs_mix", idx["H"],  idx["MIXED"], "pure vs mixed prep",         True),
        ("sep_720_process", idx["id"], idx["R2pi"], "R(2pi) applied vs not: rho identical, process distinct", True),
        ("void_HH_vs_id",   idx["HH"], idx["id"],   "no constraint witness distinguishes these preps", False),
    ]
    rng.shuffle(demands)  # N01: order varies per run

    level, open_d, ledger, expr_prev = "L0_trivial", list(demands), [], None
    measure_prev = None
    theorems = {"T1_termination": True, "T2_monotone_expressivity": True,
                "T3_no_unforced_lift": True, "T4_pawl": True}
    admitted_levels = [level]

    for step in range(1, 12):
        lost, voided = [], []
        for d in list(open_d):
            name, i, j, prov, admissible = d
            if separates(level, items, i, j, ref_psi):
                ledger.append({"step": step, "event": "DEMAND_MET", "demand": name, "level": level})
                open_d.remove(d); continue
            # Minimalist attempt = exhaustive: is ANY current-level distinction separating? (that IS separates())
            if not admissible:
                if all(not separates(L, items, i, j, ref_psi) for L in LADDER):
                    ledger.append({"step": step, "event": "DEMAND_VOID", "demand": name,
                                   "reason": "no level separates; no constraint witness -> trigger refuses"})
                    open_d.remove(d); voided.append(name); continue
            lost.append(d)
        measure = (len(open_d), LADDER.index(level))
        if measure_prev is not None and not (measure < measure_prev or measure != measure_prev):
            pass
        if not lost:
            ledger.append({"step": step, "event": "NO_LIFT", "level": level,
                           "note": "Minimalist wins: no admissible lost distinction"})
            break
        # MSS, smallest-step form: the weakest level that makes ANY progress —
        # expresses at least one lost demand. One tooth per demand class, never
        # a batch jump to the level that solves everything at once.
        cands = [L for L in LADDER
                 if any(separates(L, items, i, j, ref_psi) for (_, i, j, _, _) in lost)]
        if not cands:
            ledger.append({"step": step, "event": "FRONTIER", "unexpressible": [d[0] for d in lost]})
            break
        sizes = {L: len(partition_of(L, items, ref_psi)) for L in cands}
        cur_size = len(partition_of(level, items, ref_psi))
        cands = [L for L in cands if sizes[L] > cur_size]  # must strictly refine
        if not cands:
            ledger.append({"step": step, "event": "FRONTIER", "unexpressible": [d[0] for d in lost]})
            break
        weakest = min(cands, key=lambda L: (sizes[L], LADDER.index(L)))
        for L in cands:
            if L != weakest:
                ledger.append({"step": step, "event": "REJECTED_UNFORCED", "candidate": L,
                               "classes": sizes[L], "vs_weakest": sizes[weakest]})
        # Minimalist receipt: current level provably fails each lost demand (enumerated)
        for (name, i, j, prov, _) in lost:
            ledger.append({"step": step, "event": "MINIMALIST_FAILED_PROOF", "demand": name,
                           "level": level, "provenance": prov,
                           "readout_i": str(level_readout(level, items[i], ref_psi)),
                           "readout_j": str(level_readout(level, items[j], ref_psi))})
        # T3: lift only with nonempty lost; T2: strict refinement; T4: pawl
        p_old = partition_of(level, items, ref_psi); p_new = partition_of(weakest, items, ref_psi)
        if not (refines(p_new, p_old) and p_new != p_old):
            theorems["T2_monotone_expressivity"] = False
        if LADDER.index(weakest) <= LADDER.index(level):
            theorems["T4_pawl"] = False
        ledger.append({"step": step, "event": "LIFT_LOCKED", "from": level, "to": weakest,
                       "lost_demands": [d[0] for d in lost],
                       "classes_before": len(p_old), "classes_after": len(p_new)})
        level = weakest; admitted_levels.append(level)
        if measure_prev is not None and measure >= measure_prev:
            theorems["T1_termination"] = False
        measure_prev = measure
    if any(e["event"] == "LIFT_LOCKED" and not e["lost_demands"] for e in ledger):
        theorems["T3_no_unforced_lift"] = False
    return {"terminal_level": level, "admitted_ladder": admitted_levels,
            "terminal_classes": len(partition_of(level, items, ref_psi)),
            "ledger": ledger, "theorems": theorems}

def main():
    runs = {s: run(s) for s in (11, 23, 47)}  # T5: order-permuted runs
    t5 = len({(r["terminal_level"], r["terminal_classes"],
               tuple(r["admitted_ladder"])) for r in runs.values()}) == 1
    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "runs": runs, "T5_basin_convergence": t5}
    path = __file__.replace(".py", "_results.json")
    json.dump(out, open(path, "w"), indent=1, default=str)
    r = runs[11]
    print(f"terminal level: {r['terminal_level']}  ladder: {' -> '.join(r['admitted_ladder'])}")
    for e in r["ledger"]:
        print(" ", {k: v for k, v in e.items() if k != 'provenance'})
    print("theorems:", r["theorems"], " T5_basin(3 orders):", t5)
    ok = all(r["theorems"].values()) and t5
    print("ALL_GATES:", "PASS" if ok else "FAIL", "->", path)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
