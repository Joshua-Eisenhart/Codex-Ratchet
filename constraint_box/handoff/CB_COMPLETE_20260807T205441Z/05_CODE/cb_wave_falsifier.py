#!/usr/bin/env python3
"""cb_wave_falsifier — the failure.falsifier ROUTE, run to its contract.

WIZARD_v4_3 declares this parent route with required children and named
outputs. This runs it as a NESTED wave: each required child is itself a
council of subsubagents, and the route's declared outputs are the schema
CB gates against.

  ROUTE   failure.falsifier
  CHILDREN (required)  voice.popper · voice.pushback · voice.feynman ·
                       guard.boundary_check
  OUTPUTS (declared)   killed | open | survived  ·  overclaim correction ·
                       boundary failure  ·  minimal fix

  Layer 2  the four required children
  Layer 3  each child is a council: 2 subsubagents with distinct angles
  Barrier  the Failure council CONSUMES the Decision council's output
           (here: the premortem's failure claims)

CB gates the returned packets against the route's OWN declared outputs.
promotion_allowed=false.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_run import dispatch
from cb_strategy_memory import StrategyMemory

AGENTS = REPO / ".claude" / "agents"
MINI = Path.home() / "wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md"

# layer 2 -> layer 3: each required child is a council of subsubagents
ROUTE = {
 "voice.popper": {
   "voice": "popper",
   "subs": {
     "strongest_falsifier": "Name the single strongest live falsifier: the "
        "observation that would break this claim outright.",
     "decisive_check": "Give the decisive check or evidence path that would "
        "settle it, runnable by a stranger."}},
 "voice.pushback": {
   "voice": "pushback",
   "subs": {
     "overclaim_boundary": "Where exactly does this claim exceed its evidence? "
        "Quote the overreaching part.",
     "corrected_claim": "Restate the claim at the strength the evidence "
        "actually supports."}},
 "voice.feynman": {
   "voice": "feynman",
   "subs": {
     "mechanism": "By what mechanism would this failure actually occur? Name "
        "the operation, not the outcome.",
     "pass_fail": "Give one observable pass/fail check a stranger could run "
        "today."}},
 "guard.boundary_check": {
   "voice": "orwell",
   "subs": {
     "boundary_failure": "Name the boundary this claim crosses without a "
        "declared bridge.",
     "minimal_fix": "Give the smallest change that would make the claim "
        "admissible."}},
}

def leg(p: Path, limit: int):
    if not p.is_file(): return "", "", ""
    b = p.read_bytes()
    return b.decode(errors="ignore")[:limit], str(p), hashlib.sha256(b).hexdigest()

def build_l3(sm, target_claim):
    jobs, comp = [], {}
    for child, spec in ROUTE.items():
        v = spec["voice"]
        st, sp, sh_ = leg(AGENTS / f"voice-{v}.md", 1800)
        mt, mp, mh = leg(MINI / f"MMM_VOICE_{v.upper()}_FULL_v4_1.md", 2200)
        comp[child] = {"agent_spec": {"path": sp, "sha256": sh_},
                       "mini_mmm": {"path": mp, "sha256": mh}}
        for sub, ask in spec["subs"].items():
            jobs.append({"id": f"{child}~{sub}", "prompt":
              f"{sm.preamble()}\n\n=== AGENT SPEC ===\n{st}\n"
              f"=== MINI-MMM SALIENCE ===\n{mt}\n=== END ===\n\n"
              f"ROUTE: failure.falsifier   CHILD: {child}   SUBAGENT: {sub}\n\n"
              f"TARGET CLAIM (from the Decision council):\n{target_claim}\n\n"
              f"{ask}\n\nUnder 45 words. No preamble."})
    return jobs, comp

def build_l2(sm, l3, target_claim):
    """each required child converges its own subsubagents into ONE packet
    carrying the route's declared output fields"""
    jobs = []
    for child in ROUTE:
        body = "\n".join(f"[{k.split('~')[1]}] {v}" for k, v in l3.items()
                         if k.startswith(child + "~"))
        jobs.append({"id": child, "prompt":
          f"{sm.preamble()}\n\nYou are the convergence step of {child} inside "
          f"the failure.falsifier route.\n\nTARGET CLAIM:\n{target_claim}\n\n"
          f"Your subagents returned:\n{body}\n\n"
          f"Return ONLY this JSON object:\n"
          + json.dumps({"status": "open", "overclaim_correction": "<...>",
                        "boundary_failure": "<...>", "minimal_fix": "<...>",
                        "decisive_check": "<...>"})
          + "\nstatus must be exactly one of: killed, open, survived."})
    return jobs

DECLARED = ["status", "overclaim_correction", "boundary_failure",
            "minimal_fix", "decisive_check"]
STATUS = {"killed", "open", "survived"}

def gate_route_packet(raw):
    """gate against the ROUTE's declared outputs, not an invented schema"""
    s = raw.strip(); i, j = s.find("{"), s.rfind("}")
    if i < 0: return None, ["no JSON packet returned"]
    try: pkt = json.loads(s[i:j+1])
    except Exception as e: return None, [f"unparseable packet: {type(e).__name__}"]
    r = [f"missing declared route output: {k}" for k in DECLARED if k not in pkt]
    st = str(pkt.get("status", "")).lower()
    if st not in STATUS:
        r.append(f"status '{pkt.get('status')}' not in killed|open|survived")
    for k in DECLARED:
        v = pkt.get(k)
        if isinstance(v, str) and len(v.strip()) < 8 and k != "status":
            r.append(f"declared output '{k}' is empty or placeholder")
    return pkt, r

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", required=True)
    a = ap.parse_args()
    t0 = time.time()
    sm = StrategyMemory(
        prompt_intent="Falsify the target claim: name the strongest falsifier, "
                      "the overclaim boundary, the boundary failure, the minimal fix.",
        success_condition="each required child returns a packet carrying every "
                          "declared route output, with status in killed|open|survived",
        claim_ceiling="falsification structure only; CB does not decide whether "
                      "the claim is true")
    sm.kill("a claim survives because no one objected")
    sm.note("strategy_state", "Failure council consumes the Decision council's output")

    print("WAVE  failure.falsifier   (Failure council consumes Decision)")
    print(f"  required children: {list(ROUTE)}")
    print(f"  declared outputs : {DECLARED}\n")

    rundir = REPO/"constraint_box"/"receipts"/f"falsifier_{time.strftime('%Y%m%dT%H%M%SZ')}"
    jobs3, comp = build_l3(sm, a.claim)
    print(f"LAYER 3  {len(jobs3)} subsubagents ({len(ROUTE)} children x 2 each)")
    l3, sp3 = dispatch(jobs3, rundir/"L3", timeout=150, conc=4)
    print(f"         spawned {sp3} completed {len(l3)}  count law "
          f"{'holds' if len(l3)<=sp3 else 'VIOLATED'}")
    for k in sorted(l3): print(f"   {k:<42}{' '.join(l3[k].split())[:76]}")

    jobs2 = build_l2(sm, l3, a.claim)
    print(f"\nLAYER 2  {len(jobs2)} required children converge")
    l2, sp2 = dispatch(jobs2, rundir/"L2", timeout=150, conc=4)
    print(f"         spawned {sp2} completed {len(l2)}")

    print(f"\nCB GATE vs the route's declared outputs")
    gated, statuses = {}, []
    for child in ROUTE:
        raw = l2.get(child, "")
        pkt, reasons = gate_route_packet(raw)
        gated[child] = {"packet": pkt, "reasons": reasons}
        st = (pkt or {}).get("status", "—")
        statuses.append(str(st).lower())
        print(f"  {child:<22}{'ADMITTED' if not reasons else 'REFUSED':<10}status={st}")
        for r in reasons[:2]: print(f"        - {r}")
        if pkt and not reasons:
            print(f"        overclaim: {str(pkt.get('overclaim_correction'))[:78]}")
            print(f"        min fix  : {str(pkt.get('minimal_fix'))[:78]}")

    verdict = ("KILLED" if statuses.count("killed") >= 2 else
               "SURVIVED" if statuses and all(s == "survived" for s in statuses)
               else "OPEN")
    print(f"\nROUTE VERDICT (deterministic tally, no model decides): {verdict}")
    print(f"   killed={statuses.count('killed')} open={statuses.count('open')} "
          f"survived={statuses.count('survived')}")

    receipt = {"schema": "cb.wave.failure-falsifier.v1", "target_claim": a.claim,
        "route": "failure.falsifier", "required_children": list(ROUTE),
        "declared_outputs": DECLARED, "composition": comp,
        "L3": {"spawned": sp3, "completed": len(l3), "returns": l3},
        "L2": {"spawned": sp2, "completed": len(l2),
               "gated": {k: {"admitted": not v["reasons"], "reasons": v["reasons"],
                             "packet": v["packet"]} for k, v in gated.items()}},
        "route_verdict": verdict, "tally": {s: statuses.count(s) for s in STATUS},
        "strategy_memory": sm.receipt(), "wall_seconds": round(time.time()-t0,1),
        "promotion_allowed": False,
        "claim_ceiling": "falsification structure and packet shape only"}
    rundir.mkdir(parents=True, exist_ok=True)
    (rundir/"FALSIFIER_WAVE_RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"RECEIPT {rundir.name}/FALSIFIER_WAVE_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
