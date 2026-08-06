from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_contained_core_bundle.py"
VERIFY = ROOT / "scripts" / "verify_contained_core_bundle.py"


class ContainedCoreBundleTests(unittest.TestCase):
    def test_bundle_is_manifest_bound_and_runs_from_an_isolated_extraction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="constraintbox-contained-test-") as directory:
            bundle = Path(directory) / "constraintbox-core-0.3.4.zip"
            receipt = Path(directory) / "contained-core-verification.json"
            built = subprocess.run(
                [sys.executable, str(BUILD), "--output", str(bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=90,
            )
            self.assertEqual(built.returncode, 0, built.stderr or built.stdout)
            with zipfile.ZipFile(bundle) as archive:
                names = archive.namelist()
                self.assertTrue(any(name.endswith("/CONTAINMENT_MANIFEST.json") for name in names))
                self.assertTrue(any(name.endswith("/PRODUCT_BOUNDARY.md") for name in names))
                self.assertTrue(
                    any(
                        name.endswith(
                            "/fixtures/formal/"
                            "levos_flowmind_dna_compile_pinned_topology_fixture.json"
                        )
                        for name in names
                    )
                )
                self.assertTrue(
                    any(
                        name.endswith(
                            "/src/constraintbox/lev_eval_observation_flow.py"
                        )
                        for name in names
                    )
                )
                self.assertTrue(
                    any(
                        name.endswith("/tests/test_lev_eval_observation_flow.py")
                        for name in names
                    )
                )
                self.assertFalse(any("external_sim_estate" in name for name in names))
                self.assertFalse(any("/receipts/" in name for name in names))
                self.assertFalse(any("/results/" in name for name in names))
                self.assertFalse(any(name.endswith("/.DS_Store") for name in names))
                self.assertFalse(any("/.AppleDouble/" in name for name in names))
                self.assertFalse(any(name.endswith("/claimgate_plugin/failures.jsonl") for name in names))
            verified = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    "--bundle",
                    str(bundle),
                    "--receipt",
                    str(receipt),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr or verified.stdout)
            result = json.loads(verified.stdout)
            self.assertEqual(json.loads(receipt.read_text(encoding="utf-8")), result)
            self.assertEqual(result["state"], "VERIFIED")
            self.assertEqual(result["verification_interpreter"], sys.executable)
            self.assertFalse(result["external_estate_included"])
            self.assertFalse(result["promotion_allowed"])
            self.assertEqual(
                {row["name"]: row["actual_exit"] for row in result["commands"]},
                {
                    "runtime_verify": 0,
                    "demo": 0,
                    "mmm_smt": 0,
                    "request_missing_assumptions": 4,
                    "formal_symbolic": 0,
                    "formal_boundary_contract_valid": 0,
                    "formal_boundary_contract_conflation_blocks": 1,
                    "boundary_contract_regression_unit": 0,
                    "formal_maude_transition": 0,
                    "formal_levos_flowmind_pinned_topology": 0,
                    "failure_repair_contained_contract_unit": 0,
                    "execution_lease_minilev_unit": 0,
                    "integrated_receipt_lease_minilev_unit": 0,
                    "proposal_minilev_rustworkx_topology_unit": 0,
                    "foreign_lev_eval_observation_unit": 0,
                    "foreign_lev_eval_observation_minilev_flow_unit": 0,
                    "leviathan_minilev_reference_unit": 0,
                    "external_validation_runner_unit": 0,
                    "hypothesis_adversarial_intake_unit": 0,
                    "external_validation_index_unit": 0,
                    "contained_provider_harness_unit": 0,
                    "proposal_provider_policy_unit": 0,
                    "attractor_basin_adapter_boundary_unit": 0,
                    "attractor_basin_controller_cli_surface": 0,
                    "attractor_basin_envelope_verifier_cli_surface": 0,
                    "external_estate_absent_is_parked": 4,
                    "in_box_claimgate_admitted_fixture": 0,
                    "in_box_claimgate_insufficient_depth_fixture": 3,
                },
            )


if __name__ == "__main__":
    unittest.main()
