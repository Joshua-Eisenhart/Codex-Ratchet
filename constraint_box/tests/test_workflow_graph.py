from __future__ import annotations

import importlib
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import rustworkx

import constraintbox.workflow_graph as workflow_graph
from constraintbox.contracts import Disposition
from constraintbox.workflow_graph import WorkflowGraphProfile


def payload(nodes: list[str], edges: list[list[str]], **extra: object) -> bytes:
    body: dict[str, object] = {"nodes": nodes, "edges": edges}
    body.update(extra)
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


class WorkflowGraphProfileTests(unittest.TestCase):
    def evaluate(
        self,
        profile: WorkflowGraphProfile,
        nodes: list[str],
        edges: list[list[str]],
        **extra: object,
    ):
        with tempfile.TemporaryDirectory() as directory:
            return profile.evaluate(
                payload(nodes, edges, **extra), Path(directory)
            )

    def test_positive_formal_agent_prerequisite_dag(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"), ("hook", "skill"))
        )
        outcome = self.evaluate(
            profile,
            ["agent", "audit", "hook", "skill"],
            [
                ["agent", "hook"],
                ["audit", "skill"],
                ["hook", "skill"],
            ],
        )

        self.assertEqual(outcome.disposition, Disposition.ELIGIBLE)
        self.assertEqual(
            outcome.reason, "workflow_graph_obligations_satisfied"
        )
        self.assertEqual(
            outcome.evidence["tool"]["version"], str(rustworkx.__version__)
        )
        self.assertEqual(outcome.evidence["tool"]["required_version"], "0.17.1")
        self.assertTrue(
            outcome.evidence["tool"]["version_matches_policy"]
        )
        self.assertEqual(
            outcome.evidence["tool"]["compatible_version_window"],
            {"minimum_inclusive": "0.17.0", "maximum_exclusive": "0.18.0"},
        )
        self.assertTrue(
            outcome.evidence["tool"]["version_matches_legacy_baseline"]
        )
        self.assertTrue(
            outcome.evidence["tool"]["runtime_profile_id"].startswith(
                "core-cpython"
            )
        )
        self.assertEqual(
            outcome.evidence["tool"]["apis"],
            [
                "PyDiGraph",
                "PyDiGraph.add_nodes_from",
                "PyDiGraph.add_edges_from",
                "PyDiGraph.nodes",
                "PyDiGraph.edge_list",
                "is_directed_acyclic_graph",
                "topological_sort",
                "has_path",
            ],
        )
        self.assertTrue(
            outcome.evidence["canonical_result"]["reference"]["acyclic"]
        )
        self.assertTrue(
            outcome.evidence["canonical_result"]["rustworkx"][
                "topological_order_valid"
            ]
        )
        self.assertEqual(len(outcome.evidence["canonical_graph_sha256"]), 64)
        self.assertEqual(len(outcome.evidence["canonical_result_sha256"]), 64)
        runtime_identity = outcome.evidence["runtime_identity"]
        self.assertEqual(runtime_identity["distribution"], "rustworkx")
        self.assertEqual(runtime_identity["version"], "0.17.1")
        self.assertEqual(
            runtime_identity["compatible_version_window"],
            {"minimum_inclusive": "0.17.0", "maximum_exclusive": "0.18.0"},
        )
        self.assertFalse(
            runtime_identity["artifact_sha256_is_policy_input"]
        )
        self.assertEqual(
            len(runtime_identity["module_artifact"]["sha256"]), 64
        )
        self.assertEqual(
            len(runtime_identity["compiled_module_artifact"]["sha256"]), 64
        )
        self.assertEqual(
            runtime_identity["semantic_probe"],
            {
                "acyclic_graph_is_dag": True,
                "acyclic_topological_order_length": 2,
                "forward_path": True,
                "backward_path": False,
                "cycle_graph_is_dag": False,
            },
        )
        self.assertEqual(
            outcome.evidence["runtime_identity_post_operation"],
            runtime_identity,
        )
        self.assertIn("no semantic node", outcome.evidence["claim_ceiling"])

    def test_runtime_version_window_is_not_the_legacy_baseline_pin(self) -> None:
        profile, requirement = workflow_graph._active_rustworkx_profile()

        self.assertTrue(profile.profile_id.startswith("core-cpython"))
        self.assertTrue(
            workflow_graph._version_in_requirement("0.17.0", requirement)
        )
        self.assertTrue(
            workflow_graph._version_in_requirement("0.17.99", requirement)
        )
        self.assertFalse(
            workflow_graph._version_in_requirement("0.18.0", requirement)
        )

    def test_runtime_source_has_no_native_wheel_pin_mechanism(self) -> None:
        source = Path(workflow_graph.__file__).read_text()

        self.assertNotIn("RuntimeArtifactPin", source)
        self.assertNotIn("DistributionRuntimePin", source)
        self.assertNotIn("verify_distribution_runtime", source)
        self.assertNotIn("rustworkx.abi3.so", source)

    def test_cycle_is_a_negative_graph_result(self) -> None:
        outcome = self.evaluate(
            WorkflowGraphProfile(),
            ["agent", "hook"],
            [["agent", "hook"], ["hook", "agent"]],
        )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "workflow_graph_cycle_detected")
        self.assertFalse(
            outcome.evidence["canonical_result"]["reference"]["acyclic"]
        )

    def test_missing_controller_required_reachability_is_blocked(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),)
        )
        outcome = self.evaluate(
            profile,
            ["agent", "hook", "skill"],
            [["agent", "hook"]],
        )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(
            outcome.reason, "workflow_graph_required_reachability_missing"
        )
        self.assertEqual(
            outcome.evidence["missing_reachability"],
            [{"source": "agent", "target": "skill", "reachable": False}],
        )

    def test_node_and_edge_bounds_admit_the_boundary_and_block_overflow(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),),
            max_nodes=3,
            max_edges=2,
        )
        at_boundary = self.evaluate(
            profile,
            ["agent", "hook", "skill"],
            [["agent", "hook"], ["hook", "skill"]],
        )
        node_overflow = self.evaluate(
            profile,
            ["agent", "audit", "hook", "skill"],
            [["agent", "hook"], ["hook", "skill"]],
        )
        edge_overflow = self.evaluate(
            profile,
            ["agent", "hook", "skill"],
            [
                ["agent", "hook"],
                ["agent", "skill"],
                ["hook", "skill"],
            ],
        )

        self.assertEqual(at_boundary.disposition, Disposition.ELIGIBLE)
        self.assertEqual(
            node_overflow.reason, "workflow_graph_node_limit_exceeded"
        )
        self.assertEqual(
            edge_overflow.reason, "workflow_graph_edge_limit_exceeded"
        )

    def test_strict_schema_rejects_authority_and_noncanonical_graphs(self) -> None:
        profile = WorkflowGraphProfile()
        authority = self.evaluate(
            profile,
            ["agent"],
            [],
            verdict="PASS",
        )
        unsorted = self.evaluate(
            profile,
            ["hook", "agent"],
            [["agent", "hook"]],
        )
        duplicate_edge = self.evaluate(
            profile,
            ["agent", "hook"],
            [["agent", "hook"], ["agent", "hook"]],
        )

        self.assertEqual(
            authority.reason, "workflow_graph_contract_keys_mismatch"
        )
        self.assertEqual(unsorted.reason, "workflow_graph_nodes_invalid")
        self.assertEqual(
            duplicate_edge.reason, "workflow_graph_edges_invalid"
        )

    def test_dependency_unavailable_is_typed_parked(self) -> None:
        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=ModuleNotFoundError(
                "No module named 'rustworkx'",
                name="rustworkx",
            ),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.PARKED)
        self.assertEqual(outcome.reason, "rustworkx_unavailable")
        self.assertEqual(
            outcome.evidence["exception_type"],
            "ModuleNotFoundError",
        )
        self.assertEqual(outcome.evidence["missing_module"], "rustworkx")

    def test_transitive_rustworkx_import_error_is_blocked(self) -> None:
        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=ImportError(
                "cannot import name 'PyDiGraph' from 'rustworkx._accelerate'"
            ),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_import_error")
        self.assertEqual(outcome.evidence["exception_type"], "ImportError")
        self.assertEqual(outcome.evidence["phase"], "module_import")

    def test_transitive_rustworkx_module_absence_is_blocked(self) -> None:
        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=ModuleNotFoundError(
                "No module named 'rustworkx._accelerate'",
                name="rustworkx._accelerate",
            ),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_import_error")
        self.assertEqual(
            outcome.evidence["exception_type"],
            "ModuleNotFoundError",
        )
        self.assertEqual(
            outcome.evidence["missing_module"],
            "rustworkx._accelerate",
        )

    def test_rustworkx_version_drift_is_blocked(self) -> None:
        with mock.patch.object(rustworkx, "__version__", "0.18.0"):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_version_drift")
        self.assertEqual(outcome.evidence["tool"]["version"], "0.18.0")
        self.assertEqual(
            outcome.evidence["tool"]["required_version"],
            "0.17.1",
        )
        self.assertEqual(
            outcome.evidence["tool"]["compatible_version_window"],
            {"minimum_inclusive": "0.17.0", "maximum_exclusive": "0.18.0"},
        )
        self.assertFalse(
            outcome.evidence["tool"]["version_matches_policy"]
        )

    def test_same_version_counterfeit_module_is_blocked_by_runtime_identity(
        self,
    ) -> None:
        counterfeit = types.ModuleType("rustworkx")
        counterfeit.__version__ = "0.17.1"
        counterfeit.__file__ = "/tmp/counterfeit/rustworkx/__init__.py"
        for api in (
            "PyDiGraph",
            "is_directed_acyclic_graph",
            "topological_sort",
            "has_path",
        ):
            setattr(counterfeit, api, getattr(rustworkx, api))

        real_import_module = importlib.import_module

        def import_counterfeit(name: str):
            if name == "rustworkx":
                return counterfeit
            return real_import_module(name)

        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=import_counterfeit,
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_runtime_identity_error")
        self.assertEqual(
            outcome.evidence["phase"],
            "runtime_identity_pre_operation",
        )

    def test_genuine_paths_cannot_launder_python_callable_substitutes(
        self,
    ) -> None:
        compiled_real = importlib.import_module("rustworkx.rustworkx")
        forged_is_dag = lambda graph: True
        forged_topological_sort = lambda graph: list(range(len(graph)))

        counterfeit = types.ModuleType("rustworkx")
        counterfeit.__version__ = "0.17.1"
        counterfeit.__file__ = rustworkx.__file__
        counterfeit.__spec__ = types.SimpleNamespace(
            origin=rustworkx.__spec__.origin
        )
        counterfeit.PyDiGraph = rustworkx.PyDiGraph
        counterfeit.is_directed_acyclic_graph = forged_is_dag
        counterfeit.topological_sort = forged_topological_sort
        counterfeit.has_path = rustworkx.has_path

        compiled_counterfeit = types.ModuleType("rustworkx.rustworkx")
        compiled_counterfeit.__file__ = compiled_real.__file__
        compiled_counterfeit.__spec__ = types.SimpleNamespace(
            origin=compiled_real.__spec__.origin
        )
        compiled_counterfeit.PyDiGraph = rustworkx.PyDiGraph
        compiled_counterfeit.is_directed_acyclic_graph = forged_is_dag
        compiled_counterfeit.topological_sort = forged_topological_sort
        compiled_counterfeit.digraph_has_path = compiled_real.digraph_has_path

        def import_counterfeit(name: str):
            if name == "rustworkx":
                return counterfeit
            if name == "rustworkx.rustworkx":
                return compiled_counterfeit
            return importlib.import_module(name)

        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=import_counterfeit,
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_runtime_identity_error")
        self.assertEqual(
            outcome.evidence["phase"],
            "runtime_identity_pre_operation",
        )
        self.assertIn("compiled callable type drift", outcome.evidence["error"])

    def test_missing_rustworkx_version_is_blocked_without_escaping(self) -> None:
        class MissingVersionRustworkx:
            pass

        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            return_value=MissingVersionRustworkx(),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(
            outcome.reason,
            "rustworkx_version_inspection_error",
        )
        self.assertEqual(outcome.evidence["exception_type"], "AttributeError")
        self.assertEqual(outcome.evidence["phase"], "version_inspection")

    def test_raising_rustworkx_version_is_blocked_without_escaping(self) -> None:
        class RaisingVersionRustworkx:
            @property
            def __version__(self):
                raise RuntimeError("rustworkx version inspection failed")

        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            return_value=RaisingVersionRustworkx(),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(
            outcome.reason,
            "rustworkx_version_inspection_error",
        )
        self.assertEqual(outcome.evidence["exception_type"], "RuntimeError")
        self.assertEqual(
            outcome.evidence["error"],
            "rustworkx version inspection failed",
        )

    def test_present_but_broken_import_is_blocked_with_precise_evidence(
        self,
    ) -> None:
        with mock.patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=RuntimeError("rustworkx module initialization failed"),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["agent"],
                [],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_import_error")
        self.assertEqual(outcome.evidence["exception_type"], "RuntimeError")
        self.assertEqual(
            outcome.evidence["error"],
            "rustworkx module initialization failed",
        )

    def test_fixed_policy_semantic_replay_is_identical(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),),
            max_nodes=8,
            max_edges=12,
        )
        raw = payload(
            ["agent", "audit", "hook", "skill"],
            [
                ["agent", "hook"],
                ["audit", "skill"],
                ["hook", "skill"],
            ],
        )
        with tempfile.TemporaryDirectory() as first_directory:
            first = profile.evaluate(raw, Path(first_directory))
        with tempfile.TemporaryDirectory() as second_directory:
            replay = profile.evaluate(raw, Path(second_directory))

        self.assertEqual(first.disposition, replay.disposition)
        self.assertEqual(first.reason, replay.reason)
        self.assertEqual(
            first.evidence["canonical_graph_sha256"],
            replay.evidence["canonical_graph_sha256"],
        )
        self.assertEqual(
            first.evidence["canonical_result_sha256"],
            replay.evidence["canonical_result_sha256"],
        )
        self.assertEqual(
            first.evidence["canonical_result"],
            replay.evidence["canonical_result"],
        )
        self.assertEqual(first.evidence, replay.evidence)

    def test_controller_configuration_has_absolute_bounds(self) -> None:
        WorkflowGraphProfile(max_nodes=256, max_edges=4_096)
        with self.assertRaisesRegex(ValueError, "max_nodes"):
            WorkflowGraphProfile(max_nodes=257)
        with self.assertRaisesRegex(ValueError, "max_edges"):
            WorkflowGraphProfile(max_edges=4_097)
        with self.assertRaisesRegex(ValueError, "hard pair limit"):
            WorkflowGraphProfile(
                required_reachability=tuple(
                    (f"n{index:04d}", f"z{index:04d}")
                    for index in range(1_025)
                )
            )
        with self.assertRaisesRegex(ValueError, "distinct"):
            WorkflowGraphProfile(
                required_reachability=(("agent", "agent"),)
            )
        with self.assertRaisesRegex(ValueError, "required_version"):
            WorkflowGraphProfile(required_version="0.18.0")

    def test_every_named_rustworkx_api_is_operation_severance_sensitive(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),)
        )
        for api in (
            "PyDiGraph",
            "is_directed_acyclic_graph",
            "topological_sort",
            "has_path",
        ):
            with self.subTest(api=api), mock.patch.object(
                rustworkx, api, None
            ):
                outcome = self.evaluate(
                    profile,
                    ["agent", "skill"],
                    [["agent", "skill"]],
                )
                self.assertEqual(outcome.disposition, Disposition.BLOCKED)
                self.assertEqual(
                    outcome.reason, "rustworkx_runtime_api_drift"
                )
                self.assertEqual(outcome.evidence["missing_apis"], [api])

        for method in (
            "add_nodes_from",
            "add_edges_from",
            "nodes",
            "edge_list",
        ):
            with self.subTest(api=f"PyDiGraph.{method}"):
                class MissingGraphApi:
                    add_nodes_from = lambda self, value: value
                    add_edges_from = lambda self, value: value
                    nodes = lambda self: []
                    edge_list = lambda self: []

                setattr(MissingGraphApi, method, None)
                with mock.patch.object(
                    rustworkx,
                    "PyDiGraph",
                    MissingGraphApi,
                ):
                    outcome = self.evaluate(
                        profile,
                        ["agent", "skill"],
                        [["agent", "skill"]],
                    )
                self.assertEqual(outcome.disposition, Disposition.BLOCKED)
                self.assertEqual(
                    outcome.reason,
                    "rustworkx_runtime_api_drift",
                )
                self.assertEqual(
                    outcome.evidence["missing_apis"],
                    [f"PyDiGraph.{method}"],
                )

    def test_mutated_rustworkx_results_cannot_false_green(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),)
        )
        graph = (["agent", "hook", "skill"], [["agent", "hook"], ["hook", "skill"]])
        mutations = (
            (
                "acyclicity",
                mock.patch.object(
                    rustworkx,
                    "is_directed_acyclic_graph",
                    return_value=False,
                ),
                "workflow_graph_engine_reference_disagreement",
            ),
            (
                "topological order shape",
                mock.patch.object(
                    rustworkx,
                    "topological_sort",
                    return_value=[],
                ),
                "rustworkx_operation_error",
            ),
            (
                "reachability",
                mock.patch.object(
                    rustworkx,
                    "has_path",
                    return_value=False,
                ),
                "workflow_graph_engine_reference_disagreement",
            ),
        )
        for name, mutation, expected_reason in mutations:
            with (
                self.subTest(name=name),
                mock.patch(
                    "constraintbox.workflow_graph._verify_rustworkx_runtime",
                    return_value={"test_runtime_identity": "fixed"},
                ),
                mutation,
            ):
                outcome = self.evaluate(profile, *graph)
                self.assertEqual(outcome.disposition, Disposition.BLOCKED)
                self.assertEqual(outcome.reason, expected_reason)
                if expected_reason.endswith("disagreement"):
                    self.assertTrue(outcome.evidence["disagreements"])

    def test_non_boolean_engine_results_are_not_truthiness_coerced(self) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),)
        )
        graph = (["agent", "skill"], [["agent", "skill"]])
        for api in ("is_directed_acyclic_graph", "has_path"):
            with (
                self.subTest(api=api),
                mock.patch(
                    "constraintbox.workflow_graph._verify_rustworkx_runtime",
                    return_value={"test_runtime_identity": "fixed"},
                ),
                mock.patch.object(
                    rustworkx,
                    api,
                    return_value="false",
                ),
            ):
                outcome = self.evaluate(profile, *graph)
            self.assertEqual(outcome.disposition, Disposition.BLOCKED)
            self.assertEqual(outcome.reason, "rustworkx_operation_error")
            self.assertEqual(outcome.evidence["operation"], api)
            self.assertEqual(outcome.evidence["exception_type"], "TypeError")

    def test_engine_iterators_are_consumed_only_to_controller_bounds(self) -> None:
        class CountingIterator:
            def __init__(self) -> None:
                self.count = 0

            def __iter__(self):
                return self

            def __next__(self):
                value = self.count
                self.count += 1
                return value

        node_counter = CountingIterator()

        class ExcessNodeGraph:
            def add_nodes_from(self, nodes):
                del nodes
                return node_counter

            def add_edges_from(self, edges):
                return list(range(len(edges)))

            def nodes(self):
                return []

            def edge_list(self):
                return []

        profile = WorkflowGraphProfile(max_nodes=3, max_edges=2)
        with (
            mock.patch(
                "constraintbox.workflow_graph._verify_rustworkx_runtime",
                return_value={"test_runtime_identity": "fixed"},
            ),
            mock.patch.object(rustworkx, "PyDiGraph", ExcessNodeGraph),
        ):
            node_outcome = self.evaluate(
                profile,
                ["a", "b", "c"],
                [["a", "b"]],
            )
        self.assertEqual(node_outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(node_outcome.reason, "rustworkx_operation_error")
        self.assertEqual(
            node_outcome.evidence["operation"],
            "PyDiGraph.add_nodes_from",
        )
        self.assertEqual(node_counter.count, profile.max_nodes + 1)

        topo_counter = CountingIterator()
        profile = WorkflowGraphProfile(
            required_reachability=(("a", "c"),),
            max_nodes=3,
            max_edges=2,
        )
        with (
            mock.patch(
                "constraintbox.workflow_graph._verify_rustworkx_runtime",
                return_value={"test_runtime_identity": "fixed"},
            ),
            mock.patch.object(
                rustworkx,
                "topological_sort",
                return_value=topo_counter,
            ),
        ):
            topo_outcome = self.evaluate(
                profile,
                ["a", "b", "c"],
                [["a", "b"], ["b", "c"]],
            )
        self.assertEqual(topo_outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(topo_outcome.reason, "rustworkx_operation_error")
        self.assertEqual(topo_outcome.evidence["operation"], "topological_sort")
        self.assertEqual(topo_counter.count, profile.max_nodes + 1)

    def test_inserted_graph_structure_is_checked_before_algorithms(self) -> None:
        real_graph_type = rustworkx.PyDiGraph

        class EdgeInsertionNoop:
            def __init__(self):
                self.inner = real_graph_type()

            def add_nodes_from(self, nodes):
                return self.inner.add_nodes_from(nodes)

            def add_edges_from(self, edges):
                return list(range(len(edges)))

            def nodes(self):
                return self.inner.nodes()

            def edge_list(self):
                return self.inner.edge_list()

        with (
            mock.patch(
                "constraintbox.workflow_graph._verify_rustworkx_runtime",
                return_value={"test_runtime_identity": "fixed"},
            ),
            mock.patch.object(
                rustworkx,
                "PyDiGraph",
                EdgeInsertionNoop,
            ),
        ):
            outcome = self.evaluate(
                WorkflowGraphProfile(),
                ["a", "b", "c"],
                [["b", "a"], ["c", "b"]],
            )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_operation_error")
        self.assertEqual(
            outcome.evidence["operation"],
            "PyDiGraph.edge_list",
        )

    def test_executed_operation_exception_is_blocked_with_operation_name(
        self,
    ) -> None:
        profile = WorkflowGraphProfile(
            required_reachability=(("agent", "skill"),)
        )
        with (
            mock.patch(
                "constraintbox.workflow_graph._verify_rustworkx_runtime",
                return_value={"test_runtime_identity": "fixed"},
            ),
            mock.patch.object(
                rustworkx,
                "topological_sort",
                side_effect=RuntimeError("severed"),
            ),
        ):
            outcome = self.evaluate(
                profile,
                ["agent", "skill"],
                [["agent", "skill"]],
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "rustworkx_operation_error")
        self.assertEqual(outcome.evidence["operation"], "topological_sort")
        self.assertEqual(outcome.evidence["exception_type"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
