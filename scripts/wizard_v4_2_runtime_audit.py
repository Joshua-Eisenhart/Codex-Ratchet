#!/usr/bin/env python3
"""Audit live Wizard v4.2 runtime guardrails."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
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

LIVE_SURFACE_GLOBS = [
    (ROOT / "system_v5/wizard", "**/*.md"),
    (ROOT / "system_v5/wizard", "**/*.json"),
    (HOME / "wiki/wizard/packet-v4-2-current", "**/*.md"),
    (HOME / "wiki/wizard/packet-v4-2-current", "**/*.json"),
]

WORKER_RECEIPT_GLOBS = [
    (ROOT / "system_v5/wizard/receipts", "**/*.json"),
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
    (
        "v4_1_assignment",
        re.compile(r"(default|route|version|wizard_version|runtime)\s*[:=]\s*['\"]?v4\.1|v4\.1\s+(default|live|runtime|fanout)", re.IGNORECASE),
    ),
]

ALLOW_LINE = re.compile(
    r"(legacy v4\.1[^.]*reference-only|v4\.1[^.]*reference-only|explicitly names? v4\.1|recovery run explicitly names? v4\.1|^(banned|contrast|negative-example|do not use):|^#?\s*[A-Z0-9_]+v4_1$)",
    re.IGNORECASE,
)


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
    surfaces = set(LIVE_SURFACES)
    for base, pattern in LIVE_SURFACE_GLOBS:
        if base.exists():
            surfaces.update(path for path in base.glob(pattern) if path.is_file())
    for path in sorted(surfaces):
        if not path.exists():
            continue
        path_text = str(path)
        if "packet-v4-2-current/mmm/mini/full/compositions/md/" in path_text and "v4_1" in path.name:
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


def int_count(counts: dict[str, int | str], key: str) -> int:
    value = counts.get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def blocked_reason_valid(path: Path, *, now: datetime) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - audit report should explain bad artifacts.
        return False, f"unreadable JSON: {exc}"
    if not isinstance(data, dict):
        return False, "top-level JSON is not an object"
    timestamp = data.get("created_at") or data.get("generated_at")
    if not isinstance(timestamp, str):
        return False, "missing created_at/generated_at"
    parsed = parse_time(timestamp)
    if parsed is None:
        return False, "created_at/generated_at is not ISO-like"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if now - parsed > timedelta(hours=24):
        return False, "blocked reason is older than 24h"
    schema = str(data.get("schema", ""))
    kind = str(data.get("kind", ""))
    is_blocked_reason = kind == "blocked_reason" or schema.startswith("wizard_v4_2_blocked_reason")
    if not is_blocked_reason:
        return False, "missing kind=blocked_reason or wizard_v4_2_blocked_reason schema"
    has_reason = bool(str(data.get("reason") or data.get("scope") or data.get("claim_boundary") or "").strip())
    has_next = bool(str(data.get("next_admissible_step") or data.get("recommended_next_move") or "").strip())
    if not has_next and isinstance(data.get("blocked_candidates"), list):
        has_next = any(
            isinstance(candidate, dict) and bool(str(candidate.get("recommended_next_move", "")).strip())
            for candidate in data["blocked_candidates"]
        )
    if not has_reason:
        return False, "missing reason/scope"
    if not has_next:
        return False, "missing next_admissible_step/recommended_next_move"
    return True, "valid"


def heartbeat_status(counts: dict[str, int | str]) -> dict[str, Any]:
    idle_keys = ("lane_A", "lane_B", "lane_D", "default", "claimed")
    idle = all(int_count(counts, key) == 0 for key in idle_keys)
    now = datetime.now(timezone.utc)
    blocked_reason_details = []
    for base in (ROOT / "system_v5/ops/lego_scaling", ROOT / "system_v5/ops/wizard_admissions"):
        if not base.exists():
            continue
        for path in sorted(base.glob("*blocked*.json")):
            valid, reason = blocked_reason_valid(path, now=now)
            blocked_reason_details.append({"path": str(path.relative_to(ROOT)), "valid": valid, "reason": reason})
    blocked_reasons = [item["path"] for item in blocked_reason_details if item["valid"]]
    if not idle:
        status = "active_or_queued"
    elif blocked_reasons:
        status = "idle_with_blocked_reason"
    else:
        status = "needs_next_micro_move_or_blocked_reason"
    return {
        "status": status,
        "idle": idle,
        "idle_keys": list(idle_keys),
        "blocked_reason_artifacts": blocked_reasons,
        "blocked_reason_details": blocked_reason_details,
    }


def recent_worker_receipts(now: datetime) -> list[Path]:
    receipts: list[Path] = []
    for base, pattern in WORKER_RECEIPT_GLOBS:
        if base.exists():
            receipts.extend(path for path in base.glob(pattern) if path.is_file())
    cutoff = now - timedelta(hours=24)
    return sorted(path for path in receipts if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= cutoff)


def worker_receipt_check(now: datetime) -> dict[str, Any]:
    receipts = recent_worker_receipts(now)
    if not receipts:
        return {"ok": True, "checked": 0, "receipt_paths": []}
    command = ["python3", "scripts/validate_wizard_worker_receipts.py", "--require-artifacts", *[str(path) for path in receipts]]
    check = run(command)
    check["checked"] = len(receipts)
    check["receipt_paths"] = [rel(path) for path in receipts]
    return check


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-preflight", action="store_true", help="Skip packet/helper subprocess checks.")
    parser.add_argument("--accept-skipped-preflight", action="store_true", help="Allow ok=true when --skip-preflight is used.")
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
        checks["worker_pool_receipts"] = worker_receipt_check(datetime.now(timezone.utc))

    hard_failures = bool(findings)
    hard_failures = hard_failures or any(not check.get("ok") for check in checks.values())
    hard_failures = hard_failures or heartbeat["status"] == "needs_next_micro_move_or_blocked_reason"
    hard_failures = hard_failures or (args.skip_preflight and not args.accept_skipped_preflight)

    report = {
        "ok": not hard_failures,
        "skipped_preflight": args.skip_preflight,
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
