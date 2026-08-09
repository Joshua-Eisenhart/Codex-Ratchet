#!/usr/bin/env python3
"""cb_lateral_wave — waves are linear; INSIDE a wave, spread laterally.

Every deterministic council so far ran its members in a for-loop. With
tier-1 members costing 0.03-8 ms, that is leaving the machine idle. A
wave is a barrier, not a bottleneck: within the barrier, mass-spawn.

Measured here:
  1. lateral scaling of a deterministic council across CPU cores
  2. the width knee on this machine
  3. a config sweep that is infeasible serially and cheap laterally

No model in the loop. Seeded, replayable, promotion_allowed=false.
"""
from __future__ import annotations
import json, math, os, random, time, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

CORES = os.cpu_count() or 8

# ---- a tier-1 council unit of work: cheap members over one artifact
def council_unit(seed: int) -> dict:
    """Runs the cheap deterministic council on one generated artifact.
    Deliberately uses only stdlib+cheap libs so it is spawn-safe."""
    import hashlib, re
    rng = random.Random(seed)
    art = {"verdict": rng.choice(["PARKED", "BLOCKED", "ADMIT_FOR_TESTING"]),
           "promotion_allowed": False,
           "entropy_bits": round(rng.uniform(0, 1.2), 4),
           "modulus": round(rng.uniform(0, 1.1), 4),
           "declared": rng.randint(1, 10), "matched": rng.randint(1, 10),
           "budgets": [rng.randint(1, 6) for _ in range(7)]}
    votes = {}
    # member: range membership (portion's job, vendored)
    votes["range"] = (0.0 <= art["entropy_bits"] <= 1.0
                      and 0.0 <= art["modulus"] <= 1.0)
    # member: coverage precondition (icontract's job, vendored)
    votes["coverage"] = art["matched"] <= art["declared"]
    # member: budget product ceiling (sympy/z3's job, vendored)
    prod = 1
    for b in art["budgets"]: prod *= b
    votes["budget"] = prod <= 10000
    # member: verdict ladder (jsonschema's job, vendored)
    votes["ladder"] = art["verdict"] in {"PARKED", "BLOCKED", "ADMIT_FOR_TESTING",
                                         "RELEASED", "HOLD", "UNRESOLVED"}
    # member: canonical digest stability (rfc8785's job, vendored)
    a = hashlib.sha256(json.dumps(art, sort_keys=True).encode()).hexdigest()
    b = hashlib.sha256(json.dumps(dict(reversed(list(art.items()))),
                                  sort_keys=True).encode()).hexdigest()
    votes["canonical"] = a == b
    admitted = all(votes.values())
    return {"seed": seed, "admitted": admitted,
            "refused_by": [k for k, v in votes.items() if not v]}

def lateral(n: int, width: int) -> tuple[float, list]:
    t0 = time.time()
    if width == 1:
        out = [council_unit(s) for s in range(n)]
    else:
        with ProcessPoolExecutor(max_workers=width) as ex:
            out = list(ex.map(council_unit, range(n), chunksize=max(1, n // (width * 4))))
    return time.time() - t0, out

def main():
    print(f"machine: {CORES} CPU cores\n")
    N = 20000
    print(f"LATERAL SCALING — {N:,} council units per arm")
    print(f"{'width':>7}{'seconds':>10}{'units/sec':>12}{'speedup':>10}{'efficiency':>12}")
    base = None; rows = []
    for w in (1, 2, 4, 6, 8, 10, 12, 16, 20):
        dt, out = lateral(N, w)
        rate = N / dt
        if base is None: base = rate
        rows.append((w, dt, rate, rate / base, rate / base / w))
        print(f"{w:>7}{dt:>10.2f}{rate:>12,.0f}{rate/base:>9.2f}x{rate/base/w:>11.0%}")
    knee = max(rows, key=lambda r: r[2])
    print(f"\nKNEE: width {knee[0]} at {knee[2]:,.0f} units/sec "
          f"({knee[3]:.1f}x serial)")

    # ---- what lateral makes feasible: a config sweep that is serial-infeasible
    print(f"\nSWEEP FEASIBILITY at the knee width ({knee[0]})")
    for label, configs in (("218 compositions (earlier serial sweep)", 218),
                           ("10k configs", 10_000),
                           ("1M configs", 1_000_000)):
        serial_s = configs / base
        lat_s = configs / knee[2]
        print(f"   {label:<38} serial {serial_s:>9,.1f}s   lateral {lat_s:>9,.1f}s"
              f"   ({serial_s/max(lat_s,1e-9):.1f}x)")

    # ---- correctness must survive lateral spread
    _, a = lateral(500, 1)
    _, b = lateral(500, knee[0])
    same = a == b
    print(f"\nDETERMINISM ACROSS WIDTHS: serial result == lateral result: {same}")
    refusals = {}
    for r in a:
        for k in r["refused_by"]: refusals[k] = refusals.get(k, 0) + 1
    print(f"refusals by member over 500 units: {refusals}")
    admitted = sum(1 for r in a if r["admitted"])
    print(f"admitted {admitted}/500  ({admitted/5:.1f}%)")

    out = Path("/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/receipts") / \
        f"lateral_wave_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schema": "cb.lateral-wave.v1", "cores": CORES,
        "n_per_arm": N,
        "scaling": [{"width": w, "sec": round(d, 3), "rate": round(r),
                     "speedup": round(s, 3), "efficiency": round(e, 3)}
                    for w, d, r, s, e in rows],
        "knee_width": knee[0], "knee_rate": round(knee[2]),
        "deterministic_across_widths": same,
        "promotion_allowed": False}, indent=1))
    print(f"RECEIPT {out.name}")

if __name__ == "__main__":
    main()
