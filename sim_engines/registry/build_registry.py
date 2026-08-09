#!/usr/bin/env python3
"""Build the deterministic v9 tool registry from install and usage sources."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "sim_engines" / "install" / "profiles.v9.json"
USAGE = ROOT / "sim_engines" / "registry" / "usage-map.v9.json"
LEVELS = ROOT / "sim_engines" / "registry" / "integration-levels.v1.json"
JULIA_PROJECT = ROOT / "sim_engines" / "install" / "julia" / "Project.toml"
OUTPUT = ROOT / "sim_engines" / "registry" / "tool-registry.v9.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _python_id(distribution: str) -> str:
    return "python." + distribution.lower().replace("_", "-")


def build() -> dict[str, Any]:
    profiles = _load_json(PROFILES)
    usage = _load_json(USAGE)
    allowed_levels = set(_load_json(LEVELS)["ordered_levels"])
    by_id: dict[str, dict[str, Any]] = {}

    for profile in profiles["profiles"]:
        if profile["runtime"] != "python":
            continue
        for package in profile["packages"]:
            tool_id = _python_id(package["distribution"])
            row = by_id.setdefault(
                tool_id,
                {
                    "id": tool_id,
                    "runtime": "python",
                    "distribution": package["distribution"],
                    "import": package["import"],
                    "install_spec": package["spec"],
                    "install_profiles": [],
                    "required_apis": [],
                    "roles": [],
                    "source_paths": [],
                    "test_commands": [],
                    "evidence_paths": [],
                    "declared_integration_level": "installed_only",
                },
            )
            if package.get("quarantined"):
                row["declared_integration_level"] = "quarantined"
            row["install_profiles"].append(profile["id"])

    for tool_id, fields in usage["tools"].items():
        if tool_id not in by_id:
            raise ValueError(f"usage map names unregistered Python tool {tool_id}")
        by_id[tool_id].update(fields)

    for static in usage["static_runtime_tools"]:
        tool_id = static["id"]
        if tool_id in by_id:
            raise ValueError(f"duplicate static tool id {tool_id}")
        by_id[tool_id] = dict(static)

    project = tomllib.loads(JULIA_PROJECT.read_text(encoding="utf-8"))
    for package in sorted(project["deps"]):
        tool_id = f"julia.{package}"
        by_id.setdefault(
            tool_id,
            {
                "id": tool_id,
                "runtime": "julia_package",
                "package": package,
                "install_profiles": ["julia-strict-carrier"],
                "required_apis": [],
                "roles": ["strict_carrier_candidate"],
                "source_paths": ["sim_engines/install/julia/Project.toml"],
                "test_commands": [],
                "evidence_paths": [],
                "declared_integration_level": "installed_only",
            },
        )

    for row in by_id.values():
        level = row["declared_integration_level"]
        if level not in allowed_levels:
            raise ValueError(f"unknown integration level {level!r} for {row['id']}")
        row["install_profiles"] = sorted(set(row.get("install_profiles", [])))
        for field in ("required_apis", "roles", "source_paths", "test_commands", "evidence_paths"):
            row[field] = list(row.get(field, []))

    return {
        "schema": "codex-ratchet.sim-tool-registry.v9",
        "version": "0.1.0.dev1",
        "generated_from": [
            "sim_engines/install/profiles.v9.json",
            "sim_engines/install/julia/Project.toml",
            "sim_engines/registry/usage-map.v9.json",
            "sim_engines/registry/integration-levels.v1.json"
        ],
        "tools": [by_id[key] for key in sorted(by_id)],
    }


def encoded() -> str:
    return json.dumps(build(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = encoded()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"registry drift: run {Path(__file__).relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"registry current: {len(build()['tools'])} tools")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(build()['tools'])} tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
