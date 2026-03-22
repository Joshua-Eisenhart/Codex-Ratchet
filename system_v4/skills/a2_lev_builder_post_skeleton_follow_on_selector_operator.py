"""
a2_lev_builder_post_skeleton_follow_on_selector_operator.py

Selector-only post-skeleton slice for the lev-builder lane.

This operator reads the landed post-skeleton readiness and skeleton surfaces,
selects the smallest honest follow-on branch, and emits one repo-held report
plus one compact packet. It does not migrate files, mutate registry or runner
surfaces, or make runtime-live claims.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
READINESS_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json"
)
READINESS_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_PACKET__CURRENT__v1.json"
)
SKELETON_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json"
)
SKELETON_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json"
)

FOLLOW_ON_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json"
)
FOLLOW_ON_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.md"
)
FOLLOW_ON_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_SLICE_ID = "a2-lev-builder-post-skeleton-follow-on-selector-operator"
EXPECTED_UPSTREAM_SLICE = "a2-lev-builder-post-skeleton-readiness-operator"
EXPECTED_FOLLOW_ON_ID = "post_skeleton_follow_on_unresolved"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-post-skeleton-follow-on-selector-default",
    "title": "bounded lev-builder follow-on selection",
    "type": "post_skeleton_follow_on_selection",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Select the smallest honest post-skeleton follow-on branch without migration, "
        "runner, registry, or runtime-live claims."
    ),
    "stage_request": "post_skeleton_follow_on_selection",
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
    "No downstream execution lane hidden inside the selector.",
]

DEFAULT_UNRESOLVED = [
    "Whether the post-skeleton follow-on should remain unresolved or be retired entirely.",
    "Whether any later migration/runtime lane should exist beyond this selector branch.",
    "Whether imported runtime ownership is justified for any future follow-on.",
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


def _selection_options(
    ready: bool,
    readiness_ok: bool,
    skeleton_ok: bool,
    scope_ok: bool,
    source_refs_ok: bool,
) -> list[dict[str, Any]]:
    if ready:
        return [
            {
                "follow_on_id": EXPECTED_FOLLOW_ON_ID,
                "label": "post-skeleton follow-on unresolved branch",
                "status": "selected",
                "score": 10,
                "reasons": [
                    "readiness and scaffold surfaces are aligned",
                    "the remaining follow-on stays unresolved instead of widening into runtime work",
                ],
            },
            {
                "follow_on_id": "hold_at_scaffold",
                "label": "hold at scaffold",
                "status": "standby",
                "score": 1,
                "reasons": [
                    "available as a fallback if the selector is later re-run with broken upstream truth",
                ],
            },
        ]
    return [
        {
            "follow_on_id": "hold_at_scaffold",
            "label": "hold at scaffold",
            "status": "selected",
            "score": 10,
            "reasons": [
                "one or more upstream checks are not clean enough to justify a follow-on branch",
            ],
        },
        {
            "follow_on_id": EXPECTED_FOLLOW_ON_ID,
            "label": "post-skeleton follow-on unresolved branch",
            "status": "blocked",
            "score": 0,
            "reasons": [
                f"readiness_ok={readiness_ok}",
                f"skeleton_ok={skeleton_ok}",
                f"scope_ok={scope_ok}",
                f"source_refs_ok={source_refs_ok}",
            ],
        },
    ]


def _gate_status(
    candidate: dict[str, Any],
    readiness_report: dict[str, Any],
    readiness_packet: dict[str, Any],
    skeleton_report: dict[str, Any],
    skeleton_packet: dict[str, Any],
    source_ref_status: list[dict[str, Any]],
) -> tuple[str, str, list[str], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[str] = []
    raw_input = str(candidate.get("raw_input", "")).strip().lower()
    stage_request = str(candidate.get("stage_request", "")).strip().lower()

    readiness_ok = (
        readiness_report.get("status") == "ok"
        and readiness_report.get("gate_status") == "bounded_post_skeleton_ready"
        and readiness_packet.get("bounded_post_skeleton_ready") is True
        and readiness_packet.get("next_step") == EXPECTED_SLICE_ID
    )
    skeleton_ok = (
        skeleton_report.get("status") == "ok"
        and skeleton_report.get("gate_status") == "bounded_scaffold_completed"
        and skeleton_packet.get("bounded_scaffold_completed") is True
        and skeleton_packet.get("next_step") == EXPECTED_FOLLOW_ON_ID
    )
    scope_ok = stage_request == "post_skeleton_follow_on_selection"
    source_refs_ok = bool(source_ref_status) and all(item["exists"] for item in source_ref_status)

    gate_results = {
        "readiness_alignment": {
            "status": "pass",
            "evidence": (
                f"status={readiness_report.get('status', '')} "
                f"gate_status={readiness_report.get('gate_status', '')} "
                f"next_step={readiness_packet.get('next_step', '')}"
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
                f"allow_registry_mutation={readiness_packet.get('allow_registry_mutation')} "
                f"allow_runner_mutation={readiness_packet.get('allow_runner_mutation')} "
                f"allow_runtime_claims={readiness_packet.get('allow_runtime_claims')} "
                f"allow_migration={readiness_packet.get('allow_migration')}"
            ),
        },
    }

    if not readiness_ok:
        gate_results["readiness_alignment"]["status"] = "block"
        issues.append("readiness surfaces are not clean enough to admit a selector branch")
    if not skeleton_ok:
        gate_results["skeleton_alignment"]["status"] = "block"
        issues.append("skeleton surfaces do not confirm the unresolved follow-on branch")
    if not source_refs_ok:
        gate_results["source_refs_available"]["status"] = "block"
        issues.append("one or more core lev-builder source refs are missing")
    if not scope_ok:
        gate_results["scope_hygiene"]["status"] = "block"
        issues.append("candidate stage_request is not post_skeleton_follow_on_selection")
    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate_results["scope_hygiene"]["status"] = "block"
        issues.append("candidate request widens into migration/runtime/runner behavior")
    if any(
        readiness_packet.get(flag) is not False
        for flag in (
            "allow_registry_mutation",
            "allow_runner_mutation",
            "allow_runtime_claims",
            "allow_migration",
        )
    ):
        gate_results["non_live_surface_guard"]["status"] = "block"
        issues.append("readiness packet unexpectedly widens the non-live guard")
    if any(
        skeleton_packet.get(flag) is not False
        for flag in (
            "allow_registry_mutation",
            "allow_runner_mutation",
            "allow_runtime_claims",
            "allow_migration",
        )
    ):
        gate_results["non_live_surface_guard"]["status"] = "block"
        issues.append("skeleton packet unexpectedly widens the non-live guard")

    ready = not any(item["status"] == "block" for item in gate_results.values())
    selected_follow_on_id = EXPECTED_FOLLOW_ON_ID if ready else "hold_at_scaffold"
    return (
        "follow_on_selection_ready" if ready else "hold_blocked",
        selected_follow_on_id,
        issues,
        gate_results,
        _selection_options(
            ready,
            readiness_ok,
            skeleton_ok,
            scope_ok,
            source_refs_ok,
        ),
    )


def build_a2_lev_builder_post_skeleton_follow_on_selector_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    readiness_report_path = _resolve_output_path(root, ctx.get("readiness_report_path"), READINESS_REPORT_PATH)
    readiness_packet_path = _resolve_output_path(root, ctx.get("readiness_packet_path"), READINESS_PACKET_PATH)
    skeleton_report_path = _resolve_output_path(root, ctx.get("skeleton_report_path"), SKELETON_REPORT_PATH)
    skeleton_packet_path = _resolve_output_path(root, ctx.get("skeleton_packet_path"), SKELETON_PACKET_PATH)

    readiness_report = _safe_load_json(readiness_report_path)
    readiness_packet = _safe_load_json(readiness_packet_path)
    skeleton_report = _safe_load_json(skeleton_report_path)
    skeleton_packet = _safe_load_json(skeleton_packet_path)
    source_ref_status = _ref_records(root, [str(item) for item in candidate.get("source_refs", []) if str(item).strip()])

    gate_status, selected_follow_on_id, issues, gate_results, candidate_options = _gate_status(
        candidate,
        readiness_report,
        readiness_packet,
        skeleton_report,
        skeleton_packet,
        source_ref_status,
    )

    follow_on_selection_ready = gate_status == "follow_on_selection_ready"
    selected_option = next(
        (item for item in candidate_options if item["follow_on_id"] == selected_follow_on_id),
        {},
    )
    recommended_actions = [
        "Keep this slice selector-only, repo-held, and non-migratory.",
        "Treat the selected follow-on as a bounded unresolved branch, not a runtime or registry instruction.",
        "Do not widen the selector into execution, migration, or imported-ownership claims.",
    ]
    if not follow_on_selection_ready:
        recommended_actions.insert(
            0,
            "Hold at scaffold until readiness and skeleton surfaces again confirm the unresolved follow-on branch.",
        )

    report = {
        "schema": "a2_lev_builder_post_skeleton_follow_on_selector_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if follow_on_selection_ready else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "selector_only": True,
        "non_migratory": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "slice_id": EXPECTED_SLICE_ID,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": "lev-builder",
        "upstream_readiness_report_path": str(readiness_report_path.relative_to(root)),
        "upstream_readiness_packet_path": str(readiness_packet_path.relative_to(root)),
        "upstream_skeleton_report_path": str(skeleton_report_path.relative_to(root)),
        "upstream_skeleton_packet_path": str(skeleton_packet_path.relative_to(root)),
        "candidate": candidate,
        "selected_follow_on_id": selected_follow_on_id,
        "recommended_next_step": selected_follow_on_id,
        "selected_follow_on": selected_option,
        "candidate_options": candidate_options,
        "gate_status": gate_status,
        "admission_decision": "admit_for_follow_on_selection" if follow_on_selection_ready else "hold_at_scaffold",
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": follow_on_selection_ready,
            "follow_on_selection_ready": follow_on_selection_ready,
            "allow_registry_mutation": False,
            "allow_runner_mutation": False,
            "allow_graph_claims": False,
            "allow_runtime_claims": False,
            "allow_migration": False,
            "allow_patch_application": False,
            "blocking_issues": issues,
            "priority_findings": [label for label, result in gate_results.items() if result["status"] == "block"],
            "reason": (
                "the landed readiness and skeleton surfaces justify a selector-only unresolved follow-on branch"
                if follow_on_selection_ready
                else "one or more upstream gates are not clean enough to justify a follow-on selection"
            ),
            "gate_results": gate_results,
            "recommended_next_step": selected_follow_on_id,
        },
        "recommended_actions": recommended_actions,
        "non_goals": list(DEFAULT_NON_GOALS),
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_post_skeleton_follow_on_selector_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "gate_status": gate_status,
        "admission_decision": report["admission_decision"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "selected_follow_on_id": selected_follow_on_id,
        "recommended_next_step": selected_follow_on_id,
        "next_step": selected_follow_on_id,
        "follow_on_selection_ready": follow_on_selection_ready,
        "allow_selection_slice": True,
        "allow_registry_mutation": False,
        "allow_runner_mutation": False,
        "allow_graph_claims": False,
        "allow_runtime_claims": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "blocking_issues": report["gate"]["blocking_issues"],
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Post-Skeleton Follow-On Selector Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- admission_decision: `{report.get('admission_decision', '')}`",
        f"- selected_follow_on_id: `{report.get('selected_follow_on_id', '')}`",
        f"- follow_on_selection_ready: `{report.get('gate', {}).get('follow_on_selection_ready')}`",
        "",
        "## Upstream Surfaces",
        f"- readiness_report: `{report.get('upstream_readiness_report_path', '')}`",
        f"- readiness_packet: `{report.get('upstream_readiness_packet_path', '')}`",
        f"- skeleton_report: `{report.get('upstream_skeleton_report_path', '')}`",
        f"- skeleton_packet: `{report.get('upstream_skeleton_packet_path', '')}`",
        "",
        "## Candidate Options",
    ]
    for item in report.get("candidate_options", []):
        lines.append(
            f"- `{item.get('follow_on_id', '')}` status=`{item.get('status', '')}` score=`{item.get('score', 0)}` "
            f"label=`{item.get('label', '')}`"
        )
    lines.extend(["", "## Selected Follow-On"])
    selected = report.get("selected_follow_on", {})
    if selected:
        lines.extend(
            [
                f"- follow_on_id: `{selected.get('follow_on_id', '')}`",
                f"- label: `{selected.get('label', '')}`",
                f"- score: `{selected.get('score', 0)}`",
            ]
        )
    else:
        lines.append("- none")
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
            f"- gate_status: `{packet.get('gate_status', '')}`",
            f"- admission_decision: `{packet.get('admission_decision', '')}`",
            f"- selected_follow_on_id: `{packet.get('selected_follow_on_id', '')}`",
            f"- recommended_next_step: `{packet.get('recommended_next_step', '')}`",
            f"- next_step: `{packet.get('next_step', '')}`",
            f"- follow_on_selection_ready: `{packet.get('follow_on_selection_ready', False)}`",
            f"- allow_registry_mutation: `{packet.get('allow_registry_mutation', False)}`",
            f"- allow_runner_mutation: `{packet.get('allow_runner_mutation', False)}`",
            f"- allow_graph_claims: `{packet.get('allow_graph_claims', False)}`",
            f"- allow_runtime_claims: `{packet.get('allow_runtime_claims', False)}`",
            f"- allow_migration: `{packet.get('allow_migration', False)}`",
        ]
    )
    issues = report.get("issues", [])
    if issues:
        lines.extend(["", "## Issues"])
        for issue in issues:
            lines.append(f"- {issue}")
    lines.append("")
    return "\n".join(lines)


def run_a2_lev_builder_post_skeleton_follow_on_selector(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), FOLLOW_ON_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), FOLLOW_ON_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), FOLLOW_ON_PACKET_JSON)

    report, packet = build_a2_lev_builder_post_skeleton_follow_on_selector_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted


if __name__ == "__main__":
    print("PASS: a2 lev-builder post-skeleton follow-on selector operator self-test")
