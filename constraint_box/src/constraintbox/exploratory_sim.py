"""Controller-owned, telemetry-only execution of the finite IJK prototype.

This adapter is intentionally separate from ``cr_sim_slice``.  The IJK source
is allowed to run first and its checks are captured as observations; a false
check never suppresses the authored simulation.  Nothing in this module is an
admission decision or a claim that the prototype is the Codex-Ratchet truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from .external_runtime_profiles import inspect_external_runtime, selected_runtime_executable
from .intake import parse_json_object


RECEIPT_SCHEMA = "constraintbox.exploratory-ijk-receipt.v1"
OPERATION_ID = "manifold-ijk-engine-prototype"
SOURCE_RELATIVE = Path("system_v8/manifold/prototypes/manifold_ijk_engine_prototype.py")
DEFAULT_CR_ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CLAIM_CEILING = (
    "Executed authored finite prototype telemetry only; not manifold validation, "
    "CR truth, engine readiness, scientific proof, or promotion."
)


class ExploratorySimError(ValueError):
    """Raised for invalid controller-owned exploratory-run configuration."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _bounded_text(value: bytes, limit: int = 8192) -> str:
    text = value[:limit].decode("utf-8", errors="replace")
    if len(value) > limit:
        text += f"\n...[truncated {len(value) - limit} bytes]"
    return text


def _strict_child(root: Path, relative: Path) -> Path:
    candidate = (root / relative).resolve(strict=False)
    if candidate != root and root not in candidate.parents:
        raise ExploratorySimError(f"prototype path escapes CR root: {relative}")
    if not candidate.is_file():
        raise ExploratorySimError(f"registered prototype is missing: {candidate}")
    return candidate


def _runtime_env(run_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "PYTHONHASHSEED": "0",
        "NUMBA_CACHE_DIR": str(run_root / "numba_cache"),
        "MPLCONFIGDIR": str(run_root / "matplotlib_config"),
    }


def _telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    checks = payload.get("checks")
    math_values = payload.get("math")
    basins = payload.get("basins")
    carrier = payload.get("carrier")
    return {
        "prototype_status": payload.get("status"),
        "gate_policy": payload.get("gate_policy"),
        "checks": checks if isinstance(checks, dict) else {},
        "checks_all_true": all(checks.values()) if isinstance(checks, dict) and checks else False,
        "carrier": carrier if isinstance(carrier, dict) else {},
        "math": math_values if isinstance(math_values, dict) else {},
        "basins": basins if isinstance(basins, dict) else {},
        "interpretation_lock": payload.get("interpretation_lock", {}),
    }


def run_ijk_prototype(
    *,
    run_root: Path,
    cr_root: Path | None = None,
    timeout_seconds: float = 300.0,
) -> tuple[dict[str, Any], int]:
    """Run the fixed IJK source and capture its telemetry without gating it."""

    if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise ExploratorySimError("timeout_seconds must be positive")
    run_root = run_root.expanduser().absolute()
    if not run_root.is_absolute() or run_root.exists():
        raise ExploratorySimError("run_root must be a fresh absolute directory")
    run_root.mkdir(parents=True)
    (run_root / "numba_cache").mkdir()
    (run_root / "matplotlib_config").mkdir()
    cr_root = (cr_root or DEFAULT_CR_ROOT).expanduser().resolve(strict=True)
    if not cr_root.is_dir():
        raise ExploratorySimError("cr_root must be a directory")
    source = _strict_child(cr_root, SOURCE_RELATIVE)
    executable = selected_runtime_executable("python")
    runtime = inspect_external_runtime("python", executable)
    started = time.monotonic()
    record: dict[str, Any] = {
        "operation_id": OPERATION_ID,
        "source_path": str(source),
        "source_sha256": _sha256_file(source),
        "runtime": runtime,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "integration_level": [
            "controller_selected_source",
            "source_invocation",
            "isolated_output_dir",
            "receipt_capture",
            "telemetry_only",
        ],
        "promotion_allowed": False,
        "validation_claim": False,
        "cr_truth_claim": False,
        "claim_ceiling": CLAIM_CEILING,
        "checks_do_not_block_execution": True,
    }
    if not runtime.get("eligible") or executable is None:
        record.update(
            {
                "status": "PARKED",
                "reason": runtime.get("reason", "python_runtime_unavailable"),
                "elapsed_seconds": time.monotonic() - started,
            }
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "operation_id": OPERATION_ID,
            "status": "PARKED",
            "checks_do_not_block_execution": True,
            "execution": record,
            "promotion_allowed": False,
            "validation_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt, 4

    output_dir = run_root / "prototype"
    output_dir.mkdir()
    command = [str(executable), "-I", str(source), "--output-dir", str(output_dir)]
    env = _runtime_env(run_root)
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
        stdout, stderr = process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        (run_root / "stdout.bin").write_bytes(stdout)
        (run_root / "stderr.bin").write_bytes(stderr)
        record.update(
            {
                "command": command,
                "returncode": None,
                "status": "PARKED",
                "reason": "source_timeout",
                "elapsed_seconds": time.monotonic() - launch_started,
                "stdout_sha256": _sha256_bytes(stdout),
                "stderr_sha256": _sha256_bytes(stderr),
                "stdout_preview": _bounded_text(stdout),
                "stderr_preview": _bounded_text(stderr),
            }
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "operation_id": OPERATION_ID,
            "status": "PARKED",
            "checks_do_not_block_execution": True,
            "execution": record,
            "promotion_allowed": False,
            "validation_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt, 4
    except OSError as exc:
        record.update(
            {
                "command": command,
                "status": "PARKED",
                "reason": f"source_launch_unavailable:{type(exc).__name__}",
                "elapsed_seconds": time.monotonic() - launch_started,
            }
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "operation_id": OPERATION_ID,
            "status": "PARKED",
            "checks_do_not_block_execution": True,
            "execution": record,
            "promotion_allowed": False,
            "validation_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt, 4

    (run_root / "stdout.bin").write_bytes(stdout)
    (run_root / "stderr.bin").write_bytes(stderr)
    prototype_receipt = output_dir / "RUN_RECEIPT.json"
    payload: dict[str, Any] | None = None
    if prototype_receipt.is_file():
        try:
            payload = parse_json_object(prototype_receipt.read_bytes())
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = None
    process_ok = process.returncode == 0
    receipt_ok = payload is not None and isinstance(payload.get("checks"), dict)
    record.update(
        {
            "command": command,
            "returncode": process.returncode,
            "status": "EXECUTED" if process_ok and receipt_ok else "FAIL",
            "reason": "prototype_executed_checks_telemetry_only" if process_ok and receipt_ok else "prototype_process_or_receipt_failure",
            "elapsed_seconds": time.monotonic() - launch_started,
            "stdout_path": str(run_root / "stdout.bin"),
            "stderr_path": str(run_root / "stderr.bin"),
            "stdout_sha256": _sha256_bytes(stdout),
            "stderr_sha256": _sha256_bytes(stderr),
            "stdout_preview": _bounded_text(stdout),
            "stderr_preview": _bounded_text(stderr),
            "prototype_receipt_path": str(prototype_receipt),
        }
    )
    if prototype_receipt.is_file():
        record["prototype_receipt_sha256"] = _sha256_file(prototype_receipt)
    if payload is not None:
        record["telemetry"] = _telemetry(payload)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "operation_id": OPERATION_ID,
        "status": record["status"],
        "checks_do_not_block_execution": True,
        "execution": record,
        "promotion_allowed": False,
        "validation_claim": False,
        "cr_truth_claim": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt, 0 if record["status"] == "EXECUTED" else 1
