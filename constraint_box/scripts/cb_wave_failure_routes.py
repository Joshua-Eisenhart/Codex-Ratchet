#!/usr/bin/env python3
"""cb_wave_failure_routes — the Failure wave, run as ROUTES for the first time.

Two of the three Failure-council parent routes have never run as ROUTES —
a route is a COUNCIL of required children, each itself a council of >=5
members answering the same question under different salience, on different
lanes. `cb_skill_premortem.py` running the premortem SKILL to its own
contract (frame -> raw reasons -> one subagent per reason -> synthesis) is a
different thing and does not satisfy this. This script builds the route:

  ROUTE                       REQUIRED CHILDREN (each child is a COUNCIL)
  failure.premortem           skill.premortem, voice.hume, voice.factory,
                               voice.systems
  failure.loophole_auditor    skill.loophole_auditor, voice.strategy,
                               voice.systems, voice.hume

Required-children provenance (recorded plainly, not smoothed over): the two
docs named in the build card — NESTED_COUNCILS_FULL_ENUMERATION_20260806.md
and COUNCIL_MEMBER_CATALOG_20260806.md — enumerate ALL possible members by
kind but carry no per-route required-children table. The table above is
read from two sibling CB docs in the same directory, same date, which DO
carry it: WIZARD_V4_3_ACTUAL_STRUCTURE_20260806.md (the ASCII council tree)
and WIZARD_V4_3_READ_FROM_PACKET_20260806.md (the same set in prose, plus
each route's declared outputs). Those two agree with each other. They
DISAGREE with the raw packet-local agent-spec files at
~/wiki/wizard/packet-v4-3-current/agents/parents/failure.premortem.md
(child/subagent set: premortem-agent, voice.factory, voice.systems — no
hume) and failure.loophole_auditor.md (child/subagent set: loophole-auditor,
council-collapse-auditor, route-truth-agent — machinery/auditor agents, not
evaluative voices at all). That divergence is not reconciled here; this
build follows the CB-docs version because it is the one that names
evaluative children capable of answering a salience-diverse question, which
is what a council member under this harness must do. The packet-spec
version is left as an open finding, not silently dropped.

failure.premortem asks: assume this already failed — what killed it?
failure.loophole_auditor asks: where can this be satisfied without being
true? Its job is to find the by-construction pass, the gate that cannot
fail, the control that measures nothing — the owner's own framing, and the
reason an empty `loopholes` or `failure_modes` list is refused below rather
than admitted: a gate that let "found nothing" pass silently would itself
be exactly the kind of gate this route exists to catch.

The wave compiles ONE packet across both routes (the declared outputs are
wave-level, not per-route, per the build card):

  failure_modes (list), earliest_warning_sign, loopholes (list),
  gate_that_cannot_fail (or null), falsifier

and a deterministic gate — code, never a model — admits or refuses it. The
gate does not judge whether the findings are right. It judges whether they
arrived in a shape that can be checked, with a live council behind them.

  cb_wave_failure_routes.py --target "..." --dry-run   # structure only, free
  cb_wave_failure_routes.py --target "..."             # dispatches, costs tokens

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, difflib, json, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_wave_decision import (leg, run_jobs, collapse_check, DEFAULT_LANES,
                               COMPILE_LANE, AGENTS, MINI, SLICES, MEMBER_FLOOR)
from cb_multi_provider import provider_diversity, family_of
from cb_strategy_memory import StrategyMemory

PREMORTEM_SKILL = Path.home() / ".codex/skills/premortem/SKILL.md"
LOOPHOLE_SKILL = (Path.home() / "wiki/wizard/packet-v4-3-current/skills/"
                  "council-members/loophole-auditor/SKILL.md")

ROUTES = {
 "failure.premortem": ["skill.premortem", "voice.hume", "voice.factory",
                       "voice.systems"],
 "failure.loophole_auditor": ["skill.loophole_auditor", "voice.strategy",
                              "voice.systems", "voice.hume"],
}

# Each route frames the SAME target under a different question. A child's
# own question is scoped inside its route's frame, not a bare restatement of
# it — that is how skill.premortem differs from voice.hume even though both
# sit in the same route.
ROUTE_FRAME = {
 "failure.premortem": ("PREMORTEM FRAME: assume the target below already "
   "failed. It is done. Look back and say exactly what killed it."),
 "failure.loophole_auditor": ("LOOPHOLE FRAME: ask where the target below "
   "could be marked satisfied WITHOUT actually being true — the "
   "by-construction pass, the gate that cannot fail, the control that "
   "measures nothing."),
}

CHILD_SPEC = {
 "failure.premortem": {
  "skill.premortem": {"kind": "skill", "path": PREMORTEM_SKILL,
    "question": "Following the premortem procedure, write the SINGLE most "
                "concrete failure story: how did the target actually die? "
                "One sentence, specific to the target, not generic."},
  "voice.hume": {"kind": "voice", "voice": "hume",
    "question": "State plainly, using only what is in evidence, the ONE "
                "fact about the target that makes this failure most "
                "likely."},
  "voice.factory": {"kind": "voice", "voice": "factory",
    "question": "Name the SINGLE bottleneck or handoff in the target most "
                "likely to have broken first."},
  "voice.systems": {"kind": "voice", "voice": "systems",
    "question": "Name the SINGLE feedback loop in the target whose "
                "breakdown would explain this failure."},
 },
 "failure.loophole_auditor": {
  "skill.loophole_auditor": {"kind": "skill", "path": LOOPHOLE_SKILL,
    "question": "Running the confidence loop — are you 100% confident? — "
                "name the SINGLE loophole: where the target could be marked "
                "satisfied without actually being true."},
  "voice.strategy": {"kind": "voice", "voice": "strategy",
    "question": "Name the SINGLE sequencing or priority loophole: where "
                "satisfying the letter of the target would skip its actual "
                "goal."},
  "voice.systems": {"kind": "voice", "voice": "systems",
    "question": "Name the SINGLE feedback loop in the target that could be "
                "gamed to look closed while nothing actually changed."},
  "voice.hume": {"kind": "voice", "voice": "hume",
    "question": "State plainly, using only what is in evidence, the ONE "
                "control in the target that measures nothing."},
 },
}

DECLARED_OUTPUTS = ["failure_modes", "earliest_warning_sign", "loopholes",
                    "gate_that_cannot_fail", "falsifier"]
MIN_ITEM_CHARS = 15
MIN_CHARS = {"earliest_warning_sign": MIN_ITEM_CHARS, "falsifier": MIN_ITEM_CHARS}


# ------------------------------------------------------------------ helpers
def build_jobs(sm, target, members, lanes):
    """One job per (route, child, seat). A seat = one salience slice on one
    lane. Mirrors cb_wave_decision.build_jobs; the head text loads either a
    voice spec (+mini-MMM) or a skill file, and the route's frame is
    injected ahead of the target so premortem and loophole framings do not
    collapse into one generic question the way decision's routes share a
    single "task under decision" framing."""
    jobs, provenance = [], {}
    ci = 0
    for route, children in ROUTES.items():
        for child in children:
            ci += 1
            spec = CHILD_SPEC[route][child]
            head, sh, mh, loaded = "", "", "", False
            if spec["kind"] == "voice":
                voice = spec["voice"]
                vtext, sh = leg(AGENTS / f"voice-{voice}.md", 1500)
                mtext, mh = leg(MINI / f"MMM_VOICE_{voice.upper()}_FULL_v4_1.md", 1800)
                if vtext:
                    head += f"=== AGENT SPEC ===\n{vtext}\n"
                if mtext:
                    head += f"=== MINI-MMM ===\n{mtext}\n"
                loaded = bool(vtext)
                source = str(AGENTS / f"voice-{voice}.md")
            else:
                stext, sh = leg(spec["path"], 2200)
                if stext:
                    head += f"=== SKILL ===\n{stext}\n"
                loaded = bool(stext)
                source = str(spec["path"])
            provenance[f"{route}/{child}"] = {"kind": spec["kind"],
                "source": source, "spec_sha256_16": sh, "mini_mmm_sha256_16": mh,
                "loaded": loaded}
            for n, sl in enumerate(members):
                jobs.append({"id": f"{route}|{child}|{sl}",
                  "lane": lanes[(ci * len(members) + n) % len(lanes)],
                  "prompt":
                  f"{sm.preamble()}\n\n{head}"
                  f"=== SALIENCE SLICE: {sl} ===\n{SLICES[sl]}\n\n"
                  f"{ROUTE_FRAME[route]}\n\n"
                  f"TARGET UNDER FAILURE AUDIT:\n{target}\n\n{spec['question']}\n\n"
                  f"Answer in ONE sentence under 30 words. State only the answer."})
    return jobs, provenance


def build_compile_prompt(sm, target, councils):
    parts = []
    for route, children in ROUTES.items():
        parts.append(f"--- {route} ---")
        for child in children:
            for sl, v in councils[route][child]["answers"].items():
                parts.append(f"[{route}/{child} / {sl}] {' '.join(v.split())[:200]}")
    body = "\n".join(parts)
    schema = {"failure_modes": ["<concrete failure mode, grounded in the "
                                "councils above>", "..."],
              "earliest_warning_sign": "<the single earliest observable sign "
                                       "any failure mode above is starting>",
              "loopholes": ["<concrete loophole: how the target could pass "
                            "without being true, grounded in the councils "
                            "above>", "..."],
              "gate_that_cannot_fail": "<name the decorative control/gate "
                                       "found by the councils above, or null "
                                       "if none was named>",
              "falsifier": "<the single observation that would show these "
                           "findings are WRONG — not a restatement of them>"}
    return (f"{sm.preamble()}\n\nYou are the OUTPUT COMPILER for the FAILURE "
      f"WAVE (failure.premortem + failure.loophole_auditor). Its councils "
      f"returned:\n{body}\n\nTARGET UNDER FAILURE AUDIT:\n{target}\n\n"
      f"Compile these into the wave's declared outputs. Return ONLY JSON:\n"
      + json.dumps(schema)
      + "\nfailure_modes and loopholes MUST be non-empty lists drawn from the "
        "councils above — an audit that found nothing did not audit. "
        "gate_that_cannot_fail must be the JSON literal null ONLY if no "
        "council member above named a by-construction pass; otherwise name "
        "the one they named.")


# ------------------------------------------------------------------ THE GATE
def gate_failure_compilation(pkt: dict, councils: dict, floor=MEMBER_FLOOR) -> dict:
    """Admit or refuse the wave's compiled output. Reasons are always named."""
    reasons = []

    for route, children in ROUTES.items():
        for child in children:
            ans = councils[route][child]["answers"]
            if len(ans) < floor:
                reasons.append(f"{route}/{child}: {len(ans)} live members, "
                               f"below the conformance floor of {floor}")

    if not isinstance(pkt, dict):
        return {"admitted": False,
                "reasons": reasons + ["compilation is not a JSON object"]}

    for f in DECLARED_OUTPUTS:
        if f not in pkt:
            reasons.append(f"missing declared output: {f}")

    fm = pkt.get("failure_modes")
    if "failure_modes" in pkt:
        if not isinstance(fm, list):
            reasons.append("failure_modes: not a list")
        elif len(fm) < 1:
            reasons.append("failure_modes: empty — a premortem that found no "
                           "failure mode did not run")
        elif not all(isinstance(x, str) and len(x.strip()) >= MIN_ITEM_CHARS
                     for x in fm):
            reasons.append(f"failure_modes: an entry is empty or under "
                           f"{MIN_ITEM_CHARS} chars")

    lp = pkt.get("loopholes")
    if "loopholes" in pkt:
        if not isinstance(lp, list):
            reasons.append("loopholes: not a list")
        elif len(lp) < 1:
            reasons.append("loopholes: empty — an audit that found no "
                           "loophole did not audit")
        elif not all(isinstance(x, str) and len(x.strip()) >= MIN_ITEM_CHARS
                     for x in lp):
            reasons.append(f"loopholes: an entry is empty or under "
                           f"{MIN_ITEM_CHARS} chars")

    for f, n in MIN_CHARS.items():
        v = pkt.get(f)
        if f in pkt and (not isinstance(v, str) or len(v.strip()) < n):
            reasons.append(f"{f}: shorter than {n} chars or not a string")

    # null is a legitimate "no by-construction pass found" answer; a present
    # non-null value must still be a real string, not a token.
    if "gate_that_cannot_fail" in pkt:
        gcf = pkt["gate_that_cannot_fail"]
        if gcf is not None and (not isinstance(gcf, str)
                                or len(gcf.strip()) < MIN_ITEM_CHARS):
            reasons.append(f"gate_that_cannot_fail: present but shorter than "
                           f"{MIN_ITEM_CHARS} chars or not a string (use "
                           f"null if none was found)")

    # a falsifier that restates the finding it is meant to test is not one
    fl = str(pkt.get("falsifier", ""))
    if fl and isinstance(fm, list) and fm:
        sim = difflib.SequenceMatcher(None, str(fm[0]).lower(), fl.lower()).ratio()
        if sim >= 0.75:
            reasons.append(f"falsifier restates failure_modes[0] "
                           f"(similarity {sim:.2f})")
    if fl and isinstance(lp, list) and lp:
        sim = difflib.SequenceMatcher(None, str(lp[0]).lower(), fl.lower()).ratio()
        if sim >= 0.75:
            reasons.append(f"falsifier restates loopholes[0] "
                           f"(similarity {sim:.2f})")

    # traceability: the compilation must touch what its councils actually said
    body = " ".join(" ".join(a.split()).lower()
                    for route in ROUTES for child in ROUTES[route]
                    for a in councils[route][child]["answers"].values())
    if body:
        flat = []
        for f in DECLARED_OUTPUTS:
            v = pkt.get(f)
            flat.append(" ".join(v) if isinstance(v, list) else str(v or ""))
        toks = {w for w in " ".join(flat).lower().split() if len(w) > 6}
        if toks and not (toks & set(body.split())):
            reasons.append("compilation shares no substantive token with its "
                           "councils' answers — not traceable to the councils")

    return {"admitted": not reasons, "reasons": reasons}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True,
                    help="the plan/claim/system under failure audit")
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
        prompt_intent="Run failure.premortem and failure.loophole_auditor as "
                      "ROUTES — councils of required children, not the "
                      "premortem SKILL's own procedure — against one target, "
                      "and compile the wave's declared findings.",
        success_condition="both routes' councils meet the member floor and "
                          "the compiled packet passes the deterministic gate",
        claim_ceiling="failure-wave structure, council divergence and output "
                      "shape only; CB does not decide whether the failure "
                      "modes or loopholes found are correct")
    sm.kill("a route is a council because it is named one")
    sm.kill("an empty failure_modes or loopholes list is a clean audit result")
    sm.kill("running the premortem SKILL's own contract is the same as "
           "running the failure.premortem ROUTE")

    n_children = sum(len(v) for v in ROUTES.values())
    print("WAVE failure_routes — 2 routes, nested councils, deterministic gate")
    print(f"  routes {len(ROUTES)}  required children {n_children}  "
          f"members per child {len(members)}")
    print(f"  L3 calls = {n_children} x {len(members)} = {n_children*len(members)}")
    print(f"  members answer the SAME question under: {members}")
    print(f"  lanes ({len(lanes)}): {lanes}\n")

    jobs, prov = build_jobs(sm, a.target, members, lanes)
    missing = [k for k, v in prov.items() if not v["loaded"]]
    print(f"PROVENANCE  {len(prov)} children, "
          f"{sum(1 for v in prov.values() if v['loaded'])} with source loaded")
    for k, v in prov.items():
        print(f"   {k:<40}{v['kind']:<7}{'loaded' if v['loaded'] else 'MISSING'}"
              f"  {v['source']}")
    if missing:
        print(f"   WARNING missing source for: {missing}")

    rundir = (REPO / "constraint_box" / "receipts" /
             f"failure_routes_{time.strftime('%Y%m%dT%H%M%SZ')}")

    if a.dry_run:
        print(f"\nDRY RUN — {len(jobs)} jobs built, none dispatched.")
        by_route = {r: sum(1 for j in jobs if j["id"].startswith(r + "|"))
                   for r in ROUTES}
        for r, n in by_route.items():
            floor_ok = "OK" if n >= 5 * len(ROUTES[r]) else "BELOW FLOOR"
            print(f"   {r:<30}{n:>3} child receipts would be produced "
                  f"across {len(ROUTES[r])} children  [{floor_ok}]")
        print(f"   prompt chars: min {min(len(j['prompt']) for j in jobs)}, "
              f"max {max(len(j['prompt']) for j in jobs)}")
        print(f"   compile lane: {COMPILE_LANE}  (JSON-contract compile step "
              f"only, per the cost rule)")
        return 0

    # ------------------------------------------------------------ L3 round 1
    raw = run_jobs(jobs, width=a.conc, lanes=lanes)
    live = [r for r in raw.values() if r["ok"]]
    print(f"\nL3  dispatched {len(jobs)}  live {len(live)}  "
          f"count law {'holds' if len(live) <= len(jobs) else 'VIOLATED'}")
    by_lane = {}
    for r in raw.values():
        s = by_lane.setdefault(r["lane"], [0, 0])
        s[0] += 1
        s[1] += 1 if r["ok"] else 0
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

    # ------------------------------------------------------- wave compilation
    comp_prompt = build_compile_prompt(sm, a.target, councils)
    comp_jobs = [{"id": "failure_wave", "lane": COMPILE_LANE, "prompt": comp_prompt}]
    comp_raw = run_jobs(comp_jobs, width=1)
    comp = {k: r["text"] for k, r in comp_raw.items() if r["ok"]}
    print(f"COMPILE  dispatched 1 on {COMPILE_LANE}  returned {len(comp)}\n")

    raw_comp = comp.get("failure_wave", "")
    i, j = raw_comp.find("{"), raw_comp.rfind("}")
    try:
        pkt = json.loads(raw_comp[i:j + 1])
    except Exception:
        pkt = None

    gate = gate_failure_compilation(pkt if pkt is not None else {}, councils)
    print(f"GATE failure_wave")
    print(f"   {'ADMITTED' if gate['admitted'] else 'REFUSED'}")
    for r in gate["reasons"]:
        print(f"      - {r}")
    if pkt:
        print(f"      failure_modes ({len(pkt.get('failure_modes') or [])}): "
              f"{str((pkt.get('failure_modes') or [''])[0])[:80]}")
        print(f"      earliest_warning_sign: "
              f"{str(pkt.get('earliest_warning_sign', ''))[:80]}")
        print(f"      loopholes ({len(pkt.get('loopholes') or [])}): "
              f"{str((pkt.get('loopholes') or [''])[0])[:80]}")
        print(f"      gate_that_cannot_fail: "
              f"{str(pkt.get('gate_that_cannot_fail'))[:80]}")
        print(f"      falsifier: {str(pkt.get('falsifier', ''))[:80]}")
    print()

    print(f"{'='*72}")
    print(f"WAVE VERDICT  {'ADMITTED' if gate['admitted'] else 'REFUSED'}")
    print(f"COLLAPSE      {len(collapsed)}/{n_children} councils collapsed"
          f"{' -> ' + str(collapsed) if collapsed else ' — all diverged'}")

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir / "FAILURE_ROUTES_RECEIPT.json").write_text(json.dumps({
        "schema": "cb.wave.failure_routes.v1", "target": a.target,
        "structure": {"routes": list(ROUTES), "children_per_route":
                      {r: len(c) for r, c in ROUTES.items()},
                      "members_per_child": len(members), "slices": members,
                      "l3_calls_planned": len(jobs)},
        "required_children_provenance": {
            "docs_named_in_build_card": [
                "docs/NESTED_COUNCILS_FULL_ENUMERATION_20260806.md",
                "docs/COUNCIL_MEMBER_CATALOG_20260806.md"],
            "note": "those two enumerate members by kind but carry no "
                   "per-route required-children table; the table used here "
                   "is read from sibling same-day docs "
                   "WIZARD_V4_3_ACTUAL_STRUCTURE_20260806.md and "
                   "WIZARD_V4_3_READ_FROM_PACKET_20260806.md, which agree "
                   "with each other and diverge from the packet-local agent "
                   "specs at "
                   "wiki/wizard/packet-v4-3-current/agents/parents/"
                   "failure.premortem.md and failure.loophole_auditor.md "
                   "(unreconciled, named as an open finding)"},
        "provenance": prov,
        "L3": {"dispatched": len(jobs), "live": len(live),
               "by_lane": {k: {"called": c, "live": o}
                          for k, (c, o) in by_lane.items()}},
        "councils": councils,
        "compilation": pkt, "gate": gate, "collapsed_councils": collapsed,
        "strategy_memory": sm.receipt(),
        "wall_seconds": round(time.time() - t0, 1), "promotion_allowed": False,
        "claim_ceiling": "failure-wave structure, council divergence and "
                         "output shape only; CB does not decide whether the "
                         "findings are correct"},
        indent=1, sort_keys=True))
    print(f"RECEIPT {rundir.name}/FAILURE_ROUTES_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0 if gate["admitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
