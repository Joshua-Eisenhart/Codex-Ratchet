#!/usr/bin/env python3
"""cb_tiered_dispatch — not every tool every run; some always, some on
disagreement, some by SEEDED RANDOM SPOT-CHECK.

The point: randomness makes the gate un-gameable, and a declared seed
makes it exactly replayable. Selection is stochastic to an adversary and
deterministic to a replayer. No model decides anything.

  TIER 1  always            cheapest earners; the standing council
  TIER 2  on disagreement   fires only when tier 1 splits
  TIER 3  on demand OR
          seeded spot-check expensive members with distinctive powers,
                            sampled at declared rate p

Autoresearch subject: what sampling rate p catches a defect that ONLY a
tier-3 member can see, at what cost per artifact.
promotion_allowed=false.
"""
from __future__ import annotations
import hashlib, json, random, sys, time
from pathlib import Path

# measured costs (ms) from cb_all_tools_council on this machine
COST = {"mpmath":0.03,"numpy":0.05,"rfc8785":1.34,"xxhash":1.54,"portion":4.84,
        "rustworkx":4.99,"maude":5.06,"pysat":7.99,
        "msgspec":11.56,"zstandard":11.50,"lmdb":13.02,"cvc5":17.54,"z3":24.31,
        "icontract":32.42,"jsonschema":38.84,"beartype":66.66,
        "celpy":135.23,"pygit2":160.17,"networkx":174.46,"sympy":204.05,
        "pint":274.83,"deepdiff":392.45}
TIER1 = ["mpmath","numpy","rfc8785","xxhash","portion","rustworkx","maude","pysat"]
TIER2 = ["msgspec","zstandard","lmdb","cvc5","z3","icontract","jsonschema","beartype"]
TIER3 = ["celpy","pygit2","networkx","sympy","pint","deepdiff"]

# ---- artifact generator: some carry a SUBTLE defect only tier 3 can see
def make_artifact(rng, subtle_rate=0.15):
    a = {"schema":"cb.run.v1","verdict":"PARKED","promotion_allowed":False,
         "claim_ceiling":"machinery coverage only","declared":5,"matched":5,
         "entropy_bits":0.81,"modulus":0.70,"budgets":[3,2,4,3,5,2,2],
         "duration":1.5,"duration_unit":"second"}
    kind = "clean"
    r = rng.random()
    if r < 0.10:                       # gross defect: tier 1 sees it
        a["modulus"] = 1.2; kind = "gross"
    elif r < 0.10 + subtle_rate:       # subtle: needs a tier-3 power
        # a semantic drift only a structural differ names, and a unit
        # incoherence only pint catches
        a["duration_unit"] = "meter"; a["_prev_verdict"] = "RELEASED"
        kind = "subtle"
    return a, kind

# ---- member behaviour, abstracted to what each CAN see
def admits(member, kind):
    """True = this member ADMITS the artifact (sees nothing wrong).
    gross  : an obvious defect — every member detects it
    subtle : needs a distinctive tier-3 power — only pint/deepdiff/celpy"""
    if kind == "clean":  return True
    if kind == "gross":  return False                     # all detect
    if kind == "subtle": return member not in ("pint", "deepdiff", "celpy")
    return True

def run_artifact(art, kind, p, rng):
    """tier1 always; tier2 on disagreement; tier3 by seeded spot-check"""
    cost = 0.0; detected = False; used = []
    for m in TIER1:
        cost += COST[m]; used.append(m)
        if not admits(m, kind): detected = True
    if detected:                                   # tier 1 split -> escalate
        for m in TIER2:
            cost += COST[m]; used.append(m)
            if not admits(m, kind): detected = True
    # seeded spot-check of the expensive tier, independent of detection
    for m in TIER3:
        if rng.random() < p:
            cost += COST[m]; used.append(m)
            if not admits(m, kind): detected = True
    return detected, cost, used

def sweep(n=400, seed=20260807):
    print(f"{'p':>6}{'detect gross':>14}{'detect subtle':>15}{'ms/artifact':>13}"
          f"{'tier3 calls':>13}")
    rows=[]
    for p in (0.0,0.02,0.05,0.10,0.20,0.35,0.50,0.75,1.0):
        rng = random.Random(seed)          # SAME seed each arm: replayable
        gd=gt=sd=st=0; tot=0.0; t3=0
        for _ in range(n):
            art, kind = make_artifact(rng)
            det, cost, used = run_artifact(art, kind, p, rng)
            tot += cost; t3 += sum(1 for u in used if u in TIER3)
            if kind=="gross":  gt+=1; gd+=det
            if kind=="subtle": st+=1; sd+=det
        rows.append((p, gd/max(gt,1), sd/max(st,1), tot/n, t3/n))
        print(f"{p:>6.2f}{gd/max(gt,1):>13.0%}{sd/max(st,1):>15.0%}"
              f"{tot/n:>13.1f}{t3/n:>13.2f}")
    return rows

def replay_check(seed=20260807, n=50, p=0.2):
    """the whole point: same seed -> identical member selection"""
    def once():
        rng=random.Random(seed); sel=[]
        for _ in range(n):
            art,kind=make_artifact(rng)
            _,_,used=run_artifact(art,kind,p,rng)
            sel.append(tuple(u for u in used if u in TIER3))
        return sel
    a,b=once(),once()
    c=random.Random(seed+1)
    def other():
        rng=random.Random(seed+1); sel=[]
        for _ in range(n):
            art,kind=make_artifact(rng)
            _,_,used=run_artifact(art,kind,p,rng)
            sel.append(tuple(u for u in used if u in TIER3))
        return sel
    return a==b, a!=other()

def main():
    print("TIERED DISPATCH — seeded spot-checks, no model in the loop\n")
    print(f"TIER 1 always      {len(TIER1)} members, {sum(COST[m] for m in TIER1):.1f} ms")
    print(f"TIER 2 on split    {len(TIER2)} members, {sum(COST[m] for m in TIER2):.1f} ms")
    print(f"TIER 3 spot-check  {len(TIER3)} members, {sum(COST[m] for m in TIER3):.1f} ms\n")
    rows = sweep()
    same, differs = replay_check()
    print(f"\nREPLAYABILITY  same seed -> identical tier-3 selection: {same}")
    print(f"               different seed -> different selection:    {differs}")
    base = [r for r in rows if r[0]==0.0][0]
    full = [r for r in rows if r[0]==1.0][0]
    knee = min((r for r in rows if r[2]>=0.60), key=lambda r:r[3], default=None)
    print(f"\np=0    subtle detection {base[2]:.0%}  at {base[3]:.1f} ms/artifact")
    print(f"p=1    subtle detection {full[2]:.0%}  at {full[3]:.1f} ms/artifact")
    if knee:
        print(f"KNEE   p={knee[0]}  subtle {knee[2]:.0%}  at {knee[3]:.1f} ms/artifact "
              f"({knee[3]/full[3]*100:.0f}% of full cost)")
    out=Path("/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/receipts")/ \
        f"tiered_dispatch_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schema":"cb.tiered-dispatch.v1","seed":20260807,
        "tiers":{"t1":TIER1,"t2":TIER2,"t3":TIER3},
        "sweep":[{"p":r[0],"gross":r[1],"subtle":r[2],"ms":r[3],"t3_calls":r[4]} for r in rows],
        "replayable":same,"promotion_allowed":False}, indent=1))
    print(f"RECEIPT {out.name}")

if __name__=="__main__":
    main()
