"""Shared fixed two-node Mini-Lev flow mechanics for bounded numeric tools.

Profile modules own the actual hook functions and pin this helper's source and
function identities before calling it.  This module never accepts a caller
selected command, executable, profile, retry, or release transition.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import Any, Callable

from .external_bounded_numerics import (
    BoundedNumericsBinding,
    BoundedNumericsProfile,
    ExternalBoundedNumericsError,
    bounded_numerics_binding_from_dict,
    validate_bounded_numerics_receipt,
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


_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class ExternalBoundedNumericsFlowError(ValueError):
    """A fixed bounded-numerics Mini-Lev flow could not be completed."""


def binding_from_context(
    context: dict[str, Any],
    *,
    profile: BoundedNumericsProfile,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> BoundedNumericsBinding:
    metadata = context.get(CONTROLLER_METADATA_KEY)
    expected_metadata_keys = {
        "schema", "run_id", "policy_sha256", "node_id", "hook_id", "hook_kind"
    }
    if not isinstance(metadata, dict) or set(metadata) != expected_metadata_keys:
        raise ExternalBoundedNumericsFlowError("controller metadata is missing")
    if metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise ExternalBoundedNumericsFlowError("controller metadata mismatch")
    text = context.get("capability_binding_json")
    if not isinstance(text, str):
        raise ExternalBoundedNumericsFlowError("capability binding must be canonical JSON")
    try:
        binding = bounded_numerics_binding_from_dict(
            profile, parse_json_object(text.encode("utf-8"))
        )
    except (IntakeError, ExternalBoundedNumericsError) as exc:
        raise ExternalBoundedNumericsFlowError(f"capability binding is invalid: {exc}") from exc
    if binding.run_id != metadata["run_id"] or binding.flow_policy_sha256 != metadata["policy_sha256"]:
        raise ExternalBoundedNumericsFlowError("binding differs from controller metadata")
    return binding


def tool_observation(
    context: dict[str, Any],
    *,
    profile: BoundedNumericsProfile,
    runner: Callable[[BoundedNumericsBinding], dict[str, object]],
    expected_node_id: str,
    expected_hook_id: str,
) -> HookResult:
    binding = binding_from_context(
        context,
        profile=profile,
        expected_node_id=expected_node_id,
        expected_hook_id=expected_hook_id,
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = runner(binding)
    if not isinstance(receipt, dict) or not isinstance(receipt.get("receipt_sha256"), str):
        raise ExternalBoundedNumericsFlowError("capability runner returned no typed receipt")
    receipt_bytes = canonical_json(receipt)
    state = receipt.get("status")
    if not isinstance(state, str):
        raise ExternalBoundedNumericsFlowError("capability runner returned no state")
    return HookResult(
        HookSignal.OBSERVED,
        {"capability_state": state, "capability_receipt_sha256": receipt["receipt_sha256"]},
        {
            "capability_state": state,
            "capability_receipt_sha256": receipt["receipt_sha256"],
            "capability_receipt_json": receipt_bytes.decode("utf-8"),
        },
    )


def gate_observation(
    context: dict[str, Any],
    *,
    profile: BoundedNumericsProfile,
    expected_node_id: str,
    expected_hook_id: str,
) -> HookResult:
    binding = binding_from_context(
        context,
        profile=profile,
        expected_node_id=expected_node_id,
        expected_hook_id=expected_hook_id,
        expected_hook_kind=HookKind.GATE,
    )
    text = context.get("capability_receipt_json")
    receipt_sha256 = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(isinstance(value, str) for value in (text, receipt_sha256, state)):
        raise ExternalBoundedNumericsFlowError("capability gate fields must be strings")
    try:
        receipt = parse_json_object(text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalBoundedNumericsFlowError(f"capability receipt is invalid: {exc}") from exc
    if receipt.get("status") != state:
        raise ExternalBoundedNumericsFlowError("capability state binding mismatch")
    errors = validate_bounded_numerics_receipt(
        profile,
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=state == "PASS",
    )
    if errors:
        raise ExternalBoundedNumericsFlowError(
            "capability receipt verification failed: " + "; ".join(errors)
        )
    signal = {"PASS": HookSignal.PASS, "FAIL": HookSignal.BLOCKED, "PARKED": HookSignal.PARKED}.get(state)
    if signal is None:
        raise ExternalBoundedNumericsFlowError("capability state is unknown")
    return HookResult(signal, {"capability_state": state, "capability_receipt_sha256": receipt_sha256})


def _source_registration(
    *,
    hook_id: str,
    kind: HookKind,
    handler: Callable[[dict[str, Any]], HookResult],
    source_path: Path,
    allowed_signals: tuple[HookSignal, ...],
    allowed_update_keys: tuple[str, ...] = (),
) -> HookRegistration:
    try:
        source_sha256 = _SHA256(source_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExternalBoundedNumericsFlowError(f"flow source unavailable: {exc}") from exc
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=source_path,
        source_sha256=source_sha256,
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=524_288,
    )


def _build_flow(
    *,
    profile: BoundedNumericsProfile,
    flow_id: str,
    tool_node: str,
    gate_node: str,
    tool_hook: str,
    gate_hook: str,
    tool_handler: Callable[[dict[str, Any]], HookResult],
    gate_handler: Callable[[dict[str, Any]], HookResult],
    flow_source_path: Path,
    run_id: str,
    ledger_path: Path,
) -> MiniLevRuntime:
    tool = _source_registration(
        hook_id=tool_hook,
        kind=HookKind.TOOL,
        handler=tool_handler,
        source_path=flow_source_path,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate = _source_registration(
        hook_id=gate_hook,
        kind=HookKind.GATE,
        handler=gate_handler,
        source_path=flow_source_path,
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )
    policy = FlowPolicy(
        flow_id=flow_id,
        entry_node=tool_node,
        nodes=(FlowNode(tool_node, tool.hook_id), FlowNode(gate_node, gate.hook_id)),
        transitions=(
            FlowTransition(tool_node, HookSignal.OBSERVED, gate_node),
            FlowTransition(tool_node, HookSignal.HOLD, "HOLD"),
            FlowTransition(gate_node, HookSignal.PASS, "ELIGIBLE"),
            FlowTransition(gate_node, HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition(gate_node, HookSignal.PARKED, "PARKED"),
            FlowTransition(gate_node, HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=(tool_node, gate_node),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=profile.claim_ceiling,
    )
    try:
        return MiniLevRuntime(policy, (tool, gate), run_id=run_id, ledger_path=ledger_path)
    except MiniLevError as exc:
        raise ExternalBoundedNumericsFlowError(f"flow construction failed: {exc}") from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ExternalBoundedNumericsFlowError(f"artifact persistence failed for {path}: {exc}") from exc


def run_profile_flow(
    *,
    profile: BoundedNumericsProfile,
    flow_id: str,
    tool_node: str,
    gate_node: str,
    tool_hook: str,
    gate_hook: str,
    tool_handler: Callable[[dict[str, Any]], HookResult],
    gate_handler: Callable[[dict[str, Any]], HookResult],
    flow_source_path: Path,
    flow_result_schema: str,
    capability_receipt_name: str,
    flow_receipt_name: str,
    flow_ledger_name: str,
    run_prefix: str,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalBoundedNumericsFlowError("request_id must be a safe identifier")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ExternalBoundedNumericsFlowError("run_root must be an absolute pathlib.Path")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ExternalBoundedNumericsFlowError(f"capability run directory must be new: {exc}") from exc
    request = {
        "schema": "constraintbox.external-capability-request.v1",
        "capability_id": profile.capability_id,
        "request_id": request_id,
    }
    request_sha256 = _SHA256(canonical_json(request)).hexdigest()
    challenge_seed_hex = secrets.token_hex(32)
    run_material = {
        "request_sha256": request_sha256,
        "challenge_seed_hex": challenge_seed_hex,
        "run_root": str(run_root),
    }
    run_id = f"{run_prefix}-{_SHA256(canonical_json(run_material)).hexdigest()[:32]}"
    runtime = _build_flow(
        profile=profile,
        flow_id=flow_id,
        tool_node=tool_node,
        gate_node=gate_node,
        tool_hook=tool_hook,
        gate_hook=gate_hook,
        tool_handler=tool_handler,
        gate_handler=gate_handler,
        flow_source_path=flow_source_path,
        run_id=run_id,
        ledger_path=run_root / flow_ledger_name,
    )
    binding = BoundedNumericsBinding(
        capability_id=profile.capability_id,
        run_id=run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=profile.step_id,
        challenge_seed_hex=challenge_seed_hex,
    )
    try:
        flow_receipt = runtime.run({"capability_binding_json": canonical_json(binding.to_dict()).decode("utf-8")})
    except MiniLevError as exc:
        raise ExternalBoundedNumericsFlowError(f"flow execution failed: {exc}") from exc
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise ExternalBoundedNumericsFlowError(f"flow receipt failed verification: {reason}")
    text = flow_receipt["final_context"].get("capability_receipt_json")
    receipt_sha256 = flow_receipt["final_context"].get("capability_receipt_sha256")
    if not isinstance(text, str) or not isinstance(receipt_sha256, str):
        raise ExternalBoundedNumericsFlowError("flow produced no external receipt")
    try:
        capability_receipt = parse_json_object(text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalBoundedNumericsFlowError(f"capability receipt is invalid: {exc}") from exc
    errors = validate_bounded_numerics_receipt(
        profile,
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=flow_receipt["terminal"] == "ELIGIBLE",
    )
    if errors:
        raise ExternalBoundedNumericsFlowError("persisted receipt failed verification: " + "; ".join(errors))
    expected_terminal = {"PASS": "ELIGIBLE", "FAIL": "BLOCKED", "PARKED": "PARKED"}.get(capability_receipt.get("status"))
    if expected_terminal != flow_receipt["terminal"]:
        raise ExternalBoundedNumericsFlowError("receipt status differs from flow terminal")
    _persist_exclusive(run_root / capability_receipt_name, capability_receipt)
    _persist_exclusive(run_root / flow_receipt_name, flow_receipt)
    return {
        "schema": flow_result_schema,
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
            "capability_receipt": str(run_root / capability_receipt_name),
            "flow_receipt": str(run_root / flow_receipt_name),
            "flow_ledger": str(run_root / flow_ledger_name),
            "flow_ledger_head": str(run_root / f"{flow_ledger_name}.head"),
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": profile.claim_ceiling,
    }
