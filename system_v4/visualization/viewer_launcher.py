from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from system_v4.visualization.consumer_admission import evaluate_consumer_admission
from system_v4.visualization.inspection import inspect_run_dir


DEFAULT_VIEWER_PYTHON = Path("/tmp/codex_ratchet_viz_env/bin/python")
REPO_ROOT = Path(__file__).resolve().parents[2]


def collect_viewer_launch(
    run_dir: Path,
    *,
    consumer: str | None = None,
    off_screen_smoke: bool = False,
    python_executable: Path | None = DEFAULT_VIEWER_PYTHON,
) -> dict:
    run_dir = Path(run_dir)
    python_executable = Path(python_executable) if python_executable is not None else DEFAULT_VIEWER_PYTHON
    inspection = inspect_run_dir(run_dir)
    consumer_admission = evaluate_consumer_admission(inspection, consumer)
    command = [
        str(python_executable),
        "-m",
        "system_v4.visualization.cli",
        "view",
        "--run",
        str(run_dir),
    ]
    if off_screen_smoke:
        command.append("--off-screen-smoke")

    return {
        "run_dir": str(run_dir),
        "status_label": inspection.get("status_label"),
        "claim_state": inspection.get("claim_state"),
        "admission_stage": inspection.get("admission_stage"),
        "promotion_target_stage": inspection.get("promotion_target_stage"),
        "promotion_status": inspection.get("promotion_status"),
        "consumer": consumer,
        "consumer_admission": consumer_admission,
        "eligible_consumers": inspection.get("eligible_consumers", []),
        "blocked_consumers": inspection.get("blocked_consumers", []),
        "promotion_blockers": inspection.get("promotion_blockers", []),
        "python_executable": str(python_executable),
        "python_exists": python_executable.exists(),
        "off_screen_smoke": off_screen_smoke,
        "command": command,
    }


def render_viewer_launch(
    run_dir: Path,
    *,
    consumer: str | None = None,
    off_screen_smoke: bool = False,
    python_executable: Path | None = DEFAULT_VIEWER_PYTHON,
) -> str:
    report = collect_viewer_launch(
        run_dir,
        consumer=consumer,
        off_screen_smoke=off_screen_smoke,
        python_executable=python_executable,
    )
    return "\n".join([
        f"Run: {report['run_dir']}",
        f"Consumer: {report['consumer'] or '(none)'}",
        f"Consumer Admitted: {report['consumer_admission']['admitted']}",
        f"Consumer Decision: {report['consumer_admission']['decision']}",
        f"Claim State: {report['claim_state']}",
        f"Admission Stage: {report['admission_stage']}",
        f"Promotion Target Stage: {report['promotion_target_stage']}",
        f"Promotion Status: {report['promotion_status']}",
        f"Claim Ceiling: {report['status_label']}",
        f"Eligible Consumers: {', '.join(report['eligible_consumers']) if report['eligible_consumers'] else '(none)'}",
        f"Blocked Consumers: {', '.join(report['blocked_consumers']) if report['blocked_consumers'] else '(none)'}",
        f"Promotion Blockers: {', '.join(report['promotion_blockers']) if report['promotion_blockers'] else '(none)'}",
        f"Python: {report['python_executable']}",
        f"Python Exists: {report['python_exists']}",
        f"Off Screen Smoke: {report['off_screen_smoke']}",
        f"Command: {' '.join(report['command'])}",
    ])


def launch_viewer(
    run_dir: Path,
    *,
    consumer: str | None = None,
    off_screen_smoke: bool = False,
    dry_run: bool = False,
    python_executable: Path | None = DEFAULT_VIEWER_PYTHON,
) -> dict:
    report = collect_viewer_launch(
        run_dir,
        consumer=consumer,
        off_screen_smoke=off_screen_smoke,
        python_executable=python_executable,
    )
    if consumer is not None and not report["consumer_admission"]["admitted"]:
        raise RuntimeError(
            f"Viewer launch blocked for consumer {consumer!r}: "
            f"{', '.join(report['consumer_admission']['reasons']) or 'no admission reason recorded'}"
        )
    if not report["python_exists"]:
        raise RuntimeError(
            f"Viewer Python not found at {report['python_executable']}. "
            "Create or install the isolated viewer environment first."
        )

    if dry_run:
        return {
            "ok": True,
            "executed": False,
            **report,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    completed = subprocess.run(
        report["command"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "executed": True,
        **report,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


if __name__ == "__main__":
    payload = launch_viewer(Path(sys.argv[1]), off_screen_smoke="--off-screen-smoke" in sys.argv[2:])
    print(json.dumps(payload, indent=2))
