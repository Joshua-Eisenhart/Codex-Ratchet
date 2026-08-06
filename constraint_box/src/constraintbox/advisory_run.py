"""Persist an advisory-only explanation beside a verified local box snapshot.

This module deliberately has no edge back into the box controller.  It first
verifies a complete ``box_receipt.json`` and every artifact named by that
receipt, freezes the verified decision, and only then invokes an optional
external explainer.  Provider output is stored in a separate, new directory
and cannot change the box disposition, release state, or promotion state.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Any, Mapping

from .advice import (
    ALLOWED_FIELDS,
    AdviceError,
    accept_external_advice,
    build_audit_brief,
    decision_sha256,
    deterministic_explanation,
)
from .advisory_provider import (
    PROVIDER_REGISTRY,
    RECEIPT_SCHEMA as PROVIDER_RECEIPT_SCHEMA,
    STATE_ACCEPTED,
    STATE_PARKED,
    STATE_REJECTED,
    Transport,
    provider_policy_sha256,
    run_advisory_audit,
)
from .boxrun import (
    CLAIM_CEILING as BOX_CLAIM_CEILING,
    READY_FOR_PROPOSAL,
    SCHEMA as BOX_RECEIPT_SCHEMA,
)
from .external_engine_packet import validate_pass_receipt
from .intake import IntakeError, canonical_json, parse_json_object
from .user_profile import (
    DEFAULT_PROFILE_PATH,
    PROFILE_FIELDS,
    SCHEMA as USER_PROFILE_SCHEMA,
    compile_user_profile,
)
from .user_request import (
    BLOCKED,
    ELIGIBLE,
    EVALUATION_ERROR,
    PARKED,
    ROOT_FIELDS as USER_REQUEST_FIELDS,
    SCHEMA as USER_REQUEST_SCHEMA,
    assess_user_request,
)


FROZEN_DECISION_SCHEMA = "constraintbox.frozen-box-decision.v1"
SIDECAR_RECEIPT_SCHEMA = "constraintbox.advisory-sidecar-receipt.v1"
SIDECAR_ROOT_SCHEMA = "constraintbox.advisory-sidecar-root.v1"

MAX_BOX_RECEIPT_BYTES = 4 * 1024 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 32 * 1024 * 1024
MAX_SIDECAR_FILE_BYTES = 8 * 1024 * 1024

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_BOX_DISPOSITIONS = {
    READY_FOR_PROPOSAL,
    BLOCKED,
    PARKED,
    EVALUATION_ERROR,
}
_REQUEST_DISPOSITIONS = {
    ELIGIBLE,
    BLOCKED,
    PARKED,
    EVALUATION_ERROR,
}
_BOX_RECEIPT_FIELDS = {
    "schema",
    "disposition",
    "reason",
    "request_assessment",
    "user_context",
    "deterministic_explanation",
    "external_audit_brief",
    "external_engine_packet",
    "external_receipt_validation_errors",
    "artifacts",
    "next_step",
    "promotion_allowed",
    "release_allowed",
    "claim_ceiling",
}
_REQUEST_ASSESSMENT_FIELDS = {
    "schema",
    "request_id",
    "disposition",
    "reason",
    "request_sha256",
    "policy_id",
    "policy_sha256",
    "failed_clauses",
    "questions",
    "solver",
    "evidence",
    "claim_ceiling",
    "promotion_allowed",
}
_USER_CONTEXT_FIELDS = {
    "schema",
    "profile_id",
    "profile_version",
    "profile_sha256",
    "context_sha256",
    "pack_receipts",
    "output_contract",
    "inferred_preferences_advisory_only",
    "claim_ceiling",
}
_PACK_RECEIPT_FIELDS = {"name", "path", "sha256", "role"}
_DETERMINISTIC_EXPLANATION_FIELDS = {
    "schema",
    "decision_sha256",
    "advice_sha256",
    "plain_explanation",
    "questions",
    "suggested_resubmission",
    "advisory_only",
    "changes_deterministic_decision",
}
_AUDIT_BRIEF_FIELDS = {
    "schema",
    "decision_sha256",
    "frozen_disposition",
    "frozen_reason",
    "failed_clauses",
    "controller_questions",
    "claim_ceiling",
    "output_contract",
    "allowed_advice_fields",
    "instructions",
    "advisory_only",
}
_BASE_ARTIFACTS = {
    "user_request.json",
    "user_profile.json",
    "request_assessment.json",
    "compiled_user_context.json",
    "compiled_user_context.txt",
    "deterministic_explanation.json",
    "external_audit_brief.json",
}
_OPTIONAL_ARTIFACT = "external_engine_packet.json"
_SIDECAR_ARTIFACTS = {
    "frozen_box_decision.json",
    "advisory_provider_receipt.json",
}
_SIDECAR_RECEIPT_FIELDS = {
    "schema",
    "provider_state",
    "provider_reason_code",
    "provider",
    "frozen_box_disposition",
    "frozen_box_reason",
    "box_receipt_sha256",
    "frozen_decision_sha256",
    "output_contract",
    "advisory_only",
    "changes_box_decision",
    "decision_authority",
    "release_allowed",
    "promotion_allowed",
    "artifacts",
    "receipt_sha256",
    "root_sha256",
    "claim_ceiling",
}
_FROZEN_DECISION_FIELDS = {
    "schema",
    "box_receipt_sha256",
    "box_schema",
    "disposition",
    "reason",
    "failed_clauses",
    "questions",
    "request_assessment",
    "deterministic_explanation",
    "external_audit_brief",
    "user_context",
    "output_contract",
    "external_engine_packet",
    "external_receipt_validation_errors",
    "box_artifacts",
    "claim_ceiling",
    "promotion_allowed",
    "release_allowed",
}
_PROVIDER_RECEIPT_FIELDS = {
    "schema",
    "provider_state",
    "reason_code",
    "provider",
    "provider_sha256",
    "provider_policy_sha256",
    "endpoint",
    "endpoint_sha256",
    "requested_model",
    "requested_model_sha256",
    "returned_model",
    "returned_model_sha256",
    "returned_model_matches_request",
    "request_sha256",
    "response_sha256",
    "decision_sha256",
    "advice_sha256",
    "advice",
    "http_status",
    "response_id",
    "finish_reason",
    "usage",
    "cost_status",
    "provider_selection_basis",
    "billing_verified",
    "advisory_only",
    "decision_authority",
    "release_allowed",
    "promotion_allowed",
}
_ADVICE_RECEIPT_FIELDS = {
    "schema",
    "decision_sha256",
    "advice_sha256",
    "plain_explanation",
    "questions",
    "suggested_resubmission",
    "advisory_only",
    "changes_deterministic_decision",
}
_EXIT_CODES = {
    STATE_ACCEPTED: 0,
    STATE_REJECTED: 1,
    STATE_PARKED: 4,
}
_SIDECAR_CLAIM_CEILING = (
    "advisory explanation of one already-frozen box decision only; the "
    "provider cannot change a disposition, retry state, gate result, release, "
    "promotion, engine-readiness claim, or scientific claim"
)


class AdvisoryRunError(ValueError):
    """Raised before provider execution when a source or target is unsafe."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_exact_fields(
    value: object,
    fields: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise AdvisoryRunError(f"{label} has fields outside its exact schema")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdvisoryRunError(f"{label} must be a nonempty string")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise AdvisoryRunError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise AdvisoryRunError(f"{label} must be a list of nonempty strings")
    return value


def _read_regular_bytes(path: Path, *, maximum: int, label: str) -> bytes:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise AdvisoryRunError(f"{label} is unavailable or unsafe") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise AdvisoryRunError(f"{label} must be a regular non-symlink file")
        if metadata.st_size < 0 or metadata.st_size > maximum:
            raise AdvisoryRunError(f"{label} exceeds its byte bound")
        chunks: list[bytes] = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise AdvisoryRunError(f"{label} exceeds its byte bound")
        raw = b"".join(chunks)
        if observed != metadata.st_size:
            raise AdvisoryRunError(f"{label} changed while it was read")
        return raw
    finally:
        os.close(descriptor)


def _read_regular_at(
    directory_descriptor: int,
    name: str,
    *,
    maximum: int,
    label: str,
) -> bytes:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except OSError as exc:
        raise AdvisoryRunError(
            f"{label} must be a regular non-symlink file and is unavailable "
            "or unsafe"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise AdvisoryRunError(
                f"{label} must be a singly-linked regular non-symlink file"
            )
        if before.st_size < 0 or before.st_size > maximum:
            raise AdvisoryRunError(f"{label} exceeds its byte bound")
        chunks: list[bytes] = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise AdvisoryRunError(f"{label} exceeds its byte bound")
        after = os.fstat(descriptor)
        stable_fields = (
            "st_dev",
            "st_ino",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
        if any(
            getattr(before, field) != getattr(after, field)
            for field in stable_fields
        ):
            raise AdvisoryRunError(f"{label} changed while it was read")
        raw = b"".join(chunks)
        if len(raw) != before.st_size:
            raise AdvisoryRunError(f"{label} changed size while it was read")
        return raw
    finally:
        os.close(descriptor)


def _parse_strict_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        return parse_json_object(raw)
    except IntakeError as exc:
        raise AdvisoryRunError(f"{label} is not strict JSON") from exc


def _parse_canonical_object(raw: bytes, label: str) -> dict[str, Any]:
    value = _parse_strict_object(raw, label)
    if raw != canonical_json(value) + b"\n":
        raise AdvisoryRunError(f"{label} is not canonical generated JSON")
    return value


def _resolve_box_root(box_run: Path) -> Path:
    candidate = Path(box_run).expanduser()
    try:
        candidate_metadata = candidate.lstat()
    except OSError as exc:
        raise AdvisoryRunError("box run is unavailable") from exc
    if stat.S_ISLNK(candidate_metadata.st_mode):
        raise AdvisoryRunError("box run root must not be a symlink")
    if not stat.S_ISDIR(candidate_metadata.st_mode):
        raise AdvisoryRunError("box run root must be a directory")
    try:
        return candidate.resolve(strict=True)
    except OSError as exc:
        raise AdvisoryRunError("box run root cannot be resolved") from exc


def _enumerate_box_entries(root: Path) -> dict[str, Path]:
    entries: dict[str, Path] = {}
    try:
        with os.scandir(root) as iterator:
            for entry in iterator:
                metadata = entry.stat(follow_symlinks=False)
                if entry.is_symlink() or not stat.S_ISREG(metadata.st_mode):
                    raise AdvisoryRunError(
                        f"box artifact {entry.name!r} must be a regular "
                        "non-symlink file"
                    )
                entries[entry.name] = root / entry.name
    except AdvisoryRunError:
        raise
    except OSError as exc:
        raise AdvisoryRunError("box run could not be enumerated") from exc
    return entries


def _capture_box_entries(root: Path) -> dict[str, bytes]:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        directory_descriptor = os.open(root, flags)
    except OSError as exc:
        raise AdvisoryRunError("box run directory could not be opened") from exc
    try:
        metadata = os.fstat(directory_descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise AdvisoryRunError("box run root must remain a directory")
        names = set(os.listdir(directory_descriptor))
        if "box_receipt.json" not in names:
            raise AdvisoryRunError("box run is missing box_receipt.json")
        captured: dict[str, bytes] = {}
        total_size = 0
        for name in sorted(names):
            maximum = (
                MAX_BOX_RECEIPT_BYTES
                if name == "box_receipt.json"
                else MAX_ARTIFACT_BYTES
            )
            raw = _read_regular_at(
                directory_descriptor,
                name,
                maximum=maximum,
                label=f"box artifact {name}",
            )
            if name != "box_receipt.json":
                total_size += len(raw)
                if total_size > MAX_TOTAL_ARTIFACT_BYTES:
                    raise AdvisoryRunError(
                        "box artifacts exceed their total byte bound"
                    )
            captured[name] = raw
        return captured
    finally:
        os.close(directory_descriptor)


def _validate_request_assessment(value: object) -> dict[str, Any]:
    assessment = _require_exact_fields(
        value,
        _REQUEST_ASSESSMENT_FIELDS,
        "request assessment",
    )
    if assessment["schema"] != "constraintbox.user-request-assessment.v1":
        raise AdvisoryRunError("request assessment schema is invalid")
    request_id = assessment["request_id"]
    if request_id is not None:
        _require_text(request_id, "request assessment request_id")
    if assessment["disposition"] not in _REQUEST_DISPOSITIONS:
        raise AdvisoryRunError("request assessment disposition is invalid")
    _require_text(assessment["reason"], "request assessment reason")
    _require_sha256(
        assessment["request_sha256"],
        "request assessment request_sha256",
    )
    _require_text(assessment["policy_id"], "request assessment policy_id")
    _require_sha256(
        assessment["policy_sha256"],
        "request assessment policy_sha256",
    )
    _require_string_list(
        assessment["failed_clauses"],
        "request assessment failed_clauses",
    )
    _require_string_list(
        assessment["questions"],
        "request assessment questions",
    )
    if assessment["solver"] is not None and not isinstance(
        assessment["solver"], dict
    ):
        raise AdvisoryRunError("request assessment solver must be an object or null")
    if not isinstance(assessment["evidence"], dict):
        raise AdvisoryRunError("request assessment evidence must be an object")
    _require_text(
        assessment["claim_ceiling"],
        "request assessment claim_ceiling",
    )
    if assessment["promotion_allowed"] is not False:
        raise AdvisoryRunError("request assessment promotion must remain false")
    return assessment


def _validate_user_context(value: object) -> dict[str, Any]:
    context = _require_exact_fields(
        value,
        _USER_CONTEXT_FIELDS,
        "compiled user context",
    )
    if context["schema"] != "constraintbox.compiled-user-context.v1":
        raise AdvisoryRunError("compiled user context schema is invalid")
    _require_text(context["profile_id"], "compiled user context profile_id")
    version = context["profile_version"]
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version < 1
    ):
        raise AdvisoryRunError(
            "compiled user context profile_version must be a positive integer"
        )
    _require_sha256(
        context["profile_sha256"],
        "compiled user context profile_sha256",
    )
    _require_sha256(
        context["context_sha256"],
        "compiled user context context_sha256",
    )
    packs = context["pack_receipts"]
    if not isinstance(packs, list):
        raise AdvisoryRunError("compiled user context pack_receipts must be a list")
    seen: set[str] = set()
    for index, item in enumerate(packs):
        row = _require_exact_fields(
            item,
            _PACK_RECEIPT_FIELDS,
            f"compiled user context pack_receipts[{index}]",
        )
        name = _require_text(
            row["name"],
            f"compiled user context pack_receipts[{index}].name",
        )
        if name in seen:
            raise AdvisoryRunError("compiled user context pack names must be unique")
        seen.add(name)
        _require_text(
            row["path"],
            f"compiled user context pack_receipts[{index}].path",
        )
        _require_sha256(
            row["sha256"],
            f"compiled user context pack_receipts[{index}].sha256",
        )
        _require_text(
            row["role"],
            f"compiled user context pack_receipts[{index}].role",
        )
    output_contract = _require_string_list(
        context["output_contract"],
        "compiled user context output_contract",
    )
    if output_contract != sorted(set(output_contract)):
        raise AdvisoryRunError(
            "compiled user context output_contract must be sorted and unique"
        )
    if context["inferred_preferences_advisory_only"] is not True:
        raise AdvisoryRunError(
            "compiled user context inferred preferences must remain advisory"
        )
    _require_text(
        context["claim_ceiling"],
        "compiled user context claim_ceiling",
    )
    return context


def _validate_explanation(value: object) -> dict[str, Any]:
    explanation = _require_exact_fields(
        value,
        _DETERMINISTIC_EXPLANATION_FIELDS,
        "deterministic explanation",
    )
    if explanation["schema"] != "constraintbox.audit-advice.v1":
        raise AdvisoryRunError("deterministic explanation schema is invalid")
    _require_sha256(
        explanation["decision_sha256"],
        "deterministic explanation decision_sha256",
    )
    _require_sha256(
        explanation["advice_sha256"],
        "deterministic explanation advice_sha256",
    )
    _require_text(
        explanation["plain_explanation"],
        "deterministic explanation plain_explanation",
    )
    _require_string_list(
        explanation["questions"],
        "deterministic explanation questions",
    )
    if not isinstance(explanation["suggested_resubmission"], dict):
        raise AdvisoryRunError(
            "deterministic explanation suggested_resubmission must be an object"
        )
    if explanation["advisory_only"] is not True:
        raise AdvisoryRunError("deterministic explanation must remain advisory")
    if explanation["changes_deterministic_decision"] is not False:
        raise AdvisoryRunError(
            "deterministic explanation cannot change the decision"
        )
    return explanation


def _validate_audit_brief(value: object) -> dict[str, Any]:
    brief = _require_exact_fields(
        value,
        _AUDIT_BRIEF_FIELDS,
        "external audit brief",
    )
    if brief["schema"] != "constraintbox.audit-brief.v1":
        raise AdvisoryRunError("external audit brief schema is invalid")
    _require_sha256(
        brief["decision_sha256"],
        "external audit brief decision_sha256",
    )
    if brief["frozen_disposition"] not in _REQUEST_DISPOSITIONS:
        raise AdvisoryRunError("external audit brief disposition is invalid")
    _require_text(brief["frozen_reason"], "external audit brief frozen_reason")
    _require_string_list(
        brief["failed_clauses"],
        "external audit brief failed_clauses",
    )
    _require_string_list(
        brief["controller_questions"],
        "external audit brief controller_questions",
    )
    _require_text(brief["claim_ceiling"], "external audit brief claim_ceiling")
    _require_string_list(
        brief["output_contract"],
        "external audit brief output_contract",
    )
    allowed_fields = _require_string_list(
        brief["allowed_advice_fields"],
        "external audit brief allowed_advice_fields",
    )
    if allowed_fields != sorted(ALLOWED_FIELDS):
        raise AdvisoryRunError("external audit brief advice fields are invalid")
    _require_string_list(
        brief["instructions"],
        "external audit brief instructions",
    )
    if brief["advisory_only"] is not True:
        raise AdvisoryRunError("external audit brief must remain advisory")
    return brief


def _validate_profile_binding(
    profile_raw: bytes,
    context: dict[str, Any],
) -> None:
    profile = _parse_strict_object(profile_raw, "user profile artifact")
    _require_exact_fields(profile, PROFILE_FIELDS, "user profile artifact")
    if profile["schema"] != USER_PROFILE_SCHEMA:
        raise AdvisoryRunError("user profile artifact schema is invalid")
    if _sha256(canonical_json(profile)) != context["profile_sha256"]:
        raise AdvisoryRunError("user profile digest differs from compiled context")
    if profile["profile_id"] != context["profile_id"]:
        raise AdvisoryRunError("user profile id differs from compiled context")
    if profile["profile_version"] != context["profile_version"]:
        raise AdvisoryRunError("user profile version differs from compiled context")
    if profile["claim_ceiling"] != context["claim_ceiling"]:
        raise AdvisoryRunError(
            "user profile claim ceiling differs from compiled context"
        )
    requirements = profile["owner_requirements"]
    if not isinstance(requirements, list):
        raise AdvisoryRunError("user profile owner_requirements must be a list")
    expected_contract: list[str] = []
    for index, row in enumerate(requirements):
        if not isinstance(row, dict):
            raise AdvisoryRunError(
                f"user profile owner_requirements[{index}] must be an object"
            )
        rule = row.get("output_rule")
        if not isinstance(rule, str) or not rule.strip():
            raise AdvisoryRunError(
                f"user profile owner_requirements[{index}] output_rule is invalid"
            )
        expected_contract.append(rule)
    if sorted(set(expected_contract)) != context["output_contract"]:
        raise AdvisoryRunError(
            "user profile output contract differs from compiled context"
        )
    profile_packs = profile["mmm_packs"]
    if not isinstance(profile_packs, list):
        raise AdvisoryRunError("user profile mmm_packs must be a list")
    expected_packs: list[tuple[object, object, object]] = []
    for index, row in enumerate(profile_packs):
        if not isinstance(row, dict) or set(row) != {"name", "sha256", "role"}:
            raise AdvisoryRunError(
                f"user profile mmm_packs[{index}] has invalid fields"
            )
        expected_packs.append((row["name"], row["sha256"], row["role"]))
    observed_packs = [
        (row["name"], row["sha256"], row["role"])
        for row in context["pack_receipts"]
    ]
    if observed_packs != expected_packs:
        raise AdvisoryRunError(
            "user profile MMM packs differ from compiled context"
        )


def _validate_box_snapshot(root: Path) -> tuple[
    dict[str, Any],
    bytes,
    dict[str, bytes],
]:
    captured = _capture_box_entries(root)
    receipt_raw = captured["box_receipt.json"]
    receipt = _parse_canonical_object(receipt_raw, "box receipt")
    _require_exact_fields(receipt, _BOX_RECEIPT_FIELDS, "box receipt")
    if receipt["schema"] != BOX_RECEIPT_SCHEMA:
        raise AdvisoryRunError("box receipt schema is invalid")
    if receipt["disposition"] not in _BOX_DISPOSITIONS:
        raise AdvisoryRunError("box receipt disposition is invalid")
    _require_text(receipt["reason"], "box receipt reason")
    if receipt["promotion_allowed"] is not False:
        raise AdvisoryRunError("box receipt promotion must remain false")
    if receipt["release_allowed"] is not False:
        raise AdvisoryRunError("box receipt release must remain false")
    if receipt["claim_ceiling"] != BOX_CLAIM_CEILING:
        raise AdvisoryRunError("box receipt claim ceiling is invalid")

    artifacts = receipt["artifacts"]
    if not isinstance(artifacts, dict):
        raise AdvisoryRunError("box receipt artifacts must be an object")
    expected_artifacts = set(_BASE_ARTIFACTS)
    external_packet = receipt["external_engine_packet"]
    if external_packet is not None:
        expected_artifacts.add(_OPTIONAL_ARTIFACT)
    if set(artifacts) != expected_artifacts:
        raise AdvisoryRunError("box receipt artifact names are not exact")
    if set(captured) != expected_artifacts | {"box_receipt.json"}:
        raise AdvisoryRunError("box run contents differ from the receipt")

    artifact_raw: dict[str, bytes] = {}
    for name in sorted(expected_artifacts):
        _require_sha256(artifacts[name], f"box artifact digest {name}")
        raw = captured[name]
        if _sha256(raw) != artifacts[name]:
            raise AdvisoryRunError(f"box artifact digest mismatch: {name}")
        artifact_raw[name] = raw

    assessment = _validate_request_assessment(receipt["request_assessment"])
    context = _validate_user_context(receipt["user_context"])
    explanation = _validate_explanation(receipt["deterministic_explanation"])
    audit_brief = _validate_audit_brief(receipt["external_audit_brief"])
    validation_errors = _require_string_list(
        receipt["external_receipt_validation_errors"],
        "external receipt validation errors",
    )
    if receipt["next_step"] not in {
        "untrusted_proposal_generation",
        "user_resubmission",
        "none",
    }:
        raise AdvisoryRunError("box receipt next_step is invalid")
    expected_next_step = (
        "untrusted_proposal_generation"
        if receipt["disposition"] == READY_FOR_PROPOSAL
        else "user_resubmission"
        if receipt["disposition"] == PARKED
        else "none"
    )
    if receipt["next_step"] != expected_next_step:
        raise AdvisoryRunError("box receipt next_step is inconsistent")

    embedded_json = {
        "request_assessment.json": assessment,
        "compiled_user_context.json": context,
        "deterministic_explanation.json": explanation,
        "external_audit_brief.json": audit_brief,
    }
    for name, embedded in embedded_json.items():
        parsed = _parse_canonical_object(
            artifact_raw[name],
            f"box artifact {name}",
        )
        if parsed != embedded:
            raise AdvisoryRunError(f"embedded object differs from artifact: {name}")

    request_raw = artifact_raw["user_request.json"]
    request = _parse_strict_object(request_raw, "user request artifact")
    _require_exact_fields(
        request,
        USER_REQUEST_FIELDS,
        "user request artifact",
    )
    if request["schema"] != USER_REQUEST_SCHEMA:
        raise AdvisoryRunError("user request artifact schema is invalid")
    if _sha256(request_raw) != assessment["request_sha256"]:
        raise AdvisoryRunError(
            "user request artifact digest differs from request assessment"
        )
    fresh_assessment = assess_user_request(request_raw).to_dict()
    if fresh_assessment != assessment:
        raise AdvisoryRunError(
            "request assessment differs from the current controller policy"
        )

    profile_raw = artifact_raw["user_profile.json"]
    try:
        current_profile_raw = DEFAULT_PROFILE_PATH.read_bytes()
    except OSError as exc:
        raise AdvisoryRunError("current controller profile is unavailable") from exc
    if profile_raw != current_profile_raw:
        raise AdvisoryRunError(
            "user profile artifact differs from the current controller profile"
        )
    _validate_profile_binding(profile_raw, context)
    try:
        compiled_context = compile_user_profile(profile_raw)
    except (OSError, ValueError) as exc:
        raise AdvisoryRunError(
            "user profile artifact no longer compiles under current policy"
        ) from exc
    if compiled_context.to_dict(include_text=False) != context:
        raise AdvisoryRunError(
            "compiled user context differs from current profile compilation"
        )
    context_text_raw = artifact_raw["compiled_user_context.txt"]
    try:
        context_text = context_text_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdvisoryRunError("compiled user context text is not UTF-8") from exc
    if not context_text.strip():
        raise AdvisoryRunError("compiled user context text is empty")
    if _sha256(context_text_raw) != context["context_sha256"]:
        raise AdvisoryRunError("compiled user context text digest is invalid")
    if context_text != compiled_context.context_text:
        raise AdvisoryRunError(
            "compiled user context text differs from current compilation"
        )

    expected_explanation = deterministic_explanation(assessment).to_dict()
    if explanation != expected_explanation:
        raise AdvisoryRunError(
            "deterministic explanation is not bound to request assessment"
        )
    output_contract = tuple(context["output_contract"])
    expected_brief = build_audit_brief(
        assessment,
        output_contract=output_contract,
    )
    if audit_brief != expected_brief:
        raise AdvisoryRunError(
            "external audit brief is not bound to request assessment"
        )

    if external_packet is None:
        if _OPTIONAL_ARTIFACT in artifact_raw:
            raise AdvisoryRunError("null external packet has an artifact")
    else:
        if not isinstance(external_packet, dict):
            raise AdvisoryRunError("external engine packet must be an object or null")
        parsed_packet = _parse_canonical_object(
            artifact_raw[_OPTIONAL_ARTIFACT],
            "external engine packet artifact",
        )
        if parsed_packet != external_packet:
            raise AdvisoryRunError(
                "embedded external engine packet differs from its artifact"
            )
        _require_text(
            external_packet.get("schema"),
            "external engine packet schema",
        )
        if external_packet.get("status") not in {
            "PASS",
            "FAIL",
            "PARKED",
            "EVALUATION_ERROR",
        }:
            raise AdvisoryRunError("external engine packet status is invalid")
        if external_packet.get("external_system") is not True:
            raise AdvisoryRunError("external engine packet must remain external")
        if external_packet.get("kernel_membership") != "EXTERNAL_NOT_CB_KERNEL":
            raise AdvisoryRunError("external engine packet entered the CB kernel")
        if external_packet.get("promotion_allowed") is not False:
            raise AdvisoryRunError(
                "external engine packet promotion must remain false"
            )
        if external_packet.get("status") == "PASS":
            current_external_errors = list(
                validate_pass_receipt(external_packet)
            )
            if current_external_errors != validation_errors:
                raise AdvisoryRunError(
                    "external PASS receipt validation differs from the "
                    "recorded errors"
                )

    if receipt["disposition"] == READY_FOR_PROPOSAL:
        if assessment["disposition"] != ELIGIBLE:
            raise AdvisoryRunError(
                "ready box receipt lacks an eligible request assessment"
            )
        if (
            not isinstance(external_packet, dict)
            or external_packet.get("status") != "PASS"
        ):
            raise AdvisoryRunError("ready box receipt lacks a passing packet")
        if validation_errors:
            raise AdvisoryRunError(
                "ready box receipt has external validation errors"
            )
        if receipt["reason"] != "request_and_external_function_packet_passed":
            raise AdvisoryRunError("ready box receipt reason is inconsistent")

    return receipt, receipt_raw, artifact_raw


def _build_frozen_decision(
    receipt: dict[str, Any],
    receipt_raw: bytes,
) -> dict[str, Any]:
    assessment = receipt["request_assessment"]
    context = receipt["user_context"]
    return {
        "schema": FROZEN_DECISION_SCHEMA,
        "box_receipt_sha256": _sha256(receipt_raw),
        "box_schema": receipt["schema"],
        "disposition": receipt["disposition"],
        "reason": receipt["reason"],
        "failed_clauses": list(assessment["failed_clauses"]),
        "questions": list(assessment["questions"]),
        "request_assessment": assessment,
        "deterministic_explanation": receipt["deterministic_explanation"],
        "external_audit_brief": receipt["external_audit_brief"],
        "user_context": context,
        "output_contract": list(context["output_contract"]),
        "external_engine_packet": receipt["external_engine_packet"],
        "external_receipt_validation_errors": list(
            receipt["external_receipt_validation_errors"]
        ),
        "box_artifacts": dict(receipt["artifacts"]),
        "claim_ceiling": receipt["claim_ceiling"],
        "promotion_allowed": False,
        "release_allowed": False,
    }


def _resolve_new_sidecar_root(sidecar_run: Path, box_root: Path) -> Path:
    candidate = Path(sidecar_run).expanduser()
    if candidate.exists() or candidate.is_symlink():
        raise AdvisoryRunError("sidecar run directory already exists")
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise AdvisoryRunError("sidecar run path cannot be resolved") from exc
    try:
        resolved.relative_to(box_root)
    except ValueError:
        pass
    else:
        raise AdvisoryRunError("sidecar run must be outside the box run")
    return resolved


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _discard_staging_directory(root: Path) -> None:
    """Remove only this module's flat, unpublished staging directory."""

    try:
        metadata = root.lstat()
    except OSError:
        return
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        return
    try:
        with os.scandir(root) as iterator:
            entries = list(iterator)
        if any(
            entry.is_symlink()
            or not stat.S_ISREG(entry.stat(follow_symlinks=False).st_mode)
            for entry in entries
        ):
            return
        for entry in entries:
            (root / entry.name).unlink()
        root.rmdir()
    except OSError:
        return


def _publish_directory_exclusive(source: Path, target: Path) -> None:
    """Atomically publish a directory and fail if the target now exists."""

    library = ctypes.CDLL(None, use_errno=True)
    source_raw = os.fsencode(source)
    target_raw = os.fsencode(target)
    result: int
    if sys.platform == "darwin":
        rename_exclusive = library.renamex_np
        rename_exclusive.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename_exclusive.restype = ctypes.c_int
        result = int(
            rename_exclusive(
                source_raw,
                target_raw,
                0x00000004,  # RENAME_EXCL from <sys/stdio.h>.
            )
        )
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename_no_replace = library.renameat2
        rename_no_replace.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename_no_replace.restype = ctypes.c_int
        result = int(
            rename_no_replace(
                -100,  # AT_FDCWD on Linux.
                source_raw,
                -100,
                target_raw,
                0x00000001,  # RENAME_NOREPLACE from <linux/fs.h>.
            )
        )
    else:
        raise AdvisoryRunError(
            "exclusive atomic directory publication is unavailable"
        )
    if result == 0:
        return
    observed_errno = ctypes.get_errno()
    if observed_errno in {errno.EEXIST, errno.ENOTEMPTY}:
        raise AdvisoryRunError("sidecar run directory already exists")
    raise AdvisoryRunError(
        "sidecar directory could not be published exclusively: "
        + os.strerror(observed_errno)
    )


def _write_exclusive_json(
    root: Path,
    name: str,
    value: dict[str, Any],
) -> bytes:
    raw = canonical_json(value) + b"\n"
    if len(raw) > MAX_SIDECAR_FILE_BYTES:
        raise AdvisoryRunError(f"sidecar artifact {name} exceeds its byte bound")
    target = root / name
    temporary = root / f".{name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    linked = False
    try:
        view = memoryview(raw)
        written = 0
        while written < len(view):
            amount = os.write(descriptor, view[written:])
            if amount <= 0:
                raise OSError("short write")
            written += amount
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(temporary, target, follow_symlinks=False)
        linked = True
        _fsync_directory(root)
    except FileExistsError as exc:
        raise AdvisoryRunError(f"sidecar artifact already exists: {name}") from exc
    except OSError as exc:
        raise AdvisoryRunError(f"could not persist sidecar artifact: {name}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            if not linked:
                raise
        if linked:
            _fsync_directory(root)
    return raw


def _receipt_digest_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in receipt.items()
        if key not in {"receipt_sha256", "root_sha256"}
    }


def _root_digest(
    receipt_sha256: str,
    artifacts: dict[str, str],
) -> str:
    return _sha256(
        canonical_json(
            {
                "schema": SIDECAR_ROOT_SCHEMA,
                "receipt_sha256": receipt_sha256,
                "artifacts": artifacts,
            }
        )
    )


def _validate_frozen_decision(value: object) -> dict[str, Any]:
    frozen = _require_exact_fields(
        value,
        _FROZEN_DECISION_FIELDS,
        "persisted frozen box decision",
    )
    if frozen["schema"] != FROZEN_DECISION_SCHEMA:
        raise AdvisoryRunError("persisted frozen decision schema is invalid")
    if frozen["box_schema"] != BOX_RECEIPT_SCHEMA:
        raise AdvisoryRunError("persisted frozen box schema is invalid")
    _require_sha256(
        frozen["box_receipt_sha256"],
        "persisted frozen box receipt digest",
    )
    if frozen["disposition"] not in _BOX_DISPOSITIONS:
        raise AdvisoryRunError("persisted frozen disposition is invalid")
    _require_text(frozen["reason"], "persisted frozen reason")
    _require_string_list(
        frozen["failed_clauses"],
        "persisted frozen failed_clauses",
    )
    _require_string_list(frozen["questions"], "persisted frozen questions")
    assessment = _validate_request_assessment(frozen["request_assessment"])
    context = _validate_user_context(frozen["user_context"])
    _validate_explanation(frozen["deterministic_explanation"])
    _validate_audit_brief(frozen["external_audit_brief"])
    if frozen["failed_clauses"] != assessment["failed_clauses"]:
        raise AdvisoryRunError(
            "persisted frozen failed clauses differ from the assessment"
        )
    if frozen["questions"] != assessment["questions"]:
        raise AdvisoryRunError(
            "persisted frozen questions differ from the assessment"
        )
    if frozen["output_contract"] != context["output_contract"]:
        raise AdvisoryRunError(
            "persisted frozen output contract differs from the user context"
        )
    if not isinstance(frozen["external_engine_packet"], (dict, type(None))):
        raise AdvisoryRunError(
            "persisted frozen external packet must be an object or null"
        )
    _require_string_list(
        frozen["external_receipt_validation_errors"],
        "persisted frozen external validation errors",
    )
    artifacts = frozen["box_artifacts"]
    artifact_names = set(artifacts) if isinstance(artifacts, dict) else set()
    if not isinstance(artifacts, dict) or artifact_names not in (
        set(_BASE_ARTIFACTS),
        set(_BASE_ARTIFACTS) | {_OPTIONAL_ARTIFACT},
    ):
        raise AdvisoryRunError("persisted frozen box artifacts are invalid")
    for name, digest in artifacts.items():
        _require_sha256(digest, f"persisted frozen box artifact {name}")
    if frozen["claim_ceiling"] != BOX_CLAIM_CEILING:
        raise AdvisoryRunError("persisted frozen claim ceiling is invalid")
    if frozen["deterministic_explanation"] != deterministic_explanation(
        assessment
    ).to_dict():
        raise AdvisoryRunError(
            "persisted frozen explanation differs from its assessment"
        )
    if frozen["external_audit_brief"] != build_audit_brief(
        assessment,
        output_contract=tuple(context["output_contract"]),
    ):
        raise AdvisoryRunError(
            "persisted frozen audit brief differs from its assessment"
        )
    has_packet = frozen["external_engine_packet"] is not None
    if has_packet != (_OPTIONAL_ARTIFACT in artifacts):
        raise AdvisoryRunError(
            "persisted frozen packet differs from its artifact index"
        )
    if frozen["disposition"] == READY_FOR_PROPOSAL:
        packet = frozen["external_engine_packet"]
        if (
            assessment["disposition"] != ELIGIBLE
            or not isinstance(packet, dict)
            or packet.get("status") != "PASS"
            or frozen["external_receipt_validation_errors"]
        ):
            raise AdvisoryRunError(
                "persisted frozen READY decision lacks its required evidence"
            )
    if frozen["promotion_allowed"] is not False:
        raise AdvisoryRunError("persisted frozen promotion must remain false")
    if frozen["release_allowed"] is not False:
        raise AdvisoryRunError("persisted frozen release must remain false")
    return frozen


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, label)


def _optional_sha256(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _require_sha256(value, label)


def _validate_provider_receipt(
    value: object,
    *,
    frozen_decision: dict[str, Any],
) -> dict[str, Any]:
    provider = _require_exact_fields(
        value,
        _PROVIDER_RECEIPT_FIELDS,
        "persisted advisory provider receipt",
    )
    if provider["schema"] != PROVIDER_RECEIPT_SCHEMA:
        raise AdvisoryRunError("persisted provider receipt schema is invalid")
    if provider["provider_state"] not in {
        STATE_ACCEPTED,
        STATE_PARKED,
        STATE_REJECTED,
    }:
        raise AdvisoryRunError("persisted provider state is invalid")
    _require_text(provider["reason_code"], "persisted provider reason_code")
    provider_name = _require_text(provider["provider"], "persisted provider")
    provider_digest = _require_sha256(
        provider["provider_sha256"],
        "persisted provider name digest",
    )
    if provider_digest != _sha256(provider_name.encode("utf-8")):
        raise AdvisoryRunError("persisted provider name digest is invalid")
    policy_digest = _optional_sha256(
        provider["provider_policy_sha256"],
        "persisted provider policy digest",
    )
    spec = PROVIDER_REGISTRY.get(provider_name)
    if spec is not None:
        if policy_digest != provider_policy_sha256(provider_name):
            raise AdvisoryRunError(
                "registered provider receipt policy digest is invalid"
            )
        if provider["endpoint"] != spec.endpoint:
            raise AdvisoryRunError(
                "registered provider receipt endpoint is invalid"
            )
        if provider["requested_model"] != spec.model:
            raise AdvisoryRunError(
                "registered provider receipt model is invalid"
            )
        if provider["provider_selection_basis"] != spec.selection_basis:
            raise AdvisoryRunError(
                "registered provider selection basis is invalid"
            )
    elif policy_digest is not None or any(
        provider[field] is not None
        for field in (
            "endpoint",
            "endpoint_sha256",
            "requested_model",
            "requested_model_sha256",
            "provider_selection_basis",
        )
    ):
        raise AdvisoryRunError(
            "unknown provider receipt has an invented route or policy"
        )
    for value_field, digest_field in (
        ("endpoint", "endpoint_sha256"),
        ("requested_model", "requested_model_sha256"),
        ("returned_model", "returned_model_sha256"),
    ):
        text_value = _optional_text(
            provider[value_field],
            f"persisted provider {value_field}",
        )
        digest_value = _optional_sha256(
            provider[digest_field],
            f"persisted provider {digest_field}",
        )
        if (text_value is None) != (digest_value is None):
            raise AdvisoryRunError(
                f"persisted provider {value_field} digest pairing is invalid"
            )
        if (
            text_value is not None
            and digest_value != _sha256(text_value.encode("utf-8"))
        ):
            raise AdvisoryRunError(
                f"persisted provider {value_field} digest is invalid"
            )
    returned_matches = provider["returned_model_matches_request"]
    if returned_matches is not None and not isinstance(returned_matches, bool):
        raise AdvisoryRunError(
            "persisted returned-model match state must be boolean or null"
        )
    for field in (
        "request_sha256",
        "response_sha256",
        "decision_sha256",
        "advice_sha256",
    ):
        _optional_sha256(provider[field], f"persisted provider {field}")
    http_status = provider["http_status"]
    if http_status is not None and (
        not isinstance(http_status, int) or isinstance(http_status, bool)
    ):
        raise AdvisoryRunError("persisted provider HTTP status is invalid")
    _optional_text(provider["response_id"], "persisted provider response_id")
    _optional_text(
        provider["finish_reason"],
        "persisted provider finish_reason",
    )
    if provider["usage"] is not None and not isinstance(provider["usage"], dict):
        raise AdvisoryRunError("persisted provider usage must be an object or null")
    if provider["cost_status"] not in {
        "UNREPORTED",
        "REPORTED_ZERO",
        "REPORTED_NONZERO",
        "REPORTED_UNRESOLVED",
    }:
        raise AdvisoryRunError("persisted provider cost_status is invalid")
    _optional_text(
        provider["provider_selection_basis"],
        "persisted provider selection basis",
    )
    if provider["billing_verified"] is not False:
        raise AdvisoryRunError("persisted provider billing cannot be verified")
    for field, expected in (
        ("advisory_only", True),
        ("decision_authority", False),
        ("release_allowed", False),
        ("promotion_allowed", False),
    ):
        if provider[field] is not expected:
            raise AdvisoryRunError(
                f"persisted provider authority field is invalid: {field}"
            )

    advice = provider["advice"]
    if provider["provider_state"] == STATE_ACCEPTED:
        advice_body = _require_exact_fields(
            advice,
            _ADVICE_RECEIPT_FIELDS,
            "persisted provider advice",
        )
        if advice_body["schema"] != "constraintbox.audit-advice.v1":
            raise AdvisoryRunError("persisted provider advice schema is invalid")
        _require_sha256(
            advice_body["decision_sha256"],
            "persisted provider advice decision digest",
        )
        _require_sha256(
            advice_body["advice_sha256"],
            "persisted provider advice digest",
        )
        _require_text(
            advice_body["plain_explanation"],
            "persisted provider plain explanation",
        )
        _require_string_list(
            advice_body["questions"],
            "persisted provider questions",
        )
        if not isinstance(advice_body["suggested_resubmission"], dict):
            raise AdvisoryRunError(
                "persisted provider suggested resubmission must be an object"
            )
        if (
            advice_body["advisory_only"] is not True
            or advice_body["changes_deterministic_decision"] is not False
        ):
            raise AdvisoryRunError(
                "persisted provider advice attempted decision authority"
            )
        if provider["advice_sha256"] != advice_body["advice_sha256"]:
            raise AdvisoryRunError(
                "persisted provider advice digest summary differs"
            )
        if provider["decision_sha256"] != advice_body["decision_sha256"]:
            raise AdvisoryRunError(
                "persisted provider advice decision binding differs"
            )
        raw_advice = {
            "schema": advice_body["schema"],
            "decision_sha256": advice_body["decision_sha256"],
            "plain_explanation": advice_body["plain_explanation"],
            "questions": advice_body["questions"],
            "suggested_resubmission": advice_body["suggested_resubmission"],
        }
        try:
            revalidated = accept_external_advice(
                canonical_json(raw_advice),
                frozen_decision=frozen_decision,
            ).to_dict()
        except AdviceError as exc:
            raise AdvisoryRunError(
                "persisted provider advice violates the advisory boundary"
            ) from exc
        if revalidated != advice_body:
            raise AdvisoryRunError(
                "persisted provider advice digest or normalization is invalid"
            )
    elif advice is not None or provider["advice_sha256"] is not None:
        raise AdvisoryRunError(
            "nonaccepted provider receipt must not contain accepted advice"
        )
    return provider


def _validate_sidecar_receipt_types(value: object) -> dict[str, Any]:
    receipt = _require_exact_fields(
        value,
        _SIDECAR_RECEIPT_FIELDS,
        "persisted advisory sidecar receipt",
    )
    if receipt["schema"] != SIDECAR_RECEIPT_SCHEMA:
        raise AdvisoryRunError("persisted advisory sidecar schema is invalid")
    if receipt["provider_state"] not in {
        STATE_ACCEPTED,
        STATE_PARKED,
        STATE_REJECTED,
    }:
        raise AdvisoryRunError("persisted sidecar provider state is invalid")
    _require_text(
        receipt["provider_reason_code"],
        "persisted sidecar provider reason",
    )
    _require_text(receipt["provider"], "persisted sidecar provider")
    if receipt["frozen_box_disposition"] not in _BOX_DISPOSITIONS:
        raise AdvisoryRunError("persisted sidecar box disposition is invalid")
    _require_text(
        receipt["frozen_box_reason"],
        "persisted sidecar box reason",
    )
    for field in (
        "box_receipt_sha256",
        "frozen_decision_sha256",
        "receipt_sha256",
        "root_sha256",
    ):
        _require_sha256(receipt[field], f"persisted sidecar {field}")
    _require_string_list(
        receipt["output_contract"],
        "persisted sidecar output contract",
    )
    _require_text(receipt["claim_ceiling"], "persisted sidecar claim ceiling")
    if receipt["claim_ceiling"] != _SIDECAR_CLAIM_CEILING:
        raise AdvisoryRunError("persisted sidecar claim ceiling is invalid")
    return receipt


def _verify_persisted_sidecar(root: Path) -> dict[str, Any]:
    entries = _enumerate_box_entries(root)
    if set(entries) != _SIDECAR_ARTIFACTS | {"advisory_sidecar_receipt.json"}:
        raise AdvisoryRunError("persisted sidecar contents are not exact")
    raw_by_name = {
        name: _read_regular_bytes(
            path,
            maximum=MAX_SIDECAR_FILE_BYTES,
            label=f"persisted sidecar artifact {name}",
        )
        for name, path in entries.items()
    }
    receipt = _validate_sidecar_receipt_types(_parse_canonical_object(
        raw_by_name["advisory_sidecar_receipt.json"],
        "persisted advisory sidecar receipt",
    ))
    artifacts = receipt["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != _SIDECAR_ARTIFACTS:
        raise AdvisoryRunError("persisted advisory sidecar artifacts are invalid")
    for name in sorted(_SIDECAR_ARTIFACTS):
        _require_sha256(artifacts[name], f"persisted sidecar digest {name}")
        if artifacts[name] != _sha256(raw_by_name[name]):
            raise AdvisoryRunError(
                f"persisted advisory sidecar digest mismatch: {name}"
            )
    expected_receipt_digest = _sha256(
        canonical_json(_receipt_digest_payload(receipt))
    )
    if receipt["receipt_sha256"] != expected_receipt_digest:
        raise AdvisoryRunError("persisted sidecar receipt digest is invalid")
    expected_root = _root_digest(expected_receipt_digest, artifacts)
    if receipt["root_sha256"] != expected_root:
        raise AdvisoryRunError("persisted sidecar root digest is invalid")
    frozen = _validate_frozen_decision(_parse_canonical_object(
        raw_by_name["frozen_box_decision.json"],
        "persisted frozen box decision",
    ))
    provider = _validate_provider_receipt(
        _parse_canonical_object(
            raw_by_name["advisory_provider_receipt.json"],
            "persisted advisory provider receipt",
        ),
        frozen_decision=frozen,
    )
    frozen_digest = decision_sha256(frozen)
    if receipt["frozen_decision_sha256"] != frozen_digest:
        raise AdvisoryRunError("persisted frozen decision digest is invalid")
    provider_decision = provider.get("decision_sha256")
    if provider_decision != frozen_digest:
        if not (
            provider_decision is None
            and provider.get("provider_state") == STATE_REJECTED
            and provider.get("request_sha256") is None
        ):
            raise AdvisoryRunError(
                "provider receipt is not bound to frozen decision"
            )
    if (
        receipt["provider_state"] != provider.get("provider_state")
        or receipt["provider_reason_code"] != provider.get("reason_code")
        or receipt["provider"] != provider.get("provider")
    ):
        raise AdvisoryRunError("sidecar provider summary differs from its receipt")
    if (
        receipt["frozen_box_disposition"] != frozen.get("disposition")
        or receipt["frozen_box_reason"] != frozen.get("reason")
        or receipt["box_receipt_sha256"] != frozen.get("box_receipt_sha256")
        or receipt["output_contract"] != frozen.get("output_contract")
    ):
        raise AdvisoryRunError("sidecar receipt differs from frozen box decision")
    for field, expected in (
        ("advisory_only", True),
        ("changes_box_decision", False),
        ("decision_authority", False),
        ("release_allowed", False),
        ("promotion_allowed", False),
    ):
        if receipt[field] is not expected:
            raise AdvisoryRunError(f"sidecar authority field is invalid: {field}")
    return receipt


def run_advisory_sidecar(
    box_run: Path,
    provider: str,
    sidecar_run: Path,
    *,
    environ: Mapping[str, str] | None = None,
    transport: Transport | None = None,
) -> tuple[dict[str, Any], int]:
    """Verify one box run and persist a nonauthoritative provider sidecar.

    Source verification and target overlap checks complete before any provider
    transport can run.  A missing credential is a normal ``PARKED`` provider
    state and is still persisted for audit.
    """

    box_root = _resolve_box_root(box_run)
    receipt, receipt_raw, _ = _validate_box_snapshot(box_root)
    sidecar_root = _resolve_new_sidecar_root(sidecar_run, box_root)
    frozen = _build_frozen_decision(receipt, receipt_raw)
    output_contract = tuple(frozen["output_contract"])

    try:
        sidecar_root.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AdvisoryRunError("sidecar run parent could not be created") from exc
    parent_metadata = sidecar_root.parent.lstat()
    if (
        stat.S_ISLNK(parent_metadata.st_mode)
        or not stat.S_ISDIR(parent_metadata.st_mode)
    ):
        raise AdvisoryRunError(
            "sidecar run parent must be a non-symlink directory"
        )
    staging_root = sidecar_root.parent / (
        f".{sidecar_root.name}.{os.getpid()}.{secrets.token_hex(8)}.staging"
    )
    try:
        staging_root.mkdir(mode=0o700)
    except OSError as exc:
        raise AdvisoryRunError(
            "sidecar staging directory could not be created"
        ) from exc
    metadata = staging_root.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _discard_staging_directory(staging_root)
        raise AdvisoryRunError(
            "sidecar staging root must be a new non-symlink directory"
        )
    _fsync_directory(staging_root)
    _fsync_directory(sidecar_root.parent)

    try:
        provider_receipt = run_advisory_audit(
            provider,
            frozen,
            output_contract=output_contract,
            environ=environ,
            transport=transport,
        ).to_dict()
        frozen_raw = _write_exclusive_json(
            staging_root,
            "frozen_box_decision.json",
            frozen,
        )
        provider_raw = _write_exclusive_json(
            staging_root,
            "advisory_provider_receipt.json",
            provider_receipt,
        )
        artifact_digests = {
            "frozen_box_decision.json": _sha256(frozen_raw),
            "advisory_provider_receipt.json": _sha256(provider_raw),
        }
        body = {
            "schema": SIDECAR_RECEIPT_SCHEMA,
            "provider_state": provider_receipt["provider_state"],
            "provider_reason_code": provider_receipt["reason_code"],
            "provider": provider_receipt["provider"],
            "frozen_box_disposition": frozen["disposition"],
            "frozen_box_reason": frozen["reason"],
            "box_receipt_sha256": frozen["box_receipt_sha256"],
            "frozen_decision_sha256": decision_sha256(frozen),
            "output_contract": list(output_contract),
            "advisory_only": True,
            "changes_box_decision": False,
            "decision_authority": False,
            "release_allowed": False,
            "promotion_allowed": False,
            "artifacts": artifact_digests,
            "claim_ceiling": _SIDECAR_CLAIM_CEILING,
        }
        receipt_digest = _sha256(canonical_json(body))
        sidecar_receipt = {
            **body,
            "receipt_sha256": receipt_digest,
            "root_sha256": _root_digest(receipt_digest, artifact_digests),
        }
        _write_exclusive_json(
            staging_root,
            "advisory_sidecar_receipt.json",
            sidecar_receipt,
        )
        _verify_persisted_sidecar(staging_root)
        _publish_directory_exclusive(staging_root, sidecar_root)
        _fsync_directory(sidecar_root.parent)
    except Exception:
        _discard_staging_directory(staging_root)
        raise
    persisted = _verify_persisted_sidecar(sidecar_root)
    return persisted, _EXIT_CODES[provider_receipt["provider_state"]]
