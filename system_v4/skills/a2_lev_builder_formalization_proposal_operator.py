"""
a2_lev_builder_formalization_proposal_operator.py

Proposal-only follow-on slice for the lev-builder formalization/placement lane.

This operator consumes the landed lev-builder placement audit and emits one
bounded Ratchet-native formalization proposal packet. It does not generate
patches, migrate files, run tests, or claim imported runtime ownership.
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
REFRESH_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
)
GRAPH_AUDIT_PATH = (
    "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json"
)

FORMALIZATION_PROPOSAL_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json"
)
FORMALIZATION_PROPOSAL_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.md"
)
FORMALIZATION_PROPOSAL_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_SLICE_ID = "a2-lev-builder-formalization-proposal-operator"
EXPECTED_SOURCE_SKILL_ID = "lev-builder"
EXPECTED_UPSTREAM_SLICE = "a2-lev-builder-placement-audit-operator"
PROPOSED_NEXT_BUILD_SKILL_ID = "a2-lev-builder-formalization-skeleton-operator"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-formalization-proposal-default",
    "title": "bounded lev-builder formalization proposal packet",
    "type": "formalization_proposal",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Emit one bounded Ratchet-native formalization proposal that follows the landed lev-builder "
        "placement audit without generating files, patches, migration steps, or runtime claims."
    ),
    "stage_request": "formalization_proposal",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
    ],
    "reference_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-builder/references/dsl-spec.md",
    ],
}

DEFAULT_NON_GOALS = [
    "No path mutation or graph-plan generation.",
    "No patch generation or application.",
    "No test execution.",
    "No migration or production-path writes.",
    "No registry updates, commits, or pushes.",
    "No live runtime claims or imported runtime ownership claims.",
    "No prompt-stack or .lev substrate import.",
    "No multi-candidate ranking or broad cluster planning.",
]

BLOCKING_PHRASES = (
    "apply patch",
    "generate patch",
    "migrate to production",
    "write files into production",
    "run the tests",
    "commit the change",
    "push the change",
    "import the runtime",
    "claim integration",
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


def _resolve_input_path(root: Path, raw: Any, default_rel: str) -> Path:
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


def _proposal_target(candidate: dict[str, Any]) -> dict[str, Any]:
    proposed_skill_id = str(candidate.get("proposed_skill_id", PROPOSED_NEXT_BUILD_SKILL_ID)).strip()
    return {
        "proposed_skill_id": proposed_skill_id,
        "proposed_skill_type": "maintenance",
        "target_family": "Ratchet-native lev formalization placement",
        "trust_zone": "A2_MID_REFINEMENT",
        "graph_family": "runtime",
        "target_paths": {
            "skill_spec": f"system_v4/skill_specs/{proposed_skill_id}/SKILL.md",
            "operator_source": f"system_v4/skills/{proposed_skill_id.replace('-', '_')}.py",
            "smoke_test": f"system_v4/skills/test_{proposed_skill_id.replace('-', '_')}_smoke.py",
            "report_json": (
                "system_v4/a2_state/audit_logs/"
                "A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json"
            ),
        },
        "source_skill_carryforward": EXPECTED_SOURCE_SKILL_ID,
    }


def _formalization_plan(proposal_target: dict[str, Any]) -> dict[str, Any]:
    target_paths = proposal_target["target_paths"]
    return {
        "required_files": [
            target_paths["skill_spec"],
            target_paths["operator_source"],
            target_paths["smoke_test"],
        ],
        "required_reports": [
            PLACEMENT_REPORT_PATH,
            PLACEMENT_PACKET_PATH,
            GRAPH_AUDIT_PATH,
            REFRESH_REPORT_PATH,
        ],
        "required_smokes": [
            target_paths["smoke_test"],
        ],
        "deferred_items": [
            "any filesystem patch generation",
            "any migration or production-path write",
            "any runtime-import claim",
            "any registry mutation beyond the future bounded build slice",
        ],
        "future_skill_shape_notes": [
            "Keep the future SKILL.md lean and progressive-disclosure oriented.",
            "Separate future references from core workflow instead of porting lev-builder wholesale.",
            "Carry forward placement and prior-art discipline without importing mutation machinery.",
        ],
    }


def _acceptance_gates() -> dict[str, Any]:
    return {
        "must_exist_before_build": [
            PLACEMENT_REPORT_PATH,
            PLACEMENT_PACKET_PATH,
            REFRESH_REPORT_PATH,
            GRAPH_AUDIT_PATH,
        ],
        "must_stay_false": [
            "allow_migration",
            "allow_patch_application",
            "allow_runtime_claims",
        ],
        "proof_requirements": [
            "future bounded build slice must have a dedicated smoke",
            "graph coverage must remain converged after any later bounded build",
            "A2 refresher must return ok after any later bounded build",
        ],
    }


def _evidence_inputs(
    placement_report: dict[str, Any],
    placement_packet: dict[str, Any],
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
) -> dict[str, Any]:
    graph_skill_coverage = graph_audit.get("skill_graph_coverage", {}) if isinstance(graph_audit, dict) else {}
    return {
        "placement_report_status": placement_report.get("status"),
        "placement_gate_status": placement_report.get("gate_status"),
        "placement_upstream_slice": placement_report.get("first_slice"),
        "placement_follow_on_slice": placement_report.get("recommended_follow_on_slice_id"),
        "placement_packet_ready": placement_packet.get("allow_bounded_placement_audit"),
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
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
    source_ref_status: list[dict[str, Any]],
    reference_ref_status: list[dict[str, Any]],
) -> tuple[str, list[str], dict[str, dict[str, Any]]]:
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
                f"gate_status={placement_report.get('gate_status', '')} "
                f"follow_on={placement_report.get('recommended_follow_on_slice_id', '')}"
            ),
        },
        "placement_packet_alignment": {
            "status": "pass",
            "evidence": (
                f"allow_bounded_placement_audit={placement_packet.get('allow_bounded_placement_audit')} "
                f"follow_on={placement_packet.get('recommended_follow_on_slice_id', '')}"
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
        "reference_refs_available": {
            "status": "pass",
            "evidence": (
                f"{sum(1 for item in reference_ref_status if item['exists'])}/{len(reference_ref_status)} refs present"
            ),
        },
        "proposal_scope": {
            "status": "pass",
            "evidence": f"stage_request={stage_request}",
        },
        "proposal_hygiene": {
            "status": "pass",
            "evidence": "candidate request does not include build/migration/runtime-claim language",
        },
    }

    if placement_report.get("status") != "ok" or placement_report.get("gate_status") != "ready_for_bounded_placement_audit":
        gate["placement_alignment"]["status"] = "block"
        issues.append("upstream lev-builder placement audit is not ready")
    if placement_report.get("first_slice") != EXPECTED_UPSTREAM_SLICE:
        gate["placement_alignment"]["status"] = "block"
        issues.append("upstream placement audit is not the expected slice")
    if placement_report.get("recommended_follow_on_slice_id") != EXPECTED_SLICE_ID:
        gate["placement_alignment"]["status"] = "block"
        issues.append("placement audit does not point at this proposal-only follow-on")

    if placement_packet.get("allow_bounded_placement_audit") is not True:
        gate["placement_packet_alignment"]["status"] = "block"
        issues.append("placement packet does not allow bounded carryforward")
    if placement_packet.get("recommended_follow_on_slice_id") != EXPECTED_SLICE_ID:
        gate["placement_packet_alignment"]["status"] = "block"
        issues.append("placement packet does not point at this proposal-only follow-on")

    if refresh_report.get("status") != "ok":
        gate["refresh_alignment"]["status"] = "block"
        issues.append("A2 brain refresher is not currently ok")

    if not fully_graphed or missing_skill_count or stale_skill_count:
        gate["graph_truth_alignment"]["status"] = "block"
        issues.append("graph skill truth is not fully converged")

    if not source_ref_status or any(not item["exists"] for item in source_ref_status):
        gate["source_refs_available"]["status"] = "block"
        issues.append("one or more core lev-builder proposal refs are missing")

    if not reference_ref_status or any(not item["exists"] for item in reference_ref_status):
        gate["reference_refs_available"]["status"] = "warn"
        issues.append("one or more mined spec-hygiene refs are missing")

    if stage_request != "formalization_proposal":
        gate["proposal_scope"]["status"] = "block"
        issues.append("candidate stage_request is not formalization_proposal")

    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate["proposal_hygiene"]["status"] = "block"
        issues.append("candidate request widens into build/migration/runtime-claim behavior")

    if any(value["status"] == "block" for value in gate.values()):
        return "hold_blocked", issues, gate
    if any(value["status"] == "warn" for value in gate.values()):
        return "ready_with_attention", issues, gate
    return "ready_for_formalization_proposal", issues, gate


def build_a2_lev_builder_formalization_proposal_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    placement_report_path = _resolve_input_path(root, ctx.get("placement_report_path"), PLACEMENT_REPORT_PATH)
    placement_packet_path = _resolve_input_path(root, ctx.get("placement_packet_path"), PLACEMENT_PACKET_PATH)
    refresh_report_path = _resolve_input_path(root, ctx.get("refresh_report_path"), REFRESH_REPORT_PATH)
    graph_audit_path = _resolve_input_path(root, ctx.get("graph_audit_path"), GRAPH_AUDIT_PATH)
    placement_report = _safe_load_json(placement_report_path)
    placement_packet = _safe_load_json(placement_packet_path)
    refresh_report = _safe_load_json(refresh_report_path)
    graph_audit = _safe_load_json(graph_audit_path)
    source_ref_status = _ref_records(root, [str(item) for item in candidate.get("source_refs", []) if str(item).strip()])
    reference_ref_status = _ref_records(root, [str(item) for item in candidate.get("reference_refs", []) if str(item).strip()])

    proposal_target = _proposal_target(candidate)
    formalization_plan = _formalization_plan(proposal_target)
    acceptance_gates = _acceptance_gates()
    evidence_inputs = _evidence_inputs(placement_report, placement_packet, refresh_report, graph_audit)

    gate_status, issues, gate_results = _gate_status(
        candidate,
        placement_report,
        placement_packet,
        refresh_report,
        graph_audit,
        source_ref_status,
        reference_ref_status,
    )

    allow_formalization_proposal = gate_status.startswith("ready")
    recommended_actions = [
        "Keep this slice proposal-only and repo-held.",
        "Use the emitted proposal packet to decide whether the future skeleton slice should be built at all.",
        "Keep migration, patching, and runtime-import claims explicitly false in the follow-on build lane.",
    ]
    if not allow_formalization_proposal:
        recommended_actions.insert(
            0,
            "Repair the upstream placement/A2/graph gate inputs before treating this proposal packet as usable.",
        )

    report = {
        "schema": "a2_lev_builder_formalization_proposal_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if gate_status == "ready_for_formalization_proposal" else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "proposal_only": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "slice_id": EXPECTED_SLICE_ID,
        "source_family": "lev_os_agents_curated",
        "upstream_placement_report_path": str(placement_report_path.relative_to(root)),
        "upstream_placement_packet_path": str(placement_packet_path.relative_to(root)),
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "candidate": candidate,
        "source_ref_status": source_ref_status,
        "reference_ref_status": reference_ref_status,
        "proposal_scope": {
            "bounded_question": (
                "What exact Ratchet-native operator/spec/test/report bundle should exist next "
                "if we formalize this seam without widening claims?"
            ),
            "single_candidate_only": True,
            "stage_request": candidate.get("stage_request"),
        },
        "formalization_proposal": {
            "proposal_target": proposal_target,
            "formalization_plan": formalization_plan,
            "acceptance_gates": acceptance_gates,
            "proposal_rationale": [
                "carry forward the placement verdict from the landed audit slice",
                "declare one future build target bundle without creating files for it here",
                "keep the next actual build lane behind explicit proof and migration gates",
            ],
        },
        "evidence_inputs": evidence_inputs,
        "gate_status": gate_status,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": allow_formalization_proposal,
            "allow_formalization_proposal": allow_formalization_proposal,
            "allow_build": False,
            "allow_migration": False,
            "allow_runtime_claims": False,
            "blocking_issues": issues,
            "priority_findings": [label for label, result in gate_results.items() if result["status"] in {"warn", "block"}],
            "reason": (
                "upstream placement truth, A2 freshness, and graph truth all support one bounded proposal packet"
                if allow_formalization_proposal
                else "one or more upstream gate checks still need attention"
            ),
            "gate_results": gate_results,
            "recommended_next_step": (
                PROPOSED_NEXT_BUILD_SKILL_ID if allow_formalization_proposal else "needs_gate_repair"
            ),
        },
        "recommended_actions": recommended_actions,
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_formalization_proposal_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "proposal_only": True,
        "recommended_source_skill_id": report["recommended_source_skill_id"],
        "proposal_target_id": proposal_target["proposed_skill_id"],
        "proposal_target_paths": proposal_target["target_paths"],
        "allow_proposal_emission": report["gate"]["allow_formalization_proposal"],
        "allow_build": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "allow_runtime_claims": False,
        "required_files": formalization_plan["required_files"],
        "required_smokes": formalization_plan["required_smokes"],
        "blocking_issues": report["gate"]["blocking_issues"],
        "recommended_actions": report["recommended_actions"],
        "next_step": report["gate"]["recommended_next_step"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Formalization Proposal Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- recommended_source_skill_id: `{report.get('recommended_source_skill_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- allow_formalization_proposal: `{report.get('gate', {}).get('allow_formalization_proposal')}`",
        "",
        "## Proposal Target",
        f"- proposed_skill_id: `{report.get('formalization_proposal', {}).get('proposal_target', {}).get('proposed_skill_id', '')}`",
    ]
    for label, rel_path in report.get("formalization_proposal", {}).get("proposal_target", {}).get("target_paths", {}).items():
        lines.append(f"- {label}: `{rel_path}`")
    lines.extend(["", "## Core Source Refs"])
    for item in report.get("source_ref_status", []):
        lines.append(f"- `{item.get('path', '')}` exists=`{item.get('exists', False)}`")
    lines.extend(["", "## Mined Reference Refs"])
    for item in report.get("reference_ref_status", []):
        lines.append(f"- `{item.get('path', '')}` exists=`{item.get('exists', False)}`")
    lines.extend(["", "## Gate Results"])
    for label, result in report.get("gate", {}).get("gate_results", {}).items():
        lines.append(f"- `{label}` status=`{result.get('status', '')}` evidence=`{result.get('evidence', '')}`")
    lines.extend(["", "## Recommended Actions"])
    for action in report.get("recommended_actions", []):
        lines.append(f"- {action}")
    lines.extend(["", "## Non-Goals"])
    for item in report.get("non_goals", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Packet",
            f"- allow_proposal_emission: `{packet.get('allow_proposal_emission', False)}`",
            f"- allow_build: `{packet.get('allow_build', False)}`",
            f"- allow_migration: `{packet.get('allow_migration', False)}`",
            f"- allow_runtime_claims: `{packet.get('allow_runtime_claims', False)}`",
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


def run_a2_lev_builder_formalization_proposal(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), FORMALIZATION_PROPOSAL_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), FORMALIZATION_PROPOSAL_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), FORMALIZATION_PROPOSAL_PACKET_JSON)

    report, packet = build_a2_lev_builder_formalization_proposal_report(root, ctx)
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
    report, packet = build_a2_lev_builder_formalization_proposal_report(REPO_ROOT)
    assert report["cluster_id"] == EXPECTED_CLUSTER_ID
    assert report["slice_id"] == EXPECTED_SLICE_ID
    assert packet["allow_build"] is False
    print("PASS: a2 lev-builder formalization proposal operator self-test")
