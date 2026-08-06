"""Fixed Mini-LevOS flow for one untrusted proposal and bounded repair.

This module is deliberately a small adapter around :mod:`mini_levos`, not a
second workflow runtime.  A caller registers three controller-owned callbacks
for the lifetime of one process-local run.  The registered Mini-Lev hooks are
module-level functions whose source and code identities are checked by the
kernel on every step.  The callbacks can only return typed observations and a
sealed artifact digest; they cannot provide a next node, a terminal, a policy,
or a release flag.

The registry is not a hostile-process sandbox.  Code already running with the
same Python privileges is outside ConstraintBox's containment ceiling.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .execution_lease import ExecutionLeaseStore
from .intake import IntakeError, canonical_json, parse_json_object
from .mini_lev_topology import FixedMiniLevTopology, MiniLevTopologyError
from .mini_levos import (
    CONTROLLER_METADATA_KEY,
    ControllerMonotonicClock,
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


FLOW_ID = "constraintbox.bounded-proposal-retry-claim.v1"
FLOW_RECEIPT_NAME = "proposal_flow_receipt.json"
FLOW_LEDGER_NAME = "proposal_flow_ledger.jsonl"
TOPOLOGY_WITNESS_NAME = "proposal_flow_topology_witness.json"
EXECUTION_LEASE_DIRECTORY_NAME = "execution-leases"
PROPOSAL_OBSERVATION_LEASE_NAME = "proposal-observation.v1.json"
PROPOSAL_LEASE_OWNER_ID = "constraintbox.proposal-controller"
PROPOSAL_LEASE_CLOCK_SOURCE = "controller-monotonic-ns-root-domain-v1"
_PROPOSAL_LEASE_CLOCK_DOMAIN_SCHEMA = "constraintbox.proposal-lease-clock-domain.v1"
# The public provider bound is 180 seconds.  A single proposal observation has
# a 240-second lease ceiling so a valid bounded provider call is not guaranteed
# to expire before the post-hook verification.
PROPOSAL_LEASE_TTL_NS = 240_000_000_000
_SHA256 = hashlib.sha256
_HEX_SHA256 = frozenset("0123456789abcdef")
_CLAIM_CEILING = (
    "one controller-owned two-attempt untrusted proposal and ClaimGate check; "
    "no promotion or hostile-process containment"
)
_TOPOLOGY_NODE_ID = "topology-preflight"
_TOPOLOGY_HOOK_ID = "bounded-topology-preflight"
_TOPOLOGY_WITNESS_UPDATE_KEY = "topology_witness_sha256"
_TOPOLOGY_WITNESS_SCHEMA = "constraintbox.proposal-topology-witness.v1"
_TOPOLOGY_REQUIRED_REACHABILITY = tuple(
    sorted(
        (
            ("proposal-gate", "claim-gate"),
            ("proposal-observation", "claim-gate"),
            ("proposal-observation", "proposal-gate"),
            ("topology-preflight", "claim-gate"),
            ("topology-preflight", "proposal-gate"),
            ("topology-preflight", "proposal-observation"),
        )
    )
)
_TOPOLOGY = FixedMiniLevTopology(
    required_reachability=_TOPOLOGY_REQUIRED_REACHABILITY,
    max_nodes=4,
    max_edges=3,
)


class ProposalMiniLevFlowError(RuntimeError):
    """The fixed proposal flow could not be built, run, or verified."""


class ProposalSignal(str, Enum):
    OBSERVED = "OBSERVED"
    PARKED = "PARKED"


class ProposalGateSignal(str, Enum):
    PASS = "PASS"
    RETRY = "RETRY"
    BLOCKED = "BLOCKED"
    PARKED = "PARKED"


class ClaimGateSignal(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    PARKED = "PARKED"


@dataclass(frozen=True)
class ProposalFlowContext:
    """Controller-built context visible to one callback invocation."""

    run_id: str
    attempt_number: int
    flow_policy_sha256: str
    binding_artifact_sha256: str
    caller_source_sha256: str
    controller_source_sha256: str


@dataclass(frozen=True)
class ProposalCallbackResult:
    signal: ProposalSignal
    sealed_artifact_sha256: str


@dataclass(frozen=True)
class ProposalGateCallbackResult:
    signal: ProposalGateSignal
    sealed_artifact_sha256: str


@dataclass(frozen=True)
class ClaimGateCallbackResult:
    signal: ClaimGateSignal
    sealed_artifact_sha256: str


ProposalCallback = Callable[[ProposalFlowContext], ProposalCallbackResult]
ProposalGateCallback = Callable[[ProposalFlowContext], ProposalGateCallbackResult]
ClaimGateCallback = Callable[[ProposalFlowContext], ClaimGateCallbackResult]


@dataclass(frozen=True)
class ProposalMiniLevCallbacks:
    """The three controller-owned operations behind the fixed flow."""

    proposal: ProposalCallback
    proposal_gate: ProposalGateCallback
    claim_gate: ClaimGateCallback


@dataclass(frozen=True)
class ProposalMiniLevFlowResult:
    run_id: str
    terminal: str
    flow_policy_sha256: str
    flow_receipt_sha256: str
    binding_artifact_sha256: str
    topology_witness_sha256: str | None
    flow_root: Path
    flow_receipt_path: Path
    flow_ledger_path: Path
    flow_ledger_head_path: Path
    topology_witness_path: Path
    controller_state_root: Path
    execution_lease_state_path: Path
    execution_lease_slot_sha256: str
    flow_receipt: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "constraintbox.proposal-minilev-flow-result.v1",
            "run_id": self.run_id,
            "terminal": self.terminal,
            "flow_policy_sha256": self.flow_policy_sha256,
            "flow_receipt_sha256": self.flow_receipt_sha256,
            "binding_artifact_sha256": self.binding_artifact_sha256,
            "topology_witness_sha256": self.topology_witness_sha256,
            "flow_root": str(self.flow_root),
            "flow_receipt": str(self.flow_receipt_path),
            "flow_ledger": str(self.flow_ledger_path),
            "flow_ledger_head": str(self.flow_ledger_head_path),
            "topology_witness": str(self.topology_witness_path),
            "controller_state_root": str(self.controller_state_root),
            "execution_lease_state": str(self.execution_lease_state_path),
            "execution_lease_slot_sha256": self.execution_lease_slot_sha256,
            "claim_ceiling": self.flow_receipt["claim_ceiling"],
            "promotion_allowed": False,
        }


@dataclass
class _ActiveRun:
    context: ProposalFlowContext
    callbacks: ProposalMiniLevCallbacks
    lock: threading.RLock
    caller_source_path: Path
    controller_source_path: Path
    policy: FlowPolicy
    flow_root: Path
    topology_witness_path: Path
    topology_witness_sha256: str | None = None
    topology_preflight_invoked: bool = False
    proposal_attempt: int = 0
    gate_attempt: int = 0
    claim_invoked: bool = False


_ACTIVE_RUNS: dict[str, _ActiveRun] = {}
_ACTIVE_RUNS_LOCK = threading.RLock()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in _HEX_SHA256 for character in value)
    )


def _require_sha256(value: object, where: str) -> str:
    if not _is_sha256(value):
        raise ProposalMiniLevFlowError(f"{where} must be a lowercase SHA-256")
    return value


def _source_sha256(path: Path) -> str:
    try:
        return _SHA256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ProposalMiniLevFlowError(f"flow source is unavailable: {path}") from exc


def _verified_source_path(path: object, where: str) -> tuple[Path, str]:
    if not isinstance(path, Path) or not path.is_absolute():
        raise ProposalMiniLevFlowError(f"{where} must be an absolute pathlib.Path")
    resolved = path.resolve()
    if not resolved.is_file():
        raise ProposalMiniLevFlowError(f"{where} is not a regular source file")
    return resolved, _source_sha256(resolved)


def _controller_state_root(
    root: object,
    *,
    flow_root: Path,
) -> tuple[Path, Path]:
    """Prepare the controller-owned stable slot root outside one flow receipt.

    The state root is an explicit controller input, never a model field.  A
    flow root is intentionally fresh per run; placing a lease beside it would
    remove the cross-run ownership check and turn the lease into theatre.
    """

    if not isinstance(root, Path) or not root.is_absolute():
        raise ProposalMiniLevFlowError(
            "controller_state_root must be an absolute pathlib.Path"
        )
    original = root.expanduser()
    if original.is_symlink():
        raise ProposalMiniLevFlowError("controller_state_root must not be a symlink")
    try:
        original.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(original, 0o700)
    except OSError as exc:
        raise ProposalMiniLevFlowError(
            f"controller_state_root creation failed: {exc}"
        ) from exc
    resolved = original.resolve()
    if not resolved.is_dir():
        raise ProposalMiniLevFlowError("controller_state_root is not a directory")
    if resolved == flow_root or resolved.is_relative_to(flow_root):
        raise ProposalMiniLevFlowError(
            "controller_state_root must be outside the per-run flow root"
        )
    lease_directory = resolved / EXECUTION_LEASE_DIRECTORY_NAME
    if lease_directory.is_symlink():
        raise ProposalMiniLevFlowError("execution lease directory must not be a symlink")
    try:
        lease_directory.mkdir(exist_ok=True, mode=0o700)
        os.chmod(lease_directory, 0o700)
    except OSError as exc:
        raise ProposalMiniLevFlowError(
            f"execution lease directory creation failed: {exc}"
        ) from exc
    return resolved, lease_directory / PROPOSAL_OBSERVATION_LEASE_NAME


def _controller_lease_clock_id(
    controller_state_root: Path,
    execution_lease_state_path: Path,
) -> str:
    """Derive one local monotonic clock domain from the trusted state root.

    A per-flow clock identity would make an expired active slot permanently
    unrecoverable.  This root-bound identity lets a later flow in the same
    controller/boot domain reclaim an expired slot.  A reboot, root move, or
    different host/domain instead remains a fail-closed conflict: this v1
    lease deliberately has no cross-boot recovery protocol.
    """

    try:
        root = controller_state_root.resolve(strict=True)
        state_path = execution_lease_state_path.resolve(strict=False)
        root_stat = root.stat()
    except OSError as exc:
        raise ProposalMiniLevFlowError(
            f"execution lease clock-domain identity is unavailable: {exc}"
        ) from exc
    if not root.is_dir():
        raise ProposalMiniLevFlowError(
            "execution lease clock-domain root is not a directory"
        )
    expected_state_path = (
        root / EXECUTION_LEASE_DIRECTORY_NAME / PROPOSAL_OBSERVATION_LEASE_NAME
    )
    if state_path != expected_state_path:
        raise ProposalMiniLevFlowError(
            "execution lease clock-domain state path is not controller-selected"
        )
    material = {
        "schema": _PROPOSAL_LEASE_CLOCK_DOMAIN_SCHEMA,
        "controller_state_root": str(root),
        "root_device": root_stat.st_dev,
        "root_inode": root_stat.st_ino,
        "state_relative_path": str(state_path.relative_to(root)),
    }
    return "cb-proposal-root-" + _SHA256(canonical_json(material)).hexdigest()[:32]


def _canonical_dict(value: object, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProposalMiniLevFlowError(f"{where} must be a JSON object")
    try:
        return parse_json_object(canonical_json(value))
    except (IntakeError, TypeError, ValueError) as exc:
        raise ProposalMiniLevFlowError(
            f"{where} is not finite canonical JSON: {exc}"
        ) from exc


def _canonical_sha256(value: object, where: str) -> str:
    return _SHA256(canonical_json(_canonical_dict(value, where))).hexdigest()


def _verify_callback_sources(state: _ActiveRun) -> None:
    if _source_sha256(state.caller_source_path) != state.context.caller_source_sha256:
        raise ProposalMiniLevFlowError("proposal caller source digest drift")
    if (
        _source_sha256(state.controller_source_path)
        != state.context.controller_source_sha256
    ):
        raise ProposalMiniLevFlowError("proposal controller source digest drift")


def _source_registration(
    *,
    hook_id: str,
    kind: HookKind,
    handler,
    allowed_signals: tuple[HookSignal, ...],
    allowed_update_keys: tuple[str, ...] = (),
) -> HookRegistration:
    source_path = Path(__file__).resolve()
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=source_path,
        source_sha256=_source_sha256(source_path),
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=16_384,
    )


def _active_run(context: dict[str, Any]) -> _ActiveRun:
    metadata = context.get(CONTROLLER_METADATA_KEY)
    if not isinstance(metadata, dict):
        raise ProposalMiniLevFlowError("Mini-Lev controller metadata is missing")
    run_id = metadata.get("run_id")
    policy_sha256 = metadata.get("policy_sha256")
    if not isinstance(run_id, str) or not isinstance(policy_sha256, str):
        raise ProposalMiniLevFlowError("Mini-Lev controller metadata is malformed")
    with _ACTIVE_RUNS_LOCK:
        state = _ACTIVE_RUNS.get(run_id)
    if state is None:
        raise ProposalMiniLevFlowError("no active controller state for this flow")
    if state.context.flow_policy_sha256 != policy_sha256:
        raise ProposalMiniLevFlowError("flow policy binding drift")
    _verify_callback_sources(state)
    return state


def _proposal_result(value: object) -> ProposalCallbackResult:
    if type(value) is not ProposalCallbackResult:
        raise ProposalMiniLevFlowError("proposal callback returned the wrong type")
    if not isinstance(value.signal, ProposalSignal):
        raise ProposalMiniLevFlowError("proposal callback signal is invalid")
    _require_sha256(value.sealed_artifact_sha256, "proposal artifact digest")
    return value


def _proposal_gate_result(value: object) -> ProposalGateCallbackResult:
    if type(value) is not ProposalGateCallbackResult:
        raise ProposalMiniLevFlowError("proposal gate callback returned the wrong type")
    if not isinstance(value.signal, ProposalGateSignal):
        raise ProposalMiniLevFlowError("proposal gate callback signal is invalid")
    _require_sha256(value.sealed_artifact_sha256, "proposal gate artifact digest")
    return value


def _claim_gate_result(value: object) -> ClaimGateCallbackResult:
    if type(value) is not ClaimGateCallbackResult:
        raise ProposalMiniLevFlowError("ClaimGate callback returned the wrong type")
    if not isinstance(value.signal, ClaimGateSignal):
        raise ProposalMiniLevFlowError("ClaimGate callback signal is invalid")
    _require_sha256(value.sealed_artifact_sha256, "ClaimGate artifact digest")
    return value


def _topology_preflight_hook(context: dict[str, Any]) -> HookResult:
    """Witness the fixed non-RETRY node projection before provider callbacks.

    Terminal edges and bounded retry legality remain Mini-Lev receipt
    obligations; this preflight checks only the internal node-to-node
    projection with Rustworkx and an independent reference implementation.
    """

    state = _active_run(context)
    with state.lock:
        if state.topology_preflight_invoked:
            raise ProposalMiniLevFlowError("topology preflight ran more than once")
        state.topology_preflight_invoked = True
        try:
            preflight = _TOPOLOGY.evaluate(state.policy, state.flow_root)
        except MiniLevTopologyError as exc:
            raise ProposalMiniLevFlowError(str(exc)) from exc
        witness = _TOPOLOGY.witness_material(
            witness_schema=_TOPOLOGY_WITNESS_SCHEMA,
            run_id=state.context.run_id,
            flow_id=FLOW_ID,
            flow_policy_sha256=state.context.flow_policy_sha256,
            binding_artifact_sha256=state.context.binding_artifact_sha256,
            claim_ceiling=_CLAIM_CEILING,
            preflight=preflight,
        )
        witness_sha256 = _canonical_sha256(witness, "topology witness")
        _persist_exclusive(
            state.topology_witness_path,
            witness,
            label="topology witness",
        )
        state.topology_witness_sha256 = witness_sha256
        return HookResult(
            preflight.signal,
            {_TOPOLOGY_WITNESS_UPDATE_KEY: witness_sha256},
            {_TOPOLOGY_WITNESS_UPDATE_KEY: witness_sha256},
        )


def _proposal_hook(context: dict[str, Any]) -> HookResult:
    """Static Mini-Lev hook: obtain one untrusted provider observation."""

    state = _active_run(context)
    with state.lock:
        if state.claim_invoked:
            raise ProposalMiniLevFlowError("proposal hook ran after ClaimGate")
        state.proposal_attempt += 1
        attempt = state.proposal_attempt
        callback_context = ProposalFlowContext(
            run_id=state.context.run_id,
            attempt_number=attempt,
            flow_policy_sha256=state.context.flow_policy_sha256,
            binding_artifact_sha256=state.context.binding_artifact_sha256,
            caller_source_sha256=state.context.caller_source_sha256,
            controller_source_sha256=state.context.controller_source_sha256,
        )
        result = _proposal_result(state.callbacks.proposal(callback_context))
        return HookResult(
            HookSignal(result.signal.value),
            {
                "attempt_number": attempt,
                "sealed_artifact_sha256": result.sealed_artifact_sha256,
            },
        )


def _proposal_gate_hook(context: dict[str, Any]) -> HookResult:
    """Static Mini-Lev hook: controller-only deterministic proposal gate."""

    state = _active_run(context)
    with state.lock:
        attempt = state.proposal_attempt
        if attempt < 1 or state.gate_attempt == attempt or state.claim_invoked:
            raise ProposalMiniLevFlowError("proposal gate invocation order is invalid")
        callback_context = ProposalFlowContext(
            run_id=state.context.run_id,
            attempt_number=attempt,
            flow_policy_sha256=state.context.flow_policy_sha256,
            binding_artifact_sha256=state.context.binding_artifact_sha256,
            caller_source_sha256=state.context.caller_source_sha256,
            controller_source_sha256=state.context.controller_source_sha256,
        )
        result = _proposal_gate_result(
            state.callbacks.proposal_gate(callback_context)
        )
        state.gate_attempt = attempt
        return HookResult(
            HookSignal(result.signal.value),
            {
                "attempt_number": attempt,
                "sealed_artifact_sha256": result.sealed_artifact_sha256,
            },
        )


def _claim_gate_hook(context: dict[str, Any]) -> HookResult:
    """Static Mini-Lev hook: ClaimGate is the only route to RELEASED."""

    state = _active_run(context)
    with state.lock:
        attempt = state.proposal_attempt
        if attempt < 1 or state.gate_attempt != attempt or state.claim_invoked:
            raise ProposalMiniLevFlowError("ClaimGate invocation order is invalid")
        state.claim_invoked = True
        callback_context = ProposalFlowContext(
            run_id=state.context.run_id,
            attempt_number=attempt,
            flow_policy_sha256=state.context.flow_policy_sha256,
            binding_artifact_sha256=state.context.binding_artifact_sha256,
            caller_source_sha256=state.context.caller_source_sha256,
            controller_source_sha256=state.context.controller_source_sha256,
        )
        result = _claim_gate_result(state.callbacks.claim_gate(callback_context))
        return HookResult(
            HookSignal(result.signal.value),
            {
                "attempt_number": attempt,
                "sealed_artifact_sha256": result.sealed_artifact_sha256,
            },
        )


def _build_runtime(
    *,
    run_id: str,
    ledger_path: Path,
    execution_lease_store: ExecutionLeaseStore,
    execution_lease_clock: ControllerMonotonicClock,
    execution_lease_clock_id: str,
) -> MiniLevRuntime:
    topology_preflight = _source_registration(
        hook_id=_TOPOLOGY_HOOK_ID,
        kind=HookKind.GATE,
        handler=_topology_preflight_hook,
        allowed_signals=(
            HookSignal.PASS,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        ),
        allowed_update_keys=(_TOPOLOGY_WITNESS_UPDATE_KEY,),
    )
    proposal = _source_registration(
        hook_id="bounded-proposal-observation",
        kind=HookKind.PROPOSAL,
        handler=_proposal_hook,
        allowed_signals=(HookSignal.OBSERVED, HookSignal.PARKED),
    )
    proposal_gate = _source_registration(
        hook_id="bounded-proposal-gate",
        kind=HookKind.GATE,
        handler=_proposal_gate_hook,
        allowed_signals=(
            HookSignal.PASS,
            HookSignal.RETRY,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        ),
    )
    claim_gate = _source_registration(
        hook_id="bounded-claim-gate",
        kind=HookKind.GATE,
        handler=_claim_gate_hook,
        allowed_signals=(
            HookSignal.PASS,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        ),
    )
    policy = FlowPolicy(
        flow_id=FLOW_ID,
        entry_node=_TOPOLOGY_NODE_ID,
        nodes=(
            FlowNode(_TOPOLOGY_NODE_ID, topology_preflight.hook_id),
            FlowNode("proposal-observation", proposal.hook_id),
            FlowNode("proposal-gate", proposal_gate.hook_id),
            FlowNode("claim-gate", claim_gate.hook_id),
        ),
        transitions=(
            FlowTransition(
                _TOPOLOGY_NODE_ID,
                HookSignal.PASS,
                "proposal-observation",
            ),
            FlowTransition(
                _TOPOLOGY_NODE_ID,
                HookSignal.BLOCKED,
                "BLOCKED",
            ),
            FlowTransition(
                _TOPOLOGY_NODE_ID,
                HookSignal.PARKED,
                "PARKED",
            ),
            FlowTransition(_TOPOLOGY_NODE_ID, HookSignal.HOLD, "HOLD"),
            FlowTransition(
                "proposal-observation", HookSignal.OBSERVED, "proposal-gate"
            ),
            FlowTransition("proposal-observation", HookSignal.PARKED, "PARKED"),
            FlowTransition("proposal-observation", HookSignal.HOLD, "HOLD"),
            FlowTransition("proposal-gate", HookSignal.PASS, "claim-gate"),
            FlowTransition("proposal-gate", HookSignal.RETRY, "proposal-observation"),
            FlowTransition("proposal-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("proposal-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("proposal-gate", HookSignal.HOLD, "HOLD"),
            FlowTransition("claim-gate", HookSignal.PASS, "RELEASED"),
            FlowTransition("claim-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("claim-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("claim-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("RELEASED", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=(
            _TOPOLOGY_NODE_ID,
            "proposal-observation",
            "proposal-gate",
            "claim-gate",
        ),
        max_steps=6,
        max_visits_per_node=2,
        max_retries=1,
        max_context_bytes=8_192,
        max_event_bytes=65_536,
        max_receipt_bytes=524_288,
        claim_ceiling=_CLAIM_CEILING,
        execution_lease=ExecutionLeaseRequirement(
            node_id="proposal-observation",
            hook_id=proposal.hook_id,
            owner_id=PROPOSAL_LEASE_OWNER_ID,
            slot_sha256=execution_lease_store.slot_sha256,
            ttl_ns=PROPOSAL_LEASE_TTL_NS,
            clock_source=PROPOSAL_LEASE_CLOCK_SOURCE,
            clock_id=execution_lease_clock_id,
        ),
    )
    return MiniLevRuntime(
        policy,
        (topology_preflight, proposal, proposal_gate, claim_gate),
        run_id=run_id,
        ledger_path=ledger_path,
        execution_lease_guard=ExecutionLeaseGuard(
            policy.execution_lease,
            execution_lease_store,
            clock_sample=execution_lease_clock.sample,
        ),
    )


def _persist_exclusive(
    path: Path,
    value: dict[str, Any],
    *,
    label: str,
) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ProposalMiniLevFlowError(
            f"{label} persistence failed: {exc}"
        ) from exc


def _read_topology_witness(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"topology witness is unavailable: {exc}"
    try:
        witness = parse_json_object(raw)
    except IntakeError as exc:
        return None, f"topology witness is malformed: {exc}"
    if raw != canonical_json(witness) + b"\n":
        return None, "topology witness is not exclusively canonical"
    return witness, None


def _topology_ledger_records(
    path: Path,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    try:
        rows = path.read_bytes().splitlines()
    except OSError as exc:
        return None, f"proposal flow ledger is unavailable: {exc}"
    records: list[dict[str, Any]] = []
    try:
        for raw in rows:
            row = parse_json_object(raw)
            record = row.get("record")
            if not isinstance(record, dict):
                return None, "proposal flow ledger record is malformed"
            records.append(record)
    except IntakeError as exc:
        return None, f"proposal flow ledger row is malformed: {exc}"
    if not records:
        return None, "proposal flow ledger is empty"
    return records, None


def _verify_topology_witness(
    result: ProposalMiniLevFlowResult,
) -> tuple[bool, str]:
    """Check that the first gate's actual ledger event binds its witness."""

    if not isinstance(result.flow_root, Path) or not isinstance(
        result.topology_witness_path, Path
    ):
        return False, "topology witness path type is invalid"
    expected_path = result.flow_root / TOPOLOGY_WITNESS_NAME
    if result.topology_witness_path.resolve() != expected_path.resolve():
        return False, "topology witness path is outside the flow root"
    records, records_error = _topology_ledger_records(result.flow_ledger_path)
    if records is None:
        return False, records_error or "topology ledger read failed"
    first = records[0]
    if (
        first.get("node_id") != _TOPOLOGY_NODE_ID
        or first.get("hook_id") != _TOPOLOGY_HOOK_ID
        or first.get("node_kind") != HookKind.GATE.value
    ):
        return False, "topology preflight is not the first Mini-Lev event"
    signal = first.get("typed_signal")
    if signal not in {
        HookSignal.PASS.value,
        HookSignal.BLOCKED.value,
        HookSignal.PARKED.value,
        HookSignal.HOLD.value,
    }:
        return False, "topology preflight signal is invalid"
    witness_sha256 = result.topology_witness_sha256
    if witness_sha256 is None:
        if (
            signal == HookSignal.HOLD.value
            and result.terminal == "HOLD"
            and len(records) == 1
        ):
            return True, "topology preflight held before a witness could persist"
        return False, "topology witness is missing"
    if not _is_sha256(witness_sha256):
        return False, "topology witness digest is invalid"
    if signal == HookSignal.HOLD.value:
        return False, "topology witness exists despite a held preflight"
    witness, witness_error = _read_topology_witness(result.topology_witness_path)
    if witness is None:
        return False, witness_error or "topology witness read failed"
    try:
        observed_witness_sha256 = _canonical_sha256(witness, "topology witness")
    except ProposalMiniLevFlowError as exc:
        return False, str(exc)
    if observed_witness_sha256 != witness_sha256:
        return False, "topology witness digest mismatch"
    expected_witness_keys = {
        "schema",
        "run_id",
        "flow_id",
        "flow_policy_sha256",
        "binding_artifact_sha256",
        "projection",
        "projection_sha256",
        "profile_identity",
        "profile_outcome",
        "evaluation_executed",
        "claim_ceiling",
        "promotion_allowed",
    }
    if set(witness) != expected_witness_keys:
        return False, "topology witness keys mismatch"
    if (
        witness.get("schema") != _TOPOLOGY_WITNESS_SCHEMA
        or witness.get("run_id") != result.run_id
        or witness.get("flow_id") != FLOW_ID
        or witness.get("flow_policy_sha256") != result.flow_policy_sha256
        or witness.get("binding_artifact_sha256")
        != result.binding_artifact_sha256
        or witness.get("claim_ceiling") != _CLAIM_CEILING
        or witness.get("promotion_allowed") is not False
    ):
        return False, "topology witness fixed binding mismatch"
    initial_context = result.flow_receipt.get("initial_context")
    if not isinstance(initial_context, dict) or (
        initial_context.get("binding_artifact_sha256")
        != result.binding_artifact_sha256
    ):
        return False, "topology witness binding artifact is not in the receipt"
    try:
        receipt_projection = _TOPOLOGY.projection_from_receipt_policy(
            result.flow_receipt.get("policy")
        )
        receipt_projection_sha256 = _canonical_sha256(
            receipt_projection,
            "receipt topology projection",
        )
    except (MiniLevTopologyError, ProposalMiniLevFlowError) as exc:
        return False, str(exc)
    if (
        witness.get("projection") != receipt_projection
        or witness.get("projection_sha256") != receipt_projection_sha256
    ):
        return False, "topology witness projection binding mismatch"
    profile_identity = witness.get("profile_identity")
    profile_outcome = witness.get("profile_outcome")
    identity_valid, identity_reason = _TOPOLOGY.verify_profile_identity(
        profile_identity
    )
    if not identity_valid:
        return False, identity_reason
    if not isinstance(profile_outcome, dict):
        return False, "topology witness profile material is malformed"
    expected_outcome_keys = {
        "disposition",
        "reason",
        "evidence",
        "evidence_sha256",
    }
    if set(profile_outcome) != expected_outcome_keys:
        return False, "topology profile outcome keys mismatch"
    if not isinstance(profile_outcome.get("disposition"), str) or not isinstance(
        profile_outcome.get("reason"), str
    ):
        return False, "topology profile outcome fields are malformed"
    try:
        outcome_evidence = _canonical_dict(
            profile_outcome.get("evidence"),
            "topology profile outcome evidence",
        )
        outcome_evidence_sha256 = _canonical_sha256(
            outcome_evidence,
            "topology profile outcome evidence",
        )
    except ProposalMiniLevFlowError as exc:
        return False, str(exc)
    if profile_outcome.get("evidence_sha256") != outcome_evidence_sha256:
        return False, "topology profile evidence digest mismatch"
    evaluation_executed = witness.get("evaluation_executed")
    if not isinstance(evaluation_executed, bool):
        return False, "topology evaluation flag is invalid"
    if (
        profile_identity.get("identity_verified") is True
        and profile_outcome.get("disposition") in {"ELIGIBLE", "PARKED"}
        and evaluation_executed is not True
    ):
        return False, "topology eligible or parked outcome lacks an evaluator run"

    expected_signal = HookSignal.BLOCKED
    if profile_identity.get("identity_verified") is True:
        if profile_outcome.get("disposition") == "PARKED":
            expected_signal = HookSignal.PARKED
        elif (
            profile_outcome.get("disposition") == "ELIGIBLE"
            and profile_outcome.get("reason")
            == "workflow_graph_obligations_satisfied"
            and _TOPOLOGY.eligible_evidence(
                outcome_evidence,
                receipt_projection,
                receipt_projection_sha256,
            )
        ):
            expected_signal = HookSignal.PASS
    elif (
        profile_outcome.get("reason") != "workflow_profile_identity_drift"
        or evaluation_executed
    ):
        return False, "topology profile identity failure is inconsistent"
    if signal != expected_signal.value:
        return False, "topology event signal disagrees with witness outcome"
    expected_update = {_TOPOLOGY_WITNESS_UPDATE_KEY: witness_sha256}
    if (
        first.get("applied_context_updates") != expected_update
        or first.get("hook_observation") != expected_update
        or not isinstance(first.get("controller_output"), dict)
        or first["controller_output"].get("observation") != expected_update
        or first["controller_output"].get("context_updates") != expected_update
    ):
        return False, "topology witness is not bound to its first event"
    final_context = result.flow_receipt.get("final_context")
    if not isinstance(final_context, dict) or (
        final_context.get(_TOPOLOGY_WITNESS_UPDATE_KEY) != witness_sha256
    ):
        return False, "topology witness is not bound to the receipt context"
    if expected_signal is not HookSignal.PASS and len(records) != 1:
        return False, "provider path ran after a failed topology preflight"
    return True, "topology witness and first gate event match"


def verify_proposal_minilev_flow(
    result: ProposalMiniLevFlowResult,
) -> tuple[bool, str]:
    """Recheck the fixed Mini-Lev receipt against its retained ledger."""

    if type(result) is not ProposalMiniLevFlowResult:
        return False, "flow result type is invalid"
    if result.flow_receipt.get("terminal") != result.terminal:
        return False, "terminal binding mismatch"
    if result.flow_receipt.get("flow_id") != FLOW_ID:
        return False, "flow id mismatch"
    try:
        valid, reason = verify_flow_receipt(
            result.flow_receipt,
            expected_run_id=result.run_id,
            expected_policy_sha256=result.flow_policy_sha256,
            expected_ledger_path=result.flow_ledger_path,
            expected_retained_head_sha256=result.flow_receipt["ledger"][
                "retained_head_sha256"
            ],
            expected_receipt_sha256=result.flow_receipt_sha256,
        )
    except (KeyError, TypeError):
        return False, "flow receipt ledger binding is malformed"
    if not valid:
        return False, reason
    if (
        not isinstance(result.controller_state_root, Path)
        or not isinstance(result.execution_lease_state_path, Path)
        or not _is_sha256(result.execution_lease_slot_sha256)
    ):
        return False, "proposal execution lease result binding is malformed"
    expected_state_path = (
        result.controller_state_root.resolve()
        / EXECUTION_LEASE_DIRECTORY_NAME
        / PROPOSAL_OBSERVATION_LEASE_NAME
    )
    if result.execution_lease_state_path.resolve() != expected_state_path:
        return False, "proposal execution lease state path is outside controller state"
    try:
        expected_clock_id = _controller_lease_clock_id(
            result.controller_state_root,
            result.execution_lease_state_path,
        )
    except ProposalMiniLevFlowError as exc:
        return False, f"proposal execution lease clock-domain mismatch: {exc}"
    policy_lease = result.flow_receipt.get("policy", {}).get("execution_lease")
    if not isinstance(policy_lease, dict) or (
        policy_lease.get("slot_sha256") != result.execution_lease_slot_sha256
        or policy_lease.get("node_id") != "proposal-observation"
        or policy_lease.get("hook_id") != "bounded-proposal-observation"
        or policy_lease.get("owner_id") != PROPOSAL_LEASE_OWNER_ID
        or policy_lease.get("ttl_ns") != PROPOSAL_LEASE_TTL_NS
        or policy_lease.get("clock_source") != PROPOSAL_LEASE_CLOCK_SOURCE
        or policy_lease.get("clock_id") != expected_clock_id
    ):
        return False, "proposal execution lease policy binding mismatch"
    return _verify_topology_witness(result)


def run_proposal_minilev_flow(
    *,
    run_root: Path,
    controller_state_root: Path,
    caller_source_path: Path,
    controller_source_path: Path,
    binding_artifact_sha256: str,
    callbacks: ProposalMiniLevCallbacks,
) -> ProposalMiniLevFlowResult:
    """Run the immutable proposal -> gate -> ClaimGate flow once.

    `callbacks` is an internal controller seam, not a public user or model
    interface.  The fixed Mini-Lev transition table remains the sole owner of
    all next-node and terminal choices.
    """

    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ProposalMiniLevFlowError("run_root must be an absolute pathlib.Path")
    if type(callbacks) is not ProposalMiniLevCallbacks:
        raise ProposalMiniLevFlowError("callbacks must be ProposalMiniLevCallbacks")
    for callback, name in (
        (callbacks.proposal, "proposal callback"),
        (callbacks.proposal_gate, "proposal gate callback"),
        (callbacks.claim_gate, "ClaimGate callback"),
    ):
        if not callable(callback):
            raise ProposalMiniLevFlowError(f"{name} is not callable")
    caller_source_path, caller_source_sha256 = _verified_source_path(
        caller_source_path, "caller source path"
    )
    controller_source_path, controller_source_sha256 = _verified_source_path(
        controller_source_path, "controller source path"
    )
    binding_artifact_sha256 = _require_sha256(
        binding_artifact_sha256, "binding artifact digest"
    )
    run_root = run_root.expanduser().resolve()
    if run_root.exists():
        raise ProposalMiniLevFlowError("proposal flow root must not already exist")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ProposalMiniLevFlowError(
            f"proposal flow root creation failed: {exc}"
        ) from exc

    controller_state_root, execution_lease_state_path = _controller_state_root(
        controller_state_root,
        flow_root=run_root,
    )
    execution_lease_store = ExecutionLeaseStore(execution_lease_state_path)
    execution_lease_clock_id = _controller_lease_clock_id(
        controller_state_root,
        execution_lease_state_path,
    )

    run_id = "proposal-" + secrets.token_hex(16)
    execution_lease_clock = ControllerMonotonicClock(
        clock_id=execution_lease_clock_id
    )
    try:
        runtime = _build_runtime(
            run_id=run_id,
            ledger_path=run_root / FLOW_LEDGER_NAME,
            execution_lease_store=execution_lease_store,
            execution_lease_clock=execution_lease_clock,
            execution_lease_clock_id=execution_lease_clock_id,
        )
    except MiniLevError as exc:
        raise ProposalMiniLevFlowError(
            f"proposal flow construction failed: {exc}"
        ) from exc
    state = _ActiveRun(
        context=ProposalFlowContext(
            run_id=run_id,
            attempt_number=0,
            flow_policy_sha256=runtime.policy_sha256,
            binding_artifact_sha256=binding_artifact_sha256,
            caller_source_sha256=caller_source_sha256,
            controller_source_sha256=controller_source_sha256,
        ),
        callbacks=callbacks,
        lock=threading.RLock(),
        caller_source_path=caller_source_path,
        controller_source_path=controller_source_path,
        policy=runtime.policy,
        flow_root=run_root,
        topology_witness_path=run_root / TOPOLOGY_WITNESS_NAME,
    )
    with _ACTIVE_RUNS_LOCK:
        if run_id in _ACTIVE_RUNS:
            raise ProposalMiniLevFlowError("proposal flow run id collision")
        _ACTIVE_RUNS[run_id] = state
    try:
        flow_receipt = runtime.run(
            {
                "binding_artifact_sha256": binding_artifact_sha256,
                "caller_source_sha256": caller_source_sha256,
                "controller_source_sha256": controller_source_sha256,
            }
        )
        result = ProposalMiniLevFlowResult(
            run_id=run_id,
            terminal=flow_receipt["terminal"],
            flow_policy_sha256=runtime.policy_sha256,
            flow_receipt_sha256=runtime.receipt_sha256,
            binding_artifact_sha256=binding_artifact_sha256,
            topology_witness_sha256=state.topology_witness_sha256,
            flow_root=run_root,
            flow_receipt_path=run_root / FLOW_RECEIPT_NAME,
            flow_ledger_path=runtime.ledger_path,
            flow_ledger_head_path=runtime.ledger_path.with_name(
                runtime.ledger_path.name + ".head"
            ),
            topology_witness_path=state.topology_witness_path,
            controller_state_root=controller_state_root,
            execution_lease_state_path=execution_lease_state_path,
            execution_lease_slot_sha256=execution_lease_store.slot_sha256,
            flow_receipt=flow_receipt,
        )
        valid, reason = verify_proposal_minilev_flow(result)
        if not valid:
            raise ProposalMiniLevFlowError(
                f"proposal flow receipt failed verification: {reason}"
            )
        _persist_exclusive(
            result.flow_receipt_path,
            flow_receipt,
            label="proposal flow receipt",
        )
        return result
    except MiniLevError as exc:
        raise ProposalMiniLevFlowError(
            f"proposal flow execution failed: {exc}"
        ) from exc
    finally:
        with _ACTIVE_RUNS_LOCK:
            _ACTIVE_RUNS.pop(run_id, None)
