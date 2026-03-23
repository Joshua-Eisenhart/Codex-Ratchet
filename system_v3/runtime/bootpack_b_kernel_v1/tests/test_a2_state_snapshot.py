from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


def _seed_recovery_boot_surfaces(a2: Path) -> None:
    for rel, text in {
        "A2_BOOT_READ_ORDER__CURRENT__v1.md": "boot order\n",
        "A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md": "state record\n",
        "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json": "{}\n",
        "A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json": "{}\n",
        "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json": "{}\n",
        "A2_UPDATE_NOTE__NOT_WHITELISTED__v1.md": "ignore me\n",
    }.items():
        path = a2 / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


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

    def test_snapshot_includes_recovery_boot_surfaces_and_excludes_note_stack(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        script = repo_root / "system_v3" / "tools" / "a2_state_snapshot.py"

        with tempfile.TemporaryDirectory() as td:
            a2 = Path(td) / "a2_state"
            a2.mkdir(parents=True, exist_ok=True)
            _seed_recovery_boot_surfaces(a2)

            out_root = Path(td) / "snapshots"
            r = json.loads(
                subprocess.check_output(
                    [
                        "python3",
                        str(script),
                        "--a2-state-dir",
                        str(a2),
                        "--out-dir",
                        str(out_root),
                        "--snapshot-id",
                        "TEST_BOOT",
                    ],
                    text=True,
                ).strip()
            )

            with zipfile.ZipFile(Path(r["out_dir"]) / "a2_state_snapshot.zip", "r") as zf:
                names = set(zf.namelist())

            self.assertIn("A2_BOOT_READ_ORDER__CURRENT__v1.md", names)
            self.assertIn("A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md", names)
            self.assertIn("A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json", names)
            self.assertIn("A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json", names)
            self.assertIn("A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json", names)
            self.assertNotIn("A2_UPDATE_NOTE__NOT_WHITELISTED__v1.md", names)
