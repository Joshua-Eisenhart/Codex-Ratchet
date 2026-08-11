from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install_control_plane_profile.py"


def load_installer():
    spec = importlib.util.spec_from_file_location(
        "install_control_plane_profile_under_test", SCRIPT
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


class ControlPlaneProfileInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.installer = load_installer()

    @staticmethod
    def _pins(path: Path) -> Path:
        pin_file = path / "pins.txt"
        pin_file.write_text(
            "pydantic==2.12.5\njsonschema==4.26.0\nhypothesis==6.151.12\n",
            encoding="utf-8",
        )
        return pin_file

    @staticmethod
    def _attestation() -> bytes:
        return json.dumps(
            {
                "schema": "constraintbox.control-plane-profile-install-attestation.v1",
                "profile_ready": True,
                "direct_pin_versions_match": True,
                "packaged_profile_pins_match": True,
                "test_only_candidates": {
                    "declared": True,
                    "not_installed": True,
                },
                "wheel_metadata_direct_pins_match": True,
                "origin_checks": {
                    "all_imports_inside_explicit_profile": True,
                    "no_source_package_origin": True,
                    "pin_file_inside_explicit_profile": True,
                },
            }
        ).encode("utf-8")

    def test_canonical_three_pin_shape_keeps_hypothesis_test_only(self) -> None:
        candidates = self.installer.read_control_plane_candidate_pins(
            self.installer.DEFAULT_PINS
        )
        self.assertEqual(
            candidates,
            {
                "pydantic": "2.12.5",
                "jsonschema": "4.26.0",
                "hypothesis": "6.151.12",
            },
        )
        self.assertEqual(
            self.installer.read_direct_pins(self.installer.DEFAULT_PINS),
            {"pydantic": "2.12.5", "jsonschema": "4.26.0"},
        )
        self.assertEqual(
            self.installer.read_test_only_candidate_pins(self.installer.DEFAULT_PINS),
            {"hypothesis": "6.151.12"},
        )

    def test_attestation_program_normalizes_parenthesized_optional_metadata(self) -> None:
        requirement = 'pydantic == 2.12.5 ; (extra == "control-plane")'
        normalized = (
            requirement.replace(" ", "")
            .replace("(", "")
            .replace(")", "")
            .casefold()
        )
        self.assertEqual(normalized, 'pydantic==2.12.5;extra=="control-plane"')
        self.assertIn('replace("(", "").replace(")", "")', self.installer._ATTESTATION_PROGRAM)

    def test_default_offline_mode_requires_wheelhouse_before_any_child_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel")
            with self.assertRaisesRegex(
                self.installer.InstallError, "requires --wheelhouse"
            ):
                self.installer.install_control_plane_profile(
                    wheel,
                    root / "profile",
                    pins=self._pins(root),
                )

    def test_exact_91_runtime_target_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel")
            with self.assertRaisesRegex(
                self.installer.InstallError, "exact 91-tool CB Light runtime"
            ):
                self.installer.install_control_plane_profile(
                    wheel,
                    self.installer.ROOT / ".venv",
                    pins=self._pins(root),
                    wheelhouse=root,
                )

    def test_child_environment_scrubs_python_and_all_pip_injection_inputs(self) -> None:
        inherited = {
            "PYTHONPATH": "/untrusted/source",
            "PYTHONHOME": "/untrusted/python-home",
            "PYTHONUSERBASE": "/untrusted/user-base",
            "VIRTUAL_ENV": "/untrusted/venv",
            "PIP_CONFIG_FILE": "/untrusted/pip.conf",
            "PIP_TARGET": "/untrusted/target",
            "PIP_EXTRA_INDEX_URL": "https://untrusted.invalid/simple",
        }
        with mock.patch.dict("os.environ", inherited, clear=True):
            environment = self.installer.scrubbed_environment()

        for name in (
            "PYTHONPATH",
            "PYTHONHOME",
            "PYTHONUSERBASE",
            "VIRTUAL_ENV",
            "PIP_TARGET",
            "PIP_EXTRA_INDEX_URL",
        ):
            self.assertNotIn(name, environment)
        self.assertEqual(environment["PYTHONNOUSERSITE"], "1")
        self.assertEqual(environment["PIP_NO_INPUT"], "1")
        self.assertEqual(environment["PIP_DISABLE_PIP_VERSION_CHECK"], "1")
        self.assertEqual(environment["PIP_CONFIG_FILE"], self.installer.os.devnull)

    def test_mocked_offline_install_uses_direct_pins_and_isolated_children(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel")
            pins = self._pins(root)
            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            profile = root / "control-plane"
            fake_python = root / "profile-python"
            fake_python.touch()
            commands: list[tuple[str, ...]] = []

            def fake_invoke(argv, *, timeout, env):
                command = tuple(str(part) for part in argv)
                commands.append(command)
                if "venv" in command or ("pip" in command and "install" in command):
                    return self.installer.Invocation(command, 0, b"", b"")
                if "pip" in command and "check" in command:
                    return self.installer.Invocation(command, 0, b"", b"")
                if "constraintbox" in command:
                    return self.installer.Invocation(command, 0, b"usage: constraintbox {wave}\n", b"")
                return self.installer.Invocation(command, 0, self._attestation(), b"")

            with (
                mock.patch.object(self.installer, "invoke", fake_invoke),
                mock.patch.object(
                    self.installer, "profile_python", return_value=fake_python
                ),
            ):
                receipt = self.installer.install_control_plane_profile(
                    wheel,
                    profile,
                    pins=pins,
                    wheelhouse=wheelhouse,
                )

        self.assertEqual(receipt["state"], "READY")
        self.assertEqual(
            receipt["installer_scope"], "explicit_separate_control_plane_wave_profile"
        )
        self.assertEqual(
            receipt["direct_profile_pins"],
            {"pydantic": "2.12.5", "jsonschema": "4.26.0"},
        )
        self.assertEqual(
            receipt["test_only_candidate_pins_not_installed"],
            {"hypothesis": "6.151.12"},
        )
        self.assertFalse(receipt["exact_91_runtime_mutated"])
        self.assertTrue(receipt["local_host_only"])
        self.assertFalse(receipt["cross_platform_matrix_proved"])
        checks = {check["name"]: check for check in receipt["checks"]}
        self.assertTrue(checks["installed_profile_attestation"]["passed"])
        self.assertTrue(checks["installed_wave_command_available"]["passed"])
        self.assertTrue(all("-I" in command for command in commands))
        installs = [command for command in commands if "install" in command]
        self.assertEqual(len(installs), 2)
        self.assertTrue(all("--no-index" in command for command in installs))
        self.assertTrue(all("--find-links" in command for command in installs))
        direct_install = next(
            command for command in installs if "pydantic==2.12.5" in command
        )
        self.assertIn("jsonschema==4.26.0", direct_install)
        self.assertNotIn("hypothesis==6.151.12", direct_install)
        self.assertNotIn("--no-deps", direct_install)
        base_install = next(
            command for command in installs if str(wheel.resolve()) in command
        )
        self.assertEqual(
            base_install[:5],
            (str(fake_python), "-I", "-m", "pip", "install"),
        )
        self.assertEqual(base_install.count("-m"), 1)
        self.assertNotIn("pydantic==2.12.5", base_install)
        wave_help = next(command for command in commands if "constraintbox" in command)
        self.assertEqual(
            wave_help,
            (str(fake_python), "-I", "-m", "constraintbox", "--help"),
        )

    def test_direct_pin_failure_stops_attestation_and_wave_availability_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel")
            pins = self._pins(root)
            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            profile = root / "control-plane"
            fake_python = root / "profile-python"
            fake_python.touch()
            commands: list[tuple[str, ...]] = []

            def fake_invoke(argv, *, timeout, env):
                command = tuple(str(part) for part in argv)
                commands.append(command)
                if "pydantic==2.12.5" in command:
                    return self.installer.Invocation(command, 1, b"", b"resolver failed")
                return self.installer.Invocation(command, 0, b"", b"")

            with (
                mock.patch.object(self.installer, "invoke", fake_invoke),
                mock.patch.object(
                    self.installer, "profile_python", return_value=fake_python
                ),
            ):
                receipt = self.installer.install_control_plane_profile(
                    wheel,
                    profile,
                    pins=pins,
                    wheelhouse=wheelhouse,
                )

        self.assertEqual(receipt["state"], "FAILED")
        self.assertEqual(receipt["reason"], "direct_control_plane_pin_install_failed")
        checks = {check["name"]: check for check in receipt["checks"]}
        self.assertEqual(checks["installed_profile_attestation"]["state"], "SKIPPED")
        self.assertEqual(checks["installed_wave_command_available"]["state"], "SKIPPED")
        self.assertFalse(any("constraintbox" in command for command in commands))

    def test_missing_profile_interpreter_yields_one_finite_skip_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel")
            profile = root / "existing-profile"
            profile.mkdir()
            (profile / "pyvenv.cfg").write_text("home = test\n", encoding="utf-8")

            receipt = self.installer.install_control_plane_profile(
                wheel,
                profile,
                pins=self._pins(root),
                wheelhouse=root,
                update_existing=True,
            )

        self.assertEqual(receipt["state"], "FAILED")
        self.assertEqual(receipt["reason"], "profile_interpreter_missing")
        checks = receipt["checks"]
        self.assertEqual(len(checks), 6)
        self.assertEqual(
            [check["name"] for check in checks],
            [
                "profile_venv_create",
                "base_light_wheel_install",
                "direct_control_plane_pin_install",
                "profile_pip_dependency_check",
                "installed_profile_attestation",
                "installed_wave_command_available",
            ],
        )
        self.assertEqual(len({check["name"] for check in checks}), len(checks))

    def test_existing_profile_requires_explicit_update_and_windows_path_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "existing-profile"
            profile.mkdir()
            (profile / "pyvenv.cfg").write_text("home = test\n", encoding="utf-8")
            wheel = root / "constraintbox-0.4.0.dev1-py3-none-any.whl"
            wheel.write_bytes(b"local wheel")
            with self.assertRaisesRegex(
                self.installer.InstallError, "update-existing"
            ):
                self.installer.install_control_plane_profile(
                    wheel,
                    profile,
                    pins=self._pins(root),
                    wheelhouse=root,
                )
            with mock.patch.object(self.installer.os, "name", "nt"):
                self.assertEqual(
                    self.installer.profile_python(profile),
                    profile / "Scripts" / "python.exe",
                )


if __name__ == "__main__":
    unittest.main()
