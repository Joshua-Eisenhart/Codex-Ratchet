#!/usr/bin/env python3
"""Validate formal-scout result receipts."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULTS = ROOT / "results"
LAYER_COMPLETION_CLAIM_GATE = REPO_ROOT / "scripts" / "validate_layer_completion_claims.py"


def pass_values(section: dict[str, Any]) -> list[bool]:
    values = []
    for row in section.values():
        if isinstance(row, dict) and "pass" in row:
            values.append(bool(row["pass"]))
    return values


def validate(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_bytes().decode("utf-8"))
    errors = []
    if data.get("classification") != "formal_scout":
        errors.append("classification is not formal_scout")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed is not false")
    if not data.get("claim_ceiling"):
        errors.append("claim_ceiling missing")
    if "canonical" in str(data.get("claim_ceiling", "")).lower() and "does not admit" not in str(data.get("claim_ceiling", "")).lower():
        errors.append("claim_ceiling may overclaim")
    positives = data.get("positive")
    graveyards = data.get("graveyard_companions")
    if not isinstance(positives, dict) or not positives:
        errors.append("positive section missing")
    if not isinstance(graveyards, dict) or not graveyards:
        errors.append("graveyard_companions section missing")
    boundary = data.get("boundary")
    if not isinstance(boundary, dict) or not boundary:
        errors.append("boundary section missing")
    if not data.get("why_not_v4_probes"):
        errors.append("why_not_v4_probes missing")
    nearby = data.get("nearby_variants")
    if not isinstance(nearby, dict) or not nearby.get("total"):
        errors.append("nearby_variants summary missing")
    elif nearby.get("passed") != nearby.get("total"):
        errors.append("nearby_variants did not all pass")
    if isinstance(positives, dict) and False in pass_values(positives):
        errors.append("one or more positive checks failed")
    if isinstance(graveyards, dict) and False in pass_values(graveyards):
        errors.append("one or more graveyard checks failed")
    if isinstance(boundary, dict) and False in pass_values(boundary):
        errors.append("one or more boundary checks failed")
    if "rosetta_to_sim_contract" in data:
        errors.append("legacy rosetta_to_sim_contract key present")
    if data.get("blockers"):
        errors.append("blockers present")
    errors.extend(layer_completion_claim_errors(path))
    return {"path": str(path), "pass": not errors, "errors": errors}


def layer_completion_claim_errors(path: pathlib.Path) -> list[str]:
    if not LAYER_COMPLETION_CLAIM_GATE.exists():
        return [f"layer completion claim gate missing: {LAYER_COMPLETION_CLAIM_GATE}"]
    cmd = [sys.executable, str(LAYER_COMPLETION_CLAIM_GATE), "--evidence", str(path)]
    for claim_file in companion_claim_files(path):
        cmd.extend(["--claim-file", str(claim_file)])
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        return []
    detail = tail_text(proc.stdout or proc.stderr, 1200)
    return [f"layer completion claim gate failed: {detail}"]


def companion_claim_files(path: pathlib.Path) -> list[pathlib.Path]:
    candidates = [
        path.with_suffix(".md"),
        path.with_name(f"{path.stem}_report.md"),
        path.with_name(f"{path.stem}_closeout.md"),
    ]
    if path.name.endswith("_results.json"):
        stem = path.name.removesuffix("_results.json")
        candidates.extend(
            [
                path.with_name(f"{stem}.md"),
                path.with_name(f"{stem}_report.md"),
                path.with_name(f"{stem}_closeout.md"),
            ]
        )
    seen: set[pathlib.Path] = set()
    existing: list[pathlib.Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            existing.append(candidate)
    return existing


def script_for_result(path: pathlib.Path) -> pathlib.Path:
    stem = path.name
    if not stem.endswith("_results.json"):
        raise ValueError(f"result name does not end with _results.json: {path}")
    script_stem = stem.removesuffix("_results.json")
    direct_script = ROOT / f"{script_stem}.py"
    if script_stem.startswith("sim_") and direct_script.exists():
        return direct_script
    return ROOT / f"sim_{script_stem}.py"


def tail_text(value: str | bytes | None, limit: int = 800) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-limit:]
    return value[-limit:]


def fresh_rerun(path: pathlib.Path, timeout_seconds: int) -> dict[str, Any]:
    script = script_for_result(path)
    if not script.exists():
        return {
            "result": str(path),
            "script": str(script),
            "pass": False,
            "errors": ["matching scout script missing"],
        }
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "result": str(path),
            "script": str(script),
            "pass": False,
            "errors": [f"rerun timed out after {timeout_seconds}s"],
            "returncode": None,
            "stdout_tail": tail_text(exc.stdout),
            "stderr_tail": tail_text(exc.stderr),
        }
    errors = []
    if proc.returncode != 0:
        errors.append(f"rerun exited {proc.returncode}")
    if not path.exists():
        errors.append("expected result was not written")
    return {
        "result": str(path),
        "script": str(script),
        "pass": not errors,
        "errors": errors,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-800:],
        "stderr_tail": proc.stderr[-800:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=pathlib.Path)
    parser.add_argument(
        "--fresh-rerun",
        action="store_true",
        help="rerun matching scout scripts before validating result receipts",
    )
    parser.add_argument(
        "--fresh-rerun-timeout",
        type=int,
        default=120,
        help="timeout in seconds for each matching scout script rerun",
    )
    args = parser.parse_args()
    paths = args.paths or sorted(RESULTS.glob("*_results.json"))
    reruns = [fresh_rerun(path, args.fresh_rerun_timeout) for path in paths] if args.fresh_rerun else []
    rows = [validate(path) for path in paths]
    all_pass = all(row["pass"] for row in rows) and all(row["pass"] for row in reruns)
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "fresh_rerun": args.fresh_rerun,
                "reruns": reruns,
                "results": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
