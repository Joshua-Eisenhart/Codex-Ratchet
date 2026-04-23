from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from system_v4.visualization.admission_audit import audit_run_admission
from system_v4.visualization.inspection import inspect_run_dir


def _discover_run_dirs(root: Path) -> list[Path]:
    root = Path(root)
    manifests = sorted(root.rglob("run_manifest.json"))
    return sorted({manifest.parent for manifest in manifests})


def _inspect_runs_for_root(root: Path) -> tuple[list[dict], list[dict]]:
    root = Path(root)
    run_dirs = _discover_run_dirs(root)
    reports: list[dict] = []
    failures: list[dict] = []
    for run_dir in run_dirs:
        try:
            report = inspect_run_dir(run_dir)
        except Exception as exc:
            failures.append({
                "root": str(root),
                "run_dir": str(run_dir),
                "error": str(exc),
            })
            continue
        report["run_dir"] = str(run_dir)
        report["root"] = str(root)
        reports.append(report)
    return reports, failures


def _run_score(report: dict) -> int:
    score = 0
    if report["validation_ok"]:
        score += 1_000_000
    if report["summary_all_pass"]:
        score += 100_000
    if report["projected_path_kind"]:
        score += 10_000
    score += len(report["overlays"]) * 1_000
    score += len(report["capabilities"]) * 100
    score += int(report["frame_count"])
    return score


def _canonical_sort_key(report: dict) -> tuple:
    return (
        int(report["validation_ok"]),
        int(report["summary_all_pass"]),
        int(bool(report["projected_path_kind"])),
        len(report["overlays"]),
        len(report["capabilities"]),
        int(report["frame_count"]),
        report["root"],
        report["run_id"],
    )


def _duplicate_fingerprint(report: dict) -> str:
    basis = {
        "sim_name": report["sim_name"],
        "schema_version": report["schema_version"],
        "frame_count": report["frame_count"],
        "capabilities": sorted(report["capabilities"]),
        "path_kind": report["path_kind"],
        "projected_path_kind": report["projected_path_kind"],
        "overlays": sorted(report["overlays"]),
        "expected_invariants": report["expected_invariants"],
        "measured_invariants": report["measured_invariants"],
        "final_scalars": report.get("final_scalars", {}),
        "summary_all_pass": report["summary_all_pass"],
        "validation_ok": report["validation_ok"],
    }
    payload = json.dumps(basis, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _canonicalization_reason(group: list[dict], canonical: dict) -> str:
    criteria = [
        ("validation_ok", "higher validation status"),
        ("summary_all_pass", "passing summary checks"),
        ("projected_path_kind", "projected path coverage"),
        ("overlay_count", "richer overlay set"),
        ("capability_count", "richer capability set"),
        ("frame_count", "higher frame count"),
    ]

    improvements: list[str] = []
    for field, label in criteria:
        if field == "overlay_count":
            values = [len(item["overlays"]) for item in group]
            canonical_value = len(canonical["overlays"])
        elif field == "capability_count":
            values = [len(item["capabilities"]) for item in group]
            canonical_value = len(canonical["capabilities"])
        elif field == "projected_path_kind":
            values = [int(bool(item["projected_path_kind"])) for item in group]
            canonical_value = int(bool(canonical["projected_path_kind"]))
        else:
            values = [int(item[field]) for item in group]
            canonical_value = int(canonical[field])

        if canonical_value == max(values) and any(value != canonical_value for value in values):
            improvements.append(label)

    if improvements:
        return "canonical chosen by " + ", ".join(improvements)

    return "all replay fields matched; canonical chosen by deterministic root/run_id fallback"


def _stale_reasons(report: dict, best_report: dict) -> list[str]:
    reasons: list[str] = []
    if not report["validation_ok"]:
        reasons.append("invalid")
    if not report["summary_all_pass"]:
        reasons.append("not_all_pass")
    validation_errors = " ".join(report.get("validation_errors", []))
    if "projected_path_spec" in validation_errors:
        reasons.append("missing_projected_path")
    if "projected_s3_xyz" in validation_errors:
        reasons.append("missing_projected_frame_point")
    if best_report["projected_path_kind"] and not report["projected_path_kind"]:
        reasons.append("missing_projected_path")
    if len(report["overlays"]) < len(best_report["overlays"]):
        reasons.append("fewer_overlays")
    if len(report["capabilities"]) < len(best_report["capabilities"]):
        reasons.append("fewer_capabilities")
    if int(report["frame_count"]) < int(best_report["frame_count"]):
        reasons.append("fewer_frames")
    return list(dict.fromkeys(reasons))


def _build_batch_report(roots: list[Path], reports: list[dict], failures: list[dict]) -> dict:
    root_strings = [str(Path(root)) for root in roots]

    sim_counter = Counter(report["sim_name"] for report in reports)
    capability_counter = Counter()
    overlay_counter = Counter()
    for report in reports:
        capability_counter.update(report["capabilities"])
        overlay_counter.update(report["overlays"])

    valid_runs = [report for report in reports if report["validation_ok"]]
    invalid_runs = [report for report in reports if not report["validation_ok"]]
    ranked_runs = []
    for report in reports:
        enriched = dict(report)
        enriched["score"] = _run_score(report)
        enriched["duplicate_fingerprint"] = _duplicate_fingerprint(report)
        ranked_runs.append(enriched)
    ranked_runs.sort(key=lambda item: (item["score"], item["run_id"]), reverse=True)

    best_runs_by_sim: dict[str, dict] = {}
    stale_candidates: list[dict] = []
    reports_by_sim: dict[str, list[dict]] = {}
    for report in ranked_runs:
        reports_by_sim.setdefault(report["sim_name"], []).append(report)
    for sim_name, sim_reports in reports_by_sim.items():
        best = sim_reports[0]
        best_runs_by_sim[sim_name] = {
            "run_id": best["run_id"],
            "root": best["root"],
            "score": best["score"],
            "valid": best["validation_ok"],
            "projected_path_kind": best["projected_path_kind"],
            "overlays": best["overlays"],
        }
        for candidate in sim_reports[1:]:
            reasons = _stale_reasons(candidate, best)
            if not reasons:
                continue
            stale_candidates.append({
                "run_id": candidate["run_id"],
                "sim_name": sim_name,
                "score": candidate["score"],
                "root": candidate["root"],
                "best_run_id": best["run_id"],
                "best_root": best["root"],
                "best_score": best["score"],
                "reasons": reasons,
            })

    duplicate_groups: list[dict] = []
    reports_by_fingerprint: dict[str, list[dict]] = {}
    for report in ranked_runs:
        reports_by_fingerprint.setdefault(report["duplicate_fingerprint"], []).append(report)
    for fingerprint, group in reports_by_fingerprint.items():
        if len(group) < 2:
            continue
        sorted_group = sorted(group, key=_canonical_sort_key, reverse=True)
        canonical = sorted_group[0]
        duplicate_groups.append({
            "fingerprint": fingerprint,
            "sim_name": canonical["sim_name"],
            "canonical_run_id": canonical["run_id"],
            "canonical_root": canonical["root"],
            "canonical_reason": _canonicalization_reason(sorted_group, canonical),
            "members": [
                {
                    "run_id": item["run_id"],
                    "root": item["root"],
                    "score": item["score"],
                    "valid": item["validation_ok"],
                }
                for item in sorted_group
            ],
        })

    root_summaries: dict[str, dict] = {}
    for root in root_strings:
        root_reports = [report for report in reports if report["root"] == root]
        root_summaries[root] = {
            "run_count": len(root_reports),
            "valid_count": sum(1 for report in root_reports if report["validation_ok"]),
            "invalid_count": sum(1 for report in root_reports if not report["validation_ok"]),
        }

    run_dirs = [Path(report["run_dir"]) for report in reports]
    admission_warnings = []
    for report in reports:
        audit = audit_run_admission(Path(report["run_dir"]), run_dirs)
        report["admission_audit"] = audit
        if not audit["ok"]:
            admission_warnings.append({
                "run_id": report["run_id"],
                "sim_name": report["sim_name"],
                "root": report["root"],
                "admission_stage": audit["admission_stage"],
                "missing_lower_stages": audit["missing_lower_stages"],
            })

    return {
        "root": root_strings[0] if len(root_strings) == 1 else None,
        "roots": root_strings,
        "root_count": len(root_strings),
        "run_count": len(reports),
        "failed_to_load_count": len(failures),
        "valid_count": len(valid_runs),
        "invalid_count": len(invalid_runs),
        "sim_counts": dict(sorted(sim_counter.items())),
        "capability_counts": dict(sorted(capability_counter.items())),
        "overlay_counts": dict(sorted(overlay_counter.items())),
        "root_summaries": root_summaries,
        "admission_warning_count": len(admission_warnings),
        "admission_warnings": admission_warnings,
        "invalid_runs": [
            {
                "run_id": report["run_id"],
                "sim_name": report["sim_name"],
                "root": report["root"],
                "errors": report["validation_errors"],
            }
            for report in invalid_runs
        ],
        "load_failures": failures,
        "best_runs_by_sim": dict(sorted(best_runs_by_sim.items())),
        "stale_candidates": stale_candidates,
        "duplicate_groups": duplicate_groups,
        "runs": [
            {
                "run_id": report["run_id"],
                "sim_name": report["sim_name"],
                "root": report["root"],
                "run_dir": report["run_dir"],
                "valid": report["validation_ok"],
                "pass": report["summary_all_pass"],
                "score": report["score"],
                "frames": report["frame_count"],
                "path_kind": report["path_kind"],
                "projected_path_kind": report["projected_path_kind"],
                "overlays": report["overlays"],
                "eligible_consumers": report.get("eligible_consumers", []),
                "blocked_consumers": report.get("blocked_consumers", []),
                "promotion_blockers": report.get("promotion_blockers", []),
            }
            for report in ranked_runs
        ],
    }


def collect_batch_report(root: Path) -> dict:
    root = Path(root)
    reports, failures = _inspect_runs_for_root(root)
    return _build_batch_report([root], reports, failures)


def collect_multi_batch_report(roots: list[Path]) -> dict:
    normalized_roots = [Path(root) for root in roots]
    reports: list[dict] = []
    failures: list[dict] = []
    for root in normalized_roots:
        root_reports, root_failures = _inspect_runs_for_root(root)
        reports.extend(root_reports)
        failures.extend(root_failures)
    return _build_batch_report(normalized_roots, reports, failures)


def _render_batch_report_data(report: dict) -> str:
    multi_root = report["root_count"] > 1
    lines = [
        f"Roots: {', '.join(report['roots'])}",
        f"Runs: {report['run_count']}",
        f"Valid: {report['valid_count']}",
        f"Invalid: {report['invalid_count']}",
        f"Load Failures: {report['failed_to_load_count']}",
        f"Sim Counts: {report['sim_counts'] or {}}",
        f"Capability Counts: {report['capability_counts'] or {}}",
        f"Overlay Counts: {report['overlay_counts'] or {}}",
    ]

    if report["root_summaries"]:
        lines.append("Root Summaries:")
        for root, item in report["root_summaries"].items():
            lines.append(
                f"{root}: runs={item['run_count']} valid={item['valid_count']} invalid={item['invalid_count']}"
            )

    if report["invalid_runs"]:
        lines.append("Invalid Runs:")
        for item in report["invalid_runs"]:
            if multi_root:
                lines.append(f"{item['run_id']} ({item['sim_name']}) [{item['root']}]: {item['errors']}")
            else:
                lines.append(f"{item['run_id']} ({item['sim_name']}): {item['errors']}")

    if report["best_runs_by_sim"]:
        lines.append("Best Runs By Sim:")
        for sim_name, item in report["best_runs_by_sim"].items():
            if multi_root:
                lines.append(
                    f"{sim_name}: {item['run_id']} [{item['root']}] | score={item['score']} | "
                    f"valid={item['valid']} | projected={item['projected_path_kind']}"
                )
            else:
                lines.append(
                    f"{sim_name}: {item['run_id']} | score={item['score']} | "
                    f"valid={item['valid']} | projected={item['projected_path_kind']}"
                )

    if report["stale_candidates"]:
        lines.append("Stale Candidates:")
        for item in report["stale_candidates"]:
            if multi_root:
                lines.append(
                    f"{item['run_id']} [{item['root']}] < {item['best_run_id']} [{item['best_root']}] | "
                    f"reasons={','.join(item['reasons']) if item['reasons'] else '(none)'}"
                )
            else:
                lines.append(
                    f"{item['run_id']} < {item['best_run_id']} | "
                    f"reasons={','.join(item['reasons']) if item['reasons'] else '(none)'}"
                )

    if report["duplicate_groups"]:
        lines.append("Duplicate Groups:")
        for item in report["duplicate_groups"]:
            members = ", ".join(f"{member['run_id']} [{member['root']}]" for member in item["members"])
            if multi_root:
                lines.append(
                    f"{item['sim_name']}: canonical={item['canonical_run_id']} [{item['canonical_root']}] | members={members}"
                )
                lines.append(f"reason={item['canonical_reason']}")
            else:
                members = ", ".join(member["run_id"] for member in item["members"])
                lines.append(
                    f"{item['sim_name']}: canonical={item['canonical_run_id']} | members={members}"
                )
                lines.append(f"reason={item['canonical_reason']}")

    if report["load_failures"]:
        lines.append("Load Failures:")
        for item in report["load_failures"]:
            lines.append(f"{item['run_dir']}: {item['error']}")

    if report["runs"]:
        lines.append("Run Summaries:")
        for item in report["runs"]:
            if multi_root:
                lines.append(
                    f"{item['run_id']} [{item['root']}] | {item['sim_name']} | score={item['score']} | valid={item['valid']} | "
                    f"frames={item['frames']} | overlays={','.join(item['overlays'])}"
                )
            else:
                lines.append(
                    f"{item['run_id']} | {item['sim_name']} | score={item['score']} | valid={item['valid']} | "
                    f"frames={item['frames']} | overlays={','.join(item['overlays'])}"
                )

    return "\n".join(lines)


def render_batch_report(root: Path) -> str:
    return _render_batch_report_data(collect_batch_report(root))


def render_multi_batch_report(roots: list[Path]) -> str:
    return _render_batch_report_data(collect_multi_batch_report(roots))


def _render_dedupe_report_data(report: dict) -> str:
    multi_root = report["root_count"] > 1
    lines = [
        f"Roots: {', '.join(report['roots'])}",
        f"Duplicate Groups: {len(report['duplicate_groups'])}",
    ]
    if not report["duplicate_groups"]:
        lines.append("No replay-equivalent duplicate groups found.")
        return "\n".join(lines)

    for item in report["duplicate_groups"]:
        if multi_root:
            lines.append(
                f"{item['sim_name']}: canonical={item['canonical_run_id']} [{item['canonical_root']}]"
            )
            lines.append(f"reason={item['canonical_reason']}")
            for member in item["members"]:
                lines.append(
                    f"- {member['run_id']} [{member['root']}] | score={member['score']} | valid={member['valid']}"
                )
        else:
            lines.append(f"{item['sim_name']}: canonical={item['canonical_run_id']}")
            lines.append(f"reason={item['canonical_reason']}")
            for member in item["members"]:
                lines.append(
                    f"- {member['run_id']} | score={member['score']} | valid={member['valid']}"
                )
    return "\n".join(lines)


def render_dedupe_report(root: Path) -> str:
    return _render_dedupe_report_data(collect_batch_report(root))


def render_multi_dedupe_report(roots: list[Path]) -> str:
    return _render_dedupe_report_data(collect_multi_batch_report(roots))
