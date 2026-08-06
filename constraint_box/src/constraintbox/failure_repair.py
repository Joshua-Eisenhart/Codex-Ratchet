"""Deterministic non-pass receipt consumption for bounded capability flows.

This module is deliberately a controller-owned *planning* boundary.  It can
turn one already-completed external capability ``BLOCKED`` or ``PARKED`` flow
into a digest-bound repair contract, but it cannot run a repair, change an
environment, edit source, alter a verifier, release, or promote anything.

The external simulation engines remain outside the ConstraintBox kernel. The
load-bearing inputs here are a dispatcher-issued origin attestation, the
registered current flow/source pins, the capability flow's retained Mini-LevOS
receipt/ledger, and its self-authenticating external receipt. This remains a
local-process provenance boundary, not hostile-host containment.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from .capability_origin import (
    CAPABILITY_FLOW_RESULT_NAME,
    ORIGIN_ATTESTATION_NAME,
    ORIGIN_ATTESTATION_SCHEMA,
    ORIGIN_POLICY_ID,
    CapabilityOrigin,
    origin_for_capability,
    registry_sha256,
    source_path,
)
from .capability_receipt_replay import (
    CapabilityReceiptReplayError,
    verify_external_capability_receipt,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .mini_levos import verify_flow_receipt


REPAIR_PLAN_NAME = "repair_plan.json"
FAILURE_EVENT_SCHEMA = "constraintbox.capability-failure-event.v1"
REPAIR_PLAN_SCHEMA = "constraintbox.capability-repair-plan.v1"
REPAIR_CONTRACT_SCHEMA = "constraintbox.capability-repair-contract.v1"
REPAIR_POLICY_ID = "constraintbox.external-capability-repair-policy.v1"
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024

_SHA256 = hashlib.sha256
_HEX = re.compile(r"[0-9a-f]{64}")
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_REASON_CODE = re.compile(r"[a-z][a-z0-9_]{0,95}")
_RESULT_FIELDS = frozenset(
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
_ARTIFACT_FIELDS = frozenset(
    {
        "capability_receipt",
        "flow_receipt",
        "flow_ledger",
        "flow_ledger_head",
    }
)
_ATTESTATION_FIELDS = frozenset(
    {
        "schema",
        "policy_id",
        "capability_id",
        "request_id",
        "run_id",
        "run_root",
        "capability_result_path",
        "capability_result_sha256",
        "flow_policy_sha256",
        "result_disposition",
        "origin",
        "runner",
        "issuer",
        "issued_after_fixed_runner_return",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "promotion_allowed",
        "attestation_sha256",
    }
)
_TOLERANCE_POLICY = {
    "comparison": "exact canonical JSON and SHA-256 bindings",
    "flow_verification": "current Mini-LevOS semantic ledger replay",
    "numeric_tolerance": "none",
}

# This is a closed controller table.  A reason that is not named here receives
# the safe default ``park``.  No receipt, user input, or LLM output can add a
# mapping at runtime.
_ACTION_BY_FAILURE = {
    ("PARKED", "canonical_runtime_unavailable"): "environment_repair_request",
    ("PARKED", "external_fixture_unavailable"): "environment_repair_request",
    ("PARKED", "package_artifact_unavailable"): "environment_repair_request",
    ("PARKED", "runtime_executable_unavailable"): "environment_repair_request",
    ("PARKED", "strict_julia_carrier_unavailable"): "environment_repair_request",
    ("PARKED", "worker_source_unavailable"): "environment_repair_request",
    ("BLOCKED", "canonical_runtime_pin_mismatch"): "environment_repair_request",
    ("BLOCKED", "package_artifact_drift"): "environment_repair_request",
    ("BLOCKED", "runtime_digest_mismatch"): "environment_repair_request",
    ("BLOCKED", "controller_or_worker_source_changed_during_run"): "source_patch_candidate",
    ("BLOCKED", "profile_sources_changed_during_operation"): "source_patch_candidate",
    ("BLOCKED", "worker_source_digest_mismatch"): "source_patch_candidate",
    ("BLOCKED", "worker_protocol_invalid"): "source_patch_candidate",
    # A controller-recomputed non-pass is intentionally distinct from a
    # worker crash: the fixed external operation returned a bounded witness,
    # but an independent controller control rejected it.  The only selected
    # response is a fresh, identically pinned rerun; this contract still
    # authorizes no execution itself.
    ("BLOCKED", "controller_recomputed_check_failed"): "fresh_rerun",
    ("BLOCKED", "exact_operation_controls_failed"): "fresh_rerun",
    ("BLOCKED", "one_or_more_component_or_integration_checks_failed"): "fresh_rerun",
    ("BLOCKED", "worker_nonzero_exit"): "fresh_rerun",
    ("BLOCKED", "worker_timeout"): "fresh_rerun",
}
_ACTIONS = frozenset(
    {
        "fresh_rerun",
        "environment_repair_request",
        "source_patch_candidate",
        "park",
    }
)


class FailureRepairError(ValueError):
    """A non-pass capability receipt cannot form a deterministic repair plan."""


def _sha256(value: bytes) -> str:
    return _SHA256(value).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX.fullmatch(value) is None:
        raise FailureRepairError(f"{label} must be one lowercase SHA-256")
    return value


def _require_safe_id(value: object, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise FailureRepairError(f"{label} must be one bounded identifier")
    return value


def _parse_canonical_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = parse_json_object(raw)
    except IntakeError as exc:
        raise FailureRepairError(f"{label} is not strict JSON: {exc}") from exc
    if raw != canonical_json(value) + b"\n":
        raise FailureRepairError(f"{label} is not canonical JSON")
    return value


def _read_regular_bytes(path: Path, label: str) -> tuple[Path, bytes]:
    """Read one bounded unlinked regular artifact without following a link."""

    candidate = Path(path).expanduser()
    if not candidate.is_absolute() or candidate.is_symlink():
        raise FailureRepairError(f"{label} must be one absolute non-symlink file")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise FailureRepairError(f"could not open {label}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise FailureRepairError(f"{label} must be one unlinked regular file")
        if before.st_size < 0 or before.st_size > MAX_ARTIFACT_BYTES:
            raise FailureRepairError(f"{label} exceeds its byte bound")
        chunks: list[bytes] = []
        remaining = MAX_ARTIFACT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in fields):
            raise FailureRepairError(f"{label} changed while being read")
        if len(raw) != before.st_size or len(raw) > MAX_ARTIFACT_BYTES:
            raise FailureRepairError(f"{label} exceeds its byte bound")
        return candidate.resolve(strict=True), raw
    finally:
        os.close(descriptor)


def _validated_result(
    result: object,
    *,
    allowed_dispositions: frozenset[str],
) -> tuple[dict[str, Any], CapabilityOrigin]:
    if not isinstance(result, dict) or set(result) != _RESULT_FIELDS:
        raise FailureRepairError("capability result fields differ")
    try:
        canonical_json(result)
    except (TypeError, ValueError) as exc:
        raise FailureRepairError(f"capability result is not canonicalizable: {exc}") from exc
    fixed = {
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
    }
    for field, expected in fixed.items():
        if result.get(field) != expected:
            raise FailureRepairError(f"capability result fixed field differs: {field}")
    for field in ("capability_id", "request_id", "run_id"):
        _require_safe_id(result.get(field), field)
    if result.get("disposition") not in allowed_dispositions:
        if allowed_dispositions == frozenset({"BLOCKED", "PARKED"}):
            raise FailureRepairError("only a verified BLOCKED or PARKED result may plan repair")
        raise FailureRepairError("capability result disposition is not independently consumable")
    try:
        origin = origin_for_capability(result["capability_id"])
    except ValueError as exc:
        raise FailureRepairError("capability id is not controller-registered") from exc
    if result.get("schema") != origin.result_schema:
        raise FailureRepairError("capability result schema differs from controller origin")
    for field in (
        "request_sha256",
        "flow_policy_sha256",
        "capability_receipt_sha256",
        "flow_receipt_sha256",
    ):
        _require_sha256(result.get(field), field)
    if not isinstance(result.get("reason"), str) or _REASON_CODE.fullmatch(result["reason"]) is None:
        raise FailureRepairError("capability result reason must be one bounded reason code")
    if not isinstance(result.get("claim_ceiling"), str) or not result["claim_ceiling"]:
        raise FailureRepairError("capability result claim ceiling is invalid")
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != _ARTIFACT_FIELDS:
        raise FailureRepairError("capability result artifact fields differ")
    if any(not isinstance(value, str) for value in artifacts.values()):
        raise FailureRepairError("capability result artifact paths must be strings")
    return result, origin


def _load_artifacts(
    result: dict[str, Any],
    *,
    expected_run_root: Path | None,
) -> tuple[Path, dict[str, Path], dict[str, bytes], dict[str, dict[str, Any]]]:
    raw_artifacts: dict[str, bytes] = {}
    resolved_paths: dict[str, Path] = {}
    for name in sorted(_ARTIFACT_FIELDS):
        resolved, raw = _read_regular_bytes(Path(result["artifacts"][name]), name)
        resolved_paths[name] = resolved
        raw_artifacts[name] = raw
    run_root = resolved_paths["capability_receipt"].parent
    if any(path.parent != run_root for path in resolved_paths.values()):
        raise FailureRepairError("capability artifacts do not share one run root")
    if expected_run_root is not None:
        try:
            expected = Path(expected_run_root).expanduser().resolve(strict=True)
        except OSError as exc:
            raise FailureRepairError(f"expected capability run root is unavailable: {exc}") from exc
        if run_root != expected:
            raise FailureRepairError("capability artifacts escape the selected run root")
    parsed = {
        name: _parse_canonical_object(raw_artifacts[name], name)
        for name in ("capability_receipt", "flow_receipt")
    }
    head = raw_artifacts["flow_ledger_head"]
    if not re.fullmatch(rb"[0-9a-f]{64}\n", head):
        raise FailureRepairError("flow ledger head is not one canonical SHA-256 line")
    return run_root, resolved_paths, raw_artifacts, parsed


def _verify_parent_evidence(
    result: dict[str, Any],
    origin: CapabilityOrigin,
    resolved_paths: dict[str, Path],
    raw_artifacts: dict[str, bytes],
    parsed: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    capability_receipt = parsed["capability_receipt"]
    flow_receipt = parsed["flow_receipt"]
    receipt_sha256 = _require_sha256(
        capability_receipt.get("receipt_sha256"), "capability receipt digest"
    )
    digest_body = dict(capability_receipt)
    digest_body.pop("receipt_sha256", None)
    if receipt_sha256 != _sha256(canonical_json(digest_body)):
        raise FailureRepairError("capability receipt digest does not match its body")
    if receipt_sha256 != result["capability_receipt_sha256"]:
        raise FailureRepairError("capability receipt does not match the result binding")
    receipt_capability_id = capability_receipt.get("capability_id")
    if receipt_capability_id != result["capability_id"]:
        # The fixed packet-integration wrapper carries its capability identity
        # inside its typed binding rather than repeating it at the outer
        # receipt root. Its own static replay validator below checks that
        # binding. No other registered capability has this exception.
        if not (
            origin.capability_id == "basic-packet-cross-engine-v1"
            and receipt_capability_id is None
        ):
            raise FailureRepairError("capability receipt capability differs from the result")
    if capability_receipt.get("promotion_allowed") is not False:
        raise FailureRepairError("capability receipt attempted promotion")
    status = capability_receipt.get("status")
    expected_status = {
        "ELIGIBLE": "PASS",
        "BLOCKED": "FAIL",
        "PARKED": "PARKED",
    }[result["disposition"]]
    if status != expected_status:
        raise FailureRepairError("capability receipt status differs from result disposition")
    receipt_reason = capability_receipt.get("reason")
    if not isinstance(receipt_reason, str) or _REASON_CODE.fullmatch(receipt_reason) is None:
        raise FailureRepairError("capability receipt reason is not one bounded reason code")
    if receipt_reason != result["reason"]:
        raise FailureRepairError("capability receipt reason differs from result")

    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=result["run_id"],
        expected_policy_sha256=result["flow_policy_sha256"],
        expected_ledger_path=resolved_paths["flow_ledger"],
        expected_retained_head_sha256=raw_artifacts["flow_ledger_head"].decode("ascii").strip(),
        expected_receipt_sha256=result["flow_receipt_sha256"],
    )
    if not valid:
        raise FailureRepairError(f"parent Mini-LevOS flow failed semantic replay: {reason}")
    if flow_receipt.get("terminal") != result["disposition"]:
        raise FailureRepairError("parent flow terminal differs from result disposition")
    context = flow_receipt.get("final_context")
    if not isinstance(context, dict):
        raise FailureRepairError("parent flow final context is missing")
    if context.get("capability_state") != status:
        raise FailureRepairError("parent flow capability state differs from receipt")
    if context.get("capability_receipt_sha256") != receipt_sha256:
        raise FailureRepairError("parent flow receipt digest differs from receipt")
    receipt_text = context.get("capability_receipt_json")
    if not isinstance(receipt_text, str) or receipt_text.encode("utf-8") != canonical_json(capability_receipt):
        raise FailureRepairError("parent flow receipt text differs from capability receipt")
    runtime = flow_receipt.get("python_runtime")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("before"), dict):
        raise FailureRepairError("parent flow runtime binding is missing")
    runtime_identity = _require_sha256(
        runtime["before"].get("identity_sha256"), "parent flow runtime identity"
    )
    return capability_receipt, flow_receipt, runtime_identity


def _source_sha256(path: Path, label: str) -> str:
    try:
        return _sha256(path.read_bytes())
    except OSError as exc:
        raise FailureRepairError(f"{label} source is unavailable: {exc}") from exc


def _expected_hook_bindings(origin: CapabilityOrigin) -> tuple[Path, str, list[dict[str, str]]]:
    """Return current static hook bindings for one closed capability origin."""

    try:
        flow_source = source_path(origin.flow_source_filename).resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise FailureRepairError(f"controller flow source is unavailable: {exc}") from exc
    digest = _source_sha256(flow_source, "controller flow")
    hooks = [
        {
            "hook_id": hook.hook_id,
            "module": hook.module,
            "qualname": hook.qualname,
            "source_path": str(flow_source),
            "source_sha256": digest,
        }
        for hook in origin.hooks
    ]
    return flow_source, digest, hooks


def _verify_flow_origin_policy(
    flow_receipt: dict[str, Any],
    origin: CapabilityOrigin,
) -> None:
    """Bind a replayed receipt to its source-owned flow and hook identity."""

    if flow_receipt.get("flow_id") != origin.flow_id:
        raise FailureRepairError("parent flow id differs from controller origin")
    policy = flow_receipt.get("policy")
    if not isinstance(policy, dict) or policy.get("flow_id") != origin.flow_id:
        raise FailureRepairError("parent flow policy differs from controller origin")
    _flow_source, _digest, expected_hooks = _expected_hook_bindings(origin)
    hooks = policy.get("hooks")
    if not isinstance(hooks, list):
        raise FailureRepairError("parent flow policy hooks are missing")
    actual_by_id: dict[str, dict[str, Any]] = {}
    for hook in hooks:
        if not isinstance(hook, dict) or not isinstance(hook.get("hook_id"), str):
            raise FailureRepairError("parent flow policy hook is invalid")
        if hook["hook_id"] in actual_by_id:
            raise FailureRepairError("parent flow policy repeats a hook")
        actual_by_id[hook["hook_id"]] = hook
    expected_by_id = {hook["hook_id"]: hook for hook in expected_hooks}
    if set(actual_by_id) != set(expected_by_id):
        raise FailureRepairError("parent flow hooks differ from controller origin")
    for hook_id, expected in expected_by_id.items():
        actual = actual_by_id[hook_id]
        for field, value in expected.items():
            if actual.get(field) != value:
                raise FailureRepairError(
                    f"parent flow hook differs from controller origin: {hook_id}:{field}"
                )


def _verify_controller_origin_attestation(
    *,
    result: dict[str, Any],
    result_path: Path,
    run_root: Path,
    origin: CapabilityOrigin,
) -> tuple[dict[str, Any], str, bytes, Path]:
    """Require one dispatcher-issued, result-bound origin sidecar."""

    attestation_path, raw_attestation = _read_regular_bytes(
        run_root / ORIGIN_ATTESTATION_NAME,
        ORIGIN_ATTESTATION_NAME,
    )
    attestation = _parse_canonical_object(raw_attestation, ORIGIN_ATTESTATION_NAME)
    if set(attestation) != _ATTESTATION_FIELDS:
        raise FailureRepairError("controller origin attestation fields differ")
    digest = _require_sha256(
        attestation.get("attestation_sha256"), "controller origin attestation digest"
    )
    digest_body = dict(attestation)
    digest_body.pop("attestation_sha256", None)
    if digest != _sha256(canonical_json(digest_body)):
        raise FailureRepairError("controller origin attestation digest does not match")
    fixed = {
        "schema": ORIGIN_ATTESTATION_SCHEMA,
        "policy_id": ORIGIN_POLICY_ID,
        "capability_id": result["capability_id"],
        "request_id": result["request_id"],
        "run_id": result["run_id"],
        "run_root": str(run_root),
        "capability_result_path": str(result_path),
        "capability_result_sha256": _sha256(canonical_json(result)),
        "flow_policy_sha256": result["flow_policy_sha256"],
        "result_disposition": result["disposition"],
        "issued_after_fixed_runner_return": True,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "promotion_allowed": False,
    }
    for field, expected in fixed.items():
        if attestation.get(field) != expected:
            raise FailureRepairError(
                f"controller origin attestation differs from result: {field}"
            )

    flow_source, flow_source_sha256, expected_hooks = _expected_hook_bindings(origin)
    expected_origin = {
        "result_schema": origin.result_schema,
        "flow_id": origin.flow_id,
        "flow_module": origin.flow_module,
        "flow_source_path": str(flow_source),
        "flow_source_sha256": flow_source_sha256,
        "hooks": expected_hooks,
        "registry_sha256": registry_sha256(),
    }
    if attestation.get("origin") != expected_origin:
        raise FailureRepairError("controller origin attestation registry binding differs")
    try:
        runner_source = source_path(origin.runner_source_filename).resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise FailureRepairError(f"registered runner source is unavailable: {exc}") from exc
    expected_runner = {
        "module": origin.runner_module,
        "qualname": origin.runner_qualname,
        "source_path": str(runner_source),
        "source_sha256": _source_sha256(runner_source, "registered runner"),
    }
    if attestation.get("runner") != expected_runner:
        raise FailureRepairError("controller origin attestation runner binding differs")
    dispatch_source = Path(__file__).resolve().with_name("capability_dispatch.py")
    expected_issuer = {
        "module": "constraintbox.capability_dispatch",
        "source_path": str(dispatch_source),
        "source_sha256": _source_sha256(dispatch_source, "dispatcher"),
    }
    if attestation.get("issuer") != expected_issuer:
        raise FailureRepairError("controller origin attestation issuer binding differs")
    return attestation, digest, raw_attestation, attestation_path


def _assert_artifacts_unchanged(
    paths: dict[str, Path],
    raw_artifacts: dict[str, bytes],
    *,
    result_path: Path,
    raw_result: bytes,
    attestation_path: Path,
    raw_attestation: bytes,
) -> None:
    """Detect a simple post-replay replacement before a plan is emitted."""

    for name, path in paths.items():
        _resolved, current = _read_regular_bytes(path, name)
        if current != raw_artifacts[name]:
            raise FailureRepairError(f"{name} changed during verification")
    _resolved_result, current_result = _read_regular_bytes(
        result_path, CAPABILITY_FLOW_RESULT_NAME
    )
    if current_result != raw_result:
        raise FailureRepairError("capability result changed during verification")
    _resolved_attestation, current_attestation = _read_regular_bytes(
        attestation_path, ORIGIN_ATTESTATION_NAME
    )
    if current_attestation != raw_attestation:
        raise FailureRepairError("controller origin attestation changed during verification")


def verify_capability_result(
    result: object,
    *,
    expected_run_root: Path | None = None,
) -> dict[str, Any]:
    """Independently replay one controller-issued capability result.

    This is the suite and repair-planning admission point.  It accepts only
    the three terminal states that have a typed external receipt, and requires
    both a static controller origin and the dispatch-produced origin sidecar.
    It does not execute a repair or make a readiness/promotion decision.
    """

    result, origin = _validated_result(
        result,
        allowed_dispositions=frozenset({"ELIGIBLE", "BLOCKED", "PARKED"}),
    )
    run_root, resolved_paths, raw_artifacts, parsed = _load_artifacts(
        result,
        expected_run_root=expected_run_root,
    )
    result_path, raw_result = _read_regular_bytes(
        run_root / CAPABILITY_FLOW_RESULT_NAME,
        CAPABILITY_FLOW_RESULT_NAME,
    )
    persisted_result = _parse_canonical_object(raw_result, CAPABILITY_FLOW_RESULT_NAME)
    if persisted_result != result:
        raise FailureRepairError("persisted capability result differs from submitted result")
    attestation, attestation_sha256, raw_attestation, attestation_path = (
        _verify_controller_origin_attestation(
            result=result,
            result_path=result_path,
            run_root=run_root,
            origin=origin,
        )
    )
    capability_receipt, flow_receipt, runtime_identity = _verify_parent_evidence(
        result,
        origin,
        resolved_paths,
        raw_artifacts,
        parsed,
    )
    try:
        verify_external_capability_receipt(
            capability_id=result["capability_id"],
            receipt=capability_receipt,
            expected_receipt_sha256=result["capability_receipt_sha256"],
            require_pass=result["disposition"] == "ELIGIBLE",
        )
    except CapabilityReceiptReplayError as exc:
        raise FailureRepairError(
            f"parent external capability receipt failed independent replay: {exc}"
        ) from exc
    _verify_flow_origin_policy(flow_receipt, origin)
    _assert_artifacts_unchanged(
        resolved_paths,
        raw_artifacts,
        result_path=result_path,
        raw_result=raw_result,
        attestation_path=attestation_path,
        raw_attestation=raw_attestation,
    )
    return {
        "result": result,
        "origin": origin,
        "run_root": run_root,
        "capability_receipt": capability_receipt,
        "flow_receipt": flow_receipt,
        "runtime_identity_sha256": runtime_identity,
        "flow_ledger_head_sha256": raw_artifacts["flow_ledger_head"].decode(
            "ascii"
        ).strip(),
        "origin_attestation": attestation,
        "origin_attestation_sha256": attestation_sha256,
    }


def _selected_action(disposition: str, reason: str) -> tuple[str, str]:
    action = _ACTION_BY_FAILURE.get((disposition, reason), "park")
    if action not in _ACTIONS:
        raise FailureRepairError("controller repair action table is invalid")
    return action, (
        "controller_mapping_matched"
        if (disposition, reason) in _ACTION_BY_FAILURE
        else "controller_mapping_unmatched_default_park"
    )


def build_repair_plan_from_capability_result(
    result: dict[str, Any],
    *,
    expected_run_root: Path | None = None,
) -> dict[str, Any]:
    """Build a no-execution repair contract from one verified non-pass flow."""

    result, _origin = _validated_result(
        result,
        allowed_dispositions=frozenset({"BLOCKED", "PARKED"}),
    )
    evidence = verify_capability_result(
        result,
        expected_run_root=expected_run_root,
    )
    run_root = evidence["run_root"]
    capability_receipt = evidence["capability_receipt"]
    runtime_identity = evidence["runtime_identity_sha256"]
    action, mapping_reason = _selected_action(
        result["disposition"], capability_receipt["reason"]
    )
    event = {
        "schema": FAILURE_EVENT_SCHEMA,
        "policy_id": REPAIR_POLICY_ID,
        "capability_id": result["capability_id"],
        "request_id": result["request_id"],
        "run_id": result["run_id"],
        "disposition": result["disposition"],
        "receipt_status": capability_receipt["status"],
        "receipt_reason_code": capability_receipt["reason"],
        "parent_bindings": {
            "capability_result_sha256": _sha256(canonical_json(result)),
            "capability_receipt_sha256": result["capability_receipt_sha256"],
            "flow_receipt_sha256": result["flow_receipt_sha256"],
            "flow_policy_sha256": result["flow_policy_sha256"],
            "flow_ledger_head_sha256": evidence["flow_ledger_head_sha256"],
            "request_sha256": result["request_sha256"],
            "runtime_identity_sha256": runtime_identity,
            "controller_origin_attestation_sha256": evidence[
                "origin_attestation_sha256"
            ],
        },
        "source_run_root": str(run_root),
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "promotion_allowed": False,
    }
    event_sha256 = _sha256(canonical_json(event))
    verifier_source = Path(__file__).with_name("mini_levos.py")
    try:
        verifier_source_sha256 = _sha256(verifier_source.read_bytes())
    except OSError as exc:
        raise FailureRepairError(f"repair verifier source is unavailable: {exc}") from exc
    verifier = {
        "verifier_id": "constraintbox.mini-levos-flow-replay.v1",
        "verifier_source_sha256": verifier_source_sha256,
        "tolerance_policy": _TOLERANCE_POLICY,
        "tolerance_sha256": _sha256(canonical_json(_TOLERANCE_POLICY)),
        "required_parent_flow_policy_sha256": result["flow_policy_sha256"],
    }
    plan = {
        "schema": REPAIR_PLAN_SCHEMA,
        "policy_id": REPAIR_POLICY_ID,
        "failure_event_sha256": event_sha256,
        "selected_action": action,
        "selection_reason": mapping_reason,
        "execution_authorized": False,
        "retry_budget": {
            "authorized_attempts": 0,
            "remaining_attempts": 0,
            "reason": "no repair executor is admitted by this contract",
        },
        "required_verifier": verifier,
        "required_controller_origin": {
            "policy_id": ORIGIN_POLICY_ID,
            "registry_sha256": registry_sha256(),
            "must_match_fixed_capability_flow": True,
            "must_retain_dispatch_origin_attestation": True,
        },
        "required_regression_guard": {
            "must_replay_parent_flow": True,
            "must_rerun_same_external_capability": True,
            "must_preserve_parent_flow_policy": True,
            "rerun_challenge_policy": (
                "fresh controller-generated challenge under the unchanged "
                "fixed profile or fixture definition"
            ),
            "must_not_change": [
                "capability_id",
                "profile_or_fixture_definition",
                "controller_or_worker_source_pins",
                "controller_origin_attestation",
                "verifier_id",
                "tolerance_policy",
                "release_or_promotion_state",
            ],
        },
        "llm_authority": {
            "may_propose_non_authoritative_repair_text_only": False,
            "may_classify_failure": False,
            "may_select_action": False,
            "may_change_verifier_or_tolerance": False,
            "may_execute_repair": False,
            "may_release_or_promote": False,
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "one locally replayed non-pass external-capability receipt mapped "
            "to a non-executable deterministic repair contract; not a repair, "
            "retry, environment change, source change, engine readiness, "
            "release, promotion, or scientific claim"
        ),
    }
    plan_sha256 = _sha256(canonical_json(plan))
    contract = {
        "schema": REPAIR_CONTRACT_SCHEMA,
        "failure_event": event,
        "failure_event_sha256": event_sha256,
        "repair_plan": plan,
        "repair_plan_sha256": plan_sha256,
        "promotion_allowed": False,
    }
    return contract


def _resolve_capability_run_root(run_root: Path) -> Path:
    """Resolve one existing non-symlink capability run directory."""

    root = Path(run_root).expanduser()
    if root.is_symlink():
        raise FailureRepairError("capability run root must not be a symlink")
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise FailureRepairError(f"capability run root is unavailable: {exc}") from exc
    if not root.is_dir():
        raise FailureRepairError("capability run root must be one directory")
    return root


def load_verified_repair_contract_for_run(run_root: Path) -> dict[str, Any]:
    """Load one canonical repair contract and regenerate it from its parent.

    This remains a non-executing admission point.  It is intentionally useful
    to a separately invoked bounded outcome runner: a handwritten, stale, or
    source-drifted ``repair_plan.json`` cannot select a follow-up action merely
    because its own internal hashes look self-consistent.
    """

    root = _resolve_capability_run_root(run_root)
    plan_path, raw_plan = _read_regular_bytes(root / REPAIR_PLAN_NAME, REPAIR_PLAN_NAME)
    contract = _parse_canonical_object(raw_plan, REPAIR_PLAN_NAME)
    _result_path, raw_result = _read_regular_bytes(
        root / CAPABILITY_FLOW_RESULT_NAME,
        CAPABILITY_FLOW_RESULT_NAME,
    )
    result = _parse_canonical_object(raw_result, CAPABILITY_FLOW_RESULT_NAME)
    expected = build_repair_plan_from_capability_result(
        result,
        expected_run_root=root,
    )
    if contract != expected:
        raise FailureRepairError("repair plan differs from the regenerated controller contract")
    # Retain a fresh independent replay for any separately invoked outcome
    # consumer.  Regenerating the plan above already replays the parent, but
    # exposing this evidence avoids making a follow-up consumer infer static
    # runner/issuer bindings from the compact plan alone.
    evidence = verify_capability_result(result, expected_run_root=root)
    _rechecked_plan_path, rechecked_raw_plan = _read_regular_bytes(
        plan_path,
        REPAIR_PLAN_NAME,
    )
    if rechecked_raw_plan != raw_plan:
        raise FailureRepairError("repair plan changed during verification")
    return {
        "contract": contract,
        "result": result,
        "evidence": evidence,
        "run_root": root,
        "repair_plan_path": plan_path,
    }


def write_repair_plan_for_run(run_root: Path) -> dict[str, Any]:
    """Persist exactly one repair contract beside a canonical capability result."""

    root = _resolve_capability_run_root(run_root)
    _result_path, raw_result = _read_regular_bytes(
        root / CAPABILITY_FLOW_RESULT_NAME,
        CAPABILITY_FLOW_RESULT_NAME,
    )
    result = _parse_canonical_object(raw_result, CAPABILITY_FLOW_RESULT_NAME)
    contract = build_repair_plan_from_capability_result(
        result,
        expected_run_root=root,
    )
    output = root / REPAIR_PLAN_NAME
    try:
        with output.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(contract).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise FailureRepairError(f"could not persist repair plan: {exc}") from exc
    return contract
