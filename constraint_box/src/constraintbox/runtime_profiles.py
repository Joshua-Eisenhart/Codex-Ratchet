"""Portable, controller-owned runtime compatibility profiles for ConstraintBox.

The core must bind the Python runtime it is *actually running under* without
pretending that a particular user's venv, Homebrew cellar, CPU architecture, or
site-packages path is the product.  A profile is a deterministic compatibility
contract: it names one CPython minor and the allowed core-library version
windows.  It never selects an interpreter, installs a package, or falls back to
another profile.

Receipts retain the observed local executable and distribution origins so a run
can be audited and replayed on that runtime.  Those observations are evidence,
not global policy inputs.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import platform
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .intake import IntakeError, canonical_json, parse_json_object


DEFAULT_RUNTIME_PROFILE_REGISTRY = (
    Path(__file__).resolve().parent / "runtime_profiles" / "core_profiles_v1.json"
)
_SHA256 = hashlib.sha256


class RuntimeProfileError(RuntimeError):
    """A controller-owned runtime-profile resource is malformed or unavailable."""


@dataclass(frozen=True)
class LibraryRequirement:
    distribution: str
    import_name: str
    minimum_version: str
    maximum_exclusive_version: str
    required_attributes: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeProfile:
    profile_id: str
    implementation: str
    python_minor: tuple[int, int]
    allowed_optimization_levels: tuple[int, ...]
    require_hash_randomization: bool
    libraries: tuple[LibraryRequirement, ...]
    claim_ceiling: str


@dataclass(frozen=True)
class RuntimeProfileRegistry:
    registry_sha256: str
    profiles: tuple[RuntimeProfile, ...]


def _exact_object(value: object, expected: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeProfileError(f"{where} must contain exactly {sorted(expected)}")
    return value


def _safe_identifier(value: object, where: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-_." for character in value)
    ):
        raise RuntimeProfileError(f"{where} must be a lowercase safe identifier")
    return value


def _version_tuple(value: object, where: str) -> tuple[int, ...]:
    if not isinstance(value, str) or not value:
        raise RuntimeProfileError(f"{where} must be a non-empty numeric version")
    parts = value.split(".")
    if not parts or any(not part.isascii() or not part.isdigit() for part in parts):
        raise RuntimeProfileError(f"{where} must contain dot-separated decimal parts")
    return tuple(int(part) for part in parts)


def _version_in_window(
    observed: str,
    minimum: str,
    maximum_exclusive: str,
) -> bool:
    observed_tuple = _version_tuple(observed, "observed version")
    minimum_tuple = _version_tuple(minimum, "minimum version")
    maximum_tuple = _version_tuple(maximum_exclusive, "maximum version")
    return minimum_tuple <= observed_tuple < maximum_tuple


def _parse_registry(raw: bytes, observed_sha256: str) -> RuntimeProfileRegistry:
    try:
        body = parse_json_object(raw)
    except IntakeError as exc:
        raise RuntimeProfileError(f"runtime-profile registry is invalid: {exc}") from exc
    _exact_object(body, {"schema", "profiles"}, "$")
    if body["schema"] != "constraintbox.runtime-profile-registry.v1":
        raise RuntimeProfileError("runtime-profile registry schema mismatch")
    raw_profiles = body["profiles"]
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise RuntimeProfileError("$.profiles must be a non-empty array")

    profiles: list[RuntimeProfile] = []
    seen_ids: set[str] = set()
    seen_runtime_keys: set[tuple[str, tuple[int, int]]] = set()
    for index, raw_profile in enumerate(raw_profiles):
        profile = _exact_object(
            raw_profile,
            {
                "profile_id",
                "implementation",
                "python_minor",
                "allowed_optimization_levels",
                "require_hash_randomization",
                "libraries",
                "claim_ceiling",
            },
            f"$.profiles[{index}]",
        )
        profile_id = _safe_identifier(profile["profile_id"], f"$.profiles[{index}].profile_id")
        if profile_id in seen_ids:
            raise RuntimeProfileError("$.profiles contains duplicate profile_id values")
        seen_ids.add(profile_id)
        implementation = profile["implementation"]
        if not isinstance(implementation, str) or not implementation:
            raise RuntimeProfileError(f"$.profiles[{index}].implementation must be non-empty")
        raw_minor = profile["python_minor"]
        if (
            not isinstance(raw_minor, list)
            or len(raw_minor) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in raw_minor)
        ):
            raise RuntimeProfileError(f"$.profiles[{index}].python_minor must have two non-negative integers")
        python_minor = (raw_minor[0], raw_minor[1])
        key = (implementation, python_minor)
        if key in seen_runtime_keys:
            raise RuntimeProfileError("one Python implementation/minor may have only one core profile")
        seen_runtime_keys.add(key)
        raw_optimization = profile["allowed_optimization_levels"]
        if (
            not isinstance(raw_optimization, list)
            or not raw_optimization
            or any(isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1} for value in raw_optimization)
            or len(set(raw_optimization)) != len(raw_optimization)
        ):
            raise RuntimeProfileError(f"$.profiles[{index}].allowed_optimization_levels is invalid")
        if not isinstance(profile["require_hash_randomization"], bool):
            raise RuntimeProfileError(f"$.profiles[{index}].require_hash_randomization must be boolean")
        claim_ceiling = profile["claim_ceiling"]
        if not isinstance(claim_ceiling, str) or not claim_ceiling:
            raise RuntimeProfileError(f"$.profiles[{index}].claim_ceiling must be non-empty")

        raw_libraries = profile["libraries"]
        if not isinstance(raw_libraries, list) or not raw_libraries:
            raise RuntimeProfileError(f"$.profiles[{index}].libraries must be non-empty")
        libraries: list[LibraryRequirement] = []
        seen_distributions: set[str] = set()
        for library_index, raw_library in enumerate(raw_libraries):
            library = _exact_object(
                raw_library,
                {
                    "distribution",
                    "import_name",
                    "minimum_version",
                    "maximum_exclusive_version",
                    "required_attributes",
                },
                f"$.profiles[{index}].libraries[{library_index}]",
            )
            distribution = _safe_identifier(
                library["distribution"],
                f"$.profiles[{index}].libraries[{library_index}].distribution",
            )
            if distribution in seen_distributions:
                raise RuntimeProfileError("runtime profile has duplicate distributions")
            seen_distributions.add(distribution)
            import_name = library["import_name"]
            if (
                not isinstance(import_name, str)
                or not import_name
                or any(part == "" or not part.isidentifier() for part in import_name.split("."))
            ):
                raise RuntimeProfileError("runtime-profile import_name must be dotted Python identifiers")
            minimum_version = library["minimum_version"]
            maximum_version = library["maximum_exclusive_version"]
            _version_tuple(minimum_version, "runtime-profile minimum_version")
            _version_tuple(maximum_version, "runtime-profile maximum_exclusive_version")
            if _version_tuple(minimum_version, "runtime-profile minimum_version") >= _version_tuple(maximum_version, "runtime-profile maximum_exclusive_version"):
                raise RuntimeProfileError("runtime-profile version window is empty")
            raw_attributes = library["required_attributes"]
            if (
                not isinstance(raw_attributes, list)
                or not raw_attributes
                or any(not isinstance(attribute, str) or not attribute or "." in attribute for attribute in raw_attributes)
                or len(set(raw_attributes)) != len(raw_attributes)
            ):
                raise RuntimeProfileError("runtime-profile required_attributes is invalid")
            libraries.append(
                LibraryRequirement(
                    distribution=distribution,
                    import_name=import_name,
                    minimum_version=minimum_version,
                    maximum_exclusive_version=maximum_version,
                    required_attributes=tuple(raw_attributes),
                )
            )
        if [library.distribution for library in libraries] != sorted(library.distribution for library in libraries):
            raise RuntimeProfileError("runtime-profile libraries must be sorted by distribution")
        profiles.append(
            RuntimeProfile(
                profile_id=profile_id,
                implementation=implementation,
                python_minor=python_minor,
                allowed_optimization_levels=tuple(raw_optimization),
                require_hash_randomization=profile["require_hash_randomization"],
                libraries=tuple(libraries),
                claim_ceiling=claim_ceiling,
            )
        )
    if [profile.profile_id for profile in profiles] != sorted(profile.profile_id for profile in profiles):
        raise RuntimeProfileError("runtime profiles must be sorted by profile_id")
    return RuntimeProfileRegistry(observed_sha256, tuple(profiles))


def load_runtime_profile_registry(
    path: Path = DEFAULT_RUNTIME_PROFILE_REGISTRY,
) -> RuntimeProfileRegistry:
    """Load the package-owned portable core profile registry."""

    if path != DEFAULT_RUNTIME_PROFILE_REGISTRY:
        raise RuntimeProfileError("runtime-profile registry path is fixed")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeProfileError(f"runtime-profile registry unavailable: {exc}") from exc
    return _parse_registry(raw, _SHA256(raw).hexdigest())


def runtime_profile_registry_sha256() -> str:
    return load_runtime_profile_registry().registry_sha256


def _path_observation(value: object, attribute: str) -> tuple[str | None, str | None]:
    try:
        raw_path = getattr(value, attribute)
        path = Path(raw_path).resolve()
    except (AttributeError, OSError, TypeError, ValueError):
        return None, None
    try:
        digest = _SHA256(path.read_bytes()).hexdigest() if path.is_file() else None
    except OSError:
        digest = None
    return str(path), digest


def _module_observation(
    requirement: LibraryRequirement,
    *,
    module_loader: Callable[[str], object],
    version_provider: Callable[[str], str],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "distribution": requirement.distribution,
        "import_name": requirement.import_name,
        "minimum_version": requirement.minimum_version,
        "maximum_exclusive_version": requirement.maximum_exclusive_version,
        "required_attributes": list(requirement.required_attributes),
    }
    try:
        observed_version = version_provider(requirement.distribution)
    except importlib.metadata.PackageNotFoundError:
        return {**row, "state": "MISSING_DISTRIBUTION"}
    except Exception as exc:
        return {
            **row,
            "state": "METADATA_ERROR",
            "exception_type": type(exc).__name__,
            "error": str(exc),
        }
    row["observed_version"] = observed_version
    try:
        compatible_version = _version_in_window(
            observed_version,
            requirement.minimum_version,
            requirement.maximum_exclusive_version,
        )
    except RuntimeProfileError as exc:
        return {
            **row,
            "state": "VERSION_PARSE_ERROR",
            "error": str(exc),
        }
    if not compatible_version:
        return {**row, "state": "VERSION_OUT_OF_PROFILE"}
    try:
        distribution = importlib.metadata.distribution(requirement.distribution)
        distribution_files = distribution.files
        if distribution_files is None:
            raise RuntimeProfileError("distribution file inventory unavailable")
        distribution_paths = {
            Path(distribution.locate_file(item)).resolve()
            for item in distribution_files
        }
    except RuntimeProfileError as exc:
        return {**row, "state": "METADATA_ERROR", "error": str(exc)}
    except importlib.metadata.PackageNotFoundError:
        return {**row, "state": "MISSING_DISTRIBUTION"}
    except Exception as exc:
        return {
            **row,
            "state": "METADATA_ERROR",
            "exception_type": type(exc).__name__,
            "error": str(exc),
        }
    try:
        module = module_loader(requirement.import_name)
    except ModuleNotFoundError as exc:
        return {
            **row,
            "state": "MISSING_IMPORT",
            "missing_module": exc.name,
        }
    except Exception as exc:
        return {
            **row,
            "state": "IMPORT_ERROR",
            "exception_type": type(exc).__name__,
            "error": str(exc),
        }
    missing_attributes = [
        attribute
        for attribute in requirement.required_attributes
        if getattr(module, attribute, None) is None
    ]
    module_origin, module_sha256 = _path_observation(module, "__file__")
    spec_origin, _ = _path_observation(getattr(module, "__spec__", None), "origin")
    if missing_attributes:
        return {
            **row,
            "state": "API_MISMATCH",
            "missing_attributes": missing_attributes,
            "module_origin": module_origin,
            "module_sha256": module_sha256,
            "spec_origin": spec_origin,
        }
    observed_origins = {
        Path(origin).resolve()
        for origin in (module_origin, spec_origin)
        if origin is not None
    }
    if (
        module_origin is None
        or spec_origin is None
        or not observed_origins
        or not observed_origins.issubset(distribution_paths)
    ):
        return {
            **row,
            "state": "MODULE_ORIGIN_MISMATCH",
            "module_origin": module_origin,
            "module_sha256": module_sha256,
            "spec_origin": spec_origin,
        }
    return {
        **row,
        "state": "COMPATIBLE",
        "module_origin": module_origin,
        "module_sha256": module_sha256,
        "spec_origin": spec_origin,
    }


def inspect_active_runtime(
    *,
    registry: RuntimeProfileRegistry | None = None,
    implementation: str | None = None,
    version_info: tuple[int, int, int] | None = None,
    optimization_level: int | None = None,
    hash_randomization: int | None = None,
    module_loader: Callable[[str], object] = importlib.import_module,
    version_provider: Callable[[str], str] = importlib.metadata.version,
) -> dict[str, Any]:
    """Observe and deterministically classify the *active* core runtime.

    This function is deliberately read-only.  It does not create a venv, choose
    a Python executable, invoke pip, or replace a version.  An unmatched or
    incomplete runtime is retained as non-eligible evidence rather than being
    silently repaired.
    """

    active_registry = registry if registry is not None else load_runtime_profile_registry()
    observed_implementation = implementation if implementation is not None else platform.python_implementation()
    observed_version = version_info if version_info is not None else tuple(sys.version_info[:3])
    if (
        not isinstance(observed_version, tuple)
        or len(observed_version) != 3
        or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in observed_version)
    ):
        raise RuntimeProfileError("version_info must contain three non-negative integers")
    observed_optimization = sys.flags.optimize if optimization_level is None else optimization_level
    observed_hash_randomization = sys.flags.hash_randomization if hash_randomization is None else hash_randomization
    candidates = [
        profile
        for profile in active_registry.profiles
        if profile.implementation == observed_implementation
        and profile.python_minor == observed_version[:2]
    ]
    base = {
        "schema": "constraintbox.runtime-profile-receipt.v1",
        "registry_sha256": active_registry.registry_sha256,
        "implementation": observed_implementation,
        "version": list(observed_version),
        "cache_tag": sys.implementation.cache_tag,
        "platform": sysconfig.get_platform(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "flags": {
            "optimize": observed_optimization,
            "isolated": sys.flags.isolated,
            "ignore_environment": sys.flags.ignore_environment,
            "safe_path": bool(sys.flags.safe_path),
            "hash_randomization": observed_hash_randomization,
        },
        "executable": {
            "reported": sys.executable,
            "realpath": str(Path(sys.executable).resolve()),
        },
        "profile_id": None,
        "libraries": [],
        "promotion_allowed": False,
    }
    if not candidates:
        return {
            **base,
            "state": "PARKED",
            "reason": "unsupported_python_runtime",
            "claim_ceiling": "no configured portable ConstraintBox core profile matches this active interpreter",
        }
    if len(candidates) != 1:
        raise RuntimeProfileError("runtime-profile registry selected ambiguously")
    profile = candidates[0]
    profile_base = {
        **base,
        "profile_id": profile.profile_id,
        "claim_ceiling": profile.claim_ceiling,
    }
    if observed_optimization not in profile.allowed_optimization_levels:
        return {
            **profile_base,
            "state": "BLOCKED",
            "reason": "python_optimization_mode_out_of_profile",
        }
    if profile.require_hash_randomization and observed_hash_randomization != 1:
        return {
            **profile_base,
            "state": "BLOCKED",
            "reason": "python_hash_randomization_out_of_profile",
        }
    rows = [
        _module_observation(
            requirement,
            module_loader=module_loader,
            version_provider=version_provider,
        )
        for requirement in profile.libraries
    ]
    states = {row["state"] for row in rows}
    if states == {"COMPATIBLE"}:
        state, reason = "ELIGIBLE", "core_runtime_profile_satisfied"
    elif states & {"MISSING_DISTRIBUTION", "MISSING_IMPORT"}:
        state, reason = "PARKED", "core_runtime_dependency_unavailable"
    else:
        state, reason = "BLOCKED", "core_runtime_profile_mismatch"
    return {
        **profile_base,
        "state": state,
        "reason": reason,
        "libraries": rows,
    }


def list_runtime_profiles(
    registry: RuntimeProfileRegistry | None = None,
) -> dict[str, Any]:
    """Return the static portable profile inventory without observing a host."""

    active_registry = registry if registry is not None else load_runtime_profile_registry()
    return {
        "schema": "constraintbox.runtime-profile-list.v1",
        "registry_sha256": active_registry.registry_sha256,
        "profiles": [
            {
                "profile_id": profile.profile_id,
                "implementation": profile.implementation,
                "python_minor": list(profile.python_minor),
                "allowed_optimization_levels": list(profile.allowed_optimization_levels),
                "require_hash_randomization": profile.require_hash_randomization,
                "libraries": [
                    {
                        "distribution": requirement.distribution,
                        "import_name": requirement.import_name,
                        "minimum_version": requirement.minimum_version,
                        "maximum_exclusive_version": requirement.maximum_exclusive_version,
                        "required_attributes": list(requirement.required_attributes),
                    }
                    for requirement in profile.libraries
                ],
                "claim_ceiling": profile.claim_ceiling,
                "promotion_allowed": False,
            }
            for profile in active_registry.profiles
        ],
        "promotion_allowed": False,
    }


def runtime_receipt_sha256(receipt: Mapping[str, Any]) -> str:
    """Return the canonical digest of a portable runtime observation receipt."""

    return _SHA256(canonical_json(dict(receipt))).hexdigest()
