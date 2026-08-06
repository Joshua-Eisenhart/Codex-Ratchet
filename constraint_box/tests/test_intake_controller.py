from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest import mock

from constraintbox import (
    AgentProposalProfile,
    ConstraintBoxController,
    Disposition,
    HashChainLedger,
    RegisteredWorkerProfile,
    StrictJsonProfile,
    TaskRequest,
)
from constraintbox.contracts import ProfileOutcome
from constraintbox.python_runtime import (
    PythonRuntimeError,
    capture_python_runtime,
)


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "echo_worker.py"


def payload(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


@dataclass
class MutableProfile:
    profile_id: str = "mutable"
    claim_ceiling: str = "must never be admitted"

    def evaluate(self, raw: bytes, run_dir: Path) -> ProfileOutcome:
        del raw, run_dir
        return ProfileOutcome(Disposition.ELIGIBLE, "should_not_run")


@dataclass(frozen=True)
class FrozenProfileWithMutablePolicy:
    mutable_setting: list[str] = field(default_factory=lambda: ["unsafe"])
    profile_id: str = "frozen-shell-mutable-core"
    claim_ceiling: str = "must never be admitted"

    def evaluate(self, raw: bytes, run_dir: Path) -> ProfileOutcome:
        del raw, run_dir
        return ProfileOutcome(Disposition.ELIGIBLE, "should_not_run")


class IntakeControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        worker = RegisteredWorkerProfile(
            profile_id="constraintbox.worker.echo.profile.v1",
            worker_id="echo-worker",
            argv_template=(
                __import__("sys").executable,
                "-I",
                "{source}",
                "{input}",
                "{output}",
            ),
            source_path=WORKER,
            source_sha256=hashlib.sha256(WORKER.read_bytes()).hexdigest(),
        )
        self.ledger = HashChainLedger(self.root / "ledger.jsonl")
        self.controller = ConstraintBoxController(
            {
                "strict": StrictJsonProfile(),
                "proposal": AgentProposalProfile(),
                "echo": worker,
            },
            self.root / "runs",
            self.ledger,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_request(self, task: str, value: bytes, request_id: str):
        return self.controller.run(TaskRequest(task, value, request_id))

    def test_duplicate_key_blocks(self) -> None:
        result = self.run_request("strict", b'{"x":1,"x":2}', "duplicate")
        self.assertEqual(result.disposition, Disposition.BLOCKED)

    def test_nan_blocks(self) -> None:
        result = self.run_request("strict", b'{"x":NaN}', "nan")
        self.assertEqual(result.disposition, Disposition.BLOCKED)

    def test_case_variant_authority_field_blocks(self) -> None:
        result = self.run_request(
            "proposal",
            payload(
                {
                    "proposal_id": "p-case",
                    "candidate": {"Verdict": "PASS"},
                    "falsifiers": [],
                }
            ),
            "proposal-case",
        )
        self.assertEqual(result.disposition, Disposition.BLOCKED)

    def test_non_object_blocks(self) -> None:
        result = self.run_request("strict", b"[1,2,3]", "array")
        self.assertEqual(result.disposition, Disposition.BLOCKED)

    def test_unknown_task_cannot_select_profile(self) -> None:
        result = self.run_request(
            "fake-task",
            payload({"profile_id": "constraintbox.worker.echo.profile.v1"}),
            "unknown",
        )
        self.assertEqual(result.disposition, Disposition.BLOCKED)
        self.assertIsNone(result.profile_id)
        self.assertTrue(result.evidence["python_runtime"]["stable"])

    def test_runtime_identity_failure_holds_before_profile_evaluation(self) -> None:
        with mock.patch(
            "constraintbox.controller.capture_python_runtime",
            side_effect=PythonRuntimeError("deliberate identity failure"),
        ), mock.patch.object(
            StrictJsonProfile,
            "evaluate",
        ) as evaluate:
            result = self.run_request("strict", payload({"x": 1}), "runtime-fail")
        self.assertEqual(result.disposition, Disposition.HOLD)
        self.assertEqual(result.reason, "python_runtime_identity_error")
        self.assertFalse(result.evidence["python_runtime"]["stable"])
        evaluate.assert_not_called()

    def test_runtime_change_supersedes_an_eligible_profile_result(self) -> None:
        before = capture_python_runtime()
        after = json.loads(json.dumps(before))
        after["runtime_profile"]["flags"]["optimize"] = 99
        with mock.patch(
            "constraintbox.controller.capture_python_runtime",
            side_effect=[before, after],
        ):
            result = self.run_request("strict", payload({"x": 1}), "runtime-drift")
        self.assertEqual(result.disposition, Disposition.HOLD)
        self.assertEqual(
            result.reason,
            "python_runtime_changed_during_evaluation",
        )
        self.assertEqual(
            result.evidence["superseded_outcome"]["disposition"],
            "ELIGIBLE",
        )
        self.assertEqual(
            result.evidence["python_runtime"]["after"]["runtime_profile"]["flags"]["optimize"],
            99,
        )
        self.assertFalse(result.evidence["python_runtime"]["stable"])

    def test_profile_exception_becomes_hold_and_runtime_is_rechecked(self) -> None:
        with mock.patch.object(
            StrictJsonProfile,
            "evaluate",
            side_effect=RuntimeError("deliberate profile failure"),
        ):
            result = self.run_request(
                "strict",
                payload({"x": 1}),
                "profile-exception",
            )
        self.assertEqual(result.disposition, Disposition.HOLD)
        self.assertEqual(result.reason, "profile_evaluation_error")
        self.assertEqual(result.evidence["exception_type"], "RuntimeError")
        self.assertTrue(result.evidence["python_runtime"]["stable"])

    def test_profile_cannot_occupy_controller_runtime_evidence_key(self) -> None:
        poisoned = ProfileOutcome(
            Disposition.ELIGIBLE,
            "forged",
            {"python_runtime": {"stable": True}},
        )
        with mock.patch.object(
            StrictJsonProfile,
            "evaluate",
            return_value=poisoned,
        ):
            result = self.run_request(
                "strict",
                payload({"x": 1}),
                "reserved-evidence",
            )
        self.assertEqual(result.disposition, Disposition.HOLD)
        self.assertEqual(result.reason, "profile_used_reserved_evidence_key")
        self.assertTrue(result.evidence["python_runtime"]["stable"])

    def test_mutable_profile_is_rejected_at_controller_construction(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a frozen dataclass"):
            ConstraintBoxController(
                {"mutable": MutableProfile()},
                self.root / "mutable",
            )

    def test_frozen_profile_with_mutable_policy_is_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "mutable list"):
            ConstraintBoxController(
                {"mutable": FrozenProfileWithMutablePolicy()},
                self.root / "nested-mutable",
            )

    def test_path_traversal_request_id_blocks(self) -> None:
        result = self.run_request("echo", payload({"a": 1}), "../../outside")
        self.assertEqual(result.disposition, Disposition.BLOCKED)
        self.assertEqual(result.reason, "invalid_request_id")
        self.assertFalse((self.root.parent / "outside").exists())

    def test_oversize_payload_blocks_before_profile(self) -> None:
        controller = ConstraintBoxController(
            {"strict": StrictJsonProfile()},
            self.root / "bounded",
            max_payload_bytes=8,
        )
        oversized = b'{"value":12345}'
        real_sha256 = hashlib.sha256
        hashed_lengths: list[int] = []

        def recording_sha256(value: bytes = b""):
            hashed_lengths.append(len(value))
            return real_sha256(value)

        with mock.patch(
            "constraintbox.controller._SHA256",
            side_effect=recording_sha256,
        ):
            result = controller.run(TaskRequest("strict", oversized, "../../oversize"))

        bounded_prefix = oversized[:9]
        self.assertEqual(hashed_lengths, [len(bounded_prefix)])
        self.assertEqual(result.reason, "payload_exceeds_controller_bound")
        self.assertIsNone(result.input_sha256)
        self.assertFalse((self.root / "bounded").exists())
        result = controller.run(
            TaskRequest("strict", oversized, "oversize")
        )
        self.assertEqual(result.disposition, Disposition.BLOCKED)
        self.assertEqual(result.reason, "payload_exceeds_controller_bound")
        self.assertIsNone(result.input_sha256)
        self.assertEqual(result.evidence["observed_bytes"], len(oversized))
        self.assertEqual(result.evidence["maximum_bytes"], 8)
        self.assertEqual(
            result.evidence["inspected_prefix_bytes"],
            len(bounded_prefix),
        )
        self.assertEqual(
            result.evidence["bounded_prefix_sha256"],
            hashlib.sha256(bounded_prefix).hexdigest(),
        )
        self.assertFalse(result.evidence["input_digest_complete"])
        self.assertTrue(result.evidence["python_runtime"]["stable"])
        self.assertIn("before full hashing", result.claim_ceiling)

    def test_in_bound_payload_retains_exact_complete_digest(self) -> None:
        controller = ConstraintBoxController(
            {"strict": StrictJsonProfile()},
            self.root / "bounded-digest",
            max_payload_bytes=8,
        )
        content = b'{"x":1}'
        result = controller.run(TaskRequest("strict", content, "in-bound"))
        self.assertEqual(result.disposition, Disposition.ELIGIBLE)
        self.assertEqual(result.input_sha256, hashlib.sha256(content).hexdigest())

    def test_clean_agent_proposal_is_recorded_only(self) -> None:
        result = self.run_request(
            "proposal",
            payload(
                {
                    "proposal_id": "p1",
                    "candidate": {"mechanism": "bounded rival"},
                    "falsifiers": ["counterexample"],
                }
            ),
            "proposal-ok",
        )
        self.assertEqual(result.disposition, Disposition.ELIGIBLE)
        self.assertIn("no execution or admission", result.claim_ceiling)
        self.assertFalse(result.promotion_allowed)

    def test_nested_authority_field_is_blocked(self) -> None:
        result = self.run_request(
            "proposal",
            payload(
                {
                    "proposal_id": "p2",
                    "candidate": {"digest": {"verdict": "PASS"}},
                    "falsifiers": [],
                }
            ),
            "proposal-verdict",
        )
        self.assertEqual(result.disposition, Disposition.BLOCKED)
        self.assertEqual(result.reason, "proposal_attempted_controller_authority")
        self.assertIn("$.candidate.digest.verdict", result.evidence["forbidden_paths"])

    def test_worker_really_executes_and_binds_output(self) -> None:
        result = self.run_request("echo", payload({"a": 1}), "echo-ok")
        self.assertEqual(result.disposition, Disposition.ELIGIBLE)
        self.assertEqual(result.evidence["exit_code"], 0)
        self.assertIn("output_sha256", result.evidence)
        output = self.root / "runs" / "echo-ok" / "output.json"
        self.assertTrue(output.exists())

    def test_duplicate_worker_request_id_blocks_without_overwrite(self) -> None:
        first = self.run_request("echo", payload({"a": 1}), "echo-reused")
        second = self.run_request("echo", payload({"a": 2}), "echo-reused")
        self.assertEqual(first.disposition, Disposition.ELIGIBLE)
        self.assertEqual(second.disposition, Disposition.BLOCKED)
        self.assertEqual(second.reason, "request_run_directory_already_exists")

    def test_worker_source_drift_blocks(self) -> None:
        bad = RegisteredWorkerProfile(
            profile_id="bad",
            worker_id="bad",
            argv_template=(__import__("sys").executable, "{source}", "{input}", "{output}"),
            source_path=WORKER,
            source_sha256="0" * 64,
        )
        controller = ConstraintBoxController({"bad": bad}, self.root / "bad")
        result = controller.run(TaskRequest("bad", payload({"a": 1}), "bad"))
        self.assertEqual(result.disposition, Disposition.BLOCKED)
        self.assertEqual(result.reason, "worker_source_digest_mismatch")

    def test_ledger_tamper_is_detected(self) -> None:
        self.run_request("strict", payload({"x": 1}), "ledger-one")
        self.run_request("strict", payload({"x": 2}), "ledger-two")
        self.assertEqual(self.ledger.verify(), (True, "2 record(s)"))
        rows = self.ledger.path.read_text(encoding="utf-8").splitlines()
        first = json.loads(rows[0])
        first["record"]["reason"] = "forged"
        rows[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
        self.ledger.path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        valid, reason = self.ledger.verify()
        self.assertFalse(valid)
        self.assertIn("hash mismatch", reason)

    def test_ledger_tail_deletion_is_detected_by_retained_head(self) -> None:
        self.run_request("strict", payload({"x": 1}), "ledger-tail-one")
        self.run_request("strict", payload({"x": 2}), "ledger-tail-two")
        rows = self.ledger.path.read_text(encoding="utf-8").splitlines()
        self.ledger.path.write_text(rows[0] + "\n", encoding="utf-8")
        valid, reason = self.ledger.verify()
        self.assertFalse(valid)
        self.assertEqual(reason, "retained head mismatch")


if __name__ == "__main__":
    unittest.main()
