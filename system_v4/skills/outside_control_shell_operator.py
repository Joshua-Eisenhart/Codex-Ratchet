"""
outside_control_shell_operator.py

Bounded pi-mono-derived outside control-shell/session-host audit slice for
Ratchet.

This operator stays read-only over local pi-mono session-host evidence and
emits one repo-held report plus one compact packet. It does not claim full
pi-mono import, runtime hosting, memory integration, or A2 replacement.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET_SURFACE = (
    "work/reference_repos/other/pi-mono/packages/coding-agent/test/fixtures/large-session.jsonl"
)
DEFAULT_BEFORE_COMPACTION_SURFACE = (
    "work/reference_repos/other/pi-mono/packages/coding-agent/test/fixtures/before-compaction.jsonl"
)
DEFAULT_SESSION_DOC = "work/reference_repos/other/pi-mono/packages/coding-agent/docs/session.md"
DEFAULT_RPC_DOC = "work/reference_repos/other/pi-mono/packages/coding-agent/docs/rpc.md"
DEFAULT_INTERACTIVE_SHELL_EXAMPLE = (
    "work/reference_repos/other/pi-mono/packages/coding-agent/examples/extensions/interactive-shell.ts"
)
DEFAULT_MOM_DOC = "work/reference_repos/other/pi-mono/packages/mom/README.md"

OUTSIDE_SESSION_HOST_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json"
)
OUTSIDE_SESSION_HOST_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md"
)
OUTSIDE_SESSION_HOST_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json"
)

DEFAULT_NON_GOALS = [
    "Do not claim full pi-mono integration or runtime hosting inside Ratchet.",
    "Do not claim memory integration, startup retrieval, or A2 replacement.",
    "Do not mutate pi-mono workspaces, session files, or canonical A2 state.",
    "Do not treat mom workspace surfaces or context.jsonl as canonical control state.",
]

MOM_SAFE_SURFACES = [
    "workspace/channel layout",
    "log.jsonl",
    "context.jsonl shape only",
    "global and channel MEMORY.md",
    "global and channel skills/",
    "settings.json",
    "attachment inventory and paths only",
]

MOM_DANGEROUS_SURFACES = [
    "treating mom as a safe host runtime",
    "treating context.jsonl as canonical truth",
    "auth or credential files",
    "attachment bodies",
    "host or container execution state",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _source_ref_status(root: Path) -> dict[str, dict[str, Any]]:
    refs = {
        "session_doc": {"path": DEFAULT_SESSION_DOC, "required": True},
        "rpc_doc": {"path": DEFAULT_RPC_DOC, "required": True},
        "interactive_shell_example": {"path": DEFAULT_INTERACTIVE_SHELL_EXAMPLE, "required": True},
        "mom_doc": {"path": DEFAULT_MOM_DOC, "required": True},
        "before_compaction_fixture": {"path": DEFAULT_BEFORE_COMPACTION_SURFACE, "required": False},
    }
    status: dict[str, dict[str, Any]] = {}
    for label, spec in refs.items():
        path = root / spec["path"]
        status[label] = {
            "path": spec["path"],
            "required": bool(spec["required"]),
            "exists": path.exists(),
        }
    return status


def _parse_session_surface(target_path: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    if not target_path.exists():
        return {
            "session_header": {},
            "entry_counts": {},
            "message_counts": {},
            "assistant_stop_reasons": {},
            "compaction_summary": {
                "entry_type_count": 0,
                "entry_type_present": False,
                "message_role_count": 0,
                "message_role_present": False,
            },
            "bash_execution_present": False,
        }, [f"target session surface missing: {target_path}"]

    entry_counts: dict[str, int] = {}
    message_counts: dict[str, int] = {}
    assistant_stop_reasons: dict[str, int] = {}
    header: dict[str, Any] = {}
    compaction_entry_count = 0
    compaction_message_role_count = 0
    bash_execution_present = False

    for lineno, line in enumerate(target_path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(f"jsonl parse error at line {lineno}: {exc.msg}")
            continue

        entry_type = str(payload.get("type", "")).strip() or "<missing>"
        entry_counts[entry_type] = entry_counts.get(entry_type, 0) + 1
        if entry_type == "session" and not header:
            header = payload
        if entry_type == "compaction":
            compaction_entry_count += 1
        if entry_type != "message":
            continue

        message = payload.get("message", {})
        if not isinstance(message, dict):
            issues.append(f"message entry missing object payload at line {lineno}")
            continue

        role = str(message.get("role", "")).strip() or "<missing>"
        message_counts[role] = message_counts.get(role, 0) + 1
        if role == "assistant":
            stop_reason = str(message.get("stopReason", "")).strip() or "<missing>"
            assistant_stop_reasons[stop_reason] = assistant_stop_reasons.get(stop_reason, 0) + 1
        if role == "bashExecution":
            bash_execution_present = True
        if role == "compactionSummary":
            compaction_message_role_count += 1

    if not header:
        issues.append("session header not found in target surface")
    if not message_counts:
        issues.append("target surface has no message entries")

    selected_header = {
        key: header[key]
        for key in (
            "id",
            "timestamp",
            "cwd",
            "provider",
            "modelId",
            "thinkingLevel",
            "version",
            "parentSession",
            "branchedFrom",
        )
        if key in header
    }
    if header:
        selected_header["declared_keys"] = sorted(header.keys())
        selected_header["version_present"] = "version" in header
        selected_header["branch_reference_present"] = any(
            key in header for key in ("parentSession", "branchedFrom")
        )

    return {
        "session_header": selected_header,
        "entry_counts": entry_counts,
        "message_counts": message_counts,
        "assistant_stop_reasons": assistant_stop_reasons,
        "compaction_summary": {
            "entry_type_count": compaction_entry_count,
            "entry_type_present": compaction_entry_count > 0,
            "message_role_count": compaction_message_role_count,
            "message_role_present": compaction_message_role_count > 0,
        },
        "bash_execution_present": bash_execution_present,
    }, issues


def _interactive_shell_capability(root: Path) -> dict[str, Any]:
    rpc_path = root / DEFAULT_RPC_DOC
    example_path = root / DEFAULT_INTERACTIVE_SHELL_EXAMPLE
    rpc_text = _safe_load_text(rpc_path)
    return {
        "rpc_doc_path": DEFAULT_RPC_DOC,
        "interactive_shell_example_path": DEFAULT_INTERACTIVE_SHELL_EXAMPLE,
        "rpc_mode_documented": "RPC Mode" in rpc_text,
        "get_state_documented": '"type": "get_state"' in rpc_text,
        "steer_documented": '"type": "steer"' in rpc_text,
        "follow_up_documented": '"type": "follow_up"' in rpc_text,
        "interactive_shell_example_present": example_path.exists(),
    }


def _mom_workspace_boundary(root: Path) -> dict[str, Any]:
    mom_path = root / DEFAULT_MOM_DOC
    mom_text = _safe_load_text(mom_path)
    return {
        "doc_path": DEFAULT_MOM_DOC,
        "doc_present": mom_path.exists(),
        "workspace_layout_documented": all(
            token in mom_text
            for token in ("log.jsonl", "context.jsonl", "MEMORY.md", "skills/", "settings.json")
        ),
        "safe_observable_surfaces": MOM_SAFE_SURFACES,
        "dangerous_surfaces": MOM_DANGEROUS_SURFACES,
        "boundary_only": True,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    header = report.get("session_header", {})
    entry_counts = report.get("entry_counts", {})
    message_counts = report.get("message_counts", {})
    stop_reasons = report.get("assistant_stop_reasons", {})
    interactive = report.get("interactive_shell_capability", {})
    mom_boundary = report.get("mom_workspace_boundary", {})
    issues = report.get("issues", [])
    actions = report.get("recommended_next_actions", [])
    return "\n".join(
        [
            "# Pi-mono Outside Session Host Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- cluster_id: `{report.get('cluster_id', '')}`",
            f"- first_slice: `{report.get('first_slice', '')}`",
            f"- source_family: `{report.get('source_family', '')}`",
            f"- target_surface_path: `{report.get('target_surface_path', '')}`",
            f"- audit_only: `{report.get('audit_only', False)}`",
            f"- observer_only: `{report.get('observer_only', False)}`",
            f"- do_not_promote: `{report.get('do_not_promote', False)}`",
            "",
            "## Session Header",
            *([f"- {key}: `{value}`" for key, value in header.items()] or ["- none"]),
            "",
            "## Entry Counts",
            *([f"- {key}: `{value}`" for key, value in sorted(entry_counts.items())] or ["- none"]),
            "",
            "## Message Counts",
            *([f"- {key}: `{value}`" for key, value in sorted(message_counts.items())] or ["- none"]),
            "",
            "## Assistant Stop Reasons",
            *([f"- {key}: `{value}`" for key, value in sorted(stop_reasons.items())] or ["- none"]),
            "",
            "## Interactive Shell Capability",
            f"- rpc_mode_documented: `{interactive.get('rpc_mode_documented', False)}`",
            f"- get_state_documented: `{interactive.get('get_state_documented', False)}`",
            f"- steer_documented: `{interactive.get('steer_documented', False)}`",
            f"- follow_up_documented: `{interactive.get('follow_up_documented', False)}`",
            f"- interactive_shell_example_present: `{interactive.get('interactive_shell_example_present', False)}`",
            "",
            "## Mom Boundary",
            f"- doc_present: `{mom_boundary.get('doc_present', False)}`",
            f"- workspace_layout_documented: `{mom_boundary.get('workspace_layout_documented', False)}`",
            f"- boundary_only: `{mom_boundary.get('boundary_only', False)}`",
            "",
            "## Recommended Next Actions",
            *[f"- {item}" for item in actions],
            "",
            "## Issues",
            *([f"- {item}" for item in issues] or ["- none"]),
            "",
        ]
    )


def build_outside_control_shell_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root).resolve()
    ctx = ctx or {}
    target_path = _resolve_output_path(root, ctx.get("target_surface_path"), DEFAULT_TARGET_SURFACE)
    parsed, parse_issues = _parse_session_surface(target_path)
    source_refs = _source_ref_status(root)
    issues = list(parse_issues)

    for label, ref in source_refs.items():
        if ref["required"] and not ref["exists"]:
            issues.append(f"required source ref missing: {label}")

    interactive = _interactive_shell_capability(root)
    mom_boundary = _mom_workspace_boundary(root)
    status = "ok" if not issues else "attention_required"

    report = {
        "schema": "A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": status,
        "cluster_id": "SKILL_CLUSTER::outside-control-shell-session-host",
        "first_slice": "outside-control-shell-operator",
        "source_family": "pi-mono",
        "audit_only": True,
        "observer_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "target_surface_path": str(target_path),
        "session_header": parsed["session_header"],
        "entry_counts": parsed["entry_counts"],
        "message_counts": parsed["message_counts"],
        "assistant_stop_reasons": parsed["assistant_stop_reasons"],
        "compaction_summary": {
            **parsed["compaction_summary"],
            "before_compaction_fixture_present": source_refs["before_compaction_fixture"]["exists"],
        },
        "bash_execution_present": parsed["bash_execution_present"],
        "interactive_shell_capability": interactive,
        "mom_workspace_boundary": mom_boundary,
        "source_ref_status": source_refs,
        "issues": issues,
        "recommended_next_actions": [
            "Keep the pi-mono slice report-only and read-only until a later host/session operator is justified.",
            "Treat mom as a workspace-boundary source only; do not treat it as canonical control state.",
            "Use this report as evidence for later outside-shell planning, not as proof of runtime integration.",
        ],
        "non_goals": DEFAULT_NON_GOALS,
    }

    packet = {
        "schema": "A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "cluster_id": report["cluster_id"],
        "first_slice": report["first_slice"],
        "source_family": report["source_family"],
        "allow_read_only_slice": status == "ok",
        "target_surface_path": str(target_path),
        "session_header": report["session_header"],
        "entry_counts": report["entry_counts"],
        "message_counts": report["message_counts"],
        "assistant_stop_reasons": report["assistant_stop_reasons"],
        "bash_execution_present": report["bash_execution_present"],
        "interactive_shell_example_present": interactive["interactive_shell_example_present"],
        "mom_boundary_only": True,
        "issues": issues,
        "non_goals": DEFAULT_NON_GOALS,
    }
    return report, packet


def run_outside_control_shell_operator(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    repo = Path(str(ctx.get("repo", REPO_ROOT))).resolve()
    report_json_path = _resolve_output_path(repo, ctx.get("report_json_path"), OUTSIDE_SESSION_HOST_REPORT_JSON)
    report_md_path = _resolve_output_path(repo, ctx.get("report_md_path"), OUTSIDE_SESSION_HOST_REPORT_MD)
    packet_path = _resolve_output_path(repo, ctx.get("packet_path"), OUTSIDE_SESSION_HOST_PACKET_JSON)

    report, packet = build_outside_control_shell_report(repo, ctx)
    _write_json(report_json_path, report)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(_render_markdown(report), encoding="utf-8")
    _write_json(packet_path, packet)

    return {
        **report,
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    emitted = run_outside_control_shell_operator({})
    assert emitted["first_slice"] == "outside-control-shell-operator"
    print("PASS: outside-control-shell-operator")
