from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox.boxrun import (
    BLOCKED,
    PARKED,
    READY_FOR_PROPOSAL,
    BoxRunError,
    run_first_box,
    verify_box_run,
)
from constraintbox.intake import canonical_json


BOX_ROOT = Path(__file__).resolve().parents[1]
REQUEST = BOX_ROOT / "fixtures" / "requests" / "assemble_constraintbox_v1.json"


class FakePassingBroker:
    calls = 0

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def run(self):
        type(self).calls += 1
        return {
            "schema": "constraintbox.external-engine-packet-receipt.v1",
            "status": "PASS",
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "engine_readiness_claim": False,
            "promotion_allowed": False,
        }


class FakeFailingBroker(FakePassingBroker):
    def run(self):
        type(self).calls += 1
        return {
            "schema": "constraintbox.external-engine-packet-receipt.v1",
            "status": "FAIL",
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "engine_readiness_claim": False,
            "promotion_allowed": False,
        }


class FirstBoxRunTests(unittest.TestCase):
    def setUp(self) -> None:
        FakePassingBroker.calls = 0
        FakeFailingBroker.calls = 0
        self.request_raw = REQUEST.read_bytes()

    def run_box(
        self,
        request_raw: bytes,
        broker_class=FakePassingBroker,
        validation_errors: tuple[str, ...] = (),
    ):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_dir = Path(temporary.name) / "run"
        with patch(
            "constraintbox.boxrun.ExternalEnginePacketBroker",
            broker_class,
        ), patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=validation_errors,
        ):
            result, code = run_first_box(request_raw, run_dir)
        return result, code, run_dir

    def test_complete_request_runs_external_system_then_stops_before_llm(self):
        result, code, run_dir = self.run_box(self.request_raw)
        self.assertEqual(code, 0)
        self.assertEqual(result["disposition"], READY_FOR_PROPOSAL)
        self.assertEqual(FakePassingBroker.calls, 1)
        self.assertFalse(result["release_allowed"])
        self.assertFalse(result["promotion_allowed"])
        self.assertEqual(
            result["next_step"],
            "untrusted_proposal_generation",
        )
        self.assertTrue(
            (run_dir / "compiled_user_context.txt").is_file()
        )
        self.assertTrue(
            (run_dir / "external_audit_brief.json").is_file()
        )
        self.assertTrue(
            (run_dir / "external_engine_packet.json").is_file()
        )
        recorded = json.loads(
            (run_dir / "box_receipt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(recorded["disposition"], READY_FOR_PROPOSAL)

    def test_unresolved_request_parks_before_external_process(self):
        body = json.loads(self.request_raw)
        body["assumption_state"] = "unknown"
        body["assumptions"] = []
        result, code, run_dir = self.run_box(canonical_json(body))
        self.assertEqual(code, 4)
        self.assertEqual(result["disposition"], PARKED)
        self.assertEqual(FakePassingBroker.calls, 0)
        self.assertIsNone(result["external_engine_packet"])
        self.assertFalse(
            (run_dir / "external_engine_packet.json").exists()
        )

    def test_missing_external_authorization_blocks_before_broker(self):
        body = json.loads(self.request_raw)
        body["allowed_actions"].remove("run_external_tools")
        body["requested_external_tests"] = []
        result, code, _ = self.run_box(canonical_json(body))
        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], BLOCKED)
        self.assertEqual(
            result["reason"],
            "external_tool_execution_not_authorized",
        )
        self.assertEqual(FakePassingBroker.calls, 0)

    def test_missing_llm_authorization_blocks_before_broker(self):
        body = json.loads(self.request_raw)
        body["allowed_actions"].remove("invoke_llm")

        result, code, _ = self.run_box(canonical_json(body))

        self.assertEqual(code, 1)
        self.assertEqual(
            result["reason"],
            "untrusted_proposal_generation_not_authorized",
        )
        self.assertEqual(FakePassingBroker.calls, 0)

    def test_missing_receipt_authorization_creates_no_run_directory(self):
        body = json.loads(self.request_raw)
        body["allowed_actions"].remove("write_receipts")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_dir = Path(temporary.name) / "run"

        with patch(
            "constraintbox.boxrun.ExternalEnginePacketBroker",
            FakePassingBroker,
        ):
            result, code = run_first_box(canonical_json(body), run_dir)

        self.assertEqual(code, 1)
        self.assertEqual(result["reason"], "receipt_writing_not_authorized")
        self.assertFalse(run_dir.exists())
        self.assertEqual(FakePassingBroker.calls, 0)

    def test_malformed_request_preserves_intake_failure_without_writing(self):
        malformed = self.request_raw.rstrip()
        malformed = malformed[:-1] + b', "goal": "duplicate"}'
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_dir = Path(temporary.name) / "run"

        result, code = run_first_box(malformed, run_dir)

        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], BLOCKED)
        self.assertEqual(result["reason"], "strict_request_intake_failed")
        self.assertFalse(run_dir.exists())

    def test_executed_external_failure_blocks(self):
        result, code, _ = self.run_box(
            self.request_raw,
            broker_class=FakeFailingBroker,
        )
        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], BLOCKED)
        self.assertEqual(
            result["reason"],
            "external_function_packet_executed_and_failed",
        )
        self.assertFalse(result["release_allowed"])

    def test_fabricated_pass_receipt_is_an_evaluation_error(self):
        result, code, _ = self.run_box(
            self.request_raw,
            validation_errors=("rows are missing",),
        )

        self.assertEqual(code, 5)
        self.assertEqual(result["disposition"], "EVALUATION_ERROR")
        self.assertEqual(
            result["reason"],
            "external_packet_pass_receipt_invalid",
        )
        self.assertEqual(
            result["external_receipt_validation_errors"],
            ["rows are missing"],
        )

    def test_existing_run_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "existing"
            run_dir.mkdir()
            marker = run_dir / "keep.txt"
            marker.write_text("owner data", encoding="utf-8")
            with self.assertRaisesRegex(BoxRunError, "already exists"):
                run_first_box(
                    self.request_raw,
                    run_dir,
                )
            self.assertEqual(marker.read_text(encoding="utf-8"), "owner data")

    def test_ready_box_verifier_captures_personalized_handoff(self):
        _, _, run_dir = self.run_box(self.request_raw)

        with patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=(),
        ) as validator:
            verified = verify_box_run(run_dir)

        self.assertEqual(verified.root, run_dir.resolve())
        self.assertEqual(verified.request_id, "assemble-constraintbox-v1")
        self.assertEqual(len(verified.receipt_sha256), 64)
        self.assertEqual(len(verified.request_sha256), 64)
        self.assertEqual(len(verified.profile_sha256), 64)
        self.assertEqual(len(verified.context_sha256), 64)
        self.assertEqual(len(verified.external_engine_packet_sha256), 64)
        self.assertIn("[USER PROFILE ", verified.context_text)
        self.assertIn(
            b'"request_id":"assemble-constraintbox-v1"',
            verified.request_canonical,
        )
        validator.assert_called_once()

    def test_ready_box_verifier_rejects_context_byte_mutation(self):
        _, _, run_dir = self.run_box(self.request_raw)
        context_path = run_dir / "compiled_user_context.txt"
        context_path.write_bytes(context_path.read_bytes() + b"\nmutated")

        with patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=(),
        ), self.assertRaisesRegex(BoxRunError, "artifact digest mismatch"):
            verify_box_run(run_dir)

    def test_ready_box_verifier_rejects_nonready_receipt(self):
        _, _, run_dir = self.run_box(self.request_raw)
        receipt_path = run_dir / "box_receipt.json"
        body = json.loads(receipt_path.read_text(encoding="utf-8"))
        body["disposition"] = PARKED
        receipt_path.write_bytes(canonical_json(body) + b"\n")

        with patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=(),
        ), self.assertRaisesRegex(BoxRunError, "disposition is not proposal-ready"):
            verify_box_run(run_dir)

    def test_ready_box_verifier_rejects_extra_artifact(self):
        _, _, run_dir = self.run_box(self.request_raw)
        (run_dir / "unindexed.txt").write_text("not part of the box", encoding="utf-8")

        with patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=(),
        ), self.assertRaisesRegex(BoxRunError, "artifact set differs"):
            verify_box_run(run_dir)

    def test_ready_box_verifier_does_not_follow_artifact_symlink(self):
        _, _, run_dir = self.run_box(self.request_raw)
        context_path = run_dir / "compiled_user_context.txt"
        target = run_dir.parent / "context-outside-box.txt"
        target.write_bytes(context_path.read_bytes())
        context_path.unlink()
        context_path.symlink_to(target)

        with patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=(),
        ), self.assertRaisesRegex(BoxRunError, "could not open box artifact"):
            verify_box_run(run_dir)


if __name__ == "__main__":
    unittest.main()
