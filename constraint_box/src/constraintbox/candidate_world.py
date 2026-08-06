"""Controller-owned telemetry adapter for the finite M★ candidate world.

The candidate world is an authored, bounded exploratory construction.  This
adapter lets ConstraintBox launch its all-engine envelope and capture the
result without treating parity, controls, or an envelope pass as CR truth,
formal admission, or promotion evidence.
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


RECEIPT_SCHEMA = "constraintbox.candidate-world-mstar-receipt.v1"
OPERATION_ID = "candidate-world-mstar-all-engine-envelope"
RUNNER_RELATIVE = Path("system_v8/manifold/prototypes/candidate_world_mstar_envelope.py")
DEFAULT_CR_ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CLAIM_CEILING = (
    "Executed one bounded authored candidate-world construction through the "
    "Python/JAX/PyTorch/Julia envelope; not CR validation, physical truth, "
    "formal admission, or promotion."
)
MAX_SOURCE_BYTES = 8 * 1024 * 1024


class CandidateWorldError(ValueError):
    """Raised for invalid controller-owned candidate-world configuration."""


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
        raise CandidateWorldError(f"candidate-world runner escapes CR root: {relative}")
    if not candidate.is_file():
        raise CandidateWorldError(f"registered candidate-world runner is missing: {candidate}")
    return candidate


def _source_path(value: Path) -> Path:
    source = value.expanduser().resolve(strict=True)
    if not source.is_file():
        raise CandidateWorldError("source_markdown must be a regular file")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise CandidateWorldError(f"source_markdown exceeds {MAX_SOURCE_BYTES} bytes")
    return source


def _runtime_env(run_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "PYTHONHASHSEED": "0",
        "NUMBA_CACHE_DIR": str(run_root / "numba_cache"),
        "MPLCONFIGDIR": str(run_root / "matplotlib_config"),
    }


def _write_receipt(run_root: Path, receipt: dict[str, Any]) -> None:
    (run_root / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_candidate_world(
    *,
    source_markdown: Path,
    run_root: Path,
    cr_root: Path | None = None,
    timeout_seconds: float = 600.0,
) -> tuple[dict[str, Any], int]:
    """Run the registered M★ envelope and capture telemetry only."""

    if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise CandidateWorldError("timeout_seconds must be positive")
    run_root = run_root.expanduser().absolute()
    if not run_root.is_absolute() or run_root.exists():
        raise CandidateWorldError("run_root must be a fresh absolute directory")
    run_root.mkdir(parents=True)
    (run_root / "numba_cache").mkdir()
    (run_root / "matplotlib_config").mkdir()
    source = _source_path(source_markdown)
    cr_root = (cr_root or DEFAULT_CR_ROOT).expanduser().resolve(strict=True)
    if not cr_root.is_dir():
        raise CandidateWorldError("cr_root must be a directory")
    runner = _strict_child(cr_root, RUNNER_RELATIVE)
    executable = selected_runtime_executable("python")
    runtime = inspect_external_runtime("python", executable)
    started = time.monotonic()
    execution: dict[str, Any] = {
        "operation_id": OPERATION_ID,
        "source_markdown_path": str(source),
        "source_markdown_sha256": _sha256_file(source),
        "runner_path": str(runner),
        "runner_sha256": _sha256_file(runner),
        "runtime": runtime,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "integration_level": [
            "controller_selected_source",
            "controller_selected_envelope",
            "source_addressed_invocation",
            "all_engine_subprocesses",
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
        execution.update(
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
            "execution": execution,
            "promotion_allowed": False,
            "validation_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        _write_receipt(run_root, receipt)
        return receipt, 4

    output_dir = run_root / "engine_envelope"
    command = [
        str(executable),
        str(runner),
        "--source-markdown",
        str(source),
        "--output-dir",
        str(output_dir),
    ]
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
        execution.update(
            {
                "command": command,
                "returncode": None,
                "status": "PARKED",
                "reason": "candidate_world_timeout",
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
            "execution": execution,
            "promotion_allowed": False,
            "validation_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        _write_receipt(run_root, receipt)
        return receipt, 4
    except OSError as exc:
        execution.update(
            {
                "command": command,
                "status": "PARKED",
                "reason": f"candidate_world_launch_unavailable:{type(exc).__name__}",
                "elapsed_seconds": time.monotonic() - launch_started,
            }
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "operation_id": OPERATION_ID,
            "status": "PARKED",
            "checks_do_not_block_execution": True,
            "execution": execution,
            "promotion_allowed": False,
            "validation_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        _write_receipt(run_root, receipt)
        return receipt, 4

    (run_root / "stdout.bin").write_bytes(stdout)
    (run_root / "stderr.bin").write_bytes(stderr)
    envelope_receipt = output_dir / "receipt.json"
    payload: dict[str, Any] | None = None
    if envelope_receipt.is_file():
        try:
            payload = parse_json_object(envelope_receipt.read_bytes())
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = None
    process_ok = process.returncode == 0
    receipt_ok = payload is not None and payload.get("schema") == "codex_ratchet.candidate_world_mstar_envelope.v1"
    execution.update(
        {
            "command": command,
            "returncode": process.returncode,
            "status": "EXECUTED" if process_ok and receipt_ok else "FAIL",
            "reason": "candidate_world_envelope_executed_telemetry_only" if process_ok and receipt_ok else "candidate_world_process_or_receipt_failure",
            "elapsed_seconds": time.monotonic() - launch_started,
            "stdout_path": str(run_root / "stdout.bin"),
            "stderr_path": str(run_root / "stderr.bin"),
            "stdout_sha256": _sha256_bytes(stdout),
            "stderr_sha256": _sha256_bytes(stderr),
            "stdout_preview": _bounded_text(stdout),
            "stderr_preview": _bounded_text(stderr),
            "envelope_receipt_path": str(envelope_receipt),
        }
    )
    if envelope_receipt.is_file():
        execution["envelope_receipt_sha256"] = _sha256_file(envelope_receipt)
    if payload is not None:
        execution["envelope_status"] = payload.get("all_pass")
        execution["envelope_all_pass"] = bool(payload.get("all_pass"))
        execution["engine_mode"] = payload.get("engine_mode")
        execution["lane_names"] = sorted(payload.get("lane_receipts", {}))
        execution["structural_equal"] = payload.get("structural_equal")
        execution["controls_pass"] = payload.get("controls_pass")
        execution["chirality_max_divergence"] = payload.get("chirality_max_divergence")
        execution["engine_envelope_summary"] = {
            "schema": payload.get("schema"),
            "candidate_id": payload.get("candidate_id"),
            "classification": payload.get("classification"),
            "all_pass": payload.get("all_pass"),
            "structural_equal": payload.get("structural_equal"),
            "controls_pass": payload.get("controls_pass"),
            "chirality_max_divergence": payload.get("chirality_max_divergence"),
            "source_sha256": payload.get("source_sha256"),
            "config_sha256": payload.get("config_sha256"),
            "source_digest_checks": payload.get("source_digest_checks"),
            "config_digest_checks": payload.get("config_digest_checks"),
            "structural_comparison": payload.get("structural_comparison"),
            "claim_ceiling": payload.get("claim_ceiling"),
        }
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "operation_id": OPERATION_ID,
        "status": execution["status"],
        "checks_do_not_block_execution": True,
        "execution": execution,
        "promotion_allowed": False,
        "validation_claim": False,
        "cr_truth_claim": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_receipt(run_root, receipt)
    return receipt, 0 if execution["status"] == "EXECUTED" else 1
