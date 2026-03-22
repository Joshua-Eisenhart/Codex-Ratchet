"""
a2_workshop_analysis_gate_operator.py

Bounded imported-cluster gate that analyzes one workshop candidate and emits a
repo-held report without claiming POC, integration, or full lev workshop import.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
A2_WORKSHOP_ANALYSIS_GATE_JSON = (
    "system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.json"
)
A2_WORKSHOP_ANALYSIS_GATE_MD = (
    "system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.md"
)
A2_WORKSHOP_ANALYSIS_GATE_PACKET = (
    "system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_PACKET__CURRENT__v1.json"
)

DEFAULT_CANDIDATE = {
    "id": "workshop-analysis-default",
    "title": "bounded lev-os workshop analysis gate slice",
    "type": "pattern",
    "source": "lev-os/agents workshop-analysis cluster",
    "raw_input": (
        "Analyze one imported workshop candidate and emit a gate report that "
        "decides whether a later bounded POC slice should even be considered."
    ),
    "stage_request": "analysis_gate",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-workshop/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/lev-align/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
    ],
}

IMPORTED_MEMBER_DISPOSITION = {
    "lev-workshop": {
        "classification": "adapt",
        "keep": "intake-to-analysis phase separation and explicit success-criteria framing",
        "adapt_away_from": [
            ".lev/workshop",
            "poc staging trees",
            "poly integration routing",
            "bd tracking",
            "claude-agent-sdk dependencies",
        ],
    },
    "lev-align": {
        "classification": "adapt",
        "keep": "pass/warn/block gate discipline with evidence-backed verdicts",
        "adapt_away_from": [
            ".lev/validation-gates.yaml",
            "module-tier auto classification",
            "external gate command execution",
        ],
    },
    "work": {
        "classification": "mine",
        "keep": "bounded scope, prior-art awareness, and explicit next-action/non-goal discipline",
        "adapt_away_from": [
            ".lev/pm handoff ownership",
            "prompt-stack scaffolding",
            "git close loop requirements",
        ],
    },
}

CURRENT_EVIDENCE_SPECS = {
    "skill_source_intake": {
        "path": "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json",
        "required": True,
    },
    "tracked_work_state": {
        "path": "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json",
        "required": True,
    },
    "research_deliberation": {
        "path": "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json",
        "required": True,
    },
    "brain_surface_refresh": {
        "path": "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json",
        "required": True,
    },
    "evermem_witness_sync": {
        "path": "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json",
        "required": False,
    },
}

DEFAULT_NON_GOALS = [
    "No POC build or prototype output.",
    "No poly integration or production promotion.",
    "No .lev/workshop, .lev/pm, or validation-gates substrate import.",
    "No claim that the full lev workshop, lev-align, or work systems are ported.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = _load_json(path)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _load_candidate(root: Path, ctx: dict[str, Any]) -> dict[str, Any]:
    raw_candidate = ctx.get("candidate")
    if isinstance(raw_candidate, dict):
        candidate = dict(DEFAULT_CANDIDATE)
        candidate.update(raw_candidate)
        return candidate

    raw_candidate_path = str(ctx.get("candidate_path", "")).strip()
    if raw_candidate_path:
        candidate_path = _resolve_output_path(root, raw_candidate_path, raw_candidate_path)
        payload = _safe_load_json(candidate_path)
        candidate = dict(DEFAULT_CANDIDATE)
        candidate.update(payload)
        candidate["candidate_path"] = str(candidate_path)
        return candidate

    return dict(DEFAULT_CANDIDATE)


def _candidate_source_refs(candidate: dict[str, Any], ctx: dict[str, Any]) -> list[str]:
    refs = []
    raw_refs = candidate.get("source_refs", [])
    if isinstance(raw_refs, list):
        refs.extend(str(item) for item in raw_refs if str(item).strip())
    extra_refs = ctx.get("source_refs", [])
    if isinstance(extra_refs, list):
        refs.extend(str(item) for item in extra_refs if str(item).strip())
    deduped: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        deduped.append(ref)
    return deduped


def _evidence_inputs(root: Path) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for label, spec in CURRENT_EVIDENCE_SPECS.items():
        path = root / spec["path"]
        payload = _safe_load_json(path)
        evidence[label] = {
            "path": spec["path"],
            "required": bool(spec["required"]),
            "exists": path.exists(),
            "schema": payload.get("schema", "") if payload else "",
            "status": payload.get("status", "") if payload else "",
            "generated_utc": payload.get("generated_utc", "") if payload else "",
            "audit_only": bool(payload.get("audit_only", False)) if payload else False,
            "nonoperative": bool(payload.get("nonoperative", False)) if payload else False,
            "issues_count": len(payload.get("issues", [])) if isinstance(payload.get("issues"), list) else 0,
        }
    return evidence


def _status_rank(status: str) -> int:
    normalized = status.strip().lower()
    if normalized == "action_required":
        return 3
    if normalized == "attention_required":
        return 2
    if normalized == "ok":
        return 1
    return 0


def _gate_status_from_evidence(evidence_inputs: dict[str, dict[str, Any]]) -> tuple[str, list[str]]:
    blocking: list[str] = []
    max_rank = 0
    for label, evidence in evidence_inputs.items():
        if evidence["required"] and not evidence["exists"]:
            blocking.append(f"missing required evidence report: {label}")
            max_rank = max(max_rank, 2)
            continue
        max_rank = max(max_rank, _status_rank(str(evidence.get("status", ""))))
        if evidence["required"] and str(evidence.get("status", "")) == "attention_required":
            blocking.append(f"required evidence needs attention: {label}")
        if evidence["required"] and str(evidence.get("status", "")) == "action_required":
            blocking.append(f"required evidence blocks progress: {label}")

    if any(item.startswith("missing required evidence report:") for item in blocking):
        return "hold_missing_inputs", blocking
    if max_rank >= 3:
        return "hold_action_required_inputs", blocking
    if max_rank >= 2:
        return "hold_attention_required_inputs", blocking
    return "ready_for_bounded_analysis", blocking


def _gate_results(candidate: dict[str, Any], source_refs: list[str], gate_status: str) -> dict[str, dict[str, Any]]:
    raw_input = str(candidate.get("raw_input", "")).strip()
    stage_request = str(candidate.get("stage_request", "analysis_gate")).strip().lower()
    type_value = str(candidate.get("type", "")).strip()
    base_results = {
        "input_sufficiency": {
            "status": "pass" if all([
                str(candidate.get("title", "")).strip(),
                type_value,
                str(candidate.get("source", "")).strip(),
                raw_input,
            ]) else "block",
            "evidence": "candidate has title/type/source/raw_input"
            if all([
                str(candidate.get("title", "")).strip(),
                type_value,
                str(candidate.get("source", "")).strip(),
                raw_input,
            ]) else "candidate is missing one or more core fields",
        },
        "scope_bounded": {
            "status": "pass" if stage_request in {"analysis", "analysis_gate", "gate"} else "block",
            "evidence": f"stage_request={stage_request or 'unset'}",
        },
        "dependency_visibility": {
            "status": "pass" if source_refs else "warn",
            "evidence": f"{len(source_refs)} source refs",
        },
        "approach_defined": {
            "status": "pass",
            "evidence": "minimal approach is fixed by the bounded workshop-analysis gate contract",
        },
        "validation_defined": {
            "status": "pass",
            "evidence": "validation plan is repo-held smoke + gate report review",
        },
        "claim_boundary_safe": {
            "status": "pass" if "integrat" not in raw_input.lower() and "production" not in raw_input.lower() else "warn",
            "evidence": "candidate request stays inside analysis/gate language"
            if "integrat" not in raw_input.lower() and "production" not in raw_input.lower()
            else "candidate raw input hints at wider promotion claims",
        },
    }
    if gate_status != "ready_for_bounded_analysis":
        base_results["validation_defined"]["status"] = "warn"
        base_results["validation_defined"]["evidence"] = "upstream evidence reports need attention before workshop analysis can proceed"
    return base_results


def _analysis(candidate: dict[str, Any], source_refs: list[str]) -> dict[str, Any]:
    return {
        "dependencies": [
            "A2 skill source intake report",
            "tracked work state",
            "research deliberation report",
            "brain surface refresh report",
        ],
        "interacts_with": [
            "SKILL_CLUSTER::skill-source-intake",
            "SKILL_CLUSTER::tracked-work-planning",
            "SKILL_CLUSTER::research-deliberation",
        ],
        "minimal_approach": [
            "Take one candidate only.",
            "Check bounded source refs and current repo-held evidence.",
            "Score fixed pass/warn/block gates.",
            "Emit report + packet only, with no POC or integration claim.",
        ],
        "success_criteria": [
            "One bounded candidate is analyzed with explicit gate results.",
            "The verdict says whether a later bounded POC slice is even admissible.",
            "Non-goals remain explicit and no wider workshop import is implied.",
        ],
        "edge_cases": [
            "candidate missing core fields",
            "required upstream reports missing",
            "candidate scope widens into POC or integration",
            "source refs absent or contradictory",
        ],
        "validation_plan": [
            "Run the dedicated workshop-analysis smoke test.",
            "Verify registry discovery and dispatch binding.",
            "Review the repo-held packet before promoting any later slice.",
        ],
        "estimated_complexity": "small",
        "prior_art": source_refs,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    gate = report.get("gate", {})
    gate_lines = []
    for label, info in gate.get("gate_results", {}).items():
        gate_lines.append(f"- `{label}`: {info.get('status')} -> {info.get('evidence')}")
    evidence_lines = []
    for label, info in report.get("evidence_inputs", {}).items():
        evidence_lines.append(
            f"- `{label}`: exists={info.get('exists')} status={info.get('status') or 'missing'} required={info.get('required')}"
        )
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    next_action_lines = [f"- {item}" for item in report.get("recommended_actions", [])]
    non_goal_lines = [f"- {item}" for item in report.get("non_goals", [])]
    return "\n".join(
        [
            "# A2 Workshop Analysis Gate Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- candidate: `{report.get('candidate', {}).get('title', '')}`",
            f"- gate_status: `{gate.get('gate_status', '')}`",
            f"- allow_bounded_workshop_analysis: `{gate.get('allow_bounded_workshop_analysis', False)}`",
            "",
            "## Evidence Inputs",
            *evidence_lines,
            "",
            "## Gate Results",
            *gate_lines,
            "",
            "## Recommended Actions",
            *next_action_lines,
            "",
            "## Non-Goals",
            *non_goal_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_a2_workshop_analysis_gate_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root).resolve()
    ctx = ctx or {}

    candidate = _load_candidate(root, ctx)
    source_refs = _candidate_source_refs(candidate, ctx)
    source_ref_status = [
        {
            "path": ref,
            "exists": (root / ref).exists() if not Path(ref).is_absolute() else Path(ref).exists(),
        }
        for ref in source_refs
    ]
    evidence_inputs = _evidence_inputs(root)
    gate_status, blocking_issues = _gate_status_from_evidence(evidence_inputs)
    gate_results = _gate_results(candidate, source_refs, gate_status)

    issues = list(blocking_issues)
    for label, result in gate_results.items():
        if result["status"] == "block":
            issues.append(f"gate blocked: {label}")

    overall_status = "ok" if not issues else "attention_required"
    allow_bounded_workshop_analysis = gate_status == "ready_for_bounded_analysis" and not any(
        result["status"] == "block" for result in gate_results.values()
    )
    recommended_actions = [
        "Keep this slice analysis-only and repo-held.",
        "Use the verdict to decide whether a later bounded POC slice should even be proposed.",
        "Do not import workshop storage, validation-gate files, or production routing yet.",
    ]
    if not allow_bounded_workshop_analysis:
        recommended_actions.insert(
            0,
            "Repair the blocking inputs or gate failures before proposing any workshop-derived implementation slice.",
        )

    report = {
        "schema": "A2_WORKSHOP_ANALYSIS_GATE_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": overall_status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": "SKILL_CLUSTER::workshop-analysis-gating",
        "first_slice": "a2-workshop-analysis-gate-operator",
        "candidate": candidate,
        "source_ref_status": source_ref_status,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITION,
        "analysis": _analysis(candidate, source_refs),
        "evidence_inputs": evidence_inputs,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": allow_bounded_workshop_analysis,
            "allow_bounded_workshop_analysis": allow_bounded_workshop_analysis,
            "block_new_runtime_claims": True,
            "blocking_issues": blocking_issues,
            "priority_findings": [
                label for label, result in gate_results.items() if result["status"] in {"warn", "block"}
            ],
            "reason": (
                "required upstream reports are healthy and the candidate stays inside an analysis/gate slice"
                if allow_bounded_workshop_analysis
                else "one or more required inputs or gate checks still need attention"
            ),
            "gate_results": gate_results,
            "recommended_next_step": (
                "ready_for_poc_slice" if allow_bounded_workshop_analysis else "needs_intake_clarification"
            ),
        },
        "recommended_actions": recommended_actions,
        "non_goals": DEFAULT_NON_GOALS,
        "staged_output_targets": {
            "json_report": A2_WORKSHOP_ANALYSIS_GATE_JSON,
            "md_report": A2_WORKSHOP_ANALYSIS_GATE_MD,
            "packet_json": A2_WORKSHOP_ANALYSIS_GATE_PACKET,
        },
        "issues": issues,
    }

    packet = {
        "schema": "A2_WORKSHOP_ANALYSIS_GATE_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": report["cluster_id"],
        "first_slice": report["first_slice"],
        "gate_status": report["gate"]["gate_status"],
        "safe_to_continue": report["gate"]["safe_to_continue"],
        "allow_bounded_workshop_analysis": report["gate"]["allow_bounded_workshop_analysis"],
        "blocking_issues": report["gate"]["blocking_issues"],
        "recommended_actions": report["recommended_actions"],
    }
    return report, packet


def run_a2_workshop_analysis_gate(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo", REPO_ROOT)
    root = Path(repo_root).resolve()
    report, packet = build_a2_workshop_analysis_gate_report(root, ctx)

    report_path = _resolve_output_path(root, ctx.get("report_path"), A2_WORKSHOP_ANALYSIS_GATE_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("markdown_path"), A2_WORKSHOP_ANALYSIS_GATE_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), A2_WORKSHOP_ANALYSIS_GATE_PACKET)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report["report_path"] = str(report_path)
    report["markdown_path"] = str(markdown_path)
    report["packet_path"] = str(packet_path)
    return report


if __name__ == "__main__":
    report, packet = build_a2_workshop_analysis_gate_report(REPO_ROOT)
    assert report["cluster_id"] == "SKILL_CLUSTER::workshop-analysis-gating"
    assert report["first_slice"] == "a2-workshop-analysis-gate-operator"
    assert packet["allow_bounded_workshop_analysis"] is True
    print("PASS: a2_workshop_analysis_gate_operator self-test")
