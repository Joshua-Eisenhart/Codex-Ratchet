"""
ratchet_overseer.py — Post-batch convergence monitor

Shell-backed execution surface for the ratchet-overseer skill. This module
reads the live batch context and appends a structured convergence report
without mutating lower-loop truth surfaces.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _load_recent_reports(path: Path, limit: int = 5) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    recent = [json.loads(line) for line in lines[-limit:]]
    return recent


def _classify_state(
    candidate_count: int,
    target_count: int,
    accept_count: int,
    recent_acceptance_rates: list[float],
) -> tuple[str, str]:
    if candidate_count == 0 or target_count == 0:
        return "STALLED", "PAUSE"
    if accept_count == 0 and len(recent_acceptance_rates) >= 3:
        return "PLATEAU", "ADJUST_PARAMETERS"
    if accept_count > 0 and recent_acceptance_rates:
        prev_avg = sum(recent_acceptance_rates[:-1]) / max(1, len(recent_acceptance_rates) - 1)
        if recent_acceptance_rates[-1] >= prev_avg:
            return "CONVERGING", "CONTINUE"
    return "HEALTHY", "CONTINUE"


def build_convergence_report(
    repo: str,
    batch_id: str,
    candidate_ids: list[str],
    targets: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    outcomes: list[Any],
    batch_structural: list[str],
    skipped_probes: int,
    kernel: Any,
    sim: Any,
) -> dict[str, Any]:
    runtime_dir = Path(repo) / "system_v4" / "runtime_state"
    report_path = runtime_dir / "ratchet_overseer_reports.jsonl"

    accept = [o for o in outcomes if getattr(o, "outcome", "") == "ACCEPT"]
    park = [o for o in outcomes if getattr(o, "outcome", "") == "PARK"]
    reject = [o for o in outcomes if getattr(o, "outcome", "") == "REJECT"]
    total_outcomes = len(outcomes)
    acceptance_rate = len(accept) / total_outcomes if total_outcomes else 0.0

    recent = _load_recent_reports(report_path, limit=4)
    recent_acceptance_rates = [float(r.get("acceptance_rate", 0.0)) for r in recent]
    recent_acceptance_rates.append(acceptance_rate)

    ratchet_state, recommended_action = _classify_state(
        candidate_count=len(candidate_ids),
        target_count=len(targets),
        accept_count=len(accept),
        recent_acceptance_rates=recent_acceptance_rates,
    )

    if len(recent_acceptance_rates) >= 2:
        if recent_acceptance_rates[-1] > recent_acceptance_rates[-2]:
            trend = "improving"
        elif recent_acceptance_rates[-1] < recent_acceptance_rates[-2]:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "batch_id": batch_id,
        "candidate_count": len(candidate_ids),
        "target_count": len(targets),
        "alternative_count": len(alternatives),
        "accept_count": len(accept),
        "park_count": len(park),
        "reject_count": len(reject),
        "acceptance_rate": acceptance_rate,
        "acceptance_rate_trend": trend,
        "sim_structural_count": len(batch_structural),
        "skipped_probe_count": skipped_probes,
        "global_survivor_count": len(getattr(kernel, "survivor_ledger", {})),
        "global_park_count": len(getattr(kernel, "park_set", {})),
        "global_graveyard_count": len(getattr(kernel, "graveyard", [])),
        "global_sim_kill_count": len(getattr(sim, "kill_log", [])),
        "ratchet_state": ratchet_state,
        "recommended_action": recommended_action,
    }
    _append_jsonl(report_path, report)
    return report
