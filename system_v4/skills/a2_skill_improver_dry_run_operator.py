"""
a2_skill_improver_dry_run_operator.py

Bounded dry-run bridge that exercises skill-improver-operator against one
explicit first-target allowlist and emits repo-held report surfaces without any
repo mutation.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_improver_operator import run_skill_improver

READINESS_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json"
)
TARGET_SELECTION_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json"
)
DRY_RUN_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_DRY_RUN_REPORT__CURRENT__v1.json"
)
DRY_RUN_REPORT_MD = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_DRY_RUN_REPORT__CURRENT__v1.md"
)
DRY_RUN_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_DRY_RUN_PACKET__CURRENT__v1.json"
)

DEFAULT_TARGET_ID = "a2-skill-improver-readiness-operator"
ALLOWED_TARGETS: dict[str, dict[str, Any]] = {
    "a2-skill-improver-readiness-operator": {
        "skill_id": "a2-skill-improver-readiness-operator",
        "path": "system_v4/skills/a2_skill_improver_readiness_operator.py",
        "test_command": [
            "python3",
            "system_v4/skills/test_a2_skill_improver_readiness_operator_candidate_smoke.py",
            "{candidate_path}",
        ],
        "reason": "selector-recommended first bounded target with dedicated candidate-aware smoke proof",
    }
}

DEFAULT_NON_GOALS = [
    "Do not permit repo writeback from this dry-run slice.",
    "Do not widen target selection beyond the explicit first-target allowlist.",
    "Do not auto-generate candidate code inside this operator.",
    "Do not treat dry-run success as live mutation approval.",
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


def build_skill_improver_dry_run_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root).resolve()
    ctx = ctx or {}
    readiness_payload = _safe_load_json(root / READINESS_REPORT_JSON)
    selector_payload = _safe_load_json(root / TARGET_SELECTION_PACKET_JSON)
    default_target_id = str(selector_payload.get("recommended_target_skill_id", "")).strip() or DEFAULT_TARGET_ID
    selected_target_id = str(ctx.get("target_skill_id", default_target_id)).strip() or default_target_id
    target_spec = ALLOWED_TARGETS.get(selected_target_id)
    candidate_code = str(ctx.get("candidate_code", ""))

    issues: list[str] = []
    if not readiness_payload:
        issues.append("skill improver readiness report is missing")
    elif readiness_payload.get("target_readiness") != "bounded_ready_for_first_target":
        issues.append("skill improver readiness report is not at bounded_ready_for_first_target")
    if target_spec is None:
        issues.append(f"target skill id is not in the dry-run allowlist: {selected_target_id}")

    improver_result: dict[str, Any] = {
        "improved": False,
        "detail": "dry-run not attempted",
        "path": "",
        "proposed_change": False,
        "compile_ok": False,
        "tests_state": "not_run",
        "score": 0,
        "write_permitted": False,
        "dry_run": True,
    }
    selected_target_summary: dict[str, Any] = {
        "selected_target_id": selected_target_id,
        "selected_target_path": "",
        "test_command": [],
        "selection_reason": "",
    }

    if target_spec is not None:
        target_path = root / str(target_spec["path"])
        selected_target_summary = {
            "selected_target_id": selected_target_id,
            "selected_target_path": str(target_path.relative_to(root)),
            "test_command": list(target_spec["test_command"]),
            "selection_reason": str(target_spec["reason"]),
        }
        improver_result = run_skill_improver(
            {
                "target_skill_path": str(target_path),
                "candidate_code": candidate_code,
                "test_command": list(target_spec["test_command"]),
                "allow_write": False,
                "allowed_targets": [str(target_path)],
            }
        )

    if issues:
        status = "action_required"
    elif not candidate_code:
        status = "candidate_required"
    elif improver_result["compile_ok"] and improver_result["tests_state"] == "passed":
        status = "ok"
    else:
        status = "action_required"

    report = {
        "schema": "SKILL_IMPROVER_DRY_RUN_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": status,
        "cluster_id": "SKILL_CLUSTER::a2-skill-truth-maintenance",
        "slice_id": "a2-skill-improver-dry-run-operator",
        "source_family": "Ratchet-native A2 truth maintenance",
        "dry_run_only": True,
        "audit_only": False,
        "do_not_promote": True,
        "allow_repo_write": False,
        "readiness_report_path": READINESS_REPORT_JSON,
        "target_selection_packet_path": TARGET_SELECTION_PACKET_JSON,
        "readiness_target_readiness": readiness_payload.get("target_readiness", ""),
        "selector_recommended_target_id": default_target_id,
        "allowed_targets": [
            {
                "skill_id": target_id,
                "path": spec["path"],
                "reason": spec["reason"],
            }
            for target_id, spec in sorted(ALLOWED_TARGETS.items())
        ],
        "selected_target": selected_target_summary,
        "candidate_code_present": bool(candidate_code),
        "improver_result": improver_result,
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }
    packet = {
        "schema": "SKILL_IMPROVER_DRY_RUN_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "allow_dry_run_first_target": True,
        "allow_live_repo_mutation": False,
        "selected_target_id": selected_target_id,
        "selected_target_path": selected_target_summary["selected_target_path"],
        "selector_recommended_target_id": default_target_id,
        "status": status,
        "candidate_code_present": bool(candidate_code),
        "tests_state": improver_result["tests_state"],
        "compile_ok": improver_result["compile_ok"],
        "write_permitted": improver_result["write_permitted"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    selected = report["selected_target"]
    result = report["improver_result"]
    issues = report.get("issues", [])
    allowed_lines = [
        f"- `{item['skill_id']}` -> `{item['path']}` ({item['reason']})"
        for item in report.get("allowed_targets", [])
    ] or ["- none"]
    issue_lines = [f"- {item}" for item in issues] or ["- none"]
    return "\n".join(
        [
            "# Skill Improver Dry-Run Report",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- cluster_id: `{report['cluster_id']}`",
            f"- slice_id: `{report['slice_id']}`",
            f"- dry_run_only: `{report['dry_run_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- readiness_target_readiness: `{report['readiness_target_readiness']}`",
            f"- selector_recommended_target_id: `{report['selector_recommended_target_id']}`",
            "",
            "## Selected Target",
            f"- selected_target_id: `{selected['selected_target_id']}`",
            f"- selected_target_path: `{selected['selected_target_path']}`",
            f"- selection_reason: {selected['selection_reason']}",
            "",
            "## Allowed Targets",
            *allowed_lines,
            "",
            "## Dry-Run Result",
            f"- candidate_code_present: `{report['candidate_code_present']}`",
            f"- compile_ok: `{result['compile_ok']}`",
            f"- tests_state: `{result['tests_state']}`",
            f"- write_permitted: `{result['write_permitted']}`",
            f"- detail: {result['detail']}",
            "",
            "## Packet",
            f"- allow_dry_run_first_target: `{packet['allow_dry_run_first_target']}`",
            f"- allow_live_repo_mutation: `{packet['allow_live_repo_mutation']}`",
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def run_a2_skill_improver_dry_run(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo", REPO_ROOT)).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), DRY_RUN_REPORT_JSON)
    md_path = _resolve_output_path(root, ctx.get("report_md_path"), DRY_RUN_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), DRY_RUN_PACKET_JSON)

    report, packet = build_skill_improver_dry_run_report(root, ctx)
    _write_json(report_path, report)
    _write_json(packet_path, packet)
    _write_text(md_path, _render_markdown(report, packet))

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(md_path)
    emitted["packet_path"] = str(packet_path)
    return emitted


if __name__ == "__main__":
    payload = run_a2_skill_improver_dry_run({})
    print(json.dumps(payload, indent=2, sort_keys=True))
