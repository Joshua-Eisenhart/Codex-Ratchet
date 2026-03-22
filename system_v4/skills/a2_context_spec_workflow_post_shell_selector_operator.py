"""
a2_context_spec_workflow_post_shell_selector_operator.py

Selector-only post-shell controller slice for the context-spec-workflow-memory
cluster.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_ID = "SKILL_CLUSTER::context-spec-workflow-memory"
SLICE_ID = "a2-context-spec-workflow-post-shell-selector-operator"

APPEND_SAFE_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_REPORT__CURRENT__v1.json"
)
FOLLOW_ON_SELECTOR_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json"
)
EVERMEM_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json"
)

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_POST_SHELL_SELECTOR_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_POST_SHELL_SELECTOR_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_POST_SHELL_SELECTOR_PACKET__CURRENT__v1.json"
)

SELECTION_SCOPE = "bounded_post_shell_selection"
SELECTED_HOLD_ID = "hold_after_append_safe_shell"
STANDBY_PATTERN_ID = "executable_spec_coupling"
STANDBY_NEXT_SLICE_ID = "a2-executable-spec-coupling-audit-operator"

DEFAULT_NON_GOALS = [
    "Do not directly land another pattern family from this selector.",
    "Do not widen into multiple pattern families at once.",
    "Do not claim runtime-live, service, training, or migration authority.",
    "Do not claim canonical A2/A1 brain replacement.",
    "Do not claim graph-substrate replacement.",
    "Do not claim memory-platform ownership.",
]

DEFAULT_RECOMMENDED_ACTIONS = [
    "Keep the context/spec/workflow cluster held after the append-safe landing unless a future explicit reselection reopens it.",
    "If this cluster is reopened later, take executable-spec-coupling next before workflow-review discipline or scoped-memory-sidecar.",
    "Keep scoped-memory-sidecar blocked while EverMem/backend reachability is not green.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _load_json(path: Path) -> dict[str, Any]:
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


def _selection_options(evermem_green: bool) -> list[dict[str, Any]]:
    return [
        {
            "option_id": SELECTED_HOLD_ID,
            "pattern_id": "",
            "label": "hold after append-safe shell",
            "status": "selected",
            "score": 10,
            "recommended_next_slice_id": "",
            "reasons": [
                "the landed append-safe slice explicitly ended in a hold state",
                "continuing by momentum would skip the current audit-only fence",
            ],
            "blocking_reasons": [],
        },
        {
            "option_id": "standby_executable_spec_coupling",
            "pattern_id": STANDBY_PATTERN_ID,
            "label": "executable spec coupling",
            "status": "standby",
            "score": 8,
            "recommended_next_slice_id": STANDBY_NEXT_SLICE_ID,
            "reasons": [
                "it was already the strongest non-selected pattern in the earlier follow-on selector",
                "it best matches the repeated repo/user pressure about keeping specs live and coupled",
            ],
            "blocking_reasons": [
                "requires future explicit reselection after the current post-shell hold",
            ],
        },
        {
            "option_id": "standby_workflow_review_discipline",
            "pattern_id": "workflow_review_discipline",
            "label": "workflow review discipline",
            "status": "standby",
            "score": 6,
            "recommended_next_slice_id": "a2-workflow-review-discipline-audit-operator",
            "reasons": [
                "still useful as a later bounded cluster seam",
            ],
            "blocking_reasons": [
                "lower leverage than executable-spec-coupling once the append-safe shell is landed",
            ],
        },
        {
            "option_id": "blocked_scoped_memory_sidecar",
            "pattern_id": "scoped_memory_sidecar",
            "label": "scoped memory sidecar",
            "status": "standby" if evermem_green else "blocked",
            "score": 4 if evermem_green else 0,
            "recommended_next_slice_id": "a2-scoped-memory-sidecar-compat-audit-operator",
            "reasons": [
                "memory-sidecar pressure remains relevant later",
            ],
            "blocking_reasons": [] if evermem_green else [
                "EverMem/backend reachability is not currently green",
            ],
        },
    ]


def build_a2_context_spec_workflow_post_shell_selector_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    selection_scope = str(ctx.get("selection_scope", SELECTION_SCOPE)).strip()
    issues: list[str] = []
    if selection_scope != SELECTION_SCOPE:
        issues.append("selection_scope widened beyond bounded post-shell selection")

    append_safe_report = _load_json(
        _resolve_output_path(root, ctx.get("append_safe_report_path"), APPEND_SAFE_REPORT_PATH)
    )
    follow_on_selector_report = _load_json(
        _resolve_output_path(root, ctx.get("follow_on_selector_report_path"), FOLLOW_ON_SELECTOR_REPORT_PATH)
    )
    evermem_report = _load_json(
        _resolve_output_path(root, ctx.get("evermem_report_path"), EVERMEM_REPORT_PATH)
    )

    append_safe_ok = (
        append_safe_report.get("status") == "ok"
        and append_safe_report.get("slice_id") == "a2-append-safe-context-shell-audit-operator"
        and append_safe_report.get("recommended_next_step") == "hold_append_safe_context_shell_as_audit_only"
    )
    if not append_safe_ok:
        issues.append("append-safe context shell slice is not green enough for a post-shell selector hold")

    prior_selector_aligned = (
        follow_on_selector_report.get("status") == "ok"
        and follow_on_selector_report.get("selected_pattern_id") == "append_safe_context_shell"
        and follow_on_selector_report.get("recommended_next_slice_id") == "a2-append-safe-context-shell-audit-operator"
    )
    if not prior_selector_aligned:
        issues.append("prior follow-on selector is not aligned with the landed append-safe slice")

    evermem_green = evermem_report.get("status") == "ok"
    options = _selection_options(evermem_green)
    selected = options[0] if not issues else {
        "option_id": "hold_attention_required",
        "pattern_id": "",
        "label": "hold pending alignment repair",
        "status": "selected",
        "score": 10,
        "recommended_next_slice_id": "",
        "reasons": ["one or more upstream surfaces are not aligned enough to recommend a new standby continuation"],
        "blocking_reasons": list(issues),
    }

    report = {
        "schema": "A2_CONTEXT_SPEC_WORKFLOW_POST_SHELL_SELECTOR_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "selector_only": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "selection_scope": selection_scope,
        "append_safe_alignment": {
            "append_safe_ok": append_safe_ok,
            "prior_selector_aligned": prior_selector_aligned,
        },
        "selected_option_id": selected["option_id"],
        "selected_pattern_id": selected.get("pattern_id", ""),
        "selected_option": selected,
        "standby_pattern_id": STANDBY_PATTERN_ID if not issues else "",
        "standby_next_slice_id": STANDBY_NEXT_SLICE_ID if not issues else "",
        "selection_options": options if not issues else [selected],
        "recommended_next_slice_id": "",
        "recommended_next_step": "hold_cluster_after_append_safe_shell" if not issues else "",
        "recommended_actions": list(DEFAULT_RECOMMENDED_ACTIONS),
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "A2_CONTEXT_SPEC_WORKFLOW_POST_SHELL_SELECTOR_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "selected_option_id": report["selected_option_id"],
        "selected_pattern_id": report["selected_pattern_id"],
        "standby_pattern_id": report["standby_pattern_id"],
        "standby_next_slice_id": report["standby_next_slice_id"],
        "allow_runtime_live_claims": False,
        "allow_service_bootstrap": False,
        "allow_training": False,
        "allow_canonical_brain_replacement": False,
        "allow_graph_substrate_replacement": False,
        "allow_memory_platform_import": False,
        "allow_multi_pattern_widening": False,
        "recommended_next_slice_id": report["recommended_next_slice_id"],
        "recommended_next_step": report["recommended_next_step"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Context Spec Workflow Post Shell Selector Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- selection_scope: `{report.get('selection_scope', '')}`",
        f"- selected_option_id: `{report.get('selected_option_id', '')}`",
        f"- standby_pattern_id: `{report.get('standby_pattern_id', '')}`",
        f"- standby_next_slice_id: `{report.get('standby_next_slice_id', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        "",
        "## Options",
    ]
    for option in report.get("selection_options", []):
        lines.append(
            f"- {option.get('option_id', '')}: status=`{option.get('status', '')}` score=`{option.get('score', 0)}` next=`{option.get('recommended_next_slice_id', '')}`"
        )
    lines.extend(["", "## Packet"])
    lines.append(f"- standby_next_slice_id: `{packet.get('standby_next_slice_id', '')}`")
    lines.append(f"- allow_multi_pattern_widening: `{packet.get('allow_multi_pattern_widening', False)}`")
    lines.extend(["", "## Issues"])
    issues = report.get("issues", [])
    lines.extend(f"- {item}" for item in issues) if issues else lines.append("- none")
    lines.extend(["", "## Non-Goals"])
    lines.extend(f"- {item}" for item in report.get("non_goals", []))
    lines.append("")
    return "\n".join(lines)


def run_a2_context_spec_workflow_post_shell_selector(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_a2_context_spec_workflow_post_shell_selector_report(root, ctx)

    report_json_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    report_md_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_json_path, report)
    _write_text(report_md_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "packet_path": str(packet_path),
        "recommended_next_step": report["recommended_next_step"],
        "standby_next_slice_id": report["standby_next_slice_id"],
    }


if __name__ == "__main__":
    print(json.dumps(run_a2_context_spec_workflow_post_shell_selector({}), indent=2, sort_keys=True))
