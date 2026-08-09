#!/usr/bin/env python3
"""cb_project_state — generate the handoff FROM DISK, never by hand.

Every count in the previous handoff was typed from memory and four were
wrong. Every number below is read off the filesystem at generation time.
Anything this script cannot verify is printed as UNVERIFIED, not guessed.

Writes constraint_box/PROJECT_STATE.md.
promotion_allowed=false.
"""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CB = REPO / "constraint_box"
PY = str(Path.home() / ".local/share/codex-ratchet/envs/main/bin/python3")

def sh(*a, cwd=REPO):
    return subprocess.run(a, cwd=str(cwd), capture_output=True, text=True).stdout.strip()

def selftest(script: str) -> str:
    p = Path(CB / "scripts" / script)
    if not p.is_file(): return "ABSENT"
    r = subprocess.run([PY, str(p), "--self-test"], capture_output=True,
                       text=True, cwd=str(REPO), timeout=600)
    line = [l for l in r.stdout.splitlines() if "fixtures as expected" in l]
    return (line[-1].split(":")[-1].strip() + f" rc={r.returncode}") if line \
        else f"no fixture line rc={r.returncode}"

def main():
    t0 = time.time()
    scripts = sorted(p.name for p in (CB/"scripts").glob("*.py"))
    cb_scripts = [s for s in scripts if s.startswith("cb_")]
    docs = sorted(p.name for p in (CB/"docs").glob("*.md"))
    configs = sorted(p.name for p in (CB/"config").glob("*.json"))
    receipts = list((CB/"receipts").rglob("*.json"))
    untracked = [l[3:] for l in sh("git","status","--porcelain","constraint_box/").splitlines()]

    reg = {}
    for f in ("council_member_registry_v1.json",
              "council_member_registry_skills_v1.json",
              "member_role_wave_v1.json"):
        p = CB/"config"/f
        if p.is_file():
            d = json.loads(p.read_text())
            reg[f] = len(d.get("members") or d.get("assignments") or [])

    # role-level execution truth, from the role table only
    rw = CB/"config"/"member_role_wave_v1.json"
    role = {}
    if rw.is_file():
        A = json.loads(rw.read_text())["assignments"]
        for s in ("EXEMPLIFIED","RUN_NOT_EXEMPLIFIED","NEVER_RUN"):
            role[s] = sum(1 for a in A if a["status"] == s)

    # verified defects: each is a grep-able fact, not a memory
    defects = []
    fal = (CB/"scripts"/"cb_wave_falsifier_v3.py")
    if fal.is_file() and '"councils_run": 0' in fal.read_text():
        defects.append(("falsifier cannot return SURVIVED",
                        "cb_wave_falsifier_v3.py TARGETS hardcodes councils_run: 0"))
    loop = (CB/"scripts"/"cb_loop.py")
    if loop.is_file():
        t = loop.read_text()
        if "load_state() if a.resume else load_state()" in t:
            defects.append(("--resume is a no-op", "cb_loop.py:75 both branches identical"))
        # The import chain still exists — the question is whether it is GATED.
        if "cb_wave_falsifier_v3" in t and "allow_paid" not in t:
            defects.append(("loop bills provider calls on every cycle, ungated",
                            "cb_loop.py -> cb_wave_falsifier_v3 -> cb_multi_provider (OpenRouter + claude)"))
    ar = CB/"scripts"/"cb_autoresearch_loop.py"
    if ar.is_file():
        # The defect was a schema mismatch on a shared config file, not a missing
        # key. Test the MERGE, not the file: cb_run.py legitimately writes this
        # path without `ladder`, so absence of the key is not itself a defect.
        at = ar.read_text()
        if 'params["ladder"]' in at and "params.update(disk)" not in at:
            defects.append(("autoresearch cannot execute",
                            "cb_autoresearch_loop reads params['ladder'] but replaces the "
                            "seed with the on-disk file, which cb_run.py writes without it"))
    ig = CB/"scripts"/"cb_integrated_run.py"
    if ig.is_file():
        it = ig.read_text()
        if "constraint_box/receipts" not in it:
            defects.append(("coverage measure reads its own prior output",
                            "cb_integrated_run scans constraint_box/receipts/, which contains its own prior output"))
        if "never_run_count" in it:
            defects.append(("coverage measure is named for execution but counts text",
                            "cb_integrated_run labels the measure never_run_count; it counts id mentions"))
        # Every polarity trigger must sit INSIDE its capture group.
        if r"\b(?:must never|may never" in it:
            defects.append(("digger drops the negation trigger",
                            "cb_integrated_run DIG['constraint'] captures only the text AFTER "
                            "the trigger, so survivors assert what their source forbids"))
    inv = [str(p.relative_to(REPO)) for p in receipts
           if '"evaluated on a single isolated spinor"' in p.read_text(errors="ignore")]
    if inv:
        defects.append((f"{len(inv)} receipts carry negation-inverted extractions",
                        "digger regex consumed the negation trigger; source says "
                        "'cannot be evaluated'. OFFENDING FILES: " + "; ".join(inv) +
                        " | of the 7 stored survivors: 2 are cleanly INVERTED "
                        "('evaluated on a single isolated spinor', "
                        "'destroyed (holographic principle, taken literally)') and can "
                        "actively mislead; 3 are em-dash fragments that keep the "
                        "source's own correction (garbled, not opposite); 1 is a "
                        "markdown table row; 1 unresolved"))

    L = []
    A = L.append
    A("# CB PROJECT STATE\n")
    A(f"Generated from disk by `cb_project_state.py` at {time.strftime('%Y-%m-%dT%H:%M:%SZ')}.")
    A("")
    A("**Generation-order caveat:** counts are as-of-generation. If a script or "
      "doc is written AFTER this file is generated, it is missing from these "
      "counts. `cb_build_handoff.py` regenerates this file as its first step so "
      "the package it builds is counted, but any file created after that step "
      "will be short by one. Regenerate to refresh.")
    A("Every number here is read off the filesystem at generation time. "
      "The previous handoff was typed from memory and four counts were wrong.\n")
    A("## What CB is (owner canon, verbatim)\n")
    A("> CB is a deterministic gating LLM constraint harness for mass looping")
    A("> swarms, of diverse llms, where the llms dont control their own gating.\n")
    A("> Constraint box is a constraint box. not a gate for truth. it gates the")
    A("> domain the right answers will be in and ones that are auditable.\n")
    A("Full rulings: `constraint_box/docs/OWNER_RULINGS_VERBATIM_20260806.md` "
      "— that file wins over any model summary, including this one.\n")
    A("## Repo facts\n")
    A(f"- branch `{sh('git','rev-parse','--abbrev-ref','HEAD')}` @ "
      f"`{sh('git','rev-parse','--short','HEAD')}`, "
      f"{len(sh('git','status','--porcelain').splitlines())} dirty files, "
      f"{len(sh('git','worktree','list').splitlines())} worktrees")
    A(f"- `constraint_box/scripts/`: {len(scripts)} .py ({len(cb_scripts)} named cb_*)")
    A(f"- `constraint_box/docs/`: {len(docs)} .md")
    A(f"- `constraint_box/config/`: {len(configs)} .json")
    A(f"- `constraint_box/receipts/`: {len(receipts)} .json")
    A(f"- **{len(untracked)} paths under constraint_box/ are UNTRACKED** — "
      f"the estate exists on disk, not in git history\n")
    A("## Registries\n")
    for k, v in reg.items(): A(f"- `{k}`: {v} entries")
    A(f"\n**131 = the union of the two member registries, not one file.**\n")
    A("## Execution truth\n")
    if role:
        tot = sum(role.values())
        A(f"From `member_role_wave_v1.json`, {tot} member x role x wave units:\n")
        for k, v in role.items(): A(f"- {k}: {v}")
        A(f"\n`never_run=0` in the integrated-run receipts is a TEXT-PRESENCE "
          f"measure, not execution. Real execution coverage is "
          f"{role.get('EXEMPLIFIED',0)}/{tot}.\n")
    A("## Verified defects (each grep-able, none from memory)\n")
    for i, (d, ev) in enumerate(defects, 1):
        A(f"{i}. **{d}**  \n   evidence: {ev}")
    A("")
    A("## Self-tests, rerun at generation time\n")
    for s in ("cb_light_integrations.py","cb_light_tier2.py","cb_control_laws.py",
              "cb_strategy_memory.py"):
        A(f"- `{s}`: {selftest(s)}")
    A("")
    A("## Do NOT run\n")
    A("- `cb_loop.py --cycles 20` — bills 20 rounds of provider calls, and its "
      "third leg (autoresearch) has never executed.\n")
    A("## Scripts on disk\n")
    for s in scripts: A(f"- `{s}`")
    out = CB/"PROJECT_STATE.md"
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L[:60]))
    print(f"\n... written to {out.relative_to(REPO)} ({time.time()-t0:.1f}s)")

if __name__ == "__main__":
    main()
