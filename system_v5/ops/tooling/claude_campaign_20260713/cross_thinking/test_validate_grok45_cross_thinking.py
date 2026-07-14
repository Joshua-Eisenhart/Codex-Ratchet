#!/usr/bin/env python3
"""Negative controls for the Grok 4.5 advisory receipt validator."""

from __future__ import annotations

import json
import hashlib
import pathlib
import tempfile
import unittest

from validate_grok45_cross_thinking import DEFAULT_RECEIPT, validate


class Grok45ReceiptValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads(DEFAULT_RECEIPT.read_text(encoding="utf-8"))

    def validate_copy(self, receipt: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            return validate(path)

    def test_real_receipt_is_valid(self) -> None:
        self.assertEqual(validate(DEFAULT_RECEIPT), [])

    def test_forged_promotion_is_rejected(self) -> None:
        self.receipt["promotion_allowed"] = True
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("promotion_allowed" in error for error in errors))

    def test_forged_evidence_authority_is_rejected(self) -> None:
        self.receipt["evidence_allowed"] = True
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("evidence_allowed" in error for error in errors))

    def test_wrong_model_is_rejected(self) -> None:
        self.receipt["returned_model"] = "grok-4.3"
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("returned_model" in error for error in errors))

    def test_raw_hash_tampering_is_rejected(self) -> None:
        self.receipt["raw_response"]["sha256"] = "0" * 64
        errors = self.validate_copy(self.receipt)
        self.assertIn("raw_response.sha256 mismatch", errors)

    def test_replayed_timestamps_and_forged_git_head_are_rejected(self) -> None:
        self.receipt["started_at"] = "2000-01-01T00:00:00Z"
        self.receipt["completed_at"] = "2000-01-01T00:00:01Z"
        self.receipt["runner"]["git_head_before_run"] = "0" * 40
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("git head" in error for error in errors))

    def test_erased_provenance_is_rejected(self) -> None:
        for key in ("started_at", "completed_at", "endpoint", "provider_response_id", "usage"):
            self.receipt.pop(key)
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("receipt keys mismatch" in error for error in errors))

    def test_wrong_runtime_is_rejected(self) -> None:
        self.receipt["runner"]["python"] = "/usr/bin/python3"
        self.receipt["runner"]["command"][0] = "/usr/bin/python3"
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("Python identity" in error for error in errors))

    def test_contradictory_extra_claims_are_rejected(self) -> None:
        self.receipt.update(
            capability_fit_all_pass=True,
            partial_promotion=True,
            provider_opinion_ingested_as_evidence=True,
            verdict="partial promotion",
        )
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("receipt keys mismatch" in error for error in errors))

    def test_self_consistent_identity_substitution_is_rejected(self) -> None:
        target = pathlib.Path(__file__).resolve().parents[5] / "AGENTS.md"
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        self.receipt["prompt"] = {"path": str(target), "sha256": digest}
        self.receipt["raw_response"] = {"path": str(target), "sha256": digest, "nonempty": True}
        self.receipt["runner"]["path"] = str(target)
        self.receipt["runner"]["sha256"] = digest
        self.receipt["runner"]["command"][1] = str(target)
        errors = self.validate_copy(self.receipt)
        self.assertTrue(any("identity mismatch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
