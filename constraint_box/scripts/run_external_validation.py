#!/usr/bin/env python3
"""Run the configured external sim estate and optional live Lev comparison.

This is deliberately outside the ConstraintBox kernel.  It takes the external
runtime locations explicitly, runs the controller-owned integration workload,
and records the optional Lev dry-run comparison beside it.  No model chooses
the workload, its tools, its gates, or its terminal disposition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from constraintbox.integrated_workload import (  # noqa: E402
    IntegratedWorkloadError,
    run_integrated_core_workload,
)
from constraintbox.leviathan_reference import (  # noqa: E402
    LeviathanReferenceError,
    run_leviathan_dry_run_comparison,
)


SCHEMA = "constraintbox.external-validation-suite-receipt.v1"
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")


class ExternalValidationError(ValueError):
    """Raised when the explicit external validation configuration is unsafe."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_new_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(body, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def _absolute_directory(path: Path, *, label: str) -> Path:
    if not path.is_absolute():
        raise ExternalValidationError(f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ExternalValidationError(f"{label} is unavailable: {exc}") from exc
    if not resolved.is_dir():
        raise ExternalValidationError(f"{label} must name a directory")
    return resolved


def _absolute_executable(path: Path, *, label: str) -> Path:
    if not path.is_absolute():
        raise ExternalValidationError(f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ExternalValidationError(f"{label} is unavailable: {exc}") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise ExternalValidationError(f"{label} must name an executable file")
    return resolved


def _requested_exit_code(disposition: str) -> int:
    return {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
        "HOLD": 5,
    }.get(disposition, 5)


def _terminal_from_components(*dispositions: str) -> str:
    if any(item == "HOLD" for item in dispositions):
        return "HOLD"
    if any(item == "BLOCKED" for item in dispositions):
        return "BLOCKED"
    if any(item == "PARKED" for item in dispositions):
        return "PARKED"
    if all(item == "ELIGIBLE" for item in dispositions):
        return "ELIGIBLE"
    return "HOLD"


def _artifact(path: Path, *, root: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": _sha256_file(path),
    }


def run_external_validation(
    *,
    request_id: str,
    run_root: Path,
    formal_runtime_dir: Path,
    java_executable: Path,
    lev_root: Path | None,
    subject_root: Path,
    timeout_seconds: int,
) -> tuple[dict[str, Any], int]:
    """Run the fixed external workload under explicit deployer configuration."""

    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalValidationError("request_id must be one bounded safe identifier")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 60:
        raise ExternalValidationError("timeout_seconds must be an integer in [1, 60]")
    if not run_root.is_absolute():
        raise ExternalValidationError("run_root must be absolute")
    if run_root.exists():
        raise ExternalValidationError("run_root must be a new directory")

    runtime_dir = _absolute_directory(formal_runtime_dir, label="formal_runtime_dir")
    java = _absolute_executable(java_executable, label="java_executable")
    subject = _absolute_directory(subject_root, label="subject_root")
    lev = _absolute_directory(lev_root, label="lev_root") if lev_root else None
    if java.name != "java":
        raise ExternalValidationError("java_executable must be named java")

    previous_runtime_dir = os.environ.get("CONSTRAINTBOX_FORMAL_RUNTIME_DIR")
    previous_path = os.environ.get("PATH", "")
    os.environ["CONSTRAINTBOX_FORMAL_RUNTIME_DIR"] = str(runtime_dir)
    os.environ["PATH"] = str(java.parent) + os.pathsep + previous_path
    try:
        selected_java = shutil.which("java")
        if selected_java is None or Path(selected_java).resolve() != java:
            raise ExternalValidationError(
                "configured java executable was not selected from PATH"
            )
        run_root.mkdir(parents=True, exist_ok=False)
        result_path = run_root / "external_validation_result.json"
        integrated_root = run_root / "01_integrated_workload"
        integrated_path = run_root / "01_integrated_workload_result.json"
        lev_path = run_root / "02_leviathan_reference_result.json"
        components: dict[str, Any] = {}
        try:
            integrated, integrated_exit = run_integrated_core_workload(
                request_id=f"{request_id}-integrated",
                run_root=integrated_root,
            )
            _write_new_json(integrated_path, integrated)
            components["integrated_workload"] = {
                "requested": True,
                "disposition": integrated.get("disposition"),
                "reason": integrated.get("reason"),
                "exit_code": integrated_exit,
                "run_root": str(integrated_root.relative_to(run_root)),
                "artifact": _artifact(integrated_path, root=run_root),
            }
        except (IntegratedWorkloadError, OSError, ValueError) as exc:
            components["integrated_workload"] = {
                "requested": True,
                "disposition": "HOLD",
                "reason": "integrated_workload_exception",
                "exception_type": type(exc).__name__,
                "error": str(exc),
            }

        if lev is not None:
            try:
                lev_result = run_leviathan_dry_run_comparison(
                    lev_root=lev,
                    subject_root=subject,
                    run_root=run_root / "02_leviathan_reference",
                    request_id=f"{request_id}-lev",
                    timeout_seconds=timeout_seconds,
                )
                _write_new_json(lev_path, lev_result)
                components["leviathan_reference"] = {
                    "requested": True,
                    "disposition": lev_result.get("disposition"),
                    "reason": lev_result.get("reason"),
                    "artifact": _artifact(lev_path, root=run_root),
                }
            except (LeviathanReferenceError, OSError, ValueError) as exc:
                components["leviathan_reference"] = {
                    "requested": True,
                    "disposition": "HOLD",
                    "reason": "leviathan_reference_exception",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                }
        else:
            components["leviathan_reference"] = {
                "requested": False,
                "disposition": "NOT_REQUESTED",
                "reason": "no_lev_root_configured",
            }

        requested = [
            str(component["disposition"])
            for component in components.values()
            if component["requested"]
        ]
        disposition = _terminal_from_components(*requested)
        receipt = {
            "schema": SCHEMA,
            "request_id": request_id,
            "disposition": disposition,
            "reason": (
                "all_requested_external_validation_components_eligible"
                if disposition == "ELIGIBLE"
                else "one_or_more_requested_external_validation_components_not_eligible"
            ),
            "configuration": {
                "formal_runtime_directory": str(runtime_dir),
                "java_executable": str(java),
                "subject_root": str(subject),
                "lev_root_configured": lev is not None,
                "lev_timeout_seconds": timeout_seconds,
                "python_executable": str(Path(sys.executable).absolute()),
            },
            "components": components,
            "runner_outside_cb_kernel": True,
            "llm_decision_authority": False,
            "controller_only_stage_selection": True,
            "release_allowed": False,
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": (
                "one configured local run executed the fixed ConstraintBox external "
                "sim-engine workload and, when requested, one live Lev dry-run "
                "comparison; it does not establish whole-estate coverage, portable "
                "installation, LevOS authority, temporal-model conformance to Python, "
                "ClaimGate admission, scientific or CR truth, release, or promotion"
            ),
        }
        _write_new_json(result_path, receipt)
        return receipt, _requested_exit_code(disposition)
    finally:
        if previous_runtime_dir is None:
            os.environ.pop("CONSTRAINTBOX_FORMAL_RUNTIME_DIR", None)
        else:
            os.environ["CONSTRAINTBOX_FORMAL_RUNTIME_DIR"] = previous_runtime_dir
        os.environ["PATH"] = previous_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--formal-runtime-dir", type=Path, required=True)
    parser.add_argument("--java-executable", type=Path, required=True)
    parser.add_argument("--lev-root", type=Path)
    parser.add_argument("--subject-root", type=Path, default=ROOT)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt, exit_code = run_external_validation(
            request_id=args.request_id,
            run_root=args.run_root,
            formal_runtime_dir=args.formal_runtime_dir,
            java_executable=args.java_executable,
            lev_root=args.lev_root,
            subject_root=args.subject_root,
            timeout_seconds=args.timeout_seconds,
        )
        output = args.output if args.output is not None else args.run_root / "external_validation_result.json"
        if output.resolve() != (args.run_root / "external_validation_result.json").resolve():
            if output.exists():
                raise ExternalValidationError("output must not already exist")
            _write_new_json(output, receipt)
    except ExternalValidationError as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
