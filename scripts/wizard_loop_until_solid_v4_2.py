#!/usr/bin/env python3
"""Loop Wizard v4.2 runs, using only valid runs as the next loop input."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT_RE = re.compile(r"/tmp/[^\s]+/\d{8}T\d{6}Z")


def run(command: list[str], cwd: Path, log_path: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if log_path:
        log_path.write_text(proc.stdout, encoding="utf-8")
    return proc.returncode, proc.stdout


def extract_run_root(stdout: str) -> str | None:
    matches = ROOT_RE.findall(stdout)
    return matches[-1] if matches else None


def all_first_pass_clean(status_stdout: str) -> bool:
    try:
        data = json.loads(status_stdout)
    except json.JSONDecodeError:
        return False
    return all(bool(row.get("first_pass_clean")) for row in data.get("members") or [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--cwd", default=str(Path.cwd()))
    parser.add_argument("--out-dir", default="/tmp/wizard_v4_2_loop_solid")
    parser.add_argument("--max-loops", type=int, default=3)
    parser.add_argument("--max-repair-loops", type=int, default=3)
    parser.add_argument("--sonnet-timeout-sec", type=int, default=260)
    parser.add_argument("--opus-timeout-sec", type=int, default=320)
    parser.add_argument("--haiku-timeout-sec", type=int, default=160)
    parser.add_argument("--sonnet-budget", type=float, default=1.5)
    parser.add_argument("--opus-budget", type=float, default=2.0)
    parser.add_argument("--haiku-budget", type=float, default=0.5)
    parser.add_argument("--global-max-active", type=int, default=4)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--require-first-pass-clean", action="store_true")
    args = parser.parse_args()

    cwd = Path(args.cwd)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    task = args.task
    accepted_outputs: list[Path] = []

    full_runner = Path(__file__).with_name("wizard_full_matrix_run_v4_2.py")
    compiler = Path(__file__).with_name("wizard_compile_output_v4_2.py")
    output_gate = Path(__file__).with_name("wizard_output_gate.py")
    status = Path(__file__).with_name("wizard_member_status_v4_2.py")

    for loop_index in range(1, args.max_loops + 1):
        loop_dir = out_dir / f"loop-{loop_index:02d}"
        loop_dir.mkdir(parents=True, exist_ok=True)
        full_log = loop_dir / "full-run.log"
        code, stdout = run(
            [
                sys.executable,
                str(full_runner),
                "--task",
                task,
                "--out-dir",
                str(loop_dir),
                "--max-repair-loops",
                str(args.max_repair_loops),
                "--sonnet-timeout-sec",
                str(args.sonnet_timeout_sec),
                "--opus-timeout-sec",
                str(args.opus_timeout_sec),
                "--haiku-timeout-sec",
                str(args.haiku_timeout_sec),
                "--sonnet-budget",
                str(args.sonnet_budget),
                "--opus-budget",
                str(args.opus_budget),
                "--haiku-budget",
                str(args.haiku_budget),
                "--global-max-active",
                str(args.global_max_active),
                "--max-concurrency",
                str(args.max_concurrency),
                "--attempt-gemini",
            ],
            cwd,
            full_log,
        )
        run_root = extract_run_root(stdout)
        if code != 0 or not run_root:
            print(f"loop {loop_index}: invalid full run")
            print(f"log: {full_log}")
            return 1

        status_log = loop_dir / "status.md"
        status_code, _ = run([sys.executable, str(status), run_root], cwd, status_log)
        if status_code != 0:
            print(f"loop {loop_index}: status gate failed")
            print(f"run_root: {run_root}")
            print(f"status: {status_log}")
            return 1
        status_json_log = loop_dir / "status.json"
        status_json_code, status_json_stdout = run([sys.executable, str(status), "--json", run_root], cwd, status_json_log)
        if args.require_first_pass_clean and (status_json_code != 0 or not all_first_pass_clean(status_json_stdout)):
            print(f"loop {loop_index}: valid but not first-pass clean")
            print(f"run_root: {run_root}")
            print(f"status: {status_json_log}")
            return 1

        output_path = loop_dir / "compiled-output.md"
        compile_code, _ = run(
            [
                sys.executable,
                str(compiler),
                run_root,
                "--task",
                task,
                "--out",
                str(output_path),
                "--loop-index",
                str(loop_index),
            ],
            cwd,
            loop_dir / "compile.log",
        )
        if compile_code != 0:
            print(f"loop {loop_index}: output compile failed")
            print(f"run_root: {run_root}")
            return 1

        gate_code, gate_stdout = run([sys.executable, str(output_gate), str(output_path)], cwd, loop_dir / "output-gate.log")
        if gate_code != 0:
            print(f"loop {loop_index}: output gate failed")
            print(gate_stdout)
            print(f"output: {output_path}")
            return 1

        accepted_outputs.append(output_path)
        print(f"loop {loop_index}: valid")
        print(f"run_root: {run_root}")
        print(f"output: {output_path}")

        task = (
            "Continue hardening Wizard v4.2 using only the last valid loop output as accepted input. "
            "Pick the most valuable follow-up from that output, run full Decision -> Failure -> Follow-Up again, "
            "ensure real premortem and context strategy run, and improve any remaining weak spot without creating doc sprawl.\n\n"
            + output_path.read_text(encoding="utf-8")
        )

    print("solid loop cap reached")
    print(f"accepted_outputs={len(accepted_outputs)}")
    print(f"latest_output={accepted_outputs[-1] if accepted_outputs else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
