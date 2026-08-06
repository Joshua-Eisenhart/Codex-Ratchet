from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.paired_extension import (
    PairedExtensionError,
    validate_paired_fixture,
    validate_paired_fixture_file,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "cr" / "paired_whole_extension_v1.json"


class PairedExtensionTests(unittest.TestCase):
    def test_reference_fixture_passes_and_exposes_load_bearing_history(self) -> None:
        receipt = validate_paired_fixture_file(FIXTURE)
        self.assertEqual(receipt["status"], "PASS")
        self.assertFalse(receipt["promotion_allowed"])
        observation = receipt["canonical_observation"]
        self.assertEqual(observation["order_scar"], [3])
        self.assertEqual(observation["mss_frontier"], ["minimal_exclude_scar"])
        self.assertTrue(observation["history_is_load_bearing"])

    def test_promotion_mutation_is_rejected(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["promotion_allowed"] = True
        with self.assertRaises(PairedExtensionError):
            validate_paired_fixture(payload)

    def test_history_deletion_mutation_fails_the_gate(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["whole"]["extension_after_history_deletion"]["bo"] = ["scar_replay"]
        receipt = validate_paired_fixture(payload)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["history_deletion_collapses"])


if __name__ == "__main__":
    unittest.main()
