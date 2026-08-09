#!/usr/bin/env python3
"""cb_run — THE INTEGRATED CONSTRAINTBOX RUN.

One entry point. An LLM produces claims; CB constrains them. Skills are
loaded as skills. Autoresearch runs inside the cycle and writes back.
The verdict is deterministic; no model decides admission.

  W-PROMPT      strategy_memory preamble + skill frame + voice slices,
                diversity-gated on the VARIABLE stratum before dispatch
  W-COUNCIL     LLM children via claude_child_fanout (count law enforced)
  W-GATE        every returned claim through the deterministic stack:
                msgspec shape, jsonschema ladder, portion range,
                celpy rule, icontract precondition, SDG structure
  W-VERIFY      conserved-stratum check, count law, refusal census
  W-AUTORESEARCH score this cycle, tune, write back only if a monotone
                measure moved (LAW 8)

Usage:
  cb_run.py --task "..." --skill premortem --voices hume,popper,zhuangzi
promotion_allowed=false.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SCRIPTS = REPO / "constraint_box" / "scripts"
sys.path.insert(0, str(SCRIPTS))
FANOUT = Path.home() / ".codex/skills/claude-bridge/scripts/claude_child_fanout.py"
SKILL_DIRS = [Path.home() / ".codex/skills", Path.home() / ".agents/skills",
              Path.home() / ".claude/skills"]
TUNED = REPO / "constraint_box" / "config" / "cb_tuned_params.json"

from cb_strategy_memory import StrategyMemory
# The packaged product is now pip-installed editable, so the scripts lane can
# reuse its parsers instead of reimplementing them.
from constraintbox.intake import parse_json_object

VOICE_MMM = {
 "hume": "Terms: supported, unsupported, scope, uncertainty.",
 "popper": "Terms: falsifier, killed, open, survived.",
 "feynman": "Terms: mechanism, observable, pass/fail check.",
 "zhuangzi": "Terms: live reading, alternate interpretation, exclusion condition.",
 "orwell": "Terms: plain wording, anti-fog.",
 "pushback": "Terms: overclaim boundary, correction.",
 "factory": "Terms: bottleneck, queue, leverage.",
 "systems": "Terms: feedback loop, second-order effect.",
 "strategy": "Terms: sequence, priority, retreat condition.",
}

# ------------------------------------------------------------ skills
def load_skill(name: str) -> tuple[str, str]:
    """A skill IS its SKILL.md loaded as instructions. Invoking it means
    framing the child with it — which is what the runtimes do."""
    for d in SKILL_DIRS:
        p = d / name / "SKILL.md"
        if p.is_file():
            txt = p.read_text(errors="ignore")
            return str(p), txt[:2500]
    return "", ""

# ------------------------------------------------- W-PROMPT + diversity
def build_jobs(sm, skill_text, voices, task, claim_shape):
    jobs = []
    for v in voices:
        jobs.append({"id": f"claim~{v}", "prompt":
            f"{sm.preamble()}\n\n"
            f"--- SKILL FRAME ---\n{skill_text}\n--- END SKILL FRAME ---\n\n"
            f"{VOICE_MMM[v]}\n\nTASK: {task}\n\n"
            f"Return ONLY a JSON object with exactly these keys and no prose:\n"
            f"{json.dumps(claim_shape)}\n"
            f"verdict must be one of PARKED, BLOCKED, ADMIT_FOR_TESTING. "
            f"promotion_allowed must be false. claim_ceiling must be at least "
            f"10 characters. confidence must be a number between 0 and 1."})
    return jobs

def diversity_gate(jobs):
    """FOUR declared strata:
       conserved  = strategy_memory preamble   (identical by design, LAW 2)
       skill      = the SKILL.md frame         (identical by design)
       shared     = TASK + required claim shape(identical by design, one object)
       variable   = the MMM slice ONLY         (where divergence must live)
    Scoring anything but the variable stratum makes the manager and the
    diversity gate fight each other."""
    def var(p):
        i = p.find("Terms:")
        j = p.find("\n\nTASK:")
        return p[i:j] if (i >= 0 and j > i) else (p[i:] if i >= 0 else p)
    def sh(t, k=4):
        w = t.split()
        return {" ".join(w[i:i+k]) for i in range(max(0, len(w)-k+1))}
    S = [sh(var(j["prompt"])) for j in jobs]
    ov = [len(a & b) / len(a | b) for a, b in itertools.combinations(S, 2)] or [0]
    dup = len(jobs) - len({hashlib.sha256(j["prompt"].encode()).hexdigest()
                           for j in jobs})
    return {"max_overlap": round(max(ov), 4), "mean": round(sum(ov)/len(ov), 4),
            "duplicates": dup,
            "verdict": "DIVERSE" if max(ov) < 0.8 and dup == 0 else "COLLAPSED"}

# ------------------------------------------------------------ W-COUNCIL
def dispatch(jobs, out_dir, model="haiku", timeout=120, conc=4):
    jf = out_dir / "jobs.json"; out_dir.mkdir(parents=True, exist_ok=True)
    jf.write_text(json.dumps(jobs, indent=1))
    subprocess.run([sys.executable, str(FANOUT), "--name", out_dir.name,
                    "--model", model, "--budget", "1",
                    "--timeout-sec", str(timeout), "--max-concurrency", str(conc),
                    "--global-max-active", "8", "--jobs-file", str(jf),
                    "--out-dir", str(out_dir)], capture_output=True, text=True)
    res = {}; spawned = 0
    for rp in out_dir.glob("*/fanout_receipt.json"):
        d = json.loads(rp.read_text())
        spawned = len(d.get("children", []))
        for c in d.get("children", []):
            if c.get("status") == "completed":
                o = json.loads(Path(c["bridge_output_path"]).read_text())
                res[c["id"]] = str(o.get("result", ""))
    return res, spawned


# -------------------------------------------------------------- W-GATE
def gate_claim(raw_text, params):
    """The deterministic stack. Every refusal names the member and reason.
    No model decides admission."""
    import msgspec, jsonschema, portion as P, celpy, icontract
    reasons = []; claim = None

    # member: extract a JSON object at all
    s = raw_text.strip()
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j < 0:
        return None, ["extract: no JSON object in the return"]
    try:
        # NOT json.loads. The packaged intake parser already refuses duplicate
        # keys and non-finite tokens; plain json.loads keeps the LAST duplicate,
        # so a reply carrying "verdict" twice could silently upgrade PARKED to
        # ADMIT_FOR_TESTING — the exact bypass this gate exists to stop.
        claim = parse_json_object(s[i:j + 1].encode())
    except Exception as e:
        return None, [f"extract: {type(e).__name__}"]

    # member: msgspec strict shape
    class Claim(msgspec.Struct, forbid_unknown_fields=True):
        verdict: str
        promotion_allowed: bool
        claim_ceiling: str
        confidence: float
        finding: str
    try:
        msgspec.json.decode(json.dumps(claim).encode(), type=Claim)
    except msgspec.ValidationError as e:
        reasons.append(f"msgspec: {e}")

    # member: jsonschema ladder + promotion + ceiling length
    S = {"type": "object",
         "required": ["verdict", "promotion_allowed", "claim_ceiling"],
         "properties": {
             "verdict": {"enum": ["PARKED", "BLOCKED", "ADMIT_FOR_TESTING"]},
             "promotion_allowed": {"const": False},
             "claim_ceiling": {"type": "string",
                               "minLength": params["min_ceiling_chars"]}}}
    try:
        jsonschema.validate(claim, S)
    except jsonschema.ValidationError as e:
        reasons.append(f"jsonschema: {e.message}")

    # member: portion range on confidence
    c = claim.get("confidence")
    if not isinstance(c, (int, float)) or c not in P.closed(0.0, 1.0):
        reasons.append(f"portion: confidence {c} outside [0,1] — not a possible value")

    # member: celpy rule as DATA
    try:
        env = celpy.Environment()
        prog = env.program(env.compile(
            "promotion_allowed == false && size(claim_ceiling) >= 10"))
        if not bool(prog.evaluate({
                "promotion_allowed": celpy.json_to_cel(claim.get("promotion_allowed")),
                "claim_ceiling": celpy.json_to_cel(str(claim.get("claim_ceiling", "")))})):
            reasons.append("celpy: rule 'no promotion and a real ceiling' failed")
    except Exception as e:
        reasons.append(f"celpy: {type(e).__name__}")

    # member: icontract precondition — a claim may not out-confidence its ceiling
    @icontract.require(lambda conf, ceil_len: not (conf > 0.9 and ceil_len < 30),
                       "high confidence requires a specific ceiling")
    def confidence_gate(conf: float, ceil_len: int): return True
    try:
        confidence_gate(float(c or 0), len(str(claim.get("claim_ceiling", ""))))
    except (icontract.ViolationError, TypeError, ValueError):
        reasons.append("icontract: confidence > 0.9 with a vague ceiling")

    # member: SDG structure — no causal/agent language without a packet
    txt = str(claim.get("finding", "")).lower()
    if any(w in txt for w in ("causes", "leads to", "because of")) and \
            "causal_packet" not in claim:
        reasons.append("SDG: causal language without a causal packet")
    return claim, reasons

# ------------------------------------------------------------ W-VERIFY
def verify(sm, spawned, returned, gated):
    return {"conserved_stratum_intact": sm.verify_conserved(),
            "count_law": {"spawned": spawned, "completed": returned,
                          "counted": returned, "holds": returned <= spawned},
            "admitted": sum(1 for g in gated if not g["reasons"]),
            "refused": sum(1 for g in gated if g["reasons"])}

# ------------------------------------------------- W-AUTORESEARCH
def autoresearch(gated, params, receipt_dir):
    """score THIS cycle, tune, write back only if a measure moved"""
    from collections import Counter
    fired = Counter()
    for g in gated:
        for r in g["reasons"]:
            fired[r.split(":")[0]] += 1
    n = max(len(gated), 1)
    rate = sum(fired.values()) / n
    prev = params.get("last_refusal_rate")
    useful = 0.0 if rate == 0 else min(1.0, 1.0 / (1.0 + abs(rate - 1.0)))
    moved = prev is None or abs(rate - prev) > 1e-9
    tuned = json.loads(json.dumps(params))
    tuned["last_refusal_rate"] = round(rate, 4)
    tuned["members_fired"] = dict(fired)
    tuned["cycles"] = params.get("cycles", 0) + (1 if moved else 0)
    if moved:
        TUNED.parent.mkdir(exist_ok=True)
        TUNED.write_text(json.dumps(tuned, indent=1, sort_keys=True))
    return {"members_fired": dict(fired), "refusals_per_claim": round(rate, 3),
            "usefulness": round(useful, 3), "measure_moved": moved,
            "wrote_back": moved, "cycle": tuned["cycles"]}

# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--skill", default="premortem")
    ap.add_argument("--voices", default="hume,popper,zhuangzi,feynman,pushback")
    ap.add_argument("--intent", default="")
    a = ap.parse_args()
    t0 = time.time()
    params = json.loads(TUNED.read_text()) if TUNED.exists() else \
        {"min_ceiling_chars": 10, "cycles": 0}
    params.setdefault("min_ceiling_chars", 10)

    sm = StrategyMemory(
        prompt_intent=a.intent or a.task,
        success_condition="each voice returns a typed claim that survives the "
                          "deterministic gate stack",
        claim_ceiling="machinery and format only; CB never decides truth")
    sm.kill("a model may set its own verdict")

    skill_path, skill_text = load_skill(a.skill)
    voices = [v.strip() for v in a.voices.split(",") if v.strip() in VOICE_MMM]
    shape = {"verdict": "PARKED", "promotion_allowed": False,
             "claim_ceiling": "<what this claim does not cover>",
             "confidence": 0.5, "finding": "<one sentence>"}

    print(f"CB RUN  task={a.task[:70]!r}")
    print(f"  skill: {a.skill} -> {skill_path or 'NOT FOUND'} "
          f"({len(skill_text)} chars loaded as frame)")
    print(f"  voices: {voices}")

    jobs = build_jobs(sm, skill_text, voices, a.task, shape)
    dg = diversity_gate(jobs)
    print(f"\nW-PROMPT  diversity {dg['verdict']} "
          f"(max overlap {dg['max_overlap']}, dups {dg['duplicates']})")
    if dg["verdict"] == "COLLAPSED":
        print("  REFUSED before dispatch: one opinion in many hats")
        return 1

    rundir = REPO / "constraint_box" / "receipts" / f"cbrun_{time.strftime('%Y%m%dT%H%M%SZ')}"
    res, spawned = dispatch(jobs, rundir)
    print(f"W-COUNCIL  spawned {spawned}  completed {len(res)}")

    gated = []
    for jid, raw in res.items():
        claim, reasons = gate_claim(raw, params)
        gated.append({"id": jid, "claim": claim, "reasons": reasons})
    print(f"\nW-GATE")
    for g in gated:
        v = (g["claim"] or {}).get("verdict", "—")
        print(f"  {g['id']:<18}{'ADMITTED' if not g['reasons'] else 'REFUSED':<10}"
              f"claim_verdict={v:<18}{len(g['reasons'])} refusal(s)")
        for r in g["reasons"][:2]:
            print(f"        - {r[:110]}")

    ver = verify(sm, spawned, len(res), gated)
    print(f"\nW-VERIFY  conserved={ver['conserved_stratum_intact']}  "
          f"count law {ver['count_law']['completed']}/{ver['count_law']['spawned']} "
          f"holds={ver['count_law']['holds']}  admitted={ver['admitted']} "
          f"refused={ver['refused']}")

    ar = autoresearch(gated, params, rundir)
    print(f"W-AUTORESEARCH  members fired {ar['members_fired']}  "
          f"refusals/claim {ar['refusals_per_claim']}  "
          f"wrote_back={ar['wrote_back']} cycle={ar['cycle']}")

    receipt = {"schema": "cb.run.v1", "task": a.task, "skill": a.skill,
               "skill_path": skill_path, "voices": voices,
               "W_PROMPT": dg, "W_COUNCIL": {"spawned": spawned, "completed": len(res)},
               "W_GATE": [{"id": g["id"], "admitted": not g["reasons"],
                           "reasons": g["reasons"], "claim": g["claim"]} for g in gated],
               "W_VERIFY": ver, "W_AUTORESEARCH": ar,
               "strategy_memory": sm.receipt(),
               "wall_seconds": round(time.time() - t0, 1),
               "promotion_allowed": False,
               "claim_ceiling": "format, shape and machinery only; CB does not "
                                "decide whether any finding is true"}
    (rundir / "CB_RUN_RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"\nRECEIPT {rundir.name}/CB_RUN_RECEIPT.json  ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
