#!/usr/bin/env python3
"""Observe the live machine without confusing installation with integration."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sim_engines" / "registry" / "tool-registry.v9.json"
JULIA_PROJECT = ROOT / "sim_engines" / "install" / "julia"


def _import_visible(import_name: str) -> bool:
    """Return visibility without importing a package or crashing on a missing parent."""
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _portable_path(value: str) -> str:
    home = str(Path.home())
    return value.replace(home, "$HOME", 1) if value.startswith(home) else value


def _distribution_versions() -> dict[str, str]:
    found: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            found[name.lower().replace("_", "-")] = distribution.version
    return found


def _julia_visibility(names: list[str], timeout: int) -> dict[str, bool | None]:
    julia = shutil.which("julia")
    if julia is None:
        return {name: False for name in names}
    quoted = ",".join(json.dumps(name) for name in names)
    code = f'for n in [{quoted}]; println(n, "\\t", Base.find_package(n) === nothing ? "0" : "1"); end'
    try:
        completed = subprocess.run(
            [julia, "--startup-file=no", f"--project={JULIA_PROJECT}", "-e", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {name: None for name in names}
    observed = {name: None for name in names}
    if completed.returncode != 0:
        return observed
    for line in completed.stdout.splitlines():
        name, separator, bit = line.partition("\t")
        if separator and name in observed:
            observed[name] = bit == "1"
    return observed


def _julia_depot_visibility(names: list[str]) -> dict[str, bool]:
    """Observe installed package trees without claiming active-project visibility."""
    configured = [part for part in os.environ.get("JULIA_DEPOT_PATH", "").split(os.pathsep) if part]
    depots = [Path(part).expanduser() for part in configured]
    default = Path.home() / ".julia"
    if default not in depots:
        depots.append(default)
    return {name: any((depot / "packages" / name).is_dir() for depot in depots) for name in names}


def observe(include_julia: bool = False, julia_timeout: int = 120) -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    distributions = _distribution_versions()
    julia_names = [row["package"] for row in registry["tools"] if row["runtime"] == "julia_package"]
    julia_state = _julia_visibility(julia_names, julia_timeout) if include_julia else {name: None for name in julia_names}
    julia_depot_state = _julia_depot_visibility(julia_names)
    rows: list[dict[str, Any]] = []
    registered_distributions: set[str] = set()
    for declared in registry["tools"]:
        row = dict(declared)
        runtime = row["runtime"]
        if runtime == "python":
            normalized = row["distribution"].lower().replace("_", "-")
            registered_distributions.add(normalized)
            row["live_version"] = distributions.get(normalized)
            row["live_install_state"] = "import_visible" if _import_visible(row["import"]) else "missing"
        elif runtime == "julia_package":
            visible = julia_state[row["package"]]
            depot_installed = julia_depot_state[row["package"]]
            row["live_version"] = None
            row["julia_depot_installed"] = depot_installed
            if visible is None:
                row["live_install_state"] = "depot_installed_project_unchecked" if depot_installed else "unchecked"
            elif visible:
                row["live_install_state"] = "load_path_visible"
            elif depot_installed:
                row["live_install_state"] = "depot_installed_not_active_project"
            else:
                row["live_install_state"] = "missing"
        else:
            executable = row.get("executable")
            resolved = shutil.which(executable) if executable else None
            row["live_version"] = None
            row["live_install_state"] = "executable_visible" if resolved else "missing"
            row["resolved_executable"] = None if resolved is None else _portable_path(resolved)
        rows.append(row)
    unregistered = [
        {"distribution": name, "version": version, "live_install_state": "unregistered_installed", "declared_integration_level": "installed_only"}
        for name, version in sorted(distributions.items())
        if name not in registered_distributions
    ]
    return {
        "schema": "codex-ratchet.live-tool-index.v9",
        "registry_version": registry["version"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0], "executable": _portable_path(sys.executable)},
        "julia_probe": "executed" if include_julia else "not_requested",
        "registered_tools": rows,
        "unregistered_installed_python_distributions": unregistered,
        "summary": {
            "registered_tool_count": len(rows),
            "registered_visible_count": sum(row["live_install_state"] in {"import_visible", "load_path_visible", "executable_visible"} for row in rows),
            "registered_installed_or_visible_count": sum(row["live_install_state"] in {"import_visible", "load_path_visible", "executable_visible", "depot_installed_not_active_project", "depot_installed_project_unchecked"} for row in rows),
            "registered_missing_count": sum(row["live_install_state"] == "missing" for row in rows),
            "registered_unchecked_count": sum(row["live_install_state"] in {"unchecked", "depot_installed_project_unchecked"} for row in rows),
            "julia_depot_installed_not_active_project_count": sum(row["live_install_state"] == "depot_installed_not_active_project" for row in rows),
            "unregistered_installed_python_distribution_count": len(unregistered)
        },
        "claim_ceiling": "installation_and_declared_source_integration_index_only"
    }


def _markdown(body: dict[str, Any]) -> str:
    lines = ["# Live Sim Engines tool index", "", f"Generated: `{body['generated_at']}`", "", "Installation visibility and declared integration are independent columns.", "", "| Tool | Runtime | Live state | Declared integration | Profiles |", "|---|---|---|---|---|"]
    for row in body["registered_tools"]:
        lines.append(f"| `{row['id']}` | {row['runtime']} | {row['live_install_state']} | {row['declared_integration_level']} | {', '.join(row.get('install_profiles', []))} |")
    lines.extend(["", "## Summary", "", "```json", json.dumps(body["summary"], indent=2, sort_keys=True), "```", "", "Unregistered installed distributions are retained in the JSON index with level `installed_only`; they are omitted from this table to keep it readable.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-julia", action="store_true")
    parser.add_argument("--julia-timeout", type=int, default=120)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    body = observe(args.include_julia, args.julia_timeout)
    if args.output_dir:
        target = args.output_dir.resolve()
        target.mkdir(parents=True, exist_ok=True)
        (target / "LIVE_TOOL_INDEX.json").write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (target / "LIVE_TOOL_INDEX.md").write_text(_markdown(body), encoding="utf-8")
        print(target / "LIVE_TOOL_INDEX.json")
    else:
        print(json.dumps(body, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
