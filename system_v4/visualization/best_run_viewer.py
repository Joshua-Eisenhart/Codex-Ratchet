from __future__ import annotations

import json
from pathlib import Path

from system_v4.visualization.batch_reporting import collect_batch_report, collect_multi_batch_report
from system_v4.visualization.consumer_admission import evaluate_consumer_admission
from system_v4.visualization.viewer_launcher import (
    collect_viewer_launch,
    launch_viewer,
    render_viewer_launch,
    DEFAULT_VIEWER_PYTHON,
)


def _collect_batch(roots: list[Path]) -> dict:
    normalized = [Path(root) for root in roots]
    if len(normalized) == 1:
        return collect_batch_report(normalized[0])
    return collect_multi_batch_report(normalized)


def _resolve_best_run_for_consumer(report: dict, sim_name: str, consumer: str) -> dict | None:
    candidates = [item for item in report["runs"] if item["sim_name"] == sim_name]
    admitted_candidates = []
    blocked_candidates = []
    for item in candidates:
        admission = evaluate_consumer_admission(item, consumer)
        enriched = dict(item)
        enriched["consumer_admission"] = admission
        if admission["admitted"]:
            admitted_candidates.append(enriched)
        else:
            blocked_candidates.append(enriched)

    if admitted_candidates:
        best = admitted_candidates[0]
        return {
            "run_id": best["run_id"],
            "root": best["root"],
            "score": best["score"],
            "valid": best["valid"],
            "projected_path_kind": best["projected_path_kind"],
            "overlays": best["overlays"],
            "consumer_admission": best["consumer_admission"],
            "blocked_candidates": [
                {
                    "run_id": item["run_id"],
                    "root": item["root"],
                    "reasons": item["consumer_admission"]["reasons"],
                }
                for item in blocked_candidates
            ],
        }
    return None


def resolve_best_run_dir(roots: list[Path], sim_name: str, *, consumer: str | None = None) -> dict:
    report = _collect_batch(roots)
    best = _resolve_best_run_for_consumer(report, sim_name, consumer) if consumer is not None else report["best_runs_by_sim"].get(sim_name)
    if best is None:
        available = sorted({item["sim_name"] for item in report["runs"]})
        if consumer is not None:
            matching = [item for item in report["runs"] if item["sim_name"] == sim_name]
            if matching:
                blocked = []
                for item in matching:
                    admission = evaluate_consumer_admission(item, consumer)
                    blocked.append(f"{item['run_id']}: {','.join(admission['reasons']) or 'blocked'}")
                raise ValueError(
                    f"sim_name {sim_name!r} has no admitted run for consumer {consumer!r}. "
                    f"Blocked candidates: {'; '.join(blocked)}"
                )
        consumer_suffix = f" for consumer {consumer!r}" if consumer is not None else ""
        raise ValueError(
            f"sim_name {sim_name!r}{consumer_suffix} not found in current roots. "
            f"Available: {', '.join(available) if available else '(none)'}"
        )

    run_dir = Path(best["root"]) / best["run_id"]
    return {
        "roots": report["roots"],
        "root_count": report["root_count"],
        "sim_name": sim_name,
        "run_id": best["run_id"],
        "root": best["root"],
        "run_dir": str(run_dir),
        "score": best["score"],
        "valid": best["valid"],
        "projected_path_kind": best["projected_path_kind"],
        "overlays": best["overlays"],
        "consumer": consumer,
        "consumer_admission": best.get("consumer_admission"),
        "blocked_candidates": best.get("blocked_candidates", []),
    }


def collect_best_viewer_launch(
    roots: list[Path],
    sim_name: str,
    *,
    consumer: str | None = None,
    off_screen_smoke: bool = False,
    python_executable: Path | None = DEFAULT_VIEWER_PYTHON,
) -> dict:
    best = resolve_best_run_dir(roots, sim_name, consumer=consumer)
    launch = collect_viewer_launch(
        Path(best["run_dir"]),
        consumer=consumer,
        off_screen_smoke=off_screen_smoke,
        python_executable=python_executable,
    )
    return {
        "best_run": best,
        "launch": launch,
    }


def render_best_viewer_launch(
    roots: list[Path],
    sim_name: str,
    *,
    consumer: str | None = None,
    off_screen_smoke: bool = False,
    python_executable: Path | None = DEFAULT_VIEWER_PYTHON,
) -> str:
    report = collect_best_viewer_launch(
        roots,
        sim_name,
        consumer=consumer,
        off_screen_smoke=off_screen_smoke,
        python_executable=python_executable,
    )
    best = report["best_run"]
    launch = report["launch"]
    return "\n".join([
        f"Sim: {best['sim_name']}",
        f"Best Run: {best['run_id']}",
        f"Run Dir: {best['run_dir']}",
        f"Consumer: {best['consumer'] or '(none)'}",
        f"Claim Ceiling: {launch.get('status_label', 'exists')}",
        f"Admission Stage: {launch.get('admission_stage')}",
        f"Promotion Target Stage: {launch.get('promotion_target_stage')}",
        f"Promotion Status: {launch.get('promotion_status')}",
        f"Consumer Decision: {launch['consumer_admission']['decision']}",
        f"Promotion Blockers: {', '.join(launch.get('promotion_blockers', [])) or '(none)'}",
        f"Python: {launch['python_executable']}",
        f"Off Screen Smoke: {launch['off_screen_smoke']}",
        f"Command: {' '.join(launch['command'])}",
    ])


def launch_best_viewer(
    roots: list[Path],
    sim_name: str,
    *,
    consumer: str | None = None,
    off_screen_smoke: bool = False,
    dry_run: bool = False,
    python_executable: Path | None = DEFAULT_VIEWER_PYTHON,
) -> dict:
    best = resolve_best_run_dir(roots, sim_name, consumer=consumer)
    result = launch_viewer(
        Path(best["run_dir"]),
        consumer=consumer,
        off_screen_smoke=off_screen_smoke,
        dry_run=dry_run,
        python_executable=python_executable,
    )
    return {
        "best_run": best,
        "launch_result": result,
    }


if __name__ == "__main__":
    import sys

    payload = collect_best_viewer_launch([Path(arg) for arg in sys.argv[2:]], sys.argv[1], off_screen_smoke=True)
    print(json.dumps(payload, indent=2))
