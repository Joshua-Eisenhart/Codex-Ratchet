from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox.capability_box import (
    CAPABILITY_DIRECTORY,
    CAPABILITY_RESULT_NAME,
    READY_FOR_CAPABILITY,
    RECEIPT_NAME,
    CapabilityBoxError,
    run_pytorch_capability_box,
    verify_pytorch_capability_box_run,
)
from constraintbox.intake import canonical_json


BOX_ROOT = Path(__file__).resolve().parents[1]
REQUEST = BOX_ROOT / "fixtures" / "requests" / "capability_pytorch_jacobian_v1.json"


class PytorchCapabilityBoxTests(unittest.TestCase):
    def test_fresh_real_capability_box_runs_and_revalidates_nested_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "capability-box"

            result, code = run_pytorch_capability_box(
                REQUEST.read_bytes(),
                run_dir,
            )

            self.assertEqual(code, 0)
            self.assertEqual(result["disposition"], READY_FOR_CAPABILITY)
            self.assertFalse(result["release_allowed"])
            self.assertFalse(result["promotion_allowed"])
            self.assertEqual(
                result["next_step"],
                "verified_capability_follow_on",
            )
            self.assertTrue((run_dir / CAPABILITY_DIRECTORY).is_dir())
            self.assertTrue((run_dir / CAPABILITY_RESULT_NAME).is_file())
            self.assertTrue((run_dir / RECEIPT_NAME).is_file())

            verified = verify_pytorch_capability_box_run(run_dir)

            self.assertEqual(verified.root, run_dir.resolve())
            self.assertEqual(verified.capability_id, "pytorch-jacobian-v1")
            self.assertEqual(len(verified.capability_receipt_sha256), 64)
            self.assertEqual(len(verified.flow_receipt_sha256), 64)

            body = json.loads((run_dir / RECEIPT_NAME).read_text(encoding="utf-8"))
            body["next_step"] = "forged"
            (run_dir / RECEIPT_NAME).write_bytes(canonical_json(body) + b"\n")
            with self.assertRaisesRegex(CapabilityBoxError, "not ready"):
                verify_pytorch_capability_box_run(run_dir)

    def test_wrong_authorized_capability_blocks_before_external_flow(self) -> None:
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        request["requested_external_tests"] = ["basic_packet_v1"]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "capability-box"
            with patch(
                "constraintbox.capability_box.run_pytorch_capability_flow"
            ) as run:
                result, code = run_pytorch_capability_box(
                    canonical_json(request),
                    run_dir,
                )
            self.assertFalse((run_dir / CAPABILITY_DIRECTORY).exists())

        self.assertEqual(code, 1)
        self.assertEqual(result["disposition"], "BLOCKED")
        self.assertEqual(
            result["reason"],
            "requested_external_capability_not_bound_to_capability_box",
        )
        run.assert_not_called()

    def test_missing_external_authorization_blocks_before_flow(self) -> None:
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        request["allowed_actions"].remove("run_external_tools")
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "capability-box"
            with patch(
                "constraintbox.capability_box.run_pytorch_capability_flow"
            ) as run:
                result, code = run_pytorch_capability_box(
                    canonical_json(request),
                    run_dir,
                )

        self.assertEqual(code, 4)
        self.assertEqual(result["disposition"], "PARKED")
        self.assertEqual(
            result["reason"],
            "request_did_not_reach_capability_eligibility",
        )
        run.assert_not_called()
