#!/usr/bin/env python3
"""Verify the bounded Pydantic control-plane profile from a fresh wheel.

This is an installer verifier, not a ConstraintBox runtime command.  It
creates a temporary environment, installs one explicitly supplied local wheel
with its ``control-plane`` extra, and exercises only refusal/severance paths
through the installed module entrypoint.  The running ConstraintBox process
never installs dependencies as a consequence of this verifier.

The receipt deliberately has a narrow claim ceiling.  In particular, exact
direct Pydantic/jsonschema pins are checked, but a full transitive hash lock,
dependency provenance, and cross-platform execution are not asserted here.
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
DEFAULT_OUTPUT = ROOT / "receipts" / "CONTROL_PLANE_FRESH_WHEEL_PROFILE.json"
_ISOLATED = "-I"
_SCOPE = "control_plane_fresh_wheel_profile"
_PROFILE_EXTRA = "control-plane"
_DIRECT_PROFILE_PACKAGES = ("pydantic", "jsonschema")
_RESULT_SCHEMA = "constraintbox.control-plane-candidate-evaluation.v1"
_ATTESTATION_SCHEMA = "constraintbox.control-plane-profile-attestation.v1"


class VerificationError(ValueError):
    """The requested clean control-plane installer boundary is malformed."""


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
    """Run one verifier-owned child and preserve a bounded failure category."""

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
        return Invocation(command, 124, _bytes(exc.stdout), _bytes(exc.stderr), "timeout")
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
    """Remove inherited Python search paths before every verifier-owned child."""

    environment = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["PIP_NO_INPUT"] = "1"
    # Do not let a user/global pip.conf inject a target, index, or installer
    # option into a receipt that claims to describe this verifier-owned child.
    # ``os.devnull`` is the portable platform null device.
    environment["PIP_CONFIG_FILE"] = os.devnull
    return environment


def _venv_python(root: Path) -> Path:
    return root / "Scripts" / "python.exe" if os.name == "nt" else root / "bin" / "python"


def _json_object(raw: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _lookup(value: dict[str, Any] | None, dotted_path: str) -> object:
    """Read a dotted field while allowing keys such as ``pydantic-core``."""

    current: object = value
    parts = dotted_path.split(".")
    position = 0
    while position < len(parts):
        if not isinstance(current, dict):
            return None
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


def _failure_reason(invocation: Invocation) -> str | None:
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


def _check(
    *,
    name: str,
    invocation: Invocation,
    expected_exit: int = 0,
    expected_json: dict[str, object] | None = None,
    retain_body: bool = False,
) -> dict[str, object]:
    body = _json_object(invocation.stdout)
    expected = expected_json or {}
    observed = {key: _lookup(body, key) for key in sorted(expected)}
    json_matches = all(observed[key] == value for key, value in expected.items())
    result: dict[str, object] = {
        "name": name,
        "passed": (
            invocation.failure_kind is None
            and invocation.returncode == expected_exit
            and json_matches
        ),
        "expected_exit": expected_exit,
        "exit": invocation.returncode,
        "expected_json": expected,
        "observed_json": observed,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }
    if retain_body:
        result["attestation"] = body
    return result


def _process_check(*, name: str, invocation: Invocation) -> dict[str, object]:
    return {
        "name": name,
        "passed": invocation.failure_kind is None and invocation.returncode == 0,
        "expected_exit": 0,
        "exit": invocation.returncode,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _skipped_check(name: str, reason: str) -> dict[str, object]:
    return {"name": name, "passed": False, "state": "SKIPPED", "reason": reason}


def _local_check(name: str, passed: bool, **details: object) -> dict[str, object]:
    return {"name": name, "passed": passed, **details}


def install_argv(
    python: Path,
    wheel: Path,
    *,
    wheelhouse: Path | None,
    offline: bool,
) -> list[str]:
    """Build a dependency-resolving local-wheel install for this exact profile."""

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
    # PEP 508 direct-reference syntax makes the requested optional profile
    # explicit; a plain wheel path could install only the base dependency set.
    command.append(f"constraintbox[{_PROFILE_EXTRA}] @ {wheel.as_uri()}")
    return command


_PROFILE_ATTESTATION_PROGRAM = r"""
import json
import sys
from importlib import metadata
from pathlib import Path

import constraintbox
import hookkernel
import jsonschema
import pydantic
from hookkernel.cb_light_domain import DATA_ROOT

source_root = Path(sys.argv[1]).resolve()
environment_root = Path(sys.prefix).resolve()
packages = {
    "constraintbox": constraintbox,
    "hookkernel": hookkernel,
    "pydantic": pydantic,
    "jsonschema": jsonschema,
}

def under(path, root):
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True

origins = {}
for name, module in packages.items():
    location = getattr(module, "__file__", None)
    origins[name] = str(Path(location).resolve()) if location else None

pin_file = (
    DATA_ROOT
    / "requirements"
    / "control_plane_candidates"
    / "cb_control_plane_candidate_pins_v1.txt"
).resolve()
pins = {}
pin_error = None
try:
    for raw in pin_file.read_text(encoding="utf-8").splitlines():
        requirement = raw.split("#", 1)[0].strip()
        if not requirement:
            continue
        if requirement.count("==") != 1:
            raise ValueError("not_exact")
        name, value = (part.strip() for part in requirement.split("==", 1))
        normalized = name.casefold().replace("_", "-")
        if not normalized or not value or normalized in pins:
            raise ValueError("invalid_or_duplicate")
        pins[normalized] = value
except (OSError, ValueError) as exc:
    pin_error = type(exc).__name__

direct = ("pydantic", "jsonschema")
observed_versions = {}
for name in direct:
    try:
        observed_versions[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        observed_versions[name] = None

requires = metadata.requires("constraintbox") or []
normalized_requires = [item.replace(" ", "").casefold() for item in requires]
direct_metadata_matches = {}
for name in direct:
    expected = pins.get(name)
    prefix = f"{name}=={expected};" if expected else ""
    direct_metadata_matches[name] = any(
        item.startswith(prefix)
        and ("extra==\"control-plane\"" in item or "extra=='control-plane'" in item)
        for item in normalized_requires
    )

origin_values = [Path(value) for value in origins.values() if value]
all_inside_environment = bool(origin_values) and all(
    under(path, environment_root) for path in origin_values
)
no_source_tree_origin = all(not under(path, source_root) for path in origin_values)
pin_file_inside_environment = under(pin_file, environment_root)
direct_pin_versions_match = all(
    pins.get(name) is not None and observed_versions[name] == pins[name]
    for name in direct
)
metadata_matches = all(direct_metadata_matches.values())
profile_ready = (
    pin_error is None
    and all(name in pins for name in direct)
    and direct_pin_versions_match
    and metadata_matches
    and all_inside_environment
    and no_source_tree_origin
    and pin_file_inside_environment
)

print(json.dumps({
    "schema": "constraintbox.control-plane-profile-attestation.v1",
    "environment_root": str(environment_root),
    "module_origins": origins,
    "pin_file": str(pin_file),
    "direct_pins": {name: pins.get(name) for name in direct},
    "observed_direct_versions": observed_versions,
    "direct_metadata_matches": metadata_matches,
    "direct_metadata_by_package": direct_metadata_matches,
    "direct_pin_versions_match": direct_pin_versions_match,
    "origin_checks": {
        "all_profile_imports_inside_fresh_environment": all_inside_environment,
        "no_source_tree_origin": no_source_tree_origin,
        "pin_file_inside_fresh_environment": pin_file_inside_environment,
    },
    "pin_error": pin_error,
    "profile_ready": profile_ready,
}, sort_keys=True))
"""


def _invalid_request(*, request_id: str, capabilities: list[str]) -> dict[str, object]:
    return {
        "schema": "constraintbox.control-plane-request.v1",
        "request_id": request_id,
        "operation": "candidate_evaluation",
        "candidate_id": "pydantic",
        "snapshot_id": "0" * 64,
        "probe_run_id": "1" * 64,
        "selection_id": "2" * 64,
        # This intentionally cannot bind to a real candidate pin.  It keeps
        # the installed CLI at a deterministic pre-SQLite refusal boundary.
        "candidate_pin_sha256": "f" * 64,
        "capabilities": capabilities,
    }


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _control_plane_checks(
    *,
    python: Path,
    scratch: Path,
    timeout: float,
    env: dict[str, str],
) -> list[dict[str, object]]:
    """Exercise installed no-extra and severance routes without a Light state."""

    database = scratch / "refusal-does-not-open.sqlite"
    extra_field_request = scratch / "extra-field-refusal.json"
    capability_request = scratch / "undeclared-capability-refusal.json"
    pin_request = scratch / "candidate-pin-severance.json"

    extra_field = _invalid_request(
        request_id="profile-extra-field", capabilities=["schema_envelope"]
    )
    extra_field["unexpected"] = True
    _write_json(extra_field_request, extra_field)
    _write_json(
        capability_request,
        _invalid_request(
            request_id="profile-capability", capabilities=["provider_launch"]
        ),
    )
    _write_json(
        pin_request,
        _invalid_request(
            request_id="profile-pin-severance", capabilities=["schema_envelope"]
        ),
    )

    def cli_argv(request: Path) -> list[str]:
        return [
            str(python),
            _ISOLATED,
            "-m",
            "constraintbox.core_cli",
            "control-plane",
            "--request",
            str(request),
            "--db",
            str(database),
        ]

    expected_base = {
        "schema": _RESULT_SCHEMA,
        "disposition": "REFUSE",
        "promotion_allowed": False,
    }
    commands: tuple[tuple[str, Path, str], ...] = (
        ("installed_extra_field_refusal", extra_field_request, "REFUSE_UNEXPECTED_FIELD"),
        (
            "installed_undeclared_capability_refusal",
            capability_request,
            "REFUSE_UNDECLARED_CAPABILITY",
        ),
        (
            "installed_candidate_pin_severance",
            pin_request,
            "REFUSE_CANDIDATE_PIN_DIGEST_MISMATCH",
        ),
    )
    checks = [
        _check(
            name=name,
            invocation=invoke(cli_argv(request), timeout=timeout, env=env),
            expected_exit=2,
            expected_json={**expected_base, "reason_code": reason_code},
        )
        for name, request, reason_code in commands
    ]
    checks.append(
        _local_check(
            "installed_refusals_do_not_open_sqlite",
            not database.exists(),
            database_created=database.exists(),
        )
    )
    return checks


def verify_control_plane_profile(
    wheel: Path,
    *,
    timeout: float = 120.0,
    wheelhouse: Path | None = None,
    offline: bool = False,
    source_root: Path = ROOT,
) -> dict[str, object]:
    """Verify one clean, local control-plane wheel install and return a receipt."""

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
    source_root = source_root.expanduser().resolve()
    if not source_root.is_dir():
        raise VerificationError(f"source root is not a directory: {source_root}")

    checks: list[dict[str, object]] = []
    environment = _fresh_environment()
    install_mode = (
        "offline_wheelhouse_dependency_resolution"
        if offline
        else "normal_dependency_resolution"
    )
    later_checks = (
        "profile_pip_dependency_check",
        "installed_profile_direct_pin_attestation",
        "installed_extra_field_refusal",
        "installed_undeclared_capability_refusal",
        "installed_candidate_pin_severance",
        "installed_refusals_do_not_open_sqlite",
    )
    with tempfile.TemporaryDirectory(prefix="constraintbox-control-plane-") as directory:
        root = Path(directory)
        create = _process_check(
            name="fresh_profile_venv_create",
            invocation=invoke(
                [sys.executable, _ISOLATED, "-m", "venv", str(root)],
                timeout=timeout,
                env=environment,
            ),
        )
        checks.append(create)
        python = _venv_python(root)
        if not create["passed"] or not python.is_file():
            checks.extend(_skipped_check(name, "fresh_venv_unavailable") for name in later_checks)
            reason = "fresh_venv_creation_failed"
        else:
            install = _process_check(
                name="control_plane_extra_dependency_resolved_install",
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
                    for name in later_checks
                )
                reason = "dependency_resolution_or_wheel_install_failed"
            else:
                dependency_check = _process_check(
                    name="profile_pip_dependency_check",
                    invocation=invoke(
                        [str(python), _ISOLATED, "-m", "pip", "check"],
                        timeout=timeout,
                        env=environment,
                    ),
                )
                checks.append(dependency_check)
                if not dependency_check["passed"]:
                    checks.extend(
                        _skipped_check(name, "installed_dependency_check_failed")
                        for name in later_checks[1:]
                    )
                    reason = "installed_dependency_check_failed"
                else:
                    attestation = _check(
                        name="installed_profile_direct_pin_attestation",
                        invocation=invoke(
                            [
                                str(python),
                                _ISOLATED,
                                "-c",
                                _PROFILE_ATTESTATION_PROGRAM,
                                str(source_root),
                            ],
                            timeout=timeout,
                            env=environment,
                        ),
                        expected_json={
                            "schema": _ATTESTATION_SCHEMA,
                            "profile_ready": True,
                            "direct_pin_versions_match": True,
                            "direct_metadata_matches": True,
                            "origin_checks.all_profile_imports_inside_fresh_environment": True,
                            "origin_checks.no_source_tree_origin": True,
                            "origin_checks.pin_file_inside_fresh_environment": True,
                        },
                        retain_body=True,
                    )
                    checks.append(attestation)
                    if not attestation["passed"]:
                        checks.extend(
                            _skipped_check(name, "direct_pin_or_origin_attestation_failed")
                            for name in later_checks[2:]
                        )
                        reason = "direct_pin_or_origin_attestation_failed"
                    else:
                        checks.extend(
                            _control_plane_checks(
                                python=python,
                                scratch=root,
                                timeout=timeout,
                                env=environment,
                            )
                        )
                        reason = (
                            "clean_control_plane_profile_passed"
                            if all(check.get("passed") is True for check in checks)
                            else "clean_control_plane_profile_failed"
                        )

    passed = all(check.get("passed") is True for check in checks)
    return {
        "schema": "constraintbox.control-plane-fresh-wheel-profile.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verification_scope": _SCOPE,
        "state": "READY" if passed else "FAILED",
        "reason": reason,
        "wheel": wheel.name,
        "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "wheel_requested_extra": _PROFILE_EXTRA,
        "direct_profile_packages": list(_DIRECT_PROFILE_PACKAGES),
        "fresh_environment": True,
        "source_tree_environment_variables_scrubbed": True,
        "isolated_children": True,
        "installer_verification_only": True,
        "runtime_never_installs_dependencies": True,
        "dependency_resolution_mode": install_mode,
        "wheelhouse_supplied": wheelhouse is not None,
        "local_host_only": True,
        "direct_pins_only": True,
        "full_transitive_hash_lock_verified": False,
        "dependency_provenance_verified": False,
        "cross_platform_matrix_proved": False,
        "membership_or_adoption_proved": False,
        "provider_execution_proved": False,
        "cb_heavy_proved": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "Local-only fresh-wheel installer verification on this host: the "
            "installed control-plane profile exposed the direct pydantic and "
            "jsonschema pins, imported outside this source tree, and refused "
            "bounded no-extra/severance requests. This is not a full "
            "transitive hash lock, dependency-provenance, macOS/Linux/Windows "
            "portability, CB Light membership/adoption, provider execution, "
            "CB Heavy, release, promotion, or scientific-truth claim."
        ),
        "checks": checks,
    }


def _write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="fresh-wheel installer verification for the bounded control-plane profile"
    )
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="resolve only from the explicitly supplied wheelhouse",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT,
        help="source tree that no installed profile import may originate from",
    )
    return parser


def _configuration_failure_receipt(error: str) -> dict[str, object]:
    return {
        "schema": "constraintbox.control-plane-fresh-wheel-profile.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verification_scope": _SCOPE,
        "state": "FAILED",
        "reason": "verifier_configuration_error",
        "error": error,
        "fresh_environment": False,
        "installer_verification_only": True,
        "local_host_only": True,
        "direct_pins_only": True,
        "full_transitive_hash_lock_verified": False,
        "cross_platform_matrix_proved": False,
        "membership_or_adoption_proved": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "The local-only direct-pin installer verifier could not start; "
            "it makes no full transitive hash-lock, portability, adoption, "
            "provider, CB Heavy, release, promotion, or scientific-truth claim."
        ),
        "checks": [],
    }


def main() -> None:
    args = build_parser().parse_args()
    try:
        receipt = verify_control_plane_profile(
            args.wheel,
            timeout=args.timeout,
            wheelhouse=args.wheelhouse,
            offline=args.offline,
            source_root=args.source_root,
        )
    except VerificationError as exc:
        receipt = _configuration_failure_receipt(str(exc))
    _write_receipt(args.receipt, receipt)
    if receipt["state"] != "READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
