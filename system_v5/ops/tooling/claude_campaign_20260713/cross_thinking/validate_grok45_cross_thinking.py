#!/usr/bin/env python3
"""Validate the exact Grok 4.5 advisory artifact and its non-authority ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone
from typing import Any


HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
PROMPT = HERE / "grok45_cross_thinking_prompt.md"
RAW = HERE / "results" / "grok45_cross_thinking_raw.md"
RUNNER = HERE / "run_grok45_cross_thinking.py"
DEFAULT_RECEIPT = HERE / "results" / "grok45_cross_thinking_receipt.json"
PYTHON = pathlib.Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3")
SCHEMA = "codex-ratchet.grok-cross-thinking-receipt.v1"
CLAIM_CEILING = "External cross-thinking only; local executions, receipts, validators, and authority files decide truth."
PROMPT_RELATIVE = str(PROMPT.relative_to(REPO_ROOT))
RAW_RELATIVE = str(RAW.relative_to(REPO_ROOT))

TOP_KEYS = {
    "advisory_only", "claim_ceiling", "classification", "completed_at", "endpoint",
    "evidence_allowed", "promotion_allowed", "prompt", "provider", "provider_response_id",
    "raw_response", "requested_model", "returned_model", "route", "runner", "schema",
    "started_at", "status", "usage",
}
PROMPT_KEYS = {"path", "sha256"}
RAW_KEYS = {"nonempty", "path", "sha256"}
RUNNER_KEYS = {"command", "cwd", "git_head_before_run", "path", "python", "sha256"}
USAGE_KEYS = {"completion_tokens", "prompt_tokens", "total_tokens"}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_time(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be an ISO timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def require_exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(
            f"{label} keys mismatch: missing={sorted(expected - actual)} unknown={sorted(actual - expected)}"
        )
        return False
    return True


def git_commit_time(commit: str) -> datetime | None:
    try:
        completed = subprocess.run(
            ["git", "show", "-s", "--format=%cI", commit],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return datetime.fromisoformat(completed.stdout.strip()).astimezone(timezone.utc)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def git_is_ancestor(commit: str) -> bool:
    try:
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).returncode == 0
    except OSError:
        return False


def validate(receipt_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require_exact_keys(receipt, TOP_KEYS, "receipt", errors)

    expected = {
        "schema": SCHEMA,
        "provider": "xai",
        "route": "grok45.cross_thinking.codex_ratchet_campaign",
        "status": "completed",
        "classification": "provider_audit",
        "advisory_only": True,
        "evidence_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "requested_model": "grok-4.5",
        "returned_model": "grok-4.5",
        "endpoint": "https://api.x.ai/v1/chat/completions",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            errors.append(f"{key}: expected {value!r}, got {receipt.get(key)!r}")

    response_id = receipt.get("provider_response_id")
    if not isinstance(response_id, str) or not re.fullmatch(r"[0-9a-fA-F-]{36}", response_id):
        errors.append("provider_response_id is missing or malformed")

    started = parse_time(receipt.get("started_at"), "started_at", errors)
    completed = parse_time(receipt.get("completed_at"), "completed_at", errors)
    if started and completed:
        elapsed = (completed - started).total_seconds()
        if elapsed < 0 or elapsed > 600:
            errors.append("provider timestamp order/duration is invalid")

    prompt = receipt.get("prompt")
    if require_exact_keys(prompt, PROMPT_KEYS, "prompt", errors):
        if prompt.get("path") != PROMPT_RELATIVE:
            errors.append("prompt path identity mismatch")
        if not PROMPT.is_file() or prompt.get("sha256") != sha256_file(PROMPT):
            errors.append("prompt sha256 mismatch")

    raw = receipt.get("raw_response")
    if require_exact_keys(raw, RAW_KEYS, "raw_response", errors):
        if raw.get("path") != RAW_RELATIVE:
            errors.append("raw response path identity mismatch")
        if raw.get("nonempty") is not True or not RAW.is_file() or not RAW.read_text(encoding="utf-8").strip():
            errors.append("raw response is missing or empty")
        elif raw.get("sha256") != sha256_file(RAW):
            errors.append("raw_response.sha256 mismatch")

    runner = receipt.get("runner")
    if require_exact_keys(runner, RUNNER_KEYS, "runner", errors):
        if pathlib.Path(str(runner.get("path"))).resolve() != RUNNER.resolve():
            errors.append("runner path identity mismatch")
        if not RUNNER.is_file() or runner.get("sha256") != sha256_file(RUNNER):
            errors.append("runner sha256 mismatch")
        if pathlib.Path(str(runner.get("python"))).resolve() != PYTHON.resolve():
            errors.append("runner Python identity mismatch")
        expected_command = [str(PYTHON), str(RUNNER)]
        if runner.get("command") != expected_command:
            errors.append("runner command mismatch")
        if runner.get("cwd") != str(REPO_ROOT):
            errors.append("runner cwd mismatch")

        commit = runner.get("git_head_before_run")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit) or commit == "0" * 40:
            errors.append("runner git head is missing or malformed")
        else:
            commit_time = git_commit_time(commit)
            if commit_time is None or not git_is_ancestor(commit):
                errors.append("runner git head is not a valid ancestor commit")
            elif started and started < commit_time:
                errors.append("provider call predates the recorded runner commit")

    usage = receipt.get("usage")
    if require_exact_keys(usage, USAGE_KEYS, "usage", errors):
        values = [usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens")]
        if not all(isinstance(value, int) and value > 0 for value in values):
            errors.append("usage token counts must be positive integers")
        elif usage["total_tokens"] < usage["prompt_tokens"] + usage["completion_tokens"]:
            # xAI may include additional reasoning/cached accounting in total_tokens.
            errors.append("usage total is smaller than prompt plus completion")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", nargs="?", type=pathlib.Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    try:
        errors = validate(args.receipt.resolve())
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        errors = [f"parse failure: {error}"]
    print(json.dumps({"receipt_valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
