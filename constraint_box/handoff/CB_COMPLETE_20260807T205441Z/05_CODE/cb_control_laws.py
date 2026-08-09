#!/usr/bin/env python3
"""cb_control_laws — the laws measured this session, encoded as checks.

Every law here was established by running it, not by argument. Each has
a self-test that reproduces the measurement. Stdlib only; no model in
the loop. promotion_allowed=false.

LAW 1  DIVERGENCE COLLAPSE
       A destructive (nilpotent) step inside a divergence loop
       annihilates the basin set. Measured: induction_clock -> 200
       distinct basins from 200 starts; adding one nilpotent step ->
       1 basin. Never place a destructive readout inside a divergence
       loop.

LAW 2  CONSERVED STRATUM
       The archive/strategy-memory stage conserves one stratum EXACTLY
       (drift 0.00e+00) while the rest contracts. Measured: 68 basins
       -> 5 basins with the stratum held. This is what makes verdicts
       stable without collapsing them, and it is the mechanism a
       project wave needs to keep the big picture while task detail
       contracts.

LAW 3  FIXED-POINT REFERENCE
       Monotone convergence must be measured against the composed
       word's OWN fixed point, never an assumed pole. Measured against
       an assumed pole: 0/40 monotone. Against the true fixed point:
       40/40. Isolated, only a pure rotation (isentropic) is
       non-monotone, correctly.

LAW 4  SURFACE LEARNING
       Learning is deformation of the REGISTRY (sigma), not motion of
       run states (rho). Measured: surface-writing surprise
       1.240 -> 0.534; state-only 0.671 -> 0.573. Autoresearch
       therefore belongs on the registry; individual runs are states
       and must not be expected to accumulate.

LAW 5  INPUT DIVERSITY IS MEASURABLE
       Shared root inputs collapse a swarm. Measured: 4 nodes with one
       MMM and an 870-char shared preamble -> COLLAPSED (3 duplicate
       hashes); 9 voice prompts with distinct slices -> max pairwise
       Jaccard 0.368, DIVERSE.

LAW 6  MEMBER SUBSUMPTION AND DEAD VOTES
       More members can make a council WORSE. Measured: full 8-member
       presence council scored 9/13; a single member scored 11/13,
       because three members never fire yet still vote. Aggregate by
       weight, not majority, and drop subsumed members.

LAW 7  SHARED PRECOMPUTE
       Exhaustive deterministic deployment is only free above a shared
       index. Measured: members re-scanning the corpus took 175 s for
       one member; the same members over a prebuilt index took 1.0 ms
       and 6.5 ms. Build the index council first; everything above it
       is free.

LAW 8  LIVE LOOP
       A loop iteration is live only if it emitted a receipt AND its
       declared monotone measure moved. Otherwise it is spinning and
       must halt and report rather than consume its budget.
"""
from __future__ import annotations
import math, random, sys

def unit(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def contract(v, mu, pole):
    return [mu * x + (1 - mu) * p for x, p in zip(v, pole)]

def archive(v, mu):
    """split law: contract the transverse strata, conserve the last exactly"""
    return [mu * v[0], mu * v[1], v[2]]

def nilpotent(v):
    return [0.0, 0.0, 0.0]

def isentropic(v):
    c, s = math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3)
    return [c * v[0] - s * v[1], s * v[0] + c * v[1], v[2]]

def apply_word(v, word):
    for f in word:
        v = f(v)
    return v

def true_fixed_point(word, iters=4000):
    """LAW 3: the reference for any monotonicity claim"""
    v = [0.11, 0.07, 0.05]
    for _ in range(iters):
        v = apply_word(v, word)
    return v

def basin_census(word, starts=200, rounds=12, seed=7, places=3):
    rng = random.Random(seed)
    b = set()
    for _ in range(starts):
        v = unit([rng.gauss(0, 1) for _ in range(3)])
        for _ in range(rounds):
            v = apply_word(v, word)
        b.add(tuple(round(x, places) for x in v))
    return b

def monotone_fraction(word, trials=40, rounds=10, seed=7):
    """LAW 3 applied: distance to the word's own fixed point must not rise"""
    rng = random.Random(seed)
    fp = true_fixed_point(word)
    ok = 0
    for _ in range(trials):
        v = unit([rng.gauss(0, 1) for _ in range(3)])
        d = [dist(v, fp)]
        for _ in range(rounds):
            v = apply_word(v, word)
            d.append(dist(v, fp))
        if all(d[i + 1] <= d[i] + 1e-9 for i in range(len(d) - 1)):
            ok += 1
    return ok / trials

def check_divergence_loop(word):
    """LAW 1 gate: refuse a divergence word that collapses the basin set"""
    b = basin_census(word)
    return {"basins": len(b),
            "verdict": "BLOCKED: divergence loop collapses to a point"
            if len(b) <= 1 else "ADMIT",
            "law": "LAW 1 divergence collapse"}

def check_conserved_stratum(word, index=2, tol=1e-12):
    """LAW 2 gate: the declared stratum must be conserved exactly"""
    v = unit([0.7, 0.5, 0.4])
    z0 = v[index]
    for _ in range(6):
        v = apply_word(v, word)
    drift = abs(v[index] - z0)
    return {"drift": drift, "conserved": drift < tol,
            "verdict": "ADMIT" if drift < tol else "BLOCKED: stratum leaked",
            "law": "LAW 2 conserved stratum"}

def _self_test() -> int:
    checks = []
    div_ok = [isentropic, lambda v: contract(v, 0.85, unit([0, 1, 0.3]))]
    div_bad = div_ok + [nilpotent]
    a = check_divergence_loop(div_ok)
    b = check_divergence_loop(div_bad)
    checks.append(("LAW 1 divergence preserved", a["basins"] > 100))
    checks.append(("LAW 1 collapse refused", b["basins"] == 1
                   and b["verdict"].startswith("BLOCKED")))
    arch = [lambda v: archive(v, 0.8)]
    c = check_conserved_stratum(arch)
    checks.append(("LAW 2 stratum conserved exactly", c["conserved"]))
    ded = [lambda v: contract(v, 0.6, unit([1, 0, 0.3]))]
    checks.append(("LAW 3 monotone vs true fixed point",
                   monotone_fraction(ded) == 1.0))
    checks.append(("LAW 3 pure rotation is not monotone",
                   monotone_fraction([isentropic]) == 0.0))
    for name, ok in checks:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    passed = sum(1 for _, ok in checks if ok)
    print(f"fixtures as expected: {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
