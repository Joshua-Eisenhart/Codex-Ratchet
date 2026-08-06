from __future__ import annotations

import hashlib
import heapq
import importlib
import importlib.metadata
import platform
import re
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, canonical_json, parse_json_object
from .runtime_profiles import (
    LibraryRequirement,
    RuntimeProfile,
    RuntimeProfileError,
    load_runtime_profile_registry,
)


_NODE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_RUSTWORKX_MODULE_APIS = (
    "PyDiGraph",
    "is_directed_acyclic_graph",
    "topological_sort",
    "has_path",
)
_RUSTWORKX_GRAPH_APIS = (
    "add_nodes_from",
    "add_edges_from",
    "nodes",
    "edge_list",
)
_RUSTWORKX_APIS = (
    "PyDiGraph",
    "PyDiGraph.add_nodes_from",
    "PyDiGraph.add_edges_from",
    "PyDiGraph.nodes",
    "PyDiGraph.edge_list",
    "is_directed_acyclic_graph",
    "topological_sort",
    "has_path",
)
# This remains only as a receipt/API compatibility alias for consumers that
# previously rendered one local baseline.  It is not a gate: the controller
# owned core runtime-profile registry below supplies the actual version window.
_LEGACY_RUSTWORKX_BASELINE_VERSION = "0.17.1"
_HARD_MAX_NODES = 256
_HARD_MAX_EDGES = 4_096
_HARD_MAX_REQUIRED_REACHABILITY = 1_024


def _valid_node_name(value: object) -> bool:
    return isinstance(value, str) and _NODE_PATTERN.fullmatch(value) is not None


def _reference_graph_result(
    nodes: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
    required_reachability: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    """Small independent Kahn/DFS reference for the bounded graph claim."""

    outgoing = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for source, target in edges:
        outgoing[source].append(target)
        indegree[target] += 1
    for targets in outgoing.values():
        targets.sort()

    ready = [node for node in nodes if indegree[node] == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        source = heapq.heappop(ready)
        order.append(source)
        for target in outgoing[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)

    reachability: list[dict[str, object]] = []
    for source, target in required_reachability:
        frontier = [source]
        visited = {source}
        while frontier and target not in visited:
            current = frontier.pop()
            for child in outgoing[current]:
                if child not in visited:
                    visited.add(child)
                    frontier.append(child)
        reachability.append(
            {"source": source, "target": target, "reachable": target in visited}
        )

    acyclic = len(order) == len(nodes)
    return {
        "acyclic": acyclic,
        "canonical_topological_order": order if acyclic else None,
        "required_reachability": reachability,
    }


def _topological_order_is_valid(
    order: list[str],
    nodes: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
) -> bool:
    if len(order) != len(nodes) or set(order) != set(nodes):
        return False
    positions = {node: index for index, node in enumerate(order)}
    return all(positions[source] < positions[target] for source, target in edges)


def _bounded_items(value: object, maximum: int, operation: str) -> list[Any]:
    """Consume at most maximum plus one items from one engine result."""

    try:
        iterator = iter(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{operation} must return an iterable") from exc
    items: list[Any] = []
    for _ in range(maximum + 1):
        try:
            items.append(next(iterator))
        except StopIteration:
            break
    if len(items) > maximum:
        raise ValueError(f"{operation} result exceeds its controller bound")
    return items


class RuntimeIdentityError(RuntimeError):
    """The active Rustworkx binding cannot meet the declared graph contract."""


def _numeric_version(value: object, label: str) -> tuple[int, ...]:
    if not isinstance(value, str) or not value:
        raise RuntimeIdentityError(f"{label} must be a non-empty numeric version")
    parts = value.split(".")
    if any(not part.isascii() or not part.isdigit() for part in parts):
        raise RuntimeIdentityError(
            f"{label} must contain dot-separated decimal components"
        )
    return tuple(int(part) for part in parts)


def _version_in_requirement(
    observed: str,
    requirement: LibraryRequirement,
) -> bool:
    return (
        _numeric_version(requirement.minimum_version, "profile minimum version")
        <= _numeric_version(observed, "Rustworkx version")
        < _numeric_version(
            requirement.maximum_exclusive_version,
            "profile maximum version",
        )
    )


def _active_rustworkx_profile() -> tuple[RuntimeProfile, LibraryRequirement]:
    """Select the registry profile for this interpreter; never select Python."""

    try:
        registry = load_runtime_profile_registry()
    except RuntimeProfileError as exc:
        raise RuntimeIdentityError(
            f"ConstraintBox runtime-profile registry is unavailable: {exc}"
        ) from exc
    python_minor = (sys.version_info.major, sys.version_info.minor)
    profiles = [
        profile
        for profile in registry.profiles
        if profile.implementation == platform.python_implementation()
        and profile.python_minor == python_minor
    ]
    if len(profiles) != 1:
        raise RuntimeIdentityError(
            "active Python has no unambiguous ConstraintBox core profile"
        )
    profile = profiles[0]
    if sys.flags.optimize not in profile.allowed_optimization_levels:
        raise RuntimeIdentityError(
            "active Python optimization mode is outside its core profile"
        )
    if profile.require_hash_randomization and sys.flags.hash_randomization != 1:
        raise RuntimeIdentityError(
            "active Python hash-randomization mode is outside its core profile"
        )
    requirements = [
        requirement
        for requirement in profile.libraries
        if requirement.distribution == "rustworkx"
        and requirement.import_name == "rustworkx"
    ]
    if len(requirements) != 1:
        raise RuntimeIdentityError(
            "active core profile has no unambiguous Rustworkx requirement"
        )
    return profile, requirements[0]


def _version_window_evidence(requirement: LibraryRequirement) -> dict[str, str]:
    return {
        "minimum_inclusive": requirement.minimum_version,
        "maximum_exclusive": requirement.maximum_exclusive_version,
    }


def _module_artifact_observation(module: object, label: str) -> dict[str, Any]:
    try:
        origin = Path(getattr(module, "__file__")).resolve()
        spec_origin = Path(getattr(module.__spec__, "origin")).resolve()
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise RuntimeIdentityError(f"{label} origin is unavailable") from exc
    if origin != spec_origin or not origin.is_file():
        raise RuntimeIdentityError(f"{label} origin is invalid")
    try:
        payload = origin.read_bytes()
    except OSError as exc:
        raise RuntimeIdentityError(f"{label} cannot be read") from exc
    return {
        "origin": str(origin),
        "spec_origin": str(spec_origin),
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _distribution_paths(
    distribution: importlib.metadata.Distribution,
) -> set[Path]:
    try:
        files = distribution.files
        if files is None:
            raise RuntimeIdentityError(
                "Rustworkx distribution file inventory is unavailable"
            )
        paths = {
            Path(distribution.locate_file(item)).resolve() for item in files
        }
    except RuntimeIdentityError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise RuntimeIdentityError(
            "Rustworkx distribution file inventory is unreadable"
        ) from exc
    if not paths:
        raise RuntimeIdentityError("Rustworkx distribution file inventory is empty")
    return paths


def _require_distribution_artifact(
    artifact: dict[str, Any],
    distribution_paths: set[Path],
    label: str,
) -> None:
    origin = artifact.get("origin")
    spec_origin = artifact.get("spec_origin")
    try:
        observed = {Path(origin).resolve(), Path(spec_origin).resolve()}
    except (OSError, TypeError, ValueError) as exc:
        raise RuntimeIdentityError(f"{label} artifact origin is invalid") from exc
    if not observed.issubset(distribution_paths):
        raise RuntimeIdentityError(
            f"{label} artifact is not owned by the installed Rustworkx distribution"
        )


def _verify_compiled_function(compiled: object, name: str) -> object:
    value = getattr(compiled, name, None)
    if type(value) is not types.BuiltinFunctionType:
        raise RuntimeIdentityError(
            f"Rustworkx compiled callable type drift: {name}"
        )
    if getattr(value, "__name__", None) != name:
        raise RuntimeIdentityError(
            f"Rustworkx compiled callable identity drift: {name}"
        )
    return value


def _semantic_runtime_probe(
    rx: object,
    graph_type: type,
) -> dict[str, Any]:
    """Exercise the declared API on two tiny graphs before user graph input."""

    source, target = "cb_probe_source", "cb_probe_target"
    try:
        graph = graph_type()
        indices = _bounded_items(
            graph.add_nodes_from((source, target)),
            2,
            "runtime_probe.add_nodes_from",
        )
        if (
            len(indices) != 2
            or any(not isinstance(index, int) or isinstance(index, bool) for index in indices)
            or len(set(indices)) != 2
        ):
            raise RuntimeIdentityError("Rustworkx semantic probe node indices are invalid")
        source_index, target_index = indices
        edges = _bounded_items(
            graph.add_edges_from(
                ((source_index, target_index, None),)
            ),
            1,
            "runtime_probe.add_edges_from",
        )
        if len(edges) != 1:
            raise RuntimeIdentityError("Rustworkx semantic probe edge insertion failed")
        if _bounded_items(graph.nodes(), 2, "runtime_probe.nodes") != [source, target]:
            raise RuntimeIdentityError("Rustworkx semantic probe node readback failed")
        if _bounded_items(graph.edge_list(), 1, "runtime_probe.edge_list") != [
            (source_index, target_index)
        ]:
            raise RuntimeIdentityError("Rustworkx semantic probe edge readback failed")
        acyclic = rx.is_directed_acyclic_graph(graph)
        if type(acyclic) is not bool or not acyclic:
            raise RuntimeIdentityError("Rustworkx semantic probe acyclicity failed")
        order = _bounded_items(
            rx.topological_sort(graph),
            2,
            "runtime_probe.topological_sort",
        )
        if not _topological_order_is_valid(
            [
                source if index == source_index else target
                for index in order
                if index in {source_index, target_index}
            ],
            (source, target),
            ((source, target),),
        ):
            raise RuntimeIdentityError(
                "Rustworkx semantic probe topological sort failed"
            )
        forward = rx.has_path(graph, source_index, target_index)
        backward = rx.has_path(graph, target_index, source_index)
        if type(forward) is not bool or type(backward) is not bool:
            raise RuntimeIdentityError("Rustworkx semantic probe reachability type failed")
        if forward is not True or backward is not False:
            raise RuntimeIdentityError("Rustworkx semantic probe reachability failed")

        cyclic_graph = graph_type()
        cyclic_indices = _bounded_items(
            cyclic_graph.add_nodes_from((source, target)),
            2,
            "runtime_probe.cycle_add_nodes_from",
        )
        if len(cyclic_indices) != 2:
            raise RuntimeIdentityError("Rustworkx semantic probe cycle nodes failed")
        _bounded_items(
            cyclic_graph.add_edges_from(
                (
                    (cyclic_indices[0], cyclic_indices[1], None),
                    (cyclic_indices[1], cyclic_indices[0], None),
                )
            ),
            2,
            "runtime_probe.cycle_add_edges_from",
        )
        cyclic = rx.is_directed_acyclic_graph(cyclic_graph)
        if type(cyclic) is not bool or cyclic is not False:
            raise RuntimeIdentityError("Rustworkx semantic probe cycle detection failed")
    except RuntimeIdentityError:
        raise
    except Exception as exc:
        raise RuntimeIdentityError(
            f"Rustworkx semantic runtime probe raised {type(exc).__name__}: {exc}"
        ) from exc
    return {
        "acyclic_graph_is_dag": acyclic,
        "acyclic_topological_order_length": len(order),
        "forward_path": forward,
        "backward_path": backward,
        "cycle_graph_is_dag": cyclic,
    }


def _verify_rustworkx_runtime(rx: object) -> dict[str, Any]:
    """Bind Rustworkx to its installed distribution and exercise its API.

    Local origin and digest observations are retained in the receipt, but no
    known wheel, native-library digest, ABI size, or Python-wrapper bytecode is
    used as a policy input.  Compatibility comes from the active core profile
    and the actual graph operations below.
    """

    profile, requirement = _active_rustworkx_profile()
    try:
        observed_version = str(rx.__version__)
    except Exception as exc:
        raise RuntimeIdentityError(
            "Rustworkx version is unavailable during runtime verification"
        ) from exc
    if not _version_in_requirement(observed_version, requirement):
        raise RuntimeIdentityError("Rustworkx version is outside the core profile")
    try:
        distribution = importlib.metadata.distribution("rustworkx")
        distribution_version = str(distribution.version)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeIdentityError("Rustworkx distribution metadata is unavailable") from exc
    except Exception as exc:
        raise RuntimeIdentityError(
            "Rustworkx distribution metadata is unreadable"
        ) from exc
    if distribution_version != observed_version:
        raise RuntimeIdentityError(
            "Rustworkx module version does not match installed distribution metadata"
        )
    distribution_paths = _distribution_paths(distribution)
    module_artifact = _module_artifact_observation(rx, "Rustworkx module")
    _require_distribution_artifact(
        module_artifact,
        distribution_paths,
        "Rustworkx module",
    )
    compiled = importlib.import_module("rustworkx.rustworkx")
    compiled_artifact = _module_artifact_observation(
        compiled,
        "Rustworkx compiled module",
    )
    _require_distribution_artifact(
        compiled_artifact,
        distribution_paths,
        "Rustworkx compiled module",
    )

    graph_type = getattr(compiled, "PyDiGraph", None)
    if (
        type(graph_type) is not type
        or getattr(graph_type, "__name__", None) != "PyDiGraph"
        or getattr(rx, "PyDiGraph", None) is not graph_type
    ):
        raise RuntimeIdentityError("Rustworkx PyDiGraph binding drift")
    for method_name in _RUSTWORKX_GRAPH_APIS:
        if not callable(getattr(graph_type, method_name, None)):
            raise RuntimeIdentityError(
                f"Rustworkx graph method unavailable: {method_name}"
            )

    bindings: dict[str, dict[str, Any]] = {
        "PyDiGraph": {
            "module": getattr(graph_type, "__module__", None),
            "origin": compiled_artifact["origin"],
            "callable_type": type(graph_type).__name__,
            "methods": list(_RUSTWORKX_GRAPH_APIS),
        }
    }
    for api in ("is_directed_acyclic_graph", "topological_sort"):
        compiled_api = _verify_compiled_function(compiled, api)
        if getattr(rx, api, None) is not compiled_api:
            raise RuntimeIdentityError(
                f"Rustworkx compiled API binding drift: {api}"
            )
        bindings[api] = {
            "module": "rustworkx.rustworkx",
            "origin": compiled_artifact["origin"],
            "callable_type": type(compiled_api).__name__,
        }
    has_path = getattr(rx, "has_path", None)
    if (
        not callable(has_path)
        or getattr(has_path, "__module__", None) != "rustworkx"
        or getattr(has_path, "__name__", None) != "has_path"
    ):
        raise RuntimeIdentityError("Rustworkx has_path binding drift")
    bindings["has_path"] = {
        "module": getattr(has_path, "__module__", None),
        "origin": module_artifact["origin"],
        "callable_type": type(has_path).__name__,
    }
    semantic_probe = _semantic_runtime_probe(rx, graph_type)
    return {
        "schema": "constraintbox.workflow-graph-runtime.v2",
        "distribution": "rustworkx",
        "version": observed_version,
        "distribution_version": distribution_version,
        "runtime_profile_id": profile.profile_id,
        "compatible_version_window": _version_window_evidence(requirement),
        "module_artifact": module_artifact,
        "compiled_module_artifact": compiled_artifact,
        "compiled_module_origin": compiled_artifact["origin"],
        "artifact_sha256_is_policy_input": False,
        "api_bindings": bindings,
        "semantic_probe": semantic_probe,
    }


@dataclass(frozen=True)
class WorkflowGraphProfile:
    """Check one controller-bounded formal-agent prerequisite graph."""

    required_reachability: tuple[tuple[str, str], ...] = ()
    max_nodes: int = 64
    max_edges: int = 256
    # Compatibility alias for existing Mini-Lev receipts.  The actual
    # acceptance authority is the active core profile's version window.
    required_version: str = _LEGACY_RUSTWORKX_BASELINE_VERSION
    profile_id: str = "constraintbox.workflow.rustworkx.dag.v1"
    claim_ceiling: str = (
        "one finite declared workflow dependency graph was checked for "
        "acyclicity and controller-required reachability; no semantic node "
        "or general workflow-correctness claim"
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.max_nodes, int)
            or isinstance(self.max_nodes, bool)
            or self.max_nodes < 1
            or self.max_nodes > _HARD_MAX_NODES
        ):
            raise ValueError(
                f"max_nodes must be an integer from 1 to {_HARD_MAX_NODES}"
            )
        if (
            not isinstance(self.max_edges, int)
            or isinstance(self.max_edges, bool)
            or self.max_edges < 0
            or self.max_edges > _HARD_MAX_EDGES
        ):
            raise ValueError(
                f"max_edges must be an integer from 0 to {_HARD_MAX_EDGES}"
            )
        if self.required_version != _LEGACY_RUSTWORKX_BASELINE_VERSION:
            raise ValueError(
                "required_version is a legacy receipt alias and must be "
                f"{_LEGACY_RUSTWORKX_BASELINE_VERSION!r}"
            )
        pairs = self.required_reachability
        if (
            not isinstance(pairs, tuple)
            or any(
                not isinstance(pair, tuple)
                or len(pair) != 2
                or not _valid_node_name(pair[0])
                or not _valid_node_name(pair[1])
                or pair[0] == pair[1]
                for pair in pairs
            )
        ):
            raise ValueError(
                "required_reachability must contain distinct two-name tuples"
            )
        if len(pairs) > _HARD_MAX_REQUIRED_REACHABILITY:
            raise ValueError(
                "required_reachability exceeds the hard pair limit "
                f"of {_HARD_MAX_REQUIRED_REACHABILITY}"
            )
        if len(set(pairs)) != len(pairs) or pairs != tuple(sorted(pairs)):
            raise ValueError(
                "required_reachability must be unique and canonically sorted"
            )

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "strict_intake_failed",
                {"error": str(exc)},
            )
        if set(body) != {"nodes", "edges"}:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_contract_keys_mismatch",
                {
                    "expected_keys": ["edges", "nodes"],
                    "observed_keys": sorted(body),
                },
            )

        raw_nodes = body["nodes"]
        if (
            not isinstance(raw_nodes, list)
            or not raw_nodes
            or any(not _valid_node_name(node) for node in raw_nodes)
            or len(set(raw_nodes)) != len(raw_nodes)
            or raw_nodes != sorted(raw_nodes)
        ):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_nodes_invalid",
                {
                    "requirements": (
                        "non-empty, unique, canonically sorted strings matching "
                        "[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"
                    )
                },
            )
        nodes = tuple(raw_nodes)
        if len(nodes) > self.max_nodes:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_node_limit_exceeded",
                {"observed_nodes": len(nodes), "max_nodes": self.max_nodes},
            )

        raw_edges = body["edges"]
        if not isinstance(raw_edges, list):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_edges_invalid",
                {"requirements": "a canonically sorted list of unique node pairs"},
            )
        node_set = set(nodes)
        edge_items: list[tuple[str, str]] = []
        for edge in raw_edges:
            if (
                not isinstance(edge, list)
                or len(edge) != 2
                or not _valid_node_name(edge[0])
                or not _valid_node_name(edge[1])
                or edge[0] not in node_set
                or edge[1] not in node_set
            ):
                return ProfileOutcome(
                    Disposition.BLOCKED,
                    "workflow_graph_edges_invalid",
                    {
                        "requirements": (
                            "each edge is a two-name list whose endpoints are "
                            "declared nodes"
                        )
                    },
                )
            edge_items.append((edge[0], edge[1]))
        if (
            len(set(edge_items)) != len(edge_items)
            or edge_items != sorted(edge_items)
        ):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_edges_invalid",
                {"requirements": "edges must be unique and canonically sorted"},
            )
        edges = tuple(edge_items)
        if len(edges) > self.max_edges:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_edge_limit_exceeded",
                {"observed_edges": len(edges), "max_edges": self.max_edges},
            )

        missing_required_nodes = sorted(
            {
                node
                for pair in self.required_reachability
                for node in pair
                if node not in node_set
            }
        )
        if missing_required_nodes:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_required_node_missing",
                {"missing_nodes": missing_required_nodes},
            )

        canonical_graph = {
            "nodes": list(nodes),
            "edges": [list(edge) for edge in edges],
        }
        reference = _reference_graph_result(
            nodes, edges, self.required_reachability
        )
        pre_tool_evidence: dict[str, Any] = {
            "schema": "constraintbox.workflow-graph.evidence.v1",
            "tool": {
                "name": "rustworkx",
                "version": None,
                "required_version": self.required_version,
                "apis": list(_RUSTWORKX_APIS),
            },
            "canonical_graph": canonical_graph,
            "canonical_graph_sha256": hashlib.sha256(
                canonical_json(canonical_graph)
            ).hexdigest(),
            "reference_result": reference,
            "profile_source_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "limits": {
                "max_nodes": self.max_nodes,
                "max_edges": self.max_edges,
                "hard_max_nodes": _HARD_MAX_NODES,
                "hard_max_edges": _HARD_MAX_EDGES,
                "hard_max_required_reachability": (
                    _HARD_MAX_REQUIRED_REACHABILITY
                ),
            },
            "required_reachability": [
                list(pair) for pair in self.required_reachability
            ],
            "claim_ceiling": self.claim_ceiling,
        }
        try:
            rx = importlib.import_module("rustworkx")
        except ModuleNotFoundError as exc:
            evidence = {
                **pre_tool_evidence,
                "phase": "module_import",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "missing_module": exc.name,
            }
            if exc.name == "rustworkx":
                return ProfileOutcome(
                    Disposition.PARKED,
                    "rustworkx_unavailable",
                    evidence,
                )
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_import_error",
                evidence,
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_import_error",
                {
                    **pre_tool_evidence,
                    "phase": "module_import",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

        try:
            rustworkx_version = str(rx.__version__)
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_version_inspection_error",
                {
                    **pre_tool_evidence,
                    "phase": "version_inspection",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        try:
            runtime_profile, rustworkx_requirement = (
                _active_rustworkx_profile()
            )
            version_matches_policy = _version_in_requirement(
                rustworkx_version,
                rustworkx_requirement,
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_runtime_profile_error",
                {
                    **pre_tool_evidence,
                    "phase": "runtime_profile_selection",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        tool_evidence = {
            **pre_tool_evidence,
            "tool": {
                **pre_tool_evidence["tool"],
                "version": rustworkx_version,
                "runtime_profile_id": runtime_profile.profile_id,
                "compatible_version_window": _version_window_evidence(
                    rustworkx_requirement
                ),
                "version_matches_policy": version_matches_policy,
                "version_matches_legacy_baseline": (
                    rustworkx_version == self.required_version
                ),
            },
        }
        if not version_matches_policy:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_version_drift",
                tool_evidence,
            )
        try:
            missing_apis = [
                api
                for api in _RUSTWORKX_MODULE_APIS
                if not callable(getattr(rx, api, None))
            ]
            graph_type = getattr(rx, "PyDiGraph", None)
            if callable(graph_type):
                missing_apis.extend(
                    f"PyDiGraph.{api}"
                    for api in _RUSTWORKX_GRAPH_APIS
                    if not callable(getattr(graph_type, api, None))
                )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_api_inspection_error",
                {
                    **tool_evidence,
                    "phase": "api_inspection",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        if missing_apis:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_runtime_api_drift",
                {**tool_evidence, "missing_apis": missing_apis},
            )
        try:
            runtime_identity_before = _verify_rustworkx_runtime(rx)
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_runtime_identity_error",
                {
                    **tool_evidence,
                    "phase": "runtime_identity_pre_operation",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        tool_evidence["runtime_identity"] = runtime_identity_before

        operation = "PyDiGraph"
        try:
            graph = rx.PyDiGraph()
            operation = "PyDiGraph.add_nodes_from"
            indices = tuple(
                _bounded_items(
                    graph.add_nodes_from(nodes),
                    self.max_nodes,
                    operation,
                )
            )
            if (
                len(indices) != len(nodes)
                or any(
                    not isinstance(index, int) or isinstance(index, bool)
                    for index in indices
                )
                or len(set(indices)) != len(indices)
            ):
                raise ValueError(
                    "PyDiGraph.add_nodes_from returned invalid node indices"
                )
            node_indices = dict(zip(nodes, indices, strict=True))
            operation = "PyDiGraph.add_edges_from"
            edge_indices = _bounded_items(
                graph.add_edges_from(
                    [
                        (node_indices[source], node_indices[target], None)
                        for source, target in edges
                    ]
                ),
                self.max_edges,
                operation,
            )
            if (
                len(edge_indices) != len(edges)
                or any(
                    not isinstance(index, int) or isinstance(index, bool)
                    for index in edge_indices
                )
                or len(set(edge_indices)) != len(edge_indices)
            ):
                raise ValueError(
                    "PyDiGraph.add_edges_from returned invalid edge indices"
                )
            operation = "PyDiGraph.nodes"
            observed_nodes = _bounded_items(
                graph.nodes(),
                self.max_nodes,
                operation,
            )
            if observed_nodes != list(nodes):
                raise ValueError(
                    "PyDiGraph.nodes disagrees with the declared node sequence"
                )
            operation = "PyDiGraph.edge_list"
            observed_index_edges = _bounded_items(
                graph.edge_list(),
                self.max_edges,
                operation,
            )
            index_to_node = {
                index: node for node, index in node_indices.items()
            }
            observed_edges: list[tuple[str, str]] = []
            for edge in observed_index_edges:
                if (
                    not isinstance(edge, tuple)
                    or len(edge) != 2
                    or any(
                        not isinstance(index, int) or isinstance(index, bool)
                        for index in edge
                    )
                    or edge[0] not in index_to_node
                    or edge[1] not in index_to_node
                ):
                    raise TypeError(
                        "PyDiGraph.edge_list returned an invalid edge"
                    )
                observed_edges.append(
                    (index_to_node[edge[0]], index_to_node[edge[1]])
                )
            if sorted(observed_edges) != list(edges):
                raise ValueError(
                    "PyDiGraph.edge_list disagrees with the declared edges"
                )
            operation = "is_directed_acyclic_graph"
            acyclic_result = rx.is_directed_acyclic_graph(graph)
            if type(acyclic_result) is not bool:
                raise TypeError(
                    "is_directed_acyclic_graph must return one boolean"
                )
            rustworkx_acyclic = acyclic_result
            rustworkx_order: list[str] | None = None
            rustworkx_order_valid: bool | None = None
            if rustworkx_acyclic:
                operation = "topological_sort"
                raw_order = _bounded_items(
                    rx.topological_sort(graph),
                    self.max_nodes,
                    operation,
                )
                if (
                    len(raw_order) != len(nodes)
                    or any(
                        not isinstance(index, int) or isinstance(index, bool)
                        for index in raw_order
                    )
                    or len(set(raw_order)) != len(raw_order)
                    or any(index not in index_to_node for index in raw_order)
                ):
                    raise ValueError(
                        "topological_sort returned invalid node indices"
                    )
                rustworkx_order = [
                    index_to_node[index] for index in raw_order
                ]
                rustworkx_order_valid = _topological_order_is_valid(
                    rustworkx_order, nodes, edges
                )
            rustworkx_reachability = []
            for source, target in self.required_reachability:
                operation = "has_path"
                path_result = rx.has_path(
                    graph,
                    node_indices[source],
                    node_indices[target],
                )
                if type(path_result) is not bool:
                    raise TypeError("has_path must return one boolean")
                rustworkx_reachability.append(
                    {
                        "source": source,
                        "target": target,
                        "reachable": path_result,
                    }
                )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_operation_error",
                {
                    **tool_evidence,
                    "operation": operation,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

        try:
            runtime_identity_after = _verify_rustworkx_runtime(rx)
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_runtime_identity_error",
                {
                    **tool_evidence,
                    "phase": "runtime_identity_post_operation",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        if runtime_identity_after != runtime_identity_before:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "rustworkx_runtime_identity_drift",
                {
                    **tool_evidence,
                    "runtime_identity_post_operation": runtime_identity_after,
                },
            )
        tool_evidence["runtime_identity_post_operation"] = (
            runtime_identity_after
        )

        rustworkx_result = {
            "acyclic": rustworkx_acyclic,
            "topological_order_valid": rustworkx_order_valid,
            "required_reachability": rustworkx_reachability,
        }
        disagreements: list[str] = []
        if rustworkx_acyclic != reference["acyclic"]:
            disagreements.append("acyclicity")
        if rustworkx_acyclic and rustworkx_order_valid is not True:
            disagreements.append("topological_order")
        if rustworkx_reachability != reference["required_reachability"]:
            disagreements.append("required_reachability")

        canonical_result = {
            "rustworkx": rustworkx_result,
            "reference": reference,
        }
        evidence: dict[str, Any] = {
            **tool_evidence,
            "canonical_result": canonical_result,
            "canonical_result_sha256": hashlib.sha256(
                canonical_json(canonical_result)
            ).hexdigest(),
        }
        if disagreements:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_engine_reference_disagreement",
                {**evidence, "disagreements": disagreements},
            )
        if not reference["acyclic"]:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_cycle_detected",
                evidence,
            )
        missing_reachability = [
            item
            for item in reference["required_reachability"]
            if not item["reachable"]
        ]
        if missing_reachability:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "workflow_graph_required_reachability_missing",
                {**evidence, "missing_reachability": missing_reachability},
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "workflow_graph_obligations_satisfied",
            evidence,
        )
