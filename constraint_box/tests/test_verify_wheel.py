from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_wheel.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_wheel_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


class WheelVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = load_verifier()

    def test_default_install_uses_dependency_resolution(self) -> None:
        argv = self.verifier.install_argv(
            Path("/tmp/fresh/python"),
            Path("/tmp/constraintbox.whl"),
            wheelhouse=None,
            offline=False,
        )
        self.assertIn("install", argv)
        self.assertNotIn("--no-deps", argv)
        self.assertNotIn("--no-index", argv)
        self.assertEqual(argv[-1], "/tmp/constraintbox.whl")

    def test_offline_resolution_requires_a_wheelhouse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "constraintbox-0.3.4-py3-none-any.whl"
            wheel.write_bytes(b"not-a-real-wheel")
            with self.assertRaisesRegex(
                self.verifier.VerificationError,
                "requires an explicit --wheelhouse",
            ):
                self.verifier.verify_wheel(wheel, offline=True)

    def test_bootstrap_diagnostic_is_host_independent(self) -> None:
        invocation = self.verifier.Invocation(
            ("python", "-m", "venv", "temporary"),
            1,
            b"",
            b"error: externally-managed-environment",
        )
        self.assertEqual(
            self.verifier._failure_reason(invocation),
            "externally_managed_python_prevents_venv_bootstrap",
        )

    def test_lookup_accepts_dotted_tool_ids_and_nested_fields(self) -> None:
        body = {
            "observations": {
                "python.z3": {"status": "sat"},
                "python.maude": {"module_loaded": True},
            }
        }
        self.assertEqual(
            self.verifier._lookup(body, "observations.python.z3.status"), "sat"
        )
        self.assertIs(
            self.verifier._lookup(body, "observations.python.maude.module_loaded"),
            True,
        )

    def test_dependency_install_failure_skips_core_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "constraintbox-0.3.4-py3-none-any.whl"
            wheel.write_bytes(b"not-a-real-wheel")
            fake_python = Path(directory) / "python"
            fake_python.touch()
            calls: list[tuple[str, ...]] = []

            def fake_invoke(argv, *, timeout, env):
                command = tuple(str(part) for part in argv)
                calls.append(command)
                if "venv" in command:
                    return self.verifier.Invocation(command, 0, b"", b"")
                return self.verifier.Invocation(command, 1, b"", b"resolver failed")

            with (
                mock.patch.object(self.verifier, "invoke", fake_invoke),
                mock.patch.object(self.verifier, "_venv_python", return_value=fake_python),
            ):
                receipt = self.verifier.verify_wheel(wheel)

        self.assertEqual(receipt["state"], "FAILED")
        self.assertEqual(receipt["verification_scope"], "lean_core_install_smoke")
        self.assertFalse(receipt["full_constraintbox_product_verified"])
        self.assertEqual(
            receipt["reason"],
            "dependency_resolution_or_wheel_install_failed",
        )
        checks = {check["name"]: check for check in receipt["checks"]}
        self.assertFalse(checks["dependency_resolved_install"]["passed"])
        self.assertEqual(checks["v9_console_doctor"]["state"], "SKIPPED")
        install = next(command for command in calls if "pip" in command)
        self.assertNotIn("--no-deps", install)

    def test_ambiguous_wheel_selection_requires_an_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dist = root / "dist"
            dist.mkdir()
            (dist / "constraintbox-0.3.2-py3-none-any.whl").touch()
            (dist / "constraintbox-0.3.4-py3-none-any.whl").touch()
            with mock.patch.object(self.verifier, "ROOT", root):
                with self.assertRaisesRegex(
                    self.verifier.VerificationError,
                    "selection is ambiguous",
                ):
                    self.verifier.discover_wheel(None)


if __name__ == "__main__":
    unittest.main()
