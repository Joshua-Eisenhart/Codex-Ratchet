#!/usr/bin/env python3
"""Report stale browser/computer-use helpers before non-browser sim runs.

This script is read-only. It does not start browser tooling and it does not kill
processes. Use it as a preflight guard before sim/controller runs where stale
MCP helpers would only add memory pressure and contaminate runtime evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


HELPER_PATTERNS = {
    "playwright_mcp": ("playwright-mcp", "@playwright/mcp"),
    "computer_use_mcp": ("SkyComputerUseClient",),
}


@dataclass
class ProcessHit:
    kind: str
    pid: int
    ppid: int
    etime: str
    command: str
    suggested_stop: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return nonzero when helper processes are present.",
    )
    return parser.parse_args()


def _ps_rows() -> Iterable[tuple[int, int, str, str]]:
    proc = subprocess.run(
        ["ps", "-axo", "pid=", "-o", "ppid=", "-o", "etime=", "-o", "command="],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ps command failed")
    for line in proc.stdout.splitlines():
        parts = line.strip().split(maxsplit=3)
        if len(parts) < 4:
            continue
        pid_text, ppid_text, etime, command = parts
        try:
            yield int(pid_text), int(ppid_text), etime, command
        except ValueError:
            continue


def audit_processes() -> dict[str, object]:
    hits: list[ProcessHit] = []
    own_pid = os.getpid()
    for pid, ppid, etime, command in _ps_rows():
        if pid == own_pid:
            continue
        for kind, needles in HELPER_PATTERNS.items():
            if any(needle in command for needle in needles):
                hits.append(
                    ProcessHit(
                        kind=kind,
                        pid=pid,
                        ppid=ppid,
                        etime=etime,
                        command=command,
                        suggested_stop=f"kill {pid}",
                    )
                )
                break
    return {
        "all_pass": not hits,
        "helper_process_count": len(hits),
        "helper_processes": [asdict(hit) for hit in hits],
        "guard": "non_browser_sim_preflight",
        "note": (
            "These helpers are only suspicious for non-browser sim/controller runs; "
            "keep them if an active browser/computer-use task intentionally owns them."
        ),
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit_processes()
    except RuntimeError as exc:
        report = {
            "all_pass": False,
            "helper_process_count": None,
            "hard_findings": [{"kind": "process_audit_failed", "error": str(exc)}],
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if args.strict and not report.get("all_pass") else 0


if __name__ == "__main__":
    sys.exit(main())
