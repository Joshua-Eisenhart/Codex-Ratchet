from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import validate_readiness_receipt


HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "results/readiness_receipt.json"


class ReadinessReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_current_receipt_validates(self) -> None:
        self.assertEqual(
            validate_readiness_receipt.validate(self.receipt, verify_files=True), []
        )

    def test_launch_and_authority_mutations_are_rejected(self) -> None:
        for key in (
            "launch_ready",
            "official_launch_allowed",
            "promotion_allowed",
            "formal_admission_allowed",
            "release_eligible",
            "scientific_claim_proven",
            "llm_gate_used",
            "provider_call_attempted",
            "install_attempted",
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.receipt)
                changed[key] = True
                self.assertTrue(
                    validate_readiness_receipt.validate(changed, verify_files=True)
                )

    def test_hold_reason_erasure_is_rejected(self) -> None:
        changed = copy.deepcopy(self.receipt)
        changed["hold_reasons"].pop()
        self.assertTrue(validate_readiness_receipt.validate(changed, verify_files=True))

    def test_expected_red_flip_is_rejected(self) -> None:
        changed = copy.deepcopy(self.receipt)
        changed["checks"]["v0_semantic_forcing_red_and_state_open"] = False
        self.assertTrue(validate_readiness_receipt.validate(changed, verify_files=True))

    def test_bound_input_hash_erasure_is_rejected(self) -> None:
        changed = copy.deepcopy(self.receipt)
        changed["inputs"]["frozen_validation"]["sha256"] = "0" * 64
        self.assertTrue(validate_readiness_receipt.validate(changed, verify_files=True))

    def test_lev_identity_rewrite_is_rejected(self) -> None:
        changed = copy.deepcopy(self.receipt)
        changed["lev"]["expected_commit"] = "0" * 40
        self.assertTrue(validate_readiness_receipt.validate(changed, verify_files=True))

    def test_builtin_mutation_vector_rejects_every_case(self) -> None:
        result = validate_readiness_receipt.mutation_selftest(self.receipt)
        self.assertTrue(result["all_rejected"])
        self.assertEqual(len(result["cases"]), 8)


if __name__ == "__main__":
    unittest.main()
