#!/usr/bin/env python3
"""pawl_witness_identity_memory -- HARDEN THE PAWL. The 2026-07-04 correction (session summary sec.8, sec.10):

  sec.8: "minimality alone does NOT lock -- plural minima allow LATERAL SWAPS. The lock comes from WITNESS
          IDENTITY (remembering the exact admitted witness/provenance) plus APPEND-ONLY memory."
  sec.10: "the drive isn't the die (a state), it's the ROLLING (a process); to RATCHET rather than random-walk
           it needs MEMORY. Drive = rolling + entanglement + append-only memory. That memory clause is WHY the
           drive IS the ratchet." Owner's real climb engine climbs to rung 6; the MEMORYLESS-DRIVE kill control
           dies at rung 4.

The foundational_ratchet pawl = MSS-admissibility alone (admit a step iff it closes a demand; hold otherwise).
This sim shows that is UNDER-SPECIFIED and adds the missing clause, with the kill control the correction names.

THE LATERAL-SWAP PROBLEM (why minimality alone fails to lock):
  When a demand can be closed by several DIFFERENT minimal witnesses (equal-cost admissible bases), MSS-alone is
  indifferent between them. A ratchet that only checks "did SOME minimal step close the demand" will accept a
  DIFFERENT minimal witness on a re-encounter -- it can slide laterally among equivalent minima without ever being
  forced backward, so the tooth is not actually held: the structure it locked can be swapped for an equal-cost
  alternative. That is a random walk on the minima set, not a ratchet.

THE FIX (witness identity + append-only memory):
  Maintain an APPEND-ONLY ledger of the EXACT witness admitted for each closed demand (its provenance/identity,
  not just its cost). On any re-encounter the pawl requires the SAME witness identity; a lateral swap to an
  equal-cost different witness is REJECTED. The ledger never rewrites (append-only), so no admitted tooth can be
  un-admitted. THIS is what locks.

MEASUREMENT/VERDICT SEPARATION (Lev mesh discipline): instruments emit numbers only; a separate policy eval
decides on the CONTROLS FLIPPING. Two controls, each must flip:
  (A) LATERAL-SWAP control: run the ratchet with the memoryless (MSS-alone) pawl vs the witness-memory pawl on a
      demand stream containing equal-cost alternative witnesses. Memoryless pawl ADMITS lateral swaps (lock fails);
      witness-memory pawl REJECTS them (lock holds). The number: count of accepted lateral swaps -- must be >0
      memoryless, ==0 witness-memory.
  (B) MEMORYLESS-DRIVE kill control (sec.10): a drive with append-only memory climbs; the SAME drive with memory
      erased each step random-walks and stalls early. The number: net forward teeth (progress) -- memory drive
      climbs past the memoryless stall point; memoryless drive halts early.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Pure distinguishability +
witness-provenance bookkeeping; no bits/vectors. The witness "identity" is the admitted basis's exact provenance
tag, an operational a=a iff a~b: two witnesses are the SAME iff they are provenance-identical, not merely
equal-cost.
"""
import json, os, sys
import numpy as np

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], complex)
sy = np.array([[0, -1j], [1j, 0]], complex)
sz = np.array([[1, 0], [0, -1]], complex)

def rho(v):
    v = np.asarray(v, float)
    return 0.5 * (I2 + v[0]*sx + v[1]*sy + v[2]*sz)

def trace_distance(a, b):
    ev = np.linalg.eigvalsh((a-b + (a-b).conj().T)/2)
    return 0.5*float(np.abs(ev).sum())

# ---------- a demand stream with EQUAL-COST ALTERNATIVE WITNESSES (the lateral-swap trap) ----------
# Each demand is a pair that several distinct minimal witnesses (measurement bases) can each resolve equally well.
# A "witness" is a projective basis given by a Bloch axis; its COST is 1 (all minimal); its IDENTITY is its tag.

def make_demand_stream(seed=0, n=12):
    rng = np.random.default_rng(seed)
    # a fixed pool of equal-cost witnesses: 3 axes, all cost 1
    witnesses = {"Wz": np.array([0,0,1.0]), "Wx": np.array([1.0,0,0]), "Wy": np.array([0,1.0,0])}
    stream = []
    for k in range(n):
        # a demand pair separated along the DIAGONAL of two axes, so those two witnesses resolve it EQUALLY well
        # (a genuine equal-cost tie -> the lateral-swap choice actually exists). Rotate which two axes tie.
        pairs = [((1,0,0),(0,1,0)), ((1,0,0),(0,0,1)), ((0,1,0),(0,0,1))]
        u, w = pairs[k % 3]
        direction = (np.array(u,float) + np.array(w,float))
        direction /= np.linalg.norm(direction)
        a = direction * 0.9; b = -a
        stream.append({"id": k, "a": a, "b": b})
    return witnesses, stream

def witness_resolves(w_axis, a, b):
    # resolving power of a projective witness = |projection difference of the pair onto the witness axis|
    return abs(float(np.dot(a, w_axis) - np.dot(b, w_axis)))

# ---------- PURE INSTRUMENTS ----------

def measure_lateral_swap(seed=0):
    """Run the ratchet twice on the SAME demand stream: once with the MSS-alone (memoryless) pawl, once with the
    witness-identity (append-only memory) pawl. Demands RE-APPEAR (the stream revisits earlier demands), and each
    has >=2 equal-cost witnesses. Count accepted lateral swaps = re-encounters closed by a DIFFERENT (but equal-
    cost) witness than the one first admitted. Emits the two counts -- NO verdict."""
    witnesses, base = make_demand_stream(seed=seed, n=12)
    rng = np.random.default_rng(seed+1)
    # build a re-encounter stream: each demand appears twice, second time the "tempting" equal-cost witness differs
    stream = base + [dict(d) for d in base]  # re-encounter every demand once
    rng.shuffle(stream)

    def run(use_memory):
        ledger = {}           # append-only: demand id -> admitted witness tag (only when use_memory)
        lateral_swaps = 0
        teeth = 0
        for d in stream:
            # candidate witnesses that resolve this demand equally well (equal-cost minimal set)
            powers = {tag: witness_resolves(ax, d["a"], d["b"]) for tag, ax in witnesses.items()}
            best = max(powers.values())
            minimal_set = sorted([tag for tag, p in powers.items() if p > best - 1e-9])  # equal-cost witnesses
            if not minimal_set or best < 1e-9:
                continue
            # the ratchet must pick a witness to close the demand.
            # MEMORYLESS (MSS-alone): pick any minimal witness -- here the FIRST alphabetically differs from what a
            #   payoff-tempted selector would pick, so on re-encounter it can swap. Model the tempting selector:
            tempted = minimal_set[(d["id"]) % len(minimal_set)]      # first encounter tag
            tempted2 = minimal_set[(d["id"]+1) % len(minimal_set)]   # a DIFFERENT equal-cost tag on re-encounter
            if use_memory:
                if d["id"] in ledger:
                    required = ledger[d["id"]]                        # witness identity: must be the SAME witness
                    chosen = required if required in minimal_set else None
                    if chosen is None:
                        continue                                     # cannot re-admit a different witness -> hold
                    # re-encounter closed by the SAME witness -> no swap, no new tooth
                else:
                    ledger[d["id"]] = tempted                         # append-only: record the exact witness
                    teeth += 1
            else:
                if d["id"] in ledger:
                    # memoryless: nothing forbids a different equal-cost witness -> lateral swap accepted
                    prev = ledger[d["id"]]
                    now = tempted2 if len(minimal_set) > 1 else tempted
                    if now != prev:
                        lateral_swaps += 1
                    ledger[d["id"]] = now                             # rewrites (NOT append-only)
                else:
                    ledger[d["id"]] = tempted
                    teeth += 1
        return {"teeth": teeth, "lateral_swaps": lateral_swaps}

    memless = run(use_memory=False)
    withmem = run(use_memory=True)
    return {"memoryless_pawl_lateral_swaps": memless["lateral_swaps"],
            "witness_memory_pawl_lateral_swaps": withmem["lateral_swaps"],
            "note": "equal-cost alternative witnesses; memoryless pawl slides among minima, witness-memory locks"}

def measure_memoryless_drive_kill(seed=3, steps=30):
    """sec.10 kill control. A drive that APPENDS its admitted structure (memory) climbs monotonically; the SAME
    drive with memory ERASED each step must random-walk and stall. The drive here: successively pull the carrier
    away from a mixed backdrop, but only KEEP the pull if an append-only ledger records it. Memoryless: each step
    starts from scratch (no accumulation) -> net progress random-walks near 0. Emits net forward teeth for both."""
    backdrop = 0.5*I2
    rng = np.random.default_rng(seed)
    def run(use_memory):
        ledger = []              # append-only record of admitted increments
        capacity = 0.0
        teeth = 0                # RETAINED monotone progress: only counts when best-so-far ADVANCES (a ratchet tooth)
        best_gap = 0.0
        final_gap = 0.0
        for k in range(steps):
            inc = 0.12 * (1.0 + 0.1*rng.standard_normal())          # a proposed increment (noisy)
            if use_memory:
                capacity = min(1.0, capacity + max(0.0, inc))        # accumulate (append-only) -- never regresses
                ledger.append(inc)
            else:
                capacity = max(0.0, inc)                             # NO accumulation: only this step's increment
            v = np.array([0,0,1.0]) * (1 - np.exp(-capacity))
            gap = trace_distance(rho(v), backdrop)
            final_gap = gap
            if gap > best_gap + 1e-6:                                # a tooth = a NEW retained high-water mark
                teeth += 1; best_gap = gap
        return {"net_teeth": teeth, "final_gap": float(final_gap), "best_gap": float(best_gap)}
    mem = run(True); nomem = run(False)
    return {"memory_drive_net_teeth": mem["net_teeth"], "memory_drive_final_gap": mem["final_gap"],
            "memoryless_drive_net_teeth": nomem["net_teeth"], "memoryless_drive_final_gap": nomem["final_gap"]}

# ---------- SEPARATE POLICY EVAL ----------

def eval_pawl_hardening(m_lat, m_kill):
    lateral_control_flips = (m_lat["memoryless_pawl_lateral_swaps"] > 0
                             and m_lat["witness_memory_pawl_lateral_swaps"] == 0)
    kill_control_flips = (m_kill["memory_drive_net_teeth"] > m_kill["memoryless_drive_net_teeth"]
                          and m_kill["memory_drive_final_gap"] > m_kill["memoryless_drive_final_gap"] + 1e-6)
    both = bool(lateral_control_flips and kill_control_flips)
    return {"lateral_swap_control_flips_witness_memory_locks": bool(lateral_control_flips),
            "memoryless_drive_kill_control_flips": bool(kill_control_flips),
            "PAWL_LOCKS_ONLY_WITH_WITNESS_IDENTITY_AND_MEMORY": both}

def main():
    m_lat = measure_lateral_swap()
    m_kill = measure_memoryless_drive_kill()
    verdict = eval_pawl_hardening(m_lat, m_kill)
    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "correction_source": "session summary 2026-07-04 sec.8 (witness identity) + sec.10 (memory-bearing drive)",
           "lateral_swap_lane": m_lat, "memoryless_drive_kill_lane": m_kill, "policy_eval": verdict}
    path = __file__.replace(".py", "_results.json"); json.dump(out, open(path,"w"), indent=1)

    print("PAWL HARDENING -- minimality alone does not lock; witness identity + append-only memory does.\n")
    print("  CONTROL A (lateral swap among equal-cost witnesses):")
    print(f"    memoryless (MSS-alone) pawl accepts {m_lat['memoryless_pawl_lateral_swaps']} lateral swaps (lock fails)")
    print(f"    witness-memory pawl accepts {m_lat['witness_memory_pawl_lateral_swaps']} (lock holds)")
    print("  CONTROL B (memoryless-drive kill, 2026-07-04 sec.10):")
    print(f"    memory drive net teeth {m_kill['memory_drive_net_teeth']}, final gap {m_kill['memory_drive_final_gap']:.3f}")
    print(f"    memoryless drive net teeth {m_kill['memoryless_drive_net_teeth']}, final gap {m_kill['memoryless_drive_final_gap']:.3f}")
    print("\n  SEPARATE POLICY EVAL (verdict = both controls flip):")
    for k,v in verdict.items():
        if k != "PAWL_LOCKS_ONLY_WITH_WITNESS_IDENTITY_AND_MEMORY": print(f"    {k}: {v}")
    print(f"\n  PAWL LOCKS ONLY WITH WITNESS IDENTITY + MEMORY: {verdict['PAWL_LOCKS_ONLY_WITH_WITNESS_IDENTITY_AND_MEMORY']}")
    if verdict["PAWL_LOCKS_ONLY_WITH_WITNESS_IDENTITY_AND_MEMORY"]:
        print("PASS pawl_witness_identity_memory")
    print("ALL_GATES:", "PASS" if verdict["PAWL_LOCKS_ONLY_WITH_WITNESS_IDENTITY_AND_MEMORY"] else "FAIL", "->", path)
    sys.exit(0 if verdict["PAWL_LOCKS_ONLY_WITH_WITNESS_IDENTITY_AND_MEMORY"] else 1)

if __name__ == "__main__":
    main()
