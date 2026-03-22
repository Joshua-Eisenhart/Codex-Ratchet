"""
a2_lev_builder_post_skeleton_disposition_audit_operator.py

Audit-only post-skeleton disposition slice for the lev-builder lane.

This operator reads the landed selector and readiness surfaces and decides
whether the selected unresolved branch should be retained, held, or retired. It
does not migrate files, mutate registry or runner surfaces, or make runtime-live
claims.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTOR_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json"
)
SELECTOR_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json"
)
READINESS_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json"
)
DISPOSITION_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.json"
)
DISPOSITION_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.md"
)
DISPOSITION_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_SLICE_ID = "a2-lev-builder-post-skeleton-disposition-audit-operator"
EXPECTED_SELECTOR_SLICE_ID = "a2-lev-builder-post-skeleton-follow-on-selector-operator"
EXPECTED_SELECTED_BRANCH = "post_skeleton_follow_on_unresolved"
RECOMMENDED_NEXT_SLICE = "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-post-skeleton-disposition-default",
    "title": "bounded lev-builder post-skeleton disposition audit",
    "type": "post_skeleton_disposition_audit",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Decide whether the selected post-skeleton unresolved branch should stay open, "
        "hold at selector, or retire entirely without migration, runner, registry, "
        "or runtime-live claims."
    ),
    "stage_request": "post_skeleton_disposition_audit",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
    ],
}

DEFAULT_NON_GOALS = [
    "No file migration or production-path writes.",
    "No registry mutation or runner mutation from this slice.",
    "No runtime-live claim, runtime-import claim, or imported ownership claim.",
    "No patch generation or patch application.",
    "No completeness verdict or execution-readiness verdict from this slice.",
]

DEFAULT_UNRESOLVED = [
    "Whether any later migration/runtime lane should exist beyond the unresolved branch.",
    "Whether imported runtime ownership is justified for any future follow-on.",
    "Whether the unresolved branch should later be retired after more bounded audit evidence arrives.",
]

BLOCKING_PHRASES = (
    "apply patch",
    "generate patch",
    "migrate to production",
    "write files into production",
    "update registry",
    "update runner",
    "claim runtime-live",
    "claim integration",
    "import the runtime",
    "execution ready",
    "formalization complete",
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_candidate(ctx: dict[str, Any]) -> dict[str, Any]:
    raw_candidate = ctx.get("candidate")
    if isinstance(raw_candidate, dict):
        candidate = dict(DEFAULT_CANDIDATE)
        candidate.update(raw_candidate)
        return candidate
    return dict(DEFAULT_CANDIDATE)


def _ref_records(root: Path, refs: list[str]) -> list[dict[str, Any]]:
    records = []
    for ref in refs:
        path = root / ref
        records.append({"path": ref, "exists": path.exists()})
    return records


def _gate_status(
    candidate: dict[str, Any],
    selector_report: dict[str, Any],
    selector_packet: dict[str, Any],
    readiness_report: dict[str, Any],
    source_ref_status: list[dict[str, Any]],
) -> tuple[str, str, list[str], dict[str, dict[str, Any]]]:
    issues: list[str] = []
    raw_input = str(candidate.get("raw_input", "")).strip().lower()
    stage_request = str(candidate.get("stage_request", "")).strip().lower()

    selector_ok = (
        selector_report.get("status") == "ok"
        and selector_report.get("gate_status") == "follow_on_selection_ready"
        and selector_report.get("cluster_id") == EXPECTED_CLUSTER_ID
        and selector_report.get("slice_id") == EXPECTED_SELECTOR_SLICE_ID
        and selector_report.get("selected_follow_on_id") == EXPECTED_SELECTED_BRANCH
        and selector_packet.get("selected_follow_on_id") == EXPECTED_SELECTED_BRANCH
        and selector_packet.get("next_step") == EXPECTED_SELECTED_BRANCH
    )
    readiness_ok = (
        readiness_report.get("status") == "ok"
        and readiness_report.get("gate_status") == "bounded_post_skeleton_ready"
        and readiness_report.get("admission_decision") == "admit_for_selector_only"
    )
    scope_ok = stage_request == "post_skeleton_disposition_audit"
    source_refs_ok = bool(source_ref_status) and all(item["exists"] for item in source_ref_status)
    selector_guard_ok = all(
        selector_packet.get(flag) is False
        for flag in (
            "allow_registry_mutation",
            "allow_runner_mutation",
            "allow_runtime_claims",
            "allow_migration",
        )
    )

    gate_results = {
        "selector_alignment": {
            "status": "pass",
            "evidence": (
                f"status={selector_report.get('status', '')} "
                f"gate_status={selector_report.get('gate_status', '')} "
                f"selected_follow_on_id={selector_report.get('selected_follow_on_id', '')}"
            ),
        },
        "readiness_alignment": {
            "status": "pass",
            "evidence": (
                f"status={readiness_report.get('status', '')} "
                f"gate_status={readiness_report.get('gate_status', '')} "
                f"admission_decision={readiness_report.get('admission_decision', '')}"
            ),
        },
        "source_refs_available": {
            "status": "pass",
            "evidence": f"{sum(1 for item in source_ref_status if item['exists'])}/{len(source_ref_status)} refs present",
        },
        "scope_hygiene": {
            "status": "pass",
            "evidence": f"stage_request={stage_request}",
        },
        "non_live_surface_guard": {
            "status": "pass",
            "evidence": (
                f"allow_registry_mutation={selector_packet.get('allow_registry_mutation')} "
                f"allow_runner_mutation={selector_packet.get('allow_runner_mutation')} "
                f"allow_runtime_claims={selector_packet.get('allow_runtime_claims')} "
                f"allow_migration={selector_packet.get('allow_migration')}"
            ),
        },
    }

    if not selector_ok:
        gate_results["selector_alignment"]["status"] = "block"
        issues.append("selector surfaces are not clean enough to govern the unresolved branch")
    if not readiness_ok:
        gate_results["readiness_alignment"]["status"] = "block"
        issues.append("readiness surfaces no longer justify selector-only downstream work")
    if not source_refs_ok:
        gate_results["source_refs_available"]["status"] = "block"
        issues.append("one or more core lev-builder source refs are missing")
    if not scope_ok:
        gate_results["scope_hygiene"]["status"] = "block"
        issues.append("candidate stage_request is not post_skeleton_disposition_audit")
    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate_results["scope_hygiene"]["status"] = "block"
        issues.append("candidate request widens into migration/runtime/completeness claims")
    if not selector_guard_ok:
        gate_results["non_live_surface_guard"]["status"] = "block"
        issues.append("selector packet unexpectedly widens the non-live guard")

    retain_unresolved = not any(item["status"] == "block" for item in gate_results.values())
    disposition = "retain_unresolved_branch" if retain_unresolved else "hold_at_selector"
    return ("disposition_ready" if retain_unresolved else "hold_at_selector", disposition, issues, gate_results)


def build_a2_lev_builder_post_skeleton_disposition_audit_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    selector_report_path = _resolve_output_path(root, ctx.get("selector_report_path"), SELECTOR_REPORT_PATH)
    selector_packet_path = _resolve_output_path(root, ctx.get("selector_packet_path"), SELECTOR_PACKET_PATH)
    readiness_report_path = _resolve_output_path(root, ctx.get("readiness_report_path"), READINESS_REPORT_PATH)

    selector_report = _safe_load_json(selector_report_path)
    selector_packet = _safe_load_json(selector_packet_path)
    readiness_report = _safe_load_json(readiness_report_path)
    source_ref_status = _ref_records(root, [str(item) for item in candidate.get("source_refs", []) if str(item).strip()])

    gate_status, disposition, issues, gate_results = _gate_status(
        candidate,
        selector_report,
        selector_packet,
        readiness_report,
        source_ref_status,
    )
    retain_unresolved = disposition == "retain_unresolved_branch"
    recommended_next_step = RECOMMENDED_NEXT_SLICE if retain_unresolved else "hold_at_selector"

    report = {
        "schema": "a2_lev_builder_post_skeleton_disposition_audit_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if retain_unresolved else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "non_migratory": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "slice_id": EXPECTED_SLICE_ID,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": "lev-builder",
        "upstream_selector_report_path": str(selector_report_path.relative_to(root)),
        "upstream_selector_packet_path": str(selector_packet_path.relative_to(root)),
        "upstream_readiness_report_path": str(readiness_report_path.relative_to(root)),
        "candidate": candidate,
        "gate_status": gate_status,
        "disposition": disposition,
        "selected_branch_under_audit": EXPECTED_SELECTED_BRANCH,
        "recommended_next_step": recommended_next_step,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": retain_unresolved,
            "allow_registry_mutation": False,
            "allow_runner_mutation": False,
            "allow_graph_claims": False,
            "allow_runtime_claims": False,
            "allow_migration": False,
            "allow_patch_application": False,
            "blocking_issues": issues,
            "priority_findings": [label for label, result in gate_results.items() if result["status"] == "block"],
            "reason": (
                "the unresolved branch still has bounded governance questions and should remain open"
                if retain_unresolved
                else "upstream selector/readiness truth is not clean enough to keep the unresolved branch open"
            ),
            "gate_results": gate_results,
            "recommended_next_step": recommended_next_step,
        },
        "recommended_actions": [
            "Keep this slice audit-only, repo-held, and non-migratory.",
            "Treat the current branch as retained only for later bounded governance/audit work.",
            "Do not widen this audit into runtime, migration, or completeness claims.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_post_skeleton_disposition_audit_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "gate_status": gate_status,
        "disposition": disposition,
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "selected_branch_under_audit": EXPECTED_SELECTED_BRANCH,
        "recommended_next_step": recommended_next_step,
        "next_step": recommended_next_step,
        "allow_registry_mutation": False,
        "allow_runner_mutation": False,
        "allow_graph_claims": False,
        "allow_runtime_claims": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "blocking_issues": issues,
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Post-Skeleton Disposition Audit Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- disposition: `{report.get('disposition', '')}`",
        f"- selected_branch_under_audit: `{report.get('selected_branch_under_audit', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        "",
        "## Upstream Surfaces",
        f"- selector_report: `{report.get('upstream_selector_report_path', '')}`",
        f"- selector_packet: `{report.get('upstream_selector_packet_path', '')}`",
        f"- readiness_report: `{report.get('upstream_readiness_report_path', '')}`",
        "",
        "## Recommended Actions",
    ]
    for action in report.get("recommended_actions", []):
        lines.append(f"- {action}")
    lines.extend(["", "## Non-Goals"])
    for item in report.get("non_goals", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Unresolved Questions"])
    for item in report.get("unresolved_questions", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Packet",
            f"- gate_status: `{packet.get('gate_status', '')}`",
            f"- disposition: `{packet.get('disposition', '')}`",
            f"- selected_branch_under_audit: `{packet.get('selected_branch_under_audit', '')}`",
            f"- recommended_next_step: `{packet.get('recommended_next_step', '')}`",
            f"- allow_runtime_claims: `{packet.get('allow_runtime_claims', False)}`",
            f"- allow_migration: `{packet.get('allow_migration', False)}`",
        ]
    )
    if report.get("issues"):
        lines.extend(["", "## Issues"])
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    lines.append("")
    return "\n".join(lines)


def run_a2_lev_builder_post_skeleton_disposition_audit(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), DISPOSITION_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), DISPOSITION_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), DISPOSITION_PACKET_JSON)

    report, packet = build_a2_lev_builder_post_skeleton_disposition_audit_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted
