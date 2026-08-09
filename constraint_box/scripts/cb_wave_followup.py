#!/usr/bin/env python3
"""cb_wave_followup — the Follow-Up wave. Three routes, nested councils,
a deterministic gate, and a LANE COVERAGE TEST that can fail.

Structure, per the owner's build card:

  ROUTE                          WHAT IT DOES
  follow_up.next_move_selector   councils PROPOSE candidate follow-up options
                                  for the task, blind to the 5-lane taxonomy
  follow_up.lane_builder         5 children, one per lane (direct, alternative,
                                  reframe, back, wildcard), each builds that
                                  lane's next prompt
  follow_up.compile_gate         a DETERMINISTIC classifier (code, not a model)
                                  maps every candidate option from
                                  next_move_selector onto 0, 1, or many lanes;
                                  the gate REFUSES this route if any option
                                  maps to ZERO lanes

This is a pipeline, not three parallel lenses on one decision the way
cb_wave_decision's three routes are. The nesting shape is copied exactly
(a child is a council of >=5 members answering the SAME question under
different salience, on different lanes; the member-floor check; collapse
detection; provider diversity; a deterministic gate that names its
reasons); the per-route field list is NOT copied verbatim from
cb_wave_decision because the three routes here do genuinely different
jobs in sequence, and the task's own declared outputs (next_prompts,
lane_assignment, uncovered_options, compiled_work) are a flat set for
the WHOLE WAVE, not six repeated fields per route.

THE OPEN QUESTION this build exists to test (owner, verbatim intent):
"whether five lanes cover the option space -- build a test where an
option maps to zero lanes."

The classifier is keyword // shape rules over the candidate option TEXT,
written in this file, run in Python, never asked of a model. A model
generates candidate options (blind to the lane names); code alone decides
which lanes, if any, each option lands in. A fixed self-test
(classifier_self_test, below) proves on hardcoded fixtures that the
classifier CAN return zero lanes and CAN return more than one lane for
the SAME rule set -- if that self-test ever goes all-PASS-into-1-lane,
the classifier has decayed into the by-construction defect this project
keeps finding, and the receipt says so plainly.

  cb_wave_followup.py --task "..." --dry-run     # structure only, free
  cb_wave_followup.py --task "..."                # dispatches, costs tokens

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, difflib, itertools, json, re, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_multi_provider import provider_diversity
from cb_strategy_memory import StrategyMemory
from cb_wave_decision import (DEFAULT_LANES, COMPILE_LANE, AGENTS, MINI,
                               SLICES, leg, run_jobs, collapse_check,
                               MEMBER_FLOOR)

LANE_NAMES = ["direct", "alternative", "reframe", "back", "wildcard"]

LANE_QUESTION = {
 "direct":      "Name the most DIRECT next move: the smallest bounded action "
                "that advances the task right now, with no detour.",
 "alternative": "Name the strongest ALTERNATIVE next move: a genuinely "
                "different path a reasonable person would pick instead of "
                "the direct one.",
 "reframe":     "REFRAME the task: state a different question that, if "
                "asked instead, would change what counts as progress here.",
 "back":        "Name the BACK move: what earlier step or assumption in "
                "this task should be revisited or undone before going "
                "further.",
 "wildcard":    "Name a WILDCARD move: an orthogonal, high-uncertainty "
                "option unrelated to the direct/alternative/back path, "
                "worth a small bet.",
}

# ------------------------------------------------------------------ structure
# next_move_selector children: PROPOSE raw candidate options. Deliberately
# NOT told about the five lanes -- if the prompt named the taxonomy, every
# answer would trivially self-sort and the coverage test could never fail.
# compile_gate children: AUDIT the compiled coverage result, not generate it.
CHILD_Q = {
 "voice.zhuangzi": ("zhuangzi",
   "Name ONE candidate follow-up for this task that a completely different "
   "way of thinking about it would suggest. One short phrase, no preamble."),
 "voice.strategy": ("strategy",
   "Name ONE candidate follow-up that a campaign-level view of this task "
   "would pick next. One short phrase, no preamble."),
 "voice.factory": ("factory",
   "Name ONE candidate follow-up that would relieve this task's single "
   "biggest bottleneck. One short phrase, no preamble."),
 "voice.systems": ("systems",
   "Name ONE candidate follow-up that would change the single feedback "
   "loop this task currently sits inside. One short phrase, no preamble."),
 "voice.orwell": ("orwell",
   "Name ONE candidate follow-up that would expose a decision this task's "
   "framing is currently hiding. One short phrase, no preamble."),
 "voice.hume": ("hume",
   "State plainly what is ACTUALLY the case about this coverage result, "
   "using only what is in evidence. One sentence."),
 "voice.popper": ("popper",
   "Name the SINGLE strongest falsifier of the claim that five lanes "
   "cover this task's option space."),
 "voice.feynman": ("feynman",
   "Name the SINGLE concrete check that would show whether the lane "
   "coverage result can be trusted."),
 "guard.receipt_audit": (None,
   "Name the SINGLE claim in this follow-up work that has no receipt "
   "behind it."),
 "lane.direct":      (None, LANE_QUESTION["direct"]),
 "lane.alternative": (None, LANE_QUESTION["alternative"]),
 "lane.reframe":     (None, LANE_QUESTION["reframe"]),
 "lane.back":        (None, LANE_QUESTION["back"]),
 "lane.wildcard":    (None, LANE_QUESTION["wildcard"]),
}

ROUTES = {
 "follow_up.next_move_selector": ["voice.zhuangzi", "voice.strategy",
                                   "voice.factory", "voice.systems",
                                   "voice.orwell"],
 "follow_up.lane_builder": ["lane.direct", "lane.alternative",
                             "lane.reframe", "lane.back", "lane.wildcard"],
 "follow_up.compile_gate": ["voice.hume", "voice.popper", "voice.feynman",
                             "guard.receipt_audit"],
}

DECLARED_OUTPUTS = ["next_prompts", "lane_assignment", "uncovered_options",
                    "compiled_work"]

# ---------------------------------------------------------- the classifier
# Keyword // shape rules. An option matches a lane if any of its patterns
# hit. Deliberately specific, not catch-all -- free text about a task will
# often hit none of these, which is exactly what lets the test fail.
LANE_KEYWORDS = {
 "direct":      [r"\bimmediately\b", r"\bright now\b", r"\bnext step\b",
                 r"\bsmallest\b", r"\bdirectly\b", r"\bcontinue\b",
                 r"\bproceed\b", r"\bfinish\b", r"\bexecute\b", r"\bnow\b"],
 "alternative": [r"\binstead\b", r"\balternative\b", r"\brather than\b",
                 r"\banother (option|path|approach|way)\b", r"\bswap\b",
                 r"\bdifferent approach\b", r"\bpivot to\b"],
 "reframe":     [r"\breframe\b", r"\bredefine\b", r"\brecast\b",
                 r"\brename\b", r"\bthe real question\b", r"\bwrong "
                 r"question\b", r"\bask instead\b", r"\bchange the "
                 r"(question|framing|goal)\b"],
 "back":        [r"\bback\b", r"\brevert\b", r"\bundo\b", r"\bprevious\b",
                 r"\bearlier\b", r"\breturn to\b", r"\bre-?examine\b",
                 r"\brevisit\b", r"\brewind\b", r"\bprior step\b"],
 "wildcard":    [r"\bwildcard\b", r"\bunrelated\b", r"\borthogonal\b",
                 r"\blong shot\b", r"\bout of left field\b", r"\brandom\b",
                 r"\bunexpected\b", r"\bcompletely different\b",
                 r"\bexperiment(al)?\b"],
}
LANE_PATTERNS = {lane: [re.compile(p, re.I) for p in pats]
                 for lane, pats in LANE_KEYWORDS.items()}


def classify_option(text: str) -> list:
    """CODE, not a model. Returns the sorted lanes an option's TEXT hits.
    Can return [] (zero lanes) or >1 lane for the same fixed rule set."""
    return sorted(lane for lane, pats in LANE_PATTERNS.items()
                 if any(p.search(text) for p in pats))


# Hardcoded fixtures, not live model output. Proves the classifier is not
# rigged to always find a lane -- one fixture MUST classify to zero lanes
# and one MUST classify to more than one, on this exact rule set.
SELF_TEST_FIXTURES = [
 ("keep monitoring the existing dashboard on the usual weekly cadence", []),
 ("take the next step right now and nothing else", ["direct"]),
 ("instead of that, revert to the earlier framing", ["alternative", "back"]),
 ("try a wildcard, completely different experiment", ["wildcard"]),
 ("reframe the real question before doing anything else", ["reframe"]),
]

def classifier_self_test() -> dict:
    checks = []
    for text, expect in SELF_TEST_FIXTURES:
        got = classify_option(text)
        checks.append({"text": text, "expect": expect, "got": got,
                       "pass": got == expect})
    zero_seen = any(c["got"] == [] for c in checks)
    multi_seen = any(len(c["got"]) > 1 for c in checks)
    all_pass = all(c["pass"] for c in checks)
    return {"checks": checks, "all_fixtures_pass": all_pass,
            "proves_zero_lane_possible": zero_seen,
            "proves_multi_lane_possible": multi_seen,
            "classifier_can_fail": zero_seen and all_pass}


def normalize_option(text: str) -> str:
    """Strip bullets/quotes/markup a model tends to prepend, cap length,
    collapse whitespace. Deterministic harvesting, no model call."""
    t = " ".join(text.split())
    t = re.sub(r'^[\-\*\d\.\)\s"\'•]+', "", t)
    t = t.strip(' "\'')
    if len(t) > 160:
        t = t[:160].rsplit(" ", 1)[0]
    return t


def harvest_options(council: dict) -> list:
    """Pull every live answer across a route's children into a deduped
    list of candidate option strings. CODE, no model call -- the mapping
    downstream (classify_option) must not be the only thing kept honest;
    the harvesting that feeds it is code too."""
    seen, out = set(), []
    for child in council.values():
        for text in child["answers"].values():
            opt = normalize_option(text)
            key = opt.lower()
            if opt and key not in seen:
                seen.add(key)
                out.append(opt)
    return out


# ------------------------------------------------------------------ build
def build_jobs(sm, task, members, lanes):
    """One job per (route, child, seat). A seat = one salience slice on
    one lane. Mirrors cb_wave_decision.build_jobs exactly."""
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
                jobs.append({"id": f"{route}|{child}|{sl}",
                  "lane": lanes[(ci * len(members) + n) % len(lanes)],
                  "prompt":
                  f"{sm.preamble()}\n\n{head}"
                  f"=== SALIENCE SLICE: {sl} ===\n{SLICES[sl]}\n\n"
                  f"TASK:\n{task}\n\n{question}\n\n"
                  f"Answer in ONE sentence under 30 words. State only the answer."})
    return jobs, provenance


# ------------------------------------------------------------------ THE GATE
# Deterministic. No model reads this, and no model can argue with it.

def gate_route(route: str, pkt, council_answers: dict, floor=MEMBER_FLOOR,
              uncovered=None, n_options=0) -> dict:
    """Admit or refuse ONE route's compiled output. Reasons always named.

    Field shape differs per route (candidate_options is a list, next_prompts
    is a 5-key dict, compiled_work is a string) because the three routes do
    genuinely different jobs in this pipeline -- unlike cb_wave_decision's
    three parallel lenses on one packet shape."""
    reasons = []

    for child, ans in council_answers.items():
        if len(ans) < floor:
            reasons.append(f"{child}: {len(ans)} live members, below the "
                           f"conformance floor of {floor}")

    if not isinstance(pkt, dict):
        return {"admitted": False,
                "reasons": reasons + ["compilation is not a JSON object"]}

    if route == "follow_up.next_move_selector":
        opts = pkt.get("candidate_options")
        if "candidate_options" not in pkt:
            reasons.append("missing declared output: candidate_options")
        elif not isinstance(opts, list):
            reasons.append("candidate_options: not a list")
        elif len(opts) < 3:
            reasons.append(f"candidate_options: only {len(opts)} distinct "
                           f"options harvested, below the floor of 3 -- "
                           f"too few to test lane coverage meaningfully")
        elif not all(isinstance(x, str) and len(x.strip()) >= 3 for x in opts):
            reasons.append("candidate_options: an entry is empty or under 3 chars")

    elif route == "follow_up.lane_builder":
        np_ = pkt.get("next_prompts")
        if "next_prompts" not in pkt:
            reasons.append("missing declared output: next_prompts")
        elif not isinstance(np_, dict):
            reasons.append("next_prompts: not a dict")
        else:
            missing_lanes = [l for l in LANE_NAMES if l not in np_]
            if missing_lanes:
                reasons.append(f"next_prompts: missing lane(s) {missing_lanes}")
            short = [l for l in LANE_NAMES if l in np_ and
                    (not isinstance(np_[l], str) or len(np_[l].strip()) < 15)]
            if short:
                reasons.append(f"next_prompts: lane(s) {short} shorter than "
                               f"15 chars or not a string")
            texts = [np_[l] for l in LANE_NAMES if l in np_ and isinstance(np_[l], str)]
            if len(texts) == 5 and len(set(" ".join(t.split()).lower()
                                            for t in texts)) < 5:
                reasons.append("next_prompts: two or more lanes produced "
                               "the IDENTICAL prompt -- five lanes collapsed "
                               "into fewer than five distinct next moves")

    elif route == "follow_up.compile_gate":
        cw = pkt.get("compiled_work")
        if "compiled_work" not in pkt:
            reasons.append("missing declared output: compiled_work")
        elif not isinstance(cw, str) or len(cw.strip()) < 15:
            reasons.append("compiled_work: shorter than 15 chars or not a string")
        if n_options == 0:
            reasons.append("no candidate options were available from "
                           "follow_up.next_move_selector -- lane coverage "
                           "cannot be tested")
        elif uncovered:
            reasons.append(f"{len(uncovered)} option(s) mapped to ZERO "
                           f"lanes -- the five-lane partition failed its "
                           f"own coverage claim: {uncovered}")

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

    st = classifier_self_test()
    print("CLASSIFIER SELF-TEST (hardcoded fixtures, not live output)")
    for c in st["checks"]:
        mark = "PASS" if c["pass"] else "FAIL"
        print(f"   {mark}  {c['text'][:58]:<58} -> {c['got']}")
    print(f"   proves zero-lane possible:  {st['proves_zero_lane_possible']}")
    print(f"   proves multi-lane possible: {st['proves_multi_lane_possible']}")
    if not st["classifier_can_fail"]:
        print("   WARNING: classifier did not demonstrate zero-lane coverage "
              "on its own fixtures -- the coverage test cannot be trusted "
              "to fail when it should.")
    print()

    sm = StrategyMemory(
        prompt_intent="Generate candidate follow-up options for the task, "
                      "build one next-prompt per lane (direct, alternative, "
                      "reframe, back, wildcard), and deterministically test "
                      "whether those five lanes cover the option space.",
        success_condition="candidate options are harvested, lane prompts are "
                          "built, and the code classifier reports zero-lane "
                          "and multi-lane options honestly, with no live "
                          "option silently dropped",
        claim_ceiling="follow-up structure and lane-coverage shape only; CB "
                      "does not decide whether any option or lane is correct")
    sm.kill("a lane exists just because it is named one")
    sm.kill("a model classifying its own option into a lane is evidence of coverage")

    n_children = sum(len(v) for v in ROUTES.values())
    print("WAVE follow_up -- 3 routes, nested councils, deterministic gate")
    print(f"  routes {len(ROUTES)}  required children {n_children}  "
          f"members per child {len(members)}")
    print(f"  L3 calls = {n_children} x {len(members)} = {n_children*len(members)}")
    print(f"  members answer the SAME question under: {members}")
    print(f"  lanes ({len(lanes)}): {lanes}")
    print(f"  declared outputs: {DECLARED_OUTPUTS}\n")

    jobs, prov = build_jobs(sm, a.task, members, lanes)
    missing = [k for k, v in prov.items() if v["voice"] and not v["agent_spec_loaded"]]
    print(f"PROVENANCE  {len(prov)} children, "
          f"{sum(1 for v in prov.values() if v['agent_spec_loaded'])} with agent specs, "
          f"{sum(1 for v in prov.values() if v['mini_mmm_loaded'])} with mini-MMMs")
    if missing:
        print(f"   WARNING missing agent spec for: {missing}")

    rundir = REPO/"constraint_box"/"receipts"/f"followup_{time.strftime('%Y%m%dT%H%M%SZ')}"

    if a.dry_run:
        print(f"\nDRY RUN -- {len(jobs)} jobs built, none dispatched.")
        by_route = {r: sum(1 for j in jobs if j["id"].startswith(r+"|")) for r in ROUTES}
        for r, n in by_route.items():
            floor_ok = "OK" if n >= 5 else "BELOW FLOOR"
            print(f"   {r:<32}{n:>3} child receipts would be produced  [{floor_ok}]")
        print(f"   lane_builder children == the 5 required lanes: "
              f"{ROUTES['follow_up.lane_builder'] == [f'lane.{l}' for l in LANE_NAMES]}")
        print(f"   prompt chars: min {min(len(j['prompt']) for j in jobs)}, "
              f"max {max(len(j['prompt']) for j in jobs)}")
        print(f"   classifier_can_fail (self-test): {st['classifier_can_fail']}")
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
                               "ok": r["ok"], "sec": r.get("sec"),
                               "error": r.get("error", "")} for sl, r in recs.items()},
                "provider_diversity": pd}
            print(f"   {child:<22}{cc['verdict']:<34}"
                  f"sim {cc.get('mean_similarity')}  n={cc['members']}  "
                  f"families {pd['families']}")
            if cc["verdict"].startswith("COLLAPSED"):
                collapsed.append(f"{route}/{child}")
        print()

    # ------------------------------------------------- next_move_selector: CODE
    candidate_options = harvest_options(councils["follow_up.next_move_selector"])
    pkt_nms = {"candidate_options": candidate_options}
    print(f"HARVEST  follow_up.next_move_selector -> "
          f"{len(candidate_options)} deduped candidate options (code, no model)\n")

    # ---------------------------------- lane_builder + compile_gate: LLM compile
    comp_jobs = []
    lb_body = "\n".join(
        f"[{child} / {sl}] {' '.join(v.split())[:200]}"
        for child in ROUTES["follow_up.lane_builder"]
        for sl, v in councils["follow_up.lane_builder"][child]["answers"].items())
    comp_jobs.append({"id": "follow_up.lane_builder", "prompt":
      f"{sm.preamble()}\n\nYou are the OUTPUT COMPILER for follow_up.lane_builder.\n"
      f"Its five lane councils returned:\n{lb_body}\n\nTASK:\n{a.task}\n\n"
      f"Compile ONE next-move prompt per lane. Return ONLY JSON:\n"
      + json.dumps({"next_prompts": {l: f"<{l} next prompt>" for l in LANE_NAMES}})
      + "\nAll five lane keys are required and must be genuinely different "
        "from each other."})

    # code-computed classification, injected read-only into the compiler's prompt
    lane_assignment = {opt: classify_option(opt) for opt in candidate_options}
    uncovered_options = [o for o, ls in lane_assignment.items() if not ls]
    overcovered_options = [o for o, ls in lane_assignment.items() if len(ls) > 1]
    lane_counts = {l: sum(1 for ls in lane_assignment.values() if l in ls)
                  for l in LANE_NAMES}

    cg_body = "\n".join(
        f"[{child} / {sl}] {' '.join(v.split())[:200]}"
        for child in ROUTES["follow_up.compile_gate"]
        for sl, v in councils["follow_up.compile_gate"][child]["answers"].items())
    stats = {"n_candidate_options": len(candidate_options),
             "lane_counts": lane_counts,
             "n_uncovered": len(uncovered_options),
             "uncovered_options": uncovered_options,
             "n_overcovered": len(overcovered_options)}
    comp_jobs.append({"id": "follow_up.compile_gate", "prompt":
      f"{sm.preamble()}\n\nYou are the OUTPUT COMPILER for follow_up.compile_gate.\n"
      f"DETERMINISTIC lane-coverage result, computed by CODE -- summarize it, "
      f"do not alter these numbers:\n{json.dumps(stats)}\n\n"
      f"Its audit councils returned:\n{cg_body}\n\nTASK:\n{a.task}\n\n"
      f"Compile a one-to-two sentence synthesis tying the coverage result to "
      f"what should happen next. Return ONLY JSON:\n"
      + json.dumps({"compiled_work": "<synthesis>"})})

    for j in comp_jobs:
        j["lane"] = COMPILE_LANE
    comp_raw = run_jobs(comp_jobs, width=2)
    comp = {k: r["text"] for k, r in comp_raw.items() if r["ok"]}
    print(f"COMPILE  dispatched {len(comp_jobs)} on {COMPILE_LANE}  "
          f"returned {len(comp)}\n")

    def parse_pkt(route_id):
        raw_ = comp.get(route_id, "")
        i, j = raw_.find("{"), raw_.rfind("}")
        try:
            return json.loads(raw_[i:j+1])
        except Exception:
            return None

    pkt_lb = parse_pkt("follow_up.lane_builder")
    pkt_cg = parse_pkt("follow_up.compile_gate")

    # ---------------------------------------------------------------- the gate
    results = {}
    g_nms = gate_route("follow_up.next_move_selector", pkt_nms,
                       {c: councils["follow_up.next_move_selector"][c]["answers"]
                        for c in ROUTES["follow_up.next_move_selector"]})
    results["follow_up.next_move_selector"] = {"compiled": pkt_nms, "gate": g_nms}

    g_lb = gate_route("follow_up.lane_builder", pkt_lb if pkt_lb is not None else {},
                      {c: councils["follow_up.lane_builder"][c]["answers"]
                       for c in ROUTES["follow_up.lane_builder"]})
    results["follow_up.lane_builder"] = {"compiled": pkt_lb, "gate": g_lb}

    g_cg = gate_route("follow_up.compile_gate", pkt_cg if pkt_cg is not None else {},
                      {c: councils["follow_up.compile_gate"][c]["answers"]
                       for c in ROUTES["follow_up.compile_gate"]},
                      uncovered=uncovered_options, n_options=len(candidate_options))
    results["follow_up.compile_gate"] = {"compiled": pkt_cg, "gate": g_cg}

    for route, r in results.items():
        print(f"GATE {route}")
        print(f"   {'ADMITTED' if r['gate']['admitted'] else 'REFUSED'}")
        for reason in r["gate"]["reasons"]:
            print(f"      - {reason}")
        print()

    print("LANE COVERAGE TEST (the owner's open question)")
    print(f"   candidate options tested: {len(candidate_options)}")
    for l in LANE_NAMES:
        print(f"      {l:<12} {lane_counts[l]:>3} option(s)")
    print(f"   uncovered (0 lanes):   {len(uncovered_options)}  {uncovered_options}")
    print(f"   overcovered (>1 lane): {len(overcovered_options)}  {overcovered_options}")
    print(f"   VERDICT: {'five lanes DID NOT cover the option space this run' if uncovered_options else 'no uncovered options this run (does not prove permanent coverage)'}\n")

    declared = {
        "next_prompts": (pkt_lb or {}).get("next_prompts"),
        "lane_assignment": lane_assignment,
        "uncovered_options": uncovered_options,
        "compiled_work": (pkt_cg or {}).get("compiled_work"),
    }

    admitted = [r for r, v in results.items() if v["gate"]["admitted"]]
    print(f"{'='*72}")
    print(f"WAVE VERDICT  {len(admitted)}/{len(ROUTES)} routes admitted: {admitted or 'none'}")
    print(f"COLLAPSE      {len(collapsed)}/{n_children} councils collapsed"
          f"{' -> ' + str(collapsed) if collapsed else ' -- all diverged'}")

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir/"FOLLOWUP_RECEIPT.json").write_text(json.dumps({
        "schema": "cb.wave.followup.v1", "task": a.task,
        "structure": {"routes": list(ROUTES), "children_per_route":
                      {r: len(c) for r, c in ROUTES.items()},
                      "members_per_child": len(members), "slices": members,
                      "l3_calls_planned": len(jobs), "lane_names": LANE_NAMES},
        "classifier_self_test": st,
        "lane_keywords": {k: [p.pattern for p in v] for k, v in LANE_PATTERNS.items()},
        "provenance": prov,
        "L3": {"dispatched": len(jobs), "live": len(live),
               "by_lane": {k: {"called": c, "live": o} for k, (c, o) in by_lane.items()}},
        "councils": {r: {c: councils[r][c] for c in ROUTES[r]} for r in ROUTES},
        "candidate_options": candidate_options,
        "lane_counts": lane_counts,
        "overcovered_options": overcovered_options,
        "compilation": {r: results[r]["compiled"] for r in ROUTES},
        "gate": {r: results[r]["gate"] for r in ROUTES},
        "declared_outputs": declared,
        "routes_admitted": admitted, "collapsed_councils": collapsed,
        "strategy_memory": sm.receipt(),
        "wall_seconds": round(time.time()-t0, 1), "promotion_allowed": False,
        "claim_ceiling": "follow-up structure and lane-coverage shape only; "
                         "CB does not decide whether any option, lane, or "
                         "the compiled synthesis is correct"},
        indent=1, sort_keys=True))
    print(f"RECEIPT {rundir.name}/FOLLOWUP_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0 if admitted else 1


if __name__ == "__main__":
    sys.exit(main())
