import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load_module("sim_registry_builder", ROOT / "sim_engines" / "registry" / "build_registry.py")
installer = load_module("sim_installer", ROOT / "sim_engines" / "install.py")
doctor = load_module("sim_doctor", ROOT / "sim_engines" / "doctor.py")


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = builder.build()

    def test_tool_ids_are_unique_and_levels_are_declared(self):
        rows = self.registry["tools"]
        ids = [row["id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))
        levels = set(json.loads((ROOT / "sim_engines" / "registry" / "integration-levels.v1.json").read_text())["ordered_levels"])
        self.assertTrue(all(row["declared_integration_level"] in levels for row in rows))

    def test_all_named_source_and_evidence_paths_exist(self):
        for row in self.registry["tools"]:
            for relative in row["source_paths"] + row["evidence_paths"]:
                with self.subTest(tool=row["id"], path=relative):
                    self.assertTrue((ROOT / relative).exists())

    def test_cb_mirror_is_exactly_five_and_excludes_heavy_runtimes(self):
        profiles = installer.load_profiles()
        packages = {row["distribution"] for row in profiles["cb-mirror"]["packages"]}
        self.assertEqual(packages, {"z3-solver", "cvc5", "sympy", "rustworkx", "maude"})
        self.assertFalse(packages & {"jax", "torch", "pysindy", "pykoopman"})

    def test_java_temporal_tools_are_quarantined_external_sim_tools(self):
        rows = {row["id"]: row for row in self.registry["tools"]}
        for tool_id in ("external.java", "external.tlc", "external.apalache"):
            self.assertEqual(rows[tool_id]["declared_integration_level"], "quarantined")
            self.assertIn("temporal-formal", rows[tool_id]["install_profiles"])

    def test_install_plan_deduplicates_overlapping_profiles(self):
        planned = installer.plan(["python-base", "jax", "qit-python"])
        self.assertEqual(len(planned), len(set(planned)))
        self.assertIn("numpy==2.3.4", planned)
        self.assertIn("jax==0.10.1", planned)

    def test_holodeck_profile_resolves_base_and_torch_dependencies(self):
        planned = installer.plan(["holodeck-world-model"])
        self.assertIn("numpy==2.3.4", planned)
        self.assertIn("torch==2.11.0", planned)
        self.assertIn("lightning==2.6.5", planned)

    def test_live_doctor_preserves_declared_level_as_separate_field(self):
        report = doctor.observe(include_julia=False)
        self.assertEqual(len(report["registered_tools"]), len(self.registry["tools"]))
        self.assertTrue(all("live_install_state" in row and "declared_integration_level" in row for row in report["registered_tools"]))
        self.assertEqual(report["claim_ceiling"], "installation_and_declared_source_integration_index_only")


if __name__ == "__main__":
    unittest.main()
