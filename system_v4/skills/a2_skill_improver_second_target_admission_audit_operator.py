"""
a2_skill_improver_second_target_admission_audit_operator.py

Audit-only follow-on that decides whether skill-improver-operator should hold
at one proven target or admit one second bounded native target class.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_SKILL_ID = "skill-improver-operator"
SLICE_ID = "a2-skill-improver-second-target-admission-audit-operator"
CLUSTER_ID = "SKILL_CLUSTER::a2-skill-truth-maintenance"

REGISTRY_PATH = "system_v4/a1_state/skill_registry_v1.json"
READINESS_REPORT_PATH = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json"
TARGET_SELECTION_REPORT_PATH = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json"
TARGET_SELECTION_PACKET_PATH = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json"
FIRST_TARGET_PROOF_REPORT_PATH = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json"

REPORT_JSON = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_REPORT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_REPORT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json"

CONTROLLER_CRITICAL_SKILLS = {
    "a2-brain-surface-refresher",
}
SIDE_PROJECT_OR_EXTERNAL_SKILLS = {
    "a2-evermem-backend-reachability-audit-operator",
}
SELF_REFERENTIAL_PREFIXES = (
    "a2-skill-improver-",
)
OWNER_LAW_OR_REFRESH_TAGS = {
    "owner-law",
    "surface-refresh",
}

SECOND_TARGET_CLASS = (
    "native maintenance Python skill with dedicated smoke/spec, propose-only behavior, "
    "not imported, not side-project, and not controller-critical"
)

DEFAULT_NON_GOALS = [
    "Do not mutate any target skill from this audit slice.",
    "Do not treat one proven first target as permission for general repo mutation.",
    "Do not admit imported-cluster, side-project, or controller-critical targets as the second target class.",
    "Do not widen beyond one additional bounded target class.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _derive_smoke_path(source_path: str) -> str:
    source = Path(source_path)
    return str(source.with_name(f"test_{source.stem}_smoke.py")).replace("\\", "/")


def _candidate_review(root: Path, skill_id: str, entry: dict[str, Any], first_target_skill_id: str) -> dict[str, Any] | None:
    source_path = str(entry.get("source_path", "")).strip()
    if not source_path.startswith("system_v4/skills/") or not source_path.endswith(".py"):
        return None

    capabilities = entry.get("capabilities", {}) or {}
    adapters = entry.get("adapters", {}) or {}
    tags = [str(tag) for tag in entry.get("tags", []) or []]
    related_skills = [str(item) for item in entry.get("related_skills", []) or []]
    skill_type = str(entry.get("skill_type", "")).strip()
    source_type = str(entry.get("source_type", "")).strip()
    status = str(entry.get("status", "active")).strip()
    spec_path = str(adapters.get("codex", "")).strip()
    smoke_path = _derive_smoke_path(source_path)
    imported_cluster = "imported-cluster" in tags
    is_phase_runner = bool(capabilities.get("is_phase_runner", False))
    direct_meta_relation = (
        TARGET_SKILL_ID in related_skills
        or "truth-maintenance" in tags
        or skill_id in {"a2-brain-surface-refresher"}
    )
    owner_law_or_refresh_class = any(tag in OWNER_LAW_OR_REFRESH_TAGS for tag in tags)

    reasons: list[str] = []
    exclusions: list[str] = []
    if status != "active":
        exclusions.append("inactive")
    if skill_type != "maintenance":
        exclusions.append("not_maintenance")
    else:
        reasons.append("maintenance skill")
    if source_type != "operator_module":
        exclusions.append("not_operator_module")
    else:
        reasons.append("operator module")
    if not spec_path or not (root / spec_path).exists():
        exclusions.append("missing_spec")
    else:
        reasons.append("dedicated spec present")
    if not (root / smoke_path).exists():
        exclusions.append("missing_smoke")
    else:
        reasons.append("dedicated smoke present")
    if not bool(capabilities.get("can_only_propose", False)):
        exclusions.append("not_propose_only")
    else:
        reasons.append("propose-only gate present")
    if not is_phase_runner:
        exclusions.append("not_phase_runner")
    else:
        reasons.append("phase-runner gate present")
    if "audit-mode" not in tags:
        exclusions.append("missing_audit_mode")
    else:
        reasons.append("audit-mode tag present")
    if not direct_meta_relation:
        exclusions.append("not_in_meta_maintenance_class")
    else:
        reasons.append("directly aligned with truth-maintenance lane")

    if skill_id == TARGET_SKILL_ID:
        exclusions.append("target_self")
    if skill_id == first_target_skill_id:
        exclusions.append("first_target_already_proven")
    if skill_id == SLICE_ID:
        exclusions.append("selector_self")
    if imported_cluster:
        exclusions.append("imported_cluster")
    if owner_law_or_refresh_class:
        exclusions.append("owner_law_or_surface_refresh_class")
    if skill_id in CONTROLLER_CRITICAL_SKILLS:
        exclusions.append("controller_critical")
    if skill_id in SIDE_PROJECT_OR_EXTERNAL_SKILLS:
        exclusions.append("side_project_or_external_dependency")
    if any(skill_id.startswith(prefix) for prefix in SELF_REFERENTIAL_PREFIXES):
        exclusions.append("meta_lane_self_reference")

    score = len(reasons)
    if not imported_cluster:
        score += 1
    if not exclusions:
        score += 6

    return {
        "skill_id": skill_id,
        "source_path": source_path,
        "source_type": source_type,
        "spec_path": spec_path,
        "smoke_path": smoke_path,
        "tags": tags,
        "related_skills": related_skills,
        "imported_cluster": imported_cluster,
        "direct_meta_relation": direct_meta_relation,
        "selection_reasons": reasons,
        "exclusion_reasons": exclusions,
        "eligible": not exclusions,
        "score": score,
        "recommended_allowed_targets": [source_path] if not exclusions else [],
        "recommended_test_command": ["python3", smoke_path] if not exclusions else [],
    }


def build_skill_improver_second_target_admission_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()

    readiness_report = _safe_load_json(root / READINESS_REPORT_PATH)
    target_selection_report = _safe_load_json(root / TARGET_SELECTION_REPORT_PATH)
    target_selection_packet = _safe_load_json(root / TARGET_SELECTION_PACKET_PATH)
    first_target_proof_report = _safe_load_json(root / FIRST_TARGET_PROOF_REPORT_PATH)
    registry_payload = _safe_load_json(root / REGISTRY_PATH)

    issues: list[str] = []
    if readiness_report.get("target_readiness") != "bounded_ready_for_first_target":
        issues.append("skill-improver readiness report is not at bounded_ready_for_first_target")
    if target_selection_report.get("status") != "ok":
        issues.append("target selection report is not ok")
    if not first_target_proof_report.get("proof_completed"):
        issues.append("first target proof is not completed")

    first_target_skill_id = str(
        first_target_proof_report.get("target_skill_id")
        or target_selection_packet.get("recommended_target_skill_id")
        or target_selection_report.get("recommended_target", {}).get("skill_id", "")
    ).strip()
    if not first_target_skill_id:
        issues.append("first proven target skill id is missing")

    reviews: list[dict[str, Any]] = []
    if isinstance(registry_payload, dict):
        for skill_id, entry in registry_payload.items():
            if isinstance(entry, dict):
                row = _candidate_review(root, str(skill_id), entry, first_target_skill_id)
                if row is not None:
                    reviews.append(row)

    reviews.sort(
        key=lambda item: (
            not bool(item["eligible"]),
            -int(item["score"]),
            item["skill_id"],
        )
    )
    eligible = [item for item in reviews if item["eligible"]]
    recommended_target = eligible[0] if eligible else {}

    if issues:
        gate_status = "block_second_target_admission"
        next_step = "repair_skill_improver_gate_inputs"
    elif not eligible:
        gate_status = "hold_one_proven_target_only"
        next_step = "hold_one_proven_target_only"
    else:
        gate_status = "candidate_second_target_admissible"
        next_step = "bounded_second_target_proof_gate"

    report = {
        "schema": "SKILL_IMPROVER_SECOND_TARGET_ADMISSION_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "action_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "target_skill_id": TARGET_SKILL_ID,
        "first_proven_target_skill_id": first_target_skill_id,
        "second_target_class": SECOND_TARGET_CLASS,
        "gate_status": gate_status,
        "recommended_next_step": next_step,
        "candidate_review_count": len(reviews),
        "candidate_review": reviews[:8],
        "eligible_second_target_count": len(eligible),
        "recommended_second_target": recommended_target,
        "recommended_actions": [
            "Keep this slice audit-only and fail closed if a second target has not clearly earned admission.",
            "Retain the general skill-improver gate even if a second target becomes admissible.",
            "Do not widen to imported-cluster, side-project, controller-critical, or self-referential targets from this slice.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }

    packet = {
        "schema": "SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "target_skill_id": TARGET_SKILL_ID,
        "first_proven_target_skill_id": first_target_skill_id,
        "allow_second_target_admission": bool(eligible) and not issues,
        "retain_general_gate": True,
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "gate_status": gate_status,
        "blocking_issues": issues,
        "recommended_next_step": next_step,
        "recommended_second_target_skill_id": recommended_target.get("skill_id", "") if recommended_target else "",
        "recommended_second_target_skill_path": recommended_target.get("source_path", "") if recommended_target else "",
        "recommended_second_target_smoke_path": recommended_target.get("smoke_path", "") if recommended_target else "",
        "recommended_allowed_targets": recommended_target.get("recommended_allowed_targets", []) if recommended_target else [],
        "recommended_test_command": recommended_target.get("recommended_test_command", []) if recommended_target else [],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# Skill Improver Second Target Admission Audit",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- first_proven_target_skill_id: `{report.get('first_proven_target_skill_id', '')}`",
        f"- gate_status: `{report.get('gate_status', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        f"- eligible_second_target_count: `{report.get('eligible_second_target_count', 0)}`",
        f"- do_not_promote: `{report.get('do_not_promote', False)}`",
        "",
        "## Recommended Second Target",
    ]
    recommended = report.get("recommended_second_target", {}) or {}
    if recommended:
        lines.extend(
            [
                f"- skill_id: `{recommended.get('skill_id', '')}`",
                f"- source_path: `{recommended.get('source_path', '')}`",
                f"- smoke_path: `{recommended.get('smoke_path', '')}`",
            ]
        )
    else:
        lines.append("- none")
    lines.extend(["", "## Candidate Review"])
    for item in report.get("candidate_review", []):
        status = "eligible" if item.get("eligible") else "excluded"
        lines.append(
            f"- `{item.get('skill_id', '')}`: {status}; exclusions={item.get('exclusion_reasons', []) or ['none']}"
        )
    if not report.get("candidate_review"):
        lines.append("- none")
    lines.extend(["", "## Packet"])
    lines.extend(
        [
            f"- allow_second_target_admission: `{packet.get('allow_second_target_admission', False)}`",
            f"- retain_general_gate: `{packet.get('retain_general_gate', False)}`",
            f"- do_not_promote: `{packet.get('do_not_promote', False)}`",
        ]
    )
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    lines.extend(["", "## Issues", *issue_lines, ""])
    return "\n".join(lines)


def run_a2_skill_improver_second_target_admission_audit(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_skill_improver_second_target_admission_report(root, ctx)

    report_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "gate_status": report["gate_status"],
        "recommended_next_step": report["recommended_next_step"],
        "report_json_path": str(report_path),
        "report_md_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    result = run_a2_skill_improver_second_target_admission_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
