from __future__ import annotations

from pathlib import Path

from system_v4.visualization.batch_reporting import collect_batch_report, collect_multi_batch_report
from system_v4.visualization.inspection import inspect_run_dir
from system_v4.visualization.triage import collect_triage_report


def _collect_batch(roots: list[Path]) -> dict:
    normalized = [Path(root) for root in roots]
    if len(normalized) == 1:
        return collect_batch_report(normalized[0])
    return collect_multi_batch_report(normalized)


def collect_status_report(roots: list[Path]) -> dict:
    batch = _collect_batch(roots)
    triage = collect_triage_report(roots)

    duplicate_groups = []
    for group in batch["duplicate_groups"]:
        duplicate_groups.append({
            "sim_name": group["sim_name"],
            "canonical_run_id": group["canonical_run_id"],
            "canonical_root": group["canonical_root"],
            "canonical_reason": group["canonical_reason"],
            "duplicate_members": [
                member for member in group["members"]
                if (member["run_id"], member["root"]) != (group["canonical_run_id"], group["canonical_root"])
            ],
        })

    best_runs = []
    for sim_name, item in sorted(batch["best_runs_by_sim"].items()):
        inspection = inspect_run_dir(Path(item["root"]) / item["run_id"])
        best_runs.append({
            "sim_name": sim_name,
            "run_id": item["run_id"],
            "root": item["root"],
            "valid": item["valid"],
            "status_label": inspection.get("status_label"),
            "admission_stage": inspection.get("admission_stage"),
            "promotion_target_stage": inspection.get("promotion_target_stage"),
            "claim_state": inspection.get("claim_state"),
            "promotion_status": inspection.get("promotion_status"),
            "eligible_consumers": inspection.get("eligible_consumers", []),
            "blocked_consumers": inspection.get("blocked_consumers", []),
            "promotion_blockers": inspection.get("promotion_blockers", []),
            "projected_path_kind": item["projected_path_kind"],
            "overlays": item["overlays"],
        })

    return {
        "roots": batch["roots"],
        "root_count": batch["root_count"],
        "summary": {
            "run_count": batch["run_count"],
            "valid_count": batch["valid_count"],
            "invalid_count": batch["invalid_count"],
            "best_run_count": len(best_runs),
            "duplicate_group_count": len(duplicate_groups),
            "admission_warning_count": batch.get("admission_warning_count", 0),
            "archive_candidate_count": triage["summary"]["archive_candidate_count"],
            "reexport_candidate_count": triage["summary"]["reexport_candidate_count"],
        },
        "best_runs": best_runs,
        "duplicate_groups": duplicate_groups,
        "admission_warnings": batch.get("admission_warnings", []),
        "archive_candidates": triage["archive_candidates"],
        "reexport_candidates": triage["reexport_candidates"],
    }


def render_status_report(roots: list[Path]) -> str:
    report = collect_status_report(roots)
    lines = [
        f"Roots: {', '.join(report['roots'])}",
        f"Runs: {report['summary']['run_count']} | valid={report['summary']['valid_count']} | invalid={report['summary']['invalid_count']}",
        f"Best Runs: {report['summary']['best_run_count']} | duplicate groups={report['summary']['duplicate_group_count']}",
        f"Admission Warnings: {report['summary']['admission_warning_count']}",
        f"Needs Attention: archive={report['summary']['archive_candidate_count']} | re-export={report['summary']['reexport_candidate_count']}",
    ]

    if report["best_runs"]:
        lines.append("Best Runs:")
        for item in report["best_runs"]:
            projected = item["projected_path_kind"] or "none"
            admission_stage = item.get("admission_stage") or "unknown"
            promotion_target_stage = item.get("promotion_target_stage") or "unknown"
            status_label = item.get("status_label") or "exists"
            lines.append(
                f"{item['sim_name']}: {item['run_id']} [{item['root']}] | "
                f"status={status_label} | claim={item.get('claim_state')} | promotion={item.get('promotion_status')} | "
                f"admission={admission_stage}->{promotion_target_stage} | projected={projected}"
            )
            lines.append(
                f"  consumer_surfaces: eligible={','.join(item.get('eligible_consumers', [])) or '(none)'} | "
                f"blocked={','.join(item.get('blocked_consumers', [])) or '(none)'} | "
                f"promotion_blockers={','.join(item.get('promotion_blockers', [])) or '(none)'}"
            )

    if report["reexport_candidates"]:
        lines.append("Re-export:")
        for item in report["reexport_candidates"]:
            lines.append(
                f"{item['run_id']} [{item['root']}] -> {item['best_run_id']} [{item['best_root']}] | "
                f"reasons={','.join(item['stale_reasons'])}"
            )

    if report["archive_candidates"]:
        lines.append("Archive Candidates:")
        for item in report["archive_candidates"]:
            if "canonical_run_id" in item:
                lines.append(
                    f"{item['run_id']} [{item['root']}] -> duplicate of {item['canonical_run_id']} [{item['canonical_root']}]"
                )
            else:
                lines.append(
                    f"{item['run_id']} [{item['root']}] -> weaker than {item['best_run_id']} [{item['best_root']}] | "
                    f"reasons={','.join(item['stale_reasons'])}"
                )

    if report["admission_warnings"]:
        lines.append("Admission Warnings:")
        for item in report["admission_warnings"]:
            lines.append(
                f"{item['run_id']} [{item['root']}] | stage={item['admission_stage']} | missing_lower_stages={','.join(item['missing_lower_stages'])}"
            )

    if report["duplicate_groups"]:
        lines.append("Duplicates:")
        for item in report["duplicate_groups"]:
            duplicates = ", ".join(
                f"{member['run_id']} [{member['root']}]"
                for member in item["duplicate_members"]
            ) or "(none)"
            lines.append(
                f"{item['sim_name']}: canonical={item['canonical_run_id']} [{item['canonical_root']}] | duplicates={duplicates}"
            )

    return "\n".join(lines)
