#!/usr/bin/env python3
"""Portable profile planner and virtual-environment installer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PROFILES = ROOT / "install" / "profiles.v9.json"


def load_profiles() -> dict[str, dict[str, Any]]:
    body = json.loads(PROFILES.read_text(encoding="utf-8"))
    return {row["id"]: row for row in body["profiles"]}


def expand_profile_ids(profile_ids: list[str], profiles: dict[str, dict[str, Any]]) -> list[str]:
    """Resolve profile includes in dependency-first order and reject cycles."""
    unknown = sorted(set(profile_ids) - set(profiles))
    if unknown:
        raise ValueError(f"unknown profile(s): {', '.join(unknown)}")
    ordered: list[str] = []
    complete: set[str] = set()
    visiting: set[str] = set()

    def visit(profile_id: str) -> None:
        if profile_id in complete:
            return
        if profile_id in visiting:
            raise ValueError(f"cyclic profile include at {profile_id}")
        visiting.add(profile_id)
        for included in profiles[profile_id].get("includes", []):
            if included not in profiles:
                raise ValueError(f"profile {profile_id} includes unknown profile {included}")
            visit(included)
        visiting.remove(profile_id)
        complete.add(profile_id)
        ordered.append(profile_id)

    for profile_id in profile_ids:
        visit(profile_id)
    return ordered


def plan(profile_ids: list[str]) -> list[str]:
    profiles = load_profiles()
    specs: dict[str, str] = {}
    for profile_id in expand_profile_ids(profile_ids, profiles):
        profile = profiles[profile_id]
        if profile["runtime"] != "python":
            raise ValueError(f"profile {profile_id} is not a Python profile")
        for package in profile["packages"]:
            distribution = package["distribution"].lower().replace("_", "-")
            previous = specs.get(distribution)
            if previous is not None and previous != package["spec"]:
                raise ValueError(f"conflicting specs for {distribution}: {previous!r} vs {package['spec']!r}")
            specs[distribution] = package["spec"]
    return [specs[key] for key in sorted(specs)]


def main() -> int:
    parser = argparse.ArgumentParser(prog="sim-engines-install")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    for name in ("plan", "create"):
        command = commands.add_parser(name)
        command.add_argument("--profile", action="append", required=True, dest="profiles")
        if name == "create":
            command.add_argument("--venv", required=True, type=Path)
    args = parser.parse_args()
    profiles = load_profiles()
    if args.command == "list":
        for key in sorted(profiles):
            row = profiles[key]
            includes = ",".join(row.get("includes", [])) or "-"
            print(f"{key}\t{row['runtime']}\tdefault={str(row['default']).lower()}\tincludes={includes}\t{row['purpose']}")
        return 0
    specs = plan(args.profiles)
    if args.command == "plan":
        print("\n".join(specs))
        return 0
    venv = args.venv.expanduser().resolve()
    if venv.exists():
        raise SystemExit(f"refusing to overwrite existing venv: {venv}")
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", *specs], check=True)
    print(f"created {venv} with profiles {', '.join(args.profiles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
