from __future__ import annotations

import hashlib
import json
import tomllib
import unittest
from pathlib import Path

import constraintbox
from constraintbox.formal_registry import (
    DEFAULT_FORMAL_RUNTIME_POLICY,
    load_formal_runtime_policy,
)
from constraintbox.python_runtime import (
    DEFAULT_PYTHON_RUNTIME_POLICY,
    load_python_runtime_policy,
    python_runtime_policy_sha256,
)
from constraintbox.runtime_profiles import load_runtime_profile_registry


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = Path(constraintbox.__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PackageResourceTests(unittest.TestCase):
    def test_default_python_runtime_policy_is_a_portable_profile_resource(
        self,
    ) -> None:
        resource_root = PACKAGE_ROOT / "runtime_profiles"
        self.assertEqual(
            DEFAULT_PYTHON_RUNTIME_POLICY,
            resource_root / "core_profiles_v1.json",
        )
        self.assertTrue(DEFAULT_PYTHON_RUNTIME_POLICY.is_file())
        policy = load_python_runtime_policy()
        registry = load_runtime_profile_registry()
        self.assertEqual(policy.policy_sha256, sha256(DEFAULT_PYTHON_RUNTIME_POLICY))
        self.assertEqual(policy.policy_sha256, python_runtime_policy_sha256())
        self.assertEqual(policy.policy_sha256, registry.registry_sha256)
        self.assertEqual(
            policy.profile_ids,
            ("core-cpython311-r1", "core-cpython312-r1", "core-cpython313-r1"),
        )
        self.assertIn("itertools.product", policy.operation_ids)
        self.assertIn("math.prod", policy.operation_ids)

    def test_default_temporal_policy_and_profile_are_package_resources(
        self,
    ) -> None:
        resource_root = PACKAGE_ROOT / "formal_runtime"
        self.assertEqual(
            DEFAULT_FORMAL_RUNTIME_POLICY,
            resource_root / "formal_runtime_v1.json",
        )
        policy = load_formal_runtime_policy()
        self.assertEqual(
            policy.profile_dir,
            resource_root / "controller_lifecycle_v1",
        )
        self.assertTrue(DEFAULT_FORMAL_RUNTIME_POLICY.is_file())
        self.assertTrue((policy.profile_dir / "ConstraintBox.tla").is_file())
        self.assertTrue((policy.profile_dir / "ConstraintBox.cfg").is_file())
        self.assertTrue((policy.profile_dir / "expectations.json").is_file())

    def test_packaged_profile_hashes_bind_the_exact_resource_bytes(self) -> None:
        policy = load_formal_runtime_policy()
        expectations_path = policy.profile_dir / "expectations.json"
        self.assertEqual(
            sha256(expectations_path),
            policy.expected_expectations_sha256,
        )
        expectations = json.loads(expectations_path.read_text(encoding="utf-8"))
        self.assertEqual(
            sha256(policy.profile_dir / expectations["model_file"]),
            expectations["model_sha256"],
        )
        self.assertEqual(
            sha256(policy.profile_dir / expectations["config_file"]),
            expectations["config_sha256"],
        )

    def test_pyproject_declares_portable_core_roles_and_package_data(self) -> None:
        body = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(
            body["project"]["dependencies"],
            [
                "z3-solver>=4.16.0.0,<4.17.0.0",
                "cvc5>=1.3.3,<1.4.0",
                "sympy>=1.14.0,<1.15.0",
                "rustworkx>=0.17.0,<0.18.0",
                "maude==1.6.0",
            ],
        )
        self.assertEqual(body["project"]["requires-python"], ">=3.11,<3.14")
        extras = body["project"]["optional-dependencies"]
        self.assertEqual(extras["symbolic"], ["sympy>=1.14.0,<1.15.0"])
        self.assertEqual(extras["graph"], ["rustworkx>=0.17.0,<0.18.0"])
        # Maude is a required bounded formal/rewrite gate, not an optional
        # simulation-engine extra.
        self.assertEqual(extras["rewrite"], [])
        self.assertEqual(extras["numeric"], ["numpy==2.3.4"])
        self.assertEqual(extras["test"], ["hypothesis==6.151.12"])
        package_data = body["tool"]["setuptools"]["package-data"]["constraintbox"]
        self.assertEqual(
            package_data,
            [
                "formal_runtime/*.json",
                "formal_runtime/controller_lifecycle_v1/*",
                "runtime_profiles/*.json",
            ],
        )

    def test_lean_core_package_data_excludes_the_sim_engine_estate(self) -> None:
        package_data = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["tool"]["setuptools"]["package-data"]["constraintbox"]
        self.assertIn("runtime_profiles/*.json", package_data)
        self.assertNotIn("external_sim_estate/*", package_data)
        base_dependencies = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["dependencies"]
        self.assertEqual(
            {dependency.split(">", 1)[0] for dependency in base_dependencies},
            {"z3-solver", "cvc5", "sympy", "rustworkx", "maude==1.6.0"},
        )


if __name__ == "__main__":
    unittest.main()
