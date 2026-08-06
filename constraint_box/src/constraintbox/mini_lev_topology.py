"""Controller-owned Rustworkx preflight for fixed Mini-Lev policies.

This is deliberately not a general workflow configuration surface.  A
controller constructs one fixed profile from source literals, derives a
node-only projection that excludes ``RETRY`` transitions, and retains the
actual Rustworkx/reference evidence in a canonical witness.  The helper does
not choose transitions, terminals, or promotions; :mod:`mini_levos` remains
the authority for those decisions.
"""

from __future__ import annotations

import hashlib
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import workflow_graph as _workflow_graph_module
from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, canonical_json, parse_json_object
from .mini_levos import (
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookSignal,
    MiniLevError,
    handler_code_sha256,
)
from .runtime_profiles import (
    LibraryRequirement,
    RuntimeProfileError,
    load_runtime_profile_registry,
)
from .workflow_graph import WorkflowGraphProfile


_SHA256 = hashlib.sha256
_HELPER_SOURCE_PATH = Path(__file__).resolve()
_HELPER_SOURCE_SHA256 = _SHA256(_HELPER_SOURCE_PATH.read_bytes()).hexdigest()
_WORKFLOW_GRAPH_SOURCE_PATH = Path(_workflow_graph_module.__file__).resolve()
_WORKFLOW_GRAPH_SOURCE_SHA256 = _SHA256(
    _WORKFLOW_GRAPH_SOURCE_PATH.read_bytes()
).hexdigest()
_WORKFLOW_GRAPH_EVALUATE_CODE_SHA256 = handler_code_sha256(
    WorkflowGraphProfile.evaluate
)


def _rustworkx_profile_contract() -> tuple[str, dict[str, str]]:
    """Read the active core profile's graph-library contract.

    A Mini-Lev receipt must bind to the active profile ID and version window,
    not to one Rustworkx wheel's patch version.  This still fails closed when
    the registry is malformed, the active Python has no profile, or the
    profile lacks the declared graph library.
    """

    try:
        registry = load_runtime_profile_registry()
    except RuntimeProfileError as exc:
        raise MiniLevTopologyError(
            f"topology runtime-profile registry unavailable: {exc}"
        ) from exc
    candidates = [
        profile
        for profile in registry.profiles
        if profile.implementation == platform.python_implementation()
        and profile.python_minor == (sys.version_info.major, sys.version_info.minor)
    ]
    if len(candidates) != 1:
        raise MiniLevTopologyError(
            "topology active Python has no unambiguous core profile"
        )
    requirement_candidates: list[LibraryRequirement] = [
        requirement
        for requirement in candidates[0].libraries
        if requirement.distribution == "rustworkx"
        and requirement.import_name == "rustworkx"
    ]
    if len(requirement_candidates) != 1:
        raise MiniLevTopologyError(
            "topology active core profile lacks an unambiguous Rustworkx requirement"
        )
    requirement = requirement_candidates[0]
    return candidates[0].profile_id, {
        "minimum_inclusive": requirement.minimum_version,
        "maximum_exclusive": requirement.maximum_exclusive_version,
    }


def _numeric_version(value: object) -> tuple[int, ...] | None:
    if not isinstance(value, str) or not value:
        return None
    parts = value.split(".")
    if any(not part.isascii() or not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _version_in_window(value: object, window: dict[str, str]) -> bool:
    observed = _numeric_version(value)
    minimum = _numeric_version(window.get("minimum_inclusive"))
    maximum = _numeric_version(window.get("maximum_exclusive"))
    return (
        observed is not None
        and minimum is not None
        and maximum is not None
        and minimum <= observed < maximum
    )


class MiniLevTopologyError(RuntimeError):
    """A fixed controller topology could not be projected or checked."""


@dataclass(frozen=True)
class TopologyPreflightResult:
    """One controller-selected topology check and its retained material."""

    projection: dict[str, Any]
    projection_sha256: str
    profile_identity: dict[str, Any]
    profile_outcome: dict[str, Any]
    evaluation_executed: bool
    signal: HookSignal


@dataclass(frozen=True)
class FixedMiniLevTopology:
    """One source-owned Rustworkx profile for a fixed Mini-Lev flow.

    The constructor is a code-level controller seam only.  Nothing in this
    module parses model or user graph settings: ``FlowPolicy`` and this
    profile are both already frozen by the controller before the hook runs.
    """

    required_reachability: tuple[tuple[str, str], ...]
    max_nodes: int
    max_edges: int
    profile: WorkflowGraphProfile = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # WorkflowGraphProfile owns the strict bounds, canonical ordering, and
        # pinned Rustworkx version validation.  Keeping it here prevents an
        # adapter from quietly using a weaker graph contract.
        object.__setattr__(
            self,
            "profile",
            WorkflowGraphProfile(
                required_reachability=self.required_reachability,
                max_nodes=self.max_nodes,
                max_edges=self.max_edges,
            ),
        )

    @staticmethod
    def _source_sha256(path: Path) -> str:
        try:
            return _SHA256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise MiniLevTopologyError(
                f"topology source is unavailable: {path}"
            ) from exc

    @staticmethod
    def _canonical_object(value: object, where: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise MiniLevTopologyError(f"{where} must be a JSON object")
        try:
            return parse_json_object(canonical_json(value))
        except (IntakeError, TypeError, ValueError) as exc:
            raise MiniLevTopologyError(
                f"{where} is not finite canonical JSON: {exc}"
            ) from exc

    @classmethod
    def canonical_sha256(cls, value: object, where: str) -> str:
        return _SHA256(canonical_json(cls._canonical_object(value, where))).hexdigest()

    def projection_from_policy(self, policy: FlowPolicy) -> dict[str, Any]:
        """Return the fixed policy's internal node projection without retries.

        Declared terminal targets are intentionally outside the node-only
        graph; every other undeclared endpoint is a malformed policy, not an
        edge to silently omit.
        """

        if type(policy) is not FlowPolicy:
            raise MiniLevTopologyError("topology policy is not a FlowPolicy")
        if type(policy.nodes) is not tuple:
            raise MiniLevTopologyError("topology policy nodes are invalid")
        if type(policy.transitions) is not tuple:
            raise MiniLevTopologyError("topology policy transitions are invalid")
        if type(policy.terminal_nodes) is not tuple:
            raise MiniLevTopologyError("topology policy terminals are invalid")
        nodes: list[str] = []
        for node in policy.nodes:
            if type(node) is not FlowNode or not isinstance(node.node_id, str):
                raise MiniLevTopologyError("topology policy node is invalid")
            nodes.append(node.node_id)
        nodes.sort()
        if len(nodes) != len(set(nodes)) or not nodes:
            raise MiniLevTopologyError("topology policy nodes are invalid")
        node_set = set(nodes)
        terminals = set(policy.terminal_nodes)
        if (
            not terminals
            or len(terminals) != len(policy.terminal_nodes)
            or any(not isinstance(node, str) for node in terminals)
            or terminals & node_set
        ):
            raise MiniLevTopologyError("topology policy terminals are invalid")
        edges: list[tuple[str, str]] = []
        seen_transitions: set[tuple[str, HookSignal]] = set()
        for transition in policy.transitions:
            if type(transition) is not FlowTransition:
                raise MiniLevTopologyError("topology policy transition is invalid")
            if not isinstance(transition.from_node, str) or (
                transition.from_node not in node_set
            ):
                raise MiniLevTopologyError(
                    "topology policy transition source is undeclared"
                )
            if not isinstance(transition.signal, HookSignal):
                raise MiniLevTopologyError(
                    "topology policy transition signal is invalid"
                )
            if not isinstance(transition.to_node, str) or (
                transition.to_node not in node_set
                and transition.to_node not in terminals
            ):
                raise MiniLevTopologyError(
                    "topology policy transition target is undeclared"
                )
            transition_key = (transition.from_node, transition.signal)
            if transition_key in seen_transitions:
                raise MiniLevTopologyError("topology policy transition is duplicated")
            seen_transitions.add(transition_key)
            if transition.signal is HookSignal.RETRY:
                if transition.to_node not in node_set:
                    raise MiniLevTopologyError(
                        "topology policy RETRY target is not a flow node"
                    )
                continue
            if transition.to_node in node_set:
                edges.append((transition.from_node, transition.to_node))
        edges.sort()
        if len(edges) != len(set(edges)):
            raise MiniLevTopologyError(
                "topology policy has duplicate projection edges"
            )
        return {
            "nodes": nodes,
            "edges": [list(edge) for edge in edges],
        }

    def projection_from_receipt_policy(
        self,
        policy: object,
    ) -> dict[str, Any]:
        """Reconstruct the same strict projection from a replayed policy."""

        if not isinstance(policy, dict):
            raise MiniLevTopologyError("receipt policy is not an object")
        raw_nodes = policy.get("nodes")
        raw_transitions = policy.get("transitions")
        raw_terminals = policy.get("terminal_nodes")
        if (
            not isinstance(raw_nodes, list)
            or not isinstance(raw_transitions, list)
            or not isinstance(raw_terminals, list)
        ):
            raise MiniLevTopologyError("receipt policy topology fields are missing")
        nodes: list[str] = []
        for raw_node in raw_nodes:
            if not isinstance(raw_node, dict) or set(raw_node) != {
                "node_id",
                "hook_id",
            }:
                raise MiniLevTopologyError("receipt policy node is malformed")
            node_id = raw_node.get("node_id")
            if not isinstance(node_id, str):
                raise MiniLevTopologyError("receipt policy node id is malformed")
            nodes.append(node_id)
        nodes.sort()
        if not nodes or len(nodes) != len(set(nodes)):
            raise MiniLevTopologyError("receipt policy nodes are invalid")
        node_set = set(nodes)
        terminals = set(raw_terminals)
        if (
            not terminals
            or len(terminals) != len(raw_terminals)
            or any(not isinstance(node, str) for node in terminals)
            or terminals & node_set
        ):
            raise MiniLevTopologyError("receipt policy terminals are invalid")
        edges: list[tuple[str, str]] = []
        known_signals = {hook_signal.value for hook_signal in HookSignal}
        seen_transitions: set[tuple[str, str]] = set()
        for transition in raw_transitions:
            if not isinstance(transition, dict) or set(transition) != {
                "from_node",
                "signal",
                "to_node",
            }:
                raise MiniLevTopologyError("receipt policy transition is malformed")
            source = transition.get("from_node")
            signal = transition.get("signal")
            target = transition.get("to_node")
            if (
                not isinstance(source, str)
                or not isinstance(signal, str)
                or not isinstance(target, str)
            ):
                raise MiniLevTopologyError(
                    "receipt policy transition fields are invalid"
                )
            if source not in node_set:
                raise MiniLevTopologyError(
                    "receipt policy transition source is undeclared"
                )
            if signal not in known_signals:
                raise MiniLevTopologyError(
                    "receipt policy transition signal is invalid"
                )
            if target not in node_set and target not in terminals:
                raise MiniLevTopologyError(
                    "receipt policy transition target is undeclared"
                )
            transition_key = (source, signal)
            if transition_key in seen_transitions:
                raise MiniLevTopologyError("receipt policy transition is duplicated")
            seen_transitions.add(transition_key)
            if signal == HookSignal.RETRY.value:
                if target not in node_set:
                    raise MiniLevTopologyError(
                        "receipt policy RETRY target is not a flow node"
                    )
                continue
            if target in node_set:
                edges.append((source, target))
        edges.sort()
        if len(edges) != len(set(edges)):
            raise MiniLevTopologyError(
                "receipt policy has duplicate projection edges"
            )
        return {"nodes": nodes, "edges": [list(edge) for edge in edges]}

    def profile_identity(self) -> dict[str, Any]:
        """Capture the evaluator identity before any Rustworkx operation."""

        source_path = Path(_workflow_graph_module.__file__).resolve()
        source_sha256: str | None = None
        helper_source_path = Path(__file__).resolve()
        helper_source_sha256: str | None = None
        evaluate_code_sha256: str | None = None
        errors: list[str] = []
        try:
            source_sha256 = self._source_sha256(source_path)
        except MiniLevTopologyError as exc:
            errors.append(str(exc))
        try:
            helper_source_sha256 = self._source_sha256(helper_source_path)
        except MiniLevTopologyError as exc:
            errors.append(str(exc))
        try:
            evaluate_code_sha256 = handler_code_sha256(WorkflowGraphProfile.evaluate)
        except MiniLevError as exc:
            errors.append(f"workflow evaluator code identity unavailable: {exc}")
        profile = self.profile
        profile_config_matches = (
            type(profile) is WorkflowGraphProfile
            and profile.profile_id == "constraintbox.workflow.rustworkx.dag.v1"
            and profile.required_reachability == self.required_reachability
            and profile.max_nodes == self.max_nodes
            and profile.max_edges == self.max_edges
        )
        identity_verified = (
            source_path == _WORKFLOW_GRAPH_SOURCE_PATH
            and source_sha256 == _WORKFLOW_GRAPH_SOURCE_SHA256
            and helper_source_path == _HELPER_SOURCE_PATH
            and helper_source_sha256 == _HELPER_SOURCE_SHA256
            and evaluate_code_sha256 == _WORKFLOW_GRAPH_EVALUATE_CODE_SHA256
            and profile_config_matches
        )
        return {
            "class": "constraintbox.workflow_graph.WorkflowGraphProfile",
            "profile_id": profile.profile_id,
            "required_version": profile.required_version,
            "required_reachability": [
                list(pair) for pair in profile.required_reachability
            ],
            "max_nodes": profile.max_nodes,
            "max_edges": profile.max_edges,
            "claim_ceiling": profile.claim_ceiling,
            "source_path": str(source_path),
            "source_sha256": source_sha256,
            "helper_source_path": str(helper_source_path),
            "helper_source_sha256": helper_source_sha256,
            "evaluate_code_sha256": evaluate_code_sha256,
            "expected_source_sha256": _WORKFLOW_GRAPH_SOURCE_SHA256,
            "expected_helper_source_sha256": _HELPER_SOURCE_SHA256,
            "expected_evaluate_code_sha256": _WORKFLOW_GRAPH_EVALUATE_CODE_SHA256,
            "profile_config_matches": profile_config_matches,
            "identity_verified": identity_verified,
            "identity_errors": errors,
        }

    def expected_reachability(self) -> list[dict[str, object]]:
        return [
            {"source": source, "target": target, "reachable": True}
            for source, target in self.required_reachability
        ]

    def eligible_evidence(
        self,
        evidence: dict[str, Any],
        projection: dict[str, Any],
        projection_sha256: str,
    ) -> bool:
        """Accept an eligible result only with actual matching tool evidence."""

        if evidence.get("canonical_graph") != projection:
            return False
        if evidence.get("canonical_graph_sha256") != projection_sha256:
            return False
        if evidence.get("profile_source_sha256") != _WORKFLOW_GRAPH_SOURCE_SHA256:
            return False
        expected_reachability = self.expected_reachability()
        if evidence.get("required_reachability") != [
            list(pair) for pair in self.required_reachability
        ]:
            return False
        try:
            runtime_profile_id, version_window = _rustworkx_profile_contract()
        except MiniLevTopologyError:
            return False
        tool = evidence.get("tool")
        if not isinstance(tool, dict) or (
            tool.get("name") != "rustworkx"
            or tool.get("required_version") != self.profile.required_version
            or tool.get("runtime_profile_id") != runtime_profile_id
            or tool.get("compatible_version_window") != version_window
            or tool.get("version_matches_policy") is not True
            or not _version_in_window(tool.get("version"), version_window)
        ):
            return False
        canonical_result = evidence.get("canonical_result")
        if not isinstance(canonical_result, dict):
            return False
        if evidence.get("canonical_result_sha256") != _SHA256(
            canonical_json(canonical_result)
        ).hexdigest():
            return False
        reference = canonical_result.get("reference")
        rustworkx_result = canonical_result.get("rustworkx")
        if not isinstance(reference, dict) or not isinstance(rustworkx_result, dict):
            return False
        return (
            reference.get("acyclic") is True
            and reference.get("required_reachability") == expected_reachability
            and rustworkx_result.get("acyclic") is True
            and rustworkx_result.get("topological_order_valid") is True
            and rustworkx_result.get("required_reachability")
            == expected_reachability
        )

    def outcome_material(
        self,
        outcome: object,
        projection: dict[str, Any],
        projection_sha256: str,
    ) -> tuple[dict[str, Any], HookSignal]:
        """Canonicalize one actual profile result into a safe hook signal."""

        if type(outcome) is not ProfileOutcome:
            evidence = {"observed_type": type(outcome).__name__}
            return (
                {
                    "disposition": "INVALID",
                    "reason": "workflow_profile_outcome_type_invalid",
                    "evidence": evidence,
                    "evidence_sha256": _SHA256(canonical_json(evidence)).hexdigest(),
                },
                HookSignal.BLOCKED,
            )
        if not isinstance(outcome.disposition, Disposition) or not isinstance(
            outcome.reason, str
        ):
            return (
                {
                    "disposition": "INVALID",
                    "reason": "workflow_profile_outcome_fields_invalid",
                    "evidence": {},
                    "evidence_sha256": _SHA256(canonical_json({})).hexdigest(),
                },
                HookSignal.BLOCKED,
            )
        try:
            evidence = self._canonical_object(
                outcome.evidence,
                "workflow profile evidence",
            )
        except MiniLevTopologyError as exc:
            error_evidence = {"error": str(exc)}
            return (
                {
                    "disposition": outcome.disposition.value,
                    "reason": "workflow_profile_evidence_invalid",
                    "evidence": error_evidence,
                    "evidence_sha256": _SHA256(
                        canonical_json(error_evidence)
                    ).hexdigest(),
                },
                HookSignal.BLOCKED,
            )
        material = {
            "disposition": outcome.disposition.value,
            "reason": outcome.reason,
            "evidence": evidence,
            "evidence_sha256": _SHA256(canonical_json(evidence)).hexdigest(),
        }
        if outcome.disposition is Disposition.ELIGIBLE:
            if (
                outcome.reason != "workflow_graph_obligations_satisfied"
                or not self.eligible_evidence(
                    evidence,
                    projection,
                    projection_sha256,
                )
            ):
                return (
                    {
                        **material,
                        "reason": "workflow_profile_eligible_evidence_invalid",
                    },
                    HookSignal.BLOCKED,
                )
            return material, HookSignal.PASS
        if outcome.disposition is Disposition.PARKED:
            return material, HookSignal.PARKED
        return material, HookSignal.BLOCKED

    def evaluate(self, policy: FlowPolicy, run_dir: Path) -> TopologyPreflightResult:
        """Execute the pinned evaluator for one already-fixed policy."""

        projection = self.projection_from_policy(policy)
        projection_sha256 = self.canonical_sha256(
            projection,
            "topology projection",
        )
        profile_identity = self.profile_identity()
        evaluation_executed = False
        if profile_identity["identity_verified"] is not True:
            identity_evidence = {
                "identity_errors": profile_identity["identity_errors"],
                "profile_config_matches": profile_identity[
                    "profile_config_matches"
                ],
            }
            profile_outcome = {
                "disposition": Disposition.BLOCKED.value,
                "reason": "workflow_profile_identity_drift",
                "evidence": identity_evidence,
                "evidence_sha256": _SHA256(
                    canonical_json(identity_evidence)
                ).hexdigest(),
            }
            signal = HookSignal.BLOCKED
        else:
            try:
                outcome = self.profile.evaluate(canonical_json(projection), run_dir)
                evaluation_executed = True
            except Exception as exc:
                error_evidence = {
                    "exception_type": type(exc).__name__,
                    "error": str(exc)[:1024],
                }
                profile_outcome = {
                    "disposition": Disposition.BLOCKED.value,
                    "reason": "workflow_profile_evaluation_error",
                    "evidence": error_evidence,
                    "evidence_sha256": _SHA256(
                        canonical_json(error_evidence)
                    ).hexdigest(),
                }
                signal = HookSignal.BLOCKED
            else:
                profile_outcome, signal = self.outcome_material(
                    outcome,
                    projection,
                    projection_sha256,
                )
        return TopologyPreflightResult(
            projection=projection,
            projection_sha256=projection_sha256,
            profile_identity=profile_identity,
            profile_outcome=profile_outcome,
            evaluation_executed=evaluation_executed,
            signal=signal,
        )

    def witness_material(
        self,
        *,
        witness_schema: str,
        run_id: str,
        flow_id: str,
        flow_policy_sha256: str,
        binding_artifact_sha256: str,
        claim_ceiling: str,
        preflight: TopologyPreflightResult,
    ) -> dict[str, Any]:
        """Build the complete canonical material bound into a flow witness."""

        return {
            "schema": witness_schema,
            "run_id": run_id,
            "flow_id": flow_id,
            "flow_policy_sha256": flow_policy_sha256,
            "binding_artifact_sha256": binding_artifact_sha256,
            "projection": preflight.projection,
            "projection_sha256": preflight.projection_sha256,
            "profile_identity": preflight.profile_identity,
            "profile_outcome": preflight.profile_outcome,
            "evaluation_executed": preflight.evaluation_executed,
            "claim_ceiling": claim_ceiling,
            "promotion_allowed": False,
        }

    def verify_profile_identity(
        self,
        profile_identity: object,
    ) -> tuple[bool, str]:
        """Validate a retained identity against this pinned controller profile."""

        if not isinstance(profile_identity, dict):
            return False, "topology witness profile material is malformed"
        expected_identity_keys = {
            "class",
            "profile_id",
            "required_version",
            "required_reachability",
            "max_nodes",
            "max_edges",
            "claim_ceiling",
            "source_path",
            "source_sha256",
            "helper_source_path",
            "helper_source_sha256",
            "evaluate_code_sha256",
            "expected_source_sha256",
            "expected_helper_source_sha256",
            "expected_evaluate_code_sha256",
            "profile_config_matches",
            "identity_verified",
            "identity_errors",
        }
        if set(profile_identity) != expected_identity_keys:
            return False, "topology profile identity keys mismatch"
        if (
            profile_identity.get("class")
            != "constraintbox.workflow_graph.WorkflowGraphProfile"
            or profile_identity.get("profile_id")
            != "constraintbox.workflow.rustworkx.dag.v1"
            or profile_identity.get("required_version")
            != self.profile.required_version
            or profile_identity.get("required_reachability")
            != [list(pair) for pair in self.required_reachability]
            or profile_identity.get("max_nodes") != self.max_nodes
            or profile_identity.get("max_edges") != self.max_edges
            or profile_identity.get("claim_ceiling") != self.profile.claim_ceiling
            or profile_identity.get("expected_source_sha256")
            != _WORKFLOW_GRAPH_SOURCE_SHA256
            or profile_identity.get("expected_helper_source_sha256")
            != _HELPER_SOURCE_SHA256
            or profile_identity.get("expected_evaluate_code_sha256")
            != _WORKFLOW_GRAPH_EVALUATE_CODE_SHA256
            or not isinstance(profile_identity.get("identity_errors"), list)
            or not isinstance(profile_identity.get("profile_config_matches"), bool)
            or not isinstance(profile_identity.get("identity_verified"), bool)
        ):
            return False, "topology profile identity binding mismatch"
        if profile_identity.get("identity_verified") is True and (
            profile_identity.get("source_path")
            != str(_WORKFLOW_GRAPH_SOURCE_PATH)
            or profile_identity.get("source_sha256")
            != _WORKFLOW_GRAPH_SOURCE_SHA256
            or profile_identity.get("helper_source_path")
            != str(_HELPER_SOURCE_PATH)
            or profile_identity.get("helper_source_sha256")
            != _HELPER_SOURCE_SHA256
            or profile_identity.get("evaluate_code_sha256")
            != _WORKFLOW_GRAPH_EVALUATE_CODE_SHA256
            or profile_identity.get("profile_config_matches") is not True
        ):
            return False, "topology profile verified identity is inconsistent"
        return True, "topology profile identity matches pinned controller profile"
