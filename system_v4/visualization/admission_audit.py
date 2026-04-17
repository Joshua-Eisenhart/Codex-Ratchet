from __future__ import annotations

from pathlib import Path

from system_v4.visualization.inspection import inspect_run_dir
from system_v4.visualization.schema_v1 import ADMISSION_STAGE_LABELS


def _required_lower_stages(stage: str) -> list[str]:
    if stage not in ADMISSION_STAGE_LABELS:
        return []
    index = ADMISSION_STAGE_LABELS.index(stage)
    return list(ADMISSION_STAGE_LABELS[:index])


def audit_run_admission(target_run: Path, candidate_runs: list[Path]) -> dict:
    target = inspect_run_dir(Path(target_run))
    declared_prereqs = target.get("lane_admission", {}).get("prerequisite_lanes")
    if isinstance(declared_prereqs, list) and declared_prereqs:
        required_stages = list(declared_prereqs)
    else:
        required_stages = _required_lower_stages(target.get("admission_stage"))
    supporting_runs = []

    for run_dir in candidate_runs:
        run_dir = Path(run_dir)
        if run_dir == Path(target_run):
            continue
        try:
            report = inspect_run_dir(run_dir)
        except Exception:
            continue
        if not report.get("validation_ok"):
            continue
        if report.get("admission_stage") in required_stages:
            supporting_runs.append({
                "run_id": report.get("run_id"),
                "run_dir": str(run_dir),
                "admission_stage": report.get("admission_stage"),
                "status_label": report.get("status_label"),
                "probe_family": report.get("probe_family"),
            })

    covered = {item["admission_stage"] for item in supporting_runs}
    missing = [stage for stage in required_stages if stage not in covered]
    ok = not missing
    return {
        "run_id": target.get("run_id"),
        "probe_family": target.get("probe_family"),
        "admission_stage": target.get("admission_stage"),
        "required_lower_stages": required_stages,
        "covered_lower_stages": sorted(covered),
        "missing_lower_stages": missing,
        "supporting_runs": supporting_runs,
        "ok": ok,
    }


def audit_roots_admission(roots: list[Path]) -> dict:
    run_dirs: list[Path] = []
    for root in roots:
        run_dirs.extend(sorted(Path(root).rglob("run_manifest.json")))
    actual_run_dirs = sorted({path.parent for path in run_dirs})
    audits = [audit_run_admission(run_dir, actual_run_dirs) for run_dir in actual_run_dirs]
    return {
        "run_count": len(audits),
        "ok_count": sum(1 for item in audits if item["ok"]),
        "warning_count": sum(1 for item in audits if not item["ok"]),
        "audits": audits,
    }
