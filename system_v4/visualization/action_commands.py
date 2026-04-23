from __future__ import annotations

import json
import shlex
from pathlib import Path

from system_v4.visualization.action_plan import collect_action_plan


REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = REPO_ROOT / "archive" / "viz_replay_runs"


def _quote(value: Path | str) -> str:
    return shlex.quote(str(value))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_reexport_commands(item: dict) -> dict:
    run_dir = Path(item["root"]) / item["run_id"]
    manifest = _load_json(run_dir / "run_manifest.json")
    scene = _load_json(run_dir / "scene.json")
    suggested_run_id = f"{item['run_id']}__reexport"
    out_dir = Path(item["root"])

    if item["sim_name"] == "parallel_transport_s2_classical":
        frame_count = int(manifest["frame_count"])
        steps_per_arc = max(1, (frame_count - 1) // 3)
        export_command = (
            "python3 -m system_v4.visualization.cli export transport_s2 "
            f"--run-id {_quote(suggested_run_id)} "
            f"--out-dir {_quote(out_dir)} "
            f"--steps-per-arc {steps_per_arc}"
        )
    elif item["sim_name"] == "hopf_bundle_lift":
        n_points = int(manifest["frame_count"])
        fiber_points = int(scene.get("fiber_points", 32))
        fiber_twist = float(scene.get("fiber_twist", 1.0))
        export_command = (
            "python3 -m system_v4.visualization.cli export hopf_bundle "
            f"--run-id {_quote(suggested_run_id)} "
            f"--out-dir {_quote(out_dir)} "
            f"--n-points {n_points} "
            f"--fiber-points {fiber_points} "
            f"--fiber-twist {fiber_twist}"
        )
    else:
        export_command = None

    suggested_run_dir = out_dir / suggested_run_id
    validate_command = (
        "python3 -m system_v4.visualization.cli validate "
        f"--run {_quote(suggested_run_dir)}"
    )
    compare_command = (
        "python3 -m system_v4.visualization.cli compare "
        f"--left {_quote(suggested_run_dir)} "
        f"--right {_quote(Path(item['target_root']) / item['target_run_id'])}"
    )

    return {
        "run_id": item["run_id"],
        "root": item["root"],
        "sim_name": item["sim_name"],
        "suggested_run_id": suggested_run_id,
        "suggested_run_dir": str(suggested_run_dir),
        "export_command": export_command,
        "validate_command": validate_command,
        "compare_command": compare_command,
    }


def _build_archive_commands(item: dict) -> dict:
    source_dir = Path(item["root"]) / item["run_id"]
    dest_dir = ARCHIVE_ROOT / item["sim_name"] / item["run_id"]
    return {
        "run_id": item["run_id"],
        "root": item["root"],
        "sim_name": item["sim_name"],
        "archive_dir": str(dest_dir),
        "mkdir_command": f"mkdir -p {_quote(dest_dir.parent)}",
        "move_command": f"mv {_quote(source_dir)} {_quote(dest_dir)}",
    }


def collect_action_commands(roots: list[Path]) -> dict:
    plan = collect_action_plan(roots)

    return {
        "roots": plan["roots"],
        "root_count": plan["root_count"],
        "summary": {
            "run_count": plan["summary"]["run_count"],
            "valid_count": plan["summary"]["valid_count"],
            "invalid_count": plan["summary"]["invalid_count"],
            "reexport_command_count": len(plan["do_now"]),
            "archive_command_count": len(plan["do_later"]),
        },
        "reexport_commands": [
            _build_reexport_commands(item)
            for item in plan["do_now"]
        ],
        "archive_commands": [
            _build_archive_commands(item)
            for item in plan["do_later"]
        ],
    }


def render_action_commands(roots: list[Path]) -> str:
    report = collect_action_commands(roots)
    lines = [
        f"Roots: {', '.join(report['roots'])}",
        f"Runs: {report['summary']['run_count']} | valid={report['summary']['valid_count']} | invalid={report['summary']['invalid_count']}",
        f"Commands: re-export={report['summary']['reexport_command_count']} | archive={report['summary']['archive_command_count']}",
    ]

    if report["reexport_commands"]:
        lines.append("Run Now Commands:")
        for item in report["reexport_commands"]:
            lines.append(
                f"{item['sim_name']} | source={item['run_id']} [{item['root']}] | new_run={item['suggested_run_id']}"
            )
            if item["export_command"]:
                lines.append(item["export_command"])
            lines.append(item["validate_command"])
            lines.append(item["compare_command"])

    if report["archive_commands"]:
        lines.append("Run Later Commands:")
        for item in report["archive_commands"]:
            lines.append(
                f"{item['sim_name']} | source={item['run_id']} [{item['root']}] | archive={item['archive_dir']}"
            )
            lines.append(item["mkdir_command"])
            lines.append(item["move_command"])

    return "\n".join(lines)
