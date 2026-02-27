from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


class TestBuildSaveProfileZip(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        repo = root / "repo"
        (repo / "core_docs").mkdir(parents=True, exist_ok=True)
        (repo / "system_v3").mkdir(parents=True, exist_ok=True)
        return repo

    def test_bootstrap_excludes_runs_archives_and_nested_archives(self) -> None:
        tool = Path(__file__).resolve().parents[4] / "system_v3" / "tools" / "build_save_profile_zip.py"
        with tempfile.TemporaryDirectory() as td:
            repo = self._repo(Path(td))
            (repo / "core_docs" / "A.md").write_text("A\n", encoding="utf-8")
            (repo / "core_docs" / "ignore.zip").write_bytes(b"x")
            (repo / "system_v3" / "spec.txt").write_text("S\n", encoding="utf-8")
            (repo / "system_v3" / "runs" / "RUN_X" / "state.json").parent.mkdir(parents=True, exist_ok=True)
            (repo / "system_v3" / "runs" / "RUN_X" / "state.json").write_text("{}", encoding="utf-8")
            (repo / "archive" / "old.txt").parent.mkdir(parents=True, exist_ok=True)
            (repo / "archive" / "old.txt").write_text("old\n", encoding="utf-8")
            (repo / "system_v3" / "a2_state" / "memory.jsonl").parent.mkdir(parents=True, exist_ok=True)
            (repo / "system_v3" / "a2_state" / "memory.jsonl").write_text("{\"x\":1}\n", encoding="utf-8")
            (repo / "system_v3" / "a2_state" / "snapshots" / "snap.zip").parent.mkdir(parents=True, exist_ok=True)
            (repo / "system_v3" / "a2_state" / "snapshots" / "snap.zip").write_bytes(b"zip")

            out_zip = repo / "out" / "bootstrap.zip"
            subprocess.check_call(
                [
                    "python3",
                    str(tool),
                    "--profile",
                    "bootstrap",
                    "--repo-root",
                    str(repo),
                    "--out-zip",
                    str(out_zip),
                ]
            )

            with zipfile.ZipFile(out_zip, "r") as zf:
                names = sorted(zf.namelist())
                self.assertIn("SYSTEM_SAVE_PROFILE_MANIFEST_v1.json", names)
                self.assertIn("core_docs/A.md", names)
                self.assertIn("system_v3/spec.txt", names)
                self.assertIn("system_v3/a2_state/memory.jsonl", names)
                self.assertNotIn("core_docs/ignore.zip", names)
                self.assertNotIn("system_v3/runs/RUN_X/state.json", names)
                self.assertNotIn("archive/old.txt", names)
                self.assertNotIn("system_v3/a2_state/snapshots/snap.zip", names)

    def test_debug_includes_selected_run_only(self) -> None:
        tool = Path(__file__).resolve().parents[4] / "system_v3" / "tools" / "build_save_profile_zip.py"
        with tempfile.TemporaryDirectory() as td:
            repo = self._repo(Path(td))
            (repo / "core_docs" / "A.md").write_text("A\n", encoding="utf-8")
            (repo / "system_v3" / "runs" / "RUN_1" / "zip_packets").mkdir(parents=True, exist_ok=True)
            (repo / "system_v3" / "runs" / "RUN_1" / "zip_packets" / "pkt.zip").write_bytes(b"pkt")
            (repo / "system_v3" / "runs" / "RUN_1" / "state.json").write_text("{\"ok\":1}", encoding="utf-8")
            (repo / "system_v3" / "runs" / "RUN_2" / "state.json").parent.mkdir(parents=True, exist_ok=True)
            (repo / "system_v3" / "runs" / "RUN_2" / "state.json").write_text("{\"ok\":2}", encoding="utf-8")
            (repo / "system_v3" / "runs" / "_CURRENT_STATE").mkdir(parents=True, exist_ok=True)
            (repo / "system_v3" / "runs" / "_CURRENT_STATE" / "state.json").write_text("{\"cur\":1}", encoding="utf-8")
            (repo / "system_v3" / "runs" / "_CURRENT_RUN.txt").write_text("RUN_1\n", encoding="utf-8")

            out_zip = repo / "out" / "debug.zip"
            subprocess.check_call(
                [
                    "python3",
                    str(tool),
                    "--profile",
                    "debug",
                    "--repo-root",
                    str(repo),
                    "--include-run-id",
                    "RUN_1",
                    "--out-zip",
                    str(out_zip),
                ]
            )

            with zipfile.ZipFile(out_zip, "r") as zf:
                names = sorted(zf.namelist())
                self.assertIn("system_v3/runs/RUN_1/state.json", names)
                self.assertIn("system_v3/runs/RUN_1/zip_packets/pkt.zip", names)
                self.assertIn("system_v3/runs/_CURRENT_STATE/state.json", names)
                self.assertIn("system_v3/runs/_CURRENT_RUN.txt", names)
                self.assertNotIn("system_v3/runs/RUN_2/state.json", names)

    def test_bootstrap_is_deterministic(self) -> None:
        tool = Path(__file__).resolve().parents[4] / "system_v3" / "tools" / "build_save_profile_zip.py"
        with tempfile.TemporaryDirectory() as td:
            repo = self._repo(Path(td))
            (repo / "core_docs" / "A.md").write_text("A\n", encoding="utf-8")
            (repo / "system_v3" / "B.txt").write_text("B\n", encoding="utf-8")
            out_a = repo / "out" / "a.zip"
            out_b = repo / "out" / "b.zip"

            subprocess.check_call(
                [
                    "python3",
                    str(tool),
                    "--profile",
                    "bootstrap",
                    "--repo-root",
                    str(repo),
                    "--out-zip",
                    str(out_a),
                ]
            )
            subprocess.check_call(
                [
                    "python3",
                    str(tool),
                    "--profile",
                    "bootstrap",
                    "--repo-root",
                    str(repo),
                    "--out-zip",
                    str(out_b),
                ]
            )
            self.assertEqual(out_a.read_bytes(), out_b.read_bytes())
            # Profile result output remains machine-readable JSON.
            out = subprocess.check_output(
                [
                    "python3",
                    str(tool),
                    "--profile",
                    "bootstrap",
                    "--repo-root",
                    str(repo),
                    "--out-zip",
                    str(out_b),
                ],
                text=True,
            ).strip()
            payload = json.loads(out)
            self.assertEqual("bootstrap", payload["profile"])
            self.assertTrue(payload["file_count"] >= 2)


if __name__ == "__main__":
    unittest.main()
