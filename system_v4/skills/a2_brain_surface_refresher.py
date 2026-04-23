"""
a2_brain_surface_refresher.py

Audit-mode A2 truth-maintenance slice that inspects the standing controller-facing
brain surfaces against current repo truth and emits bounded repo-held reports
without mutating canonical A2 owner surfaces.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.runtime_context_snapshot import record_current_runtime_context
from system_v4.skills.skill_registry import SkillRegistry
A2_BRAIN_REFRESH_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
)
A2_BRAIN_REFRESH_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.md"
)
A2_BRAIN_REFRESH_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_PACKET__CURRENT__v1.json"
)

PRIMARY_A2_SURFACES = [
    "system_v3/a2_state/INTENT_SUMMARY.md",
    "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
    "system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
    "system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md",
    "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md",
    "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
    "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
    "system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
    "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
    "system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md",
]

OWNER_LAW_BASELINES = [
    "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
    "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
    "system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md",
    "system_v4/V4_SYSTEM_SPEC__CURRENT.md",
    "A2_V4_RECOVERY_AUDIT.md",
]

FRONT_DOOR_CORPUS_DOCS = [
    "SKILL_SOURCE_CORPUS.md",
    "REPO_SKILL_INTEGRATION_TRACKER.md",
    "SKILL_CANDIDATES_BACKLOG.md",
    "LOCAL_SOURCE_REPO_INVENTORY.md",
]

CURRENT_REPORT_PATTERNS = [
    "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json",
    "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json",
    "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json",
    "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json",
    "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__*.json",
    "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json",
]

CURRENT_JSON_PATTERNS = [
    "system_v3/a2_state/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__*.json",
    "system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__*.json",
    "system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__*.json",
]

STALE_PATTERN_RULES = [
    {
        "id": "owner_law_indexing_stale",
        "summary": "surface still claims owner-law docs are not indexed",
        "patterns": [
            "does not index these key owner specs",
            "owner-law docs are not indexed",
        ],
        "expected_truth": "doc_index now contains the 01/02/07/19 owner-law docs.",
        "severity": "high",
    },
    {
        "id": "front_door_indexing_stale",
        "summary": "surface still claims the front-door corpus docs are outside canonical A2",
        "patterns": [
            "front-door corpus docs are still outside canonical A2 indexing",
            "outside canonical A2 indexing",
            "not indexed into canonical A2",
        ],
        "expected_truth": (
            "doc_index now contains SKILL_SOURCE_CORPUS.md, "
            "REPO_SKILL_INTEGRATION_TRACKER.md, "
            "SKILL_CANDIDATES_BACKLOG.md, and LOCAL_SOURCE_REPO_INVENTORY.md."
        ),
        "severity": "high",
    },
    {
        "id": "registry_zero_stale",
        "summary": "surface still claims the live registry collapses to zero",
        "patterns": [
            "registry fail-closes to `0`",
            "registry fail-closes to 0",
            "loads `0` skills",
            "loads 0 skills",
            "collapsing to `0`",
            "collapsed to `0`",
        ],
        "expected_truth": "SkillRegistry('.') currently loads the live active skill set with 0 load issues.",
        "severity": "high",
    },
    {
        "id": "graph_coverage_stale",
        "summary": "surface still carries stale graph/registry skill counts",
        "patterns": [
            "88 registry skills vs 82 graphed",
            "82 active skills graphed",
            "82 graph skill nodes",
            "6 missing graph nodes",
        ],
        "expected_truth": "Current graph coverage shows equal active and graphed skill counts with 0 missing and 0 stale.",
        "severity": "medium",
    },
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _generated_utc_timestamp(path: Path) -> float | None:
    if path.suffix.lower() != ".json" or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    generated_utc = str(payload.get("generated_utc", "")).strip()
    if not generated_utc:
        return None
    try:
        parsed = time.strptime(generated_utc, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return float(calendar.timegm(parsed))


def _evidence_timestamp(path: Path) -> float:
    generated_timestamp = _generated_utc_timestamp(path)
    if generated_timestamp is not None:
        return generated_timestamp
    return path.stat().st_mtime


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = _load_json(path)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resolve_output_path(root: Path, raw: str | None, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(raw)
    return path if path.is_absolute() else root / path


def _glob_latest(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _collect_existing_paths(root: Path, patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        if "*" in pattern:
            paths.extend(sorted(root.glob(pattern)))
        else:
            path = root / pattern
            if path.exists():
                paths.append(path)
    return paths


def _doc_index_status(root: Path) -> dict[str, Any]:
    doc_index_path = root / "system_v3/a2_state/doc_index.json"
    doc_index = _safe_load_json(doc_index_path)
    documents = doc_index.get("documents", [])
    indexed_paths = {
        str(item.get("path", ""))
        for item in documents
        if isinstance(item, dict)
    }

    owner_indexed = {
        rel: rel in indexed_paths for rel in [
            "system_v3/specs/01_REQUIREMENTS_LEDGER.md",
            "system_v3/specs/02_OWNERSHIP_MAP.md",
            "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
            "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
        ]
    }
    front_door_indexed = {rel: rel in indexed_paths for rel in FRONT_DOOR_CORPUS_DOCS}
    return {
        "path": str(doc_index_path),
        "exists": doc_index_path.exists(),
        "owner_law_indexed": owner_indexed,
        "front_door_indexed": front_door_indexed,
    }


def _graph_skill_coverage(root: Path) -> dict[str, Any]:
    audit_path = _glob_latest(root, "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__*.json")
    if audit_path is None:
        return {"exists": False, "path": "", "coverage": {}}
    payload = _safe_load_json(audit_path)
    coverage = payload.get("skill_graph_coverage", {})
    return {
        "exists": True,
        "path": str(audit_path),
        "coverage": coverage if isinstance(coverage, dict) else {},
    }


def _surface_excerpt(text: str, start: int, length: int = 180) -> str:
    excerpt = text[max(0, start - 40): start + length]
    return " ".join(excerpt.split())


def _stale_claim_hits(text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    hits: list[dict[str, Any]] = []
    for rule in STALE_PATTERN_RULES:
        for pattern in rule["patterns"]:
            idx = lowered.find(pattern.lower())
            if idx == -1:
                continue
            hits.append(
                {
                    "id": rule["id"],
                    "severity": rule["severity"],
                    "summary": rule["summary"],
                    "matched_pattern": pattern,
                    "excerpt": _surface_excerpt(text, idx),
                    "expected_truth": rule["expected_truth"],
                }
            )
            break
    return hits


def _extract_heading_dates(text: str) -> list[str]:
    return re.findall(r"(?:Date|Updated):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)


def _surface_status(root: Path, rel_path: str, latest_evidence_mtime: float) -> dict[str, Any]:
    path = root / rel_path
    status: dict[str, Any] = {
        "path": rel_path,
        "exists": path.exists(),
        "stale_claim_hits": [],
        "older_than_latest_evidence": False,
        "heading_dates": [],
        "sha256": "",
        "size_bytes": 0,
        "modified_utc": "",
    }
    if not path.exists():
        status["issues"] = ["missing_surface"]
        return status

    text = _load_text(path)
    modified = path.stat().st_mtime
    status["size_bytes"] = path.stat().st_size
    status["modified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(modified))
    status["sha256"] = _sha256(path)
    status["heading_dates"] = _extract_heading_dates(text)
    status["stale_claim_hits"] = _stale_claim_hits(text)
    if latest_evidence_mtime > 0 and modified + 1 < latest_evidence_mtime:
        status["older_than_latest_evidence"] = True

    issues: list[str] = []
    if status["stale_claim_hits"]:
        issues.append("explicit_stale_claims_present")
    if status["older_than_latest_evidence"]:
        issues.append("older_than_latest_evidence")
    status["issues"] = issues
    return status


def _render_markdown(report: dict[str, Any]) -> str:
    surface_lines = []
    for surface in report.get("active_owner_surface_status", []):
        issue_labels = ", ".join(surface.get("issues", [])) or "none"
        surface_lines.append(
            f"- `{surface.get('path', '')}`: exists={surface.get('exists', False)}; "
            f"issues={issue_labels}"
        )
    action_lines = [f"- {item}" for item in report.get("recommended_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    stale_lines = []
    for finding in report.get("priority_surface_findings", []):
        stale_lines.append(
            f"- `{finding.get('path', '')}`: {finding.get('summary', '')} "
            f"({finding.get('severity', '')})"
        )
    priority_block = stale_lines if stale_lines else ["- none"]
    return "\n".join(
        [
            "# A2 Brain Surface Refresh Audit Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- refresh_required: `{report.get('refresh_required', False)}`",
            f"- safe_to_continue: `{report.get('safe_to_continue', False)}`",
            f"- audit_only: `{report.get('audit_only', False)}`",
            f"- task_signal: `{report.get('task_signal', '')}`",
            "",
            "## Surface Findings",
            *surface_lines,
            "",
            "## Priority Findings",
            *priority_block,
            "",
            "## Recommended Actions",
            *action_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def _recommended_actions(
    missing_surfaces: list[str],
    priority_findings: list[dict[str, Any]],
    stale_surface_count: int,
    older_surface_count: int,
) -> list[str]:
    actions: list[str] = []
    if missing_surfaces:
        actions.append(
            "Restore or recreate missing standing A2 surfaces before treating the controller-facing brain as coherent."
        )
    if priority_findings:
        actions.append(
            "Patch the flagged standing A2 surfaces directly with current repo truth instead of adding another same-scope note chain."
        )
    if older_surface_count:
        actions.append(
            "Refresh the standing A2 surfaces from current v4 reports and controller evidence so they stop lagging recent repairs."
        )
    if stale_surface_count or older_surface_count:
        actions.append(
            "Keep this operator audit-only until the standing A2 surfaces and current reports agree on registry, graph, and corpus truth."
        )
    actions.append(
        "Do not promote this report into canonical A2 automatically; use it as a bounded maintenance audit packet."
    )
    return actions


def build_a2_brain_surface_refresh_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    ctx = ctx or {}

    input_summary = {
        "changed_paths": list(ctx.get("changed_paths", [])),
        "changed_tools": list(ctx.get("changed_tools", [])),
        "new_run_evidence": list(ctx.get("new_run_evidence", [])),
        "pending_a1_work": ctx.get("pending_a1_work"),
    }

    doc_index_status = _doc_index_status(root)
    skill_health = SkillRegistry(str(root)).health_pass()
    graph_coverage_status = _graph_skill_coverage(root)

    self_output_paths = {
        _resolve_output_path(
            root,
            ctx.get("report_path") if name == "report_path" else (
                ctx.get("markdown_path") if name == "markdown_path" else ctx.get("packet_path")
            ),
            default_rel,
        ).resolve()
        for name, default_rel in (
            ("report_path", A2_BRAIN_REFRESH_REPORT_JSON),
            ("markdown_path", A2_BRAIN_REFRESH_REPORT_MD),
            ("packet_path", A2_BRAIN_REFRESH_PACKET_JSON),
        )
    }

    current_report_paths = [
        path
        for path in _collect_existing_paths(root, CURRENT_REPORT_PATTERNS)
        if path.resolve() not in self_output_paths
    ]
    controller_paths = _collect_existing_paths(root, CURRENT_JSON_PATTERNS)
    evidence_paths = current_report_paths + controller_paths + [root / rel for rel in FRONT_DOOR_CORPUS_DOCS if (root / rel).exists()]
    latest_evidence_path = max(evidence_paths, key=_evidence_timestamp) if evidence_paths else None
    latest_evidence_mtime = _evidence_timestamp(latest_evidence_path) if latest_evidence_path else 0.0

    surface_status = [_surface_status(root, rel_path, latest_evidence_mtime) for rel_path in PRIMARY_A2_SURFACES]
    missing_surfaces = [item["path"] for item in surface_status if not item["exists"]]
    stale_surfaces = [item for item in surface_status if item["stale_claim_hits"]]
    older_surfaces = [item for item in surface_status if item["older_than_latest_evidence"]]
    priority_findings = [
        {
            "path": item["path"],
            **finding,
        }
        for item in stale_surfaces
        for finding in item["stale_claim_hits"]
    ]

    front_door_ok = all(doc_index_status["front_door_indexed"].values()) if doc_index_status["exists"] else False
    owner_law_ok = all(doc_index_status["owner_law_indexed"].values()) if doc_index_status["exists"] else False
    graph_coverage = graph_coverage_status.get("coverage", {})
    graph_missing_count = int(graph_coverage.get("missing_active_skill_count", 0) or 0)
    graph_stale_count = int(graph_coverage.get("stale_skill_node_count", 0) or 0)

    refresh_required = bool(missing_surfaces or stale_surfaces or older_surfaces)
    safe_to_continue = not missing_surfaces and not stale_surfaces
    issues: list[str] = []
    if not owner_law_ok:
        issues.append("owner-law docs are not fully indexed in canonical A2 doc_index")
    if not front_door_ok:
        issues.append("front-door corpus docs are not fully indexed in canonical A2 doc_index")
    if stale_surfaces:
        issues.append(f"{len(stale_surfaces)} standing A2 surfaces contain explicit stale claims")
    if older_surfaces:
        issues.append(f"{len(older_surfaces)} standing A2 surfaces are older than the latest current evidence")
    if missing_surfaces:
        issues.append(f"{len(missing_surfaces)} primary standing A2 surfaces are missing")
    if graph_missing_count or graph_stale_count:
        issues.append("graph capability audit reports missing or stale skill-node coverage")

    runtime_context_snapshot = ctx.get("runtime_context_snapshot")
    report = {
        "schema": "A2_BRAIN_SURFACE_REFRESH_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": (
            "ok"
            if not issues
            else "action_required" if (missing_surfaces or stale_surfaces) else "attention_required"
        ),
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "refresh_required": refresh_required,
        "safe_to_continue": safe_to_continue,
        "task_signal": str(ctx.get("task_signal", "a2_brain_surface_refresh_audit")),
        "input_summary": input_summary,
        "runtime_context_snapshot": runtime_context_snapshot or {},
        "active_owner_surface_status": surface_status,
        "surface_classification_summary": {
            "primary_surface_count": len(PRIMARY_A2_SURFACES),
            "missing_surface_count": len(missing_surfaces),
            "stale_surface_count": len(stale_surfaces),
            "older_than_latest_evidence_count": len(older_surfaces),
            "owner_law_indexed": owner_law_ok,
            "front_door_corpus_indexed": front_door_ok,
        },
        "current_truth_summary": {
            "doc_index_path": doc_index_status["path"],
            "owner_law_indexed": doc_index_status["owner_law_indexed"],
            "front_door_indexed": doc_index_status["front_door_indexed"],
            "registry_health": skill_health,
            "graph_skill_coverage": graph_coverage,
            "latest_evidence_path": str(latest_evidence_path) if latest_evidence_path else "",
            "latest_evidence_utc": (
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(latest_evidence_mtime))
                if latest_evidence_mtime
                else ""
            ),
            "current_report_paths": [_relative(root, path) for path in current_report_paths],
            "current_controller_paths": [_relative(root, path) for path in controller_paths],
        },
        "priority_surface_findings": priority_findings,
        "drift_flags": [
            f"MISSING_SURFACES::{len(missing_surfaces)}",
            f"EXPLICIT_STALE_SURFACES::{len(stale_surfaces)}",
            f"OLDER_THAN_LATEST_EVIDENCE::{len(older_surfaces)}",
        ],
        "off_process_flags": [
            "standing_a2_contains_stale_truth" if stale_surfaces else "",
            "standing_a2_missing_primary_surfaces" if missing_surfaces else "",
        ],
        "a1_impact": {
            "pause_new_a1_expansion": bool(missing_surfaces or stale_surfaces),
            "allow_bounded_maintenance": True,
            "reason": (
                "standing A2 brain contains missing or stale controller-facing truth"
                if (missing_surfaces or stale_surfaces)
                else (
                    "standing A2 brain is usable but still lags latest evidence"
                    if older_surfaces
                    else "standing A2 brain is current against latest evidence"
                )
            ),
        },
        "recommended_actions": _recommended_actions(
            missing_surfaces=missing_surfaces,
            priority_findings=priority_findings,
            stale_surface_count=len(stale_surfaces),
            older_surface_count=len(older_surfaces),
        ),
        "staged_output_targets": {
            "json_report": ctx.get("report_path") or A2_BRAIN_REFRESH_REPORT_JSON,
            "markdown_report": ctx.get("markdown_path") or A2_BRAIN_REFRESH_REPORT_MD,
            "packet_json": ctx.get("packet_path") or A2_BRAIN_REFRESH_PACKET_JSON,
        },
        "issues": issues,
    }
    report["off_process_flags"] = [flag for flag in report["off_process_flags"] if flag]
    return report


def run_a2_brain_surface_refresher(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo", REPO_ROOT)).resolve()
    runtime_context_snapshot: dict[str, Any] = {}
    if ctx.get("record_runtime_context"):
        try:
            runtime_context_snapshot = record_current_runtime_context(str(root))
        except Exception as exc:  # pragma: no cover - defensive path
            runtime_context_snapshot = {
                "recorded": False,
                "status": "error",
                "error": str(exc),
            }

    report = build_a2_brain_surface_refresh_report(
        root,
        {
            **ctx,
            "runtime_context_snapshot": runtime_context_snapshot,
        },
    )
    report_path = _resolve_output_path(root, ctx.get("report_path"), A2_BRAIN_REFRESH_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("markdown_path"), A2_BRAIN_REFRESH_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), A2_BRAIN_REFRESH_PACKET_JSON)
    for output in (report_path, markdown_path, packet_path):
        output.parent.mkdir(parents=True, exist_ok=True)

    packet = {
        "schema": "A2_BRAIN_SURFACE_REFRESH_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "status": report["status"],
        "refresh_required": report["refresh_required"],
        "safe_to_continue": report["safe_to_continue"],
        "missing_surfaces": [
            item["path"] for item in report["active_owner_surface_status"] if not item["exists"]
        ],
        "priority_surface_findings": report["priority_surface_findings"],
        "recommended_actions": report["recommended_actions"],
        "a1_impact": report["a1_impact"],
    }

    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
    report["markdown_path"] = str(markdown_path)
    report["packet_path"] = str(packet_path)
    return report


if __name__ == "__main__":
    result = build_a2_brain_surface_refresh_report(REPO_ROOT)
    assert result["surface_classification_summary"]["primary_surface_count"] == len(PRIMARY_A2_SURFACES)
    assert result["audit_only"] is True
    print("PASS: a2_brain_surface_refresher self-test")
