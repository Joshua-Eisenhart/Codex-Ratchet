"""
a2_skill_improver_target_selector_operator.py

Audit-only target-selection slice for the live skill improver operator.

This operator does not mutate any target skill. It reads the current readiness
gate, inspects the live registry/spec/smoke surfaces, ranks eligible first
targets, and emits one bounded repo-held report plus one compact packet so the
first real skill-improver use can be explicit instead of ad hoc.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_SKILL_ID = "skill-improver-operator"
SELECTOR_SKILL_ID = "a2-skill-improver-target-selector-operator"
READINESS_SKILL_ID = "a2-skill-improver-readiness-operator"
REGISTRY_PATH = "system_v4/a1_state/skill_registry_v1.json"
READINESS_REPORT_PATH = "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json"

TARGET_SELECTOR_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json"
)
TARGET_SELECTOR_REPORT_MD = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.md"
)
TARGET_SELECTOR_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json"
)

RECOMMENDED_FIRST_TARGET_CLASS = (
    "native maintenance Python skill with dedicated smoke, codex spec, and audit-only/propose-only behavior"
)

DEFAULT_NON_GOALS = [
    "Do not mutate any target skill from this selector slice.",
    "Do not auto-promote the selected target into live repo mutation.",
    "Do not treat target ranking as proof that candidate mutation is safe.",
    "Do not widen selection beyond the bounded first-target class.",
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


def _candidate_record(root: Path, skill_id: str, entry: dict[str, Any]) -> dict[str, Any] | None:
    source_path = str(entry.get("source_path", "")).strip()
    if skill_id in {TARGET_SKILL_ID, SELECTOR_SKILL_ID} or not source_path.startswith("system_v4/skills/") or not source_path.endswith(".py"):
        return None
    if str(entry.get("status", "")).strip() != "active":
        return None

    capabilities = entry.get("capabilities", {})
    adapters = entry.get("adapters", {})
    tags = [str(tag) for tag in entry.get("tags", [])]
    related_skills = [str(item) for item in entry.get("related_skills", [])]
    skill_type = str(entry.get("skill_type", "")).strip()

    spec_path = str(adapters.get("codex", "")).strip()
    smoke_path = _derive_smoke_path(source_path)

    spec_exists = bool(spec_path) and (root / spec_path).exists()
    smoke_exists = (root / smoke_path).exists()
    can_only_propose = bool(capabilities.get("can_only_propose", False))
    audit_mode = "audit-mode" in tags
    maintenance = skill_type == "maintenance"
    imported_cluster = "imported-cluster" in tags
    direct_meta_relation = (
        TARGET_SKILL_ID in related_skills
        or skill_id == "a2-skill-improver-readiness-operator"
        or "skill-improver-readiness" in tags
        or "truth-maintenance" in tags
    )

    score = 0
    reasons: list[str] = []
    if maintenance:
        score += 2
        reasons.append("maintenance skill")
    if spec_exists:
        score += 1
        reasons.append("dedicated codex spec present")
    if smoke_exists:
        score += 2
        reasons.append("dedicated smoke present")
    if can_only_propose:
        score += 2
        reasons.append("propose-only gate present")
    if audit_mode:
        score += 1
        reasons.append("audit-mode tag present")
    if direct_meta_relation:
        score += 2
        reasons.append("directly aligned with the skill-improver maintenance lane")
    if skill_id == READINESS_SKILL_ID:
        score += 2
        reasons.append("smallest directly related readiness-gate target")
    if imported_cluster:
        score -= 1
        reasons.append("imported cluster, so lower priority for the first native target")

    eligible = maintenance and spec_exists and smoke_exists and can_only_propose and audit_mode
    if not eligible:
        return None

    return {
        "skill_id": skill_id,
        "source_path": source_path,
        "skill_type": skill_type,
        "spec_path": spec_path,
        "smoke_path": smoke_path,
        "tags": tags,
        "score": score,
        "eligible": True,
        "selection_reasons": reasons,
        "related_to_skill_improver": direct_meta_relation,
        "imported_cluster": imported_cluster,
        "recommended_test_command": ["python3", smoke_path],
        "recommended_allowed_targets": [source_path],
    }


def build_skill_improver_target_selection_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root)

    readiness_report = _safe_load_json(root / READINESS_REPORT_PATH)
    readiness_ok = readiness_report.get("target_readiness") == "bounded_ready_for_first_target"

    registry_payload = _safe_load_json(root / REGISTRY_PATH)
    registry_items = registry_payload.items() if isinstance(registry_payload, dict) else []
    candidates = [
        item
        for skill_id, entry in registry_items
        if isinstance(entry, dict)
        for item in [_candidate_record(root, str(skill_id), entry)]
        if item is not None
    ]
    candidates.sort(
        key=lambda item: (
            -int(item["score"]),
            not bool(item["related_to_skill_improver"]),
            bool(item["imported_cluster"]),
            item["skill_id"],
        )
    )

    recommended_target = candidates[0] if readiness_ok and candidates else None
    issues: list[str] = []
    if not readiness_ok:
        issues.append("skill-improver readiness report does not currently allow first-target selection")
    if not candidates:
        issues.append("no eligible first-target candidates were found")

    report = {
        "schema": "skill_improver_target_selection_report_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "action_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": "SKILL_CLUSTER::a2-skill-truth-maintenance",
        "slice_id": "a2-skill-improver-target-selector-operator",
        "source_family": "Ratchet-native A2 truth maintenance",
        "target_skill_id": TARGET_SKILL_ID,
        "readiness_report_path": READINESS_REPORT_PATH,
        "readiness_gate_status": readiness_report.get("target_readiness", ""),
        "recommended_first_target_class": RECOMMENDED_FIRST_TARGET_CLASS,
        "candidate_count": len(candidates),
        "candidate_targets": candidates[:5],
        "recommended_target": recommended_target or {},
        "recommended_actions": [
            "Keep this slice audit-only; do not mutate any skill from this selection report.",
            "If a first target is chosen, keep skill-improver-operator behind its explicit allowlist + approval-token gate.",
            "Use the recommended smoke path as the first bounded proof surface rather than widening to general repo mutation.",
        ],
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "skill_improver_target_selection_packet_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": report["cluster_id"],
        "selection_operator": report["slice_id"],
        "target_skill_id": TARGET_SKILL_ID,
        "allow_selection_slice": True,
        "allow_live_repo_mutation": False,
        "target_ready_for_first_class": readiness_ok,
        "recommended_first_target_class": RECOMMENDED_FIRST_TARGET_CLASS,
        "recommended_target_skill_id": recommended_target.get("skill_id", "") if recommended_target else "",
        "recommended_target_skill_path": recommended_target.get("source_path", "") if recommended_target else "",
        "recommended_target_smoke_path": recommended_target.get("smoke_path", "") if recommended_target else "",
        "recommended_test_command": recommended_target.get("recommended_test_command", []) if recommended_target else [],
        "recommended_allowed_targets": recommended_target.get("recommended_allowed_targets", []) if recommended_target else [],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    candidates = report.get("candidate_targets", [])
    lines = [
        "# Skill Improver Target Selection Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- target_skill_id: `{report.get('target_skill_id', '')}`",
        f"- readiness_gate_status: `{report.get('readiness_gate_status', '')}`",
        f"- candidate_count: `{report.get('candidate_count', 0)}`",
        f"- recommended_first_target_class: `{report.get('recommended_first_target_class', '')}`",
        f"- do_not_promote: `{report.get('do_not_promote', False)}`",
        "",
        "## Recommended Target",
    ]
    recommended_target = report.get("recommended_target", {})
    if recommended_target:
        lines.extend(
            [
                f"- skill_id: `{recommended_target.get('skill_id', '')}`",
                f"- source_path: `{recommended_target.get('source_path', '')}`",
                f"- smoke_path: `{recommended_target.get('smoke_path', '')}`",
                f"- score: `{recommended_target.get('score', 0)}`",
            ]
        )
    else:
        lines.append("- none")

    lines.extend(["", "## Candidate Targets"])
    if candidates:
        for item in candidates:
            lines.append(
                f"- `{item.get('skill_id', '')}`: score={item.get('score', 0)}; "
                f"source={item.get('source_path', '')}; smoke={item.get('smoke_path', '')}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Recommended Actions"])
    for action in report.get("recommended_actions", []):
        lines.append(f"- {action}")

    lines.extend(["", "## Packet Summary"])
    lines.append(f"- target_ready_for_first_class: `{packet.get('target_ready_for_first_class', False)}`")
    lines.append(f"- recommended_target_skill_id: `{packet.get('recommended_target_skill_id', '')}`")
    return "\n".join(lines) + "\n"


def run_a2_skill_improver_target_selector(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), TARGET_SELECTOR_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), TARGET_SELECTOR_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), TARGET_SELECTOR_PACKET_JSON)

    report, packet = build_skill_improver_target_selection_report(root, ctx)
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
    print("PASS: a2 skill improver target selector operator self-test")
