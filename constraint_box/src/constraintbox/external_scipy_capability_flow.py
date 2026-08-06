"""Fixed Mini-Lev flow for the external SciPy ``linalg.expm`` profile."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
from pathlib import Path
from typing import Any, Iterator

from . import external_bounded_numerics_flow_core as _core
from .external_bounded_numerics import BoundedNumericsBinding
from .external_scipy_capability import (
    SCIPY_EXPM_PROFILE,
    run_scipy_expm_capability,
    run_scipy_expm_replay_severance_rehearsal,
)
from .mini_levos import HookKind, HookResult


FLOW_RESULT_SCHEMA = "constraintbox.external-scipy-capability-flow-result.v1"
CAPABILITY_RECEIPT_NAME = "scipy_expm_capability_receipt.json"
FLOW_RECEIPT_NAME = "scipy_expm_flow_receipt.json"
FLOW_LEDGER_NAME = "scipy_expm_flow_events.jsonl"
_FLOW_SOURCE_PATH = Path(__file__).resolve()
_FLOW_CORE_SOURCE_PATH = Path(_core.__file__).resolve()
_FLOW_CORE_SOURCE_SHA256 = hashlib.sha256(_FLOW_CORE_SOURCE_PATH.read_bytes()).hexdigest()
_PINNED_PROFILE = SCIPY_EXPM_PROFILE
_PINNED_RUNNER = run_scipy_expm_capability
_PINNED_REHEARSAL_RUNNER = run_scipy_expm_replay_severance_rehearsal
_PINNED_TOOL_OBSERVATION = _core.tool_observation
_PINNED_GATE_OBSERVATION = _core.gate_observation
_PINNED_RUN_PROFILE_FLOW = _core.run_profile_flow
_REPLAY_SEVERANCE_REHEARSAL_ACTIVE: ContextVar[bool] = ContextVar(
    "constraintbox_scipy_replay_severance_rehearsal_active",
    default=False,
)


def _verify_live_dependencies() -> None:
    if (
        SCIPY_EXPM_PROFILE is not _PINNED_PROFILE
        or run_scipy_expm_capability is not _PINNED_RUNNER
        or run_scipy_expm_replay_severance_rehearsal is not _PINNED_REHEARSAL_RUNNER
        or _core.tool_observation is not _PINNED_TOOL_OBSERVATION
        or _core.gate_observation is not _PINNED_GATE_OBSERVATION
        or _core.run_profile_flow is not _PINNED_RUN_PROFILE_FLOW
        or hashlib.sha256(_FLOW_CORE_SOURCE_PATH.read_bytes()).hexdigest()
        != _FLOW_CORE_SOURCE_SHA256
    ):
        raise _core.ExternalBoundedNumericsFlowError("SciPy flow dependency binding drift")


@contextmanager
def controller_replay_severance_rehearsal_scope() -> Iterator[None]:
    """Activate the one source-owned replay-severance rehearsal for this call.

    This is a process-local test-instrument scope, not an environment variable
    or user/LLM input.  The public engine-test route never enters it.  Its
    caller is required to retain a separate rehearsal receipt that identifies
    the deliberate replay-only intervention.
    """

    _verify_live_dependencies()
    if _REPLAY_SEVERANCE_REHEARSAL_ACTIVE.get():
        raise _core.ExternalBoundedNumericsFlowError(
            "SciPy replay-severance rehearsal scope cannot be nested"
        )
    token = _REPLAY_SEVERANCE_REHEARSAL_ACTIVE.set(True)
    try:
        yield
    finally:
        _REPLAY_SEVERANCE_REHEARSAL_ACTIVE.reset(token)


def _selected_scipy_runner() -> Any:
    if _REPLAY_SEVERANCE_REHEARSAL_ACTIVE.get():
        return _PINNED_REHEARSAL_RUNNER
    return _PINNED_RUNNER


def _scipy_capability_tool(context: dict[str, Any]) -> HookResult:
    _verify_live_dependencies()
    return _PINNED_TOOL_OBSERVATION(
        context,
        profile=_PINNED_PROFILE,
        runner=_selected_scipy_runner(),
        expected_node_id="scipy-expm-capability-tool",
        expected_hook_id="scipy-expm-capability-tool",
    )


def _scipy_capability_gate(context: dict[str, Any]) -> HookResult:
    _verify_live_dependencies()
    return _PINNED_GATE_OBSERVATION(
        context,
        profile=_PINNED_PROFILE,
        expected_node_id="scipy-expm-capability-gate",
        expected_hook_id="scipy-expm-capability-gate",
    )


def run_scipy_expm_capability_flow(
    *,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    """Run the two-node, controller-owned SciPy capability flow."""

    _verify_live_dependencies()
    return _PINNED_RUN_PROFILE_FLOW(
        profile=_PINNED_PROFILE,
        flow_id="constraintbox.scipy-expm-capability-flow.v1",
        tool_node="scipy-expm-capability-tool",
        gate_node="scipy-expm-capability-gate",
        tool_hook="scipy-expm-capability-tool",
        gate_hook="scipy-expm-capability-gate",
        tool_handler=_scipy_capability_tool,
        gate_handler=_scipy_capability_gate,
        flow_source_path=_FLOW_SOURCE_PATH,
        flow_result_schema=FLOW_RESULT_SCHEMA,
        capability_receipt_name=CAPABILITY_RECEIPT_NAME,
        flow_receipt_name=FLOW_RECEIPT_NAME,
        flow_ledger_name=FLOW_LEDGER_NAME,
        run_prefix="scipy",
        request_id=request_id,
        run_root=run_root,
    )
