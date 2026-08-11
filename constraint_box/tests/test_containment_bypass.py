"""Bypass tests: verify ConstraintBox containment is breach-safe.

These tests simulate external modules attempting to import ConstraintBox directly.
If any fail, the boundary has leaked into API surface."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContainmentBypassTests(unittest.TestCase):
    """Verify that ConstraintBox containment is breach-safe."""

    def test_sim_engines_cannot_directly_import_constraintbox(self):
        """sim_engines/—an independent product—cannot import CB directly.
        If this fails, CB implementation leaked into the API surface."""
        code = "from constraintbox import core_tools; print('LEAKED')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(ROOT.parents[0] / "sim_engines"),
        )
        self.assertNotEqual(
            result.returncode, 0,
            f"Sim engines can import CB—boundary leaked. Output: {result.stderr}"
        )

    def test_holodeck_cannot_directly_import_constraintbox(self):
        """holodeck/—a peer product—cannot import CB directly."""
        code = "from constraintbox import core_tools; print('LEAKED')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(ROOT.parents[0] / "holodeck"),
        )
        self.assertNotEqual(
            result.returncode, 0,
            f"Holodeck can import CB—boundary leaked. Output: {result.stderr}"
        )

    def test_ratchet_engine_cannot_directly_import_constraintbox(self):
        """ratchet_engine/ (codex-ratchet implementation) cannot import CB directly."""
        code = "from constraintbox import core_tools; print('LEAKED')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(ROOT.parents[0] / "ratchet_engine"),
        )
        self.assertNotEqual(
            result.returncode, 0,
            f"Ratchet engine can import CB—boundary leaked. Output: {result.stderr}"
        )

    def test_external_packet_bridge_is_cb_internal(self):
        """The external_engine_packet adapter is CB-internal."""
        path = ROOT / "src" / "constraintbox" / "external_engine_packet.py"
        self.assertTrue(path.exists(), f"Expected {path} to exist")
        source = path.read_text(encoding="utf-8")
        self.assertIn("def", source, "external_engine_packet.py has callables")

    def test_cr_adapter_is_cb_internal(self):
        """The CR bridge adapter is CB-internal."""
        path = ROOT / "src" / "constraintbox" / "adapters" / "cr.py"
        self.assertTrue(path.exists(), f"Expected {path} to exist")
        source = path.read_text(encoding="utf-8")
        self.assertIn("def", source, "adapters/cr.py has callables")

    def test_no_bridge_exposes_cb_internals(self):
        """Bridge schemas should not reference CB implementation modules."""
        registry_path = ROOT.parents[0] / "system_v9" / "bridges" / "registry.v9.json"
        with open(registry_path) as f:
            registry = json.load(f)

        for bridge in registry["bridges"]:
            request_schema = bridge.get("request_schema", "")
            result_schema = bridge.get("result_schema", "")

            for schema_path_str in [request_schema, result_schema]:
                if not schema_path_str:
                    continue
                schema_path = ROOT.parents[0] / schema_path_str
                if not schema_path.exists():
                    continue

                with open(schema_path) as f:
                    schema_source = json.dumps(json.load(f))

                forbidden = ["constraintbox.core_", "constraintbox.src.", "constraintbox._"]
                for pattern in forbidden:
                    self.assertNotIn(
                        pattern,
                        schema_source,
                        f"{bridge['id']} schema {schema_path_str} leaks CB internals: {pattern}"
                    )


if __name__ == "__main__":
    unittest.main()
