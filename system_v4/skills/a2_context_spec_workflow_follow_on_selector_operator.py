"""
a2_context_spec_workflow_follow_on_selector_operator.py

Selector-only follow-on slice for the context-spec-workflow-memory cluster.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_ID = "SKILL_CLUSTER::context-spec-workflow-memory"
SLICE_ID = "a2-context-spec-workflow-follow-on-selector-operator"

PATTERN_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.json"
)
PATTERN_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_PACKET__CURRENT__v1.json"
)
SOURCE_SELECTOR_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_SOURCE_FAMILY_LANE_SELECTION_REPORT__CURRENT__v1.json"
)
EVERMEM_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json"
)
CONTROLLER_RECORD_PATH = "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md"

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json"
)

SELECTION_SCOPE = "bounded_cluster_follow_on_selection"

PATTERN_OPTIONS = [
    {
        "pattern_id": "append_safe_context_shell",
        "label": "append-safe context shell",
        "recommended_next_slice_id": "a2-append-safe-context-shell-audit-operator",
        "reasons": [
            "Directly matches the persistent user pressure around low-bloat continuity, saved intent, and thread-to-thread carry-forward.",
            "Maps to standing A2 continuity surfaces that already need disciplined append-safe maintenance.",
            "Improves the system's self-awareness substrate without opening runtime, service, or memory-platform claims.",
        ],
    },
    {
        "pattern_id": "executable_spec_coupling",
        "label": "executable spec coupling",
        "recommended_next_slice_id": "a2-executable-spec-coupling-audit-operator",
        "reasons": [
            "Directly addresses the repeated concern that specs can decouple from live system behavior.",
            "Maps cleanly onto owner-law and current build-plan surfaces.",
            "Best second choice once the continuity shell is explicitly tightened.",
        ],
    },
    {
        "pattern_id": "workflow_review_discipline",
        "label": "workflow review discipline",
        "recommended_next_slice_id": "a2-workflow-review-discipline-audit-operator",
        "reasons": [
            "Useful for keeping planning, delegation, and verification bounded.",
            "Lower leverage than continuity/spec coupling because the repo already has multiple selector and audit lanes.",
        ],
    },
    {
        "pattern_id": "scoped_memory_sidecar",
        "label": "scoped memory sidecar",
        "recommended_next_slice_id": "a2-scoped-memory-sidecar-compat-audit-operator",
        "reasons": [
            "Conceptually relevant to memory-sidecar patterns.",
            "Should stay behind EverMem/backend reachability and canonical-brain separation.",
        ],
    },
]

DEFAULT_NON_GOALS = [
    "Do not widen into runtime import, service bootstrap, or training.",
    "Do not claim canonical A2/A1 brain replacement.",
    "Do not claim graph-substrate replacement.",
    "Do not select more than one follow-on pattern family at once.",
    "Do not mutate registry, graph, or external services from this selector slice.",
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


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _source_selector_cluster_record(selector_report: dict[str, Any]) -> dict[str, Any]:
    for item in selector_report.get("candidate_clusters", []):
        if item.get("cluster_id") == CLUSTER_ID:
            return item
    return {}


def _pattern_record(pattern_report: dict[str, Any], pattern_id: str) -> dict[str, Any]:
    for item in pattern_report.get("admissible_pattern_families", []):
        if item.get("pattern_id") == pattern_id:
            return item
    return {}


def _selection_options(
    pattern_report: dict[str, Any],
    evermem_report: dict[str, Any],
    controller_record_text: str,
) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    evermem_blocked = evermem_report.get("status") != "ok"
    continuity_pressure = "append-safe" in controller_record_text.lower() or "low-bloat" in controller_record_text.lower()
    _ = continuity_pressure  # used for explanation clarity only

    for index, option in enumerate(PATTERN_OPTIONS):
        pattern_id = option["pattern_id"]
        pattern_exists = bool(_pattern_record(pattern_report, pattern_id))
        status = "standby"
        score = max(1, 10 - index * 2)
        reasons = list(option["reasons"])
        blocking_reasons: list[str] = []

        if not pattern_exists:
            status = "blocked"
            score = 0
            blocking_reasons.append("pattern family was not admitted by the first slice")

        if pattern_id == "scoped_memory_sidecar" and evermem_blocked:
            status = "blocked"
            score = 0
            blocking_reasons.append("current outside-memory / EverMem lane is not green")

        if pattern_id == "append_safe_context_shell" and pattern_exists:
            status = "selected"
            score = 10
            reasons.append(
                "Selected first because the standing controller/user pressure is primarily about preserving nuanced context without doc bloat."
            )

        options.append(
            {
                "pattern_id": pattern_id,
                "label": option["label"],
                "recommended_next_slice_id": option["recommended_next_slice_id"],
                "status": status,
                "score": score,
                "reasons": reasons,
                "blocking_reasons": blocking_reasons,
            }
        )

    return options


def _recommended_choice(options: list[dict[str, Any]]) -> dict[str, Any]:
    for option in options:
        if option["status"] == "selected":
            return option
    return {}


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Context Spec Workflow Follow-On Selector Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- selection_scope: `{report.get('selection_scope', '')}`",
        f"- selected_pattern_id: `{report.get('selected_pattern_id', '')}`",
        f"- recommended_next_slice_id: `{report.get('recommended_next_slice_id', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        "",
        "## Options",
    ]
    for option in report.get("selection_options", []):
        lines.append(
            f"- {option.get('pattern_id', '')}: status=`{option.get('status', '')}` score=`{option.get('score', 0)}` next=`{option.get('recommended_next_slice_id', '')}`"
        )
    if not report.get("selection_options"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Packet",
            f"- selected_pattern_id: `{packet.get('selected_pattern_id', '')}`",
            f"- recommended_next_slice_id: `{packet.get('recommended_next_slice_id', '')}`",
            f"- allow_runtime_live_claims: `{packet.get('allow_runtime_live_claims', False)}`",
            "",
            "## Issues",
        ]
    )
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    lines.extend(issue_lines)
    lines.append("")
    return "\n".join(lines)


def build_a2_context_spec_workflow_follow_on_selector_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    pattern_report_path = _resolve_output_path(root, ctx.get("pattern_report_path"), PATTERN_REPORT_PATH)
    pattern_packet_path = _resolve_output_path(root, ctx.get("pattern_packet_path"), PATTERN_PACKET_PATH)
    source_selector_report_path = _resolve_output_path(
        root, ctx.get("source_selector_report_path"), SOURCE_SELECTOR_REPORT_PATH
    )
    evermem_report_path = _resolve_output_path(root, ctx.get("evermem_report_path"), EVERMEM_REPORT_PATH)
    controller_record_path = _resolve_output_path(root, ctx.get("controller_record_path"), CONTROLLER_RECORD_PATH)

    selection_scope = str(ctx.get("selection_scope", SELECTION_SCOPE)).strip()

    pattern_report = _load_json(pattern_report_path)
    pattern_packet = _load_json(pattern_packet_path)
    source_selector_report = _load_json(source_selector_report_path)
    evermem_report = _load_json(evermem_report_path)
    controller_record_text = _load_text(controller_record_path)

    issues: list[str] = []
    if selection_scope != SELECTION_SCOPE:
        issues.append("selection_scope widened beyond bounded cluster follow-on selection")
    if pattern_report.get("status") != "ok":
        issues.append("pattern audit report is missing or not ok")
    if pattern_packet.get("recommended_next_step") != "hold_first_slice_as_audit_only":
        issues.append("pattern audit no longer justifies a bounded follow-on selector")

    cluster_record = _source_selector_cluster_record(source_selector_report)
    if not cluster_record:
        issues.append("source-family selector does not currently describe the context-spec-workflow cluster")
    else:
        if cluster_record.get("already_landed") is not True:
            issues.append("source-family selector does not confirm that the first slice is already landed")
        if cluster_record.get("recommended_first_slice_id") != "a2-context-spec-workflow-pattern-audit-operator":
            issues.append("source-family selector no longer aligns with the landed first slice")

    selection_options = _selection_options(pattern_report, evermem_report, controller_record_text) if not issues else []
    selected = _recommended_choice(selection_options)
    recommended_next_slice_id = str(selected.get("recommended_next_slice_id", "")) if selected else ""
    selected_pattern_id = str(selected.get("pattern_id", "")) if selected else ""
    recommended_next_step = recommended_next_slice_id if selected else ""

    report = {
        "schema": "A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues and selected else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "selection_scope": selection_scope,
        "source_family": "Context-Engineering / spec-kit / superpowers / mem0 source set",
        "selected_pattern_id": selected_pattern_id,
        "recommended_next_slice_id": recommended_next_slice_id,
        "recommended_next_step": recommended_next_step,
        "selection_options": selection_options,
        "supporting_signals": {
            "pattern_audit_status": pattern_report.get("status", ""),
            "pattern_audit_next_step": pattern_packet.get("recommended_next_step", ""),
            "source_selector_fail_closed": (
                source_selector_report.get("selection_state", "") == "hold_no_eligible_lane"
                or (
                    source_selector_report.get("status", "") == "attention_required"
                    and not source_selector_report.get("recommended_next_cluster")
                )
            ),
            "evermem_status": evermem_report.get("status", ""),
        },
        "recommended_actions": [
            "Keep this selector-only and open only one bounded follow-on pattern family next.",
            "Do not widen context, specs, workflow, and memory all at once.",
            "Use the selected follow-on to tighten existing Ratchet seams before any substrate or automation claim.",
        ],
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "selection_scope": selection_scope,
        "selected_pattern_id": selected_pattern_id,
        "recommended_next_slice_id": recommended_next_slice_id,
        "recommended_next_step": recommended_next_step,
        "allow_runtime_live_claims": False,
        "allow_service_bootstrap": False,
        "allow_training": False,
        "allow_canonical_brain_replacement": False,
        "allow_graph_substrate_replacement": False,
        "allow_registry_mutation": False,
    }
    return report, packet


def run_a2_context_spec_workflow_follow_on_selector(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    report, packet = build_a2_context_spec_workflow_follow_on_selector_report(root, ctx)
    _write_json(report_path, report)
    _write_json(packet_path, packet)
    _write_text(markdown_path, _render_markdown(report, packet))

    return {
        "status": report["status"],
        "selected_pattern_id": report["selected_pattern_id"],
        "recommended_next_slice_id": report["recommended_next_slice_id"],
        "report_json_path": str(report_path),
        "report_md_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    result = run_a2_context_spec_workflow_follow_on_selector({"repo_root": REPO_ROOT})
    print(json.dumps(result, indent=2, sort_keys=True))
