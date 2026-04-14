#!/usr/bin/env python3
"""Lane B classical sweep runner.

Fires every sim whose classification == "classical_baseline" (or whose imports
are numpy/sympy-only, implying classical substrate) without gate ceremony.
Lane B results are never promoted to canonical — divergences are boundary data.

Usage:
    classical_sweep_runner.py --dry-run
    classical_sweep_runner.py --minutes 30 [--max-parallel 4]
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROBES_DIR = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes")
ARCHIVE_NAME = "_archive_lane_c"
REPORT_DIR = PROBES_DIR / "a2_state" / "sim_results"
PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"

MPLCONFIGDIR = "/tmp/codex-mpl"
NUMBA_CACHE_DIR = "/tmp/codex-numba"

CLASSIFICATION_RE = re.compile(
    r'''^\s*classification\s*=\s*["']([^"']+)["']''', re.MULTILINE
)

# Modules we consider "classical substrate" if they are the ONLY third-party
# imports in a file with missing classification.
CLASSICAL_STDLIB_OR_ALLOWED = {
    "numpy", "sympy",
    # stdlib-ish (anything from stdlib is fine; explicit allowlist for common names)
    "os", "sys", "json", "math", "time", "typing", "pathlib", "argparse",
    "dataclasses", "collections", "itertools", "functools", "re", "random",
    "subprocess", "datetime", "hashlib", "copy", "ast", "textwrap",
    "warnings", "contextlib", "enum", "fractions", "decimal", "statistics",
}


def child_env() -> dict:
    env = dict(os.environ)
    env["MPLCONFIGDIR"] = MPLCONFIGDIR
    env["NUMBA_CACHE_DIR"] = NUMBA_CACHE_DIR
    return env


def extract_classification(src: str) -> str | None:
    m = CLASSIFICATION_RE.search(src)
    return m.group(1) if m else None


def top_level_imports(src: str) -> set[str] | None:
    """Return the set of top-level import roots, or None if parse fails."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import, local package
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def is_classical_by_substrate(imports: set[str]) -> bool:
    """True iff every import is in the classical allowlist AND numpy is used."""
    if "numpy" not in imports:
        return False
    return all(imp in CLASSICAL_STDLIB_OR_ALLOWED for imp in imports)


def select_sims(include_heuristic: bool = False) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Return (selected, ambiguous). ambiguous = (path, reason).

    Default: only files with explicit classification="classical_baseline".
    If include_heuristic=True, also select files lacking classification whose
    imports are numpy/sympy-only (classical substrate).
    """
    selected: list[Path] = []
    ambiguous: list[tuple[Path, str]] = []

    for path in sorted(PROBES_DIR.rglob("sim_*.py")):
        if ARCHIVE_NAME in path.parts:
            continue
        if path.name.endswith(" 2.py"):
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            ambiguous.append((path, f"read_error: {exc}"))
            continue

        cls = extract_classification(src)
        if cls == "classical_baseline":
            selected.append(path)
            continue
        if cls == "canonical":
            continue
        if cls is not None:
            ambiguous.append((path, f"unknown_classification={cls!r}"))
            continue

        # classification missing
        if not include_heuristic:
            continue  # strict mode: require explicit declaration
        imports = top_level_imports(src)
        if imports is None:
            ambiguous.append((path, "syntax_error_in_parse"))
            continue
        if is_classical_by_substrate(imports):
            selected.append(path)
        # else: missing classification + non-classical imports → skip silently

    return selected, ambiguous


def run_one(path: Path, timeout_s: int = 600) -> dict:
    t0 = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=child_env(),
            cwd=str(PROBES_DIR),
        )
        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = -1
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timed_out = True
    dur = time.time() - t0

    # Look for an accompanying result JSON the sim may have written.
    result_json_path = None
    all_pass = None
    candidate = path.with_suffix(".json")
    if candidate.exists():
        result_json_path = str(candidate)
        try:
            data = json.loads(candidate.read_text())
            if isinstance(data, dict):
                if "all_pass" in data:
                    all_pass = bool(data["all_pass"])
                elif "pass" in data:
                    all_pass = bool(data["pass"])
        except (OSError, json.JSONDecodeError):
            pass

    return {
        "name": path.name,
        "path": str(path),
        "exit_code": exit_code,
        "duration_s": round(dur, 3),
        "timed_out": timed_out,
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
        "result_json_path": result_json_path,
        "result_all_pass": all_pass,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=None,
                    help="Time budget in minutes. Omit = run to completion.")
    ap.add_argument("--max-parallel", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=600,
                    help="Per-sim timeout in seconds (default 600).")
    ap.add_argument("--include-heuristic", action="store_true",
                    help="Also select sims lacking explicit classification "
                         "whose imports are numpy/sympy-only (legacy behavior).")
    args = ap.parse_args()

    selected, ambiguous = select_sims(include_heuristic=args.include_heuristic)

    if args.dry_run:
        print(f"classical_sweep_runner DRY RUN")
        print(f"selected: {len(selected)}")
        print(f"ambiguous: {len(ambiguous)}")
        for p in selected[:10]:
            print(f"  [sel] {p.name}")
        for p, reason in ambiguous[:20]:
            print(f"  [amb] {p.name}: {reason}")
        return 0

    os.makedirs(MPLCONFIGDIR, exist_ok=True)
    os.makedirs(NUMBA_CACHE_DIR, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    deadline = None
    if args.minutes is not None:
        deadline = time.time() + args.minutes * 60.0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"classical_sweep_{ts}.json"

    rows: list[dict] = []
    skipped: list[str] = []
    n = len(selected)
    started = 0
    completed = 0

    def budget_ok() -> bool:
        return deadline is None or time.time() < deadline

    with cf.ThreadPoolExecutor(max_workers=max(1, args.max_parallel)) as ex:
        futures: dict[cf.Future, Path] = {}
        it = iter(selected)

        # prime
        for _ in range(min(args.max_parallel, n)):
            try:
                p = next(it)
            except StopIteration:
                break
            if not budget_ok():
                skipped.append(p.name)
                continue
            futures[ex.submit(run_one, p, args.timeout)] = p
            started += 1

        while futures:
            done, _ = cf.wait(futures, return_when=cf.FIRST_COMPLETED)
            for fut in done:
                p = futures.pop(fut)
                try:
                    row = fut.result()
                except Exception as exc:  # noqa: BLE001
                    row = {
                        "name": p.name, "path": str(p),
                        "exit_code": -2, "duration_s": 0.0,
                        "timed_out": False,
                        "stdout_tail": "", "stderr_tail": f"runner_exception: {exc}",
                        "result_json_path": None, "result_all_pass": None,
                    }
                rows.append(row)
                completed += 1
                print(
                    f"[{completed}/{n}] {row['name']} "
                    f"exit={row['exit_code']} dur={row['duration_s']}s "
                    f"pass={row['result_all_pass']}"
                )
                # feed next
                if budget_ok():
                    try:
                        np_ = next(it)
                        futures[ex.submit(run_one, np_, args.timeout)] = np_
                        started += 1
                    except StopIteration:
                        pass

        # anything not started because budget ran out
        for p in it:
            skipped.append(p.name)

    report = {
        "timestamp_utc": ts,
        "python": PYTHON,
        "probes_dir": str(PROBES_DIR),
        "selected_count": n,
        "started_count": started,
        "completed_count": completed,
        "skipped_due_to_budget": skipped,
        "ambiguous": [{"path": str(p), "reason": r} for p, r in ambiguous],
        "minutes_budget": args.minutes,
        "max_parallel": args.max_parallel,
        "per_sim_timeout_s": args.timeout,
        "rows": rows,
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nreport: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
