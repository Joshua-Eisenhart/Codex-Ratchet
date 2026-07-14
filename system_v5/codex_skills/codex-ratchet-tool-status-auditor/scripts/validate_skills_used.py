#!/usr/bin/env python3
"""Validate a hash-bound Codex Ratchet ``skills_used`` sidecar receipt.

This validator proves only the consistency of the local file-command-artifact
chain described by the receipt. It does not attest that a tool API was
load-bearing and it does not promote scientific claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


RECEIPT_SCHEMA = "codex-ratchet-skills-used-v1"
VERDICT_SCHEMA = "codex-ratchet-skills-used-verdict-v1"
TOP_LEVEL_KEYS = {"schema", "receipt_id", "commands", "skills_used"}
SKILL_KEYS = {"path", "sha256", "role", "affected_commands"}
COMMAND_KEYS = {"id", "argv", "exit_code", "output_artifacts"}
ARTIFACT_KEYS = {"path", "sha256"}
ROLES = {"guidance", "executable_validator", "executable_runner"}
EXECUTABLE_ROLES = {"executable_validator", "executable_runner"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_scoped_file(
    raw_path: Any,
    *,
    repo_root: Path,
    allowed_roots: tuple[Path, ...],
    field: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{field} must be a non-empty path string")
        return None
    if raw_path.startswith("~"):
        errors.append(f"{field} may not use '~'; record the exact path")
        return None

    requested = Path(raw_path)
    candidate = requested if requested.is_absolute() else repo_root / requested
    resolved = candidate.resolve(strict=False)
    if not any(_is_within(resolved, root) for root in allowed_roots):
        errors.append(f"{field} escapes the allowed roots: {raw_path}")
        return None
    if not resolved.is_file():
        errors.append(f"{field} is not an existing file: {raw_path}")
        return None
    return resolved


def _check_exact_keys(value: dict[str, Any], expected: set[str], field: str, errors: list[str]) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        errors.append(f"{field} keys must be exact; missing={missing}, extra={extra}")


def _check_hash(
    recorded: Any,
    path: Path | None,
    *,
    field: str,
    errors: list[str],
) -> None:
    if not isinstance(recorded, str) or SHA256_RE.fullmatch(recorded) is None:
        errors.append(f"{field} must be exactly 64 lowercase hexadecimal characters")
        return
    if path is None:
        return
    try:
        current = sha256_file(path)
    except OSError as exc:
        errors.append(f"{field} could not hash {path}: {exc}")
        return
    if current != recorded:
        errors.append(f"{field} does not match current bytes for {path}")


def _nearest_skill_root(path: Path) -> Path | None:
    for parent in path.parents:
        if (parent / "SKILL.md").is_file():
            return parent
    return None


def _argv_invokes_path(argv: list[str], target: Path, repo_root: Path) -> bool:
    for token in argv:
        candidate = Path(token)
        resolved = candidate if candidate.is_absolute() else repo_root / candidate
        if resolved.resolve(strict=False) == target:
            return True
    return False


def _blocked_verdict(errors: list[str], counts: dict[str, int]) -> dict[str, Any]:
    return {
        "schema": VERDICT_SCHEMA,
        "all_pass": False,
        "errors": errors,
        "counts": counts,
        "max_skill_provenance_level": "BLOCKED",
        "l3_eligible": False,
        "external_runner_receipt_required": False,
        "claim_ceiling": "blocked; no skill-use claim is admitted",
    }


def validate_receipt(
    payload: Any,
    *,
    repo_root: Path,
    extra_allowed_roots: tuple[Path, ...] = (),
) -> dict[str, Any]:
    """Return a deterministic verdict for one parsed receipt payload."""

    root = repo_root.resolve(strict=True)
    allowed_roots = tuple(dict.fromkeys((root, *(path.resolve(strict=True) for path in extra_allowed_roots))))
    errors: list[str] = []
    counts = {"guidance": 0, "executable_validator": 0, "executable_runner": 0}

    if not isinstance(payload, dict):
        return _blocked_verdict(["receipt must be a JSON object"], counts)

    _check_exact_keys(payload, TOP_LEVEL_KEYS, "receipt", errors)
    if payload.get("schema") != RECEIPT_SCHEMA:
        errors.append(f"schema must equal {RECEIPT_SCHEMA!r}")
    receipt_id = payload.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        errors.append("receipt_id must be a non-empty string")

    raw_commands = payload.get("commands")
    commands: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_commands, list):
        errors.append("commands must be a list")
        raw_commands = []

    for index, command in enumerate(raw_commands):
        field = f"commands[{index}]"
        if not isinstance(command, dict):
            errors.append(f"{field} must be an object")
            continue
        _check_exact_keys(command, COMMAND_KEYS, field, errors)
        command_id = command.get("id")
        if not isinstance(command_id, str) or not command_id.strip():
            errors.append(f"{field}.id must be a non-empty string")
            continue
        if command_id in commands:
            errors.append(f"duplicate command id: {command_id}")
            continue

        argv = command.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
            errors.append(f"{field}.argv must be a non-empty list of non-empty strings")
            argv = []
        exit_code = command.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            errors.append(f"{field}.exit_code must be an integer")

        raw_artifacts = command.get("output_artifacts")
        artifact_count = 0
        if not isinstance(raw_artifacts, list):
            errors.append(f"{field}.output_artifacts must be a list")
            raw_artifacts = []
        for artifact_index, artifact in enumerate(raw_artifacts):
            artifact_field = f"{field}.output_artifacts[{artifact_index}]"
            if not isinstance(artifact, dict):
                errors.append(f"{artifact_field} must be an object")
                continue
            _check_exact_keys(artifact, ARTIFACT_KEYS, artifact_field, errors)
            artifact_path = _resolve_scoped_file(
                artifact.get("path"),
                repo_root=root,
                allowed_roots=allowed_roots,
                field=f"{artifact_field}.path",
                errors=errors,
            )
            _check_hash(
                artifact.get("sha256"),
                artifact_path,
                field=f"{artifact_field}.sha256",
                errors=errors,
            )
            if artifact_path is not None:
                artifact_count += 1

        commands[command_id] = {
            "argv": argv,
            "exit_code": exit_code,
            "artifact_count": artifact_count,
        }

    raw_skills = payload.get("skills_used")
    if not isinstance(raw_skills, list) or not raw_skills:
        errors.append("skills_used must be a non-empty list")
        raw_skills = []

    resolved_entries: list[dict[str, Any]] = []
    seen_entries: set[tuple[Path, str]] = set()
    for index, entry in enumerate(raw_skills):
        field = f"skills_used[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{field} must be an object")
            continue
        _check_exact_keys(entry, SKILL_KEYS, field, errors)
        path = _resolve_scoped_file(
            entry.get("path"),
            repo_root=root,
            allowed_roots=allowed_roots,
            field=f"{field}.path",
            errors=errors,
        )
        _check_hash(entry.get("sha256"), path, field=f"{field}.sha256", errors=errors)

        role = entry.get("role")
        if role not in ROLES:
            errors.append(f"{field}.role must be one of {sorted(ROLES)}")
            role = "invalid"
        else:
            counts[role] += 1

        affected = entry.get("affected_commands")
        if not isinstance(affected, list) or not all(isinstance(item, str) and item for item in affected):
            errors.append(f"{field}.affected_commands must be a list of non-empty command IDs")
            affected = []
        elif len(affected) != len(set(affected)):
            errors.append(f"{field}.affected_commands must not contain duplicates")

        if path is not None:
            identity = (path, role)
            if identity in seen_entries:
                errors.append(f"duplicate skill provenance entry for {path} with role {role}")
            seen_entries.add(identity)

        for command_id in affected:
            command = commands.get(command_id)
            if command is None:
                errors.append(f"{field}.affected_commands references unknown command: {command_id}")
            elif command["exit_code"] != 0:
                errors.append(f"{field}.affected_commands references nonzero command: {command_id}")

        if role == "guidance" and path is not None and path.name != "SKILL.md":
            errors.append(f"{field}.path must point to SKILL.md for role guidance")
        if role in EXECUTABLE_ROLES and not affected:
            errors.append(f"{field}.affected_commands must be non-empty for role {role}")

        resolved_entries.append({"field": field, "path": path, "role": role, "affected": affected})

    guidance_paths = {
        entry["path"]
        for entry in resolved_entries
        if entry["role"] == "guidance" and entry["path"] is not None
    }
    for entry in resolved_entries:
        if entry["role"] not in EXECUTABLE_ROLES or entry["path"] is None:
            continue
        field = entry["field"]
        path = entry["path"]
        skill_root = _nearest_skill_root(path)
        if skill_root is None or not _is_within(path, (skill_root / "scripts").resolve(strict=False)):
            errors.append(f"{field}.path must be under a skill scripts/ directory")
            continue
        skill_file = (skill_root / "SKILL.md").resolve(strict=True)
        if skill_file not in guidance_paths:
            errors.append(f"{field} requires a matching guidance entry for {skill_file}")
        for command_id in entry["affected"]:
            command = commands.get(command_id)
            if command is None:
                continue
            if not _argv_invokes_path(command["argv"], path, root):
                errors.append(f"{field} command {command_id} does not invoke the exact executable path")
            if command["artifact_count"] < 1:
                errors.append(f"{field} command {command_id} has no hash-bound output artifact")

    if errors:
        return _blocked_verdict(errors, counts)

    executable_count = counts["executable_validator"] + counts["executable_runner"]
    if executable_count:
        ceiling = (
            "L2 internal-consistency evidence only; executable use is self-reported and requires "
            "an independent hash-bound runner receipt for actual L3"
        )
    else:
        ceiling = "L2 hash-bound guidance declaration only; no executable or scientific evidence"
    return {
        "schema": VERDICT_SCHEMA,
        "all_pass": True,
        "errors": [],
        "counts": counts,
        "max_skill_provenance_level": "L2",
        "l3_eligible": bool(executable_count),
        "external_runner_receipt_required": bool(executable_count),
        "claim_ceiling": ceiling,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--allow-root", action="append", type=Path, default=[])
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    counts = {"guidance": 0, "executable_validator": 0, "executable_runner": 0}
    try:
        payload = json.loads(args.receipt.read_text(encoding="utf-8"))
        verdict = validate_receipt(
            payload,
            repo_root=args.repo_root,
            extra_allowed_roots=tuple(args.allow_root),
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        verdict = _blocked_verdict([f"could not validate receipt: {exc}"], counts)

    rendered = json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if verdict["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
