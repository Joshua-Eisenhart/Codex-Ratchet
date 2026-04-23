"""
a2_lev_builder_formalization_skeleton_operator.py

Bounded scaffold-proof slice for the lev-builder formalization lane.

This operator consumes the landed lev-builder formalization proposal packet,
verifies the expected scaffold bundle now exists on disk, and emits one
repo-held report plus one compact packet. It does not migrate files, mutate
existing code, claim runtime ownership, or widen into a production import lane.
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
REFRESH_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
)
GRAPH_AUDIT_PATH = (
    "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json"
)

SKELETON_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json"
)
SKELETON_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.md"
)
SKELETON_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json"
)

EXPECTED_CLUSTER_ID = "SKILL_CLUSTER::lev-formalization-placement"
EXPECTED_SLICE_ID = "a2-lev-builder-formalization-skeleton-operator"
EXPECTED_UPSTREAM_SLICE = "a2-lev-builder-formalization-proposal-operator"
EXPECTED_SOURCE_SKILL_ID = "lev-builder"

DEFAULT_CANDIDATE = {
    "id": "lev-builder-formalization-skeleton-default",
    "title": "bounded lev-builder scaffold proof",
    "type": "formalization_skeleton",
    "source": "lev-os/agents formalize / placement / migrate cluster",
    "raw_input": (
        "Verify the bounded Ratchet-native lev-builder formalization scaffold bundle is landed "
        "without migration, patching, registry mutation, or runtime claims."
    ),
    "stage_request": "formalization_skeleton",
    "source_refs": [
        "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
        "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
    ],
}

DEFAULT_NON_GOALS = [
    "No migration or production-path writes.",
    "No patch generation or application.",
    "No runtime integration claim.",
    "No imported runtime ownership claim.",
    "No graph-plan generation.",
    "No full lev-builder workflow port.",
    "No registry mutation or runner mutation from inside this operator.",
    "No broad cluster planning or multi-candidate ranking.",
]

DEFAULT_UNRESOLVED = [
    "Whether any post-skeleton migration slice should exist at all.",
    "Whether the scaffold bundle is only an artifact or later admissible runtime code.",
    "Whether lev-formalization is complete enough for execution, not just placement/proposal/scaffold.",
    "Whether any imported runtime ownership or flatten-import claim is justified.",
]

BLOCKING_PHRASES = (
    "apply patch",
    "generate patch",
    "migrate to production",
    "write files into production",
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


def _expected_target_paths() -> dict[str, str]:
    return {
        "skill_spec": "system_v4/skill_specs/a2-lev-builder-formalization-skeleton-operator/SKILL.md",
        "operator_source": "system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py",
        "smoke_test": "system_v4/skills/test_a2_lev_builder_formalization_skeleton_operator_smoke.py",
        "report_json": SKELETON_REPORT_JSON,
    }


def _target_paths_from_packet(proposal_packet: dict[str, Any]) -> dict[str, str]:
    raw_paths = proposal_packet.get("proposal_target_paths")
    if not isinstance(raw_paths, dict):
        return _expected_target_paths()
    expected = _expected_target_paths()
    return {
        "skill_spec": str(raw_paths.get("skill_spec") or expected["skill_spec"]),
        "operator_source": str(raw_paths.get("operator_source") or expected["operator_source"]),
        "smoke_test": str(raw_paths.get("smoke_test") or expected["smoke_test"]),
        "report_json": str(raw_paths.get("report_json") or expected["report_json"]),
    }


def _scaffold_records(root: Path, target_paths: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for label, rel_path in target_paths.items():
        if label == "report_json":
            continue
        path = root / rel_path
        records.append(
            {
                "label": label,
                "path": rel_path,
                "exists": path.exists(),
                "write_action": "existing_scaffold_bundle" if path.exists() else "missing",
            }
        )
    return records


def _scaffold_plan(target_paths: dict[str, str]) -> dict[str, Any]:
    return {
        "required_files": [
            target_paths["skill_spec"],
            target_paths["operator_source"],
            target_paths["smoke_test"],
        ],
        "report_surfaces": [
            SKELETON_REPORT_JSON,
            SKELETON_REPORT_MD,
            SKELETON_PACKET_JSON,
        ],
        "scaffold_mode": "repo_landed_bundle",
        "proof_shape": [
            "verify upstream proposal packet alignment",
            "verify scaffold bundle presence",
            "verify bounded non-goal language remains intact",
            "emit one report and one packet only",
        ],
    }


def _smoke_result(target_paths: dict[str, str], scaffold_records: list[dict[str, Any]]) -> dict[str, Any]:
    smoke_rel = target_paths["smoke_test"]
    smoke_exists = any(
        item["label"] == "smoke_test" and item["exists"] for item in scaffold_records
    )
    return {
        "smoke_path": smoke_rel,
        "smoke_file_present": smoke_exists,
        "smoke_execution_claimed": False,
        "reason": "This slice records scaffold readiness only; smoke execution is external proof.",
    }


def _evidence_inputs(
    placement_report: dict[str, Any],
    placement_packet: dict[str, Any],
    proposal_report: dict[str, Any],
    proposal_packet: dict[str, Any],
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
    refresh_report: dict[str, Any],
    graph_audit: dict[str, Any],
    source_ref_status: list[dict[str, Any]],
    scaffold_records: list[dict[str, Any]],
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
        "proposal_alignment": {
            "status": "pass",
            "evidence": (
                f"status={proposal_report.get('status', '')} "
                f"gate_status={proposal_report.get('gate_status', '')} "
                f"next_step={proposal_packet.get('next_step', '')}"
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
        "scaffold_bundle_present": {
            "status": "pass",
            "evidence": (
                f"{sum(1 for item in scaffold_records if item['exists'])}/{len(scaffold_records)} scaffold paths present"
            ),
        },
        "scope_hygiene": {
            "status": "pass",
            "evidence": f"stage_request={stage_request}",
        },
    }

    if placement_report.get("status") != "ok" or placement_report.get("recommended_follow_on_slice_id") != EXPECTED_UPSTREAM_SLICE:
        gate["placement_alignment"]["status"] = "block"
        issues.append("placement audit does not point cleanly at the landed proposal slice")

    if placement_packet.get("allow_bounded_placement_audit") is not True:
        gate["placement_packet_alignment"]["status"] = "block"
        issues.append("placement packet does not allow bounded carryforward")
    if placement_packet.get("recommended_follow_on_slice_id") != EXPECTED_UPSTREAM_SLICE:
        gate["placement_packet_alignment"]["status"] = "block"
        issues.append("placement packet does not point at the landed proposal slice")

    proposed_skill = (
        proposal_report.get("formalization_proposal", {})
        .get("proposal_target", {})
        .get("proposed_skill_id")
    )
    if proposal_report.get("status") != "ok" or proposal_report.get("gate_status") != "ready_for_formalization_proposal":
        gate["proposal_alignment"]["status"] = "block"
        issues.append("upstream formalization proposal is not ready")
    if proposal_packet.get("next_step") != EXPECTED_SLICE_ID or proposed_skill != EXPECTED_SLICE_ID:
        gate["proposal_alignment"]["status"] = "block"
        issues.append("proposal surfaces do not point at this skeleton slice")
    if proposal_packet.get("allow_build") is not False or proposal_packet.get("allow_migration") is not False:
        gate["proposal_alignment"]["status"] = "block"
        issues.append("proposal packet widened beyond the bounded non-migratory gate")
    if proposal_packet.get("allow_runtime_claims") is not False:
        gate["proposal_alignment"]["status"] = "block"
        issues.append("proposal packet allows runtime claims unexpectedly")

    if refresh_report.get("status") != "ok":
        gate["refresh_alignment"]["status"] = "block"
        issues.append("A2 brain refresher is not currently ok")

    if not fully_graphed or missing_skill_count or stale_skill_count:
        gate["graph_truth_alignment"]["status"] = "block"
        issues.append("graph skill truth is not fully converged")

    if not source_ref_status or any(not item["exists"] for item in source_ref_status):
        gate["source_refs_available"]["status"] = "block"
        issues.append("one or more core lev-builder scaffold refs are missing")

    if not scaffold_records or any(not item["exists"] for item in scaffold_records):
        gate["scaffold_bundle_present"]["status"] = "block"
        issues.append("one or more scaffold bundle files are missing")

    if stage_request != "formalization_skeleton":
        gate["scope_hygiene"]["status"] = "block"
        issues.append("candidate stage_request is not formalization_skeleton")
    if any(phrase in raw_input for phrase in BLOCKING_PHRASES):
        gate["scope_hygiene"]["status"] = "block"
        issues.append("candidate request widens into migration/runtime/runner behavior")

    if any(value["status"] == "block" for value in gate.values()):
        return "hold_blocked", issues, gate
    return "bounded_scaffold_completed", issues, gate


def build_a2_lev_builder_formalization_skeleton_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    candidate = _load_candidate(ctx)
    placement_report_path = _resolve_input_path(root, ctx.get("placement_report_path"), PLACEMENT_REPORT_PATH)
    placement_packet_path = _resolve_input_path(root, ctx.get("placement_packet_path"), PLACEMENT_PACKET_PATH)
    proposal_report_path = _resolve_input_path(root, ctx.get("proposal_report_path"), PROPOSAL_REPORT_PATH)
    proposal_packet_path = _resolve_input_path(root, ctx.get("proposal_packet_path"), PROPOSAL_PACKET_PATH)
    refresh_report_path = _resolve_input_path(root, ctx.get("refresh_report_path"), REFRESH_REPORT_PATH)
    graph_audit_path = _resolve_input_path(root, ctx.get("graph_audit_path"), GRAPH_AUDIT_PATH)

    placement_report = _safe_load_json(placement_report_path)
    placement_packet = _safe_load_json(placement_packet_path)
    proposal_report = _safe_load_json(proposal_report_path)
    proposal_packet = _safe_load_json(proposal_packet_path)
    refresh_report = _safe_load_json(refresh_report_path)
    graph_audit = _safe_load_json(graph_audit_path)

    target_paths = _target_paths_from_packet(proposal_packet)
    source_ref_status = _ref_records(root, [str(item) for item in candidate.get("source_refs", []) if str(item).strip()])
    scaffold_records = _scaffold_records(root, target_paths)
    scaffold_plan = _scaffold_plan(target_paths)
    smoke_result = _smoke_result(target_paths, scaffold_records)
    evidence_inputs = _evidence_inputs(
        placement_report,
        placement_packet,
        proposal_report,
        proposal_packet,
        refresh_report,
        graph_audit,
    )
    gate_status, issues, gate_results = _gate_status(
        candidate,
        placement_report,
        placement_packet,
        proposal_report,
        proposal_packet,
        refresh_report,
        graph_audit,
        source_ref_status,
        scaffold_records,
    )

    bounded_scaffold_completed = gate_status == "bounded_scaffold_completed"
    recommended_actions = [
        "Keep this slice scaffold-only, repo-held, and non-migratory.",
        "Treat any post-skeleton migration/runtime follow-on as separately gated.",
        "Do not widen this landed scaffold slice into imported runtime ownership claims.",
    ]
    if not bounded_scaffold_completed:
        recommended_actions.insert(
            0,
            "Repair the upstream proposal/A2/graph/scaffold inputs before treating the scaffold bundle as landed.",
        )

    report = {
        "schema": "a2_lev_builder_formalization_skeleton_report_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if bounded_scaffold_completed else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "scaffold_only": True,
        "non_migratory": True,
        "do_not_promote": True,
        "cluster_id": EXPECTED_CLUSTER_ID,
        "slice_id": EXPECTED_SLICE_ID,
        "source_family": "lev_os_agents_curated",
        "recommended_source_skill_id": EXPECTED_SOURCE_SKILL_ID,
        "upstream_placement_report_path": str(placement_report_path.relative_to(root)),
        "upstream_placement_packet_path": str(placement_packet_path.relative_to(root)),
        "upstream_proposal_report_path": str(proposal_report_path.relative_to(root)),
        "upstream_proposal_packet_path": str(proposal_packet_path.relative_to(root)),
        "candidate": candidate,
        "target_paths": target_paths,
        "source_ref_status": source_ref_status,
        "scaffold_plan": scaffold_plan,
        "scaffold_write_results": scaffold_records,
        "smoke_result": smoke_result,
        "evidence_inputs": evidence_inputs,
        "gate_status": gate_status,
        "gate": {
            "gate_status": gate_status,
            "safe_to_continue": bounded_scaffold_completed,
            "bounded_scaffold_completed": bounded_scaffold_completed,
            "allow_registry_mutation": False,
            "allow_runner_mutation": False,
            "allow_graph_claims": False,
            "allow_runtime_claims": False,
            "allow_migration": False,
            "allow_patch_application": False,
            "blocking_issues": issues,
            "priority_findings": [label for label, result in gate_results.items() if result["status"] == "block"],
            "reason": (
                "upstream proposal truth is clean and the bounded scaffold bundle is present"
                if bounded_scaffold_completed
                else "one or more upstream gate checks still need attention"
            ),
            "gate_results": gate_results,
            "recommended_next_step": (
                "post_skeleton_follow_on_unresolved" if bounded_scaffold_completed else "needs_gate_repair"
            ),
        },
        "recommended_actions": recommended_actions,
        "non_goals": list(DEFAULT_NON_GOALS),
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_builder_formalization_skeleton_packet_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "target_paths": target_paths,
        "bounded_scaffold_completed": bounded_scaffold_completed,
        "scaffold_write_mode": "repo_landed_bundle",
        "allow_registry_mutation": False,
        "allow_runner_mutation": False,
        "allow_graph_claims": False,
        "allow_runtime_claims": False,
        "allow_migration": False,
        "allow_patch_application": False,
        "required_files": scaffold_plan["required_files"],
        "required_smokes": [target_paths["smoke_test"]],
        "blocking_issues": report["gate"]["blocking_issues"],
        "next_step": report["gate"]["recommended_next_step"],
        "unresolved_questions": list(DEFAULT_UNRESOLVED),
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 lev-builder Formalization Skeleton Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- bounded_scaffold_completed: `{report.get('gate', {}).get('bounded_scaffold_completed')}`",
        "",
        "## Target Paths",
    ]
    for label, rel_path in report.get("target_paths", {}).items():
        lines.append(f"- {label}: `{rel_path}`")
    lines.extend(["", "## Scaffold Bundle"])
    for item in report.get("scaffold_write_results", []):
        lines.append(
            f"- `{item.get('label', '')}` path=`{item.get('path', '')}` "
            f"exists=`{item.get('exists', False)}` action=`{item.get('write_action', '')}`"
        )
    lines.extend(["", "## Gate Results"])
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
            f"- bounded_scaffold_completed: `{packet.get('bounded_scaffold_completed', False)}`",
            f"- allow_registry_mutation: `{packet.get('allow_registry_mutation', False)}`",
            f"- allow_runner_mutation: `{packet.get('allow_runner_mutation', False)}`",
            f"- allow_graph_claims: `{packet.get('allow_graph_claims', False)}`",
            f"- allow_runtime_claims: `{packet.get('allow_runtime_claims', False)}`",
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


def run_a2_lev_builder_formalization_skeleton(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), SKELETON_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), SKELETON_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), SKELETON_PACKET_JSON)

    report, packet = build_a2_lev_builder_formalization_skeleton_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted
