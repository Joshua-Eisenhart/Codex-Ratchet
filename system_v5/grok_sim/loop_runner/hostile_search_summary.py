#!/usr/bin/env python3
"""hostile_search_summary.py — cross-lego corpus aggregator.

Walks receipts/hostile_search/, applies the runs-gate to every executable
attack across every lego, and writes a single CORPUS_SUMMARY.md.

Two-gate model (matches hostile_search.py):
  - light gate: parse + required functions + no banned-identifier hits (already
    recorded in each manifest.json)
  - runs gate: execute main() in a 30s-budgeted subprocess; survived iff exit 0
    AND no `KILLED` substring in captured stdout. A file that reports KILLED
    on its own positive/negative/boundary test is a corpse even though the
    process exited cleanly. See RUN_SNIPPET for the exact check.

Output: receipts/hostile_search/CORPUS_SUMMARY.md
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE / "receipts" / "hostile_search"
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
RUN_BUDGET_S = 30

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
    # gate: any KILLED line in main's stdout fails the runs gate
    if 'KILLED' in captured:
        # surface the first KILLED line
        first = next((ln for ln in captured.splitlines() if 'KILLED' in ln), 'KILLED')
        print(f'FAIL:SelfKilled:{{first[:200]}}')
    else:
        print('OK')
except Exception as e:
    print(f'FAIL:{{type(e).__name__}}:{{str(e)[:200]}}')
""".format(budget=RUN_BUDGET_S)


def execute_attack(path: Path) -> tuple[bool, str]:
    """Returns (survived_runs_gate, message). The runs gate now fails
    attacks whose own main() prints 'KILLED' even if no exception was raised
    — a file that reports its own test failed should not be a survivor."""
    if path.suffix == ".md":
        return True, "naming-audit md (non-executable by design)"
    try:
        r = subprocess.run(
            [PYTHON_BIN, "-c", RUN_SNIPPET, str(path)],
            capture_output=True, text=True, timeout=RUN_BUDGET_S + 10,
        )
        out = (r.stdout + r.stderr).strip().splitlines()
        last = out[-1] if out else ""
        if last == "OK":
            return True, "main() executed AND no KILLED in stdout"
        return False, last[:200] or f"exit={r.returncode}"
    except subprocess.TimeoutExpired:
        return False, f"timeout > {RUN_BUDGET_S}s"
    except Exception as e:
        return False, f"runner_error: {type(e).__name__}: {str(e)[:160]}"


def aggregate():
    if not ROOT.exists():
        print(f"no receipts dir: {ROOT}"); return
    runs = sorted([d for d in ROOT.iterdir() if d.is_dir() and (d / "manifest.json").exists()])
    if not runs:
        print(f"no manifests in {ROOT}"); return

    lines = [
        "# Hostile-search corpus summary",
        "",
        f"Aggregated from `{ROOT}`. Two-gate model:",
        "- **light gate** = parse + required functions + no banned identifiers (recorded at attack time)",
        f"- **runs gate** = `main()` executes without exception in {RUN_BUDGET_S}s",
        "",
        "Naming-audit attacks are non-executable by design; they are counted as gate-neutral receipts.",
        "",
        "## Per-lego results",
        "",
        "| Lego | Light surv | Runs surv (of exec) | Audits | Total attacks |",
        "|---|---|---|---|---|",
    ]

    totals = {"runs_total": 0, "runs_surv": 0, "light_total": 0, "light_surv": 0}
    detail_blocks = []

    for run_dir in runs:
        manifest = json.loads((run_dir / "manifest.json").read_text())
        key = manifest["primitive_key"]
        name = manifest.get("primitive_name", key)
        ts = manifest.get("timestamp_utc", "?")
        receipts = manifest.get("receipts", [])
        light_total = len(receipts)
        light_surv = sum(1 for r in receipts if r.get("passed_gate"))
        audits = sum(1 for r in receipts if r.get("attack_shape") == "naming_audit")

        # Apply runs gate to every light-gate survivor that's executable
        executable = [r for r in receipts if r.get("passed_gate") and r.get("attack_shape") != "naming_audit"]
        runs_results = []
        for r in executable:
            p = run_dir / r["attack_path"]
            if not p.exists():
                runs_results.append((r, False, "missing file"))
                continue
            ok, msg = execute_attack(p)
            runs_results.append((r, ok, msg))
        runs_total = len(executable)
        runs_surv = sum(1 for _, ok, _ in runs_results if ok)

        totals["runs_total"] += runs_total
        totals["runs_surv"] += runs_surv
        totals["light_total"] += light_total
        totals["light_surv"] += light_surv

        lines.append(f"| `{key}` | {light_surv}/{light_total} | {runs_surv}/{runs_total} | {audits} | {light_total} |")

        block = [f"### {name} (`{key}`, {ts})", ""]
        if runs_surv:
            block.append("**Runs-gate survivors:**")
            for r, ok, msg in runs_results:
                if ok:
                    block.append(f"- attack_{r['idx']:02d} · {r['pool']} · {r['attack_shape']} · {r['mmm_language']} → `{r['attack_path']}`")
            block.append("")
        if any(not ok for _, ok, _ in runs_results):
            block.append("**Graveyard (runs gate):**")
            for r, ok, msg in runs_results:
                if not ok:
                    block.append(f"- attack_{r['idx']:02d} · {r['pool']} · {r['attack_shape']} · {r['mmm_language']} — *{msg}*")
            block.append("")
        if audits:
            block.append(f"**Naming-audit receipts:** {audits} markdown audit(s) present.")
            block.append("")
        detail_blocks.append("\n".join(block))

    lines.append("")
    lines.append(f"**Corpus totals:** runs-gate survived {totals['runs_surv']}/{totals['runs_total']} executable, "
                 f"light-gate survived {totals['light_surv']}/{totals['light_total']} total.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.extend(detail_blocks)

    out = ROOT / "CORPUS_SUMMARY.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")
    print(f"runs-gate: {totals['runs_surv']}/{totals['runs_total']} survived across {len(runs)} legos")


if __name__ == "__main__":
    aggregate()
