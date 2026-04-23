from __future__ import annotations

from pathlib import Path

from system_v4.visualization.status import collect_status_report
from system_v4.visualization.triage import collect_triage_report


def collect_action_plan(roots: list[Path]) -> dict:
    triage = collect_triage_report(roots)
    status = collect_status_report(roots)

    keep_canonical: list[dict] = []
    for item in triage["keep_runs"]:
        keep_canonical.append({
            "priority": "keep",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "reason": item["reason"],
        })

    do_now: list[dict] = []
    for item in triage["reexport_candidates"]:
        do_now.append({
            "priority": "now",
            "action": "re_export",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "reason": item["reason"],
            "stale_reasons": item["stale_reasons"],
            "target_run_id": item["best_run_id"],
            "target_root": item["best_root"],
        })

    do_later: list[dict] = []
    for item in triage["archive_candidates"]:
        action = {
            "priority": "later",
            "action": "archive_candidate",
            "run_id": item["run_id"],
            "root": item["root"],
            "sim_name": item["sim_name"],
            "reason": item["reason"],
        }
        if "canonical_run_id" in item:
            action["target_run_id"] = item["canonical_run_id"]
            action["target_root"] = item["canonical_root"]
            action["target_reason"] = item["canonical_reason"]
        if "best_run_id" in item:
            action["target_run_id"] = item["best_run_id"]
            action["target_root"] = item["best_root"]
            action["stale_reasons"] = item["stale_reasons"]
        do_later.append(action)

    return {
        "roots": status["roots"],
        "root_count": status["root_count"],
        "summary": {
            "run_count": status["summary"]["run_count"],
            "valid_count": status["summary"]["valid_count"],
            "invalid_count": status["summary"]["invalid_count"],
            "keep_count": len(keep_canonical),
            "now_count": len(do_now),
            "later_count": len(do_later),
        },
        "keep_canonical": keep_canonical,
        "do_now": do_now,
        "do_later": do_later,
    }


def render_action_plan(roots: list[Path]) -> str:
    report = collect_action_plan(roots)
    lines = [
        f"Roots: {', '.join(report['roots'])}",
        f"Runs: {report['summary']['run_count']} | valid={report['summary']['valid_count']} | invalid={report['summary']['invalid_count']}",
        f"Plan: keep={report['summary']['keep_count']} | now={report['summary']['now_count']} | later={report['summary']['later_count']}",
    ]

    if report["keep_canonical"]:
        lines.append("Keep Canonical:")
        for item in report["keep_canonical"]:
            lines.append(
                f"{item['run_id']} [{item['root']}] | {item['sim_name']} | reason={item['reason']}"
            )

    if report["do_now"]:
        lines.append("Do Now:")
        for item in report["do_now"]:
            lines.append(
                f"re-export {item['run_id']} [{item['root']}] -> {item['target_run_id']} [{item['target_root']}] | "
                f"reasons={','.join(item['stale_reasons'])}"
            )

    if report["do_later"]:
        lines.append("Do Later:")
        for item in report["do_later"]:
            if item["reason"] == "duplicate_of_canonical":
                lines.append(
                    f"archive {item['run_id']} [{item['root']}] -> duplicate of {item['target_run_id']} [{item['target_root']}]"
                )
            else:
                lines.append(
                    f"archive {item['run_id']} [{item['root']}] -> weaker than {item['target_run_id']} [{item['target_root']}] | "
                    f"reasons={','.join(item.get('stale_reasons', []))}"
                )

    return "\n".join(lines)
