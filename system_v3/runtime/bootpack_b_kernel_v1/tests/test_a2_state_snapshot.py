from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestA2StateSnapshot(unittest.TestCase):
    def test_snapshot_zip_is_deterministic_for_fixed_id(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        script = repo_root / "system_v3" / "tools" / "a2_state_snapshot.py"
        a2_state_dir = repo_root / "system_v3" / "a2_state"

        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td)
            cmd = [
                "python3",
                str(script),
                "--a2-state-dir",
                str(a2_state_dir),
                "--out-dir",
                str(out_root),
                "--snapshot-id",
                "TEST_FIXED",
            ]
            r1 = json.loads(subprocess.check_output(cmd, text=True).strip())
            out_dir = Path(r1["out_dir"])
            z1 = (out_dir / "a2_state_snapshot.zip").read_bytes()

            r2 = json.loads(subprocess.check_output(cmd, text=True).strip())
            self.assertEqual(r1["out_dir"], r2["out_dir"])
            self.assertEqual(r1["manifest_sha256"], r2["manifest_sha256"])

            z2 = (out_dir / "a2_state_snapshot.zip").read_bytes()
            self.assertEqual(z1, z2)
