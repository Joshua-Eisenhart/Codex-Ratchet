"""Caller-reachable two-node mini-LevOS flow for one external JAX capability."""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import Any

from .external_jax_capability import (
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    STEP_ID,
    ExternalJaxCapabilityError,
    JaxAutodiffCapabilityBroker,
    JaxCapabilityBinding,
    jax_capability_binding_from_dict,
    validate_jax_capability_receipt,
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


FLOW_RESULT_SCHEMA = "constraintbox.external-jax-capability-flow-result.v1"
FLOW_RECEIPT_NAME = "jax_autodiff_flow_receipt.json"
FLOW_LEDGER_NAME = "jax_autodiff_flow_events.jsonl"
CAPABILITY_RECEIPT_NAME = "jax_autodiff_capability_receipt.json"
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class ExternalJaxCapabilityFlowError(ValueError):
    """The fixed external JAX capability flow could not run or verify."""


_PINNED_CAPABILITY_BROKER = JaxAutodiffCapabilityBroker
_PINNED_BINDING_PARSER = jax_capability_binding_from_dict
_PINNED_RECEIPT_VALIDATOR = validate_jax_capability_receipt


def _verify_live_dependencies() -> None:
    """Reject ordinary in-process rebinding of the fixed handler dependencies."""

    if (
        JaxAutodiffCapabilityBroker is not _PINNED_CAPABILITY_BROKER
        or jax_capability_binding_from_dict is not _PINNED_BINDING_PARSER
        or validate_jax_capability_receipt is not _PINNED_RECEIPT_VALIDATOR
    ):
        raise ExternalJaxCapabilityFlowError(
            "JAX capability handler dependency binding drift"
        )


def _binding_from_context(
    context: dict[str, Any],
    *,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> JaxCapabilityBinding:
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
        raise ExternalJaxCapabilityFlowError(
            "JAX capability flow controller metadata is missing"
        )
    if metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise ExternalJaxCapabilityFlowError(
            "JAX capability flow controller metadata mismatch"
        )
    text = context.get("capability_binding_json")
    if not isinstance(text, str):
        raise ExternalJaxCapabilityFlowError(
            "JAX capability flow binding must be canonical JSON text"
        )
    try:
        value = parse_json_object(text.encode("utf-8"))
        binding = jax_capability_binding_from_dict(value)
    except (IntakeError, ExternalJaxCapabilityError) as exc:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability flow binding is invalid: {exc}"
        ) from exc
    if (
        binding.run_id != metadata["run_id"]
        or binding.flow_policy_sha256 != metadata["policy_sha256"]
    ):
        raise ExternalJaxCapabilityFlowError(
            "JAX capability binding differs from controller runtime metadata"
        )
    return binding


def _jax_capability_tool(context: dict[str, Any]) -> HookResult:
    """Run the fixed JAX broker and return only a typed observation."""

    binding = _binding_from_context(
        context,
        expected_node_id="jax-capability-tool",
        expected_hook_id="jax-autodiff-capability-tool",
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = JaxAutodiffCapabilityBroker().run(binding)
    receipt_bytes = canonical_json(receipt)
    receipt_sha256 = receipt["receipt_sha256"]
    return HookResult(
        HookSignal.OBSERVED,
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt_sha256,
        },
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt_sha256,
            "capability_receipt_json": receipt_bytes.decode("utf-8"),
        },
    )


def _jax_capability_gate(context: dict[str, Any]) -> HookResult:
    """Revalidate the JAX receipt and report a non-authoritative signal."""

    binding = _binding_from_context(
        context,
        expected_node_id="jax-capability-gate",
        expected_hook_id="jax-autodiff-capability-gate",
        expected_hook_kind=HookKind.GATE,
    )
    receipt_text = context.get("capability_receipt_json")
    expected_sha256 = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(
        isinstance(value, str)
        for value in (receipt_text, expected_sha256, state)
    ):
        raise ExternalJaxCapabilityFlowError(
            "JAX capability gate context fields must be strings"
        )
    try:
        receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability receipt is not strict JSON: {exc}"
        ) from exc
    if receipt.get("status") != state:
        raise ExternalJaxCapabilityFlowError("JAX capability state binding mismatch")
    errors = validate_jax_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=expected_sha256,
        require_pass=state == "PASS",
    )
    if errors:
        raise ExternalJaxCapabilityFlowError(
            "JAX capability receipt verification failed: " + "; ".join(errors)
        )
    signal = {
        "PASS": HookSignal.PASS,
        "PARKED": HookSignal.PARKED,
        "FAIL": HookSignal.BLOCKED,
    }.get(state)
    if signal is None:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability broker returned an unknown state: {state}"
        )
    return HookResult(
        signal,
        {
            "capability_state": state,
            "capability_receipt_sha256": expected_sha256,
        },
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
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability flow source unavailable: {exc}"
        ) from exc
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


def _build_jax_capability_flow(
    *,
    run_id: str,
    ledger_path: Path,
) -> MiniLevRuntime:
    """Construct the exact JAX tool-then-gate external capability flow."""

    tool = _source_registration(
        hook_id="jax-autodiff-capability-tool",
        kind=HookKind.TOOL,
        handler=_jax_capability_tool,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate = _source_registration(
        hook_id="jax-autodiff-capability-gate",
        kind=HookKind.GATE,
        handler=_jax_capability_gate,
        allowed_signals=(
            HookSignal.PASS,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        ),
    )
    policy = FlowPolicy(
        flow_id="constraintbox.jax-autodiff-capability-flow.v1",
        entry_node="jax-capability-tool",
        nodes=(
            FlowNode("jax-capability-tool", tool.hook_id),
            FlowNode("jax-capability-gate", gate.hook_id),
        ),
        transitions=(
            FlowTransition(
                "jax-capability-tool",
                HookSignal.OBSERVED,
                "jax-capability-gate",
            ),
            FlowTransition("jax-capability-tool", HookSignal.HOLD, "HOLD"),
            FlowTransition("jax-capability-gate", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("jax-capability-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("jax-capability-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("jax-capability-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=("jax-capability-tool", "jax-capability-gate"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=CAPABILITY_CLAIM_CEILING,
    )
    try:
        return MiniLevRuntime(
            policy,
            (tool, gate),
            run_id=run_id,
            ledger_path=ledger_path,
        )
    except MiniLevError as exc:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability flow construction failed: {exc}"
        ) from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability artifact persistence failed for {path}: {exc}"
        ) from exc


def run_jax_capability_flow(
    *,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    """Run one fresh, controller-challenged external JAX capability flow."""

    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalJaxCapabilityFlowError(
            "request_id must be one safe bounded identifier"
        )
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ExternalJaxCapabilityFlowError(
            "run_root must be one absolute pathlib.Path"
        )
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ExternalJaxCapabilityFlowError(
            f"capability run directory must be new: {exc}"
        ) from exc
    request_body = {
        "schema": "constraintbox.external-capability-request.v1",
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
    }
    request_sha256 = _SHA256(canonical_json(request_body)).hexdigest()
    challenge_seed_hex = secrets.token_hex(32)
    run_material = {
        "request_sha256": request_sha256,
        "challenge_seed_hex": challenge_seed_hex,
        "run_root": str(run_root),
    }
    run_id = f"jax-{_SHA256(canonical_json(run_material)).hexdigest()[:32]}"
    runtime = _build_jax_capability_flow(
        run_id=run_id,
        ledger_path=run_root / FLOW_LEDGER_NAME,
    )
    binding = JaxCapabilityBinding(
        capability_id=CAPABILITY_ID,
        run_id=run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=STEP_ID,
        challenge_seed_hex=challenge_seed_hex,
    )
    try:
        flow_receipt = runtime.run(
            {
                "capability_binding_json": canonical_json(
                    binding.to_dict()
                ).decode("utf-8")
            }
        )
    except MiniLevError as exc:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability flow execution failed: {exc}"
        ) from exc
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability flow receipt failed verification: {reason}"
        )
    receipt_text = flow_receipt["final_context"].get(
        "capability_receipt_json"
    )
    receipt_sha256 = flow_receipt["final_context"].get(
        "capability_receipt_sha256"
    )
    if not isinstance(receipt_text, str) or not isinstance(receipt_sha256, str):
        raise ExternalJaxCapabilityFlowError(
            "JAX capability flow produced no external receipt"
        )
    try:
        capability_receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalJaxCapabilityFlowError(
            f"JAX capability receipt is invalid: {exc}"
        ) from exc
    capability_errors = validate_jax_capability_receipt(
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=flow_receipt["terminal"] == "ELIGIBLE",
    )
    if capability_errors:
        raise ExternalJaxCapabilityFlowError(
            "persisted JAX capability receipt failed verification: "
            + "; ".join(capability_errors)
        )
    expected_terminal = {
        "PASS": "ELIGIBLE",
        "FAIL": "BLOCKED",
        "PARKED": "PARKED",
    }.get(capability_receipt.get("status"))
    if expected_terminal != flow_receipt["terminal"]:
        raise ExternalJaxCapabilityFlowError(
            "JAX capability receipt status differs from flow terminal"
        )
    _persist_exclusive(run_root / CAPABILITY_RECEIPT_NAME, capability_receipt)
    _persist_exclusive(run_root / FLOW_RECEIPT_NAME, flow_receipt)
    return {
        "schema": FLOW_RESULT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "run_id": run_id,
        "flow_policy_sha256": runtime.policy_sha256,
        "disposition": flow_receipt["terminal"],
        "reason": capability_receipt["reason"],
        "capability_receipt_sha256": receipt_sha256,
        "flow_receipt_sha256": runtime.receipt_sha256,
        "artifacts": {
            "capability_receipt": str(run_root / CAPABILITY_RECEIPT_NAME),
            "flow_receipt": str(run_root / FLOW_RECEIPT_NAME),
            "flow_ledger": str(run_root / FLOW_LEDGER_NAME),
            "flow_ledger_head": str(run_root / f"{FLOW_LEDGER_NAME}.head"),
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }
