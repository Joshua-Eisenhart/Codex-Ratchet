#!/usr/bin/env python3
"""cb_wave_falsifier_v2 — layer 3 as REAL councils, not field-splits.

The v1 error: each "subsubcouncil" asked its members DISJOINT questions
(strongest_falsifier, decisive_check). Disjoint questions cannot
disagree, so convergence was concatenation and divergence was zero by
construction. That is a collapsed council wearing the name.

A real subsubcouncil: N members answer THE SAME question under different
salience, so they CAN disagree, convergence is meaningful, and collapse
is detectable.

  L2 child           voice.popper (the route's required child)
  L3 subsubcouncil   5 members, ALL asked popper's question, each under a
                     different sub-slice
  collapse check     if all members return the same answer, the council
                     collapsed (council-collapse-auditor's job)
  debate round 2     fires only where members disagreed

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, difflib, hashlib, itertools, json, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_run import dispatch
from cb_strategy_memory import StrategyMemory

AGENTS = REPO / ".claude" / "agents"
MINI = Path.home() / "wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md"

# each required child = ONE question, answered by N members under different slices
CHILDREN = {
 "voice.popper": ("popper",
   "Name the SINGLE strongest live falsifier for the target claim: the one "
   "observation that would break it outright."),
 "voice.pushback": ("pushback",
   "Name the SINGLE place where the target claim most exceeds its evidence."),
 "voice.feynman": ("feynman",
   "Name the SINGLE mechanism by which the claimed failure would actually occur."),
 "guard.boundary_check": ("orwell",
   "Name the SINGLE boundary the target claim crosses without a declared bridge."),
}
# the sub-slices: different salience, SAME question -> disagreement is possible
SLICES = {
 "literal":    "Read the claim at its most literal. Take every word at face value.",
 "operational":"Read the claim as an operation to be executed. What actually runs?",
 "adversarial":"Read the claim as a hostile auditor looking for the weakest joint.",
 "historical": "Read the claim against how this class of thing has failed before.",
 "boundary":   "Read the claim at its edges: the cases just inside and just outside.",
}

def leg(p, limit):
    if not p.is_file(): return "", ""
    b = p.read_bytes()
    return b.decode(errors="ignore")[:limit], hashlib.sha256(b).hexdigest()

def build_l3(sm, claim, members):
    jobs = {}
    for child, (voice, question) in CHILDREN.items():
        spec, sh = leg(AGENTS / f"voice-{voice}.md", 1500)
        mini, mh = leg(MINI / f"MMM_VOICE_{voice.upper()}_FULL_v4_1.md", 1800)
        for sl in members:
            jobs[f"{child}~{sl}"] = {"id": f"{child}~{sl}", "prompt":
              f"{sm.preamble()}\n\n=== AGENT SPEC ===\n{spec}\n"
              f"=== MINI-MMM ===\n{mini}\n=== SUB-SLICE: {sl} ===\n{SLICES[sl]}\n\n"
              f"TARGET CLAIM:\n{claim}\n\n{question}\n\n"
              f"Answer in ONE sentence under 30 words. State only the answer."}
    return list(jobs.values())

def collapse_check(answers: dict):
    """council-collapse-auditor: did the members actually diverge?"""
    vals = [" ".join(v.split()).lower() for v in answers.values() if v.strip()]
    if len(vals) < 2:
        return {"members": len(vals), "verdict": "INSUFFICIENT"}
    sims = [difflib.SequenceMatcher(None, a, b).ratio()
            for a, b in itertools.combinations(vals, 2)]
    mean = sum(sims) / len(sims); mx = max(sims)
    identical = len({v for v in vals}) == 1
    verdict = ("COLLAPSED: identical answers" if identical else
               "COLLAPSED: mean similarity >= 0.85" if mean >= 0.85 else
               "CONVERGENT (agree, not identical)" if mean >= 0.55 else
               "DIVERGENT")
    return {"members": len(vals), "mean_similarity": round(mean, 3),
            "max_similarity": round(mx, 3), "verdict": verdict,
            "could_disagree": True}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", required=True)
    ap.add_argument("--members", type=int, default=5)
    a = ap.parse_args()
    t0 = time.time()
    members = list(SLICES)[:a.members]
    sm = StrategyMemory(
        prompt_intent="Falsify the target claim. Each required child is a COUNCIL "
                      "whose members answer the same question under different salience.",
        success_condition="each subsubcouncil shows measurable divergence, then converges",
        claim_ceiling="falsification structure only; CB does not decide truth")
    sm.kill("disjoint questions constitute a council")

    print("WAVE failure.falsifier v2 — layer 3 as REAL councils")
    print(f"  {len(CHILDREN)} required children x {len(members)} members "
          f"= {len(CHILDREN)*len(members)} L3 calls")
    print(f"  members answer the SAME question under: {members}\n")

    rundir = REPO/"constraint_box"/"receipts"/f"falsifier2_{time.strftime('%Y%m%dT%H%M%SZ')}"
    jobs = build_l3(sm, a.claim, members)
    l3, sp = dispatch(jobs, rundir/"L3r1", timeout=150, conc=4)
    print(f"L3 round 1  spawned {sp} completed {len(l3)}  count law "
          f"{'holds' if len(l3)<=sp else 'VIOLATED'}\n")

    councils, needs_round2 = {}, []
    for child in CHILDREN:
        ans = {k.split('~')[1]: v for k, v in l3.items() if k.startswith(child+"~")}
        cc = collapse_check(ans)
        councils[child] = {"answers": ans, "collapse": cc}
        print(f"  {child}")
        for sl, v in ans.items():
            print(f"     [{sl:<12}] {' '.join(v.split())[:88]}")
        print(f"     -> {cc['verdict']}  (mean sim {cc.get('mean_similarity')}, "
              f"{cc['members']} members)")
        if cc["verdict"].startswith("DIVERGENT"):
            needs_round2.append(child)
        print()

    print(f"DEBATE ROUND 2 fires for divergent councils: {needs_round2 or 'none'}")
    r2jobs = []
    for child in needs_round2:
        voice, question = CHILDREN[child]
        body = "\n".join(f"[{k}] {' '.join(v.split())[:200]}"
                         for k, v in councils[child]["answers"].items())
        r2jobs.append({"id": f"{child}~round2", "prompt":
          f"{sm.preamble()}\n\nYou are the convergence of the {child} council. "
          f"Its members disagreed:\n{body}\n\nTARGET CLAIM:\n{a.claim}\n\n"
          f"Return ONLY JSON: "
          + json.dumps({"status":"open","chosen":"<the strongest single answer>",
                        "why_it_beats_the_others":"<one sentence>",
                        "retained_rival":"<the answer worth keeping alive>"})
          + "\nstatus in killed|open|survived."})
    r2, sp2 = dispatch(r2jobs, rundir/"L3r2", timeout=150, conc=4) if r2jobs else ({}, 0)
    print(f"   round 2 spawned {sp2} completed {len(r2)}\n")

    statuses = []
    for child, raw in r2.items():
        s = raw.strip(); i, j = s.find("{"), s.rfind("}")
        try: pkt = json.loads(s[i:j+1])
        except Exception: pkt = {}
        statuses.append(str(pkt.get("status","")).lower())
        print(f"  {child.split('~')[0]:<22}status={pkt.get('status','—')}")
        print(f"     chosen : {str(pkt.get('chosen',''))[:92]}")
        print(f"     retained rival: {str(pkt.get('retained_rival',''))[:82]}")

    verdict = ("KILLED" if statuses.count("killed") >= 2 else
               "SURVIVED" if statuses and all(s=="survived" for s in statuses) else "OPEN")
    collapsed = [c for c,v in councils.items() if v["collapse"]["verdict"].startswith("COLLAPSED")]
    print(f"\nROUTE VERDICT (deterministic tally): {verdict}")
    print(f"COLLAPSE AUDIT: {len(collapsed)}/{len(CHILDREN)} subsubcouncils collapsed"
          f"{' -> ' + str(collapsed) if collapsed else ' — all diverged'}")

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir/"FALSIFIER2_RECEIPT.json").write_text(json.dumps({
        "schema":"cb.wave.failure-falsifier.v2","target_claim":a.claim,
        "structure":{"children":len(CHILDREN),"members_per_child":len(members),
                     "l3_calls":len(jobs),"slices":members},
        "L3_round1":{"spawned":sp,"completed":len(l3)},
        "councils":{k:{"collapse":v["collapse"],"answers":v["answers"]}
                    for k,v in councils.items()},
        "round2":{"fired_for":needs_round2,"spawned":sp2,"completed":len(r2)},
        "route_verdict":verdict,"collapsed_councils":collapsed,
        "wall_seconds":round(time.time()-t0,1),"promotion_allowed":False,
        "claim_ceiling":"falsification structure and divergence measurement only"},
        indent=1, sort_keys=True))
    print(f"RECEIPT {rundir.name}/FALSIFIER2_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
