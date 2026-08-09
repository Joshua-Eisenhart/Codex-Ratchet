#!/usr/bin/env python3
"""cb_wave_decision — the Decision wave. Three councils, nested, gated by code.

Structure, per the owner's build card:

  ROUTE                    REQUIRED CHILDREN (each child is itself a COUNCIL)
  decision.context_strategy  voice.strategy, voice.systems, voice.hume, voice.feynman
  decision.move_selection    voice.factory, voice.orwell, voice.hume,
                             lane.direct, lane.alternative
  decision.evidence_boundary voice.hume, voice.popper, voice.feynman,
                             guard.receipt_audit

Nesting, exactly as cb_wave_falsifier_v2 established it: a child is not one
call. A child is a council of N members who all answer THE SAME question under
different salience, so they CAN disagree and collapse is detectable. Members
default to 5, the conformance floor.

The route then compiles its council answers into the six DECLARED OUTPUTS:

  selected_move, why_now, rejected_alternatives, operating_boundary,
  evidence_boundary, falsifier

and a deterministic gate — code, never a model — admits or refuses that
compilation. The gate does not judge whether the move is good. It judges
whether the answer arrived in a shape that can be checked.

  cb_wave_decision.py --task "..." --dry-run     # structure only, free
  cb_wave_decision.py --task "..."               # dispatches, costs tokens

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, difflib, hashlib, itertools, json, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
import concurrent.futures as cf
from cb_multi_provider import call_lane, provider_diversity, family_of
from cb_strategy_memory import StrategyMemory

# One council seat per LANE. Members then differ by model family AND salience,
# which is the owner's "diverse llms" requirement — five prompts to one model is
# one model in five hats. Verified live on this machine; free unless noted.
DEFAULT_LANES = [
    "nv:meta/llama-3.3-70b-instruct",                 # NVIDIA API, free
    "nv:deepseek-ai/deepseek-v4-flash-0731",          # NVIDIA API, free
    "nv:nvidia/llama-3.3-nemotron-super-49b-v1.5",    # NVIDIA API, free
    "nv:meta/llama-3.1-8b-instruct",                  # NVIDIA API, free, fast
    "nv:nvidia/nemotron-3-nano-30b-a3b",              # NVIDIA API, free, fast
    "nv:openai/gpt-oss-120b",                         # NVIDIA API, free, fast
    "nvidia/nemotron-nano-9b-v2:free",                # OpenRouter, free
    "openai/gpt-oss-20b:free",                        # OpenRouter, free
]
# Verified live on this machine. Catalog membership is NOT availability:
# llama-3.1-nemotron-70b-instruct and mistral-large-2 are listed and 404;
# phi-4-mini, qwen2.5-coder and gemma-3-27b are listed and 410.
COMPILE_LANE = "haiku"   # the compiler must follow a JSON contract; haiku does

AGENTS = REPO / ".claude" / "agents"
MINI = Path.home() / "wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md"

# ------------------------------------------------------------------ structure
# Each child carries ONE question. Its council members all answer that question.
CHILD_Q = {
 "voice.strategy": ("strategy",
   "Name the SINGLE campaign-level consideration that should decide this move."),
 "voice.systems": ("systems",
   "Name the SINGLE feedback loop that this move would enter or disturb."),
 "voice.hume": ("hume",
   "State plainly what is ACTUALLY the case here, using only what is in evidence."),
 "voice.feynman": ("feynman",
   "Name the SINGLE concrete check that would show whether this move worked."),
 "voice.factory": ("factory",
   "Name the SINGLE bottleneck that determines throughput on this move."),
 "voice.orwell": ("orwell",
   "Name the SINGLE phrase in this framing that is hiding a decision."),
 "voice.popper": ("popper",
   "Name the SINGLE strongest falsifier of the move being proposed."),
 "lane.direct": (None,
   "Name the most DIRECT next move: the smallest thing that advances the task now."),
 "lane.alternative": (None,
   "Name the strongest ALTERNATIVE move that a reasonable person would pick instead."),
 "guard.receipt_audit": (None,
   "Name the SINGLE claim here that has no receipt behind it."),
}

ROUTES = {
 "decision.context_strategy": ["voice.strategy", "voice.systems",
                               "voice.hume", "voice.feynman"],
 "decision.move_selection":   ["voice.factory", "voice.orwell", "voice.hume",
                               "lane.direct", "lane.alternative"],
 "decision.evidence_boundary":["voice.hume", "voice.popper", "voice.feynman",
                               "guard.receipt_audit"],
}

SLICES = {
 "literal":     "Read the task at its most literal. Take every word at face value.",
 "operational": "Read the task as an operation to be executed. What actually runs?",
 "adversarial": "Read the task as a hostile auditor looking for the weakest joint.",
 "historical":  "Read the task against how this class of thing has failed before.",
 "boundary":    "Read the task at its edges: the cases just inside and just outside.",
 "cost":        "Read the task as a budget holder. What does this consume, and for what?",
}

DECLARED_OUTPUTS = ["selected_move", "why_now", "rejected_alternatives",
                    "operating_boundary", "evidence_boundary", "falsifier"]

# ------------------------------------------------------------------ helpers
def leg(p: Path, limit: int):
    if not p.is_file():
        return "", ""
    b = p.read_bytes()
    return b.decode(errors="ignore")[:limit], hashlib.sha256(b).hexdigest()[:16]


def build_jobs(sm, task, members, lanes):
    """One job per (route, child, seat). A seat = one salience slice on one lane."""
    jobs, provenance = [], {}
    ci = 0
    for route, children in ROUTES.items():
        for child in children:
            ci += 1
            voice, question = CHILD_Q[child]
            spec = mini = ""
            sh = mh = ""
            if voice:
                spec, sh = leg(AGENTS / f"voice-{voice}.md", 1500)
                mini, mh = leg(MINI / f"MMM_VOICE_{voice.upper()}_FULL_v4_1.md", 1800)
            provenance[f"{route}/{child}"] = {"voice": voice,
                                              "agent_spec_sha": sh, "mini_mmm_sha": mh,
                                              "agent_spec_loaded": bool(spec),
                                              "mini_mmm_loaded": bool(mini)}
            for n, sl in enumerate(members):
                head = ""
                if spec:
                    head += f"=== AGENT SPEC ===\n{spec}\n"
                if mini:
                    head += f"=== MINI-MMM ===\n{mini}\n"
                # Rotate the lane offset per child so 13 councils x 5 seats
                # spread over all lanes instead of hammering the first five.
                jobs.append({"id": f"{route}|{child}|{sl}",
                  "lane": lanes[(ci * len(members) + n) % len(lanes)],
                  "prompt":
                  f"{sm.preamble()}\n\n{head}"
                  f"=== SALIENCE SLICE: {sl} ===\n{SLICES[sl]}\n\n"
                  f"TASK UNDER DECISION:\n{task}\n\n{question}\n\n"
                  f"Answer in ONE sentence under 30 words. State only the answer."})
    return jobs, provenance


def run_jobs(jobs, width=8, retries=3, lanes=None):
    """Dispatch across provider lanes, REASSIGNING dead seats to another lane.

    Free lanes rate-limit under concurrency. A seat lost to a 429 or a read
    timeout is a transport failure, not a member declining to answer, and
    leaving it dead silently under-populates the council. Retrying on the same
    lane just hits the same limit, so each retry moves the seat to the next
    lane and backs off.
    """
    pool = lanes or DEFAULT_LANES

    def one(j):
        r = call_lane(j["lane"], j["prompt"])
        r["id"] = j["id"]; r["lane"] = j["lane"]
        return r

    out = {}
    todo = list(jobs)
    for attempt in range(retries + 1):
        if not todo:
            break
        if attempt:
            time.sleep(4 * attempt)
            for j in todo:                      # move to a different lane
                cur = pool.index(j["lane"]) if j["lane"] in pool else 0
                j["lane"] = pool[(cur + attempt) % len(pool)]
            print(f"      retry {attempt}: {len(todo)} dead seats reassigned")
        with cf.ThreadPoolExecutor(max_workers=width) as ex:
            for r in ex.map(one, todo):
                r["attempt"] = attempt
                out[r["id"]] = r
        todo = [j for j in todo if not out[j["id"]]["ok"]]
    return out


def collapse_check(answers: dict):
    """Did this council's members actually diverge, or is it one voice in five hats?"""
    vals = [" ".join(v.split()).lower() for v in answers.values() if v.strip()]
    if len(vals) < 2:
        return {"members": len(vals), "verdict": "INSUFFICIENT",
                "mean_similarity": None, "distinct_answers": len(set(vals))}
    sims = [difflib.SequenceMatcher(None, a, b).ratio()
            for a, b in itertools.combinations(vals, 2)]
    mean = sum(sims) / len(sims)
    distinct = len(set(vals))
    verdict = ("COLLAPSED: identical answers" if distinct == 1 else
               "COLLAPSED: mean similarity >= 0.85" if mean >= 0.85 else
               "CONVERGENT (agree, not identical)" if mean >= 0.55 else
               "DIVERGENT")
    return {"members": len(vals), "distinct_answers": distinct,
            "mean_similarity": round(mean, 3), "max_similarity": round(max(sims), 3),
            "verdict": verdict}


# ------------------------------------------------------------------ THE GATE
# Deterministic. No model reads this, and no model can argue with it.
MIN_CHARS = {"selected_move": 15, "why_now": 15, "operating_boundary": 15,
             "evidence_boundary": 15, "falsifier": 15}

MEMBER_FLOOR = 5

def gate_compilation(pkt: dict, council_answers: dict, floor=MEMBER_FLOOR) -> dict:
    """Admit or refuse ONE route's compiled output. Reasons are always named."""
    reasons = []

    # A council that lost seats to dead lanes is under-populated. The output can
    # still be well-shaped, so shape alone would admit it — the floor must be
    # its own check or lane failures become invisible.
    for child, ans in council_answers.items():
        if len(ans) < floor:
            reasons.append(f"{child}: {len(ans)} live members, below the "
                           f"conformance floor of {floor}")

    if not isinstance(pkt, dict):
        return {"admitted": False,
                "reasons": reasons + ["compilation is not a JSON object"]}

    for f in DECLARED_OUTPUTS:
        if f not in pkt:
            reasons.append(f"missing declared output: {f}")

    for f, n in MIN_CHARS.items():
        v = pkt.get(f)
        if f in pkt and (not isinstance(v, str) or len(v.strip()) < n):
            reasons.append(f"{f}: shorter than {n} chars or not a string")

    # The owner's requirement: select ONE move while PRESERVING live alternatives.
    ra = pkt.get("rejected_alternatives")
    if "rejected_alternatives" in pkt:
        if not isinstance(ra, list):
            reasons.append("rejected_alternatives: not a list")
        elif len(ra) < 1:
            reasons.append("rejected_alternatives: empty — a selection that "
                           "rejected nothing did not select")
        elif not all(isinstance(x, str) and len(x.strip()) >= 10 for x in ra):
            reasons.append("rejected_alternatives: an entry is empty or under 10 chars")

    # A falsifier that restates the move is not a falsifier.
    sm_, fl = str(pkt.get("selected_move", "")), str(pkt.get("falsifier", ""))
    if sm_ and fl:
        sim = difflib.SequenceMatcher(None, sm_.lower(), fl.lower()).ratio()
        if sim >= 0.75:
            reasons.append(f"falsifier restates selected_move (similarity {sim:.2f})")

    # Traceability: the compilation must touch what its council actually said.
    body = " ".join(" ".join(a.split()).lower()
                    for ans in council_answers.values() for a in ans.values())
    if body:
        toks = {w for w in " ".join(str(pkt.get(f, "")) for f in DECLARED_OUTPUTS)
                .lower().split() if len(w) > 6}
        if toks and not (toks & set(body.split())):
            reasons.append("compilation shares no substantive token with its "
                           "council's answers — not traceable to the council")

    return {"admitted": not reasons, "reasons": reasons}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--members", type=int, default=5,
                    help="council seats per child; floor is 5")
    ap.add_argument("--dry-run", action="store_true",
                    help="build and gate the STRUCTURE without dispatching")
    ap.add_argument("--lanes", default=",".join(DEFAULT_LANES))
    ap.add_argument("--conc", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time()
    lanes = [x.strip() for x in a.lanes.split(",") if x.strip()]

    if a.members < 5:
        print(f"REFUSED: --members {a.members} is below the conformance floor of 5.")
        return 2
    members = list(SLICES)[:a.members]

    sm = StrategyMemory(
        prompt_intent="Select ONE bounded move for the task while preserving live "
                      "alternatives, with the evidence boundary declared.",
        success_condition="each route compiles the six declared outputs and passes "
                          "the deterministic gate",
        claim_ceiling="decision structure only; CB does not decide whether the "
                      "selected move is correct")
    sm.kill("a route is a council because it is named one")
    sm.kill("one model answering four questions is four children")

    n_children = sum(len(v) for v in ROUTES.values())
    print("WAVE decision — 3 routes, nested councils, deterministic gate")
    print(f"  routes {len(ROUTES)}  required children {n_children}  "
          f"members per child {len(members)}")
    print(f"  L3 calls = {n_children} x {len(members)} = {n_children*len(members)}")
    print(f"  members answer the SAME question under: {members}")
    print(f"  lanes ({len(lanes)}): {lanes}\n")

    jobs, prov = build_jobs(sm, a.task, members, lanes)
    missing = [k for k, v in prov.items() if v["voice"] and not v["agent_spec_loaded"]]
    print(f"PROVENANCE  {len(prov)} children, "
          f"{sum(1 for v in prov.values() if v['agent_spec_loaded'])} with agent specs, "
          f"{sum(1 for v in prov.values() if v['mini_mmm_loaded'])} with mini-MMMs")
    if missing:
        print(f"   WARNING missing agent spec for: {missing}")

    rundir = REPO/"constraint_box"/"receipts"/f"decision_{time.strftime('%Y%m%dT%H%M%SZ')}"

    if a.dry_run:
        print(f"\nDRY RUN — {len(jobs)} jobs built, none dispatched.")
        by_route = {r: sum(1 for j in jobs if j["id"].startswith(r+"|")) for r in ROUTES}
        for r, n in by_route.items():
            floor_ok = "OK" if n >= 5 else "BELOW FLOOR"
            print(f"   {r:<30}{n:>3} child receipts would be produced  [{floor_ok}]")
        print(f"   prompt chars: min {min(len(j['prompt']) for j in jobs)}, "
              f"max {max(len(j['prompt']) for j in jobs)}")
        return 0

    # ------------------------------------------------------------ L3 round 1
    raw = run_jobs(jobs, width=a.conc, lanes=lanes)
    live = [r for r in raw.values() if r["ok"]]
    print(f"\nL3  dispatched {len(jobs)}  live {len(live)}  "
          f"count law {'holds' if len(live) <= len(jobs) else 'VIOLATED'}")
    by_lane = {}
    for r in raw.values():
        s = by_lane.setdefault(r["lane"], [0, 0])
        s[0] += 1; s[1] += 1 if r["ok"] else 0
    for ln, (c, o) in by_lane.items():
        print(f"      {ln:<44}{o}/{c} live")
    print()

    councils, collapsed = {}, []
    for route, children in ROUTES.items():
        print(f"{route}")
        councils[route] = {}
        for child in children:
            recs = {k.split("|")[2]: v for k, v in raw.items()
                    if k.startswith(f"{route}|{child}|")}
            ans = {sl: r["text"] for sl, r in recs.items() if r["ok"] and r["text"]}
            cc = collapse_check(ans)
            pd = provider_diversity(list(recs.values()))
            councils[route][child] = {
                "answers": ans, "collapse": cc,
                "seats": {sl: {"lane": r["lane"], "model": r.get("model"),
                               "family": family_of(r), "ok": r["ok"],
                               "sec": r.get("sec"),
                               "error": r.get("error", "")} for sl, r in recs.items()},
                "provider_diversity": pd}
            print(f"   {child:<22}{cc['verdict']:<34}"
                  f"sim {cc.get('mean_similarity')}  n={cc['members']}  "
                  f"families {pd['families']}")
            if cc["verdict"].startswith("COLLAPSED"):
                collapsed.append(f"{route}/{child}")
        print()

    # ------------------------------------------------------- route compilation
    comp_jobs = []
    for route, children in ROUTES.items():
        body = "\n".join(
            f"[{child} / {sl}] {' '.join(v.split())[:200]}"
            for child in children
            for sl, v in councils[route][child]["answers"].items())
        comp_jobs.append({"id": route, "prompt":
          f"{sm.preamble()}\n\nYou are the OUTPUT COMPILER for the {route} route.\n"
          f"Its councils returned:\n{body}\n\nTASK UNDER DECISION:\n{a.task}\n\n"
          f"Compile these into the route's declared outputs. Return ONLY JSON:\n"
          + json.dumps({"selected_move": "<one bounded move>",
                        "why_now": "<one sentence>",
                        "rejected_alternatives": ["<alternative kept alive, not deleted>"],
                        "operating_boundary": "<what this move does NOT touch>",
                        "evidence_boundary": "<what would have to be true, and what is unchecked>",
                        "falsifier": "<what would show this move was wrong — NOT a restatement of it>"})
          + "\nrejected_alternatives must be a non-empty list of real alternatives "
            "you are preserving, not discarding."})

    for j in comp_jobs:
        j["lane"] = COMPILE_LANE
    comp_raw = run_jobs(comp_jobs, width=3)
    comp = {k: r["text"] for k, r in comp_raw.items() if r["ok"]}
    print(f"COMPILE  dispatched {len(comp_jobs)} on {COMPILE_LANE}  "
          f"returned {len(comp)}\n")

    # ---------------------------------------------------------------- the gate
    results = {}
    for route in ROUTES:
        raw = comp.get(route, "")
        i, j = raw.find("{"), raw.rfind("}")
        try:
            pkt = json.loads(raw[i:j+1])
        except Exception:
            pkt = None
        g = gate_compilation(pkt if pkt is not None else {},
                             {c: councils[route][c]["answers"] for c in ROUTES[route]})
        results[route] = {"compiled": pkt, "gate": g}
        print(f"GATE {route}")
        print(f"   {'ADMITTED' if g['admitted'] else 'REFUSED'}")
        for r in g["reasons"]:
            print(f"      - {r}")
        if pkt:
            print(f"      selected_move: {str(pkt.get('selected_move',''))[:90]}")
            print(f"      falsifier    : {str(pkt.get('falsifier',''))[:90]}")
            print(f"      alternatives kept: {len(pkt.get('rejected_alternatives') or [])}")
        print()

    admitted = [r for r, v in results.items() if v["gate"]["admitted"]]
    print(f"{'='*72}")
    print(f"WAVE VERDICT  {len(admitted)}/{len(ROUTES)} routes admitted: {admitted or 'none'}")
    print(f"COLLAPSE      {len(collapsed)}/{n_children} councils collapsed"
          f"{' -> ' + str(collapsed) if collapsed else ' — all diverged'}")

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir/"DECISION_RECEIPT.json").write_text(json.dumps({
        "schema": "cb.wave.decision.v1", "task": a.task,
        "structure": {"routes": list(ROUTES), "children_per_route":
                      {r: len(c) for r, c in ROUTES.items()},
                      "members_per_child": len(members), "slices": members,
                      "l3_calls_planned": len(jobs)},
        "provenance": prov,
        "L3": {"dispatched": len(jobs), "live": len(live),
               "by_lane": {k: {"called": c, "live": o} for k, (c, o) in by_lane.items()}},
        "councils": {r: {c: councils[r][c] for c in ROUTES[r]} for r in ROUTES},
        "compilation": {r: results[r]["compiled"] for r in ROUTES},
        "gate": {r: results[r]["gate"] for r in ROUTES},
        "routes_admitted": admitted, "collapsed_councils": collapsed,
        "strategy_memory": sm.receipt(),
        "wall_seconds": round(time.time()-t0, 1), "promotion_allowed": False,
        "claim_ceiling": "decision structure, council divergence and output shape "
                         "only; CB does not decide whether the move is correct"},
        indent=1, sort_keys=True))
    print(f"RECEIPT {rundir.name}/DECISION_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0 if admitted else 1


if __name__ == "__main__":
    sys.exit(main())
