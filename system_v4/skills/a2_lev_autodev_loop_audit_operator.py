"""
a2_lev_autodev_loop_audit_operator.py

Bounded audit over the lev-os/agents autodev / execution / validation cluster.

This operator does not schedule ticks, run heartbeat loops, own `.lev` plan
surfaces, control prompt-stack sessions, or import the lev autodev runtime.
It emits one repo-held report and packet describing the smallest honest
Ratchet-native slice over the autodev loop seam.
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
    "system_v4/a2_state/audit_logs/A2_LEV_AUTODEV_LOOP_AUDIT_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_AUTODEV_LOOP_AUDIT_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_AUTODEV_LOOP_AUDIT_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-autodev-exec-validation"
EXPECTED_FIRST_SLICE = "a2-lev-autodev-loop-audit-operator"
EXPECTED_SOURCE_SKILL_ID = "autodev-loop"

DEFAULT_CANDIDATE = {
    "id": "lev-autodev-loop-default",
    "title": "bounded lev-autodev loop-shape audit",
    "type": "autodev_loop_audit",
    "source": "lev-os/agents autodev / execution / validation cluster",
    "raw_input": (
        "Audit autodev-loop as the next bounded imported source for Ratchet-native "
        "execution and validation loop shape, without importing cron, heartbeat "
        "runtime continuity, or `.lev` ownership."
    ),
    "stage_request": "autodev_loop_audit",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/autodev-loop/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/autodev-lev/SKILL.md",
        "work/reference_repos/lev-os/leviathan/plugins/core-sdlc/src/commands/autodev.ts",
    ],
    "background_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/stack/SKILL.md",
        "work/reference_repos/lev-os/leviathan/plugins/core-sdlc/support/README.md",
        "work/reference_repos/lev-os/leviathan/core/poly/src/surfaces/cli/index.ts",
    ],
}

IMPORTED_MEMBER_DISPOSITIONS = {
    "autodev-loop": {
        "classification": "adapt",
        "keep": [
            "one-tick execution / validation separation",
            "priority waterfall over sweep, validate, execute, and bounded hygiene",
            "explicit stop conditions instead of infinite autonomy claims",
        ],
        "adapt_away_from": [
            "CronCreate ownership",
            "bd queue dependence",
            "`.lev/pm/handoffs/` tick log ownership",
            "hygiene proposal generation as a live control-plane replacement",
        ],
    },
    "autodev-lev": {
        "classification": "mine",
        "keep": [
            "heartbeat exit-condition framing",
            "circuit-breaker language",
            "separation of zero-cost scan from token-spend execution as a pattern only",
        ],
        "adapt_away_from": [
            "`lev loop autodev` runtime continuity",
            "in-process sleep heartbeat ownership",
            "concurrent worker execution claims",
            "session/tick writer ownership",
        ],
    },
    "lev-plan": {
        "classification": "mine",
        "keep": [
            "entity lifecycle vocabulary for later bounded follow-ons",
            "ready / needs_validation / validated state language as background only",
        ],
        "adapt_away_from": [
            "`.lev/pm/plans/` lifecycle ownership",
            "plan mutation or transition authority",
        ],
    },
    "stack": {
        "classification": "background_only",
        "keep": [
            "prompt-stack staging as external background context only",
        ],
        "adapt_away_from": [
            "Leviathan prompt-stack runtime ownership",
            "session init / next / record / validate control",
        ],
    },
}

RUNTIME_COUPLING_SUMMARY = {
    "cron_scheduler": {
        "source": "autodev-loop skill",
        "state": "forbid",
        "why": "first Ratchet slice must not create or own recurring cron ticks",
    },
    "heartbeat_process": {
        "source": "autodev-lev skill and core-sdlc autodev command",
        "state": "forbid",
        "why": "in-process continuity, sleep pacing, and loop ownership exceed the current bounded audit scope",
    },
    "plan_surface_ownership": {
        "source": "lev-plan skill and discoverPlans wiring",
        "state": "forbid",
        "why": "Ratchet should not import `.lev/pm/plans/` lifecycle ownership as part of the first slice",
    },
    "prompt_stack_runtime": {
        "source": "stack skill and autodev stackId wiring",
        "state": "background_only",
        "why": "prompt-stack references are execution background, not a Ratchet-owned runtime seam here",
    },
    "git_sync": {
        "source": "autodev.ts --push",
        "state": "forbid",
        "why": "git pull/push after successful ticks is explicitly outside the bounded audit",
    },
    "launchd_service": {
        "source": "support README",
        "state": "forbid",
        "why": "background service installation is not admissible in the first imported autodev slice",
    },
}

LOOP_AXES = {
    "execution_validation_split": {
        "treatment": "keep",
        "why": "the separation between work execution and later validation is the strongest reusable shape in the source family",
    },
    "priority_tick_waterfall": {
        "treatment": "adapt",
        "why": "the sweep / validate / execute ordering is valuable, but hygiene generation must stay bounded and non-owning",
    },
    "exit_and_circuit_breakers": {
        "treatment": "adapt",
        "why": "explicit bounded exit conditions are reusable without importing heartbeat runtime continuity",
    },
    "heartbeat_runtime_continuity": {
        "treatment": "mine",
        "why": "useful as a later pattern source, but too runtime-coupled for this first slice",
    },
    "cron_or_service_scheduling": {
        "treatment": "skip",
        "why": "cron and launchd behavior are not admissible in the first Ratchet-native audit",
    },
    "git_close_loop": {
        "treatment": "skip",
        "why": "git pull/push control is not part of this operator",
    },
}

DEFAULT_NON_GOALS = [
    "No cron scheduling or recurring tick creation.",
    "No heartbeat process or `lev loop autodev` runtime ownership.",
    "No `.lev/pm/plans/`, `.lev/pm/handoffs/`, or validation-gates substrate ownership.",
    "No prompt-stack session control or external plugin runtime import.",
    "No git pull/push, launchd service setup, or background runner claim.",
    "No claim that Ratchet now has a live autodev loop.",
]

BLOCKING_PHRASES = (
    "lev loop autodev",
    "start the heartbeat",
    "start cron",
    "create cron",
    "launchd",
    "background service",
    "git push",
    "git pull",
    ".lev/pm/plans",
    "own the plan lifecycle",
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


def _background_ref_records(root: Path, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    refs = [str(item) for item in candidate.get("background_refs", []) if str(item).strip()]
    return _source_ref_records(root, refs)


def _analysis(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_question": (
            "What is the smallest honest Ratchet-native slice we can keep from the lev autodev family "
            "without importing recurring execution ownership?"
        ),
        "smallest_honest_slice": (
            "one bounded repo-held audit over loop shape, execution/validation separation, "
            "exit-condition discipline, and explicit forbid lines"
        ),
        "core_source_priority": ["autodev-loop", "autodev-lev"],
        "background_only_sources": ["lev-plan", "stack"],
        "recommended_follow_on_shape": (
            "only a later bounded validation-boundary or loop-state probe if this audit remains clean"
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
            "evidence": "candidate request does not widen into runtime ownership or background-service control",
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
        issues.append("neither the promotion packet nor the imported cluster map currently points at this autodev-loop audit slice")

    if refresh_report.get("status") != "ok":
        gate["refresh_alignment"]["status"] = "warn"
        issues.append("A2 brain refresher is not currently ok")

    if not source_ref_records or any(not item["exists"] for item in source_ref_records):
        gate["source_refs_available"]["status"] = "block"
        issues.append("one or more lev autodev source refs are missing")

    if stage_request != "autodev_loop_audit":
        gate["scope_bounded"]["status"] = "block"
        issues.append("candidate stage_request is not autodev_loop_audit")

    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate["non_goal_hygiene"]["status"] = "block"
        issues.append("candidate request widens into runtime loop, service, or substrate ownership")

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
    return "ready_for_bounded_autodev_loop_audit", issues, gate


def _render_markdown(report: dict[str, Any]) -> str:
    disposition_lines = [
        f"- `{name}`: {info['classification']} -> {', '.join(info['keep'])}"
        for name, info in report.get("imported_member_disposition", {}).items()
    ]
    coupling_lines = [
        f"- `{name}`: {info['state']} -> {info['why']}"
        for name, info in report.get("runtime_coupling_summary", {}).items()
    ]
    gate_lines = [
        f"- `{label}`: {result['status']} -> {result['evidence']}"
        for label, result in report.get("gate", {}).get("gate_results", {}).items()
    ]
    action_lines = [f"- {item}" for item in report.get("recommended_actions", [])]
    non_goal_lines = [f"- {item}" for item in report.get("non_goals", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# A2 lev Autodev Loop Audit Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- cluster_id: `{report.get('cluster_id', '')}`",
            f"- first_slice: `{report.get('first_slice', '')}`",
            f"- gate_status: `{report.get('gate_status', '')}`",
            f"- recommended_source_skill_id: `{report.get('recommended_source_skill_id', '')}`",
            f"- recommended_next_step: `{report.get('gate', {}).get('recommended_next_step', '')}`",
            "",
            "## Imported Member Disposition",
            *disposition_lines,
            "",
            "## Runtime Coupling Summary",
            *coupling_lines,
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


def build_a2_lev_autodev_loop_audit_report(
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
    background_ref_records = _background_ref_records(root, candidate)
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

    allow_bounded_autodev_loop_audit = gate_status.startswith("ready")
    recommended_actions = [
        "Keep this slice audit-only, repo-held, and nonoperative.",
        "Use the report to scope a later validation-boundary or exit-condition follow-on only if the gate stays clean.",
        "Do not widen this slice into cron, heartbeat runtime, prompt-stack control, `.lev` ownership, git sync, or service installation.",
    ]
    if not allow_bounded_autodev_loop_audit:
        recommended_actions.insert(
            0,
            "Repair the blocking gate inputs before treating lev-autodev as the next bounded imported execution-loop lane.",
        )

    report = {
        "schema": "A2_LEV_AUTODEV_LOOP_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if allow_bounded_autodev_loop_audit else "attention_required",
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
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITIONS,
        "runtime_coupling_summary": RUNTIME_COUPLING_SUMMARY,
        "loop_axes": LOOP_AXES,
        "analysis": _analysis(candidate),
        "evidence_inputs": evidence_inputs,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": allow_bounded_autodev_loop_audit,
            "allow_bounded_autodev_loop_audit": allow_bounded_autodev_loop_audit,
            "allow_runtime_loop_claims": False,
            "allow_cron_claims": False,
            "allow_heartbeat_process_claims": False,
            "allow_git_sync_claims": False,
            "allow_prompt_stack_runtime_claims": False,
            "allow_plan_surface_ownership": False,
            "reason": (
                "current promotion truth, source refs, and non-goal fences support one bounded loop-shape audit only"
                if allow_bounded_autodev_loop_audit
                else "one or more required inputs or gate checks still need attention"
            ),
            "gate_results": gate,
            "recommended_next_step": (
                "candidate_autodev_validation_boundary_probe"
                if allow_bounded_autodev_loop_audit
                else "needs_gate_repair"
            ),
            "blocking_issues": issues,
        },
        "recommended_next_action": recommended_actions[0],
        "recommended_actions": recommended_actions,
        "non_goals": list(DEFAULT_NON_GOALS),
        "staged_output_targets": {
            "json_report": REPORT_JSON,
            "md_report": REPORT_MD,
            "packet_json": PACKET_JSON,
        },
        "issues": issues,
    }

    packet = {
        "schema": "A2_LEV_AUTODEV_LOOP_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "first_slice": EXPECTED_FIRST_SLICE,
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "gate_status": report["gate"]["gate_status"],
        "safe_to_continue": report["gate"]["safe_to_continue"],
        "allow_bounded_autodev_loop_audit": report["gate"]["allow_bounded_autodev_loop_audit"],
        "allow_runtime_loop_claims": False,
        "allow_cron_claims": False,
        "allow_heartbeat_process_claims": False,
        "allow_git_sync_claims": False,
        "allow_prompt_stack_runtime_claims": False,
        "allow_plan_surface_ownership": False,
        "recommended_next_step": report["gate"]["recommended_next_step"],
        "blocking_issues": report["gate"]["blocking_issues"],
        "recommended_actions": report["recommended_actions"],
    }
    return report, packet


def run_a2_lev_autodev_loop_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root", REPO_ROOT)
    root = Path(repo_root).resolve()
    report, packet = build_a2_lev_autodev_loop_audit_report(root, ctx)

    report_json_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    report_md_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_json_path, report)
    _write_text(report_md_path, _render_markdown(report))
    _write_json(packet_path, packet)

    report["report_json_path"] = str(report_json_path)
    report["report_md_path"] = str(report_md_path)
    report["packet_path"] = str(packet_path)
    return report


if __name__ == "__main__":
    report, packet = build_a2_lev_autodev_loop_audit_report(REPO_ROOT)
    assert report["cluster_id"] == EXPECTED_CLUSTER_ID
    assert report["first_slice"] == EXPECTED_FIRST_SLICE
    assert packet["allow_runtime_loop_claims"] is False
    print("PASS: a2_lev_autodev_loop_audit_operator self-test")
