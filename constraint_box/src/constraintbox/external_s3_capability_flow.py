"""Two-node deterministic Mini-Lev flows for bounded external S3 profiles.

This is intentionally only a tool observation followed by a receipt gate.
The Mini-Lev controller selects the binding and terminal transition; neither
PyDMD nor PyMDP can select a retry, release, or promotion outcome.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import Any

from .external_s3_capability import (
    CAPABILITY_SCHEMA,
    PYDMD_PROFILE,
    PYMDP_PROFILE,
    ExternalS3CapabilityBroker,
    ExternalS3CapabilityError,
    S3CapabilityBinding,
    S3CapabilityProfile,
    s3_capability_binding_from_dict,
    validate_s3_capability_receipt,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .mini_levos import (
    CONTROLLER_METADATA_KEY,
    CONTROLLER_METADATA_SCHEMA,
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
    verify_flow_receipt,
)


FLOW_RESULT_SCHEMA = "constraintbox.external-s3-capability-flow-result.v1"
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")

_FLOW_NAMES = {
    PYDMD_PROFILE.capability_id: {
        "tool_node": "pydmd-capability-tool",
        "gate_node": "pydmd-capability-gate",
        "tool_hook": "pydmd-discrete-rate-capability-tool",
        "gate_hook": "pydmd-discrete-rate-capability-gate",
        "prefix": "pydmd",
        "receipt": "pydmd_discrete_rate_capability_receipt.json",
        "flow_receipt": "pydmd_discrete_rate_flow_receipt.json",
        "ledger": "pydmd_discrete_rate_flow_events.jsonl",
    },
    PYMDP_PROFILE.capability_id: {
        "tool_node": "pymdp-capability-tool",
        "gate_node": "pymdp-capability-gate",
        "tool_hook": "pymdp-two-state-inference-capability-tool",
        "gate_hook": "pymdp-two-state-inference-capability-gate",
        "prefix": "pymdp",
        "receipt": "pymdp_two_state_capability_receipt.json",
        "flow_receipt": "pymdp_two_state_flow_receipt.json",
        "ledger": "pymdp_two_state_flow_events.jsonl",
    },
}

_PINNED_BROKER = ExternalS3CapabilityBroker
_PINNED_BINDING_PARSER = s3_capability_binding_from_dict
_PINNED_RECEIPT_VALIDATOR = validate_s3_capability_receipt


class ExternalS3CapabilityFlowError(ValueError):
    """The fixed external S3 Mini-Lev flow could not run or verify."""


def _names(profile: S3CapabilityProfile) -> dict[str, str]:
    try:
        return _FLOW_NAMES[profile.capability_id]
    except (AttributeError, KeyError) as exc:
        raise ExternalS3CapabilityFlowError("unknown fixed capability profile") from exc


def _verify_live_dependencies() -> None:
    if (
        ExternalS3CapabilityBroker is not _PINNED_BROKER
        or s3_capability_binding_from_dict is not _PINNED_BINDING_PARSER
        or validate_s3_capability_receipt is not _PINNED_RECEIPT_VALIDATOR
    ):
        raise ExternalS3CapabilityFlowError("capability handler dependency binding drift")


def _binding_from_context(
    profile: S3CapabilityProfile,
    context: dict[str, Any],
    *,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> S3CapabilityBinding:
    _verify_live_dependencies()
    metadata = context.get(CONTROLLER_METADATA_KEY)
    if not isinstance(metadata, dict) or set(metadata) != {
        "schema",
        "run_id",
        "policy_sha256",
        "node_id",
        "hook_id",
        "hook_kind",
    }:
        raise ExternalS3CapabilityFlowError("capability flow controller metadata is missing")
    if metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise ExternalS3CapabilityFlowError("capability flow controller metadata mismatch")
    text = context.get("capability_binding_json")
    if not isinstance(text, str):
        raise ExternalS3CapabilityFlowError("capability flow binding must be canonical JSON text")
    try:
        binding = s3_capability_binding_from_dict(profile, parse_json_object(text.encode("utf-8")))
    except (IntakeError, ExternalS3CapabilityError) as exc:
        raise ExternalS3CapabilityFlowError(f"capability flow binding is invalid: {exc}") from exc
    if binding.run_id != metadata["run_id"] or binding.flow_policy_sha256 != metadata["policy_sha256"]:
        raise ExternalS3CapabilityFlowError("capability binding differs from controller runtime metadata")
    return binding


def _capability_tool(profile: S3CapabilityProfile, context: dict[str, Any]) -> HookResult:
    names = _names(profile)
    binding = _binding_from_context(
        profile,
        context,
        expected_node_id=names["tool_node"],
        expected_hook_id=names["tool_hook"],
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = ExternalS3CapabilityBroker(profile).run(binding)
    receipt_bytes = canonical_json(receipt)
    return HookResult(
        HookSignal.OBSERVED,
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
        },
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
            "capability_receipt_json": receipt_bytes.decode("utf-8"),
        },
    )


def _capability_gate(profile: S3CapabilityProfile, context: dict[str, Any]) -> HookResult:
    names = _names(profile)
    binding = _binding_from_context(
        profile,
        context,
        expected_node_id=names["gate_node"],
        expected_hook_id=names["gate_hook"],
        expected_hook_kind=HookKind.GATE,
    )
    receipt_text = context.get("capability_receipt_json")
    receipt_sha256 = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(isinstance(value, str) for value in (receipt_text, receipt_sha256, state)):
        raise ExternalS3CapabilityFlowError("capability gate context fields must be strings")
    try:
        receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalS3CapabilityFlowError(f"capability receipt is not strict JSON: {exc}") from exc
    if receipt.get("status") != state:
        raise ExternalS3CapabilityFlowError("capability state binding mismatch")
    errors = validate_s3_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=state == "PASS",
    )
    if errors:
        raise ExternalS3CapabilityFlowError("capability receipt verification failed: " + "; ".join(errors))
    signal = {
        "PASS": HookSignal.PASS,
        "PARKED": HookSignal.PARKED,
        "FAIL": HookSignal.BLOCKED,
    }.get(state)
    if signal is None:
        raise ExternalS3CapabilityFlowError("capability broker returned an unknown state")
    return HookResult(
        signal,
        {"capability_state": state, "capability_receipt_sha256": receipt_sha256},
    )


def _pydmd_capability_tool(context: dict[str, Any]) -> HookResult:
    return _capability_tool(PYDMD_PROFILE, context)


def _pydmd_capability_gate(context: dict[str, Any]) -> HookResult:
    return _capability_gate(PYDMD_PROFILE, context)


def _pymdp_capability_tool(context: dict[str, Any]) -> HookResult:
    return _capability_tool(PYMDP_PROFILE, context)


def _pymdp_capability_gate(context: dict[str, Any]) -> HookResult:
    return _capability_gate(PYMDP_PROFILE, context)


def _source_registration(
    *,
    hook_id: str,
    kind: HookKind,
    handler,
    allowed_signals: tuple[HookSignal, ...],
    allowed_update_keys: tuple[str, ...] = (),
) -> HookRegistration:
    source_path = Path(__file__).resolve()
    try:
        source_sha256 = _SHA256(source_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExternalS3CapabilityFlowError(f"capability flow source unavailable: {exc}") from exc
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=source_path,
        source_sha256=source_sha256,
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=1_048_576,
    )


def _build_s3_capability_flow(
    profile: S3CapabilityProfile, *, run_id: str, ledger_path: Path
) -> MiniLevRuntime:
    names = _names(profile)
    if profile is PYDMD_PROFILE:
        tool = _pydmd_capability_tool
        gate = _pydmd_capability_gate
    elif profile is PYMDP_PROFILE:
        tool = _pymdp_capability_tool
        gate = _pymdp_capability_gate
    else:
        raise ExternalS3CapabilityFlowError("unknown fixed capability profile")

    tool_registration = _source_registration(
        hook_id=names["tool_hook"],
        kind=HookKind.TOOL,
        handler=tool,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate_registration = _source_registration(
        hook_id=names["gate_hook"],
        kind=HookKind.GATE,
        handler=gate,
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )
    policy = FlowPolicy(
        flow_id=profile.flow_id,
        entry_node=names["tool_node"],
        nodes=(
            FlowNode(names["tool_node"], tool_registration.hook_id),
            FlowNode(names["gate_node"], gate_registration.hook_id),
        ),
        transitions=(
            FlowTransition(names["tool_node"], HookSignal.OBSERVED, names["gate_node"]),
            FlowTransition(names["tool_node"], HookSignal.HOLD, "HOLD"),
            FlowTransition(names["gate_node"], HookSignal.PASS, "ELIGIBLE"),
            FlowTransition(names["gate_node"], HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition(names["gate_node"], HookSignal.PARKED, "PARKED"),
            FlowTransition(names["gate_node"], HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=(names["tool_node"], names["gate_node"]),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=profile.claim_ceiling,
    )
    try:
        return MiniLevRuntime(
            policy,
            (tool_registration, gate_registration),
            run_id=run_id,
            ledger_path=ledger_path,
        )
    except MiniLevError as exc:
        raise ExternalS3CapabilityFlowError(f"capability flow construction failed: {exc}") from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ExternalS3CapabilityFlowError(f"capability artifact persistence failed: {exc}") from exc


def _run_s3_capability_flow(
    profile: S3CapabilityProfile, *, request_id: str, run_root: Path
) -> dict[str, Any]:
    """Run one fresh two-node controller-owned external capability flow."""

    names = _names(profile)
    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalS3CapabilityFlowError("request_id must be one safe bounded identifier")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ExternalS3CapabilityFlowError("run_root must be one absolute pathlib.Path")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ExternalS3CapabilityFlowError(f"capability run directory must be new: {exc}") from exc
    request_body = {
        "schema": "constraintbox.external-s3-capability-request.v1",
        "capability_id": profile.capability_id,
        "request_id": request_id,
    }
    request_sha256 = _SHA256(canonical_json(request_body)).hexdigest()
    challenge_seed_hex = secrets.token_hex(32)
    run_material = {
        "request_sha256": request_sha256,
        "challenge_seed_hex": challenge_seed_hex,
        "run_root": str(run_root),
    }
    run_id = f"{names['prefix']}-{_SHA256(canonical_json(run_material)).hexdigest()[:32]}"
    runtime = _build_s3_capability_flow(
        profile, run_id=run_id, ledger_path=run_root / names["ledger"]
    )
    binding = S3CapabilityBinding(
        capability_id=profile.capability_id,
        run_id=run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=profile.step_id,
        challenge_seed_hex=challenge_seed_hex,
    )
    try:
        flow_receipt = runtime.run(
            {
                "capability_binding_json": canonical_json(binding.to_dict()).decode("utf-8")
            }
        )
    except MiniLevError as exc:
        raise ExternalS3CapabilityFlowError(f"capability flow execution failed: {exc}") from exc
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise ExternalS3CapabilityFlowError(f"capability flow receipt failed verification: {reason}")
    receipt_text = flow_receipt["final_context"].get("capability_receipt_json")
    receipt_sha256 = flow_receipt["final_context"].get("capability_receipt_sha256")
    if not isinstance(receipt_text, str) or not isinstance(receipt_sha256, str):
        raise ExternalS3CapabilityFlowError("capability flow produced no external receipt")
    try:
        capability_receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalS3CapabilityFlowError(f"capability receipt is invalid: {exc}") from exc
    errors = validate_s3_capability_receipt(
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=flow_receipt["terminal"] == "ELIGIBLE",
    )
    if errors:
        raise ExternalS3CapabilityFlowError("persisted capability receipt failed verification: " + "; ".join(errors))
    expected_terminal = {"PASS": "ELIGIBLE", "FAIL": "BLOCKED", "PARKED": "PARKED"}.get(
        capability_receipt.get("status")
    )
    if expected_terminal != flow_receipt["terminal"]:
        raise ExternalS3CapabilityFlowError("capability receipt status differs from flow terminal")
    _persist_exclusive(run_root / names["receipt"], capability_receipt)
    _persist_exclusive(run_root / names["flow_receipt"], flow_receipt)
    return {
        "schema": FLOW_RESULT_SCHEMA,
        "capability_id": profile.capability_id,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "run_id": run_id,
        "flow_policy_sha256": runtime.policy_sha256,
        "disposition": flow_receipt["terminal"],
        "reason": capability_receipt["reason"],
        "capability_receipt_sha256": receipt_sha256,
        "flow_receipt_sha256": runtime.receipt_sha256,
        "artifacts": {
            "capability_receipt": str(run_root / names["receipt"]),
            "flow_receipt": str(run_root / names["flow_receipt"]),
            "flow_ledger": str(run_root / names["ledger"]),
            "flow_ledger_head": str(run_root / f"{names['ledger']}.head"),
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": profile.claim_ceiling,
    }
