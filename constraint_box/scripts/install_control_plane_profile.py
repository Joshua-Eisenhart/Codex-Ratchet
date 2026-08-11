#!/usr/bin/env python3
"""Install one explicit, separate CB Light control-plane/wave profile.

The exact 91-tool CB Light runtime deliberately does not contain Pydantic or
JSON Schema.  This installer creates or deliberately updates a *different*
virtual environment from one user-supplied local ConstraintBox wheel.  It
installs the wheel's normal CB Light dependencies and then the two direct,
exact control-plane pins from the canonical pin file.

The default is offline and fail-closed: callers must supply a wheelhouse
unless they explicitly opt in to network dependency resolution.  No shell
syntax is used; all child processes receive a scrubbed environment and use
``-I``.  The receipt is intentionally local-host-only.  It is not a portable
adoption, hash-lock, provider, CB Heavy, promotion, or release claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PINS = (
    ROOT
    / "requirements"
    / "control_plane_candidates"
    / "cb_control_plane_candidate_pins_v1.txt"
)
DEFAULT_RECEIPT = ROOT / "receipts" / "CONTROL_PLANE_PROFILE_INSTALL.json"
_ISOLATED = "-I"
_REQUIRED_PIN_NAMES = ("pydantic", "jsonschema")
_TEST_ONLY_CANDIDATE_PIN_NAMES = ("hypothesis",)
_CANONICAL_PIN_NAMES = _REQUIRED_PIN_NAMES + _TEST_ONLY_CANDIDATE_PIN_NAMES
_CORE_PROFILE_PATHS = (ROOT / ".venv", ROOT / ".venv-clean")


class InstallError(ValueError):
    """The requested persistent control-plane profile is unsafe or incomplete."""


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
    argv: Iterable[str], *, timeout: float, env: dict[str, str]
) -> Invocation:
    """Run one installer-owned child and preserve a bounded failure category."""

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


def scrubbed_environment() -> dict[str, str]:
    """Remove inherited Python and pip configuration from every child process."""

    environment = dict(os.environ)
    for name in tuple(environment):
        if name in {"PYTHONHOME", "PYTHONPATH", "PYTHONUSERBASE", "VIRTUAL_ENV"}:
            environment.pop(name, None)
        elif name.startswith("PIP_"):
            environment.pop(name, None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["PIP_NO_INPUT"] = "1"
    # ``os.devnull`` is portable.  It prevents global/user pip.conf from
    # injecting a target, index, or installer option into this receipt.
    environment["PIP_CONFIG_FILE"] = os.devnull
    return environment


def profile_python(profile: Path) -> Path:
    """Return the venv interpreter path without assuming a POSIX shell layout."""

    return profile / "Scripts" / "python.exe" if os.name == "nt" else profile / "bin" / "python"


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


def _process_check(name: str, invocation: Invocation) -> dict[str, object]:
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


def _json_object(raw: bytes) -> dict[str, object] | None:
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _attestation_check(invocation: Invocation) -> dict[str, object]:
    body = _json_object(invocation.stdout)
    expected = {
        "schema": "constraintbox.control-plane-profile-install-attestation.v1",
        "profile_ready": True,
        "direct_pin_versions_match": True,
        "packaged_profile_pins_match": True,
        "test_only_candidates.declared": True,
        "test_only_candidates.not_installed": True,
        "wheel_metadata_direct_pins_match": True,
        "origin_checks.all_imports_inside_explicit_profile": True,
        "origin_checks.no_source_package_origin": True,
        "origin_checks.pin_file_inside_explicit_profile": True,
    }
    observed: dict[str, object] = {}
    for dotted, expected_value in expected.items():
        current: object = body
        for part in dotted.split("."):
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(part)
        observed[dotted] = current
    return {
        "name": "installed_profile_attestation",
        "passed": (
            invocation.failure_kind is None
            and invocation.returncode == 0
            and all(observed[key] == value for key, value in expected.items())
        ),
        "expected_exit": 0,
        "exit": invocation.returncode,
        "expected_json": expected,
        "observed_json": observed,
        "attestation": body,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _wave_help_check(invocation: Invocation) -> dict[str, object]:
    output = invocation.stdout.decode("utf-8", "replace")
    return {
        "name": "installed_wave_command_available",
        "passed": (
            invocation.failure_kind is None
            and invocation.returncode == 0
            and "wave" in output
        ),
        "expected_exit": 0,
        "exit": invocation.returncode,
        "wave_listed_in_help": "wave" in output,
        "stdout_sha256": hashlib.sha256(invocation.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(invocation.stderr).hexdigest(),
        "failure_kind": invocation.failure_kind,
        "failure_reason": _failure_reason(invocation),
    }


def _skipped(name: str, reason: str) -> dict[str, object]:
    return {"name": name, "passed": False, "state": "SKIPPED", "reason": reason}


def _skipped_checks(names: Iterable[str], reason: str) -> list[dict[str, object]]:
    """Materialize one finite skip set so a failure receipt cannot duplicate it."""

    return [_skipped(name, reason) for name in names]


def read_control_plane_candidate_pins(pin_file: Path) -> dict[str, str]:
    """Parse the canonical exact candidate pins without admitting all of them."""

    pin_file = pin_file.expanduser().resolve()
    if not pin_file.is_file():
        raise InstallError(f"control-plane pin file does not exist: {pin_file}")
    pins: dict[str, str] = {}
    try:
        lines = pin_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InstallError(f"cannot read control-plane pin file: {pin_file}") from exc
    for raw in lines:
        requirement = raw.split("#", 1)[0].strip()
        if not requirement:
            continue
        if requirement.count("==") != 1:
            raise InstallError("control-plane pin file must use exact == pins only")
        name, version = (part.strip() for part in requirement.split("==", 1))
        normalized = name.casefold().replace("_", "-")
        if (
            normalized not in _CANONICAL_PIN_NAMES
            or not version
            or normalized in pins
        ):
            raise InstallError(
                "control-plane pin file must contain each canonical candidate pin "
                "exactly once and no other requirement"
            )
        pins[normalized] = version
    if tuple(sorted(pins)) != tuple(sorted(_CANONICAL_PIN_NAMES)):
        raise InstallError(
            "control-plane pin file must contain exactly pydantic, jsonschema, and "
            "the test-only hypothesis candidate"
        )
    return {name: pins[name] for name in _CANONICAL_PIN_NAMES}


def read_direct_pins(pin_file: Path) -> dict[str, str]:
    """Return only the two direct runtime pins from the canonical candidate file."""

    candidates = read_control_plane_candidate_pins(pin_file)
    return {name: candidates[name] for name in _REQUIRED_PIN_NAMES}


def read_test_only_candidate_pins(pin_file: Path) -> dict[str, str]:
    """Return declared test-only candidates which this profile must not install."""

    candidates = read_control_plane_candidate_pins(pin_file)
    return {name: candidates[name] for name in _TEST_ONLY_CANDIDATE_PIN_NAMES}


def _resolver_options(*, wheelhouse: Path | None, allow_network: bool) -> list[str]:
    options: list[str] = []
    if wheelhouse is not None:
        options.extend(("--find-links", str(wheelhouse)))
    if not allow_network:
        options.append("--no-index")
    return options


def _pip_install_prefix(python: Path) -> list[str]:
    """Build exactly one isolated ``python -m pip install`` command prefix."""

    return [
        str(python),
        _ISOLATED,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--upgrade",
        "--force-reinstall",
    ]


def base_wheel_install_argv(
    python: Path, wheel: Path, *, wheelhouse: Path | None, allow_network: bool
) -> list[str]:
    """Install the local Light wheel and its declared base dependencies."""

    return [
        *_pip_install_prefix(python),
        *_resolver_options(wheelhouse=wheelhouse, allow_network=allow_network),
        str(wheel),
    ]


def direct_pin_install_argv(
    python: Path,
    pins: dict[str, str],
    *,
    wheelhouse: Path | None,
    allow_network: bool,
) -> list[str]:
    """Install Pydantic and JSON Schema as explicit exact direct requirements."""

    return [
        *_pip_install_prefix(python),
        *_resolver_options(wheelhouse=wheelhouse, allow_network=allow_network),
        *(f"{name}=={pins[name]}" for name in _REQUIRED_PIN_NAMES),
    ]


_ATTESTATION_PROGRAM = r"""
import json
import sys
from importlib import metadata
from pathlib import Path

import constraintbox
import hookkernel
import jsonschema
import pydantic
from hookkernel.cb_light_domain import DATA_ROOT

profile = Path(sys.argv[1]).resolve()
source_root = Path(sys.argv[2]).resolve()
expected = json.loads(sys.argv[3])
expected_pins = expected["profile_pins"]
expected_test_only_pins = expected["test_only_candidate_pins"]

def under(path, root):
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True

modules = {
    "constraintbox": constraintbox,
    "hookkernel": hookkernel,
    "pydantic": pydantic,
    "jsonschema": jsonschema,
}
origins = {}
for name, module in modules.items():
    location = getattr(module, "__file__", None)
    origins[name] = str(Path(location).resolve()) if location else None
origin_paths = [Path(location) for location in origins.values() if location]

pin_file = (
    DATA_ROOT
    / "requirements"
    / "control_plane_candidates"
    / "cb_control_plane_candidate_pins_v1.txt"
).resolve()
packaged_pins = {}
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
        if normalized in packaged_pins or not normalized or not value:
            raise ValueError("invalid_or_duplicate")
        packaged_pins[normalized] = value
except (OSError, ValueError) as exc:
    pin_error = type(exc).__name__

observed_versions = {}
for name in ("pydantic", "jsonschema"):
    try:
        observed_versions[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        observed_versions[name] = None

observed_test_only_versions = {}
for name in expected_test_only_pins:
    try:
        observed_test_only_versions[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        observed_test_only_versions[name] = None

requires = metadata.requires("constraintbox") or []
# Packaging metadata may render an optional marker with or without enclosing
# parentheses.  The comparison below concerns only the exact requirement and
# extra marker, so normalize either PEP 566 presentation before matching.
normalized_requires = [
    item.replace(" ", "").replace("(", "").replace(")", "").casefold()
    for item in requires
]
metadata_matches = {}
for name, version in expected_pins.items():
    prefix = f"{name}=={version};"
    metadata_matches[name] = any(
        item.startswith(prefix)
        and ("extra==\"control-plane\"" in item or "extra=='control-plane'" in item)
        for item in normalized_requires
    )

source_package_roots = [
    source_root / "light_runtime" / "src",
    source_root / "src",
]
all_inside_profile = bool(origin_paths) and all(under(path, profile) for path in origin_paths)
no_source_package_origin = all(
    not any(under(path, candidate) for candidate in source_package_roots)
    for path in origin_paths
)
pin_file_inside_profile = under(pin_file, profile)
direct_versions_match = all(
    observed_versions.get(name) == version for name, version in expected_pins.items()
)
packaged_profile_pins_match = pin_error is None and all(
    packaged_pins.get(name) == version for name, version in expected_pins.items()
)
test_only_candidate_declared = pin_error is None and all(
    packaged_pins.get(name) == version
    for name, version in expected_test_only_pins.items()
)
test_only_candidates_not_installed = all(
    observed_test_only_versions.get(name) is None
    for name in expected_test_only_pins
)
wheel_metadata_matches = all(metadata_matches.values())
profile_ready = (
    direct_versions_match
    and packaged_profile_pins_match
    and test_only_candidate_declared
    and test_only_candidates_not_installed
    and wheel_metadata_matches
    and all_inside_profile
    and no_source_package_origin
    and pin_file_inside_profile
)

print(json.dumps({
    "schema": "constraintbox.control-plane-profile-install-attestation.v1",
    "profile": str(profile),
    "module_origins": origins,
    "pin_file": str(pin_file),
    "expected_direct_pins": expected_pins,
    "expected_test_only_candidate_pins": expected_test_only_pins,
    "packaged_profile_pins": {name: packaged_pins.get(name) for name in expected_pins},
    "packaged_test_only_candidate_pins": {
        name: packaged_pins.get(name) for name in expected_test_only_pins
    },
    "observed_direct_versions": observed_versions,
    "observed_test_only_candidate_versions": observed_test_only_versions,
    "direct_pin_versions_match": direct_versions_match,
    "packaged_profile_pins_match": packaged_profile_pins_match,
    "test_only_candidates": {
        "declared": test_only_candidate_declared,
        "not_installed": test_only_candidates_not_installed,
    },
    "wheel_metadata_direct_pins_match": wheel_metadata_matches,
    "wheel_metadata_by_package": metadata_matches,
    "origin_checks": {
        "all_imports_inside_explicit_profile": all_inside_profile,
        "no_source_package_origin": no_source_package_origin,
        "pin_file_inside_explicit_profile": pin_file_inside_profile,
    },
    "pin_error": pin_error,
    "profile_ready": profile_ready,
}, sort_keys=True))
"""


def _validate_inputs(
    wheel: Path,
    profile: Path,
    *,
    wheelhouse: Path | None,
    allow_network: bool,
    update_existing: bool,
    pins: Path,
) -> tuple[Path, Path, Path | None, dict[str, str], dict[str, str], bool]:
    wheel = wheel.expanduser().resolve()
    profile = profile.expanduser().resolve()
    pins = pins.expanduser().resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise InstallError(f"wheel does not exist or is not a wheel: {wheel}")
    if profile in {path.resolve() for path in _CORE_PROFILE_PATHS}:
        raise InstallError(
            "refusing to target the exact 91-tool CB Light runtime; choose a "
            "separate profile such as .venv-control-plane"
        )
    if profile == ROOT.resolve() or profile == Path(sys.prefix).resolve():
        raise InstallError("profile target may not be the source root or active interpreter")
    existed = profile.exists()
    if existed:
        if not profile.is_dir() or not (profile / "pyvenv.cfg").is_file():
            raise InstallError("existing profile target is not a Python virtual environment")
        if not update_existing:
            raise InstallError("profile already exists; pass --update-existing to modify it")
    if wheelhouse is not None:
        wheelhouse = wheelhouse.expanduser().resolve()
        if not wheelhouse.is_dir():
            raise InstallError(f"wheelhouse is not a directory: {wheelhouse}")
    if not allow_network and wheelhouse is None:
        raise InstallError(
            "offline-by-default installation requires --wheelhouse; use "
            "--allow-network only for an explicit network resolver run"
        )
    candidate_pins = read_control_plane_candidate_pins(pins)
    direct_pins = {name: candidate_pins[name] for name in _REQUIRED_PIN_NAMES}
    test_only_pins = {
        name: candidate_pins[name] for name in _TEST_ONLY_CANDIDATE_PIN_NAMES
    }
    return wheel, profile, wheelhouse, direct_pins, test_only_pins, existed


def install_control_plane_profile(
    wheel: Path,
    profile: Path,
    *,
    pins: Path = DEFAULT_PINS,
    wheelhouse: Path | None = None,
    allow_network: bool = False,
    update_existing: bool = False,
    timeout: float = 120.0,
    source_root: Path = ROOT,
) -> dict[str, object]:
    """Install and attest one explicit Pydantic-enabled local profile."""

    if timeout <= 0:
        raise InstallError("timeout must be positive")
    (
        wheel,
        profile,
        wheelhouse,
        direct_pins,
        test_only_pins,
        profile_existed,
    ) = _validate_inputs(
        wheel,
        profile,
        wheelhouse=wheelhouse,
        allow_network=allow_network,
        update_existing=update_existing,
        pins=pins,
    )
    source_root = source_root.expanduser().resolve()
    if not source_root.is_dir():
        raise InstallError(f"source root is not a directory: {source_root}")

    checks: list[dict[str, object]] = []
    environment = scrubbed_environment()
    later_checks = (
        "base_light_wheel_install",
        "direct_control_plane_pin_install",
        "profile_pip_dependency_check",
        "installed_profile_attestation",
        "installed_wave_command_available",
    )
    if not profile_existed:
        create = _process_check(
            "profile_venv_create",
            invoke(
                [sys.executable, _ISOLATED, "-m", "venv", str(profile)],
                timeout=timeout,
                env=environment,
            ),
        )
        checks.append(create)
        if not create["passed"]:
            checks.extend(_skipped(name, "profile_venv_creation_failed") for name in later_checks)
            reason = "profile_venv_creation_failed"
            return _receipt(
                state="FAILED",
                reason=reason,
                wheel=wheel,
                profile=profile,
                direct_pins=direct_pins,
                test_only_pins=test_only_pins,
                profile_existed=profile_existed,
                allow_network=allow_network,
                wheelhouse=wheelhouse,
                checks=checks,
            )
    else:
        checks.append(
            {
                "name": "profile_venv_create",
                "passed": True,
                "state": "NOT_RUN",
                "reason": "explicit_existing_profile_update",
            }
        )

    python = profile_python(profile)
    if not python.is_file():
        checks.extend(_skipped_checks(later_checks, "profile_interpreter_missing"))
        return _receipt(
            state="FAILED",
            reason="profile_interpreter_missing",
            wheel=wheel,
            profile=profile,
            direct_pins=direct_pins,
            test_only_pins=test_only_pins,
            profile_existed=profile_existed,
            allow_network=allow_network,
            wheelhouse=wheelhouse,
            checks=checks,
        )

    base_install = _process_check(
        "base_light_wheel_install",
        invoke(
            base_wheel_install_argv(
                python, wheel, wheelhouse=wheelhouse, allow_network=allow_network
            ),
            timeout=timeout,
            env=environment,
        ),
    )
    checks.append(base_install)
    if not base_install["passed"]:
        checks.extend(
            _skipped(name, "base_light_wheel_install_failed") for name in later_checks[1:]
        )
        return _receipt(
            state="FAILED",
            reason="base_light_wheel_install_failed",
            wheel=wheel,
            profile=profile,
            direct_pins=direct_pins,
            test_only_pins=test_only_pins,
            profile_existed=profile_existed,
            allow_network=allow_network,
            wheelhouse=wheelhouse,
            checks=checks,
        )

    pin_install = _process_check(
        "direct_control_plane_pin_install",
        invoke(
            direct_pin_install_argv(
                python,
                direct_pins,
                wheelhouse=wheelhouse,
                allow_network=allow_network,
            ),
            timeout=timeout,
            env=environment,
        ),
    )
    checks.append(pin_install)
    if not pin_install["passed"]:
        checks.extend(
            _skipped(name, "direct_control_plane_pin_install_failed")
            for name in later_checks[2:]
        )
        return _receipt(
            state="FAILED",
            reason="direct_control_plane_pin_install_failed",
            wheel=wheel,
            profile=profile,
            direct_pins=direct_pins,
            test_only_pins=test_only_pins,
            profile_existed=profile_existed,
            allow_network=allow_network,
            wheelhouse=wheelhouse,
            checks=checks,
        )

    dependency_check = _process_check(
        "profile_pip_dependency_check",
        invoke(
            [str(python), _ISOLATED, "-m", "pip", "check"],
            timeout=timeout,
            env=environment,
        ),
    )
    checks.append(dependency_check)
    if not dependency_check["passed"]:
        checks.extend(
            _skipped(name, "profile_pip_dependency_check_failed") for name in later_checks[3:]
        )
        return _receipt(
            state="FAILED",
            reason="profile_pip_dependency_check_failed",
            wheel=wheel,
            profile=profile,
            direct_pins=direct_pins,
            test_only_pins=test_only_pins,
            profile_existed=profile_existed,
            allow_network=allow_network,
            wheelhouse=wheelhouse,
            checks=checks,
        )

    attestation = _attestation_check(
        invoke(
            [
                str(python),
                _ISOLATED,
                "-c",
                _ATTESTATION_PROGRAM,
                str(profile),
                str(source_root),
                json.dumps(
                    {
                        "profile_pins": direct_pins,
                        "test_only_candidate_pins": test_only_pins,
                    },
                    sort_keys=True,
                ),
            ],
            timeout=timeout,
            env=environment,
        )
    )
    checks.append(attestation)
    if not attestation["passed"]:
        checks.append(_skipped("installed_wave_command_available", "profile_attestation_failed"))
        return _receipt(
            state="FAILED",
            reason="profile_attestation_failed",
            wheel=wheel,
            profile=profile,
            direct_pins=direct_pins,
            test_only_pins=test_only_pins,
            profile_existed=profile_existed,
            allow_network=allow_network,
            wheelhouse=wheelhouse,
            checks=checks,
        )

    wave_help = _wave_help_check(
        invoke(
            [str(python), _ISOLATED, "-m", "constraintbox", "--help"],
            timeout=timeout,
            env=environment,
        )
    )
    checks.append(wave_help)
    passed = all(check.get("passed") is True for check in checks)
    return _receipt(
        state="READY" if passed else "FAILED",
        reason="persistent_control_plane_profile_installed" if passed else "wave_command_unavailable",
        wheel=wheel,
        profile=profile,
        direct_pins=direct_pins,
        test_only_pins=test_only_pins,
        profile_existed=profile_existed,
        allow_network=allow_network,
        wheelhouse=wheelhouse,
        checks=checks,
    )


def _receipt(
    *,
    state: str,
    reason: str,
    wheel: Path,
    profile: Path,
    direct_pins: dict[str, str],
    test_only_pins: dict[str, str],
    profile_existed: bool,
    allow_network: bool,
    wheelhouse: Path | None,
    checks: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema": "constraintbox.control-plane-profile-install.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "installer_scope": "explicit_separate_control_plane_wave_profile",
        "state": state,
        "reason": reason,
        "wheel": wheel.name,
        "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "profile_target": str(profile),
        "profile_existed_before": profile_existed,
        "profile_update_explicit": profile_existed,
        "direct_profile_pins": direct_pins,
        "test_only_candidate_pins_not_installed": test_only_pins,
        "dependency_resolution_mode": (
            "network_opt_in" if allow_network else "offline_explicit_wheelhouse"
        ),
        "wheelhouse_supplied": wheelhouse is not None,
        "environment_injection_scrubbed": True,
        "isolated_children": True,
        "exact_91_runtime_target_refused": True,
        "exact_91_runtime_mutated": False,
        "local_host_only": True,
        "full_transitive_hash_lock_verified": False,
        "dependency_provenance_verified": False,
        "cross_platform_design": "pathlib_and_platform_venv_interpreter_layout",
        "cross_platform_matrix_proved": False,
        "membership_or_adoption_proved": False,
        "provider_execution_proved": False,
        "cb_heavy_proved": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "This receipt records only a local, explicit persistent control-plane "
            "profile install and isolated attestation of the direct Pydantic and "
            "jsonschema pins plus the packaged wave command; Hypothesis remains a "
            "declared test-only candidate and is attested absent. It does not prove a "
            "full transitive hash lock, dependency provenance, macOS/Linux/Windows "
            "execution, 91-tool membership/adoption, provider/MMM/skill execution, "
            "CB Heavy, release, promotion, or semantic truth."
        ),
        "checks": checks,
    }


def _configuration_failure_receipt(error: str) -> dict[str, object]:
    return {
        "schema": "constraintbox.control-plane-profile-install.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "installer_scope": "explicit_separate_control_plane_wave_profile",
        "state": "FAILED",
        "reason": "installer_configuration_error",
        "error": error,
        "exact_91_runtime_mutated": False,
        "local_host_only": True,
        "cross_platform_matrix_proved": False,
        "membership_or_adoption_proved": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "The local-only separate-profile installer could not start. It makes "
            "no install, portability, adoption, provider, CB Heavy, release, "
            "promotion, or semantic-truth claim."
        ),
        "checks": [],
    }


def write_receipt(path: Path, receipt: dict[str, object]) -> None:
    """Write a receipt atomically using portable filesystem operations."""

    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="install one explicit separate CB Light control-plane/wave profile"
    )
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--pins", type=Path, default=DEFAULT_PINS)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="explicitly permit package-index resolution; default requires a wheelhouse",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="explicitly update an existing virtual environment in place; no deletion occurs",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        receipt = install_control_plane_profile(
            args.wheel,
            args.profile,
            pins=args.pins,
            wheelhouse=args.wheelhouse,
            allow_network=args.allow_network,
            update_existing=args.update_existing,
            timeout=args.timeout,
            source_root=args.source_root,
        )
    except InstallError as exc:
        receipt = _configuration_failure_receipt(str(exc))
    write_receipt(args.receipt, receipt)
    if receipt["state"] != "READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
