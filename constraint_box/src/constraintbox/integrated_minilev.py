"""Controller-owned Mini-LevOS lease workload used by ConstraintBox itself.

The integrated core workload has no model-selected hooks or lease parameters.
This module fixes a single hook which can pass only when the controller has
already derived a binding from the external-suite and SMT receipts.  It runs a
positive lease lifecycle and a deliberately expired control lifecycle through
the same real persistence and Mini-Lev runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .execution_lease import ClockSample, ExecutionLeaseStore
from .intake import canonical_json
from .mini_levos import (
    CONTROLLER_METADATA_KEY,
    ExecutionLeaseGuard,
    ExecutionLeaseRequirement,
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


_HEX = re.compile(r"[0-9a-f]{64}")
_CLOCK_ID = "constraintbox-integrated-fixed-clock-v1"
_FLOW_ID = "constraintbox-integrated-receipt-lease-v1"
_NODE_ID = "receipt-bound-gate"
_HOOK_ID = "receipt-binding-hook"
_OWNER_ID = "constraintbox-integrated-controller"


class IntegratedMiniLevError(ValueError):
    """The fixed internal Mini-Lev lease workload could not execute."""


class _FixedLeaseClock:
    """A bounded controller clock for deterministic lease boundary controls."""

    def __init__(self, ticks: tuple[int, ...]):
        self._ticks = iter(ticks)

    def sample(self) -> ClockSample:
        try:
            tick = next(self._ticks)
        except StopIteration as exc:
            raise IntegratedMiniLevError("lease clock exhausted") from exc
        return ClockSample(_CLOCK_ID, tick)


def _binding_sha256(suite_receipt_sha256: str, smt_crosscheck_sha256: str) -> str:
    return hashlib.sha256(
        canonical_json(
            {
                "smt_crosscheck_sha256": smt_crosscheck_sha256,
                "suite_receipt_sha256": suite_receipt_sha256,
            }
        )
    ).hexdigest()


def _receipt_binding_hook(context: dict[str, object]) -> HookResult:
    """Accept only the fixed controller-derived two-receipt binding.

    This hook does not select a next stage or decide release.  Mini-LevOS owns
    the signal/transition authority and the lease guard owns acquire, verify,
    and release.  The function merely recomputes the bounded receipt binding
    handed to it by the fixed controller.
    """

    expected_keys = {
        CONTROLLER_METADATA_KEY,
        "receipt_binding_sha256",
        "smt_crosscheck_sha256",
        "suite_receipt_sha256",
    }
    if set(context) != expected_keys:
        return HookResult(
            HookSignal.BLOCKED,
            {"reason": "receipt_binding_context_keys_mismatch"},
        )
    suite = context.get("suite_receipt_sha256")
    smt = context.get("smt_crosscheck_sha256")
    binding = context.get("receipt_binding_sha256")
    if (
        not isinstance(suite, str)
        or not isinstance(smt, str)
        or not isinstance(binding, str)
        or _HEX.fullmatch(suite) is None
        or _HEX.fullmatch(smt) is None
        or _HEX.fullmatch(binding) is None
    ):
        return HookResult(
            HookSignal.BLOCKED,
            {"reason": "receipt_binding_context_invalid"},
        )
    if binding != _binding_sha256(suite, smt):
        return HookResult(
            HookSignal.BLOCKED,
            {"reason": "receipt_binding_digest_mismatch"},
        )
    return HookResult(
        HookSignal.PASS,
        {
            "receipt_binding_sha256": binding,
            "smt_crosscheck_sha256": smt,
            "suite_receipt_sha256": suite,
        },
    )


def _registration() -> HookRegistration:
    source = Path(__file__).resolve()
    return HookRegistration(
        hook_id=_HOOK_ID,
        kind=HookKind.GATE,
        handler=_receipt_binding_hook,
        source_path=source,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        code_sha256=handler_code_sha256(_receipt_binding_hook),
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED),
    )


def _policy(requirement: ExecutionLeaseRequirement) -> FlowPolicy:
    return FlowPolicy(
        flow_id=_FLOW_ID,
        entry_node=_NODE_ID,
        nodes=(FlowNode(_NODE_ID, _HOOK_ID),),
        transitions=(
            FlowTransition(_NODE_ID, HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition(_NODE_ID, HookSignal.HOLD, "HOLD"),
            FlowTransition(_NODE_ID, HookSignal.PASS, "RELEASED"),
        ),
        terminal_nodes=("BLOCKED", "HOLD", "RELEASED"),
        required_nodes=(_NODE_ID,),
        max_steps=1,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=4_096,
        max_event_bytes=65_536,
        max_receipt_bytes=262_144,
        claim_ceiling=(
            "one local controller-owned Mini-LevOS receipt-binding lease "
            "lifecycle and one expiry control; not a distributed lease, "
            "agent identity, user authorization, release, or promotion claim"
        ),
        execution_lease=requirement,
    )


def _write_new_json(path: Path, body: dict[str, Any]) -> None:
    if path.exists():
        raise IntegratedMiniLevError(f"refusing to overwrite artifact: {path}")
    path.write_bytes(canonical_json(body) + b"\n")


def _artifact(path: Path, root: Path) -> dict[str, str]:
    if not path.is_file():
        raise IntegratedMiniLevError(f"required Mini-Lev artifact is missing: {path}")
    return {
        "path": str(path.relative_to(root)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _run_lease_flow(
    *,
    root: Path,
    run_id: str,
    initial_context: dict[str, object],
    clock_ticks: tuple[int, ...],
) -> tuple[dict[str, Any], dict[str, str]]:
    root.mkdir(parents=True, exist_ok=False)
    store_path = root / "execution_lease_store.json"
    store = ExecutionLeaseStore(store_path)
    requirement = ExecutionLeaseRequirement(
        node_id=_NODE_ID,
        hook_id=_HOOK_ID,
        owner_id=_OWNER_ID,
        slot_sha256=store.slot_sha256,
        ttl_ns=10,
        clock_source="constraintbox-fixed-control-clock-v1",
        clock_id=_CLOCK_ID,
    )
    runtime = MiniLevRuntime(
        _policy(requirement),
        (_registration(),),
        run_id=run_id,
        ledger_path=root / "mini_lev_ledger.jsonl",
        execution_lease_guard=ExecutionLeaseGuard(
            requirement,
            store,
            clock_sample=_FixedLeaseClock(clock_ticks).sample,
        ),
    )
    receipt = runtime.run(initial_context)
    receipt_path = root / "mini_lev_flow_receipt.json"
    _write_new_json(receipt_path, receipt)
    valid, reason = verify_flow_receipt(
        receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise IntegratedMiniLevError(f"Mini-Lev receipt verification failed: {reason}")
    return receipt, {
        "flow_receipt": str(receipt_path),
        "ledger": str(runtime.ledger_path),
        "ledger_head": str(runtime.ledger_path.with_name("mini_lev_ledger.jsonl.head")),
        "lease_store": str(store_path),
    }


def _lease_audit(receipt: dict[str, Any]) -> dict[str, Any]:
    ledger = receipt.get("ledger")
    if not isinstance(ledger, dict) or not isinstance(ledger.get("path"), str):
        raise IntegratedMiniLevError("Mini-Lev receipt ledger binding is invalid")
    lines = Path(ledger["path"]).read_text(encoding="utf-8").splitlines()
    if len(lines) != 1:
        raise IntegratedMiniLevError("Mini-Lev lease flow must retain one event")
    try:
        event = json.loads(lines[0])
        record = event["record"]
        audit = record["execution_lease"]
    except (KeyError, TypeError, ValueError) as exc:
        raise IntegratedMiniLevError("Mini-Lev lease audit is malformed") from exc
    if not isinstance(audit, dict):
        raise IntegratedMiniLevError("Mini-Lev lease audit is not an object")
    return audit


def run_integrated_receipt_lease(
    *,
    run_root: Path,
    request_id: str,
    suite_receipt_sha256: str,
    smt_crosscheck_sha256: str,
) -> dict[str, Any]:
    """Run the fixed lease gate plus a real expiry control.

    The positive flow must release before its positive terminal.  The expiry
    control uses the same hook and persistence store interface but advances
    the controller clock to the exact TTL boundary after the callback; it must
    therefore be retained as HOLD rather than released.
    """

    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise IntegratedMiniLevError("run_root must be an absolute pathlib.Path")
    if not isinstance(request_id, str) or not request_id:
        raise IntegratedMiniLevError("request_id must be one non-empty string")
    if _HEX.fullmatch(suite_receipt_sha256) is None or _HEX.fullmatch(
        smt_crosscheck_sha256
    ) is None:
        raise IntegratedMiniLevError("receipt digests must be lowercase SHA-256")
    if run_root.exists():
        raise IntegratedMiniLevError("Mini-Lev stage root must be new")

    binding = _binding_sha256(suite_receipt_sha256, smt_crosscheck_sha256)
    context: dict[str, object] = {
        "receipt_binding_sha256": binding,
        "smt_crosscheck_sha256": smt_crosscheck_sha256,
        "suite_receipt_sha256": suite_receipt_sha256,
    }
    try:
        positive, positive_paths = _run_lease_flow(
            root=run_root / "positive",
            run_id=f"{request_id}-receipt-lease",
            initial_context=context,
            clock_ticks=(0, 1, 2, 3),
        )
        expiry, expiry_paths = _run_lease_flow(
            root=run_root / "expiry_control",
            run_id=f"{request_id}-receipt-lease-expiry",
            initial_context=context,
            clock_ticks=(0, 1, 10, 11),
        )
        positive_audit = _lease_audit(positive)
        expiry_audit = _lease_audit(expiry)
    except (MiniLevError, OSError, ValueError) as exc:
        return {
            "disposition": "HOLD",
            "reason": "integrated_minilev_lease_execution_error",
            "exception_type": type(exc).__name__,
            "error": str(exc),
        }

    positive_ok = (
        positive.get("terminal") == "RELEASED"
        and positive.get("execution_lease", {}).get(
            "all_protected_events_released"
        )
        is True
        and positive_audit.get("handler_started") is True
        and positive_audit.get("handler_completed") is True
        and positive_audit.get("failure_stage") is None
        and positive_audit.get("release_status") == "RELEASED"
    )
    expiry_ok = (
        expiry.get("terminal") == "HOLD"
        and expiry.get("execution_lease", {}).get(
            "all_protected_events_released"
        )
        is False
        and expiry_audit.get("handler_started") is True
        and expiry_audit.get("handler_completed") is True
        and expiry_audit.get("failure_stage") == "post_hook_verify"
        and expiry_audit.get("release_status") == "RELEASE_FAILED"
    )
    return {
        "disposition": "ELIGIBLE" if positive_ok and expiry_ok else "BLOCKED",
        "reason": "receipt_bound_lease_released_and_expiry_control_held"
        if positive_ok and expiry_ok
        else "receipt_bound_lease_or_expiry_control_failed",
        "receipt_binding_sha256": binding,
        "positive": {
            "terminal": positive.get("terminal"),
            "execution_lease": positive.get("execution_lease"),
            "audit": positive_audit,
            "artifacts": {
                name: _artifact(Path(path), run_root)
                for name, path in positive_paths.items()
            },
        },
        "expiry_control": {
            "terminal": expiry.get("terminal"),
            "execution_lease": expiry.get("execution_lease"),
            "audit": expiry_audit,
            "artifacts": {
                name: _artifact(Path(path), run_root)
                for name, path in expiry_paths.items()
            },
        },
        "controller_selected": True,
        "llm_decision_authority": False,
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "one local fixed Mini-LevOS hook and execution-lease lifecycle, "
            "including an exact expiry control; not distributed coordination, "
            "agent authorization, user authorization, or release permission"
        ),
    }
