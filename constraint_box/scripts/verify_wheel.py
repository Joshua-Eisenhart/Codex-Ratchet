#!/usr/bin/env python3
"""Verify the portable ConstraintBox *core* from a freshly installed wheel.

This is packaging verification, not a ConstraintBox runtime command.  It is
allowed to invoke pip because it proves an installer boundary; the installed
``constraintbox`` process never installs, selects, or substitutes an
interpreter or a library.

The smoke deliberately covers only the current five-tool v9 core through its
installed public entrypoint. Sim-engine adapters, MMM/user profiles, hosted
advisers, external ClaimGate composition, and temporal checkers remain
separate contracts and are not made silently load-bearing here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "receipts" / "WHEEL_SMOKE.json"
_ISOLATED = "-I"
_VERIFICATION_SCOPE = "lean_core_install_smoke"
_EXCLUDED_PRODUCT_SURFACES = (
    "user_mmm_and_profile_request_preflight_not_packaged_in_this_wheel",
    "external_sim_engine_adapters_and_estate",
    "external_temporal_runtime_profiles",
    "hosted_llm_advisers_and_proposal_release_surfaces",
    "claimgate_full_product_composition",
)
_LEAN_CORE_OPERATION_IDS = (
    "v9_console_doctor",
    "v9_module_exercise",
)


class VerificationError(ValueError):
    """The requested installer-verification boundary is malformed."""


@dataclass(frozen=True)
class Invocation:
    argv: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes
    failure_kind: str | None = None


def _bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    return value if isinstance(value, bytes) else value.encode("utf-8", "replace")


def invoke(
    argv: Iterable[str],
    *,
    timeout: float,
    env: dict[str, str],
) -> Invocation:
    """Run one verifier-owned child and retain failures as receipt data."""

    command = tuple(str(part) for part in argv)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return Invocation(
            command,
            124,
            _bytes(exc.stdout),
            _bytes(exc.stderr),
            "timeout",
        )
    except OSError as exc:
        return Invocation(
            command,
            127,
            b"",
            str(exc).encode("utf-8", "replace"),
            "os_error",
        )
    return Invocation(command, completed.returncode, completed.stdout, completed.stderr)


def _fresh_environment() -> dict[str, str]:
    """Prevent a source checkout or caller venv from satisfying the smoke."""

    environment = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return environment


def _venv_python(root: Path) -> Path:
    return (
        root / "Scripts" / "python.exe"
        if os.name == "nt"
        else root / "bin" / "python"
    )


def _json_object(raw: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _failure_reason(invocation: Invocation) -> str | None:
    """Return a bounded, portable diagnostic category without copying host logs."""

    if invocation.failure_kind is not None:
        return invocation.failure_kind
    if invocation.returncode == 0:
        return None
    text = (invocation.stdout + b"\n" + invocation.stderr).decode(
        "utf-8", "replace"
    ).casefold()
    if "externally-managed-environment" in text:
        return "externally_managed_python_prevents_venv_bootstrap"
    if "failed to establish a new connection" in text or "nodename nor servname" in text:
        return "package_index_connection_failed"
    if "no matching distribution found" in text:
        return "dependency_not_resolved_from_configured_index"
    if "requires-python" in text or "requires python" in text:
        return "interpreter_outside_declared_python_range"
    return "subprocess_exit_nonzero"


def _lookup(value: dict[str, Any] | None, dotted_path: str) -> object:
    current: object = value
    parts = dotted_path.split(".")
    position = 0
    while position < len(parts):
        if not isinstance(current, dict):
            return None
        # Tool identifiers are intentionally dotted (for example ``python.z3``),
        # while the verifier also uses dotted navigation. Prefer the longest
        # actual key at each level so both forms remain unambiguous.
        match: str | None = None
        next_position = position
        for end in range(len(parts), position, -1):
            candidate = ".".join(parts[position:end])
            if candidate in current:
                match = candidate
                next_position = end
                break
        if match is None:
            return None
        current = current[match]
        position = next_position
    return current


def _check(
    *,
    name: str,
    invocation: Invocation,
    expected_exit: int = 0,
    expected_json: dict[str, object] | None = None,
) -> dict[str, object]:
    body = _json_object(invocation.stdout)
    observed = {
        key: _lookup(body, key)
        for key in sorted((expected_json or {}))
    }
    json_matches = all(
        observed[key] == expected
        for key, expected in (expected_json or {}).items()
    )
    passed = (
        invocation.failure_kind is None
        and invocation.returncode == expected_exit
        and json_matches
    )
    return {
        "name": name,
        "passed": passed,
        "expected_exit": expected_exit,
        "exit": invocation.returncode,
        "expected_json": expected_json or {},
        "observed_json": observed,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _process_check(
    *,
    name: str,
    invocation: Invocation,
    expected_exit: int = 0,
) -> dict[str, object]:
    passed = (
        invocation.failure_kind is None
        and invocation.returncode == expected_exit
    )
    return {
        "name": name,
        "passed": passed,
        "expected_exit": expected_exit,
        "exit": invocation.returncode,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _skipped_check(name: str, reason: str) -> dict[str, object]:
    return {
        "name": name,
        "passed": False,
        "state": "SKIPPED",
        "reason": reason,
    }


def _wheel_candidates(dist: Path) -> tuple[Path, ...]:
    return tuple(sorted(dist.glob("constraintbox-*.whl")))


def discover_wheel(wheel: Path | None) -> Path:
    """Resolve exactly one wheel without selecting a newest arbitrary artifact."""

    if wheel is not None:
        candidate = wheel.expanduser().resolve()
        if not candidate.is_file() or candidate.suffix != ".whl":
            raise VerificationError(f"wheel does not exist or is not a wheel: {candidate}")
        return candidate
    candidates = _wheel_candidates(ROOT / "dist")
    if not candidates:
        raise VerificationError("no constraintbox wheel found; build one before verification")
    if len(candidates) != 1:
        names = ", ".join(candidate.name for candidate in candidates)
        raise VerificationError(
            "wheel selection is ambiguous; pass --wheel explicitly: " + names
        )
    return candidates[0]


def install_argv(
    python: Path,
    wheel: Path,
    *,
    wheelhouse: Path | None,
    offline: bool,
) -> list[str]:
    """Build a normal dependency-resolving installer invocation.

    ``--no-deps`` is intentionally absent.  A wheelhouse is an explicit,
    reproducible offline resolver input; it is never inferred from this host.
    """

    command = [
        str(python),
        _ISOLATED,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
    ]
    if wheelhouse is not None:
        command.extend(("--find-links", str(wheelhouse)))
    if offline:
        command.append("--no-index")
    command.append(str(wheel))
    return command


_INSTALLED_ORIGIN_PROGRAM = """
import json
import sys
from pathlib import Path
import constraintbox

environment_root = Path(sys.prefix).resolve()
module_path = Path(constraintbox.__file__).resolve()
print(json.dumps({
    "schema": "constraintbox.fresh-install-origin.v1",
    "module": "constraintbox",
    "inside_fresh_environment": environment_root == module_path.parent or environment_root in module_path.parents,
}, sort_keys=True))
"""

_DEFAULT_CLI_BOUNDARY_PROGRAM = """
import json
from constraintbox.core_cli import build_parser

parser = build_parser()
subparsers = next(
    action for action in parser._actions if getattr(action, "choices", None)
)
print(json.dumps({
    "schema": "constraintbox.default-cli-boundary.v1",
    "commands": sorted(subparsers.choices),
    "gate_exposed": "gate" in subparsers.choices,
}, sort_keys=True))
"""

def _core_checks(
    *,
    python: Path,
    scratch: Path,
    timeout: float,
    env: dict[str, str],
) -> list[dict[str, object]]:
    console = python.with_name("constraintbox.exe" if os.name == "nt" else "constraintbox")
    absent_optional_request = scratch / "control-plane-optional-dependency.json"
    absent_optional_request.write_text("{}\n", encoding="utf-8")
    absent_optional_db = scratch / "control-plane-optional-dependency.sqlite"
    commands: tuple[tuple[str, list[str], int, dict[str, object]], ...] = (
        (
            "installed_origin",
            [str(python), _ISOLATED, "-c", _INSTALLED_ORIGIN_PROGRAM],
            0,
            {
                "schema": "constraintbox.fresh-install-origin.v1",
                "module": "constraintbox",
                "inside_fresh_environment": True,
            },
        ),
        (
            "v9_default_cli_external_surface_exclusion",
            [str(python), _ISOLATED, "-c", _DEFAULT_CLI_BOUNDARY_PROGRAM],
            0,
            {
                "schema": "constraintbox.default-cli-boundary.v1",
                "commands": ["control-plane", "doctor", "exercise"],
                "gate_exposed": False,
            },
        ),
        (
            "v9_console_doctor",
            [str(console), "doctor", "--json"],
            0,
            {
                "schema": "constraintbox.core-doctor.v9",
                "missing": [],
                "core_tool_ids": [
                    "python.z3",
                    "python.cvc5",
                    "python.sympy",
                    "python.rustworkx",
                    "python.maude",
                ],
            },
        ),
        (
            "v9_module_exercise",
            [
                str(python),
                _ISOLATED,
                "-m",
                "constraintbox",
                "exercise",
                "--json",
            ],
            0,
            {
                "schema": "constraintbox.core-exercise.v9",
                "promotion_allowed": False,
                "claim_ceiling": "five_tool_function_exercise_only",
                "observations.python.z3.status": "sat",
                "observations.python.cvc5.status": "sat",
                "observations.python.maude.module_loaded": True,
            },
        ),
        (
            "v9_control_plane_dependency_severance",
            [
                str(console),
                "control-plane",
                "--request",
                str(absent_optional_request),
                "--db",
                str(absent_optional_db),
            ],
            2,
            {
                "disposition": "HOLD",
                "reason_code": "HOLD_CONTROL_PLANE_DEPENDENCY_MISSING",
            },
        ),
    )
    return [
        _check(
            name=name,
            invocation=invoke(argv, timeout=timeout, env=env),
            expected_exit=expected_exit,
            expected_json=expected,
        )
        for name, argv, expected_exit, expected in commands
    ]


def verify_wheel(
    wheel: Path,
    *,
    timeout: float = 120.0,
    wheelhouse: Path | None = None,
    offline: bool = False,
) -> dict[str, object]:
    """Install a wheel into a new venv and run the portable core smoke.

    A resolver failure is a failed installer boundary.  It is not converted
    into a source-run, a ``--no-deps`` install, or a partial passing receipt.
    """

    wheel = wheel.expanduser().resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise VerificationError(f"wheel does not exist or is not a wheel: {wheel}")
    if timeout <= 0:
        raise VerificationError("timeout must be positive")
    if offline and wheelhouse is None:
        raise VerificationError("--offline requires an explicit --wheelhouse")
    if wheelhouse is not None:
        wheelhouse = wheelhouse.expanduser().resolve()
        if not wheelhouse.is_dir():
            raise VerificationError(f"wheelhouse is not a directory: {wheelhouse}")

    checks: list[dict[str, object]] = []
    environment = _fresh_environment()
    install_mode = (
        "offline_wheelhouse_dependency_resolution"
        if offline
        else "normal_dependency_resolution"
    )
    with tempfile.TemporaryDirectory(prefix="constraintbox-wheel-") as directory:
        root = Path(directory)
        create = _process_check(
            name="fresh_venv_create",
            invocation=invoke(
                [sys.executable, "-m", "venv", str(root)],
                timeout=timeout,
                env=environment,
            ),
        )
        checks.append(create)
        python = _venv_python(root)
        if not create["passed"] or not python.is_file():
            checks.extend(
                _skipped_check(name, "fresh_venv_unavailable")
                for name in (
                    "dependency_resolved_install",
                    "pip_dependency_check",
                    "installed_origin",
                    "v9_default_cli_external_surface_exclusion",
                    "v9_console_doctor",
                    "v9_module_exercise",
                    "v9_control_plane_dependency_severance",
                )
            )
            reason = "fresh_venv_creation_failed"
        else:
            install = _process_check(
                name="dependency_resolved_install",
                invocation=invoke(
                    install_argv(
                        python,
                        wheel,
                        wheelhouse=wheelhouse,
                        offline=offline,
                    ),
                    timeout=timeout,
                    env=environment,
                ),
            )
            checks.append(install)
            if not install["passed"]:
                checks.extend(
                    _skipped_check(name, "dependency_resolution_or_wheel_install_failed")
                    for name in (
                        "pip_dependency_check",
                        "installed_origin",
                        "v9_default_cli_external_surface_exclusion",
                        "v9_console_doctor",
                        "v9_module_exercise",
                        "v9_control_plane_dependency_severance",
                    )
                )
                reason = "dependency_resolution_or_wheel_install_failed"
            else:
                checks.append(
                    _process_check(
                        name="pip_dependency_check",
                        invocation=invoke(
                            [str(python), _ISOLATED, "-m", "pip", "check"],
                            timeout=timeout,
                            env=environment,
                        ),
                    )
                )
                checks.extend(
                    _core_checks(
                        python=python,
                        scratch=root,
                        timeout=timeout,
                        env=environment,
                    )
                )
                reason = (
                    "clean_wheel_smoke_passed"
                    if all(check.get("passed") is True for check in checks)
                    else "clean_wheel_smoke_failed"
                )

    passed = all(check.get("passed") is True for check in checks)
    return {
        "schema": "constraintbox.wheel-smoke.v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verification_scope": _VERIFICATION_SCOPE,
        "full_constraintbox_product_verified": False,
        "verified_lean_core_operations": list(_LEAN_CORE_OPERATION_IDS),
        "excluded_product_surfaces": list(_EXCLUDED_PRODUCT_SURFACES),
        "claim_ceiling": (
            "a fresh dependency-resolved installation on this host executed "
            "the declared five-tool v9 core checks only; this is not Linux or "
            "Windows execution, cross-platform adoption, full ConstraintBox "
            "product verification, user MMM/profile resources, external sim "
            "estate, LLM/provider paths, ClaimGate composition, release, "
            "promotion, or scientific truth"
        ),
        "wheel": wheel.name,
        "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "fresh_environment": True,
        "isolated_children": True,
        "cross_platform_matrix_proved": False,
        "installer_verification_only": True,
        "runtime_never_installs_dependencies": True,
        "dependency_resolution_mode": install_mode,
        "wheelhouse_supplied": wheelhouse is not None,
        "checks": checks,
        "reason": reason,
        "state": "READY" if passed else "FAILED",
        "promotion_allowed": False,
    }


def _write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="fresh-install verification for the portable ConstraintBox core"
    )
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="resolve only from the explicitly supplied wheelhouse",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        receipt = verify_wheel(
            discover_wheel(args.wheel),
            timeout=args.timeout,
            wheelhouse=args.wheelhouse,
            offline=args.offline,
        )
    except VerificationError as exc:
        receipt = {
            "schema": "constraintbox.wheel-smoke.v2",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "verification_scope": _VERIFICATION_SCOPE,
            "full_constraintbox_product_verified": False,
            "verified_lean_core_operations": list(_LEAN_CORE_OPERATION_IDS),
            "excluded_product_surfaces": list(_EXCLUDED_PRODUCT_SURFACES),
            "claim_ceiling": (
                "installer verification could not start; it is not a full "
                "ConstraintBox product verification"
            ),
            "fresh_environment": False,
            "installer_verification_only": True,
            "runtime_never_installs_dependencies": True,
            "checks": [],
            "reason": "verifier_configuration_error",
            "error": str(exc),
            "state": "FAILED",
            "promotion_allowed": False,
        }
    _write_receipt(args.receipt, receipt)
    if receipt["state"] != "READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
