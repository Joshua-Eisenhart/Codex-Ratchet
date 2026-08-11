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


class ContainedCoreBundleTests(unittest.TestCase):
    def test_bundle_is_manifest_bound_and_runs_from_an_isolated_extraction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="constraintbox-contained-test-") as directory:
            bundle = Path(directory) / "constraintbox-core-0.3.4.zip"
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
            extracted = Path(directory) / "extracted"
            extracted.mkdir()
            with zipfile.ZipFile(bundle) as archive:
                archive.extractall(extracted)
            source_root = next(extracted.rglob("src/constraintbox"), None)
            self.assertIsNotNone(source_root)
            environment = {**__import__("os").environ, "PYTHONPATH": str(source_root.parent)}
            for command in ("doctor", "exercise"):
                verified = subprocess.run(
                    [sys.executable, "-m", "constraintbox", command, "--json"],
                    cwd=directory,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=90,
                )
                self.assertEqual(verified.returncode, 0, verified.stderr or verified.stdout)
                result = json.loads(verified.stdout)
                self.assertIn("schema", result)


if __name__ == "__main__":
    unittest.main()
