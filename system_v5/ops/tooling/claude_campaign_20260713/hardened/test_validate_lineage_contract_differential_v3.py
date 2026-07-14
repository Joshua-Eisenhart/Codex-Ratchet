#!/usr/bin/env python3
"""Adversarial tests for the H lineage contract differential validator."""

from __future__ import annotations

import copy
import json
import unittest

from validate_lineage_contract_differential_v3 import (
    DEFAULT_RECEIPT,
    receipt_content_sha256,
    validate,
)


class LineageContractDifferentialValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads(DEFAULT_RECEIPT.read_text(encoding="utf-8"))

    def reseal(self, candidate: dict) -> dict:
        candidate["receipt_content_sha256"] = receipt_content_sha256(candidate)
        return candidate

    def errors_after(self, mutate) -> list[str]:
        candidate = copy.deepcopy(self.receipt)
        mutate(candidate)
        return validate(self.reseal(candidate))

    def test_real_receipt_is_valid(self) -> None:
        self.assertEqual(validate(self.receipt), [])

    def test_forged_h_green_is_rejected_even_when_resealed(self) -> None:
        errors = self.errors_after(lambda raw: raw.update(all_pass=True))
        self.assertTrue(any("all_pass" in error for error in errors))

    def test_forged_integrity_defect_is_rejected_even_when_resealed(self) -> None:
        errors = self.errors_after(lambda raw: raw.update(integrity_defect_admitted=True))
        self.assertTrue(any("integrity_defect_admitted" in error for error in errors))

    def test_forged_strict_acceptance_of_packet_cycle_is_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            raw["same_packet_cycle_ledger"]["strict_ancestry_dag_mode"]["accepted"] = True

        errors = self.errors_after(mutate)
        self.assertTrue(any("same_packet_cycle_ledger strict accepted" in error for error in errors))

    def test_forged_native_acceptance_of_hash_tamper_is_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            raw["tampered_hash_control"]["native_mode"]["accepted"] = True

        errors = self.errors_after(mutate)
        self.assertTrue(any("tampered_hash_control native accepted" in error for error in errors))

    def test_relabeling_strict_mode_as_packet_native_is_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            raw["mode_contracts"]["strict_ancestry_dag_mode"]["authority"] = "packet_native"

        errors = self.errors_after(mutate)
        self.assertTrue(any("strict contract must remain audit-only" in error for error in errors))

    def test_claim_ceiling_expansion_is_rejected(self) -> None:
        errors = self.errors_after(
            lambda raw: raw.update(claim_ceiling="production integrity defect confirmed")
        )
        self.assertTrue(any("claim_ceiling" in error for error in errors))

    def test_erasing_blocked_consumers_is_rejected(self) -> None:
        errors = self.errors_after(lambda raw: raw.update(blocked_consumers=[]))
        self.assertTrue(any("blocked consumers" in error for error in errors))

    def test_self_consistent_source_hash_substitution_is_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            raw["sources"]["audit_source_sha256"] = "0" * 64

        errors = self.errors_after(mutate)
        self.assertTrue(any("audit source sha256" in error for error in errors))

    def test_unsealed_receipt_mutation_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.receipt)
        candidate["h_lane_status"] = "green"
        errors = validate(candidate)
        self.assertTrue(any("receipt_content_sha256" in error for error in errors))

    def test_alias_claim_is_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            raw["production_defect_verified"] = True

        errors = self.errors_after(mutate)
        self.assertTrue(any("top-level receipt keys" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
