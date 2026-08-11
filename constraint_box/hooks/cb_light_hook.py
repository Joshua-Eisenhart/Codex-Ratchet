#!/usr/bin/env python3
"""Contained Claude Code hook controller for the CB Light 91-tool lifecycle."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from typing import Any, Mapping


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    # The contained wheel supplies the active ``hookkernel`` package.  Keep
    # the checkout available only for the hook wrapper modules, after
    # site-packages, so a legacy root package cannot shadow the Light wheel.
    sys.path.append(str(ROOT))

from hookkernel.cb_light_runtime import (  # noqa: E402
    MANDATED_INTERPRETER,
    same_declared_interpreter,
)
from hooks.cb_light_command_guard import (  # noqa: E402
    classify_command,
    command_from_payload,
    git_transition,
)


# Historical callback actions continue to use this module, but they no longer
# launch through a separate shared environment.  The launcher identity and the
# runtime whose receipts are inspected are the same contained Light runtime.
BOOTSTRAP_INTERPRETER = MANDATED_INTERPRETER
MANIFEST = ROOT / "config/cb_light_tools_v1.json"
CONTRACT = ROOT / "config/cb_light_contract_v1.json"
LOCK = ROOT / "requirements/locks/constraintbox-py313-macos-estate.lock"
RECEIPTS = ROOT / "receipts"
RUNTIME_RECEIPT = RECEIPTS / "cb_light_install_runtime_v1.json"
CLEAN_RECEIPT = RECEIPTS / "cb_light_install_clean_v1.json"
OPERATION_RECEIPT = RECEIPTS / "cb_light_tool_probes_v1.json"
METADATA_RECEIPT = RECEIPTS / "cb_light_metadata_v1.json"
SELECTION_RECEIPT = RECEIPTS / "cb_light_selection_v1.json"
LIGHT_HEAVY_SEPARATION_RECEIPT = (
    RECEIPTS / "cb_light_heavy_separation_audit_v2.json"
)
HOOK_RECEIPT = RECEIPTS / "cb_light_hook_run_v1.json"
LIFECYCLE_LOCK = RECEIPTS / ".cb_light_lifecycle.lock"
RUNTIME_INSTALL_REPORT = RECEIPTS / "cb_light_runtime_install_report_v1.json"
CLEAN_INSTALL_REPORT = RECEIPTS / "cb_light_clean_install_report_v1.json"
SETTINGS = REPO / ".claude/settings.json"
BROKER = ROOT / "bin/cb-light"
# These distributions implement the contained control plane itself.  They are
# deliberately outside the finite 91-tool candidate domain: `pip` provides the
# installer and `constraintbox` provides the gate.  Treating either as a tool
# candidate would falsely turn controller closure into tool adoption.
RUNTIME_INFRASTRUCTURE_DISTRIBUTIONS = frozenset({"pip", "constraintbox"})

_REQUIRED_HOOKS = {
    "SessionStart": (
        "startup|resume|clear|compact",
        "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh\"",
    ),
    "PreToolUse": (
        "Bash|Edit|Write|NotebookEdit",
        "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/cb_pretooluse_guard.sh\"",
    ),
    "PostToolUse": (
        "Bash|Edit|Write|NotebookEdit",
        "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/cb_posttooluse_record.sh\"",
    ),
    "PostToolUseFailure": (
        "Bash",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/post_tool_failure.sh\"",
    ),
    "TaskCompleted": (
        "",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/task_completed.sh\"",
    ),
    "SubagentStop": (
        "",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/subagent_stop.sh\"",
    ),
    "PostToolBatch": (
        "",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/post_tool_batch.sh\"",
    ),
    "Stop": (
        "",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/stop.sh\"",
    ),
    "ConfigChange": (
        "user_settings|project_settings|local_settings|policy_settings|skills",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/config_change.sh\"",
    ),
    "FileChanged": (
        "settings.json|cb_light_contract_v1.json|cb_light_tools_v1.json|constraintbox-py313-macos-estate.lock",
        "bash \"$CLAUDE_PROJECT_DIR/constraint_box/hooks/file_changed.sh\"",
    ),
}


class HookRefusal(RuntimeError):
    def __init__(self, reason_code: str, detail: str):
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


@contextmanager
def lifecycle_lock():
    """Serialize authoritative install/refresh receipt writers.

    A status check is read-only and can run concurrently.  Install and refresh
    rewrite a fixed family of runtime, selection, and hook receipts, so an
    atomic lock file is the minimum truthful ownership boundary.  A stale lock
    is deliberately a HOLD rather than a guessed deletion: an operator can
    inspect its JSON before clearing it.
    """

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            LIFECYCLE_LOCK,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        try:
            detail = LIFECYCLE_LOCK.read_text(encoding="utf-8")[:500]
        except OSError:
            detail = str(LIFECYCLE_LOCK)
        raise HookRefusal("CB_LIGHT_LIFECYCLE_LOCK_HELD", detail) from exc
    try:
        payload = json.dumps(
            {
                "schema": "constraintbox.cb-light-lifecycle-lock.v1",
                "pid": os.getpid(),
                "acquired_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            },
            sort_keys=True,
        ).encode("utf-8")
        os.write(descriptor, payload)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        yield
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            LIFECYCLE_LOCK.unlink()
        except FileNotFoundError:
            pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HookRefusal("MALFORMED_JSON_OBJECT", str(path))
    return value


def verify_manifest() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    identity = dict(manifest)
    claimed = identity.pop("manifest_sha256", None)
    observed = hashlib.sha256(canonical_json(identity)).hexdigest()
    if manifest.get("schema") != "constraintbox.cb-light-tool-manifest.v1":
        raise HookRefusal("MANIFEST_SCHEMA_INVALID", str(MANIFEST))
    if claimed != observed:
        raise HookRefusal("MANIFEST_DIGEST_MISMATCH", str(MANIFEST))
    contract = load_json(CONTRACT)
    expected_roots = int(
        (contract.get("expected_counts") or {}).get("install_proposals", -1)
    )
    rows = manifest.get("tools")
    if not isinstance(rows, list) or len(rows) != expected_roots:
        raise HookRefusal(
            "MANIFEST_ROOT_COUNT_MISMATCH",
            f"expected={expected_roots},observed={len(rows or [])}",
        )
    names = [str(row.get("normalized_name")) for row in rows]
    if len(set(names)) != expected_roots:
        raise HookRefusal("MANIFEST_IDENTITIES_NOT_UNIQUE", "duplicate tool")
    source_hashes = manifest.get("source_hashes")
    if not isinstance(source_hashes, dict):
        raise HookRefusal("MANIFEST_SOURCE_HASHES_MISSING", str(MANIFEST))
    required_paths = contract.get("required_source_paths")
    if (
        contract.get("schema") != "constraintbox.cb-light-contract.v1"
        or not isinstance(required_paths, list)
        or len(required_paths) != len(set(required_paths))
        or set(source_hashes) != set(required_paths)
    ):
        raise HookRefusal(
            "MANIFEST_SOURCE_SET_MISMATCH", "contract required_source_paths"
        )
    for relative, expected in source_hashes.items():
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError as exc:
            raise HookRefusal("MANIFEST_SOURCE_PATH_ESCAPES_ROOT", relative) from exc
        if not path.is_file() or sha256_file(path) != expected:
            raise HookRefusal("MANIFEST_SOURCE_DIGEST_MISMATCH", relative)
    expected_hook_files = {
        pathlib.Path(relative).name
        for relative in required_paths
        if pathlib.PurePosixPath(relative).parent == pathlib.PurePosixPath("hooks")
    }
    observed_hook_files = {
        path.name
        for path in (ROOT / "hooks").iterdir()
        if path.is_file() and path.suffix in {".py", ".sh"}
    }
    if observed_hook_files != expected_hook_files:
        raise HookRefusal(
            "HOOK_FILE_SET_DRIFT",
            f"missing={sorted(expected_hook_files-observed_hook_files)},"
            f"extra={sorted(observed_hook_files-expected_hook_files)}",
        )
    return manifest


def read_payload(value: str | None) -> dict[str, Any]:
    raw = value if value is not None else sys.stdin.read()
    if not raw.strip():
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise HookRefusal("HOOK_PAYLOAD_NOT_OBJECT", "hook input must be JSON object")
    return parsed


def deny_pretool(reason_code: str, detail: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"CB Light {reason_code}: {detail}",
                }
            },
            sort_keys=True,
        )
    )
    return 0


def blocking_failure(reason_code: str, detail: str) -> int:
    print(f"CB Light {reason_code}: {detail}", file=sys.stderr)
    return 2


def _project_cwd(payload: Mapping[str, Any]) -> pathlib.Path:
    raw = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or str(REPO)
    try:
        return pathlib.Path(str(raw)).expanduser().resolve()
    except OSError:
        return REPO.resolve()


def _tool_name(payload: Mapping[str, Any]) -> str:
    return str(payload.get("tool_name") or "")


def _tool_path(payload: Mapping[str, Any]) -> pathlib.Path | None:
    nested = payload.get("tool_input")
    if not isinstance(nested, Mapping):
        nested = payload.get("inputs")
    if not isinstance(nested, Mapping):
        return None
    raw = nested.get("file_path") or nested.get("notebook_path") or nested.get("path")
    if not isinstance(raw, str) or not raw:
        return None
    path = pathlib.Path(raw).expanduser()
    if not path.is_absolute():
        path = _project_cwd(payload) / path
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _is_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def evaluate_file_write(payload: Mapping[str, Any]) -> dict[str, Any]:
    tool_name = _tool_name(payload)
    if tool_name not in {"Edit", "Write", "NotebookEdit"}:
        return {"disposition": "ADMIT", "reason_code": "NOT_A_FILE_WRITE"}
    target = _tool_path(payload)
    if target is None:
        raise HookRefusal("WRITE_TARGET_MISSING", tool_name)
    protected_directories = {
        "contained_runtime": ROOT / ".venv",
        "authoritative_receipts": RECEIPTS,
        "hook_controller": ROOT / "hooks",
        "project_hook_configuration": REPO / ".claude",
    }
    for label, directory in protected_directories.items():
        if _is_within(target, directory):
            raise HookRefusal(
                "PROTECTED_CB_LIGHT_WRITE_REFUSED", f"{label}:{target}"
            )
    protected_files = {MANIFEST.resolve(), CONTRACT.resolve(), LOCK.resolve()}
    if target in protected_files:
        raise HookRefusal("PROTECTED_CB_LIGHT_WRITE_REFUSED", str(target))
    return {
        "disposition": "ADMIT",
        "reason_code": "UNPROTECTED_SOURCE_WRITE_REQUIRES_POSTCONDITION",
        "target": str(target),
    }


def evaluate_install(payload: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    del manifest
    command = command_from_payload(payload)
    evaluated = classify_command(
        command,
        cwd=_project_cwd(payload),
        broker=BROKER,
    )
    evaluated["command_sha256"] = hashlib.sha256(command.encode()).hexdigest()
    if evaluated.get("disposition") == "DENY":
        raise HookRefusal(
            str(evaluated.get("reason_code")),
            f"use {BROKER} install; the contained runtime is remeasured after Bash",
        )
    return evaluated


def hook_config_errors() -> list[str]:
    if not SETTINGS.is_file():
        return ["missing .claude/settings.json"]
    try:
        settings = load_json(SETTINGS)
    except Exception as exc:
        return [f"settings unreadable: {type(exc).__name__}: {exc}"]
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return ["settings hooks object missing"]
    errors: list[str] = []
    for event, (required_matcher, required_command) in _REQUIRED_HOOKS.items():
        groups = hooks.get(event)
        matched = False
        if isinstance(groups, list):
            for group in groups:
                if not isinstance(group, dict):
                    continue
                if group.get("matcher") != required_matcher:
                    continue
                for hook in group.get("hooks", []):
                    if (
                        isinstance(hook, dict)
                        and hook.get("type") == "command"
                        and hook.get("command") == required_command
                    ):
                        matched = True
        if not matched:
            errors.append(
                f"{event} missing contained command under matcher "
                f"{required_matcher!r}: {required_command}"
            )
    return errors


def source_paths(manifest: Mapping[str, Any] | None = None) -> dict[str, pathlib.Path]:
    manifest = manifest or load_json(MANIFEST)
    source_hashes = manifest.get("source_hashes")
    if not isinstance(source_hashes, dict):
        raise HookRefusal("MANIFEST_SOURCE_HASHES_MISSING", str(MANIFEST))
    contained = {relative: ROOT / relative for relative in source_hashes}
    contained["config/cb_light_tools_v1.json"] = MANIFEST
    contained["runtime:contained_interpreter"] = MANDATED_INTERPRETER
    contained["runtime:hook_launcher_interpreter"] = BOOTSTRAP_INTERPRETER.resolve()
    contained["host:.claude/settings.json"] = SETTINGS
    return contained


def run_checked(command: list[str], *, accepted: set[int]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        timeout=1800,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"},
    )
    result = {
        "command": command,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "stdout_tail": completed.stdout[-1000:],
        "stderr_tail": completed.stderr[-1000:],
    }
    if completed.returncode not in accepted:
        raise HookRefusal(
            "REFRESH_COMMAND_FAILED",
            f"rc={completed.returncode} command={command} stderr={completed.stderr[-400:]}",
        )
    return result


def runtime_inventory() -> dict[str, str]:
    if not MANDATED_INTERPRETER.is_file():
        raise HookRefusal("CONTAINED_RUNTIME_MISSING", str(MANDATED_INTERPRETER))
    code = (
        "import importlib.metadata as m,json,pathlib,re,sysconfig; "
        "paths=sorted({str(pathlib.Path(value).resolve()) for key,value in "
        "sysconfig.get_paths().items() if key in {'purelib','platlib'} and value}); "
        "n=lambda s:re.sub(r'[-_.]+','-',s).lower(); "
        "print(json.dumps({n(d.metadata['Name']):d.version for d in "
        "m.distributions(path=paths) if d.metadata.get('Name')},sort_keys=True))"
    )
    completed = subprocess.run(
        [str(MANDATED_INTERPRETER), "-I", "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"},
    )
    if completed.returncode != 0:
        raise HookRefusal(
            "CONTAINED_RUNTIME_INVENTORY_FAILED", completed.stderr[-400:]
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise HookRefusal("CONTAINED_RUNTIME_INVENTORY_MALFORMED", "not an object")
    return {str(name): str(version) for name, version in value.items()}


def _is_runtime_infrastructure_artifact(path: pathlib.Path) -> bool:
    """Return true for editable controller metadata outside the tool domain."""
    if path.name.startswith("__editable__.constraintbox-") and path.suffix == ".pth":
        return True
    return any(
        part.startswith("constraintbox-") and part.endswith(".dist-info")
        for part in path.parts
    )


def runtime_site_packages_snapshot(runtime_receipt: Mapping[str, Any]) -> dict[str, Any]:
    expected = runtime_receipt.get("site_packages_snapshot")
    environment = runtime_receipt.get("environment")
    if not isinstance(expected, Mapping) or not isinstance(environment, Mapping):
        raise HookRefusal("RUNTIME_SNAPSHOT_EVIDENCE_MISSING", str(RUNTIME_RECEIPT))
    prefix = pathlib.Path(str(environment.get("prefix", ""))).resolve()
    roots = expected.get("roots")
    if not isinstance(roots, list) or not roots:
        raise HookRefusal("RUNTIME_SNAPSHOT_ROOTS_MISSING", str(RUNTIME_RECEIPT))
    entries: list[dict[str, Any]] = []
    normalized_roots: list[str] = []
    for raw in roots:
        root = (prefix / str(raw)).resolve()
        if not _is_within(root, prefix) or not root.is_dir():
            raise HookRefusal("RUNTIME_SNAPSHOT_ROOT_INVALID", str(root))
        normalized_roots.append(str(root.relative_to(prefix)))
        for path in sorted(root.rglob("*"), key=str):
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if _is_runtime_infrastructure_artifact(path):
                continue
            try:
                if not path.is_file():
                    continue
                resolved = path.resolve()
                relative = str(resolved.relative_to(prefix))
                size = path.stat().st_size
                digest = sha256_file(path)
            except (OSError, ValueError):
                continue
            entries.append({"path": relative, "bytes": size, "sha256": digest})
    return {
        "algorithm": "sha256(canonical(path,bytes,sha256) rows)",
        "excluded": [
            "**/__pycache__/**",
            "*.pyc",
            "*.pyo",
            "**/__editable__.constraintbox-*.pth",
            "**/constraintbox-*.dist-info/**",
        ],
        "roots": normalized_roots,
        "file_count": len(entries),
        "total_bytes": sum(int(row["bytes"]) for row in entries),
        "digest": hashlib.sha256(canonical_json(entries)).hexdigest(),
    }


def runtime_import_attestation(manifest: Mapping[str, Any]) -> tuple[bool, str]:
    imports = {
        str(row.get("normalized_name")): str((row.get("import_names") or [""])[0])
        for row in manifest.get("tools") or []
    }
    code = """
import contextlib, importlib, io, json, pathlib, sys
names = json.loads(sys.argv[1])
prefix = pathlib.Path(sys.prefix).resolve()
rows = {}
for identity, import_name in names.items():
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            module = importlib.import_module(import_name)
        raw = getattr(module, '__file__', None)
        origin = pathlib.Path(raw).resolve() if raw else None
        rows[identity] = bool(origin and origin.is_relative_to(prefix))
    except BaseException:
        rows[identity] = False
print(json.dumps(rows, sort_keys=True))
"""
    completed = subprocess.run(
        [str(MANDATED_INTERPRETER), "-I", "-c", code, json.dumps(imports, sort_keys=True)],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"},
    )
    if completed.returncode != 0:
        return False, f"RUNTIME_IMPORT_ATTESTATION_FAILED:{completed.stderr[-300:]}"
    try:
        rows = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, "RUNTIME_IMPORT_ATTESTATION_MALFORMED"
    failed = sorted(name for name, passed in rows.items() if passed is not True)
    if set(rows) != set(imports):
        return False, "RUNTIME_IMPORT_ATTESTATION_SET_MISMATCH"
    if failed:
        return False, f"RUNTIME_IMPORT_DRIFT:{failed}"
    return True, "RUNTIME_IMPORTS_RESOLVE_UNDER_CONTAINED_PREFIX"


def installed_light_package_source_integrity(
    manifest: Mapping[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """Bind the actual installed Light wheel files to the source contract.

    The runtime inventory receipt proves dependency closure, but it cannot
    distinguish a newly edited checkout from an older wheel still installed in
    ``.venv``.  Every distributable ``constraintbox`` and ``hookkernel`` file
    must therefore be present under the mandated interpreter, be inside its
    prefix, and match the manifest's source hash exactly.  This is deliberately
    independent of the fresh-wheel separation audit: one proves what a new
    wheel would contain; this proves what the gate will execute now.
    """

    source_hashes = manifest.get("source_hashes")
    if not isinstance(source_hashes, Mapping):
        return False, "INSTALLED_LIGHT_PACKAGE_SOURCE_HASHES_MISSING", {}
    expected: dict[str, str] = {
        str(relative): str(digest)
        for relative, digest in source_hashes.items()
        if str(relative).startswith(
            (
                "light_runtime/src/constraintbox/",
                "light_runtime/src/hookkernel/",
            )
        )
    }
    if not expected:
        return False, "INSTALLED_LIGHT_PACKAGE_SOURCE_SET_MISSING", {}
    code = """
import importlib, json, sys
from pathlib import Path
packages = {}
for name in ('constraintbox', 'hookkernel'):
    module = importlib.import_module(name)
    packages[name] = str(Path(module.__file__).resolve().parent)
print(json.dumps({'prefix': str(Path(sys.prefix).resolve()), 'packages': packages}, sort_keys=True))
"""
    completed = subprocess.run(
        [str(MANDATED_INTERPRETER), "-I", "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"},
    )
    try:
        observed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        observed = None
    if completed.returncode != 0 or not isinstance(observed, Mapping):
        return (
            False,
            "INSTALLED_LIGHT_PACKAGE_ORIGIN_PROBE_FAILED",
            {
                "returncode": completed.returncode,
                "stderr_tail": completed.stderr[-400:],
            },
        )
    raw_prefix = observed.get("prefix")
    raw_packages = observed.get("packages")
    if not isinstance(raw_prefix, str) or not isinstance(raw_packages, Mapping):
        return False, "INSTALLED_LIGHT_PACKAGE_ORIGIN_MALFORMED", {}
    prefix = pathlib.Path(raw_prefix).resolve()
    package_roots: dict[str, pathlib.Path] = {}
    for package in ("constraintbox", "hookkernel"):
        raw_root = raw_packages.get(package)
        if not isinstance(raw_root, str):
            return False, f"INSTALLED_LIGHT_PACKAGE_ROOT_MISSING:{package}", {}
        root = pathlib.Path(raw_root).resolve()
        if not _is_within(root, prefix):
            return (
                False,
                f"INSTALLED_LIGHT_PACKAGE_OUTSIDE_CONTAINED_PREFIX:{package}",
                {"prefix": str(prefix), "package_roots": {package: str(root)}},
            )
        package_roots[package] = root

    actual_files: dict[str, pathlib.Path] = {}
    for package, root in package_roots.items():
        for path in sorted(root.rglob("*"), key=str):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            relative = f"light_runtime/src/{package}/{path.relative_to(root).as_posix()}"
            actual_files[relative] = path
    expected_paths = set(expected)
    actual_paths = set(actual_files)
    missing = sorted(expected_paths - actual_paths)
    unexpected = sorted(actual_paths - expected_paths)
    mismatches = sorted(
        relative
        for relative in expected_paths & actual_paths
        if sha256_file(actual_files[relative]) != expected[relative]
    )
    evidence = {
        "schema": "constraintbox.cb-light-installed-package-source-integrity.v1",
        "prefix": str(prefix),
        "package_roots": {name: str(path) for name, path in package_roots.items()},
        "expected_file_count": len(expected_paths),
        "observed_file_count": len(actual_paths),
        "missing_paths": missing,
        "unexpected_paths": unexpected,
        "hash_mismatch_paths": mismatches,
        "expected_hashes_sha256": hashlib.sha256(canonical_json(expected)).hexdigest(),
        "observed_hashes_sha256": hashlib.sha256(
            canonical_json(
                {
                    relative: sha256_file(path)
                    for relative, path in sorted(actual_files.items())
                }
            )
        ).hexdigest(),
    }
    if missing:
        return False, f"INSTALLED_LIGHT_PACKAGE_SOURCE_MISSING:{missing}", evidence
    if unexpected:
        return False, f"INSTALLED_LIGHT_PACKAGE_SOURCE_UNEXPECTED:{unexpected}", evidence
    if mismatches:
        return (
            False,
            f"INSTALLED_LIGHT_PACKAGE_SOURCE_HASH_MISMATCH:{mismatches}",
            evidence,
        )
    return True, "INSTALLED_LIGHT_PACKAGE_SOURCES_MATCH_MANIFEST", evidence


def verify_runtime_postcondition(
    runtime_receipt: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
    package_integrity: tuple[bool, str, dict[str, Any]] | None = None,
) -> tuple[bool, str]:
    closure_rows = runtime_receipt.get("closure")
    if not isinstance(closure_rows, list):
        return False, "RUNTIME_RECEIPT_CLOSURE_MISSING"
    expected = {
        str(row.get("distribution")): str(row.get("version"))
        for row in closure_rows
        if row.get("installed") is True
    }
    observed = runtime_inventory()
    if "constraintbox" not in observed:
        return False, "CONTAINED_CONTROLLER_PACKAGE_MISSING"
    observed_without_bootstrap = {
        name: version
        for name, version in observed.items()
        if name not in RUNTIME_INFRASTRUCTURE_DISTRIBUTIONS
    }
    if set(observed_without_bootstrap) != set(expected):
        missing = sorted(set(expected) - set(observed_without_bootstrap))
        extra = sorted(set(observed_without_bootstrap) - set(expected))
        return False, f"RUNTIME_DISTRIBUTION_SET_DRIFT:missing={missing},extra={extra}"
    mismatched = sorted(
        name for name in expected if observed_without_bootstrap.get(name) != expected[name]
    )
    if mismatched:
        return False, f"RUNTIME_VERSION_DRIFT:{mismatched}"
    expected_snapshot = runtime_receipt.get("site_packages_snapshot")
    try:
        observed_snapshot = runtime_site_packages_snapshot(runtime_receipt)
    except HookRefusal as exc:
        return False, f"{exc.reason_code}:{exc.detail}"
    if observed_snapshot != expected_snapshot:
        return False, (
            "RUNTIME_SITE_PACKAGES_FILE_DRIFT:"
            f"expected={getattr(expected_snapshot, 'get', lambda *_: None)('digest')},"
            f"observed={observed_snapshot.get('digest')}"
        )
    try:
        current_manifest = manifest or verify_manifest()
    except HookRefusal as exc:
        return False, f"{exc.reason_code}:{exc.detail}"
    integrity_ok, integrity_reason, _ = package_integrity or (
        installed_light_package_source_integrity(current_manifest)
    )
    if not integrity_ok:
        return False, integrity_reason
    imports_ok, import_reason = runtime_import_attestation(current_manifest)
    if not imports_ok:
        return False, import_reason
    return True, (
        "RUNTIME_DISTRIBUTIONS_FILES_AND_IMPORTS_MATCH_INSTALL_RECEIPT"
    )


def verify_light_heavy_separation(
    manifest: Mapping[str, Any],
    *,
    receipt_path: pathlib.Path = LIGHT_HEAVY_SEPARATION_RECEIPT,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Check the receipt produced by the actual Light/Heavy package gate.

    This is intentionally not a source-presence check.  The audit must have
    built the Light-only wheel, installed it into a fresh interpreter, and
    observed that its prohibited module paths are absent.  The hook binds the
    exact receipt separately, so a later mutation cannot substitute a stale
    clean result for the refresh that consumed it.
    """

    try:
        receipt = load_json(receipt_path)
    except FileNotFoundError:
        return False, "LIGHT_HEAVY_SEPARATION_RECEIPT_MISSING", None
    except (OSError, json.JSONDecodeError, HookRefusal) as exc:
        return False, f"LIGHT_HEAVY_SEPARATION_RECEIPT_INVALID:{type(exc).__name__}", None
    if receipt.get("schema") != "constraintbox.cb-light-heavy-separation-audit.v2":
        return False, "LIGHT_HEAVY_SEPARATION_SCHEMA_INVALID", receipt
    if receipt.get("manifest_identity_sha256") != manifest.get("manifest_sha256"):
        return False, "LIGHT_HEAVY_SEPARATION_MANIFEST_STALE", receipt
    if receipt.get("disposition") != "ADMIT":
        return False, "LIGHT_HEAVY_SEPARATION_REFUSED", receipt
    failures = receipt.get("failures")
    if not isinstance(failures, Mapping):
        return False, "LIGHT_HEAVY_SEPARATION_FAILURES_MALFORMED", receipt
    fresh_wheel = failures.get("fresh_wheel_probe")
    if not isinstance(fresh_wheel, Mapping) or fresh_wheel.get("passed") is not True:
        return False, "LIGHT_HEAVY_FRESH_WHEEL_PROBE_MISSING", receipt
    contained_runtime = failures.get("contained_runtime_probe")
    if (
        not isinstance(contained_runtime, Mapping)
        or contained_runtime.get("passed") is not True
    ):
        return False, "LIGHT_HEAVY_CONTAINED_RUNTIME_PROBE_MISSING", receipt
    if failures.get("audit_source_bound") is not True:
        return False, "LIGHT_HEAVY_AUDIT_SOURCE_NOT_BOUND", receipt
    return True, "LIGHT_HEAVY_SEPARATION_VERIFIED", receipt


def verify_live_light_heavy_separation(
    manifest: Mapping[str, Any],
) -> tuple[bool, str]:
    """Re-run the boundary audit at a real transition without mutating receipts.

    The persisted receipt binds a refresh.  A status, completion, or git
    transition additionally runs the same fresh-wheel *and* actual-runtime
    probe into a verifier-owned temporary file, so the gate cannot merely
    point at yesterday's clean artifact.
    """

    try:
        with tempfile.TemporaryDirectory(prefix="cb-light-live-boundary-") as temporary:
            receipt_path = pathlib.Path(temporary) / "separation.json"
            completed = subprocess.run(
                [
                    str(MANDATED_INTERPRETER),
                    "-I",
                    str(ROOT / "scripts/audit_cb_light_heavy_separation.py"),
                    "--output",
                    str(receipt_path),
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "NO_COLOR": "1",
                },
            )
            if completed.returncode != 0:
                return (
                    False,
                    "LIVE_LIGHT_HEAVY_SEPARATION_AUDIT_FAILED:"
                    f"rc={completed.returncode}:{completed.stderr[-240:]}",
                )
            allowed, reason, _ = verify_light_heavy_separation(
                manifest, receipt_path=receipt_path
            )
            return allowed, (
                "LIVE_LIGHT_HEAVY_SEPARATION_VERIFIED"
                if allowed
                else f"LIVE_{reason}"
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"LIVE_LIGHT_HEAVY_SEPARATION_ERROR:{type(exc).__name__}"


def refresh(*, lock_held: bool = False) -> dict[str, Any]:
    """Rebuild the authoritative local-evaluation receipts under one writer."""

    if lock_held:
        return _refresh()
    with lifecycle_lock():
        return _refresh()


def _refresh() -> dict[str, Any]:
    manifest = verify_manifest()
    if not same_declared_interpreter(
        str(manifest.get("mandated_interpreter", "")), MANDATED_INTERPRETER
    ):
        raise HookRefusal("MANIFEST_RUNTIME_PATH_MISMATCH", str(MANDATED_INTERPRETER))
    if not CLEAN_RECEIPT.is_file():
        raise HookRefusal("CLEAN_INSTALL_RECEIPT_MISSING", str(CLEAN_RECEIPT))
    runs = {
        "runtime_install": run_checked(
            [
                str(MANDATED_INTERPRETER),
                "-I",
                str(ROOT / "scripts/cb_light_install_probe.py"),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(RUNTIME_RECEIPT),
                "--environment-role",
                "runtime",
                "--expected-python",
                str(MANDATED_INTERPRETER),
                "--install-report",
                str(RUNTIME_INSTALL_REPORT),
                "--quiet",
            ],
            accepted={0, 1},
        ),
        "metadata": run_checked(
            [
                str(MANDATED_INTERPRETER),
                "-I",
                str(ROOT / "scripts/cb_light_metadata_probe.py"),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(METADATA_RECEIPT),
                "--jobs",
                "16",
                "--timeout",
                "20",
            ],
            accepted={0},
        ),
        "operation": run_checked(
            [
                str(MANDATED_INTERPRETER),
                "-I",
                str(ROOT / "light_runtime/src/constraintbox/cb_light_tool_probes.py"),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(OPERATION_RECEIPT),
                "--jobs",
                "12",
                "--timeout",
                "60",
            ],
            accepted={0, 1},
        ),
    }
    runs["selection"] = run_checked(
        [
            str(MANDATED_INTERPRETER),
            "-I",
            str(ROOT / "scripts/cb_light_select.py"),
            "--manifest",
            str(MANIFEST),
            "--runtime-install",
            str(RUNTIME_RECEIPT),
            "--clean-install",
            str(CLEAN_RECEIPT),
            "--operation",
            str(OPERATION_RECEIPT),
            "--metadata",
            str(METADATA_RECEIPT),
            "--output",
            str(SELECTION_RECEIPT),
        ],
        accepted={0},
    )
    # The separation audit is a real transition, not a side report: it builds
    # the Light-only wheel, installs it in a fresh interpreter, and performs
    # both module-path and dependency negatives.  A successful selection is
    # not usable as a CB Light evaluation unless this boundary is current too.
    runs["light_heavy_separation"] = run_checked(
        [
            str(MANDATED_INTERPRETER),
            "-I",
            str(ROOT / "scripts/audit_cb_light_heavy_separation.py"),
            "--output",
            str(LIGHT_HEAVY_SEPARATION_RECEIPT),
        ],
        accepted={0},
    )
    selection = load_json(SELECTION_RECEIPT)
    runtime_receipt = load_json(RUNTIME_RECEIPT)
    package_integrity = installed_light_package_source_integrity(manifest)
    runtime_ok, runtime_reason = verify_runtime_postcondition(
        runtime_receipt,
        manifest=manifest,
        package_integrity=package_integrity,
    )
    separation_ok, separation_reason, separation_receipt = verify_light_heavy_separation(
        manifest
    )
    if not separation_ok or separation_receipt is None:
        raise HookRefusal("LIGHT_HEAVY_SEPARATION_REQUIRED", separation_reason)
    errors = hook_config_errors()
    sources = source_paths()
    missing_sources = [name for name, path in sources.items() if not path.is_file()]
    if missing_sources:
        raise HookRefusal("HOOK_SOURCE_MISSING", ", ".join(missing_sources))
    hashes = {name: sha256_file(path) for name, path in sources.items()}
    body = {
        "schema": "constraintbox.cb-light-hook-run.v1",
        "evaluated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest_identity_sha256": manifest["manifest_sha256"],
        "selection_receipt_sha256": sha256_file(SELECTION_RECEIPT),
        "source_hashes": hashes,
        "source_set_sha256": hashlib.sha256(canonical_json(hashes)).hexdigest(),
        "hook_config_errors": errors,
        "hook_activation_claim": (
            "project settings and executable hook sources are present; actual hook firing "
            "is evidenced separately by receipts/cb_light_hook_events.jsonl and requires "
            "Claude Code to start with this repository as its project root"
        ),
        "runs": runs,
        "selection_counts": selection.get("counts"),
        "runtime_postcondition": {
            "passed": runtime_ok,
            "reason_code": runtime_reason,
            "inventory_sha256": hashlib.sha256(
                canonical_json(runtime_inventory())
            ).hexdigest(),
            "installed_light_package_source_integrity": {
                "passed": package_integrity[0],
                "reason_code": package_integrity[1],
                "evidence": package_integrity[2],
            },
        },
        "light_heavy_separation": {
            "receipt_path": str(LIGHT_HEAVY_SEPARATION_RECEIPT),
            "receipt_sha256": sha256_file(LIGHT_HEAVY_SEPARATION_RECEIPT),
            "passed": separation_ok,
            "reason_code": separation_reason,
            "fresh_wheel_probe_passed": (
                (separation_receipt.get("failures") or {})
                .get("fresh_wheel_probe", {})
                .get("passed")
                is True
            ),
        },
        "evaluation_allowed": bool(
            selection.get("evaluation_allowed")
            and runtime_ok
            and separation_ok
            and not errors
        ),
        # A current local Light evaluation is deliberately not a completed
        # ConstraintBox system.  Portable adoption, a real consumer, owner
        # approval, and a separately managed Heavy profile remain distinct
        # transitions with their own receipts.
        "completion_allowed": False,
        "system_completion_reason": (
            "LOCAL_CB_LIGHT_EVALUATION_DOES_NOT_EARN_SYSTEM_COMPLETION"
        ),
        "promotion_allowed": False,
        "claim_ceiling": (
            "contained CB Light installation, fresh-wheel Light/Heavy separation, and "
            "current-work selection only; no portable adoption, production integration, "
            "CB Heavy setup or bridge, simulation, promotion, or release"
        ),
    }
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    HOOK_RECEIPT.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


def verify_evaluation(
    max_age_hours: float = 24.0,
    *,
    require_live_boundary: bool = False,
) -> tuple[bool, str]:
    try:
        manifest = verify_manifest()
        contract = load_json(CONTRACT)
        expected_counts = contract.get("expected_counts") or {}
        expected_roots = int(expected_counts.get("install_proposals", -1))
        expected_exclusions = int(expected_counts.get("preinstall_excluded", -1))
        expected_domain = expected_roots + expected_exclusions
        config_errors = hook_config_errors()
        if config_errors:
            return False, "HOOK_CONFIG_INVALID: " + "; ".join(config_errors)
        hook = load_json(HOOK_RECEIPT)
        selection = load_json(SELECTION_RECEIPT)
        runtime_receipt = load_json(RUNTIME_RECEIPT)
        if hook.get("schema") != "constraintbox.cb-light-hook-run.v1":
            return False, "HOOK_RECEIPT_SCHEMA_INVALID"
        if selection.get("schema") != "constraintbox.cb-light-selection.v1":
            return False, "SELECTION_RECEIPT_SCHEMA_INVALID"
        if hook.get("manifest_identity_sha256") != manifest.get("manifest_sha256"):
            return False, "HOOK_RECEIPT_MANIFEST_STALE"
        if selection.get("manifest_identity_sha256") != manifest.get("manifest_sha256"):
            return False, "SELECTION_RECEIPT_MANIFEST_STALE"
        if sha256_file(SELECTION_RECEIPT) != hook.get("selection_receipt_sha256"):
            return False, "SELECTION_RECEIPT_TAMPERED"
        separation_ok, separation_reason, separation = verify_light_heavy_separation(
            manifest
        )
        if not separation_ok or separation is None:
            return False, separation_reason
        recorded_separation = hook.get("light_heavy_separation")
        if not isinstance(recorded_separation, Mapping):
            return False, "HOOK_LIGHT_HEAVY_SEPARATION_NOT_RECORDED"
        if pathlib.Path(
            str(recorded_separation.get("receipt_path", ""))
        ).resolve() != LIGHT_HEAVY_SEPARATION_RECEIPT.resolve():
            return False, "HOOK_LIGHT_HEAVY_SEPARATION_PATH_MISMATCH"
        if (
            sha256_file(LIGHT_HEAVY_SEPARATION_RECEIPT)
            != recorded_separation.get("receipt_sha256")
        ):
            return False, "HOOK_LIGHT_HEAVY_SEPARATION_TAMPERED"
        if (
            recorded_separation.get("passed") is not True
            or recorded_separation.get("reason_code") != separation_reason
            or recorded_separation.get("fresh_wheel_probe_passed") is not True
        ):
            return False, "HOOK_LIGHT_HEAVY_SEPARATION_INVALID"
        observed_sources = source_paths()
        claimed_hashes = hook.get("source_hashes")
        if not isinstance(claimed_hashes, dict) or set(claimed_hashes) != set(
            observed_sources
        ):
            return False, "HOOK_SOURCE_SET_MISMATCH"
        if hook.get("source_set_sha256") != hashlib.sha256(
            canonical_json(claimed_hashes)
        ).hexdigest():
            return False, "HOOK_SOURCE_SET_DIGEST_MISMATCH"
        for name, path in observed_sources.items():
            expected = claimed_hashes[name]
            if not path.is_file() or sha256_file(path) != expected:
                return False, f"HOOK_SOURCE_DRIFT:{name}"
        authoritative_inputs = {
            "manifest": MANIFEST,
            "runtime_install": RUNTIME_RECEIPT,
            "clean_install": CLEAN_RECEIPT,
            "operation": OPERATION_RECEIPT,
            "metadata": METADATA_RECEIPT,
        }
        input_receipts = selection.get("input_receipts")
        if not isinstance(input_receipts, dict) or set(input_receipts) != set(
            authoritative_inputs
        ):
            return False, "SELECTION_INPUT_SET_MISMATCH"
        for label, expected_path in authoritative_inputs.items():
            binding = input_receipts[label]
            path = pathlib.Path(str(binding.get("path", ""))).resolve()
            if path != expected_path.resolve():
                return False, f"SELECTION_INPUT_PATH_MISMATCH:{label}"
            if not path.is_file() or sha256_file(path) != binding.get("sha256"):
                return False, f"SELECTION_INPUT_DRIFT:{label}"
        contract_binding = selection.get("contract") or {}
        contract_path = ROOT / "config/cb_light_contract_v1.json"
        if pathlib.Path(str(contract_binding.get("path", ""))).resolve() != contract_path.resolve():
            return False, "SELECTION_CONTRACT_PATH_MISMATCH"
        if sha256_file(contract_path) != contract_binding.get("sha256"):
            return False, "SELECTION_CONTRACT_DRIFT"
        probe_sources = selection.get("probe_sources")
        expected_probe_sources = {
            "install": ROOT / "scripts/cb_light_install_probe.py",
            "metadata": ROOT / "scripts/cb_light_metadata_probe.py",
            "operation": ROOT / "light_runtime/src/constraintbox/cb_light_tool_probes.py",
        }
        if not isinstance(probe_sources, dict) or set(probe_sources) != set(
            expected_probe_sources
        ):
            return False, "PROBE_SOURCE_SET_MISMATCH"
        for label, expected_path in expected_probe_sources.items():
            binding = probe_sources[label]
            if pathlib.Path(str(binding.get("path", ""))).resolve() != expected_path.resolve():
                return False, f"PROBE_SOURCE_PATH_MISMATCH:{label}"
            if sha256_file(expected_path) != binding.get("sha256"):
                return False, f"PROBE_SOURCE_DRIFT:{label}"
        captured = dt.datetime.fromisoformat(str(hook["evaluated_at"]))
        if captured.tzinfo is None:
            return False, "HOOK_RECEIPT_TIMESTAMP_NAIVE"
        age = dt.datetime.now(dt.timezone.utc) - captured.astimezone(dt.timezone.utc)
        if age.total_seconds() < -300:
            return False, "HOOK_RECEIPT_TIMESTAMP_IN_FUTURE"
        if age.total_seconds() > max_age_hours * 3600:
            return False, f"HOOK_RECEIPT_STALE_HOURS:{age.total_seconds() / 3600:.2f}"
        counts = selection.get("counts") or {}
        accounted = (
            int(counts.get("selected_for_work", 0))
            + int(counts.get("hold_missing_evidence", 0))
            + int(counts.get("hold_decider_disagreement", 0))
        )
        if (
            counts.get("proposed") != expected_roots
            or counts.get("preinstall_excluded") != expected_exclusions
            or counts.get("evaluated_candidate_domain") != expected_domain
            or accounted != expected_roots
        ):
            return False, "SELECTION_NOT_EXACTLY_91_ACCOUNTED"
        if counts.get("hold_decider_disagreement") != 0:
            return False, "SMT_DECIDER_DISAGREEMENT"
        rows = selection.get("rows")
        if not isinstance(rows, list) or len(rows) != expected_roots:
            return False, f"SELECTION_ROWS_NOT_EXACTLY_{expected_roots}"
        manifest_names = {
            str(row.get("normalized_name")) for row in manifest.get("tools", [])
        }
        selection_names = {str(row.get("normalized_name")) for row in rows}
        if selection_names != manifest_names:
            return False, "SELECTION_ROW_IDENTITIES_MISMATCH"
        finite_decision = selection.get("finite_selection_decision")
        if not isinstance(finite_decision, dict):
            return False, "FINITE_SELECTION_DECISION_MISSING"
        if finite_decision.get("agree") is not True or finite_decision.get(
            "unique_assignment"
        ) is not True:
            return False, "FINITE_SELECTION_DECIDERS_INVALID"
        assignments = finite_decision.get("assignment") or {}
        deciders = finite_decision.get("deciders") or {}
        if set(assignments) != manifest_names:
            return False, "FINITE_SELECTION_ASSIGNMENT_SET_MISMATCH"
        for row in rows:
            disposition = row.get("work_disposition")
            facts = row.get("usable_now_facts")
            votes = row.get("decider_votes")
            if not isinstance(facts, dict) or not isinstance(votes, dict):
                return False, "SELECTION_ROW_EVIDENCE_MALFORMED"
            expected_votes = {
                name: (body.get("assignment") or {}).get(row.get("normalized_name"))
                for name, body in deciders.items()
            }
            if votes != expected_votes or len(set(votes.values())) != 1:
                return False, "SELECTION_ROW_DECIDER_INVALID"
            expected_selected = all(value is True for value in facts.values())
            if assignments.get(row.get("normalized_name")) is not expected_selected:
                return False, "FINITE_SELECTION_ASSIGNMENT_FACT_MISMATCH"
            if disposition == "SELECTED_FOR_WORK":
                if not expected_selected:
                    return False, "SELECTED_ROW_NOT_WITNESSED"
            elif disposition == "HOLD_MISSING_EVIDENCE":
                if expected_selected:
                    return False, "HELD_ROW_NOT_WITNESSED"
            else:
                return False, "SELECTION_ROW_DISPOSITION_INVALID"
        derived_counts = {
            "proposed": len(rows),
            "selected_for_work": sum(
                row.get("work_disposition") == "SELECTED_FOR_WORK" for row in rows
            ),
            "hold_missing_evidence": sum(
                row.get("work_disposition") == "HOLD_MISSING_EVIDENCE" for row in rows
            ),
            "hold_decider_disagreement": sum(
                row.get("work_disposition") == "HOLD_DECIDER_DISAGREEMENT" for row in rows
            ),
            "portable_adopted": sum(row.get("adopted") is True for row in rows),
            "selected_core": sum(
                row.get("work_disposition") == "SELECTED_FOR_WORK"
                and row.get("source_group") == "core"
                for row in rows
            ),
        }
        if any(counts.get(key) != value for key, value in derived_counts.items()):
            return False, "SELECTION_COUNT_ROW_MISMATCH"
        runtime_ok, runtime_reason = verify_runtime_postcondition(runtime_receipt)
        if not runtime_ok:
            return False, runtime_reason
        recorded_postcondition = hook.get("runtime_postcondition") or {}
        if recorded_postcondition.get("passed") is not True:
            return False, "HOOK_RUNTIME_POSTCONDITION_NOT_RECORDED"
        recorded_package_integrity = recorded_postcondition.get(
            "installed_light_package_source_integrity"
        )
        if (
            not isinstance(recorded_package_integrity, Mapping)
            or recorded_package_integrity.get("passed") is not True
        ):
            return False, "HOOK_INSTALLED_LIGHT_PACKAGE_INTEGRITY_NOT_RECORDED"
        if selection.get("evaluation_complete") is not True:
            return False, "SELECTION_EVALUATION_INCOMPLETE"
        if selection.get("evaluation_allowed") is not True:
            return False, "SELECTION_EVALUATION_NOT_ALLOWED"
        if hook.get("evaluation_allowed") is not True:
            return False, "HOOK_EVALUATION_NOT_ALLOWED"
        if require_live_boundary:
            live_ok, live_reason = verify_live_light_heavy_separation(manifest)
            if not live_ok:
                return False, live_reason
        return True, (
            "CB_LIGHT_EVALUATION_VERIFIED:"
            f"selected={counts.get('selected_for_work')},"
            f"held={counts.get('hold_missing_evidence')},"
            f"excluded_before_install={expected_exclusions}"
        )
    except FileNotFoundError as exc:
        return False, f"REQUIRED_RECEIPT_MISSING:{exc.filename}"
    except (HookRefusal, ValueError, KeyError, json.JSONDecodeError) as exc:
        return False, f"EVALUATION_VERIFICATION_ERROR:{type(exc).__name__}:{exc}"


def verify_completion_state(
    max_age_hours: float = 24.0,
    *,
    require_live_boundary: bool = False,
) -> tuple[bool, str, bool, str]:
    """Return completion and its exact underlying evaluation state.

    A completion transition is intentionally unavailable for this local CB
    Light slice.  Keeping the evaluation verdict beside the completion HOLD
    prevents a command from live-checking one state and printing a stale value
    for the other.
    """

    evaluation_allowed, evaluation_reason = verify_evaluation(
        max_age_hours, require_live_boundary=require_live_boundary
    )
    if not evaluation_allowed:
        return False, evaluation_reason, False, evaluation_reason
    return (
        False,
        "SYSTEM_COMPLETION_NOT_EARNED:"
        "PORTABLE_ADOPTION_OWNER_APPROVAL_REAL_CONSUMER_AND_HEAVY_PROFILE_PENDING",
        True,
        evaluation_reason,
    )


def verify_completion(
    max_age_hours: float = 24.0,
    *,
    require_live_boundary: bool = False,
) -> tuple[bool, str]:
    """Refuse a global completion claim even when Light evaluation is current.

    Retaining this function keeps the old public call shape fail-closed while
    making the lifecycle distinction literal.  Callers that need to protect a
    Light-local operation must use :func:`verify_evaluation`; they must not
    accidentally use a nonexistent system-release transition as a liveness
    gate.
    """

    completion_allowed, completion_reason, _, _ = verify_completion_state(
        max_age_hours, require_live_boundary=require_live_boundary
    )
    return completion_allowed, completion_reason


def record_post_failure(payload: Mapping[str, Any]) -> None:
    target = RECEIPTS / "cb_light_post_tool_failures.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "constraintbox.cb-light-post-tool-failure.v1",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload_sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        "tool_name": payload.get("tool_name"),
        "command_sha256": hashlib.sha256(command_from_payload(payload).encode()).hexdigest(),
        "error_type": payload.get("error_type"),
        "is_interrupt": payload.get("is_interrupt"),
        "is_timeout": payload.get("is_timeout"),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def record_hook_event(event: str, payload: Mapping[str, Any]) -> None:
    target = RECEIPTS / "cb_light_hook_events.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "constraintbox.cb-light-hook-event.v1",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event": event,
        "hook_event_name": payload.get("hook_event_name"),
        "tool_name": payload.get("tool_name"),
        "session_id": payload.get("session_id"),
        "payload_sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cb-light-hook")
    parser.add_argument(
        "event",
        choices=(
            "pre-tool",
            "post-tool",
            "post-tool-failure",
            "post-tool-batch",
            "task-completed",
            "subagent-stop",
            "stop",
            "session-start",
            "config-change",
            "file-changed",
            "refresh",
            "status",
        ),
    )
    parser.add_argument("--payload-json")
    args = parser.parse_args(argv)

    try:
        if args.event == "refresh":
            body = refresh()
            print(json.dumps(body, indent=2, sort_keys=True))
            return 0 if body["evaluation_allowed"] else 2
        if args.event == "status":
            allowed, reason = verify_evaluation(require_live_boundary=True)
            print(
                json.dumps(
                    {
                        "completion_allowed": False,
                        "evaluation_allowed": allowed,
                        "reason_code": reason,
                        "system_completion_reason": (
                            "LOCAL_CB_LIGHT_EVALUATION_DOES_NOT_EARN_SYSTEM_COMPLETION"
                        ),
                    },
                    sort_keys=True,
                )
            )
            return 0 if allowed else 1

        payload = read_payload(args.payload_json)
        if not payload:
            return blocking_failure("HOOK_PAYLOAD_MISSING", args.event)
        if args.event in {"stop", "subagent-stop"} and payload.get(
            "stop_hook_active"
        ) is True:
            # Avoid creating a receipt solely to record that a recursive stop
            # check was suppressed.  The negative control is the zero-write,
            # zero-recursion path itself.
            print(
                f"CB Light {args.event} verification already active; "
                "returning without a recursive block",
                file=sys.stderr,
            )
            return 0
        record_hook_event(args.event, payload)
        if args.event == "pre-tool":
            manifest = verify_manifest()
            try:
                if _tool_name(payload) == "Bash":
                    command = command_from_payload(payload)
                    evaluated = evaluate_install(payload, manifest)
                    transition = git_transition(command)
                    if transition:
                        allowed, reason = verify_evaluation(require_live_boundary=True)
                        if not allowed:
                            return deny_pretool(
                                f"{transition.upper()}_REQUIRES_CURRENT_CB_LIGHT_RECEIPT",
                                reason,
                            )
                else:
                    evaluated = evaluate_file_write(payload)
            except HookRefusal as exc:
                return deny_pretool(exc.reason_code, exc.detail)
            if evaluated.get("mutation") or evaluated.get("target"):
                print(json.dumps(evaluated, sort_keys=True))
            return 0
        if args.event == "post-tool":
            manifest = verify_manifest()
            if _tool_name(payload) == "Bash":
                evaluate_install(payload, manifest)
            else:
                evaluate_file_write(payload)
            allowed, reason = verify_evaluation()
            if not allowed:
                return blocking_failure("BASH_POSTCONDITION_FAILED", reason)
            body = load_json(HOOK_RECEIPT)
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PostToolUse",
                            "additionalContext": (
                                "CB Light post-Bash check preserved the contained runtime: "
                                f"{body['selection_counts']}"
                            ),
                        }
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.event == "post-tool-failure":
            record_post_failure(payload)
            evaluated = classify_command(
                command_from_payload(payload),
                cwd=_project_cwd(payload),
                broker=BROKER,
            )
            if evaluated.get("broker"):
                return blocking_failure(
                    "BROKER_TOOL_FAILED", str(payload.get("error") or payload.get("error_type"))
                )
            return 0
        if args.event in {
            "post-tool-batch",
            "task-completed",
            "subagent-stop",
            "stop",
        }:
            allowed, reason = verify_evaluation(require_live_boundary=True)
            reason_code = {
                "post-tool-batch": "TOOL_BATCH_POSTCONDITION_REFUSED",
                "task-completed": "TASK_COMPLETION_REFUSED",
                "subagent-stop": "SUBAGENT_COMPLETION_REFUSED",
                "stop": "STOP_COMPLETION_REFUSED",
            }[args.event]
            return 0 if allowed else blocking_failure(reason_code, reason)
        if args.event == "config-change":
            errors = hook_config_errors()
            return 0 if not errors else blocking_failure("HOOK_CONFIG_DRIFT", "; ".join(errors))
        if args.event == "file-changed":
            allowed, reason = verify_evaluation()
            print(
                json.dumps(
                    {
                        "systemMessage": (
                            "CB Light FileChanged observation only (this event cannot block): "
                            f"current={allowed}; status={reason}"
                        )
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.event == "session-start":
            allowed, reason = verify_evaluation()
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "SessionStart",
                            "additionalContext": (
                                f"ConstraintBox Light is a separate 91-tool Python profile. "
                                f"Local evaluation current={allowed}; status={reason}. "
                                "System completion remains unearned; do not treat external "
                                "simulation-engine stacks as Light membership."
                            ),
                        }
                    },
                    sort_keys=True,
                )
            )
            return 0
    except HookRefusal as exc:
        if args.event == "pre-tool":
            return deny_pretool(exc.reason_code, exc.detail)
        return blocking_failure(exc.reason_code, exc.detail)
    except Exception as exc:
        return blocking_failure(
            "HOOK_INTERNAL_ERROR", f"{type(exc).__name__}: {str(exc)[:500]}"
        )
    raise AssertionError(args.event)


if __name__ == "__main__":
    raise SystemExit(main())
