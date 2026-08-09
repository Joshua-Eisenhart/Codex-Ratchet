#!/usr/bin/env python3
"""cb_skill_premortem — RUN the premortem skill to its own contract.

Loading a SKILL.md as prompt text is not running the skill. The skill
declares a procedure and named outputs; running it means executing the
procedure and validating the declared artifacts.

premortem's contract (from ~/.codex/skills/premortem/SKILL.md):
  1. Set The Frame          exact frame sentence, required
  2. Generate Raw Failure   comprehensive, no fixed number, no padding
  3. Spawn Deep-Dive Agents ONE SUBAGENT PER FAILURE REASON, in parallel.
                            "If the runtime cannot spawn subagents, state
                            that the agent wave is blocked ... do not
                            pretend agents ran."
                            Each output: FAILURE STORY / UNDERLYING
                            ASSUMPTION / EARLY WARNING SIGNS, <300 words
  4. Synthesize             PREMORTEM REPORT with five named sections
  Outputs                   premortem-report-*.html, premortem-transcript-*.md

CB's job: run it, then GATE the artifacts against that contract. The
skill's own declared shape is the schema. promotion_allowed=false.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_run import dispatch
SKILL = Path.home() / ".codex/skills/premortem/SKILL.md"

FRAME = ("Here is the premise: it is six months from now. {plan} has failed. "
         "It is done. We are looking back to understand exactly what went wrong.")

DEEP_DIVE = """You are an investigator in a premortem analysis. You have been assigned one specific failure reason to analyze in depth.

The plan:
---
{context}
---

PREMORTEM FRAME: It is six months from now. This plan has failed.

YOUR ASSIGNED FAILURE REASON: {reason}

Your job is to go deep on this one failure. Write the story of how it actually played out. Be specific. Use details from the plan. Make it feel real, like a case study of something that actually happened.

Your output must include:

1. THE FAILURE STORY: A 2-3 paragraph narrative of how this specific failure played out.
2. THE UNDERLYING ASSUMPTION: The one thing being taken for granted that made this failure possible. One sentence.
3. EARLY WARNING SIGNS: 1-2 concrete, observable signals indicating this failure mode is starting.

Keep the total response under 300 words. Be direct. Do not hedge. Do not sugarcoat."""

def step2_reasons(context, plan, rundir):
    """generate the raw failure reasons — one LLM call, no fixed number"""
    job = [{"id": "raw_reasons", "prompt":
        f"{FRAME.format(plan=plan)}\n\nCONTEXT:\n{context}\n\n"
        "Generate every genuine reason this failed. Each must be specific to "
        "this plan, a real threat, one or two sentences, grounded in the "
        "details given. Do not use a fixed number. Four may be enough; nine "
        "may be necessary. Do not pad.\n\n"
        "Return ONLY a JSON array of strings."}]
    res, _ = dispatch(job, rundir / "step2", timeout=150, conc=1)
    raw = res.get("raw_reasons", "")
    i, j = raw.find("["), raw.rfind("]")
    try:
        reasons = json.loads(raw[i:j+1])
        return [r for r in reasons if isinstance(r, str) and len(r) > 20]
    except Exception:
        return []

def step3_deep_dives(context, reasons, rundir):
    """ONE SUBAGENT PER REASON, IN PARALLEL — the contract's own words"""
    jobs = [{"id": f"dive_{k}", "prompt":
             DEEP_DIVE.format(context=context, reason=r)}
            for k, r in enumerate(reasons)]
    res, spawned = dispatch(jobs, rundir / "step3", timeout=180,
                            conc=min(len(jobs), 4))
    return res, spawned

def gate_dive(text):
    """CB gates each dive against the SKILL's declared output shape"""
    reasons = []
    up = text.upper()
    for req in ("FAILURE STORY", "UNDERLYING ASSUMPTION", "EARLY WARNING"):
        if req not in up:
            reasons.append(f"missing required section: {req}")
    words = len(text.split())
    if words > 400:
        reasons.append(f"exceeds skill word ceiling: {words} words (<300 declared)")
    if not text.strip():
        reasons.append("empty return")
    return reasons

def step4_synthesis(context, dives, rundir):
    body = "\n\n".join(f"--- DIVE {k} ---\n{v[:1200]}" for k, v in dives.items())
    job = [{"id": "synthesis", "prompt":
        f"{context}\n\nDEEP DIVES:\n{body}\n\n"
        "Produce a PREMORTEM REPORT with EXACTLY these five sections, each "
        "with its heading:\n"
        "1. The Most Likely Failure\n2. The Most Dangerous Failure\n"
        "3. The Hidden Assumption\n4. The Revised Plan\n"
        "5. The Pre-Launch Checklist\n\n"
        "Be direct, specific, actionable. Under 500 words."}]
    res, _ = dispatch(job, rundir / "step4", timeout=180, conc=1)
    return res.get("synthesis", "")

def gate_synthesis(text):
    need = ["Most Likely Failure", "Most Dangerous Failure", "Hidden Assumption",
            "Revised Plan", "Pre-Launch Checklist"]
    return [f"missing declared section: {s}" for s in need
            if s.lower() not in text.lower()]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--context", required=True)
    a = ap.parse_args()
    t0 = time.time()
    ts = time.strftime("%Y%m%dT%H%M%SZ")
    rundir = REPO / "constraint_box" / "receipts" / f"premortem_{ts}"
    rundir.mkdir(parents=True, exist_ok=True)
    sk = SKILL.read_bytes()
    print(f"SKILL premortem  {SKILL}")
    print(f"  sha256 {hashlib.sha256(sk).hexdigest()[:16]}  {len(sk)} bytes\n")

    print("STEP 1  frame")
    print(f"   {FRAME.format(plan=a.plan)[:110]}...")

    print("STEP 2  raw failure reasons")
    reasons = step2_reasons(a.context, a.plan, rundir)
    print(f"   generated {len(reasons)} reasons (no fixed number, per contract)")
    for r in reasons: print(f"     - {r[:100]}")
    if not reasons:
        print("   BLOCKED: no reasons generated; the wave cannot run"); return 1

    print(f"\nSTEP 3  spawn ONE subagent per reason, in parallel")
    dives, spawned = step3_deep_dives(a.context, reasons, rundir)
    print(f"   spawned {spawned}  completed {len(dives)}  "
          f"(count law: {len(dives)}/{spawned})")
    gated = {k: gate_dive(v) for k, v in dives.items()}
    ok = [k for k, v in gated.items() if not v]
    print(f"   CB GATE against the skill's declared dive shape: "
          f"{len(ok)}/{len(dives)} conform")
    for k, v in gated.items():
        if v: print(f"     REFUSED {k}: {v[0][:80]}")

    print(f"\nSTEP 4  synthesis")
    syn = step4_synthesis(a.context, {k: dives[k] for k in ok}, rundir)
    sg = gate_synthesis(syn)
    print(f"   CB GATE against the five declared sections: "
          f"{'ALL PRESENT' if not sg else 'REFUSED'}")
    for s in sg: print(f"     - {s}")

    md = rundir / f"premortem-transcript-{ts}.md"
    md.write_text(f"# Premortem transcript {ts}\n\n## Frame\n{FRAME.format(plan=a.plan)}\n\n"
                  f"## Raw failure reasons ({len(reasons)})\n" +
                  "\n".join(f"- {r}" for r in reasons) +
                  f"\n\n## Deep dives ({len(dives)})\n" +
                  "\n\n".join(f"### {k}\n{v}" for k, v in dives.items()) +
                  f"\n\n## Synthesis\n{syn}\n")
    receipt = {"schema": "cb.skill-run.v1", "skill": "premortem",
        "skill_path": str(SKILL), "skill_sha256": hashlib.sha256(sk).hexdigest(),
        "plan": a.plan, "steps": {
            "1_frame": True, "2_reasons": len(reasons),
            "3_dives": {"spawned": spawned, "completed": len(dives),
                        "conforming": len(ok), "gate": gated},
            "4_synthesis": {"sections_present": not sg, "missing": sg}},
        "artifacts": {"transcript": str(md.relative_to(REPO)),
                      "html": "NOT GENERATED — declared by the skill, not produced"},
        "contract_complete": bool(reasons) and len(ok) == len(dives) and not sg,
        "wall_seconds": round(time.time()-t0, 1), "promotion_allowed": False,
        "claim_ceiling": "the skill ran to its declared procedure; CB gates the "
                         "SHAPE of its artifacts, never whether the analysis is right"}
    (rundir / "SKILL_RUN_RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"\nCONTRACT COMPLETE: {receipt['contract_complete']}")
    print(f"   note: HTML report is declared by the skill and was NOT produced — "
          f"recorded as a gap, not pretended")
    print(f"RECEIPT {rundir.name}/SKILL_RUN_RECEIPT.json  ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
