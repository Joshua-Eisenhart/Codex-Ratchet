#!/usr/bin/env python3
"""Verify that all declared CB dependencies are installed at correct versions.

This script checks:
1. Every hard dependency is importable
2. Every declared version constraint is satisfied
3. Every optional extra's dependencies are available (if extra installed)

Exit code:
  0 = all required dependencies OK
  1 = missing required dependency or version mismatch
"""

from __future__ import annotations

import importlib.metadata
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class PackageStatus:
    """Status of a single package check."""
    name: str
    required: bool  # True if hard dependency, False if extra/optional
    installed: bool
    found_version: str | None = None
    expected_constraint: str | None = None
    satisfies_constraint: bool | None = None
    error: str | None = None


def parse_version_constraint(constraint: str) -> tuple[str, str | None]:
    """Parse constraint like '>=4.16.0.0,<4.17.0.0' into (package, (lower, upper))."""
    # Handle constraints like:
    # "z3-solver>=4.16.0.0,<4.17.0.0" -> ("z3-solver", ">=4.16.0.0,<4.17.0.0")
    parts = constraint.split(">")
    if len(parts) > 1:
        pkg_part = parts[0].strip()
        return pkg_part, constraint

    parts = constraint.split("<")
    if len(parts) > 1:
        pkg_part = parts[0].strip()
        return pkg_part, constraint

    parts = constraint.split("=")
    if len(parts) > 1:
        pkg_part = parts[0].strip()
        return pkg_part, constraint

    # No version specifier
    return constraint.strip(), None


# Distribution name -> import name, for the few where they differ.
IMPORT_NAMES = {
    "z3-solver": "z3",
    "python-Levenshtein": "Levenshtein",
    "beautifulsoup4": "bs4",
    "protobuf": "google.protobuf",
    "PyJWT": "jwt",
}


def package_from_import_name(import_name: str, declared_name: str) -> str:
    """Map import names to distribution names.

    For example:
    - z3-solver (declared) -> z3 (import)
    - libcst -> libcst
    """
    mapping = {
        "z3": "z3-solver",
        "cvc5": "cvc5",
        "sympy": "sympy",
        "rustworkx": "rustworkx",
        "maude": "maude",
        "libcst": "libcst",
        "hypothesis": "hypothesis",
    }
    return mapping.get(declared_name, declared_name)


def check_single_package(
    import_name: str,
    declared_name: str,
    constraint: str | None,
    required: bool,
) -> PackageStatus:
    """Check if a single package is installed and satisfies constraints."""
    status = PackageStatus(
        name=declared_name,
        required=required,
        installed=False,
        expected_constraint=constraint,
    )

    # Try to import the package
    try:
        module = importlib.import_module(import_name)
        status.installed = True
    except ImportError as e:
        status.error = str(e)
        return status

    # Check version if constraint exists
    if constraint:
        try:
            dist_name = package_from_import_name(import_name, declared_name)
            dist = importlib.metadata.distribution(dist_name)
            found_version = dist.version
            status.found_version = found_version

            # Parse and check constraint
            status.satisfies_constraint = check_version_constraint(
                found_version, constraint
            )

            if not status.satisfies_constraint:
                status.error = f"Version mismatch: found {found_version}, need {constraint}"
        except importlib.metadata.PackageNotFoundError:
            status.error = f"Package {declared_name} not found in metadata"
            status.satisfies_constraint = False
        except Exception as e:
            status.error = str(e)
            status.satisfies_constraint = False
    else:
        # No version constraint, just check if importable
        status.satisfies_constraint = True

    return status


def check_version_constraint(found: str, constraint: str) -> bool:
    """Check if found version satisfies constraint string.

    Handles:
    - ">=4.16.0.0,<4.17.0.0"
    - "==1.6.0"
    - ">=1.3.3,<1.4.0"
    """
    # Simple version comparison - not a full semver parser
    # Just split on . and compare numerically

    def version_tuple(v: str) -> tuple[int, ...]:
        """Convert '4.16.0.0' to (4, 16, 0, 0)."""
        parts = []
        for p in v.split("."):
            try:
                parts.append(int(p))
            except ValueError:
                # For non-numeric parts, put them at the end
                return tuple(parts)
        return tuple(parts)

    found_tuple = version_tuple(found)

    # Parse constraints like ">=4.16.0.0,<4.17.0.0" or "==1.6.0"
    constraints = constraint.split(",")

    for c in constraints:
        c = c.strip()
        if c.startswith("=="):
            required = version_tuple(c[2:])
            if found_tuple != required:
                return False
        elif c.startswith(">="):
            min_version = version_tuple(c[2:])
            if found_tuple < min_version:
                return False
        elif c.startswith("<="):
            max_version = version_tuple(c[2:])
            if found_tuple > max_version:
                return False
        elif c.startswith(">"):
            min_version = version_tuple(c[1:])
            if found_tuple <= min_version:
                return False
        elif c.startswith("<"):
            max_version = version_tuple(c[1:])
            if found_tuple >= max_version:
                return False

    return True


def main() -> int:
    """Run verification checks and report results."""

    # Hard dependencies are READ FROM pyproject.toml, never hardcoded here.
    # A verifier that embeds its own copy of the contract is not verifying the
    # contract, it is asserting a second one. That defect was live in this file:
    # it pinned libcst >=0.4.0,<0.5.0 after libcst had been removed from the
    # declared dependencies, so it refused the very environment CB runs in.
    import tomllib

    pyproject = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text())["project"]
    hard_deps = []
    for spec in declared["dependencies"]:
        name = re.split(r"[><=!~\[]", spec, 1)[0].strip()
        constraint = spec[len(name):].strip()
        hard_deps.append((IMPORT_NAMES.get(name, name.replace("-", "_")), name, constraint))

    test_deps = []
    for spec in declared.get("optional-dependencies", {}).get("test", []):
        name = re.split(r"[><=!~\[]", spec, 1)[0].strip()
        constraint = spec[len(name):].strip()
        test_deps.append((IMPORT_NAMES.get(name, name.replace("-", "_")), name, constraint))

    # Check all packages
    results = []
    has_error = False

    print("Checking hard dependencies (required):")
    print("-" * 80)
    for import_name, declared_name, constraint in hard_deps:
        status = check_single_package(
            import_name, declared_name, constraint, required=True
        )
        results.append(status)

        if status.installed:
            if status.satisfies_constraint:
                icon = "✓"
                detail = f"OK (version {status.found_version})"
            else:
                icon = "✗"
                detail = status.error or "Version mismatch"
                has_error = True
        else:
            icon = "✗"
            detail = status.error or "Not installed"
            has_error = True

        print(f"  {icon} {declared_name:20} {detail}")

    print("\nOptional test dependencies (if 'full' extra installed):")
    print("-" * 80)
    for import_name, declared_name, constraint in test_deps:
        status = check_single_package(
            import_name, declared_name, constraint, required=False
        )
        results.append(status)

        if status.installed:
            if status.satisfies_constraint:
                icon = "✓"
                detail = f"OK (version {status.found_version})"
            else:
                icon = "○"
                detail = status.error or "Version mismatch (optional)"
        else:
            icon = "○"
            detail = "Not installed (optional)"

        print(f"  {icon} {declared_name:20} {detail}")

    # Summary
    print("\n" + "=" * 80)
    required_ok = all(
        s.installed and s.satisfies_constraint
        for s in results
        if s.required
    )

    if required_ok:
        print("✓ All required dependencies installed and at correct versions.")
        return 0
    else:
        print("✗ Some required dependencies are missing or have version mismatches.")
        print("\nFailing packages:")
        for s in results:
            if s.required and not (s.installed and s.satisfies_constraint):
                print(f"  - {s.name}: {s.error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
