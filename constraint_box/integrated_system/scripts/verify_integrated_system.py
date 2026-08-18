#!/usr/bin/env python3
"""Run the bounded, model-free verification of an integrated CB package.

This verifier is deliberately a controller, not a second gate implementation.
It runs named local commands, records their exact invocation and bounded output,
then performs a few independent hash/projection checks over the retained
artifacts.  It never launches a provider, chooses a model, promotes a wave, or
turns a missing optional runtime into a green result.

The command is usable from a source checkout and from the extracted bundle::

    python verify_integrated_system.py --box-root /path/to/constraint_box \
        --light-python /path/to/light/python \
        --jax-python /path/to/jax/python --output VERIFY.json

The report is intentionally bounded.  Full subprocess streams are not copied
into the report; their lengths, hashes, and tails are retained so a human can
diagnose a failure without making the package depend on a giant log corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


SCHEMA = "constraintbox.integrated-system-verification.v1"
MAX_CAPTURE_BYTES = 8_192
DEFAULT_TIMEOUT_SECONDS = 300.0

# The verifier is deliberately model-free.  Provider adapter unit tests use
# fixture runners, but they are not part of the default release verification
# route: an accidental provider binary in PATH must never become a side effect
# of ``cb verify``.
PROVIDER_TEST_PATHS = (
    "constraint_box/tests/test_provider_call_receipt.py",
    "constraint_box/tests/test_grok_cli_adapter.py",
    "constraint_box/tests/test_claude_bridge_adapter.py",
    "constraint_box/tests/test_codex_cli_adapter.py",
)

BRIDGE_CHILD_NAMES = (
    "seed",
    "etf_exact",
    "etf_dual",
    "maintenance",
    "context",
    "exploration",
    "dualsolve",
)

# These are receipt fields that identify retained files/directories.  Runtime
# identity fields such as ``interpreter`` and ``realpath`` are intentionally
# excluded: an external JAX interpreter is a declared boundary, not a retained
# product artifact.
_RETAINED_PATH_KEYS = frozenset(
    {
        "path",
        "root",
        "cwd",
        "declared_path",
        "resolved_path",
        "relative_path",
        "project_mmm_draft",
        "user_mmm_draft",
        "output_path",
        "input_path",
        "source_path",
        "fixture_path",
    }
)

_EPOCH_POINTER_SCHEMA = "constraintbox.current-context-epoch-pointer.v1"
_EPOCH_SCHEMA = "constraintbox.context-epoch.v2"
_EPOCH_BOUND_FILE_KEYS = frozenset(
    {
        "corpus",
        "corpus_manifest",
        "refresh_ledger",
        "current_context",
        "wave_bootstrap",
        "consolidation",
        "retained_receipt_manifest",
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_without(value: dict[str, Any], field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    return sha256_bytes(canonical_json_bytes(body))


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tail_text(value: str, limit: int = MAX_CAPTURE_BYTES) -> str:
    if len(value) <= limit:
        return value
    return "...[truncated]...\n" + value[-limit:]


def relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def parse_pytest_summary(output: str) -> dict[str, Any]:
    """Extract the small stable part of pytest's summary without trusting it."""

    text = output.strip()
    fields: dict[str, int] = {}
    for name in (
        "passed",
        "failed",
        "skipped",
        "xfailed",
        "xpassed",
        "error",
        "errors",
        "warnings",
    ):
        match = re.search(rf"(?<![A-Za-z])([0-9]+) {name}\b", text)
        if match:
            fields[name] = int(match.group(1))
    collected = re.search(r"([0-9]+) tests? collected", text)
    if collected:
        fields["collected"] = int(collected.group(1))
    if "no tests ran" in text.lower():
        fields["no_tests_ran"] = 1
    return fields


def _reported_env(env: dict[str, str]) -> dict[str, str]:
    keys = (
        "PYTHONPATH",
        "PYTHONNOUSERSITE",
        "PYTHONDONTWRITEBYTECODE",
        "CB_BOX_ROOT",
        "CB_CONTROLLER_SRC",
        "CB_LIGHT_PYTHON",
        "CB_LIGHT_BUILD_INTERPRETER",
        "CB_LIGHT_ROOT",
        "CB_LIGHT_INTERPRETER",
        "CB_JAX_PYTHON",
        "CB_SKILLS_ROOT",
        "CB_MMM_ROOT",
        "CB_MMM_PACKS_ROOT",
        "CB_PYTHON",
    )
    return {key: env[key] for key in keys if key in env}


def run_command(
    command_id: str,
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
    expected_returncodes: Iterable[int] = (0,),
    missing_is_hold: bool = True,
) -> dict[str, Any]:
    """Run one explicit command and return a bounded, receipt-like record."""

    expected = sorted(set(int(code) for code in expected_returncodes))
    started = time.monotonic()
    record: dict[str, Any] = {
        "id": command_id,
        "argv": [str(item) for item in argv],
        "cwd": str(cwd.resolve()),
        "env": _reported_env(env),
        "expected_returncodes": expected,
        "timeout_seconds": timeout_seconds,
    }
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=False,
            timeout=timeout_seconds,
        )
        stdout_bytes = bytes(completed.stdout or b"")
        stderr_bytes = bytes(completed.stderr or b"")
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        record.update(
            {
                "returncode": completed.returncode,
                "status": "PASS" if completed.returncode in expected else "FAIL",
                "duration_seconds": round(time.monotonic() - started, 6),
                "stdout_bytes": len(stdout_bytes),
                "stderr_bytes": len(stderr_bytes),
                "stdout_sha256": sha256_bytes(stdout_bytes),
                "stderr_sha256": sha256_bytes(stderr_bytes),
                "stdout_tail": tail_text(stdout),
                "stderr_tail": tail_text(stderr),
            }
        )
        summary = parse_pytest_summary(stdout + "\n" + stderr)
        if summary:
            record["pytest_summary"] = summary
        return record
    except FileNotFoundError as exc:
        record.update(
            {
                "status": "HOLD" if missing_is_hold else "FAIL",
                "reason_code": "HOLD_COMMAND_MISSING" if missing_is_hold else "FAIL_COMMAND_MISSING",
                "detail": str(exc),
                "duration_seconds": round(time.monotonic() - started, 6),
            }
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"") if isinstance(exc.stdout, bytes) else (exc.stdout or "").encode()
        stderr = (exc.stderr or b"") if isinstance(exc.stderr, bytes) else (exc.stderr or "").encode()
        record.update(
            {
                "status": "HOLD",
                "reason_code": "HOLD_COMMAND_TIMEOUT",
                "duration_seconds": round(time.monotonic() - started, 6),
                "stdout_bytes": len(stdout),
                "stderr_bytes": len(stderr),
                "stdout_sha256": sha256_bytes(stdout),
                "stderr_sha256": sha256_bytes(stderr),
                "stdout_tail": tail_text(stdout.decode("utf-8", errors="replace")),
                "stderr_tail": tail_text(stderr.decode("utf-8", errors="replace")),
            }
        )
    except OSError as exc:
        record.update(
            {
                "status": "HOLD" if missing_is_hold else "FAIL",
                "reason_code": "HOLD_COMMAND_OS_ERROR" if missing_is_hold else "FAIL_COMMAND_OS_ERROR",
                "detail": f"{type(exc).__name__}:{exc}",
                "duration_seconds": round(time.monotonic() - started, 6),
            }
        )
    return record


def make_env(box_root: Path, light_python: Path, jax_python: Path | None) -> dict[str, str]:
    repo_root = box_root.parent
    system_root = box_root / "integrated_system"
    # A fresh bundle has one merged controller source and one separate ZIP
    # Agent source.  A source checkout still has the pre-merge roots.  Prefer
    # the merged roots when present, but retain the checkout fallback so this
    # verifier can attest both layouts without importing a duplicate package.
    controller = system_root / "runtime" / "controller_src"
    zip_runtime = system_root / "runtime" / "zip_agent_src"
    if controller.is_dir() and zip_runtime.is_dir():
        # The merged controller and ZIP Agent roots are the only runtime
        # authorities in an extracted product.  Do not put an ambient
        # checkout root ahead of them: its ``src/constraintbox`` can shadow
        # the source closure the bundle just attested.
        roots = [controller, zip_runtime]
        controller_source = controller
    else:
        # A source checkout has no generated merged tree.  Prefer the
        # selected Light overlay, then ZIP Agent, and use the historical root
        # only as a last-resort compatibility fallback for source-only tests.
        controller_source = box_root / "light_runtime" / "src"
        if not controller_source.is_dir():
            controller_source = box_root / "src"
        roots = [
            controller_source,
            box_root / "zip_agent" / "src",
            box_root / "src",
            repo_root,
        ]
    env = os.environ.copy()
    env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "CB_BOX_ROOT": str(box_root),
            "CB_LIGHT_PYTHON": str(light_python),
            "CB_LIGHT_ROOT": str(box_root),
            "CB_LIGHT_INTERPRETER": str(light_python),
            "CB_CONTROLLER_SRC": str(controller_source),
            "CB_SKILLS_ROOT": str(box_root / "integrated_system" / "skills"),
            "CB_MMM_ROOT": str(box_root / "integrated_system" / "mmms" / "primary"),
            "CB_MMM_PACKS_ROOT": str(box_root / "mmm" / "packs"),
            "PYTHONPATH": os.pathsep.join(str(path) for path in roots if path.is_dir()),
        }
    )
    if jax_python is not None:
        env["CB_JAX_PYTHON"] = str(jax_python)
    build_python = box_root / ".bootstrap-light-build" / "bin" / "python"
    if build_python.is_file():
        env["CB_LIGHT_BUILD_INTERPRETER"] = str(build_python)
    return env


def find_interpreter(value: str | None, fallback: Path) -> Path | None:
    candidate = Path(value).expanduser() if value else fallback
    candidate = candidate.absolute()
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate
    return None


def _load_epoch_module(system_root: Path) -> Any:
    """Load the canonical epoch verifier shipped beside this verifier.

    The integrated verifier is also imported directly by focused tests and is
    executed from a fresh extract, so relying on the process ``sys.path`` to
    find ``seal_context_epoch`` would make the context gate host-dependent.
    Loading the adjacent source file by path keeps the epoch implementation
    the single authority in both layouts.
    """

    scripts_root = system_root / "scripts"
    if scripts_root.is_symlink():
        raise ValueError(f"REFUSE_EPOCH_VERIFIER_SCRIPTS_SYMLINK:{scripts_root}")
    script = scripts_root / "seal_context_epoch.py"
    if script.is_symlink():
        raise ValueError(f"REFUSE_EPOCH_VERIFIER_SYMLINK:{script}")
    if not script.exists():
        raise FileNotFoundError(f"epoch verifier is missing: {script}")
    if not script.is_file() or not stat.S_ISREG(script.stat().st_mode):
        raise ValueError(f"REFUSE_EPOCH_VERIFIER_NOT_REGULAR:{script}")
    try:
        resolved_scripts_root = scripts_root.resolve(strict=True)
        resolved_script = script.resolve(strict=True)
        resolved_script.relative_to(resolved_scripts_root)
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"REFUSE_EPOCH_VERIFIER_PATH_ESCAPE:{script}"
        ) from exc
    module_sha256 = sha256_file(resolved_script)
    spec = importlib.util.spec_from_file_location(
        "constraintbox_integrated_seal_context_epoch", resolved_script
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load epoch verifier: {resolved_script}")
    module = importlib.util.module_from_spec(spec)
    prior_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior_dont_write_bytecode
    return module, module_sha256, resolved_script


def _verify_current_epoch(system_root: Path) -> dict[str, Any]:
    """Verify CURRENT_EPOCH, its complete chain, and every bound file.

    Epoch paths are rooted at the repository/project root (the parent of the
    ``constraint_box`` directory), which remains true after extraction under
    ``PROJECT/constraint_box``.  The pointer is intentionally non-authoritative
    metadata; it is still consumed and checked because it identifies the epoch
    selected for this product.
    """

    pointer_candidate = system_root / "state" / "CURRENT_EPOCH.json"
    pointer_path = pointer_candidate
    if not pointer_candidate.is_file():
        return {
            "status": "FAIL",
            "reason_codes": ["FAIL_CONTEXT_CURRENT_EPOCH_MISSING"],
            "promotion_allowed": False,
        }
    try:
        # Normalize only the surrounding checkout path.  The epoch module
        # still walks the normalized relative pointer and refuses a symlinked
        # pointer/file component; this avoids macOS /var -> /private/var
        # lexical mismatches when verifying a fresh extracted bundle.
        system_path = system_root.expanduser().resolve(strict=True)
        pointer_path = system_path / "state" / "CURRENT_EPOCH.json"
        root = system_path.parent.parent
        epoch_module, epoch_module_sha256, epoch_module_path = _load_epoch_module(
            system_path
        )
        verified = epoch_module.verify_pointer(root, pointer_path)
        pointer = read_json(pointer_path)
        epoch_ref = pointer.get("epoch")
        if not isinstance(epoch_ref, Mapping):
            raise ValueError("CURRENT_EPOCH epoch reference is not an object")
        epoch_path, reason = _safe_scoped_path(
            epoch_ref.get("path"), root, reason_prefix="FAIL_CONTEXT_EPOCH"
        )
        if epoch_path is None:
            raise ValueError(reason or "invalid CURRENT_EPOCH epoch path")
        epoch = read_json(epoch_path)
    except Exception as exc:  # the epoch module reports the precise refusal
        return {
            "status": "FAIL",
            "reason_codes": [
                f"FAIL_CONTEXT_EPOCH:{type(exc).__name__}:{exc}"
            ],
            "pointer_path": relative_or_absolute(pointer_path, system_root),
            "promotion_allowed": False,
        }

    if pointer.get("schema") != _EPOCH_POINTER_SCHEMA:
        return {
            "status": "FAIL",
            "reason_codes": ["FAIL_CONTEXT_EPOCH_POINTER_SCHEMA"],
            "pointer_path": relative_or_absolute(pointer_path, system_root),
            "promotion_allowed": False,
        }
    if epoch.get("schema") != _EPOCH_SCHEMA:
        return {
            "status": "FAIL",
            "reason_codes": ["FAIL_CONTEXT_EPOCH_SCHEMA"],
            "pointer_path": relative_or_absolute(pointer_path, system_root),
            "promotion_allowed": False,
        }
    bound_files = epoch.get("bound_files")
    if not isinstance(bound_files, Mapping) or set(bound_files) != _EPOCH_BOUND_FILE_KEYS:
        return {
            "status": "FAIL",
            "reason_codes": ["FAIL_CONTEXT_EPOCH_BOUND_FILE_SET"],
            "pointer_path": relative_or_absolute(pointer_path, system_root),
            "promotion_allowed": False,
        }
    current_context = bound_files.get("current_context")
    current_context_count = len(current_context) if isinstance(current_context, Mapping) else 0
    epoch_summary = verified.get("epoch") if isinstance(verified, Mapping) else {}
    return {
        "status": "PASS",
        "reason_codes": [],
        "pointer_path": relative_or_absolute(pointer_path, system_root),
        "epoch_verifier_path": relative_or_absolute(
            epoch_module_path, system_root
        ),
        "epoch_verifier_sha256": epoch_module_sha256,
        "pointer_sha256": sha256_file(pointer_path),
        "epoch_path": epoch_summary.get("path"),
        "epoch_sha256": epoch_summary.get("sha256"),
        "epoch_id": epoch.get("epoch_id"),
        "epoch_sequence": epoch.get("epoch_sequence"),
        "epoch_parent": epoch.get("parent"),
        "bound_file_keys": sorted(bound_files),
        "bound_current_context_count": current_context_count,
        "promotion_allowed": False,
    }


def check_context(system_root: Path) -> dict[str, Any]:
    """Recompute the context projection and require the current epoch chain.

    ``GENESIS.json`` is verified only as the immutable root of the epoch chain
    by ``seal_context_epoch``.  Mutable current documents are never compared
    to Genesis hashes; their exact bytes are checked through the selected
    CURRENT_EPOCH binding instead.
    """

    errors: list[str] = []
    epoch_check = _verify_current_epoch(system_root)
    if epoch_check.get("status") != "PASS":
        errors.extend(str(code) for code in epoch_check.get("reason_codes", []))
    manifest_path = system_root / "context" / "full" / "CORPUS_MANIFEST.json"
    corpus_path = system_root / "context" / "full" / "prompt_plan_progress_corpus.jsonl"
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "FAIL",
            "reason_codes": [*errors, "FAIL_CONTEXT_METADATA"],
            "detail": f"{type(exc).__name__}:{exc}",
            "epoch": epoch_check,
            "promotion_allowed": False,
        }
    if not corpus_path.is_file():
        errors.append("FAIL_CONTEXT_CORPUS_MISSING")
        corpus_sha = None
        corpus_bytes = None
        event_count = 0
    else:
        corpus_bytes = corpus_path.stat().st_size
        corpus_sha = sha256_file(corpus_path)
        event_count = 0
        try:
            for line in corpus_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                json.loads(line)
                event_count += 1
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"FAIL_CONTEXT_CORPUS_INVALID:{type(exc).__name__}")
    if corpus_sha != manifest.get("output_sha256"):
        errors.append("FAIL_CONTEXT_CORPUS_DIGEST_MISMATCH")
    if corpus_bytes != manifest.get("output_bytes"):
        errors.append("FAIL_CONTEXT_CORPUS_SIZE_MISMATCH")
    if event_count != manifest.get("selected_event_count"):
        errors.append("FAIL_CONTEXT_EVENT_COUNT_MISMATCH")
    if manifest.get("promotion_allowed") is not False:
        errors.append("FAIL_CONTEXT_PROMOTION_FLAG")
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "corpus_sha256": corpus_sha,
        "corpus_bytes": corpus_bytes,
        "event_count": event_count,
        "manifest_event_count": manifest.get("selected_event_count"),
        "source_event_count": manifest.get("source_event_count"),
        "epoch": epoch_check,
        "epoch_verifier_path": epoch_check.get("epoch_verifier_path"),
        "epoch_verifier_sha256": epoch_check.get("epoch_verifier_sha256"),
        "promotion_allowed": False,
    }


def check_jax_profile(system_root: Path) -> dict[str, Any]:
    """Attest the shipped, external JAX profile without installing or probing it."""

    profile = system_root / "runtime_profiles" / "jax_qit"
    required = (
        "README.md",
        "STACK_MANIFEST.template.json",
        "bootstrap_jax_qit.py",
        "probe_runtime.py",
        "requirements.in",
        "requirements.lock",
    )
    errors = [
        f"FAIL_JAX_PROFILE_MISSING:{name}"
        for name in required
        if not (profile / name).is_file()
    ]
    template: dict[str, Any] = {}
    template_path = profile / "STACK_MANIFEST.template.json"
    if template_path.is_file():
        try:
            template = read_json(template_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"FAIL_JAX_PROFILE_TEMPLATE:{type(exc).__name__}")
    if template:
        if template.get("schema") != "constraintbox.jax-qit-stack-manifest.v1":
            errors.append("FAIL_JAX_PROFILE_TEMPLATE_SCHEMA")
        if template.get("profile") != "jax_qit":
            errors.append("FAIL_JAX_PROFILE_TEMPLATE_PROFILE")
        if template.get("promotion_allowed") is not False:
            errors.append("FAIL_JAX_PROFILE_PROMOTION_FLAG")
        boundaries = template.get("boundaries")
        if not isinstance(boundaries, dict) or boundaries.get("cb_light_runtime") is not False:
            errors.append("FAIL_JAX_PROFILE_LIGHT_BOUNDARY")
        if not isinstance(boundaries, dict) or boundaries.get("project_source_installed") is not False:
            errors.append("FAIL_JAX_PROFILE_PROJECT_BOUNDARY")
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "profile": relative_or_absolute(profile, system_root),
        "requirements_sha256": sha256_file(profile / "requirements.in") if (profile / "requirements.in").is_file() else None,
        "lock_sha256": sha256_file(profile / "requirements.lock") if (profile / "requirements.lock").is_file() else None,
        "runtime_probe_is_live": False,
        "promotion_allowed": False,
    }


def _load_public_wave_catalog(system_root: Path) -> dict[str, Any]:
    """Reuse the public launcher catalog without activating any wave.

    ``bin/cb`` is the trusted public discovery surface.  Loading it with
    bytecode writes disabled keeps this model-free inventory read-only while
    preserving the launcher as the sole classification authority.
    """

    launcher = system_root / "bin" / "cb"
    result: dict[str, Any] = {
        "source_path": relative_or_absolute(launcher, system_root),
        "source_sha256": None,
        "catalog": None,
        "error": None,
    }
    if launcher.is_symlink():
        result["error"] = f"REFUSE_PUBLIC_CATALOG_SYMLINK:{launcher}"
        return result
    if not launcher.is_file() or not stat.S_ISREG(launcher.stat().st_mode):
        result["error"] = f"REFUSE_PUBLIC_CATALOG_NOT_REGULAR:{launcher}"
        return result
    result["source_sha256"] = sha256_file(launcher)
    try:
        loader = SourceFileLoader("constraintbox_public_catalog_launcher", str(launcher))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if spec is None or spec.loader is None:
            raise ImportError("catalog_loader_missing")
        module = importlib.util.module_from_spec(spec)
        prior_dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
            discover = getattr(module, "discover_wave_catalog", None)
            if not callable(discover):
                raise AttributeError("discover_wave_catalog_missing")
            result["catalog"] = discover(system_root=system_root)
        finally:
            sys.dont_write_bytecode = prior_dont_write_bytecode
    except Exception as exc:  # fail closed at the verifier boundary
        result["error"] = f"REFUSE_PUBLIC_CATALOG_LOAD:{type(exc).__name__}:{exc}"
    return result


def _catalog_projection(catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Select source-bound public catalog fields for a stable digest."""

    rows = catalog.get("waves")
    if not isinstance(rows, list):
        return []
    projection: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            projection.append({"row": row})
            continue
        projection.append(
            {
                "wave_id": row.get("wave_id"),
                "definition": row.get("definition"),
                "definition_wave_id": row.get("definition_wave_id"),
                "definition_sha256": row.get("definition_sha256"),
                "source_sha256": row.get("source_sha256"),
                "skill_sha256": row.get("skill_sha256"),
                "classification": row.get("classification"),
                "runnable": row.get("runnable"),
                "promotion_allowed": row.get("promotion_allowed"),
            }
        )
    return projection


def check_skill_estate(system_root: Path) -> dict[str, Any]:
    skills_root = system_root / "skills"
    errors: list[str] = []
    manifest = skills_root / "MANIFEST.txt"
    active_path = skills_root / "ACTIVE_WAVES.json"
    if not manifest.is_file() or not manifest.read_text(encoding="utf-8").strip():
        errors.append("FAIL_SKILL_MANIFEST_MISSING")
    try:
        active = read_json(active_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "reason_codes": ["FAIL_ACTIVE_WAVE_MANIFEST", f"{type(exc).__name__}:{exc}"]}
    definitions = list(active.get("wave_definitions") or [])
    runnable = list(active.get("runnable_cohort") or [])
    zip_definition = active.get("zip_wave_definition")
    if not definitions or not isinstance(zip_definition, str):
        errors.append("FAIL_ACTIVE_WAVE_MANIFEST_SHAPE")
    seen_relative: set[object] = set()
    for relative in [*definitions, zip_definition]:
        if relative in seen_relative:
            errors.append(f"FAIL_WAVE_DEFINITION_PATH_DUPLICATE:{relative}")
            continue
        seen_relative.add(relative)
        path, reason = _safe_scoped_path(relative, skills_root, reason_prefix="FAIL_WAVE_DEFINITION")
        if path is None:
            errors.append(f"{reason}:{relative}")
            continue
        try:
            body = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"FAIL_WAVE_DEFINITION:{relative}:{type(exc).__name__}")
            continue
        if body.get("promotion_allowed") is True:
            errors.append(f"FAIL_WAVE_PROMOTION_FLAG:{relative}")
    catalog_result: dict[str, Any] = {
        "source_path": relative_or_absolute(system_root / "bin" / "cb", system_root),
        "source_sha256": None,
        "catalog": None,
        "error": None,
    }
    catalog_rows: list[Mapping[str, Any]] = []
    active_catalog: list[Mapping[str, Any]] = []
    authored_catalog: list[Mapping[str, Any]] = []
    candidate_catalog: list[Mapping[str, Any]] = []
    catalog_sha256: str | None = None
    if not errors:
        catalog_result = _load_public_wave_catalog(system_root)
        catalog = catalog_result.get("catalog")
        if catalog_result.get("error"):
            errors.append(str(catalog_result["error"]))
        elif not isinstance(catalog, Mapping):
            errors.append("FAIL_PUBLIC_WAVE_CATALOG_SHAPE")
        else:
            if catalog.get("catalog_state") != "READY":
                errors.append("FAIL_PUBLIC_WAVE_CATALOG_STATE")
            catalog_errors = catalog.get("catalog_errors")
            if isinstance(catalog_errors, list):
                errors.extend(f"FAIL_PUBLIC_WAVE_CATALOG:{value}" for value in catalog_errors)
            rows = catalog.get("waves")
            if not isinstance(rows, list):
                errors.append("FAIL_PUBLIC_WAVE_CATALOG_WAVES_SHAPE")
            else:
                catalog_rows = [row for row in rows if isinstance(row, Mapping)]
                active_catalog = [
                    row for row in catalog_rows if row.get("classification") == "ACTIVE"
                ]
                authored_catalog = [
                    row
                    for row in catalog_rows
                    if row.get("classification") == "AUTHORED_INACTIVE"
                ]
                candidate_catalog = [
                    row
                    for row in catalog_rows
                    if row.get("classification") == "UNREGISTERED_CANDIDATE"
                ]
                for row in candidate_catalog:
                    if row.get("runnable") is not False:
                        errors.append(
                            f"FAIL_PUBLIC_WAVE_CANDIDATE_RUNNABLE:{row.get('wave_id')}"
                        )
                    if row.get("promotion_allowed") is not False:
                        errors.append(
                            f"FAIL_PUBLIC_WAVE_CANDIDATE_PROMOTION:{row.get('wave_id')}"
                        )
                projection = {
                    "catalog_schema": catalog.get("catalog_schema"),
                    "catalog_state": catalog.get("catalog_state"),
                    "manifest_sha256": sha256_file(active_path)
                    if active_path.is_file()
                    else None,
                    "waves": _catalog_projection(catalog),
                }
                catalog_sha256 = sha256_bytes(canonical_json_bytes(projection))
    if not catalog_rows:
        catalog_rows = []
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "manifest_sha256": sha256_file(manifest) if manifest.is_file() else None,
        "active_manifest_sha256": sha256_file(active_path) if active_path.is_file() else None,
        "active_wave_count": len(active_catalog) if catalog_rows else len(runnable),
        "runnable_wave_count": len(active_catalog) if catalog_rows else len(runnable),
        "runnable_wave_ids": [
            row.get("wave_id")
            for row in (active_catalog if catalog_rows else runnable)
            if isinstance(row, Mapping)
        ],
        "wave_definition_count": len(catalog_rows) if catalog_rows else len(definitions),
        "catalog_definition_count": len(catalog_rows) if catalog_rows else len(definitions),
        "catalog_source": catalog_result.get("source_path"),
        "catalog_source_sha256": catalog_result.get("source_sha256"),
        "catalog_sha256": catalog_sha256,
        "wave_catalog_sha256": catalog_sha256,
        "zip_wave_definition": zip_definition,
        "script_backed_without_wave_definition": active.get("script_backed_without_wave_definition", []),
        "authored_specs_not_active": [
            row.get("wave_id") for row in authored_catalog
        ]
        if catalog_rows
        else active.get("authored_specs_not_active", []),
        "authored_specs_not_active_count": (
            len(authored_catalog)
            if catalog_rows
            else len(active.get("authored_specs_not_active", []))
        ),
        "unregistered_candidates": [row.get("wave_id") for row in candidate_catalog],
        "unregistered_candidate_count": len(candidate_catalog),
        "promotion_allowed": False,
    }


def check_retained_artifacts(system_root: Path) -> dict[str, Any]:
    """Check durable receipts without treating them as fresh execution."""

    errors: list[str] = []
    required = [
        system_root / "00_READ_THIS_FIRST.md",
        system_root / "bin" / "cb",
        system_root / "context" / "current" / "OWNER_OBJECT.md",
        system_root / "context" / "current" / "CURRENT_PLAN.md",
        system_root / "context" / "current" / "FAILURE_MEMORY.md",
        system_root / "state" / "GENESIS.json",
    ]
    missing = [relative_or_absolute(path, system_root) for path in required if not path.is_file()]
    errors.extend(f"FAIL_REQUIRED_ARTIFACT_MISSING:{path}" for path in missing)
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "required_count": len(required),
        "missing": missing,
        "promotion_allowed": False,
    }


def _safe_scoped_path(
    value: object, root: Path, *, reason_prefix: str
) -> tuple[Path | None, str | None]:
    """Resolve ``value`` as a path scoped strictly under ``root``.

    Returns ``(path, None)`` on success or ``(None, reason_code)`` naming why
    the path was rejected: not a non-empty string, absolute, containing a
    ``.``/``..`` segment, or escaping ``root`` after symlink resolution.  The
    caller is responsible for detecting duplicate-path ambiguity across the
    set of declared entries it is scoping.
    """

    if not isinstance(value, str) or not value:
        return None, f"{reason_prefix}_PATH_MISSING"
    if "\x00" in value:
        return None, f"{reason_prefix}_PATH_MALFORMED"
    # Check the authored spelling before PurePosixPath normalizes it.  These
    # paths are current authority declarations; accepting ``./x`` or ``x//y``
    # after normalization would let two spellings name one wave and would
    # hide malformed/backslash escapes in a supposedly portable packet.
    if "\\" in value:
        return None, f"{reason_prefix}_PATH_BACKSLASH"
    if "//" in value:
        return None, f"{reason_prefix}_PATH_DUPLICATE_SEPARATOR"
    raw_parts = value.split("/")
    if any(part == "." for part in raw_parts):
        return None, f"{reason_prefix}_PATH_DOT_SEGMENT"
    if any(part == ".." for part in raw_parts):
        return None, f"{reason_prefix}_PATH_PARENT_TRAVERSAL"
    posix = PurePosixPath(value)
    if posix.is_absolute():
        return None, f"{reason_prefix}_PATH_ABSOLUTE"
    if any(part == "" for part in raw_parts):
        return None, f"{reason_prefix}_PATH_EMPTY_SEGMENT"
    parts = posix.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        return None, f"{reason_prefix}_PATH_PARENT_TRAVERSAL"
    candidate = root.joinpath(*parts)
    try:
        root_resolved = root.resolve()
        resolved = candidate.resolve()
    except OSError:
        return None, f"{reason_prefix}_PATH_UNRESOLVABLE"
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return None, f"{reason_prefix}_PATH_SYMLINK_ESCAPE"
    return candidate, None


def _retained_path_findings(
    value: object,
    *,
    product_root: Path,
    location: str = "",
) -> list[dict[str, str]]:
    """Classify path-bearing fields in historical receipts.

    Receipts under the retained-evidence boundary are historical observations,
    not release payload authority.  A syntactically valid absolute path is
    therefore ``STALE``: it usually names the checkout that produced the old
    receipt and must never turn an otherwise valid product into ``FAIL`` just
    because that checkout is absent.  Relative traversal, malformed values,
    and symlink/executable escapes remain ``FAIL`` because they are actionable
    path-integrity defects.  Provider/runtime identity fields are not
    inspected here because they intentionally identify external interpreters.
    """

    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}" if location else str(key)
            if str(key).lower() in _RETAINED_PATH_KEYS:
                # ``path`` is also used by a few finite-state projections as
                # a list, and ``root`` can carry a diagnostic mapping.  Those
                # containers are semantic values; recurse into them and only
                # classify scalar path declarations.
                if isinstance(child, (dict, list)):
                    pass
                elif not isinstance(child, str) or not child or "\x00" in child:
                    findings.append(
                        {
                            "severity": "FAIL",
                            "location": child_location,
                            "value": str(child),
                            "reason": "MALFORMED_PATH",
                        }
                    )
                else:
                    posix = PurePosixPath(child)
                    if "\\" in child or any(
                        part in ("", ".", "..") for part in posix.parts
                    ):
                        findings.append(
                            {
                                "severity": "FAIL",
                                "location": child_location,
                                "value": child,
                                "reason": "MALFORMED_OR_TRAVERSAL_PATH",
                            }
                        )
                    else:
                        try:
                            candidate = Path(child).expanduser()
                        except (OSError, RuntimeError, ValueError):
                            findings.append(
                                {
                                    "severity": "FAIL",
                                    "location": child_location,
                                    "value": child,
                                    "reason": "MALFORMED_PATH",
                                }
                            )
                        else:
                            if candidate.is_absolute():
                                findings.append(
                                    {
                                        "severity": "STALE",
                                        "location": child_location,
                                        "value": child,
                                        "reason": "ABSOLUTE_HISTORICAL_PATH",
                                    }
                                )
                            else:
                                candidate = product_root / candidate
                                try:
                                    resolved = candidate.resolve(strict=False)
                                    product = product_root.resolve(strict=True)
                                    resolved.relative_to(product)
                                except (OSError, ValueError):
                                    findings.append(
                                        {
                                            "severity": "FAIL",
                                            "location": child_location,
                                            "value": child,
                                            "reason": "EXECUTABLE_PATH_ESCAPE",
                                        }
                                    )
                # Some receipt fields are semantic paths (for example a
                # finite state path ["z_left", "a"], not filesystem paths.
                # Recurse into mappings/lists, but do not mistake those
                # sequences for retained file references.
            findings.extend(
                _retained_path_findings(
                    child, product_root=product_root, location=child_location
                )
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(
                _retained_path_findings(
                    child,
                    product_root=product_root,
                    location=f"{location}[{index}]" if location else f"[{index}]",
                )
            )
    return findings


def _child_file_path_findings(
    bindings: object, *, run_root: Path
) -> tuple[list[str], list[str]]:
    """Validate the relative keys of a receipt's child-file hash registry."""

    if not isinstance(bindings, dict):
        return [], []
    children = bindings.get("child_file_sha256")
    if not isinstance(children, dict):
        return [], []
    errors: list[str] = []
    stale: list[str] = []
    for relative in children:
        path, disposition, reason = _historical_receipt_path(
            relative,
            root=run_root,
            reason_prefix="BRIDGE_CHILD_FILE",
        )
        if disposition == "STALE" and reason:
            stale.append(reason)
        elif path is None:
            errors.append(reason or f"FAIL_BRIDGE_CHILD_FILE_PATH:{relative}")
    return errors, stale


def _historical_receipt_path(
    value: object,
    *,
    root: Path,
    reason_prefix: str,
) -> tuple[Path | None, str | None, str | None]:
    """Resolve an explicitly audited receipt path with stale-path handling.

    The return tuple is ``(path, disposition, reason_code)``.  ``disposition``
    is ``STALE`` for a valid absolute historical path, ``FAIL`` for a malformed
    or executable escape, and ``None`` for a safe relative path.
    """

    findings = _retained_path_findings(
        {"path": value}, product_root=root, location="path"
    )
    if findings:
        finding = findings[0]
        if finding.get("severity") == "STALE":
            return (
                None,
                "STALE",
                f"STALE_{reason_prefix}_PATH_ABSOLUTE:{finding.get('value')}",
            )
        scoped_reason: str | None = None
        if isinstance(value, str):
            _scoped_path, scoped_reason = _safe_scoped_path(
                value,
                root,
                reason_prefix=f"FAIL_{reason_prefix}",
            )
        return (
            None,
            "FAIL",
            (
                f"{scoped_reason}:{value}"
                if scoped_reason
                else f"FAIL_{reason_prefix}_{finding.get('reason', 'PATH_INVALID')}:{finding.get('value')}"
            ),
        )
    path, reason = _safe_scoped_path(
        value, root, reason_prefix=f"FAIL_{reason_prefix}"
    )
    if path is None:
        return None, "FAIL", f"{reason}:{value}"
    return path, None, None


_CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})[ \t][ *](.+)$")

# A fresh extracted product may acquire these machine-local runtimes before
# its envelope is rechecked.  They are deliberately an exact, product-local
# allowlist: the roots themselves must be ordinary directories, while their
# generated contents (including the normal venv interpreter symlink) are not
# part of the release payload closure.
_GENERATED_RUNTIME_ROOTS = (
    "PROJECT/constraint_box/.venv",
    "PROJECT/constraint_box/.venv-clean",
    "PROJECT/constraint_box/.bootstrap-light-build",
    "PROJECT/constraint_box/integrated_system/runs",
    "PROJECT/constraint_box/receipts",
)


def _bundle_runtime_root_exclusions(
    bundle_root: Path,
) -> tuple[set[str], list[str]]:
    """Return exact generated roots and refuse malformed root replacements."""

    excluded: set[str] = set()
    errors: list[str] = []
    for relative in _GENERATED_RUNTIME_ROOTS:
        path = bundle_root.joinpath(*PurePosixPath(relative).parts)
        if path.is_symlink():
            errors.append(f"FAIL_BUNDLE_RUNTIME_ROOT_SYMLINK:{relative}")
        elif path.exists():
            try:
                is_regular_directory = stat.S_ISDIR(path.stat().st_mode)
            except OSError:
                is_regular_directory = False
            if not is_regular_directory:
                errors.append(f"FAIL_BUNDLE_RUNTIME_ROOT_NOT_DIRECTORY:{relative}")
            else:
                excluded.add(relative)
    return excluded, errors


def _safe_bundle_path(value: object, bundle_root: Path) -> Path | None:
    """Resolve a manifest/checksum path safely under ``bundle_root``.

    Rejects malformed raw spellings (dot segments, duplicate separators,
    backslashes, NULs, empty segments), absolute/traversal paths, and any
    resolution that lands outside ``bundle_root``.  A tampered bundle cannot
    use normalization to disguise an unsafe path or a safe-looking relative
    path to point at a file outside the bundle root.
    """

    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    if "\\" in value or "//" in value:
        return None
    raw_parts = value.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        return None
    posix = PurePosixPath(value)
    if posix.is_absolute():
        return None
    parts = posix.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        return None
    candidate = bundle_root.joinpath(*parts)
    try:
        resolved = candidate.resolve()
        root_resolved = bundle_root.resolve()
    except OSError:
        return None
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return None
    return candidate


def find_bundle_root(box_root: Path) -> Path | None:
    """Find the extracted bundle's top-level directory, if one is present.

    Checks ``box_root`` itself, then two ancestor directories, then immediate
    children, for the three files that make up a release bundle envelope.
    An extracted release keeps that envelope two levels above
    ``PROJECT/constraint_box``.  A source checkout has no such directory, so
    this returns ``None`` rather than guessing.
    """

    def has_envelope(path: Path) -> bool:
        return (
            path.is_dir()
            and (path / "SYSTEM_MANIFEST.json").is_file()
            and (path / "BUNDLE_METADATA.json").is_file()
            and (path / "SHA256SUMS").is_file()
        )

    for candidate in (box_root, box_root.parent, box_root.parent.parent):
        if has_envelope(candidate):
            return candidate
    if not box_root.is_dir():
        return None
    for child in sorted(box_root.iterdir()):
        if not child.is_symlink() and has_envelope(child):
            return child
    return None


def _bundle_physical_files(bundle_root: Path) -> tuple[set[str], list[str]]:
    """Return regular physical files and reject symlinked bundle entries."""

    files: set[str] = set()
    errors: list[str] = []
    if bundle_root.is_symlink():
        return files, ["FAIL_BUNDLE_ROOT_SYMLINK"]
    if not bundle_root.is_dir():
        return files, ["FAIL_BUNDLE_ROOT_NOT_DIRECTORY"]
    excluded_runtime_roots, runtime_root_errors = _bundle_runtime_root_exclusions(
        bundle_root
    )
    errors.extend(runtime_root_errors)
    for current, directories, names in os.walk(
        bundle_root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current_path / name
            relative = path.relative_to(bundle_root).as_posix()
            if relative in excluded_runtime_roots:
                continue
            if path.is_symlink():
                errors.append(f"FAIL_BUNDLE_SYMLINK_DIRECTORY:{path.name}")
            elif name == "__pycache__":
                errors.append(f"FAIL_BUNDLE_UNLISTED_CACHE_DIRECTORY:{relative}")
            else:
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in sorted(names):
            path = current_path / name
            relative = path.relative_to(bundle_root).as_posix()
            if path.is_symlink():
                errors.append(f"FAIL_BUNDLE_SYMLINK_FILE:{relative}")
            elif name == "__pycache__":
                errors.append(f"FAIL_BUNDLE_UNLISTED_CACHE_PATH:{relative}")
            elif not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
                errors.append(f"FAIL_BUNDLE_NONREGULAR_FILE:{relative}")
            else:
                files.add(relative)
    return files, errors


def cleanup_generated_bytecode(
    box_root: Path, initial_envelope: Mapping[str, Any]
) -> dict[str, Any]:
    """Remove only fresh, direct regular ``.pyc`` cache entries.

    The initial envelope check deliberately treats every source ``__pycache__``
    as an unexpected physical directory.  Therefore a PASS there establishes
    the baseline: any cache found here was created by this verification run.
    Generated runtime roots remain excluded by their exact allowlist, while a
    malformed cache is refused before any cleanup mutation occurs.
    """

    base: dict[str, Any] = {
        "count": 0,
        "paths": [],
        "digests": {},
        "cache_dirs": [],
        "promotion_allowed": False,
    }
    if initial_envelope.get("status") != "PASS":
        return {
            **base,
            "status": "NOT_APPLICABLE",
            "reason_codes": ["NOT_APPLICABLE_INITIAL_BUNDLE_ENVELOPE"],
        }

    bundle_root = find_bundle_root(box_root)
    if bundle_root is None:
        return {
            **base,
            "status": "FAIL",
            "reason_codes": ["FAIL_GENERATED_BYTECODE_BUNDLE_ROOT_MISSING"],
        }
    excluded_runtime_roots, runtime_root_errors = _bundle_runtime_root_exclusions(
        bundle_root
    )
    if runtime_root_errors:
        return {
            **base,
            "status": "FAIL",
            "reason_codes": runtime_root_errors,
            "bundle_root": str(bundle_root),
        }

    errors: list[str] = []
    cache_dirs: list[Path] = []

    def walk_error(exc: OSError) -> None:
        errors.append(
            f"FAIL_GENERATED_BYTECODE_WALK:{type(exc).__name__}:{exc.filename}"
        )

    for current, directories, names in os.walk(
        bundle_root,
        topdown=True,
        followlinks=False,
        onerror=walk_error,
    ):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current_path / name
            relative = path.relative_to(bundle_root).as_posix()
            if relative in excluded_runtime_roots:
                continue
            if name == "__pycache__":
                if path.is_symlink():
                    errors.append(f"FAIL_GENERATED_BYTECODE_CACHE_SYMLINK:{relative}")
                else:
                    cache_dirs.append(path)
                continue
            if path.is_symlink():
                # The post-envelope scan remains authoritative for unrelated
                # fresh symlinks; do not follow one while inventorying caches.
                continue
            kept_directories.append(name)
        directories[:] = kept_directories
        for name in sorted(names):
            if name != "__pycache__":
                continue
            path = current_path / name
            relative = path.relative_to(bundle_root).as_posix()
            if path.is_symlink():
                errors.append(f"FAIL_GENERATED_BYTECODE_CACHE_SYMLINK:{relative}")
            else:
                errors.append(f"FAIL_GENERATED_BYTECODE_CACHE_NOT_DIRECTORY:{relative}")

    candidates: list[tuple[Path, str, str]] = []
    for cache_dir in sorted(cache_dirs, key=lambda item: str(item)):
        relative_dir = cache_dir.relative_to(bundle_root).as_posix()
        try:
            if cache_dir.is_symlink() or not stat.S_ISDIR(cache_dir.stat().st_mode):
                errors.append(
                    f"FAIL_GENERATED_BYTECODE_CACHE_NOT_DIRECTORY:{relative_dir}"
                )
                continue
            entries = sorted(cache_dir.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            errors.append(
                f"FAIL_GENERATED_BYTECODE_CACHE_READ:{relative_dir}:{type(exc).__name__}"
            )
            continue
        for entry in entries:
            relative = entry.relative_to(bundle_root).as_posix()
            if entry.is_symlink():
                errors.append(f"FAIL_GENERATED_BYTECODE_SYMLINK:{relative}")
                continue
            try:
                mode = entry.stat().st_mode
            except OSError as exc:
                errors.append(
                    f"FAIL_GENERATED_BYTECODE_STAT:{relative}:{type(exc).__name__}"
                )
                continue
            if stat.S_ISDIR(mode):
                errors.append(f"FAIL_GENERATED_BYTECODE_NESTED_DIRECTORY:{relative}")
                continue
            if not stat.S_ISREG(mode):
                errors.append(f"FAIL_GENERATED_BYTECODE_NONREGULAR:{relative}")
                continue
            if entry.suffix != ".pyc":
                errors.append(f"FAIL_GENERATED_BYTECODE_FOREIGN_ENTRY:{relative}")
                continue
            try:
                digest = sha256_file(entry)
            except OSError as exc:
                errors.append(
                    f"FAIL_GENERATED_BYTECODE_DIGEST:{relative}:{type(exc).__name__}"
                )
                continue
            candidates.append((entry, relative, digest))

    # Validate the entire candidate set before unlinking anything.  A single
    # malformed or unremovable entry must not trigger partial cache cleanup.
    removed: list[tuple[str, str]] = []
    if not errors:
        for path, relative, digest in candidates:
            try:
                path.unlink()
            except OSError as exc:
                errors.append(
                    f"FAIL_GENERATED_BYTECODE_UNLINK:{relative}:{type(exc).__name__}"
                )
                break
            removed.append((relative, digest))
        for cache_dir in sorted(cache_dirs, key=lambda item: str(item), reverse=True):
            relative_dir = cache_dir.relative_to(bundle_root).as_posix()
            try:
                cache_dir.rmdir()
            except OSError as exc:
                errors.append(
                    f"FAIL_GENERATED_BYTECODE_RMDIR:{relative_dir}:{type(exc).__name__}"
                )

    paths = [relative for relative, _ in removed]
    digests = {relative: digest for relative, digest in removed}
    return {
        **base,
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "bundle_root": str(bundle_root),
        "count": len(removed),
        "paths": paths,
        "digests": digests,
        "cache_dirs": [
            cache_dir.relative_to(bundle_root).as_posix()
            for cache_dir in cache_dirs
            if not cache_dir.exists()
        ],
    }


def check_bundle_envelope(box_root: Path) -> dict[str, Any]:
    """Verify a release bundle's manifest/metadata/checksum envelope.

    This is a bounded, local, hash-only check: no provider is launched and
    no claim ceiling changes.  A source checkout carries no bundle envelope;
    that is NOT_APPLICABLE, not a false PASS or HOLD.
    """

    bundle_root = find_bundle_root(box_root)
    if bundle_root is None:
        return {
            "status": "NOT_APPLICABLE",
            "reason_codes": ["NOT_APPLICABLE_NO_BUNDLE_ENVELOPE"],
            "detail": "no directory under box_root carries SYSTEM_MANIFEST.json, BUNDLE_METADATA.json, and SHA256SUMS together",
            "promotion_allowed": False,
        }

    manifest_path = bundle_root / "SYSTEM_MANIFEST.json"
    metadata_path = bundle_root / "BUNDLE_METADATA.json"
    checksums_path = bundle_root / "SHA256SUMS"

    envelope_errors: list[str] = []
    for label, path in (
        ("MANIFEST", manifest_path),
        ("METADATA", metadata_path),
        ("CHECKSUMS", checksums_path),
    ):
        if path.is_symlink():
            envelope_errors.append(f"FAIL_BUNDLE_{label}_SYMLINK")
        elif not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            envelope_errors.append(f"FAIL_BUNDLE_{label}_NOT_REGULAR")
    physical_paths, physical_errors = _bundle_physical_files(bundle_root)
    envelope_errors.extend(physical_errors)
    if envelope_errors:
        return {
            "status": "FAIL",
            "reason_codes": list(dict.fromkeys(envelope_errors)),
            "bundle_root": str(bundle_root),
            "promotion_allowed": False,
        }

    manifest_bytes = manifest_path.read_bytes()
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as exc:
        return {
            "status": "FAIL",
            "reason_codes": [f"FAIL_BUNDLE_MANIFEST_INVALID_JSON:{type(exc).__name__}"],
            "bundle_root": str(bundle_root),
            "promotion_allowed": False,
        }
    if not isinstance(manifest, dict):
        return {
            "status": "FAIL",
            "reason_codes": ["FAIL_BUNDLE_MANIFEST_SHAPE"],
            "bundle_root": str(bundle_root),
            "promotion_allowed": False,
        }
    try:
        metadata = read_json(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "FAIL",
            "reason_codes": [f"FAIL_BUNDLE_METADATA_INVALID:{type(exc).__name__}"],
            "bundle_root": str(bundle_root),
            "promotion_allowed": False,
        }

    errors: list[str] = []
    manifest_sha256 = sha256_bytes(manifest_bytes)
    if manifest_sha256 != metadata.get("manifest_sha256"):
        errors.append("FAIL_BUNDLE_MANIFEST_DIGEST_MISMATCH")

    rows = manifest.get("files")
    if not isinstance(rows, list):
        errors.append("FAIL_BUNDLE_MANIFEST_FILES_SHAPE")
        rows = []
    if manifest.get("file_count") != len(rows):
        errors.append("FAIL_BUNDLE_MANIFEST_FILE_COUNT_MISMATCH")

    payload_bytes_total = 0
    expected_paths: set[str] = set()
    actual_digest_by_path: dict[str, str] = {}
    seen_manifest_paths: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("FAIL_BUNDLE_MANIFEST_ROW_SHAPE")
            continue
        raw_path = row.get("path")
        declared_bytes = row.get("bytes")
        declared_sha = row.get("sha256")
        target = _safe_bundle_path(raw_path, bundle_root)
        if target is None:
            errors.append(f"FAIL_BUNDLE_MANIFEST_PATH_UNSAFE:{raw_path!r}")
            continue
        safe_path = PurePosixPath(str(raw_path)).as_posix()
        if safe_path in seen_manifest_paths:
            errors.append(f"FAIL_BUNDLE_MANIFEST_DUPLICATE_PATH:{safe_path}")
        seen_manifest_paths.add(safe_path)
        expected_paths.add(safe_path)
        if isinstance(declared_bytes, int):
            payload_bytes_total += declared_bytes
        if target.is_symlink():
            errors.append(f"FAIL_BUNDLE_PAYLOAD_SYMLINK:{safe_path}")
            continue
        if not target.is_file() or not stat.S_ISREG(target.stat().st_mode):
            errors.append(f"FAIL_BUNDLE_PAYLOAD_MISSING:{safe_path}")
            continue
        actual_bytes = target.stat().st_size
        if declared_bytes != actual_bytes:
            errors.append(f"FAIL_BUNDLE_PAYLOAD_SIZE_MISMATCH:{safe_path}")
        actual_sha = sha256_file(target)
        actual_digest_by_path[safe_path] = actual_sha
        if not isinstance(declared_sha, str) or declared_sha != actual_sha:
            errors.append(f"FAIL_BUNDLE_PAYLOAD_DIGEST_MISMATCH:{safe_path}")

    if manifest.get("payload_bytes") != payload_bytes_total:
        errors.append("FAIL_BUNDLE_MANIFEST_PAYLOAD_BYTES_MISMATCH")

    # The source-closure digest binds the complete selected payload table.  It
    # is independent of the ZIP bytes and therefore survives extraction while
    # still detecting a missing, added, or changed source row.
    closure_rows = [
        {
            "path": row.get("path"),
            "bytes": row.get("bytes"),
            "sha256": row.get("sha256"),
            "mode": row.get("mode"),
        }
        for row in rows
        if isinstance(row, dict)
    ]
    source_closure_sha256 = sha256_bytes(canonical_json_bytes(closure_rows))
    if manifest.get("source_closure_sha256") != source_closure_sha256:
        errors.append("FAIL_BUNDLE_SOURCE_CLOSURE_DIGEST_MISMATCH")
    if metadata.get("source_closure_sha256") != source_closure_sha256:
        errors.append("FAIL_BUNDLE_METADATA_SOURCE_CLOSURE_MISMATCH")

    # The envelope documents themselves must also be covered by SHA256SUMS.
    expected_paths.add("SYSTEM_MANIFEST.json")
    actual_digest_by_path["SYSTEM_MANIFEST.json"] = manifest_sha256
    metadata_bytes = metadata_path.read_bytes()
    expected_paths.add("BUNDLE_METADATA.json")
    actual_digest_by_path["BUNDLE_METADATA.json"] = sha256_bytes(metadata_bytes)

    try:
        checksums_text = checksums_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"FAIL_BUNDLE_CHECKSUMS_UNREADABLE:{type(exc).__name__}")
        checksums_text = ""

    top_level_prefix: str | None = None
    top_level_mismatch = False
    found_checksum_paths: dict[str, str] = {}
    duplicate_checksum_paths: set[str] = set()
    for line_number, line in enumerate(checksums_text.splitlines(), start=1):
        if not line.strip():
            continue
        match = _CHECKSUM_LINE.match(line)
        if not match:
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_LINE_SHAPE:{line_number}")
            continue
        digest, entry_path = match.group(1).lower(), match.group(2)
        if (
            not isinstance(entry_path, str)
            or not entry_path
            or "\x00" in entry_path
            or "\\" in entry_path
            or "//" in entry_path
            or any(part in ("", ".", "..") for part in entry_path.split("/"))
        ):
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_PATH_UNSAFE:{entry_path!r}")
            continue
        posix_entry = PurePosixPath(entry_path)
        if posix_entry.is_absolute() or len(posix_entry.parts) < 2:
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_PATH_UNSAFE:{entry_path!r}")
            continue
        prefix = posix_entry.parts[0]
        rest = PurePosixPath(*posix_entry.parts[1:])
        if top_level_prefix is None:
            top_level_prefix = prefix
        elif prefix != top_level_prefix:
            top_level_mismatch = True
        if _safe_bundle_path(str(rest), bundle_root) is None:
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_PATH_UNSAFE:{entry_path!r}")
            continue
        rest_str = rest.as_posix()
        if rest_str in found_checksum_paths:
            duplicate_checksum_paths.add(rest_str)
            continue
        found_checksum_paths[rest_str] = digest

    if top_level_mismatch:
        errors.append("FAIL_BUNDLE_CHECKSUMS_TOP_LEVEL_INCONSISTENT")
    if top_level_prefix is not None and top_level_prefix != manifest.get("top_level"):
        errors.append("FAIL_BUNDLE_CHECKSUMS_TOP_LEVEL_MISMATCH")
    if manifest.get("top_level") != bundle_root.name:
        errors.append("FAIL_BUNDLE_MANIFEST_TOP_LEVEL_MISMATCH")
    for path in sorted(duplicate_checksum_paths):
        errors.append(f"FAIL_BUNDLE_CHECKSUMS_DUPLICATE:{path}")

    found_paths = set(found_checksum_paths)
    # SHA256SUMS cannot include its own final digest without a recursive
    # definition, so it is the one explicitly documented envelope exception.
    physical_checksum_paths = physical_paths - {"SHA256SUMS"}
    for path in sorted(physical_checksum_paths - found_paths):
        errors.append(f"FAIL_BUNDLE_CHECKSUMS_MISSING_PHYSICAL:{path}")
    for path in sorted(expected_paths - found_paths):
        errors.append(f"FAIL_BUNDLE_CHECKSUMS_MISSING:{path}")
    for path in sorted(found_paths - expected_paths):
        # SHA256SUMS need not cover itself.  If it does, the listed digest
        # still has to match the file bytes.
        if path == "SHA256SUMS":
            continue
        errors.append(f"FAIL_BUNDLE_CHECKSUMS_UNEXPECTED:{path}")
    for path in sorted(found_paths):
        target = _safe_bundle_path(path, bundle_root)
        if target is None:
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_PATH_UNSAFE:{path}")
        elif target.is_symlink():
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_SYMLINK:{path}")
        elif not target.is_file() or not stat.S_ISREG(target.stat().st_mode):
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_FILE_MISSING:{path}")
    if "SHA256SUMS" in found_checksum_paths:
        actual_digest_by_path["SHA256SUMS"] = sha256_file(checksums_path)
        if found_checksum_paths["SHA256SUMS"] != actual_digest_by_path["SHA256SUMS"]:
            errors.append("FAIL_BUNDLE_CHECKSUMS_DIGEST_MISMATCH:SHA256SUMS")
    for path in sorted(expected_paths & found_paths):
        actual = actual_digest_by_path.get(path)
        if actual is not None and found_checksum_paths[path] != actual:
            errors.append(f"FAIL_BUNDLE_CHECKSUMS_DIGEST_MISMATCH:{path}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "bundle_root": str(bundle_root),
        "top_level": manifest.get("top_level"),
        "manifest_sha256": manifest_sha256,
        "manifest_file_count": len(rows),
        "manifest_payload_bytes": payload_bytes_total,
        "source_closure_sha256": source_closure_sha256,
        "checksum_entry_count": len(found_checksum_paths),
        "promotion_allowed": False,
    }


def structured_projection(value: dict[str, Any]) -> dict[str, Any]:
    """Select fields whose meaning is shared by exact and dual engines."""

    return {
        "schema": value.get("schema"),
        "status": value.get("status"),
        "finding": value.get("finding"),
        "fixture_id": value.get("fixture_id"),
        "structured": value.get("structured"),
        "generic_endomap_control": value.get("generic_endomap_control"),
        "solver": value.get("solver"),
        "controls": value.get("controls"),
        "forbidden_inferences": value.get("forbidden_inferences"),
        "next_operation": value.get("next_operation"),
        "claim_ceiling": value.get("claim_ceiling"),
        "promotion_allowed": value.get("promotion_allowed"),
    }


def check_structured_receipt(system_root: Path) -> dict[str, Any]:
    runs = system_root / "runs"
    crosscheck_path = runs / "STRUCTURED_OPEN_BIND_CROSSCHECK.json"
    if not crosscheck_path.is_file():
        return {
            "status": "NOT_APPLICABLE",
            "reason_codes": ["NOT_APPLICABLE_NO_RETAINED_STRUCTURED_RECEIPT"],
            "promotion_allowed": False,
        }
    errors: list[str] = []
    stale_reasons: list[str] = []
    try:
        crosscheck = read_json(crosscheck_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "reason_codes": ["FAIL_STRUCTURED_RECEIPT", f"{type(exc).__name__}:{exc}"]}
    for finding in _retained_path_findings(
        crosscheck, product_root=system_root.parent, location="crosscheck"
    ):
        finding_text = f"{finding['location']}:{finding['value']}"
        if finding.get("severity") == "STALE":
            stale_reasons.append(f"STALE_STRUCTURED_RETAINED_PATH:{finding_text}")
        else:
            errors.append(f"FAIL_STRUCTURED_RETAINED_PATH:{finding_text}")
    exact_record = crosscheck.get("exact")
    dual_record = crosscheck.get("dual")
    exact_record = exact_record if isinstance(exact_record, dict) else {}
    dual_record = dual_record if isinstance(dual_record, dict) else {}
    exact_path, exact_disposition, exact_reason = _historical_receipt_path(
        exact_record.get("path"),
        root=runs,
        reason_prefix="STRUCTURED_RECEIPT",
    )
    dual_path, dual_disposition, dual_reason = _historical_receipt_path(
        dual_record.get("path"),
        root=runs,
        reason_prefix="STRUCTURED_RECEIPT",
    )
    for disposition, reason in (
        (exact_disposition, exact_reason),
        (dual_disposition, dual_reason),
    ):
        if reason and disposition == "STALE":
            stale_reasons.append(reason)
        elif reason:
            errors.append(reason)
    if exact_path is not None and dual_path is not None and exact_path == dual_path:
        return {"status": "FAIL", "reason_codes": ["FAIL_STRUCTURED_RECEIPT_PATH_DUPLICATE"]}
    exact: dict[str, Any] | None = None
    dual: dict[str, Any] | None = None
    for label, path in (("exact", exact_path), ("dual", dual_path)):
        if path is None:
            continue
        try:
            value = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"FAIL_STRUCTURED_RECEIPT:{label}:{type(exc).__name__}")
            continue
        if label == "exact":
            exact = value
        else:
            dual = value
    if crosscheck.get("status") != "PASS":
        errors.append("FAIL_STRUCTURED_CROSSCHECK_STATUS")
    if crosscheck.get("exact_jax_agreement") is not True:
        errors.append("FAIL_STRUCTURED_JAX_AGREEMENT")
    if exact is not None and exact.get("status") != "PASS":
        errors.append("FAIL_STRUCTURED_RESULT_STATUS:exact")
    if dual is not None and dual.get("status") != "PASS":
        errors.append("FAIL_STRUCTURED_RESULT_STATUS:dual")
    if (exact_path is not None and exact is None) or (dual_path is not None and dual is None):
        errors.append("FAIL_STRUCTURED_RESULT_MISSING")
    if exact is not None and exact.get("promotion_allowed") is not False:
        errors.append("FAIL_STRUCTURED_PROMOTION_FLAG:exact")
    if dual is not None and dual.get("promotion_allowed") is not False:
        errors.append("FAIL_STRUCTURED_PROMOTION_FLAG:dual")
    if exact is not None and dual is not None:
        exact_projection = structured_projection(exact)
        dual_projection = structured_projection(dual)
        projection_sha = sha256_bytes(canonical_json_bytes(exact_projection))
        if exact_projection != dual_projection:
            errors.append("FAIL_STRUCTURED_SEMANTIC_PROJECTION_MISMATCH")
    else:
        exact_projection = None
        dual_projection = None
        projection_sha = None
    for label, value in (("exact", exact), ("dual", dual)):
        if value is None:
            continue
        for finding in _retained_path_findings(
            value, product_root=system_root.parent, location=label
        ):
            reason = f"{finding['location']}:{finding['value']}"
            if finding.get("severity") == "STALE":
                stale_reasons.append(f"STALE_STRUCTURED_RETAINED_PATH:{reason}")
            else:
                errors.append(f"FAIL_STRUCTURED_RETAINED_PATH:{reason}")
    expected_projection = crosscheck.get("shared_semantic_projection_sha256")
    # The historical crosscheck stores a digest but does not store the
    # projection schema/field-selection recipe that produced it.  Do not
    # silently pretend our verifier's independently selected projection is the
    # same object.  Exact/dual equality is checked above; the old digest is
    # reported as an un-recomputed historical binding instead of being used as
    # a false-green or false-red verdict.
    for path, row, value in (
        (exact_path, exact_record, exact),
        (dual_path, dual_record, dual),
    ):
        if path is None or value is None:
            continue
        actual_file_sha = sha256_file(path)
        if row.get("file_sha256") is not None and row.get("file_sha256") != actual_file_sha:
            errors.append(f"FAIL_STRUCTURED_FILE_DIGEST:{path.name}")
        result_sha = value.get("result_sha256")
        if result_sha is not None and result_sha != digest_without(value, "result_sha256"):
            errors.append(f"FAIL_STRUCTURED_RESULT_DIGEST:{path.name}")
    stale_reasons = list(dict.fromkeys(stale_reasons))
    status = "FAIL" if errors else ("STALE" if stale_reasons else "PASS")
    return {
        "status": status,
        "reason_codes": [*errors, *stale_reasons],
        "stale_reason_codes": stale_reasons,
        "exact_file_sha256": sha256_file(exact_path) if exact_path is not None and exact_path.is_file() else None,
        "dual_file_sha256": sha256_file(dual_path) if dual_path is not None and dual_path.is_file() else None,
        "semantic_projection_sha256": projection_sha,
        "crosscheck_projection_sha256": expected_projection,
        "crosscheck_projection_recomputed": False,
        "crosscheck_projection_basis": "historical digest has no declared field-selection recipe",
        "exact_jax_agreement": crosscheck.get("exact_jax_agreement"),
        "claim_ceiling": crosscheck.get("claim_ceiling"),
        "promotion_allowed": False,
    }


def check_bridge_receipt(system_root: Path) -> dict[str, Any]:
    replay_path = system_root / "runs" / "LIGHT_JAX_WAVE_REPLAY.json"
    if not replay_path.is_file():
        return {
            "status": "NOT_APPLICABLE",
            "reason_codes": ["NOT_APPLICABLE_NO_RETAINED_BRIDGE_RECEIPT"],
            "promotion_allowed": False,
        }
    errors: list[str] = []
    stale_reasons: list[str] = []
    try:
        replay = read_json(replay_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "reason_codes": ["FAIL_BRIDGE_REPLAY_METADATA", f"{type(exc).__name__}:{exc}"]}
    rows = replay.get("runs")
    if replay.get("status") != "PASS" or replay.get("semantic_replay_identical") is not True:
        errors.append("FAIL_BRIDGE_REPLAY_STATUS")
    if not isinstance(rows, list) or len(rows) < 2:
        errors.append("FAIL_BRIDGE_REPLAY_RUN_COUNT")
        rows = []
    receipts: list[dict[str, Any]] = []
    box_root = system_root.parent
    for finding in _retained_path_findings(
        replay, product_root=box_root, location="replay"
    ):
        finding_text = f"{finding['location']}:{finding['value']}"
        if finding.get("severity") == "STALE":
            stale_reasons.append(f"STALE_BRIDGE_RETAINED_PATH:{finding_text}")
        else:
            errors.append(f"FAIL_BRIDGE_RETAINED_PATH_OUTSIDE_PRODUCT:{finding_text}")
    current_binding_paths = {
        "bridge_source_sha256": system_root / "scripts" / "run_light_jax_wave_bridge.py",
        "field_source_sha256": box_root / "scripts" / "contained_light" / "entropic_time_field.py",
        "seed_source_sha256": box_root / "scripts" / "contained_light" / "seed_check.py",
        "fixture_sha256": box_root / "scripts" / "contained_light" / "fixtures" / "entropic_time_field_v1.json",
        "campaign_source_sha256": box_root / "experiments" / "manifold_capability" / "v1" / "campaign.py",
        "campaign_custody_sha256": box_root / "experiments" / "manifold_capability" / "v1" / "REPLAY_CUSTODY.json",
    }
    current_bindings = {
        name: sha256_file(path) if path.is_file() else None
        for name, path in current_binding_paths.items()
    }
    seen_paths: set[Path] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("FAIL_BRIDGE_REPLAY_ROW_SHAPE")
            continue
        declared = row.get("path")
        path, disposition, reason = _historical_receipt_path(
            declared,
            root=system_root / "runs",
            reason_prefix="BRIDGE_RECEIPT",
        )
        if disposition == "STALE" and reason:
            stale_reasons.append(reason)
            continue
        if path is None:
            errors.append(reason or f"FAIL_BRIDGE_RECEIPT_PATH:{declared}")
            continue
        if path in seen_paths:
            errors.append(f"FAIL_BRIDGE_RECEIPT_PATH_DUPLICATE:{declared}")
            continue
        seen_paths.add(path)
        try:
            receipt = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"FAIL_BRIDGE_RECEIPT:{type(exc).__name__}")
            continue
        receipts.append(receipt)
        actual_file_sha = sha256_file(path)
        if row.get("file_sha256") != actual_file_sha:
            errors.append(f"FAIL_BRIDGE_FILE_DIGEST:{path.name}")
        if row.get("replay_projection_sha256") != receipt.get("replay_projection_sha256"):
            errors.append(f"FAIL_BRIDGE_PROJECTION_DIGEST:{path.name}")
        if receipt.get("receipt_sha256") != digest_without(receipt, "receipt_sha256"):
            errors.append(f"FAIL_BRIDGE_RECEIPT_DIGEST:{path.name}")
        if receipt.get("status") != "PASS" or receipt.get("promotion_allowed") is not False:
            errors.append(f"FAIL_BRIDGE_RECEIPT_STATUS:{path.name}")
        child_errors, child_stale = _child_file_path_findings(
            receipt.get("bindings"), run_root=path.parent
        )
        errors.extend(child_errors)
        stale_reasons.extend(child_stale)
        for finding in _retained_path_findings(
            receipt, product_root=box_root, location=path.name
        ):
            finding_text = f"{finding['location']}:{finding['value']}"
            if finding.get("severity") == "STALE":
                stale_reasons.append(
                    f"STALE_BRIDGE_RETAINED_PATH:{finding_text}"
                )
            else:
                errors.append(
                    "FAIL_BRIDGE_RETAINED_PATH_OUTSIDE_PRODUCT:"
                    f"{finding_text}"
                )

        children = receipt.get("children")
        if not isinstance(children, dict):
            errors.append(f"FAIL_BRIDGE_CHILDREN_MISSING:{path.name}")
        else:
            # A child return code is part of the authority boundary.  A
            # forged PASS body with a nonzero subprocess code is never a
            # retained PASS receipt.
            for child_name in BRIDGE_CHILD_NAMES:
                child = children.get(child_name)
                if not isinstance(child, dict):
                    errors.append(f"FAIL_BRIDGE_CHILD_MISSING:{path.name}:{child_name}")
                    continue
                if child.get("returncode") != 0:
                    errors.append(
                        f"FAIL_BRIDGE_CHILD_RETURNCODE:{path.name}:{child_name}"
                    )
        bindings = receipt.get("bindings")
        if not isinstance(bindings, dict):
            stale_reasons.append(f"STALE_BRIDGE_SOURCE_BINDINGS_MISSING:{path.name}")
        else:
            for name, current_sha in current_bindings.items():
                if current_sha is None:
                    stale_reasons.append(f"STALE_BRIDGE_CURRENT_SOURCE_MISSING:{name}")
                elif bindings.get(name) != current_sha:
                    stale_reasons.append(f"STALE_BRIDGE_SOURCE_BINDING:{path.name}:{name}")
    if len(receipts) >= 2:
        projections = [receipt.get("replay_projection") for receipt in receipts]
        if projections[0] != projections[1]:
            errors.append("FAIL_BRIDGE_SEMANTIC_REPLAY_MISMATCH")
    stale_reasons = list(dict.fromkeys(stale_reasons))
    status = "FAIL" if errors else ("STALE" if stale_reasons else "PASS")
    return {
        "status": status,
        "reason_codes": [*errors, *stale_reasons],
        "stale_path_count": len(
            [code for code in stale_reasons if "PATH" in code]
        ),
        "retained_run_count": len(receipts),
        "semantic_replay_identical": replay.get("semantic_replay_identical"),
        "replay_projection_sha256": [row.get("replay_projection_sha256") for row in rows],
        "current_source_bindings": current_bindings,
        "stale_reason_codes": stale_reasons,
        "promotion_allowed": False,
    }


def _missing_record(command_id: str, reason: str) -> dict[str, Any]:
    return {"id": command_id, "status": "HOLD", "reason_code": reason}


def command_statuses(records: Iterable[dict[str, Any]]) -> list[str]:
    return [str(record.get("status")) for record in records]


def add_command(
    records: list[dict[str, Any]],
    command_id: str,
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    record = run_command(
        command_id,
        argv,
        cwd=cwd,
        env=env,
        timeout_seconds=timeout_seconds,
    )
    records.append(record)
    return record


def run_zip_demo(
    *,
    light_python: Path,
    repo_root: Path,
    env: dict[str, str],
    timeout_seconds: float,
    records: list[dict[str, Any]],
    temp_root: Path,
) -> dict[str, Any]:
    packet = temp_root / "zip-demo.zip"
    returned_a = temp_root / "zip-demo.return-a.zip"
    returned_b = temp_root / "zip-demo.return-b.zip"
    cache = temp_root / "cache"
    module = [str(light_python), "-m", "constraintbox_zip_agent"]
    add_command(records, "zip_build_demo", [*module, "build-demo", "--out", str(packet)], cwd=repo_root, env=env, timeout_seconds=timeout_seconds)
    validate = add_command(records, "zip_validate_demo", [*module, "validate", str(packet)], cwd=repo_root, env=env, timeout_seconds=timeout_seconds)
    run_a = add_command(records, "zip_run_demo_a", [*module, "run", str(packet), "--return-zip", str(returned_a), "--cache-dir", str(cache)], cwd=repo_root, env=env, timeout_seconds=timeout_seconds)
    verify_a = add_command(records, "zip_verify_return_a", [*module, "verify-return", str(returned_a), "--input", str(packet)], cwd=repo_root, env=env, timeout_seconds=timeout_seconds)
    run_b = add_command(records, "zip_run_demo_b", [*module, "run", str(packet), "--return-zip", str(returned_b), "--cache-dir", str(cache)], cwd=repo_root, env=env, timeout_seconds=timeout_seconds)
    verify_b = add_command(records, "zip_verify_return_b", [*module, "verify-return", str(returned_b), "--input", str(packet)], cwd=repo_root, env=env, timeout_seconds=timeout_seconds)
    errors: list[str] = []
    if any(record.get("status") != "PASS" for record in (validate, run_a, verify_a, run_b, verify_b)):
        errors.append("FAIL_ZIP_DEMO_COMMAND")
    if not packet.is_file() or not returned_a.is_file() or not returned_b.is_file():
        errors.append("FAIL_ZIP_DEMO_OUTPUT_MISSING")
    else:
        digest_a = sha256_file(returned_a)
        digest_b = sha256_file(returned_b)
        if digest_a != digest_b:
            errors.append("FAIL_ZIP_DEMO_REPLAY_MISMATCH")
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "packet_sha256": sha256_file(packet) if packet.is_file() else None,
        "return_a_sha256": sha256_file(returned_a) if returned_a.is_file() else None,
        "return_b_sha256": sha256_file(returned_b) if returned_b.is_file() else None,
        "replay_identical": returned_a.is_file() and returned_b.is_file() and sha256_file(returned_a) == sha256_file(returned_b),
        "promotion_allowed": False,
    }


def run_structured_probe(
    *,
    box_root: Path,
    system_root: Path,
    light_python: Path,
    jax_python: Path | None,
    env: dict[str, str],
    timeout_seconds: float,
    records: list[dict[str, Any]],
    temp_root: Path,
) -> dict[str, Any]:
    fixture = system_root / "fixtures" / "structured_open_bind_v1.json"
    script = system_root / "scripts" / "structured_open_bind_probe.py"
    exact_path = temp_root / "structured-exact.json"
    exact = add_command(records, "structured_probe_exact", [str(light_python), str(script), "--input", str(fixture), "--output", str(exact_path), "--engine", "exact"], cwd=box_root, env=env, timeout_seconds=timeout_seconds)
    if jax_python is None:
        dual = _missing_record("structured_probe_dual", "HOLD_JAX_INTERPRETER_MISSING")
        records.append(dual)
        return {"status": "HOLD", "reason_codes": ["HOLD_JAX_INTERPRETER_MISSING"], "exact_command_status": exact.get("status"), "promotion_allowed": False}
    dual_path = temp_root / "structured-dual.json"
    dual = add_command(records, "structured_probe_dual", [str(jax_python), str(script), "--input", str(fixture), "--output", str(dual_path), "--engine", "dual"], cwd=box_root, env=env, timeout_seconds=timeout_seconds)
    errors: list[str] = []
    exact_body: dict[str, Any] | None = None
    dual_body: dict[str, Any] | None = None
    for label, path, command in (("exact", exact_path, exact), ("dual", dual_path, dual)):
        if command.get("status") != "PASS":
            errors.append(f"FAIL_STRUCTURED_COMMAND:{label}")
        try:
            body = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"FAIL_STRUCTURED_OUTPUT:{label}:{type(exc).__name__}")
            continue
        if body.get("status") != "PASS":
            errors.append(f"FAIL_STRUCTURED_RESULT:{label}")
        if label == "exact":
            exact_body = body
        else:
            dual_body = body
    projection_sha = None
    if exact_body is not None and dual_body is not None:
        left = structured_projection(exact_body)
        right = structured_projection(dual_body)
        if left != right:
            errors.append("FAIL_STRUCTURED_LIVE_PROJECTION_MISMATCH")
        projection_sha = sha256_bytes(canonical_json_bytes(left))
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "exact_output_sha256": sha256_file(exact_path) if exact_path.is_file() else None,
        "dual_output_sha256": sha256_file(dual_path) if dual_path.is_file() else None,
        "live_semantic_projection_sha256": projection_sha,
        "promotion_allowed": False,
    }


def run_bridge_pair(
    *,
    box_root: Path,
    system_root: Path,
    light_python: Path,
    jax_python: Path | None,
    env: dict[str, str],
    timeout_seconds: float,
    records: list[dict[str, Any]],
    temp_root: Path,
) -> dict[str, Any]:
    if jax_python is None:
        record = _missing_record("light_jax_wave_bridge", "HOLD_JAX_INTERPRETER_MISSING")
        records.append(record)
        return {"status": "HOLD", "reason_codes": [record["reason_code"]], "promotion_allowed": False}
    script = system_root / "scripts" / "run_light_jax_wave_bridge.py"
    skills = system_root / "skills"
    mmms = system_root / "mmms" / "primary"
    receipts: list[dict[str, Any]] = []
    for index in (1, 2):
        output_dir = temp_root / f"bridge-{index}"
        command = add_command(
            records,
            f"light_jax_wave_bridge_{index}",
            [
                str(light_python),
                str(script),
                "--box-root",
                str(box_root),
                "--light-python",
                str(light_python),
                "--jax-python",
                str(jax_python),
                "--skills-root",
                str(skills),
                "--mmm-root",
                str(mmms),
                "--output-dir",
                str(output_dir),
            ],
            cwd=box_root,
            env=env,
            timeout_seconds=max(timeout_seconds, 360.0),
        )
        receipt_path = output_dir / "bridge_receipt.json"
        if command.get("status") != "PASS":
            continue
        try:
            receipt = read_json(receipt_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        receipts.append(receipt)
    errors: list[str] = []
    if len(receipts) != 2:
        errors.append("FAIL_LIVE_BRIDGE_RECEIPT_COUNT")
    for index, receipt in enumerate(receipts, start=1):
        if receipt.get("status") != "PASS":
            errors.append(f"FAIL_LIVE_BRIDGE_STATUS:{index}")
        if receipt.get("receipt_sha256") != digest_without(receipt, "receipt_sha256"):
            errors.append(f"FAIL_LIVE_BRIDGE_DIGEST:{index}")
    if len(receipts) == 2:
        if receipts[0].get("replay_projection") != receipts[1].get("replay_projection"):
            errors.append("FAIL_LIVE_BRIDGE_REPLAY_MISMATCH")
        if receipts[0].get("replay_projection_sha256") != receipts[1].get("replay_projection_sha256"):
            errors.append("FAIL_LIVE_BRIDGE_REPLAY_DIGEST_MISMATCH")
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason_codes": errors,
        "live_replay_projection_sha256": [row.get("replay_projection_sha256") for row in receipts],
        "promotion_allowed": False,
    }


@contextmanager
def _bridge_output_directory(*, box_root: Path, system_root: Path):
    """Yield a product-confined bridge staging directory and always clean it."""

    verification_runs = system_root / "runs"
    created_runs = False
    if verification_runs.exists():
        if verification_runs.is_symlink() or not verification_runs.is_dir():
            raise ValueError(
                f"REFUSE_BRIDGE_RUNS_ROOT_NOT_REGULAR:{verification_runs}"
            )
    else:
        verification_runs.mkdir(parents=True, exist_ok=False)
        created_runs = True
    try:
        product_root = box_root.expanduser().resolve(strict=True)
        runs_root = verification_runs.resolve(strict=True)
        runs_root.relative_to(product_root)
        with tempfile.TemporaryDirectory(
            prefix=".verify-", dir=verification_runs
        ) as bridge_name:
            yield Path(bridge_name)
    finally:
        if created_runs:
            try:
                verification_runs.rmdir()
            except OSError:
                pass


def run_contained_overlay(
    *,
    box_root: Path,
    light_python: Path,
    env: dict[str, str],
    timeout_seconds: float,
    records: list[dict[str, Any]],
    supplied_root: Path | None,
) -> dict[str, Any]:
    candidates = [
        supplied_root,
        box_root / "contained_light",
        box_root / "integrated_system" / "contained_light",
        box_root / "scripts" / "contained_light" / "light",
    ]
    root: Path | None = None
    for candidate in candidates:
        if candidate is None:
            continue
        candidate = candidate.expanduser().absolute()
        if (candidate / "scripts" / "verify.sh").is_file():
            root = candidate
            break
    if root is None:
        return {
            "status": "NOT_APPLICABLE",
            "reason_codes": ["OPTIONAL_LEGACY_OVERLAY_NOT_PRESENT"],
            "detail": "the integrated package verifies canonical Light directly",
            "promotion_allowed": False,
        }
    overlay_env = dict(env)
    overlay_env["CB_PYTHON"] = str(light_python)
    record = add_command(records, "contained_light_overlay", ["sh", str(root / "scripts" / "verify.sh")], cwd=root, env=overlay_env, timeout_seconds=max(timeout_seconds, 360.0))
    return {"status": record.get("status"), "reason_codes": [] if record.get("status") == "PASS" else ["FAIL_CONTAINED_OVERLAY_VERIFY"], "root": str(root), "promotion_allowed": False}


def test_groups(*, include_provider_adapters: bool = False) -> dict[str, list[str]]:
    groups = {
        # Keep the self-verifying integrated-system suite first.  Later groups
        # may import source modules and create bytecode caches; this group
        # must inspect the clean extracted envelope before that can happen.
        "integrated_system": ["constraint_box/integrated_system/tests"],
        "light_core": [
            "constraint_box/tests/test_cb_light_system.py",
            "constraint_box/tests/test_cb_light_core_probes.py",
            "constraint_box/tests/test_cb_light_runtime_spine.py",
            "constraint_box/tests/test_cb_light_heavy_separation.py",
        ],
        "finite_kernel": [
            "constraint_box/tests/test_bound_quotient.py",
            "constraint_box/tests/test_contained_light.py",
            "constraint_box/tests/test_distinguishability.py",
            "constraint_box/tests/test_entropic_time_field.py",
        ],
        "hooks": [
            "constraint_box/tests/test_hook_adapter.py",
            "constraint_box/tests/test_hook_completion_resolution.py",
            "constraint_box/tests/test_hook_currentness_authority.py",
            "constraint_box/tests/test_hook_lifecycle.py",
        ],
        "zip_agent": ["constraint_box/zip_agent/tests"],
        "curated_skills": [
            "constraint_box/integrated_system/skills",
            "--ignore=constraint_box/integrated_system/skills/cb-wave-author/tests/test_wave_definitions.py",
            "--ignore=constraint_box/integrated_system/skills/cb-wave-admission-gate/tests/test_admit.py",
        ],
    }
    if include_provider_adapters:
        groups["provider_adapters"] = list(PROVIDER_TEST_PATHS)
    return groups


def run_test_groups(
    *,
    light_python: Path,
    repo_root: Path,
    env: dict[str, str],
    timeout_seconds: float,
    records: list[dict[str, Any]],
    include_provider_adapters: bool = False,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    box_root = Path(env["CB_BOX_ROOT"])
    system_root = box_root / "integrated_system"
    merged_controller = system_root / "runtime" / "controller_src"
    merged_zip = system_root / "runtime" / "zip_agent_src"
    light_source = box_root / "light_runtime" / "src"
    root_source = box_root / "src"
    zip_source = box_root / "zip_agent" / "src"

    def group_env(name: str) -> dict[str, str]:
        selected = dict(env)
        if name == "light_core":
            # ``-I`` below intentionally verifies the installed contained
            # Light wheel. Do not let a source overlay mask stale installation.
            selected.pop("PYTHONPATH", None)
            selected["CB_CONTROLLER_SRC"] = str(
                light_source if light_source.is_dir() else merged_controller
            )
        elif name in {"finite_kernel", "hooks", "provider_adapters"}:
            controller = (
                merged_controller if merged_controller.is_dir() else root_source
            )
            selected["PYTHONPATH"] = str(controller)
            selected["CB_CONTROLLER_SRC"] = str(controller)
        elif name == "zip_agent":
            # The ZIP core and model-free operations must import standalone.
            # Provider tests create their own declared controller fixtures.
            standalone = merged_zip if merged_zip.is_dir() else zip_source
            selected["PYTHONPATH"] = str(standalone)
            selected.pop("CB_CONTROLLER_SRC", None)
        return selected

    for name, paths in test_groups(
        include_provider_adapters=include_provider_adapters
    ).items():
        missing = [path for path in paths if not path.startswith("--") and not (repo_root / path).exists()]
        if missing:
            record = _missing_record(f"pytest_{name}", f"FAIL_TEST_PATH_MISSING:{','.join(missing)}")
            record["status"] = "FAIL"
            records.append(record)
            results[name] = {"status": "FAIL", "reason_codes": record["reason_code"], "missing": missing}
            continue
        # ``-B`` prevents test imports from creating source ``__pycache__``
        # entries; ``-I`` keeps the installed Light wheel isolated from the
        # checkout.  Both are required because the post-command envelope
        # check treats any unlisted source cache as a real payload mutation.
        isolation = ["-B", "-I"] if name == "light_core" else []
        argv = [str(light_python), *isolation, "-m", "pytest", "-q", "-p", "no:cacheprovider", *[path for path in paths if not path.startswith("--")]]
        argv.extend(path for path in paths if path.startswith("--"))
        record = add_command(
            records,
            f"pytest_{name}",
            argv,
            cwd=repo_root,
            env=group_env(name),
            timeout_seconds=timeout_seconds,
        )
        results[name] = {
            "status": record.get("status"),
            "reason_codes": [] if record.get("status") == "PASS" else [f"FAIL_TEST_GROUP:{name}"],
            "pytest_summary": record.get("pytest_summary", {}),
        }
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verify_integrated_system")
    parser.add_argument("--box-root", required=True, type=Path)
    parser.add_argument("--light-python", type=Path)
    parser.add_argument("--jax-python", type=Path)
    parser.add_argument("--contained-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--require-jax", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument(
        "--include-provider-adapters",
        action="store_true",
        help="opt in to fixture-only provider adapter unit tests; never launches a provider",
    )
    parser.add_argument(
        "--include-retained-evidence",
        action="store_true",
        help="audit historical local run receipts; excluded from the release ZIP and default verdict",
    )
    return parser


def verify(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    include_provider_adapters = bool(getattr(args, "include_provider_adapters", False))
    include_retained_evidence = bool(
        getattr(args, "include_retained_evidence", False)
    )
    box_root = args.box_root.expanduser().absolute()
    system_root = box_root / "integrated_system"
    repo_root = box_root.parent
    light = find_interpreter(str(args.light_python) if args.light_python else os.environ.get("CB_LIGHT_PYTHON"), box_root / ".venv" / "bin" / "python")
    generic_jax_root = Path(
        os.environ.get(
            "CB_JAX_QIT_ROOT",
            str(Path.home() / ".local" / "share" / "jax-qit-stack"),
        )
    )
    jax = find_interpreter(
        str(args.jax_python) if args.jax_python else os.environ.get("CB_JAX_PYTHON"),
        generic_jax_root / "bin" / "python",
    )
    env = make_env(box_root, light or Path(args.light_python or box_root / ".venv/bin/python"), jax)
    records: list[dict[str, Any]] = []
    light_jax_separation_checked = False
    retained_not_requested = {
        "status": "NOT_APPLICABLE",
        "reason_codes": ["RETAINED_EVIDENCE_NOT_REQUESTED"],
        "detail": "generated local runs are excluded from the release payload",
        "promotion_allowed": False,
    }
    checks: dict[str, Any] = {
        "context": check_context(system_root),
        "jax_profile": check_jax_profile(system_root),
        "skill_estate": check_skill_estate(system_root),
        "retained_artifacts": (
            check_retained_artifacts(system_root)
            if include_retained_evidence
            else dict(retained_not_requested)
        ),
        "structured_retained": (
            check_structured_receipt(system_root)
            if include_retained_evidence
            else dict(retained_not_requested)
        ),
        "bridge_retained": (
            check_bridge_receipt(system_root)
            if include_retained_evidence
            else dict(retained_not_requested)
        ),
        "bundle_envelope": check_bundle_envelope(box_root),
    }
    if light is None:
        records.append(_missing_record("light_interpreter", "HOLD_LIGHT_INTERPRETER_MISSING"))
        checks["live_operations"] = {"status": "HOLD", "reason_codes": ["HOLD_LIGHT_INTERPRETER_MISSING"]}
        test_results: dict[str, Any] = {}
    else:
        launcher = system_root / "bin" / "cb"
        doctor_argv = [str(light), str(launcher), "--light-python", str(light)]
        if jax is not None:
            doctor_argv.extend(["--jax-python", str(jax)])
        doctor = add_command(records, "doctor", [*doctor_argv, "doctor"], cwd=box_root, env=env, timeout_seconds=args.timeout_seconds)
        if jax is None and doctor.get("status") == "FAIL" and "JAX" in str(doctor.get("stdout_tail", "")) + str(doctor.get("stderr_tail", "")):
            doctor["status"] = "HOLD"
            doctor["reason_code"] = "HOLD_JAX_INTERPRETER_MISSING"
        seed_output = tempfile.NamedTemporaryFile(prefix="cb-seed-", suffix=".json", delete=False)
        seed_output.close()
        seed = add_command(records, "light_seed", [str(light), str(launcher), "--light-python", str(light), "light-seed", "--out", seed_output.name], cwd=box_root, env=env, timeout_seconds=args.timeout_seconds)
        checks["seed_command"] = {"status": seed.get("status"), "output_sha256": sha256_file(Path(seed_output.name)) if Path(seed_output.name).is_file() else None}
        try:
            Path(seed_output.name).unlink()
        except OSError:
            pass
        # Bridge children emit path-bearing receipts, but a documented direct
        # verifier invocation must not retain generated observations.  ZIP and
        # structured probes stay external; bridge outputs must be product-
        # confined because the bridge itself enforces that boundary.  The
        # ignored runs subtree is cleaned completely after the bridge pair.
        with tempfile.TemporaryDirectory(prefix="cb-integrated-verify-") as temp_name:
            temp_root = Path(temp_name)
            checks["zip_demo"] = run_zip_demo(light_python=light, repo_root=repo_root, env=env, timeout_seconds=args.timeout_seconds, records=records, temp_root=temp_root / "zip")
            checks["structured_live"] = run_structured_probe(box_root=box_root, system_root=system_root, light_python=light, jax_python=jax, env=env, timeout_seconds=args.timeout_seconds, records=records, temp_root=temp_root / "structured")
            with _bridge_output_directory(
                box_root=box_root, system_root=system_root
            ) as bridge_root:
                checks["bridge_live"] = run_bridge_pair(
                    box_root=box_root,
                    system_root=system_root,
                    light_python=light,
                    jax_python=jax,
                    env=env,
                    timeout_seconds=args.timeout_seconds,
                    records=records,
                    temp_root=bridge_root,
                )
            checks["contained_overlay"] = run_contained_overlay(box_root=box_root, light_python=light, env=env, timeout_seconds=args.timeout_seconds, records=records, supplied_root=args.contained_root)
        test_results = (
            {}
            if args.skip_tests
            else run_test_groups(
                light_python=light,
                repo_root=repo_root,
                env=env,
                timeout_seconds=args.timeout_seconds,
                records=records,
                include_provider_adapters=include_provider_adapters,
            )
        )
        checks["tests"] = {"status": "PASS" if all(row.get("status") == "PASS" for row in test_results.values()) else "FAIL", "groups": test_results, "skipped": args.skip_tests}
        if args.skip_tests:
            checks["tests"]["status"] = "HOLD"
            checks["tests"]["reason_codes"] = ["HOLD_TESTS_SKIPPED"]
        git = shutil.which("git")
        if git is not None and (repo_root / ".git").exists():
            checks["git_diff_check"] = add_command(records, "git_diff_check", [git, "diff", "--check", "--"], cwd=repo_root, env=env, timeout_seconds=args.timeout_seconds)
        else:
            checks["git_diff_check"] = {
                "status": "NOT_APPLICABLE",
                "reason_codes": ["NOT_A_GIT_CHECKOUT"],
            }
        live_operation_checks = {
            "doctor": doctor.get("status"),
            "seed": seed.get("status"),
            "zip_demo": checks["zip_demo"].get("status"),
            "structured_live": checks["structured_live"].get("status"),
            "bridge_live": checks["bridge_live"].get("status"),
        }
        if any(value == "FAIL" for value in live_operation_checks.values()):
            live_status = "FAIL"
        elif any(value != "PASS" for value in live_operation_checks.values()):
            live_status = "HOLD"
        else:
            live_status = "PASS"
        live_reason_codes = [
            f"{live_status}_LIVE_OPERATIONS_{name.upper()}"
            for name, value in live_operation_checks.items()
            if value != "PASS"
        ]
        checks["live_operations"] = {
            "status": live_status,
            "reason_codes": live_reason_codes,
            "checked": live_operation_checks,
            "jax_available": jax is not None,
        }
        light_jax_separation_checked = jax is not None and doctor.get("status") == "PASS"
    # Commands and test imports are allowed to create only the exact generated
    # product roots accepted by ``check_bundle_envelope``.  Recheck after the
    # final command so a clean precheck cannot hide a post-bootstrap cache or
    # extra physical file introduced during verification.
    checks["generated_bytecode_cleanup"] = cleanup_generated_bytecode(
        box_root, checks["bundle_envelope"]
    )
    checks["bundle_envelope_post"] = check_bundle_envelope(box_root)
    statuses: list[str] = []
    for check in checks.values():
        if isinstance(check, dict) and "status" in check:
            statuses.append(str(check["status"]))
        if isinstance(check, dict) and isinstance(check.get("groups"), dict):
            statuses.extend(str(row.get("status")) for row in check["groups"].values())
    statuses.extend(command_statuses(records))
    failures = [status for status in statuses if status == "FAIL"]
    holds = [status for status in statuses if status in {"HOLD", "SKIP", "STALE"}]
    if failures:
        status = "FAIL"
    elif holds or (jax is None and not args.require_jax):
        status = "HOLD"
    else:
        status = "PASS"
    if args.require_jax and jax is None:
        status = "FAIL"
        checks.setdefault("live_operations", {}).setdefault("reason_codes", []).append("FAIL_JAX_INTERPRETER_REQUIRED")
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "status": status,
        "started_at": started_at,
        "completed_at": utc_now(),
        "box_root": str(box_root),
        "system_root": str(system_root),
        "repo_root": str(repo_root),
        "interpreters": {
            "light": str(light) if light else None,
            "jax": str(jax) if jax else None,
            "light_jax_separation_checked": light_jax_separation_checked,
        },
        "checks": checks,
        "commands": records,
        "command_count": len(records),
        "boundaries": {
            "models_launched": False,
            "providers_launched": False,
            "provider_adapter_tests_run": bool(
                include_provider_adapters and not args.skip_tests
            ),
            "retained_evidence_checked": include_retained_evidence,
            "light_contains_jax": False,
            "heavy_admitted": False,
            "wave_promotion": False,
            "receipt_verification_is_not_semantic_promotion": True,
        },
        "claim_ceiling": (
            "bounded local integrated-system verification: source hashes, selected tests, "
            "ZIP replay, exact/JAX observation agreement, wave receipts, and context custody; "
            "not portable installation, provider execution, Heavy admission, scientific truth, or promotion"
        ),
        "promotion_allowed": False,
    }
    report["receipt_sha256"] = digest_without(report, "receipt_sha256")
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = verify(args)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        report = {
            "schema": SCHEMA,
            "status": "FAIL",
            "reason_codes": ["FAIL_VERIFIER_EXCEPTION"],
            "detail": f"{type(exc).__name__}:{exc}",
            "promotion_allowed": False,
        }
        report["receipt_sha256"] = digest_without(report, "receipt_sha256")
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        destination = args.output.expanduser().absolute()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
