"""Replayable Mini-Lev path mass, joint entropy/topology, and SMT disposition.

This is one finite operation. It enumerates legal traces of the reference
proposal Mini-Lev policy, mutates that policy with controller operations
the flow already understands, and measures quotient, mass, Hartley
capacity, and used-transition topology on the same surviving rows.

Memory methods only propose a class. dual_solve writes the disposition.
Nothing here is an attractor basin, physical time, Hopfield energy as
Hartley capacity, or spinor-memory geometry.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Any

from constraintbox.bound_quotient import decide_bound_packet
from constraintbox.dualsolve import dual_solve


PACKET_SCHEMA = "constraintbox.bound-observation.packet.v1"
RECEIPT_SCHEMA = "constraintbox.constraint-path-mass.receipt.v1"
OPERATION = "constraint_path_mass.v1"
DEFAULT_PROBES: tuple[str, ...] = (
    "terminal",
    "retried",
    "visits_claim_gate",
    "released",
    "parked",
    "blocked",
)
CLAIM_CEILING = (
    "finite Mini-Lev path family from the reference proposal policy; "
    "probe-relative quotient and exact leftover mass; Hartley support and "
    "record capacities; used-transition topology; hash/Hopfield/quaternion/"
    "hostile proposals only; SMT writes admission; not an attractor basin, "
    "physical time, jointly evolving (S_C/~_P, mu_C), Hopfield energy, "
    "or spinor-memory geometry"
)
_NOT = (
    "attractor_basin",
    "physical_time",
    "jointly_evolving_mass_entropy_topology",
    "hopfield_energy_as_hartley",
    "spinor_memory_geometry",
    "many_body_qit",
    "promotion",
)
_HELPER_SOURCE_PATH = Path(__file__).resolve()
_TERMINAL_BITS = ("RELEASED", "BLOCKED", "PARKED", "HOLD")
_HOSTILE_SEED = "constraint_path_mass.v1.hostile"
_ALLOWED_PROBES = frozenset(DEFAULT_PROBES)
_DEFAULT_MUTATIONS = (
    "remove_repair",
    "zero_retry_budget",
    "erase_release",
    "restrict_probes_to_terminal",
)
_MAX_INPUT_BYTES = 262_144
FLOW_ID = "constraintbox.bounded-proposal-retry-claim.v1"
REFERENCE_FIXTURE_NAME = "proposal_reference_policy_v1.json"


class HookSignal(str, Enum):
    """Minimal signal vocabulary copied into the bounded path object."""

    OBSERVED = "OBSERVED"
    PASS = "PASS"
    RETRY = "RETRY"
    BLOCKED = "BLOCKED"
    PARKED = "PARKED"
    HOLD = "HOLD"


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
class FlowPolicy:
    """Small JSON-backed policy representation used by this operation only."""

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


class PathMassError(ValueError):
    """The finite path-mass object could not be built."""


@dataclass(frozen=True)
class PathMassLimits:
    """Hard limits for one finite, replayable path-mass run."""

    max_paths: int = 128
    max_steps: int = 6
    max_mutations: int = 16
    max_probe_count: int = 16
    max_receipt_bytes: int = 8 * 1024 * 1024
    jax_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        for name in (
            "max_paths",
            "max_steps",
            "max_mutations",
            "max_probe_count",
            "max_receipt_bytes",
        ):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise PathMassError(f"{name} must be a positive integer")
        if self.max_paths > 1_024 or self.max_steps > 64:
            raise PathMassError("finite path limits exceed the operation ceiling")
        if self.max_mutations > 32 or self.max_probe_count > 32:
            raise PathMassError("mutation/probe limits exceed the operation ceiling")
        if self.max_receipt_bytes > 16 * 1024 * 1024:
            raise PathMassError("max_receipt_bytes exceeds the operation ceiling")
        if isinstance(self.jax_timeout_seconds, bool) or type(self.jax_timeout_seconds) not in (int, float):
            raise PathMassError("jax_timeout_seconds must be a finite number")
        if not math.isfinite(float(self.jax_timeout_seconds)) or not (
            0.1 <= float(self.jax_timeout_seconds) <= 120.0
        ):
            raise PathMassError("jax_timeout_seconds is outside the bounded range")

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_paths": self.max_paths,
            "max_steps": self.max_steps,
            "max_mutations": self.max_mutations,
            "max_probe_count": self.max_probe_count,
            "max_receipt_bytes": self.max_receipt_bytes,
            "jax_timeout_seconds": float(self.jax_timeout_seconds),
        }


@dataclass(frozen=True)
class ConstraintPathMassRequest:
    """Typed request for one bounded path-mass operation.

    The optional JAX crossing is deliberately an external interpreter input.
    A missing interpreter leaves the Light operation usable but records a
    reason-specific JAX HOLD; it never falls back to importing JAX in this
    controller process.
    """

    probes: tuple[str, ...] = DEFAULT_PROBES
    mutation_ids: tuple[str, ...] = _DEFAULT_MUTATIONS
    jax_interpreter: Path | None = None
    fixture_path: Path | None = None
    require_jax: bool = False
    limits: PathMassLimits = PathMassLimits()

    def __post_init__(self) -> None:
        if type(self.probes) is not tuple or not self.probes:
            raise PathMassError("probes must be a nonempty tuple")
        if len(self.probes) > self.limits.max_probe_count:
            raise PathMassError("probe count exceeds the bounded request limit")
        if any(type(name) is not str or not name for name in self.probes):
            raise PathMassError("probes must contain nonempty text")
        if len(set(self.probes)) != len(self.probes):
            raise PathMassError("probes must be unique")
        if any(name not in _ALLOWED_PROBES for name in self.probes):
            raise PathMassError("probe is not in the finite operation vocabulary")
        if type(self.mutation_ids) is not tuple or not self.mutation_ids:
            raise PathMassError("mutation_ids must be a nonempty tuple")
        if len(self.mutation_ids) > self.limits.max_mutations:
            raise PathMassError("mutation count exceeds the bounded request limit")
        if any(type(name) is not str or not name for name in self.mutation_ids):
            raise PathMassError("mutation_ids must contain nonempty text")
        if len(set(self.mutation_ids)) != len(self.mutation_ids):
            raise PathMassError("mutation_ids must be unique")
        if any(name not in _DEFAULT_MUTATIONS for name in self.mutation_ids):
            raise PathMassError("mutation is not in the finite operation vocabulary")
        if type(self.require_jax) is not bool:
            raise PathMassError("require_jax must be boolean")
        if type(self.limits) is not PathMassLimits:
            raise PathMassError("limits must be PathMassLimits")
        if self.jax_interpreter is not None:
            if not isinstance(self.jax_interpreter, Path) or not self.jax_interpreter.is_absolute():
                raise PathMassError("jax_interpreter must be an absolute pathlib.Path")
            if not self.jax_interpreter.exists() or not self.jax_interpreter.is_file():
                raise PathMassError("jax_interpreter must be a regular file")
        if self.fixture_path is not None:
            if not isinstance(self.fixture_path, Path) or not self.fixture_path.is_absolute():
                raise PathMassError("fixture_path must be an absolute pathlib.Path")
            if not self.fixture_path.exists() or not self.fixture_path.is_file():
                raise PathMassError("fixture_path must be a regular file")
        if self.require_jax and self.jax_interpreter is None:
            raise PathMassError("require_jax needs a declared external interpreter")

    def as_dict(
        self,
        *,
        interpreter_sha256: str | None = None,
        fixture_sha256: str | None = None,
    ) -> dict[str, Any]:
        return {
            "probes": list(self.probes),
            "mutation_ids": list(self.mutation_ids),
            "require_jax": self.require_jax,
            "limits": self.limits.as_dict(),
            "jax_interpreter_declared": self.jax_interpreter is not None,
            "jax_interpreter_sha256": interpreter_sha256,
            "fixture_sha256": fixture_sha256,
        }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def default_reference_fixture_path() -> Path:
    """Find the contained fixture in source and fresh merged layouts."""

    for parent in (_HELPER_SOURCE_PATH.parent, *_HELPER_SOURCE_PATH.parents):
        candidate = parent / "fixtures" / "minilev" / REFERENCE_FIXTURE_NAME
        if candidate.is_file():
            return candidate
    raise PathMassError("REFUSE_REFERENCE_FIXTURE_MISSING")


def _fixture_path(path: Path | None) -> Path:
    selected = default_reference_fixture_path() if path is None else path
    if not isinstance(selected, Path) or not selected.is_absolute():
        raise PathMassError("reference fixture must be an absolute pathlib.Path")
    try:
        resolved = selected.resolve(strict=True)
    except OSError as exc:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_UNREADABLE") from exc
    if not resolved.is_file():
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_UNREADABLE")
    return resolved


def _load_reference_fixture(path: Path | None = None) -> dict[str, Any]:
    selected = _fixture_path(path)
    try:
        raw = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_INVALID") from exc
    if type(raw) is not dict or set(raw) != {
        "schema",
        "policy",
        "allowed_signals",
        "provenance",
    }:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_SHAPE")
    if raw["schema"] != "constraintbox.minilev-reference-policy.v1":
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_SCHEMA")
    if type(raw["provenance"]) is not dict:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_PROVENANCE")
    source_hash = raw["provenance"].get("source_sha256")
    if type(source_hash) is not str or len(source_hash) != 64:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_PROVENANCE")
    return raw


def reference_fixture_material(path: Path | None = None) -> dict[str, Any]:
    """Return policy and allowed-signal material without importing Mini-Lev."""

    raw = _load_reference_fixture(path)
    policy = raw["policy"]
    allowed = raw["allowed_signals"]
    if type(policy) is not dict or type(allowed) is not dict:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_SHAPE")
    return {
        "policy": policy,
        "allowed_signals": allowed,
        "provenance": dict(raw["provenance"]),
    }


def _policy_from_fixture(path: Path | None = None) -> FlowPolicy:
    material = reference_fixture_material(path)
    raw = material["policy"]
    try:
        nodes = tuple(
            FlowNode(str(item["node_id"]), str(item["hook_id"]))
            for item in raw["nodes"]
        )
        transitions = tuple(
            FlowTransition(
                str(item["from_node"]),
                HookSignal(str(item["signal"])),
                str(item["to_node"]),
            )
            for item in raw["transitions"]
        )
        return FlowPolicy(
            flow_id=str(raw["flow_id"]),
            entry_node=str(raw["entry_node"]),
            nodes=nodes,
            transitions=transitions,
            terminal_nodes=tuple(str(value) for value in raw["terminal_nodes"]),
            required_nodes=tuple(str(value) for value in raw["required_nodes"]),
            max_steps=int(raw["max_steps"]),
            max_visits_per_node=int(raw["max_visits_per_node"]),
            max_retries=int(raw["max_retries"]),
            max_context_bytes=int(raw["max_context_bytes"]),
            max_event_bytes=int(raw["max_event_bytes"]),
            max_receipt_bytes=int(raw["max_receipt_bytes"]),
            claim_ceiling=str(raw["claim_ceiling"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_POLICY") from exc


def reference_flow_policy(path: Path | None = None) -> FlowPolicy:
    return _policy_from_fixture(path)


def reference_allowed_signals(
    path: Path | None = None,
) -> dict[str, tuple[HookSignal, ...]]:
    material = reference_fixture_material(path)
    try:
        return {
            str(node): tuple(HookSignal(str(value)) for value in values)
            for node, values in material["allowed_signals"].items()
        }
    except (TypeError, ValueError) as exc:
        raise PathMassError("REFUSE_REFERENCE_FIXTURE_ALLOWED_SIGNALS") from exc


def fixture_material_from_policy(
    policy: Any,
    allowed: Any,
) -> dict[str, Any]:
    """Canonicalize the dev-only live Mini-Lev policy into fixture material."""

    try:
        policy_material = {
            "flow_id": str(policy.flow_id),
            "entry_node": str(policy.entry_node),
            "nodes": [
                {"node_id": str(node.node_id), "hook_id": str(node.hook_id)}
                for node in policy.nodes
            ],
            "transitions": [
                {
                    "from_node": str(transition.from_node),
                    "signal": str(transition.signal.value),
                    "to_node": str(transition.to_node),
                }
                for transition in policy.transitions
            ],
            "terminal_nodes": [str(value) for value in policy.terminal_nodes],
            "required_nodes": [str(value) for value in policy.required_nodes],
            "max_steps": int(policy.max_steps),
            "max_visits_per_node": int(policy.max_visits_per_node),
            "max_retries": int(policy.max_retries),
            "max_context_bytes": int(policy.max_context_bytes),
            "max_event_bytes": int(policy.max_event_bytes),
            "max_receipt_bytes": int(policy.max_receipt_bytes),
            "claim_ceiling": str(policy.claim_ceiling),
        }
        allowed_material = {
            str(node): [str(signal.value) for signal in signals]
            for node, signals in allowed.items()
        }
    except (AttributeError, TypeError, ValueError) as exc:
        raise PathMassError("live reference policy cannot be canonicalized") from exc
    return {"policy": policy_material, "allowed_signals": allowed_material}


def _policy_material(policy: FlowPolicy) -> dict[str, Any]:
    return {
        "flow_id": policy.flow_id,
        "entry_node": policy.entry_node,
        "nodes": [
            {"node_id": node.node_id, "hook_id": node.hook_id} for node in policy.nodes
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
        "max_steps": policy.max_steps,
        "max_visits_per_node": policy.max_visits_per_node,
        "max_retries": policy.max_retries,
        "max_context_bytes": policy.max_context_bytes,
        "max_event_bytes": policy.max_event_bytes,
        "max_receipt_bytes": policy.max_receipt_bytes,
        "claim_ceiling": policy.claim_ceiling,
    }


def _transition_map(policy: FlowPolicy) -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    for transition in policy.transitions:
        key = (transition.from_node, transition.signal.value)
        if key in mapping:
            raise PathMassError("duplicate policy transition")
        mapping[key] = transition.to_node
    return mapping


def _validate_reference_policy(
    policy: FlowPolicy,
    allowed: dict[str, tuple[HookSignal, ...]],
    fixture_path: Path | None = None,
) -> None:
    """Refuse foreign flows while permitting the bounded mutations we own."""

    if policy.flow_id != FLOW_ID:
        raise PathMassError("policy is not the reference proposal Mini-Lev flow")
    reference = reference_flow_policy(fixture_path)
    if policy.entry_node != reference.entry_node:
        raise PathMassError("policy entry node differs from the reference flow")
    if tuple(node.node_id for node in policy.nodes) != tuple(
        node.node_id for node in reference.nodes
    ):
        raise PathMassError("policy nodes differ from the reference flow")
    if tuple(policy.terminal_nodes) != tuple(reference.terminal_nodes):
        raise PathMassError("policy terminals differ from the reference flow")
    if tuple(policy.required_nodes) != tuple(reference.required_nodes):
        raise PathMassError("policy required nodes differ from the reference flow")
    if policy.max_steps <= 0 or policy.max_steps > reference.max_steps:
        raise PathMassError("policy max_steps exceeds the reference bound")
    if policy.max_visits_per_node <= 0 or policy.max_visits_per_node > reference.max_visits_per_node:
        raise PathMassError("policy max_visits_per_node exceeds the reference bound")
    if policy.max_retries < 0 or policy.max_retries > reference.max_retries:
        raise PathMassError("policy max_retries exceeds the reference bound")
    reference_keys = {
        (transition.from_node, transition.signal.value)
        for transition in reference.transitions
    }
    policy_keys = {
        (transition.from_node, transition.signal.value)
        for transition in policy.transitions
    }
    if policy_keys != reference_keys:
        raise PathMassError("policy transitions differ from the reference vocabulary")
    known_targets = {
        node.node_id for node in reference.nodes
    } | set(reference.terminal_nodes)
    if any(transition.to_node not in known_targets for transition in policy.transitions):
        raise PathMassError("policy transition targets leave the reference flow")
    reference_allowed = reference_allowed_signals(fixture_path)
    if type(allowed) is not dict or set(allowed) != set(reference_allowed):
        raise PathMassError("allowed signals differ from the reference hook vocabulary")
    for node, signals in allowed.items():
        if type(signals) is not tuple or not signals:
            raise PathMassError(f"allowed signals for {node} must be a nonempty tuple")
        if any(type(signal) is not HookSignal for signal in signals):
            raise PathMassError("allowed signals must contain HookSignal values")
        if len(set(signals)) != len(signals):
            raise PathMassError("allowed signals must be unique")
        if not set(signals).issubset(set(reference_allowed[node])):
            raise PathMassError("allowed signal is not emitted by the reference hook")
        for signal in signals:
            if (node, signal.value) not in policy_keys:
                raise PathMassError("allowed signal has no policy transition")


def enumerate_policy_paths(
    policy: FlowPolicy,
    allowed: dict[str, tuple[HookSignal, ...]] | None = None,
    fixture_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Enumerate legal hook-signal traces under the policy budgets.

    A path is a controller-selected walk. Hooks do not choose the next node.
    Traces that exhaust a budget without a terminal are dropped, not invented.
    """

    if type(policy) is not FlowPolicy:
        raise PathMassError("policy is not a FlowPolicy")
    allowed = allowed if allowed is not None else reference_allowed_signals(fixture_path)
    _validate_reference_policy(policy, allowed, fixture_path)
    mapping = _transition_map(policy)
    terminals = set(policy.terminal_nodes)
    traces: list[tuple[tuple[tuple[str, str, str], ...], str]] = []

    def walk(
        node: str,
        visits: dict[str, int],
        retries: int,
        steps: int,
        acc: tuple[tuple[str, str, str], ...],
    ) -> None:
        if node in terminals:
            traces.append((acc, node))
            return
        if steps >= policy.max_steps:
            return
        if visits.get(node, 0) >= policy.max_visits_per_node:
            return
        next_visits = dict(visits)
        next_visits[node] = next_visits.get(node, 0) + 1
        signals = allowed.get(node, ())
        for signal in signals:
            dest = mapping.get((node, signal.value))
            if dest is None:
                continue
            next_retries = retries
            if signal is HookSignal.RETRY:
                if retries >= policy.max_retries:
                    continue
                next_retries = retries + 1
            walk(
                dest,
                next_visits,
                next_retries,
                steps + 1,
                acc + ((node, signal.value, dest),),
            )

    walk(policy.entry_node, {}, 0, 0, ())
    traces.sort(key=lambda item: (_canonical_bytes(item[0]), item[1]))
    paths: list[dict[str, Any]] = []
    for index, (steps, terminal) in enumerate(traces):
        path_id = f"P{index:03d}"
        visits_claim = int(
            any(step[0] == "claim-gate" or step[2] == "claim-gate" for step in steps)
        )
        retried = int(any(step[1] == HookSignal.RETRY.value for step in steps))
        observation = {
            "terminal": terminal,
            "retried": retried,
            "visits_claim_gate": visits_claim,
            "released": int(terminal == "RELEASED"),
            "parked": int(terminal == "PARKED"),
            "blocked": int(terminal == "BLOCKED"),
        }
        paths.append(
            {
                "id": path_id,
                "steps": [
                    {"from_node": src, "signal": signal, "to_node": dest}
                    for src, signal, dest in steps
                ],
                "observation": observation,
            }
        )
    return paths


def _bound_packet(
    paths: list[dict[str, Any]], probes: tuple[str, ...] | list[str], claim: str
) -> dict[str, Any]:
    rows = []
    for path in paths:
        for probe in probes:
            rows.append(
                {
                    "candidate": path["id"],
                    "probe": probe,
                    "value": path["observation"][probe],
                }
            )
    return {
        "schema": PACKET_SCHEMA,
        "claim": claim,
        "candidates": [path["id"] for path in paths],
        "probes": list(probes),
        "rows": rows,
        "authority": "none",
        "promotion_allowed": False,
    }


def _mass_from_quotient(
    quotient: dict[str, Any], n_paths: int
) -> list[dict[str, Any]]:
    masses: list[dict[str, Any]] = []
    if n_paths <= 0 or not quotient.get("quotient_admitted"):
        return masses
    for basin in quotient["basins"]:
        fraction = Fraction(int(basin["size"]), n_paths)
        masses.append(
            {
                "id": basin["id"],
                "members": list(basin["members"]),
                "size": int(basin["size"]),
                "mu_numerator": fraction.numerator,
                "mu_denominator": fraction.denominator,
            }
        )
    return masses


def _entropy(
    n_paths: int,
    distinct_tuples: int,
    n_classes: int,
    *,
    released_count: int = 0,
    held_count: int = 0,
) -> dict[str, Any]:
    return {
        "support_W": n_paths,
        "support_K": math.log2(n_paths) if n_paths > 0 else 0.0,
        "record_distinct_tuples": distinct_tuples,
        "record_K": math.log2(distinct_tuples) if distinct_tuples > 0 else 0.0,
        "class_count": n_classes,
        "class_K": math.log2(n_classes) if n_classes > 0 else 0.0,
        "released_count": released_count,
        "held_count": held_count,
    }


def _used_graph(paths: list[dict[str, Any]]) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    nodes: set[str] = set()
    edges: set[tuple[str, str]] = set()
    for path in paths:
        for step in path["steps"]:
            nodes.add(step["from_node"])
            nodes.add(step["to_node"])
            edges.add((step["from_node"], step["to_node"]))
    return tuple(sorted(nodes)), tuple(sorted(edges))


def _reference_topology(
    nodes: tuple[str, ...], edges: tuple[tuple[str, str], ...]
) -> dict[str, Any]:
    parent = {node: node for node in nodes}

    def find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for source, target in edges:
        parent[find(source)] = find(target)
    components = len({find(node) for node in nodes}) if nodes else 0
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for source, target in edges:
        outgoing[source].append(target)
        indegree[target] += 1
    ready = [node for node in nodes if indegree[node] == 0]
    seen = 0
    while ready:
        source = ready.pop(0)
        seen += 1
        for target in outgoing[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return {
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "n_weak_components": components,
        "is_dag": seen == len(nodes),
    }


def _rustworkx_topology(
    nodes: tuple[str, ...], edges: tuple[tuple[str, str], ...]
) -> dict[str, Any] | None:
    try:
        import rustworkx as rx
    except ImportError:
        return None
    graph = rx.PyDiGraph()
    index = {node: graph.add_node(node) for node in nodes}
    for source, target in edges:
        graph.add_edge(index[source], index[target], None)
    return {
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "n_weak_components": len(rx.weakly_connected_components(graph)),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def _topology(paths: list[dict[str, Any]]) -> dict[str, Any]:
    nodes, edges = _used_graph(paths)
    reference = _reference_topology(nodes, edges)
    library = _rustworkx_topology(nodes, edges)
    payload = {
        "nodes": list(nodes),
        "edges": [{"from_node": src, "to_node": dest} for src, dest in edges],
        "nodes_sha256": _sha256(list(nodes)),
        "edges_sha256": _sha256([[src, dest] for src, dest in edges]),
        "reference": reference,
        "rustworkx": library,
        "agree": library == reference if library is not None else False,
    }
    payload.update(reference)
    return payload


def _measure(
    paths: list[dict[str, Any]], probes: tuple[str, ...] | list[str], claim: str
) -> dict[str, Any]:
    if not paths:
        return {
            "n_paths": 0,
            "probes": list(probes),
            "quotient": {
                "status": "HOLD",
                "reason": "NO_SURVIVING_PATHS",
                "quotient_admitted": False,
            },
            "mass": [],
            "entropy": _entropy(0, 0, 0),
            "topology": _topology([]),
        }
    packet = _bound_packet(paths, probes, claim)
    quotient = decide_bound_packet(packet)
    n_classes = len(quotient.get("basins") or [])
    distinct = int(
        (quotient.get("capacities") or {}).get("record", {}).get(
            "distinct_observation_tuples", 0
        )
    )
    released_count = sum(path["observation"]["released"] for path in paths)
    held_count = sum(
        1 for path in paths if path["observation"]["terminal"] == "HOLD"
    )
    return {
        "n_paths": len(paths),
        "probes": list(probes),
        "packet_sha256": quotient.get("packet_sha256"),
        "quotient": quotient,
        "mass": _mass_from_quotient(quotient, len(paths)),
        "entropy": _entropy(
            len(paths),
            distinct,
            n_classes,
            released_count=released_count,
            held_count=held_count,
        ),
        "topology": _topology(paths),
    }


def _remap_transition(
    policy: FlowPolicy, from_node: str, signal: HookSignal, to_node: str
) -> FlowPolicy:
    replaced = False
    transitions: list[FlowTransition] = []
    for transition in policy.transitions:
        if transition.from_node == from_node and transition.signal is signal:
            transitions.append(FlowTransition(from_node, signal, to_node))
            replaced = True
        else:
            transitions.append(transition)
    if not replaced:
        raise PathMassError(f"missing transition {from_node}/{signal.value}")
    return replace(policy, transitions=tuple(transitions))


def _mutations() -> list[dict[str, Any]]:
    return [
        {
            "id": "remove_repair",
            "kind": "remap_transition",
            "from_node": "proposal-gate",
            "signal": HookSignal.RETRY.value,
            "to_node": "BLOCKED",
            "why": "Mini-Lev already maps failing gate signals to BLOCKED; this removes repair",
        },
        {
            "id": "zero_retry_budget",
            "kind": "set_max_retries",
            "max_retries": 0,
            "why": "the reference policy already owns max_retries; zero drops retry walks",
        },
        {
            "id": "erase_release",
            "kind": "remap_transition",
            "from_node": "claim-gate",
            "signal": HookSignal.PASS.value,
            "to_node": "HOLD",
            "why": "erases the success bond by sending PASS to HOLD",
        },
        {
            "id": "restrict_probes_to_terminal",
            "kind": "restrict_probes",
            "probes": ["terminal"],
            "why": "structured probe restriction; paths stay, observation family shrinks",
        },
    ]


def _apply_mutation(
    policy: FlowPolicy, probes: tuple[str, ...], mutation: dict[str, Any]
) -> tuple[FlowPolicy, tuple[str, ...]]:
    kind = mutation["kind"]
    if kind == "remap_transition":
        return (
            _remap_transition(
                policy,
                mutation["from_node"],
                HookSignal(mutation["signal"]),
                mutation["to_node"],
            ),
            probes,
        )
    if kind == "set_max_retries":
        return replace(policy, max_retries=int(mutation["max_retries"])), probes
    if kind == "restrict_probes":
        restricted = tuple(mutation["probes"])
        if any(name not in probes for name in restricted):
            raise PathMassError("restricted probe is not in the active family")
        return policy, restricted
    raise PathMassError(f"unknown mutation kind {kind}")


def _class_of(path_id: str, quotient: dict[str, Any]) -> str | None:
    for basin in quotient.get("basins") or []:
        if path_id in basin["members"]:
            return str(basin["id"])
    return None


def _bipolar(observation: dict[str, Any], probes: list[str]) -> tuple[int, ...]:
    bits = [
        1 if observation.get("terminal") == name else -1 for name in _TERMINAL_BITS
    ]
    for probe in probes:
        if probe == "terminal":
            continue
        bits.append(1 if observation[probe] else -1)
    return tuple(bits)


def _sign_vec(values: list[int]) -> tuple[int, ...]:
    return tuple(1 if value > 0 else -1 if value < 0 else 0 for value in values)


def _hopfield_recall(
    query: tuple[int, ...], patterns: list[tuple[int, ...]], steps: int = 8
) -> tuple[int, ...] | None:
    if not patterns or not query:
        return None
    dim = len(query)
    weights = [[0 for _ in range(dim)] for _ in range(dim)]
    for pattern in patterns:
        if len(pattern) != dim:
            return None
        for i, left in enumerate(pattern):
            for j, right in enumerate(pattern):
                if i == j:
                    continue
                weights[i][j] += left * right
    state = list(query)
    for _ in range(steps):
        nxt = []
        for i in range(dim):
            acc = sum(weights[i][j] * state[j] for j in range(dim))
            nxt.append(1 if acc > 0 else -1 if acc < 0 else state[i])
        if nxt == state:
            break
        state = nxt
    recalled = tuple(state)
    if all(value == 0 for value in recalled):
        return None
    return recalled


def _nearest_pattern(
    vector: tuple[int, ...], labeled: list[tuple[str, tuple[int, ...]]]
) -> str | None:
    if vector is None or not labeled:
        return None
    best: str | None = None
    best_score: int | None = None
    for label, pattern in labeled:
        if len(pattern) != len(vector):
            continue
        score = sum(left * right for left, right in zip(vector, pattern, strict=True))
        if best_score is None or score > best_score:
            best_score = score
            best = label
    if best_score is None or best_score <= 0:
        return None
    return best


def _qmul(
    left: tuple[float, float, float, float], right: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    w1, x1, y1, z1 = left
    w2, x2, y2, z2 = right
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def _as_quaternion(vector: tuple[int, ...]) -> tuple[float, float, float, float] | None:
    coords = list(vector[:4])
    while len(coords) < 4:
        coords.append(0)
    norm = math.sqrt(sum(value * value for value in coords))
    if norm == 0:
        return None
    return (coords[0] / norm, coords[1] / norm, coords[2] / norm, coords[3] / norm)


def _quaternion_recall(
    query: tuple[int, ...], labeled: list[tuple[str, tuple[int, ...]]]
) -> str | None:
    query_q = _as_quaternion(query)
    if query_q is None or not labeled:
        return None
    best: str | None = None
    best_score: float | None = None
    for label, pattern in labeled:
        stored = _as_quaternion(pattern)
        if stored is None:
            continue
        conj = (stored[0], -stored[1], -stored[2], -stored[3])
        score = _qmul(conj, query_q)[0]
        if best_score is None or score > best_score:
            best_score = score
            best = label
    if best_score is None or best_score <= 0:
        return None
    return best


def _hostile_label(path_id: str, labels: list[str]) -> str:
    digest = hashlib.sha256(f"{_HOSTILE_SEED}:{path_id}".encode("utf-8")).hexdigest()
    return labels[int(digest[:8], 16) % len(labels)]


def _score_methods(
    paths: list[dict[str, Any]],
    probes: list[str],
    quotient: dict[str, Any],
    *,
    erased: bool,
) -> dict[str, Any]:
    if not quotient.get("quotient_admitted"):
        return {"status": "HOLD", "reason": "NO_QUOTIENT"}
    labels = [str(basin["id"]) for basin in quotient["basins"]]
    members: dict[str, list[str]] = {
        str(basin["id"]): list(basin["members"]) for basin in quotient["basins"]
    }
    vectors = {
        path["id"]: _bipolar(path["observation"], probes) for path in paths
    }
    prototypes: list[tuple[str, tuple[int, ...]]] = []
    if not erased:
        for label in labels:
            acc = [0] * len(next(iter(vectors.values())))
            for path_id in members[label]:
                for index, bit in enumerate(vectors[path_id]):
                    acc[index] += bit
            prototypes.append((label, _sign_vec(acc)))
    hash_store = {}
    if not erased:
        for path in paths:
            key = tuple(path["observation"][probe] for probe in probes)
            hash_store.setdefault(key, _class_of(path["id"], quotient))

    counts = {
        "hash_lookup": 0,
        "scalar_hopfield": 0,
        "quaternion_recall": 0,
        "hostile_random": 0,
    }
    survivors = {name: 0 for name in counts}
    details: list[dict[str, Any]] = []
    for path in paths:
        truth = _class_of(path["id"], quotient)
        key = tuple(path["observation"][probe] for probe in probes)
        hash_guess = hash_store.get(key)
        hopfield_state = _hopfield_recall(
            vectors[path["id"]], [pattern for _, pattern in prototypes]
        )
        hopfield_guess = _nearest_pattern(hopfield_state, prototypes) if hopfield_state else None
        quat_guess = _quaternion_recall(vectors[path["id"]], prototypes)
        hostile_guess = _hostile_label(path["id"], labels) if labels and not erased else None
        guesses = {
            "hash_lookup": hash_guess,
            "scalar_hopfield": hopfield_guess,
            "quaternion_recall": quat_guess,
            "hostile_random": hostile_guess,
        }
        for name, guess in guesses.items():
            if guess is not None:
                survivors[name] += 1
            if guess is not None and guess == truth:
                counts[name] += 1
        details.append({"id": path["id"], "truth": truth, **guesses})

    n_paths = len(paths)
    return {
        "status": "PASS",
        "erased": erased,
        "n_paths": n_paths,
        "n_classes": len(labels),
        "correct": counts,
        "survivors": survivors,
        "details_sha256": _sha256(details),
    }


_JAX_CROSSING_SCRIPT = r'''
import json
import sys

payload = json.load(sys.stdin)
jax = __import__("jax")
jnp = __import__("jax.numpy", fromlist=["numpy"])

vectors = payload["vectors"]
prototypes = payload["prototypes"]
pattern_stack = jnp.asarray([item[1] for item in prototypes], dtype=jnp.int32)
labels = [item[0] for item in prototypes]
dim = int(pattern_stack.shape[1])
weights = jnp.zeros((dim, dim), dtype=jnp.int32)
for pattern in pattern_stack:
    weights = weights + jnp.outer(pattern, pattern)
weights = weights.at[jnp.diag_indices(dim)].set(0)

hopfield = []
quaternion = []
for query in vectors:
    query_j = jnp.asarray(query["vector"], dtype=jnp.int32)
    state = query_j
    for _ in range(8):
        acc = weights @ state
        state = jnp.where(acc > 0, 1, jnp.where(acc < 0, -1, state))
    overlaps = pattern_stack @ state
    if int(jnp.max(overlaps)) <= 0:
        hopfield.append(None)
    else:
        hopfield.append(labels[int(jnp.argmax(overlaps))])

    coords = list(query["vector"][:4])
    while len(coords) < 4:
        coords.append(0)
    norm = jnp.sqrt(jnp.sum(jnp.asarray(coords, dtype=jnp.float32) ** 2))
    if float(norm) == 0.0:
        quaternion.append(None)
        continue
    q = jnp.asarray(coords, dtype=jnp.float32) / norm
    scores = []
    for label, pattern in prototypes:
        stored_coords = list(pattern[:4])
        while len(stored_coords) < 4:
            stored_coords.append(0)
        stored_norm = jnp.sqrt(jnp.sum(jnp.asarray(stored_coords, dtype=jnp.float32) ** 2))
        if float(stored_norm) == 0.0:
            scores.append((-1.0, label))
            continue
        stored = jnp.asarray(stored_coords, dtype=jnp.float32) / stored_norm
        real = stored[0] * q[0] + stored[1] * q[1] + stored[2] * q[2] + stored[3] * q[3]
        scores.append((float(real), label))
    best_score, best_label = max(scores, key=lambda item: item[0])
    quaternion.append(best_label if best_score > 0 else None)

runtime = {
    "python_version": sys.version.split()[0],
    "python_implementation": getattr(sys, "implementation", None).name,
    "jax_version": str(jax.__version__),
    "jaxlib_version": str(getattr(jax.lib, "__version__", "unknown")),
    "device_count": len(jax.devices()),
}
print(json.dumps({"runtime": runtime, "hopfield": hopfield, "quaternion": quaternion}, sort_keys=True))
'''
_JAX_CROSSING_SOURCE_SHA256 = hashlib.sha256(
    _JAX_CROSSING_SCRIPT.encode("utf-8")
).hexdigest()


def _jax_input(
    paths: list[dict[str, Any]], probes: list[str], quotient: dict[str, Any]
) -> tuple[dict[str, Any], list[tuple[str, tuple[int, ...]]]]:
    labels = [str(basin["id"]) for basin in quotient["basins"]]
    members = {str(basin["id"]): list(basin["members"]) for basin in quotient["basins"]}
    vectors = {
        path["id"]: _bipolar(path["observation"], probes) for path in paths
    }
    dim = len(next(iter(vectors.values())))
    prototypes: list[tuple[str, tuple[int, ...]]] = []
    for label in labels:
        acc = [0] * dim
        for path_id in members[label]:
            for index, bit in enumerate(vectors[path_id]):
                acc[index] += bit
        prototypes.append((label, _sign_vec(acc)))
    payload = {
        "vectors": [
            {"id": path["id"], "vector": list(vectors[path["id"]])}
            for path in paths
        ],
        "prototypes": [[label, list(pattern)] for label, pattern in prototypes],
    }
    return payload, prototypes


def _jax_crossing(
    paths: list[dict[str, Any]],
    probes: list[str],
    quotient: dict[str, Any],
    *,
    interpreter: Path | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    base = {
        "ran": False,
        "declared": interpreter is not None,
        "source_sha256": _JAX_CROSSING_SOURCE_SHA256,
    }
    if interpreter is None:
        return {"status": "HOLD", "reason": "JAX_INTERPRETER_UNDECLARED", **base}
    if not quotient.get("quotient_admitted"):
        return {"status": "HOLD", "reason": "NO_QUOTIENT", **base}
    try:
        resolved = interpreter.resolve(strict=True)
        if not resolved.is_file():
            raise OSError("not a regular file")
        # A venv's ``bin/python`` may resolve to the same system binary while
        # selecting a different ``sys.prefix``.  Compare the declared path,
        # not only its target, so a declared external environment remains
        # usable while the controller's own executable is refused.
        if interpreter.absolute() == Path(sys.executable).absolute():
            return {
                "status": "HOLD",
                "reason": "REFUSE_JAX_INTERPRETER_NOT_EXTERNAL",
                **base,
            }
        interpreter_sha256 = _sha256_bytes(resolved.read_bytes())
    except OSError as exc:
        return {
            "status": "HOLD",
            "reason": "JAX_INTERPRETER_UNREADABLE",
            "detail": type(exc).__name__,
            **base,
        }
    payload, prototypes = _jax_input(paths, probes, quotient)
    input_bytes = _canonical_bytes(payload)
    if len(input_bytes) > _MAX_INPUT_BYTES:
        return {
            "status": "HOLD",
            "reason": "JAX_INPUT_EXCEEDS_BOUND",
            "input_bytes": len(input_bytes),
            **base,
        }
    python_hopfield: list[str | None] = []
    python_quat: list[str | None] = []
    for item in payload["vectors"]:
        query = tuple(int(value) for value in item["vector"])
        python_state = _hopfield_recall(query, [pattern for _, pattern in prototypes])
        python_hopfield.append(
            _nearest_pattern(python_state, prototypes) if python_state else None
        )
        python_quat.append(_quaternion_recall(query, prototypes))
    try:
        completed = subprocess.run(
            [str(interpreter), "-I", "-c", _JAX_CROSSING_SCRIPT],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=float(timeout_seconds),
        )
    except FileNotFoundError:
        return {"status": "HOLD", "reason": "JAX_INTERPRETER_UNAVAILABLE", **base}
    except subprocess.TimeoutExpired:
        return {"status": "HOLD", "reason": "JAX_CROSSING_TIMEOUT", **base}
    if completed.returncode != 0:
        return {
            "status": "HOLD",
            "reason": "JAX_CROSSING_FAILED",
            "returncode": completed.returncode,
            "stderr_sha256": _sha256_bytes(bytes(completed.stderr or b"")),
            **base,
        }
    try:
        response = json.loads(bytes(completed.stdout).decode("utf-8"))
        if type(response) is not dict or set(response) != {"runtime", "hopfield", "quaternion"}:
            raise ValueError("response shape")
        runtime = response["runtime"]
        if type(runtime) is not dict:
            raise ValueError("runtime shape")
        expected_runtime_keys = {
            "python_version",
            "python_implementation",
            "jax_version",
            "jaxlib_version",
            "device_count",
        }
        if set(runtime) != expected_runtime_keys:
            raise ValueError("runtime fields")
        if any(type(runtime[key]) is not str for key in expected_runtime_keys - {"device_count"}):
            raise ValueError("runtime identity")
        if type(runtime["device_count"]) is not int or runtime["device_count"] <= 0:
            raise ValueError("runtime device count")
        if response["hopfield"] != python_hopfield or response["quaternion"] != python_quat:
            return {
                "status": "HOLD",
                "reason": "JAX_RESULT_DISAGREEMENT",
                **base,
            }
        runtime_sha256 = _sha256(runtime)
    except (ValueError, TypeError, json.JSONDecodeError):
        return {"status": "HOLD", "reason": "JAX_RESPONSE_INVALID", **base}
    return {
        "status": "PASS",
        "ran": True,
        "declared": True,
        "source_sha256": _JAX_CROSSING_SOURCE_SHA256,
        "runtime_sha256": runtime_sha256,
        "interpreter_sha256": interpreter_sha256,
        "interpreter_name": resolved.name,
        "input_sha256": _sha256_bytes(input_bytes),
        "runtime": runtime,
        "hopfield_agree": True,
        "quaternion_agree": True,
    }


def _iff_and(result_var: str, left: str, right: str) -> dict[str, Any]:
    return {
        "op": "or",
        "constraints": [
            {
                "op": "and",
                "constraints": [
                    {"op": "eq", "left": {"var": result_var}, "right": {"const": 1}},
                    {"op": "eq", "left": {"var": left}, "right": {"const": 1}},
                    {"op": "eq", "left": {"var": right}, "right": {"const": 1}},
                ],
            },
            {
                "op": "and",
                "constraints": [
                    {"op": "eq", "left": {"var": result_var}, "right": {"const": 0}},
                    {
                        "op": "or",
                        "constraints": [
                            {"op": "eq", "left": {"var": left}, "right": {"const": 0}},
                            {"op": "eq", "left": {"var": right}, "right": {"const": 0}},
                        ],
                    },
                ],
            },
        ],
    }


def _fact_eq(name: str, value: int) -> dict[str, Any]:
    return {"op": "eq", "left": {"var": name}, "right": {"const": value}}


def _smt_problems(facts: dict[str, int]) -> dict[str, Any]:
    variables = {
        "fact_hash_exact": [0, 1],
        "fact_hopfield_beats_hostile": [0, 1],
        "fact_spinor_beats_hostile": [0, 1],
        "fact_erased_hash_empty": [0, 1],
        "fact_erased_hopfield_empty": [0, 1],
        "fact_erased_spinor_empty": [0, 1],
        "fact_probe_restriction_entropy_only": [0, 1],
        "fact_some_mutation_changes_both": [0, 1],
        "admit_hash": [0, 1],
        "admit_hopfield": [0, 1],
        "admit_spinor": [0, 1],
        "admit_hostile": [0, 1],
        "admit_same_object": [0, 1],
    }
    common = [
        _fact_eq("admit_hostile", 0),
        _fact_eq("admit_same_object", 0),
        {
            "op": "eq",
            "left": {"var": "admit_hash"},
            "right": {"var": "fact_hash_exact"},
        },
        _iff_and(
            "admit_hopfield",
            "fact_hopfield_beats_hostile",
            "fact_erased_hopfield_empty",
        ),
        _iff_and(
            "admit_spinor",
            "fact_spinor_beats_hostile",
            "fact_erased_spinor_empty",
        ),
    ]
    real_constraints = [
        _fact_eq(name, value) for name, value in facts.items()
    ] + common
    real_constraints.append(
        {
            "op": "or",
            "constraints": [
                _fact_eq("admit_hash", 1),
                _fact_eq("admit_hopfield", 1),
                _fact_eq("admit_spinor", 1),
            ],
        }
    )
    erased_facts = dict(facts)
    erased_facts["fact_hash_exact"] = 0
    erased_facts["fact_hopfield_beats_hostile"] = 0
    erased_facts["fact_spinor_beats_hostile"] = 0
    erased_constraints = [
        _fact_eq(name, value) for name, value in erased_facts.items()
    ] + common
    erased_constraints.append(
        {
            "op": "or",
            "constraints": [
                _fact_eq("admit_hash", 1),
                _fact_eq("admit_hopfield", 1),
                _fact_eq("admit_spinor", 1),
            ],
        }
    )
    real = dual_solve({"variables": variables, "constraints": real_constraints})
    erased = dual_solve({"variables": variables, "constraints": erased_constraints})
    witnesses = real.get("witnesses") or {}
    agreed_witness = None
    if real.get("agree") and real.get("z3") == "BOUNDED_SAT":
        agreed_witness = witnesses.get("z3")
        if not (
            agreed_witness
            and witnesses.get("cvc5") == agreed_witness
            and witnesses.get("enumeration") == agreed_witness
        ):
            agreed_witness = None
    return {
        "real_memory": {
            "z3": real.get("z3"),
            "cvc5": real.get("cvc5"),
            "enumeration": real.get("enumeration"),
            "agree": bool(real.get("agree")),
            "witness": agreed_witness,
        },
        "erased_memory": {
            "z3": erased.get("z3"),
            "cvc5": erased.get("cvc5"),
            "enumeration": erased.get("enumeration"),
            "agree": bool(erased.get("agree")),
        },
        "facts": facts,
    }


def _delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "support_W": after["entropy"]["support_W"] - before["entropy"]["support_W"],
        "record_K": after["entropy"]["record_K"] - before["entropy"]["record_K"],
        "class_count": after["entropy"]["class_count"] - before["entropy"]["class_count"],
        "released_count": after["entropy"]["released_count"]
        - before["entropy"]["released_count"],
        "held_count": after["entropy"]["held_count"] - before["entropy"]["held_count"],
        "n_edges": after["topology"]["n_edges"] - before["topology"]["n_edges"],
        "n_weak_components": after["topology"]["n_weak_components"]
        - before["topology"]["n_weak_components"],
        "is_dag_changed": after["topology"]["is_dag"] != before["topology"]["is_dag"],
        "node_set_changed": before["topology"].get("nodes_sha256")
        != after["topology"].get("nodes_sha256"),
        "edge_set_changed": before["topology"].get("edges_sha256")
        != after["topology"].get("edges_sha256"),
    }


def _changes_entropy(delta: dict[str, Any]) -> bool:
    return (
        delta["support_W"] != 0
        or delta["record_K"] != 0.0
        or delta["class_count"] != 0
        or delta["released_count"] != 0
        or delta["held_count"] != 0
    )


def _changes_topology(delta: dict[str, Any]) -> bool:
    return (
        delta["n_edges"] != 0
        or delta["n_weak_components"] != 0
        or delta["is_dag_changed"]
        or delta["node_set_changed"]
        or delta["edge_set_changed"]
    )


def module_imports_jax_at_top_level() -> bool:
    tree = ast.parse(_HELPER_SOURCE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name.split(".", 1)[0] == "jax" for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] == "jax":
                return True
    return False


def _interpreter_sha256(interpreter: Path | None) -> str | None:
    if interpreter is None:
        return None
    try:
        return _sha256_bytes(interpreter.resolve(strict=True).read_bytes())
    except OSError as exc:
        raise PathMassError("jax_interpreter cannot be hashed") from exc


def _negative_controls(
    paths: list[dict[str, Any]],
    probes: tuple[str, ...],
    fixture_path: Path,
) -> list[dict[str, Any]]:
    """Run reason-specific refusal controls without writing authority."""

    packet = _bound_packet(paths, probes, "negative missing-row control")
    packet["rows"] = packet["rows"][:-1]
    missing = decide_bound_packet(packet)
    try:
        ConstraintPathMassRequest(probes=("unknown_probe",))
    except PathMassError as exc:
        unknown_status = "REFUSE"
        unknown_reason = "REFUSE_PROBE_OUTSIDE_VOCABULARY"
        unknown_detail = str(exc)
    else:  # pragma: no cover - defensive: the typed constructor must refuse it
        unknown_status = "FAIL"
        unknown_reason = "NEGATIVE_CONTROL_ACCEPTED"
        unknown_detail = None
    try:
        foreign = replace(reference_flow_policy(fixture_path), flow_id="foreign-flow")
        enumerate_policy_paths(foreign, reference_allowed_signals(fixture_path), fixture_path)
    except PathMassError as exc:
        foreign_status = "REFUSE"
        foreign_reason = "REFUSE_FOREIGN_MINILEV_FLOW"
        foreign_detail = str(exc)
    else:  # pragma: no cover - defensive: the policy validator must refuse it
        foreign_status = "FAIL"
        foreign_reason = "NEGATIVE_CONTROL_ACCEPTED"
        foreign_detail = None
    controls: list[dict[str, Any]] = [
        {
            "id": "missing_observation_row",
            "expected_status": "HOLD",
            "status": missing.get("status"),
            "reason_code": "REFUSE_UNBOUND_OBSERVATION",
            "observed_reason": missing.get("reason"),
            "authority": "none",
        },
        {
            "id": "unknown_probe_request",
            "expected_status": "REFUSE",
            "status": unknown_status,
            "reason_code": unknown_reason,
            "detail": unknown_detail,
            "authority": "none",
        },
        {
            "id": "foreign_policy_request",
            "expected_status": "REFUSE",
            "status": foreign_status,
            "reason_code": foreign_reason,
            "detail": foreign_detail,
            "authority": "none",
        },
    ]
    return controls


def _request_or_default(request: ConstraintPathMassRequest | None) -> ConstraintPathMassRequest:
    if request is None:
        return ConstraintPathMassRequest()
    if type(request) is not ConstraintPathMassRequest:
        raise PathMassError("request must be ConstraintPathMassRequest")
    return request


def run_constraint_path_mass(
    request: ConstraintPathMassRequest | None = None,
) -> dict[str, Any]:
    """Run one bounded operation and return a deterministic, hashed receipt."""

    request = _request_or_default(request)

    fixture_path = _fixture_path(request.fixture_path)
    fixture_sha256 = _sha256_bytes(fixture_path.read_bytes())
    policy = reference_flow_policy(fixture_path)
    allowed = reference_allowed_signals(fixture_path)
    if request.limits.max_steps != policy.max_steps:
        policy = replace(policy, max_steps=request.limits.max_steps)
    probes = request.probes
    baseline_paths = enumerate_policy_paths(policy, allowed, fixture_path)
    if len(baseline_paths) > request.limits.max_paths:
        raise PathMassError("reference path count exceeds the bounded request limit")
    baseline = _measure(
        baseline_paths,
        probes,
        "baseline Mini-Lev traces under the reference proposal policy",
    )
    independent: list[dict[str, Any]] = []
    both_changed = False
    probe_restriction_entropy_only = False
    mutation_catalog = {item["id"]: item for item in _mutations()}
    selected_mutations = [mutation_catalog[item] for item in request.mutation_ids]
    for mutation in selected_mutations:
        mutated_policy, mutated_probes = _apply_mutation(policy, probes, mutation)
        mutated_paths = enumerate_policy_paths(mutated_policy, allowed, fixture_path)
        if len(mutated_paths) > request.limits.max_paths:
            raise PathMassError(
                f"mutation {mutation['id']} exceeds the bounded path limit"
            )
        measured = _measure(
            mutated_paths, mutated_probes, f"after {mutation['id']}"
        )
        delta = _delta(baseline, measured)
        entropy_changed = _changes_entropy(delta)
        topology_changed = _changes_topology(delta)
        if entropy_changed and topology_changed:
            both_changed = True
        if (
            mutation["id"] == "restrict_probes_to_terminal"
            and entropy_changed
            and not topology_changed
        ):
            probe_restriction_entropy_only = True
        independent.append(
            {
                "mutation": mutation,
                "n_paths": measured["n_paths"],
                "entropy": measured["entropy"],
                "topology": {
                    key: measured["topology"][key]
                    for key in (
                        "n_nodes",
                        "n_edges",
                        "n_weak_components",
                        "is_dag",
                        "agree",
                    )
                },
                "mass": measured["mass"],
                "quotient_admitted": bool(
                    measured["quotient"].get("quotient_admitted")
                ),
                "delta_from_baseline": delta,
                "changes_entropy": entropy_changed,
                "changes_topology": topology_changed,
            }
        )

    ratchet: list[dict[str, Any]] = []
    current_policy = policy
    current_probes = probes
    previous = baseline
    for mutation_id in request.mutation_ids:
        mutation = mutation_catalog[mutation_id]
        current_policy, current_probes = _apply_mutation(
            current_policy, current_probes, mutation
        )
        current_paths = enumerate_policy_paths(current_policy, allowed, fixture_path)
        if len(current_paths) > request.limits.max_paths:
            raise PathMassError(
                f"ratchet {mutation_id} exceeds the bounded path limit"
            )
        measured = _measure(current_paths, current_probes, f"ratchet {mutation_id}")
        delta = _delta(previous, measured)
        ratchet.append(
            {
                "mutation_id": mutation_id,
                "n_paths": measured["n_paths"],
                "entropy": measured["entropy"],
                "topology": {
                    key: measured["topology"][key]
                    for key in (
                        "n_nodes",
                        "n_edges",
                        "n_weak_components",
                        "is_dag",
                    )
                },
                "mass": measured["mass"],
                "delta_from_previous": delta,
                "changes_entropy": _changes_entropy(delta),
                "changes_topology": _changes_topology(delta),
            }
        )
        previous = measured

    recall = _score_methods(
        baseline_paths, list(probes), baseline["quotient"], erased=False
    )
    erased = _score_methods(
        baseline_paths, list(probes), baseline["quotient"], erased=True
    )
    n_paths = recall.get("n_paths") or 0
    correct = recall.get("correct") or {}
    erased_survivors = erased.get("survivors") or {}
    facts = {
        "fact_hash_exact": int(
            recall.get("status") == "PASS" and correct.get("hash_lookup") == n_paths
        ),
        "fact_hopfield_beats_hostile": int(
            correct.get("scalar_hopfield", 0) > correct.get("hostile_random", 0)
        ),
        "fact_spinor_beats_hostile": int(
            correct.get("quaternion_recall", 0) > correct.get("hostile_random", 0)
        ),
        "fact_erased_hash_empty": int(erased_survivors.get("hash_lookup", 1) == 0),
        "fact_erased_hopfield_empty": int(
            erased_survivors.get("scalar_hopfield", 1) == 0
        ),
        "fact_erased_spinor_empty": int(
            erased_survivors.get("quaternion_recall", 1) == 0
        ),
        "fact_probe_restriction_entropy_only": int(probe_restriction_entropy_only),
        "fact_some_mutation_changes_both": int(both_changed),
    }
    smt = _smt_problems(facts)
    real = smt["real_memory"]
    erased_smt = smt["erased_memory"]
    topology_ok = bool(baseline["topology"].get("agree"))
    status = (
        "PASS"
        if (
            baseline["quotient"].get("status") == "PASS"
            and topology_ok
            and real["agree"]
            and real["z3"] == "BOUNDED_SAT"
            and real["witness"] is not None
            and erased_smt["agree"]
            and erased_smt["z3"] == "BOUNDED_UNSAT"
            and not module_imports_jax_at_top_level()
        )
        else "HOLD"
    )
    jax_info = _jax_crossing(
        baseline_paths,
        list(probes),
        baseline["quotient"],
        interpreter=request.jax_interpreter,
        timeout_seconds=request.limits.jax_timeout_seconds,
    )
    source_sha256 = _sha256_bytes(_HELPER_SOURCE_PATH.read_bytes())
    interpreter_sha256 = _interpreter_sha256(request.jax_interpreter)
    request_material = request.as_dict(
        interpreter_sha256=interpreter_sha256,
        fixture_sha256=fixture_sha256,
    )
    negative_controls = _negative_controls(baseline_paths, probes, fixture_path)
    payload: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "operation": OPERATION,
        "status": status,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "not": list(_NOT),
        "request": request_material,
        "request_sha256": _sha256(request_material),
        "generator": {
            "flow_id": FLOW_ID,
            "policy_sha256": _sha256(_policy_material(policy)),
            "fixture_sha256": fixture_sha256,
            "fixture_provenance": reference_fixture_material(fixture_path)["provenance"],
            "n_paths": len(baseline_paths),
            "allowed_signals": {
                node: [signal.value for signal in signals]
                for node, signals in allowed.items()
            },
            "limits": request.limits.as_dict(),
        },
        "probes": list(probes),
        "baseline": {
            "n_paths": baseline["n_paths"],
            "entropy": baseline["entropy"],
            "topology": {
                key: baseline["topology"][key]
                for key in (
                    "n_nodes",
                    "n_edges",
                    "n_weak_components",
                    "is_dag",
                    "agree",
                )
            },
            "mass": baseline["mass"],
            "quotient_admitted": bool(baseline["quotient"].get("quotient_admitted")),
            "class_count": baseline["entropy"]["class_count"],
            "packet_sha256": baseline.get("packet_sha256"),
        },
        "mutations": independent,
        "ratchet": ratchet,
        "recall": {"stored": recall, "erased": erased},
        "jax_crossing": jax_info,
        "negative_controls": negative_controls,
        "smt": smt,
        "disposition": real["witness"],
        "source_sha256": source_sha256,
        "replay": {
            "replayable": True,
            "operation": OPERATION,
            "request_sha256": _sha256(request_material),
            "source_sha256": source_sha256,
            "jax_interpreter_sha256": interpreter_sha256,
        },
    }
    if request.require_jax and jax_info.get("status") != "PASS":
        payload["status"] = "HOLD"
        payload["hold_reason"] = str(jax_info.get("reason", "JAX_CROSSING_NOT_VERIFIED"))
    if len(_canonical_bytes(payload)) > request.limits.max_receipt_bytes:
        raise PathMassError("receipt exceeds the bounded request limit")
    payload["receipt_sha256"] = _sha256(
        {key: value for key, value in payload.items() if key != "receipt_sha256"}
    )
    return payload


def replay_receipt(
    path: Path,
    *,
    jax_interpreter: Path | None = None,
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Re-run a stored receipt's typed request and compare exact content."""

    if not isinstance(path, Path) or not path.is_file():
        raise PathMassError("replay receipt path must be a regular pathlib.Path")
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PathMassError("replay receipt is not readable JSON") from exc
    if type(stored) is not dict or stored.get("schema") != RECEIPT_SCHEMA:
        raise PathMassError("replay receipt schema is unsupported")
    raw_request = stored.get("request")
    if type(raw_request) is not dict:
        raise PathMassError("replay receipt has no typed request")
    limits_raw = raw_request.get("limits")
    if type(limits_raw) is not dict:
        raise PathMassError("replay receipt has no bounded limits")
    selected_fixture = _fixture_path(fixture_path)
    stored_fixture_sha256 = raw_request.get("fixture_sha256")
    if stored_fixture_sha256 != _sha256_bytes(selected_fixture.read_bytes()):
        raise PathMassError("REPLAY_REFERENCE_FIXTURE_MISMATCH")
    try:
        request = ConstraintPathMassRequest(
            probes=tuple(raw_request["probes"]),
            mutation_ids=tuple(raw_request["mutation_ids"]),
            jax_interpreter=jax_interpreter,
            fixture_path=selected_fixture,
            require_jax=bool(raw_request["require_jax"]),
            limits=PathMassLimits(**limits_raw),
        )
    except (KeyError, TypeError, PathMassError) as exc:
        raise PathMassError("replay receipt request is invalid") from exc
    replayed = run_constraint_path_mass(request)
    stored_body = {
        key: value for key, value in stored.items() if key != "receipt_sha256"
    }
    replay_body = {
        key: value for key, value in replayed.items() if key != "receipt_sha256"
    }
    matches = stored_body == replay_body
    return {
        "schema": "constraintbox.constraint-path-mass.replay.v1",
        "status": "PASS" if matches else "HOLD",
        "reason": None if matches else "REPLAY_RECEIPT_MISMATCH",
        "stored_receipt_sha256": stored.get("receipt_sha256"),
        "replayed_receipt_sha256": replayed.get("receipt_sha256"),
        "request_sha256": replayed.get("request_sha256"),
        "source_sha256": replayed.get("source_sha256"),
        "promotion_allowed": False,
    }


def write_receipt(
    path: Path,
    request: ConstraintPathMassRequest | None = None,
) -> dict[str, Any]:
    if not isinstance(path, Path):
        raise PathMassError("receipt path must be pathlib.Path")
    receipt = run_constraint_path_mass(request)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=OPERATION)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("receipts/constraint_path_mass/v1/result.json"),
    )
    parser.add_argument(
        "--jax-python",
        type=Path,
        default=None,
        help="explicit external interpreter for the optional JAX crossing",
    )
    parser.add_argument(
        "--require-jax",
        action="store_true",
        help="HOLD unless the declared external JAX crossing passes",
    )
    args = parser.parse_args()
    try:
        request = ConstraintPathMassRequest(
            jax_interpreter=args.jax_python,
            require_jax=args.require_jax,
        )
        receipt = write_receipt(args.out, request)
    except PathMassError as exc:
        print(json.dumps({"status": "REFUSE", "reason": str(exc)}, sort_keys=True))
        return 3
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt_sha256": receipt["receipt_sha256"],
                "out": str(args.out),
                "n_paths": receipt["generator"]["n_paths"],
                "smt": {
                    "real": receipt["smt"]["real_memory"]["z3"],
                    "erased": receipt["smt"]["erased_memory"]["z3"],
                    "agree": receipt["smt"]["real_memory"]["agree"],
                },
                "jax": receipt["jax_crossing"].get("status"),
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
