#!/usr/bin/env python3
"""Lint sim audit verdicts against current packet state.

This is a stale-audit guard. It intentionally reads the sim's current result
files and, when an audit claims a packet-level pass/ok state, reruns the
packet-local validator in a temporary overlay so validator result writes do not
touch the working sim directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_SIMS_ROOT = REPO / "system_v6" / "sims"
DEFAULT_PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")

POSITIVE_STATUS = re.compile(
    r"\b(PASS|PASSED|OK|GREEN|GENUINE|GENUINE_WITH_CAVEATS|ACCEPTED|CLEAN)\b",
    re.IGNORECASE,
)
NEGATIVE_STATUS = re.compile(
    r"\b(NEEDS_FIX|FAIL|FAILED|RED|REJECT|REJECTED|BLOCKED|NOT\s+OK|INVALID)\b",
    re.IGNORECASE,
)
STATUS_LINE = re.compile(r"^\s*(Bottom line|Overall verdict|Overall)\s*:\s*(.+?)\s*$", re.IGNORECASE)
SUPERSEDED_BY = re.compile(r"^\s*SUPERSEDED BY\s+([^\s`]+)\s*$", re.IGNORECASE | re.MULTILINE)
CLAIM_CEILING_LINE = re.compile(
    r"(?:"
    r"(?:exact\s+admissible\s+claim\s+ceiling|admissible\s+claim\s+ceiling)\s*:\s*(.+)"
    r"|`?claim_ceiling`?\s*[:=]\s*(.+)"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidatorResult:
    ok: bool
    command: list[str]
    returncode: int
    stdout_tail: str
    stderr_tail: str
    timed_out: bool = False


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def tail(text: str, limit: int = 2000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def marker_target(text: str) -> str | None:
    match = SUPERSEDED_BY.search(text)
    return match.group(1) if match else None


def audit_claims_positive(text: str) -> bool:
    for line in text.splitlines():
        match = STATUS_LINE.match(line)
        if not match:
            continue
        status = match.group(2)
        if NEGATIVE_STATUS.search(status):
            return False
        if POSITIVE_STATUS.search(status):
            return True
    return False


def clean_claim_ceiling(raw: str) -> str:
    raw = raw.strip()
    grouped = [*re.findall(r"`([^`]+)`", raw), *re.findall(r'"([^"]+)"', raw)]
    for item in grouped:
        match = re.match(r"\s*claim_ceiling\s*[:=]\s*(.+?)\s*$", item, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip("\"'`").rstrip(".").strip()
    for pattern in (
        r"claim_ceiling\s*[:=]\s*`([^`]+)`",
        r"claim_ceiling\s*[:=]\s*\"([^\"]+)\"",
        r"claim_ceiling\s*[:=]\s*'([^']+)'",
        r"claim_ceiling\s*[:=]\s*([^;,\)\n]+)",
    ):
        embedded = re.search(pattern, raw, re.IGNORECASE)
        if embedded:
            return embedded.group(1).strip().strip("\"'`").rstrip(".").strip()
    if grouped:
        useful = [item for item in grouped if item.strip().lower() != "claim_ceiling"]
        return (useful[0] if useful else grouped[0]).strip()
    raw = raw.lstrip("-* ").strip().strip("\"'`")
    raw = re.split(r"\s{2,}", raw, maxsplit=1)[0].strip()
    return raw.rstrip(".").strip()


def audit_claim_ceilings(text: str) -> set[str]:
    ceilings: set[str] = set()
    for line in text.splitlines():
        lowered = line.lower()
        if "source_claim_ceiling" in lowered or "source claim ceiling" in lowered:
            continue
        match = CLAIM_CEILING_LINE.search(line)
        if not match:
            continue
        ceiling = clean_claim_ceiling(match.group(0))
        if ceiling:
            ceilings.add(ceiling)
    return ceilings


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def result_claim_ceiling(sim_dir: Path) -> tuple[str | None, Path | None]:
    results_dir = sim_dir / "results"
    sim_id = sim_dir.name
    candidates = [
        results_dir / f"{sim_id}_results.json",
        results_dir / f"{sim_id}_envelope_results.json",
        results_dir / f"{sim_id}_python_results.json",
        results_dir / f"{sim_id}_julia_results.json",
        results_dir / f"{sim_id}_jax_results.json",
        results_dir / f"{sim_id}_pytorch_results.json",
    ]
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        obj = load_json(path)
        if isinstance(obj, dict) and isinstance(obj.get("claim_ceiling"), str):
            return obj["claim_ceiling"].strip(), path

    found: list[tuple[str, Path]] = []
    if results_dir.is_dir():
        for path in sorted(results_dir.glob("*.json")):
            if path in seen:
                continue
            obj = load_json(path)
            if isinstance(obj, dict) and isinstance(obj.get("claim_ceiling"), str):
                found.append((obj["claim_ceiling"].strip(), path))
    distinct = {value for value, _path in found}
    if len(distinct) == 1 and found:
        return found[0]
    return None, None


def find_validator(sim_dir: Path) -> Path | None:
    preferred = sim_dir / f"validate_{sim_dir.name}.py"
    if preferred.is_file():
        return preferred
    validators = sorted(sim_dir.glob("validate_*.py"))
    return validators[0] if validators else None


class TempRepoOverlay:
    def __init__(self) -> None:
        self._tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self.repo: Path | None = None

    def close(self) -> None:
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None
            self.repo = None

    def ensure(self) -> Path:
        if self.repo is not None:
            return self.repo
        self._tmpdir = tempfile.TemporaryDirectory(prefix="audit-consistency-")
        self.repo = Path(self._tmpdir.name) / "repo"
        self.repo.mkdir(parents=True)
        ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
        for name in ("scripts", "system_v4", "system_v5", "system_v6"):
            source = REPO / name
            if source.exists():
                shutil.copytree(source, self.repo / name, ignore=ignore)
        return self.repo


def run_validator(validator: Path, python: Path, timeout: float, overlay: TempRepoOverlay) -> ValidatorResult:
    tmp_repo = overlay.ensure()
    tmp_validator = tmp_repo / validator.relative_to(REPO)
    command = [str(python), rel(validator)]
    env = os.environ.copy()
    scripts_path = str(tmp_repo / "scripts")
    env["PYTHONPATH"] = scripts_path + os.pathsep + env.get("PYTHONPATH", "")
    try:
        completed = subprocess.run(
            [str(python), str(tmp_validator.relative_to(tmp_repo))],
            cwd=tmp_repo,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ValidatorResult(
            ok=False,
            command=command,
            returncode=124,
            stdout_tail=tail(exc.stdout or ""),
            stderr_tail=tail(exc.stderr or f"validator timed out after {timeout:g}s"),
            timed_out=True,
        )
    return ValidatorResult(
        ok=completed.returncode == 0,
        command=command,
        returncode=completed.returncode,
        stdout_tail=tail(completed.stdout),
        stderr_tail=tail(completed.stderr),
    )


def temp_overlay_error(result: ValidatorResult) -> bool:
    return (
        "not in the subpath of" in result.stderr_tail
        and str(REPO) in result.stderr_tail
        and "audit-consistency-" in result.stderr_tail
    )


def sim_dirs_from_arg(path: Path) -> list[Path]:
    path = path.resolve()
    if path.is_dir() and path.name == "sims":
        return sorted(child for child in path.iterdir() if child.is_dir())
    if path.is_dir() and path.parent.name == "sims":
        return [path]
    if path.is_dir():
        return sorted(child for child in path.iterdir() if child.is_dir())
    raise SystemExit(f"not a sim directory or sims root: {path}")


def lint_sim(sim_dir: Path, python: Path, timeout: float, overlay: TempRepoOverlay) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    audits = sorted(sim_dir.glob("audit_verdict*.md"))
    audit_texts = {path: read_text(path) for path in audits}

    if len(audits) > 1:
        newest = max(audits, key=lambda path: (path.stat().st_mtime_ns, path.name))
        audit_names = {path.name for path in audits}
        for audit in audits:
            if audit == newest:
                continue
            target = marker_target(audit_texts[audit])
            if target not in audit_names:
                flags.append(
                    {
                        "sim": rel(sim_dir),
                        "kind": "unsuperseded_audit_verdict",
                        "detail": (
                            f"{rel(audit)} is older than {newest.name} but lacks "
                            f"'SUPERSEDED BY {newest.name}'"
                        ),
                    }
                )

    result_ceiling, result_path = result_claim_ceiling(sim_dir)
    if result_ceiling is not None and result_path is not None:
        for audit, text in audit_texts.items():
            ceilings = audit_claim_ceilings(text)
            mismatches = sorted(ceiling for ceiling in ceilings if ceiling != result_ceiling)
            if mismatches:
                flags.append(
                    {
                        "sim": rel(sim_dir),
                        "kind": "claim_ceiling_mismatch",
                        "detail": (
                            f"{rel(audit)} states {mismatches}; "
                            f"{rel(result_path)} has {result_ceiling!r}"
                        ),
                    }
                )

    positive_audits = [audit for audit, text in audit_texts.items() if audit_claims_positive(text)]
    if positive_audits:
        validator = find_validator(sim_dir)
        if validator is not None:
            validator_result = run_validator(validator, python, timeout, overlay)
            if not validator_result.ok:
                kind = "validator_temp_overlay_error" if temp_overlay_error(validator_result) else "audit_pass_validator_red"
                for audit in positive_audits:
                    flags.append(
                        {
                            "sim": rel(sim_dir),
                            "kind": kind,
                            "detail": (
                                f"{rel(audit)} has a positive packet-level verdict, but fresh "
                                f"{rel(validator)} returned {validator_result.returncode}; "
                                f"stdout_tail={validator_result.stdout_tail!r}; "
                                f"stderr_tail={validator_result.stderr_tail!r}"
                            ),
                        }
                    )
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_SIMS_ROOT,
        help="A sim directory or sims root. Defaults to system_v6/sims.",
    )
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON, help="Interpreter for packet validators.")
    parser.add_argument("--validator-timeout", type=float, default=120.0, help="Seconds per packet validator.")
    args = parser.parse_args()

    flags: list[dict[str, str]] = []
    overlay = TempRepoOverlay()
    try:
        for sim_dir in sim_dirs_from_arg(args.path):
            flags.extend(lint_sim(sim_dir, args.python, args.validator_timeout, overlay))
    finally:
        overlay.close()

    payload = {"ok": not flags, "flags": flags}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
