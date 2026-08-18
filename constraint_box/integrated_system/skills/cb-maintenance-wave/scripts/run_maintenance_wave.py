#!/usr/bin/env python3
"""Run the model-free, mutation-free CB maintenance wave.

The runner is intentionally conservative. It hashes only paths named by the
invocation, classifies candidates, and writes one receipt. It never calls
``shutil.move``, ``unlink``, ``git commit``, or ``git push``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "constraintbox.maintenance-receipt.v1"
WAVE_ID = "cb-maintenance-wave-v1"
FRESHNESS_HOURS = 72

DENY_PREFIXES = (
    ".git",
    "Archive",
    "archive",
    "config",
    "requirements",
    "light_runtime",
    "zip_agent/src",
    "integrated_system/bin",
    "integrated_system/context",
    "integrated_system/mmms",
    "integrated_system/runtime_profiles",
    "integrated_system/scripts",
    "integrated_system/skills",
    "hooks",
    "fixtures",
    "experiments",
)
ALLOW_PREFIXES = (
    "integrated_system/runs",
    "receipts/generated",
    "RUNS",
)
PROTECTED_RUN_FILES = {
    "integrated_system/runs/_CURRENT_STATE",
    "integrated_system/runs/CURRENT.json",
    "integrated_system/runs/_RUNS_REGISTRY.jsonl",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _root_path(root: Path) -> Path:
    return root.expanduser().resolve(strict=False)


def resolve_declared(root: Path, value: str | os.PathLike[str]) -> tuple[Path, str | None]:
    """Resolve a path and return its root-relative spelling when contained."""

    root_abs = _root_path(root)
    raw = Path(value).expanduser()
    absolute = raw if raw.is_absolute() else root_abs / raw
    resolved = absolute.resolve(strict=False)
    try:
        relative = resolved.relative_to(root_abs).as_posix()
    except ValueError:
        return resolved, None
    return resolved, relative or "."


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_digest(path: Path) -> str:
    """Hash a directory by sorted relative file names and bytes."""

    digest = hashlib.sha256()
    files = sorted(
        (
            item
            for item in path.rglob("*")
            if item.is_file()
            and "__pycache__" not in item.relative_to(path).parts
            and ".pytest_cache" not in item.relative_to(path).parts
            and item.suffix not in {".pyc", ".pyo"}
        ),
        key=lambda item: item.relative_to(path).as_posix(),
    )
    for item in files:
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(_file_digest(item).encode("ascii"))
    return digest.hexdigest()


def path_state(root: Path, value: str | os.PathLike[str]) -> dict[str, Any]:
    path, relative = resolve_declared(root, value)
    state: dict[str, Any] = {
        "declared_path": str(value),
        "resolved_path": str(path),
        "relative_path": relative,
        "exists": path.exists(),
        "kind": "missing",
    }
    if relative is None:
        state["error"] = "PATH_OUTSIDE_ROOT"
        return state
    if not path.exists():
        return state
    try:
        stat = path.stat()
        state["mtime_ns"] = stat.st_mtime_ns
        state["size"] = stat.st_size if path.is_file() else None
        if path.is_file():
            state["kind"] = "file"
            state["sha256"] = _file_digest(path)
        elif path.is_dir():
            state["kind"] = "directory"
            state["sha256"] = _tree_digest(path)
        else:
            state["kind"] = "other"
    except (OSError, ValueError) as exc:
        state["error"] = f"UNREADABLE_PATH:{type(exc).__name__}"
    return state


def declared_digest(root: Path, values: Sequence[str]) -> tuple[str, list[dict[str, Any]]]:
    states = [path_state(root, value) for value in values]
    manifest = [{key: state[key] for key in sorted(state) if key not in {"resolved_path", "mtime_ns"}} for state in states]
    return canonical_sha256(manifest), states


def _prefix_matches(relative: str, prefixes: Iterable[str]) -> bool:
    return any(relative == prefix or relative.startswith(prefix + "/") for prefix in prefixes)


def _is_owner_surface(relative: str) -> bool:
    return "owner" in Path(relative).parts or Path(relative).name.upper().startswith("OWNER_")


def _age_hours(path: Path, now: datetime) -> float | None:
    try:
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None
    return max(0.0, (now - modified).total_seconds() / 3600.0)


def classify_candidate(root: Path, value: str, *, now: datetime, requested_action: str = "classify") -> dict[str, Any]:
    path, relative = resolve_declared(root, value)
    result: dict[str, Any] = {
        "declared_path": value,
        "resolved_path": str(path),
        "relative_path": relative,
        "classification": "BLOCKED_REQUIRES_PREP",
        "reason_code": "UNCLASSIFIED",
        "mutation_performed": False,
    }
    if requested_action != "classify":
        result["reason_code"] = "REFUSE_DESTRUCTIVE_ACTION"
        result["requested_action"] = requested_action
        return result
    if relative is None:
        result["reason_code"] = "PATH_OUTSIDE_ROOT"
        return result
    if _prefix_matches(relative, DENY_PREFIXES):
        result["reason_code"] = "ARCHIVE_SOURCE" if relative == "archive" or relative.startswith("archive/") else "DENYLIST_PATH"
        return result
    if relative in PROTECTED_RUN_FILES:
        result["reason_code"] = "PROTECTED_RUN_STATE"
        return result
    if _is_owner_surface(relative):
        age = _age_hours(path, now) if path.exists() else None
        result["age_hours"] = age
        result["reason_code"] = "FRESH_OWNER_SURFACE" if age is not None and age <= FRESHNESS_HOURS else "AMBIGUOUS_OWNER_SURFACE"
        return result
    if _prefix_matches(relative, ALLOW_PREFIXES):
        if Path(relative).name.startswith("tmp__"):
            result["classification"] = "MOVE_TO_ARCHIVE"
            result["reason_code"] = "EXACT_TMP_STAGING_ARTIFACT_PROPOSAL"
            result["proposed_destination"] = "archive/maintenance/" + relative
            result["execution"] = "NOT_PERFORMED"
            return result
        result["reason_code"] = "ALLOWLIST_REQUIRES_EXACT_PREP"
        return result
    result["classification"] = "KEEP_ACTIVE"
    result["reason_code"] = "OUTSIDE_MAINTENANCE_MOVE_SCOPE"
    return result


def _git_command(command: Sequence[str]) -> tuple[bool, int | None, str, str, str | None]:
    """Run one read-only git command and normalize unavailable-git failures."""

    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return False, None, "", "", f"GIT_UNAVAILABLE:{type(exc).__name__}"
    return completed.returncode == 0, completed.returncode, completed.stdout, completed.stderr, None


def _git_status_at(path: Path) -> dict[str, Any]:
    command = ["git", "-C", str(path), "status", "--porcelain=v1", "--untracked-files=normal"]
    available, returncode, stdout, stderr, error = _git_command(command)
    if error:
        return {"available": False, "error": error}
    lines = [line for line in stdout.splitlines() if line]
    return {
        "available": available,
        "returncode": returncode,
        "changed_count": len(lines),
        "entries": lines[:200],
        "truncated": len(lines) > 200,
        "stderr": stderr.strip()[:1000],
    }


def _git_identity(path: Path) -> tuple[str | None, str | None]:
    """Return the live branch and HEAD for a worktree, without changing it."""

    head_ok, _head_returncode, head_stdout, _head_stderr, _head_error = _git_command(
        ["git", "-C", str(path), "rev-parse", "--verify", "HEAD"]
    )
    branch_ok, _branch_returncode, branch_stdout, _branch_stderr, _branch_error = _git_command(
        ["git", "-C", str(path), "symbolic-ref", "--quiet", "--short", "HEAD"]
    )
    head = head_stdout.strip() if head_ok and head_stdout.strip() else None
    branch = branch_stdout.strip() if branch_ok and branch_stdout.strip() else None
    return branch, head


def _parse_worktree_porcelain(output: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            entries.append(current)
        current = None

    for line in output.splitlines():
        if not line:
            flush()
        elif line.startswith("worktree "):
            flush()
            current = {"registered_path": line[len("worktree ") :]}
        elif current is None:
            # A malformed or future extension before the first worktree is
            # ignored rather than being treated as a path or authority.
            continue
        elif line.startswith("HEAD "):
            current["listed_head"] = line[len("HEAD ") :].strip()
        elif line.startswith("branch "):
            current["listed_branch_ref"] = line[len("branch ") :].strip()
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True
        elif line.startswith("prunable "):
            current["prunable_reason"] = line[len("prunable ") :].strip()
        elif line.startswith("locked"):
            current["locked"] = True
    flush()
    return entries


def _worktree_state(entry: Mapping[str, Any]) -> dict[str, Any]:
    registered = str(entry.get("registered_path", ""))
    path = Path(registered).expanduser().resolve(strict=False)
    state: dict[str, Any] = {
        "registered_path": registered,
        "resolved_path": str(path),
        "exists": path.exists(),
        "listed_head": entry.get("listed_head"),
        "listed_branch_ref": entry.get("listed_branch_ref"),
        "bare": bool(entry.get("bare", False)),
        "detached": bool(entry.get("detached", False)),
        "prunable_reason": entry.get("prunable_reason"),
        "locked": bool(entry.get("locked", False)),
    }
    if not path.exists() or state["bare"]:
        state["branch"] = None
        state["head"] = state["listed_head"]
        state["status"] = {
            "available": False,
            "error": "WORKTREE_PATH_MISSING" if not path.exists() else "BARE_WORKTREE_NO_STATUS",
        }
        return state
    branch, head = _git_identity(path)
    listed_branch_ref = state.get("listed_branch_ref")
    if branch is None and isinstance(listed_branch_ref, str) and listed_branch_ref.startswith("refs/heads/"):
        branch = listed_branch_ref.removeprefix("refs/heads/")
    state["branch"] = branch
    state["head"] = head or state["listed_head"]
    state["status"] = _git_status_at(path)
    return state


def git_worktree_inventory(root: Path) -> dict[str, Any]:
    """Enumerate registered worktrees and read their identity/status only."""

    command = ["git", "-C", str(root), "worktree", "list", "--porcelain"]
    available, returncode, stdout, stderr, error = _git_command(command)
    if error:
        return {
            "available": False,
            "returncode": None,
            "source": "git worktree list --porcelain",
            "worktrees": [],
            "stderr": "",
            "error": error,
        }
    if not available:
        return {
            "available": False,
            "returncode": returncode,
            "source": "git worktree list --porcelain",
            "worktrees": [],
            "stderr": stderr.strip()[:1000],
            "error": "GIT_REPOSITORY_UNAVAILABLE",
        }
    parsed = _parse_worktree_porcelain(stdout)
    return {
        "available": True,
        "returncode": returncode,
        "source": "git worktree list --porcelain",
        "worktrees": [_worktree_state(entry) for entry in parsed],
        "count": len(parsed),
        "stderr": stderr.strip()[:1000],
    }


def git_status(root: Path) -> dict[str, Any]:
    status = _git_status_at(root)
    if not status.get("available"):
        # Keep missing Git / non-repository diagnostics non-blocking for a
        # fresh extracted ZIP.  The inventory is still explicit and empty.
        status["worktree_inventory"] = git_worktree_inventory(root)
        status["worktrees"] = []
        return status
    branch, head = _git_identity(root)
    status["branch"] = branch
    status["head"] = head
    inventory = git_worktree_inventory(root)
    status["worktree_inventory"] = inventory
    status["worktrees"] = inventory.get("worktrees", [])
    status["worktrees_available"] = bool(inventory.get("available"))
    return status


def ledger_state(root: Path, value: str | None) -> dict[str, Any]:
    if not value:
        return {"declared": False}
    state = path_state(root, value)
    if state.get("kind") != "file":
        return state
    path = Path(state["resolved_path"])
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError) as exc:
        state["error"] = f"LEDGER_UNREADABLE:{type(exc).__name__}"
        return state
    state["event_count"] = len(lines)
    state["head_sha256"] = sha256_bytes(lines[-1].encode("utf-8")) if lines else None
    return state


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def run_wave(
    *,
    root: str | os.PathLike[str],
    package: str | os.PathLike[str],
    source_paths: Sequence[str],
    context_paths: Sequence[str],
    ledger_path: str | None = None,
    map_paths: Sequence[str] = (),
    hook_paths: Sequence[str] = (),
    provider_paths: Sequence[str] = (),
    required_receipts: Sequence[str] = (),
    candidates: Sequence[str] = (),
    requested_action: str = "classify",
    run_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root_path = _root_path(Path(root))
    package_path, package_relative = resolve_declared(root_path, package)
    clock = now or datetime.now(timezone.utc)
    timestamp = clock.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    blockers: list[dict[str, str]] = []
    if not root_path.exists() or not root_path.is_dir():
        blockers.append({"code": "MISSING_ROOT", "path": str(root_path)})
    if package_relative is None:
        blockers.append({"code": "PACKAGE_OUTSIDE_ROOT", "path": str(package_path)})
    if not package_path.exists() or not package_path.is_dir():
        blockers.append({"code": "MISSING_PACKAGE", "path": str(package_path)})
    if requested_action != "classify":
        blockers.append({"code": "REFUSE_DESTRUCTIVE_ACTION", "requested_action": requested_action})

    source_digest, source_manifest = declared_digest(root_path, source_paths)
    context_digest, context_manifest = declared_digest(root_path, context_paths)
    for label, manifest in (("source", source_manifest), ("context", context_manifest)):
        for state in manifest:
            if not state.get("exists"):
                blockers.append({"code": f"MISSING_{label.upper()}_PATH", "path": str(state.get("declared_path"))})
            elif state.get("error"):
                blockers.append({"code": f"UNREADABLE_{label.upper()}_PATH", "path": str(state.get("declared_path"))})

    required_states = [path_state(root_path, value) for value in required_receipts]
    for state in required_states:
        if not state.get("exists") or state.get("kind") != "file":
            blockers.append({"code": "REFUSE_MISSING_RECEIPT", "path": str(state.get("declared_path"))})

    decisions = [classify_candidate(root_path, value, now=clock, requested_action=requested_action) for value in candidates]
    for decision in decisions:
        if decision["classification"] == "BLOCKED_REQUIRES_PREP":
            blockers.append({"code": decision["reason_code"], "path": decision["declared_path"]})

    diagnostics = {
        "root": path_state(root_path, "."),
        "package": path_state(root_path, package),
        "ledger": ledger_state(root_path, ledger_path),
        "map": [path_state(root_path, value) for value in map_paths],
        "hooks": [path_state(root_path, value) for value in hook_paths],
        "providers": [path_state(root_path, value) for value in provider_paths],
        "git": git_status(root_path),
    }
    source_after, _ = declared_digest(root_path, source_paths)
    context_after, _ = declared_digest(root_path, context_paths)
    if source_after != source_digest or context_after != context_digest:
        blockers.append({"code": "SOURCE_OR_CONTEXT_DRIFT", "path": "declared_paths"})

    status = "READY" if not blockers else "HOLD"
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "wave_id": WAVE_ID,
        "run_id": run_id or f"maintenance-{source_digest[:12]}-{context_digest[:12]}",
        "created_at": timestamp,
        "root": str(root_path),
        "package": str(package_path),
        "requested_action": requested_action,
        "status": status,
        "source_digest": source_digest,
        "context_digest": context_digest,
        "source_manifest": source_manifest,
        "context_manifest": context_manifest,
        "required_receipts": required_states,
        "diagnostics": diagnostics,
        "candidate_decisions": decisions,
        "blockers": blockers,
        "writes_allowed": False,
        "mutation_performed": False,
        "moves_performed": [],
        "deletions_performed": [],
        "child_receipts": [],
        "preload_receipts": [],
        "provider_call_receipt": None,
        "cancellation_state": "NOT_REQUESTED",
        "disagreement_state": "NOT_APPLICABLE",
        "claim_ceiling": "Bounded diagnostic and dry-run classification only; no mutation or campaign authority.",
    }
    body["output_digest"] = canonical_sha256(body)
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--source-path", action="append", required=True)
    parser.add_argument("--context-path", action="append", required=True)
    parser.add_argument("--ledger-path")
    parser.add_argument("--map-path", action="append", default=[])
    parser.add_argument("--hook-path", action="append", default=[])
    parser.add_argument("--provider-receipt", action="append", default=[])
    parser.add_argument("--required-receipt", action="append", default=[])
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--requested-action", default="classify")
    parser.add_argument("--run-id")
    parser.add_argument("--now", help="ISO-8601 time, useful for replayable freshness tests")
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    receipt = run_wave(
        root=args.root,
        package=args.package,
        source_paths=args.source_path,
        context_paths=args.context_path,
        ledger_path=args.ledger_path,
        map_paths=args.map_path,
        hook_paths=args.hook_path,
        provider_paths=args.provider_receipt,
        required_receipts=args.required_receipt,
        candidates=args.candidate,
        requested_action=args.requested_action,
        run_id=args.run_id,
        now=_parse_now(args.now),
    )
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(receipt) + b"\n")
    print(json.dumps({"status": receipt["status"], "run_id": receipt["run_id"], "receipt": str(output), "blockers": receipt["blockers"]}, sort_keys=True))
    return 0 if receipt["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
