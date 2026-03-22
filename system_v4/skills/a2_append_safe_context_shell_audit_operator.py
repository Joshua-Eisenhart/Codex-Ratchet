"""
a2_append_safe_context_shell_audit_operator.py

Bounded append-safe context-shell follow-on slice for the
context-spec-workflow-memory cluster.

This audit makes the current Ratchet continuity shell explicit. It does not
replace canonical memory, bootstrap a service, or create a new owner-surface
family.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_ID = "SKILL_CLUSTER::context-spec-workflow-memory"
SLICE_ID = "a2-append-safe-context-shell-audit-operator"

FOLLOW_ON_SELECTOR_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json"
)
PATTERN_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.json"
)

CONTEXT_ENGINEERING_PATH = "work/reference_repos/external_audit/Context-Engineering"
SPEC_KIT_PATH = "work/reference_repos/external_audit/spec-kit"
SUPERPOWERS_PATH = "work/reference_repos/external_audit/superpowers"
MEM0_PATH = "work/reference_repos/external_audit/mem0"

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_PACKET__CURRENT__v1.json"
)

SHELL_SURFACES = [
    {
        "surface_id": "intent_summary",
        "path": "system_v3/a2_state/INTENT_SUMMARY.md",
        "role": "standing summary shell",
        "admitted_write_shape": "summary_refresh_only",
    },
    {
        "surface_id": "a2_brain_slice",
        "path": "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
        "role": "standing compressed brain shell",
        "admitted_write_shape": "summary_refresh_only",
    },
    {
        "surface_id": "a2_key_context_append_log",
        "path": "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
        "role": "append-first continuity log",
        "admitted_write_shape": "append_log_delta",
    },
    {
        "surface_id": "open_unresolved",
        "path": "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
        "role": "live tensions and unresolved blocker shell",
        "admitted_write_shape": "unresolved_refresh_only",
    },
    {
        "surface_id": "controller_state",
        "path": "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
        "role": "controller-facing current state shell",
        "admitted_write_shape": "controller_state_refresh_only",
    },
]

IMPORTED_MEMBER_DISPOSITION = {
    "Context-Engineering": {
        "classification": "adapt",
        "keep": "layered context shells, protocol-shell discipline, and carry-forward framing without whole-thread replay",
        "adapt_away_from": [
            "full framework import",
            "field-theory or ontology claims as runtime law",
            "tooling-owned context replacement",
        ],
    },
    "spec-kit": {
        "classification": "adapt",
        "keep": "explicit contract language for what stays standing owner memory versus bounded task or note surfaces",
        "adapt_away_from": [
            "CLI scaffolding assumptions",
            "slash-command workflow ownership",
            "project generator claims",
        ],
    },
    "superpowers": {
        "classification": "mine",
        "keep": "review-before-completion and bounded workflow discipline so shell updates stay deliberate",
        "adapt_away_from": [
            "full workflow operating-system replacement",
            "plugin marketplace assumptions",
            "git-worktree ownership",
        ],
    },
    "mem0": {
        "classification": "mine",
        "keep": "scoped memory-sidecar, mutation-history, and session/run identity ideas only as later bounded sidecar pressure",
        "adapt_away_from": [
            "canonical brain replacement",
            "memory platform ownership",
            "vector-db or graph substrate ownership",
        ],
    },
}

ADMISSIBLE_WRITE_SHAPES = [
    {
        "shape_id": "append_log_delta",
        "target_surface": "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
        "allowed_when": "new recurring pressure, communication nuance, design correction, or carry-forward instruction should persist without rewriting summaries",
    },
    {
        "shape_id": "summary_refresh_only",
        "target_surfaces": [
            "system_v3/a2_state/INTENT_SUMMARY.md",
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
        ],
        "allowed_when": "standing compressed understanding actually changed and append-log-only carry is no longer enough",
    },
    {
        "shape_id": "unresolved_refresh_only",
        "target_surface": "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
        "allowed_when": "a live blocker, tension, ambiguity, or explicit hold state changed",
    },
    {
        "shape_id": "controller_state_refresh_only",
        "target_surface": "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
        "allowed_when": "current lane, selector result, hold state, or admitted current truth changed",
    },
    {
        "shape_id": "bounded_delta_note_pair",
        "target_surface_class": "A2_UPDATE_NOTE plus optional A2_TO_A1_IMPACT_NOTE",
        "allowed_when": "one bounded tranche lands and needs explicit repo-held delta capture without becoming the continuity shell itself",
    },
]

DEFAULT_NON_GOALS = [
    "No canonical A2/A1 brain replacement claim.",
    "No new owner-surface family creation claim.",
    "No background session-manager or workflow-host ownership claim.",
    "No external memory platform or service bootstrap claim.",
    "No graph-substrate replacement claim.",
    "No selector widening by momentum.",
]

DEFAULT_RECOMMENDED_ACTIONS = [
    "Keep the standing continuity shell small and explicit: append nuance into the append log first, then refresh summaries only when shell meaning actually changed.",
    "Treat A2 update-note pairs as bounded tranche evidence, not as the continuity shell itself.",
    "Hold this slice as audit-only; do not convert it into a live memory manager, background process, or canonical-brain replacement.",
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


def _repo_status(root: Path, rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    readme = path / "README.md"
    return {
        "path": rel_path,
        "exists": path.exists(),
        "readme_exists": readme.exists(),
    }


def _surface_status(root: Path, rel_path: str, role: str, admitted_write_shape: str) -> dict[str, Any]:
    path = root / rel_path
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "path": rel_path,
        "exists": path.exists(),
        "role": role,
        "admitted_write_shape": admitted_write_shape,
        "line_count": len(text.splitlines()) if text else 0,
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "modified_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime)) if path.exists() else "",
    }


def _selector_alignment(selector_report: dict[str, Any], issues: list[str]) -> dict[str, Any]:
    selected_pattern_id = str(selector_report.get("selected_pattern_id", "")).strip()
    recommended_next_slice_id = str(selector_report.get("recommended_next_slice_id", "")).strip()
    aligned = selected_pattern_id == "append_safe_context_shell" and recommended_next_slice_id == SLICE_ID
    if not aligned:
        issues.append("follow-on selector did not explicitly choose this append-safe context-shell slice")
    return {
        "selected_pattern_id": selected_pattern_id,
        "recommended_next_slice_id": recommended_next_slice_id,
        "aligned": aligned,
    }


def build_a2_append_safe_context_shell_audit_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    audit_scope = str(ctx.get("audit_scope", "bounded_append_safe_context_shell_audit")).strip()
    issues: list[str] = []
    if audit_scope != "bounded_append_safe_context_shell_audit":
        issues.append("audit_scope widened beyond bounded append-safe context shell audit")

    selector_report = _load_json(
        _resolve_output_path(root, ctx.get("follow_on_selector_report_path"), FOLLOW_ON_SELECTOR_REPORT_PATH)
    )
    pattern_report = _load_json(
        _resolve_output_path(root, ctx.get("pattern_report_path"), PATTERN_REPORT_PATH)
    )
    alignment = _selector_alignment(selector_report, issues)

    local_sources = {
        "Context-Engineering": _repo_status(root, CONTEXT_ENGINEERING_PATH),
        "spec-kit": _repo_status(root, SPEC_KIT_PATH),
        "superpowers": _repo_status(root, SUPERPOWERS_PATH),
        "mem0": _repo_status(root, MEM0_PATH),
    }
    for label, status in local_sources.items():
        if not status["exists"]:
            issues.append(f"missing local source repo: {label}")

    pattern_ids = {
        str(item.get("pattern_id", "")).strip()
        for item in pattern_report.get("admissible_pattern_families", [])
        if isinstance(item, dict)
    }
    if "append_safe_context_shell" not in pattern_ids:
        issues.append("append_safe_context_shell pattern family is not admitted by first slice")

    shell_surface_inventory = [
        _surface_status(root, item["path"], item["role"], item["admitted_write_shape"])
        for item in SHELL_SURFACES
    ]
    for item in shell_surface_inventory:
        if not item["exists"]:
            issues.append(f"missing continuity shell surface: {item['path']}")

    continuity_shell_contract = {
        "primary_shell_surface_paths": [item["path"] for item in shell_surface_inventory],
        "preferred_append_surface_path": "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
        "summary_refresh_surface_paths": [
            "system_v3/a2_state/INTENT_SUMMARY.md",
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
        ],
        "controller_refresh_surface_path": "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
        "unresolved_surface_path": "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
        "bounded_delta_surface_class": "A2_UPDATE_NOTE plus optional A2_TO_A1_IMPACT_NOTE",
        "blocked_expansions": [
            "canonical brain replacement",
            "new owner-surface family creation",
            "background session-manager ownership",
            "external memory platform ownership",
            "graph-substrate replacement",
        ],
    }

    report = {
        "schema": "A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "audit_scope": audit_scope,
        "selector_alignment": alignment,
        "source_family": "Context-Engineering / spec-kit / superpowers / mem0 source set",
        "local_sources": local_sources,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITION,
        "shell_surface_inventory": shell_surface_inventory,
        "continuity_shell_contract": continuity_shell_contract,
        "admissible_write_shapes": list(ADMISSIBLE_WRITE_SHAPES),
        "blocked_related_pattern_ids": [
            option.get("pattern_id", "")
            for option in selector_report.get("selection_options", [])
            if option.get("status") == "blocked"
        ],
        "recommended_next_step": "hold_append_safe_context_shell_as_audit_only" if not issues else "",
        "recommended_actions": list(DEFAULT_RECOMMENDED_ACTIONS),
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "selected_pattern_id": alignment["selected_pattern_id"],
        "allow_runtime_live_claims": False,
        "allow_training": False,
        "allow_service_bootstrap": False,
        "allow_canonical_brain_replacement": False,
        "allow_new_owner_surface_creation": False,
        "allow_background_session_manager": False,
        "allow_graph_substrate_replacement": False,
        "allow_memory_platform_import": False,
        "primary_shell_surface_paths": continuity_shell_contract["primary_shell_surface_paths"],
        "preferred_append_surface_path": continuity_shell_contract["preferred_append_surface_path"],
        "recommended_next_step": report["recommended_next_step"],
        "do_not_promote": True,
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Append Safe Context Shell Audit Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- audit_scope: `{report.get('audit_scope', '')}`",
        f"- selected_pattern_id: `{report.get('selector_alignment', {}).get('selected_pattern_id', '')}`",
        f"- recommended_next_step: `{packet.get('recommended_next_step', '')}`",
        "",
        "## Continuity Shell Surfaces",
    ]
    for item in report.get("shell_surface_inventory", []):
        lines.append(
            f"- `{item.get('path', '')}`: exists=`{item.get('exists', False)}` role=`{item.get('role', '')}` write_shape=`{item.get('admitted_write_shape', '')}`"
        )
    lines.extend(["", "## Admissible Write Shapes"])
    for item in report.get("admissible_write_shapes", []):
        lines.append(f"- `{item.get('shape_id', '')}`: `{item.get('allowed_when', '')}`")
    lines.extend(["", "## Imported Member Disposition"])
    for label, item in report.get("imported_member_disposition", {}).items():
        lines.append(f"- `{label}`: {item.get('classification', '')} -> {item.get('keep', '')}")
    lines.extend(["", "## Packet"])
    lines.append(f"- preferred_append_surface_path: `{packet.get('preferred_append_surface_path', '')}`")
    lines.append(f"- allow_new_owner_surface_creation: `{packet.get('allow_new_owner_surface_creation', False)}`")
    lines.append(f"- allow_canonical_brain_replacement: `{packet.get('allow_canonical_brain_replacement', False)}`")
    lines.extend(["", "## Issues"])
    issues = report.get("issues", [])
    lines.extend(f"- {item}" for item in issues) if issues else lines.append("- none")
    lines.extend(["", "## Non-Goals"])
    lines.extend(f"- {item}" for item in report.get("non_goals", []))
    lines.append("")
    return "\n".join(lines)


def run_a2_append_safe_context_shell_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_a2_append_safe_context_shell_audit_report(root, ctx)

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
        "recommended_next_step": packet["recommended_next_step"],
    }


if __name__ == "__main__":
    print(json.dumps(run_a2_append_safe_context_shell_audit({}), indent=2, sort_keys=True))
