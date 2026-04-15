#!/usr/bin/env python3
"""Read-only summary of the live sim corpus, queue mix, and plan alignment."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import adaptive_controller
import queue_claim


PROBES = adaptive_controller.PROBES
QUEUE = adaptive_controller.QUEUE


def all_sims() -> list[Path]:
    return sorted(
        path for path in PROBES.glob("sim_*.py")
        if path.is_file() and " 2" not in path.name and path.stem not in adaptive_controller.QUEUE_BLACKLIST
    )


def top_families(sim_paths: list[Path], limit: int = 12) -> dict[str, int]:
    counts = Counter(adaptive_controller.sim_family(path.name) for path in sim_paths)
    return dict(counts.most_common(limit))


def top_buckets(sim_paths: list[Path]) -> dict[str, int]:
    counts = Counter(adaptive_controller.plan_bucket(path.name) for path in sim_paths)
    return dict(counts)


def queue_blocked_reasons(limit: int = 8) -> dict[str, int]:
    counts: Counter[str] = Counter()
    blocked = QUEUE / "blocked"
    if blocked.exists():
        for item in blocked.iterdir():
            if not item.is_file():
                continue
            data = adaptive_controller.load_result(item)
            counts[str(data.get("blocked_reason", "unknown"))] += 1
    return dict(counts.most_common(limit))


def next_queue_candidates(lane: str, limit: int = 10) -> list[dict]:
    lane_dir = QUEUE / lane
    if not lane_dir.exists():
        return []
    out: list[dict] = []
    for item in sorted(lane_dir.glob("*.json"), key=queue_claim._claim_order)[:limit]:
        data = adaptive_controller.load_result(item)
        sim_path = str(data.get("sim_path", ""))
        out.append({
            "sim": Path(sim_path).name,
            "priority": data.get("priority") or queue_claim._priority_for_bucket(
                str(data.get("plan_bucket") or queue_claim._plan_bucket_from_sim_path(sim_path))
            ),
            "plan_bucket": data.get("plan_bucket") or queue_claim._plan_bucket_from_sim_path(sim_path),
        })
    return out


def unresolved_sim_paths(sim_paths: list[Path]) -> list[Path]:
    unresolved: list[Path] = []
    for sim in sim_paths:
        result_path = adaptive_controller.RESULTS / f"{sim.stem}_results.json"
        if not result_path.exists():
            unresolved.append(sim)
    return unresolved


def main() -> int:
    state = adaptive_controller.triage_cycle(dry=True)
    integration = adaptive_controller.build_integration_summary(state)
    snapshot = adaptive_controller.build_plane_snapshot(state, integration)
    sims = all_sims()
    never_run = [PROBES / f"{stem}.py" for stem in state.get("never_run", []) if (PROBES / f"{stem}.py").exists()]

    report = {
        "corpus": {
            "total_sims": len(sims),
            "top_families": top_families(sims),
            "top_buckets": top_buckets(sims),
        },
        "triage": snapshot["state_plane"]["triage"],
        "program": snapshot["state_plane"]["program"],
        "next_queue_candidates": {
            "lane_A": next_queue_candidates("lane_A"),
            "lane_B": next_queue_candidates("lane_B"),
        },
        "top_never_run_examples": [path.name for path in never_run[:12]],
        "top_never_run_families": top_families(never_run),
        "top_never_run_buckets": top_buckets(never_run),
        "blocked_reasons": queue_blocked_reasons(),
        "top_failing": state.get("failing", [])[:12],
        "rosetta_candidate_clusters": integration.get("rosetta_candidate_clusters", 0),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
