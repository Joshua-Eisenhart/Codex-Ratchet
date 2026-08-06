from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

try:  # The controller refuses to launch us if POSIX limits are unavailable.
    import resource
except ImportError:  # pragma: no cover - checked through the worker contract.
    resource = None  # type: ignore[assignment]


_JOB_SCHEMA = "constraintbox.maude-worker.request.v1"
_OBSERVATION_SCHEMA = "constraintbox.maude-worker.observation.v1"
_JOB_KEYS = {
    "schema",
    "module_name",
    "module_source",
    "module_source_sha256",
    "source_term",
    "rule_label",
    "max_applications",
    "max_rules",
    "max_equations",
    "cpu_limit_seconds",
    "memory_limit_bytes",
    "memory_limit_mebibytes",
    "memory_limit_mechanism",
    "required_maude_version",
    "required_maude_core_version",
    "expected_maude_wrapper_path",
    "expected_maude_wrapper_sha256",
    "expected_maude_native_extension_path",
    "expected_maude_native_extension_sha256",
    "expected_maude_core_library_path",
    "expected_maude_core_library_sha256",
}
_OBSERVATION_KEYS = {
    "schema",
    "status",
    "operation",
    "error_type",
    "error",
    "exact_api",
    "maude_version",
    "maude_core_version",
    "runtime_identity",
    "resource_limits",
    "module_name",
    "module_source_sha256",
    "module_loaded",
    "rule_inventory",
    "rule_inventory_overflow",
    "equation_count",
    "equation_inventory_overflow",
    "parsed_term",
    "applications",
    "application_count",
}
_EXACT_API = (
    "maude.init(loadPrelude=False, randomSeed=0, advise=False, "
    "handleInterrupts=False)",
    "maude.input(controller_rendered_module)",
    "maude.getModule(module_name)",
    "Module.getRules()",
    "Module.getEquations()",
    "Rule.getLabel()",
    "Rule.getMetadata()",
    "Rule.getLhs()",
    "Rule.getRhs()",
    "Rule.hasCondition()",
    "Module.parseTerm(encoded_state)",
    "Term.apply(rule_label, minDepth=0, maxDepth=0)",
    "Substitution.size()",
    "Substitution.matchedPortion()",
)
_MODULE_NAME_RE = re.compile(r"CBM_[0-9A-F]{16}")
_STATE_TERM_RE = re.compile(r"s(?:0|[1-9][0-9]{0,3})")
_RULE_LABEL_RE = re.compile(r"r(?:0|[1-9][0-9]{0,4})")
_MAX_JOB_BYTES = 1_048_576
_MAX_MODULE_CHARS = 524_288
_MAX_APPLICATIONS = 16
_MAX_RULES = 4_096
_MAX_CPU_LIMIT_SECONDS = 31
_MAX_MEMORY_LIMIT_BYTES = 1_073_741_824
_MIN_MEMORY_LIMIT_BYTES = 134_217_728
_MAX_OBSERVATION_TEXT_CHARS = 4_096
_MAX_SERIALIZED_OBSERVATION_BYTES = 524_288
_RUNTIME_IDENTITY_KEYS = {
    "wrapper",
    "native_extension",
    "core_library",
}
_RESOURCE_LIMIT_KEYS = {
    "cpu_seconds",
    "memory_limit_bytes",
    "memory_limit_mebibytes",
    "memory_limit_mechanism",
}


class _JobError(ValueError):
    pass


class _OperationUnavailable(RuntimeError):
    pass


class _DependencyUnavailable(FileNotFoundError):
    pass


class _RuntimeIdentityError(RuntimeError):
    pass


class _ResourceLimitError(RuntimeError):
    pass


class _BoundExceeded(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _JobError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _no_constants(token: str) -> None:
    raise _JobError(f"non-finite JSON token: {token}")


def _finite_walk(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise _JobError("non-finite JSON number")
    if isinstance(value, dict):
        for child in value.values():
            _finite_walk(child)
    elif isinstance(value, list):
        for child in value:
            _finite_walk(child)


def _parse_job(raw: bytes) -> dict[str, Any]:
    if len(raw) > _MAX_JOB_BYTES:
        raise _JobError("worker job exceeds byte limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_no_constants,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _JobError(f"invalid JSON: {exc}") from exc
    _finite_walk(value)
    if not isinstance(value, dict) or set(value) != _JOB_KEYS:
        raise _JobError("worker job keys mismatch")
    if value["schema"] != _JOB_SCHEMA:
        raise _JobError("worker job schema mismatch")

    string_fields = (
        "module_name",
        "module_source",
        "module_source_sha256",
        "source_term",
        "rule_label",
        "required_maude_version",
        "required_maude_core_version",
        "expected_maude_wrapper_path",
        "expected_maude_wrapper_sha256",
        "expected_maude_native_extension_path",
        "expected_maude_core_library_path",
        "expected_maude_native_extension_sha256",
        "expected_maude_core_library_sha256",
    )
    if any(not isinstance(value[field], str) for field in string_fields):
        raise _JobError("worker job string field has the wrong type")
    if _MODULE_NAME_RE.fullmatch(value["module_name"]) is None:
        raise _JobError("worker module name is invalid")
    if len(value["module_source"]) > _MAX_MODULE_CHARS:
        raise _JobError("worker module source exceeds character limit")
    if re.fullmatch(r"[0-9a-f]{64}", value["module_source_sha256"]) is None:
        raise _JobError("worker module hash is invalid")
    actual_module_hash = hashlib.sha256(
        value["module_source"].encode("utf-8")
    ).hexdigest()
    if actual_module_hash != value["module_source_sha256"]:
        raise _JobError("worker module hash mismatch")
    if _STATE_TERM_RE.fullmatch(value["source_term"]) is None:
        raise _JobError("worker source term is invalid")
    if _RULE_LABEL_RE.fullmatch(value["rule_label"]) is None:
        raise _JobError("worker rule label is invalid")
    max_applications = value["max_applications"]
    if (
        isinstance(max_applications, bool)
        or not isinstance(max_applications, int)
        or not 1 <= max_applications <= _MAX_APPLICATIONS
    ):
        raise _JobError("worker application limit is invalid")
    if value["required_maude_version"] != "1.6.0":
        raise _JobError("worker required Maude version is invalid")
    if value["required_maude_core_version"] != "3.5.1+smc":
        raise _JobError("worker required Maude core version is invalid")
    for key in (
        "expected_maude_wrapper_path",
        "expected_maude_native_extension_path",
    ):
        path = Path(value[key])
        if not path.is_absolute() or "\x00" in value[key]:
            raise _JobError(f"worker {key} is invalid")
    for key in (
        "expected_maude_wrapper_sha256",
        "expected_maude_native_extension_sha256",
    ):
        if re.fullmatch(r"[0-9a-f]{64}", value[key]) is None:
            raise _JobError(f"worker {key} is invalid")
    max_rules = value["max_rules"]
    if (
        isinstance(max_rules, bool)
        or not isinstance(max_rules, int)
        or not 1 <= max_rules <= _MAX_RULES
    ):
        raise _JobError("worker rule limit is invalid")
    if (
        isinstance(value["max_equations"], bool)
        or not isinstance(value["max_equations"], int)
        or value["max_equations"] != 0
    ):
        raise _JobError("worker equation limit must be zero")
    cpu_limit_seconds = value["cpu_limit_seconds"]
    if (
        isinstance(cpu_limit_seconds, bool)
        or not isinstance(cpu_limit_seconds, int)
        or not 1 <= cpu_limit_seconds <= _MAX_CPU_LIMIT_SECONDS
    ):
        raise _JobError("worker CPU resource limit is invalid")
    memory_limit_bytes = value["memory_limit_bytes"]
    if (
        isinstance(memory_limit_bytes, bool)
        or not isinstance(memory_limit_bytes, int)
        or not _MIN_MEMORY_LIMIT_BYTES
        <= memory_limit_bytes
        <= _MAX_MEMORY_LIMIT_BYTES
    ):
        raise _JobError("worker memory resource limit is invalid")
    memory_limit_mebibytes = value["memory_limit_mebibytes"]
    if (
        isinstance(memory_limit_mebibytes, bool)
        or not isinstance(memory_limit_mebibytes, int)
        or memory_limit_mebibytes != memory_limit_bytes // (1024 * 1024)
    ):
        raise _JobError("worker memory mebibyte limit is invalid")
    if not isinstance(value["memory_limit_mechanism"], str) or value[
        "memory_limit_mechanism"
    ] not in {
        "rlimit_as",
        "darwin_taskpolicy",
    }:
        raise _JobError("worker memory-limit mechanism is invalid")
    return value


def _blank_observation(
    *,
    status: str,
    operation: str,
    error_type: str | None = None,
    error: str | None = None,
    job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "schema": _OBSERVATION_SCHEMA,
        "status": status,
        "operation": operation,
        "error_type": error_type,
        "error": error,
        "exact_api": list(_EXACT_API),
        "maude_version": None,
        "maude_core_version": None,
        "runtime_identity": {
            "wrapper": {"path": "", "sha256": ""},
            "native_extension": {"path": "", "sha256": ""},
            "core_library": {"path": "", "sha256": ""},
        },
        "resource_limits": {
            "cpu_seconds": 0,
            "memory_limit_bytes": 0,
            "memory_limit_mebibytes": 0,
            "memory_limit_mechanism": "",
        },
        "module_name": None,
        "module_source_sha256": None,
        "module_loaded": False,
        "rule_inventory": [],
        "rule_inventory_overflow": False,
        "equation_count": 0,
        "equation_inventory_overflow": False,
        "parsed_term": None,
        "applications": [],
        "application_count": 0,
    }
    if job is not None:
        observation["module_name"] = job["module_name"]
        observation["module_source_sha256"] = job["module_source_sha256"]
        observation["resource_limits"] = {
            "cpu_seconds": job["cpu_limit_seconds"],
            "memory_limit_bytes": job["memory_limit_bytes"],
            "memory_limit_mebibytes": job["memory_limit_mebibytes"],
            "memory_limit_mechanism": job["memory_limit_mechanism"],
        }
    return observation


def _verify_worker_resource_limits(
    job: dict[str, Any],
) -> dict[str, int | str]:
    """Verify the controller-selected CPU and memory-limit mechanism."""

    if (
        resource is None
        or not callable(getattr(resource, "getrlimit", None))
    ):
        raise _ResourceLimitError("POSIX resource inspection is unavailable")
    expected = {
        "cpu_seconds": job["cpu_limit_seconds"],
        "memory_limit_bytes": job["memory_limit_bytes"],
        "memory_limit_mebibytes": job["memory_limit_mebibytes"],
        "memory_limit_mechanism": job["memory_limit_mechanism"],
    }
    resource_names = [("cpu_seconds", "RLIMIT_CPU")]
    if expected["memory_limit_mechanism"] == "rlimit_as":
        resource_names.append(("memory_limit_bytes", "RLIMIT_AS"))
    elif expected["memory_limit_mechanism"] == "darwin_taskpolicy":
        if sys.platform != "darwin":
            raise _ResourceLimitError(
                "Darwin taskpolicy memory limit is unavailable on this host"
            )
    else:
        raise _ResourceLimitError("worker memory-limit mechanism is invalid")
    for key, resource_name in resource_names:
        resource_id = getattr(resource, resource_name, None)
        if isinstance(resource_id, bool) or not isinstance(resource_id, int):
            raise _ResourceLimitError(
                f"{resource_name} is unavailable in worker"
            )
        try:
            soft, hard = resource.getrlimit(resource_id)
        except (OSError, ValueError) as exc:
            raise _ResourceLimitError(
                f"cannot inspect {resource_name} in worker"
            ) from exc
        if (
            isinstance(soft, bool)
            or isinstance(hard, bool)
            or not isinstance(soft, int)
            or not isinstance(hard, int)
            or soft != expected[key]
            or hard != expected[key]
        ):
            raise _ResourceLimitError(
                f"{resource_name} does not equal the controller limit"
            )
    if (
        os.environ.get("CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MEBIBYTES")
        != str(expected["memory_limit_mebibytes"])
        or os.environ.get("CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MECHANISM")
        != expected["memory_limit_mechanism"]
    ):
        raise _ResourceLimitError(
            "worker memory-limit environment does not match controller job"
        )
    return expected


def _bounded_enumeration(
    values: object,
    *,
    maximum: int,
    operation: str,
):
    """Yield at most ``maximum`` values and reject rather than serialize more."""

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise TypeError(f"{operation} did not return an iterable") from exc
    for _index in range(maximum):
        try:
            yield next(iterator)
        except StopIteration:
            return
    try:
        next(iterator)
    except StopIteration:
        return
    raise _BoundExceeded(
        f"{operation} exceeds controller maximum of {maximum}"
    )


def _bounded_text(value: object, *, operation: str) -> str:
    text = str(value)
    if len(text) > _MAX_OBSERVATION_TEXT_CHARS:
        raise _BoundExceeded(
            f"{operation} text exceeds {_MAX_OBSERVATION_TEXT_CHARS} characters"
        )
    return text


def _require_callable(owner: object, name: str, operation: str) -> Any:
    value = getattr(owner, name, None)
    if not callable(value):
        raise _OperationUnavailable(f"{operation} is unavailable")
    return value


def _artifact_identity(path_text: str) -> dict[str, str]:
    try:
        path = Path(path_text).resolve(strict=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (FileNotFoundError, OSError) as exc:
        raise _DependencyUnavailable(
            f"runtime artifact is unavailable: {path_text}"
        ) from exc
    return {"path": str(path), "sha256": digest}


def _expected_runtime_identity(job: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        "wrapper": {
            "path": job["expected_maude_wrapper_path"],
            "sha256": job["expected_maude_wrapper_sha256"],
        },
        "native_extension": {
            "path": job["expected_maude_native_extension_path"],
            "sha256": job["expected_maude_native_extension_sha256"],
        },
        "core_library": {
            "path": job["expected_maude_core_library_path"],
            "sha256": job["expected_maude_core_library_sha256"],
        },
    }


def _preimport_runtime_identity(
    job: dict[str, Any],
) -> dict[str, dict[str, str]]:
    expected = _expected_runtime_identity(job)
    observed = {
        name: _artifact_identity(artifact["path"])
        for name, artifact in expected.items()
    }
    if observed != expected:
        raise _RuntimeIdentityError(
            "pre-import Maude runtime identity does not match controller pins"
        )
    return observed


def _imported_artifact_identity(
    module: object,
    *,
    label: str,
) -> dict[str, str]:
    file_value = getattr(module, "__file__", None)
    spec = getattr(module, "__spec__", None)
    origin = getattr(spec, "origin", None)
    if not isinstance(file_value, str) or not isinstance(origin, str):
        raise _RuntimeIdentityError(
            f"imported Maude {label} path metadata is unavailable"
        )
    file_identity = _artifact_identity(file_value)
    origin_identity = _artifact_identity(origin)
    if file_identity != origin_identity:
        raise _RuntimeIdentityError(
            f"imported Maude {label} file and spec origins disagree"
        )
    return file_identity


def observe(raw: bytes) -> dict[str, Any]:
    """Execute one controller-authored Maude observation.

    This worker deliberately has no disposition or promotion vocabulary.
    """

    try:
        job = _parse_job(raw)
    except Exception as exc:
        return _blank_observation(
            status="invalid_job",
            operation="job_validation",
            error_type=type(exc).__name__,
            error=str(exc),
        )

    try:
        applied_resource_limits = _verify_worker_resource_limits(job)
    except Exception as exc:
        return _blank_observation(
            status="operation_error",
            operation="resource_limits_preflight",
            error_type=type(exc).__name__,
            error=str(exc),
            job=job,
        )

    try:
        preimport_identity = _preimport_runtime_identity(job)
    except _DependencyUnavailable as exc:
        return _blank_observation(
            status="dependency_unavailable",
            operation="runtime_identity_preflight",
            error_type=type(exc).__name__,
            error=str(exc),
            job=job,
        )
    except Exception as exc:
        return _blank_observation(
            status="operation_error",
            operation="runtime_identity_preflight",
            error_type=type(exc).__name__,
            error=str(exc),
            job=job,
        )

    try:
        import maude  # type: ignore
    except (ImportError, ModuleNotFoundError) as exc:
        return _blank_observation(
            status="dependency_unavailable",
            operation="import maude",
            error_type=type(exc).__name__,
            error=str(exc),
            job=job,
        )
    except Exception as exc:
        return _blank_observation(
            status="operation_error",
            operation="import maude",
            error_type=type(exc).__name__,
            error=str(exc),
            job=job,
        )

    try:
        native_module = getattr(maude, "_maude", None)
        if native_module is None:
            raise _RuntimeIdentityError(
                "imported maude._maude module is unavailable"
            )
        wrapper_identity = _imported_artifact_identity(
            maude,
            label="wrapper",
        )
        native_identity = _imported_artifact_identity(
            native_module,
            label="native extension",
        )
        core_library_path = str(
            Path(native_identity["path"]).with_name("libmaude.dylib")
        )
        imported_identity = {
            "wrapper": wrapper_identity,
            "native_extension": native_identity,
            "core_library": _artifact_identity(core_library_path),
        }
        if (
            imported_identity != preimport_identity
            or imported_identity != _expected_runtime_identity(job)
        ):
            raise _RuntimeIdentityError(
                "imported Maude runtime identity does not match controller pins"
            )
    except Exception as exc:
        observation = _blank_observation(
            status="operation_error",
            operation="runtime_identity_postimport",
            error_type=type(exc).__name__,
            error=str(exc),
            job=job,
        )
        return observation

    version = getattr(maude, "__version__", None)
    if not isinstance(version, str) or version != job["required_maude_version"]:
        observation = _blank_observation(
            status="operation_error",
            operation="maude.__version__",
            error_type="VersionMismatch",
            error=(
                f"required {job['required_maude_version']}, "
                f"observed {version!r}"
            ),
            job=job,
        )
        observation["maude_version"] = version if isinstance(version, str) else None
        observation["runtime_identity"] = imported_identity
        return observation
    core_version = getattr(maude, "MAUDE_VERSION", None)
    if (
        not isinstance(core_version, str)
        or core_version != job["required_maude_core_version"]
    ):
        observation = _blank_observation(
            status="operation_error",
            operation="maude.MAUDE_VERSION",
            error_type="VersionMismatch",
            error=(
                f"required {job['required_maude_core_version']}, "
                f"observed {core_version!r}"
            ),
            job=job,
        )
        observation["maude_version"] = version
        observation["maude_core_version"] = (
            core_version if isinstance(core_version, str) else None
        )
        observation["runtime_identity"] = imported_identity
        return observation

    observation = _blank_observation(
        status="operation_error",
        operation="maude.init",
        job=job,
    )
    observation["maude_version"] = version
    observation["maude_core_version"] = core_version
    observation["runtime_identity"] = imported_identity
    observation["resource_limits"] = applied_resource_limits

    operation = "maude.init"
    try:
        init = _require_callable(maude, "init", operation)
        init_result = init(
            loadPrelude=False,
            randomSeed=0,
            advise=False,
            handleInterrupts=False,
        )
        if init_result is not True:
            raise RuntimeError("maude.init did not return True")

        operation = "maude.input"
        input_module = _require_callable(maude, "input", operation)
        if input_module(job["module_source"]) is not True:
            raise RuntimeError("maude.input did not accept the module")

        operation = "maude.getModule"
        get_module = _require_callable(maude, "getModule", operation)
        module = get_module(job["module_name"])
        if module is None:
            raise RuntimeError("maude.getModule returned no module")
        observation["module_loaded"] = True

        operation = "Module.getRules"
        get_rules = _require_callable(module, "getRules", operation)

        operation = "Module.getEquations"
        get_equations = _require_callable(module, "getEquations", operation)
        equation_count = 0
        try:
            for _equation in _bounded_enumeration(
                get_equations(),
                maximum=job["max_equations"],
                operation=operation,
            ):
                equation_count += 1
        except _BoundExceeded:
            observation["equation_count"] = equation_count
            observation["equation_inventory_overflow"] = True
            raise
        observation["equation_count"] = equation_count
        observation["equation_inventory_overflow"] = False

        rule_inventory: list[dict[str, Any]] = []
        inventory_operation = "Module.getRules"
        operation = inventory_operation
        try:
            for rule in _bounded_enumeration(
                get_rules(),
                maximum=job["max_rules"],
                operation=operation,
            ):
                operation = "Rule.getLabel"
                label = _require_callable(rule, "getLabel", operation)()
                operation = "Rule.getMetadata"
                metadata = _require_callable(rule, "getMetadata", operation)()
                operation = "Rule.getLhs"
                lhs = _require_callable(rule, "getLhs", operation)()
                operation = "Rule.getRhs"
                rhs = _require_callable(rule, "getRhs", operation)()
                operation = "Rule.hasCondition"
                has_condition = _require_callable(
                    rule, "hasCondition", operation
                )()
                if not isinstance(label, str) or not label:
                    raise TypeError("Rule.getLabel returned an invalid label")
                if not isinstance(metadata, str):
                    raise TypeError(
                        "Rule.getMetadata returned a non-string value"
                    )
                if lhs is None or rhs is None:
                    raise TypeError("rule endpoint term is unavailable")
                if not isinstance(has_condition, bool):
                    raise TypeError(
                        "Rule.hasCondition returned a non-boolean value"
                    )
                rule_inventory.append(
                    {
                        "label": _bounded_text(
                            label,
                            operation="Rule.getLabel",
                        ),
                        "metadata": _bounded_text(
                            metadata,
                            operation="Rule.getMetadata",
                        ),
                        "lhs": _bounded_text(
                            lhs,
                            operation="Rule.getLhs",
                        ),
                        "rhs": _bounded_text(
                            rhs,
                            operation="Rule.getRhs",
                        ),
                        "has_condition": has_condition,
                    }
                )
        except _BoundExceeded:
            operation = inventory_operation
            observation["rule_inventory"] = rule_inventory
            observation["rule_inventory_overflow"] = True
            raise
        observation["rule_inventory"] = rule_inventory
        observation["rule_inventory_overflow"] = False

        operation = "Module.parseTerm"
        parse_term = _require_callable(module, "parseTerm", operation)
        term = parse_term(job["source_term"])
        if term is None:
            raise RuntimeError("Module.parseTerm returned no term")
        observation["parsed_term"] = _bounded_text(
            term,
            operation="Module.parseTerm",
        )

        operation = "Term.apply"
        apply_rule = _require_callable(term, "apply", operation)
        application_iterator = apply_rule(
            job["rule_label"],
            minDepth=0,
            maxDepth=0,
        )
        applications: list[dict[str, Any]] = []
        application_operation = "Term.apply"
        try:
            for application in _bounded_enumeration(
                application_iterator,
                maximum=job["max_applications"],
                operation=application_operation,
            ):
                if (
                    not isinstance(application, tuple)
                    or len(application) != 4
                ):
                    raise TypeError("Term.apply yielded an invalid application")
                result_term, substitution, context, applied_rule = application
                substitution_type = getattr(maude, "Substitution", None)
                if (
                    not isinstance(substitution_type, type)
                    or not isinstance(substitution, substitution_type)
                ):
                    raise TypeError(
                        "Term.apply yielded an invalid substitution type"
                    )
                operation = "Substitution.size"
                substitution_size = _require_callable(
                    substitution, "size", operation
                )()
                if (
                    isinstance(substitution_size, bool)
                    or not isinstance(substitution_size, int)
                    or substitution_size < 0
                ):
                    raise TypeError(
                        "Substitution.size returned an invalid value"
                    )
                operation = "Substitution.matchedPortion"
                matched_portion_term = _require_callable(
                    substitution, "matchedPortion", operation
                )()
                matched_portion = (
                    None
                    if matched_portion_term is None
                    else _bounded_text(
                        matched_portion_term,
                        operation="Substitution.matchedPortion",
                    )
                )
                context_callable = callable(context)
                operation = "Rule.getLabel"
                applied_label = _require_callable(
                    applied_rule, "getLabel", operation
                )()
                operation = "Rule.getMetadata"
                applied_metadata = _require_callable(
                    applied_rule, "getMetadata", operation
                )()
                if not isinstance(applied_label, str) or not applied_label:
                    raise TypeError(
                        "applied Rule.getLabel returned an invalid label"
                    )
                if not isinstance(applied_metadata, str):
                    raise TypeError(
                        "applied Rule.getMetadata returned a non-string value"
                    )
                applications.append(
                    {
                        "term": _bounded_text(
                            result_term,
                            operation="Term.apply",
                        ),
                        "rule_label": _bounded_text(
                            applied_label,
                            operation="Rule.getLabel",
                        ),
                        "rule_metadata": _bounded_text(
                            applied_metadata,
                            operation="Rule.getMetadata",
                        ),
                        "substitution_size": substitution_size,
                        "matched_portion": matched_portion,
                        "context_callable": context_callable,
                    }
                )
        except _BoundExceeded:
            operation = application_operation
            observation["applications"] = applications
            observation["application_count"] = len(applications)
            raise

        observation["applications"] = applications
        observation["application_count"] = len(applications)
        observation["status"] = "ok"
        observation["operation"] = "complete"
        observation["error_type"] = None
        observation["error"] = None
        return observation
    except _OperationUnavailable as exc:
        observation["status"] = "operation_error"
        observation["operation"] = operation
        observation["error_type"] = type(exc).__name__
        observation["error"] = str(exc)
        return observation
    except Exception as exc:
        observation["status"] = "operation_error"
        observation["operation"] = operation
        observation["error_type"] = type(exc).__name__
        observation["error"] = str(exc)
        return observation


def _emit(observation: dict[str, Any]) -> None:
    if set(observation) != _OBSERVATION_KEYS:
        raise RuntimeError("internal observation schema mismatch")
    encoded = json.dumps(
        observation,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > _MAX_SERIALIZED_OBSERVATION_BYTES:
        # Do not turn a pathological native value into a large JSON response.
        # The controller will block this typed operation error; this worker
        # never decides a disposition itself.
        fallback = _blank_observation(
            status="operation_error",
            operation="observation_serialization",
            error_type="BoundExceeded",
            error=(
                "serialized observation exceeds "
                f"{_MAX_SERIALIZED_OBSERVATION_BYTES} bytes"
            ),
        )
        encoded = json.dumps(
            fallback,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.write(b"\n")


def main() -> int:
    raw = sys.stdin.buffer.read(_MAX_JOB_BYTES + 1)
    _emit(observe(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
