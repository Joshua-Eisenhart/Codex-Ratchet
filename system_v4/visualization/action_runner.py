from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_bundle(bundle_path: Path) -> dict:
    return json.loads(Path(bundle_path).read_text(encoding="utf-8"))


def _flatten_steps(bundle: dict) -> list[dict]:
    steps: list[dict] = []

    for item in bundle.get("reexport_commands", []):
        base = f"reexport:{item['run_id']}"
        if item.get("export_command"):
            steps.append({
                "step_id": f"{base}:export",
                "category": "reexport",
                "kind": "export",
                "run_id": item["run_id"],
                "root": item["root"],
                "sim_name": item["sim_name"],
                "command": item["export_command"],
            })
        steps.append({
            "step_id": f"{base}:validate",
            "category": "reexport",
            "kind": "validate",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "command": item["validate_command"],
        })
        steps.append({
            "step_id": f"{base}:compare",
            "category": "reexport",
            "kind": "compare",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "command": item["compare_command"],
        })

    for item in bundle.get("archive_commands", []):
        base = f"archive:{item['run_id']}"
        steps.append({
            "step_id": f"{base}:mkdir",
            "category": "archive",
            "kind": "mkdir",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "command": item["mkdir_command"],
        })
        steps.append({
            "step_id": f"{base}:move",
            "category": "archive",
            "kind": "move",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "command": item["move_command"],
        })

    return steps


def collect_bundle_steps(bundle_path: Path) -> dict:
    bundle = _load_bundle(bundle_path)
    steps = _flatten_steps(bundle)
    return {
        "bundle_path": str(Path(bundle_path)),
        "roots": bundle["roots"],
        "root_count": bundle["root_count"],
        "summary": {
            **bundle["summary"],
            "step_count": len(steps),
        },
        "steps": steps,
    }


def render_bundle_steps(bundle_path: Path) -> str:
    report = collect_bundle_steps(bundle_path)
    lines = [
        f"Bundle: {report['bundle_path']}",
        f"Roots: {', '.join(report['roots'])}",
        f"Steps: {report['summary']['step_count']}",
    ]
    for step in report["steps"]:
        lines.append(
            f"{step['step_id']} | {step['category']} | {step['sim_name']} | {step['command']}"
        )
    return "\n".join(lines)


def run_bundle_step(bundle_path: Path, step_id: str, allow_archive: bool = False, dry_run: bool = False) -> dict:
    report = collect_bundle_steps(bundle_path)
    step = next((item for item in report["steps"] if item["step_id"] == step_id), None)
    if step is None:
        raise ValueError(f"unknown step_id: {step_id}")

    if step["category"] == "archive" and not allow_archive:
        raise ValueError("archive steps require allow_archive=True")

    if dry_run:
        return {
            "ok": True,
            "executed": False,
            "step": step,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    completed = subprocess.run(
        shlex.split(step["command"]),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "executed": True,
        "step": step,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
