"""
a2_context_spec_workflow_pattern_audit_operator.py

Bounded first slice for the context-spec-workflow-memory source family.

This audit mines only the smallest honest pattern families from the local
Context-Engineering, spec-kit, superpowers, and mem0 repos. It does not import
their runtimes, hosted services, plugin systems, or memory substrates.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_ID = "SKILL_CLUSTER::context-spec-workflow-memory"
SLICE_ID = "a2-context-spec-workflow-pattern-audit-operator"

CONTEXT_ENGINEERING_PATH = "work/reference_repos/external_audit/Context-Engineering"
SPEC_KIT_PATH = "work/reference_repos/external_audit/spec-kit"
SUPERPOWERS_PATH = "work/reference_repos/external_audit/superpowers"
MEM0_PATH = "work/reference_repos/external_audit/mem0"

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_PACKET__CURRENT__v1.json"
)

IMPORTED_MEMBER_DISPOSITION = {
    "Context-Engineering": {
        "classification": "adapt",
        "keep": "append-safe context shells, layered state framing, protocol-shell discipline, and hierarchical context structure",
        "adapt_away_from": [
            "field-theory doctrine as runtime truth",
            "quantum or attractor rhetoric as canonical substrate law",
            "full framework import",
        ],
    },
    "spec-kit": {
        "classification": "adapt",
        "keep": "explicit constitution/spec/plan/tasks separation and executable-spec coupling discipline",
        "adapt_away_from": [
            "CLI-driven project scaffolding assumptions",
            "slash-command workflow import",
            "project-generation or install-tooling claims",
        ],
    },
    "superpowers": {
        "classification": "mine",
        "keep": "plan-before-implementation discipline, bounded subagent review, and verification-before-completion patterns",
        "adapt_away_from": [
            "plugin marketplace assumptions",
            "git-worktree workflow ownership",
            "full superpowers operating-system replacement claims",
        ],
    },
    "mem0": {
        "classification": "mine",
        "keep": "user/session/agent/run scoping, mutation history, and export/import memory-sidecar patterns",
        "adapt_away_from": [
            "hosted memory platform assumptions",
            "canonical brain replacement",
            "graph or vector-db substrate ownership claims",
        ],
    },
}

EXTRACTED_PATTERNS = [
    {
        "pattern_id": "append_safe_context_shell",
        "source_member": "Context-Engineering",
        "ratchet_translation": "keep layered context/state shells small, append-safe, and explicit instead of re-explaining whole threads",
    },
    {
        "pattern_id": "executable_spec_coupling",
        "source_member": "spec-kit",
        "ratchet_translation": "keep specs, plans, and implementation artifacts coupled enough that spec surfaces remain live and read",
    },
    {
        "pattern_id": "workflow_review_discipline",
        "source_member": "superpowers",
        "ratchet_translation": "treat planning, bounded delegation, and verification as workflow discipline, not as a replacement controller substrate",
    },
    {
        "pattern_id": "scoped_memory_sidecar",
        "source_member": "mem0",
        "ratchet_translation": "treat memory as scoped sidecar/history support rather than as canonical A2/A1 memory or graph ownership",
    },
]

RATCHET_SEAM_MAPPINGS = [
    {
        "pattern_id": "append_safe_context_shell",
        "ratchet_surfaces": [
            "system_v3/a2_state/INTENT_SUMMARY.md",
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
            "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
        ],
        "current_role": "standing A2 continuity and low-bloat context retention",
    },
    {
        "pattern_id": "executable_spec_coupling",
        "ratchet_surfaces": [
            "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
            "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
            "system_v4/V4_SYSTEM_SPEC__CURRENT.md",
            "SYSTEM_SKILL_BUILD_PLAN.md",
        ],
        "current_role": "keep spec surfaces coupled to active implementation and build order",
    },
    {
        "pattern_id": "workflow_review_discipline",
        "ratchet_surfaces": [
            "system_v4/a2_state/audit_logs/A2_SOURCE_FAMILY_LANE_SELECTION_REPORT__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json",
        ],
        "current_role": "bounded planning, review, and selector discipline without adopting an external workflow host",
    },
    {
        "pattern_id": "scoped_memory_sidecar",
        "ratchet_surfaces": [
            "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json",
            "system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md",
        ],
        "current_role": "scoped outside-memory support without canonical brain replacement",
    },
]

DEFAULT_RECOMMENDED_ACTIONS = [
    "Keep this first slice audit-only and treat it as a cluster-entry map, not as a runtime or service import.",
    "If this cluster continues, choose one bounded follow-on only after explicit reselection instead of widening context, specs, workflow, and memory all at once.",
    "Use the extracted pattern families to tighten existing Ratchet seams before proposing any new substrate or automation claims.",
]

DEFAULT_NON_GOALS = [
    "No runtime import, service bootstrap, or training claim.",
    "No canonical A2/A1 brain replacement claim.",
    "No live automation or controller-substrate replacement claim.",
    "No graph-substrate replacement claim.",
    "No registry, graph, or external-service mutation.",
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


def build_a2_context_spec_workflow_pattern_audit_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    analysis_scope = str(ctx.get("analysis_scope", "bounded_pattern_audit")).strip()
    scope_valid = analysis_scope == "bounded_pattern_audit"
    issues: list[str] = []
    if not scope_valid:
        issues.append("analysis_scope widened beyond bounded pattern audit")

    local_sources = {
        "Context-Engineering": _repo_status(root, CONTEXT_ENGINEERING_PATH),
        "spec-kit": _repo_status(root, SPEC_KIT_PATH),
        "superpowers": _repo_status(root, SUPERPOWERS_PATH),
        "mem0": _repo_status(root, MEM0_PATH),
    }
    for label, status in local_sources.items():
        if not status["exists"]:
            issues.append(f"missing local source repo: {label}")

    admitted_patterns = EXTRACTED_PATTERNS if not issues else []
    report = {
        "schema": "A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "analysis_scope": analysis_scope,
        "source_family": "Context-Engineering / spec-kit / superpowers / mem0 source set",
        "local_sources": local_sources,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITION,
        "admissible_pattern_families": admitted_patterns,
        "ratchet_seam_mappings": RATCHET_SEAM_MAPPINGS,
        "recommended_next_step": "hold_first_slice_as_audit_only" if not issues else "",
        "recommended_actions": list(DEFAULT_RECOMMENDED_ACTIONS),
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "analysis_scope": analysis_scope,
        "allow_runtime_live_claims": False,
        "allow_training": False,
        "allow_service_bootstrap": False,
        "allow_canonical_brain_replacement": False,
        "allow_graph_substrate_replacement": False,
        "allow_registry_mutation": False,
        "admissible_pattern_family_ids": [item["pattern_id"] for item in admitted_patterns],
        "recommended_next_step": report["recommended_next_step"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Context Spec Workflow Pattern Audit Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- analysis_scope: `{report.get('analysis_scope', '')}`",
        f"- admissible_pattern_family_count: `{len(report.get('admissible_pattern_families', []))}`",
        f"- recommended_next_step: `{packet.get('recommended_next_step', '')}`",
        "",
        "## Local Sources",
    ]
    for label, status in report.get("local_sources", {}).items():
        lines.append(f"- `{label}`: exists=`{status.get('exists', False)}` readme_exists=`{status.get('readme_exists', False)}`")
    lines.extend(["", "## Pattern Families"])
    for item in report.get("admissible_pattern_families", []):
        lines.append(f"- `{item.get('pattern_id', '')}`")
        lines.append(f"  - source_member: `{item.get('source_member', '')}`")
        lines.append(f"  - ratchet_translation: `{item.get('ratchet_translation', '')}`")
    lines.extend(["", "## Imported Member Disposition"])
    for label, item in report.get("imported_member_disposition", {}).items():
        lines.append(f"- `{label}`: {item.get('classification', '')} -> {item.get('keep', '')}")
    lines.extend(["", "## Ratchet Seam Mappings"])
    for item in report.get("ratchet_seam_mappings", []):
        lines.append(f"- `{item.get('pattern_id', '')}` -> `{item.get('current_role', '')}`")
    lines.extend(["", "## Issues"])
    issues = report.get("issues", [])
    lines.extend(f"- {item}" for item in issues) if issues else lines.append("- none")
    lines.extend(["", "## Non-Goals"])
    lines.extend(f"- {item}" for item in report.get("non_goals", []))
    lines.append("")
    return "\n".join(lines)


def run_a2_context_spec_workflow_pattern_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_a2_context_spec_workflow_pattern_audit_report(root, ctx)

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
    result = run_a2_context_spec_workflow_pattern_audit({"repo_root": REPO_ROOT})
    print(
        "PASS: a2_context_spec_workflow_pattern_audit_operator"
        f" status={result['status']}"
        f" next={result['recommended_next_step']}"
    )
