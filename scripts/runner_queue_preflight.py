#!/usr/bin/env python3
"""Fail-closed queue preflight before launching parallel sim runners."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


CLAIM_RECONCILE_SAFETY_SECONDS = 72 * 60 * 60
LATE_STAGE_RE = re.compile(
    r"(tier_d|boundary_flux|bridge|coupling|pairwise|coexistence|rho_ab|phi0|kernel|"
    r"emergence|axis|axis0|bipartite|partial_trace|entanglement|mutual_information|"
    r"mutual_info|coherent_information|coherent_info|concurrence|negativity|schmidt|"
    r"entropy|capacity|capacities|carnot|szilard|landauer|thermo|engine|qit|nonclassical)",
    re.I,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_gate(root: Path) -> dict[str, Any]:
    path = root / "system_v5" / "ops" / "stage_gate.json"
    if not path.exists():
        return {"active_stage": None, "allow_default_queue_late_stage": False, "allow_tier_d_launch": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "active_stage": payload.get("active_stage"),
        "allow_default_queue_late_stage": payload.get("allow_default_queue_late_stage") is True,
        "allow_tier_d_launch": payload.get("allow_tier_d_launch") is True,
    }


def rows(path: Path) -> list[str]:
    if not path.exists():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if item and not item.startswith("#"):
            out.append(item)
    return out


def claim_for_row(row: str) -> str | None:
    low = row.lower()
    stem = Path(low).stem
    if stem.startswith("classical_baseline_"):
        return None
    if "tier_d" in low or "boundary_flux" in low:
        return "tier_d"
    if any(token in low for token in ("bridge", "coupling", "pairwise", "coexistence", "rho_ab", "phi0", "kernel", "emergence", "engine", "qit", "nonclassical")):
        return "scientific_coupling"
    if "axis" in low:
        return "axis"
    if LATE_STAGE_RE.search(low):
        return "default_late_stage"
    return None


def _direct_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(item for item in path.iterdir() if item.is_file())


def _queue_files(path: Path) -> list[Path]:
    return [item for item in _direct_files(path) if item.match("*.json*")]


def _junk_files(path: Path) -> list[Path]:
    return [item for item in _direct_files(path) if not item.match("*.json*")]


def _utc_iso(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, UTC).isoformat()


def _as_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _load_claim_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _pid_from_claim_name(path: Path) -> int | None:
    if ".json." not in path.name:
        return None
    tail = path.name.split(".json.", 1)[1]
    return _as_int(tail.split(".", 1)[0])


def _pid_alive(pid: int | None) -> bool | None:
    if pid is None or pid <= 0:
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def claimed_queue_safety_summary(
    claimed_files: list[Path],
    *,
    root: Path,
    now: float | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    now = time.time() if now is None else now
    records: list[dict[str, Any]] = []
    claim_timestamps: list[float] = []
    for path in claimed_files:
        payload = _load_claim_payload(path)
        stat = path.stat()
        claimed_at = _as_float(payload.get("claimed_at"))
        timestamp_source = "payload.claimed_at" if claimed_at is not None else "mtime"
        timestamp = claimed_at if claimed_at is not None else stat.st_mtime
        claim_timestamps.append(timestamp)
        pid = _as_int(payload.get("claimed_pid"))
        if pid is None:
            pid = _pid_from_claim_name(path)
        records.append(
            {
                "path": str(path.relative_to(root)),
                "claimed_at_utc": _utc_iso(timestamp),
                "age_seconds": max(0.0, now - timestamp),
                "timestamp_source": timestamp_source,
                "pid": pid,
                "pid_alive": _pid_alive(pid),
            }
        )

    records.sort(key=lambda row: float(row["age_seconds"]), reverse=True)
    oldest = min(claim_timestamps) if claim_timestamps else None
    newest = max(claim_timestamps) if claim_timestamps else None
    safe_after = None if newest is None else newest + CLAIM_RECONCILE_SAFETY_SECONDS
    pid_values = [record.get("pid_alive") for record in records]
    return {
        "count": len(records),
        "safety_window_seconds": CLAIM_RECONCILE_SAFETY_SECONDS,
        "oldest_claimed_at_utc": _utc_iso(oldest),
        "newest_claimed_at_utc": _utc_iso(newest),
        "oldest_age_seconds": (max(float(record["age_seconds"]) for record in records) if records else None),
        "newest_age_seconds": (min(float(record["age_seconds"]) for record in records) if records else None),
        "safe_to_reconcile_after_utc": _utc_iso(safe_after),
        "seconds_until_safe_to_reconcile": None if safe_after is None else max(0.0, safe_after - now),
        "all_claims_past_safety_window": safe_after is not None and now >= safe_after,
        "pid_summary": {
            "with_pid": sum(1 for record in records if record.get("pid") is not None),
            "alive": sum(1 for value in pid_values if value is True),
            "not_alive": sum(1 for value in pid_values if value is False),
            "unknown": sum(1 for value in pid_values if value is None),
        },
        "oldest_samples": records[:limit],
    }


def atomic_queue_counts(root: Path) -> dict[str, int]:
    queue_root = root / "system_v4" / "probes" / "a2_state" / "queue"
    return {
        "claimed": len(_queue_files(queue_root / "claimed")),
        "blocked": len(_queue_files(queue_root / "blocked")),
        "done": len(_queue_files(queue_root / "done")),
    }


def atomic_queue_junk_counts(root: Path) -> dict[str, int]:
    queue_root = root / "system_v4" / "probes" / "a2_state" / "queue"
    return {
        "root": len(_junk_files(queue_root)),
        "lane_A": len(_junk_files(queue_root / "lane_A")),
        "lane_B": len(_junk_files(queue_root / "lane_B")),
        "claimed": len(_junk_files(queue_root / "claimed")),
        "blocked": len(_junk_files(queue_root / "blocked")),
        "done": len(_junk_files(queue_root / "done")),
    }


def audit(root: Path | None = None, *, now: float | None = None) -> dict[str, Any]:
    root = root or repo_root()
    ops = root / "system_v5" / "ops"
    gate = load_gate(root)
    atomics = atomic_queue_counts(root)
    atomic_junk = atomic_queue_junk_counts(root)
    findings: list[dict[str, Any]] = []

    if atomics["claimed"]:
        queue_root = root / "system_v4" / "probes" / "a2_state" / "queue"
        claimed_files = _queue_files(queue_root / "claimed")
        findings.append(
            {
                "kind": "atomic_claimed_queue_not_empty",
                "queue": "system_v4/probes/a2_state/queue/claimed",
                "count": atomics["claimed"],
                "sample": [
                    str(path.relative_to(root))
                    for path in claimed_files[:5]
                ],
                "claim_safety": claimed_queue_safety_summary(claimed_files, root=root, now=now),
            }
        )

    blocked_default = 0
    if not gate.get("allow_default_queue_late_stage"):
        for row in rows(ops / "queue_default.txt"):
            claim = claim_for_row(row)
            if claim:
                blocked_default += 1
                findings.append(
                    {
                        "kind": "default_queue_late_stage_blocked",
                        "queue": "system_v5/ops/queue_default.txt",
                        "row": row,
                        "claim": claim,
                    }
                )

    blocked_priority = 0
    for rel in ("queue_tier_a.txt", "queue_tier_b.txt"):
        queue = ops / rel
        for row in rows(queue):
            claim = claim_for_row(row)
            if claim in {"scientific_coupling", "axis", "tier_d", "default_late_stage"}:
                blocked_priority += 1
                findings.append(
                    {
                        "kind": "priority_queue_stage_gate_blocked",
                        "queue": f"system_v5/ops/{rel}",
                        "row": row,
                        "claim": claim,
                    }
                )

    return {
        "all_pass": not findings,
        "active_stage": gate.get("active_stage"),
        "atomic_queue_counts": atomics,
        "atomic_queue_junk_counts": atomic_junk,
        "blocked_default_queue_count": blocked_default,
        "blocked_stage_gate_queue_count": blocked_priority,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root()))
    args = parser.parse_args()
    report = audit(Path(args.repo_root))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
