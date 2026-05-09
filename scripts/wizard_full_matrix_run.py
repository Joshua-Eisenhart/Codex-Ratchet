#!/usr/bin/env python3
"""Run the current Wizard v4.1 nine-member matrix under one clean root."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from wizard_topology import EXPECTED_CURRENT_TOPOLOGY_MEMBERS, ROUTES


def default_prompt(route: str, task: str) -> str:
    return (
        f"Run Wizard v4.1 current topology route {route} for this task: {task}. "
        "Use only the current v4.1 packet topology. Do not use obsolete Failure Six Hats. "
        "Return a concise receipt with member-specific findings and parent/child truth."
    )


def run_route(args: argparse.Namespace, route: str, root: Path) -> int:
    script = Path(__file__).with_name("wizard_child_matrix.py")
    command = [
        sys.executable,
        str(script),
        "--route",
        route,
        "--prompt",
        default_prompt(route, args.task),
        "--followup-prompt",
        args.followup_prompt,
        "--payoff",
        args.payoff,
        "--use-when",
        args.use_when,
        "--stop-if",
        args.stop_if,
        "--boundary",
        args.boundary,
        "--cwd",
        args.cwd,
        "--out-dir",
        str(root),
        "--run-id",
        args.run_id,
        "--sonnet-timeout-sec",
        str(args.sonnet_timeout_sec),
        "--opus-timeout-sec",
        str(args.opus_timeout_sec),
        "--haiku-timeout-sec",
        str(args.haiku_timeout_sec),
        "--global-max-active",
        str(args.global_max_active),
        "--max-concurrency",
        str(args.max_concurrency),
    ]
    if args.attempt_gemini:
        command.append("--attempt-gemini")
    if args.dry_run:
        command.append("--dry-run")
    print(f"== {route} ==")
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--cwd", default=str(Path.cwd()))
    parser.add_argument("--out-dir", default="/tmp/wizard_v4_1_full")
    parser.add_argument("--followup-prompt", default="Produce the next best bounded prompt if this route finds a blocker.")
    parser.add_argument("--payoff", default="Expose real route/member failure before synthesis.")
    parser.add_argument("--use-when", default="Use when validating Wizard v4.1 current topology.")
    parser.add_argument("--stop-if", default="Stop if a required current-topology route cannot launch or returns no usable children.")
    parser.add_argument("--boundary", default="Do not edit repo files from child routes; controller owns synthesis and edits.")
    parser.add_argument("--sonnet-timeout-sec", type=int, default=240)
    parser.add_argument("--opus-timeout-sec", type=int, default=300)
    parser.add_argument("--haiku-timeout-sec", type=int, default=180)
    parser.add_argument("--global-max-active", type=int, default=4)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--attempt-gemini", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.run_id = f"wizard-v4-1-full-{stamp}"
    if len(ROUTES) != EXPECTED_CURRENT_TOPOLOGY_MEMBERS:
        print(
            f"BLOCKED: current topology allowlist has {len(ROUTES)} members; "
            f"expected {EXPECTED_CURRENT_TOPOLOGY_MEMBERS}."
        )
        return 1
    root = Path(args.out_dir) / stamp
    root.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for route in ROUTES:
        code = run_route(args, route, root)
        if code != 0:
            failures.append(route)

    status_script = Path(__file__).with_name("wizard_member_status.py")
    print("\n== member status ==")
    status = subprocess.run([sys.executable, str(status_script), str(root)], check=False)
    if failures:
        print("\nRoutes with nonzero launcher exits: " + ", ".join(failures))
        return 1
    return status.returncode


if __name__ == "__main__":
    raise SystemExit(main())
