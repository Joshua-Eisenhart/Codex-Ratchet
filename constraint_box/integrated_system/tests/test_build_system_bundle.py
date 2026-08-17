from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SYSTEM = Path(__file__).resolve().parents[1]
BOX = SYSTEM.parent
BUILD = SYSTEM / "scripts" / "build_system_bundle.py"
TOP_LEVEL = "constraintbox-integrated-system-v1"


class BuildSystemBundleTests(unittest.TestCase):
    def _build(self, output: Path) -> dict[str, object]:
        completed = subprocess.run(
            [
                sys.executable,
                str(BUILD),
                "--box-root",
                str(BOX),
                "--output",
                str(output),
            ],
            cwd=BOX,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["state"], "BUILT")
        return result

    def test_build_system_bundle_is_deterministic_and_has_one_runtime_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cb-integrated-bundle-test-") as directory:
            root = Path(directory)
            first = root / "one.zip"
            second = root / "two.zip"
            first_result = self._build(first)
            second_result = self._build(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_result["bundle_sha256"], second_result["bundle_sha256"])

            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(names)
                self.assertTrue(all(name.startswith(f"{TOP_LEVEL}/") for name in names))
                self.assertIn(f"{TOP_LEVEL}/00_READ_THIS_FIRST.md", names)
                self.assertIn(f"{TOP_LEVEL}/SYSTEM_ARCHITECTURE.md", names)
                self.assertIn(f"{TOP_LEVEL}/HOW_TO_RUN.md", names)
                self.assertIn(f"{TOP_LEVEL}/WHAT_IS_PROVEN.md", names)
                self.assertIn(f"{TOP_LEVEL}/bin/cb", names)
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/SYSTEM_ARCHITECTURE.md",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/HOW_TO_RUN.md",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/WHAT_IS_PROVEN.md",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime/controller_src/constraintbox/core_cli.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime/zip_agent_src/constraintbox_zip_agent/runtime.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/zip_agent/src/constraintbox_zip_agent/runtime.py",
                    names,
                )
                self.assertNotIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/src/constraintbox/core_cli.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/light_runtime/src/constraintbox/core_cli.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/cb_light_cli.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/mmm/packs/nominalist.md",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/mmm/packs/smt.md",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/.claude/settings.json",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/.claude/hooks/session-start.sh",
                    names,
                )
                self.assertNotIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/pyproject.toml",
                    names,
                )
                self.assertFalse(
                    [name for name in names if "/PROJECT/constraint_box/docs/" in name]
                )
                forbidden = (
                    "__pycache__",
                    ".pytest_cache",
                    "/cache/",
                    ".sqlite",
                    ".pyc",
                    "/receipts/",
                    "probe_rows.jsonl",
                    "gate_rows.jsonl",
                )
                self.assertFalse(
                    [name for name in names if any(marker in name for marker in forbidden)]
                )

                manifest = json.loads(archive.read(f"{TOP_LEVEL}/SYSTEM_MANIFEST.json"))
                metadata = json.loads(archive.read(f"{TOP_LEVEL}/BUNDLE_METADATA.json"))
                self.assertEqual(manifest["schema"], "constraintbox.integrated-system-manifest.v1")
                self.assertEqual(manifest["file_count"], len(manifest["files"]))
                self.assertEqual(metadata["manifest_sha256"], hashlib.sha256(archive.read(f"{TOP_LEVEL}/SYSTEM_MANIFEST.json")).hexdigest())
                self.assertFalse(manifest["light_heavy_boundary"]["jax_in_light"])
                self.assertFalse(manifest["light_heavy_boundary"]["heavy_interpreter_included"])

                for row in manifest["files"]:
                    member = f"{TOP_LEVEL}/{row['path']}"
                    payload = archive.read(member)
                    self.assertEqual(row["bytes"], len(payload), member)
                    self.assertEqual(row["sha256"], hashlib.sha256(payload).hexdigest(), member)

                checksums = archive.read(f"{TOP_LEVEL}/SHA256SUMS").decode("utf-8").splitlines()
                checksum_map = {
                    path: digest for digest, _, path in (line.partition("  ") for line in checksums)
                }
                for member in names:
                    if member.endswith("/SHA256SUMS"):
                        continue
                    self.assertIn(member, checksum_map)
                    self.assertEqual(checksum_map[member], hashlib.sha256(archive.read(member)).hexdigest())

                cb_mode = archive.getinfo(f"{TOP_LEVEL}/bin/cb").external_attr >> 16
                self.assertEqual(cb_mode & 0o111, 0o111)

    def test_build_system_bundle_fresh_extract_imports_both_runtime_packages(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cb-integrated-bundle-extract-") as directory:
            bundle = Path(directory) / "system.zip"
            self._build(bundle)
            extracted = Path(directory) / "extract"
            extracted.mkdir()
            with zipfile.ZipFile(bundle) as archive:
                archive.extractall(extracted)
            package_root = extracted / TOP_LEVEL / "PROJECT" / "constraint_box"
            controller = package_root / "integrated_system" / "runtime" / "controller_src"
            zip_agent = package_root / "integrated_system" / "runtime" / "zip_agent_src"
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join((str(controller), str(zip_agent)))
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import constraintbox, constraintbox_zip_agent, constraintbox.hook_adapter, constraintbox.provider_call_receipt; print(constraintbox.__name__, constraintbox_zip_agent.__version__, constraintbox.__file__, constraintbox.hook_adapter.__file__)",
                ],
                cwd=extracted,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertIn("constraintbox 0.1.0", completed.stdout)
            self.assertIn(str(controller / "constraintbox"), completed.stdout)
            self.assertIn(str(controller / "constraintbox" / "hook_adapter.py"), completed.stdout)


if __name__ == "__main__":
    unittest.main()
