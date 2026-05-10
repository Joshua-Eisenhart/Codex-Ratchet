#!/usr/bin/env python3
"""Report stale computer-use helpers before non-browser sim runs.

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
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


HELPER_PATTERNS = {
    "computer_use_mcp": ("SkyComputerUseClient",),
}


@dataclass
class ProcessHit:
    kind: str
    pid: int
    ppid: int
    etime: str
    command: str
    parent_command: str | None
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
    commands_by_pid: dict[int, str] = {}
    rows = list(_ps_rows())
    for pid, _ppid, _etime, command in rows:
        commands_by_pid[pid] = command
    own_pid = os.getpid()
    for pid, ppid, etime, command in rows:
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
                        parent_command=commands_by_pid.get(ppid),
                        suggested_stop=f"kill {pid}",
                    )
                )
                break
    likely_root_cause = None
    if any("codex app-server" in (hit.parent_command or "") for hit in hits):
        likely_root_cause = (
            "Codex App app-server is the parent for one or more helpers; check "
            "global Codex MCP/plugin config before treating this as repo code."
        )
    return {
        "all_pass": not hits,
        "helper_process_count": len(hits),
        "helper_processes": [asdict(hit) for hit in hits],
        "mcp_config_findings": [],
        "guard": "non_browser_sim_preflight",
        "likely_root_cause": likely_root_cause,
        "note": (
            "These helpers are only suspicious for non-browser sim/controller runs; "
            "keep them if an active browser/computer-use task intentionally owns them."
        ),
    }


def audit_mcp_config(config_path: Path | None = None) -> dict[str, object]:
    config_path = config_path or Path.home() / ".codex" / "config.toml"
    if not config_path.exists():
        return {"config_path": str(config_path), "findings": [], "parse_error": None}
    try:
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "config_path": str(config_path),
            "findings": [{"kind": "codex_config_parse_error", "error": str(exc)}],
            "parse_error": str(exc),
        }
    servers = payload.get("mcp_servers") or {}
    findings: list[dict[str, object]] = []
    return {"config_path": str(config_path), "findings": findings, "parse_error": None}


def audit_all() -> dict[str, object]:
    process_report = audit_processes()
    config_report = audit_mcp_config()
    findings = list(config_report.get("findings") or [])
    process_report["mcp_config_findings"] = findings
    process_report["mcp_config_path"] = config_report.get("config_path")
    process_report["mcp_config_parse_error"] = config_report.get("parse_error")
    process_report["all_pass"] = bool(process_report.get("all_pass")) and not findings
    return process_report


def main() -> int:
    args = parse_args()
    try:
        report = audit_all()
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
