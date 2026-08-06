from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class GateStandaloneTests(unittest.TestCase):
    def test_box_only_copy_uses_its_own_claimgate_chain(self):
        source_box = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            clean_root = Path(directory).resolve()
            copied_box = clean_root / "constraint_box"
            shutil.copytree(source_box / "src", copied_box / "src")
            shutil.copytree(
                source_box / "claimgate_plugin",
                copied_box / "claimgate_plugin",
            )

            for ancestor in (clean_root, *clean_root.parents):
                self.assertFalse((ancestor / ".git").is_dir())
                self.assertFalse((ancestor / "system_v8").is_dir())

            receipt = (
                copied_box
                / "claimgate_plugin"
                / "fixtures"
                / "hook_clean_receipt.json"
            )
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(copied_box / "src")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "constraintbox",
                    "gate",
                    str(receipt),
                ],
                cwd=clean_root,
                env=environment,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["disposition"], "ADMITTED")
            self.assertEqual(result["chain_root"], str(copied_box))
            self.assertTrue(result["chain_root_inside_box"])
            self.assertEqual(
                result["tier0_checker"],
                str(copied_box / "claimgate_plugin" / "claimgate.mjs"),
            )


if __name__ == "__main__":
    unittest.main()
