from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox.contracts import Disposition
from constraintbox.boundary_contract import BoundaryContractProfile, TASK_BOUNDARY_CONTRACT
from constraintbox import maude_rewrite
from constraintbox.formal_registry import (
    DEFAULT_FORMAL_RUNTIME_POLICY,
    TASK_INTEGRATED_WORKLOAD_TRANSITION,
    TASK_LEVOS_FLOWMIND_GRAPH,
    TASK_PHASE_TRANSITION,
    TASK_SYMBOLIC_POLYNOMIAL,
    TASK_WORKFLOW_GRAPH,
    FormalRuntimeResolved,
    formal_catalog,
    formal_task_kinds,
    formal_task_policy,
    load_formal_runtime_policy,
    run_formal_task,
    run_temporal_pair,
)
from constraintbox.formalcheck import FormalCheckReceipt, FormalCheckStatus
from constraintbox.formal_flow import FORMAL_FLOW_LEDGER, FORMAL_FLOW_RECEIPT
from constraintbox.maude_rewrite import MaudeTransitionProfile
from constraintbox.levos_flowmind import LevDnaFlowMindGraphProfile
from constraintbox.symbolic import SympyRationalPolynomialProfile
from constraintbox.workflow_graph import WorkflowGraphProfile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "formal"


def passing_formal_receipt(backend: str) -> FormalCheckReceipt:
    return FormalCheckReceipt(
        schema="constraintbox.formalcheck.receipt.v1",
        profile_id="controller_lifecycle_v1",
        backend=backend,
        status=FormalCheckStatus.PASSED,
        disposition=Disposition.ELIGIBLE,
        reason=f"bounded_{backend}_controls_passed",
        controls={"positive": True, "behavior_mutation": True},
        evidence={
            "positive_semantics": {
                "status": "PASS",
                "version": "test",
            },
            "mutation_semantics": {
                "status": "INVARIANT_VIOLATION",
                "invariant_results": {"EvidenceBeforeEligibility": "FAIL"},
            },
            "post_run_hashes": {"model_sha256": "a" * 64},
        },
        claim_ceiling="bounded test receipt",
        blocked_consumers=("general_correctness",),
    )


class FormalRegistryTests(unittest.TestCase):
    def test_catalog_keeps_tools_reference_methods_and_external_systems_distinct(
        self,
    ) -> None:
        catalog = formal_catalog()
        names = {row["name"] for row in catalog["instruments"]}
        self.assertEqual(
            names,
            {"Apalache", "CVC5", "Maude", "Rustworkx", "SymPy", "TLC", "Z3"},
        )
        checker_rows = {
            row["name"]: row
            for row in catalog["instruments"]
            if row["name"] in {"Apalache", "TLC"}
        }
        self.assertTrue(all(row["version"] is None for row in checker_rows.values()))
        self.assertTrue(
            all(
                row["version_evidence"]
                == "must come from the current temporal receipt"
                for row in checker_rows.values()
            )
        )
        reference = catalog["internal_reference_methods"]
        self.assertEqual(reference[0]["name"], "bounded exhaustive enumeration")
        self.assertFalse(reference[0]["external_tool"])
        self.assertIn("profile-verified active CPython", reference[0]["role"])
        substrate = catalog["execution_substrate"]
        self.assertEqual(substrate["name"], "CPython")
        self.assertEqual(
            substrate["profile_ids"],
            ["core-cpython311-r1", "core-cpython312-r1", "core-cpython313-r1"],
        )
        self.assertIn(substrate["active_runtime"]["state"], {"ELIGIBLE", "PARKED", "BLOCKED"})
        self.assertIn("itertools.product", substrate["operation_ids"])
        self.assertIn("MiniLevRuntime.run", substrate["callers"])
        self.assertFalse(substrate["decision_authority"])
        self.assertFalse(substrate["promotion_allowed"])
        self.assertEqual(catalog["test_only"][0]["name"], "Hypothesis")
        self.assertFalse(catalog["test_only"][0]["runtime_authority"])
        self.assertEqual(catalog["optional_not_default"][0]["name"], "NumPy")
        self.assertIn("allowed", catalog["optional_not_default"][0]["role"])
        self.assertFalse(catalog["promotion_allowed"])
        self.assertIn(
            "cb:external-sim-validation-adapter",
            catalog["external_system_boundary"],
        )
        self.assertIn("sim:*", catalog["external_system_boundary"])

    def test_default_policy_is_fixed_and_excludes_numpy(self) -> None:
        policy = formal_task_policy()
        self.assertEqual(tuple(sorted(policy)), formal_task_kinds())
        self.assertEqual(
            set(policy),
            {
                TASK_BOUNDARY_CONTRACT,
                TASK_LEVOS_FLOWMIND_GRAPH,
                TASK_INTEGRATED_WORKLOAD_TRANSITION,
                TASK_PHASE_TRANSITION,
                TASK_SYMBOLIC_POLYNOMIAL,
                TASK_WORKFLOW_GRAPH,
            },
        )
        self.assertIsInstance(
            policy[TASK_BOUNDARY_CONTRACT], BoundaryContractProfile
        )
        self.assertIsInstance(
            policy[TASK_SYMBOLIC_POLYNOMIAL],
            SympyRationalPolynomialProfile,
        )
        self.assertIsInstance(policy[TASK_WORKFLOW_GRAPH], WorkflowGraphProfile)
        self.assertIsInstance(
            policy[TASK_LEVOS_FLOWMIND_GRAPH],
            LevDnaFlowMindGraphProfile,
        )
        self.assertIsInstance(policy[TASK_PHASE_TRANSITION], MaudeTransitionProfile)
        self.assertIsInstance(
            policy[TASK_INTEGRATED_WORKLOAD_TRANSITION],
            MaudeTransitionProfile,
        )

    def _run(self, task: str, fixture: str, request_id: str):
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=task,
                request_id=request_id,
                payload=(FIXTURES / fixture).read_bytes(),
                run_root=run_root,
            )
            ledger = run_root / "formal_decisions.jsonl"
            self.assertTrue(ledger.is_file())
            self.assertTrue(ledger.read_text(encoding="utf-8").strip())
            return decision

    def test_symbolic_profile_is_reached_through_the_fixed_controller(self) -> None:
        decision = self._run(
            TASK_SYMBOLIC_POLYNOMIAL,
            "symbolic_polynomial_valid.json",
            "symbolic-1",
        )
        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(decision.reason, "exact_polynomial_recomputed")
        self.assertFalse(decision.promotion_allowed)

    def test_workflow_profile_is_reached_through_the_fixed_controller(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=TASK_WORKFLOW_GRAPH,
                request_id="workflow-1",
                payload=(FIXTURES / "workflow_graph_valid.json").read_bytes(),
                run_root=run_root,
            )
            flow_receipt = json.loads(
                (run_root / FORMAL_FLOW_RECEIPT).read_text(encoding="utf-8")
            )
            self.assertTrue((run_root / FORMAL_FLOW_LEDGER).is_file())
            self.assertTrue(
                (run_root / f"{FORMAL_FLOW_LEDGER}.head").is_file()
            )
        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(decision.reason, "workflow_graph_obligations_satisfied")
        self.assertEqual(flow_receipt["terminal"], "ELIGIBLE")
        self.assertEqual(flow_receipt["steps"], 2)
        self.assertEqual(
            flow_receipt["completed_nodes"],
            ["formal-gate", "formal-tool"],
        )
        self.assertFalse(flow_receipt["promotion_allowed"])

    def test_maude_profile_is_reached_through_the_fixed_controller(self) -> None:
        decision = self._run(
            TASK_PHASE_TRANSITION,
            "phase_transition_valid.json",
            "transition-1",
        )
        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(decision.reason, "maude_transition_observed")
        self.assertTrue(decision.evidence["controller_table_agrees"])

    def test_integrated_workload_transition_is_reached_through_minilev(self) -> None:
        payload = json.dumps(
            {
                "from_state": "received",
                "action": "observe_suite",
                "to_state": "suite_observed",
            }
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=TASK_INTEGRATED_WORKLOAD_TRANSITION,
                request_id="integrated-transition-1",
                payload=payload,
                run_root=run_root,
            )
        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(decision.reason, "maude_transition_observed")
        self.assertTrue(decision.evidence["controller_table_agrees"])

    def test_levos_flowmind_foreign_graph_runs_through_minilev(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=TASK_LEVOS_FLOWMIND_GRAPH,
                request_id="levos-flowmind-1",
                payload=(
                    FIXTURES
                    / "levos_flowmind_dna_compile_pinned_topology_fixture.json"
                ).read_bytes(),
                run_root=run_root,
            )
            flow_receipt = json.loads(
                (run_root / FORMAL_FLOW_RECEIPT).read_text(encoding="utf-8")
            )
            observation = (
                run_root
                / "levos-flowmind-1"
                / "foreign_lev_dna_compile.json"
            )
            self.assertTrue(observation.is_file())
        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(
            decision.reason,
            "levos_flowmind_structure_obligations_satisfied",
        )
        self.assertEqual(flow_receipt["terminal"], "ELIGIBLE")
        self.assertEqual(flow_receipt["steps"], 2)
        self.assertFalse(decision.promotion_allowed)

    def test_levos_non_utf8_foreign_text_is_a_formal_block_not_a_hold(self) -> None:
        body = json.loads(
            (
                FIXTURES
                / "levos_flowmind_dna_compile_pinned_topology_fixture.json"
            ).read_text(encoding="utf-8")
        )
        body["operation"]["request_id"] = chr(0xD800)
        payload = json.dumps(
            body,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=TASK_LEVOS_FLOWMIND_GRAPH,
                request_id="levos-invalid-unicode",
                payload=payload,
                run_root=run_root,
            )
            flow_receipt = json.loads(
                (run_root / FORMAL_FLOW_RECEIPT).read_text(encoding="utf-8")
            )
        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(
            decision.reason,
            "levos_dna_compile_text_not_utf8_encodable",
        )
        self.assertEqual(flow_receipt["terminal"], "BLOCKED")

    def test_unknown_task_cannot_choose_an_unregistered_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            decision = run_formal_task(
                task_kind="formal.tool.numpy",
                request_id="unknown-1",
                payload=b"{}",
                run_root=Path(temporary).resolve(),
            )
        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(decision.reason, "unknown_task_kind")

    def test_runtime_policy_is_hash_pinned_and_requires_both_backends(self) -> None:
        policy = load_formal_runtime_policy()
        self.assertEqual(
            set(policy.backends),
            {"apalache", "tlc"},
        )
        self.assertTrue(all(item.required for item in policy.backends.values()))
        self.assertEqual(
            policy.runtime_directory_env,
            "CONSTRAINTBOX_FORMAL_RUNTIME_DIR",
        )
        self.assertEqual(policy.java_command, "java")
        self.assertEqual(
            policy.profile_dir,
            (
                DEFAULT_FORMAL_RUNTIME_POLICY.parent
                / "controller_lifecycle_v1"
            ).resolve(),
        )
        with patch.object(
            Path,
            "read_bytes",
            return_value=b'{"schema":"changed"}',
        ):
            with self.assertRaisesRegex(
                ValueError,
                "digest differs",
            ):
                load_formal_runtime_policy(DEFAULT_FORMAL_RUNTIME_POLICY)

    def test_formal_tool_policies_do_not_encode_a_developer_home_path(self) -> None:
        self.assertNotIn(
            "/Users/",
            DEFAULT_FORMAL_RUNTIME_POLICY.read_text(encoding="utf-8"),
        )
        self.assertNotIn(
            "/Users/",
            Path(maude_rewrite.__file__).read_text(encoding="utf-8"),
        )

    def test_temporal_pair_runs_both_required_backends_without_a_backend_input(
        self,
    ) -> None:
        calls: list[str] = []

        def fake_run(profile):
            calls.append(profile.backend)
            return passing_formal_receipt(profile.backend)

        resolved = FormalRuntimeResolved(
            runtime_directory=Path("/formal-runtime"),
            java_executable=Path("/usr/bin/java"),
            checker_artifacts={
                "apalache": Path("/formal-runtime/apalache.jar"),
                "tlc": Path("/formal-runtime/tla2tools.jar"),
            },
        )
        with patch(
            "constraintbox.formal_registry.resolve_formal_runtime",
            return_value=resolved,
        ), patch(
            "constraintbox.formal_registry.run_temporal_check",
            side_effect=fake_run,
        ):
            first = run_temporal_pair()
            second = run_temporal_pair()
        self.assertEqual(calls, ["apalache", "tlc", "apalache", "tlc"])
        self.assertEqual(first["status"], "PASSED")
        self.assertEqual(first["disposition"], "ELIGIBLE")
        self.assertEqual(first["required_backends"], ["apalache", "tlc"])
        self.assertIn(
            "decision_correctness_claims",
            first["blocked_consumers"],
        )
        self.assertIn("single-run abstract", first["claim_ceiling"])
        self.assertEqual(
            first["semantic_results_sha256"],
            second["semantic_results_sha256"],
        )
        self.assertFalse(first["promotion_allowed"])

    def test_temporal_pair_parks_if_one_required_backend_is_unavailable(
        self,
    ) -> None:
        def fake_run(profile):
            if profile.backend == "tlc":
                return FormalCheckReceipt(
                    schema="constraintbox.formalcheck.receipt.v1",
                    profile_id="controller_lifecycle_v1",
                    backend="tlc",
                    status=FormalCheckStatus.UNAVAILABLE,
                    disposition=Disposition.PARKED,
                    reason="sandbox_socket_denied",
                    controls={},
                    evidence={},
                    claim_ceiling="bounded test receipt",
                    blocked_consumers=("general_correctness",),
                )
            return passing_formal_receipt("apalache")

        resolved = FormalRuntimeResolved(
            runtime_directory=Path("/formal-runtime"),
            java_executable=Path("/usr/bin/java"),
            checker_artifacts={
                "apalache": Path("/formal-runtime/apalache.jar"),
                "tlc": Path("/formal-runtime/tla2tools.jar"),
            },
        )
        with patch(
            "constraintbox.formal_registry.resolve_formal_runtime",
            return_value=resolved,
        ), patch(
            "constraintbox.formal_registry.run_temporal_check",
            side_effect=fake_run,
        ):
            receipt = run_temporal_pair()
        self.assertEqual(receipt["status"], "UNAVAILABLE")
        self.assertEqual(receipt["disposition"], "PARKED")

    def test_temporal_pair_parks_without_declared_runtime_configuration(
        self,
    ) -> None:
        with patch.dict(
            os.environ,
            {"CONSTRAINTBOX_FORMAL_RUNTIME_DIR": ""},
        ):
            receipt = run_temporal_pair()
        self.assertEqual(receipt["status"], "UNAVAILABLE")
        self.assertEqual(receipt["disposition"], "PARKED")
        self.assertEqual(receipt["reason"], "formal_runtime_unavailable")
        self.assertEqual(
            receipt["runtime_directory_env"],
            "CONSTRAINTBOX_FORMAL_RUNTIME_DIR",
        )


if __name__ == "__main__":
    unittest.main()
