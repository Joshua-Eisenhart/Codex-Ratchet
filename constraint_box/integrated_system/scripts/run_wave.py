#!/usr/bin/env python3
"""Truthful public surface for the contained, model-free wave cohort.

This module deliberately treats a ``wave.json`` as metadata, not as proof that
anything can run.  A public run is admitted only when the manifest names a
contained script and definition, their pinned digests still match, and all
declared host-independent inputs exist inside the extracted product.  The
three current direct runners are model-free; composite/spec-only waves remain
visible but inactive.

Commands emit JSON on stdout.  ``run`` writes a receipt in the requested
contained output directory and returns zero only when the child returned the
declared code and emitted the declared status.  A child HOLD/REFUSE is a
truthful nonzero result, never a PASS-like wrapper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA = "constraintbox.public-wave-run.v1"
MANIFEST_SCHEMA = "constraintbox.active-wave-set.v1"
_HOST_PATH = re.compile(r"(?:/Users/|/home/|~/(?:\.codex|\.agents)(?:/|$))")


class PathViolation(ValueError):
    """A manifest or invocation tried to leave the extracted product."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_digest(path: Path) -> str:
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


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise PathViolation(f"PATH_OUTSIDE_PRODUCT:{path}") from exc


def confined_path(value: str | os.PathLike[str], root: Path, *, label: str) -> Path:
    """Resolve a path and reject symlink/``..`` escapes from ``root``."""

    root_resolved = root.expanduser().resolve(strict=True)
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else root_resolved / raw
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathViolation(f"{label}_OUTSIDE_PRODUCT:{value}") from exc
    return resolved


def _read_manifest(system_root: Path) -> dict[str, Any]:
    path = confined_path("skills/ACTIVE_WAVES.json", system_root, label="MANIFEST")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"HOLD_MANIFEST_UNREADABLE:{type(exc).__name__}") from exc
    if not isinstance(data, dict) or data.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("HOLD_MANIFEST_SCHEMA")
    if not isinstance(data.get("runnable_cohort"), list):
        raise ValueError("HOLD_RUNNABLE_COHORT_MISSING")
    return data


def _cohort(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in manifest.get("runnable_cohort", []):
        if isinstance(item, dict) and isinstance(item.get("wave_id"), str):
            rows[item["wave_id"]] = dict(item)
    return rows


def _inactive_ids(manifest: Mapping[str, Any]) -> list[str]:
    rows: list[str] = []
    for key in ("authored_specs_not_active", "script_backed_without_wave_definition"):
        for value in manifest.get(key, []) or []:
            if isinstance(value, str) and value not in rows:
                rows.append(value.removesuffix("/wave.json"))
    for value in manifest.get("wave_definitions", []) or []:
        if isinstance(value, str):
            wave = value.split("/", 1)[0]
            if wave not in _cohort(manifest) and wave not in rows:
                rows.append(wave)
    return rows


def _host_path_findings(paths: Sequence[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in paths:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError) as exc:
            findings.append({"path": str(path), "reason": f"UNREADABLE:{type(exc).__name__}"})
            continue
        if _HOST_PATH.search(raw):
            findings.append({"path": str(path), "reason": "ABSOLUTE_HOST_PATH"})
    return findings


def _path_state(path: Path, root: Path) -> dict[str, Any]:
    state: dict[str, Any] = {
        "path": _relative(path, root),
        "exists": path.exists(),
        "kind": "missing",
    }
    if not path.exists():
        return state
    state["kind"] = "file" if path.is_file() else "directory" if path.is_dir() else "other"
    state["sha256"] = _tree_digest(path)
    return state


def inspect_wave(
    wave_id: str,
    *,
    system_root: Path | None = None,
) -> dict[str, Any]:
    """Inspect one manifest row without launching any process."""

    system = (system_root or Path(__file__).resolve().parents[1]).expanduser().resolve(strict=True)
    manifest_path = confined_path("skills/ACTIVE_WAVES.json", system, label="MANIFEST")
    manifest = _read_manifest(system)
    cohort = _cohort(manifest)
    if wave_id not in cohort:
        reason = "INACTIVE_SPEC_ONLY" if wave_id in _inactive_ids(manifest) else "UNKNOWN_WAVE"
        return {
            "schema": "constraintbox.public-wave-inspection.v1",
            "wave_id": wave_id,
            "runnable": False,
            "status": "INACTIVE" if reason == "INACTIVE_SPEC_ONLY" else "REFUSE",
            "reason_code": reason,
            "manifest": _relative(manifest_path, system),
            "promotion_allowed": False,
        }

    spec = cohort[wave_id]
    findings: list[dict[str, str]] = []
    paths: list[Path] = []
    input_states: list[dict[str, Any]] = []
    box = system.parent
    for key in ("script", "definition"):
        value = spec.get(key)
        if not isinstance(value, str):
            findings.append({"path": str(value), "reason": f"MISSING_{key.upper()}_DECLARATION"})
            continue
        try:
            path = confined_path(value, system, label=key.upper())
        except PathViolation as exc:
            findings.append({"path": value, "reason": str(exc)})
            continue
        paths.append(path)
        if not path.is_file():
            findings.append({"path": value, "reason": "MISSING_DEPENDENCY"})
            continue
        expected_key = f"{key}_sha256"
        expected = spec.get(expected_key)
        actual = sha256_path(path)
        if not isinstance(expected, str) or actual != expected:
            findings.append({"path": value, "reason": "SOURCE_TAMPERED"})
    for value in spec.get("required_files", []) or []:
        if not isinstance(value, str):
            findings.append({"path": str(value), "reason": "BAD_REQUIRED_FILE"})
            continue
        try:
            path = confined_path(value, system, label="DEPENDENCY")
        except PathViolation as exc:
            findings.append({"path": value, "reason": str(exc)})
            continue
        paths.append(path)
        if not path.is_file():
            findings.append({"path": value, "reason": "MISSING_DEPENDENCY"})
    for value in spec.get("input_paths", []) or []:
        if not isinstance(value, str):
            findings.append({"path": str(value), "reason": "BAD_INPUT_PATH"})
            continue
        try:
            path = confined_path(value, box, label="INPUT")
        except PathViolation as exc:
            findings.append({"path": value, "reason": str(exc)})
            continue
        input_states.append(_path_state(path, box))
        if not path.exists():
            findings.append({"path": value, "reason": "MISSING_DEPENDENCY"})
        # Input corpora are data, not executable/configuration dependencies.
        # They may preserve historical source references; those do not grant
        # the runner a host binding.  Only executable/config files above are
        # scanned for absolute host paths.
    findings.extend(_host_path_findings(paths))
    source = []
    for path in paths:
        source.append(_path_state(path, system))
    runnable = not findings
    return {
        "schema": "constraintbox.public-wave-inspection.v1",
        "wave_id": wave_id,
        "runnable": runnable,
        "status": "READY" if runnable else "HOLD",
        "reason_code": None if runnable else findings[0]["reason"],
        "findings": findings,
        "manifest": _relative(manifest_path, system),
        "script": spec.get("script"),
        "definition": spec.get("definition"),
        "source": source,
        "inputs": input_states,
        "expected_status": spec.get("expected_status"),
        "expected_returncode": spec.get("expected_returncode"),
        "claim_ceiling": spec.get("claim_ceiling"),
        "promotion_allowed": False,
    }


def list_waves(*, system_root: Path | None = None) -> dict[str, Any]:
    system = (system_root or Path(__file__).resolve().parents[1]).expanduser().resolve(strict=True)
    manifest = _read_manifest(system)
    rows = []
    for wave_id in sorted(_cohort(manifest)):
        rows.append(inspect_wave(wave_id, system_root=system))
    inactive = [
        {
            "wave_id": wave_id,
            "status": "INACTIVE",
            "runnable": False,
            "reason_code": "INACTIVE_SPEC_ONLY",
            "promotion_allowed": False,
        }
        for wave_id in sorted(_inactive_ids(manifest))
        if wave_id not in _cohort(manifest)
    ]
    return {
        "schema": "constraintbox.public-wave-list.v1",
        "runnable_cohort": rows,
        "inactive": inactive,
        "promotion_allowed": False,
    }


def _kill_process(process: subprocess.Popen[str], sig: int) -> None:
    try:
        if hasattr(os, "killpg") and process.pid:
            os.killpg(process.pid, sig)
        else:
            process.send_signal(sig)
    except (OSError, ProcessLookupError):
        pass


def _run_process(
    argv: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: float,
    cancel_file: Path | None,
) -> dict[str, Any]:
    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    cancelled = False
    timed_out = False
    while process.poll() is None:
        if cancel_file is not None and cancel_file.exists():
            cancelled = True
            _kill_process(process, signal.SIGTERM)
            break
        if time.monotonic() - started >= timeout_seconds:
            timed_out = True
            _kill_process(process, signal.SIGTERM)
            break
        time.sleep(0.02)
    try:
        stdout, stderr = process.communicate(timeout=1.0)
    except subprocess.TimeoutExpired:
        _kill_process(process, signal.SIGKILL)
        stdout, stderr = process.communicate()
    return {
        "returncode": process.returncode,
        "stdout": stdout or "",
        "stderr": stderr or "",
        "stdout_sha256": sha256_bytes((stdout or "").encode("utf-8")),
        "stderr_sha256": sha256_bytes((stderr or "").encode("utf-8")),
        "timed_out": timed_out,
        "cancelled": cancelled,
        "duration_ms": int((time.monotonic() - started) * 1000),
    }


def _child_args(wave_id: str, spec: Mapping[str, Any], *, box: Path, output: Path, run_id: str) -> list[str]:
    script = confined_path(str(spec["script"]), box / "integrated_system", label="SCRIPT")
    if wave_id == "cb-maintenance-wave":
        return [
            sys.executable,
            "-I",
            str(script),
            "--root",
            str(box),
            "--package",
            "zip_agent",
            "--source-path",
            "integrated_system/scripts",
            "--source-path",
            "integrated_system/skills",
            "--source-path",
            "integrated_system/mmms/primary/mini",
            "--source-path",
            "light_runtime/src",
            "--source-path",
            "zip_agent/src",
            "--context-path",
            "integrated_system/context/current",
            "--candidate",
            "integrated_system",
            "--requested-action",
            "classify",
            "--run-id",
            run_id,
            "--output",
            str(output),
        ]
    if wave_id == "cb-context-strategy-wave":
        return [
            sys.executable,
            "-I",
            str(script),
            "--root",
            str(box),
            "--prompt-path",
            "integrated_system/context/current",
            "--prompt-path",
            "integrated_system/context/full/prompt_plan_progress_corpus.jsonl",
            "--output-path",
            "integrated_system/state",
            "--output-path",
            "integrated_system/WHAT_IS_PROVEN.md",
            "--out",
            str(output),
        ]
    if wave_id == "cb-exploration-wave":
        return [
            sys.executable,
            "-I",
            str(script),
            "--root",
            str(box),
            "--seed",
            "integrated_system/fixtures/structured_open_bind_v1.json",
            "--out",
            str(output),
        ]
    raise ValueError(f"INACTIVE_WAVE:{wave_id}")


def run_wave(
    wave_id: str,
    *,
    system_root: Path | None = None,
    output_dir: Path | None = None,
    python_executable: Path | None = None,
    timeout_seconds: float = 120.0,
    cancel_file: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    system = (system_root or Path(__file__).resolve().parents[1]).expanduser().resolve(strict=True)
    box = system.parent
    inspection = inspect_wave(wave_id, system_root=system)
    default_dir = system / "runs" / "public" / wave_id
    try:
        out_dir = confined_path(str(output_dir or default_dir), system, label="OUTPUT")
    except PathViolation as exc:
        out_dir = system / "runs" / "public" / "refused"
        out_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = out_dir / "receipt.json"
        body = {
            "schema": SCHEMA,
            "wave_id": wave_id,
            "run_id": run_id or "refused-path",
            "status": "REFUSE",
            "reason_code": str(exc).split(":", 1)[0],
            "promotion_allowed": False,
            "output_path": _relative(receipt_path, system),
            "subprocess": None,
        }
        body["receipt_sha256"] = sha256_bytes(canonical_json_bytes(body))
        receipt_path.write_bytes(canonical_json_bytes(body) + b"\n")
        return body
    out_dir.mkdir(parents=True, exist_ok=True)
    child_path = confined_path("child.json", out_dir, label="OUTPUT")
    receipt_path = confined_path("receipt.json", out_dir, label="OUTPUT")
    if cancel_file is not None:
        try:
            cancel_file = confined_path(str(cancel_file), system, label="CANCEL")
        except PathViolation as exc:
            body = {
                "schema": SCHEMA,
                "wave_id": wave_id,
                "run_id": run_id or "refused-cancel-path",
                "status": "REFUSE",
                "reason_code": str(exc).split(":", 1)[0],
                "promotion_allowed": False,
                "output_path": _relative(receipt_path, system),
                "subprocess": None,
            }
            body["receipt_sha256"] = sha256_bytes(canonical_json_bytes(body))
            receipt_path.write_bytes(canonical_json_bytes(body) + b"\n")
            return body
    run_key = run_id or sha256_bytes(canonical_json_bytes({"wave_id": wave_id, "source": inspection.get("source")}))[:16]

    base: dict[str, Any] = {
        "schema": SCHEMA,
        "wave_id": wave_id,
        "run_id": run_key,
        "promotion_allowed": False,
        "claim_ceiling": inspection.get("claim_ceiling"),
        "inspection": inspection,
        "output_path": _relative(receipt_path, system),
        "child_output_path": _relative(child_path, system),
        "timeout_seconds": timeout_seconds,
        "cancel_file": _relative(cancel_file, system) if cancel_file else None,
    }
    if not inspection.get("runnable"):
        base.update({"status": "HOLD", "reason_code": inspection.get("reason_code", "HOLD_NOT_RUNNABLE"), "subprocess": None})
        base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
        receipt_path.write_bytes(canonical_json_bytes(base) + b"\n")
        return base
    if cancel_file is not None and cancel_file.exists():
        base.update({"status": "CANCELLED", "reason_code": "CANCELLED_BEFORE_SPAWN", "subprocess": None})
        base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
        receipt_path.write_bytes(canonical_json_bytes(base) + b"\n")
        return base

    spec = _cohort(_read_manifest(system))[wave_id]
    interpreter = (python_executable or Path(sys.executable)).expanduser().absolute()
    argv = _child_args(wave_id, spec, box=box, output=child_path, run_id=run_key)
    # The declared interpreter is used for execution; replace the command's
    # interpreter while retaining the exact -I/script invocation shape.
    argv[0] = str(interpreter)
    env = os.environ.copy()
    env.update({
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "CB_WAVE_RUN_ID": run_key,
        "CB_BOX_ROOT": str(box),
        "CB_SYSTEM_ROOT": str(system),
    })
    process = _run_process(
        argv,
        cwd=box,
        env=env,
        timeout_seconds=timeout_seconds,
        cancel_file=cancel_file,
    )
    child: dict[str, Any] = {}
    if child_path.is_file():
        try:
            loaded = json.loads(child_path.read_text(encoding="utf-8"))
            child = loaded if isinstance(loaded, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            child = {}
    expected_status = spec.get("expected_status")
    expected_rc = spec.get("expected_returncode")
    if process["cancelled"]:
        status, reason = "CANCELLED", "CANCELLED_DURING_RUN"
    elif process["timed_out"]:
        status, reason = "HOLD", "HOLD_TIMEOUT"
    elif not child:
        status, reason = "HOLD", "HOLD_CHILD_RECEIPT_MISSING"
    elif process["returncode"] != expected_rc:
        status, reason = "HOLD", "HOLD_CHILD_RETURNCODE"
    elif child.get("status") != expected_status:
        status, reason = "HOLD", "HOLD_CHILD_STATUS"
    else:
        status, reason = "PASS", None
    base.update({
        "status": status,
        "reason_code": reason,
        "command": argv,
        "cwd": _relative(box, box),
        "source": inspection.get("source"),
        "input_paths": spec.get("input_paths", []),
        "subprocess": {
            key: value
            for key, value in process.items()
            if key not in {"stdout", "stderr"}
        },
        "stdout_tail": process["stdout"][-2000:],
        "stderr_tail": process["stderr"][-2000:],
        "child_status": child.get("status"),
        "child_reason": child.get("reason"),
        "child_receipt_sha256": sha256_path(child_path) if child_path.is_file() else None,
    })
    base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
    receipt_path.write_bytes(canonical_json_bytes(base) + b"\n")
    return base


def _dump(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "inspect", "run"))
    parser.add_argument("wave_id", nargs="?")
    parser.add_argument("--system-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--python", dest="python_executable", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--cancel-file", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)
    system = args.system_root
    if args.command == "list":
        _dump(list_waves(system_root=system))
        return 0
    if not args.wave_id:
        parser.error("inspect/run requires wave_id")
    if args.command == "inspect":
        result = inspect_wave(args.wave_id, system_root=system)
        _dump(result)
        return 0 if result.get("runnable") else 2
    result = run_wave(
        args.wave_id,
        system_root=system,
        output_dir=args.output_dir,
        python_executable=args.python_executable,
        timeout_seconds=args.timeout,
        cancel_file=args.cancel_file,
        run_id=args.run_id,
    )
    _dump(result)
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
