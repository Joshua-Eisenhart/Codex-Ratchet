from __future__ import annotations

import ast
import json
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKER_ROOT = ROOT / "workers" / "attractor_basin_v1"


class AttractorBasinAdapterTests(unittest.TestCase):
    def test_required_source_and_environment_declarations_are_contained(self) -> None:
        expected = {
            "README.md",
            "basin_controller.py",
            "jax_basin.py",
            "julia_basin.jl",
            "object_card.json",
            "smt_basin.py",
            "torch_basin.py",
        }
        self.assertTrue(WORKER_ROOT.is_dir())
        self.assertTrue(expected.issubset({path.name for path in WORKER_ROOT.iterdir()}))
        self.assertTrue((WORKER_ROOT / "julia_environment" / "Project.toml").is_file())
        self.assertTrue((WORKER_ROOT / "julia_environment" / "Manifest.toml").is_file())
        self.assertTrue(
            (ROOT / "requirements" / "attractor_basin_external_observed_20260801.txt").is_file()
        )
        self.assertTrue((ROOT / "docs" / "ATTRACTOR_BASIN_EXTERNAL_VALIDATION.md").is_file())

    def test_python_sources_parse_without_loading_external_engines(self) -> None:
        for name in (
            "basin_controller.py",
            "jax_basin.py",
            "smt_basin.py",
            "torch_basin.py",
        ):
            source = (WORKER_ROOT / name).read_text(encoding="utf-8")
            ast.parse(source, filename=name)

    def test_adapter_sources_have_no_builder_host_or_fixed_output_path(self) -> None:
        forbidden = (
            "/Users/",
            "/opt/homebrew",
            "Documents/Codex",
            "outputs/cb_attractor",
            "work/cb_attractor",
            "@codex-ratchet",
        )
        for path in sorted(WORKER_ROOT.rglob("*")):
            # Test source/config text only.  Python may create __pycache__
            # during the CLI checks, and the Julia environment contains a
            # binary manifest cache on some hosts; neither is adapter source.
            if (
                not path.is_file()
                or path.name == "Manifest.toml"
                or path.name == ".DS_Store"
                or path.suffix in {".pyc", ".pyo"}
            ):
                continue
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, text, f"{path} contains {value}")

    def test_object_card_and_role_boundary_are_explicit(self) -> None:
        card = json.loads((WORKER_ROOT / "object_card.json").read_text(encoding="utf-8"))
        self.assertEqual(card["schema_version"], "wizard_v4_3_primary_object_card_v1")
        controller = (WORKER_ROOT / "basin_controller.py").read_text(encoding="utf-8")
        self.assertIn("external_sim_engines_are_constraintbox_core\": False", controller)
        self.assertIn("smt_is_external_sim_engine\": False", controller)
        self.assertIn("claim_gate_sim_admission\": False", controller)
        self.assertIn("continuous_basin_proof\": False", controller)

    def test_external_versions_are_not_core_dependencies(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        core = "\n".join(project["project"]["dependencies"])
        for external in ("jax", "diffrax", "torch", "torch-geometric", "numpy", "scipy"):
            self.assertNotIn(external, core)

    def test_operation_severance_controls_are_executed_not_literal_false(self) -> None:
        jax_source = (WORKER_ROOT / "jax_basin.py").read_text(encoding="utf-8")
        controller = (WORKER_ROOT / "basin_controller.py").read_text(encoding="utf-8")
        smt_source = (WORKER_ROOT / "smt_basin.py").read_text(encoding="utf-8")
        verifier = (ROOT / "scripts" / "verify_attractor_basin_envelope.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("CB_DIFFRAX_OPERATION_SEVERED", jax_source)
        self.assertIn("expected_returncode=1", controller)
        self.assertIn('expected_terminal="BLOCKED"', controller)
        self.assertIn('flow_directory="outer_minilev_smt_severed"', controller)
        self.assertNotIn("all_pass_if_diffrax_severed", jax_source)
        self.assertNotIn("severed_gate =", controller)
        self.assertNotIn("required Z3 4.16", smt_source)
        self.assertNotIn("required CVC5 1.3.3", smt_source)
        self.assertIn("normalize_jax", verifier)
        self.assertIn("normalize_julia", verifier)
        self.assertIn("normalize_torch", verifier)
        self.assertIn("normalize_smt", verifier)


if __name__ == "__main__":
    unittest.main()
