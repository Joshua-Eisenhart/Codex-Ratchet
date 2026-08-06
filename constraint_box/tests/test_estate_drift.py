from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import constraintbox.estate as estate_module
from constraintbox.estate import CapabilityState, EstateRunner


PACK_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = PACK_ROOT.parent / "external_sim_estate" / "legacy_estate_v2"
WORKER = EXTERNAL_ROOT / "workers" / "capability_worker.py"
BLOCKER = EXTERNAL_ROOT / "workers" / "import_blocker.py"
FIXTURE = EXTERNAL_ROOT / "fixtures" / "manifold_fixture_v1.json"
DRIFTED_VERSION = "0.0.0-not-installed"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EstateDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import numpy  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest("numpy is not importable") from exc

        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest_path = self.root / "estate.json"
        body = {
            "schema": "constraintbox.sim-estate.v1",
            "status": "PROPOSED",
            "promotion_allowed": False,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "controller_sha256": digest(Path(estate_module.__file__)),
            "worker_sha256": digest(WORKER),
            "import_blocker_sha256": digest(BLOCKER),
            "tiers": [
                {
                    "tier_id": "S1",
                    "name": "test-drift",
                    "boot_budget_seconds": 10,
                    "capabilities": [
                        {
                            "id": "numpy_density",
                            "required": True,
                            "locked_version": DRIFTED_VERSION,
                        }
                    ],
                }
            ],
        }
        self.manifest_path.write_text(json.dumps(body), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_drifted_tier(self):
        runner = EstateRunner(PACK_ROOT, self.manifest_path, FIXTURE)
        return runner.run_tier("S1", "acceptance")

    def test_drifted_capability_runs_acceptance_controls(self) -> None:
        tier = self.run_drifted_tier()
        capability = tier.capabilities[0]

        self.assertEqual(capability.state, CapabilityState.DRIFT)
        self.assertEqual(
            capability.reason, "installed_version_differs_from_tested_lock"
        )
        self.assertNotEqual(capability.controls, {"positive": False})
        for control in (
            "operation",
            "mutation",
            "replay",
            "severance",
            "dispatch",
            "positive",
        ):
            self.assertIn(control, capability.controls)
            self.assertIsInstance(capability.controls[control], bool)
        self.assertTrue(capability.controls["positive"])
        self.assertEqual(
            capability.evidence["version_drift"]["expected"], DRIFTED_VERSION
        )
        self.assertEqual(
            capability.evidence["version_drift"]["observed"],
            capability.observed_version,
        )
        self.assertIsInstance(capability.observed_version, str)
        self.assertTrue(capability.observed_version)

    def test_drifted_tier_is_not_promoted_when_controls_pass(self) -> None:
        tier = self.run_drifted_tier()

        self.assertTrue(all(tier.capabilities[0].controls.values()))
        self.assertEqual(tier.capabilities[0].state, CapabilityState.DRIFT)
        self.assertEqual(tier.state, CapabilityState.DRIFT)

    def test_passing_drift_reason_excludes_control_failure(self) -> None:
        capability = self.run_drifted_tier().capabilities[0]

        self.assertTrue(all(capability.controls.values()))
        self.assertEqual(
            capability.reason, "installed_version_differs_from_tested_lock"
        )
        self.assertNotEqual(
            capability.reason,
            (
                "installed_version_differs_from_tested_lock"
                "_and_one_or_more_controls_failed"
            ),
        )


if __name__ == "__main__":
    unittest.main()
