#!/usr/bin/env python3
"""Execute the frozen V8 nonofficial stress corpus without LLM gates or installs."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from typing import Any


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "campaign_spec.json"
PREREG_PATH = HERE / "preregistration.json"
PREREG_VALIDATOR = HERE / "validate_preregistration.py"
RESULTS = HERE / "results"
LOGS = RESULTS / "logs"
SNAPSHOTS = RESULTS / "pre_run_snapshots"
OUT = RESULTS / "campaign_execution.json"
WRITE_LOCK = threading.Lock()


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def resolve_artifact(raw: str, root: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else root / path


def expected_matches(expected: str, returncode: int) -> bool:
    if expected == "zero":
        return returncode == 0
    if expected == "nonzero":
        return returncode != 0
    return expected == "any"


def git_state(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "root": str(root),
        "returncode": proc.returncode,
        "porcelain": proc.stdout.splitlines(),
        "stderr": proc.stderr.strip(),
    }


def archive_preexisting(case: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    archived: list[dict[str, Any]] = []
    destination = SNAPSHOTS / case["case_id"]
    for index, raw in enumerate(case.get("required_artifacts", []), start=1):
        source = resolve_artifact(raw, root)
        before = file_state(source)
        row: dict[str, Any] = {"source": before, "snapshot": None}
        if source.is_file():
            destination.mkdir(parents=True, exist_ok=True)
            suffix = source.suffix or ".artifact"
            target = destination / f"{index:02d}_{source.stem}.{before['sha256'][:16]}{suffix}"
            if not target.exists():
                shutil.copy2(source, target)
            row["snapshot"] = file_state(target)
        archived.append(row)
    return archived


def run_step(
    case_id: str,
    step: dict[str, Any],
    root: Path,
    base_env: dict[str, str],
    default_timeout: int,
) -> dict[str, Any]:
    step_id = step["step_id"]
    cwd = Path(step.get("cwd", root))
    command = [str(part) for part in step["command"]]
    env = dict(base_env)
    env.update({str(key): str(value) for key, value in step.get("env", {}).items()})
    timeout_seconds = int(step.get("timeout_seconds", default_timeout))
    started = utc_now()
    started_mono = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stderr += f"\nTIMEOUT after {timeout_seconds}s"

    duration = time.monotonic() - started_mono
    log_dir = LOGS / case_id
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{step_id}.stdout.txt"
    stderr_path = log_dir / f"{step_id}.stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    expected = step["expected_exit"]
    matched = expected_matches(expected, returncode) and not timed_out
    return {
        "step_id": step_id,
        "receipt_role": step["receipt_role"],
        "command": command,
        "cwd": str(cwd),
        "env_overrides": step.get("env", {}),
        "started_at": started,
        "finished_at": utc_now(),
        "duration_seconds": round(duration, 6),
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "returncode": returncode,
        "expected_exit": expected,
        "expected_exit_observed": matched,
        "stdout": file_state(stdout_path),
        "stderr": file_state(stderr_path),
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }


def run_case(
    case: dict[str, Any],
    root: Path,
    base_env: dict[str, str],
    default_timeout: int,
    preexisting: list[dict[str, Any]],
) -> dict[str, Any]:
    case_started = utc_now()
    rows: list[dict[str, Any]] = []
    blocker: str | None = None
    for step in case["steps"]:
        if blocker is not None:
            rows.append({
                "step_id": step["step_id"],
                "receipt_role": step["receipt_role"],
                "command": step["command"],
                "expected_exit": step["expected_exit"],
                "executed": False,
                "expected_exit_observed": False,
                "blocked_by": blocker,
            })
            continue
        row = run_step(case["case_id"], step, root, base_env, default_timeout)
        row["executed"] = True
        rows.append(row)
        if not row["expected_exit_observed"]:
            blocker = step["step_id"]

    artifacts_after = [
        file_state(resolve_artifact(raw, root))
        for raw in case.get("required_artifacts", [])
    ]
    artifacts_present = all(row["exists"] for row in artifacts_after)
    outcomes_observed = all(row.get("executed") and row.get("expected_exit_observed") for row in rows)
    return {
        "case_id": case["case_id"],
        "cohort": case["cohort"],
        "claim_ceiling": case["claim_ceiling"],
        "started_at": case_started,
        "finished_at": utc_now(),
        "steps": rows,
        "pre_run_artifacts": preexisting,
        "artifacts_after": artifacts_after,
        "all_required_artifacts_present": artifacts_present,
        "all_expected_outcomes_observed": outcomes_observed,
        "case_execution_pass": outcomes_observed and artifacts_present,
    }


def write_receipt(receipt: dict[str, Any]) -> None:
    with WRITE_LOCK:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    if not 1 <= args.max_workers <= 3:
        raise SystemExit("--max-workers must be between 1 and 3")

    prereg_check = subprocess.run(
        [sys.executable, str(PREREG_VALIDATOR)],
        cwd=HERE,
        text=True,
        capture_output=True,
        check=False,
    )
    if prereg_check.returncode != 0:
        sys.stderr.write(prereg_check.stdout)
        sys.stderr.write(prereg_check.stderr)
        return 2

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    root = Path(spec["frozen_source_state"]["repo_root"])
    deep_root = Path(spec["frozen_source_state"]["deep_stack_repo_root"])
    first_rung_root = Path(spec["frozen_source_state"]["first_rung_repo_root"])
    lev_root = Path(spec["frozen_source_state"]["lev_repo_root"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    base_env = dict(os.environ)
    base_env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "JULIA_PKG_OFFLINE": "true",
        "JULIA_LOAD_PATH": spec["runtime_contract"]["julia_load_path"],
        "NUMBA_CACHE_DIR": spec["runtime_contract"]["numba_cache_dir"],
        "MPLCONFIGDIR": "/private/tmp/codex_mplconfig",
        "JAX_ENABLE_X64": "1",
    })

    preexisting = {
        case["case_id"]: archive_preexisting(case, root)
        for case in spec["cases"]
    }
    receipt: dict[str, Any] = {
        "schema": "codex_ratchet.v8_nonofficial_stress_campaign.execution.v1",
        "campaign_id": spec["campaign_id"],
        "started_at": utc_now(),
        "finished_at": None,
        "classification": spec["classification"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "llm_gate_used": False,
        "install_attempted": False,
        "spec_sha256": sha256(SPEC_PATH),
        "preregistration_sha256": sha256(PREREG_PATH),
        "preregistration_validator": {
            "returncode": prereg_check.returncode,
            "stdout": prereg_check.stdout,
            "stderr": prereg_check.stderr,
        },
        "git_state_before": [git_state(root), git_state(deep_root), git_state(first_rung_root), git_state(lev_root)],
        "cases": [],
        "blocked_cases": spec["blocked_cases"],
        "all_expected_outcomes_observed": False,
        "all_required_artifacts_present": False,
        "execution_integrity_pass": False,
        "all_systems_green": False,
    }
    write_receipt(receipt)

    completed: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {
            pool.submit(run_case, case, root, base_env, args.timeout, preexisting[case["case_id"]]): case["case_id"]
            for case in spec["cases"]
        }
        for future in concurrent.futures.as_completed(futures):
            case_id = futures[future]
            try:
                completed[case_id] = future.result()
            except Exception as exc:  # fail closed while preserving the campaign receipt
                completed[case_id] = {
                    "case_id": case_id,
                    "case_execution_pass": False,
                    "all_expected_outcomes_observed": False,
                    "all_required_artifacts_present": False,
                    "runner_exception": repr(exc),
                }
            receipt["cases"] = [completed[c["case_id"]] for c in spec["cases"] if c["case_id"] in completed]
            write_receipt(receipt)

    receipt["cases"] = [completed[case["case_id"]] for case in spec["cases"]]
    receipt["finished_at"] = utc_now()
    receipt["git_state_after"] = [git_state(root), git_state(deep_root), git_state(first_rung_root), git_state(lev_root)]
    receipt["all_expected_outcomes_observed"] = all(
        case.get("all_expected_outcomes_observed") is True for case in receipt["cases"]
    )
    receipt["all_required_artifacts_present"] = all(
        case.get("all_required_artifacts_present") is True for case in receipt["cases"]
    )
    receipt["execution_integrity_pass"] = (
        receipt["all_expected_outcomes_observed"]
        and receipt["all_required_artifacts_present"]
    )
    receipt["all_systems_green"] = False
    write_receipt(receipt)
    print(json.dumps({
        "out": str(OUT),
        "case_count": len(receipt["cases"]),
        "execution_integrity_pass": receipt["execution_integrity_pass"],
        "all_systems_green": False,
    }, indent=2, sort_keys=True))
    return 0 if receipt["execution_integrity_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
