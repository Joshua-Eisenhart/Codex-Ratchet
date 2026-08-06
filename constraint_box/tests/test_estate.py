from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import constraintbox.estate as estate_module
from constraintbox.estate import CapabilityState, EstateRunner
from constraintbox.maintenance import (
    load_trusted_receipt_set,
    major_run_preflight,
)
from constraintbox.parity import compare_density_receipts


PACK_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = PACK_ROOT.parent / "external_sim_estate" / "legacy_estate_v2"
WORKER = EXTERNAL_ROOT / "workers" / "capability_worker.py"
BLOCKER = EXTERNAL_ROOT / "workers" / "import_blocker.py"
FIXTURE = EXTERNAL_ROOT / "fixtures" / "manifold_fixture_v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EstateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manifest(self, controller_sha: str | None = None) -> Path:
        path = self.root / "estate.json"
        body = {
            "schema": "constraintbox.sim-estate.v1",
            "status": "PROPOSED",
            "promotion_allowed": False,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "controller_sha256": controller_sha
            or digest(Path(estate_module.__file__)),
            "worker_sha256": digest(WORKER),
            "import_blocker_sha256": digest(BLOCKER),
            "tiers": [
                {
                    "tier_id": "S1",
                    "name": "test-finite",
                    "boot_budget_seconds": 10,
                    "capabilities": [
                        {
                            "id": "stdlib_finite",
                            "required": True,
                            "locked_version": "builtin",
                        }
                    ],
                }
            ],
        }
        path.write_text(json.dumps(body), encoding="utf-8")
        return path

    def density_receipt(
        self,
        layer: str,
        capability_id: str,
        observed: dict[str, object],
    ) -> Path:
        fixture_sha256 = "1" * 64
        path = self.root / f"{layer}.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.sim-tier-receipt.v2",
                    "layer_id": layer,
                    "layer_name": f"test-{layer}",
                    "mode": "acceptance",
                    "state": "READY",
                    "manifest_sha256": "2" * 64,
                    "fixture_sha256": fixture_sha256,
                    "controller_sha256": "3" * 64,
                    "python_executable": sys.executable,
                    "python_version": (
                        f"{sys.version_info.major}.{sys.version_info.minor}"
                    ),
                    "environment": {"state": "TEST"},
                    "elapsed_seconds": 0.01,
                    "capabilities": [
                        {
                            "capability_id": capability_id,
                            "required": True,
                            "state": "READY",
                            "reason": "test_fixture",
                            "expected_version": "test",
                            "observed_version": "test",
                            "elapsed_seconds": 0.01,
                            "worker_sha256": "4" * 64,
                            "fixture_sha256": fixture_sha256,
                            "controls": {
                                "positive": True,
                                "mutation": True,
                                "replay": True,
                                "severance": True,
                            },
                            "evidence": {"observed": observed},
                        }
                    ],
                    "generated_at_utc": "2026-07-25T19:00:00+00:00",
                    "promotion_allowed": False,
                }
            ),
            encoding="utf-8",
        )
        return path

    def trust_receipts(self, paths: list[Path]):
        trust_path = self.root / "trusted-receipts.json"
        trust_path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.trusted-receipt-set.v1",
                    "trust_set_id": "estate-test-controller-pin",
                    "receipt_bindings": [
                        {
                            "receipt_sha256": digest(path),
                            "receipt_schema": "constraintbox.sim-tier-receipt.v2",
                            "layer_id": json.loads(
                                path.read_text(encoding="utf-8")
                            )["layer_id"],
                        }
                        for path in paths
                    ],
                    "promotion_allowed": False,
                }
            ),
            encoding="utf-8",
        )
        return load_trusted_receipt_set(
            trust_path,
            expected_manifest_sha256=digest(trust_path),
        )

    def test_stdlib_capability_runs_four_of_five_controls(self) -> None:
        """stdlib_finite has no block_import, so severance never runs.

        The old name for this test was `..._runs_all_acceptance_controls`, which
        asserted this exact four-key dict — documenting the gap as correct. The
        exemption is legitimate; naming it "all" was not. The receipt must now
        name the control it did not measure and must not claim "all".
        """
        runner = EstateRunner(PACK_ROOT, self.manifest(), FIXTURE)
        receipt = runner.run_tier("S1", "acceptance")
        self.assertEqual(receipt.state, CapabilityState.READY)
        capability = receipt.capabilities[0]
        self.assertEqual(
            capability.controls,
            {
                "positive": True,
                "dispatch": True,
                "mutation": True,
                "replay": True,
            },
        )
        self.assertNotIn("severance", capability.controls)
        self.assertEqual(capability.reason, "measured_controls_passed_others_not_run")
        self.assertEqual(
            capability.evidence.get("controls_not_measured"), ["severance"]
        )
        self.assertEqual(
            capability.evidence["controller_worker_environment"],
            {
                "ephemeral_cache_config": ["NUMBA_CACHE_DIR", "MPLCONFIGDIR"],
                "host_cache_config_inherited": False,
            },
        )

    def test_controller_source_drift_fails_before_worker(self) -> None:
        runner = EstateRunner(PACK_ROOT, self.manifest("0" * 64), FIXTURE)
        receipt = runner.run_tier("S1", "boot")
        self.assertEqual(receipt.state, CapabilityState.DRIFT)
        self.assertEqual(
            receipt.capabilities[0].reason,
            "controller_source_digest_mismatch",
        )

    def test_real_controller_receipt_is_accepted_when_externally_bound(self) -> None:
        runner = EstateRunner(PACK_ROOT, self.manifest(), FIXTURE)
        receipt_path = self.root / "controller-produced-S1.json"
        receipt = runner.run_tier("S1", "acceptance").to_dict()
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        generated = datetime.fromisoformat(receipt["generated_at_utc"])
        result = major_run_preflight(
            [receipt_path],
            ["S1"],
            24,
            trusted_receipts=self.trust_receipts([receipt_path]),
            now=generated + timedelta(minutes=1),
        )
        self.assertEqual(result["disposition"], "READY")
        self.assertEqual(result["trust_binding"]["status"], "BOUND")

    def test_virtual_environment_interpreter_path_is_not_resolved(self) -> None:
        venv_python = self.root / "candidate" / "bin" / "python"
        venv_python.parent.mkdir(parents=True)
        os.symlink(sys.executable, venv_python)
        runner = EstateRunner(
            PACK_ROOT,
            self.manifest(),
            FIXTURE,
            venv_python,
        )
        self.assertEqual(runner.python, venv_python)

    def test_worker_gets_fresh_controller_cache_directories(self) -> None:
        """Workers cannot inherit host Numba or matplotlib cache locations."""

        worker = self.root / "cache_probe.py"
        worker.write_text(
            "import json, os\n"
            "from pathlib import Path\n"
            "numba = Path(os.environ['NUMBA_CACHE_DIR'])\n"
            "matplotlib = Path(os.environ['MPLCONFIGDIR'])\n"
            "assert numba.is_dir() and matplotlib.is_dir()\n"
            "assert str(numba) != '/hostile/numba'\n"
            "assert str(matplotlib) != '/hostile/matplotlib'\n"
            "print(json.dumps({'numba': str(numba), 'matplotlib': str(matplotlib)}))\n",
            encoding="utf-8",
        )
        runner = EstateRunner(PACK_ROOT, self.manifest(), FIXTURE)
        runner.worker = worker
        with patch.dict(
            os.environ,
            {
                "NUMBA_CACHE_DIR": "/hostile/numba",
                "MPLCONFIGDIR": "/hostile/matplotlib",
            },
            clear=False,
        ):
            code, stdout, stderr, _elapsed, timed_out = runner._run_worker(
                "numpy_density", FIXTURE, 10
            )
        self.assertEqual(code, 0, stderr.decode("utf-8", errors="replace"))
        self.assertFalse(timed_out)
        observed = json.loads(stdout)
        # The context is torn down as soon as the child has exited, so no
        # cache/config contents persist as estate evidence or host state.
        self.assertFalse(Path(observed["numba"]).exists())
        self.assertFalse(Path(observed["matplotlib"]).exists())

    def test_cross_estate_density_parity_requires_two_families(self) -> None:
        observed = {
            "trace": 1.0,
            "eigenvalues": [0.1464466094067262, 0.8535533905932737],
            "rank": 2,
            "hartley_bits": 1.0,
            "von_neumann_bits": 0.6008760366928562,
            "dephased_entropy_bits": 0.8112781244591328,
        }
        paths = [
            self.density_receipt("E0", "numpy_density", observed),
            self.density_receipt("E1", "jax_density", observed),
        ]
        result = compare_density_receipts(
            paths, trusted_receipts=self.trust_receipts(paths)
        )
        self.assertEqual(result["state"], "CONSISTENT")
        self.assertTrue(result["comparisons"][0]["consistent"])
        self.assertTrue(result["consistency_only"])
        self.assertFalse(result["execution_verified"])
        self.assertFalse(result["engine_readiness_verified"])

    def test_cross_estate_density_parity_rejects_one_family(self) -> None:
        path = self.density_receipt(
            "E0",
            "numpy_density",
            {
                field: 1.0
                for field in (
                    "trace",
                    "rank",
                    "hartley_bits",
                    "von_neumann_bits",
                    "dephased_entropy_bits",
                )
            }
            | {"eigenvalues": [0.0, 1.0]},
        )
        result = compare_density_receipts(
            [path], trusted_receipts=self.trust_receipts([path])
        )
        self.assertEqual(result["state"], "INSUFFICIENT")

    def test_hand_authored_ready_json_without_trust_is_parked(self) -> None:
        """A matching number plus a READY label is not an execution receipt."""
        path = self.root / "hostile-fake-ready.json"
        path.write_text(
            json.dumps(
                {
                    "capabilities": [
                        {
                            "capability_id": "numpy_density",
                            "state": "READY",
                            "evidence": {"observed": {"trace": 1.0}},
                        },
                        {
                            "capability_id": "jax_density",
                            "state": "READY",
                            "evidence": {"observed": {"trace": 1.0}},
                        },
                    ],
                    "state": "READY",
                }
            ),
            encoding="utf-8",
        )
        result = compare_density_receipts([path])
        self.assertEqual(result["state"], "PARKED")
        self.assertEqual(
            result["problems"], [{"reason": "trusted_receipt_set_missing"}]
        )
        self.assertEqual(result["comparisons"], [])

    def test_trusted_digest_does_not_make_minimal_fake_a_typed_receipt(self) -> None:
        """Even a pinned blob must have controller-produced receipt provenance."""
        path = self.root / "pinned-but-fake.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.sim-tier-receipt.v2",
                    "layer_id": "E0",
                    "state": "READY",
                    "capabilities": [],
                }
            ),
            encoding="utf-8",
        )
        result = compare_density_receipts(
            [path], trusted_receipts=self.trust_receipts([path])
        )
        self.assertEqual(result["state"], "PARKED")
        self.assertEqual(result["problems"][0]["reason"], "receipt_type_invalid")

    def test_receipt_tampered_after_controller_binding_is_parked(self) -> None:
        observed = {
            field: 1.0
            for field in (
                "trace",
                "rank",
                "hartley_bits",
                "von_neumann_bits",
                "dephased_entropy_bits",
            )
        } | {"eigenvalues": [0.0, 1.0]}
        path = self.density_receipt("E0", "numpy_density", observed)
        trusted = self.trust_receipts([path])
        body = json.loads(path.read_text(encoding="utf-8"))
        body["capabilities"][0]["evidence"]["observed"]["trace"] = 99.0
        path.write_text(json.dumps(body), encoding="utf-8")
        result = compare_density_receipts([path], trusted_receipts=trusted)
        self.assertEqual(result["state"], "PARKED")
        self.assertEqual(
            result["problems"][0]["reason"], "receipt_digest_not_trusted"
        )


if __name__ == "__main__":
    unittest.main()
