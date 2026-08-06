"""Fixed Mini-Lev flow for the external Diffrax Tsit5 profile."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from . import external_bounded_numerics_flow_core as _core
from .external_diffrax_capability import (
    DIFFRAX_TSIT5_PROFILE,
    run_diffrax_tsit5_capability,
)
from .mini_levos import HookResult


FLOW_RESULT_SCHEMA = "constraintbox.external-diffrax-capability-flow-result.v1"
CAPABILITY_RECEIPT_NAME = "diffrax_tsit5_capability_receipt.json"
FLOW_RECEIPT_NAME = "diffrax_tsit5_flow_receipt.json"
FLOW_LEDGER_NAME = "diffrax_tsit5_flow_events.jsonl"
_FLOW_SOURCE_PATH = Path(__file__).resolve()
_FLOW_CORE_SOURCE_PATH = Path(_core.__file__).resolve()
_FLOW_CORE_SOURCE_SHA256 = hashlib.sha256(_FLOW_CORE_SOURCE_PATH.read_bytes()).hexdigest()
_PINNED_PROFILE = DIFFRAX_TSIT5_PROFILE
_PINNED_RUNNER = run_diffrax_tsit5_capability
_PINNED_TOOL_OBSERVATION = _core.tool_observation
_PINNED_GATE_OBSERVATION = _core.gate_observation
_PINNED_RUN_PROFILE_FLOW = _core.run_profile_flow


def _verify_live_dependencies() -> None:
    if (
        DIFFRAX_TSIT5_PROFILE is not _PINNED_PROFILE
        or run_diffrax_tsit5_capability is not _PINNED_RUNNER
        or _core.tool_observation is not _PINNED_TOOL_OBSERVATION
        or _core.gate_observation is not _PINNED_GATE_OBSERVATION
        or _core.run_profile_flow is not _PINNED_RUN_PROFILE_FLOW
        or hashlib.sha256(_FLOW_CORE_SOURCE_PATH.read_bytes()).hexdigest()
        != _FLOW_CORE_SOURCE_SHA256
    ):
        raise _core.ExternalBoundedNumericsFlowError("Diffrax flow dependency binding drift")


def _diffrax_capability_tool(context: dict[str, Any]) -> HookResult:
    _verify_live_dependencies()
    return _PINNED_TOOL_OBSERVATION(
        context,
        profile=_PINNED_PROFILE,
        runner=_PINNED_RUNNER,
        expected_node_id="diffrax-tsit5-capability-tool",
        expected_hook_id="diffrax-tsit5-capability-tool",
    )


def _diffrax_capability_gate(context: dict[str, Any]) -> HookResult:
    _verify_live_dependencies()
    return _PINNED_GATE_OBSERVATION(
        context,
        profile=_PINNED_PROFILE,
        expected_node_id="diffrax-tsit5-capability-gate",
        expected_hook_id="diffrax-tsit5-capability-gate",
    )


def run_diffrax_tsit5_capability_flow(
    *,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    """Run the two-node, controller-owned Diffrax capability flow."""

    _verify_live_dependencies()
    return _PINNED_RUN_PROFILE_FLOW(
        profile=_PINNED_PROFILE,
        flow_id="constraintbox.diffrax-tsit5-capability-flow.v1",
        tool_node="diffrax-tsit5-capability-tool",
        gate_node="diffrax-tsit5-capability-gate",
        tool_hook="diffrax-tsit5-capability-tool",
        gate_hook="diffrax-tsit5-capability-gate",
        tool_handler=_diffrax_capability_tool,
        gate_handler=_diffrax_capability_gate,
        flow_source_path=_FLOW_SOURCE_PATH,
        flow_result_schema=FLOW_RESULT_SCHEMA,
        capability_receipt_name=CAPABILITY_RECEIPT_NAME,
        flow_receipt_name=FLOW_RECEIPT_NAME,
        flow_ledger_name=FLOW_LEDGER_NAME,
        run_prefix="diffrax",
        request_id=request_id,
        run_root=run_root,
    )
