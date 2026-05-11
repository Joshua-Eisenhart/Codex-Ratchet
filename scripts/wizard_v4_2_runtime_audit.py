#!/usr/bin/env python3
"""Audit live Wizard v4.2 runtime guardrails."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()

LIVE_SURFACES = [
    ROOT / "AGENTS.md",
    ROOT / "CODEX.md",
    ROOT / "system_v5/ops/SIM_RUNNER.md",
    ROOT / "system_v5/ops/sim_runner.sh",
    ROOT / "scripts/overnight_two_runner.sh",
    ROOT / "scripts/wizard_v4_2.py",
    ROOT / "scripts/wizard_full_matrix_run_v4_2.py",
    ROOT / "scripts/wizard_autoresearch_sim_loop.py",
    ROOT / "scripts/wizard_sim_admission.py",
    HOME / ".codex/config.toml",
    HOME / ".codex/hooks.json",
]

LEGACY_ALLOWED = {
    ROOT / "scripts/wizard_full_matrix_run.py",
    ROOT / "scripts/wizard_topology.py",
    ROOT / "scripts/wizard_member_status.py",
    ROOT / "scripts/run_wizard_system.py",
}

DISALLOWED = [
    ("v4_1_packet_path", re.compile(r"packet-v4-1-current|WIZARD_FULL_v4_1|FULL_MMM_v4_1|SKILLS_MANIFEST_v4_1")),
    (
        "v4_1_live_default",
        re.compile(r"Wizard v4\.1 Max|Run Wizard v4\.1|v4\.1 queue-ready|v4\.1 admission artifacts|Wizard v4\.1 fanout guard"),
    ),
]

ALLOW_LINE = re.compile(r"legacy|reference-only|explicitly names? v4\.1|recovery run", re.IGNORECASE)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "ok": result.returncode == 0,
    }


def scan_live_surfaces() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in LIVE_SURFACES:
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            if ALLOW_LINE.search(line):
                continue
            for code, pattern in DISALLOWED:
                if pattern.search(line):
                    findings.append({"file": rel(path), "line": number, "code": code, "text": line.strip()})
    return findings


def queue_counts() -> dict[str, int | str]:
    check = run(["python3", "scripts/queue_claim.py", "counts"])
    if not check["ok"]:
        return {"error": check["stderr"] or check["stdout"] or "queue count command failed"}
    try:
        parsed = json.loads(str(check["stdout"]))
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return {
            str(key): int(value) if isinstance(value, int) else str(value)
            for key, value in parsed.items()
        }
    counts: dict[str, int | str] = {}
    for line in str(check["stdout"]).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        try:
            counts[key.strip()] = int(value.strip())
        except ValueError:
            counts[key.strip()] = value.strip()
    return counts


def heartbeat_status(counts: dict[str, int | str]) -> dict[str, Any]:
    idle = counts.get("lane_A") == 0 and counts.get("lane_B") == 0 and counts.get("claimed") == 0
    blocked_reasons = sorted(
        str(path.relative_to(ROOT))
        for base in (ROOT / "system_v5/ops/lego_scaling", ROOT / "system_v5/ops/wizard_admissions")
        if base.exists()
        for path in base.glob("*blocked*.json")
    )
    if not idle:
        status = "active_or_queued"
    elif blocked_reasons:
        status = "idle_with_blocked_reason"
    else:
        status = "needs_next_micro_move_or_blocked_reason"
    return {"status": status, "idle": idle, "blocked_reason_artifacts": blocked_reasons}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-preflight", action="store_true", help="Skip packet/helper subprocess checks.")
    args = parser.parse_args(argv)

    findings = scan_live_surfaces()
    counts = queue_counts()
    heartbeat = heartbeat_status(counts)
    checks: dict[str, Any] = {}

    if not args.skip_preflight:
        checks["packet_conformance"] = run(
            ["python3", str(HOME / "wiki/wizard/packet-v4-2-current/conformance/validate_v4_2_packet.py")]
        )
        checks["helper_processes"] = run(["python3", "scripts/helper_process_audit.py", "--strict"])

    hard_failures = bool(findings)
    hard_failures = hard_failures or any(not check.get("ok") for check in checks.values())
    hard_failures = hard_failures or heartbeat["status"] == "needs_next_micro_move_or_blocked_reason"

    report = {
        "ok": not hard_failures,
        "legacy_allowed_files": [rel(path) for path in sorted(LEGACY_ALLOWED)],
        "version_drift_findings": findings,
        "queue_counts": counts,
        "sim_heartbeat": heartbeat,
        "checks": checks,
    }
    print(json.dumps(report, indent=2))
    return 1 if hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
