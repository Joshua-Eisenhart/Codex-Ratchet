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
        "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json": "{}\n",
        "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json": "{}\n",
        "A2_UPDATE_NOTE__NOT_WHITELISTED__v1.md": "ignore me\n",
    }.items():
        path = a2 / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class TestA2StatePersistTick(unittest.TestCase):
    def test_tick_appends_and_shards_memory(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        script = repo_root / "system_v3" / "tools" / "a2_state_persist_tick.py"

        with tempfile.TemporaryDirectory() as td:
            a2 = Path(td) / "a2_state"
            a2.mkdir(parents=True, exist_ok=True)
            _seed_recovery_boot_surfaces(a2)

            # Seed a memory log that will exceed the shard cap after a tick append.
            (a2 / "memory.jsonl").write_text(("x" * 300) + "\n", encoding="utf-8")

            out = subprocess.check_output(
                [
                    "python3",
                    str(script),
                    "--a2-state-dir",
                    str(a2),
                    "--max-memory-bytes",
                    "200",
                    "--retain-shards",
                    "8",
                ],
                text=True,
            ).strip()
            j = json.loads(out)
            self.assertEqual(j["seq"], 1)
            self.assertTrue((a2 / "autosave_seq.txt").exists())

            shard_dir = a2 / "memory_shards"
            self.assertTrue((shard_dir / "index_v1.json").exists())
            index = json.loads((shard_dir / "index_v1.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index), 1)

            # New live memory.jsonl should exist and contain a shard-open marker.
            live = (a2 / "memory.jsonl").read_text(encoding="utf-8")
            self.assertIn("\"type\":\"memory_shard_open\"", live)

    def test_tick_write_latest_zip_includes_recovery_boot_surfaces(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        script = repo_root / "system_v3" / "tools" / "a2_state_persist_tick.py"

        with tempfile.TemporaryDirectory() as td:
            a2 = Path(td) / "a2_state"
            a2.mkdir(parents=True, exist_ok=True)
            _seed_recovery_boot_surfaces(a2)
            (a2 / "memory.jsonl").write_text("seed\n", encoding="utf-8")

            subprocess.check_output(
                [
                    "python3",
                    str(script),
                    "--a2-state-dir",
                    str(a2),
                    "--write-latest-zip",
                    "--max-memory-bytes",
                    "1000000",
                    "--retain-shards",
                    "8",
                ],
                text=True,
            )

            zip_path = a2 / "snapshots" / "a2_state_snapshot_latest.zip"
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = set(zf.namelist())

            self.assertIn("A2_BOOT_READ_ORDER__CURRENT__v1.md", names)
            self.assertIn("A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md", names)
            self.assertIn("A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json", names)
            self.assertIn("A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json", names)
            self.assertNotIn("A2_UPDATE_NOTE__NOT_WHITELISTED__v1.md", names)
