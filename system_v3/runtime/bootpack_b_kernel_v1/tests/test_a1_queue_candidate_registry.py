from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_object_drafts"
sys.path.insert(0, str(TOOLS))

from validate_a1_queue_candidate_registry import validate as validate_registry  # noqa: E402


class TestA1QueueCandidateRegistry(unittest.TestCase):
    def test_empty_registry_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "registry.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual([], packet["candidate_family_slice_jsons"])
            self.assertTrue(validate_registry(packet)["valid"])

    def test_registry_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "registry.json"
            family_slice = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--family-slice-json",
                    str(family_slice),
                    "--selected-family-slice-json",
                    str(family_slice),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(validate_registry(packet)["valid"])


if __name__ == "__main__":
    unittest.main()
