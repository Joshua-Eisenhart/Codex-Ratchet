#!/usr/bin/env python3
"""Adversarial tests for the H lineage contract differential validator."""

from __future__ import annotations

import copy
import json
import unittest

from validate_lineage_contract_differential_v3 import (
    DEFAULT_RECEIPT,
    DEFAULT_SOURCE,
    receipt_content_sha256,
    sha256_file,
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

    def test_self_consistent_source_path_and_hash_substitution_is_rejected(self) -> None:
        substitute = DEFAULT_SOURCE.parents[5] / "AGENTS.md"
        candidate = copy.deepcopy(self.receipt)
        candidate["sources"]["audit_source_path"] = str(substitute.resolve())
        candidate["sources"]["audit_source_sha256"] = sha256_file(substitute)
        errors = validate(self.reseal(candidate), source_path=substitute)
        self.assertTrue(any("source path must be the pinned" in error for error in errors))

    def test_self_consistent_validator_path_and_hash_substitution_is_rejected(self) -> None:
        substitute = DEFAULT_SOURCE.parents[5] / "AGENTS.md"
        candidate = copy.deepcopy(self.receipt)
        candidate["sources"]["validator_source_path"] = str(substitute.resolve())
        candidate["sources"]["validator_source_sha256"] = sha256_file(substitute)
        errors = validate(self.reseal(candidate), validator_path=substitute)
        self.assertTrue(any("validator path must be this pinned" in error for error in errors))

    def test_wrong_archive_path_and_matching_hash_are_rejected(self) -> None:
        substitute = DEFAULT_SOURCE.parents[5] / "AGENTS.md"
        candidate = copy.deepcopy(self.receipt)
        candidate["sources"]["archive_path"] = str(substitute.resolve())
        candidate["sources"]["archive_sha256"] = sha256_file(substitute)
        errors = validate(self.reseal(candidate), archive_path=substitute)
        self.assertTrue(any("archive path must be the pinned" in error for error in errors))

    def test_forged_command_runtime_and_evidence_metadata_are_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            raw["command"] = []
            raw["runner_identity"] = {
                "python_executable": "/usr/bin/python3",
                "python_version": "fabricated",
                "rustworkx_version": "fabricated",
            }
            raw["evidence_level"] = "L5_production_integrity_proof"
            raw["process_exit_semantics"] = "exit 0 proves a production integrity defect"

        errors = self.errors_after(mutate)
        self.assertTrue(any("producer command mismatch" in error for error in errors))
        self.assertTrue(any("fresh producer semantic mismatch" in error for error in errors))

    def test_fixture_replay_cannot_replace_actual_packet_mutations(self) -> None:
        def mutate(raw: dict) -> None:
            cycle = copy.deepcopy(raw["same_packet_cycle_ledger"])
            dag = copy.deepcopy(raw["fixture_controls"]["valid_dag_positive"])
            projection = raw["actual_packet_topology_mutations"]["dag_projection"]
            projection.update(
                method="replayed generic DAG fixture",
                removed_edge_count=1,
                removed_variation_ids=["fabricated_variation_id"],
                result=dag,
            )
            injection = raw["actual_packet_topology_mutations"][
                "rehash_consistent_reverse_edge_injection"
            ]
            injection.update(
                method="replayed original packet scenario; no mutation executed",
                mutation={
                    "reversed_existing_variation_id": "fabricated",
                    "injected_edge": {
                        "operator": "audit_only_reverse_edge_injection",
                        "parent_id": "x",
                        "child_id": "y",
                        "variation_id": "fabricated",
                    },
                },
                result=cycle,
            )

        errors = self.errors_after(mutate)
        self.assertTrue(any("fresh producer semantic mismatch" in error for error in errors))

    def test_fabricated_topology_bodies_and_mode_reasons_are_rejected(self) -> None:
        def mutate(raw: dict) -> None:
            scenarios = (
                raw["same_packet_cycle_ledger"],
                raw["fixture_controls"]["cycle_negative"],
                raw["actual_packet_topology_mutations"][
                    "rehash_consistent_reverse_edge_injection"
                ]["result"],
            )
            for scenario in scenarios:
                scenario["topology_observation"].update(
                    node_count=0,
                    edge_count=999999,
                    one_cycle={"nodes": ["fabricated"], "edges": []},
                )
                scenario["native_mode"]["reason"] = "fabricated native reason"
                scenario["strict_ancestry_dag_mode"]["reason"] = (
                    "fabricated strict reason"
                )

        errors = self.errors_after(mutate)
        self.assertTrue(any("fresh producer semantic mismatch" in error for error in errors))

    def test_unchecked_semantic_prose_cannot_be_resealed(self) -> None:
        def mutate(raw: dict) -> None:
            raw["semantic_verdict"]["native_contract_accepts_cycles"] = False
            raw["semantic_verdict"]["audit_only_strict_contract_rejects_cycles"] = False
            raw["mode_contracts"]["strict_ancestry_dag_mode"]["definition"] = (
                "production verifier now enforces a DAG"
            )

        errors = self.errors_after(mutate)
        self.assertTrue(any("fresh producer semantic mismatch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
