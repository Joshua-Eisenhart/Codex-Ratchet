from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from constraintbox import python_runtime
from constraintbox.doctor import build_report
from constraintbox.python_runtime import (
    PythonRuntimeError,
    capture_python_runtime,
    load_python_runtime_policy,
    verify_python_runtime_stable,
)
from constraintbox.runtime_profiles import (
    DEFAULT_RUNTIME_PROFILE_REGISTRY,
    inspect_active_runtime,
    list_runtime_profiles,
    load_runtime_profile_registry,
)


class PythonRuntimeTests(unittest.TestCase):
    def test_active_runtime_is_bound_to_a_portable_core_profile(self) -> None:
        receipt = capture_python_runtime()
        policy = load_python_runtime_policy()
        self.assertEqual(receipt["schema"], "constraintbox.python-runtime-receipt.v2")
        self.assertEqual(receipt["policy_sha256"], policy.policy_sha256)
        self.assertIn(receipt["profile_id"], policy.profile_ids)
        self.assertEqual(receipt["runtime_profile"]["state"], "ELIGIBLE")
        self.assertIn(
            "maude",
            {row["distribution"] for row in receipt["runtime_profile"]["libraries"]},
        )
        self.assertEqual(
            set(receipt["operations"]),
            set(policy.operation_ids),
        )
        self.assertTrue(
            all(
                value is True
                for value in receipt["operation_witnesses"].values()
                if value != "binding_only"
            )
        )
        self.assertFalse(receipt["promotion_allowed"])
        self.assertIn("portable", receipt["claim_ceiling"])

    def test_registry_is_portable_configuration_not_a_host_attestation(self) -> None:
        raw = DEFAULT_RUNTIME_PROFILE_REGISTRY.read_text(encoding="utf-8")
        registry = load_runtime_profile_registry()
        self.assertNotIn("/Users/", raw)
        self.assertNotIn("/opt/homebrew/", raw)
        self.assertNotIn("3.13.6", raw)
        self.assertEqual(
            [profile.profile_id for profile in registry.profiles],
            ["core-cpython311-r1", "core-cpython312-r1", "core-cpython313-r1"],
        )
        self.assertEqual(
            list_runtime_profiles()["registry_sha256"],
            registry.registry_sha256,
        )

    def test_profile_resolution_supports_each_declared_python_minor(self) -> None:
        for minor in (11, 12, 13):
            with self.subTest(minor=minor):
                receipt = inspect_active_runtime(
                    implementation="CPython",
                    version_info=(3, minor, 0),
                )
                self.assertEqual(receipt["profile_id"], f"core-cpython3{minor}-r1")
                self.assertEqual(receipt["state"], "ELIGIBLE")

    def test_unknown_python_minor_parks_without_any_fallback(self) -> None:
        receipt = inspect_active_runtime(
            implementation="CPython",
            version_info=(3, 14, 0),
        )
        self.assertEqual(receipt["state"], "PARKED")
        self.assertEqual(receipt["reason"], "unsupported_python_runtime")
        self.assertIsNone(receipt["profile_id"])

    def test_version_window_drift_blocks_instead_of_silently_substituting(self) -> None:
        actual_versions = {
            row["distribution"]: row["observed_version"]
            for row in inspect_active_runtime()["libraries"]
        }

        def version_provider(distribution: str) -> str:
            if distribution == "sympy":
                return "1.15.0"
            return actual_versions[distribution]

        receipt = inspect_active_runtime(version_provider=version_provider)
        self.assertEqual(receipt["state"], "BLOCKED")
        self.assertEqual(receipt["reason"], "core_runtime_profile_mismatch")
        sympy = next(
            row for row in receipt["libraries"] if row["distribution"] == "sympy"
        )
        self.assertEqual(sympy["state"], "VERSION_OUT_OF_PROFILE")

    def test_runtime_change_remains_fail_closed_within_a_run(self) -> None:
        before = capture_python_runtime()
        after = json.loads(json.dumps(before))
        after["runtime_profile"]["flags"]["optimize"] = 99
        with self.assertRaisesRegex(PythonRuntimeError, "changed during evaluation"):
            verify_python_runtime_stable(before, after)

    def test_operation_binding_severance_fails_closed(self) -> None:
        original = python_runtime.itertools.product
        python_runtime.itertools.product = None
        try:
            with self.assertRaisesRegex(
                PythonRuntimeError,
                "Python operation binding drift: itertools.product",
            ):
                capture_python_runtime()
        finally:
            python_runtime.itertools.product = original

    def test_cli_reports_v9_core_tools_without_an_interpreter_override(self) -> None:
        root = Path(__file__).resolve().parents[1]
        environment = {
            **dict(__import__("os").environ),
            "PYTHONPATH": str(root / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        completed = subprocess.run(
            [sys.executable, "-m", "constraintbox", "doctor", "--json"],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["schema"], "constraintbox.core-doctor.v9")
        self.assertEqual(result["core_tool_ids"], [
            "python.z3",
            "python.cvc5",
            "python.sympy",
            "python.rustworkx",
            "python.maude",
        ])

    def test_doctor_exposes_profile_status_but_does_not_grant_it_authority(self) -> None:
        report = build_report()
        self.assertEqual(report["schema"], "constraintbox.doctor.v2")
        runtime = report["runtime_profile"]
        self.assertEqual(runtime["state"], "ELIGIBLE")
        self.assertFalse(runtime["promotion_allowed"])
        self.assertIn("never selects or installs", report["status_rule"])


if __name__ == "__main__":
    unittest.main()
