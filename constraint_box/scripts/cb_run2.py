#!/usr/bin/env python3
"""cb_run2 — FULL composition: formal agent + mini-MMM + CB MMM pack + skill.

Each child is a composed member with FOUR file-backed inputs, every one
hashed into the receipt. This satisfies the route-truth requirement that
a run receipt name the agent spec, the MMM/slice preload, the runtime
target and the output — and the voice specs' own rule: "Load salience
first (required) ... A receipt that did not load it is not counted."

  leg 1  AGENT SPEC   ~/Codex-Ratchet/.claude/agents/voice-*.md
  leg 2  MINI-MMM     ~/wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md/
  leg 3  CB MMM PACK  constraint_box/mmm/packs/*.md
  leg 4  SKILL        ~/.codex/skills/<name>/SKILL.md

Gates unchanged: msgspec, jsonschema, portion, celpy, icontract, SDG.
No model decides admission. promotion_allowed=false.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SCRIPTS = REPO / "constraint_box" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from cb_strategy_memory import StrategyMemory
from cb_run import gate_claim, dispatch, TUNED

AGENTS = REPO / ".claude" / "agents"
MINI = Path.home() / "wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md"
PACKS = REPO / "constraint_box" / "mmm" / "packs"
SKILLS = [Path.home() / ".codex/skills", Path.home() / ".agents/skills",
          Path.home() / ".claude/skills"]

def load(p: Path, limit: int) -> tuple[str, str, str]:
    """returns (text, path, sha256) — every leg is provable"""
    if not p or not p.is_file():
        return "", "", ""
    b = p.read_bytes()
    return b.decode(errors="ignore")[:limit], str(p), hashlib.sha256(b).hexdigest()

def find_skill(name: str) -> Path | None:
    for d in SKILLS:
        p = d / name / "SKILL.md"
        if p.is_file():
            return p
    return None

def compose(voice: str, pack: str, skill: str) -> dict:
    spec_t, spec_p, spec_h = load(AGENTS / f"voice-{voice}.md", 2200)
    mini_t, mini_p, mini_h = load(MINI / f"MMM_VOICE_{voice.upper()}_FULL_v4_1.md", 2600)
    pack_t, pack_p, pack_h = load(PACKS / f"{pack}.md", 2200)
    sk = find_skill(skill)
    sk_t, sk_p, sk_h = load(sk, 1800) if sk else ("", "", "")
    return {"voice": voice,
            "agent_spec": {"path": spec_p, "sha256": spec_h, "chars": len(spec_t)},
            "mini_mmm":   {"path": mini_p, "sha256": mini_h, "chars": len(mini_t)},
            "cb_pack":    {"path": pack_p, "sha256": pack_h, "chars": len(pack_t)},
            "skill":      {"path": sk_p,   "sha256": sk_h,   "chars": len(sk_t)},
            "_text": {"spec": spec_t, "mini": mini_t, "pack": pack_t, "skill": sk_t}}

SHAPE = {"verdict": "PARKED", "promotion_allowed": False,
         "claim_ceiling": "<what this claim does not cover>",
         "confidence": 0.5, "finding": "<one sentence>"}

def build(sm, members, role, task):
    jobs = []
    for m in members:
        t = m["_text"]
        jobs.append({"id": f"{m['voice']}~{role}", "prompt":
          f"{sm.preamble()}\n\n"
          f"=== AGENT SPEC (leg 1) ===\n{t['spec']}\n"
          f"=== MINI-MMM SALIENCE (leg 2, required by your spec) ===\n{t['mini']}\n"
          f"=== CB MMM PACK (leg 3) ===\n{t['pack']}\n"
          f"=== SKILL FRAME (leg 4) ===\n{t['skill']}\n"
          f"=== END COMPOSITION ===\n\n"
          f"FORMAL ROLE: {role}\nTASK: {task}\n\n"
          f"Return ONLY this JSON object, no prose:\n{json.dumps(SHAPE)}\n"
          f"verdict in [PARKED, BLOCKED, ADMIT_FOR_TESTING]; promotion_allowed "
          f"false; claim_ceiling >= 10 chars; confidence a number in [0,1]."})
    return jobs

def diversity(jobs):
    """variable stratum = agent spec + mini-MMM (legs 1-2). The CB pack,
    skill frame, role and task are shared by design."""
    def var(p):
        i = p.find("=== AGENT SPEC"); j = p.find("=== CB MMM PACK")
        return p[i:j] if i >= 0 and j > i else p
    def sh(t, k=4):
        w = t.split()
        return {" ".join(w[i:i+k]) for i in range(max(0, len(w)-k+1))}
    S = [sh(var(j["prompt"])) for j in jobs]
    ov = [len(a & b)/len(a | b) for a, b in itertools.combinations(S, 2)] or [0]
    dup = len(jobs) - len({hashlib.sha256(j["prompt"].encode()).hexdigest() for j in jobs})
    return {"max_overlap": round(max(ov), 4), "mean_overlap": round(sum(ov)/len(ov), 4),
            "duplicates": dup,
            "verdict": "DIVERSE" if max(ov) < 0.8 and dup == 0 else "COLLAPSED"}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--role", default="failure.falsifier")
    ap.add_argument("--pack", default="nominalist")
    ap.add_argument("--skill", default="premortem")
    ap.add_argument("--voices", default="hume,popper,zhuangzi,feynman,pushback,factory")
    a = ap.parse_args()
    t0 = time.time()
    params = json.loads(TUNED.read_text()) if TUNED.exists() else {"min_ceiling_chars": 10}
    params.setdefault("min_ceiling_chars", 10)

    sm = StrategyMemory(prompt_intent=a.task,
        success_condition="each composed member returns a typed claim that "
                          "survives the deterministic gate stack",
        claim_ceiling="format, shape and machinery only; CB never decides truth")
    sm.kill("a model may set its own verdict")
    sm.note("strategy_state", f"formal role {a.role}; CB pack {a.pack}; skill {a.skill}")

    voices = [v.strip() for v in a.voices.split(",") if v.strip()]
    members = [compose(v, a.pack, a.skill) for v in voices]

    print(f"CB RUN v2 — FULL COMPOSITION")
    print(f"{'voice':<10}{'agent spec':>11}{'mini-MMM':>10}{'CB pack':>9}{'skill':>7}   all four legs")
    ok_all = True
    for m in members:
        legs = [m['agent_spec'], m['mini_mmm'], m['cb_pack'], m['skill']]
        have = all(l['sha256'] for l in legs)
        ok_all &= have
        print(f"{m['voice']:<10}{m['agent_spec']['chars']:>11}{m['mini_mmm']['chars']:>10}"
              f"{m['cb_pack']['chars']:>9}{m['skill']['chars']:>7}   {'YES' if have else 'MISSING LEG'}")
    print(f"\nrole={a.role}  pack={a.pack}  skill={a.skill}  all_members_complete={ok_all}")

    jobs = build(sm, members, a.role, a.task)
    dg = diversity(jobs)
    print(f"W-PROMPT  diversity {dg['verdict']} (max {dg['max_overlap']}, "
          f"mean {dg['mean_overlap']}, dups {dg['duplicates']})")
    if dg["verdict"] == "COLLAPSED":
        print("  REFUSED before dispatch"); return 1

    rundir = REPO/"constraint_box"/"receipts"/f"cbrun2_{time.strftime('%Y%m%dT%H%M%SZ')}"
    res, spawned = dispatch(jobs, rundir, timeout=150, conc=4)
    print(f"W-COUNCIL  spawned {spawned} completed {len(res)}")

    gated = []
    for jid, raw in res.items():
        claim, reasons = gate_claim(raw, params)
        gated.append({"id": jid, "claim": claim, "reasons": reasons})
    print(f"\nW-GATE")
    for g in sorted(gated, key=lambda x: x["id"]):
        c = g["claim"] or {}
        print(f"  {g['id']:<26}{'ADMITTED' if not g['reasons'] else 'REFUSED':<10}"
              f"{str(c.get('verdict','—')):<20}conf={c.get('confidence','—')}")
        for r in g["reasons"][:2]: print(f"        - {r[:104]}")
        if not g["reasons"]:
            print(f"        finding: {str(c.get('finding',''))[:96]}")

    adm = sum(1 for g in gated if not g["reasons"])
    receipt = {"schema": "cb.run.v2", "task": a.task, "role": a.role,
        "cb_pack": a.pack, "skill": a.skill,
        "composition": [{k: v for k, v in m.items() if k != "_text"} for m in members],
        "W_PROMPT": dg, "W_COUNCIL": {"spawned": spawned, "completed": len(res),
                                      "count_law_holds": len(res) <= spawned},
        "W_GATE": [{"id": g["id"], "admitted": not g["reasons"],
                    "reasons": g["reasons"], "claim": g["claim"]} for g in gated],
        "W_VERIFY": {"conserved_stratum_intact": sm.verify_conserved(),
                     "admitted": adm, "refused": len(gated)-adm,
                     "all_members_four_legs": ok_all},
        "strategy_memory": sm.receipt(),
        "wall_seconds": round(time.time()-t0, 1), "promotion_allowed": False,
        "claim_ceiling": "format, shape and machinery only; CB does not decide truth"}
    (rundir/"CB_RUN2_RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"\nW-VERIFY  conserved={sm.verify_conserved()}  admitted={adm} "
          f"refused={len(gated)-adm}  four_legs={ok_all}")
    print(f"RECEIPT {rundir.name}/CB_RUN2_RECEIPT.json  ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
