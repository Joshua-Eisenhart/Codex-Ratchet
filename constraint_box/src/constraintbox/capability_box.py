"""A verified ConstraintBox front door for one fixed external capability.

This is deliberately separate from the legacy ``basic_packet_v1`` estate
diagnostic.  The controller owns the selected PyTorch capability and its
two-node Mini-LevOS ``TOOL -> GATE`` flow.  The user request can authorize
that fixed profile, but cannot substitute a module, worker, function,
challenge, policy, transition, or disposition.

The simulation implementation remains an external system.  A successful box
run is only an integrity-checked local snapshot of one bounded external
operation; it is not an LLM proposal, release, engine-readiness result, or
scientific claim.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .advice import build_audit_brief, deterministic_explanation
from .external_capability import (
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    ExternalCapabilityError,
    capability_binding_from_dict,
    validate_pytorch_capability_receipt,
)
from .external_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalCapabilityFlowError,
    run_pytorch_capability_flow,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .mini_levos import verify_flow_receipt
from .user_profile import DEFAULT_PROFILE_PATH, compile_user_profile
from .user_request import (
    BLOCKED,
    ELIGIBLE,
    EVALUATION_ERROR,
    PARKED,
    assess_user_request,
)


SCHEMA = "constraintbox.capability-box-run.v1"
READY_FOR_CAPABILITY = "VERIFIED_EXTERNAL_CAPABILITY"
CAPABILITY_DIRECTORY = "capability"
CAPABILITY_RESULT_NAME = "capability_flow_result.json"
RECEIPT_NAME = "capability_box_receipt.json"
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
CLAIM_CEILING = (
    "at most, this local run establishes that one explicit user request passed "
    "the deterministic request gate and that the controller-selected "
    "pytorch-jacobian-v1 Mini-LevOS tool and gate flow passed its bounded "
    "controls; it does not establish an LLM proposal, release, PyTorch or "
    "sim-stack readiness, CR truth, scientific proof, hostile-code containment, "
    "or canonical promotion"
)
EXIT_CODES = {
    READY_FOR_CAPABILITY: 0,
    BLOCKED: 1,
    PARKED: 4,
    EVALUATION_ERROR: 5,
}

ROOT_ARTIFACT_NAMES = frozenset(
    {
        "compiled_user_context.json",
        "compiled_user_context.txt",
        "deterministic_explanation.json",
        "external_audit_brief.json",
        CAPABILITY_RESULT_NAME,
        "request_assessment.json",
        "user_profile.json",
        "user_request.json",
    }
)
CAPABILITY_ARTIFACT_NAMES = frozenset(
    {
        CAPABILITY_RECEIPT_NAME,
        FLOW_RECEIPT_NAME,
        FLOW_LEDGER_NAME,
        f"{FLOW_LEDGER_NAME}.head",
    }
)
_RECEIPT_FIELDS = frozenset(
    {
        "artifacts",
        "capability_flow_result",
        "capability_id",
        "claim_ceiling",
        "deterministic_explanation",
        "disposition",
        "external_audit_brief",
        "next_step",
        "promotion_allowed",
        "reason",
        "release_allowed",
        "request_assessment",
        "schema",
        "user_context",
    }
)
_FLOW_RESULT_FIELDS = frozenset(
    {
        "schema",
        "capability_id",
        "request_id",
        "request_sha256",
        "run_id",
        "flow_policy_sha256",
        "disposition",
        "reason",
        "capability_receipt_sha256",
        "flow_receipt_sha256",
        "artifacts",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
    }
)


class CapabilityBoxError(ValueError):
    """The fixed capability front door could not construct or verify a run."""


@dataclass(frozen=True)
class VerifiedCapabilityBoxRun:
    """One captured, independently revalidated fixed-capability snapshot.

    This is intentionally not accepted by the LLM proposal runner yet.  The
    proposed data it exposes is for a future controller-owned follow-on flow,
    not permission for an LLM to treat the tool outcome as a release.
    """

    root: Path
    receipt_sha256: str
    request_id: str
    request_sha256: str
    context_sha256: str
    capability_id: str
    capability_receipt_sha256: str
    flow_receipt_sha256: str
    artifact_sha256s: tuple[tuple[str, str], ...]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_new_bytes(path: Path, value: bytes) -> None:
    """Persist one new root artifact without replacing an existing entry."""

    try:
        with path.open("xb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise CapabilityBoxError(
            f"could not persist capability-box artifact {path.name}: {exc}"
        ) from exc


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    _write_new_bytes(path, canonical_json(value) + b"\n")


def _read_regular_at(directory_descriptor: int, name: str) -> bytes:
    """Capture one bounded, unlinked regular file from an open directory."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except OSError as exc:
        raise CapabilityBoxError(
            f"could not open capability-box artifact {name}: {exc}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise CapabilityBoxError(
                f"capability-box artifact is not a regular file: {name}"
            )
        if before.st_nlink != 1:
            raise CapabilityBoxError(
                f"capability-box artifact has an unexpected link count: {name}"
            )
        if before.st_size < 0 or before.st_size > MAX_ARTIFACT_BYTES:
            raise CapabilityBoxError(
                f"capability-box artifact exceeds its byte bound: {name}"
            )
        chunks: list[bytes] = []
        remaining = MAX_ARTIFACT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        value = b"".join(chunks)
        after = os.fstat(descriptor)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in fields):
            raise CapabilityBoxError(
                f"capability-box artifact changed while being read: {name}"
            )
        if len(value) != before.st_size or len(value) > MAX_ARTIFACT_BYTES:
            raise CapabilityBoxError(
                f"capability-box artifact exceeds its byte bound: {name}"
            )
        return value
    finally:
        os.close(descriptor)


def _parse_canonical_json(raw: bytes, name: str) -> dict[str, Any]:
    try:
        value = parse_json_object(raw)
    except IntakeError as exc:
        raise CapabilityBoxError(
            f"capability-box artifact JSON is invalid: {name}: {exc}"
        ) from exc
    if raw != canonical_json(value) + b"\n":
        raise CapabilityBoxError(
            f"capability-box artifact is not canonical JSON: {name}"
        )
    return value


def _directory_snapshot(descriptor: int, label: str) -> tuple[os.stat_result, set[str]]:
    before = os.fstat(descriptor)
    names = set(os.listdir(descriptor))
    return before, names


def _assert_directory_unchanged(
    descriptor: int,
    before: os.stat_result,
    names: set[str],
    label: str,
) -> None:
    after = os.fstat(descriptor)
    if set(os.listdir(descriptor)) != names or any(
        getattr(before, field) != getattr(after, field)
        for field in ("st_dev", "st_ino", "st_mtime_ns", "st_ctime_ns")
    ):
        raise CapabilityBoxError(
            f"capability-box {label} directory changed while being captured"
        )


def _capture_ready_run(run_dir: Path) -> tuple[Path, dict[str, bytes]]:
    candidate = Path(run_dir).expanduser()
    try:
        if candidate.is_symlink():
            raise CapabilityBoxError("capability-box run directory must not be a symlink")
        root = candidate.resolve(strict=True)
    except OSError as exc:
        raise CapabilityBoxError(
            f"capability-box run directory is unavailable: {exc}"
        ) from exc
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        root_descriptor = os.open(root, directory_flags)
    except OSError as exc:
        raise CapabilityBoxError(
            f"could not open capability-box run directory: {exc}"
        ) from exc
    try:
        root_before, root_names = _directory_snapshot(root_descriptor, "root")
        expected_root_names = set(ROOT_ARTIFACT_NAMES) | {
            CAPABILITY_DIRECTORY,
            RECEIPT_NAME,
        }
        if root_names != expected_root_names:
            raise CapabilityBoxError("capability-box root artifact set differs")
        try:
            capability_descriptor = os.open(
                CAPABILITY_DIRECTORY,
                directory_flags,
                dir_fd=root_descriptor,
            )
        except OSError as exc:
            raise CapabilityBoxError(
                f"could not open capability-box capability directory: {exc}"
            ) from exc
        try:
            capability_before, capability_names = _directory_snapshot(
                capability_descriptor,
                "capability",
            )
            if capability_names != set(CAPABILITY_ARTIFACT_NAMES):
                raise CapabilityBoxError(
                    "capability-box nested artifact set differs"
                )
            captured = {
                name: _read_regular_at(root_descriptor, name)
                for name in sorted(set(ROOT_ARTIFACT_NAMES) | {RECEIPT_NAME})
            }
            captured.update(
                {
                    f"{CAPABILITY_DIRECTORY}/{name}": _read_regular_at(
                        capability_descriptor,
                        name,
                    )
                    for name in sorted(CAPABILITY_ARTIFACT_NAMES)
                }
            )
            _assert_directory_unchanged(
                capability_descriptor,
                capability_before,
                capability_names,
                "capability",
            )
        finally:
            os.close(capability_descriptor)
        _assert_directory_unchanged(
            root_descriptor,
            root_before,
            root_names,
            "root",
        )
    finally:
        os.close(root_descriptor)
    return root, captured


def _expected_artifact_paths(capability_root: Path) -> dict[str, str]:
    return {
        "capability_receipt": str(capability_root / CAPABILITY_RECEIPT_NAME),
        "flow_receipt": str(capability_root / FLOW_RECEIPT_NAME),
        "flow_ledger": str(capability_root / FLOW_LEDGER_NAME),
        "flow_ledger_head": str(capability_root / f"{FLOW_LEDGER_NAME}.head"),
    }


def _validate_capability_flow(
    result: dict[str, Any],
    *,
    request_id: str,
    capability_root: Path,
    capability_receipt: dict[str, Any],
    flow_receipt: dict[str, Any],
) -> None:
    """Revalidate the fixed external receipt and the Mini-Lev flow receipt."""

    if set(result) != _FLOW_RESULT_FIELDS:
        raise CapabilityBoxError("capability flow result fields differ")
    fixed = {
        "schema": "constraintbox.external-capability-flow-result.v1",
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }
    for key, expected in fixed.items():
        if result.get(key) != expected:
            raise CapabilityBoxError(
                f"capability flow result fixed field differs: {key}"
            )
    if result.get("artifacts") != _expected_artifact_paths(capability_root):
        raise CapabilityBoxError("capability flow artifact paths differ")
    if result.get("disposition") not in {"ELIGIBLE", "BLOCKED", "PARKED", "HOLD"}:
        raise CapabilityBoxError("capability flow disposition is invalid")
    for key in (
        "request_sha256",
        "flow_policy_sha256",
        "capability_receipt_sha256",
        "flow_receipt_sha256",
    ):
        value = result.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise CapabilityBoxError(f"capability flow {key} is invalid")
    if not isinstance(result.get("run_id"), str) or not result["run_id"]:
        raise CapabilityBoxError("capability flow run_id is invalid")
    if not isinstance(result.get("reason"), str) or not result["reason"]:
        raise CapabilityBoxError("capability flow reason is invalid")

    try:
        binding = capability_binding_from_dict(capability_receipt.get("binding"))
    except ExternalCapabilityError as exc:
        raise CapabilityBoxError(f"capability binding is invalid: {exc}") from exc
    if (
        binding.capability_id != CAPABILITY_ID
        or binding.run_id != result["run_id"]
        or binding.flow_policy_sha256 != result["flow_policy_sha256"]
        or capability_receipt.get("receipt_sha256")
        != result["capability_receipt_sha256"]
    ):
        raise CapabilityBoxError("capability receipt binding differs from flow result")
    errors = validate_pytorch_capability_receipt(
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=result["capability_receipt_sha256"],
        require_pass=result["disposition"] == "ELIGIBLE",
    )
    if errors:
        raise CapabilityBoxError(
            "capability receipt validation failed: " + "; ".join(errors)
        )
    ledger = flow_receipt.get("ledger")
    if not isinstance(ledger, dict):
        raise CapabilityBoxError("flow receipt has no ledger binding")
    retained_head = ledger.get("retained_head_sha256")
    if not isinstance(retained_head, str):
        raise CapabilityBoxError("flow receipt retained ledger head is invalid")
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=result["run_id"],
        expected_policy_sha256=result["flow_policy_sha256"],
        expected_ledger_path=capability_root / FLOW_LEDGER_NAME,
        expected_retained_head_sha256=retained_head,
        expected_receipt_sha256=result["flow_receipt_sha256"],
    )
    if not valid:
        raise CapabilityBoxError(f"Mini-Lev flow receipt validation failed: {reason}")
    if flow_receipt.get("terminal") != result["disposition"]:
        raise CapabilityBoxError("Mini-Lev terminal differs from flow disposition")
    expected_terminal = {
        "PASS": "ELIGIBLE",
        "FAIL": "BLOCKED",
        "PARKED": "PARKED",
    }.get(capability_receipt.get("status"))
    if expected_terminal != result["disposition"]:
        raise CapabilityBoxError("capability status differs from Mini-Lev terminal")


def run_pytorch_capability_box(
    request_raw: bytes,
    run_dir: Path,
) -> tuple[dict[str, Any], int]:
    """Run the fixed controller-selected PyTorch capability front door once."""

    assessment = assess_user_request(request_raw)
    decision = assessment.to_dict()
    try:
        profile_raw = DEFAULT_PROFILE_PATH.read_bytes()
        context = compile_user_profile(profile_raw)
    except (OSError, ValueError) as exc:
        return (
            {
                "schema": SCHEMA,
                "capability_id": CAPABILITY_ID,
                "disposition": EVALUATION_ERROR,
                "reason": "user_profile_configuration_error",
                "error": str(exc),
                "request_assessment": decision,
                "promotion_allowed": False,
                "release_allowed": False,
                "claim_ceiling": CLAIM_CEILING,
            },
            EXIT_CODES[EVALUATION_ERROR],
        )
    allowed_actions = {
        action
        for action in assessment.evidence.get("allowed_actions", [])
        if isinstance(action, str)
    }
    if "write_receipts" not in allowed_actions:
        disposition = BLOCKED if assessment.disposition == ELIGIBLE else assessment.disposition
        return (
            {
                "schema": SCHEMA,
                "capability_id": CAPABILITY_ID,
                "disposition": disposition,
                "reason": (
                    "receipt_writing_not_authorized"
                    if assessment.disposition == ELIGIBLE
                    else assessment.reason
                ),
                "request_assessment": decision,
                "promotion_allowed": False,
                "release_allowed": False,
                "claim_ceiling": CLAIM_CEILING,
            },
            EXIT_CODES[disposition],
        )

    root = Path(run_dir).expanduser().resolve()
    try:
        root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise CapabilityBoxError(f"run directory already exists: {root}") from exc
    except OSError as exc:
        raise CapabilityBoxError(f"could not create run directory: {exc}") from exc

    _write_new_bytes(root / "user_request.json", request_raw)
    _write_new_bytes(root / "user_profile.json", profile_raw)
    context_metadata = context.to_dict(include_text=False)
    _write_new_json(root / "request_assessment.json", decision)
    _write_new_json(root / "compiled_user_context.json", context_metadata)
    _write_new_bytes(root / "compiled_user_context.txt", context.context_text.encode("utf-8"))
    explanation = deterministic_explanation(decision).to_dict()
    audit_brief = build_audit_brief(decision, output_contract=context.output_contract)
    _write_new_json(root / "deterministic_explanation.json", explanation)
    _write_new_json(root / "external_audit_brief.json", audit_brief)

    result: dict[str, Any] | None = None
    capability_root = root / CAPABILITY_DIRECTORY
    if assessment.disposition != ELIGIBLE:
        disposition, reason = assessment.disposition, "request_did_not_reach_capability_eligibility"
    elif "run_external_tools" not in allowed_actions:
        disposition, reason = BLOCKED, "external_tool_execution_not_authorized"
    elif assessment.evidence.get("requested_external_tests") != [CAPABILITY_ID]:
        disposition, reason = BLOCKED, "requested_external_capability_not_bound_to_capability_box"
    else:
        try:
            result = run_pytorch_capability_flow(
                request_id=assessment.request_id or "missing-request-id",
                run_root=capability_root,
            )
            _write_new_json(root / CAPABILITY_RESULT_NAME, result)
            capability_receipt = _parse_canonical_json(
                (capability_root / CAPABILITY_RECEIPT_NAME).read_bytes(),
                f"{CAPABILITY_DIRECTORY}/{CAPABILITY_RECEIPT_NAME}",
            )
            flow_receipt = _parse_canonical_json(
                (capability_root / FLOW_RECEIPT_NAME).read_bytes(),
                f"{CAPABILITY_DIRECTORY}/{FLOW_RECEIPT_NAME}",
            )
            _validate_capability_flow(
                result,
                request_id=assessment.request_id or "missing-request-id",
                capability_root=capability_root,
                capability_receipt=capability_receipt,
                flow_receipt=flow_receipt,
            )
        except (OSError, ValueError) as exc:
            result = {
                "schema": "constraintbox.capability-flow-error.v1",
                "capability_id": CAPABILITY_ID,
                "reason": "external_capability_flow_exception",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "release_allowed": False,
                "engine_readiness_claim": False,
                "cr_truth_claim": False,
                "promotion_allowed": False,
            }
            _write_new_json(root / CAPABILITY_RESULT_NAME, result)
            disposition, reason = EVALUATION_ERROR, "external_capability_flow_exception"
        else:
            disposition = {
                "ELIGIBLE": READY_FOR_CAPABILITY,
                "BLOCKED": BLOCKED,
                "PARKED": PARKED,
                "HOLD": EVALUATION_ERROR,
            }.get(result["disposition"], EVALUATION_ERROR)
            reason = {
                READY_FOR_CAPABILITY: "request_and_fixed_external_capability_passed",
                BLOCKED: "external_capability_executed_and_failed",
                PARKED: "external_capability_unavailable_or_unresolved",
                EVALUATION_ERROR: "external_capability_returned_unknown_or_held_state",
            }[disposition]

    if result is None:
        _write_new_json(
            root / CAPABILITY_RESULT_NAME,
            {
                "schema": "constraintbox.capability-flow-not-run.v1",
                "capability_id": CAPABILITY_ID,
                "reason": reason,
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "release_allowed": False,
                "engine_readiness_claim": False,
                "cr_truth_claim": False,
                "promotion_allowed": False,
            },
        )
        result = _parse_canonical_json(
            (root / CAPABILITY_RESULT_NAME).read_bytes(),
            CAPABILITY_RESULT_NAME,
        )

    artifacts = {
        path.name: _sha256(path.read_bytes())
        for path in sorted(root.iterdir())
        if path.is_file() and path.name != RECEIPT_NAME
    }
    if capability_root.is_dir():
        artifacts.update(
            {
                f"{CAPABILITY_DIRECTORY}/{path.name}": _sha256(path.read_bytes())
                for path in sorted(capability_root.iterdir())
                if path.is_file()
            }
        )
    receipt = {
        "schema": SCHEMA,
        "capability_id": CAPABILITY_ID,
        "disposition": disposition,
        "reason": reason,
        "request_assessment": decision,
        "user_context": context_metadata,
        "deterministic_explanation": explanation,
        "external_audit_brief": audit_brief,
        "capability_flow_result": result,
        "artifacts": artifacts,
        "next_step": (
            "verified_capability_follow_on"
            if disposition == READY_FOR_CAPABILITY
            else "user_resubmission"
            if disposition == PARKED
            else "none"
        ),
        "promotion_allowed": False,
        "release_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_new_json(root / RECEIPT_NAME, receipt)
    return receipt, EXIT_CODES[disposition]


def verify_pytorch_capability_box_run(run_dir: Path) -> VerifiedCapabilityBoxRun:
    """Independently capture and verify one positive fixed-capability run."""

    root, captured = _capture_ready_run(run_dir)
    receipt_raw = captured[RECEIPT_NAME]
    receipt = _parse_canonical_json(receipt_raw, RECEIPT_NAME)
    if set(receipt) != _RECEIPT_FIELDS:
        raise CapabilityBoxError("capability-box receipt fields differ")
    fixed = {
        "schema": SCHEMA,
        "capability_id": CAPABILITY_ID,
        "disposition": READY_FOR_CAPABILITY,
        "reason": "request_and_fixed_external_capability_passed",
        "next_step": "verified_capability_follow_on",
        "promotion_allowed": False,
        "release_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    for key, expected in fixed.items():
        if receipt.get(key) != expected:
            raise CapabilityBoxError(f"capability-box receipt {key} is not ready")

    expected_artifacts = set(ROOT_ARTIFACT_NAMES) | {
        f"{CAPABILITY_DIRECTORY}/{name}" for name in CAPABILITY_ARTIFACT_NAMES
    }
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != expected_artifacts:
        raise CapabilityBoxError("capability-box artifact index differs")
    for name in expected_artifacts:
        expected_digest = artifacts.get(name)
        if (
            not isinstance(expected_digest, str)
            or len(expected_digest) != 64
            or any(character not in "0123456789abcdef" for character in expected_digest)
            or _sha256(captured[name]) != expected_digest
        ):
            raise CapabilityBoxError(f"capability-box artifact digest mismatch: {name}")

    try:
        request_body = parse_json_object(captured["user_request.json"])
    except IntakeError as exc:
        raise CapabilityBoxError(f"captured user request is invalid: {exc}") from exc
    assessment = assess_user_request(captured["user_request.json"]).to_dict()
    recorded_assessment = _parse_canonical_json(
        captured["request_assessment.json"], "request_assessment.json"
    )
    if assessment != recorded_assessment or receipt.get("request_assessment") != assessment:
        raise CapabilityBoxError("captured request assessment differs from current policy")
    if assessment.get("disposition") != ELIGIBLE:
        raise CapabilityBoxError("captured request is not capability eligible")
    evidence = assessment.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("requested_external_tests") != [CAPABILITY_ID]:
        raise CapabilityBoxError("captured request capability binding differs")
    if not {"run_external_tools", "write_receipts"}.issubset(
        set(evidence.get("allowed_actions", []))
    ):
        raise CapabilityBoxError("captured request does not authorize capability run")
    request_id = request_body.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise CapabilityBoxError("captured request_id is invalid")

    try:
        current_profile = DEFAULT_PROFILE_PATH.read_bytes()
    except OSError as exc:
        raise CapabilityBoxError(f"controller user profile is unavailable: {exc}") from exc
    if current_profile != captured["user_profile.json"]:
        raise CapabilityBoxError("captured user profile differs from controller profile")
    try:
        context = compile_user_profile(captured["user_profile.json"])
    except (OSError, ValueError) as exc:
        raise CapabilityBoxError(f"captured profile no longer compiles: {exc}") from exc
    context_metadata = _parse_canonical_json(
        captured["compiled_user_context.json"], "compiled_user_context.json"
    )
    if (
        context_metadata != context.to_dict(include_text=False)
        or captured["compiled_user_context.txt"] != context.context_text.encode("utf-8")
        or receipt.get("user_context") != context_metadata
    ):
        raise CapabilityBoxError("captured user context differs from current compilation")
    explanation = _parse_canonical_json(
        captured["deterministic_explanation.json"], "deterministic_explanation.json"
    )
    if explanation != deterministic_explanation(assessment).to_dict() or receipt.get(
        "deterministic_explanation"
    ) != explanation:
        raise CapabilityBoxError("captured deterministic explanation differs")
    audit_brief = _parse_canonical_json(
        captured["external_audit_brief.json"], "external_audit_brief.json"
    )
    if audit_brief != build_audit_brief(
        assessment, output_contract=context.output_contract
    ) or receipt.get("external_audit_brief") != audit_brief:
        raise CapabilityBoxError("captured external audit brief differs")

    result = _parse_canonical_json(captured[CAPABILITY_RESULT_NAME], CAPABILITY_RESULT_NAME)
    capability_receipt = _parse_canonical_json(
        captured[f"{CAPABILITY_DIRECTORY}/{CAPABILITY_RECEIPT_NAME}"],
        f"{CAPABILITY_DIRECTORY}/{CAPABILITY_RECEIPT_NAME}",
    )
    flow_receipt = _parse_canonical_json(
        captured[f"{CAPABILITY_DIRECTORY}/{FLOW_RECEIPT_NAME}"],
        f"{CAPABILITY_DIRECTORY}/{FLOW_RECEIPT_NAME}",
    )
    _validate_capability_flow(
        result,
        request_id=request_id,
        capability_root=root / CAPABILITY_DIRECTORY,
        capability_receipt=capability_receipt,
        flow_receipt=flow_receipt,
    )
    if receipt.get("capability_flow_result") != result:
        raise CapabilityBoxError("capability-box receipt result differs from artifact")
    return VerifiedCapabilityBoxRun(
        root=root,
        receipt_sha256=_sha256(receipt_raw),
        request_id=request_id,
        request_sha256=_sha256(captured["user_request.json"]),
        context_sha256=context.context_sha256,
        capability_id=CAPABILITY_ID,
        capability_receipt_sha256=result["capability_receipt_sha256"],
        flow_receipt_sha256=result["flow_receipt_sha256"],
        artifact_sha256s=tuple(sorted(artifacts.items())),
    )
