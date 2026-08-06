"""ConstraintBox adapter for a registered, external Codex-Ratchet sim slice.

The adapter is intentionally narrower than a general process runner.  The
manifest is controller-owned and names the only CR source programs that can be
invoked.  A caller supplies a CR checkout and a fresh receipt directory, but
cannot supply a command, executable, tolerance, or verdict.  CR remains an
external system; this receipt records operation and handoff evidence only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .external_runtime_profiles import inspect_external_runtime, selected_runtime_executable
from .intake import canonical_json, parse_json_object
from .manifold_foundation import validate_foundation_file
from .paired_extension import validate_paired_fixture_file


MANIFEST_SCHEMA = "constraintbox.cr-sim-slice-manifest.v1"
RECEIPT_SCHEMA = "constraintbox.cr-sim-slice-receipt.v1"
CLAIM_CEILING = (
    "Source-addressed local operation evidence only; not CR validation, engine "
    "readiness, scientific proof, hostile-code containment, or promotion."
)
DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "config" / "cr_sim_slice_v1.json"
DEFAULT_CR_ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")


class CRSimSliceError(ValueError):
    """Raised for a malformed manifest, unsafe path, or invalid receipt."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _bounded_text(value: bytes, limit: int = 8192) -> str:
    if len(value) <= limit:
        return value.decode("utf-8", errors="replace")
    return value[:limit].decode("utf-8", errors="replace") + f"\n...[truncated {len(value) - limit} bytes]"


def _strict_child(root: Path, relative: str, *, must_exist: bool) -> Path:
    if not isinstance(relative, str) or not relative or relative.startswith("/"):
        raise CRSimSliceError("manifest paths must be non-empty relative paths")
    candidate = (root / relative).resolve(strict=False)
    if candidate != root and root not in candidate.parents:
        raise CRSimSliceError(f"manifest path escapes CR root: {relative}")
    if must_exist and not candidate.is_file():
        raise CRSimSliceError(f"registered CR source/result is missing: {candidate}")
    return candidate


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise CRSimSliceError("unsupported CR sim-slice manifest schema")
    if not isinstance(manifest.get("manifest_id"), str) or not manifest["manifest_id"]:
        raise CRSimSliceError("manifest_id is required")
    profiles = manifest.get("profiles")
    entries = manifest.get("entries")
    if not isinstance(profiles, dict) or not profiles:
        raise CRSimSliceError("manifest profiles must be a non-empty object")
    if not isinstance(entries, list) or not entries:
        raise CRSimSliceError("manifest entries must be a non-empty array")
    ids: set[str] = set()
    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            raise CRSimSliceError(f"entries[{index}] must be an object")
        required = {"id", "group", "engine", "source", "result", "result_mode", "reads_peer_result", "integration_level"}
        allowed = required | {"julia_project", "fixture", "fixture_kind"}
        if not required <= set(item) or not set(item) <= allowed:
            raise CRSimSliceError(f"entries[{index}] fields differ")
        entry_id = item.get("id")
        if not isinstance(entry_id, str) or not entry_id or entry_id in ids:
            raise CRSimSliceError(f"entries[{index}].id must be unique non-empty text")
        ids.add(entry_id)
        if item.get("engine") not in {"python", "julia"}:
            raise CRSimSliceError(f"entries[{index}].engine is not supported")
        if item.get("result_mode") not in {"json_all_pass", "json_receipt", "exit_zero"}:
            raise CRSimSliceError(f"entries[{index}].result_mode is not supported")
        if not isinstance(item.get("reads_peer_result"), bool):
            raise CRSimSliceError(f"entries[{index}].reads_peer_result must be boolean")
        if not isinstance(item.get("integration_level"), list) or not item["integration_level"]:
            raise CRSimSliceError(f"entries[{index}].integration_level must be non-empty")
        if item.get("engine") == "julia" and not isinstance(item.get("julia_project"), str):
            raise CRSimSliceError(f"entries[{index}].julia_project is required for Julia")
        if "fixture" in item and (not isinstance(item["fixture"], str) or not item["fixture"]):
            raise CRSimSliceError(f"entries[{index}].fixture must be a non-empty relative path")
        if "fixture_kind" in item and (not isinstance(item["fixture_kind"], str) or not item["fixture_kind"]):
            raise CRSimSliceError(f"entries[{index}].fixture_kind must be non-empty text")
        if "fixture_kind" in item and "fixture" not in item:
            raise CRSimSliceError(f"entries[{index}].fixture_kind requires fixture")
    for profile, selected in profiles.items():
        if not isinstance(profile, str) or not profile or not isinstance(selected, list) or not selected:
            raise CRSimSliceError("profiles must map names to non-empty entry-id arrays")
        if len(set(selected)) != len(selected) or not set(selected).issubset(ids):
            raise CRSimSliceError(f"profile {profile!r} references unknown or duplicate entries")


def _runtime_env(*, run_root: Path, julia: bool) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "PYTHONHASHSEED": "0",
    }
    env["NUMBA_CACHE_DIR"] = str(run_root / "numba_cache")
    env["MPLCONFIGDIR"] = str(run_root / "matplotlib_config")
    if julia:
        env["JULIA_LOAD_PATH"] = "@:@stdlib"
        # Keep compiled cache writes in the bounded run directory while still
        # allowing the installed package bodies from the operator's depot.
        env["JULIA_DEPOT_PATH"] = f"{run_root / 'julia_depot'}:{Path.home() / '.julia'}"
    return env


def _foundation_path(manifest: dict[str, Any], cr_root: Path) -> Path:
    relative = manifest.get("foundation_fixture", "constraint_box/fixtures/cr/manifold_time_first_seed_v1.json")
    return _strict_child(cr_root, relative, must_exist=True)


def _entry_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in manifest["entries"]}


def _result_payload(result_path: Path) -> dict[str, Any] | None:
    if not result_path.is_file():
        return None
    try:
        value = parse_json_object(result_path.read_bytes())
    except Exception:
        return None
    return value


def _payload_check(
    entry: dict[str, Any],
    payload: dict[str, Any] | None,
    fixture: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    mode = entry["result_mode"]
    if mode == "exit_zero":
        return True, "source_exit_zero"
    if payload is None:
        return False, "result_missing_or_not_strict_json"
    if fixture is not None:
        if payload.get("fixture_sha256") != fixture["source_sha256"]:
            return False, "fixture_hash_mismatch"
        if fixture.get("kind") == "paired_whole_extension":
            if payload.get("canonical_observation") != fixture.get("canonical_observation"):
                return False, "fixture_observation_mismatch"
    if mode == "json_all_pass":
        if payload.get("all_pass") is not True:
            return False, "result_all_pass_false_or_missing"
        if "reads_peer_result" in payload and payload["reads_peer_result"] is not entry["reads_peer_result"]:
            return False, "reads_peer_result_mismatch"
        if payload.get("promotion_allowed") is not False:
            return False, "promotion_boundary_missing"
        if payload.get("classification") not in {None, "scratch_diagnostic", "formal_scout"}:
            return False, "unexpected_classification"
        return True, "controller_recheck_all_pass"
    if mode == "json_receipt":
        if not isinstance(payload.get("provenance"), dict):
            return False, "receipt_provenance_missing"
        return True, "controller_recheck_receipt"
    return False, "unsupported_result_mode"


def run_cr_sim_slice(
    *,
    profile: str,
    run_root: Path,
    cr_root: Path | None = None,
    manifest_path: Path | None = None,
    timeout_seconds: float = 300.0,
) -> tuple[dict[str, Any], int]:
    """Run one fixed CR slice and return its receipt plus CLI-style exit code."""

    if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise CRSimSliceError("timeout_seconds must be positive")
    run_root = run_root.expanduser().absolute()
    if not run_root.is_absolute() or run_root.exists():
        raise CRSimSliceError("run_root must be a fresh absolute directory")
    run_root.mkdir(parents=True)
    (run_root / "numba_cache").mkdir()
    (run_root / "matplotlib_config").mkdir()
    (run_root / "julia_depot").mkdir()

    cr_root = (cr_root or Path(os.environ.get("CONSTRAINTBOX_CR_ROOT", str(DEFAULT_CR_ROOT)))).expanduser().resolve(strict=True)
    if not cr_root.is_dir():
        raise CRSimSliceError("cr_root must be a directory")
    manifest_path = (manifest_path or DEFAULT_MANIFEST).expanduser().resolve(strict=True)
    manifest = parse_json_object(manifest_path.read_bytes())
    _validate_manifest(manifest)
    if profile not in manifest["profiles"]:
        raise CRSimSliceError(f"unknown CR slice profile: {profile}")

    foundation = validate_foundation_file(_foundation_path(manifest, cr_root))
    if foundation.get("status") != "PASS":
        raise CRSimSliceError("time-first foundation seed did not validate")

    entries = _entry_lookup(manifest)
    entry_fixtures: dict[str, dict[str, Any] | None] = {}
    fixture_receipts: dict[str, dict[str, Any]] = {}
    for entry_id, entry in entries.items():
        relative_fixture = entry.get("fixture")
        if not relative_fixture:
            entry_fixtures[entry_id] = None
            continue
        fixture_path = _strict_child(cr_root, relative_fixture, must_exist=True)
        fixture_kind = entry.get("fixture_kind")
        if fixture_kind == "paired_whole_extension":
            fixture_validation = validate_paired_fixture_file(fixture_path)
            if fixture_validation.get("status") != "PASS":
                raise CRSimSliceError(f"paired fixture did not validate: {fixture_path}")
        else:
            fixture_validation = {
                "status": "PRESENT",
                "source_path": str(fixture_path),
                "source_sha256": _sha256_file(fixture_path),
            }
        fixture_metadata = {
            "path": str(fixture_path),
            "kind": fixture_kind,
            "source_sha256": fixture_validation["source_sha256"],
            "canonical_observation": fixture_validation.get("canonical_observation"),
        }
        entry_fixtures[entry_id] = fixture_metadata
        fixture_receipts[str(fixture_path)] = fixture_validation
    selected_ids = manifest["profiles"][profile]
    python_executable = selected_runtime_executable("python")
    julia_executable = selected_runtime_executable("julia")
    runtimes = {
        "python": inspect_external_runtime("python", python_executable),
        "julia": inspect_external_runtime("julia", julia_executable),
    }
    receipt_entries: list[dict[str, Any]] = []
    started = time.monotonic()
    for entry_id in selected_ids:
        entry = entries[entry_id]
        source = _strict_child(cr_root, entry["source"], must_exist=True)
        result = _strict_child(cr_root, entry["result"], must_exist=False) if entry["result"] else None
        runtime = runtimes[entry["engine"]]
        record: dict[str, Any] = {
            "entry_id": entry_id,
            "group": entry["group"],
            "engine": entry["engine"],
            "source_path": str(source),
            "source_sha256": _sha256_file(source),
            "result_path": str(result) if result else None,
            "integration_level": entry["integration_level"],
            "reads_peer_result_declared": entry["reads_peer_result"],
            "runtime": runtime,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        fixture = entry_fixtures[entry_id]
        if fixture is not None:
            record.update(
                {
                    "fixture_path": fixture["path"],
                    "fixture_kind": fixture.get("kind"),
                    "fixture_sha256": fixture["source_sha256"],
                }
            )
        if not runtime.get("eligible"):
            record.update({"status": "PARKED", "reason": runtime.get("reason", "runtime_unavailable")})
            receipt_entries.append(record)
            continue
        if entry["engine"] == "python":
            command = [str(python_executable), "-I", str(source)]
        else:
            project = _strict_child(cr_root, entry["julia_project"], must_exist=False)
            command = [str(julia_executable), "--startup-file=no", f"--project={project}", str(source)]
        env = _runtime_env(run_root=run_root, julia=entry["engine"] == "julia")
        launch_started = time.monotonic()
        try:
            process = subprocess.run(
                command,
                cwd=str(cr_root),
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
            stdout = process.stdout
            stderr = process.stderr
            (run_root / f"{entry_id}.stdout").write_bytes(stdout)
            (run_root / f"{entry_id}.stderr").write_bytes(stderr)
            record.update(
                {
                    "command": command,
                    "returncode": process.returncode,
                    "elapsed_seconds": time.monotonic() - launch_started,
                    "stdout_sha256": _sha256_bytes(stdout),
                    "stderr_sha256": _sha256_bytes(stderr),
                    "stdout_preview": _bounded_text(stdout),
                    "stderr_preview": _bounded_text(stderr),
                }
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            (run_root / f"{entry_id}.stdout").write_bytes(stdout)
            (run_root / f"{entry_id}.stderr").write_bytes(stderr)
            record.update(
                {
                    "command": command,
                    "returncode": None,
                    "elapsed_seconds": time.monotonic() - launch_started,
                    "stdout_sha256": _sha256_bytes(stdout),
                    "stderr_sha256": _sha256_bytes(stderr),
                    "stdout_preview": _bounded_text(stdout),
                    "stderr_preview": _bounded_text(stderr),
                    "status": "FAIL",
                    "reason": "source_timeout",
                }
            )
            receipt_entries.append(record)
            continue
        except OSError as exc:
            record.update({"status": "PARKED", "reason": f"source_launch_unavailable:{type(exc).__name__}"})
            receipt_entries.append(record)
            continue

        payload = _result_payload(result) if result else None
        payload_ok, payload_reason = _payload_check(entry, payload, fixture)
        process_ok = record["returncode"] == 0
        status = "PASS" if process_ok and payload_ok else "FAIL"
        if process_ok and entry["result_mode"] != "exit_zero" and result and payload is not None:
            captured = run_root / f"{entry_id}.result.json"
            captured.write_bytes(result.read_bytes())
            record["captured_result_path"] = str(captured)
            record["result_sha256"] = _sha256_file(result)
            if isinstance(payload.get("source_path"), str) and payload["source_path"] not in {str(source), entry["source"]}:
                status = "FAIL"
                payload_reason = "result_source_path_mismatch"
        record.update({"status": status, "reason": payload_reason if status == "PASS" else payload_reason})
        receipt_entries.append(record)

    statuses = {entry["status"] for entry in receipt_entries}
    if "FAIL" in statuses:
        status = "FAIL"
        exit_code = 1
    elif "PARKED" in statuses:
        status = "PARKED"
        exit_code = 4
    else:
        status = "PASS"
        exit_code = 0
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "slice_id": manifest["manifest_id"],
        "profile": profile,
        "status": status,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "promotion_allowed": False,
        "cr_truth_claim": False,
        "claim_ceiling": CLAIM_CEILING,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "cr_root": str(cr_root),
        "foundation": foundation,
        "fixtures": fixture_receipts,
        "runtimes": runtimes,
        "entries": receipt_entries,
        "elapsed_seconds": time.monotonic() - started,
        "controller_source_path": str(Path(__file__).resolve()),
        "controller_source_sha256": _sha256_file(Path(__file__).resolve()),
    }
    (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt, exit_code
