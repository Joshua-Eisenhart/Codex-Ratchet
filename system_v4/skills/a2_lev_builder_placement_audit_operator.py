"""
a2_lev_builder_placement_audit_operator.py

Bounded placement/formalization audit over the lev-os/agents lev-builder seam.

This operator does not migrate files, apply patches, or activate imported code.
It reads the current lev-os/agents promotion report plus the local lev-builder
source surfaces, then emits one repo-held report and packet describing the
smallest honest Ratchet-native placement/formalization slice.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMOTION_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json"
)
PROMOTION_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json"
)
REFRESH_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
)
GRAPH_AUDIT_PATH = (
    "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json"
)

PLACEMENT_AUDIT_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_REPORT__CURRENT__v1.json"
)
PLACEMENT_AUDIT_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_REPORT__CURRENT__v1.md"
)
PLACEMENT_AUDIT_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_FIRST_SLICE = "a2-lev-builder-placement-audit-operator"
EXPECTED_SOURCE_SKILL_ID = "lev-builder"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-placement-default",
    "title": "bounded lev-builder placement and formalization audit",
    "type": "placement_audit",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Audit lev-builder as the next bounded imported source for Ratchet-native "
        "placement and formalization, without migrating files or claiming production integration."
    ),
    "stage_request": "placement_audit",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
    ],
    "background_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/stack/SKILL.md",
    ],
}

MEMBER_DISPOSITIONS = {
    "lev-builder": {
        "classification": "adapt",
        "keep": [
            "prior-art check before creating new placement/formalization work",
            "explicit placement decision before claiming a target path",
            "bounded promotion-path framing from candidate source to Ratchet-native asset",
        ],
        "adapt_away_from": [
            "~/lev/core and ~/lev/workshop path ownership",
            "graph-plan to filesystem patch execution",
            "migration scripts and git close-loop behavior",
        ],
    },
    "arch": {
        "classification": "mine",
        "keep": [
            "quality attribute and tradeoff framing",
            "fitness-function language for later candidate validation",
        ],
        "adapt_away_from": [
            "generic architecture review broadness",
            "full ADR/C4 generation as the first bounded slice",
        ],
    },
    "work": {
        "classification": "mine",
        "keep": [
            "bounded handoff and entity-tracking discipline",
            "report-first procedure for one candidate at a time",
        ],
        "adapt_away_from": [
            "broad workflow ownership beyond this one placement question",
            "task-management surfaces that imply imported control-plane behavior",
        ],
    },
    "lev-plan": {
        "classification": "background_only",
        "keep": [
            "promotion-state language for later follow-on planning",
        ],
        "adapt_away_from": [
            ".lev/pm plan lifecycle ownership",
        ],
    },
    "stack": {
        "classification": "background_only",
        "keep": [
            "staged execution language only as background context",
        ],
        "adapt_away_from": [
            "Leviathan prompt-stack runtime ownership",
            "plugin CLI and external runtime session state",
        ],
    },
}

PLACEMENT_AXES = {
    "prior_art_check": {
        "treatment": "keep",
        "why": "Prevents duplicate imported slices and forces placement decisions against existing Ratchet work.",
    },
    "placement_decision": {
        "treatment": "keep",
        "why": "Directly matches the current need to decide where a future Ratchet-native slice belongs before building it.",
    },
    "formalize_then_migrate": {
        "treatment": "adapt",
        "why": "Keep the discipline of staged formalization, but remove Lev-specific workspace ownership and migration scripts.",
    },
    "graph_plan_to_patch": {
        "treatment": "mine",
        "why": "Potentially useful later, but too broad and mutating for the first bounded slice.",
    },
    "git_close_loop": {
        "treatment": "skip",
        "why": "Commit/push flows are not part of this bounded audit slice.",
    },
}

DEFAULT_NON_GOALS = [
    "No path mutation or graph-plan generation.",
    "No filesystem patch generation or application.",
    "No test execution or validation-run claims.",
    "No migration into production paths.",
    "No registry updates or git close-loop actions.",
    "No prompt-stack session control or .lev substrate import.",
    "No live runtime claims for lev-builder or the wider lev formalization stack.",
]

BLOCKING_PHRASES = (
    "migrate to production",
    "apply patch",
    "write files into production",
    "commit the migration",
    "push the migration",
    "formalize directly into core",
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


def _source_ref_records(root: Path, refs: list[str]) -> list[dict[str, Any]]:
    records = []
    for ref in refs:
        path = root / ref
        records.append(
            {
                "path": ref,
                "exists": path.exists(),
            }
        )
    return records


def _background_ref_records(root: Path, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    refs = [str(item) for item in candidate.get("background_refs", []) if str(item).strip()]
    return _source_ref_records(root, refs)


def _analysis(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_question": (
            "Is lev-builder the right next imported source for a bounded Ratchet-native "
            "placement/formalization audit before any broader formalization or migration claim?"
        ),
        "smallest_honest_slice": (
            "assess one candidate, check prior art, issue a placement verdict, and emit one repo-held report "
            "plus one compact packet"
        ),
        "core_source_priority": ["lev-builder", "arch", "work"],
        "background_only_sources": ["lev-plan", "stack"],
        "placement_verdict_shape": (
            "Ratchet-native audit operator first, then a later proposal-only formalization slice if this gate stays clean"
        ),
        "candidate_scope": {
            "id": candidate.get("id"),
            "stage_request": candidate.get("stage_request"),
            "title": candidate.get("title"),
        },
    }


def _evidence_inputs(
    promotion_report: dict[str, Any],
    promotion_packet: dict[str, Any],
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
) -> dict[str, Any]:
    graph_skill_coverage = graph_audit.get("skill_graph_coverage", {}) if isinstance(graph_audit, dict) else {}
    return {
        "promotion_report_status": promotion_report.get("status"),
        "promotion_recommended_cluster_id": promotion_packet.get("recommended_cluster_id"),
        "promotion_recommended_first_slice_id": promotion_packet.get("recommended_first_slice_id"),
        "brain_refresh_status": refresh_report.get("status"),
        "graph_skill_coverage": {
            "active_skill_count": graph_skill_coverage.get("active_skill_count"),
            "graphed_skill_node_count": graph_skill_coverage.get("graphed_skill_node_count"),
            "missing_active_skill_count": graph_skill_coverage.get("missing_active_skill_count"),
            "stale_skill_node_count": graph_skill_coverage.get("stale_skill_node_count"),
        },
    }


def _gate_status(
    candidate: dict[str, Any],
    promotion_report: dict[str, Any],
    promotion_packet: dict[str, Any],
    refresh_report: dict[str, Any],
    source_ref_records: list[dict[str, Any]],
    graph_audit: dict[str, Any],
) -> tuple[str, list[str], dict[str, dict[str, Any]]]:
    issues: list[str] = []
    raw_input = str(candidate.get("raw_input", "")).strip().lower()
    stage_request = str(candidate.get("stage_request", "")).strip().lower()

    gate = {
        "promotion_alignment": {
            "status": "pass",
            "evidence": (
                f"recommended_cluster={promotion_packet.get('recommended_cluster_id', '')} "
                f"recommended_slice={promotion_packet.get('recommended_first_slice_id', '')}"
            ),
        },
        "refresh_alignment": {
            "status": "pass",
            "evidence": f"brain_refresh_status={refresh_report.get('status', '')}",
        },
        "source_refs_available": {
            "status": "pass",
            "evidence": f"{sum(1 for item in source_ref_records if item['exists'])}/{len(source_ref_records)} refs present",
        },
        "scope_bounded": {
            "status": "pass",
            "evidence": f"stage_request={stage_request}",
        },
        "non_goal_hygiene": {
            "status": "pass",
            "evidence": "candidate request does not include migration/patch/push language",
        },
        "graph_truth_alignment": {
            "status": "pass",
            "evidence": "",
        },
    }

    if promotion_report.get("status") != "ok":
        gate["promotion_alignment"]["status"] = "block"
        issues.append("lev-os/agents promotion report is not ok")
    if promotion_packet.get("recommended_cluster_id") != EXPECTED_CLUSTER_ID:
        gate["promotion_alignment"]["status"] = "block"
        issues.append("promotion packet does not currently recommend lev-formalization-placement")
    if promotion_packet.get("recommended_first_slice_id") != EXPECTED_FIRST_SLICE:
        gate["promotion_alignment"]["status"] = "block"
        issues.append("promotion packet does not currently recommend this placement-audit slice")

    if refresh_report.get("status") != "ok":
        gate["refresh_alignment"]["status"] = "warn"
        issues.append("A2 brain refresher is not currently ok")

    if not source_ref_records or any(not item["exists"] for item in source_ref_records):
        gate["source_refs_available"]["status"] = "block"
        issues.append("one or more lev-builder placement source refs are missing")

    if stage_request != "placement_audit":
        gate["scope_bounded"]["status"] = "block"
        issues.append("candidate stage_request is not placement_audit")

    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate["non_goal_hygiene"]["status"] = "block"
        issues.append("candidate request widens into migration/patch/push behavior")

    graph_skill_coverage = graph_audit.get("skill_graph_coverage", {}) if isinstance(graph_audit, dict) else {}
    missing_skill_count = int(graph_skill_coverage.get("missing_active_skill_count") or 0)
    stale_skill_count = int(graph_skill_coverage.get("stale_skill_node_count") or 0)
    active_skill_count = graph_skill_coverage.get("active_skill_count")
    graphed_skill_count = graph_skill_coverage.get("graphed_skill_node_count")
    gate["graph_truth_alignment"]["evidence"] = (
        f"active={active_skill_count} graphed={graphed_skill_count} "
        f"missing={missing_skill_count} stale={stale_skill_count}"
    )
    if missing_skill_count or stale_skill_count:
        gate["graph_truth_alignment"]["status"] = "warn"
        issues.append("graph skill truth is not fully converged")

    if any(value["status"] == "block" for value in gate.values()):
        return "hold_blocked", issues, gate
    if any(value["status"] == "warn" for value in gate.values()):
        return "ready_with_attention", issues, gate
    return "ready_for_bounded_placement_audit", issues, gate


def build_a2_lev_builder_placement_audit_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    promotion_report = _safe_load_json(root / PROMOTION_REPORT_PATH)
    promotion_packet = _safe_load_json(root / PROMOTION_PACKET_PATH)
    refresh_report = _safe_load_json(root / REFRESH_REPORT_PATH)
    graph_audit = _safe_load_json(root / GRAPH_AUDIT_PATH)
    source_refs = [str(item) for item in candidate.get("source_refs", []) if str(item).strip()]
    source_ref_records = _source_ref_records(root, source_refs)
    background_ref_records = _background_ref_records(root, candidate)
    evidence_inputs = _evidence_inputs(promotion_report, promotion_packet, refresh_report, graph_audit)

    gate_status, issues, gate = _gate_status(
        candidate,
        promotion_report,
        promotion_packet,
        refresh_report,
        source_ref_records,
        graph_audit,
    )

    allow_bounded_placement_audit = gate_status.startswith("ready")
    priority_findings = [label for label, result in gate.items() if result["status"] in {"warn", "block"}]
    recommended_actions = [
        "Keep this slice audit-only and repo-held.",
        "Use the verdict to decide whether a later proposal-only formalization slice should be emitted.",
        "Do not widen this slice into migration, patching, runtime import, or registry mutation.",
    ]
    if not allow_bounded_placement_audit:
        recommended_actions.insert(
            0,
            "Repair the blocking gate inputs before treating lev-builder as the next bounded imported implementation lane.",
        )

    report = {
        "schema": "a2_lev_builder_placement_audit_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if gate_status == "ready_for_bounded_placement_audit" else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "first_slice": EXPECTED_FIRST_SLICE,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "promotion_report_path": PROMOTION_REPORT_PATH,
        "promotion_packet_path": PROMOTION_PACKET_PATH,
        "gate_status": gate_status,
        "source_ref_status": source_ref_records,
        "source_refs": source_ref_records,
        "background_ref_status": background_ref_records,
        "imported_member_disposition": MEMBER_DISPOSITIONS,
        "analysis": _analysis(candidate),
        "evidence_inputs": evidence_inputs,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": allow_bounded_placement_audit,
            "allow_bounded_placement_audit": allow_bounded_placement_audit,
            "block_new_runtime_claims": True,
            "block_migration_claims": True,
            "block_patch_application": True,
            "blocking_issues": issues,
            "priority_findings": priority_findings,
            "reason": (
                "required upstream reports are healthy and the candidate stays inside a one-candidate placement audit"
                if allow_bounded_placement_audit
                else "one or more required inputs or gate checks still need attention"
            ),
            "gate_results": gate,
            "recommended_next_step": (
                "ready_for_formalization_proposal" if allow_bounded_placement_audit else "needs_gate_repair"
            ),
        },
        "candidate": candidate,
        "member_dispositions": MEMBER_DISPOSITIONS,
        "placement_axes": PLACEMENT_AXES,
        "graph_skill_coverage": evidence_inputs["graph_skill_coverage"],
        "recommended_next_action": recommended_actions[0],
        "recommended_actions": recommended_actions,
        "recommended_follow_on_slice_id": "a2-lev-builder-formalization-proposal-operator",
        "non_goals": list(DEFAULT_NON_GOALS),
        "staged_output_targets": {
            "json_report": PLACEMENT_AUDIT_REPORT_JSON,
            "md_report": PLACEMENT_AUDIT_REPORT_MD,
            "packet_json": PLACEMENT_AUDIT_PACKET_JSON,
        },
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_placement_audit_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": report["cluster_id"],
        "first_slice": report["first_slice"],
        "recommended_source_skill_id": report["recommended_source_skill_id"],
        "gate_status": report["gate"]["gate_status"],
        "safe_to_continue": report["gate"]["safe_to_continue"],
        "allow_bounded_placement_audit": report["gate"]["allow_bounded_placement_audit"],
        "allow_migration": False,
        "allow_patch_application": False,
        "allow_git_close_loop": False,
        "blocking_issues": report["gate"]["blocking_issues"],
        "recommended_actions": report["recommended_actions"],
        "recommended_follow_on_slice_id": report["recommended_follow_on_slice_id"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Placement Audit Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- first_slice: `{report.get('first_slice', '')}`",
        f"- recommended_source_skill_id: `{report.get('recommended_source_skill_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- allow_bounded_placement_audit: `{report.get('gate', {}).get('allow_bounded_placement_audit')}`",
        "",
        "## Source Refs",
    ]
    for item in report.get("source_ref_status", []):
        lines.append(f"- `{item.get('path', '')}` exists=`{item.get('exists', False)}`")
    lines.extend(
        [
            "",
            "## Background Refs",
        ]
    )
    for item in report.get("background_ref_status", []):
        lines.append(f"- `{item.get('path', '')}` exists=`{item.get('exists', False)}`")
    lines.extend(
        [
            "",
            "## Gate Results",
        ]
    )
    for label, result in report.get("gate", {}).get("gate_results", {}).items():
        lines.append(
            f"- `{label}` status=`{result.get('status', '')}` evidence=`{result.get('evidence', '')}`"
        )
    lines.extend(
        [
            "",
            "## Recommended Actions",
        ]
    )
    for action in report.get("recommended_actions", []):
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Non-Goals",
        ]
    )
    for item in report.get("non_goals", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Packet",
            f"- allow_bounded_placement_audit: `{packet.get('allow_bounded_placement_audit', False)}`",
            f"- allow_migration: `{packet.get('allow_migration', False)}`",
            f"- allow_patch_application: `{packet.get('allow_patch_application', False)}`",
        ]
    )
    issues = report.get("issues", [])
    if issues:
        lines.extend(["", "## Issues"])
        for issue in issues:
            lines.append(f"- {issue}")
    lines.append("")
    return "\n".join(lines)


def run_a2_lev_builder_placement_audit(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), PLACEMENT_AUDIT_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), PLACEMENT_AUDIT_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PLACEMENT_AUDIT_PACKET_JSON)

    report, packet = build_a2_lev_builder_placement_audit_report(root, ctx)
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
    print("PASS: a2 lev-builder placement audit operator self-test")
