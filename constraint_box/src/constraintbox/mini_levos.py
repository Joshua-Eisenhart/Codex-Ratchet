"""A narrow, deterministic, CB-native flow kernel inspired by LevOS.

The useful LevOS ideas are typed instructions, pure controller-selected
transitions, bounded loops, and durable events.  ConstraintBox does not import
Lev as an authority and does not admit arbitrary commands or model-authored
flows.  Registered hooks return observations; only this controller chooses the
next node or terminal state.
"""

from __future__ import annotations

import hashlib
import inspect
import marshal
import os
import re
import sys
import time
import types
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .execution_lease import (
    MAX_TTL_NS,
    ClockSample,
    ExecutionLeaseBinding,
    ExecutionLeaseStore,
    ReleaseCause,
    VerificationStatus,
    validate_execution_lease_receipt,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .ledger import GENESIS, HashChainLedger
from .python_runtime import (
    PythonRuntimeError,
    capture_python_runtime,
    python_runtime_policy_sha256,
    verify_python_runtime_stable,
)


SCHEMA = "constraintbox.mini-levos-receipt.v1"
EVENT_SCHEMA = "constraintbox.mini-levos-event.v1"
CONTROLLER_METADATA_SCHEMA = "constraintbox.mini-levos-controller-metadata.v1"
CONTROLLER_METADATA_KEY = "__constraintbox_controller_metadata__"
EXECUTION_LEASE_REQUIREMENT_SCHEMA = "constraintbox.execution-lease-requirement.v1"
EXECUTION_LEASE_HOOK_AUDIT_SCHEMA = "constraintbox.execution-lease-hook-audit.v1"
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_TERMINALS = frozenset(
    {"ELIGIBLE", "BLOCKED", "PARKED", "HOLD", "RELEASED"}
)
_POSITIVE_TERMINALS = frozenset({"ELIGIBLE", "RELEASED"})
_HARD_MAX_STEPS = 4_096
_HARD_MAX_VISITS_PER_NODE = 1_024
_HARD_MAX_RETRIES = 256
_HARD_MAX_CONTEXT_BYTES = 1_048_576
_HARD_MAX_EVENT_BYTES = 2_097_152
_HARD_MAX_RECEIPT_BYTES = 8_388_608
_HARD_MAX_HOOK_OUTPUT_BYTES = 1_048_576
_AUTHORITY_KEYS = frozenset(
    {
        "allpass",
        "command",
        "constraintboxcontrollermetadata",
        "decision",
        "disposition",
        "executable",
        "hook",
        "hookid",
        "maxsteps",
        "nextnode",
        "pass",
        "policy",
        "profileid",
        "promotionallowed",
        "provider",
        "python",
        "release",
        "retrybudget",
        "timeout",
        "tolerance",
        "terminal",
        "transition",
        "verdict",
    }
)


class MiniLevError(RuntimeError):
    """The fixed flow could not be constructed, executed, or verified."""


class HookKind(str, Enum):
    PROPOSAL = "proposal"
    GATE = "gate"
    HOOK = "hook"
    TOOL = "tool"


class HookSignal(str, Enum):
    OBSERVED = "OBSERVED"
    PASS = "PASS"
    RETRY = "RETRY"
    BLOCKED = "BLOCKED"
    PARKED = "PARKED"
    HOLD = "HOLD"


@dataclass(frozen=True)
class HookResult:
    """One hook observation.  It never contains a next-node selection."""

    signal: HookSignal
    observation: dict[str, Any] = field(default_factory=dict)
    context_updates: dict[str, Any] = field(default_factory=dict)


HookHandler = Callable[[dict[str, Any]], HookResult]


@dataclass(frozen=True)
class HookRegistration:
    hook_id: str
    kind: HookKind
    handler: HookHandler
    source_path: Path
    source_sha256: str
    code_sha256: str
    allowed_signals: tuple[HookSignal, ...]
    allowed_update_keys: tuple[str, ...] = ()
    max_output_bytes: int = 65_536


@dataclass(frozen=True)
class FlowNode:
    node_id: str
    hook_id: str


@dataclass(frozen=True)
class FlowTransition:
    from_node: str
    signal: HookSignal
    to_node: str


@dataclass(frozen=True)
class ExecutionLeaseRequirement:
    """One controller-owned lease requirement embedded in a frozen policy.

    The requirement names exactly one Mini-Lev node and hook.  It is not a
    capability exposed to the hook, provider, or model.  The durable slot is
    selected by the controller before the runtime is constructed, and the
    resulting ``slot_sha256`` is sealed into the policy material.
    """

    node_id: str
    hook_id: str
    owner_id: str
    slot_sha256: str
    ttl_ns: int
    clock_source: str
    clock_id: str
    tokens_persisted: bool = False
    heartbeat_allowed: bool = False

    def __post_init__(self) -> None:
        _safe_identifier(self.node_id, "execution lease node_id")
        _safe_identifier(self.hook_id, "execution lease hook_id")
        _safe_identifier(self.owner_id, "execution lease owner_id")
        _lower_sha256(self.slot_sha256, "execution lease slot_sha256")
        ttl = _positive_int(self.ttl_ns, "execution lease ttl_ns")
        if ttl > MAX_TTL_NS:
            raise MiniLevError("execution lease ttl_ns exceeds the lease ceiling")
        _safe_identifier(self.clock_source, "execution lease clock_source")
        _safe_identifier(self.clock_id, "execution lease clock_id")
        if self.tokens_persisted is not False:
            raise MiniLevError("execution lease tokens must never be persisted")
        if self.heartbeat_allowed is not False:
            raise MiniLevError("execution lease v1 does not allow heartbeat")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": EXECUTION_LEASE_REQUIREMENT_SCHEMA,
            "node_id": self.node_id,
            "hook_id": self.hook_id,
            "owner_id": self.owner_id,
            "slot_sha256": self.slot_sha256,
            "ttl_ns": self.ttl_ns,
            "clock_source": self.clock_source,
            "clock_id": self.clock_id,
            "tokens_persisted": False,
            "heartbeat_allowed": False,
        }

    @property
    def sha256(self) -> str:
        return _SHA256(canonical_json(self.as_dict())).hexdigest()


@dataclass(frozen=True)
class FlowPolicy:
    flow_id: str
    entry_node: str
    nodes: tuple[FlowNode, ...]
    transitions: tuple[FlowTransition, ...]
    terminal_nodes: tuple[str, ...]
    required_nodes: tuple[str, ...]
    max_steps: int
    max_visits_per_node: int
    max_retries: int
    max_context_bytes: int
    max_event_bytes: int
    max_receipt_bytes: int
    claim_ceiling: str
    execution_lease: ExecutionLeaseRequirement | None = None


@dataclass(frozen=True)
class _LeaseInvocation:
    """Controller-only result of one optionally leased hook invocation."""

    result: object
    audit: dict[str, Any]
    hook_reported_signal: str | None
    controller_reason: str | None


class ControllerMonotonicClock:
    """Small controller clock with monotonic output even on coarse timers."""

    def __init__(self, *, clock_id: str):
        self.clock_id = _safe_identifier(clock_id, "execution lease clock_id")
        self._last_tick_ns = -1

    def sample(self) -> ClockSample:
        tick_ns = time.monotonic_ns()
        if not isinstance(tick_ns, int) or isinstance(tick_ns, bool):
            raise MiniLevError("controller monotonic clock returned a non-integer")
        if tick_ns < 0:
            raise MiniLevError("controller monotonic clock returned a negative tick")
        if tick_ns <= self._last_tick_ns:
            tick_ns = self._last_tick_ns + 1
        self._last_tick_ns = tick_ns
        return ClockSample(clock_id=self.clock_id, tick_ns=tick_ns)


class ExecutionLeaseGuard:
    """Keep a selected hook inside a controller-owned lease lifecycle.

    Tokens remain local to this object.  The returned audit contains only
    public records and deterministic verdict material so it can be inserted
    into the Mini-Lev hash chain and replayed after the current slot advances.
    """

    def __init__(
        self,
        requirement: ExecutionLeaseRequirement,
        store: ExecutionLeaseStore,
        *,
        clock_sample: Callable[[], ClockSample],
    ):
        if type(requirement) is not ExecutionLeaseRequirement:
            raise MiniLevError("execution lease guard needs one frozen requirement")
        if not isinstance(store, ExecutionLeaseStore):
            raise MiniLevError("execution lease guard needs an ExecutionLeaseStore")
        if not callable(clock_sample):
            raise MiniLevError("execution lease guard needs a controller clock")
        if requirement.slot_sha256 != store.slot_sha256:
            raise MiniLevError("execution lease guard store does not match policy slot")
        self.requirement = requirement
        self._store = store
        self._clock_sample = clock_sample

    @staticmethod
    def _error_detail(exc: Exception) -> str:
        return f"{type(exc).__name__}: {str(exc)[:768]}"

    @staticmethod
    def _verdict_material(value: object) -> dict[str, Any] | None:
        status = getattr(value, "status", None)
        reason = getattr(value, "reason", None)
        record_sha256 = getattr(value, "record_sha256", None)
        if not isinstance(status, VerificationStatus) or not isinstance(reason, str):
            return None
        if record_sha256 is not None:
            _lower_sha256(record_sha256, "execution lease verdict record_sha256")
        return {
            "status": status.value,
            "reason": reason,
            "record_sha256": record_sha256,
        }

    def _sample(self) -> ClockSample:
        sample = self._clock_sample()
        if not isinstance(sample, ClockSample):
            raise MiniLevError("execution lease clock did not return ClockSample")
        if sample.clock_id != self.requirement.clock_id:
            raise MiniLevError("execution lease clock does not match policy clock_id")
        return sample

    def execute(
        self,
        *,
        run_id: str,
        flow_id: str,
        policy_sha256: str,
        runtime_identity_sha256: str,
        node: FlowNode,
        registration: HookRegistration,
        visit: int,
        input_sha256: str,
        handler_context: dict[str, Any],
    ) -> _LeaseInvocation:
        """Acquire, recheck, invoke, recheck, and durably close one hook."""

        requirement = self.requirement
        if node.node_id != requirement.node_id or registration.hook_id != requirement.hook_id:
            raise MiniLevError("execution lease guard was called for another hook")
        flow_sha256 = _execution_lease_flow_sha256(flow_id)
        instruction_sha256 = _execution_lease_instruction_sha256(
            flow_id=flow_id,
            node=node,
            registration=registration,
            input_sha256=input_sha256,
        )
        binding = ExecutionLeaseBinding(
            owner_id=requirement.owner_id,
            run_id=run_id,
            node_id=node.node_id,
            visit=visit,
            slot_sha256=requirement.slot_sha256,
            flow_sha256=flow_sha256,
            policy_sha256=policy_sha256,
            runtime_sha256=runtime_identity_sha256,
            instruction_sha256=instruction_sha256,
        )
        audit: dict[str, Any] = {
            "schema": EXECUTION_LEASE_HOOK_AUDIT_SCHEMA,
            "requirement_sha256": requirement.sha256,
            "binding": binding.as_dict(),
            "binding_sha256": binding.sha256,
            "slot_sha256": requirement.slot_sha256,
            "clock_source": requirement.clock_source,
            # This is the policy-bound expected domain, even if sampling
            # fails before an observed ClockSample can be admitted.  Keeping
            # it present lets an acquire failure retain a replayable HOLD
            # receipt instead of collapsing the entire flow verification.
            "clock_id": requirement.clock_id,
            "acquire_record": None,
            "pre_hook_verdict": None,
            "handler_started": False,
            "handler_completed": False,
            "post_hook_verdict": None,
            "release_cause": None,
            "release_record": None,
            "release_status": "NOT_ACQUIRED",
            "failure_stage": None,
            "failure_detail": None,
        }
        token = None
        handler_result: object | None = None
        hook_reported_signal: str | None = None
        failure_stage: str | None = None
        failure_detail: str | None = None

        try:
            acquired_clock = self._sample()
            grant = self._store.acquire(
                binding,
                ttl_ns=requirement.ttl_ns,
                clock=acquired_clock,
            )
            token = grant.token
            audit["acquire_record"] = dict(grant.receipt)
        except Exception as exc:  # noqa: BLE001 - fail closed at ownership boundary
            failure_stage = "acquire"
            failure_detail = self._error_detail(exc)

        if token is not None and failure_stage is None:
            try:
                pre_clock = self._sample()
                if audit["clock_id"] != pre_clock.clock_id:
                    raise MiniLevError("execution lease clock domain changed")
                pre_verdict = self._store.verify(binding, token, clock=pre_clock)
                audit["pre_hook_verdict"] = self._verdict_material(pre_verdict)
                if pre_verdict.status is not VerificationStatus.VALID:
                    failure_stage = "pre_hook_verify"
                    failure_detail = pre_verdict.reason
            except Exception as exc:  # noqa: BLE001 - fail closed at ownership boundary
                failure_stage = "pre_hook_verify"
                failure_detail = self._error_detail(exc)

        if token is not None and failure_stage is None:
            audit["handler_started"] = True
            try:
                handler_result = registration.handler(handler_context)
                audit["handler_completed"] = True
                if isinstance(handler_result, HookResult) and isinstance(
                    handler_result.signal, HookSignal
                ):
                    hook_reported_signal = handler_result.signal.value
            except Exception as exc:  # noqa: BLE001 - preserve controller HOLD
                failure_stage = "handler"
                failure_detail = self._error_detail(exc)

        if token is not None and failure_stage is None:
            try:
                post_clock = self._sample()
                if audit["clock_id"] != post_clock.clock_id:
                    raise MiniLevError("execution lease clock domain changed")
                post_verdict = self._store.verify(binding, token, clock=post_clock)
                audit["post_hook_verdict"] = self._verdict_material(post_verdict)
                if post_verdict.status is not VerificationStatus.VALID:
                    failure_stage = "post_hook_verify"
                    failure_detail = post_verdict.reason
            except Exception as exc:  # noqa: BLE001 - fail closed at ownership boundary
                failure_stage = "post_hook_verify"
                failure_detail = self._error_detail(exc)

        if token is not None:
            cause = (
                ReleaseCause.COMPLETED
                if failure_stage is None and audit["handler_completed"] is True
                else ReleaseCause.FAILED
            )
            audit["release_cause"] = cause.value
            try:
                release_clock = self._sample()
                if audit["clock_id"] != release_clock.clock_id:
                    raise MiniLevError("execution lease clock domain changed")
                released = self._store.release(
                    binding,
                    token,
                    clock=release_clock,
                    cause=cause,
                )
                audit["release_record"] = dict(released)
                audit["release_status"] = "RELEASED"
            except Exception as exc:  # noqa: BLE001 - release ambiguity is a HOLD
                audit["release_status"] = "RELEASE_FAILED"
                if failure_stage is None:
                    failure_stage = "release"
                    failure_detail = self._error_detail(exc)
                elif failure_detail is None:
                    failure_detail = self._error_detail(exc)

        audit["failure_stage"] = failure_stage
        audit["failure_detail"] = failure_detail
        if failure_stage is not None:
            reason = "execution_lease_" + failure_stage
            return _LeaseInvocation(
                _minimal_hold_result(reason, failure_detail),
                audit,
                hook_reported_signal,
                reason,
            )
        if handler_result is None:
            return _LeaseInvocation(
                _minimal_hold_result("execution_lease_handler_missing"),
                audit,
                hook_reported_signal,
                "execution_lease_handler_missing",
            )
        return _LeaseInvocation(handler_result, audit, hook_reported_signal, None)


def handler_code_sha256(handler: HookHandler) -> str:
    code = getattr(handler, "__code__", None)
    if not isinstance(code, types.CodeType):
        raise MiniLevError("registered hook must be a Python function")
    if getattr(handler, "__closure__", None) is not None:
        raise MiniLevError("registered hook closures are not admitted")
    try:
        defaults = canonical_json(
            {
                "defaults": getattr(handler, "__defaults__", None),
                "kwdefaults": getattr(handler, "__kwdefaults__", None),
            }
        )
    except (TypeError, ValueError) as exc:
        raise MiniLevError("registered hook defaults are not canonical JSON") from exc
    digest = _SHA256()
    digest.update(marshal.dumps(code))
    digest.update(b"\0")
    digest.update(defaults)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _SHA256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise MiniLevError(f"hook source unavailable: {path}") from exc


def _safe_identifier(value: object, where: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise MiniLevError(f"{where} is not a safe bounded identifier")
    return value


def _positive_int(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MiniLevError(f"{where} must be a positive integer")
    return value


def _nonnegative_int(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MiniLevError(f"{where} must be a non-negative integer")
    return value


def _lower_sha256(value: object, where: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise MiniLevError(f"{where} must be a lowercase SHA-256")
    return value


def _execution_lease_flow_sha256(flow_id: str) -> str:
    return _SHA256(
        canonical_json(
            {
                "schema": "constraintbox.execution-lease-flow-binding.v1",
                "flow_id": _safe_identifier(flow_id, "execution lease flow_id"),
            }
        )
    ).hexdigest()


def _execution_lease_instruction_sha256(
    *,
    flow_id: str,
    node: FlowNode,
    registration: HookRegistration,
    input_sha256: str,
) -> str:
    """Bind the exact static hook and canonical input, never model text."""

    return _SHA256(
        canonical_json(
            {
                "schema": "constraintbox.execution-lease-instruction.v1",
                "flow_id": _safe_identifier(flow_id, "execution lease flow_id"),
                "node_id": _safe_identifier(
                    node.node_id, "execution lease instruction node_id"
                ),
                "hook_id": _safe_identifier(
                    registration.hook_id,
                    "execution lease instruction hook_id",
                ),
                "hook_source_sha256": _lower_sha256(
                    registration.source_sha256,
                    "execution lease instruction source_sha256",
                ),
                "hook_code_sha256": _lower_sha256(
                    registration.code_sha256,
                    "execution lease instruction code_sha256",
                ),
                "input_sha256": _lower_sha256(
                    input_sha256, "execution lease instruction input_sha256"
                ),
            }
        )
    ).hexdigest()


def _execution_lease_instruction_sha256_from_material(
    *,
    flow_id: str,
    node_id: str,
    hook_id: str,
    hook_source_sha256: str,
    hook_code_sha256: str,
    input_sha256: str,
) -> str:
    return _SHA256(
        canonical_json(
            {
                "schema": "constraintbox.execution-lease-instruction.v1",
                "flow_id": _safe_identifier(flow_id, "execution lease flow_id"),
                "node_id": _safe_identifier(
                    node_id, "execution lease instruction node_id"
                ),
                "hook_id": _safe_identifier(
                    hook_id, "execution lease instruction hook_id"
                ),
                "hook_source_sha256": _lower_sha256(
                    hook_source_sha256,
                    "execution lease instruction source_sha256",
                ),
                "hook_code_sha256": _lower_sha256(
                    hook_code_sha256,
                    "execution lease instruction code_sha256",
                ),
                "input_sha256": _lower_sha256(
                    input_sha256, "execution lease instruction input_sha256"
                ),
            }
        )
    ).hexdigest()


def _execution_lease_requirement_from_material(
    value: object,
    *,
    node_hooks: dict[str, str],
) -> dict[str, Any] | None:
    """Validate the optional policy-bound lease requirement for replay."""

    if value is None:
        return None
    if not isinstance(value, dict):
        raise MiniLevError("embedded execution lease requirement is malformed")
    expected_keys = {
        "schema",
        "node_id",
        "hook_id",
        "owner_id",
        "slot_sha256",
        "ttl_ns",
        "clock_source",
        "clock_id",
        "tokens_persisted",
        "heartbeat_allowed",
    }
    if set(value) != expected_keys:
        raise MiniLevError("embedded execution lease requirement keys mismatch")
    if value.get("schema") != EXECUTION_LEASE_REQUIREMENT_SCHEMA:
        raise MiniLevError("embedded execution lease requirement schema mismatch")
    requirement = ExecutionLeaseRequirement(
        node_id=value.get("node_id"),
        hook_id=value.get("hook_id"),
        owner_id=value.get("owner_id"),
        slot_sha256=value.get("slot_sha256"),
        ttl_ns=value.get("ttl_ns"),
        clock_source=value.get("clock_source"),
        clock_id=value.get("clock_id"),
        tokens_persisted=value.get("tokens_persisted"),
        heartbeat_allowed=value.get("heartbeat_allowed"),
    )
    if node_hooks.get(requirement.node_id) != requirement.hook_id:
        raise MiniLevError("embedded execution lease node-hook binding mismatch")
    material = requirement.as_dict()
    if value != material:
        raise MiniLevError("embedded execution lease requirement is not canonical")
    return material


def _canonical_object(value: object, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MiniLevError(f"{where} must be a JSON object")
    try:
        raw = canonical_json(value)
        return parse_json_object(raw)
    except (IntakeError, TypeError, ValueError) as exc:
        raise MiniLevError(f"{where} is not finite canonical JSON: {exc}") from exc


def _normalized_key(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _authority_paths(value: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _normalized_key(str(key)) in _AUTHORITY_KEYS:
                found.append(child_path)
            found.extend(_authority_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_authority_paths(child, f"{path}[{index}]"))
    return found


def _resolve_module_binding(handler: HookHandler) -> object:
    module_name = getattr(handler, "__module__", None)
    qualname = getattr(handler, "__qualname__", None)
    if (
        not isinstance(module_name, str)
        or module_name not in sys.modules
        or not isinstance(qualname, str)
        or "<locals>" in qualname
    ):
        raise MiniLevError("registered hook has no stable module binding")
    value: object = sys.modules[module_name]
    for part in qualname.split("."):
        try:
            value = getattr(value, part)
        except AttributeError as exc:
            raise MiniLevError(
                f"registered hook binding is unavailable: {module_name}.{qualname}"
            ) from exc
    return value


def _verify_hook_identity(registration: HookRegistration) -> dict[str, Any]:
    source_path = registration.source_path.resolve()
    if not source_path.is_file():
        raise MiniLevError(f"hook source is not a file: {source_path}")
    observed_source = _sha256_file(source_path)
    if observed_source != registration.source_sha256:
        raise MiniLevError(f"hook source digest drift: {registration.hook_id}")
    try:
        observed_path = Path(inspect.getsourcefile(registration.handler)).resolve()
    except (OSError, TypeError) as exc:
        raise MiniLevError(
            f"hook source identity unavailable: {registration.hook_id}"
        ) from exc
    if observed_path != source_path:
        raise MiniLevError(f"hook source path drift: {registration.hook_id}")
    observed_code = handler_code_sha256(registration.handler)
    if observed_code != registration.code_sha256:
        raise MiniLevError(f"hook code digest drift: {registration.hook_id}")
    if _resolve_module_binding(registration.handler) is not registration.handler:
        raise MiniLevError(f"hook live binding drift: {registration.hook_id}")
    return {
        "hook_id": registration.hook_id,
        "kind": registration.kind.value,
        "module": registration.handler.__module__,
        "qualname": registration.handler.__qualname__,
        "source_path": str(source_path),
        "source_sha256": observed_source,
        "code_sha256": observed_code,
    }


def _registration_material(registration: HookRegistration) -> dict[str, Any]:
    if type(registration) is not HookRegistration:
        raise MiniLevError("hook registry entries must be HookRegistration values")
    _safe_identifier(registration.hook_id, "hook_id")
    if not isinstance(registration.kind, HookKind):
        raise MiniLevError("hook kind must be a HookKind")
    if type(registration.handler) is not types.FunctionType:
        raise MiniLevError("registered hook must be one Python function")
    if not isinstance(registration.source_path, Path):
        raise MiniLevError("hook source_path must be a pathlib.Path")
    _lower_sha256(registration.source_sha256, "hook source_sha256")
    _lower_sha256(registration.code_sha256, "hook code_sha256")
    _positive_int(registration.max_output_bytes, "hook max_output_bytes")
    if registration.max_output_bytes > _HARD_MAX_HOOK_OUTPUT_BYTES:
        raise MiniLevError("hook max_output_bytes exceeds the kernel ceiling")
    if (
        type(registration.allowed_signals) is not tuple
        or not registration.allowed_signals
        or len(set(registration.allowed_signals))
        != len(registration.allowed_signals)
        or any(
            not isinstance(signal, HookSignal)
            for signal in registration.allowed_signals
        )
    ):
        raise MiniLevError("hook allowed_signals must be unique HookSignal values")
    allowed_by_kind = {
        HookKind.PROPOSAL: {HookSignal.OBSERVED, HookSignal.PARKED},
        HookKind.HOOK: {HookSignal.OBSERVED, HookSignal.PARKED},
        HookKind.TOOL: {HookSignal.OBSERVED, HookSignal.PARKED},
        HookKind.GATE: {
            HookSignal.PASS,
            HookSignal.RETRY,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        },
    }[registration.kind]
    if not set(registration.allowed_signals).issubset(allowed_by_kind):
        raise MiniLevError(
            f"hook kind {registration.kind.value} cannot emit one of its signals"
        )
    if (
        type(registration.allowed_update_keys) is not tuple
        or len(set(registration.allowed_update_keys))
        != len(registration.allowed_update_keys)
        or any(
            not isinstance(key, str)
            or not key
            or _normalized_key(key) in _AUTHORITY_KEYS
            for key in registration.allowed_update_keys
        )
    ):
        raise MiniLevError("hook allowed_update_keys are invalid")
    _verify_hook_identity(registration)
    return {
        "hook_id": registration.hook_id,
        "kind": registration.kind.value,
        "module": registration.handler.__module__,
        "qualname": registration.handler.__qualname__,
        "source_path": str(registration.source_path.resolve()),
        "source_sha256": registration.source_sha256,
        "code_sha256": registration.code_sha256,
        "allowed_signals": sorted(
            signal.value for signal in registration.allowed_signals
        ),
        "allowed_update_keys": sorted(registration.allowed_update_keys),
        "max_output_bytes": registration.max_output_bytes,
    }


def _is_dag(
    nodes: set[str],
    edges: list[tuple[str, str]],
) -> bool:
    indegree = {node: 0 for node in nodes}
    outgoing = {node: [] for node in nodes}
    for source, target in edges:
        outgoing[source].append(target)
        indegree[target] += 1
    ready = sorted(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while ready:
        node = ready.pop(0)
        visited += 1
        for target in sorted(outgoing[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    return visited == len(nodes)


def _reachable(
    start: str,
    outgoing: dict[str, set[str]],
) -> set[str]:
    seen: set[str] = set()
    pending = [start]
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(sorted(outgoing.get(node, ()), reverse=True))
    return seen


def _build_policy_material(
    policy: FlowPolicy,
    registrations: tuple[HookRegistration, ...],
) -> tuple[dict[str, Any], dict[str, HookRegistration], dict[tuple[str, HookSignal], str]]:
    if type(policy) is not FlowPolicy:
        raise MiniLevError("flow policy must be one frozen FlowPolicy")
    if type(registrations) is not tuple:
        raise MiniLevError("hook registry must be an immutable tuple")
    for value, where in (
        (policy.nodes, "nodes"),
        (policy.transitions, "transitions"),
        (policy.terminal_nodes, "terminal_nodes"),
        (policy.required_nodes, "required_nodes"),
    ):
        if type(value) is not tuple:
            raise MiniLevError(f"{where} must be an immutable tuple")
    _safe_identifier(policy.flow_id, "flow_id")
    _safe_identifier(policy.entry_node, "entry_node")
    for value, where in (
        (policy.max_steps, "max_steps"),
        (policy.max_visits_per_node, "max_visits_per_node"),
        (policy.max_context_bytes, "max_context_bytes"),
        (policy.max_event_bytes, "max_event_bytes"),
        (policy.max_receipt_bytes, "max_receipt_bytes"),
    ):
        _positive_int(value, where)
    _nonnegative_int(policy.max_retries, "max_retries")
    hard_bounds = (
        (policy.max_steps, _HARD_MAX_STEPS, "max_steps"),
        (
            policy.max_visits_per_node,
            _HARD_MAX_VISITS_PER_NODE,
            "max_visits_per_node",
        ),
        (policy.max_retries, _HARD_MAX_RETRIES, "max_retries"),
        (
            policy.max_context_bytes,
            _HARD_MAX_CONTEXT_BYTES,
            "max_context_bytes",
        ),
        (policy.max_event_bytes, _HARD_MAX_EVENT_BYTES, "max_event_bytes"),
        (
            policy.max_receipt_bytes,
            _HARD_MAX_RECEIPT_BYTES,
            "max_receipt_bytes",
        ),
    )
    for observed, maximum, where in hard_bounds:
        if observed > maximum:
            raise MiniLevError(f"{where} exceeds the kernel ceiling")
    if not isinstance(policy.claim_ceiling, str) or not policy.claim_ceiling:
        raise MiniLevError("claim_ceiling must be non-empty")

    hook_map: dict[str, HookRegistration] = {}
    hook_material: list[dict[str, Any]] = []
    for registration in registrations:
        if registration.hook_id in hook_map:
            raise MiniLevError("duplicate hook registration")
        hook_map[registration.hook_id] = registration
        hook_material.append(_registration_material(registration))

    node_map: dict[str, FlowNode] = {}
    for node in policy.nodes:
        if type(node) is not FlowNode:
            raise MiniLevError("flow nodes must be FlowNode values")
        _safe_identifier(node.node_id, "node_id")
        _safe_identifier(node.hook_id, "node hook_id")
        if node.node_id in node_map:
            raise MiniLevError("duplicate flow node")
        if node.hook_id not in hook_map:
            raise MiniLevError(f"node uses an unregistered hook: {node.hook_id}")
        node_map[node.node_id] = node
    if not node_map or policy.entry_node not in node_map:
        raise MiniLevError("entry node must be a registered flow node")
    if set(hook_map) != {node.hook_id for node in policy.nodes}:
        raise MiniLevError("hook registry must exactly match the flow nodes")
    execution_lease_material: dict[str, Any] | None = None
    if policy.execution_lease is not None:
        if type(policy.execution_lease) is not ExecutionLeaseRequirement:
            raise MiniLevError("execution lease policy must be one frozen requirement")
        requirement = policy.execution_lease
        if node_map[requirement.node_id].hook_id != requirement.hook_id:
            raise MiniLevError("execution lease node and hook do not match the flow")
        execution_lease_material = requirement.as_dict()

    terminals = set(policy.terminal_nodes)
    if (
        not terminals
        or len(terminals) != len(policy.terminal_nodes)
        or not terminals.issubset(_TERMINALS)
        or terminals & set(node_map)
    ):
        raise MiniLevError("terminal_nodes are invalid")
    required = set(policy.required_nodes)
    if (
        len(required) != len(policy.required_nodes)
        or not required.issubset(node_map)
    ):
        raise MiniLevError("required_nodes must be unique registered nodes")

    transition_map: dict[tuple[str, HookSignal], str] = {}
    outgoing_all: dict[str, set[str]] = {node: set() for node in node_map}
    outgoing_with_terminals: dict[str, set[str]] = {
        node: set() for node in (*node_map, *terminals)
    }
    nonretry_edges: list[tuple[str, str]] = []
    for transition in policy.transitions:
        if type(transition) is not FlowTransition:
            raise MiniLevError("flow transitions must be FlowTransition values")
        if transition.from_node not in node_map:
            raise MiniLevError("transition source is not a flow node")
        if not isinstance(transition.signal, HookSignal):
            raise MiniLevError("transition signal must be a HookSignal")
        if transition.to_node not in node_map and transition.to_node not in terminals:
            raise MiniLevError("transition target is not a node or terminal")
        key = (transition.from_node, transition.signal)
        if key in transition_map:
            raise MiniLevError("duplicate transition for node and signal")
        transition_map[key] = transition.to_node
        outgoing_with_terminals[transition.from_node].add(transition.to_node)
        source_kind = hook_map[node_map[transition.from_node].hook_id].kind
        if transition.signal in {
            HookSignal.BLOCKED,
            HookSignal.PARKED,
            HookSignal.HOLD,
        } and transition.to_node != transition.signal.value:
            raise MiniLevError(
                f"{transition.signal.value} must map to its matching terminal"
            )
        if (
            transition.signal is HookSignal.RETRY
            and transition.to_node not in node_map
        ):
            raise MiniLevError("RETRY must map to another bounded flow node")
        if transition.to_node in _POSITIVE_TERMINALS and (
            transition.signal is not HookSignal.PASS
            or source_kind is not HookKind.GATE
        ):
            raise MiniLevError(
                "positive terminals are reachable only from a gate PASS"
            )
        if transition.to_node in node_map:
            outgoing_all[transition.from_node].add(transition.to_node)
            if transition.signal is not HookSignal.RETRY:
                nonretry_edges.append(
                    (transition.from_node, transition.to_node)
                )
        if (
            transition.signal is HookSignal.RETRY
            and hook_map[node_map[transition.from_node].hook_id].kind
            is not HookKind.GATE
        ):
            raise MiniLevError("only deterministic gate hooks may request retry")

    for node in policy.nodes:
        registration = hook_map[node.hook_id]
        expected_signals = set(registration.allowed_signals) | {HookSignal.HOLD}
        observed_signals = {
            signal
            for source, signal in transition_map
            if source == node.node_id
        }
        if observed_signals != expected_signals:
            raise MiniLevError(
                f"node {node.node_id} lacks an exhaustive transition map"
            )

    if not _is_dag(set(node_map), nonretry_edges):
        raise MiniLevError("non-retry flow edges must form a DAG")
    reachable = _reachable(policy.entry_node, outgoing_with_terminals)
    if set(node_map) - reachable or required - reachable:
        raise MiniLevError("all flow and required nodes must be reachable")
    for node in node_map:
        if not (_reachable(node, outgoing_with_terminals) & terminals):
            raise MiniLevError(f"node cannot reach a terminal: {node}")

    source_path = Path(__file__).resolve()
    material = {
        "schema": "constraintbox.mini-levos-policy.v1",
        "flow_id": policy.flow_id,
        "entry_node": policy.entry_node,
        "nodes": [
            {"node_id": node.node_id, "hook_id": node.hook_id}
            for node in policy.nodes
        ],
        "transitions": [
            {
                "from_node": transition.from_node,
                "signal": transition.signal.value,
                "to_node": transition.to_node,
            }
            for transition in policy.transitions
        ],
        "terminal_nodes": list(policy.terminal_nodes),
        "required_nodes": list(policy.required_nodes),
        "bounds": {
            "max_steps": policy.max_steps,
            "max_visits_per_node": policy.max_visits_per_node,
            "max_retries": policy.max_retries,
            "max_context_bytes": policy.max_context_bytes,
            "max_event_bytes": policy.max_event_bytes,
            "max_receipt_bytes": policy.max_receipt_bytes,
        },
        "hooks": sorted(hook_material, key=lambda row: row["hook_id"]),
        "python_runtime_policy_sha256": python_runtime_policy_sha256(),
        "kernel_source_sha256": _sha256_file(source_path),
        "claim_ceiling": policy.claim_ceiling,
        "promotion_allowed": False,
    }
    if execution_lease_material is not None:
        material["execution_lease"] = execution_lease_material
    return material, hook_map, transition_map


def _validate_embedded_policy_material(
    policy: dict[str, Any],
) -> tuple[
    dict[str, int],
    dict[str, str],
    dict[str, str],
    dict[str, set[str]],
    dict[str, dict[str, Any]],
    dict[tuple[str, str], str],
    set[str],
    list[str],
    dict[str, Any] | None,
]:
    """Recheck construction invariants without trusting the receipt producer."""

    expected_policy_keys = {
        "schema",
        "flow_id",
        "entry_node",
        "nodes",
        "transitions",
        "terminal_nodes",
        "required_nodes",
        "bounds",
        "hooks",
        "python_runtime_policy_sha256",
        "kernel_source_sha256",
        "claim_ceiling",
        "promotion_allowed",
    }
    optional_policy_keys = {"execution_lease"}
    policy_keys = set(policy)
    if (
        policy_keys != expected_policy_keys
        and policy_keys != expected_policy_keys | optional_policy_keys
    ):
        raise MiniLevError("embedded policy keys mismatch")
    if policy.get("schema") != "constraintbox.mini-levos-policy.v1":
        raise MiniLevError("embedded policy schema mismatch")
    _safe_identifier(policy.get("flow_id"), "embedded policy flow_id")
    entry_node = _safe_identifier(
        policy.get("entry_node"),
        "embedded policy entry_node",
    )
    claim_ceiling = policy.get("claim_ceiling")
    if not isinstance(claim_ceiling, str) or not claim_ceiling:
        raise MiniLevError("embedded policy claim_ceiling must be non-empty")
    if policy.get("promotion_allowed") is not False:
        raise MiniLevError("embedded policy attempted promotion")
    if (
        policy.get("python_runtime_policy_sha256")
        != python_runtime_policy_sha256()
    ):
        raise MiniLevError("embedded policy Python binding mismatch")
    kernel_source_sha256 = _lower_sha256(
        policy.get("kernel_source_sha256"),
        "embedded policy kernel_source_sha256",
    )
    if kernel_source_sha256 != _sha256_file(Path(__file__).resolve()):
        raise MiniLevError("embedded policy kernel source digest mismatch")

    bounds = policy.get("bounds")
    expected_bound_keys = {
        "max_steps",
        "max_visits_per_node",
        "max_retries",
        "max_context_bytes",
        "max_event_bytes",
        "max_receipt_bytes",
    }
    if not isinstance(bounds, dict) or set(bounds) != expected_bound_keys:
        raise MiniLevError("embedded policy bounds keys mismatch")
    checked_bounds: dict[str, int] = {}
    for key in expected_bound_keys - {"max_retries"}:
        checked_bounds[key] = _positive_int(
            bounds[key],
            f"embedded policy {key}",
        )
    checked_bounds["max_retries"] = _nonnegative_int(
        bounds["max_retries"],
        "embedded policy max_retries",
    )
    hard_bounds = (
        (checked_bounds["max_steps"], _HARD_MAX_STEPS, "max_steps"),
        (
            checked_bounds["max_visits_per_node"],
            _HARD_MAX_VISITS_PER_NODE,
            "max_visits_per_node",
        ),
        (checked_bounds["max_retries"], _HARD_MAX_RETRIES, "max_retries"),
        (
            checked_bounds["max_context_bytes"],
            _HARD_MAX_CONTEXT_BYTES,
            "max_context_bytes",
        ),
        (
            checked_bounds["max_event_bytes"],
            _HARD_MAX_EVENT_BYTES,
            "max_event_bytes",
        ),
        (
            checked_bounds["max_receipt_bytes"],
            _HARD_MAX_RECEIPT_BYTES,
            "max_receipt_bytes",
        ),
    )
    for observed, maximum, where in hard_bounds:
        if observed > maximum:
            raise MiniLevError(
                f"embedded policy {where} exceeds the kernel ceiling"
            )

    hooks = policy.get("hooks")
    if not isinstance(hooks, list) or not hooks:
        raise MiniLevError("embedded policy hooks are missing")
    expected_hook_keys = {
        "hook_id",
        "kind",
        "module",
        "qualname",
        "source_path",
        "source_sha256",
        "code_sha256",
        "allowed_signals",
        "allowed_update_keys",
        "max_output_bytes",
    }
    allowed_by_kind = {
        HookKind.PROPOSAL.value: {
            HookSignal.OBSERVED.value,
            HookSignal.PARKED.value,
        },
        HookKind.HOOK.value: {
            HookSignal.OBSERVED.value,
            HookSignal.PARKED.value,
        },
        HookKind.TOOL.value: {
            HookSignal.OBSERVED.value,
            HookSignal.PARKED.value,
        },
        HookKind.GATE.value: {
            HookSignal.PASS.value,
            HookSignal.RETRY.value,
            HookSignal.BLOCKED.value,
            HookSignal.PARKED.value,
        },
    }
    hook_kinds: dict[str, str] = {}
    hook_allowed_signals: dict[str, set[str]] = {}
    hook_update_keys: dict[str, set[str]] = {}
    hook_identities: dict[str, dict[str, Any]] = {}
    for hook in hooks:
        if not isinstance(hook, dict) or set(hook) != expected_hook_keys:
            raise MiniLevError("embedded policy hook is malformed")
        hook_id = _safe_identifier(
            hook.get("hook_id"),
            "embedded policy hook_id",
        )
        if hook_id in hook_kinds:
            raise MiniLevError("embedded policy hook is duplicated")
        kind = hook.get("kind")
        if kind not in allowed_by_kind:
            raise MiniLevError("embedded policy hook kind is invalid")
        module = hook.get("module")
        qualname = hook.get("qualname")
        source_path = hook.get("source_path")
        if (
            not isinstance(module, str)
            or not module
            or not isinstance(qualname, str)
            or not qualname
            or "<locals>" in qualname
            or not isinstance(source_path, str)
            or not source_path
            or not Path(source_path).is_absolute()
        ):
            raise MiniLevError("embedded policy hook identity is invalid")
        _lower_sha256(
            hook.get("source_sha256"),
            "embedded policy hook source_sha256",
        )
        _lower_sha256(
            hook.get("code_sha256"),
            "embedded policy hook code_sha256",
        )
        max_output_bytes = _positive_int(
            hook.get("max_output_bytes"),
            "embedded policy hook max_output_bytes",
        )
        if max_output_bytes > _HARD_MAX_HOOK_OUTPUT_BYTES:
            raise MiniLevError(
                "embedded policy hook max_output_bytes exceeds the kernel ceiling"
            )
        allowed_signals = hook.get("allowed_signals")
        if (
            not isinstance(allowed_signals, list)
            or not allowed_signals
            or any(not isinstance(signal, str) for signal in allowed_signals)
            or len(set(allowed_signals)) != len(allowed_signals)
            or not set(allowed_signals).issubset(allowed_by_kind[kind])
        ):
            raise MiniLevError("embedded policy hook signals are invalid")
        allowed_update_keys = hook.get("allowed_update_keys")
        if (
            not isinstance(allowed_update_keys, list)
            or len(set(allowed_update_keys)) != len(allowed_update_keys)
            or any(
                not isinstance(key, str)
                or not key
                or _normalized_key(key) in _AUTHORITY_KEYS
                for key in allowed_update_keys
            )
        ):
            raise MiniLevError("embedded policy hook update keys are invalid")
        hook_kinds[hook_id] = kind
        hook_allowed_signals[hook_id] = set(allowed_signals)
        hook_update_keys[hook_id] = set(allowed_update_keys)
        hook_identities[hook_id] = {
            "source_sha256": hook["source_sha256"],
            "code_sha256": hook["code_sha256"],
        }

    nodes = policy.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise MiniLevError("embedded policy nodes are missing")
    node_hooks: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {
            "node_id",
            "hook_id",
        }:
            raise MiniLevError("embedded policy node is malformed")
        node_id = _safe_identifier(
            node.get("node_id"),
            "embedded policy node_id",
        )
        hook_id = _safe_identifier(
            node.get("hook_id"),
            "embedded policy node hook_id",
        )
        if node_id in node_hooks:
            raise MiniLevError("embedded policy node is duplicated")
        if hook_id not in hook_kinds:
            raise MiniLevError("embedded policy node uses an unknown hook")
        node_hooks[node_id] = hook_id
    if set(node_hooks.values()) != set(hook_kinds):
        raise MiniLevError("embedded policy node-hook binding mismatch")
    if entry_node not in node_hooks:
        raise MiniLevError("embedded policy entry node is not registered")
    execution_lease_requirement = _execution_lease_requirement_from_material(
        policy.get("execution_lease"),
        node_hooks=node_hooks,
    )

    terminals = policy.get("terminal_nodes")
    if not isinstance(terminals, list):
        raise MiniLevError("embedded policy terminals are malformed")
    terminal_set = set(terminals)
    if (
        not terminal_set
        or len(terminal_set) != len(terminals)
        or any(not isinstance(terminal, str) for terminal in terminals)
        or not terminal_set.issubset(_TERMINALS)
        or terminal_set & set(node_hooks)
    ):
        raise MiniLevError("embedded policy terminals are malformed")
    required_nodes = policy.get("required_nodes")
    if (
        not isinstance(required_nodes, list)
        or any(not isinstance(node, str) for node in required_nodes)
        or len(set(required_nodes)) != len(required_nodes)
        or not set(required_nodes).issubset(node_hooks)
    ):
        raise MiniLevError("embedded policy required nodes are malformed")

    transitions = policy.get("transitions")
    if not isinstance(transitions, list):
        raise MiniLevError("embedded policy transitions are malformed")
    transition_map: dict[tuple[str, str], str] = {}
    outgoing_all: dict[str, set[str]] = {
        node: set() for node in node_hooks
    }
    outgoing_with_terminals: dict[str, set[str]] = {
        node: set() for node in (*node_hooks, *terminal_set)
    }
    nonretry_edges: list[tuple[str, str]] = []
    for transition in transitions:
        if not isinstance(transition, dict) or set(transition) != {
            "from_node",
            "signal",
            "to_node",
        }:
            raise MiniLevError("embedded policy transition is malformed")
        source = transition.get("from_node")
        signal = transition.get("signal")
        target = transition.get("to_node")
        if source not in node_hooks:
            raise MiniLevError("embedded policy transition source is invalid")
        if signal not in {item.value for item in HookSignal}:
            raise MiniLevError("embedded policy transition signal is invalid")
        if target not in set(node_hooks) | terminal_set:
            raise MiniLevError("embedded policy transition target is invalid")
        key = (source, signal)
        if key in transition_map:
            raise MiniLevError("embedded policy transition is duplicated")
        transition_map[key] = target
        outgoing_with_terminals[source].add(target)
        if signal in {
            HookSignal.BLOCKED.value,
            HookSignal.PARKED.value,
            HookSignal.HOLD.value,
        } and target != signal:
            raise MiniLevError(
                f"embedded policy {signal} must map to its matching terminal"
            )
        source_kind = hook_kinds[node_hooks[source]]
        if signal == HookSignal.RETRY.value:
            if source_kind != HookKind.GATE.value:
                raise MiniLevError(
                    "embedded policy RETRY may originate only from a gate"
                )
            if target not in node_hooks:
                raise MiniLevError(
                    "embedded policy RETRY must map to a bounded flow node"
                )
        if target in _POSITIVE_TERMINALS and (
            signal != HookSignal.PASS.value
            or source_kind != HookKind.GATE.value
        ):
            raise MiniLevError(
                "embedded policy positive terminals require a gate PASS"
            )
        if target in node_hooks:
            outgoing_all[source].add(target)
            if signal != HookSignal.RETRY.value:
                nonretry_edges.append((source, target))

    for node_id, hook_id in node_hooks.items():
        expected_signals = hook_allowed_signals[hook_id] | {
            HookSignal.HOLD.value
        }
        observed_signals = {
            signal
            for source, signal in transition_map
            if source == node_id
        }
        if observed_signals != expected_signals:
            raise MiniLevError(
                f"embedded policy node {node_id} lacks exhaustive transitions"
            )
    if not _is_dag(set(node_hooks), nonretry_edges):
        raise MiniLevError("embedded policy non-retry edges must form a DAG")
    reachable = _reachable(entry_node, outgoing_with_terminals)
    if set(node_hooks) - reachable or set(required_nodes) - reachable:
        raise MiniLevError("embedded policy flow nodes are not fully reachable")
    for node_id in node_hooks:
        if not (_reachable(node_id, outgoing_with_terminals) & terminal_set):
            raise MiniLevError(
                f"embedded policy node cannot reach a terminal: {node_id}"
            )

    return (
        checked_bounds,
        node_hooks,
        hook_kinds,
        hook_update_keys,
        hook_identities,
        transition_map,
        terminal_set,
        required_nodes,
        execution_lease_requirement,
    )


def _minimal_hold_result(
    reason: str,
    detail: str | None = None,
) -> HookResult:
    observation: dict[str, Any] = {"controller_reason": reason}
    if detail:
        observation["detail"] = detail[:1024]
    return HookResult(HookSignal.HOLD, observation, {})


def _event_record(
    *,
    run_id: str,
    policy_sha256: str,
    runtime_identity_sha256: str,
    sequence: int,
    node: FlowNode,
    registration: HookRegistration,
    visit: int,
    input_sha256: str,
    output_sha256: str,
    hook_reported_signal: str | None,
    hook_observation: dict[str, Any] | None,
    applied_context_updates: dict[str, Any],
    controller_output: dict[str, Any],
    controller_accepted_signal: HookSignal,
    signal: HookSignal,
    next_node: str,
    context_sha256: str,
    controller_reason: str | None,
    execution_lease: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema": EVENT_SCHEMA,
        "run_id": run_id,
        "policy_sha256": policy_sha256,
        "runtime_identity_sha256": runtime_identity_sha256,
        "sequence": sequence,
        "node_id": node.node_id,
        "node_kind": registration.kind.value,
        "hook_id": registration.hook_id,
        "visit": visit,
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "hook_reported_signal": hook_reported_signal,
        "hook_observation": hook_observation,
        "applied_context_updates": applied_context_updates,
        "controller_output": controller_output,
        "controller_accepted_signal": controller_accepted_signal.value,
        "typed_signal": signal.value,
        "controller_selected_next": next_node,
        "context_sha256": context_sha256,
        "controller_reason": controller_reason,
        "execution_lease": execution_lease,
    }


def _valid_lease_verdict_material(
    value: object,
    *,
    expected_record_sha256: str,
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "status",
        "reason",
        "record_sha256",
    }:
        return False
    return (
        value.get("status") == VerificationStatus.VALID.value
        and isinstance(value.get("reason"), str)
        and value.get("record_sha256") == expected_record_sha256
    )


def _validate_lease_release_record(
    value: object,
    *,
    binding: ExecutionLeaseBinding,
    acquire_record: dict[str, Any],
    expected_clock_id: str,
    expected_cause: str,
) -> bool:
    if not isinstance(value, dict):
        return False
    record = validate_execution_lease_receipt(value)
    return (
        record.get("event") == "RELEASED"
        and record.get("status") == "RELEASED"
        and record.get("binding") == binding.as_dict()
        and record.get("binding_sha256") == binding.sha256
        and record.get("clock_id") == expected_clock_id
        and record.get("release_cause") == expected_cause
        and record.get("previous_record_sha256")
        == acquire_record.get("record_sha256")
        and record.get("generation") == acquire_record.get("generation", -1) + 1
        and record.get("nonce_sha256") is None
    )


def _verify_execution_lease_audit(
    audit: object,
    *,
    requirement: dict[str, Any],
    run_id: str,
    flow_id: str,
    policy_sha256: str,
    runtime_identity_sha256: str,
    node_id: str,
    hook_id: str,
    visit: int,
    input_sha256: str,
    hook_identity: dict[str, Any],
    typed_signal: str,
    controller_reason: object,
) -> tuple[bool, str, bool]:
    """Validate one retained public lease lifecycle from a ledger event."""

    if not isinstance(audit, dict):
        return False, "execution lease audit is missing", False
    expected_keys = {
        "schema",
        "requirement_sha256",
        "binding",
        "binding_sha256",
        "slot_sha256",
        "clock_source",
        "clock_id",
        "acquire_record",
        "pre_hook_verdict",
        "handler_started",
        "handler_completed",
        "post_hook_verdict",
        "release_cause",
        "release_record",
        "release_status",
        "failure_stage",
        "failure_detail",
    }
    if set(audit) != expected_keys:
        return False, "execution lease audit keys mismatch", False
    if audit.get("schema") != EXECUTION_LEASE_HOOK_AUDIT_SCHEMA:
        return False, "execution lease audit schema mismatch", False
    requirement_object = _execution_lease_requirement_from_material(
        requirement,
        node_hooks={node_id: hook_id},
    )
    if requirement_object is None:
        return False, "execution lease requirement is absent", False
    requirement_sha256 = _SHA256(canonical_json(requirement_object)).hexdigest()
    if audit.get("requirement_sha256") != requirement_sha256:
        return False, "execution lease requirement digest mismatch", False
    if (
        audit.get("slot_sha256") != requirement_object["slot_sha256"]
        or audit.get("clock_source") != requirement_object["clock_source"]
        or audit.get("clock_id") != requirement_object["clock_id"]
    ):
        return False, "execution lease audit policy binding mismatch", False
    binding = ExecutionLeaseBinding.from_dict(audit.get("binding"))
    if audit.get("binding_sha256") != binding.sha256:
        return False, "execution lease binding digest mismatch", False
    expected_instruction_sha256 = _execution_lease_instruction_sha256_from_material(
        flow_id=flow_id,
        node_id=node_id,
        hook_id=hook_id,
        hook_source_sha256=hook_identity.get("source_sha256"),
        hook_code_sha256=hook_identity.get("code_sha256"),
        input_sha256=input_sha256,
    )
    if binding.as_dict() != {
        "owner_id": requirement_object["owner_id"],
        "run_id": run_id,
        "node_id": node_id,
        "visit": visit,
        "slot_sha256": requirement_object["slot_sha256"],
        "flow_sha256": _execution_lease_flow_sha256(flow_id),
        "policy_sha256": policy_sha256,
        "runtime_sha256": runtime_identity_sha256,
        "instruction_sha256": expected_instruction_sha256,
    }:
        return False, "execution lease binding fields mismatch", False
    clock_id = audit.get("clock_id")
    if not isinstance(clock_id, str):
        return False, "execution lease clock id is missing", False
    _safe_identifier(clock_id, "execution lease audit clock_id")
    if (
        not isinstance(audit.get("handler_started"), bool)
        or not isinstance(audit.get("handler_completed"), bool)
        or audit.get("release_status")
        not in {"NOT_ACQUIRED", "RELEASED", "RELEASE_FAILED"}
    ):
        return False, "execution lease audit lifecycle fields are malformed", False
    failure_stage = audit.get("failure_stage")
    if failure_stage not in {
        None,
        "acquire",
        "pre_hook_verify",
        "handler",
        "post_hook_verify",
        "release",
    }:
        return False, "execution lease audit failure stage is invalid", False
    failure_detail = audit.get("failure_detail")
    if failure_stage is None:
        if failure_detail is not None:
            return False, "successful execution lease has failure detail", False
    elif not isinstance(failure_detail, str):
        return False, "failed execution lease has no failure detail", False

    acquire_record = audit.get("acquire_record")
    if failure_stage == "acquire":
        if (
            acquire_record is not None
            or audit.get("pre_hook_verdict") is not None
            or audit.get("post_hook_verdict") is not None
            or audit.get("release_record") is not None
            or audit.get("release_cause") is not None
            or audit.get("release_status") != "NOT_ACQUIRED"
            or audit.get("handler_started") is not False
            or audit.get("handler_completed") is not False
        ):
            return False, "acquire failure audit is inconsistent", False
        if (
            typed_signal != HookSignal.HOLD.value
            or controller_reason != "execution_lease_acquire"
        ):
            return False, "execution lease acquire failure did not fail closed", False
        return True, "execution lease acquire failure failed closed", False
    else:
        if not isinstance(acquire_record, dict):
            return False, "execution lease acquire record is missing", False
        acquire_record = validate_execution_lease_receipt(acquire_record)
        if (
            acquire_record.get("event")
            not in {"ACQUIRED", "ACQUIRED_AFTER_EXPIRY", "ACQUIRED_AFTER_RELEASE"}
            or acquire_record.get("status") != "ACTIVE"
            or acquire_record.get("binding") != binding.as_dict()
            or acquire_record.get("binding_sha256") != binding.sha256
            or acquire_record.get("clock_id") != clock_id
            or acquire_record.get("ttl_ns") != requirement_object["ttl_ns"]
        ):
            return False, "execution lease acquire record binding mismatch", False
        if failure_stage in {"handler", "post_hook_verify", "release", None} and not _valid_lease_verdict_material(
            audit.get("pre_hook_verdict"),
            expected_record_sha256=acquire_record["record_sha256"],
        ):
            return False, "execution lease pre-hook verification mismatch", False

    if failure_stage is None:
        if (
            audit.get("handler_started") is not True
            or audit.get("handler_completed") is not True
            or not _valid_lease_verdict_material(
                audit.get("pre_hook_verdict"),
                expected_record_sha256=acquire_record["record_sha256"],
            )
            or not _valid_lease_verdict_material(
                audit.get("post_hook_verdict"),
                expected_record_sha256=acquire_record["record_sha256"],
            )
            or audit.get("release_cause") != ReleaseCause.COMPLETED.value
            or audit.get("release_status") != "RELEASED"
            or not _validate_lease_release_record(
                audit.get("release_record"),
                binding=binding,
                acquire_record=acquire_record,
                expected_clock_id=clock_id,
                expected_cause=ReleaseCause.COMPLETED.value,
            )
        ):
            return False, "successful execution lease lifecycle mismatch", False
        return True, "execution lease lifecycle matches", True

    expected_reason = "execution_lease_" + failure_stage
    if typed_signal != HookSignal.HOLD.value or controller_reason != expected_reason:
        return False, "execution lease failure did not fail closed", False
    if failure_stage == "handler" and (
        audit.get("handler_started") is not True
        or audit.get("handler_completed") is not False
    ):
        return False, "execution lease handler failure is inconsistent", False
    if failure_stage in {"post_hook_verify", "release"} and (
        audit.get("handler_started") is not True
        or audit.get("handler_completed") is not True
    ):
        return False, "execution lease post-handler failure is inconsistent", False
    if failure_stage == "release" and not _valid_lease_verdict_material(
        audit.get("post_hook_verdict"),
        expected_record_sha256=acquire_record["record_sha256"],
    ):
        return False, "execution lease release failure lacks valid post-check", False
    if audit.get("release_status") == "RELEASED":
        if (
            audit.get("release_cause") != ReleaseCause.FAILED.value
            or not _validate_lease_release_record(
                audit.get("release_record"),
                binding=binding,
                acquire_record=acquire_record,
                expected_clock_id=clock_id,
                expected_cause=ReleaseCause.FAILED.value,
            )
        ):
            return False, "execution lease failed release record mismatch", False
    elif audit.get("release_status") == "RELEASE_FAILED":
        if audit.get("release_record") is not None:
            return False, "execution lease failed release retained a record", False
    else:
        return False, "execution lease failed lifecycle omitted release state", False
    return True, "execution lease failure failed closed", False


class MiniLevRuntime:
    """Execute one frozen flow with registered Python hooks and finite budgets."""

    def __init__(
        self,
        policy: FlowPolicy,
        registrations: tuple[HookRegistration, ...],
        *,
        run_id: str,
        ledger_path: Path,
        execution_lease_guard: ExecutionLeaseGuard | None = None,
    ):
        self.policy = policy
        self.run_id = _safe_identifier(run_id, "run_id")
        self.ledger_path = Path(ledger_path).expanduser().resolve()
        if self.ledger_path.exists() or self.ledger_path.with_name(
            self.ledger_path.name + ".head"
        ).exists():
            raise MiniLevError("mini-LevOS ledger path already exists")
        (
            self._policy_material,
            self._hook_map,
            self._transition_map,
        ) = _build_policy_material(policy, registrations)
        if policy.execution_lease is None:
            if execution_lease_guard is not None:
                raise MiniLevError("execution lease guard supplied without a policy requirement")
        elif (
            type(execution_lease_guard) is not ExecutionLeaseGuard
            or execution_lease_guard.requirement != policy.execution_lease
        ):
            raise MiniLevError("execution lease policy requires its matching guard")
        self._execution_lease_guard = execution_lease_guard
        self._execution_lease_requirement = policy.execution_lease
        self.policy_sha256 = _SHA256(
            canonical_json(self._policy_material)
        ).hexdigest()
        self._node_map = {node.node_id: node for node in policy.nodes}
        self._retained_head_sha256: str | None = None
        self._receipt_sha256: str | None = None

    @property
    def retained_head_sha256(self) -> str:
        if self._retained_head_sha256 is None:
            raise MiniLevError("flow has not retained a ledger head")
        return self._retained_head_sha256

    @property
    def receipt_sha256(self) -> str:
        if self._receipt_sha256 is None:
            raise MiniLevError("flow has not emitted a receipt digest")
        return self._receipt_sha256

    def _reserve_ledger(self) -> HashChainLedger:
        """Atomically claim this run's exact local ledger path."""

        ledger = HashChainLedger(self.ledger_path)
        try:
            ledger.path.parent.mkdir(parents=True, exist_ok=True)
            with ledger.path.open("x", encoding="utf-8") as stream:
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise MiniLevError("mini-LevOS ledger path is already reserved") from exc
        except OSError as exc:
            raise MiniLevError(f"mini-LevOS ledger reservation failed: {exc}") from exc
        try:
            with ledger.head_path.open("x", encoding="ascii") as stream:
                stream.write(GENESIS + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except (FileExistsError, OSError) as exc:
            try:
                ledger.path.unlink()
            except OSError:
                pass
            raise MiniLevError(
                f"mini-LevOS retained-head reservation failed: {exc}"
            ) from exc
        return ledger

    def run(self, initial_context: dict[str, Any]) -> dict[str, Any]:
        context = _canonical_object(initial_context, "initial_context")
        if CONTROLLER_METADATA_KEY in context:
            raise MiniLevError(
                "initial context contains reserved controller metadata"
            )
        initial_bytes = canonical_json(context)
        initial_context_record = parse_json_object(initial_bytes)
        if len(initial_bytes) > self.policy.max_context_bytes:
            raise MiniLevError("initial context exceeds the controller bound")
        try:
            runtime_before = capture_python_runtime()
        except PythonRuntimeError as exc:
            raise MiniLevError(
                f"Python runtime identity unavailable before flow: {exc}"
            ) from exc
        ledger = self._reserve_ledger()

        current = self.policy.entry_node
        visits = {node.node_id: 0 for node in self.policy.nodes}
        retries = 0
        event_hashes: list[str] = []
        completed_nodes: set[str] = set()
        leased_event_summaries: list[dict[str, Any]] = []
        terminal: str | None = None
        runtime_after = runtime_before

        for sequence in range(1, self.policy.max_steps + 1):
            node = self._node_map[current]
            registration = self._hook_map[node.hook_id]
            visits[current] += 1
            visit = visits[current]
            input_bytes = canonical_json(context)
            input_sha256 = _SHA256(input_bytes).hexdigest()
            controller_reason: str | None = None
            hook_reported_signal: str | None = None
            hook_observation: dict[str, Any] | None = None
            execution_lease_audit: dict[str, Any] | None = None
            applied_context_updates: dict[str, Any] = {}
            pending_context = context
            pending_context_updates: dict[str, Any] = {}

            if visit > self.policy.max_visits_per_node:
                result = _minimal_hold_result("node_visit_budget_exhausted")
                controller_reason = "node_visit_budget_exhausted"
            else:
                try:
                    _verify_hook_identity(registration)
                    handler_context = parse_json_object(input_bytes)
                    handler_context[CONTROLLER_METADATA_KEY] = {
                        "schema": CONTROLLER_METADATA_SCHEMA,
                        "run_id": self.run_id,
                        "policy_sha256": self.policy_sha256,
                        "node_id": node.node_id,
                        "hook_id": registration.hook_id,
                        "hook_kind": registration.kind.value,
                    }
                    if (
                        self._execution_lease_guard is not None
                        and node.node_id
                        == self._execution_lease_guard.requirement.node_id
                    ):
                        invocation = self._execution_lease_guard.execute(
                            run_id=self.run_id,
                            flow_id=self.policy.flow_id,
                            policy_sha256=self.policy_sha256,
                            runtime_identity_sha256=runtime_before["identity_sha256"],
                            node=node,
                            registration=registration,
                            visit=visit,
                            input_sha256=input_sha256,
                            handler_context=handler_context,
                        )
                        result = invocation.result
                        execution_lease_audit = invocation.audit
                        hook_reported_signal = invocation.hook_reported_signal
                        if invocation.controller_reason is not None:
                            controller_reason = invocation.controller_reason
                    else:
                        result = registration.handler(handler_context)
                        if isinstance(result, HookResult) and isinstance(
                            result.signal, HookSignal
                        ):
                            hook_reported_signal = result.signal.value
                except Exception as exc:
                    result = _minimal_hold_result(
                        "hook_execution_error",
                        f"{type(exc).__name__}: {exc}",
                    )
                    controller_reason = "hook_execution_error"

            if controller_reason is not None:
                # A controller-generated HOLD is already authoritative.  It
                # must not be mistaken for an unauthorized hook-emitted signal.
                pass
            elif not isinstance(result, HookResult):
                result = _minimal_hold_result("hook_result_type_invalid")
                controller_reason = "hook_result_type_invalid"
            elif (
                not isinstance(result.signal, HookSignal)
                or result.signal not in registration.allowed_signals
            ):
                result = _minimal_hold_result("hook_signal_not_authorized")
                controller_reason = "hook_signal_not_authorized"
            else:
                try:
                    observation = _canonical_object(
                        result.observation,
                        "hook observation",
                    )
                    updates = _canonical_object(
                        result.context_updates,
                        "hook context_updates",
                    )
                except MiniLevError as exc:
                    result = _minimal_hold_result(
                        "hook_output_not_canonical",
                        str(exc),
                    )
                    controller_reason = "hook_output_not_canonical"
                else:
                    hook_observation = observation
                    authority_paths = _authority_paths(observation) + _authority_paths(
                        updates
                    )
                    if authority_paths:
                        result = _minimal_hold_result(
                            "hook_attempted_controller_authority",
                            ",".join(authority_paths),
                        )
                        controller_reason = "hook_attempted_controller_authority"
                    elif not set(updates).issubset(
                        registration.allowed_update_keys
                    ):
                        result = _minimal_hold_result(
                            "hook_update_key_not_authorized"
                        )
                        controller_reason = "hook_update_key_not_authorized"
                    else:
                        output_probe = canonical_json(
                            {
                                "signal": result.signal.value,
                                "observation": observation,
                                "context_updates": updates,
                            }
                        )
                        if len(output_probe) > registration.max_output_bytes:
                            result = _minimal_hold_result(
                                "hook_output_exceeds_bound"
                            )
                            controller_reason = "hook_output_exceeds_bound"
                        else:
                            updated_context = {**context, **updates}
                            updated_bytes = canonical_json(updated_context)
                            if len(updated_bytes) > self.policy.max_context_bytes:
                                result = _minimal_hold_result(
                                    "context_exceeds_bound"
                                )
                                controller_reason = "context_exceeds_bound"
                            else:
                                pending_context = parse_json_object(updated_bytes)
                                pending_context_updates = updates

            signal = result.signal
            if signal is HookSignal.RETRY:
                if retries >= self.policy.max_retries:
                    result = _minimal_hold_result("retry_budget_exhausted")
                    signal = HookSignal.HOLD
                    controller_reason = "retry_budget_exhausted"

            if sequence == self.policy.max_steps:
                proposed_target = self._transition_map[(current, signal)]
                if proposed_target not in self.policy.terminal_nodes:
                    result = _minimal_hold_result("step_budget_exhausted")
                    signal = HookSignal.HOLD
                    controller_reason = "step_budget_exhausted"

            try:
                _verify_hook_identity(registration)
                runtime_after = capture_python_runtime()
                verify_python_runtime_stable(runtime_before, runtime_after)
            except (MiniLevError, PythonRuntimeError) as exc:
                result = _minimal_hold_result(
                    "runtime_or_hook_identity_changed",
                    str(exc),
                )
                signal = HookSignal.HOLD
                controller_reason = "runtime_or_hook_identity_changed"

            target = self._transition_map[(current, signal)]
            controller_accepted_signal = signal
            node_completed = (
                controller_accepted_signal is HookSignal.PASS
                if registration.kind is HookKind.GATE
                else controller_accepted_signal is HookSignal.OBSERVED
            )
            if node_completed:
                completed_nodes.add(current)
            if target in _POSITIVE_TERMINALS:
                missing_required = sorted(
                    required
                    for required in self.policy.required_nodes
                    if required not in completed_nodes
                )
                if missing_required:
                    result = _minimal_hold_result(
                        "required_nodes_not_executed",
                        ",".join(missing_required),
                    )
                    signal = HookSignal.HOLD
                    controller_reason = "required_nodes_not_executed"
                    target = self._transition_map[(current, signal)]
            if signal is HookSignal.RETRY:
                # Count only a retry transition that is actually persisted and
                # taken.  A proposed RETRY converted to HOLD by a controller
                # budget or identity check is not a retry.
                retries += 1
            if controller_reason is None:
                context = pending_context
                applied_context_updates = pending_context_updates
            controller_output = {
                "signal": signal.value,
                "observation": result.observation,
                "context_updates": result.context_updates,
            }
            output_bytes = canonical_json(controller_output)
            event = _event_record(
                run_id=self.run_id,
                policy_sha256=self.policy_sha256,
                runtime_identity_sha256=runtime_after["identity_sha256"],
                sequence=sequence,
                node=node,
                registration=registration,
                visit=visit,
                input_sha256=input_sha256,
                output_sha256=_SHA256(output_bytes).hexdigest(),
                hook_reported_signal=hook_reported_signal,
                hook_observation=hook_observation,
                applied_context_updates=applied_context_updates,
                controller_output=controller_output,
                controller_accepted_signal=controller_accepted_signal,
                signal=signal,
                next_node=target,
                context_sha256=_SHA256(canonical_json(context)).hexdigest(),
                controller_reason=controller_reason,
                execution_lease=execution_lease_audit,
            )
            if len(canonical_json(event)) > self.policy.max_event_bytes:
                raise MiniLevError("semantic event exceeds the controller bound")
            try:
                event_hashes.append(ledger.append(event))
            except (OSError, ValueError) as exc:
                raise MiniLevError(
                    f"semantic event persistence failed: {exc}"
                ) from exc
            if execution_lease_audit is not None:
                leased_event_summaries.append(
                    {
                        "sequence": sequence,
                        "binding_sha256": execution_lease_audit["binding_sha256"],
                        "release_status": execution_lease_audit["release_status"],
                        "failure_stage": execution_lease_audit["failure_stage"],
                    }
                )

            if target in self.policy.terminal_nodes:
                terminal = target
                break
            current = target

        if terminal is None:
            raise MiniLevError("flow exhausted without a terminal transition")
        ledger_valid, ledger_reason = ledger.verify()
        if not ledger_valid:
            raise MiniLevError(f"semantic ledger verification failed: {ledger_reason}")
        head = ledger.head_path.read_text(encoding="ascii").strip()
        receipt = {
            "schema": SCHEMA,
            "run_id": self.run_id,
            "flow_id": self.policy.flow_id,
            "policy_sha256": self.policy_sha256,
            "policy": self._policy_material,
            "terminal": terminal,
            "steps": len(event_hashes),
            "retries": retries,
            "visits": visits,
            "completed_nodes": sorted(completed_nodes),
            "initial_context": initial_context_record,
            "initial_context_sha256": _SHA256(initial_bytes).hexdigest(),
            "final_context": context,
            "final_context_sha256": _SHA256(canonical_json(context)).hexdigest(),
            "event_hashes": event_hashes,
            "ledger": {
                "path": str(ledger.path),
                "head_path": str(ledger.head_path),
                "retained_head_sha256": head,
                "verification": ledger_reason,
            },
            "python_runtime": {
                "before": runtime_before,
                "after": runtime_after,
                "stable": True,
            },
            "claim_ceiling": self.policy.claim_ceiling,
            "promotion_allowed": False,
        }
        if self._execution_lease_requirement is not None:
            receipt["execution_lease"] = {
                "schema": "constraintbox.execution-lease-flow-summary.v1",
                "requirement": self._execution_lease_requirement.as_dict(),
                "requirement_sha256": self._execution_lease_requirement.sha256,
                "protected_event_sequences": [
                    row["sequence"] for row in leased_event_summaries
                ],
                "all_protected_events_released": bool(leased_event_summaries)
                and all(
                    row["release_status"] == "RELEASED"
                    and row["failure_stage"] is None
                    for row in leased_event_summaries
                ),
            }
        receipt_with_digest = {
            **receipt,
            "receipt_sha256": _SHA256(canonical_json(receipt)).hexdigest(),
        }
        if len(canonical_json(receipt_with_digest)) > self.policy.max_receipt_bytes:
            raise MiniLevError("flow receipt exceeds the controller bound")
        self._retained_head_sha256 = head
        self._receipt_sha256 = receipt_with_digest["receipt_sha256"]
        valid, reason = verify_flow_receipt(
            receipt_with_digest,
            expected_run_id=self.run_id,
            expected_policy_sha256=self.policy_sha256,
            expected_ledger_path=self.ledger_path,
            expected_retained_head_sha256=self._retained_head_sha256,
            expected_receipt_sha256=self._receipt_sha256,
        )
        if not valid:
            raise MiniLevError(f"flow self-verification failed: {reason}")
        return receipt_with_digest


def verify_flow_receipt(
    receipt: dict[str, Any],
    *,
    expected_run_id: str,
    expected_policy_sha256: str,
    expected_ledger_path: Path,
    expected_retained_head_sha256: str,
    expected_receipt_sha256: str,
) -> tuple[bool, str]:
    """Verify a current flow receipt against its expected retained ledger."""

    try:
        body = _canonical_object(receipt, "flow receipt")
        expected_receipt_keys = {
            "schema",
            "run_id",
            "flow_id",
            "policy_sha256",
            "policy",
            "terminal",
            "steps",
            "retries",
            "visits",
            "completed_nodes",
            "initial_context",
            "initial_context_sha256",
            "final_context",
            "final_context_sha256",
            "event_hashes",
            "ledger",
            "python_runtime",
            "claim_ceiling",
            "promotion_allowed",
            "receipt_sha256",
        }
        optional_receipt_key = "execution_lease"
        receipt_keys = set(body)
        if (
            receipt_keys != expected_receipt_keys
            and receipt_keys != expected_receipt_keys | {optional_receipt_key}
        ):
            return False, "receipt keys mismatch"
        digest_body = dict(body)
        supplied_digest = digest_body.pop("receipt_sha256")
        if supplied_digest != expected_receipt_sha256:
            return False, "receipt root binding mismatch"
        if supplied_digest != _SHA256(canonical_json(digest_body)).hexdigest():
            return False, "receipt digest mismatch"
        if body.get("schema") != SCHEMA:
            return False, "receipt schema mismatch"
        if body.get("run_id") != expected_run_id:
            return False, "run binding mismatch"
        if body.get("policy_sha256") != expected_policy_sha256:
            return False, "policy binding mismatch"
        if body.get("promotion_allowed") is not False:
            return False, "receipt attempted promotion"
        if body.get("terminal") not in _TERMINALS:
            return False, "terminal is invalid"
        policy = body.get("policy")
        if not isinstance(policy, dict):
            return False, "policy material missing"
        if _SHA256(canonical_json(policy)).hexdigest() != expected_policy_sha256:
            return False, "policy material digest mismatch"
        if policy.get("flow_id") != body.get("flow_id"):
            return False, "flow binding mismatch"
        (
            bounds,
            node_hooks,
            hook_kinds,
            hook_update_keys,
            hook_identities,
            transition_map,
            terminal_set,
            required_nodes,
            execution_lease_requirement,
        ) = _validate_embedded_policy_material(policy)
        if execution_lease_requirement is None:
            if optional_receipt_key in body:
                return False, "receipt has an unrequired execution lease summary"
        elif optional_receipt_key not in body:
            return False, "receipt is missing its execution lease summary"
        steps = _positive_int(body.get("steps"), "receipt steps")
        retries = _nonnegative_int(body.get("retries"), "receipt retries")
        if steps > bounds["max_steps"]:
            return False, "step bound exceeded"
        if retries > bounds["max_retries"]:
            return False, "retry bound exceeded"

        runtime = body.get("python_runtime")
        if (
            not isinstance(runtime, dict)
            or set(runtime) != {"before", "after", "stable"}
            or runtime.get("stable") is not True
        ):
            return False, "Python runtime was not stable"
        runtime_before = runtime.get("before")
        runtime_after = runtime.get("after")
        if not isinstance(runtime_before, dict) or not isinstance(
            runtime_after, dict
        ):
            return False, "Python runtime receipts are missing"
        if runtime_before != runtime_after:
            return False, "Python runtime receipts differ"
        runtime_digest = runtime_before.get("identity_sha256")
        runtime_body = dict(runtime_before)
        runtime_body.pop("identity_sha256", None)
        if runtime_digest != _SHA256(canonical_json(runtime_body)).hexdigest():
            return False, "Python runtime receipt digest mismatch"
        if (
            runtime_before.get("policy_sha256")
            != python_runtime_policy_sha256()
            or runtime_before.get("promotion_allowed") is not False
        ):
            return False, "Python runtime receipt policy mismatch"
        current_runtime = capture_python_runtime()
        verify_python_runtime_stable(runtime_before, current_runtime)

        ledger_body = body.get("ledger")
        if not isinstance(ledger_body, dict) or set(ledger_body) != {
            "path",
            "head_path",
            "retained_head_sha256",
            "verification",
        }:
            return False, "ledger binding missing"
        expected_path = Path(expected_ledger_path).expanduser().resolve()
        expected_head = _lower_sha256(
            expected_retained_head_sha256,
            "expected retained head",
        )
        if ledger_body.get("retained_head_sha256") != expected_head:
            return False, "ledger root binding mismatch"
        if Path(ledger_body["path"]).expanduser().resolve() != expected_path:
            return False, "ledger path binding mismatch"
        expected_head_path = expected_path.with_name(expected_path.name + ".head")
        if (
            Path(ledger_body["head_path"]).expanduser().resolve()
            != expected_head_path
        ):
            return False, "ledger head path binding mismatch"
        ledger = HashChainLedger(
            expected_path,
            expected_head_path,
        )
        valid, reason = ledger.verify()
        if not valid:
            return False, f"semantic ledger invalid: {reason}"
        retained_head = ledger.head_path.read_text(encoding="ascii").strip()
        if retained_head != expected_head:
            return False, "retained ledger head mismatch"
        rows = ledger.path.read_text(encoding="utf-8").splitlines()
        if len(rows) != steps:
            return False, "event count mismatch"
        event_hashes = body.get("event_hashes")
        if not isinstance(event_hashes, list) or len(event_hashes) != len(rows):
            return False, "event hash list mismatch"
        observed_visits = {node_id: 0 for node_id in node_hooks}
        observed_completed_nodes: set[str] = set()
        observed_retries = 0
        previous_next: str | None = None
        initial_context = body.get("initial_context")
        if not isinstance(initial_context, dict):
            return False, "initial context missing"
        if CONTROLLER_METADATA_KEY in initial_context:
            return False, "initial context contains reserved controller metadata"
        replay_context = _canonical_object(initial_context, "initial context")
        initial_context_sha256 = _SHA256(canonical_json(replay_context)).hexdigest()
        if initial_context_sha256 != body.get("initial_context_sha256"):
            return False, "initial context digest mismatch"
        expected_event_keys = {
            "schema",
            "run_id",
            "policy_sha256",
            "runtime_identity_sha256",
            "sequence",
            "node_id",
            "node_kind",
            "hook_id",
            "visit",
            "input_sha256",
            "output_sha256",
            "hook_reported_signal",
            "hook_observation",
            "applied_context_updates",
            "controller_output",
            "controller_accepted_signal",
            "typed_signal",
            "controller_selected_next",
            "context_sha256",
            "controller_reason",
            "execution_lease",
        }
        protected_lease_events: list[dict[str, Any]] = []
        for index, raw in enumerate(rows):
            row = parse_json_object(raw.encode("utf-8"))
            if set(row) != {"previous_sha256", "record", "line_sha256"}:
                return False, "ledger row keys mismatch"
            if row.get("line_sha256") != event_hashes[index]:
                return False, "event hash binding mismatch"
            event = row.get("record")
            if not isinstance(event, dict) or set(event) != expected_event_keys:
                return False, "event record missing"
            if event.get("schema") != EVENT_SCHEMA:
                return False, "event schema mismatch"
            if event.get("run_id") != expected_run_id:
                return False, "event run binding mismatch"
            if event.get("policy_sha256") != expected_policy_sha256:
                return False, "event policy binding mismatch"
            if event.get("sequence") != index + 1:
                return False, "event sequence mismatch"
            if event.get("runtime_identity_sha256") != runtime_digest:
                return False, "event runtime binding mismatch"
            node_id = event.get("node_id")
            if node_id not in node_hooks:
                return False, "event node is not in policy"
            if index == 0 and node_id != policy.get("entry_node"):
                return False, "event stream did not start at the entry node"
            if previous_next is not None and node_id != previous_next:
                return False, "event path skipped the selected transition"
            hook_id = node_hooks[node_id]
            if (
                event.get("hook_id") != hook_id
                or event.get("node_kind") != hook_kinds[hook_id]
            ):
                return False, "event hook binding mismatch"
            observed_visits[node_id] += 1
            if event.get("visit") != observed_visits[node_id]:
                return False, "event visit count mismatch"
            if observed_visits[node_id] > bounds["max_visits_per_node"] + 1:
                return False, "event visit bound exceeded"
            signal = event.get("typed_signal")
            accepted_signal = event.get("controller_accepted_signal")
            selected_next = event.get("controller_selected_next")
            if accepted_signal not in {
                item.value for item in HookSignal
            }:
                return False, "controller-accepted signal is invalid"
            for digest_field in (
                "input_sha256",
                "output_sha256",
                "context_sha256",
            ):
                _lower_sha256(
                    event.get(digest_field),
                    f"event {digest_field}",
                )
            if event.get("input_sha256") != _SHA256(
                canonical_json(replay_context)
            ).hexdigest():
                return False, "event context chain mismatch"
            execution_lease_audit = event.get("execution_lease")
            if execution_lease_requirement is None:
                if execution_lease_audit is not None:
                    return False, "event has an unrequired execution lease audit"
            elif node_id == execution_lease_requirement["node_id"]:
                valid_lease, lease_reason, released = _verify_execution_lease_audit(
                    execution_lease_audit,
                    requirement=execution_lease_requirement,
                    run_id=expected_run_id,
                    flow_id=body["flow_id"],
                    policy_sha256=expected_policy_sha256,
                    runtime_identity_sha256=runtime_digest,
                    node_id=node_id,
                    hook_id=hook_id,
                    visit=observed_visits[node_id],
                    input_sha256=event["input_sha256"],
                    hook_identity=hook_identities[hook_id],
                    typed_signal=event.get("typed_signal"),
                    controller_reason=event.get("controller_reason"),
                )
                if not valid_lease:
                    return False, lease_reason
                if not released and event.get("typed_signal") != HookSignal.HOLD.value:
                    return False, "unreleased execution lease selected a non-HOLD signal"
                protected_lease_events.append(
                    {
                        "sequence": event["sequence"],
                        "binding_sha256": execution_lease_audit["binding_sha256"],
                        "release_status": execution_lease_audit["release_status"],
                        "failure_stage": execution_lease_audit["failure_stage"],
                    }
                )
            elif execution_lease_audit is not None:
                return False, "event has an execution lease for the wrong node"
            hook_signal = event.get("hook_reported_signal")
            if hook_signal is not None and hook_signal not in {
                item.value for item in HookSignal
            }:
                return False, "hook-reported signal is invalid"
            hook_observation = event.get("hook_observation")
            if hook_observation is not None and not isinstance(
                hook_observation, dict
            ):
                return False, "hook observation is malformed"
            if isinstance(hook_observation, dict):
                _canonical_object(hook_observation, "event hook observation")
            applied_updates = event.get("applied_context_updates")
            if (
                not isinstance(applied_updates, dict)
                or not set(applied_updates).issubset(hook_update_keys[hook_id])
            ):
                return False, "event context updates are not authorized"
            applied_updates = _canonical_object(
                applied_updates,
                "event context updates",
            )
            replay_context = _canonical_object(
                {**replay_context, **applied_updates},
                "replayed context",
            )
            if event.get("context_sha256") != _SHA256(
                canonical_json(replay_context)
            ).hexdigest():
                return False, "event context result mismatch"
            controller_output = event.get("controller_output")
            if not isinstance(controller_output, dict) or set(
                controller_output
            ) != {"signal", "observation", "context_updates"}:
                return False, "controller output is malformed"
            controller_output = _canonical_object(
                controller_output,
                "event controller output",
            )
            if (
                controller_output.get("signal") != signal
                or event.get("output_sha256")
                != _SHA256(canonical_json(controller_output)).hexdigest()
            ):
                return False, "controller output binding mismatch"
            if transition_map.get((node_id, signal)) != selected_next:
                return False, "event transition differs from policy"
            if event.get("controller_reason") == "required_nodes_not_executed":
                if (
                    signal != HookSignal.HOLD.value
                    or accepted_signal != HookSignal.PASS.value
                    or hook_kinds[hook_id] != HookKind.GATE.value
                ):
                    return False, "required-node hold did not follow a gate PASS"
            elif accepted_signal != signal:
                return False, "accepted and persisted signals differ"
            if signal == HookSignal.RETRY.value:
                observed_retries += 1
            if (
                hook_kinds[hook_id] == HookKind.GATE.value
                and accepted_signal == HookSignal.PASS.value
            ) or (
                hook_kinds[hook_id] != HookKind.GATE.value
                and accepted_signal == HookSignal.OBSERVED.value
            ):
                observed_completed_nodes.add(node_id)
            if index < len(rows) - 1 and selected_next in terminal_set:
                return False, "event stream continued after a terminal transition"
            previous_next = (
                selected_next if selected_next in node_hooks else None
            )
        final_event = parse_json_object(rows[-1].encode("utf-8"))["record"]
        if final_event.get("controller_selected_next") != body.get("terminal"):
            return False, "terminal does not match final transition"
        if previous_next is not None:
            return False, "final event did not select a terminal"
        visits = body.get("visits")
        if visits != observed_visits:
            return False, "receipt visit counts mismatch"
        if retries != observed_retries:
            return False, "receipt retry count mismatch"
        if body.get("completed_nodes") != sorted(observed_completed_nodes):
            return False, "receipt completed-node set mismatch"
        final_context = body.get("final_context")
        if not isinstance(final_context, dict):
            return False, "final context missing"
        if CONTROLLER_METADATA_KEY in final_context:
            return False, "final context contains reserved controller metadata"
        if _canonical_object(final_context, "final context") != replay_context:
            return False, "final context differs from replay"
        final_context_sha256 = _SHA256(canonical_json(final_context)).hexdigest()
        if (
            final_context_sha256 != body.get("final_context_sha256")
            or final_context_sha256 != final_event.get("context_sha256")
        ):
            return False, "final context binding mismatch"
        if body.get("terminal") in _POSITIVE_TERMINALS and any(
            required not in observed_completed_nodes for required in required_nodes
        ):
            return False, "positive terminal did not discharge a required node"
        if execution_lease_requirement is not None:
            summary = body.get("execution_lease")
            expected_summary_keys = {
                "schema",
                "requirement",
                "requirement_sha256",
                "protected_event_sequences",
                "all_protected_events_released",
            }
            if not isinstance(summary, dict) or set(summary) != expected_summary_keys:
                return False, "execution lease summary is malformed"
            expected_requirement_sha256 = _SHA256(
                canonical_json(execution_lease_requirement)
            ).hexdigest()
            expected_all_released = bool(protected_lease_events) and all(
                row["release_status"] == "RELEASED"
                and row["failure_stage"] is None
                for row in protected_lease_events
            )
            if (
                summary.get("schema")
                != "constraintbox.execution-lease-flow-summary.v1"
                or summary.get("requirement") != execution_lease_requirement
                or summary.get("requirement_sha256")
                != expected_requirement_sha256
                or summary.get("protected_event_sequences")
                != [row["sequence"] for row in protected_lease_events]
                or summary.get("all_protected_events_released")
                is not expected_all_released
            ):
                return False, "execution lease summary does not match the ledger"
            if body.get("terminal") in _POSITIVE_TERMINALS and not expected_all_released:
                return False, "positive terminal lacks a released execution lease"
        if body.get("claim_ceiling") != policy.get("claim_ceiling"):
            return False, "claim ceiling binding mismatch"
    except (
        KeyError,
        OSError,
        IntakeError,
        MiniLevError,
        PythonRuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        return False, f"receipt verification error: {exc}"
    return True, "flow receipt and semantic ledger match"
