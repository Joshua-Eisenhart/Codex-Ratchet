"""Caller-reachable mini-LevOS wrapper for the fixed formal task controller.

The tool node executes the already registered formal controller.  It returns a
controller receipt as an opaque canonical JSON string plus a narrow state
observation.  A separate deterministic gate node validates that binding and
maps the formal disposition through the frozen flow transition table.  Neither
the request nor a model supplies hooks, transitions, paths, bounds, or a
verdict.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contracts import DecisionRecord, Disposition
from .intake import canonical_json, parse_json_object
from .mini_levos import (
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


FORMAL_FLOW_RECEIPT = "formal_flow_receipt.json"
FORMAL_FLOW_LEDGER = "formal_flow_events.jsonl"
_SHA256 = hashlib.sha256
_DECISION_KEYS = {
    "schema",
    "request_id",
    "task_kind",
    "profile_id",
    "policy_sha256",
    "input_sha256",
    "disposition",
    "reason",
    "evidence",
    "claim_ceiling",
    "controller_emitted",
    "promotion_allowed",
}


class FormalFlowError(RuntimeError):
    """The fixed formal flow failed construction or receipt verification."""


def _formal_controller_tool(context: dict[str, Any]) -> HookResult:
    """Execute one controller-selected formal task as an observation tool."""

    try:
        task_kind = context["task_kind"]
        request_id = context["request_id"]
        payload_hex = context["payload_hex"]
        run_root = Path(context["run_root"])
        if not all(
            isinstance(value, str)
            for value in (task_kind, request_id, payload_hex)
        ):
            raise TypeError("formal tool context fields must be strings")
        if not isinstance(context["run_root"], str) or not run_root.is_absolute():
            raise TypeError("formal tool run_root must be an absolute path")
        payload = bytes.fromhex(payload_hex)
    except (KeyError, TypeError, ValueError) as exc:
        raise FormalFlowError(f"formal tool context is invalid: {exc}") from exc

    # Lazy import avoids making formal_registry and this wrapper a cyclic
    # authority surface at module import time.
    from .formal_registry import _run_formal_task_core

    decision = _run_formal_task_core(
        task_kind=task_kind,
        request_id=request_id,
        payload=payload,
        run_root=run_root,
    )
    decision_bytes = canonical_json(decision.to_dict())
    state = decision.disposition.value
    decision_sha256 = _SHA256(decision_bytes).hexdigest()
    return HookResult(
        HookSignal.OBSERVED,
        {
            "formal_state": state,
            "formal_record_sha256": decision_sha256,
        },
        {
            "formal_state": state,
            "formal_record_sha256": decision_sha256,
            "formal_record_json": decision_bytes.decode("utf-8"),
        },
    )


def _formal_disposition_gate(context: dict[str, Any]) -> HookResult:
    """Validate the tool receipt and report one typed gate observation."""

    try:
        state = context["formal_state"]
        record_text = context["formal_record_json"]
        expected_sha256 = context["formal_record_sha256"]
        if not all(
            isinstance(value, str)
            for value in (state, record_text, expected_sha256)
        ):
            raise TypeError("formal gate context fields must be strings")
        record = parse_json_object(record_text.encode("utf-8"))
    except (KeyError, TypeError, ValueError) as exc:
        raise FormalFlowError(f"formal gate context is invalid: {exc}") from exc
    if set(record) != _DECISION_KEYS:
        raise FormalFlowError("formal decision record keys mismatch")
    if _SHA256(canonical_json(record)).hexdigest() != expected_sha256:
        raise FormalFlowError("formal decision record digest mismatch")
    if (
        record.get("disposition") != state
        or record.get("controller_emitted") is not True
        or record.get("promotion_allowed") is not False
    ):
        raise FormalFlowError("formal decision authority fields mismatch")
    signal_by_state = {
        Disposition.ELIGIBLE.value: HookSignal.PASS,
        Disposition.BLOCKED.value: HookSignal.BLOCKED,
        Disposition.PARKED.value: HookSignal.PARKED,
    }
    signal = signal_by_state.get(state)
    if signal is None:
        raise FormalFlowError(f"formal controller did not admit a state: {state}")
    return HookResult(
        signal,
        {
            "formal_state": state,
            "formal_record_sha256": expected_sha256,
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
        raise FormalFlowError(f"formal flow source unavailable: {exc}") from exc
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=source_path,
        source_sha256=source_sha256,
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=262_144,
    )


def build_formal_flow(
    *,
    run_id: str,
    ledger_path: Path,
) -> MiniLevRuntime:
    """Construct the exact two-node formal-controller flow."""

    tool = _source_registration(
        hook_id="formal-controller-tool",
        kind=HookKind.TOOL,
        handler=_formal_controller_tool,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "formal_state",
            "formal_record_sha256",
            "formal_record_json",
        ),
    )
    gate = _source_registration(
        hook_id="formal-disposition-gate",
        kind=HookKind.GATE,
        handler=_formal_disposition_gate,
        allowed_signals=(
            HookSignal.PASS,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        ),
    )
    policy = FlowPolicy(
        flow_id="constraintbox.formal-controller-flow.v1",
        entry_node="formal-tool",
        nodes=(
            FlowNode("formal-tool", tool.hook_id),
            FlowNode("formal-gate", gate.hook_id),
        ),
        transitions=(
            FlowTransition(
                "formal-tool",
                HookSignal.OBSERVED,
                "formal-gate",
            ),
            FlowTransition("formal-tool", HookSignal.HOLD, "HOLD"),
            FlowTransition("formal-gate", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("formal-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("formal-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("formal-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=("formal-tool", "formal-gate"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=524_288,
        max_event_bytes=786_432,
        max_receipt_bytes=4_194_304,
        claim_ceiling=(
            "one fixed formal controller task and its disposition mapping ran "
            "through the two-node CB mini-LevOS flow on the selected local runtime"
        ),
    )
    try:
        return MiniLevRuntime(
            policy,
            (tool, gate),
            run_id=run_id,
            ledger_path=ledger_path,
        )
    except MiniLevError as exc:
        raise FormalFlowError(f"formal flow construction failed: {exc}") from exc


def _decision_from_record(record: dict[str, Any]) -> DecisionRecord:
    if set(record) != _DECISION_KEYS:
        raise FormalFlowError("formal decision record keys mismatch")
    try:
        return DecisionRecord(
            schema=record["schema"],
            request_id=record["request_id"],
            task_kind=record["task_kind"],
            profile_id=record["profile_id"],
            policy_sha256=record["policy_sha256"],
            input_sha256=record["input_sha256"],
            disposition=Disposition(record["disposition"]),
            reason=record["reason"],
            evidence=record["evidence"],
            claim_ceiling=record["claim_ceiling"],
            controller_emitted=record["controller_emitted"],
            promotion_allowed=record["promotion_allowed"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise FormalFlowError(f"formal decision record is invalid: {exc}") from exc


def run_formal_flow(
    *,
    task_kind: str,
    request_id: str,
    payload: bytes,
    run_root: Path,
) -> DecisionRecord:
    """Run and verify the caller-reachable mini-LevOS formal path."""

    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise FormalFlowError("run_root must be an absolute pathlib.Path")
    binding = canonical_json(
        {
            "task_kind": task_kind,
            "request_id": request_id,
            "payload_sha256": _SHA256(payload).hexdigest(),
            "run_root": str(run_root),
        }
    )
    run_id = f"formal-{_SHA256(binding).hexdigest()[:32]}"
    ledger_path = run_root / FORMAL_FLOW_LEDGER
    runtime = build_formal_flow(run_id=run_id, ledger_path=ledger_path)
    try:
        receipt = runtime.run(
            {
                "task_kind": task_kind,
                "request_id": request_id,
                "payload_hex": payload.hex(),
                "run_root": str(run_root),
            }
        )
    except MiniLevError as exc:
        raise FormalFlowError(f"formal flow execution failed: {exc}") from exc
    valid, reason = verify_flow_receipt(
        receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise FormalFlowError(f"formal flow receipt failed verification: {reason}")
    record_text = receipt["final_context"].get("formal_record_json")
    if not isinstance(record_text, str):
        raise FormalFlowError("formal flow produced no decision record")
    record = parse_json_object(record_text.encode("utf-8"))
    decision = _decision_from_record(record)
    expected_terminal = {
        Disposition.ELIGIBLE: "ELIGIBLE",
        Disposition.BLOCKED: "BLOCKED",
        Disposition.PARKED: "PARKED",
    }.get(decision.disposition)
    if expected_terminal != receipt["terminal"]:
        raise FormalFlowError("formal flow terminal differs from decision record")

    receipt_path = run_root / FORMAL_FLOW_RECEIPT
    temporary_path = receipt_path.with_name(receipt_path.name + ".tmp")
    try:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_bytes(canonical_json(receipt) + b"\n")
        temporary_path.replace(receipt_path)
    except OSError as exc:
        raise FormalFlowError(f"formal flow receipt persistence failed: {exc}") from exc
    return decision
