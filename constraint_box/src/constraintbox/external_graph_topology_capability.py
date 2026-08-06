"""Controller-owned graph/topology capability flow for ConstraintBox.

The profile is intentionally an external workload, not part of the CB kernel:
it checks whether a selected Python environment can really execute a small
shared finite-complex workload.  The CB controller owns the topology, graph
fixtures, API list, replay, severance controls, Mini-Lev transition, and
receipt validation.  An LLM has no route to select any of those values.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .graph_topology_worker import (
    EXACT_APIS,
    FAILURE_SCHEMA,
    REQUEST_SCHEMA as WORKER_REQUEST_SCHEMA,
    SEVERED_EXIT_CODE,
    SEVERED_PREFIX,
    WITNESS_SCHEMA,
    WORKER_ARGUMENT,
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


CAPABILITY_ID = "graph-topology-crosscheck-v1"
STEP_ID = "graph-topology-crosscheck-tool"
RECEIPT_SCHEMA = "constraintbox.external-graph-topology-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-graph-topology-capability-binding.v1"
FLOW_RESULT_SCHEMA = "constraintbox.external-graph-topology-capability-flow-result.v1"
FLOW_ID = "constraintbox.graph-topology-crosscheck-capability-flow.v1"
FLOW_RECEIPT_NAME = "graph_topology_crosscheck_flow_receipt.json"
FLOW_LEDGER_NAME = "graph_topology_crosscheck_flow_events.jsonl"
CAPABILITY_RECEIPT_NAME = "graph_topology_crosscheck_capability_receipt.json"
CACHE_ROOT_NAME = ".constraintbox-graph-topology-cache"
WORKER_TIMEOUT_SECONDS = 90.0
MAX_WORKER_STREAM_BYTES = 1_048_576
_ALLOWED_INITIALIZATION_STDERR = "Matplotlib is building the font cache; this may take a moment.\n"
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_HEX = re.compile(r"[0-9a-f]{64}")

CAPABILITY_CLAIM_CEILING = (
    "one controller-owned bounded finite-complex and connectivity workload that "
    "actually invokes GUDHI, TopoNetX, XGI, NetworkX, igraph, Rustworkx, "
    "PyTorch, and PyG under a selected local Python runtime, with independent "
    "replay and one API-severance control per named call; not complete graph or "
    "topology-engine readiness, not a full sim-estate integration, not CR truth, "
    "not scientific proof, not hostile-code containment, not release, and not "
    "canonical promotion"
)


class ExternalGraphTopologyCapabilityError(RuntimeError):
    """The bounded graph/topology capability could not be verified."""


class ExternalGraphTopologyCapabilityFlowError(ValueError):
    """The fixed graph/topology Mini-Lev flow could not complete."""


class _WorkerUnavailable(ExternalGraphTopologyCapabilityError):
    """The selected runtime cannot execute the fixed worker workload."""


@dataclass(frozen=True)
class GraphTopologyCapabilityBinding:
    """Controller-owned identity material for one fixed profile execution."""

    capability_id: str
    run_id: str
    flow_policy_sha256: str
    request_sha256: str
    step_id: str
    cache_root: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": BINDING_SCHEMA,
            "capability_id": self.capability_id,
            "run_id": self.run_id,
            "flow_policy_sha256": self.flow_policy_sha256,
            "request_sha256": self.request_sha256,
            "step_id": self.step_id,
            "cache_root": self.cache_root,
        }


def _sha256_file(path: Path) -> str:
    try:
        return _SHA256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExternalGraphTopologyCapabilityError(
            f"source is unavailable: {path.name}: {exc}"
        ) from exc


def _is_hex(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def _cache_root_from_text(value: object) -> Path:
    if not isinstance(value, str):
        raise ExternalGraphTopologyCapabilityError("binding cache root is invalid")
    path = Path(value)
    if not path.is_absolute() or path.name != CACHE_ROOT_NAME:
        raise ExternalGraphTopologyCapabilityError("binding cache root is invalid")
    resolved = path.resolve(strict=False)
    if str(path) != str(resolved):
        raise ExternalGraphTopologyCapabilityError("binding cache root is not normalized")
    return path


def validate_graph_topology_binding(
    binding: GraphTopologyCapabilityBinding,
) -> dict[str, str]:
    """Reject profile or runtime substitution before a tool call starts."""

    if type(binding) is not GraphTopologyCapabilityBinding:
        raise ExternalGraphTopologyCapabilityError("binding has the wrong type")
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalGraphTopologyCapabilityError("binding capability id mismatch")
    if binding.step_id != STEP_ID:
        raise ExternalGraphTopologyCapabilityError("binding step id mismatch")
    for key, value in (
        ("capability_id", binding.capability_id),
        ("run_id", binding.run_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalGraphTopologyCapabilityError(f"binding {key} is invalid")
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
    ):
        if not _is_hex(value):
            raise ExternalGraphTopologyCapabilityError(f"binding {key} is invalid")
    _cache_root_from_text(binding.cache_root)
    return binding.to_dict()


def graph_topology_binding_from_dict(value: object) -> GraphTopologyCapabilityBinding:
    expected = {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "cache_root",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ExternalGraphTopologyCapabilityError("binding has an unexpected shape")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalGraphTopologyCapabilityError("binding schema is invalid")
    if not all(isinstance(value[key], str) for key in expected):
        raise ExternalGraphTopologyCapabilityError("binding values must be strings")
    binding = GraphTopologyCapabilityBinding(
        capability_id=value["capability_id"],
        run_id=value["run_id"],
        flow_policy_sha256=value["flow_policy_sha256"],
        request_sha256=value["request_sha256"],
        step_id=value["step_id"],
        cache_root=value["cache_root"],
    )
    validate_graph_topology_binding(binding)
    return binding


def _worker_path() -> Path:
    path = Path(__file__).with_name("graph_topology_worker.py")
    if not path.is_file():
        raise ExternalGraphTopologyCapabilityError("graph/topology worker source is absent")
    return path.resolve()


def _runtime_identity() -> dict[str, object]:
    return {
        "implementation": sys.implementation.name,
        "version": list(sys.version_info[:3]),
        "executable": sys.executable,
    }


def _make_private_cache_root(run_root: Path) -> Path:
    cache_root = run_root / CACHE_ROOT_NAME
    try:
        cache_root.mkdir(mode=0o700)
        os.chmod(cache_root, 0o700)
        (cache_root / "matplotlib").mkdir(mode=0o700)
    except OSError as exc:
        raise ExternalGraphTopologyCapabilityError(
            f"could not create private worker cache: {exc}"
        ) from exc
    return cache_root


def _worker_environment(cache_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment["MPLCONFIGDIR"] = str(cache_root / "matplotlib")
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _decode_worker_json(stdout: bytes) -> dict[str, Any]:
    try:
        value = parse_json_object(stdout.rstrip(b"\n"))
    except IntakeError as exc:
        raise ExternalGraphTopologyCapabilityError(
            f"worker returned invalid JSON: {exc}"
        ) from exc
    return value


def _run_worker(
    *,
    binding: GraphTopologyCapabilityBinding,
    poison_api: str | None,
) -> dict[str, Any]:
    cache_root = _cache_root_from_text(binding.cache_root)
    worker_path = _worker_path()
    request = {
        "schema": WORKER_REQUEST_SCHEMA,
        "binding": binding.to_dict(),
        "poison_api": poison_api,
    }
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(worker_path), WORKER_ARGUMENT],
            input=canonical_json(request),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cache_root,
            env=_worker_environment(cache_root),
            timeout=WORKER_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _WorkerUnavailable(f"worker could not execute: {exc}") from exc
    if len(completed.stdout) + len(completed.stderr) > MAX_WORKER_STREAM_BYTES:
        raise ExternalGraphTopologyCapabilityError("worker stream exceeded the fixed limit")
    if poison_api is not None:
        expected_marker = f"{SEVERED_PREFIX}{poison_api}".encode("utf-8")
        if (
            completed.returncode != SEVERED_EXIT_CODE
            or completed.stdout != b""
            or completed.stderr.strip() != expected_marker
        ):
            raise ExternalGraphTopologyCapabilityError(
                f"operation-severance control failed for {poison_api}"
            )
        return {"api": poison_api, "severed": True}
    if completed.returncode != 0:
        raise _WorkerUnavailable(
            "worker exited before the graph/topology operation: "
            + completed.stderr.decode("utf-8", errors="replace")[:400]
        )
    stderr_text = completed.stderr.decode("utf-8", errors="replace")
    if stderr_text not in {"", _ALLOWED_INITIALIZATION_STDERR}:
        raise ExternalGraphTopologyCapabilityError(
            "worker wrote unexpected stderr: " + stderr_text[:400]
        )
    value = _decode_worker_json(completed.stdout)
    if value.get("schema") == FAILURE_SCHEMA:
        raise _WorkerUnavailable(
            "worker could not load or execute a required API: "
            + str(value.get("error", "unknown worker failure"))
        )
    if set(value) != {
        "schema",
        "binding",
        "exact_api",
        "worker_pid",
        "runtime",
        "observed",
    }:
        raise ExternalGraphTopologyCapabilityError("worker witness has an unexpected shape")
    if value.get("schema") != WITNESS_SCHEMA:
        raise ExternalGraphTopologyCapabilityError("worker witness schema is invalid")
    if value.get("binding") != binding.to_dict():
        raise ExternalGraphTopologyCapabilityError("worker witness binding mismatch")
    if value.get("exact_api") != list(EXACT_APIS):
        raise ExternalGraphTopologyCapabilityError("worker API declaration mismatch")
    if not isinstance(value.get("worker_pid"), int) or value["worker_pid"] == os.getpid():
        raise ExternalGraphTopologyCapabilityError("worker process identity is invalid")
    if not isinstance(value.get("runtime"), dict) or not isinstance(value.get("observed"), dict):
        raise ExternalGraphTopologyCapabilityError("worker witness has invalid observation data")
    value["controller_initialization_stderr"] = stderr_text
    return value


def _all_equal(values: dict[str, object], expected: int) -> bool:
    return set(values) == {"networkx", "igraph", "rustworkx", "pyg_torch"} and all(
        isinstance(value, int) and not isinstance(value, bool) and value == expected
        for value in values.values()
    )


def _controls(
    normal: dict[str, Any], replay: dict[str, Any], severance: dict[str, Any]
) -> dict[str, bool]:
    observed = normal.get("observed")
    replay_observed = replay.get("observed")
    if not isinstance(observed, dict) or not isinstance(replay_observed, dict):
        return {
            "positive": False,
            "targeted_negative": False,
            "boundary": False,
            "independent_replay": False,
            "operation_severance": False,
        }
    topology = observed.get("topology")
    connectivity = observed.get("connectivity")
    cycle = topology.get("cycle") if isinstance(topology, dict) else None
    filled = topology.get("filled") if isinstance(topology, dict) else None
    disconnected = connectivity.get("disconnected") if isinstance(connectivity, dict) else None
    chain = connectivity.get("chain") if isinstance(connectivity, dict) else None
    topology_positive = (
        isinstance(cycle, dict)
        and isinstance(filled, dict)
        and cycle.get("gudhi_b1") == 1
        and cycle.get("toponetx_b1") == 1
        and cycle.get("xgi_edge_sizes") == [2, 2, 2]
        and filled.get("gudhi_b1") == 0
        and filled.get("toponetx_b1") == 0
        and filled.get("xgi_edge_sizes") == [2, 2, 2, 3]
    )
    return {
        "positive": topology_positive and isinstance(disconnected, dict) and _all_equal(disconnected, 2),
        "targeted_negative": (
            isinstance(cycle, dict)
            and isinstance(filled, dict)
            and filled.get("gudhi_b1") != cycle.get("gudhi_b1")
            and filled.get("toponetx_b1") != cycle.get("toponetx_b1")
        ),
        "boundary": isinstance(chain, dict) and _all_equal(chain, 1),
        "independent_replay": observed == replay_observed,
        "operation_severance": (
            set(severance) == set(EXACT_APIS)
            and all(
                isinstance(severance[api], dict)
                and severance[api] == {"api": api, "severed": True}
                for api in EXACT_APIS
            )
        ),
    }


def _receipt_body(
    *,
    binding: GraphTopologyCapabilityBinding,
    normal: dict[str, Any] | None,
    replay: dict[str, Any] | None,
    severance: dict[str, Any],
    controls: dict[str, bool],
    status: str,
    reason: str,
) -> dict[str, Any]:
    source_path = Path(__file__).resolve()
    worker_path = _worker_path()
    return {
        "schema": RECEIPT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "status": status,
        "reason": reason,
        "binding": binding.to_dict(),
        "exact_api": list(EXACT_APIS),
        "controller_runtime": _runtime_identity(),
        "profile_source_sha256": _sha256_file(source_path),
        "worker_source_sha256": _sha256_file(worker_path),
        "normal": normal,
        "replay": replay,
        "severance": severance,
        "controls": controls,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }


class GraphTopologyCapabilityBroker:
    """Execute and independently challenge one fixed graph/topology profile."""

    def run(self, binding: GraphTopologyCapabilityBinding) -> dict[str, Any]:
        validate_graph_topology_binding(binding)
        normal: dict[str, Any] | None = None
        replay: dict[str, Any] | None = None
        severance: dict[str, Any] = {}
        controls = {
            "positive": False,
            "targeted_negative": False,
            "boundary": False,
            "independent_replay": False,
            "operation_severance": False,
        }
        try:
            normal = _run_worker(binding=binding, poison_api=None)
            replay = _run_worker(binding=binding, poison_api=None)
            severance = {
                api: _run_worker(binding=binding, poison_api=api) for api in EXACT_APIS
            }
            controls = _controls(normal, replay, severance)
            status = "PASS" if all(controls.values()) else "FAIL"
            reason = (
                "all_fixed_graph_topology_controls_passed"
                if status == "PASS"
                else "one_or_more_graph_topology_controls_failed"
            )
        except _WorkerUnavailable as exc:
            status = "PARKED"
            reason = f"selected_runtime_could_not_execute_profile:{exc}"
        except ExternalGraphTopologyCapabilityError as exc:
            status = "FAIL"
            reason = f"controller_graph_topology_verification_failed:{exc}"
        body = _receipt_body(
            binding=binding,
            normal=normal,
            replay=replay,
            severance=severance,
            controls=controls,
            status=status,
            reason=reason,
        )
        return {**body, "receipt_sha256": _SHA256(canonical_json(body)).hexdigest()}


def validate_graph_topology_receipt(
    receipt: object,
    *,
    expected_binding: GraphTopologyCapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Recompute the controller-visible checks before a Mini-Lev gate accepts it."""

    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ("receipt is not an object",)
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append("receipt schema differs")
    if receipt.get("capability_id") != CAPABILITY_ID:
        errors.append("receipt capability id differs")
    if receipt.get("exact_api") != list(EXACT_APIS):
        errors.append("receipt API declaration differs")
    if receipt.get("binding") != expected_binding.to_dict():
        errors.append("receipt binding differs")
    status = receipt.get("status")
    if status not in {"PASS", "FAIL", "PARKED"}:
        errors.append("receipt status is invalid")
    root = receipt.get("receipt_sha256")
    if root != expected_receipt_sha256 or not _is_hex(root):
        errors.append("receipt hash binding differs")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    if _SHA256(canonical_json(body)).hexdigest() != root:
        errors.append("receipt hash is not a canonical body hash")
    try:
        if receipt.get("profile_source_sha256") != _sha256_file(Path(__file__).resolve()):
            errors.append("profile source hash drifted")
        if receipt.get("worker_source_sha256") != _sha256_file(_worker_path()):
            errors.append("worker source hash drifted")
    except ExternalGraphTopologyCapabilityError as exc:
        errors.append(str(exc))
    controls = receipt.get("controls")
    normal = receipt.get("normal")
    replay = receipt.get("replay")
    severance = receipt.get("severance")
    if status == "PASS":
        if not isinstance(normal, dict) or not isinstance(replay, dict) or not isinstance(severance, dict):
            errors.append("passing receipt lacks worker observations")
        else:
            recomputed = _controls(normal, replay, severance)
            if controls != recomputed:
                errors.append("receipt controls differ from controller recomputation")
            if not all(recomputed.values()):
                errors.append("passing receipt has a failed controller control")
    if require_pass and status != "PASS":
        errors.append("receipt did not pass")
    for field in (
        "external_system",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
    ):
        expected = field == "external_system"
        if receipt.get(field) is not expected:
            errors.append(f"receipt {field} differs from capability boundary")
    if receipt.get("kernel_membership") != "EXTERNAL_NOT_CB_KERNEL":
        errors.append("receipt kernel membership differs")
    if receipt.get("claim_ceiling") != CAPABILITY_CLAIM_CEILING:
        errors.append("receipt claim ceiling differs")
    return tuple(errors)


def _binding_from_context(
    context: dict[str, Any],
    *,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> GraphTopologyCapabilityBinding:
    metadata = context.get(CONTROLLER_METADATA_KEY)
    expected_keys = {"schema", "run_id", "policy_sha256", "node_id", "hook_id", "hook_kind"}
    if not isinstance(metadata, dict) or set(metadata) != expected_keys:
        raise ExternalGraphTopologyCapabilityFlowError("controller metadata is missing")
    if metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise ExternalGraphTopologyCapabilityFlowError("controller metadata mismatch")
    text = context.get("capability_binding_json")
    if not isinstance(text, str):
        raise ExternalGraphTopologyCapabilityFlowError("capability binding is absent")
    try:
        binding = graph_topology_binding_from_dict(parse_json_object(text.encode("utf-8")))
    except (IntakeError, ExternalGraphTopologyCapabilityError) as exc:
        raise ExternalGraphTopologyCapabilityFlowError(f"capability binding is invalid: {exc}") from exc
    if binding.run_id != metadata["run_id"] or binding.flow_policy_sha256 != metadata["policy_sha256"]:
        raise ExternalGraphTopologyCapabilityFlowError("binding differs from controller metadata")
    return binding


def _graph_topology_capability_tool(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id="graph-topology-capability-tool",
        expected_hook_id="graph-topology-crosscheck-capability-tool",
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = GraphTopologyCapabilityBroker().run(binding)
    receipt_text = canonical_json(receipt).decode("utf-8")
    return HookResult(
        HookSignal.OBSERVED,
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
        },
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
            "capability_receipt_json": receipt_text,
        },
    )


def _graph_topology_capability_gate(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id="graph-topology-capability-gate",
        expected_hook_id="graph-topology-crosscheck-capability-gate",
        expected_hook_kind=HookKind.GATE,
    )
    text = context.get("capability_receipt_json")
    receipt_sha256 = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(isinstance(value, str) for value in (text, receipt_sha256, state)):
        raise ExternalGraphTopologyCapabilityFlowError("capability gate fields are invalid")
    try:
        receipt = parse_json_object(text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalGraphTopologyCapabilityFlowError(f"capability receipt is invalid: {exc}") from exc
    if receipt.get("status") != state:
        raise ExternalGraphTopologyCapabilityFlowError("capability state binding mismatch")
    errors = validate_graph_topology_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=state == "PASS",
    )
    if errors:
        raise ExternalGraphTopologyCapabilityFlowError(
            "capability receipt verification failed: " + "; ".join(errors)
        )
    signal = {"PASS": HookSignal.PASS, "FAIL": HookSignal.BLOCKED, "PARKED": HookSignal.PARKED}.get(state)
    if signal is None:
        raise ExternalGraphTopologyCapabilityFlowError("capability state is unknown")
    return HookResult(signal, {"capability_state": state, "capability_receipt_sha256": receipt_sha256})


def _registration(
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
        source_sha256=_sha256_file(source_path),
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=524_288,
    )


def _build_graph_topology_capability_flow(
    *, run_id: str, ledger_path: Path
) -> MiniLevRuntime:
    tool = _registration(
        hook_id="graph-topology-crosscheck-capability-tool",
        kind=HookKind.TOOL,
        handler=_graph_topology_capability_tool,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate = _registration(
        hook_id="graph-topology-crosscheck-capability-gate",
        kind=HookKind.GATE,
        handler=_graph_topology_capability_gate,
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )
    policy = FlowPolicy(
        flow_id=FLOW_ID,
        entry_node="graph-topology-capability-tool",
        nodes=(
            FlowNode("graph-topology-capability-tool", tool.hook_id),
            FlowNode("graph-topology-capability-gate", gate.hook_id),
        ),
        transitions=(
            FlowTransition("graph-topology-capability-tool", HookSignal.OBSERVED, "graph-topology-capability-gate"),
            FlowTransition("graph-topology-capability-tool", HookSignal.HOLD, "HOLD"),
            FlowTransition("graph-topology-capability-gate", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("graph-topology-capability-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("graph-topology-capability-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("graph-topology-capability-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=("graph-topology-capability-tool", "graph-topology-capability-gate"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=CAPABILITY_CLAIM_CEILING,
    )
    try:
        return MiniLevRuntime(policy, (tool, gate), run_id=run_id, ledger_path=ledger_path)
    except MiniLevError as exc:
        raise ExternalGraphTopologyCapabilityFlowError(
            f"capability flow construction failed: {exc}"
        ) from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ExternalGraphTopologyCapabilityFlowError(
            f"could not persist capability artifact: {exc}"
        ) from exc


def run_graph_topology_capability_flow(
    *, request_id: str, run_root: Path
) -> dict[str, Any]:
    """Run the fixed tool-to-gate flow with no caller-selected workload surface."""

    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalGraphTopologyCapabilityFlowError("request_id must be a safe identifier")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ExternalGraphTopologyCapabilityFlowError("run_root must be absolute")
    run_root = run_root.resolve(strict=False)
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ExternalGraphTopologyCapabilityFlowError(
            f"capability run directory must be new: {exc}"
        ) from exc
    cache_root = _make_private_cache_root(run_root)
    request_body = {
        "schema": "constraintbox.external-graph-topology-capability-request.v1",
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
    }
    request_sha256 = _SHA256(canonical_json(request_body)).hexdigest()
    bootstrap_run_id = "graph-topology-" + _SHA256(canonical_json(request_body)).hexdigest()[:32]
    runtime = _build_graph_topology_capability_flow(
        run_id=bootstrap_run_id,
        ledger_path=run_root / FLOW_LEDGER_NAME,
    )
    binding = GraphTopologyCapabilityBinding(
        capability_id=CAPABILITY_ID,
        run_id=runtime.run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=STEP_ID,
        cache_root=str(cache_root),
    )
    try:
        flow_receipt = runtime.run(
            {"capability_binding_json": canonical_json(binding.to_dict()).decode("utf-8")}
        )
    except MiniLevError as exc:
        raise ExternalGraphTopologyCapabilityFlowError(f"capability flow execution failed: {exc}") from exc
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise ExternalGraphTopologyCapabilityFlowError(f"flow receipt failed verification: {reason}")
    receipt_text = flow_receipt["final_context"].get("capability_receipt_json")
    receipt_sha256 = flow_receipt["final_context"].get("capability_receipt_sha256")
    if not isinstance(receipt_text, str) or not isinstance(receipt_sha256, str):
        raise ExternalGraphTopologyCapabilityFlowError("flow produced no capability receipt")
    try:
        capability_receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalGraphTopologyCapabilityFlowError(f"capability receipt is invalid: {exc}") from exc
    errors = validate_graph_topology_receipt(
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=flow_receipt["terminal"] == "ELIGIBLE",
    )
    if errors:
        raise ExternalGraphTopologyCapabilityFlowError(
            "persisted capability receipt failed verification: " + "; ".join(errors)
        )
    expected_terminal = {"PASS": "ELIGIBLE", "FAIL": "BLOCKED", "PARKED": "PARKED"}.get(
        capability_receipt.get("status")
    )
    if expected_terminal != flow_receipt["terminal"]:
        raise ExternalGraphTopologyCapabilityFlowError("capability status differs from flow terminal")
    _persist_exclusive(run_root / CAPABILITY_RECEIPT_NAME, capability_receipt)
    _persist_exclusive(run_root / FLOW_RECEIPT_NAME, flow_receipt)
    return {
        "schema": FLOW_RESULT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "run_id": runtime.run_id,
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
