"""Portable, controller-owned runtime selection for external sim workloads.

The external simulation estate is deliberately not part of the ConstraintBox
kernel.  It still needs a deterministic deployment contract, though: a worker
must run under the interpreter selected by the controller process, satisfy a
bounded runtime profile, and leave an auditable observation in its receipt.

This module therefore does *not* bless an arbitrary executable supplied by an
LLM, request, or CLI flag.  Python is always the interpreter that launched the
controller.  Julia is discovered once from the operator's ``PATH`` and then
version-checked before the same executable is used for the worker.  Paths and
binary digests are receipt observations rather than policy inputs, so a normal
install is not tied to one machine, venv, Homebrew cellar, or patch release.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNTIME_PROFILE_SCHEMA = "constraintbox.external-runtime-profile.v1"
_JULIA_VERSION = re.compile(r"^julia version (\d+)\.(\d+)\.(\d+)(?:\D.*)?$")


@dataclass(frozen=True)
class ExternalRuntimeProfile:
    """A bounded deployment contract, never a machine-specific attestation."""

    profile_id: str
    family: str
    executable_selection: str
    implementation: str
    minimum_version: tuple[int, int, int]
    maximum_exclusive_version: tuple[int, int, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RUNTIME_PROFILE_SCHEMA,
            "profile_id": self.profile_id,
            "family": self.family,
            "executable_selection": self.executable_selection,
            "implementation": self.implementation,
            "minimum_version": ".".join(map(str, self.minimum_version)),
            "maximum_exclusive_version": ".".join(
                map(str, self.maximum_exclusive_version)
            ),
            "artifact_sha256_is_policy_input": False,
        }


EXTERNAL_RUNTIME_PROFILES: dict[str, ExternalRuntimeProfile] = {
    "python": ExternalRuntimeProfile(
        profile_id="external-cpython-3.11-3.13-v1",
        family="python",
        executable_selection="controller_process",
        implementation="CPython",
        minimum_version=(3, 11, 0),
        maximum_exclusive_version=(3, 14, 0),
    ),
    "julia": ExternalRuntimeProfile(
        profile_id="external-julia-1.12-v1",
        family="julia",
        executable_selection="operator_path_lookup",
        implementation="Julia",
        minimum_version=(1, 12, 0),
        maximum_exclusive_version=(1, 13, 0),
    ),
}


def runtime_profile_dict(family: str) -> dict[str, object]:
    """Return the controller-owned portable profile for an external family."""

    try:
        return EXTERNAL_RUNTIME_PROFILES[family].to_dict()
    except KeyError as exc:
        raise ValueError(f"unknown external runtime family: {family}") from exc


def selected_runtime_executable(family: str) -> Path | None:
    """Select a runtime without accepting a request/LLM executable override."""

    if family == "python":
        return Path(sys.executable).absolute()
    if family == "julia":
        candidate = shutil.which("julia")
        return Path(candidate).absolute() if candidate else None
    raise ValueError(f"unknown external runtime family: {family}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _version_in_profile(
    value: tuple[int, int, int], profile: ExternalRuntimeProfile
) -> bool:
    return profile.minimum_version <= value < profile.maximum_exclusive_version


def _julia_version(executable: Path) -> tuple[tuple[int, int, int] | None, str | None]:
    """Ask the candidate that will be executed; never infer Julia from a path."""

    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            [str(executable), "--startup-file=no", "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(timeout=10.0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        if process is not None:
            process.kill()
            process.communicate()
        return None, f"{type(exc).__name__}: {exc}"
    text = (stdout + stderr).decode("utf-8", errors="replace").strip()
    match = _JULIA_VERSION.fullmatch(text)
    if process.returncode != 0 or match is None:
        return None, f"unparseable_julia_version:{text[:256]}"
    return tuple(int(match.group(index)) for index in (1, 2, 3)), None


def inspect_external_runtime(
    family: str,
    executable: Path | None = None,
    *,
    explicit_override: bool = False,
) -> dict[str, Any]:
    """Inspect one controller-selected runtime against a portable profile.

    ``explicit_override`` is intentionally a failure condition when it differs
    from the controller's selected executable.  It makes injected alternate
    runtimes visible in a receipt instead of silently switching the gate.
    """

    profile = EXTERNAL_RUNTIME_PROFILES[family]
    selected = selected_runtime_executable(family)
    observed = executable if executable is not None else selected
    result: dict[str, Any] = {
        "runtime_pin": runtime_profile_dict(family),
        "executable_path": str(observed) if observed is not None else None,
    }
    if selected is None:
        return result | {
            "eligible": False,
            "disposition": "PARKED",
            "reason": "runtime_executable_unavailable",
        }
    if observed is None:
        return result | {
            "eligible": False,
            "disposition": "PARKED",
            "reason": "runtime_executable_unavailable",
        }

    # Use absolute paths rather than resolve() for the selection comparison.
    # A venv launcher is the selected Python even when its realpath is the base
    # interpreter; resolve() would accidentally erase the venv context.
    selected_absolute = selected.absolute()
    observed_absolute = observed.absolute()
    if explicit_override and observed_absolute != selected_absolute:
        return result | {
            "controller_selected_executable": str(selected_absolute),
            "eligible": False,
            "disposition": "FAIL",
            "reason": "runtime_selection_override_rejected",
        }
    if observed_absolute != selected_absolute:
        return result | {
            "controller_selected_executable": str(selected_absolute),
            "eligible": False,
            "disposition": "FAIL",
            "reason": "runtime_selection_mismatch",
        }
    if not observed_absolute.is_file():
        return result | {
            "eligible": False,
            "disposition": "PARKED",
            "reason": "runtime_executable_unavailable",
        }
    try:
        resolved = observed_absolute.resolve(strict=True)
        digest = _sha256_file(resolved)
    except OSError as exc:
        return result | {
            "eligible": False,
            "disposition": "PARKED",
            "reason": "runtime_executable_unavailable",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    result.update(
        {
            "executable_path": str(observed_absolute),
            "executable_resolved_path": str(resolved),
            "executable_sha256": digest,
            "executable_sha256_is_policy_input": False,
        }
    )

    if family == "python":
        version = tuple(sys.version_info[:3])
        implementation = platform.python_implementation()
        result.update(
            {
                "runtime_version": ".".join(map(str, version)),
                "runtime_implementation": implementation,
            }
        )
        if implementation != profile.implementation:
            return result | {
                "eligible": False,
                "disposition": "PARKED",
                "reason": "runtime_implementation_unsupported",
            }
    else:
        version, detail = _julia_version(observed_absolute)
        if version is None:
            return result | {
                "eligible": False,
                "disposition": "PARKED",
                "reason": "runtime_version_unavailable",
                "detail": detail,
            }
        result.update(
            {
                "runtime_version": ".".join(map(str, version)),
                "runtime_implementation": profile.implementation,
            }
        )
    if not _version_in_profile(version, profile):
        return result | {
            "eligible": False,
            "disposition": "PARKED",
            "reason": "runtime_version_unsupported",
        }
    return result | {
        "eligible": True,
        "disposition": "PASS",
        "reason": "runtime_profile_matched",
    }


def _parse_release(value: str) -> tuple[int, int, int] | None:
    """Parse the numeric front of a package version without normalizing it."""

    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:\D.*)?$", value)
    if match is None:
        return None
    return tuple(int(match.group(index)) for index in (1, 2, 3))


def inspect_python_distributions(
    requirements: tuple[tuple[str, tuple[str, ...], tuple[int, int, int], tuple[int, int, int]], ...],
) -> dict[str, Any]:
    """Check distribution ownership and a bounded version window.

    The caller owns the requirement tuple.  Distribution files and hashes are
    retained as observations only; success comes from a compatible version,
    the expected import surfaces resolving inside that distribution, and the
    later controller-recomputed operation.
    """

    rows: list[dict[str, Any]] = []
    status = "PASS"
    reason = "python_distributions_match_runtime_profile"
    for distribution_name, modules, minimum, maximum in requirements:
        row: dict[str, Any] = {
            "distribution": distribution_name,
            "required_version_window": {
                "minimum_inclusive": ".".join(map(str, minimum)),
                "maximum_exclusive": ".".join(map(str, maximum)),
            },
            "module_origins": [],
            "artifact_sha256_is_policy_input": False,
        }
        try:
            distribution = importlib.metadata.distribution(distribution_name)
            version = distribution.version
        except importlib.metadata.PackageNotFoundError:
            row.update({"observed": False, "reason": "distribution_unavailable"})
            status = "PARKED"
            reason = "python_distribution_unavailable"
            rows.append(row)
            continue
        parsed = _parse_release(version)
        row.update({"observed": True, "version": version})
        if parsed is None or not (minimum <= parsed < maximum):
            row["reason"] = "distribution_version_unsupported"
            status = "PARKED"
            reason = "python_distribution_version_unsupported"
            rows.append(row)
            continue
        module_failure = False
        for module in modules:
            spec = importlib.util.find_spec(module)
            origin = spec.origin if spec is not None else None
            module_row: dict[str, Any] = {"module": module, "origin": origin}
            if origin is None or origin in {"built-in", "frozen"}:
                module_row["matches_distribution"] = False
                module_row["reason"] = "module_origin_unavailable"
                module_failure = True
            else:
                origin_path = Path(origin)
                try:
                    origin_resolved = origin_path.resolve(strict=True)
                    package_relative = Path(*module.split(".")) / "__init__.py"
                    expected = Path(distribution.locate_file(package_relative)).resolve(
                        strict=True
                    )
                    module_row.update(
                        {
                            "resolved_origin": str(origin_resolved),
                            "sha256": _sha256_file(origin_resolved),
                            "matches_distribution": origin_resolved == expected,
                        }
                    )
                    if origin_resolved != expected:
                        module_failure = True
                except OSError as exc:
                    module_row.update(
                        {
                            "matches_distribution": False,
                            "reason": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    module_failure = True
            row["module_origins"].append(module_row)
        if module_failure:
            row["reason"] = "module_origin_distribution_mismatch"
            status = "FAIL"
            reason = "python_distribution_origin_mismatch"
        else:
            row["reason"] = "distribution_profile_matched"
        rows.append(row)
    return {"status": status, "reason": reason, "artifacts": rows}
