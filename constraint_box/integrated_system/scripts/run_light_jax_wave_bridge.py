#!/usr/bin/env python3
"""Run one bounded Light -> JAX observation -> wave -> Light settlement route."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "constraintbox.light-jax-wave-bridge.v1"

# Context is deliberately split into the compact, current projection and the
# repo-held full prompt/plan/progress JSONL.  The context runner already
# supports multiple ``--prompt-path`` arguments; keep these paths explicit so
# the bridge can bind and currentness-check the exact inputs it sends.
CONTEXT_CURRENT_REL = Path("integrated_system/context/current")
FULL_PROMPT_CORPUS_REL = Path(
    "integrated_system/context/full/prompt_plan_progress_corpus.jsonl"
)
CONTEXT_STRATEGY_RUNNER_REL = Path(
    "cb-context-strategy-wave/scripts/run_context_strategy.py"
)
CONTEXT_SNAPSHOT_REL = Path("context_snapshot")
CONTEXT_SNAPSHOT_SCHEMA = "constraintbox.light-jax-wave-context-snapshot.v1"
CONTEXT_SNAPSHOT_CLAIM = (
    "context inputs are immutable bytes captured before bridge children; "
    "the bridge does not claim that live source remained current after capture"
)
CONTEXT_FILE_SUFFIXES = frozenset({".md", ".txt", ".json", ".jsonl"})

# Children produced by run_json().  Each must retain its subprocess return
# code so a nonzero exit cannot be masked by a PASS-like JSON body.
RUN_JSON_CHILD_NAMES = (
    "seed",
    "etf_exact",
    "etf_dual",
    "maintenance",
    "context",
    "exploration",
    "dualsolve",
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_tree(path: Path) -> str:
    """Hash a contained file tree without cache/bytecode noise."""

    if path.is_file():
        return sha256_path(path)
    digest = hashlib.sha256()
    files = [
        item
        for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.relative_to(path).parts
        and ".pytest_cache" not in item.relative_to(path).parts
        and item.suffix not in {".pyc", ".pyo"}
    ]
    for item in sorted(files, key=lambda value: value.relative_to(path).as_posix()):
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(sha256_path(item).encode("ascii"))
    return digest.hexdigest()


def declared_interpreter(path: Path) -> Path:
    """Validate without resolving a venv/symlink into its base interpreter."""
    declared = path.expanduser().absolute()
    if not declared.is_file() or not os.access(declared, os.X_OK):
        raise ValueError(f"interpreter is not executable: {declared}")
    return declared


def confined_output_dir(box_root: Path, output_dir: Path) -> Path:
    """Require bridge artifacts to remain below the selected product root."""

    product = box_root.expanduser().resolve(strict=True)
    candidate = output_dir.expanduser().resolve(strict=False)
    try:
        candidate.relative_to(product)
    except ValueError as exc:
        raise ValueError("REFUSE_BRIDGE_OUTPUT_OUTSIDE_PRODUCT") from exc
    return candidate


def confined_input_path(
    box_root: Path,
    input_path: Path,
    *,
    label: str,
    kind: str = "file",
) -> Path:
    """Resolve one bridge input and reject missing or escaping paths.

    ``Path.resolve`` is intentional here: an in-product symlink to an
    external file is just as unsafe as an explicit ``..`` escape.  The bridge
    only sends inputs to the context runner after this check succeeds.
    """

    product = box_root.expanduser().resolve(strict=True)
    raw = input_path.expanduser()
    candidate = raw if raw.is_absolute() else product / raw
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(product)
    except ValueError as exc:
        raise ValueError(f"REFUSE_BRIDGE_{label}_OUTSIDE_PRODUCT") from exc
    if kind == "file" and not resolved.is_file():
        raise ValueError(f"REFUSE_BRIDGE_{label}_MISSING")
    if kind == "directory" and not resolved.is_dir():
        raise ValueError(f"REFUSE_BRIDGE_{label}_MISSING")
    if kind not in {"file", "directory"}:
        raise ValueError(f"REFUSE_BRIDGE_{label}_KIND")
    return resolved


def _assert_tree_links_confined(path: Path, product: Path, *, label: str) -> None:
    """Reject an input directory containing a symlink to bytes outside product."""

    for item in path.rglob("*"):
        if not item.is_symlink():
            continue
        resolved = item.resolve(strict=False)
        try:
            resolved.relative_to(product)
        except ValueError as exc:
            raise ValueError(f"REFUSE_BRIDGE_{label}_OUTSIDE_PRODUCT") from exc


def _assert_tree_entries_regular(path: Path, *, label: str) -> None:
    """Reject symlink/nonregular entries before hashing a live context tree."""

    for item in path.rglob("*"):
        try:
            mode = item.lstat().st_mode
        except OSError as exc:
            raise ValueError(f"REFUSE_BRIDGE_{label}_MISSING") from exc
        if stat.S_ISLNK(mode):
            raise ValueError(f"REFUSE_BRIDGE_{label}_SYMLINK")
        if not stat.S_ISDIR(mode) and not stat.S_ISREG(mode):
            raise ValueError(f"REFUSE_BRIDGE_{label}_NONREGULAR")


def _assert_direct_input_regular(path: Path, *, label: str) -> None:
    """Reject symlink/nonregular direct context inputs before resolution."""

    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"REFUSE_BRIDGE_{label}_MISSING") from exc
    if stat.S_ISLNK(mode):
        raise ValueError(f"REFUSE_BRIDGE_{label}_SYMLINK")
    if not stat.S_ISREG(mode):
        raise ValueError(f"REFUSE_BRIDGE_{label}_NONREGULAR")


def context_input_paths(
    box_root: Path,
    skills_root: Path | None = None,
) -> dict[str, Path]:
    """Return the exact contained context files/directories used by the bridge."""

    box_root = box_root.expanduser().resolve(strict=True)
    selected_skills = skills_root or (box_root / "integrated_system" / "skills")
    if not selected_skills.is_absolute():
        selected_skills = box_root / selected_skills
    _assert_direct_input_regular(
        box_root / FULL_PROMPT_CORPUS_REL, label="FULL_PROMPT_CORPUS"
    )
    _assert_direct_input_regular(
        selected_skills / CONTEXT_STRATEGY_RUNNER_REL,
        label="CONTEXT_STRATEGY_RUNNER",
    )
    paths = {
        "current": confined_input_path(
            box_root,
            box_root / CONTEXT_CURRENT_REL,
            label="CONTEXT_CURRENT",
            kind="directory",
        ),
        "full_prompt_corpus": confined_input_path(
            box_root,
            box_root / FULL_PROMPT_CORPUS_REL,
            label="FULL_PROMPT_CORPUS",
            kind="file",
        ),
        "context_strategy_runner": confined_input_path(
            box_root,
            selected_skills / CONTEXT_STRATEGY_RUNNER_REL,
            label="CONTEXT_STRATEGY_RUNNER",
            kind="file",
        ),
    }
    _assert_tree_links_confined(
        paths["current"], box_root, label="CONTEXT_CURRENT"
    )
    _assert_tree_entries_regular(paths["current"], label="CONTEXT_CURRENT")
    return paths


def context_input_bindings(
    box_root: Path,
    skills_root: Path | None = None,
) -> dict[str, str]:
    """Bind context input bytes and runner source for replay/currentness."""

    box_root = box_root.expanduser().resolve(strict=True)
    paths = context_input_paths(box_root, skills_root)
    return {
        "context_current_path": str(
            paths["current"].relative_to(box_root).as_posix()
        ),
        "context_current_sha256": sha256_tree(paths["current"]),
        "full_prompt_corpus_path": str(
            paths["full_prompt_corpus"].relative_to(box_root).as_posix()
        ),
        "full_prompt_corpus_sha256": sha256_path(paths["full_prompt_corpus"]),
        "context_strategy_runner_path": str(
            paths["context_strategy_runner"].relative_to(box_root).as_posix()
        ),
        "context_strategy_runner_sha256": sha256_path(
            paths["context_strategy_runner"]
        ),
    }


def _snapshot_source_path(
    path: Path,
    *,
    product: Path,
    label: str,
    kind: str = "file",
) -> Path:
    """Validate a snapshot source without accepting symlink substitution."""

    candidate = path.expanduser()
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(product)
    except ValueError as exc:
        raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_OUTSIDE_PRODUCT") from exc
    try:
        mode = candidate.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_MISSING") from exc
    if stat.S_ISLNK(mode):
        raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_SYMLINK")
    if kind == "directory" and not stat.S_ISDIR(mode):
        raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_NONREGULAR")
    if kind == "file" and not stat.S_ISREG(mode):
        raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_NONREGULAR")
    return candidate


def _read_snapshot_source(path: Path, *, product: Path, label: str) -> bytes:
    """Read one regular source file with a no-follow descriptor where available."""

    _snapshot_source_path(path, product=product, label=label, kind="file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_UNREADABLE") from exc
    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise ValueError(f"REFUSE_BRIDGE_SNAPSHOT_{label}_NONREGULAR")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            return stream.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _snapshot_current_files(current: Path, *, product: Path) -> list[Path]:
    """Enumerate context files while refusing symlink and nonregular entries."""

    _snapshot_source_path(
        current, product=product, label="CONTEXT_CURRENT", kind="directory"
    )
    files: list[Path] = []
    for item in sorted(current.rglob("*"), key=lambda value: value.as_posix()):
        try:
            mode = item.lstat().st_mode
        except OSError as exc:
            raise ValueError("REFUSE_BRIDGE_SNAPSHOT_CONTEXT_CURRENT_MISSING") from exc
        if stat.S_ISLNK(mode):
            raise ValueError("REFUSE_BRIDGE_SNAPSHOT_CONTEXT_CURRENT_SYMLINK")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("REFUSE_BRIDGE_SNAPSHOT_CONTEXT_CURRENT_NONREGULAR")
        if item.suffix.lower() in CONTEXT_FILE_SUFFIXES:
            files.append(item)
    return files


def _snapshot_tree_digest(entries: list[dict[str, Any]], prefix: str) -> str:
    """Match ``sha256_tree`` over captured entries, without rereading sources."""

    digest = hashlib.sha256()
    prefix_path = Path(prefix)
    selected = [
        entry
        for entry in entries
        if Path(str(entry["relative_path"])).is_relative_to(prefix_path)
    ]
    for entry in sorted(selected, key=lambda value: str(value["relative_path"])):
        relative = Path(str(entry["relative_path"])).relative_to(prefix_path)
        encoded = relative.as_posix().encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(str(entry["sha256"]).encode("ascii"))
    return digest.hexdigest()


def _write_snapshot_bytes(path: Path, raw: bytes) -> None:
    """Write bytes durably into a private staging tree."""

    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def create_context_snapshot(
    *,
    box_root: Path,
    skills_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Atomically capture all context-runner inputs before bridge children run."""

    product = box_root.expanduser().resolve(strict=True)
    skills_root = _snapshot_source_path(
        skills_root.expanduser(),
        product=product,
        label="SKILLS_ROOT",
        kind="directory",
    )
    output = confined_output_dir(product, output_dir)
    output.mkdir(parents=True, exist_ok=True)
    snapshot_path = output / CONTEXT_SNAPSHOT_REL
    if snapshot_path.exists() or snapshot_path.is_symlink():
        raise ValueError("REFUSE_BRIDGE_CONTEXT_SNAPSHOT_EXISTS")

    # Use raw paths for this preflight so an in-product symlink is refused,
    # rather than resolved and silently accepted by the older input helper.
    current_source = _snapshot_source_path(
        product / CONTEXT_CURRENT_REL,
        product=product,
        label="CONTEXT_CURRENT",
        kind="directory",
    )
    full_source = _snapshot_source_path(
        product / FULL_PROMPT_CORPUS_REL,
        product=product,
        label="FULL_PROMPT_CORPUS",
        kind="file",
    )
    runner_source = _snapshot_source_path(
        skills_root / CONTEXT_STRATEGY_RUNNER_REL,
        product=product,
        label="CONTEXT_STRATEGY_RUNNER",
        kind="file",
    )
    current_files = _snapshot_current_files(current_source, product=product)
    sources = [(path, "CONTEXT_CURRENT") for path in current_files]
    sources.extend(
        [
            (full_source, "FULL_PROMPT_CORPUS"),
            (runner_source, "CONTEXT_STRATEGY_RUNNER"),
        ]
    )

    staging = Path(tempfile.mkdtemp(prefix=".context-snapshot.", dir=str(output)))
    entries: list[dict[str, Any]] = []
    try:
        for source, label in sources:
            raw = _read_snapshot_source(source, product=product, label=label)
            relative = source.relative_to(product).as_posix()
            destination = staging / relative
            _write_snapshot_bytes(destination, raw)
            entries.append(
                {
                    "relative_path": relative,
                    "byte_length": len(raw),
                    "sha256": sha256_bytes(raw),
                }
            )
        entries.sort(key=lambda value: value["relative_path"])
        source_at_capture = {
            "context_current_sha256": _snapshot_tree_digest(
                entries, CONTEXT_CURRENT_REL.as_posix()
            ),
            "full_prompt_corpus_sha256": next(
                entry["sha256"]
                for entry in entries
                if entry["relative_path"] == FULL_PROMPT_CORPUS_REL.as_posix()
            ),
            "context_strategy_runner_sha256": next(
                entry["sha256"]
                for entry in entries
                if entry["relative_path"]
                == (skills_root / CONTEXT_STRATEGY_RUNNER_REL)
                .relative_to(product)
                .as_posix()
            ),
        }
        manifest_core = {
            "schema": CONTEXT_SNAPSHOT_SCHEMA,
            "files": entries,
            "source_at_capture": source_at_capture,
        }
        snapshot_digest = sha256_bytes(canonical_json_bytes(manifest_core))
        captured_at = datetime.now(timezone.utc).isoformat()
        manifest = {
            **manifest_core,
            "snapshot_digest": snapshot_digest,
            "captured_at": captured_at,
            "claim_ceiling": CONTEXT_SNAPSHOT_CLAIM,
        }
        manifest_bytes = canonical_json_bytes(manifest) + b"\n"
        manifest_path = staging / "manifest.json"
        _write_snapshot_bytes(manifest_path, manifest_bytes)
        os.replace(staging, snapshot_path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return {
        "path": CONTEXT_SNAPSHOT_REL.as_posix(),
        "root": snapshot_path,
        "runner_relative_path": runner_source.relative_to(product).as_posix(),
        "manifest_path": snapshot_path / "manifest.json",
        "manifest": manifest,
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "snapshot_digest": snapshot_digest,
        "source_at_capture": source_at_capture,
        "captured_at": captured_at,
        "claim_ceiling": CONTEXT_SNAPSHOT_CLAIM,
    }


def snapshot_source_currentness(
    snapshot: dict[str, Any],
    *,
    after: dict[str, str] | None,
    error: str | None = None,
) -> dict[str, Any]:
    """Report live drift against capture bytes without changing the snapshot."""

    before = dict(snapshot["source_at_capture"])
    keys = tuple(before)
    if after is None:
        return {
            "status": "STALE_AFTER_CAPTURE",
            "basis": "SNAPSHOT_AT_CAPTURE",
            "changed_keys": list(keys),
            "before": before,
            "after": None,
            "error": error or "source currentness unavailable",
        }
    changed = [key for key in keys if before.get(key) != after.get(key)]
    return {
        "status": "CURRENT" if not changed else "STALE_AFTER_CAPTURE",
        "basis": "SNAPSHOT_AT_CAPTURE",
        "changed_keys": changed,
        "before": before,
        "after": {key: after.get(key) for key in keys},
    }


def bind_snapshot_context_result(
    context: dict[str, Any],
    *,
    snapshot: dict[str, Any],
    source_currentness: dict[str, Any],
) -> dict[str, Any]:
    """Bind a context child to snapshot bytes and preserve later source drift."""

    bound = dict(context)
    manifest = snapshot["manifest"]
    expected_path = FULL_PROMPT_CORPUS_REL.as_posix()
    expected_sha = next(
        entry["sha256"]
        for entry in manifest["files"]
        if entry["relative_path"] == expected_path
    )
    reported = [
        row
        for row in bound.get("jsonl_index") or []
        if isinstance(row, dict) and row.get("path") == expected_path
    ]
    bound["context_snapshot_path"] = snapshot["path"]
    bound["context_input_root"] = snapshot["path"]
    bound["context_snapshot_manifest_sha256"] = snapshot["manifest_sha256"]
    bound["context_snapshot_digest"] = snapshot["snapshot_digest"]
    bound["context_snapshot_captured_at"] = snapshot["captured_at"]
    bound["snapshot_claim_ceiling"] = snapshot["claim_ceiling"]
    bound["source_at_capture"] = snapshot["source_at_capture"]
    bound["bridge_input_bindings"] = snapshot["source_at_capture"]
    bound["context_current_sha256"] = snapshot["source_at_capture"][
        "context_current_sha256"
    ]
    bound["context_strategy_runner_sha256"] = snapshot["source_at_capture"][
        "context_strategy_runner_sha256"
    ]
    bound["input_currentness"] = source_currentness
    bound["snapshot_valid"] = True
    bound["full_prompt_corpus_sha256"] = expected_sha
    if not reported:
        bound["snapshot_valid"] = False
        bound["status"] = "HOLD_CONTEXT_CORPUS_UNBOUND"
        bound["reason"] = "HOLD_CONTEXT_CORPUS_UNBOUND"
    elif reported[0].get("sha256") != expected_sha:
        bound["snapshot_valid"] = False
        bound["status"] = "HOLD_CONTEXT_CORPUS_STALE"
        bound["reason"] = "HOLD_CONTEXT_CORPUS_STALE"
    return bound


def context_input_currentness(
    before: dict[str, str],
    after: dict[str, str],
) -> dict[str, Any]:
    """Compare the bound context inputs before and after runner execution."""

    keys = (
        "context_current_sha256",
        "full_prompt_corpus_sha256",
        "context_strategy_runner_sha256",
    )
    changed = [key for key in keys if before.get(key) != after.get(key)]
    return {
        "status": "CURRENT" if not changed else "STALE",
        "checked_keys": list(keys),
        "changed_keys": changed,
        "before": {key: before.get(key) for key in keys},
        "after": {key: after.get(key) for key in keys},
    }


def bind_context_result(
    context: dict[str, Any],
    *,
    before: dict[str, str],
    after: dict[str, str],
) -> dict[str, Any]:
    """Attach input bindings and hold a result that omits or misbinds the corpus."""

    bound = dict(context)
    currentness = context_input_currentness(before, after)
    bound["bridge_input_bindings"] = {
        key: before[key]
        for key in (
            "context_current_sha256",
            "full_prompt_corpus_sha256",
            "context_strategy_runner_sha256",
        )
    }
    bound["context_current_sha256"] = before["context_current_sha256"]
    bound["full_prompt_corpus_sha256"] = before["full_prompt_corpus_sha256"]
    bound["context_strategy_runner_sha256"] = before[
        "context_strategy_runner_sha256"
    ]
    bound["input_currentness"] = currentness
    if currentness["status"] != "CURRENT":
        bound["status"] = "HOLD_CONTEXT_INPUT_STALE"
        bound["reason"] = "HOLD_CONTEXT_INPUT_STALE"
        return bound

    expected_path = before["full_prompt_corpus_path"]
    reported = [
        row
        for row in bound.get("jsonl_index") or []
        if isinstance(row, dict) and row.get("path") == expected_path
    ]
    if not reported:
        bound["status"] = "HOLD_CONTEXT_CORPUS_UNBOUND"
        bound["reason"] = "HOLD_CONTEXT_CORPUS_UNBOUND"
        return bound
    if reported[0].get("sha256") != before["full_prompt_corpus_sha256"]:
        bound["status"] = "HOLD_CONTEXT_CORPUS_STALE"
        bound["reason"] = "HOLD_CONTEXT_CORPUS_STALE"
    return bound


def context_runner_command(
    *,
    light_python: Path,
    context_runner: Path,
    box_root: Path,
    output_dir: Path,
    context_path: Path,
) -> list[str]:
    """Build the context runner invocation with both prompt corpora bound."""

    return [
        str(light_python),
        "-I",
        str(context_runner),
        "--root",
        str(box_root),
        "--prompt-path",
        str(CONTEXT_CURRENT_REL),
        "--prompt-path",
        str(FULL_PROMPT_CORPUS_REL),
        "--output-path",
        str(output_dir),
        "--out",
        str(context_path),
    ]


def selected_controller_overlay(
    box_root: Path, output_dir: Path
) -> Path:
    """Build a Light-first selected-controller overlay for source checkouts.

    Release bundles already carry ``runtime/controller_src``.  A checkout may
    still have only the lean Light tree, so this creates a bounded overlay in
    the run directory: Light is copied first and only the one root module
    required by the model-free distinguishability child is filled in.  This
    avoids putting the legacy root package ahead of Light on ``PYTHONPATH``.
    """

    merged = box_root / "integrated_system" / "runtime" / "controller_src"
    if merged.is_dir():
        return merged
    light = box_root / "light_runtime" / "src"
    root = box_root / "src"
    if not light.is_dir():
        return root
    overlay = output_dir / ".controller_src"
    if overlay.exists():
        return overlay
    shutil.copytree(light, overlay)
    selected = ("distinguishability.py",)
    target_package = overlay / "constraintbox"
    root_package = root / "constraintbox"
    for name in selected:
        source = root_package / name
        destination = target_package / name
        if source.is_file() and not destination.exists():
            shutil.copy2(source, destination)
    return overlay


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_json(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 180.0,
) -> tuple[int, dict[str, Any], str]:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    text = (completed.stdout or "").strip()
    try:
        value = json.loads(text)
        body = value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        body = {}
    return completed.returncode, body, (completed.stderr or "")[-1000:]


def runtime_probe(python: Path, modules: list[str]) -> dict[str, Any]:
    code = (
        "import importlib,json,pathlib,sys; rows={}; "
        "[(lambda n: rows.update({n:{'imported':True,'version':str(getattr(importlib.import_module(n),'__version__',None)),'origin':getattr(importlib.import_module(n),'__file__',None)}}))(n) for n in json.loads(sys.argv[1])]; "
        "print(json.dumps({'executable':sys.executable,'realpath':str(pathlib.Path(sys.executable).resolve()),'prefix':sys.prefix,'modules':rows},sort_keys=True))"
    )
    completed = subprocess.run(
        [str(python), "-I", "-c", code, json.dumps(modules)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return {
            "status": "HOLD_RUNTIME_PROBE",
            "returncode": completed.returncode,
            "stderr": (completed.stderr or "")[-1000:],
        }
    return {"status": "PROBED", **json.loads(completed.stdout)}


def light_jax_negative(light_python: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [str(light_python), "-I", "-c", "import jax"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return {
        "status": "PASS" if completed.returncode != 0 else "REFUSE_JAX_IN_LIGHT",
        "returncode": completed.returncode,
        "stderr_sha256": sha256_bytes((completed.stderr or "").encode("utf-8")),
    }


def settle(children: dict[str, dict[str, Any]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if children["light_jax_negative"].get("status") != "PASS":
        reasons.append("REFUSE_JAX_IN_LIGHT")
    if children["jax_runtime"].get("status") != "PROBED":
        reasons.append("HOLD_JAX_RUNTIME")
    if children["seed"].get("disposition") != "ADMIT":
        reasons.append("HOLD_LIGHT_SEED")
    for name in ("etf_exact", "etf_dual"):
        if children[name].get("status") != "PASS":
            reasons.append(f"HOLD_{name.upper()}")
    if children["maintenance"].get("status") != "READY":
        reasons.append("HOLD_MAINTENANCE")
    if children["context"].get("status") != "CONTEXT_SNAPSHOT_READY":
        reasons.append("HOLD_CONTEXT_WAVE")
    context_currentness = children["context"].get("input_currentness")
    if (
        isinstance(context_currentness, dict)
        and context_currentness.get("status") != "CURRENT"
    ):
        reasons.append("HOLD_CONTEXT_INPUT_CURRENTNESS")
    if children["exploration"].get("status") != "ANTICHAIN_OPEN":
        reasons.append("HOLD_EXPLORATION_WAVE")
    if children["dualsolve"].get("status") != "BOUNDED_SAT":
        reasons.append("HOLD_LIGHT_SETTLEMENT")
    for name in RUN_JSON_CHILD_NAMES:
        child = children.get(name)
        returncode = child.get("returncode") if isinstance(child, dict) else None
        if type(returncode) is not int or returncode != 0:
            reasons.append(f"HOLD_{name.upper()}_RETURNCODE")
    return ("PASS" if not reasons else "HOLD"), reasons


def replay_projection(
    children: dict[str, dict[str, Any]],
    *,
    target_sha256: str,
    source_bindings: dict[str, str],
) -> dict[str, Any]:
    seed = children["seed"]
    exact = children["etf_exact"]
    dual = children["etf_dual"]
    maintenance = children["maintenance"]
    context = children["context"]
    exploration = children["exploration"]
    settlement = children["dualsolve"]
    return {
        "light_jax_negative": children["light_jax_negative"].get("status"),
        "jax_runtime": {
            "status": children["jax_runtime"].get("status"),
            "prefix": children["jax_runtime"].get("prefix"),
            "modules": {
                name: {
                    "imported": row.get("imported"),
                    "version": row.get("version"),
                }
                for name, row in sorted(
                    (children["jax_runtime"].get("modules") or {}).items()
                )
            },
        },
        "seed": {
            "disposition": seed.get("disposition"),
            "source_sha256": seed.get("source_sha256"),
            "support_counts": seed.get("support_counts"),
            "delta_K": seed.get("delta_K"),
        },
        "etf_exact": {
            "status": exact.get("status"),
            "result_sha256": exact.get("result_sha256"),
        },
        "etf_dual": {
            "status": dual.get("status"),
            "result_sha256": dual.get("result_sha256"),
            "jax_output_sha256": (dual.get("jax") or {}).get("output_sha256"),
        },
        "maintenance": {
            "status": maintenance.get("status"),
            "source_digest": maintenance.get("source_digest"),
            "context_digest": maintenance.get("context_digest"),
            "candidate_decisions": [
                {
                    "relative_path": row.get("relative_path"),
                    "classification": row.get("classification"),
                    "reason_code": row.get("reason_code"),
                }
                for row in maintenance.get("candidate_decisions") or []
            ],
        },
        "context": {
            "status": context.get("status"),
            "prompt_corpus_digest": context.get("prompt_corpus_digest"),
            "full_prompt_corpus_sha256": context.get(
                "full_prompt_corpus_sha256",
                source_bindings.get("full_prompt_corpus_sha256"),
            ),
            "context_strategy_runner_sha256": context.get(
                "context_strategy_runner_sha256",
                source_bindings.get("context_strategy_runner_sha256"),
            ),
            "context_snapshot_digest": context.get(
                "context_snapshot_digest",
                source_bindings.get("context_snapshot_digest"),
            ),
            "context_input_root": context.get("context_input_root"),
            "source_at_capture": context.get("source_at_capture"),
            "snapshot_valid": context.get("snapshot_valid"),
            "input_currentness": context.get("input_currentness"),
            "user_mmm_draft_digest": context.get("user_mmm_draft_digest"),
            # The project draft's source refs include this scratch output
            # directory.  Its raw digest is receipt custody, not replay
            # decision material, so keep it out of the path-independent
            # projection while retaining the full child receipt.
        },
        "exploration": {
            "status": exploration.get("status"),
            "seed_digest": exploration.get("seed_digest"),
            "reading_count": exploration.get("reading_count"),
            "family_count": exploration.get("family_count"),
            "antichain_digest": exploration.get("antichain_digest"),
            "distinguish_packet_digest": exploration.get(
                "distinguish_packet_digest"
            ),
        },
        "dualsolve": {
            "status": settlement.get("status"),
            "packet_sha256": settlement.get("packet_sha256"),
            "receipt_sha256": settlement.get("receipt_sha256"),
            "agree": (settlement.get("dual_solve") or {}).get("agree"),
        },
        "context_input_currentness": context.get("input_currentness"),
        "target_sha256": target_sha256,
        # The manifest file records capture time and therefore has a
        # per-run digest.  The canonical, content-only snapshot digest above
        # is the replay identity; retain the manifest digest in the receipt.
        "source_bindings": {
            key: value
            for key, value in source_bindings.items()
            if key != "context_snapshot_manifest_sha256"
        },
    }


def run_bridge(
    *,
    box_root: Path,
    light_python: Path,
    jax_python: Path,
    skills_root: Path,
    mmm_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    box_root = box_root.resolve(strict=True)
    light_python = declared_interpreter(light_python)
    jax_python = declared_interpreter(jax_python)
    skills_root = skills_root.resolve(strict=True)
    mmm_root = mmm_root.resolve(strict=True)
    output_dir = confined_output_dir(box_root, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    observations_dir = output_dir / "observations"
    observations_dir.mkdir(parents=True, exist_ok=True)
    fixture = box_root / "scripts/contained_light/fixtures/entropic_time_field_v1.json"
    field_source = box_root / "scripts/contained_light/entropic_time_field.py"
    seed_source = box_root / "scripts/contained_light/seed_check.py"
    campaign_source = box_root / "experiments/manifold_capability/v1/campaign.py"
    campaign_custody = box_root / "experiments/manifold_capability/v1/REPLAY_CUSTODY.json"

    # Capture context bytes before any Light/JAX/wave child can run or mutate
    # the live checkout.  All later context reads use this immutable tree.
    context_snapshot = create_context_snapshot(
        box_root=box_root,
        skills_root=skills_root,
        output_dir=output_dir,
    )
    controller_src = selected_controller_overlay(box_root, output_dir)
    python_roots = [str(controller_src), str(box_root / "zip_agent/src")]
    common_env = os.environ.copy()
    common_env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "CB_SKILLS_ROOT": str(skills_root),
            "CB_BOX_ROOT": str(box_root),
            "CB_LIGHT_PYTHON": str(light_python),
            "CB_MMM_ROOT": str(mmm_root),
            "PYTHONPATH": os.pathsep.join(python_roots),
        }
    )

    children: dict[str, dict[str, Any]] = {}
    children["light_jax_negative"] = light_jax_negative(light_python)
    children["jax_runtime"] = runtime_probe(
        jax_python, ["jax", "jaxlib", "sympy", "rustworkx", "z3", "cvc5"]
    )

    seed_path = output_dir / "seed_check.json"
    seed_rc, seed, seed_stderr = run_json(
        [str(light_python), str(seed_source), "--root", str(box_root), "--out", str(seed_path)],
        cwd=box_root,
        env=common_env,
    )
    children["seed"] = {**seed, "stderr": seed_stderr, "returncode": seed_rc}

    exact_path = observations_dir / "etf_exact.json"
    exact_rc, exact, exact_stderr = run_json(
        [
            str(light_python),
            str(field_source),
            "--input",
            str(fixture),
            "--output",
            str(exact_path),
            "--engine",
            "exact",
        ],
        cwd=box_root,
        env=common_env,
    )
    children["etf_exact"] = {**exact, "stderr": exact_stderr, "returncode": exact_rc}

    dual_path = observations_dir / "etf_dual.json"
    dual_rc, dual, dual_stderr = run_json(
        [
            str(jax_python),
            str(field_source),
            "--input",
            str(fixture),
            "--output",
            str(dual_path),
            "--engine",
            "dual",
        ],
        cwd=box_root,
        env=common_env,
        timeout=240,
    )
    children["etf_dual"] = {**dual, "stderr": dual_stderr, "returncode": dual_rc}

    target = {
        "schema": "constraintbox.light-jax-wave-target.v1",
        "operation": "finite_entropic_time_dual_engine_observation.v1",
        "light_seed_source_sha256": seed.get("source_sha256"),
        "light_seed_support_counts": seed.get("support_counts"),
        "light_seed_delta_K": seed.get("delta_K"),
        "etf_exact_sha256": sha256_path(exact_path) if exact_path.is_file() else None,
        "etf_dual_sha256": sha256_path(dual_path) if dual_path.is_file() else None,
        "campaign_source_sha256": sha256_path(campaign_source),
        "campaign_custody_sha256": sha256_path(campaign_custody),
        "questions": [
            "Does structured support-extension/probe-restriction preserve a non-generic order scar?",
            "Which probe family changes Q without inventing observations?",
            "Which two-hand controls should falsify the current fixture?",
        ],
        "claim_ceiling": (
            "bounded Light seed plus exact/JAX agreement and campaign custody inputs; "
            "not chirality, not manifold admission, not provider execution"
        ),
        "promotion_allowed": False,
    }
    target_path = observations_dir / "bridge_target.json"
    write_json(target_path, target)

    zip_source_path = "zip_agent/src"
    zip_package_path = "zip_agent"
    if not (box_root / zip_source_path).is_dir():
        zip_source_path = "integrated_system/runtime/zip_agent_src"
        zip_package_path = zip_source_path
    maintenance_path = output_dir / "maintenance.json"
    maintenance_rc, maintenance, _ = run_json(
        [
            str(light_python),
            "-I",
            str(skills_root / "cb-maintenance-wave/scripts/run_maintenance_wave.py"),
            "--root",
            str(box_root),
            "--package",
            zip_package_path,
            "--source-path",
            "integrated_system/scripts",
            "--source-path",
            "integrated_system/skills",
            "--source-path",
            "integrated_system/mmms/primary/mini",
            "--source-path",
            "light_runtime/src",
            "--source-path",
            zip_source_path,
            "--context-path",
            "integrated_system/context/current",
            "--candidate",
            "integrated_system",
            "--requested-action",
            "classify",
            "--run-id",
            "light-jax-wave-bridge",
            "--output",
            str(maintenance_path),
        ],
        cwd=box_root,
        env=common_env,
    )
    if maintenance_path.is_file():
        maintenance = json.loads(maintenance_path.read_text(encoding="utf-8"))
    children["maintenance"] = {**maintenance, "returncode": maintenance_rc}

    # The context child receives only the immutable snapshot tree.  In
    # particular, do not pass live ``context/current`` or full-corpus paths.
    snapshot_root = context_snapshot["root"]
    snapshot_runner = snapshot_root / context_snapshot["runner_relative_path"]
    context_path = output_dir / "context_strategy.json"
    context_rc, context, _ = run_json(
        context_runner_command(
            light_python=light_python,
            context_runner=snapshot_runner,
            box_root=snapshot_root,
            output_dir=observations_dir,
            context_path=context_path,
        ),
        cwd=box_root,
        env=common_env,
    )
    if context_path.is_file():
        context = json.loads(context_path.read_text(encoding="utf-8"))
    context = bind_snapshot_context_result(
        context,
        snapshot=context_snapshot,
        source_currentness=snapshot_source_currentness(
            context_snapshot, after=context_snapshot["source_at_capture"]
        ),
    )
    children["context"] = {**context, "returncode": context_rc}

    readings = {
        "readings": [
            {
                "id": "structured-map-family",
                "family": "structured_open_bind",
                "text": "Open extends support and bind restricts by named probes and constraints.",
            },
            {
                "id": "generic-order-scar",
                "family": "generic_noncommutation_control",
                "text": "The observed order gap may be generic endomap noncommutation.",
            },
            {
                "id": "two-functional-hands",
                "family": "two_hand_field_hypothesis",
                "text": "One gradient may admit two ordered functional readings without two clocks.",
            },
            {
                "id": "measurement-artifact",
                "family": "probe_artifact_control",
                "text": "A different finite probe family may erase the apparent scar.",
            },
        ]
    }
    readings_path = output_dir / "readings.json"
    write_json(readings_path, readings)
    exploration_path = output_dir / "exploration.json"
    exploration_rc, exploration, _ = run_json(
        [
            str(light_python),
            "-I",
            str(skills_root / "cb-exploration-wave/scripts/run_exploration.py"),
            "--root",
            str(box_root),
            "--seed",
            str(target_path),
            "--readings",
            str(readings_path),
            "--out",
            str(exploration_path),
        ],
        cwd=box_root,
        env=common_env,
    )
    if exploration_path.is_file():
        exploration = json.loads(exploration_path.read_text(encoding="utf-8"))
    children["exploration"] = {**exploration, "returncode": exploration_rc}

    packet_path = output_dir / "distinguish.packet.json"
    dualsolve_rc, dualsolve, dualsolve_stderr = run_json(
        [str(light_python), "-m", "constraintbox.distinguishability", str(packet_path)],
        cwd=box_root,
        env=common_env,
    )
    children["dualsolve"] = {**dualsolve, "stderr": dualsolve_stderr, "returncode": dualsolve_rc}

    # Compare live source only for a later-drift currentness finding.  The
    # child already consumed snapshot bytes, so this check cannot change its
    # input or output; it only prevents a live-current claim after capture.
    try:
        context_bindings_after = context_input_bindings(box_root, skills_root)
        context_currentness = snapshot_source_currentness(
            context_snapshot, after=context_bindings_after
        )
    except (OSError, ValueError) as exc:
        context_currentness = snapshot_source_currentness(
            context_snapshot, after=None, error=f"{type(exc).__name__}:{exc}"
        )
    context = bind_snapshot_context_result(
        children["context"],
        snapshot=context_snapshot,
        source_currentness=context_currentness,
    )
    children["context"] = context
    status, reasons = settle(children)
    child_files = [
        path
        for path in (
            seed_path,
            exact_path,
            dual_path,
            target_path,
            maintenance_path,
            context_path,
            exploration_path,
            packet_path,
            context_snapshot["manifest_path"],
        )
        if path.is_file()
    ]
    source_bindings = {
        "bridge_source_sha256": sha256_path(Path(__file__)),
        "field_source_sha256": sha256_path(field_source),
        "seed_source_sha256": sha256_path(seed_source),
        "fixture_sha256": sha256_path(fixture),
        "campaign_source_sha256": sha256_path(campaign_source),
        "campaign_custody_sha256": sha256_path(campaign_custody),
        "context_current_sha256": context_snapshot["source_at_capture"][
            "context_current_sha256"
        ],
        "full_prompt_corpus_sha256": context_snapshot["source_at_capture"][
            "full_prompt_corpus_sha256"
        ],
        "context_strategy_runner_sha256": context_snapshot["source_at_capture"][
            "context_strategy_runner_sha256"
        ],
        "context_snapshot_digest": context_snapshot["snapshot_digest"],
        "context_snapshot_manifest_sha256": context_snapshot["manifest_sha256"],
    }
    projection = replay_projection(
        children,
        target_sha256=sha256_path(target_path),
        source_bindings=source_bindings,
    )
    receipt = {
        "schema": SCHEMA,
        "status": status,
        "reason_codes": reasons,
        "operation": "light_jax_wave_bridge.v1",
        "children": children,
        "bindings": {
            **source_bindings,
            "context_input_paths": {
                "root": context_snapshot["path"],
                "current": (
                    CONTEXT_SNAPSHOT_REL / CONTEXT_CURRENT_REL
                ).as_posix(),
                "full_prompt_corpus": (
                    CONTEXT_SNAPSHOT_REL / FULL_PROMPT_CORPUS_REL
                ).as_posix(),
                "context_strategy_runner": (
                    CONTEXT_SNAPSHOT_REL
                    / Path(context_snapshot["runner_relative_path"])
                ).as_posix(),
            },
            "context_source_paths_at_capture": {
                "current": CONTEXT_CURRENT_REL.as_posix(),
                "full_prompt_corpus": FULL_PROMPT_CORPUS_REL.as_posix(),
                "context_strategy_runner": context_snapshot[
                    "runner_relative_path"
                ],
            },
            "context_snapshot_path": context_snapshot["path"],
            "context_snapshot_manifest_path": (
                CONTEXT_SNAPSHOT_REL / "manifest.json"
            ).as_posix(),
            "context_snapshot_captured_at": context_snapshot["captured_at"],
            "context_snapshot_claim_ceiling": context_snapshot["claim_ceiling"],
            "context_source_at_capture": context_snapshot["source_at_capture"],
            "context_input_currentness": context_currentness,
            "child_file_sha256": {
                str(path.relative_to(output_dir)): sha256_path(path)
                for path in child_files
            },
        },
        "boundaries": {
            "one_system": True,
            "interpreter_count": 2,
            "light_contains_jax": False,
            "jax_output_is_observation_only": True,
            "wave_can_promote": False,
            "dualsolve_invents_probes": False,
            "context_child_reads_snapshot_only": True,
            "context_snapshot_is_immutable": True,
            "live_context_currentness_checked_after_capture": True,
        },
        "next_operation": "structured_open_bind_family_probe.v1",
        "context_snapshot_path": context_snapshot["path"],
        "context_snapshot_digest": context_snapshot["snapshot_digest"],
        "context_snapshot_manifest_sha256": context_snapshot["manifest_sha256"],
        "context_snapshot_captured_at": context_snapshot["captured_at"],
        "context_snapshot_claim_ceiling": context_snapshot["claim_ceiling"],
        "context_source_at_capture": context_snapshot["source_at_capture"],
        "context_input_currentness": context_currentness,
        "replay_projection": projection,
        "replay_projection_sha256": sha256_bytes(canonical_json_bytes(projection)),
        "claim_ceiling": (
            "local Light/JAX boundary and two model-free wave children with Light "
            "finite settlement; context is historical-at-capture snapshot material; "
            "not provider execution, structured-map success, chirality, manifold "
            "admission, or promotion"
        ),
        "promotion_allowed": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    write_json(output_dir / "bridge_receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--box-root", required=True, type=Path)
    parser.add_argument("--light-python", required=True, type=Path)
    parser.add_argument("--jax-python", required=True, type=Path)
    parser.add_argument("--skills-root", required=True, type=Path)
    parser.add_argument("--mmm-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = run_bridge(
            box_root=args.box_root,
            light_python=args.light_python,
            jax_python=args.jax_python,
            skills_root=args.skills_root,
            mmm_root=args.mmm_root,
            output_dir=args.output_dir,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "status": "REFUSE",
                    "reason_codes": ["REFUSE_BRIDGE_EXECUTION"],
                    "detail": f"{type(exc).__name__}:{exc}",
                    "promotion_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "status": receipt["status"],
                "reason_codes": receipt["reason_codes"],
                "receipt_sha256": receipt["receipt_sha256"],
                "promotion_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
