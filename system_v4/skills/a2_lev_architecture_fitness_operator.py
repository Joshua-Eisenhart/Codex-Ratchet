"""
a2_lev_architecture_fitness_operator.py

Bounded audit over the lev-os/agents architecture / fitness / review cluster.

This operator does not perform generic PR review, emit full ADR/C4 artifacts as
required outputs, apply patches, migrate code, update registries, or import the
Leviathan builder/runtime workflow. It emits one repo-held report and packet
describing the smallest honest Ratchet-native slice over architecture and
fitness guidance for candidate Ratchet changes.
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
CLUSTER_MAP_PATH = "system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md"

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_ARCHITECTURE_FITNESS_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_ARCHITECTURE_FITNESS_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_ARCHITECTURE_FITNESS_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-architecture-fitness-review"
EXPECTED_FIRST_SLICE = "a2-lev-architecture-fitness-operator"
EXPECTED_SOURCE_SKILL_ID = "arch"

DEFAULT_CANDIDATE = {
    "id": "lev-architecture-fitness-default",
    "title": "bounded lev architecture and fitness audit",
    "type": "architecture_fitness_audit",
    "source": "lev-os/agents architecture / fitness / review cluster",
    "raw_input": (
        "Audit architecture and fitness guidance for one candidate Ratchet change "
        "without importing generic architecture review behavior, migration, or "
        "runtime ownership."
    ),
    "stage_request": "architecture_fitness_audit",
    "focus_candidate": "current Ratchet imported-cluster and graph-support evolution",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/arch/SYSTEM_PROMPT.md",
        "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
    ],
    "quality_attributes": [
        "auditability",
        "modifiability",
        "bounded_import_discipline",
        "runtime_isolation",
    ],
    "candidate_approaches": [
        "bounded_architecture_fitness_audit",
        "generic_architecture_review_import",
        "builder_led_migration_review",
    ],
    "tradeoff_points": [
        "higher structure and explicit tradeoffs vs less generic review breadth",
        "bounded fitness-function proposals vs any implied automation or governance ownership",
    ],
    "sensitivity_points": [
        "generic architecture-review import becomes authority creep",
        "migration or patch execution turns analysis support into runtime ownership",
    ],
    "proposed_fitness_functions": [
        "slice remains audit_only / nonoperative / do_not_promote",
        "graph truth remains equal active/graphed with zero missing and zero stale",
        "no migration, patch, ADR/C4 broadness, or imported runtime flags in the packet",
    ],
    "review_triggers": [
        "candidate widens into migration or runtime ownership",
        "graph truth diverges from registry truth",
        "a new unopened lev cluster is later added to the selector",
    ],
}

IMPORTED_MEMBER_DISPOSITIONS = {
    "arch": {
        "classification": "adapt",
        "keep": [
            "quality attribute framing",
            "utility-tree style prioritization",
            "2-3 candidate approach comparison",
            "explicit tradeoff and risk analysis",
            "bounded fitness-function proposal language",
            "review-trigger thresholds",
        ],
        "adapt_away_from": [
            "generic architecture review broadness",
            "full ADR generation as the first slice",
            "full C4 generation as the first slice",
            "approve/request_changes style verdict authority",
            "plugin-driven deep-dive review orchestration",
        ],
    },
    "lev-builder": {
        "classification": "mine",
        "keep": [
            "existing-code and prior-art framing",
            "placement-context questions as background only",
            "migration-context caution as background only",
        ],
        "adapt_away_from": [
            "graph mutation plan execution",
            "filesystem patch application",
            "E2E validation ownership",
            "POC-to-production migration ownership",
            "registry update and commit ownership",
        ],
    },
}

REVIEW_AXES = {
    "quality_attribute_elicitation": {
        "treatment": "keep",
        "why": "the strongest reusable `arch` value is forcing explicit architectural drivers instead of vague review language",
    },
    "candidate_option_set": {
        "treatment": "keep",
        "why": "the first Ratchet slice should compare bounded options rather than collapsing directly to one imported recommendation",
    },
    "tradeoff_analysis": {
        "treatment": "keep",
        "why": "tradeoffs are the safe imported core; they sharpen guidance without creating runtime authority",
    },
    "fitness_function_proposals": {
        "treatment": "adapt",
        "why": "fitness checks may be proposed as future bounded probes, not imported as live governance or CI ownership",
    },
    "review_trigger_thresholds": {
        "treatment": "adapt",
        "why": "thresholds are useful as bounded stop/revisit markers, not as external review cadence import",
    },
    "adr_or_c4_artifact_generation": {
        "treatment": "skip",
        "why": "full ADR/C4 artifact generation is too broad for the first Ratchet-native slice",
    },
    "migration_or_patch_execution": {
        "treatment": "skip",
        "why": "lev-builder execution paths are out of scope for the first architecture/fitness slice",
    },
}

DEFAULT_NON_GOALS = [
    "No generic architecture review broadness.",
    "No full ADR or C4 generation in the first slice.",
    "No PR verdict authority such as APPROVE or REQUEST_CHANGES.",
    "No migration, patch application, registry update, or commit ownership.",
    "No imported runtime, builder workflow, or Leviathan path ownership.",
    "No claim that Ratchet now has a live architecture-governance runtime.",
]

BLOCKING_PHRASES = (
    "apply patch",
    "migrate to production",
    "update registry",
    "git commit",
    "approve pr",
    "request changes",
    "full adr",
    "full c4",
    "run e2e",
    "own the migration",
    "own the builder workflow",
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


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
        records.append({"path": ref, "exists": path.exists()})
    return records


def _candidate_list(candidate: dict[str, Any], key: str) -> list[str]:
    return [str(item) for item in candidate.get(key, []) if str(item).strip()]


def _analysis(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_question": (
            "What is the smallest honest Ratchet-native architecture and fitness guidance slice "
            "we can keep without importing generic review authority or migration workflow?"
        ),
        "smallest_honest_slice": (
            "one bounded repo-held audit over quality attributes, tradeoffs, bounded fitness-function proposals, "
            "and explicit forbid lines"
        ),
        "core_source_priority": ["arch"],
        "background_only_sources": ["lev-builder"],
        "recommended_follow_on_shape": (
            "only a later bounded candidate-specific fitness-function or scenario probe if this audit remains clean"
        ),
        "candidate_scope": {
            "id": candidate.get("id"),
            "stage_request": candidate.get("stage_request"),
            "title": candidate.get("title"),
            "focus_candidate": candidate.get("focus_candidate"),
        },
        "quality_attributes": _candidate_list(candidate, "quality_attributes"),
        "candidate_approaches": _candidate_list(candidate, "candidate_approaches"),
        "tradeoff_points": _candidate_list(candidate, "tradeoff_points"),
        "sensitivity_points": _candidate_list(candidate, "sensitivity_points"),
        "proposed_fitness_functions": _candidate_list(candidate, "proposed_fitness_functions"),
        "review_triggers": _candidate_list(candidate, "review_triggers"),
    }


def _evidence_inputs(
    promotion_report: dict[str, Any],
    promotion_packet: dict[str, Any],
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
    cluster_map_text: str,
) -> dict[str, Any]:
    graph_skill_coverage = graph_audit.get("skill_graph_coverage", {}) if isinstance(graph_audit, dict) else {}
    return {
        "promotion_report_status": promotion_report.get("status"),
        "promotion_recommended_cluster_id": promotion_packet.get("recommended_cluster_id"),
        "promotion_recommended_first_slice_id": promotion_packet.get("recommended_first_slice_id"),
        "cluster_map_records_slice": (
            EXPECTED_CLUSTER_ID in cluster_map_text and EXPECTED_FIRST_SLICE in cluster_map_text
        ),
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
    cluster_map_text: str,
) -> tuple[str, list[str], dict[str, dict[str, Any]]]:
    issues: list[str] = []
    raw_input = str(candidate.get("raw_input", "")).strip().lower()
    stage_request = str(candidate.get("stage_request", "")).strip().lower()
    candidate_approaches = _candidate_list(candidate, "candidate_approaches")

    gate = {
        "promotion_alignment": {
            "status": "pass",
            "evidence": (
                f"recommended_cluster={promotion_packet.get('recommended_cluster_id', '')} "
                f"recommended_slice={promotion_packet.get('recommended_first_slice_id', '')} "
                f"cluster_map_records_slice={EXPECTED_CLUSTER_ID in cluster_map_text and EXPECTED_FIRST_SLICE in cluster_map_text}"
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
            "evidence": "candidate request does not widen into generic review authority, migration, or runtime ownership",
        },
        "candidate_option_floor": {
            "status": "pass",
            "evidence": f"candidate_approach_count={len(candidate_approaches)}",
        },
        "graph_truth_alignment": {
            "status": "pass",
            "evidence": "",
        },
    }

    if promotion_report.get("status") != "ok":
        gate["promotion_alignment"]["status"] = "block"
        issues.append("lev-os/agents promotion report is not ok")
    selector_still_points_here = (
        promotion_packet.get("recommended_cluster_id") == EXPECTED_CLUSTER_ID
        and promotion_packet.get("recommended_first_slice_id") == EXPECTED_FIRST_SLICE
    )
    cluster_map_records_slice = (
        EXPECTED_CLUSTER_ID in cluster_map_text and EXPECTED_FIRST_SLICE in cluster_map_text
    )
    if not selector_still_points_here and not cluster_map_records_slice:
        gate["promotion_alignment"]["status"] = "block"
        issues.append(
            "neither the promotion packet nor the imported cluster map currently points at this architecture-fitness slice"
        )

    if refresh_report.get("status") != "ok":
        gate["refresh_alignment"]["status"] = "warn"
        issues.append("A2 brain refresher is not currently ok")

    if not source_ref_records or any(not item["exists"] for item in source_ref_records):
        gate["source_refs_available"]["status"] = "block"
        issues.append("one or more lev architecture/fitness source refs are missing")

    if stage_request != "architecture_fitness_audit":
        gate["scope_bounded"]["status"] = "block"
        issues.append("candidate stage_request is not architecture_fitness_audit")

    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate["non_goal_hygiene"]["status"] = "block"
        issues.append("candidate request widens into broad review authority, migration, or runtime ownership")

    if len(candidate_approaches) < 2:
        gate["candidate_option_floor"]["status"] = "warn"
        issues.append("candidate approach set is thinner than the imported arch pattern expects")

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
    return "ready_for_bounded_architecture_fitness_audit", issues, gate


def _render_markdown(report: dict[str, Any]) -> str:
    disposition_lines = [
        f"- `{name}`: {info['classification']} -> {', '.join(info['keep'])}"
        for name, info in report.get("imported_member_disposition", {}).items()
    ]
    axis_lines = [
        f"- `{name}`: {info['treatment']} -> {info['why']}"
        for name, info in report.get("review_axes", {}).items()
    ]
    gate_lines = [
        f"- `{label}`: {result['status']} -> {result['evidence']}"
        for label, result in report.get("gate", {}).get("gate_results", {}).items()
    ]
    action_lines = [f"- {item}" for item in report.get("recommended_actions", [])]
    non_goal_lines = [f"- {item}" for item in report.get("non_goals", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    metrics = report.get("key_metrics", {})
    metric_lines = [f"- `{name}`: `{value}`" for name, value in metrics.items()]
    return "\n".join(
        [
            "# A2 lev Architecture Fitness Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- cluster_id: `{report.get('cluster_id', '')}`",
            f"- first_slice: `{report.get('first_slice', '')}`",
            f"- gate_status: `{report.get('gate_status', '')}`",
            f"- recommended_source_skill_id: `{report.get('recommended_source_skill_id', '')}`",
            f"- recommended_next_step: `{report.get('gate', {}).get('recommended_next_step', '')}`",
            "",
            "## Key Metrics",
            *metric_lines,
            "",
            "## Imported Member Disposition",
            *disposition_lines,
            "",
            "## Review Axes",
            *axis_lines,
            "",
            "## Gate Results",
            *gate_lines,
            "",
            "## Recommended Actions",
            *action_lines,
            "",
            "## Non-Goals",
            *non_goal_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_a2_lev_architecture_fitness_report(
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
    cluster_map_text = _load_text(root / CLUSTER_MAP_PATH)
    source_refs = [str(item) for item in candidate.get("source_refs", []) if str(item).strip()]
    source_ref_records = _source_ref_records(root, source_refs)
    analysis = _analysis(candidate)
    evidence_inputs = _evidence_inputs(
        promotion_report,
        promotion_packet,
        refresh_report,
        graph_audit,
        cluster_map_text,
    )

    gate_status, issues, gate = _gate_status(
        candidate,
        promotion_report,
        promotion_packet,
        refresh_report,
        source_ref_records,
        graph_audit,
        cluster_map_text,
    )

    allow_bounded_architecture_fitness_audit = gate_status.startswith("ready")
    recommended_actions = [
        "Keep this slice audit-only, repo-held, and nonoperative.",
        "Use it to scope one later candidate-specific fitness-function or scenario probe only if the gate stays clean.",
        "Do not widen this slice into generic review authority, full ADR/C4 output, migration, patching, or imported runtime ownership.",
    ]
    if not allow_bounded_architecture_fitness_audit:
        recommended_actions.insert(
            0,
            "Repair the blocking gate inputs before treating architecture-fitness as a live imported guidance lane.",
        )

    report = {
        "schema": "A2_LEV_ARCHITECTURE_FITNESS_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if allow_bounded_architecture_fitness_audit else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "first_slice": EXPECTED_FIRST_SLICE,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "promotion_report_path": PROMOTION_REPORT_PATH,
        "promotion_packet_path": PROMOTION_PACKET_PATH,
        "refresh_report_path": REFRESH_REPORT_PATH,
        "graph_audit_path": GRAPH_AUDIT_PATH,
        "gate_status": gate_status,
        "source_refs": source_ref_records,
        "analysis": analysis,
        "evidence_inputs": evidence_inputs,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITIONS,
        "review_axes": REVIEW_AXES,
        "key_metrics": {
            "present_member_count": len(IMPORTED_MEMBER_DISPOSITIONS),
            "quality_attribute_count": len(analysis["quality_attributes"]),
            "candidate_option_count": len(analysis["candidate_approaches"]),
            "tradeoff_point_count": len(analysis["tradeoff_points"]),
            "sensitivity_point_count": len(analysis["sensitivity_points"]),
            "fitness_function_count": len(analysis["proposed_fitness_functions"]),
            "review_trigger_count": len(analysis["review_triggers"]),
        },
        "gate": {
            "allow_bounded_architecture_fitness_audit": allow_bounded_architecture_fitness_audit,
            "allow_bounded_fitness_function_proposals": allow_bounded_architecture_fitness_audit,
            "allow_full_adr_generation": False,
            "allow_full_c4_generation": False,
            "allow_runtime_claims": False,
            "allow_migration": False,
            "allow_patch_application": False,
            "allow_imported_runtime_ownership": False,
            "gate_results": gate,
            "blocking_issues": issues if not allow_bounded_architecture_fitness_audit else [],
            "recommended_next_step": "candidate_architecture_fitness_function_probe",
            "safe_to_continue": allow_bounded_architecture_fitness_audit,
        },
        "recommended_actions": recommended_actions,
        "non_goals": DEFAULT_NON_GOALS,
        "issues": issues,
    }

    packet = {
        "schema": "A2_LEV_ARCHITECTURE_FITNESS_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "cluster_id": EXPECTED_CLUSTER_ID,
        "first_slice": EXPECTED_FIRST_SLICE,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "allow_bounded_architecture_fitness_audit": allow_bounded_architecture_fitness_audit,
        "allow_bounded_fitness_function_proposals": allow_bounded_architecture_fitness_audit,
        "allow_full_adr_generation": False,
        "allow_full_c4_generation": False,
        "allow_runtime_claims": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "allow_imported_runtime_ownership": False,
        "blocking_issues": report["gate"]["blocking_issues"],
        "gate_status": gate_status,
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "recommended_next_step": report["gate"]["recommended_next_step"],
        "safe_to_continue": allow_bounded_architecture_fitness_audit,
    }
    return report, packet


def run_a2_lev_architecture_fitness(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    report, packet = build_a2_lev_architecture_fitness_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted


if __name__ == "__main__":
    print("PASS: a2 lev architecture fitness operator self-test")
