from __future__ import annotations

import hashlib
import json
import os
import re
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
_HOST_PATH = re.compile(rb"/(?:Users|home)/[A-Za-z0-9_.-]+/")
_HOST_RELATIVE_PATH = re.compile(rb"(?<![A-Za-z0-9_.-])~/[^\s\"'`]+")

# Portability applies to executable and configuration payloads.  The
# append-only context corpus and MMM material are deliberately absent from
# this list: host paths in historical prose are not runtime dependencies.
_EXECUTION_CONFIG_PREFIXES = (
    f"{TOP_LEVEL}/PROJECT/.claude/",
    f"{TOP_LEVEL}/PROJECT/bin/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/config/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/requirements/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/light_runtime/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/zip_agent/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/hooks/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/bin/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/config/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/hooks/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/bin/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/scripts/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime_profiles/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime/controller_src/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime/zip_agent_src/",
)
_CONFIG_DATA_PREFIXES = (
    f"{TOP_LEVEL}/PROJECT/.claude/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/config/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/requirements/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/config/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/hooks/",
    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime_profiles/",
)
_CONFIG_DATA_SUFFIXES = (
    ".cfg",
    ".in",
    ".ini",
    ".json",
    ".jsonl",
    ".lock",
    ".toml",
    ".yaml",
    ".yml",
)


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
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/state/CURRENT_EPOCH.json",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/state/epochs/epoch-00000001.json",
                    names,
                )
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
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime_profiles/jax_qit/requirements.lock",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime_profiles/jax_qit/README.md",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/bin/cb",
                    names,
                )
                self.assertIn(
                    b"~/.local/share",
                    archive.read(
                        f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/runtime_profiles/jax_qit/README.md"
                    ),
                )
                self.assertIn(
                    b'startswith("~/")',
                    archive.read(f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/bin/cb"),
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/experiments/manifold_capability/v1/campaign.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/context/full/prompt_plan_progress_corpus.jsonl",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/hooks/cb_hook.sh",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/light_runtime/src/constraintbox/core_cli.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/zip_agent/src/constraintbox_zip_agent/runtime.py",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/skills/ACTIVE_WAVES.json",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/mmms/primary/mini/MEMBER_MINI_MMM_REGISTRY_v4_3.md",
                    names,
                )
                load_bearing = (
                    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/contained_light/00_READ_THIS_FIRST.md",
                    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/contained_light/build.sh",
                    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/contained_light/seed-check",
                    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/contained_light/bin/cb",
                    f"{TOP_LEVEL}/PROJECT/constraint_box/scripts/exercise_cb_light_hook_boundaries.py",
                )
                for member in load_bearing:
                    self.assertIn(member, names)
                    self.assertIsNone(_HOST_PATH.search(archive.read(member)), member)
                self.assertNotIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/config/sim_estate_v2.json",
                    names,
                )
                self.assertNotIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/config/council_member_registry_v1.json",
                    names,
                )
                self.assertNotIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/requirements/locks/constraintbox-py313-macos-full.lock",
                    names,
                )
                self.assertNotIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/requirements/locks/constraintbox-py313-macos-gates.lock",
                    names,
                )
                self.assertIn(
                    f"{TOP_LEVEL}/PROJECT/constraint_box/integrated_system/scripts/run_wave.py",
                    names,
                )
                self.assertFalse(
                    [name for name in names if "/integrated_system/runs/" in name]
                )
                self.assertFalse(
                    [
                        name
                        for name in names
                        if "/integrated_system/state/receipts/" in name
                        and not name.endswith("/RETENTION_MANIFEST.json")
                    ]
                )
                self.assertTrue(
                    any(
                        name.endswith("/integrated_system/state/receipts/boot-20260817-light-summary/RETENTION_MANIFEST.json")
                        for name in names
                    )
                )
                self.assertFalse(
                    [name for name in names if "/integrated_system/state/campaigns/" in name]
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
                    "/.venv/",
                    "/venv/",
                    "/cache/",
                    ".sqlite",
                    ".pyc",
                    "/campaigns/",
                    "autoresearch",
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
                closure = hashlib.sha256(
                    json.dumps(
                        [
                            {
                                "path": row["path"],
                                "bytes": row["bytes"],
                                "sha256": row["sha256"],
                                "mode": row["mode"],
                            }
                            for row in manifest["files"]
                        ],
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                self.assertEqual(manifest["source_closure_sha256"], closure)
                self.assertEqual(metadata["source_closure_sha256"], closure)
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

                execution_config = [
                    name
                    for name in names
                    if name.startswith(_EXECUTION_CONFIG_PREFIXES)
                ]
                self.assertTrue(execution_config)
                original_root = str(BOX.resolve()).encode()
                for name in execution_config:
                    body = archive.read(name)
                    self.assertNotIn(original_root, body, name)
                    self.assertIsNone(_HOST_PATH.search(body), name)
                config_data = [
                    name
                    for name in names
                    if name.startswith(_CONFIG_DATA_PREFIXES)
                    and any(name.endswith(suffix) for suffix in _CONFIG_DATA_SUFFIXES)
                ]
                for name in config_data:
                    self.assertIsNone(_HOST_RELATIVE_PATH.search(archive.read(name)), name)

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

            # The selected Mini-Lev path-mass operation must also run from a
            # fresh extract and replay its receipt without the source checkout
            # on PYTHONPATH.
            wrapper = package_root / "integrated_system" / "scripts" / "run_constraint_path_mass.py"
            controller = package_root / "integrated_system" / "runtime" / "controller_src" / "constraintbox"
            self.assertFalse((controller / "proposal_minilev_flow.py").exists())
            self.assertFalse((controller / "mini_levos.py").exists())
            output = Path(directory) / "path-mass-result.json"
            fresh_env = dict(os.environ)
            fresh_env["PYTHONPATH"] = os.pathsep.join((str(controller), str(zip_agent)))
            run = subprocess.run(
                [sys.executable, str(wrapper), "--out", str(output)],
                cwd=extracted,
                env=fresh_env,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(run.returncode, 0, run.stderr or run.stdout)
            summary = json.loads(run.stdout)
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["n_paths"], 14)
            replay = subprocess.run(
                [sys.executable, str(wrapper), "--replay", str(output)],
                cwd=extracted,
                env=fresh_env,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(replay.returncode, 0, replay.stderr or replay.stdout)
            replay_summary = json.loads(replay.stdout)
            self.assertEqual(replay_summary["status"], "PASS")
            self.assertEqual(
                replay_summary["stored_receipt_sha256"],
                replay_summary["replayed_receipt_sha256"],
            )

    def test_direct_verifier_on_clean_extract_has_no_physical_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cb-integrated-direct-verify-") as directory:
            root = Path(directory)
            bundle = root / "system.zip"
            self._build(bundle)
            extracted = root / "extract"
            extracted.mkdir()
            with zipfile.ZipFile(bundle) as archive:
                archive.extractall(extracted)
            package_root = extracted / TOP_LEVEL / "PROJECT" / "constraint_box"
            verifier = package_root / "integrated_system" / "scripts" / "verify_integrated_system.py"
            before = {
                path.relative_to(extracted).as_posix()
                for path in extracted.rglob("*")
                if path.is_file() or path.is_symlink()
            }
            environment = dict(os.environ)
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(verifier),
                    "--box-root",
                    str(package_root),
                    "--light-python",
                    str(package_root / "missing-python"),
                    "--skip-tests",
                ],
                cwd=extracted,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            after = {
                path.relative_to(extracted).as_posix()
                for path in extracted.rglob("*")
                if path.is_file() or path.is_symlink()
            }
            self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
            self.assertEqual(before, after)
            self.assertFalse([path for path in after if "__pycache__" in path])


if __name__ == "__main__":
    unittest.main()
