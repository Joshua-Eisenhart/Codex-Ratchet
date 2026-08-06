import json
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from holodeck_world.doctor import report


class HolodeckBoundaryTests(unittest.TestCase):
    def test_default_install_has_no_heavy_dependency(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        self.assertEqual(project["dependencies"], [])
        self.assertIn("torch==2.11.0", project["optional-dependencies"]["world-model"])

    def test_qit_engine_remains_an_external_blocked_bridge(self):
        boundary = json.loads((ROOT / "PRODUCT_BOUNDARY.v9.json").read_text(encoding="utf-8"))
        self.assertIn("qit_engine_implementation", boundary["does_not_own"])
        self.assertEqual(boundary["qit_bridge_state"], "blocked_pending_independent_qit_engine_reality_gate")

    def test_source_index_is_resolved_without_claiming_integration(self):
        body = report()
        self.assertTrue(all(row["exists"] for row in body["candidate_sources"]))
        self.assertEqual(body["claim_ceiling"], "product_scaffold_and_live_tool_visibility_only")


if __name__ == "__main__":
    unittest.main()
