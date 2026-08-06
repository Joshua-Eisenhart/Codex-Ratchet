"""The first composed ConstraintBox front door.

This joins deterministic user intake, source-bound personalized MMM context,
and a separately executed external-engine packet.  It deliberately stops at
``READY_FOR_UNTRUSTED_PROPOSAL``: no LLM prose is allowed to become a verdict
or a release merely because the front door and tool packet passed.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .advice import build_audit_brief, deterministic_explanation
from .external_engine_packet import (
    ExternalEnginePacketBroker,
    validate_pass_receipt,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .user_profile import DEFAULT_PROFILE_PATH, compile_user_profile
from .user_request import (
    BLOCKED,
    ELIGIBLE,
    EVALUATION_ERROR,
    PARKED,
    assess_user_request,
)


SCHEMA = "constraintbox.first-box-run.v1"
READY_FOR_PROPOSAL = "READY_FOR_UNTRUSTED_PROPOSAL"
EXIT_CODES = {
    READY_FOR_PROPOSAL: 0,
    BLOCKED: 1,
    PARKED: 4,
    EVALUATION_ERROR: 5,
}
CLAIM_CEILING = (
    "at most, this run can establish that the user request passed deterministic "
    "explicitness checks and that the named external function packet passed "
    "its bounded controls; it cannot admit an LLM proposal, final answer, "
    "scientific claim, engine-readiness claim, or release"
)
MAX_BOX_ARTIFACT_BYTES = 4 * 1024 * 1024
READY_ARTIFACT_NAMES = frozenset(
    {
        "compiled_user_context.json",
        "compiled_user_context.txt",
        "deterministic_explanation.json",
        "external_audit_brief.json",
        "external_engine_packet.json",
        "request_assessment.json",
        "user_profile.json",
        "user_request.json",
    }
)
BOX_RECEIPT_FIELDS = frozenset(
    {
        "artifacts",
        "claim_ceiling",
        "deterministic_explanation",
        "disposition",
        "external_audit_brief",
        "external_engine_packet",
        "external_receipt_validation_errors",
        "next_step",
        "promotion_allowed",
        "reason",
        "release_allowed",
        "request_assessment",
        "schema",
        "user_context",
    }
)


class BoxRunError(ValueError):
    pass


@dataclass(frozen=True)
class VerifiedBoxRun:
    """One captured and independently revalidated first-box snapshot.

    The byte-derived fields are the only handoff data an agent run may use.
    This is an integrity-checked local snapshot, not hostile-code containment
    or authentication against another process running as the same OS user.
    """

    root: Path
    receipt_sha256: str
    request_id: str
    request_sha256: str
    request_canonical: bytes
    profile_sha256: str
    context_sha256: str
    context_text: str
    external_engine_packet_sha256: str
    artifact_sha256s: tuple[tuple[str, str], ...]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_bytes_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(value)
    os.replace(temporary, path)


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    _write_bytes_atomic(path, canonical_json(value) + b"\n")


def _read_regular_at(
    directory_descriptor: int,
    name: str,
    *,
    maximum_bytes: int = MAX_BOX_ARTIFACT_BYTES,
) -> bytes:
    """Capture one bounded regular file without following its final symlink."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except OSError as exc:
        raise BoxRunError(f"could not open box artifact {name}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise BoxRunError(f"box artifact is not a regular file: {name}")
        if before.st_nlink != 1:
            raise BoxRunError(f"box artifact has an unexpected link count: {name}")
        if before.st_size < 0 or before.st_size > maximum_bytes:
            raise BoxRunError(f"box artifact exceeds its byte bound: {name}")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        value = b"".join(chunks)
        after = os.fstat(descriptor)
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(
            getattr(before, field) != getattr(after, field)
            for field in stable_fields
        ):
            raise BoxRunError(f"box artifact changed while being read: {name}")
        if len(value) != before.st_size:
            raise BoxRunError(f"box artifact size changed while being read: {name}")
        if len(value) > maximum_bytes:
            raise BoxRunError(f"box artifact exceeds its byte bound: {name}")
        return value
    finally:
        os.close(descriptor)


def _parse_generated_json(raw: bytes, name: str) -> dict[str, Any]:
    try:
        value = parse_json_object(raw)
    except IntakeError as exc:
        raise BoxRunError(f"box artifact JSON is invalid: {name}: {exc}") from exc
    if raw != canonical_json(value) + b"\n":
        raise BoxRunError(f"box artifact is not canonical JSON: {name}")
    return value


def verify_box_run(run_dir: Path) -> VerifiedBoxRun:
    """Capture and independently revalidate one READY first-box run.

    Validation completes before the returned bytes can reach a provider.  The
    caller must use the captured fields rather than reopening paths later.
    """

    candidate = Path(run_dir).expanduser()
    try:
        if candidate.is_symlink():
            raise BoxRunError("box run directory must not be a symlink")
        root = candidate.resolve(strict=True)
    except OSError as exc:
        raise BoxRunError(f"box run directory is unavailable: {exc}") from exc
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        directory_descriptor = os.open(root, flags)
    except OSError as exc:
        raise BoxRunError(f"could not open box run directory: {exc}") from exc
    try:
        directory_before = os.fstat(directory_descriptor)
        names = set(os.listdir(directory_descriptor))
        expected_names = set(READY_ARTIFACT_NAMES) | {"box_receipt.json"}
        if names != expected_names:
            missing = sorted(expected_names - names)
            extra = sorted(names - expected_names)
            raise BoxRunError(
                "ready box artifact set differs"
                + (f"; missing={missing}" if missing else "")
                + (f"; extra={extra}" if extra else "")
            )
        captured = {
            name: _read_regular_at(directory_descriptor, name)
            for name in sorted(expected_names)
        }
        directory_after = os.fstat(directory_descriptor)
        if set(os.listdir(directory_descriptor)) != names or any(
            getattr(directory_before, field) != getattr(directory_after, field)
            for field in ("st_dev", "st_ino", "st_mtime_ns", "st_ctime_ns")
        ):
            raise BoxRunError("box run directory changed while being captured")
    finally:
        os.close(directory_descriptor)

    receipt_raw = captured["box_receipt.json"]
    receipt = _parse_generated_json(receipt_raw, "box_receipt.json")
    if set(receipt) != BOX_RECEIPT_FIELDS:
        raise BoxRunError("box receipt fields differ from the fixed schema")
    fixed_expectations = {
        "schema": SCHEMA,
        "disposition": READY_FOR_PROPOSAL,
        "reason": "request_and_external_function_packet_passed",
        "next_step": "untrusted_proposal_generation",
        "promotion_allowed": False,
        "release_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "external_receipt_validation_errors": [],
    }
    for field, expected in fixed_expectations.items():
        if receipt.get(field) != expected:
            raise BoxRunError(f"box receipt {field} is not proposal-ready")

    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != READY_ARTIFACT_NAMES:
        raise BoxRunError("box receipt artifact index differs from the ready set")
    for name in READY_ARTIFACT_NAMES:
        expected_digest = artifacts.get(name)
        if (
            not isinstance(expected_digest, str)
            or len(expected_digest) != 64
            or any(character not in "0123456789abcdef" for character in expected_digest)
        ):
            raise BoxRunError(f"box receipt artifact digest is invalid: {name}")
        if _sha256_bytes(captured[name]) != expected_digest:
            raise BoxRunError(f"box artifact digest mismatch: {name}")

    try:
        request_body = parse_json_object(captured["user_request.json"])
    except IntakeError as exc:
        raise BoxRunError(f"captured user request is invalid: {exc}") from exc
    fresh_assessment = assess_user_request(captured["user_request.json"]).to_dict()
    recorded_assessment = _parse_generated_json(
        captured["request_assessment.json"],
        "request_assessment.json",
    )
    if fresh_assessment != recorded_assessment:
        raise BoxRunError("captured request assessment does not match current policy")
    if receipt.get("request_assessment") != recorded_assessment:
        raise BoxRunError("box receipt request assessment differs from its artifact")
    if recorded_assessment.get("disposition") != ELIGIBLE:
        raise BoxRunError("captured request is not eligible for proposal generation")
    evidence = recorded_assessment.get("evidence")
    if not isinstance(evidence, dict):
        raise BoxRunError("captured request evidence is invalid")
    allowed_actions = evidence.get("allowed_actions")
    if not isinstance(allowed_actions, list) or not {
        "invoke_llm",
        "run_external_tools",
        "write_receipts",
    }.issubset(set(allowed_actions)):
        raise BoxRunError("captured request does not authorize the proposal handoff")
    if evidence.get("requested_external_tests") != ["basic_packet_v1"]:
        raise BoxRunError("captured request external packet binding differs")
    request_id = request_body.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise BoxRunError("captured request_id is invalid")

    try:
        current_profile_raw = DEFAULT_PROFILE_PATH.read_bytes()
    except OSError as exc:
        raise BoxRunError(f"controller user profile is unavailable: {exc}") from exc
    if captured["user_profile.json"] != current_profile_raw:
        raise BoxRunError("captured user profile differs from the controller profile")
    try:
        compiled_context = compile_user_profile(captured["user_profile.json"])
    except (OSError, ValueError) as exc:
        raise BoxRunError(f"captured user profile no longer compiles: {exc}") from exc
    context_metadata = _parse_generated_json(
        captured["compiled_user_context.json"],
        "compiled_user_context.json",
    )
    expected_context_metadata = compiled_context.to_dict(include_text=False)
    if context_metadata != expected_context_metadata:
        raise BoxRunError(
            "compiled user context metadata differs from current compilation"
        )
    if receipt.get("user_context") != context_metadata:
        raise BoxRunError("box receipt user context differs from its artifact")
    expected_context_raw = compiled_context.context_text.encode("utf-8")
    if captured["compiled_user_context.txt"] != expected_context_raw:
        raise BoxRunError("compiled user context text differs from current compilation")

    external_receipt = _parse_generated_json(
        captured["external_engine_packet.json"],
        "external_engine_packet.json",
    )
    if receipt.get("external_engine_packet") != external_receipt:
        raise BoxRunError("box receipt external packet differs from its artifact")
    external_errors = validate_pass_receipt(external_receipt)
    if external_errors:
        raise BoxRunError(
            "captured external PASS receipt is invalid: " + "; ".join(external_errors)
        )

    expected_explanation = deterministic_explanation(fresh_assessment).to_dict()
    recorded_explanation = _parse_generated_json(
        captured["deterministic_explanation.json"],
        "deterministic_explanation.json",
    )
    if recorded_explanation != expected_explanation:
        raise BoxRunError("deterministic explanation differs from current assessment")
    if receipt.get("deterministic_explanation") != recorded_explanation:
        raise BoxRunError("box receipt explanation differs from its artifact")
    expected_audit_brief = build_audit_brief(
        fresh_assessment,
        output_contract=compiled_context.output_contract,
    )
    recorded_audit_brief = _parse_generated_json(
        captured["external_audit_brief.json"],
        "external_audit_brief.json",
    )
    if recorded_audit_brief != expected_audit_brief:
        raise BoxRunError("external audit brief differs from current assessment")
    if receipt.get("external_audit_brief") != recorded_audit_brief:
        raise BoxRunError("box receipt audit brief differs from its artifact")

    return VerifiedBoxRun(
        root=root,
        receipt_sha256=_sha256_bytes(receipt_raw),
        request_id=request_id,
        request_sha256=_sha256_bytes(captured["user_request.json"]),
        request_canonical=canonical_json(request_body),
        profile_sha256=_sha256_bytes(captured["user_profile.json"]),
        context_sha256=compiled_context.context_sha256,
        context_text=compiled_context.context_text,
        external_engine_packet_sha256=_sha256_bytes(
            captured["external_engine_packet.json"]
        ),
        artifact_sha256s=tuple(sorted(artifacts.items())),
    )


def run_first_box(
    request_raw: bytes,
    run_dir: Path,
) -> tuple[dict[str, Any], int]:
    """Run the deterministic front door and external packet once.

    The supported entry point selects the owner profile, packet broker, runtime
    pins, and resource bounds.  None of those are request-authored arguments.
    """

    assessment = assess_user_request(request_raw)
    try:
        profile_raw = DEFAULT_PROFILE_PATH.read_bytes()
        context = compile_user_profile(profile_raw)
    except (OSError, ValueError) as exc:
        result = {
            "schema": SCHEMA,
            "disposition": EVALUATION_ERROR,
            "reason": "user_profile_configuration_error",
            "error": str(exc),
            "request_assessment": assessment.to_dict(),
            "external_engine_packet": None,
            "promotion_allowed": False,
            "release_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        return result, EXIT_CODES[EVALUATION_ERROR]

    decision = assessment.to_dict()
    allowed_actions = set(
        action
        for action in assessment.evidence.get("allowed_actions", [])
        if isinstance(action, str)
    )
    if "write_receipts" not in allowed_actions:
        no_write_disposition = (
            BLOCKED
            if assessment.disposition == ELIGIBLE
            else assessment.disposition
        )
        result = {
            "schema": SCHEMA,
            "disposition": no_write_disposition,
            "reason": (
                "receipt_writing_not_authorized"
                if assessment.disposition == ELIGIBLE
                else assessment.reason
            ),
            "request_assessment": decision,
            "external_engine_packet": None,
            "promotion_allowed": False,
            "release_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        return result, EXIT_CODES[no_write_disposition]

    root = Path(run_dir).expanduser().resolve()
    try:
        root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise BoxRunError(f"run directory already exists: {root}") from exc
    except OSError as exc:
        raise BoxRunError(f"could not create run directory: {exc}") from exc

    request_path = root / "user_request.json"
    profile_path = root / "user_profile.json"
    _write_bytes_atomic(request_path, request_raw)
    _write_bytes_atomic(profile_path, profile_raw)

    context_metadata = context.to_dict(include_text=False)
    _write_json_atomic(root / "request_assessment.json", decision)
    _write_json_atomic(root / "compiled_user_context.json", context_metadata)
    _write_bytes_atomic(
        root / "compiled_user_context.txt",
        context.context_text.encode("utf-8"),
    )
    deterministic_advice = deterministic_explanation(decision).to_dict()
    audit_brief = build_audit_brief(
        decision,
        output_contract=context.output_contract,
    )
    _write_json_atomic(root / "deterministic_explanation.json", deterministic_advice)
    _write_json_atomic(root / "external_audit_brief.json", audit_brief)

    external_receipt: dict[str, Any] | None = None
    external_validation_errors: list[str] = []
    if assessment.disposition != ELIGIBLE:
        disposition = assessment.disposition
        reason = "request_did_not_reach_proposal_eligibility"
    elif "run_external_tools" not in allowed_actions:
        disposition = BLOCKED
        reason = "external_tool_execution_not_authorized"
    elif assessment.evidence.get("requested_external_tests") != [
        "basic_packet_v1"
    ]:
        disposition = BLOCKED
        reason = "requested_external_packet_not_bound_to_first_box"
    elif "invoke_llm" not in allowed_actions:
        disposition = BLOCKED
        reason = "untrusted_proposal_generation_not_authorized"
    else:
        try:
            external_receipt = ExternalEnginePacketBroker().run()
        except (OSError, ValueError) as exc:
            external_receipt = {
                "schema": "constraintbox.external-engine-packet-error.v1",
                "status": "EVALUATION_ERROR",
                "reason": "external_packet_broker_exception",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "promotion_allowed": False,
            }
        _write_json_atomic(
            root / "external_engine_packet.json",
            external_receipt,
        )
        external_status = external_receipt.get("status")
        if external_status == "PASS":
            external_validation_errors = list(
                validate_pass_receipt(external_receipt)
            )
            if external_validation_errors:
                disposition = EVALUATION_ERROR
                reason = "external_packet_pass_receipt_invalid"
            else:
                disposition = READY_FOR_PROPOSAL
                reason = "request_and_external_function_packet_passed"
        elif external_status == "PARKED":
            disposition = PARKED
            reason = "external_function_packet_unavailable_or_unresolved"
        elif external_status == "FAIL":
            disposition = BLOCKED
            reason = "external_function_packet_executed_and_failed"
        else:
            disposition = EVALUATION_ERROR
            reason = "external_function_packet_returned_unknown_status"

    artifacts = {}
    for path in sorted(root.iterdir()):
        if path.is_file() and path.name != "box_receipt.json":
            artifacts[path.name] = _sha256_bytes(path.read_bytes())
    result = {
        "schema": SCHEMA,
        "disposition": disposition,
        "reason": reason,
        "request_assessment": decision,
        "user_context": context_metadata,
        "deterministic_explanation": deterministic_advice,
        "external_audit_brief": audit_brief,
        "external_engine_packet": external_receipt,
        "external_receipt_validation_errors": external_validation_errors,
        "artifacts": artifacts,
        "next_step": (
            "untrusted_proposal_generation"
            if disposition == READY_FOR_PROPOSAL
            else "user_resubmission"
            if disposition == PARKED
            else "none"
        ),
        "promotion_allowed": False,
        "release_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json_atomic(root / "box_receipt.json", result)
    return result, EXIT_CODES[disposition]
