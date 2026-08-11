"""Bounded local candidate-evaluation consumer for CB Light.

This module is deliberately narrow.  It validates one typed control request,
binds it to an existing CB Light SQLite selection triple, and records only a
local candidate-evaluation operation.  It cannot promote a dependency,
authorize a provider, or launch CB Heavy.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable, Mapping

from hookkernel.cb_light_domain import DATA_ROOT, compile_domain
from hookkernel.cb_light_runtime import MANDATED_INTERPRETER, same_declared_interpreter
from hookkernel.cb_light_state import StateError, connect, record_candidate_evaluation


PIN_FILE = (
    DATA_ROOT
    / "requirements"
    / "control_plane_candidates"
    / "cb_control_plane_candidate_pins_v1.txt"
)
REQUEST_SCHEMA = "constraintbox.control-plane-request.v1"
RESULT_SCHEMA = "constraintbox.control-plane-candidate-evaluation.v1"


class ControlPlaneError(RuntimeError):
    """A typed refusal or hold from the bounded candidate consumer."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class ValidatedControlRequest:
    """Validated request bytes and the schema that constrained them."""

    payload: dict[str, Any]
    request_sha256: str
    schema_sha256: str


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _control_plane_provider_pins() -> dict[str, str]:
    """Read the exact runtime pins for the explicit control-plane profile.

    The profile intentionally lives outside the 91-root CB Light estate.  It
    still needs its own deterministic runtime boundary: merely reporting the
    versions that happened to be imported would let a drifted optional profile
    attest an estate it was not configured to judge.
    """

    try:
        lines = PIN_FILE.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ControlPlaneError(
            "HOLD_CONTROL_PLANE_PIN_FILE_MISSING",
            f"Cannot read control-plane pin file: {PIN_FILE}",
        ) from exc

    pins: dict[str, str] = {}
    for line in lines:
        requirement = line.split("#", 1)[0].strip()
        if not requirement:
            continue
        if requirement.count("==") != 1:
            raise ControlPlaneError(
                "HOLD_CONTROL_PLANE_PIN_FILE_INVALID",
                f"Control-plane requirement is not an exact pin: {requirement!r}",
            )
        name, value = (part.strip() for part in requirement.split("==", 1))
        normalized_name = name.lower().replace("_", "-")
        if not name or not value or normalized_name in pins:
            raise ControlPlaneError(
                "HOLD_CONTROL_PLANE_PIN_FILE_INVALID",
                f"Control-plane pin file has an invalid or duplicate pin: {requirement!r}",
            )
        pins[normalized_name] = value

    required = {"pydantic", "jsonschema"}
    if not required.issubset(pins):
        raise ControlPlaneError(
            "HOLD_CONTROL_PLANE_PIN_FILE_INVALID",
            "Control-plane pin file must exactly pin pydantic and jsonschema.",
        )
    return pins


def _runtime_attestation() -> dict[str, str]:
    """Capture the exact optional-provider runtime that executed this route."""

    pins = _control_plane_provider_pins()
    try:
        pydantic_version = version("pydantic")
        jsonschema_version = version("jsonschema")
    except PackageNotFoundError as exc:
        raise ControlPlaneError(
            "HOLD_CONTROL_PLANE_DEPENDENCY_MISSING",
            f"Required control-plane provider is unavailable: {exc.name}",
        ) from exc
    observed = {
        "pydantic": pydantic_version,
        "jsonschema": jsonschema_version,
    }
    mismatches = {
        name: {"expected": pins[name], "observed": observed[name]}
        for name in sorted(observed)
        if observed[name] != pins[name]
    }
    if mismatches:
        raise ControlPlaneError(
            "HOLD_CONTROL_PLANE_PROVIDER_VERSION_MISMATCH",
            "Control-plane providers do not match the pinned profile: "
            + json.dumps(mismatches, sort_keys=True),
        )
    return {
        "interpreter": sys.executable,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "pydantic_version": pydantic_version,
        "jsonschema_version": jsonschema_version,
    }


def _light_runtime_python_version() -> str:
    """Read the version from the actual contained Light runtime, not this profile."""

    if not MANDATED_INTERPRETER.is_file():
        raise ControlPlaneError(
            "HOLD_LIGHT_RUNTIME_MISSING",
            f"Contained CB Light interpreter is unavailable: {MANDATED_INTERPRETER}",
        )
    completed = subprocess.run(
        [
            str(MANDATED_INTERPRETER),
            "-I",
            "-c",
            "import sys; print('.'.join(map(str, sys.version_info[:3])))",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    observed = completed.stdout.strip()
    if completed.returncode != 0 or not observed:
        raise ControlPlaneError(
            "HOLD_LIGHT_RUNTIME_UNREADABLE",
            "Cannot attest the contained CB Light interpreter version.",
        )
    return observed


def _request_model():
    """Load optional boundary dependencies only for this explicit command."""

    try:
        from pydantic import BaseModel, ConfigDict, Field, ValidationError
    except ModuleNotFoundError as exc:
        if exc.name in {"pydantic", "pydantic_core"}:
            raise ControlPlaneError(
                "HOLD_CONTROL_PLANE_DEPENDENCY_MISSING",
                "Pydantic is unavailable in the executing interpreter.",
            ) from exc
        raise

    from typing import Literal

    class ControlRequest(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

        contract_schema: Literal[REQUEST_SCHEMA] = Field(
            alias="schema",
            serialization_alias="schema",
        )
        request_id: str = Field(
            min_length=3,
            max_length=64,
            pattern=r"^[a-z0-9][a-z0-9_-]*$",
        )
        operation: Literal["candidate_evaluation"]
        candidate_id: Literal["pydantic"]
        snapshot_id: str = Field(pattern=r"^[0-9a-f]{64}$")
        probe_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
        selection_id: str = Field(pattern=r"^[0-9a-f]{64}$")
        candidate_pin_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
        capabilities: list[Literal["schema_envelope"]] = Field(
            min_length=1,
            max_length=1,
        )

    return ControlRequest, ValidationError


def _validation_reason(errors: list[dict[str, Any]]) -> str:
    error_types = {str(error.get("type", "")) for error in errors}
    locations = {tuple(error.get("loc", ())) for error in errors}
    if "extra_forbidden" in error_types:
        return "REFUSE_UNEXPECTED_FIELD"
    if any(location and location[0] == "capabilities" for location in locations):
        return "REFUSE_UNDECLARED_CAPABILITY"
    if any(error_type.endswith("_type") for error_type in error_types):
        return "REFUSE_STRICT_TYPE"
    return "REFUSE_CONTROL_REQUEST_INVALID"


def validate_control_request(raw: Mapping[str, Any]) -> ValidatedControlRequest:
    """Strictly validate one request and independently cross-check its schema."""

    if not isinstance(raw, Mapping):
        raise ControlPlaneError(
            "REFUSE_CONTROL_REQUEST_INVALID",
            "A control request must be an object.",
        )

    model, validation_error = _request_model()
    try:
        value = model.model_validate(dict(raw), strict=True)
    except validation_error as exc:
        raise ControlPlaneError(
            _validation_reason(exc.errors()),
            "Pydantic rejected the control request.",
        ) from exc

    payload = value.model_dump(mode="json", by_alias=True)
    schema = model.model_json_schema(by_alias=True)
    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        if exc.name == "jsonschema":
            raise ControlPlaneError(
                "HOLD_CONTROL_PLANE_DEPENDENCY_MISSING",
                "jsonschema is unavailable in the executing interpreter.",
            ) from exc
        raise

    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as exc:
        raise ControlPlaneError(
            "HOLD_SCHEMA_CROSSCHECK_FAILED",
            "The independently generated JSON Schema rejected the Pydantic payload.",
        ) from exc

    return ValidatedControlRequest(
        payload=payload,
        request_sha256=sha256_bytes(canonical_json(payload)),
        schema_sha256=sha256_bytes(canonical_json(schema)),
    )


def _result(
    disposition: str,
    reason_code: str,
    *,
    detail: str,
    **extra: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "profile": "cb_light",
        "operation": "candidate_evaluation",
        "disposition": disposition,
        "reason_code": reason_code,
        "detail": detail,
        "promotion_allowed": False,
        "claim_ceiling": (
            "One strict local Pydantic candidate-evaluation consumer only; "
            "no membership, adoption, portable, provider, CB Heavy, or release claim."
        ),
    }
    body.update(extra)
    return body


def _verify_selection(
    connection: Any,
    request: ValidatedControlRequest,
) -> dict[str, str]:
    payload = request.payload
    row = connection.execute(
        """
        SELECT
            selection_run.selection_id,
            selection_run.snapshot_id,
            selection_run.probe_run_id,
            domain_snapshot.source_manifest_sha256,
            probe_run.all_contracts_satisfied,
            probe_run.interpreter AS probe_interpreter,
            probe_run.python_version AS probe_python_version
        FROM selection_run
        JOIN domain_snapshot
            ON domain_snapshot.snapshot_id = selection_run.snapshot_id
        LEFT JOIN probe_run
            ON probe_run.run_id = selection_run.probe_run_id
        WHERE selection_run.selection_id = ?
        """,
        (payload["selection_id"],),
    ).fetchone()
    if row is None:
        raise ControlPlaneError(
            "HOLD_SELECTION_MISSING",
            "The supplied selection_id is not present in the CB Light state database.",
        )
    if (
        row["snapshot_id"] != payload["snapshot_id"]
        or row["probe_run_id"] != payload["probe_run_id"]
    ):
        raise ControlPlaneError(
            "REFUSE_SELECTION_TRIPLE_MISMATCH",
            "The supplied snapshot/probe/selection triple is not bound in SQLite.",
        )
    if row["all_contracts_satisfied"] != 1:
        raise ControlPlaneError(
            "HOLD_CORE_PROBES_UNSATISFIED",
            "The bound probe run did not satisfy all current core probe contracts.",
        )

    if not same_declared_interpreter(
        str(row["probe_interpreter"]), MANDATED_INTERPRETER
    ):
        raise ControlPlaneError(
            "HOLD_LIGHT_PROBE_RUNTIME_MISMATCH",
            "The selection's core probe did not run in the contained CB Light runtime.",
        )
    light_python_version = _light_runtime_python_version()
    if row["probe_python_version"] != light_python_version:
        raise ControlPlaneError(
            "HOLD_LIGHT_PROBE_PYTHON_VERSION_MISMATCH",
            "The selection's core probe used a different CB Light Python version.",
        )

    current_source_manifest = compile_domain(
        interpreter=str(MANDATED_INTERPRETER)
    )["source_manifest_sha256"]
    if row["source_manifest_sha256"] != current_source_manifest:
        raise ControlPlaneError(
            "HOLD_SELECTION_SOURCE_DRIFT",
            "The selection was produced from a different current source manifest.",
        )
    return {
        "snapshot_id": str(row["snapshot_id"]),
        "probe_run_id": str(row["probe_run_id"]),
        "selection_id": str(row["selection_id"]),
        "source_manifest_sha256": str(row["source_manifest_sha256"]),
        "probe_interpreter": str(row["probe_interpreter"]),
        "probe_python_version": str(row["probe_python_version"]),
        "light_runtime_interpreter": str(MANDATED_INTERPRETER),
        "light_runtime_python_version": light_python_version,
    }


def run_candidate_evaluation(
    raw: Mapping[str, Any],
    *,
    db_path: Path,
    validator: Callable[[Mapping[str, Any]], ValidatedControlRequest] = (
        validate_control_request
    ),
) -> dict[str, Any]:
    """Consume one validated Pydantic candidate request against CB Light state."""

    try:
        request = validator(raw)
    except ControlPlaneError as exc:
        return _result(
            "HOLD" if exc.reason_code.startswith("HOLD_") else "REFUSE",
            exc.reason_code,
            detail=exc.detail,
        )

    if not isinstance(request, ValidatedControlRequest):
        return _result(
            "HOLD",
            "HOLD_VALIDATED_ENVELOPE_REQUIRED",
            detail="A raw mapping cannot cross the candidate-evaluation boundary.",
        )
    if not PIN_FILE.is_file():
        return _result(
            "HOLD",
            "HOLD_CANDIDATE_PIN_FILE_MISSING",
            detail=f"Missing candidate pin file: {PIN_FILE}",
        )
    observed_pin_sha256 = sha256_file(PIN_FILE)
    if request.payload["candidate_pin_sha256"] != observed_pin_sha256:
        return _result(
            "REFUSE",
            "REFUSE_CANDIDATE_PIN_DIGEST_MISMATCH",
            detail="The request is not bound to the current candidate pin file.",
        )

    try:
        runtime = _runtime_attestation()
    except ControlPlaneError as exc:
        return _result("HOLD", exc.reason_code, detail=exc.detail)
    runtime_sha256 = sha256_bytes(canonical_json(runtime))

    connection = connect(db_path)
    try:
        binding = _verify_selection(connection, request)
        source_sha256 = sha256_file(Path(__file__))
        operation_id = sha256_bytes(
            canonical_json(
                {
                    "request_sha256": request.request_sha256,
                    "schema_sha256": request.schema_sha256,
                    "candidate_pin_sha256": observed_pin_sha256,
                    "selection_id": binding["selection_id"],
                    "source_sha256": source_sha256,
                    "runtime_sha256": runtime_sha256,
                }
            )
        )
        try:
            record_candidate_evaluation(
                connection,
                operation_id=operation_id,
                request_id=request.payload["request_id"],
                request_sha256=request.request_sha256,
                schema_sha256=request.schema_sha256,
                candidate_id=request.payload["candidate_id"],
                candidate_pin_sha256=observed_pin_sha256,
                source_sha256=source_sha256,
                snapshot_id=binding["snapshot_id"],
                probe_run_id=binding["probe_run_id"],
                selection_id=binding["selection_id"],
            )
        except StateError as exc:
            return _result(
                "REFUSE",
                "REFUSE_REQUEST_ID_REUSE",
                detail=str(exc),
            )
        return _result(
            "CANDIDATE_EVALUATED_LOCAL",
            "STRICT_PACKET_AND_SELECTION_BOUND",
            detail="Pydantic and jsonschema validated a request that consumed a current CB Light selection triple.",
            operation_id=operation_id,
            request_id=request.payload["request_id"],
            request_sha256=request.request_sha256,
            request_schema_sha256=request.schema_sha256,
            candidate_pin_sha256=observed_pin_sha256,
            control_plane_source_sha256=source_sha256,
            control_plane_runtime=runtime,
            control_plane_runtime_sha256=runtime_sha256,
            **binding,
        )
    except ControlPlaneError as exc:
        return _result("HOLD" if exc.reason_code.startswith("HOLD_") else "REFUSE", exc.reason_code, detail=exc.detail)
    finally:
        connection.close()


def run_candidate_evaluation_file(request_path: Path, *, db_path: Path) -> dict[str, Any]:
    """Read a JSON request without allowing arbitrary callable or dict injection."""

    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _result(
            "REFUSE",
            "REFUSE_CONTROL_REQUEST_JSON_INVALID",
            detail=f"Cannot load request JSON: {exc}",
        )
    return run_candidate_evaluation(raw, db_path=db_path)
