from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.adapters.cr import cr_semantic_profile, cr_whole_state_obligations
from constraintbox.adapters.lev import to_lev_evidence_event
from constraintbox.applicability import ApplicabilityRegistry
from constraintbox.contracts import DecisionRecord, Disposition


ROOT = Path(__file__).resolve().parents[1]


class SemanticAndAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = cr_semantic_profile(ROOT / "config" / "semantic_registry_v1.json")
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def evaluate(self, relative_path: str):
        return self.profile.evaluate((ROOT / relative_path).read_bytes(), self.run_dir)

    def test_valid_typed_claim_is_structurally_eligible(self) -> None:
        outcome = self.evaluate("fixtures/manifold/semantic_claim_valid.json")
        self.assertEqual(outcome.disposition, Disposition.ELIGIBLE)
        self.assertEqual(outcome.reason, "semantic_claim_structurally_eligible")

    def test_entropy_soup_is_blocked(self) -> None:
        outcome = self.evaluate("fixtures/hostile/semantic_claim_entropy_soup.json")
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "heterogeneous_scalarization_forbidden")

    def test_absolute_mss_is_blocked(self) -> None:
        outcome = self.evaluate("fixtures/hostile/semantic_claim_absolute_mss.json")
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "absolute_or_undefined_mss_forbidden")

    def test_provider_authority_is_blocked_at_any_depth(self) -> None:
        body = json.loads(
            (ROOT / "fixtures/manifold/semantic_claim_valid.json").read_text()
        )
        body["evidence"] = {"verdict": "PASS"}
        outcome = self.profile.evaluate(json.dumps(body).encode(), self.run_dir)
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "claim_attempted_controller_authority")

    def test_applicability_is_controller_owned(self) -> None:
        registry = ApplicabilityRegistry.from_path(
            ROOT / "config" / "applicability_v1.json"
        )
        parked = registry.assess("finite_constraint", {"stdlib_finite": "READY"})
        self.assertEqual(parked["disposition"], "PARKED")
        eligible = registry.assess(
            "finite_constraint",
            {"stdlib_finite": "READY", "z3_finite": "READY"},
        )
        self.assertEqual(eligible["disposition"], "ELIGIBLE_FOR_CHECKS")
        self.assertFalse(eligible["promotion_allowed"])

    def test_cr_obligations_are_proposals_not_admissions(self) -> None:
        obligations = cr_whole_state_obligations()
        self.assertEqual(obligations["status"], "PROPOSED")
        self.assertFalse(obligations["promotion_allowed"])

    def test_lev_adapter_translates_but_does_not_promote(self) -> None:
        decision = DecisionRecord(
            schema="constraintbox.decision.v1",
            request_id="r1",
            task_kind="finite-constraint",
            profile_id="constraintbox.constraints.finite.v1",
            policy_sha256="a" * 64,
            input_sha256="b" * 64,
            disposition=Disposition.ELIGIBLE,
            reason="bounded_witness_found",
            evidence={"solver_status": "BOUNDED_SAT"},
            claim_ceiling="one finite encoding was checked",
        )
        event = to_lev_evidence_event(
            decision, session_id="session-1", event_id="event-1"
        )
        self.assertEqual(event["disposition"], "ELIGIBLE")
        self.assertFalse(event["promotion_allowed"])
        with self.assertRaises(ValueError):
            to_lev_evidence_event(decision, session_id="", event_id="event-1")


if __name__ == "__main__":
    unittest.main()
