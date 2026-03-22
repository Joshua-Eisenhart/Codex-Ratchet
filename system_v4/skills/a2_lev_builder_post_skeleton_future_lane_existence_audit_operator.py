"""
a2_lev_builder_post_skeleton_future_lane_existence_audit_operator.py

Audit-only future-lane existence slice for the lev-builder post-skeleton seam.

This operator reads the landed disposition surface, decides whether the retained
unresolved branch still justifies a repo-held future lane artifact, and emits
one bounded report plus one compact packet. It does not migrate files, mutate
registry or runner surfaces, or make runtime-live claims.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DISPOSITION_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.json"
)
DISPOSITION_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_PACKET__CURRENT__v1.json"
)

FUTURE_LANE_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FUTURE_LANE_EXISTENCE_AUDIT_REPORT__CURRENT__v1.json"
)
FUTURE_LANE_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FUTURE_LANE_EXISTENCE_AUDIT_REPORT__CURRENT__v1.md"
)
FUTURE_LANE_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FUTURE_LANE_EXISTENCE_AUDIT_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_SLICE_ID = "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator"
EXPECTED_UPSTREAM_SLICE = "a2-lev-builder-post-skeleton-disposition-audit-operator"
EXPECTED_SELECTED_BRANCH = "post_skeleton_follow_on_unresolved"
EXPECTED_EXISTENCE_DECISION = "future_lane_exists_as_governance_artifact"
EXPECTED_HOLD_DECISION = "hold_at_disposition"
EXPECTED_AUDITED_GATE_STATUS = "future_lane_existence_audited"
EXPECTED_BLOCKED_GATE_STATUS = "future_lane_existence_blocked"
EXPECTED_SOURCE_SKILL_ID = "lev-builder"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-post-skeleton-future-lane-existence-default",
    "title": "bounded lev-builder future lane existence audit",
    "type": "post_skeleton_future_lane_existence_audit",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Audit whether the retained post-skeleton unresolved branch still exists "
        "as a repo-held future lane artifact without migration, registry, runner, "
        "or runtime-live claims."
    ),
    "stage_request": "post_skeleton_future_lane_existence_audit",
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
    "No execution, promotion, or downstream build work hidden inside the audit.",
]

DEFAULT_UNRESOLVED = [
    "Whether the unresolved branch should remain a repo-held future lane artifact or be retired after more bounded evidence.",
    "Whether any downstream runtime or migration lane should ever follow this audit.",
    "Whether branch-governance-only handling should remain the permanent boundary for this cluster.",
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
    "runtime lane",
    "execution ready",
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


def _future_lane_target() -> dict[str, Any]:
    return {
        "decision_scope": "post_skeleton_future_lane_existence",
        "admission_mode": "governance_only",
        "recognized_branch": EXPECTED_SELECTED_BRANCH,
        "lane_form": "repo_held_future_lane_artifact",
        "disallowed_follow_on_classes": [
            "migration",
            "runtime_import",
            "runtime_live_claim",
            "registry_mutation",
            "runner_mutation",
        ],
    }


def _gate_status(
    candidate: dict[str, Any],
    disposition_report: dict[str, Any],
    disposition_packet: dict[str, Any],
    source_ref_status: list[dict[str, Any]],
) -> tuple[str, str, list[str], dict[str, dict[str, Any]]]:
    issues: list[str] = []
    raw_input = str(candidate.get("raw_input", "")).strip().lower()
    stage_request = str(candidate.get("stage_request", "")).strip().lower()

    disposition_ok = (
        disposition_report.get("status") == "ok"
        and disposition_report.get("gate_status") == "disposition_ready"
        and disposition_report.get("disposition") == "retain_unresolved_branch"
        and disposition_report.get("selected_branch_under_audit") == EXPECTED_SELECTED_BRANCH
        and disposition_report.get("recommended_next_step") == EXPECTED_SLICE_ID
        and disposition_packet.get("next_step") == EXPECTED_SLICE_ID
        and disposition_packet.get("selected_branch_under_audit") == EXPECTED_SELECTED_BRANCH
    )
    source_refs_ok = bool(source_ref_status) and all(item["exists"] for item in source_ref_status)
    scope_ok = stage_request == "post_skeleton_future_lane_existence_audit"
    non_live_guard_ok = all(
        disposition_packet.get(flag) is False
        for flag in (
            "allow_registry_mutation",
            "allow_runner_mutation",
            "allow_graph_claims",
            "allow_runtime_claims",
            "allow_migration",
            "allow_patch_application",
        )
    )

    gate_results = {
        "disposition_alignment": {
            "status": "pass",
            "evidence": (
                f"status={disposition_report.get('status', '')} "
                f"gate_status={disposition_report.get('gate_status', '')} "
                f"disposition={disposition_report.get('disposition', '')} "
                f"next_step={disposition_packet.get('next_step', '')}"
            ),
        },
        "branch_governance_alignment": {
            "status": "pass",
            "evidence": (
                f"selected_branch_under_audit={disposition_report.get('selected_branch_under_audit', '')} "
                f"recommended_next_step={disposition_report.get('recommended_next_step', '')}"
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
                f"allow_registry_mutation={disposition_packet.get('allow_registry_mutation')} "
                f"allow_runner_mutation={disposition_packet.get('allow_runner_mutation')} "
                f"allow_graph_claims={disposition_packet.get('allow_graph_claims')} "
                f"allow_runtime_claims={disposition_packet.get('allow_runtime_claims')} "
                f"allow_migration={disposition_packet.get('allow_migration')} "
                f"allow_patch_application={disposition_packet.get('allow_patch_application')}"
            ),
        },
    }

    if not disposition_ok:
        gate_results["disposition_alignment"]["status"] = "block"
        issues.append("disposition surfaces are not clean enough to recognize a future lane artifact")
    if not source_refs_ok:
        gate_results["source_refs_available"]["status"] = "block"
        issues.append("one or more core lev-builder source refs are missing")
    if not scope_ok:
        gate_results["scope_hygiene"]["status"] = "block"
        issues.append("candidate stage_request is not post_skeleton_future_lane_existence_audit")
    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate_results["scope_hygiene"]["status"] = "block"
        issues.append("candidate request widens into migration/runtime/runner/execution claims")
    if not non_live_guard_ok:
        gate_results["non_live_surface_guard"]["status"] = "block"
        issues.append("disposition packet unexpectedly widens the non-live guard")

    future_lane_exists = not any(item["status"] == "block" for item in gate_results.values())
    existence_decision = (
        EXPECTED_EXISTENCE_DECISION if future_lane_exists else EXPECTED_HOLD_DECISION
    )
    gate_status = EXPECTED_AUDITED_GATE_STATUS if future_lane_exists else EXPECTED_BLOCKED_GATE_STATUS
    return gate_status, existence_decision, issues, gate_results


def build_a2_lev_builder_post_skeleton_future_lane_existence_audit_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    disposition_report_path = _resolve_output_path(root, ctx.get("disposition_report_path"), DISPOSITION_REPORT_PATH)
    disposition_packet_path = _resolve_output_path(root, ctx.get("disposition_packet_path"), DISPOSITION_PACKET_PATH)

    disposition_report = _safe_load_json(disposition_report_path)
    disposition_packet = _safe_load_json(disposition_packet_path)
    source_ref_status = _ref_records(root, [str(item) for item in candidate.get("source_refs", []) if str(item).strip()])

    target = _future_lane_target()
    gate_status, existence_decision, issues, gate_results = _gate_status(
        candidate,
        disposition_report,
        disposition_packet,
        source_ref_status,
    )

    future_lane_exists = existence_decision == EXPECTED_EXISTENCE_DECISION
    recommended_next_step = EXPECTED_HOLD_DECISION

    report = {
        "schema": "a2_lev_builder_post_skeleton_future_lane_existence_audit_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if future_lane_exists else "attention_required",
        "audit_only": True,
        "branch_governance_only": True,
        "nonoperative": True,
        "non_migratory": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "slice_id": EXPECTED_SLICE_ID,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "upstream_disposition_report_path": str(disposition_report_path.relative_to(root)),
        "upstream_disposition_packet_path": str(disposition_packet_path.relative_to(root)),
        "candidate": candidate,
        "future_lane_target": target,
        "source_ref_status": source_ref_status,
        "gate_status": gate_status,
        "existence_decision": existence_decision,
        "future_lane_exists": future_lane_exists,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": False,
            "future_lane_exists": future_lane_exists,
            "allow_bounded_future_lane_audit": False,
            "allow_registry_mutation": False,
            "allow_runner_mutation": False,
            "allow_graph_claims": False,
            "allow_runtime_claims": False,
            "allow_migration": False,
            "allow_patch_application": False,
            "blocking_issues": issues,
            "priority_findings": [label for label, result in gate_results.items() if result["status"] == "block"],
            "reason": (
                "the retained unresolved branch remains a repo-held future lane artifact, but no additional lane is admitted"
                if future_lane_exists
                else "disposition surfaces are not clean enough to recognize a future lane artifact"
            ),
            "gate_results": gate_results,
            "recommended_next_step": recommended_next_step,
        },
        "recommended_actions": [
            "Keep this slice audit-only, repo-held, and branch-governance-only.",
            "Treat the retained unresolved branch as a future lane artifact only in the bounded governance sense.",
            "Hold at disposition after this audit unless later bounded evidence reopens the question.",
            "Do not widen this audit into runtime, migration, registry, runner, or patch claims.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_post_skeleton_future_lane_existence_audit_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "gate_status": gate_status,
        "existence_decision": existence_decision,
        "future_lane_exists": future_lane_exists,
        "allow_bounded_future_lane_audit": False,
        "allow_registry_mutation": False,
        "allow_runner_mutation": False,
        "allow_graph_claims": False,
        "allow_runtime_claims": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "blocking_issues": issues,
        "next_step": recommended_next_step,
        "recommended_next_step": recommended_next_step,
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Post-Skeleton Future Lane Existence Audit Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- existence_decision: `{report.get('existence_decision', '')}`",
        f"- future_lane_exists: `{report.get('future_lane_exists', False)}`",
        "",
        "## Future Lane Target",
        f"- decision_scope: `{report.get('future_lane_target', {}).get('decision_scope', '')}`",
        f"- admission_mode: `{report.get('future_lane_target', {}).get('admission_mode', '')}`",
        f"- recognized_branch: `{report.get('future_lane_target', {}).get('recognized_branch', '')}`",
        f"- lane_form: `{report.get('future_lane_target', {}).get('lane_form', '')}`",
        "",
        "## Gate Results",
    ]
    for label, result in report.get("gate", {}).get("gate_results", {}).items():
        lines.append(f"- `{label}` status=`{result.get('status', '')}` evidence=`{result.get('evidence', '')}`")
    lines.extend(["", "## Recommended Actions"])
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
            f"- existence_decision: `{packet.get('existence_decision', '')}`",
            f"- future_lane_exists: `{packet.get('future_lane_exists', False)}`",
            f"- allow_bounded_future_lane_audit: `{packet.get('allow_bounded_future_lane_audit', False)}`",
            f"- allow_registry_mutation: `{packet.get('allow_registry_mutation', False)}`",
            f"- allow_runner_mutation: `{packet.get('allow_runner_mutation', False)}`",
            f"- allow_graph_claims: `{packet.get('allow_graph_claims', False)}`",
            f"- allow_runtime_claims: `{packet.get('allow_runtime_claims', False)}`",
            f"- allow_migration: `{packet.get('allow_migration', False)}`",
            f"- allow_patch_application: `{packet.get('allow_patch_application', False)}`",
            f"- next_step: `{packet.get('next_step', '')}`",
        ]
    )
    if report.get("issues"):
        lines.extend(["", "## Issues"])
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    lines.append("")
    return "\n".join(lines)


def run_a2_lev_builder_post_skeleton_future_lane_existence_audit(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), FUTURE_LANE_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), FUTURE_LANE_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), FUTURE_LANE_PACKET_JSON)

    report, packet = build_a2_lev_builder_post_skeleton_future_lane_existence_audit_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted
