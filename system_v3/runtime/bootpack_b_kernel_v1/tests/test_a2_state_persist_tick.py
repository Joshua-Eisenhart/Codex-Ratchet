from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestA2StatePersistTick(unittest.TestCase):
    def test_tick_appends_and_shards_memory(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        script = repo_root / "system_v3" / "tools" / "a2_state_persist_tick.py"

        with tempfile.TemporaryDirectory() as td:
            a2 = Path(td) / "a2_state"
            a2.mkdir(parents=True, exist_ok=True)

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

