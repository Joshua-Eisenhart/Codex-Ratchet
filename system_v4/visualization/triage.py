from __future__ import annotations

from pathlib import Path

from system_v4.visualization.batch_reporting import collect_batch_report, collect_multi_batch_report


def _collect_report(roots: list[Path]) -> dict:
    normalized = [Path(root) for root in roots]
    if len(normalized) == 1:
        return collect_batch_report(normalized[0])
    return collect_multi_batch_report(normalized)


def collect_triage_report(roots: list[Path]) -> dict:
    report = _collect_report(roots)

    keep_runs: list[dict] = []
    archive_candidates: list[dict] = []
    reexport_candidates: list[dict] = []
    keep_seen: set[tuple[str, str]] = set()
    replacement_available: set[tuple[str, str, str]] = set()

    for sim_name, item in report["best_runs_by_sim"].items():
        keep_runs.append({
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": sim_name,
            "reason": "best_run_for_sim_family",
        })
        keep_seen.add((item["root"], item["run_id"]))

    duplicate_member_keys: set[tuple[str, str]] = set()
    for group in report["duplicate_groups"]:
        canonical_key = (group["canonical_root"], group["canonical_run_id"])
        replacement_available.add((group["sim_name"], group["canonical_run_id"], group["canonical_root"]))
        if canonical_key not in keep_seen:
            keep_runs.append({
                "run_id": group["canonical_run_id"],
                "root": group["canonical_root"],
                "sim_name": group["sim_name"],
                "reason": "canonical_duplicate_survivor",
            })
            keep_seen.add(canonical_key)

        for member in group["members"]:
            member_key = (member["root"], member["run_id"])
            duplicate_member_keys.add(member_key)
            if member_key == canonical_key:
                continue
            archive_candidates.append({
                "run_id": member["run_id"],
                "root": member["root"],
                "sim_name": group["sim_name"],
                "reason": "duplicate_of_canonical",
                "canonical_run_id": group["canonical_run_id"],
                "canonical_root": group["canonical_root"],
                "canonical_reason": group["canonical_reason"],
            })

    for item in report["stale_candidates"]:
        key = (item["root"], item["run_id"])
        if key in duplicate_member_keys:
            continue
        best_key = (item["sim_name"], item["best_run_id"], item["best_root"])
        invalid_needs_refresh = (
            "invalid" in item["reasons"]
            or "missing_projected_path" in item["reasons"]
            or "missing_projected_frame_point" in item["reasons"]
        )
        if invalid_needs_refresh and best_key not in replacement_available:
            reexport_candidates.append({
                "run_id": item["run_id"],
                "root": item["root"],
                "sim_name": item["sim_name"],
                "reason": "re_export_candidate",
                "stale_reasons": item["reasons"],
                "best_run_id": item["best_run_id"],
                "best_root": item["best_root"],
            })
        else:
            archive_candidates.append({
                "run_id": item["run_id"],
                "root": item["root"],
                "sim_name": item["sim_name"],
                "reason": "stale_weaker_sibling" if not invalid_needs_refresh else "superseded_invalid_run",
                "stale_reasons": item["reasons"],
                "best_run_id": item["best_run_id"],
                "best_root": item["best_root"],
            })

    return {
        "roots": report["roots"],
        "root_count": report["root_count"],
        "summary": {
            "run_count": report["run_count"],
            "valid_count": report["valid_count"],
            "invalid_count": report["invalid_count"],
            "duplicate_group_count": len(report["duplicate_groups"]),
            "keep_count": len(keep_runs),
            "archive_candidate_count": len(archive_candidates),
            "reexport_candidate_count": len(reexport_candidates),
        },
        "keep_runs": keep_runs,
        "archive_candidates": archive_candidates,
        "reexport_candidates": reexport_candidates,
    }


def render_triage_report(roots: list[Path]) -> str:
    report = collect_triage_report(roots)
    lines = [
        f"Roots: {', '.join(report['roots'])}",
        f"Runs: {report['summary']['run_count']}",
        f"Keep: {report['summary']['keep_count']}",
        f"Archive Candidates: {report['summary']['archive_candidate_count']}",
        f"Re-export Candidates: {report['summary']['reexport_candidate_count']}",
    ]

    if report["keep_runs"]:
        lines.append("Keep:")
        for item in report["keep_runs"]:
            lines.append(
                f"{item['run_id']} [{item['root']}] | {item['sim_name']} | reason={item['reason']}"
            )

    if report["archive_candidates"]:
        lines.append("Archive Candidates:")
        for item in report["archive_candidates"]:
            extra = ""
            if "canonical_run_id" in item:
                extra = f" | canonical={item['canonical_run_id']} [{item['canonical_root']}]"
            elif "best_run_id" in item:
                extra = f" | stronger={item['best_run_id']} [{item['best_root']}]"
            lines.append(
                f"{item['run_id']} [{item['root']}] | {item['sim_name']} | reason={item['reason']}{extra}"
            )

    if report["reexport_candidates"]:
        lines.append("Re-export Candidates:")
        for item in report["reexport_candidates"]:
            lines.append(
                f"{item['run_id']} [{item['root']}] | {item['sim_name']} | "
                f"reasons={','.join(item['stale_reasons'])} | target={item['best_run_id']} [{item['best_root']}]"
            )

    return "\n".join(lines)
