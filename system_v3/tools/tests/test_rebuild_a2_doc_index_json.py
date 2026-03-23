from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestRebuildA2DocIndexJson(unittest.TestCase):
    def _repo_root(self, root: Path) -> Path:
        repo = root / "repo"
        (repo / "core_docs").mkdir(parents=True, exist_ok=True)
        (repo / "system_v3" / "specs").mkdir(parents=True, exist_ok=True)
        (repo / "system_v3" / "a2_state").mkdir(parents=True, exist_ok=True)
        return repo

    def test_rebuild_indexes_owner_law_and_active_boot_surfaces(self) -> None:
        tool = Path(__file__).resolve().parents[1] / "rebuild_a2_doc_index_json.py"

        with tempfile.TemporaryDirectory() as td:
            repo = self._repo_root(Path(td))
            (repo / "core_docs" / "A.md").write_text("core\n", encoding="utf-8")
            (repo / "system_v3" / "specs" / "01_REQUIREMENTS_LEDGER.md").write_text("owner law\n", encoding="utf-8")
            (repo / "system_v3" / "specs" / "02_OWNERSHIP_MAP.md").write_text("owner map\n", encoding="utf-8")
            (repo / "system_v3" / "a2_state" / "A2_BOOT_READ_ORDER__CURRENT__v1.md").write_text("boot order\n", encoding="utf-8")
            (repo / "system_v3" / "a2_state" / "A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md").write_text("intake\n", encoding="utf-8")
            (repo / "system_v3" / "00_CANONICAL_ENTRYPOINTS_v1.md").write_text("entrypoints\n", encoding="utf-8")
            (repo / "SKILL_SOURCE_CORPUS.md").write_text("corpus\n", encoding="utf-8")
            (repo / "system_v3" / "a2_state" / "doc_index.json").write_text("stale\n", encoding="utf-8")

            out = subprocess.check_output(["python3", str(tool)], cwd=repo, text=True).strip()
            payload = json.loads(out)

            out_path = Path(payload["out"])
            index = json.loads(out_path.read_text(encoding="utf-8"))
            documents = index["documents"]
            by_path = {row["path"]: row for row in documents}

            self.assertEqual(payload["doc_count"], len(documents))
            self.assertEqual(sorted(by_path), [row["path"] for row in documents])
            self.assertIn("core_docs/A.md", by_path)
            self.assertIn("SKILL_SOURCE_CORPUS.md", by_path)
            self.assertIn("system_v3/00_CANONICAL_ENTRYPOINTS_v1.md", by_path)
            self.assertIn("system_v3/specs/01_REQUIREMENTS_LEDGER.md", by_path)
            self.assertIn("system_v3/specs/02_OWNERSHIP_MAP.md", by_path)
            self.assertIn("system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md", by_path)
            self.assertIn("system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md", by_path)
            self.assertNotIn("system_v3/a2_state/doc_index.json", by_path)

            self.assertEqual("ROOT_SOURCE_CORPUS", by_path["SKILL_SOURCE_CORPUS.md"]["layer"])
            self.assertEqual("ACTIVE_FRONT_DOOR", by_path["SKILL_SOURCE_CORPUS.md"]["source_local_status"])
            self.assertEqual("SYSTEM_V3_BOOT_ENTRYPOINTS", by_path["system_v3/00_CANONICAL_ENTRYPOINTS_v1.md"]["layer"])
            self.assertEqual("READ_ONLY_SOURCE", by_path["system_v3/specs/01_REQUIREMENTS_LEDGER.md"]["source_local_status"])
            self.assertEqual("SYSTEM_V3_OWNER_LAW", by_path["system_v3/specs/02_OWNERSHIP_MAP.md"]["layer"])
            self.assertEqual("SYSTEM_V3_ACTIVE_BOOT", by_path["system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md"]["layer"])
            self.assertEqual("ACTIVE_BOOT_SURFACE", by_path["system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md"]["source_local_status"])


if __name__ == "__main__":
    unittest.main()
