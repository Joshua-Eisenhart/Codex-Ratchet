#!/usr/bin/env python3
"""Focused fail-closed mutation controls for the independent validator."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import validate_free_length_dual_ratchet_schedule_selector_v0 as validator


class ValidatorMutationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = validator.validate_packet()

    def assert_rejected(self, callback) -> None:
        with self.assertRaises(validator.ValidationError):
            callback()

    def test_current_packet_passes(self) -> None:
        self.assertFalse(self.context.packet.summary["scientific_pass"])
        self.assertEqual(
            self.context.packet.summary["scientific_verdict"],
            self.context.packet.spec["scientific_pass_rule"]["red_verdict"],
        )

    def test_duplicate_json_key_and_nonfinite_number_rejected(self) -> None:
        for payload in ('{"x": 1, "x": 2}', '{"x": 1e999}'):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"
                path.write_text(payload, encoding="utf-8")
                self.assert_rejected(lambda: validator.strict_json_load(path))

    def test_catalog_word_mutation_rejected(self) -> None:
        catalog = copy.deepcopy(self.context.packet.catalog)
        catalog["candidates"][1]["operator_indices"] = [0, 2]
        self.assert_rejected(
            lambda: validator.verify_catalog(catalog, self.context.packet.spec)
        )

    def test_source_hash_mutation_rejected(self) -> None:
        packet = copy.copy(self.context.packet)
        packet.summary = dict(packet.summary)
        packet.summary["source_hashes"] = dict(packet.summary["source_hashes"])
        packet.summary["source_hashes"][validator.relative(validator.PRODUCER_PATH)] = "0" * 64
        self.assert_rejected(lambda: validator.verify_source_and_hash_locks(packet))

    def test_raw_shape_mutation_rejected(self) -> None:
        raw = dict(self.context.packet.raw)
        raw["arrays"] = dict(raw["arrays"])
        raw["arrays"]["combined_score"] = dict(raw["arrays"]["combined_score"])
        raw["arrays"]["combined_score"]["shape"] = [36, 2, 11585]
        self.assert_rejected(
            lambda: validator.verify_raw(
                raw, self.context.packet.spec, validator.sha256(validator.CATALOG_PATH)
            )
        )

    def test_raw_base64_byte_mutation_rejected(self) -> None:
        raw = dict(self.context.packet.raw)
        raw["arrays"] = dict(raw["arrays"])
        descriptor = dict(raw["arrays"]["geometry_loss"])
        data = descriptor["data"]
        descriptor["data"] = ("A" if data[0] != "A" else "B") + data[1:]
        raw["arrays"]["geometry_loss"] = descriptor
        self.assert_rejected(
            lambda: validator.verify_raw(
                raw, self.context.packet.spec, validator.sha256(validator.CATALOG_PATH)
            )
        )

    def test_summary_winner_mutation_rejected(self) -> None:
        summary = copy.deepcopy(self.context.packet.summary)
        summary["scenario_results"][0]["engines"]["Type1_left"]["winner_cycle_ids"] = [
            "L4:Ti>Te>Fi>Fe"
        ]
        self.assert_rejected(
            lambda: validator.verify_main_summary(
                summary,
                self.context.main_arrays,
                self.context.candidates,
                self.context.packet.spec,
            )
        )

    def test_scientific_verdict_flip_rejected(self) -> None:
        summary = dict(self.context.packet.summary)
        summary["scientific_pass"] = True
        self.assert_rejected(
            lambda: validator.verify_ceilings_and_verdict(
                summary,
                self.context.packet.spec,
                self.context.packet.prereg,
                self.context.packet.summary["scientific_signal"],
                True,
                True,
            )
        )

    def test_non_boolean_ceiling_rejected(self) -> None:
        summary = dict(self.context.packet.summary)
        summary["promotion_allowed"] = 0
        self.assert_rejected(lambda: validator.verify_boolean_types(summary, "summary"))

    def test_blocked_consumer_removal_rejected(self) -> None:
        summary = dict(self.context.packet.summary)
        summary["blocked_consumers"] = summary["blocked_consumers"][:-1]
        self.assert_rejected(
            lambda: validator.verify_ceilings_and_verdict(
                summary,
                self.context.packet.spec,
                self.context.packet.prereg,
                self.context.packet.summary["scientific_signal"],
                self.context.packet.summary["physical_preconditions_pass"],
                self.context.packet.summary["gating_controls_pass"],
            )
        )

    def test_control_array_mutation_rejected(self) -> None:
        controls = dict(self.context.control_arrays)
        controls["operator_identity_erasure"] = controls[
            "operator_identity_erasure"
        ].copy()
        controls["operator_identity_erasure"][0, 0, 0] += 0.1
        self.assert_rejected(
            lambda: validator.verify_controls(
                self.context.packet.summary,
                self.context.main_arrays,
                controls,
                self.context.candidates,
                self.context.packet.spec,
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
