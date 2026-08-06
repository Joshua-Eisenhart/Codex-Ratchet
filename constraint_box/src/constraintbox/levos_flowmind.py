"""Controller-owned structural intake for one Lev-shaped DNA/FlowMind artifact.

The input is caller-supplied JSON shaped like the external
``lev dna compile … --json`` surface. ConstraintBox does not establish that a
Lev process, source path, or checkout produced it. ConstraintBox consumes only
a deliberately tiny, non-executable projection: node identifiers and declared
``next``/``branches`` edges. Descriptions, ``op``/``eval`` strings, agent
material, hooks, prompts, and profile hints are neither interpreted nor made
authoritative here.

This is not a Lev runtime emulator or a ClaimGate/Lev admission path.  It is a
bounded foreign-observation adapter whose graph obligations are decided by the
existing controller-owned Rustworkx plus independent-reference profile.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, canonical_json, parse_json_object
from . import workflow_graph as _workflow_graph
from .workflow_graph import WorkflowGraphProfile


_SHA256 = hashlib.sha256
_OBSERVATION_FILENAME = "foreign_lev_dna_compile.json"
_TOP_LEVEL_KEYS = frozenset(
    {"version", "operation", "side_effect", "policy", "result", "evidence"}
)
_OPERATION_KEYS = frozenset({"id", "service", "method", "surface", "request_id"})
_SIDE_EFFECT_KEYS = frozenset({"class", "dry_run"})
_POLICY_KEYS = frozenset({"decision"})
_RESULT_KEYS = frozenset({"status", "data", "exit_code"})
_DATA_KEYS = frozenset(
    {
        "path",
        "entry",
        "nodeCount",
        "executionProfileHint",
        "kellyProfileHint",
        "executionProfileAlignment",
        "graph",
    }
)
_GRAPH_KEYS = frozenset({"name", "entry", "nodes"})
_NODE_KEYS = frozenset(
    {"description", "terminal", "op", "eval", "next", "branches"}
)
_EVIDENCE_KEYS = frozenset(
    {"receipt_refs", "event_refs", "artifact_refs", "proof_refs"}
)
_FOREIGN_AUTHORITY_FIELDS = frozenset(
    {
        "allpass",
        "claimceiling",
        "compatibilityonly",
        "command",
        "constraintboxcontrollermetadata",
        "contentaddress",
        "controlleremitted",
        "decision",
        "disposition",
        "executable",
        "formaladmissionallowed",
        "hook",
        "hookid",
        "ledger",
        "livelevconsumed",
        "maxsteps",
        "nextnode",
        "pass",
        "policy",
        "profileid",
        "promotionallowed",
        "provider",
        "python",
        "recordable",
        "releaseadmissionallowed",
        "releaseallowed",
        "retrybudget",
        "terminal",
        "timeout",
        "tolerance",
        "transition",
        "verdict",
    }
)
_PINNED_FLOWMIND_TOPOLOGY_SHA256 = (
    "146f017529ada5e799bd47d6e56240a9ce6375c31ffffb68c49e3f46bff258e0"
)
_PINNED_WORKFLOW_GRAPH_SOURCE_SHA256 = (
    "97f017cada9480d8869f7160e79c43ec0a0290631a3a53e097032e1f6aec5cd0"
)
_CLAIM_CEILING = (
    "one caller-supplied Lev-shaped compiler artifact was reduced to a fixed "
    "finite FlowMind topology and checked for graph mechanics; this does not "
    "establish Lev execution behavior, producer identity, equivalence, "
    "ClaimGate admission, agent authority, or promotion"
)


def _authority_key_form(key: str) -> str:
    """Normalize spelling variants without interpreting foreign values."""

    return "".join(character for character in key.casefold() if character.isalnum())


def _allowed_foreign_authority_key(*, key_form: str, child_path: str) -> bool:
    """Allow only the fixed syntactic slots needed by this exact envelope."""

    if child_path == "$.policy" and key_form == "policy":
        return True
    if child_path == "$.policy.decision" and key_form == "decision":
        return True
    if (
        key_form == "terminal"
        and child_path.startswith("$.result.data.graph.nodes.")
        and ".branches." not in child_path
    ):
        return True
    if key_form == "pass" and child_path.endswith(".branches.pass"):
        return True
    return False


def _key_paths(value: object, *, path: str = "$") -> list[str]:
    """Find foreign fields that attempt to assert controller authority."""

    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_form = _authority_key_form(key)
            if (
                key_form in _FOREIGN_AUTHORITY_FIELDS
                and not _allowed_foreign_authority_key(
                    key_form=key_form,
                    child_path=child_path,
                )
            ):
                paths.append(child_path)
            paths.extend(_key_paths(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _first_non_utf8_text_path(value: object, *, path: str = "$") -> str | None:
    """Return a safe structural path for the first non-UTF-8 text value."""

    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return path
        return None
    if isinstance(value, dict):
        for index, (key, child) in enumerate(value.items()):
            try:
                key.encode("utf-8")
            except UnicodeEncodeError:
                return f"{path}.key[{index}]"
            child_path = f"{path}.value[{index}]"
            invalid_path = _first_non_utf8_text_path(child, path=child_path)
            if invalid_path is not None:
                return invalid_path
        return None
    if isinstance(value, list):
        for index, child in enumerate(value):
            invalid_path = _first_non_utf8_text_path(child, path=f"{path}[{index}]")
            if invalid_path is not None:
                return invalid_path
    return None


def _blocked(reason: str, **evidence: Any) -> ProfileOutcome:
    return ProfileOutcome(Disposition.BLOCKED, reason, evidence)


def _mapping(value: object, *, path: str) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return value


def _persist_foreign_observation(
    *, run_dir: Path, payload: bytes
) -> tuple[Path, str] | None:
    """Retain the exact foreign bytes without replacing an older observation."""

    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return None
    observation_path = run_dir / _OBSERVATION_FILENAME
    temporary_path = observation_path.with_name(
        f".{observation_path.name}.{os.getpid()}.tmp"
    )
    try:
        with temporary_path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, observation_path)
        directory_fd = os.open(run_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return observation_path, _SHA256(payload).hexdigest()
    except OSError:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


@dataclass(frozen=True)
class LevDnaFlowMindGraphProfile:
    """Check one fixed Lev FlowMind-contract graph as a foreign observation."""

    expected_graph_name: str = "flowmind_contract"
    expected_entry: str = "gate_compiler_not_executor"
    expected_terminal: str = "done"
    expected_canonical_graph_sha256: str = _PINNED_FLOWMIND_TOPOLOGY_SHA256
    expected_workflow_graph_source_sha256: str = (
        _PINNED_WORKFLOW_GRAPH_SOURCE_SHA256
    )
    max_nodes: int = 128
    max_edges: int = 512
    profile_id: str = "constraintbox.levos.flowmind-contract.rustworkx.v1"
    claim_ceiling: str = _CLAIM_CEILING

    def __post_init__(self) -> None:
        # This is a fixed controller profile, not a caller-configurable graph
        # checker. A caller that could substitute either digest could admit a
        # merely Lev-shaped topology under the production task kind.
        fixed_settings = (
            ("expected_graph_name", self.expected_graph_name, "flowmind_contract"),
            (
                "expected_entry",
                self.expected_entry,
                "gate_compiler_not_executor",
            ),
            ("expected_terminal", self.expected_terminal, "done"),
            (
                "expected_canonical_graph_sha256",
                self.expected_canonical_graph_sha256,
                _PINNED_FLOWMIND_TOPOLOGY_SHA256,
            ),
            (
                "expected_workflow_graph_source_sha256",
                self.expected_workflow_graph_source_sha256,
                _PINNED_WORKFLOW_GRAPH_SOURCE_SHA256,
            ),
            ("max_nodes", self.max_nodes, 128),
            ("max_edges", self.max_edges, 512),
            (
                "profile_id",
                self.profile_id,
                "constraintbox.levos.flowmind-contract.rustworkx.v1",
            ),
            ("claim_ceiling", self.claim_ceiling, _CLAIM_CEILING),
        )
        for name, observed, expected in fixed_settings:
            if observed != expected:
                raise ValueError(f"{name} is controller-pinned")

        # Reuse the graph profile's hard bounds and exact node-name grammar for
        # controller settings before any foreign input is accepted.
        WorkflowGraphProfile(
            required_reachability=((self.expected_entry, self.expected_terminal),),
            max_nodes=self.max_nodes,
            max_edges=self.max_edges,
        )

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        """Validate, retain, project, then gate one compiler observation."""

        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return _blocked("levos_dna_compile_intake_invalid", error=str(exc))

        non_utf8_text_path = _first_non_utf8_text_path(body)
        if non_utf8_text_path is not None:
            return _blocked(
                "levos_dna_compile_text_not_utf8_encodable",
                structural_path=non_utf8_text_path,
            )
        authority_paths = _key_paths(body)
        if authority_paths:
            return _blocked(
                "levos_foreign_authority_field_present",
                forbidden_paths=authority_paths,
            )
        if set(body) != _TOP_LEVEL_KEYS:
            return _blocked(
                "levos_dna_compile_envelope_keys_mismatch",
                expected_keys=sorted(_TOP_LEVEL_KEYS),
                observed_keys=sorted(body),
            )
        if type(body["version"]) is not int or body["version"] != 1:
            return _blocked("levos_dna_compile_version_mismatch")

        operation = _mapping(body["operation"], path="$.operation")
        side_effect = _mapping(body["side_effect"], path="$.side_effect")
        policy = _mapping(body["policy"], path="$.policy")
        result = _mapping(body["result"], path="$.result")
        evidence = _mapping(body["evidence"], path="$.evidence")
        if any(
            value is None
            for value in (operation, side_effect, policy, result, evidence)
        ):
            return _blocked("levos_dna_compile_envelope_value_invalid")
        if (
            operation is None
            or side_effect is None
            or policy is None
            or result is None
            or evidence is None
        ):
            return _blocked("levos_dna_compile_envelope_value_invalid")

        if set(operation) != _OPERATION_KEYS or (
            operation.get("id"),
            operation.get("service"),
            operation.get("method"),
            operation.get("surface"),
        ) != ("dna.compile", "dna", "compile", "cli"):
            return _blocked("levos_dna_compile_operation_mismatch")
        request_id = operation.get("request_id")
        if not isinstance(request_id, str) or not request_id or len(request_id) > 256:
            return _blocked("levos_dna_compile_request_id_invalid")
        if (
            set(side_effect) != _SIDE_EFFECT_KEYS
            or side_effect.get("class") != "read"
            or type(side_effect.get("dry_run")) is not bool
            or side_effect.get("dry_run") is not False
        ):
            return _blocked("levos_dna_compile_side_effect_mismatch")
        if set(policy) != _POLICY_KEYS or policy != {"decision": "allow"}:
            return _blocked("levos_dna_compile_policy_mismatch")
        if (
            set(result) != _RESULT_KEYS
            or result.get("status") != "ok"
            or type(result.get("exit_code")) is not int
            or result.get("exit_code") != 0
        ):
            return _blocked("levos_dna_compile_result_mismatch")
        if set(evidence) != _EVIDENCE_KEYS or any(
            not isinstance(value, list) or value for value in evidence.values()
        ):
            return _blocked("levos_dna_compile_evidence_mismatch")

        data = _mapping(result.get("data"), path="$.result.data")
        if data is None or set(data) != _DATA_KEYS:
            return _blocked("levos_dna_compile_data_keys_mismatch")
        if any(
            not isinstance(data[name], dict)
            for name in (
                "executionProfileHint",
                "kellyProfileHint",
                "executionProfileAlignment",
            )
        ):
            return _blocked("levos_dna_compile_hints_invalid")
        source_path = data.get("path")
        entry = data.get("entry")
        node_count = data.get("nodeCount")
        graph = _mapping(data.get("graph"), path="$.result.data.graph")
        if (
            not isinstance(source_path, str)
            or not source_path
            or len(source_path) > 4_096
            or not isinstance(entry, str)
            or type(node_count) is not int
            or graph is None
        ):
            return _blocked("levos_dna_compile_data_values_invalid")
        if set(graph) != _GRAPH_KEYS or (
            graph.get("name"),
            graph.get("entry"),
        ) != (self.expected_graph_name, self.expected_entry):
            return _blocked("levos_flowmind_graph_identity_mismatch")
        if entry != self.expected_entry:
            return _blocked("levos_flowmind_entry_mismatch")

        raw_nodes = _mapping(graph.get("nodes"), path="$.result.data.graph.nodes")
        if raw_nodes is None or not raw_nodes or len(raw_nodes) != node_count:
            return _blocked("levos_flowmind_node_count_mismatch")
        if len(raw_nodes) > self.max_nodes:
            return _blocked(
                "levos_flowmind_node_limit_exceeded",
                observed_nodes=len(raw_nodes),
                max_nodes=self.max_nodes,
            )

        nodes = sorted(raw_nodes)
        edges: set[tuple[str, str]] = set()
        declared_edge_count = 0
        for node_id in nodes:
            node = _mapping(raw_nodes[node_id], path=f"$.result.data.graph.nodes.{node_id}")
            if node is None or set(node) - _NODE_KEYS:
                return _blocked("levos_flowmind_node_schema_invalid", node=node_id)
            description = node.get("description")
            if not isinstance(description, str) or len(description) > 16_384:
                return _blocked("levos_flowmind_node_description_invalid", node=node_id)
            for opaque_field in ("op", "eval"):
                if opaque_field in node and not isinstance(node[opaque_field], str):
                    return _blocked(
                        "levos_flowmind_node_opaque_field_invalid",
                        node=node_id,
                        field=opaque_field,
                    )
            if "terminal" in node and type(node["terminal"]) is not bool:
                return _blocked("levos_flowmind_node_terminal_invalid", node=node_id)
            terminal = node.get("terminal", False)
            has_next = "next" in node
            has_branches = "branches" in node
            next_node = node.get("next")
            branches = node.get("branches")
            if has_next and not isinstance(next_node, str):
                return _blocked("levos_flowmind_next_invalid", node=node_id)
            if has_branches and not isinstance(branches, dict):
                return _blocked("levos_flowmind_branches_invalid", node=node_id)
            if terminal is True and (has_next or has_branches):
                return _blocked("levos_flowmind_terminal_has_outgoing", node=node_id)
            if terminal is not True and has_next == has_branches:
                return _blocked("levos_flowmind_node_transition_shape_invalid", node=node_id)
            if has_next:
                declared_edge_count += 1
                if next_node not in raw_nodes:
                    return _blocked(
                        "levos_flowmind_edge_target_missing",
                        source=node_id,
                        target=next_node,
                    )
                edges.add((node_id, next_node))
            if has_branches:
                if not branches:
                    return _blocked("levos_flowmind_branches_empty", node=node_id)
                for label, target in branches.items():
                    declared_edge_count += 1
                    if declared_edge_count > self.max_edges:
                        return _blocked(
                            "levos_flowmind_declared_edge_limit_exceeded",
                            observed_declared_edges=declared_edge_count,
                            max_edges=self.max_edges,
                        )
                    if (
                        not isinstance(label, str)
                        or not label
                        or len(label) > 128
                        or not isinstance(target, str)
                        or target not in raw_nodes
                    ):
                        return _blocked(
                            "levos_flowmind_branch_target_invalid", node=node_id
                    )
                    edges.add((node_id, target))

            if declared_edge_count > self.max_edges:
                return _blocked(
                    "levos_flowmind_declared_edge_limit_exceeded",
                    observed_declared_edges=declared_edge_count,
                    max_edges=self.max_edges,
                )

        if self.expected_terminal not in raw_nodes or raw_nodes[
            self.expected_terminal
        ].get("terminal") is not True:
            return _blocked("levos_flowmind_expected_terminal_invalid")
        canonical_graph = {
            "nodes": nodes,
            "edges": [list(edge) for edge in sorted(edges)],
        }
        if len(canonical_graph["edges"]) > self.max_edges:
            return _blocked(
                "levos_flowmind_edge_limit_exceeded",
                observed_edges=len(canonical_graph["edges"]),
                max_edges=self.max_edges,
            )
        canonical_graph_sha256 = _SHA256(canonical_json(canonical_graph)).hexdigest()
        if canonical_graph_sha256 != self.expected_canonical_graph_sha256:
            return _blocked(
                "levos_flowmind_topology_digest_mismatch",
                expected_canonical_graph_sha256=self.expected_canonical_graph_sha256,
                observed_canonical_graph_sha256=canonical_graph_sha256,
            )

        workflow_graph_source_path = Path(_workflow_graph.__file__).resolve()
        try:
            actual_workflow_graph_source_sha256 = _SHA256(
                workflow_graph_source_path.read_bytes()
            ).hexdigest()
        except OSError as exc:
            return _blocked(
                "levos_workflow_graph_source_unavailable",
                error=str(exc),
            )
        if (
            actual_workflow_graph_source_sha256
            != self.expected_workflow_graph_source_sha256
        ):
            return _blocked(
                "levos_workflow_graph_source_digest_mismatch",
                expected_workflow_graph_source_sha256=(
                    self.expected_workflow_graph_source_sha256
                ),
                observed_workflow_graph_source_sha256=(
                    actual_workflow_graph_source_sha256
                ),
            )

        try:
            observation = _persist_foreign_observation(
                run_dir=run_dir,
                payload=payload,
            )
        except OSError as exc:
            return _blocked(
                "levos_foreign_observation_persistence_failed",
                error=str(exc),
            )
        if observation is None:
            return _blocked(
                "levos_foreign_observation_run_directory_already_exists",
                run_directory=str(run_dir),
            )
        observation_path, foreign_sha256 = observation

        workflow = WorkflowGraphProfile(
            required_reachability=((self.expected_entry, self.expected_terminal),),
            max_nodes=self.max_nodes,
            max_edges=self.max_edges,
        )
        workflow_outcome = workflow.evaluate(canonical_json(canonical_graph), run_dir)
        adapter_evidence = {
            "schema": "constraintbox.levos-flowmind-import.evidence.v1",
            "foreign_observation": {
                "claimed_kind": "lev.dna.compile.cli.json",
                "sha256": foreign_sha256,
                "artifact": _OBSERVATION_FILENAME,
                "source_path_text_sha256": _SHA256(
                    source_path.encode("utf-8")
                ).hexdigest(),
                "operation": "dna.compile",
                "foreign_authority": False,
                "producer_authenticated": False,
                "source_path_authenticated": False,
            },
            "structural_projection": {
                "graph_name": self.expected_graph_name,
                "entry": self.expected_entry,
                "required_terminal": self.expected_terminal,
                "canonical_graph": canonical_graph,
                "canonical_graph_sha256": canonical_graph_sha256,
                "workflow_graph_source_sha256": actual_workflow_graph_source_sha256,
                "ignored_node_content_fields": ["description", "eval", "op"],
            },
            "workflow_graph": workflow_outcome.evidence,
            "foreign_system_claim": "LevOS",
            "external_not_cb_kernel": True,
            "promotion_allowed": False,
        }
        if workflow_outcome.disposition is not Disposition.ELIGIBLE:
            return ProfileOutcome(
                workflow_outcome.disposition,
                f"levos_{workflow_outcome.reason}",
                adapter_evidence,
            )
        try:
            persisted_payload = observation_path.read_bytes()
        except OSError as exc:
            return _blocked(
                "levos_foreign_observation_persistence_verification_failed",
                error=str(exc),
            )
        if (
            not observation_path.is_file()
            or _SHA256(persisted_payload).hexdigest() != foreign_sha256
        ):
            return _blocked("levos_foreign_observation_persistence_drift")
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "levos_flowmind_structure_obligations_satisfied",
            adapter_evidence,
        )
