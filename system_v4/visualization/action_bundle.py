from __future__ import annotations

import json
from pathlib import Path

from system_v4.visualization.action_commands import collect_action_commands


def _build_shell_script(report: dict) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Generated dry-run command bundle for the visualization replay lane.",
        "# Inspect before running. Nothing here was executed automatically.",
    ]

    if report["reexport_commands"]:
        lines.extend(["", "# Re-export commands"])
        for item in report["reexport_commands"]:
            lines.append(
                f"# {item['sim_name']} | source={item['run_id']} | new_run={item['suggested_run_id']}"
            )
            if item["export_command"]:
                lines.append(item["export_command"])
            lines.append(item["validate_command"])
            lines.append(item["compare_command"])

    if report["archive_commands"]:
        lines.extend(["", "# Archive commands"])
        for item in report["archive_commands"]:
            lines.append(
                f"# {item['sim_name']} | source={item['run_id']} | archive={item['archive_dir']}"
            )
            lines.append(item["mkdir_command"])
            lines.append(item["move_command"])

    lines.append("")
    return "\n".join(lines)


def write_action_bundle(roots: list[Path], out_dir: Path, prefix: str = "viz_action_bundle") -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = collect_action_commands(roots)
    json_path = out_dir / f"{prefix}.json"
    script_path = out_dir / f"{prefix}.sh"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    script_path.write_text(_build_shell_script(report), encoding="utf-8")
    script_path.chmod(0o755)

    return {
        "roots": report["roots"],
        "root_count": report["root_count"],
        "summary": report["summary"],
        "bundle_dir": str(out_dir),
        "json_path": str(json_path),
        "script_path": str(script_path),
    }


def render_action_bundle_write_result(roots: list[Path], out_dir: Path, prefix: str = "viz_action_bundle") -> str:
    result = write_action_bundle(roots, out_dir, prefix=prefix)
    return "\n".join([
        f"Roots: {', '.join(result['roots'])}",
        f"Bundle Dir: {result['bundle_dir']}",
        f"JSON: {result['json_path']}",
        f"Script: {result['script_path']}",
        f"Commands: re-export={result['summary']['reexport_command_count']} | archive={result['summary']['archive_command_count']}",
    ])
