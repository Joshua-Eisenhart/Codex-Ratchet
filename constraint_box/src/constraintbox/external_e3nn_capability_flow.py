"""Two-node deterministic Mini-Lev flow for the bounded external e3nn profile.

This is intentionally only a tool observation followed by a receipt gate.
The Mini-Lev controller selects the binding and terminal transition; e3nn
cannot select a retry, release, or promotion outcome.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import Any

from .external_e3nn_capability import (
    E3NN_WIGNER_PROFILE,
    E3nnCapabilityBinding,
    E3nnCapabilityBroker,
    ExternalE3nnCapabilityError,
    e3nn_capability_binding_from_dict,
    validate_e3nn_capability_receipt,
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


FLOW_RESULT_SCHEMA = "constraintbox.external-e3nn-capability-flow-result.v1"
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")

_NAMES = {
    "tool_node": "e3nn-capability-tool",
    "gate_node": "e3nn-capability-gate",
    "tool_hook": "e3nn-wigner-crosscheck-capability-tool",
    "gate_hook": "e3nn-wigner-crosscheck-capability-gate",
    "prefix": "e3nn",
    "receipt": "e3nn_wigner_crosscheck_capability_receipt.json",
    "flow_receipt": "e3nn_wigner_crosscheck_flow_receipt.json",
    "ledger": "e3nn_wigner_crosscheck_flow_events.jsonl",
}

CAPABILITY_RECEIPT_NAME = _NAMES["receipt"]
FLOW_RECEIPT_NAME = _NAMES["flow_receipt"]
FLOW_LEDGER_NAME = _NAMES["ledger"]

_PINNED_BROKER = E3nnCapabilityBroker
_PINNED_BINDING_PARSER = e3nn_capability_binding_from_dict
_PINNED_RECEIPT_VALIDATOR = validate_e3nn_capability_receipt


class ExternalE3nnCapabilityFlowError(ValueError):
    """The fixed external e3nn Mini-Lev flow could not run or verify."""


def _verify_live_dependencies() -> None:
    if (
        E3nnCapabilityBroker is not _PINNED_BROKER
        or e3nn_capability_binding_from_dict is not _PINNED_BINDING_PARSER
        or validate_e3nn_capability_receipt is not _PINNED_RECEIPT_VALIDATOR
    ):
        raise ExternalE3nnCapabilityFlowError("capability handler dependency binding drift")


def _binding_from_context(
    context: dict[str, Any],
    *,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> E3nnCapabilityBinding:
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
        raise ExternalE3nnCapabilityFlowError("capability flow controller metadata is missing")
    if metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise ExternalE3nnCapabilityFlowError("capability flow controller metadata mismatch")
    text = context.get("capability_binding_json")
    if not isinstance(text, str):
        raise ExternalE3nnCapabilityFlowError("capability flow binding must be canonical JSON text")
    try:
        binding = e3nn_capability_binding_from_dict(parse_json_object(text.encode("utf-8")))
    except (IntakeError, ExternalE3nnCapabilityError) as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability flow binding is invalid: {exc}") from exc
    if binding.run_id != metadata["run_id"] or binding.flow_policy_sha256 != metadata["policy_sha256"]:
        raise ExternalE3nnCapabilityFlowError("capability binding differs from controller runtime metadata")
    return binding


def _e3nn_capability_tool(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id=_NAMES["tool_node"],
        expected_hook_id=_NAMES["tool_hook"],
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = E3nnCapabilityBroker().run(binding)
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


def _e3nn_capability_gate(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id=_NAMES["gate_node"],
        expected_hook_id=_NAMES["gate_hook"],
        expected_hook_kind=HookKind.GATE,
    )
    receipt_text = context.get("capability_receipt_json")
    receipt_sha256 = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(isinstance(value, str) for value in (receipt_text, receipt_sha256, state)):
        raise ExternalE3nnCapabilityFlowError("capability gate context fields must be strings")
    try:
        receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability receipt is not strict JSON: {exc}") from exc
    if receipt.get("status") != state:
        raise ExternalE3nnCapabilityFlowError("capability state binding mismatch")
    errors = validate_e3nn_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=state == "PASS",
    )
    if errors:
        raise ExternalE3nnCapabilityFlowError(
            "capability receipt verification failed: " + "; ".join(errors)
        )
    signal = {
        "PASS": HookSignal.PASS,
        "PARKED": HookSignal.PARKED,
        "FAIL": HookSignal.BLOCKED,
    }.get(state)
    if signal is None:
        raise ExternalE3nnCapabilityFlowError("capability broker returned an unknown state")
    return HookResult(
        signal,
        {"capability_state": state, "capability_receipt_sha256": receipt_sha256},
    )


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
        raise ExternalE3nnCapabilityFlowError(f"capability flow source unavailable: {exc}") from exc
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


def _build_e3nn_capability_flow(*, run_id: str, ledger_path: Path) -> MiniLevRuntime:
    tool_registration = _source_registration(
        hook_id=_NAMES["tool_hook"],
        kind=HookKind.TOOL,
        handler=_e3nn_capability_tool,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate_registration = _source_registration(
        hook_id=_NAMES["gate_hook"],
        kind=HookKind.GATE,
        handler=_e3nn_capability_gate,
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )
    policy = FlowPolicy(
        flow_id=E3NN_WIGNER_PROFILE.flow_id,
        entry_node=_NAMES["tool_node"],
        nodes=(
            FlowNode(_NAMES["tool_node"], tool_registration.hook_id),
            FlowNode(_NAMES["gate_node"], gate_registration.hook_id),
        ),
        transitions=(
            FlowTransition(_NAMES["tool_node"], HookSignal.OBSERVED, _NAMES["gate_node"]),
            FlowTransition(_NAMES["tool_node"], HookSignal.HOLD, "HOLD"),
            FlowTransition(_NAMES["gate_node"], HookSignal.PASS, "ELIGIBLE"),
            FlowTransition(_NAMES["gate_node"], HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition(_NAMES["gate_node"], HookSignal.PARKED, "PARKED"),
            FlowTransition(_NAMES["gate_node"], HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=(_NAMES["tool_node"], _NAMES["gate_node"]),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=E3NN_WIGNER_PROFILE.claim_ceiling,
    )
    try:
        return MiniLevRuntime(
            policy,
            (tool_registration, gate_registration),
            run_id=run_id,
            ledger_path=ledger_path,
        )
    except MiniLevError as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability flow construction failed: {exc}") from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability artifact persistence failed: {exc}") from exc


def run_e3nn_capability_flow(*, request_id: str, run_root: Path) -> dict[str, Any]:
    """Run one fresh two-node controller-owned external capability flow."""

    profile = E3NN_WIGNER_PROFILE
    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalE3nnCapabilityFlowError("request_id must be one safe bounded identifier")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ExternalE3nnCapabilityFlowError("run_root must be one absolute pathlib.Path")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability run directory must be new: {exc}") from exc
    request_body = {
        "schema": "constraintbox.external-e3nn-capability-request.v1",
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
    run_id = f"{_NAMES['prefix']}-{_SHA256(canonical_json(run_material)).hexdigest()[:32]}"
    runtime = _build_e3nn_capability_flow(run_id=run_id, ledger_path=run_root / _NAMES["ledger"])
    binding = E3nnCapabilityBinding(
        capability_id=profile.capability_id,
        run_id=run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=profile.step_id,
        challenge_seed_hex=challenge_seed_hex,
    )
    try:
        flow_receipt = runtime.run(
            {"capability_binding_json": canonical_json(binding.to_dict()).decode("utf-8")}
        )
    except MiniLevError as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability flow execution failed: {exc}") from exc
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise ExternalE3nnCapabilityFlowError(f"capability flow receipt failed verification: {reason}")
    receipt_text = flow_receipt["final_context"].get("capability_receipt_json")
    receipt_sha256 = flow_receipt["final_context"].get("capability_receipt_sha256")
    if not isinstance(receipt_text, str) or not isinstance(receipt_sha256, str):
        raise ExternalE3nnCapabilityFlowError("capability flow produced no external receipt")
    try:
        capability_receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalE3nnCapabilityFlowError(f"capability receipt is invalid: {exc}") from exc
    errors = validate_e3nn_capability_receipt(
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=flow_receipt["terminal"] == "ELIGIBLE",
    )
    if errors:
        raise ExternalE3nnCapabilityFlowError(
            "persisted capability receipt failed verification: " + "; ".join(errors)
        )
    expected_terminal = {"PASS": "ELIGIBLE", "FAIL": "BLOCKED", "PARKED": "PARKED"}.get(
        capability_receipt.get("status")
    )
    if expected_terminal != flow_receipt["terminal"]:
        raise ExternalE3nnCapabilityFlowError("capability receipt status differs from flow terminal")
    _persist_exclusive(run_root / _NAMES["receipt"], capability_receipt)
    _persist_exclusive(run_root / _NAMES["flow_receipt"], flow_receipt)
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
            "capability_receipt": str(run_root / _NAMES["receipt"]),
            "flow_receipt": str(run_root / _NAMES["flow_receipt"]),
            "flow_ledger": str(run_root / _NAMES["ledger"]),
            "flow_ledger_head": str(run_root / f"{_NAMES['ledger']}.head"),
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": profile.claim_ceiling,
    }
