from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox.sim_admission import SimAdmissionError, build_claim, verify_claim


class SimAdmissionContractTests(unittest.TestCase):
    def _claim(self, root: Path) -> Path:
        suite = root / "suite.json"
        basin = root / "basin.json"
        suite.write_text("{}\n", encoding="utf-8")
        basin.write_text("{}\n", encoding="utf-8")
        claim = root / "claim.json"
        claim.write_text(
            json.dumps(build_claim(capability_suite=suite, attractor_basin_envelope=basin)),
            encoding="utf-8",
        )
        return claim

    def test_valid_typed_claim_reaches_both_evaluator_owned_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            claim = self._claim(Path(directory))
            with patch("constraintbox.sim_admission._verify_capability_suite") as suite, patch(
                "constraintbox.sim_admission._verify_attractor_basin"
            ) as basin:
                result = verify_claim(claim)
            self.assertEqual(result["state"], "ELIGIBLE")
            suite.assert_called_once()
            basin.assert_called_once()
            self.assertFalse(result["release_allowed"])
            self.assertFalse(result["promotion_allowed"])

    def test_tampered_artifact_hash_never_reaches_the_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            claim = self._claim(Path(directory))
            body = json.loads(claim.read_text(encoding="utf-8"))
            body["capability_suite"]["sha256"] = "0" * 64
            claim.write_text(json.dumps(body), encoding="utf-8")
            with patch("constraintbox.sim_admission._verify_capability_suite") as suite:
                with self.assertRaisesRegex(SimAdmissionError, "does not bind"):
                    verify_claim(claim)
            suite.assert_not_called()


if __name__ == "__main__":
    unittest.main()
