"""Run one simulation in place and emit a bounded execution receipt.

Exit codes:

* 0 -- the simulation exited zero.
* 1 -- the simulation exited non-zero.
* 2 -- runner usage or I/O failure.
* 3 -- the simulation timed out.

The receipt is execution evidence only.  It never grants promotion or lets a
simulation choose its own claim kind.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 300.0
INTERPRETER_PROBE_TIMEOUT_SECONDS = 15.0
MAX_SNAPSHOT_FILES = 20_000
MAX_SNAPSHOT_FILE_BYTES = 64 * 1024 * 1024
STREAM_HEAD_CHARS = 2_000
SKIPPED_DIRECTORY_NAMES = frozenset({".git", "__pycache__", ".pytest_cache"})

# Controller policy, deliberately small and ordered longest-prefix-first.
CLAIM_KIND_POLICY: tuple[tuple[str, str], ...] = (
    ("system_v7/constraint_core/", "manifold_sim"),
    ("system_v8/", "manifold_sim"),
)
CLAIM_KIND_DEFAULT = "field_only"
CLAIM_KIND_SOURCE = "constraintbox.simrun policy table"
REPO_ROOT = Path(__file__).resolve().parents[3]

_CLAIM_KIND_PATTERN = re.compile(
    r"""["']claim_kind["']\s*:\s*["']([^"']+)["']"""
)


class SimRunError(RuntimeError):
    """Runner usage or I/O failure."""


@dataclass(frozen=True)
class Snapshot:
    files: dict[Path, tuple[str, int, int]]
    skipped_large: tuple[Path, ...]
    truncated: bool


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError as exc:
        raise SimRunError(f"could not hash {path}: {exc}") from exc
    return hasher.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _repo_relative(path: Path, repo_root: Path) -> str | None:
    absolute = Path(os.path.abspath(path))
    try:
        return absolute.relative_to(repo_root).as_posix()
    except ValueError:
        return None


def _display_path(path: Path, repo_root: Path) -> str:
    relative = _repo_relative(path, repo_root)
    return relative if relative is not None else str(Path(os.path.abspath(path)))


def _resolve_interpreter(
    value: Path | str | None,
) -> tuple[str, str | None, str | None, str | None]:
    requested = str(value) if value is not None else None
    invocation = requested if requested is not None else sys.executable
    expanded = Path(invocation).expanduser()

    if expanded.is_file():
        interpreter = str(expanded)
        realpath = expanded.resolve()
    else:
        located = shutil.which(invocation)
        if located is None:
            return invocation, requested, None, None
        interpreter = invocation
        realpath = Path(located).resolve()

    return (
        interpreter,
        requested,
        str(realpath),
        _sha256_file(realpath),
    )


def _short_probe_error(reason: str) -> str:
    normalized = " ".join(reason.split())
    return normalized[:240] if normalized else "unknown interpreter probe error"


def _probe_interpreter_environment(
    interpreter: str,
    *,
    cwd: Path,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "interpreter_prefix": None,
        "interpreter_base_prefix": None,
        "interpreter_is_venv": None,
    }
    command = [
        interpreter,
        "-c",
        (
            "import json,sys;"
            "print(json.dumps([sys.prefix,sys.base_prefix]))"
        ),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=INTERPRETER_PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        fields["interpreter_probe_error"] = (
            "interpreter probe timed out after 15 seconds"
        )
        return fields
    except OSError as exc:
        fields["interpreter_probe_error"] = _short_probe_error(
            f"could not execute interpreter probe: {exc}"
        )
        return fields

    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        reason = f"interpreter probe exited {completed.returncode}"
        if detail:
            reason = f"{reason}: {detail[-1]}"
        fields["interpreter_probe_error"] = _short_probe_error(reason)
        return fields

    try:
        probe_output = json.loads(completed.stdout)
        if not (
            isinstance(probe_output, list)
            and len(probe_output) == 2
        ):
            raise ValueError("expected a two-item JSON list")
        prefix, base_prefix = probe_output
        if not (
            isinstance(prefix, str)
            and prefix
            and isinstance(base_prefix, str)
            and base_prefix
        ):
            raise ValueError("prefix values must be non-empty strings")
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        fields["interpreter_probe_error"] = _short_probe_error(
            f"invalid interpreter probe output: {exc}"
        )
        return fields

    fields.update(
        {
            "interpreter_prefix": prefix,
            "interpreter_base_prefix": base_prefix,
            "interpreter_is_venv": prefix != base_prefix,
        }
    )
    return fields


def _snapshot(directory: Path) -> Snapshot:
    files: dict[Path, tuple[str, int, int]] = {}
    skipped_large: list[Path] = []
    inspected = 0
    truncated = False

    def fail_walk(error: OSError) -> None:
        raise SimRunError(f"could not snapshot {directory}: {error}") from error

    for current, directory_names, file_names in os.walk(
        directory,
        topdown=True,
        followlinks=False,
        onerror=fail_walk,
    ):
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in SKIPPED_DIRECTORY_NAMES
        )
        for name in sorted(file_names):
            if inspected >= MAX_SNAPSHOT_FILES:
                truncated = True
                break
            inspected += 1

            path = Path(current, name)
            try:
                metadata = path.stat()
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise SimRunError(f"could not stat {path}: {exc}") from exc

            if not stat.S_ISREG(metadata.st_mode):
                continue
            if metadata.st_size > MAX_SNAPSHOT_FILE_BYTES:
                skipped_large.append(path)
                continue
            files[path] = (
                _sha256_file(path),
                metadata.st_mtime_ns,
                metadata.st_size,
            )
        if truncated:
            break

    return Snapshot(
        files=files,
        skipped_large=tuple(skipped_large),
        truncated=truncated,
    )


def _artifact_row(
    path: Path,
    before: str | None,
    after: str | None,
    repo_root: Path,
) -> dict[str, str | None]:
    return {
        "path": _display_path(path, repo_root),
        "sha256_before": before,
        "sha256_after": after,
    }


def _diff_snapshots(
    before: Snapshot,
    after: Snapshot,
    repo_root: Path,
) -> tuple[dict[str, Any], tuple[Path, ...]]:
    before_paths = set(before.files)
    after_paths = set(after.files)

    created_paths = sorted(after_paths - before_paths)
    removed_paths = sorted(before_paths - after_paths)
    common_paths = before_paths & after_paths
    overwritten_paths = sorted(
        path
        for path in common_paths
        if before.files[path][0] != after.files[path][0]
    )
    rewritten_identical_paths = sorted(
        path
        for path in common_paths
        if (
            before.files[path][0] == after.files[path][0]
            and before.files[path][1] != after.files[path][1]
        )
    )
    unchanged_count = sum(
        (
            before.files[path][0] == after.files[path][0]
            and before.files[path][1] == after.files[path][1]
        )
        for path in common_paths
    )
    skipped_large = sorted(set(before.skipped_large) | set(after.skipped_large))

    artifacts = {
        "created": [
            _artifact_row(path, None, after.files[path][0], repo_root)
            for path in created_paths
        ],
        "overwritten": [
            _artifact_row(
                path,
                before.files[path][0],
                after.files[path][0],
                repo_root,
            )
            for path in overwritten_paths
        ],
        "removed": [
            _artifact_row(path, before.files[path][0], None, repo_root)
            for path in removed_paths
        ],
        "rewritten_identical": [
            {
                "path": _display_path(path, repo_root),
                "sha256": before.files[path][0],
                "mtime_ns_before": before.files[path][1],
                "mtime_ns_after": after.files[path][1],
            }
            for path in rewritten_identical_paths
        ],
        "unchanged_count": unchanged_count,
        "skipped_large": [
            _display_path(path, repo_root)
            for path in skipped_large
        ],
        "snapshot_truncated": before.truncated or after.truncated,
    }
    return artifacts, tuple(created_paths)


def _stream_fields(prefix: str, raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return {
        f"{prefix}_sha256": _sha256_bytes(raw),
        f"{prefix}_bytes": len(raw),
        f"{prefix}_first_line": lines[0] if lines else "",
        f"{prefix}_last_line": lines[-1] if lines else "",
        f"{prefix}_head": text[:STREAM_HEAD_CHARS],
    }


def _as_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def _collect_claim_kinds(value: Any, found: list[Any]) -> None:
    if isinstance(value, dict):
        if "claim_kind" in value:
            found.append(value["claim_kind"])
        for child in value.values():
            _collect_claim_kinds(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_claim_kinds(child, found)


def _stdout_claim_kinds(stdout: bytes) -> list[Any]:
    text = stdout.decode("utf-8", errors="replace")
    found: list[Any] = []
    stripped = text.strip()
    if stripped:
        try:
            _collect_claim_kinds(json.loads(stripped), found)
        except json.JSONDecodeError:
            pass
        for line in text.splitlines():
            try:
                _collect_claim_kinds(json.loads(line), found)
            except json.JSONDecodeError:
                pass
    found.extend(_CLAIM_KIND_PATTERN.findall(text))
    return found


def _artifact_claim_kinds(created_paths: tuple[Path, ...]) -> list[Any]:
    found: list[Any] = []
    for path in created_paths:
        if path.suffix.lower() != ".json":
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        _collect_claim_kinds(value, found)
    return found


def _deduplicate(values: list[Any]) -> list[Any]:
    unique: list[Any] = []
    markers: set[str] = set()
    for value in values:
        marker = json.dumps(value, sort_keys=True, separators=(",", ":"))
        if marker not in markers:
            markers.add(marker)
            unique.append(value)
    return unique


def _quarantined_claim_kind(
    stdout: bytes,
    created_paths: tuple[Path, ...],
) -> Any:
    values = _deduplicate(
        _stdout_claim_kinds(stdout) + _artifact_claim_kinds(created_paths)
    )
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return values


def _claim_kind_for(
    sim_path: Path,
    repo_root: Path,
) -> tuple[str, str]:
    relative = _repo_relative(sim_path, repo_root)
    if relative is not None:
        for prefix, claim_kind in CLAIM_KIND_POLICY:
            if relative.startswith(prefix):
                return claim_kind, prefix
    return CLAIM_KIND_DEFAULT, "default"


def _claim_kind_conflicts(asserted: Any, assigned: str) -> bool:
    if asserted is None:
        return False
    if isinstance(asserted, list):
        return any(value != assigned for value in asserted)
    return asserted != assigned


def run_sim(
    sim_path: Path,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    interpreter: Path | str | None = None,
) -> tuple[dict[str, Any], int]:
    """Run ``sim_path`` in its own directory and return its receipt and exit code."""

    try:
        timeout_seconds = float(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise SimRunError("timeout must be a number") from exc
    if timeout_seconds <= 0:
        raise SimRunError("timeout must be greater than zero")

    sim_path = Path(sim_path).expanduser().resolve()
    if not sim_path.is_file():
        raise SimRunError(f"missing sim path: {sim_path}")

    repo_root = REPO_ROOT
    sim_sha256 = _sha256_file(sim_path)
    (
        actual_interpreter,
        interpreter_requested,
        interpreter_realpath,
        interpreter_sha256,
    ) = _resolve_interpreter(interpreter)
    command = [actual_interpreter, str(sim_path)]
    interpreter_environment = _probe_interpreter_environment(
        actual_interpreter,
        cwd=sim_path.parent,
    )

    before = _snapshot(sim_path.parent)
    started_at_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    timed_out = False
    exit_code: int | None
    try:
        completed = subprocess.run(
            command,
            cwd=sim_path.parent,
            capture_output=True,
            timeout=timeout_seconds,
        )
        exit_code = completed.returncode
        stdout = _as_bytes(completed.stdout)
        stderr = _as_bytes(completed.stderr)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = _as_bytes(exc.stdout)
        stderr = _as_bytes(exc.stderr)
    except OSError as exc:
        raise SimRunError(f"could not execute sim: {exc}") from exc
    wall_seconds = time.monotonic() - started
    after = _snapshot(sim_path.parent)

    artifacts, created_paths = _diff_snapshots(before, after, repo_root)
    claim_kind, claim_kind_rule = _claim_kind_for(sim_path, repo_root)
    sim_asserted_claim_kind = _quarantined_claim_kind(stdout, created_paths)
    content_changed = bool(artifacts["overwritten"])
    rewritten_identically = bool(artifacts["rewritten_identical"])
    replay_stable = not (content_changed or rewritten_identically)
    if content_changed and rewritten_identically:
        replay_stable_reason = "content changed and identical rewrites"
    elif content_changed:
        replay_stable_reason = "content changed"
    elif rewritten_identically:
        replay_stable_reason = "rewritten with identical bytes"
    else:
        replay_stable_reason = "no writes observed"

    receipt: dict[str, Any] = {
        "schema": "constraintbox.simrun.v1",
        "sim_path": _display_path(sim_path, repo_root),
        "sim_sha256": sim_sha256,
        "command": command,
        "interpreter": actual_interpreter,
        "interpreter_requested": interpreter_requested,
        "interpreter_realpath": interpreter_realpath,
        "interpreter_sha256": interpreter_sha256,
        **interpreter_environment,
        "cwd": str(sim_path.parent),
        "timeout_seconds": timeout_seconds,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "wall_seconds": wall_seconds,
        "started_at_utc": started_at_utc,
        **_stream_fields("stdout", stdout),
        **_stream_fields("stderr", stderr),
        "artifacts": artifacts,
        "replay_stable": replay_stable,
        "replay_stable_reason": replay_stable_reason,
        "claim_kind": claim_kind,
        "claim_kind_source": CLAIM_KIND_SOURCE,
        "claim_kind_rule": claim_kind_rule,
        "sim_asserted_claim_kind": sim_asserted_claim_kind,
        "claim_kind_conflict": _claim_kind_conflicts(
            sim_asserted_claim_kind,
            claim_kind,
        ),
        "produced_by": "constraintbox.simrun",
        "promotion_allowed": False,
    }

    if timed_out:
        runner_exit_code = 3
    elif exit_code == 0:
        runner_exit_code = 0
    else:
        runner_exit_code = 1
    return receipt, runner_exit_code


def render_receipt(receipt: dict[str, Any]) -> str:
    return json.dumps(receipt, sort_keys=True, indent=2) + "\n"


def write_receipt_atomic(path: Path, receipt: dict[str, Any]) -> None:
    """Atomically replace ``path`` with the sorted-key JSON receipt."""

    path = Path(path).expanduser()
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(render_receipt(receipt))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise
