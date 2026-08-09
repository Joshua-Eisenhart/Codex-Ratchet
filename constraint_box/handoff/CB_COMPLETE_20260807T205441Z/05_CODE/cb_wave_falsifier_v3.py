#!/usr/bin/env python3
"""cb_wave_falsifier_v3 — the falsification wave, strengthened.

Three strengthenings over v2:
  1. MULTI-PROVIDER lanes  — members span provider families, so the
     council cannot collapse the way one model with five prompts can
  2. DETERMINISTIC MEMBERS VOTE — z3, rustworkx, portion, celpy,
     icontract sit IN the council, not as a fence around it. A tool
     member cannot be argued with, and its verdict outranks any voice
     that contradicts it.
  3. STRUCTURAL CLAIMS — the wave can falsify a WAVE DESIGN, not only a
     prose claim. That is how it is used on the Decision and Follow-Up
     waves: their design assertions become the target.

Lineage note (owner): CB began as ClaimGate; ClaimGate began as the
Wizard. The three-council shape is inherited, not invented here, and
need not stay identical — but the Failure council is the one that keeps
the rest honest, so it is built first.

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, difflib, itertools, json, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_multi_provider import fanout, provider_diversity
from cb_strategy_memory import StrategyMemory

LANES = ["haiku", "nvidia/nemotron-3-super-120b-a12b:free",
         "nvidia/nemotron-nano-9b-v2:free", "openai/gpt-oss-20b:free",
         "cohere/north-mini-code:free"]

# ---------------- DETERMINISTIC MEMBERS OF THE FALSIFIER COUNCIL ----------
def det_members(spec: dict) -> dict:
    """Each returns a structural verdict about the TARGET's declared shape.
    These cannot be argued with; they outrank any voice that contradicts."""
    out = {}

    # rustworkx: is the target's declared control graph bounded?
    try:
        import rustworkx as rx
        g = rx.PyDiGraph(); idx = {n: g.add_node(n) for n in spec.get("nodes", [])}
        for a, b in spec.get("edges", []):
            if a in idx and b in idx: g.add_edge(idx[a], idx[b], None)
        cyc = list(rx.simple_cycles(g))
        out["rustworkx"] = {"cycles": len(cyc),
            "verdict": "ADMIT" if (spec.get("cycles_allowed") or not cyc) else
                       "REFUTE: cycle present where the claim asserts none"}
    except Exception as e:
        out["rustworkx"] = {"verdict": f"UNRESOLVED: {type(e).__name__}"}

    # z3: is the declared budget/coverage arithmetic satisfiable?
    try:
        import z3
        s = z3.Solver()
        req = spec.get("required_children", 0); mem = spec.get("members_per_child", 0)
        floor_lo, floor_hi = spec.get("child_receipt_floor", (5, 10))
        x = z3.Int("total")
        s.add(x == req * mem, x >= req * floor_lo)
        r = s.check()
        out["z3"] = {"query": f"{req} children x {mem} members >= {req*floor_lo}",
            "result": str(r),
            "verdict": "ADMIT" if r == z3.sat else
                       "REFUTE: declared structure is below the conformance floor"}
    except Exception as e:
        out["z3"] = {"verdict": f"UNRESOLVED: {type(e).__name__}"}

    # portion: are the declared ratios inside their possible box?
    try:
        import portion as P
        cov = spec.get("claimed_coverage", 0.0)
        out["portion"] = {"coverage": cov,
            "verdict": "ADMIT" if cov in P.closed(0.0, 1.0) else
                       "REFUTE: claimed coverage outside [0,1] — not a possible value"}
    except Exception as e:
        out["portion"] = {"verdict": f"UNRESOLVED: {type(e).__name__}"}

    # celpy: the conformance rule as DATA, not code
    try:
        import celpy
        env = celpy.Environment()
        prog = env.program(env.compile(
            "councils_run == councils_declared && members_per_child >= floor"))
        ok = bool(prog.evaluate({
            "councils_run": celpy.json_to_cel(spec.get("councils_run", 0)),
            "councils_declared": celpy.json_to_cel(spec.get("councils_declared", 0)),
            "members_per_child": celpy.json_to_cel(spec.get("members_per_child", 0)),
            "floor": celpy.json_to_cel(spec.get("child_receipt_floor", (5, 10))[0])}))
        out["celpy"] = {"rule": "all councils run AND members >= floor",
            "verdict": "ADMIT" if ok else "REFUTE: conformance rule fails on the declared numbers"}
    except Exception as e:
        out["celpy"] = {"verdict": f"UNRESOLVED: {type(e).__name__}"}

    # icontract: a wave may not claim coverage it did not run
    try:
        import icontract
        @icontract.require(lambda run, decl: run <= decl,
                           "cannot run more councils than are declared")
        def gate(run: int, decl: int): return True
        gate(spec.get("councils_run", 0), spec.get("councils_declared", 1))
        out["icontract"] = {"verdict": "ADMIT"}
    except Exception as e:
        out["icontract"] = {"verdict": f"REFUTE: {type(e).__name__}"}
    return out

def collapse_audit(texts):
    vals = [" ".join(t.split()).lower()[:600] for t in texts if t.strip()]
    if len(vals) < 2: return {"verdict": "INSUFFICIENT", "mean": None}
    sims = [difflib.SequenceMatcher(None, a, b).ratio()
            for a, b in itertools.combinations(vals, 2)]
    m = sum(sims)/len(sims)
    return {"mean": round(m, 3), "max": round(max(sims), 3),
            "verdict": "COLLAPSED" if m >= 0.75 else
                       "CONVERGENT" if m >= 0.5 else "DIVERGENT"}


# ---------------------------------------------------------------- targets
# The other two waves' DESIGN ASSERTIONS become falsification targets.
TARGETS = {
 "decision": {
   "claim": "The Decision council's three routes — context_strategy, "
            "move_selection, evidence_boundary — are sufficient to select ONE "
            "bounded move while preserving live alternatives, without any "
            "further route.",
   "spec": {"nodes": ["context_strategy", "move_selection", "evidence_boundary"],
            "edges": [("context_strategy", "move_selection"),
                      ("move_selection", "evidence_boundary")],
            "cycles_allowed": False, "required_children": 3,
            "members_per_child": 4, "child_receipt_floor": (5, 10),
            "claimed_coverage": 1.0, "councils_run": 0, "councils_declared": 3}},
 "followup": {
   "claim": "The Follow-Up council's three routes — next_move_selector, "
            "lane_builder, compile_gate — generate divergent next prompts and "
            "compile the useful ones into bounded work, and the five lanes "
            "(direct, alternative, reframe, back, wildcard) are enough to "
            "cover the option space.",
   "spec": {"nodes": ["next_move_selector", "lane_builder", "compile_gate"],
            "edges": [("next_move_selector", "lane_builder"),
                      ("lane_builder", "compile_gate")],
            "cycles_allowed": False, "required_children": 3,
            "members_per_child": 5, "child_receipt_floor": (5, 10),
            "claimed_coverage": 1.0, "councils_run": 0, "councils_declared": 3}},
}

QUESTION = ("TARGET DESIGN CLAIM:\n{claim}\n\n"
            "DETERMINISTIC MEMBERS OF YOUR COUNCIL ALREADY RETURNED:\n{det}\n\n"
            "Name the SINGLE strongest live falsifier for this design claim: "
            "the one thing that would show the design is insufficient. "
            "Tool verdicts are fact and outrank any reasoning that contradicts "
            "them. One sentence, under 30 words, falsifier only.")

def run_target(name, target, lanes):
    print(f"\n{'='*72}\nTARGET: {name}\n{target['claim'][:150]}\n{'='*72}")
    det = det_members(target["spec"])
    print("DETERMINISTIC MEMBERS (vote first, free, un-arguable):")
    refutes = []
    for k, v in det.items():
        vd = v["verdict"]
        if vd.startswith("REFUTE"): refutes.append(k)
        print(f"   {k:<12}{vd[:88]}")
    print(f"   -> {len(refutes)} deterministic REFUTATION(S): {refutes or 'none'}")

    q = QUESTION.format(claim=target["claim"],
                        det=json.dumps({k: v["verdict"] for k, v in det.items()}))
    res = fanout(q, lanes, width=len(lanes))
    print("\nLLM MEMBERS (multi-provider):")
    for r in res:
        if r["ok"]:
            print(f"   {r['model'][:38]:<40}{' '.join(r['text'].split())[:74]}")
        else:
            print(f"   {r['model'][:38]:<40}[DEAD] {r.get('error','')[:40]}")
    pd = provider_diversity(res)
    ca = collapse_audit([r["text"] for r in res if r["ok"]])
    print(f"\n   provider audit : {pd['verdict']}  families={pd['families']} "
          f"live={pd['lanes_live']}/{pd['lanes_called']}")
    print(f"   collapse audit : {ca['verdict']}  mean sim {ca.get('mean')}")

    verdict = ("KILLED (deterministic refutation)" if refutes else
               "OPEN" if pd["lanes_live"] else "UNRESOLVED: no live lane")
    print(f"   ROUTE VERDICT  : {verdict}")
    return {"claim": target["claim"], "deterministic": det,
            "deterministic_refutations": refutes,
            "llm": res, "provider_audit": pd, "collapse_audit": ca,
            "verdict": verdict}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="decision,followup")
    ap.add_argument("--lanes", default=",".join(LANES))
    a = ap.parse_args()
    t0 = time.time()
    lanes = [x.strip() for x in a.lanes.split(",") if x.strip()]
    sm = StrategyMemory(
        prompt_intent="Falsify the DESIGN of the Decision and Follow-Up waves "
                      "before building them.",
        success_condition="each design claim is KILLED with a named structural "
                          "refutation, or OPEN with the falsifier stated",
        claim_ceiling="wave design structure only; CB does not decide whether "
                      "the councils would produce good judgments")
    sm.kill("a wave design is sound because it was inherited")
    print("WAVE failure.falsifier v3 — deterministic members vote, "
          "multi-provider LLM lanes, structural targets")
    print(f"lanes: {lanes}")
    out = {}
    for name in [t.strip() for t in a.targets.split(",")]:
        if name in TARGETS:
            out[name] = run_target(name, TARGETS[name], lanes)
    killed = [k for k, v in out.items() if v["verdict"].startswith("KILLED")]
    print(f"\n{'='*72}")
    print(f"SUMMARY  targets {len(out)}  killed by deterministic members: "
          f"{len(killed)} {killed}")
    for k, v in out.items():
        print(f"   {k:<10}{v['verdict'][:60]}  "
              f"refutations={v['deterministic_refutations']}")
    rd = REPO/"constraint_box"/"receipts"/f"falsifier3_{time.strftime('%Y%m%dT%H%M%SZ')}"
    rd.mkdir(parents=True, exist_ok=True)
    (rd/"FALSIFIER3_RECEIPT.json").write_text(json.dumps(
        {"schema": "cb.wave.failure-falsifier.v3", "lanes": lanes,
         "targets": out, "strategy_memory": sm.receipt(),
         "wall_seconds": round(time.time()-t0, 1), "promotion_allowed": False,
         "claim_ceiling": "wave design structure only"}, indent=1, sort_keys=True))
    print(f"RECEIPT {rd.name}/FALSIFIER3_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
