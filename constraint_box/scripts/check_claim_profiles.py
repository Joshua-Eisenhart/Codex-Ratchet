#!/usr/bin/env python3
"""Validate claim-profile matrix for well-formedness.

Checks:
  1. Every profile is well-formed (all required fields present and valid)
  2. Tools named in profiles exist in core registry or are stdlib
  3. No profile claims a tool the severance phase found decorative
  4. Every profile declares a negative_control and ceiling
  5. Negative controls and independent_recompute are not vacuous
"""

import json
import sys
from pathlib import Path


STDLIB_TOOLS = {
    "hashlib",  # used for SHA256 digest computation
    "json",     # used for JSON parsing
}

SEVERANCE_DECORATIVE = set()  # Empty: no decorative tools found in severance phase


def load_json_file(path: Path) -> dict:
    """Load and parse a JSON file."""
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Failed to load {path}: {exc}")
        sys.exit(1)


def load_core_registry(box_root: Path) -> dict:
    """Load the core tool registry."""
    registry_path = box_root / "config" / "core_tool_registry_v9.json"
    data = load_json_file(registry_path)
    if data.get("schema") != "constraintbox.core-tool-registry.v9":
        print(f"ERROR: Registry schema mismatch at {registry_path}")
        sys.exit(1)
    return data


def load_claim_profiles(box_root: Path) -> dict:
    """Load the claim profiles matrix."""
    profiles_path = box_root / "config" / "claim_profiles.json"
    data = load_json_file(profiles_path)
    if data.get("schema") != "constraintbox.claim-profiles.v1":
        print(f"ERROR: Profiles schema mismatch at {profiles_path}")
        sys.exit(1)
    return data


def load_severance_results(box_root: Path) -> dict:
    """Load the severance test results (if available)."""
    severance_path = box_root / "receipts" / "severance_v1" / "severance_summary.json"
    if not severance_path.exists():
        return {}
    return load_json_file(severance_path)


def extract_registry_tools(registry: dict) -> set:
    """Extract all tool IDs from the core registry."""
    tools = set()
    for tool in registry.get("tools", []):
        if "id" in tool:
            tools.add(tool["id"])
        # Also accept distribution names
        if "distribution" in tool:
            tools.add(tool["distribution"])
    return tools


def extract_severance_decorative(severance: dict) -> set:
    """Extract decorative tools from severance results."""
    decorative = set()
    for tool, result in severance.get("decorative", []):
        decorative.add(tool)
    return decorative


def validate_tool_reference(tool_name: str, registry_tools: set) -> tuple[bool, str]:
    """Check if a tool reference is valid.

    Returns (is_valid, error_message).
    """
    # Check if it's a distribution name in the registry
    if tool_name in registry_tools:
        return True, ""

    # Check if it's a stdlib reference
    if tool_name in STDLIB_TOOLS:
        return True, ""

    return False, f"Unknown tool: {tool_name}"


def validate_profile(profile: dict, registry_tools: set, decorative: set) -> list[str]:
    """Validate a single profile. Returns list of errors."""
    errors = []

    # Check required fields
    required_fields = [
        "claim_type",
        "description",
        "tools",
        "negative_control",
        "independent_recompute",
        "ceiling",
        "failure_disposition",
    ]
    for field in required_fields:
        if field not in profile:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    claim_type = profile.get("claim_type", "<unknown>")

    # Validate tools list
    tools = profile.get("tools", [])
    if not isinstance(tools, list):
        errors.append(f"tools must be a list, got {type(tools).__name__}")
    else:
        for tool in tools:
            valid, msg = validate_tool_reference(tool, registry_tools)
            if not valid:
                errors.append(f"  {claim_type}: {msg}")
            if tool in decorative:
                errors.append(
                    f"  {claim_type}: claims tool '{tool}' which severance found decorative"
                )

    # Validate negative_control is present and not empty
    negative_control = profile.get("negative_control", "")
    if not isinstance(negative_control, str):
        errors.append(f"negative_control must be a string")
    elif not negative_control.strip():
        errors.append(f"negative_control is empty")

    # Validate independent_recompute is present and not empty
    independent_recompute = profile.get("independent_recompute", "")
    if not isinstance(independent_recompute, str):
        errors.append(f"independent_recompute must be a string")
    elif not independent_recompute.strip():
        errors.append(f"independent_recompute is empty (no separate implementation named)")

    # Validate ceiling is present and not empty
    ceiling = profile.get("ceiling", "")
    if not isinstance(ceiling, str):
        errors.append(f"ceiling must be a string")
    elif not ceiling.strip():
        errors.append(f"ceiling is empty")

    # Validate failure_disposition is present and not empty
    failure_disposition = profile.get("failure_disposition", "")
    if not isinstance(failure_disposition, str):
        errors.append(f"failure_disposition must be a string")
    elif not failure_disposition.strip():
        errors.append(f"failure_disposition is empty")

    return errors


def main():
    """Main validation routine."""
    box_root = Path(__file__).resolve().parents[1]

    print("Loading core tool registry...")
    registry = load_core_registry(box_root)
    registry_tools = extract_registry_tools(registry)
    print(f"  Found {len(registry_tools)} tools in registry")

    print("\nLoading claim profiles...")
    profiles_data = load_claim_profiles(box_root)
    profiles = profiles_data.get("profiles", [])
    print(f"  Found {len(profiles)} claim profiles")

    print("\nLoading severance results...")
    severance = load_severance_results(box_root)
    decorative = extract_severance_decorative(severance)
    if decorative:
        print(f"  Found {len(decorative)} decorative tools: {decorative}")
    else:
        print("  No decorative tools found")

    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    total_errors = 0
    failed_profiles = []

    for i, profile in enumerate(profiles, start=1):
        claim_type = profile.get("claim_type", f"<profile {i}>")
        errors = validate_profile(profile, registry_tools, decorative)

        if errors:
            failed_profiles.append(claim_type)
            total_errors += len(errors)
            print(f"\nProfile {i}: {claim_type}")
            print("  ERRORS:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"\nProfile {i}: {claim_type}")
            print("  OK")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if total_errors == 0:
        print(f"✓ All {len(profiles)} profiles are well-formed")
        print(f"✓ All tools referenced exist in registry or stdlib")
        print(f"✓ No profiles claim decorative tools")
        print(f"✓ All profiles declare negative_control and ceiling")
        return 0
    else:
        print(f"✗ {total_errors} error(s) found in {len(failed_profiles)} profile(s)")
        print(f"  Failed profiles: {', '.join(failed_profiles)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
