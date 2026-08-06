import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "mmm" / "load.py"
SPEC = importlib.util.spec_from_file_location("constraint_box_mmm_load", LOADER)
MMM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MMM)


class TestMmm(unittest.TestCase):
    def run_loader(self, *args):
        return subprocess.run(
            [sys.executable, str(LOADER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_every_discovered_pack_loads_nonempty(self):
        for name in MMM.discover_packs():
            with self.subTest(pack=name):
                self.assertTrue(MMM.load_pack(name).strip())

    def test_expected_packs_are_present(self):
        expected = {
            "claimgate",
            "cr-ratchet",
            "lev-os",
            "constraint-programming",
            "smt",
            "nominalist",
        }
        self.assertTrue(expected.issubset(set(MMM.discover_packs())))

    def test_unknown_pack_cli_errors(self):
        result = self.run_loader("nosuchpack")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nosuchpack", result.stderr)
        for name in MMM.discover_packs():
            self.assertIn(name, result.stderr)
        self.assertEqual(result.stdout, "")

        json_result = self.run_loader("nosuchpack", "--json")
        self.assertNotEqual(json_result.returncode, 0)
        self.assertIn("nosuchpack", json_result.stderr)
        self.assertEqual(json_result.stdout, "")

    def test_composition_is_deterministic_and_order_stable(self):
        args = ("claimgate", "smt", "nominalist")
        first = self.run_loader(*args)
        second = self.run_loader(*args)
        reordered = self.run_loader("nominalist", "smt", "claimgate")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout.encode(), second.stdout.encode())
        self.assertNotEqual(first.stdout.encode(), reordered.stdout.encode())

    def test_json_round_trip_preserves_order(self):
        names = ["claimgate", "smt", "claimgate"]
        result = self.run_loader(*names, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["packs"], names)
        self.assertEqual(len(payload["texts"]), len(names))

    def test_every_pack_keeps_required_shape(self):
        headings = (
            "**Epistemology.",
            "**Ontology (the nouns of this world).**",
            "**In-voice vocabulary (use these phrases).**",
        )
        for name in MMM.discover_packs():
            text = MMM.load_pack(name)
            with self.subTest(pack=name):
                for heading in headings:
                    self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
