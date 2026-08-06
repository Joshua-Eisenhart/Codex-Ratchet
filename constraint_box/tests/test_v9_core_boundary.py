import json
import tomllib
import unittest
from pathlib import Path

from constraintbox import core_tools


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"z3-solver", "cvc5", "sympy", "rustworkx", "maude"}
FORBIDDEN = {"jax", "torch", "pysindy", "pykoopman", "julia", "tlc", "apalache", "java"}


class V9CoreBoundaryTests(unittest.TestCase):
    def test_runtime_dependencies_are_exactly_the_five_core_tools(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        names = {entry.split("<", 1)[0].split(">", 1)[0].split("=", 1)[0].strip().lower() for entry in project["dependencies"]}
        self.assertEqual(names, EXPECTED)

    def test_registry_is_the_same_exact_five_tool_set(self):
        registry = core_tools.load_registry()
        ids = {row["id"].split(".", 1)[1] for row in registry["tools"]}
        self.assertEqual(ids, {"z3", "cvc5", "sympy", "rustworkx", "maude"})

    def test_default_entrypoint_is_lean_and_legacy_entrypoint_is_named(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        self.assertEqual(project["scripts"]["constraintbox"], "constraintbox.core_cli:main")
        self.assertEqual(project["scripts"]["constraintbox-legacy"], "constraintbox.cli:main")

    def test_core_modules_do_not_name_forbidden_runtimes(self):
        text = "\n".join((ROOT / "src" / "constraintbox" / name).read_text(encoding="utf-8").lower() for name in ("core_tools.py", "core_cli.py"))
        for forbidden in FORBIDDEN:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(f"import {forbidden}", text)

    def test_doctor_reports_five_rows(self):
        report = core_tools.doctor()
        self.assertEqual(len(report["rows"]), 5)
        self.assertEqual(set(report["core_tool_ids"]), set(core_tools.CORE_TOOL_IDS))

    def test_product_boundary_explicitly_records_legacy_debt(self):
        body = json.loads((ROOT / "PRODUCT_BOUNDARY.v9.json").read_text(encoding="utf-8"))
        self.assertEqual(set(body["core_third_party_tools"]), {"z3", "cvc5", "sympy", "rustworkx", "maude"})
        self.assertIn("formalcheck_temporal_pair", body["legacy_bridge_debt"])
        self.assertFalse(body["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
