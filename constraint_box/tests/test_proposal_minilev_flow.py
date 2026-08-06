from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from constraintbox import mini_lev_topology, proposal_minilev_flow
from constraintbox.contracts import Disposition, ProfileOutcome
from constraintbox.execution_lease import (
    ClockSample,
    ExecutionLeaseBinding,
    ExecutionLeaseStore,
)
from constraintbox.mini_levos import (
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookSignal,
)
from constraintbox.proposal_minilev_flow import (
    ClaimGateCallbackResult,
    ClaimGateSignal,
    ProposalCallbackResult,
    ProposalGateCallbackResult,
    ProposalGateSignal,
    ProposalMiniLevCallbacks,
    ProposalSignal,
    run_proposal_minilev_flow,
    verify_proposal_minilev_flow,
)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class ProposalMiniLevFlowTests(unittest.TestCase):
    def _run_flow_at(self, callbacks: ProposalMiniLevCallbacks, root: Path):
        return run_proposal_minilev_flow(
            run_root=root / "proposal-flow",
            controller_state_root=root / "controller-state",
            caller_source_path=Path(__file__).resolve(),
            controller_source_path=Path(__file__).resolve(),
            binding_artifact_sha256=digest("binding"),
            callbacks=callbacks,
        )

    def run_flow(self, callbacks: ProposalMiniLevCallbacks):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return self._run_flow_at(callbacks, Path(temporary.name))

    def test_exact_retry_then_claim_gate_release_path_is_receipted(self):
        proposal_calls: list[int] = []
        gate_calls: list[int] = []
        claim_calls: list[int] = []

        def proposal(context):
            proposal_calls.append(context.attempt_number)
            return ProposalCallbackResult(
                ProposalSignal.OBSERVED,
                digest(f"proposal-{context.attempt_number}"),
            )

        def proposal_gate(context):
            gate_calls.append(context.attempt_number)
            return ProposalGateCallbackResult(
                (
                    ProposalGateSignal.RETRY
                    if context.attempt_number == 1
                    else ProposalGateSignal.PASS
                ),
                digest(f"proposal-gate-{context.attempt_number}"),
            )

        def claim_gate(context):
            claim_calls.append(context.attempt_number)
            return ClaimGateCallbackResult(
                ClaimGateSignal.PASS,
                digest(f"claim-gate-{context.attempt_number}"),
            )

        result = self.run_flow(
            ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
        )

        self.assertEqual(result.terminal, "RELEASED")
        self.assertEqual(result.flow_receipt["steps"], 6)
        self.assertEqual(result.flow_receipt["retries"], 1)
        self.assertEqual(
            result.flow_receipt["completed_nodes"],
            [
                "claim-gate",
                "proposal-gate",
                "proposal-observation",
                "topology-preflight",
            ],
        )
        self.assertEqual(proposal_calls, [1, 2])
        self.assertEqual(gate_calls, [1, 2])
        self.assertEqual(claim_calls, [2])
        valid, reason = verify_proposal_minilev_flow(result)
        self.assertTrue(valid, reason)
        self.assertTrue(result.flow_receipt_path.is_file())
        self.assertTrue(result.topology_witness_path.is_file())
        self.assertIsNotNone(result.topology_witness_sha256)
        self.assertFalse(result.flow_receipt["promotion_allowed"])
        witness = json.loads(
            result.topology_witness_path.read_text(encoding="utf-8")
        )
        self.assertTrue(witness["profile_identity"]["identity_verified"])
        self.assertTrue(witness["evaluation_executed"])
        topology_evidence = witness["profile_outcome"]["evidence"]
        self.assertEqual(topology_evidence["tool"]["name"], "rustworkx")
        self.assertTrue(topology_evidence["tool"]["version_matches_policy"])
        self.assertIn(
            topology_evidence["tool"]["runtime_profile_id"],
            {"core-cpython311-r1", "core-cpython312-r1", "core-cpython313-r1"},
        )
        version = tuple(
            int(part) for part in topology_evidence["tool"]["version"].split(".")
        )
        window = topology_evidence["tool"]["compatible_version_window"]
        self.assertGreaterEqual(
            version,
            tuple(int(part) for part in window["minimum_inclusive"].split(".")),
        )
        self.assertLess(
            version,
            tuple(int(part) for part in window["maximum_exclusive"].split(".")),
        )
        self.assertTrue(
            topology_evidence["canonical_result"]["rustworkx"]["acyclic"]
        )
        self.assertEqual(
            witness["projection"],
            {
                "nodes": [
                    "claim-gate",
                    "proposal-gate",
                    "proposal-observation",
                    "topology-preflight",
                ],
                "edges": [
                    ["proposal-gate", "claim-gate"],
                    ["proposal-observation", "proposal-gate"],
                    ["topology-preflight", "proposal-observation"],
                ],
            },
        )
        self.assertNotIn(
            ["proposal-gate", "proposal-observation"],
            witness["projection"]["edges"],
        )

        records = [
            json.loads(line)["record"]
            for line in result.flow_ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(
            [record["node_id"] for record in records],
            [
                "topology-preflight",
                "proposal-observation",
                "proposal-gate",
                "proposal-observation",
                "proposal-gate",
                "claim-gate",
            ],
        )
        self.assertEqual(
            [record["controller_selected_next"] for record in records],
            [
                "proposal-observation",
                "proposal-gate",
                "proposal-observation",
                "proposal-gate",
                "claim-gate",
                "RELEASED",
            ],
        )
        lease_events = [
            record for record in records if record["node_id"] == "proposal-observation"
        ]
        self.assertEqual(len(lease_events), 2)
        self.assertEqual(
            result.flow_receipt["execution_lease"]["protected_event_sequences"],
            [2, 4],
        )
        self.assertTrue(
            result.flow_receipt["execution_lease"]["all_protected_events_released"]
        )
        for record in lease_events:
            audit = record["execution_lease"]
            self.assertEqual(audit["pre_hook_verdict"]["status"], "VALID")
            self.assertEqual(audit["post_hook_verdict"]["status"], "VALID")
            self.assertEqual(audit["release_status"], "RELEASED")
            self.assertEqual(audit["release_cause"], "COMPLETED")
            self.assertNotIn("nonce", audit)
            self.assertNotIn("nonce", audit["acquire_record"])
            self.assertNotIn("nonce", audit["release_record"])
        self.assertEqual(
            ExecutionLeaseStore(result.execution_lease_state_path).read_receipt()[
                "status"
            ],
            "RELEASED",
        )

    def test_invalid_callback_cannot_supply_a_transition_or_release(self):
        def invalid_proposal(context):
            del context
            return {"signal": "PASS", "next_node": "RELEASED"}

        def forbidden_gate(context):
            raise AssertionError(f"gate should not run: {context}")

        def forbidden_claim(context):
            raise AssertionError(f"claim gate should not run: {context}")

        result = self.run_flow(
            ProposalMiniLevCallbacks(
                invalid_proposal,
                forbidden_gate,
                forbidden_claim,
            )
        )
        self.assertEqual(result.terminal, "HOLD")
        self.assertEqual(result.flow_receipt["steps"], 2)
        self.assertNotEqual(result.terminal, "RELEASED")
        valid, reason = verify_proposal_minilev_flow(result)
        self.assertTrue(valid, reason)

    def test_topology_helper_rejects_undeclared_policy_and_receipt_edges(self):
        malformed_policy = FlowPolicy(
            flow_id="test-topology-policy",
            entry_node="node-a",
            nodes=(FlowNode("node-a", "hook-a"),),
            transitions=(
                FlowTransition("node-a", HookSignal.PASS, "undeclared-node"),
            ),
            terminal_nodes=("RELEASED",),
            required_nodes=("node-a",),
            max_steps=1,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=1,
            max_event_bytes=1,
            max_receipt_bytes=1,
            claim_ceiling="test-only topology helper input",
        )
        with self.assertRaisesRegex(
            mini_lev_topology.MiniLevTopologyError,
            "target is undeclared",
        ):
            proposal_minilev_flow._TOPOLOGY.projection_from_policy(
                malformed_policy
            )

        def proposal(context):
            return ProposalCallbackResult(
                ProposalSignal.OBSERVED,
                digest(f"proposal-{context.attempt_number}"),
            )

        def proposal_gate(context):
            return ProposalGateCallbackResult(
                ProposalGateSignal.PASS,
                digest(f"proposal-gate-{context.attempt_number}"),
            )

        def claim_gate(context):
            return ClaimGateCallbackResult(
                ClaimGateSignal.PASS,
                digest(f"claim-gate-{context.attempt_number}"),
            )

        result = self.run_flow(
            ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
        )
        malformed_receipt_policy = copy.deepcopy(result.flow_receipt["policy"])
        malformed_receipt_policy["transitions"][0]["to_node"] = "undeclared-node"
        with self.assertRaisesRegex(
            mini_lev_topology.MiniLevTopologyError,
            "target is undeclared",
        ):
            proposal_minilev_flow._TOPOLOGY.projection_from_receipt_policy(
                malformed_receipt_policy
            )
        malformed_receipt_policy = copy.deepcopy(result.flow_receipt["policy"])
        malformed_receipt_policy["transitions"][0]["signal"] = "NOT_A_SIGNAL"
        with self.assertRaisesRegex(
            mini_lev_topology.MiniLevTopologyError,
            "signal is invalid",
        ):
            proposal_minilev_flow._TOPOLOGY.projection_from_receipt_policy(
                malformed_receipt_policy
            )

    def test_provider_boundary_parked_never_runs_a_gate(self):
        calls: list[str] = []

        def proposal(context):
            calls.append(f"proposal-{context.attempt_number}")
            return ProposalCallbackResult(
                ProposalSignal.PARKED,
                digest("provider-boundary-parked"),
            )

        def proposal_gate(context):
            del context
            calls.append("proposal-gate")
            return ProposalGateCallbackResult(
                ProposalGateSignal.PASS,
                digest("should-not-run"),
            )

        def claim_gate(context):
            del context
            calls.append("claim-gate")
            return ClaimGateCallbackResult(
                ClaimGateSignal.PASS,
                digest("should-not-run"),
            )

        result = self.run_flow(
            ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
        )
        self.assertEqual(result.terminal, "PARKED")
        self.assertEqual(calls, ["proposal-1"])
        self.assertEqual(result.flow_receipt["steps"], 2)

    def test_claim_gate_block_is_not_a_release(self):
        def proposal(context):
            return ProposalCallbackResult(
                ProposalSignal.OBSERVED,
                digest(f"proposal-{context.attempt_number}"),
            )

        def proposal_gate(context):
            return ProposalGateCallbackResult(
                ProposalGateSignal.PASS,
                digest(f"proposal-gate-{context.attempt_number}"),
            )

        def claim_gate(context):
            return ClaimGateCallbackResult(
                ClaimGateSignal.BLOCKED,
                digest(f"claim-gate-{context.attempt_number}"),
            )

        result = self.run_flow(
            ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
        )
        self.assertEqual(result.terminal, "BLOCKED")
        self.assertEqual(result.flow_receipt["steps"], 4)
        self.assertFalse(result.flow_receipt["promotion_allowed"])

    def test_callback_source_drift_holds_before_the_next_gate(self):
        drifted = False
        original_source_sha256 = proposal_minilev_flow._source_sha256

        def source_sha256(path: Path) -> str:
            return digest("drift") if drifted else original_source_sha256(path)

        def proposal(context):
            nonlocal drifted
            drifted = True
            return ProposalCallbackResult(
                ProposalSignal.OBSERVED,
                digest(f"proposal-{context.attempt_number}"),
            )

        def forbidden_gate(context):
            raise AssertionError(f"gate should not run after drift: {context}")

        def forbidden_claim(context):
            raise AssertionError(f"claim should not run after drift: {context}")

        with patch.object(
            proposal_minilev_flow,
            "_source_sha256",
            side_effect=source_sha256,
        ):
            result = self.run_flow(
                ProposalMiniLevCallbacks(
                    proposal,
                    forbidden_gate,
                    forbidden_claim,
                )
        )
        self.assertEqual(result.terminal, "HOLD")
        self.assertEqual(result.flow_receipt["steps"], 3)

    def test_topology_witness_tamper_is_detected_after_a_valid_run(self):
        def proposal(context):
            return ProposalCallbackResult(
                ProposalSignal.OBSERVED,
                digest(f"proposal-{context.attempt_number}"),
            )

        def proposal_gate(context):
            return ProposalGateCallbackResult(
                ProposalGateSignal.PASS,
                digest(f"proposal-gate-{context.attempt_number}"),
            )

        def claim_gate(context):
            return ClaimGateCallbackResult(
                ClaimGateSignal.PASS,
                digest(f"claim-gate-{context.attempt_number}"),
            )

        result = self.run_flow(
            ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
        )
        witness = json.loads(
            result.topology_witness_path.read_text(encoding="utf-8")
        )
        witness["binding_artifact_sha256"] = digest("tampered-binding")
        result.topology_witness_path.write_bytes(
            proposal_minilev_flow.canonical_json(witness) + b"\n"
        )

        valid, reason = verify_proposal_minilev_flow(result)
        self.assertFalse(valid)
        self.assertEqual(reason, "topology witness digest mismatch")

    def test_preoccupied_controller_slot_holds_before_provider_callback(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        state_path = (
            root
            / "controller-state"
            / proposal_minilev_flow.EXECUTION_LEASE_DIRECTORY_NAME
            / proposal_minilev_flow.PROPOSAL_OBSERVATION_LEASE_NAME
        )
        store = ExecutionLeaseStore(state_path)
        blocking_binding = ExecutionLeaseBinding(
            owner_id="another-controller",
            run_id="other-run",
            node_id="other-node",
            visit=1,
            slot_sha256=store.slot_sha256,
            flow_sha256=digest("other-flow"),
            policy_sha256=digest("other-policy"),
            runtime_sha256=digest("other-runtime"),
            instruction_sha256=digest("other-instruction"),
        )
        store.acquire(
            blocking_binding,
            ttl_ns=10,
            clock=ClockSample("other-clock", 0),
        )
        calls: list[str] = []

        def proposal(context):
            del context
            calls.append("provider")
            return ProposalCallbackResult(ProposalSignal.OBSERVED, digest("proposal"))

        def gate(context):
            del context
            calls.append("gate")
            return ProposalGateCallbackResult(ProposalGateSignal.PASS, digest("gate"))

        def claim(context):
            del context
            calls.append("claim")
            return ClaimGateCallbackResult(ClaimGateSignal.PASS, digest("claim"))

        result = self._run_flow_at(
            ProposalMiniLevCallbacks(proposal, gate, claim),
            root,
        )

        self.assertEqual(result.terminal, "HOLD")
        self.assertEqual(calls, [])
        records = [
            json.loads(line)["record"]
            for line in result.flow_ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual([record["node_id"] for record in records], [
            "topology-preflight",
            "proposal-observation",
        ])
        audit = records[-1]["execution_lease"]
        self.assertEqual(audit["failure_stage"], "acquire")
        self.assertEqual(audit["release_status"], "NOT_ACQUIRED")
        valid, reason = verify_proposal_minilev_flow(result)
        self.assertTrue(valid, reason)

    def test_expired_same_domain_slot_is_reclaimed_by_the_next_flow(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        controller_state_root = root / "controller-state"
        controller_state_root.mkdir(mode=0o700)
        state_path = (
            controller_state_root
            / proposal_minilev_flow.EXECUTION_LEASE_DIRECTORY_NAME
            / proposal_minilev_flow.PROPOSAL_OBSERVATION_LEASE_NAME
        )
        store = ExecutionLeaseStore(state_path)
        clock_id = proposal_minilev_flow._controller_lease_clock_id(
            controller_state_root.resolve(),
            state_path,
        )
        abandoned_binding = ExecutionLeaseBinding(
            owner_id="abandoned-controller",
            run_id="abandoned-run",
            node_id="abandoned-node",
            visit=1,
            slot_sha256=store.slot_sha256,
            flow_sha256=digest("abandoned-flow"),
            policy_sha256=digest("abandoned-policy"),
            runtime_sha256=digest("abandoned-runtime"),
            instruction_sha256=digest("abandoned-instruction"),
        )
        store.acquire(
            abandoned_binding,
            ttl_ns=1,
            clock=ClockSample(clock_id, 0),
        )
        calls: list[str] = []

        def proposal(context):
            del context
            calls.append("provider")
            return ProposalCallbackResult(ProposalSignal.OBSERVED, digest("proposal"))

        def gate(context):
            del context
            calls.append("gate")
            return ProposalGateCallbackResult(ProposalGateSignal.PASS, digest("gate"))

        def claim(context):
            del context
            calls.append("claim")
            return ClaimGateCallbackResult(ClaimGateSignal.PASS, digest("claim"))

        with patch(
            "constraintbox.mini_levos.time.monotonic_ns",
            side_effect=[10, 11, 12, 13],
        ):
            result = self._run_flow_at(
                ProposalMiniLevCallbacks(proposal, gate, claim), root
            )

        self.assertEqual(result.terminal, "RELEASED")
        self.assertEqual(calls, ["provider", "gate", "claim"])
        records = [
            json.loads(line)["record"]
            for line in result.flow_ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        audit = records[1]["execution_lease"]
        self.assertEqual(audit["clock_id"], clock_id)
        self.assertEqual(audit["acquire_record"]["event"], "ACQUIRED_AFTER_EXPIRY")
        self.assertEqual(
            ExecutionLeaseStore(result.execution_lease_state_path).read_receipt()[
                "status"
            ],
            "RELEASED",
        )
        valid, reason = verify_proposal_minilev_flow(result)
        self.assertTrue(valid, reason)

    def test_rechained_lease_audit_tamper_is_detected(self):
        def proposal(context):
            return ProposalCallbackResult(
                ProposalSignal.OBSERVED,
                digest(f"proposal-{context.attempt_number}"),
            )

        def gate(context):
            return ProposalGateCallbackResult(
                ProposalGateSignal.PASS,
                digest(f"gate-{context.attempt_number}"),
            )

        def claim(context):
            return ClaimGateCallbackResult(
                ClaimGateSignal.PASS,
                digest(f"claim-{context.attempt_number}"),
            )

        result = self.run_flow(ProposalMiniLevCallbacks(proposal, gate, claim))
        rows = [
            json.loads(line)
            for line in result.flow_ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        rows[1]["record"]["execution_lease"]["release_record"][
            "release_cause"
        ] = "FAILED"
        previous = "0" * 64
        event_hashes: list[str] = []
        rewritten: list[dict[str, object]] = []
        for row in rows:
            body = {"previous_sha256": previous, "record": row["record"]}
            line_sha256 = hashlib.sha256(
                proposal_minilev_flow.canonical_json(body)
            ).hexdigest()
            rewritten.append({**body, "line_sha256": line_sha256})
            event_hashes.append(line_sha256)
            previous = line_sha256
        result.flow_ledger_path.write_text(
            "".join(
                proposal_minilev_flow.canonical_json(row).decode("utf-8") + "\n"
                for row in rewritten
            ),
            encoding="utf-8",
        )
        result.flow_ledger_head_path.write_text(previous + "\n", encoding="ascii")
        result.flow_receipt["event_hashes"] = event_hashes
        result.flow_receipt["ledger"]["retained_head_sha256"] = previous
        result.flow_receipt["ledger"]["verification"] = f"{len(rows)} record(s)"
        receipt_body = dict(result.flow_receipt)
        receipt_body.pop("receipt_sha256", None)
        result.flow_receipt["receipt_sha256"] = hashlib.sha256(
            proposal_minilev_flow.canonical_json(receipt_body)
        ).hexdigest()
        tampered = replace(
            result,
            flow_receipt_sha256=result.flow_receipt["receipt_sha256"],
        )

        valid, reason = verify_proposal_minilev_flow(tampered)
        self.assertFalse(valid)
        self.assertIn("record digest mismatch", reason)

    def test_rehashed_unexecuted_parked_topology_witness_is_rejected(self):
        def proposal(context):
            raise AssertionError(f"proposal should not run: {context}")

        def proposal_gate(context):
            raise AssertionError(f"proposal gate should not run: {context}")

        def claim_gate(context):
            raise AssertionError(f"ClaimGate should not run: {context}")

        missing_rustworkx = ModuleNotFoundError(
            "No module named 'rustworkx'",
            name="rustworkx",
        )
        with patch(
            "constraintbox.workflow_graph.importlib.import_module",
            side_effect=missing_rustworkx,
        ):
            result = self.run_flow(
                ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
            )

        self.assertEqual(result.terminal, "PARKED")
        witness = json.loads(
            result.topology_witness_path.read_text(encoding="utf-8")
        )
        self.assertTrue(witness["profile_identity"]["identity_verified"])
        self.assertTrue(witness["evaluation_executed"])
        self.assertEqual(
            witness["profile_outcome"]["reason"],
            "rustworkx_unavailable",
        )

        # Rehash every retained artifact as an adversary with local write access
        # might.  The topology verifier must still reject an evidence claim that
        # says the pinned evaluator was never run.
        witness["evaluation_executed"] = False
        witness_sha256 = hashlib.sha256(
            proposal_minilev_flow.canonical_json(witness)
        ).hexdigest()
        result.topology_witness_path.write_bytes(
            proposal_minilev_flow.canonical_json(witness) + b"\n"
        )
        rows = [
            json.loads(line)
            for line in result.flow_ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(rows), 1)
        update = {
            proposal_minilev_flow._TOPOLOGY_WITNESS_UPDATE_KEY: witness_sha256
        }
        record = rows[0]["record"]
        record["applied_context_updates"] = update
        record["hook_observation"] = update
        record["controller_output"]["observation"] = update
        record["controller_output"]["context_updates"] = update
        result.flow_receipt["final_context"][
            proposal_minilev_flow._TOPOLOGY_WITNESS_UPDATE_KEY
        ] = witness_sha256
        record["context_sha256"] = hashlib.sha256(
            proposal_minilev_flow.canonical_json(result.flow_receipt["final_context"])
        ).hexdigest()
        record["output_sha256"] = hashlib.sha256(
            proposal_minilev_flow.canonical_json(record["controller_output"])
        ).hexdigest()
        ledger_body = {"previous_sha256": "0" * 64, "record": record}
        ledger_sha256 = hashlib.sha256(
            proposal_minilev_flow.canonical_json(ledger_body)
        ).hexdigest()
        result.flow_ledger_path.write_text(
            proposal_minilev_flow.canonical_json(
                {**ledger_body, "line_sha256": ledger_sha256}
            ).decode("utf-8")
            + "\n",
            encoding="utf-8",
        )
        result.flow_ledger_head_path.write_text(
            ledger_sha256 + "\n",
            encoding="ascii",
        )
        result.flow_receipt["event_hashes"] = [ledger_sha256]
        result.flow_receipt["ledger"]["retained_head_sha256"] = ledger_sha256
        result.flow_receipt["ledger"]["verification"] = "1 record(s)"
        result.flow_receipt["final_context_sha256"] = hashlib.sha256(
            proposal_minilev_flow.canonical_json(result.flow_receipt["final_context"])
        ).hexdigest()
        receipt_body = dict(result.flow_receipt)
        receipt_body.pop("receipt_sha256", None)
        receipt_sha256 = hashlib.sha256(
            proposal_minilev_flow.canonical_json(receipt_body)
        ).hexdigest()
        result.flow_receipt["receipt_sha256"] = receipt_sha256
        tampered = replace(
            result,
            topology_witness_sha256=witness_sha256,
            flow_receipt_sha256=receipt_sha256,
        )

        valid, reason = verify_proposal_minilev_flow(tampered)
        self.assertFalse(valid)
        self.assertEqual(
            reason,
            "topology eligible or parked outcome lacks an evaluator run",
        )

    def test_poisoned_workflow_evaluator_blocks_before_provider_callback(self):
        calls: list[str] = []

        def proposal(context):
            del context
            calls.append("proposal")
            return ProposalCallbackResult(ProposalSignal.OBSERVED, digest("proposal"))

        def proposal_gate(context):
            del context
            calls.append("proposal-gate")
            return ProposalGateCallbackResult(ProposalGateSignal.PASS, digest("gate"))

        def claim_gate(context):
            del context
            calls.append("claim-gate")
            return ClaimGateCallbackResult(ClaimGateSignal.PASS, digest("claim"))

        poison = ProfileOutcome(
            Disposition.ELIGIBLE,
            "workflow_graph_obligations_satisfied",
            {},
        )
        with patch.object(
            mini_lev_topology.WorkflowGraphProfile,
            "evaluate",
            return_value=poison,
        ) as evaluator:
            result = self.run_flow(
                ProposalMiniLevCallbacks(proposal, proposal_gate, claim_gate)
            )

        self.assertEqual(result.terminal, "BLOCKED")
        self.assertEqual(result.flow_receipt["steps"], 1)
        self.assertEqual(calls, [])
        evaluator.assert_not_called()
        witness = json.loads(
            result.topology_witness_path.read_text(encoding="utf-8")
        )
        self.assertFalse(witness["profile_identity"]["identity_verified"])
        self.assertFalse(witness["evaluation_executed"])
        self.assertEqual(
            witness["profile_outcome"]["reason"],
            "workflow_profile_identity_drift",
        )
        valid, reason = verify_proposal_minilev_flow(result)
        self.assertTrue(valid, reason)


if __name__ == "__main__":
    unittest.main()
