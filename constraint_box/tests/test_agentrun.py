from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox import agentrun
from constraintbox.boxrun import BoxRunError, VerifiedBoxRun
from constraintbox.constraints import SolverResult, SolverStatus
from constraintbox.discharge import Discharge, PASS, POLICY_SATISFIED
from constraintbox.execution_lease import ExecutionLeaseStore


from constraintbox._provider_harness.providers import (
    FakeFailureProvider,
    FakeSuccessProvider,
)

try:
    import z3  # noqa: F401
except ImportError:
    HAS_Z3 = False
else:
    HAS_Z3 = True


class PromptSequenceProvider:
    name = "sequence"

    def __init__(
        self,
        claims: list[str],
        *,
        mark_tool_calls: bool = False,
        use_wrong_evidence: bool = False,
    ):
        self.claims = claims
        self.mark_tool_calls = mark_tool_calls
        self.use_wrong_evidence = use_wrong_evidence
        self.calls = 0
        self.prompts: list[str] = []

    def run(
        self,
        job,
        *,
        timeout=None,
        started_at=None,
        completed_at=None,
    ):
        del timeout
        claim = self.claims[min(self.calls, len(self.claims) - 1)]
        self.calls += 1
        self.prompts.append(job.task.prompt)
        match = re.search(r"evidence_ref=([0-9a-f]{64})", job.task.prompt)
        if match is None:
            raise AssertionError("controller evidence reference absent from prompt")
        evidence_ref = "0" * 64 if self.use_wrong_evidence else match.group(1)
        body = json.dumps(
            {
                "proposal_id": f"proposal-{self.calls}",
                "candidate": {
                    "requested_claim": claim,
                    "evidence_ref": evidence_ref,
                },
                "falsifiers": ["the operation-severance control stops flipping"],
            },
            sort_keys=True,
        )
        receipt = FakeSuccessProvider(body).run(
            job,
            started_at=started_at,
            completed_at=completed_at,
        )
        receipt.has_tool_calls = self.mark_tool_calls
        receipt.tool_calls = (
            [{"name": "forbidden"}] if self.mark_tool_calls else None
        )
        return receipt


class RaisingProvider:
    name = "sequence"

    def run(self, job, **kwargs):
        del job, kwargs
        raise RuntimeError("provider boundary unavailable")


class FailureProvider:
    name = "sequence"

    def run(self, job, **kwargs):
        return FakeFailureProvider().run(job, **kwargs)


def fake_profile_inputs() -> dict:
    text = "bounded test MMM"
    return {
        "fixture": {"path": "fixture", "sha256": "f" * 64},
        "estate_controller": {"path": "estate", "sha256": "e" * 64},
        "worker": {"path": "worker", "sha256": "w" * 64},
        "import_blocker": {"path": "blocker", "sha256": "b" * 64},
        "operation_poisoner": {"path": "poisoner", "sha256": "p" * 64},
        "mmm": {
            "packs": [],
            "sha256": agentrun._sha256_bytes(text.encode("utf-8")),
            "text": text,
        },
    }


def fake_tool_receipt() -> dict:
    controls = {
        "positive": True,
        "dispatch": True,
        "mutation": True,
        "replay": True,
        "severance": True,
        "operation": True,
    }
    return {
        "schema": "constraintbox.agent-tool-receipt.v1",
        "profile_id": agentrun.PROFILE_ID,
        "profile_manifest": "controller_profile_manifest.json",
        "profile_manifest_sha256": "a" * 64,
        "estate_receipt": {
            "schema": "constraintbox.sim-tier-receipt.v2",
            "state": "READY",
            "capabilities": [
                {
                    "capability_id": "numpy_density",
                    "state": "READY",
                    "reason": "all_required_controls_passed",
                    "controls": controls,
                    "expected_version": agentrun.PROFILE_NUMPY_VERSION,
                    "observed_version": agentrun.PROFILE_NUMPY_VERSION,
                    "worker_sha256": agentrun.PROFILE_PINS["worker"],
                    "fixture_sha256": agentrun.PROFILE_PINS["fixture"],
                    "evidence": {
                        "dispatch": [
                            "numpy.asarray",
                            "numpy.linalg.eigvalsh",
                            "numpy.trace",
                        ],
                        "operation_severed": "numpy.linalg.eigvalsh",
                    },
                }
            ],
        },
        "claim_ceiling": agentrun.CLAIM_CEILING,
        "promotion_allowed": False,
    }


def fake_verified_box(root: Path) -> VerifiedBoxRun:
    request = (
        b'{"allowed_actions":["invoke_llm"],'
        b'"request_id":"boxed-test","schema":"constraintbox.user-request.v1"}'
    )
    context = (
        "[USER PROFILE constraintbox-test-owner v1]\n"
        "[OWNER-ASSERTED COMMUNICATION REQUIREMENTS]\n"
        "- personalized context must be load-bearing"
    )
    return VerifiedBoxRun(
        root=root.resolve(),
        receipt_sha256="1" * 64,
        request_id="boxed-test",
        request_sha256=agentrun._sha256_bytes(request),
        request_canonical=request,
        profile_sha256="2" * 64,
        context_sha256=agentrun._sha256_bytes(context.encode("utf-8")),
        context_text=context,
        external_engine_packet_sha256="3" * 64,
        artifact_sha256s=(("compiled_user_context.txt", "4" * 64),),
    )


def strong_claim_gate(path: Path) -> dict:
    body = json.loads(path.read_text(encoding="utf-8"))
    if body["release_statement"] != agentrun.RELEASE_TEXT:
        raise AssertionError("provider prose reached the release receipt")
    return {
        "disposition": "ADMITTED",
        "chain_exit_code": 0,
        "chain_verdict": "VERIFIED",
        "required_tiers": ["tier0"],
        "verified_tiers": ["tier0"],
        "required_unmet": [],
        "tamper_events": [],
    }


@unittest.skipUnless(HAS_Z3, "closed loop requires the SMT backend")
class AgentRunTests(unittest.TestCase):
    def run_box(
        self,
        provider: PromptSequenceProvider,
        *,
        claim_gate=strong_claim_gate,
    ):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        box_dir = root / "box"
        box_dir.mkdir()
        run_dir = root / "run"
        verified_box = fake_verified_box(box_dir)
        with (
            patch.object(
                agentrun,
                "verify_box_run",
                return_value=verified_box,
            ),
            patch.object(
                agentrun,
                "_load_profile_inputs",
                return_value=(fake_profile_inputs(), []),
            ),
            patch.object(
                agentrun,
                "_run_fixed_tool",
                return_value=(fake_tool_receipt(), []),
            ),
            patch.dict(
                os.environ,
                {"LLM_HARNESS_HMAC_KEY": "constraintbox-test-key"},
            ),
        ):
            result, code = agentrun._run_agent_for_test(
                box_dir,
                run_dir,
                provider=provider,
                claim_gate=claim_gate,
            )
        return result, code, run_dir

    def test_overclaim_is_repaired_then_only_controller_text_is_released(self):
        provider = PromptSequenceProvider(
            ["scientific_result", agentrun.ALLOWED_CLAIM]
        )
        result, code, run_dir = self.run_box(provider)
        self.assertEqual(code, 0)
        self.assertEqual(result["disposition"], "RELEASED")
        self.assertTrue(result["release_allowed"])
        self.assertEqual(result["release"], agentrun.RELEASE_TEXT)
        self.assertEqual(provider.calls, 2)
        self.assertIn(
            "personalized context must be load-bearing",
            provider.prompts[0],
        )
        self.assertIn("box_receipt_sha256=" + "1" * 64, provider.prompts[0])
        self.assertIn("CB core gates are cb:* IDs", provider.prompts[0])
        self.assertIn("sim:* IDs", provider.prompts[0])
        self.assertEqual(result["box_input"]["box_receipt_sha256"], "1" * 64)
        task_body = json.loads(
            (run_dir / "task.json").read_text(encoding="utf-8")
        )
        self.assertEqual(task_body["schema"], agentrun.TASK_SCHEMA)
        self.assertEqual(task_body["box_receipt_sha256"], "1" * 64)
        first_receipt = json.loads(
            (run_dir / "attempt-1" / "provider_receipt.json").read_text(
                encoding="utf-8"
            )
        )
        for digest in (
            "1" * 64,
            task_body["request_sha256"],
            "2" * 64,
            task_body["compiled_user_context_sha256"],
            "3" * 64,
        ):
            self.assertIn(digest, first_receipt["input_refs"])
        self.assertEqual(result["attempts"][0]["disposition"], "BLOCKED")
        self.assertIn(
            "CLAIM_CEILING_EXCEEDED",
            result["attempts"][0]["reason_codes"],
        )
        self.assertEqual(result["attempts"][1]["disposition"], "ELIGIBLE")
        self.assertEqual(
            result["attempts"][0]["feedback_sha256"],
            result["attempts"][1]["feedback_input_sha256"],
        )
        proposal_flow = result["proposal_flow"]
        self.assertTrue(proposal_flow["caller_replay_verified"])
        self.assertEqual(proposal_flow["terminal"], "RELEASED")
        flow_receipt = json.loads(
            Path(proposal_flow["flow_receipt"]).read_text(encoding="utf-8")
        )
        self.assertEqual(flow_receipt["terminal"], "RELEASED")
        self.assertEqual(flow_receipt["steps"], 6)
        self.assertEqual(flow_receipt["retries"], 1)
        self.assertEqual(
            flow_receipt["completed_nodes"],
            [
                "claim-gate",
                "proposal-gate",
                "proposal-observation",
                "topology-preflight",
            ],
        )
        flow_events = [
            json.loads(line)["record"]
            for line in Path(proposal_flow["flow_ledger"])
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            [row["node_id"] for row in flow_events],
            [
                "topology-preflight",
                "proposal-observation",
                "proposal-gate",
                "proposal-observation",
                "proposal-gate",
                "claim-gate",
            ],
        )
        leased_events = [
            row
            for row in flow_events
            if row["node_id"] == "proposal-observation"
        ]
        self.assertEqual(len(leased_events), 2)
        self.assertTrue(flow_receipt["execution_lease"]["all_protected_events_released"])
        self.assertEqual(
            flow_receipt["execution_lease"]["protected_event_sequences"],
            [2, 4],
        )
        for row in leased_events:
            audit = row["execution_lease"]
            self.assertEqual(audit["release_status"], "RELEASED")
            self.assertEqual(audit["release_cause"], "COMPLETED")
            self.assertNotIn("nonce", audit)
        self.assertEqual(
            ExecutionLeaseStore(Path(proposal_flow["execution_lease_state"])).read_receipt()[
                "status"
            ],
            "RELEASED",
        )
        topology_witness = json.loads(
            Path(proposal_flow["topology_witness"]).read_text(encoding="utf-8")
        )
        self.assertEqual(
            topology_witness["flow_policy_sha256"],
            proposal_flow["flow_policy_sha256"],
        )
        self.assertEqual(
            topology_witness["binding_artifact_sha256"],
            proposal_flow["binding_sha256"],
        )
        self.assertEqual(
            proposal_flow["topology_witness_sha256"],
            agentrun._sha256_bytes(
                agentrun.canonical_json(topology_witness)
            ),
        )
        second_receipt = json.loads(
            (run_dir / "attempt-2" / "provider_receipt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(
            result["attempts"][0]["feedback_sha256"],
            second_receipt["input_refs"],
        )
        self.assertEqual(
            result["branch_ledger"]["branches"]["attempt-1"]["status"],
            "PARKED",
        )
        self.assertEqual(
            result["branch_ledger"]["branches"]["attempt-2"]["status"],
            "LIVE",
        )
        release_receipt = json.loads(
            (run_dir / "release_receipt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(release_receipt["box_receipt_sha256"], "1" * 64)
        self.assertEqual(
            release_receipt["compiled_user_context_sha256"],
            task_body["compiled_user_context_sha256"],
        )
        self.assertEqual(
            release_receipt["external_engine_packet_sha256"],
            "3" * 64,
        )

    def test_discharge_pass_severance_cannot_release_overclaim(self):
        provider = PromptSequenceProvider(
            ["scientific_result", "scientific_result"]
        )
        forced_pass = Discharge(
            status=PASS,
            policy_id="severed",
            reason_code=POLICY_SATISFIED,
            blocking=False,
            decided_at=0.0,
        )
        with patch.object(agentrun, "discharge", return_value=forced_pass):
            result, code, _ = self.run_box(provider)
        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], "REFUSED")
        self.assertIsNone(result["release"])
        for attempt in result["attempts"]:
            self.assertIn("RELEASE_SAFETY_VETO", attempt["reason_codes"])
            self.assertFalse(attempt["release_safety"])

    def test_provider_tool_use_is_blocked(self):
        provider = PromptSequenceProvider(
            [agentrun.ALLOWED_CLAIM, agentrun.ALLOWED_CLAIM],
            mark_tool_calls=True,
        )
        result, code, _ = self.run_box(provider)
        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], "REFUSED")
        self.assertIsNone(result["release"])
        self.assertIn(
            "PROVIDER_TOOL_USE",
            result["attempts"][0]["reason_codes"],
        )

    def test_claim_gate_admitted_contradiction_parks_without_release(self):
        def contradictory_gate(path: Path) -> dict:
            del path
            return {
                "disposition": "ADMITTED",
                "chain_exit_code": 0,
                "chain_verdict": "VERIFIED",
                "required_tiers": ["tier0"],
                "verified_tiers": [],
                "required_unmet": [],
                "tamper_events": [],
            }

        provider = PromptSequenceProvider([agentrun.ALLOWED_CLAIM])
        result, code, _ = self.run_box(
            provider,
            claim_gate=contradictory_gate,
        )
        self.assertEqual(code, 4)
        self.assertEqual(result["disposition"], "PARKED")
        self.assertIsNone(result["release"])
        self.assertEqual(result["proposal_flow"]["terminal"], "PARKED")

    def test_wrong_evidence_reference_never_releases(self):
        provider = PromptSequenceProvider(
            [agentrun.ALLOWED_CLAIM, agentrun.ALLOWED_CLAIM],
            use_wrong_evidence=True,
        )
        result, code, _ = self.run_box(provider)
        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], "REFUSED")
        self.assertIn(
            "EVIDENCE_REF_MISMATCH",
            result["attempts"][0]["reason_codes"],
        )

    def test_provider_boundary_exception_parks_with_receipt(self):
        result, code, run_dir = self.run_box(RaisingProvider())
        self.assertEqual(code, 4)
        self.assertEqual(result["disposition"], "PARKED")
        self.assertIsNone(result["release"])
        self.assertEqual(
            result["attempts"][0]["reason_codes"],
            ["PROVIDER_BOUNDARY_ERROR"],
        )
        self.assertEqual(result["proposal_flow"]["terminal"], "PARKED")
        self.assertTrue(
            (run_dir / "attempt-1" / "provider_boundary_error.json").is_file()
        )

    def test_absent_proposal_is_not_mislabeled_as_an_overclaim(self):
        result, code, _ = self.run_box(FailureProvider())
        self.assertEqual(code, 4)
        reasons = result["attempts"][0]["reason_codes"]
        self.assertIn("PROPOSAL_CLAIM_MISSING", reasons)
        self.assertIn("EVIDENCE_REF_MISSING", reasons)
        self.assertNotIn("CLAIM_CEILING_EXCEEDED", reasons)
        self.assertNotIn("EVIDENCE_REF_MISMATCH", reasons)


class AgentHandoffBoundaryTests(unittest.TestCase):
    def test_invalid_box_fails_before_run_directory_or_provider_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "agent-run"
            provider = PromptSequenceProvider([agentrun.ALLOWED_CLAIM])
            with patch.object(
                agentrun,
                "verify_box_run",
                side_effect=BoxRunError("artifact digest mismatch"),
            ), patch.object(agentrun, "_harness_components") as harness:
                with self.assertRaisesRegex(
                    agentrun.AgentRunError,
                    "first-box handoff verification failed",
                ):
                    agentrun._run_agent_for_test(
                        root / "box",
                        run_dir,
                        provider=provider,
                    )
            self.assertFalse(run_dir.exists())
            self.assertEqual(provider.calls, 0)
            harness.assert_not_called()

    def test_agent_run_directory_cannot_overlap_verified_box(self):
        with tempfile.TemporaryDirectory() as directory:
            box_dir = Path(directory) / "box"
            box_dir.mkdir()
            run_dir = box_dir / "agent-run"
            provider = PromptSequenceProvider([agentrun.ALLOWED_CLAIM])
            with patch.object(
                agentrun,
                "verify_box_run",
                return_value=fake_verified_box(box_dir),
            ), patch.object(agentrun, "_harness_components") as harness:
                with self.assertRaisesRegex(
                    agentrun.AgentRunError,
                    "must be separate",
                ):
                    agentrun._run_agent_for_test(
                        box_dir,
                        run_dir,
                        provider=provider,
                    )
            self.assertFalse(run_dir.exists())
            self.assertEqual(provider.calls, 0)
            harness.assert_not_called()

    def test_direct_task_file_loader_is_fail_closed(self):
        with self.assertRaisesRegex(
            agentrun.AgentRunError,
            "direct agent task files are disabled",
        ):
            agentrun.load_task(Path("/not/consulted/task.json"))

    def test_public_runner_rejects_provider_and_gate_injection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "agent-run"
            with self.assertRaises(TypeError):
                agentrun.run_agent(
                    root / "box",
                    run_dir,
                    provider=PromptSequenceProvider([agentrun.ALLOWED_CLAIM]),
                )
            with self.assertRaises(TypeError):
                agentrun.run_agent(
                    root / "box",
                    run_dir,
                    claim_gate=strong_claim_gate,
                )
            self.assertFalse(run_dir.exists())


@unittest.skipUnless(HAS_Z3, "SMT negative control requires Z3")
class SmtGateTests(unittest.TestCase):
    def test_hostile_overclaim_constraint_is_load_bearing(self):
        observed = {name: True for name in agentrun._BOOLEAN_GATES}
        observed["requested_claim"] = agentrun.ALLOWED_CLAIM
        result = agentrun._smt_gate(observed)
        self.assertTrue(result["settled"])
        self.assertTrue(result["proposal_admitted"])
        self.assertEqual(
            result["hostile_overclaim"]["z3"]["status"],
            "BOUNDED_UNSAT",
        )
        self.assertEqual(
            result["claim_constraint_erased_control"]["z3"]["status"],
            "BOUNDED_SAT",
        )
        self.assertEqual(
            result["hostile_overclaim"]["cvc5"]["status"],
            "BOUNDED_UNSAT",
        )
        self.assertEqual(
            result["claim_constraint_erased_control"]["cvc5"]["status"],
            "BOUNDED_SAT",
        )

    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_cvc5_abstention_stops_settlement(self, solve_cvc5):
        solve_cvc5.return_value = SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "forced_cvc5_unknown",
            "cvc5",
        )
        observed = {name: True for name in agentrun._BOOLEAN_GATES}
        observed["requested_claim"] = agentrun.ALLOWED_CLAIM
        result = agentrun._smt_gate(observed)
        self.assertFalse(result["settled"])
        self.assertFalse(result["proposal_admitted"])
        self.assertEqual(result["proposal"]["cvc5"]["status"], "UNKNOWN")


class ToolProfilePredicateTests(unittest.TestCase):
    def test_in_memory_estate_tuple_is_accepted(self):
        receipt = fake_tool_receipt()["estate_receipt"]
        receipt["capabilities"] = tuple(receipt["capabilities"])
        self.assertEqual(agentrun._tool_profile_errors(receipt), [])

    def test_operation_control_cannot_be_omitted(self):
        receipt = fake_tool_receipt()["estate_receipt"]
        del receipt["capabilities"][0]["controls"]["operation"]
        errors = agentrun._tool_profile_errors(receipt)
        self.assertIn("TOOL_CONTROL_SET_INCOMPLETE", errors)

if __name__ == "__main__":
    unittest.main()
