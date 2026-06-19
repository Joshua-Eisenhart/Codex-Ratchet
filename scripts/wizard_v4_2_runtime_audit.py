#!/usr/bin/env python3
"""Audit live Wizard v4.2 runtime guardrails."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import adaptive_controller
import lint_sim_contract


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
BYPASS_RECEIPT_GLOB = ROOT / "system_v5/ops/wizard_admissions"
BYPASS_SENTINEL = ROOT / "system_v5/ops/.allow_admission_bypass_recovery"
DEFAULT_CONTRACT_LINT_TIMEOUT_SEC = 2.0

OPS_REPORTS = [
    ROOT / "system_v5/ops/blocked_reason_breakdown.json",
    ROOT / "system_v5/ops/c1_classification_proposals.json",
    ROOT / "system_v5/ops/c4_divergence_log_proposals.json",
    ROOT / "system_v5/ops/c6_loadbearing_report.json",
    ROOT / "system_v5/ops/c6_loadbearing_decision_table.json",
    ROOT / "system_v5/ops/proposal_apply_preview.json",
    ROOT / "system_v5/ops/runner_taxonomy_unknowns.json",
    ROOT / "system_v5/ops/never_run_cohorts.json",
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
        return {"_valid": 0, "error": check["stderr"] or check["stdout"] or "queue count command failed"}
    try:
        parsed = json.loads(str(check["stdout"]))
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        counts = {
            str(key): int(value) if isinstance(value, int) else str(value)
            for key, value in parsed.items()
        }
        counts["_valid"] = 1
        return counts
    counts: dict[str, int | str] = {}
    for line in str(check["stdout"]).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        try:
            counts[key.strip()] = int(value.strip())
        except ValueError:
            counts[key.strip()] = value.strip()
    counts["_valid"] = 1 if counts else 0
    if not counts:
        counts["error"] = "queue count output was not parseable"
    return counts


def int_count(counts: dict[str, int | str], key: str) -> int:
    value = counts.get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def iter_jsonish_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted(path for path in base.iterdir() if path.is_file() and ".json" in path.name)


def newest_mtime(paths: list[Path]) -> datetime | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) for path in existing)


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
    queue_counts_valid = int_count(counts, "_valid") == 1
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
    blocked_count = int_count(counts, "blocked")
    runner_idle_with_backlog = idle and blocked_count > 0
    if not queue_counts_valid:
        status = "queue_counts_invalid"
    elif runner_idle_with_backlog:
        status = "runner_idle_with_backlog"
    elif not idle:
        status = "active_or_queued"
    elif blocked_reasons:
        status = "idle_with_blocked_reason"
    else:
        status = "needs_next_micro_move_or_blocked_reason"
    return {
        "status": status,
        "queue_counts_valid": queue_counts_valid,
        "queue_counts_error": counts.get("error"),
        "idle": idle,
        "idle_keys": list(idle_keys),
        "blocked_count": blocked_count,
        "runner_idle_with_backlog": runner_idle_with_backlog,
        "dominant_blocked_reason": dominant_blocked_reason(),
        "blocked_reason_artifacts": blocked_reasons,
        "blocked_reason_details": blocked_reason_details,
    }


def dominant_blocked_reason() -> dict[str, Any] | None:
    blocked_dir = ROOT / "system_v4/probes/a2_state/queue/blocked"
    counts: dict[str, int] = {}
    total = 0
    for path in iter_jsonish_files(blocked_dir):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        reason = str(data.get("blocked_reason") or "unknown")
        counts[reason] = counts.get(reason, 0) + 1
        total += 1
    if not counts:
        return None
    reason, count = max(counts.items(), key=lambda item: item[1])
    return {"reason": reason, "count": count, "total": total, "percent": round((count / total) * 100, 1)}


def reports_freshness(now: datetime) -> dict[str, Any]:
    source_dirs = [
        ROOT / "system_v4/probes",
        ROOT / "system_v4/probes/a2_state/queue/blocked",
        ROOT / "system_v4/probes/a2_state/queue/lane_A",
        ROOT / "system_v4/probes/a2_state/queue/lane_B",
        ROOT / "system_v4/probes/a2_state/queue/claimed",
    ]
    source_files: list[Path] = []
    for base in source_dirs:
        if not base.exists():
            continue
        if base.name == "probes":
            source_files.extend(path for path in base.glob("sim_*.py") if path.is_file())
        else:
            source_files.extend(iter_jsonish_files(base))
    newest_source = newest_mtime(source_files)
    source_missing = newest_source is None
    reports = []
    stale = False
    missing = False
    for path in OPS_REPORTS:
        exists = path.exists()
        report_mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) if exists else None
        is_stale = bool(exists and newest_source and report_mtime and report_mtime < newest_source)
        missing = missing or not exists
        stale = stale or is_stale
        reports.append(
            {
                "path": rel(path),
                "exists": exists,
                "mtime": report_mtime.isoformat() if report_mtime else None,
                "stale_vs_newest_source": is_stale,
            }
        )
    return {
        "ok": not stale and not missing and not source_missing,
        "freshness_rule": "each report mtime must be newer than the newest sim source or live queue JSON-like record",
        "timestamp_source": "filesystem_mtime_utc",
        "generated_at": now.isoformat(),
        "source_file_count": len(source_files),
        "newest_source_mtime": newest_source.isoformat() if newest_source else None,
        "source_missing": source_missing,
        "missing": missing,
        "stale": stale,
        "reports": reports,
    }


def contract_lint_ratchet_counts() -> dict[str, int] | None:
    path = ROOT / "system_v5/ops/state/contract_lint_ratchet.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    try:
        return {
            "violation_total": int(data.get("violation_total") or 0),
            "sims_with_violations": int(data.get("sims_with_violations") or 0),
        }
    except (TypeError, ValueError):
        return None


def contract_lint_summary(*, max_seconds: float = DEFAULT_CONTRACT_LINT_TIMEOUT_SEC) -> dict[str, Any]:
    paths = [
        path
        for path in sorted(adaptive_controller.PROBES.glob("sim_*.py"))
        if path.is_file() and " 2" not in path.name
    ]
    ratchet_counts = contract_lint_ratchet_counts()
    command = ["python3", "scripts/lint_sim_contract.py"]
    timeout = max_seconds if max_seconds > 0 else None
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "closeout_check": "python3 scripts/lint_sim_contract.py",
            "command": command,
            "complete": False,
            "timed_out": True,
            "timeout_seconds": max_seconds,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "sim_file_total": len(paths),
            "checked": 0,
            "unchecked": len(paths),
            "violation_total": ratchet_counts["violation_total"] if ratchet_counts else 0,
            "sims_with_violations": ratchet_counts["sims_with_violations"] if ratchet_counts else 0,
            "violations_by_type": {},
            "count_source": "contract_lint_ratchet_timeout_fallback" if ratchet_counts else "timeout_no_count_source",
            "error": "contract lint exceeded runtime-audit time budget",
        }
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "closeout_check": "python3 scripts/lint_sim_contract.py",
            "command": command,
            "complete": True,
            "timed_out": False,
            "timeout_seconds": max_seconds,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "sim_file_total": len(paths),
            "checked": 0,
            "unchecked": len(paths),
            "violation_total": ratchet_counts["violation_total"] if ratchet_counts else 0,
            "sims_with_violations": ratchet_counts["sims_with_violations"] if ratchet_counts else 0,
            "violations_by_type": {},
            "count_source": "contract_lint_ratchet_parse_fallback" if ratchet_counts else "parse_failure_no_count_source",
            "error": result.stderr.strip() or result.stdout.strip() or "contract lint output was not JSON",
        }
    violation_total = int(parsed.get("violation_total") or 0)
    checked = int(parsed.get("checked") or 0)
    return {
        "ok": result.returncode == 0 and violation_total == 0,
        "closeout_check": "python3 scripts/lint_sim_contract.py",
        "command": command,
        "complete": True,
        "timed_out": False,
        "timeout_seconds": max_seconds,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "sim_file_total": len(paths),
        "checked": checked,
        "unchecked": max(0, len(paths) - checked),
        "violation_total": violation_total,
        "sims_with_violations": int(parsed.get("sims_with_violations") or 0),
        "violations_by_type": dict(parsed.get("violations_by_type") or {}),
        "top_offenders": list(parsed.get("top_offenders") or [])[:10],
        "count_source": "live_contract_lint",
    }


def never_run_summary() -> dict[str, Any]:
    path = ROOT / "system_v5/ops/never_run_cohorts.json"
    if not path.exists():
        return {"ok": False, "path": rel(path), "error": "missing_report"}
    data = json.loads(path.read_text())
    total = int(data.get("never_run_count") or 0)
    return {
        "ok": total == 0,
        "closeout_check": "python3 scripts/never_run_cohort_report.py",
        "path": rel(path),
        "never_run_total": total,
        "top_families": dict(list(dict(data.get("family_counts") or {}).items())[:10]),
    }


def taxonomy_allowlist_summary(now: datetime) -> dict[str, Any]:
    unknown_path = ROOT / "system_v5/ops/runner_taxonomy_unknowns.json"
    allowlist_path = ROOT / "system_v5/docs/RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md"
    if not unknown_path.exists() or not allowlist_path.exists():
        return {"ok": False, "error": "missing_unknown_report_or_allowlist"}
    report = json.loads(unknown_path.read_text())
    text = allowlist_path.read_text()
    rows = [str(row.get("sim") or "") for row in report.get("rows", []) if isinstance(row, dict)]
    allowlisted = [row for row in rows if row and row in text]
    review_match = re.search(r"review_by:\s*(\d{4}-\d{2}-\d{2})", text)
    review_by = review_match.group(1) if review_match else None
    review_due = False
    if review_by:
        review_due = datetime.fromisoformat(review_by).replace(tzinfo=timezone.utc) < now
    drift = len(rows) - len(allowlisted)
    return {
        "ok": drift == 0 and not review_due,
        "closeout_check": "python3 scripts/runner_taxonomy_unknowns_report.py",
        "path": rel(allowlist_path),
        "unknown_count": len(rows),
        "allowlisted_count": len(allowlisted),
        "drift": drift,
        "review_by": review_by,
        "review_due": review_due,
    }


def dominant_blocked_reason_next_check(heartbeat: dict[str, Any]) -> dict[str, str] | None:
    dominant = heartbeat.get("dominant_blocked_reason")
    if not isinstance(dominant, dict):
        return None
    reason = dominant.get("reason")
    if reason == "wizard_admission_blocked":
        return {
            "owner_surface": "system_v5/ops/blocked_reason_breakdown.json",
            "next_check": "review wizard_admission_blocked rows by contract_subreasons before queue admission",
        }
    if reason == "stage_gate_blocked":
        return {
            "owner_surface": "system_v5/docs/LEGO_SIM_CONTRACT.md",
            "next_check": "verify exact stage prerequisite receipts before requeue",
        }
    return {
        "owner_surface": "system_v5/ops/blocked_reason_breakdown.json",
        "next_check": "inspect dominant blocked reason rows and record one admissible next step",
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


def recent_admission_bypass_receipts(now: datetime) -> list[str]:
    if not BYPASS_RECEIPT_GLOB.exists():
        return []
    cutoff = now - timedelta(hours=24)
    return [
        rel(path)
        for path in sorted(BYPASS_RECEIPT_GLOB.glob("bypass_*.json"))
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= cutoff
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-preflight", action="store_true", help="Skip packet/helper subprocess checks.")
    parser.add_argument("--accept-skipped-preflight", action="store_true", help="Allow ok=true when --skip-preflight is used.")
    parser.add_argument(
        "--contract-lint-timeout-sec",
        type=float,
        default=DEFAULT_CONTRACT_LINT_TIMEOUT_SEC,
        help="Maximum seconds to spend summarizing sim contract lint before reporting a bounded guard failure.",
    )
    args = parser.parse_args(argv)

    findings = scan_live_surfaces()
    counts = queue_counts()
    heartbeat = heartbeat_status(counts)
    checks: dict[str, Any] = {}

    now = datetime.now(timezone.utc)
    checks["worker_pool_receipts"] = worker_receipt_check(now)
    checks["ops_reports_freshness"] = reports_freshness(now)
    checks["contract_lint_summary"] = contract_lint_summary(max_seconds=args.contract_lint_timeout_sec)
    checks["never_run_summary"] = never_run_summary()
    checks["taxonomy_unknown_allowlist"] = taxonomy_allowlist_summary(now)
    heartbeat["dominant_blocked_reason_next_check"] = dominant_blocked_reason_next_check(heartbeat)

    if not args.skip_preflight:
        checks["packet_conformance"] = run(
            ["python3", str(HOME / "wiki/wizard/packet-v4-2-current/conformance/validate_v4_2_packet.py")]
        )
        checks["helper_processes"] = run(["python3", "scripts/helper_process_audit.py", "--strict"])

    recent_bypass_receipts = recent_admission_bypass_receipts(now)
    bypass_sentinel_present = BYPASS_SENTINEL.exists()
    worker_pool_receipts_warning = None
    if checks.get("worker_pool_receipts", {}).get("checked") == 0:
        worker_pool_receipts_warning = "no_recent_receipts_present_topology_counts_not_independently_validated"

    hard_failures = bool(findings)
    hard_failures = hard_failures or any(not check.get("ok") for check in checks.values())
    hard_failures = hard_failures or heartbeat["status"] in {"needs_next_micro_move_or_blocked_reason", "runner_idle_with_backlog"}
    hard_failures = hard_failures or (args.skip_preflight and not args.accept_skipped_preflight)
    hard_failures = hard_failures or bypass_sentinel_present

    report = {
        "ok": not hard_failures,
        "skipped_preflight": args.skip_preflight,
        "bypass_sentinel_present": bypass_sentinel_present,
        "bypass_sentinel_path": rel(BYPASS_SENTINEL),
        "recent_admission_bypass_receipts": recent_bypass_receipts,
        "worker_pool_receipts_warning": worker_pool_receipts_warning,
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
