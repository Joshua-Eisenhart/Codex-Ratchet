"""
a2_lev_builder_post_skeleton_readiness_operator.py

Bounded readiness gate for the lev-builder post-skeleton seam.

This operator consumes the landed placement/proposal/skeleton reports, verifies
that graph truth and A2 refresh are still converged, and emits one repo-held
readiness verdict about whether any downstream post-skeleton slice should even
be considered. It does not migrate files, mutate existing code, or claim
runtime ownership.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PLACEMENT_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_REPORT__CURRENT__v1.json"
)
PLACEMENT_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_PACKET__CURRENT__v1.json"
)
PROPOSAL_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json"
)
PROPOSAL_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_PACKET__CURRENT__v1.json"
)
SKELETON_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json"
)
SKELETON_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json"
)
REFRESH_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
)
GRAPH_AUDIT_PATH = (
    "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json"
)

READINESS_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json"
)
READINESS_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.md"
)
READINESS_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_SLICE_ID = "a2-lev-builder-post-skeleton-readiness-operator"
EXPECTED_UPSTREAM_SLICE = "a2-lev-builder-formalization-skeleton-operator"
EXPECTED_NEXT_STEP = "a2-lev-builder-post-skeleton-follow-on-selector-operator"
EXPECTED_SOURCE_SKILL_ID = "lev-builder"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-post-skeleton-readiness-default",
    "title": "bounded lev-builder post-skeleton readiness gate",
    "type": "post_skeleton_readiness",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Emit one bounded readiness verdict over the lev-builder post-skeleton seam "
        "without migration, runtime-live, registry, or runner claims."
    ),
    "stage_request": "post_skeleton_readiness",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
    ],
}

DEFAULT_NON_GOALS = [
    "No file mutation, patch generation, or patch application.",
    "No migration or production-path writes.",
    "No registry mutation or runner mutation from this slice.",
    "No runtime-live claim, formalization-complete claim, or imported runtime ownership claim.",
    "No downstream target selection or multi-candidate ranking inside this slice.",
    "No full lev-builder workflow port or .lev substrate import.",
]

DEFAULT_UNRESOLVED = [
    "Whether any post-skeleton migration/runtime follow-on should exist at all.",
    "Whether formalization is complete enough for execution, not just placement/proposal/scaffold/readiness.",
    "Whether migration permission should ever be granted for this cluster.",
    "Whether any imported runtime ownership claim is justified.",
]

BLOCKING_PHRASES = (
    "apply patch",
    "generate patch",
    "migrate to production",
    "write files into production",
    "claim runtime-live",
    "claim integration",
    "import the runtime",
    "update registry",
    "update runner",
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


def _resolve_path(root: Path, raw: Any, default_rel: str) -> Path:
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


def _readiness_target() -> dict[str, Any]:
    return {
        "decision_scope": "any_downstream_post_skeleton_slice",
        "admission_mode": "selector_only_if_ready",
        "recommended_next_skill_id": EXPECTED_NEXT_STEP,
        "disallowed_follow_on_classes": [
            "migration",
            "runtime_import",
            "runtime_live_claim",
            "imported_runtime_ownership",
        ],
    }


def _evidence_inputs(
    placement_report: dict[str, Any],
    placement_packet: dict[str, Any],
    proposal_report: dict[str, Any],
    proposal_packet: dict[str, Any],
    skeleton_report: dict[str, Any],
    skeleton_packet: dict[str, Any],
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
) -> dict[str, Any]:
    graph_skill_coverage = graph_audit.get("skill_graph_coverage", {}) if isinstance(graph_audit, dict) else {}
    return {
        "placement_report_status": placement_report.get("status"),
        "placement_follow_on_slice": placement_report.get("recommended_follow_on_slice_id"),
        "placement_packet_allow_bounded_placement_audit": placement_packet.get("allow_bounded_placement_audit"),
        "proposal_report_status": proposal_report.get("status"),
        "proposal_gate_status": proposal_report.get("gate_status"),
        "proposal_next_step": proposal_packet.get("next_step"),
        "skeleton_report_status": skeleton_report.get("status"),
        "skeleton_gate_status": skeleton_report.get("gate_status"),
        "skeleton_next_step": skeleton_packet.get("next_step"),
        "skeleton_bounded_scaffold_completed": skeleton_packet.get("bounded_scaffold_completed"),
        "brain_refresh_status": refresh_report.get("status"),
        "graph_skill_coverage": {
            "active_skill_count": graph_skill_coverage.get("active_skill_count"),
            "graphed_skill_node_count": graph_skill_coverage.get("graphed_skill_node_count"),
            "missing_active_skill_count": graph_skill_coverage.get("missing_active_skill_count"),
            "stale_skill_node_count": graph_skill_coverage.get("stale_skill_node_count"),
            "fully_graphed": graph_skill_coverage.get("fully_graphed"),
        },
    }


def _gate_status(
    candidate: dict[str, Any],
    placement_report: dict[str, Any],
    placement_packet: dict[str, Any],
    proposal_report: dict[str, Any],
    proposal_packet: dict[str, Any],
    skeleton_report: dict[str, Any],
    skeleton_packet: dict[str, Any],
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
    source_ref_status: list[dict[str, Any]],
) -> tuple[str, str, list[str], dict[str, dict[str, Any]]]:
    issues: list[str] = []
    raw_input = str(candidate.get("raw_input", "")).strip().lower()
    stage_request = str(candidate.get("stage_request", "")).strip().lower()

    graph_skill_coverage = graph_audit.get("skill_graph_coverage", {}) if isinstance(graph_audit, dict) else {}
    missing_skill_count = int(graph_skill_coverage.get("missing_active_skill_count") or 0)
    stale_skill_count = int(graph_skill_coverage.get("stale_skill_node_count") or 0)
    fully_graphed = bool(graph_skill_coverage.get("fully_graphed", False))

    gate = {
        "placement_alignment": {
            "status": "pass",
            "evidence": (
                f"status={placement_report.get('status', '')} "
                f"follow_on={placement_report.get('recommended_follow_on_slice_id', '')}"
            ),
        },
        "proposal_alignment": {
            "status": "pass",
            "evidence": (
                f"status={proposal_report.get('status', '')} "
                f"gate_status={proposal_report.get('gate_status', '')} "
                f"next_step={proposal_packet.get('next_step', '')}"
            ),
        },
        "skeleton_alignment": {
            "status": "pass",
            "evidence": (
                f"status={skeleton_report.get('status', '')} "
                f"gate_status={skeleton_report.get('gate_status', '')} "
                f"next_step={skeleton_packet.get('next_step', '')}"
            ),
        },
        "refresh_alignment": {
            "status": "pass",
            "evidence": f"brain_refresh_status={refresh_report.get('status', '')}",
        },
        "graph_truth_alignment": {
            "status": "pass",
            "evidence": (
                f"active={graph_skill_coverage.get('active_skill_count')} "
                f"graphed={graph_skill_coverage.get('graphed_skill_node_count')} "
                f"missing={missing_skill_count} stale={stale_skill_count}"
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
    }

    if placement_report.get("status") != "ok" or placement_report.get("recommended_follow_on_slice_id") != "a2-lev-builder-formalization-proposal-operator":
        gate["placement_alignment"]["status"] = "block"
        issues.append("placement audit no longer points cleanly at the proposal slice")
    if placement_packet.get("allow_bounded_placement_audit") is not True:
        gate["placement_alignment"]["status"] = "block"
        issues.append("placement packet no longer allows bounded carryforward")

    if proposal_report.get("status") != "ok" or proposal_report.get("gate_status") != "ready_for_formalization_proposal":
        gate["proposal_alignment"]["status"] = "block"
        issues.append("formalization proposal is not currently healthy")
    if proposal_packet.get("next_step") != EXPECTED_UPSTREAM_SLICE:
        gate["proposal_alignment"]["status"] = "block"
        issues.append("proposal packet no longer points at the skeleton slice")

    if skeleton_report.get("status") != "ok" or skeleton_report.get("gate_status") != "bounded_scaffold_completed":
        gate["skeleton_alignment"]["status"] = "block"
        issues.append("skeleton slice is not currently completed and healthy")
    if skeleton_packet.get("bounded_scaffold_completed") is not True:
        gate["skeleton_alignment"]["status"] = "block"
        issues.append("skeleton packet does not confirm bounded scaffold completion")
    if skeleton_packet.get("allow_runtime_claims") is not False or skeleton_packet.get("allow_migration") is not False:
        gate["skeleton_alignment"]["status"] = "block"
        issues.append("skeleton packet widened into runtime or migration claims")

    if refresh_report.get("status") != "ok":
        gate["refresh_alignment"]["status"] = "block"
        issues.append("A2 brain refresher is not currently ok")

    if not fully_graphed or missing_skill_count or stale_skill_count:
        gate["graph_truth_alignment"]["status"] = "block"
        issues.append("graph skill truth is not fully converged")

    if not source_ref_status or any(not item["exists"] for item in source_ref_status):
        gate["source_refs_available"]["status"] = "block"
        issues.append("one or more core lev-builder readiness refs are missing")

    if stage_request != "post_skeleton_readiness":
        gate["scope_hygiene"]["status"] = "block"
        issues.append("candidate stage_request is not post_skeleton_readiness")
    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate["scope_hygiene"]["status"] = "block"
        issues.append("candidate request widens into migration/runtime/runner behavior")

    if any(value["status"] == "block" for value in gate.values()):
        return "hold_blocked", "hold_at_scaffold", issues, gate
    return "bounded_post_skeleton_ready", "admit_for_selector_only", issues, gate


def build_a2_lev_builder_post_skeleton_readiness_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    placement_report_path = _resolve_path(root, ctx.get("placement_report_path"), PLACEMENT_REPORT_PATH)
    placement_packet_path = _resolve_path(root, ctx.get("placement_packet_path"), PLACEMENT_PACKET_PATH)
    proposal_report_path = _resolve_path(root, ctx.get("proposal_report_path"), PROPOSAL_REPORT_PATH)
    proposal_packet_path = _resolve_path(root, ctx.get("proposal_packet_path"), PROPOSAL_PACKET_PATH)
    skeleton_report_path = _resolve_path(root, ctx.get("skeleton_report_path"), SKELETON_REPORT_PATH)
    skeleton_packet_path = _resolve_path(root, ctx.get("skeleton_packet_path"), SKELETON_PACKET_PATH)
    refresh_report_path = _resolve_path(root, ctx.get("refresh_report_path"), REFRESH_REPORT_PATH)
    graph_audit_path = _resolve_path(root, ctx.get("graph_audit_path"), GRAPH_AUDIT_PATH)

    placement_report = _safe_load_json(placement_report_path)
    placement_packet = _safe_load_json(placement_packet_path)
    proposal_report = _safe_load_json(proposal_report_path)
    proposal_packet = _safe_load_json(proposal_packet_path)
    skeleton_report = _safe_load_json(skeleton_report_path)
    skeleton_packet = _safe_load_json(skeleton_packet_path)
    refresh_report = _safe_load_json(refresh_report_path)
    graph_audit = _safe_load_json(graph_audit_path)
    source_ref_status = _ref_records(root, [str(item) for item in candidate.get("source_refs", []) if str(item).strip()])

    readiness_target = _readiness_target()
    evidence_inputs = _evidence_inputs(
        placement_report,
        placement_packet,
        proposal_report,
        proposal_packet,
        skeleton_report,
        skeleton_packet,
        refresh_report,
        graph_audit,
    )
    gate_status, admission_decision, issues, gate_results = _gate_status(
        candidate,
        placement_report,
        placement_packet,
        proposal_report,
        proposal_packet,
        skeleton_report,
        skeleton_packet,
        refresh_report,
        graph_audit,
        source_ref_status,
    )

    bounded_post_skeleton_ready = gate_status == "bounded_post_skeleton_ready"
    recommended_actions = [
        "Keep this slice readiness-only, repo-held, and non-migratory.",
        "Treat any next slice as a selector-only admission step, not proof or migration.",
        "Do not widen this readiness result into runtime-live or imported-runtime-ownership claims.",
    ]
    if not bounded_post_skeleton_ready:
        recommended_actions.insert(
            0,
            "Hold the cluster at scaffold-as-artifact until placement/proposal/skeleton/A2/graph truth converges again.",
        )

    report = {
        "schema": "a2_lev_builder_post_skeleton_readiness_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if bounded_post_skeleton_ready else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "readiness_only": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "slice_id": EXPECTED_SLICE_ID,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "upstream_placement_report_path": str(placement_report_path.relative_to(root)),
        "upstream_placement_packet_path": str(placement_packet_path.relative_to(root)),
        "upstream_proposal_report_path": str(proposal_report_path.relative_to(root)),
        "upstream_proposal_packet_path": str(proposal_packet_path.relative_to(root)),
        "upstream_skeleton_report_path": str(skeleton_report_path.relative_to(root)),
        "upstream_skeleton_packet_path": str(skeleton_packet_path.relative_to(root)),
        "candidate": candidate,
        "readiness_target": readiness_target,
        "source_ref_status": source_ref_status,
        "evidence_inputs": evidence_inputs,
        "gate_status": gate_status,
        "admission_decision": admission_decision,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": bounded_post_skeleton_ready,
            "bounded_post_skeleton_ready": bounded_post_skeleton_ready,
            "allow_registry_mutation": False,
            "allow_runner_mutation": False,
            "allow_graph_claims": False,
            "allow_runtime_claims": False,
            "allow_a2_truth_update": False,
            "allow_migration": False,
            "allow_patch_application": False,
            "blocking_issues": issues,
            "priority_findings": [label for label, result in gate_results.items() if result["status"] == "block"],
            "reason": (
                "the landed scaffold bundle plus converged graph and A2 truth justify a selector-only downstream decision"
                if bounded_post_skeleton_ready
                else "one or more upstream gates are not clean enough to justify any downstream post-skeleton slice"
            ),
            "gate_results": gate_results,
            "recommended_next_step": EXPECTED_NEXT_STEP if bounded_post_skeleton_ready else "hold_at_scaffold",
        },
        "recommended_actions": recommended_actions,
        "non_goals": list(DEFAULT_NON_GOALS),
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_post_skeleton_readiness_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "bounded_post_skeleton_ready": bounded_post_skeleton_ready,
        "admission_decision": admission_decision,
        "allow_registry_mutation": False,
        "allow_runner_mutation": False,
        "allow_graph_claims": False,
        "allow_runtime_claims": False,
        "allow_a2_truth_update": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "blocking_issues": report["gate"]["blocking_issues"],
        "next_step": report["gate"]["recommended_next_step"],
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Post-Skeleton Readiness Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- admission_decision: `{report.get('admission_decision', '')}`",
        f"- bounded_post_skeleton_ready: `{report.get('gate', {}).get('bounded_post_skeleton_ready')}`",
        "",
        "## Readiness Target",
        f"- decision_scope: `{report.get('readiness_target', {}).get('decision_scope', '')}`",
        f"- admission_mode: `{report.get('readiness_target', {}).get('admission_mode', '')}`",
        f"- recommended_next_skill_id: `{report.get('readiness_target', {}).get('recommended_next_skill_id', '')}`",
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
            f"- bounded_post_skeleton_ready: `{packet.get('bounded_post_skeleton_ready', False)}`",
            f"- admission_decision: `{packet.get('admission_decision', '')}`",
            f"- allow_registry_mutation: `{packet.get('allow_registry_mutation', False)}`",
            f"- allow_runner_mutation: `{packet.get('allow_runner_mutation', False)}`",
            f"- allow_graph_claims: `{packet.get('allow_graph_claims', False)}`",
            f"- allow_runtime_claims: `{packet.get('allow_runtime_claims', False)}`",
            f"- allow_a2_truth_update: `{packet.get('allow_a2_truth_update', False)}`",
            f"- allow_migration: `{packet.get('allow_migration', False)}`",
            f"- next_step: `{packet.get('next_step', '')}`",
        ]
    )
    issues = report.get("issues", [])
    if issues:
        lines.extend(["", "## Issues"])
        for issue in issues:
            lines.append(f"- {issue}")
    lines.append("")
    return "\n".join(lines)


def run_a2_lev_builder_post_skeleton_readiness(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_path(root, ctx.get("report_json_path"), READINESS_REPORT_JSON)
    markdown_path = _resolve_path(root, ctx.get("report_md_path"), READINESS_REPORT_MD)
    packet_path = _resolve_path(root, ctx.get("packet_path"), READINESS_PACKET_JSON)

    report, packet = build_a2_lev_builder_post_skeleton_readiness_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted
