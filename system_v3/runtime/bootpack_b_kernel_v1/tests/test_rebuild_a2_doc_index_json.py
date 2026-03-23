import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[4]
    module_path = repo_root / "system_v3" / "tools" / "rebuild_a2_doc_index_json.py"
    spec = importlib.util.spec_from_file_location("rebuild_a2_doc_index_json", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestRebuildA2DocIndexJson(unittest.TestCase):
    def test_build_doc_index_includes_owner_law_and_boot_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            core_docs_dir = repo_root / "core_docs"
            specs_dir = repo_root / "system_v3" / "specs"
            a2_state_dir = repo_root / "system_v3" / "a2_state"

            _write_text(core_docs_dir / "note.txt", "core docs\n")
            _write_text(specs_dir / "01_REQUIREMENTS_LEDGER.md", "# owner law\n")
            _write_text(specs_dir / "19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md", "# seal\n")
            _write_text(a2_state_dir / "A2_BOOT_READ_ORDER__CURRENT__v1.md", "# boot order\n")
            _write_text(a2_state_dir / "A2_KEY_CONTEXT_APPEND_LOG__v1.md", "# active boot\n")
            _write_text(a2_state_dir / "memory.jsonl", "{\"entry\": 1}\n")
            _write_text(a2_state_dir / "doc_index.json", "{\"stale\": true}\n")

            out_path = a2_state_dir / "doc_index.json"
            index = MODULE.build_doc_index(repo_root, core_docs_dir, specs_dir, a2_state_dir, out_path)

            paths = [doc["path"] for doc in index["documents"]]
            self.assertEqual(paths, sorted(paths))
            self.assertIn("core_docs/note.txt", paths)
            self.assertIn("system_v3/specs/01_REQUIREMENTS_LEDGER.md", paths)
            self.assertIn("system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md", paths)
            self.assertIn("system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md", paths)
            self.assertIn("system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md", paths)
            self.assertIn("system_v3/a2_state/memory.jsonl", paths)
            self.assertNotIn("system_v3/a2_state/doc_index.json", paths)

            owner = next(doc for doc in index["documents"] if doc["path"] == "system_v3/specs/01_REQUIREMENTS_LEDGER.md")
            boot = next(doc for doc in index["documents"] if doc["path"] == "system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md")
            state = next(doc for doc in index["documents"] if doc["path"] == "system_v3/a2_state/memory.jsonl")

            self.assertEqual(owner["layer"], "SYSTEM_V3_OWNER_LAW")
            self.assertEqual(owner["source_local_status"], "READ_ONLY_SOURCE")
            self.assertEqual(boot["layer"], "SYSTEM_V3_ACTIVE_BOOT")
            self.assertEqual(boot["source_local_status"], "ACTIVE_BOOT_SURFACE")
            self.assertEqual(state["layer"], "SYSTEM_V3_ACTIVE_BOOT")
            self.assertEqual(state["source_local_status"], "ACTIVE_BOOT_SURFACE")

    def test_main_writes_index_from_current_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            core_docs_dir = repo_root / "core_docs"
            specs_dir = repo_root / "system_v3" / "specs"
            a2_state_dir = repo_root / "system_v3" / "a2_state"

            _write_text(core_docs_dir / "note.txt", "core docs\n")
            _write_text(specs_dir / "01_REQUIREMENTS_LEDGER.md", "# owner law\n")
            _write_text(a2_state_dir / "A2_BOOT_READ_ORDER__CURRENT__v1.md", "# boot order\n")
            _write_text(a2_state_dir / "doc_index.json", "{\"stale\": true}\n")

            cwd = Path.cwd()
            try:
                os.chdir(repo_root)
                with contextlib.redirect_stdout(io.StringIO()):
                    result = MODULE.main([])
            finally:
                os.chdir(cwd)

            self.assertEqual(result, 0)
            out_path = a2_state_dir / "doc_index.json"
            self.assertTrue(out_path.is_file())
            output = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(output["schema"], "A2_DOC_INDEX_v1")
            self.assertEqual(output["schema_version"], 1)
            self.assertIn("system_v3/specs/01_REQUIREMENTS_LEDGER.md", {doc["path"] for doc in output["documents"]})
            self.assertNotIn("system_v3/a2_state/doc_index.json", {doc["path"] for doc in output["documents"]})


if __name__ == "__main__":
    unittest.main()
