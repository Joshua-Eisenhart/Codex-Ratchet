from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_control_plane_profile.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_control_plane_profile_under_test", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


class ControlPlaneFreshWheelProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = load_verifier()

    def _positive_attestation(self) -> bytes:
        return json.dumps(
            {
                "schema": "constraintbox.control-plane-profile-attestation.v1",
                "direct_pins": {"pydantic": "2.12.5", "jsonschema": "4.26.0"},
                "observed_direct_versions": {
                    "pydantic": "2.12.5",
                    "jsonschema": "4.26.0",
                },
                "direct_metadata_matches": True,
                "direct_pin_versions_match": True,
                "origin_checks": {
                    "all_profile_imports_inside_fresh_environment": True,
                    "no_source_tree_origin": True,
                    "pin_file_inside_fresh_environment": True,
                },
                "profile_ready": True,
            }
        ).encode("utf-8")

    def _refusal(self, reason_code: str) -> bytes:
        return json.dumps(
            {
                "schema": "constraintbox.control-plane-candidate-evaluation.v1",
                "disposition": "REFUSE",
                "reason_code": reason_code,
                "promotion_allowed": False,
            }
        ).encode("utf-8")

    def test_install_requests_the_control_plane_extra_without_no_deps(self) -> None:
        wheel = Path("/tmp/constraintbox-0.4.0.dev1-py3-none-any.whl")
        argv = self.verifier.install_argv(
            Path("/tmp/fresh/python"),
            wheel,
            wheelhouse=None,
            offline=False,
        )

        self.assertIn("install", argv)
        self.assertNotIn("--no-deps", argv)
        self.assertNotIn("--no-index", argv)
        self.assertEqual(
            argv[-1],
            "constraintbox[control-plane] @ file:///tmp/constraintbox-0.4.0.dev1-py3-none-any.whl",
        )

    def test_offline_mode_requires_an_explicit_wheelhouse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"not-a-real-wheel")
            with self.assertRaisesRegex(
                self.verifier.VerificationError,
                "requires an explicit --wheelhouse",
            ):
                self.verifier.verify_control_plane_profile(wheel, offline=True)

    def test_child_environment_scrubs_python_and_pip_configuration_inputs(self) -> None:
        inherited = {
            "PYTHONPATH": "/untrusted/source",
            "PYTHONHOME": "/untrusted/python-home",
            "VIRTUAL_ENV": "/untrusted/venv",
            "PIP_CONFIG_FILE": "/untrusted/pip.conf",
        }
        with mock.patch.dict("os.environ", inherited, clear=True):
            environment = self.verifier._fresh_environment()

        for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            self.assertNotIn(name, environment)
        self.assertEqual(environment["PYTHONNOUSERSITE"], "1")
        self.assertEqual(environment["PIP_NO_INPUT"], "1")
        self.assertEqual(environment["PIP_DISABLE_PIP_VERSION_CHECK"], "1")
        self.assertEqual(environment["PIP_CONFIG_FILE"], self.verifier.os.devnull)

    def test_mocked_clean_profile_receipt_requires_direct_pins_and_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel bytes")
            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            fake_python = root / "fresh-python"
            fake_python.touch()
            commands: list[tuple[str, ...]] = []

            def fake_invoke(argv, *, timeout, env):
                command = tuple(str(part) for part in argv)
                commands.append(command)
                if "venv" in command:
                    return self.verifier.Invocation(command, 0, b"", b"")
                if "pip" in command and "install" in command:
                    return self.verifier.Invocation(command, 0, b"", b"")
                if "pip" in command and "check" in command:
                    return self.verifier.Invocation(command, 0, b"", b"")
                if "constraintbox.core_cli" in command:
                    request = next(
                        value
                        for value in command
                        if value.endswith(".json") and "refusal" in value
                        or value.endswith("candidate-pin-severance.json")
                    )
                    if request.endswith("extra-field-refusal.json"):
                        body = self._refusal("REFUSE_UNEXPECTED_FIELD")
                    elif request.endswith("undeclared-capability-refusal.json"):
                        body = self._refusal("REFUSE_UNDECLARED_CAPABILITY")
                    else:
                        body = self._refusal("REFUSE_CANDIDATE_PIN_DIGEST_MISMATCH")
                    return self.verifier.Invocation(command, 2, body, b"")
                return self.verifier.Invocation(
                    command, 0, self._positive_attestation(), b""
                )

            with (
                mock.patch.object(self.verifier, "invoke", fake_invoke),
                mock.patch.object(self.verifier, "_venv_python", return_value=fake_python),
            ):
                receipt = self.verifier.verify_control_plane_profile(
                    wheel,
                    offline=True,
                    wheelhouse=wheelhouse,
                )

        self.assertEqual(receipt["state"], "READY")
        self.assertEqual(receipt["verification_scope"], "control_plane_fresh_wheel_profile")
        self.assertTrue(receipt["local_host_only"])
        self.assertTrue(receipt["direct_pins_only"])
        self.assertFalse(receipt["full_transitive_hash_lock_verified"])
        self.assertFalse(receipt["cross_platform_matrix_proved"])
        self.assertIn("Local-only fresh-wheel", receipt["claim_ceiling"])
        checks = {check["name"]: check for check in receipt["checks"]}
        self.assertTrue(checks["installed_profile_direct_pin_attestation"]["passed"])
        self.assertEqual(
            checks["installed_profile_direct_pin_attestation"]["attestation"][
                "direct_pins"
            ],
            {"pydantic": "2.12.5", "jsonschema": "4.26.0"},
        )
        self.assertTrue(checks["installed_refusals_do_not_open_sqlite"]["passed"])
        install = next(command for command in commands if "install" in command)
        self.assertIn("--no-index", install)
        self.assertIn("constraintbox[control-plane] @ file://", install[-1])
        self.assertNotIn("--no-deps", install)
        # Every child, including venv bootstrap, is isolated from the source cwd.
        self.assertTrue(all("-I" in command for command in commands))

    def test_origin_or_pin_attestation_failure_blocks_installed_cli_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel bytes")
            fake_python = root / "fresh-python"
            fake_python.touch()
            calls: list[tuple[str, ...]] = []
            bad_attestation = json.loads(self._positive_attestation())
            bad_attestation["origin_checks"]["no_source_tree_origin"] = False
            bad_attestation["profile_ready"] = False

            def fake_invoke(argv, *, timeout, env):
                command = tuple(str(part) for part in argv)
                calls.append(command)
                if "venv" in command or "pip" in command:
                    return self.verifier.Invocation(command, 0, b"", b"")
                return self.verifier.Invocation(
                    command, 0, json.dumps(bad_attestation).encode("utf-8"), b""
                )

            with (
                mock.patch.object(self.verifier, "invoke", fake_invoke),
                mock.patch.object(self.verifier, "_venv_python", return_value=fake_python),
            ):
                receipt = self.verifier.verify_control_plane_profile(wheel)

        self.assertEqual(receipt["state"], "FAILED")
        self.assertEqual(receipt["reason"], "direct_pin_or_origin_attestation_failed")
        checks = {check["name"]: check for check in receipt["checks"]}
        self.assertFalse(checks["installed_profile_direct_pin_attestation"]["passed"])
        self.assertEqual(
            checks["installed_undeclared_capability_refusal"]["state"], "SKIPPED"
        )
        self.assertFalse(any("constraintbox.core_cli" in command for command in calls))

    def test_failed_install_skips_profile_and_refusal_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel bytes")
            fake_python = root / "fresh-python"
            fake_python.touch()
            commands: list[tuple[str, ...]] = []

            def fake_invoke(argv, *, timeout, env):
                command = tuple(str(part) for part in argv)
                commands.append(command)
                if "venv" in command:
                    return self.verifier.Invocation(command, 0, b"", b"")
                return self.verifier.Invocation(command, 1, b"", b"resolver failed")

            with (
                mock.patch.object(self.verifier, "invoke", fake_invoke),
                mock.patch.object(self.verifier, "_venv_python", return_value=fake_python),
            ):
                receipt = self.verifier.verify_control_plane_profile(wheel)

        self.assertEqual(receipt["state"], "FAILED")
        self.assertEqual(
            receipt["reason"], "dependency_resolution_or_wheel_install_failed"
        )
        checks = {check["name"]: check for check in receipt["checks"]}
        self.assertEqual(
            checks["installed_profile_direct_pin_attestation"]["state"], "SKIPPED"
        )
        self.assertEqual(
            checks["installed_candidate_pin_severance"]["state"], "SKIPPED"
        )
        self.assertFalse(any("constraintbox.core_cli" in command for command in commands))


if __name__ == "__main__":
    unittest.main()
