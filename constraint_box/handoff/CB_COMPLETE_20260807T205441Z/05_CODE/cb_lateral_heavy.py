#!/usr/bin/env python3
"""cb_lateral_heavy — lateral spread on the HEAVY tier, measuring the real
trade: wall time DOWN, total burn UP.

Cheap members lose to spawn overhead (measured: knee at width 6, only
2.7x, negative past 10). Heavy members are the opposite case: per-unit
work dwarfs coordination, so width buys latency.

What is measured per width:
  wall      elapsed seconds the operator waits
  burn      summed CPU seconds actually consumed across workers
  ratio     burn / wall  (how much machine is in flight at once)
  overhead  burn(width) / burn(serial)  (the cost of going wide)

The rule this produces: width per MEMBER CLASS, not one width for the run.
promotion_allowed=false.
"""
from __future__ import annotations
import json, os, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

CORES = os.cpu_count() or 8

def heavy_unit(seed: int) -> dict:
    """One artifact through the expensive tier: deepdiff, pint, sympy,
    networkx, celpy. Each import happens in the worker, as it would in a
    real spawned member."""
    t_cpu0 = time.process_time()
    import random
    rng = random.Random(seed)
    art = {"verdict": "PARKED", "promotion_allowed": False,
           "declared": rng.randint(1, 9), "matched": rng.randint(1, 9),
           "duration": 1.5, "duration_unit": rng.choice(["second", "meter"]),
           "budgets": [rng.randint(1, 6) for _ in range(7)],
           "nested": {"a": [1, 2, {"b": rng.randint(0, 3)}]}}
    votes = {}

    from deepdiff import DeepDiff
    twin = json.loads(json.dumps(art)); twin["nested"]["a"][2]["b"] += 1
    votes["deepdiff"] = bool(DeepDiff(art, twin))          # names the change

    import pint
    u = pint.UnitRegistry()
    try:
        (art["duration"] * u(art["duration_unit"])).to("millisecond")
        votes["pint"] = True
    except Exception:
        votes["pint"] = False

    import sympy as sp
    votes["sympy"] = int(sp.prod(art["budgets"])) <= 10000

    import networkx as nx
    g = nx.DiGraph([(0, 1), (1, 2), (2, 3)])
    votes["networkx"] = nx.is_directed_acyclic_graph(g)

    import celpy
    env = celpy.Environment()
    prog = env.program(env.compile("matched <= declared"))
    votes["celpy"] = bool(prog.evaluate(
        {"matched": celpy.json_to_cel(art["matched"]),
         "declared": celpy.json_to_cel(art["declared"])}))

    return {"seed": seed, "admitted": all(votes.values()),
            "refused_by": [k for k, v in votes.items() if not v],
            "cpu": time.process_time() - t_cpu0}

def arm(n: int, width: int):
    t0 = time.time()
    if width == 1:
        out = [heavy_unit(s) for s in range(n)]
    else:
        with ProcessPoolExecutor(max_workers=width) as ex:
            out = list(ex.map(heavy_unit, range(n), chunksize=1))
    wall = time.time() - t0
    burn = sum(r["cpu"] for r in out)
    return wall, burn, out

def main():
    N = 60
    print(f"machine {CORES} cores | HEAVY tier: deepdiff+pint+sympy+networkx+celpy")
    print(f"{N} artifacts per arm\n")
    print(f"{'width':>6}{'wall s':>9}{'burn s':>9}{'burn/wall':>11}"
          f"{'speedup':>9}{'burn cost':>11}{'sec/artifact':>14}")
    rows = []; w1 = b1 = None
    for w in (1, 2, 4, 6, 8, 10):
        wall, burn, out = arm(N, w)
        if w1 is None: w1, b1 = wall, burn
        rows.append((w, wall, burn, burn / wall, w1 / wall, burn / b1, wall / N))
        print(f"{w:>6}{wall:>9.2f}{burn:>9.2f}{burn/wall:>11.2f}"
              f"{w1/wall:>8.2f}x{burn/b1:>10.2f}x{wall/N:>14.3f}")

    best = max(rows, key=lambda r: r[4])
    print(f"\nFASTEST: width {best[0]} — wall {best[1]:.2f}s ({best[4]:.2f}x faster) "
          f"while burning {best[5]:.2f}x the CPU")
    # find the width where extra burn stops buying wall time
    knee = None
    for a, b in zip(rows, rows[1:]):
        if b[4] < a[4] * 1.05:      # <5% further speedup
            knee = a; break
    if knee:
        print(f"DIMINISHING RETURN at width {knee[0]}: beyond it, burn rises "
              f"without shortening wall time")
    print(f"\nTRADE, stated: lateral does not reduce work. It converts "
          f"{best[5]:.2f}x burn into {best[4]:.2f}x less waiting.")

    _, _, a = arm(12, 1); _, _, b = arm(12, 6)
    same = [x["admitted"] for x in a] == [x["admitted"] for x in b]
    print(f"determinism across widths: {same}")

    out = Path("/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/receipts") / \
        f"lateral_heavy_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schema": "cb.lateral-heavy.v1", "cores": CORES,
        "n": N, "rows": [{"width": r[0], "wall": round(r[1], 3),
                          "burn": round(r[2], 3), "burn_per_wall": round(r[3], 2),
                          "speedup": round(r[4], 3), "burn_cost": round(r[5], 3)}
                         for r in rows],
        "fastest_width": best[0], "deterministic": same,
        "promotion_allowed": False}, indent=1))
    print(f"RECEIPT {out.name}")

if __name__ == "__main__":
    main()
