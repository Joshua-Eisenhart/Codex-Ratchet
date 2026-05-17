#!/usr/bin/env python3
"""hostile_search_audit_gate.py — third-gate runner.

The hostile_search pipeline has two automated gates:
  1. light gate (parse + required functions + no banned identifiers)
  2. runs gate (main() executes without exception in 30s)

This script adds the third gate: a reviewer audit. It walks every receipts/
hostile_search/<lego>_<ts>/ directory, identifies runs-gate survivors, and
writes a per-survivor audit-prompt file plus an AUDIT_QUEUE.md listing all
survivors awaiting reviewer audit.

Usage from inside Claude session:
  python hostile_search_audit_gate.py
then read AUDIT_QUEUE.md and spawn one code-reviewer subagent per row using
its `audit_prompt.txt`. Each subagent writes its verdict to
AUDIT_<attack_basename>.md alongside the survivor.

Subagents can't be spawned by a python script — they're spawned by the parent
Claude session via the Agent tool. This script's job is to prepare the queue
deterministically so the session just iterates the rows.
"""
import importlib.util
import json
import signal
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE / "receipts" / "hostile_search"
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
RUN_BUDGET_S = 30


# Runs-gate snippet — MUST match hostile_search_summary.py exactly:
# an attack that exits 0 but prints KILLED on its own positive/negative/
# boundary test is a corpse, NOT a survivor. The previous version of this
# gate let those through and contaminated the audit queue with self-killed
# attacks. Keep this snippet in sync with hostile_search_summary.RUN_SNIPPET.
RUN_SNIPPET = """
import sys, io, importlib.util, signal, contextlib
def _to(s,f): raise TimeoutError()
signal.signal(signal.SIGALRM, _to); signal.alarm({budget})
spec = importlib.util.spec_from_file_location('m', sys.argv[1])
m = importlib.util.module_from_spec(spec)
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        spec.loader.exec_module(m)
        r = m.main() if hasattr(m,'main') else None
    captured = buf.getvalue()
    if 'KILLED' in captured:
        first = next((ln for ln in captured.splitlines() if 'KILLED' in ln), 'KILLED')
        print(f'FAIL:SelfKilled:{{first[:200]}}')
    else:
        print('OK')
except Exception as e:
    print(f'FAIL:{{type(e).__name__}}:{{str(e)[:200]}}')
""".format(budget=RUN_BUDGET_S)


AUDIT_PROMPT_TEMPLATE = """Audit one survivor file from a hostile-search proposal round on a 4-qubit-carrier math primitive.

Lego under test: `{lego_name}`
Spec: {lego_math}

File: `{path}`

It has already passed two gates:
1. Light gate: parses, has run_positive/run_negative/run_boundary/main, no banned-jargon identifiers
2. Runs gate: main() executes without exception in {budget}s AND emits no `KILLED` status in stdout (self-killed attacks — files that report KILLED on their own positive/negative/boundary tests — are filtered before reaching this queue)

Attack metadata:
- pool: {pool}
- attack_shape: {attack_shape}
- mmm_language: {mmm}
- response_chars: {chars}, wall_seconds: {wall}

What to check, priority order:

1. Is the math actually right? Specifically the positive test ({positive_test}) — does the code's main() output evidence that constraint actually holds, or does it print "SURVIVED" without computing it?
2. Is the negative control ({negative_test}) genuine, or is it the shallowest possible negative (e.g. flipping a sign / setting a parameter to 0)? A strong negative perturbation should be a fraction of the positive threshold.
3. Is the boundary test ({boundary_test}) exercised non-trivially?
4. Any hidden cheats — synthetic returns, hardcoded test values, hash-based distinguishers, decorative tools in TOOL_MANIFEST that are imported but never invoked, identity-channel disguised as non-trivial?
5. Strictest honest claim ceiling if this file were promoted into `system_v4/probes/`.
6. The strongest negative control this file does NOT yet run.

Report under 400 words. Tag each finding P0 (blocks promotion) / P1 (must fix before promotion) / P2 (nice to have). End with one line: VERDICT: PROMOTION_READY | PROMOTION_BLOCKED | NEEDS_REVISION.
"""


def runs_gate(path: Path) -> bool:
    if path.suffix == ".md":
        return False  # naming-audit is gate-neutral, not a survivor to audit
    try:
        r = subprocess.run([PYTHON_BIN, "-c", RUN_SNIPPET, str(path)],
                           capture_output=True, text=True, timeout=RUN_BUDGET_S + 10)
        out = (r.stdout + r.stderr).strip().splitlines()
        return bool(out) and out[-1] == "OK"
    except Exception:
        return False


def main():
    spec_mod_spec = importlib.util.spec_from_file_location("p", HERE / "propose_axis_lego.py")
    p = importlib.util.module_from_spec(spec_mod_spec)
    spec_mod_spec.loader.exec_module(p)
    queue_rows = []

    runs = sorted([d for d in ROOT.iterdir() if d.is_dir() and (d / "manifest.json").exists()])
    for run_dir in runs:
        manifest = json.loads((run_dir / "manifest.json").read_text())
        key = manifest["primitive_key"]
        if key not in p.PRIMITIVE_SPECS:
            continue
        lego_spec = p.PRIMITIVE_SPECS[key]
        for r in manifest.get("receipts", []):
            if not r.get("passed_gate"):
                continue
            if r.get("attack_shape") == "naming_audit":
                continue
            attack_path = run_dir / r["attack_path"]
            if not attack_path.exists():
                continue
            if not runs_gate(attack_path):
                continue
            # already audited?
            audit_path = run_dir / f"AUDIT_{attack_path.stem}.md"
            if audit_path.exists():
                continue
            # write audit prompt
            prompt_path = run_dir / f"audit_prompt_{attack_path.stem}.txt"
            prompt_path.write_text(AUDIT_PROMPT_TEMPLATE.format(
                lego_name=lego_spec["name"], lego_math=lego_spec["math"],
                path=str(attack_path), budget=RUN_BUDGET_S,
                pool=r["pool"], attack_shape=r["attack_shape"], mmm=r["mmm_language"],
                chars=r["response_chars"], wall=r["wall_seconds"],
                positive_test=lego_spec["positive_test"],
                negative_test=lego_spec["negative_test"],
                boundary_test=lego_spec["boundary_test"],
            ))
            queue_rows.append({
                "lego": key,
                "attack": attack_path.stem,
                "run_dir": str(run_dir.name),
                "audit_prompt_file": prompt_path.name,
                "audit_output_file": audit_path.name,
            })

    queue_md = ["# Audit queue — hostile-search survivors awaiting reviewer audit", ""]
    if not queue_rows:
        queue_md.append("Queue is empty: every runs-gate survivor has an audit on disk, or there are no survivors yet.")
    else:
        queue_md.append(f"{len(queue_rows)} survivor(s) await reviewer audit.")
        queue_md.append("")
        queue_md.append("| Lego | Attack | Audit prompt | Audit output |")
        queue_md.append("|---|---|---|---|")
        for q in queue_rows:
            queue_md.append(f"| `{q['lego']}` | `{q['attack']}` | `{q['run_dir']}/{q['audit_prompt_file']}` | `{q['run_dir']}/{q['audit_output_file']}` |")
    (ROOT / "AUDIT_QUEUE.md").write_text("\n".join(queue_md) + "\n")
    print(f"queue rows: {len(queue_rows)} → {ROOT / 'AUDIT_QUEUE.md'}")


if __name__ == "__main__":
    main()
