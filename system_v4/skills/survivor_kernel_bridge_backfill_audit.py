"""
survivor_kernel_bridge_backfill_audit.py

Audit whether any direct B_SURVIVOR -> KERNEL_CONCEPT backfills are honestly
available under the current graph truth.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from system_v4.skills.graph_store import load_graph_json


REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
BRIDGE_SOURCE_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/SURVIVOR_KERNEL_BRIDGE_BACKFILL_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/SURVIVOR_KERNEL_BRIDGE_BACKFILL_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/SURVIVOR_KERNEL_BRIDGE_BACKFILL_PACKET__CURRENT__v1.json"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        path.relative_to(REPO_ROOT / "system_v4" / "a2_state" / "graphs")
        return load_graph_json(REPO_ROOT, str(path.relative_to(REPO_ROOT)), default={})
    except ValueError:
        pass
    except FileNotFoundError:
        return {}
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _classify_survivors(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    existing_pairs = {
        (edge.get("source_id"), edge.get("target_id"), edge.get("relation"))
        for edge in edges
        if isinstance(edge, dict) and edge.get("relation") == "ACCEPTED_FROM"
    }
    class_counts: Counter[str] = Counter()
    examples: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    direct_kernel_backfill_candidates: list[dict[str, Any]] = []

    for survivor_id, node in nodes.items():
        if node.get("node_type") != "B_SURVIVOR":
            continue
        props = node.get("properties", {}) or {}
        target_id = str(props.get("source_concept_id", "") or "")
        if not target_id:
            bucket = "blank_source_concept_id"
        elif target_id not in nodes:
            bucket = "missing_target"
        else:
            target_type = str(nodes[target_id].get("node_type"))
            edge_exists = (survivor_id, target_id, "ACCEPTED_FROM") in existing_pairs
            if target_type == "KERNEL_CONCEPT":
                if edge_exists:
                    bucket = "live_kernel_already_linked"
                else:
                    bucket = "live_kernel_backfillable_now"
                    direct_kernel_backfill_candidates.append(
                        {
                            "survivor_id": survivor_id,
                            "target_id": target_id,
                            "target_name": nodes[target_id].get("name"),
                        }
                    )
            else:
                if edge_exists:
                    bucket = f"live_nonkernel_already_linked::{target_type}"
                else:
                    bucket = f"live_nonkernel_unlinked::{target_type}"
        class_counts[bucket] += 1
        if len(examples[bucket]) < 3:
            examples[bucket].append(
                {
                    "survivor_id": survivor_id,
                    "target_id": target_id,
                    "target_node_type": nodes.get(target_id, {}).get("node_type") if target_id in nodes else "",
                }
            )

    return {
        "class_counts": dict(class_counts),
        "examples": dict(examples),
        "direct_kernel_backfill_candidates": direct_kernel_backfill_candidates,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    class_lines = [
        f"- `{bucket}`: `{count}`"
        for bucket, count in sorted(report.get("survivor_source_class_counts", {}).items())
    ]
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Survivor Kernel Bridge Backfill Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- authoritative_graph: `{report['authoritative_graph']}`",
            f"- allow_direct_kernel_backfill_now: `{report['allow_direct_kernel_backfill_now']}`",
            "",
            "## Survivor Source Classes",
            *class_lines,
            "",
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_survivor_kernel_bridge_backfill_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    graph_path = root / AUTHORITATIVE_GRAPH
    bridge_source = _load_json(root / BRIDGE_SOURCE_JSON)

    issues: list[str] = []
    if not graph_path.exists():
        issues.append("missing authoritative live graph store")
    if not bridge_source:
        issues.append("missing or unreadable bridge-source audit")

    graph = _load_json(graph_path) if graph_path.exists() else {}
    nodes = graph.get("nodes", {}) if isinstance(graph, dict) else {}
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    if not isinstance(nodes, dict):
        nodes = {}
    if not isinstance(edges, list):
        edges = []

    survivor_summary = _classify_survivors(nodes, edges) if graph_path.exists() else {
        "class_counts": {},
        "examples": {},
        "direct_kernel_backfill_candidates": [],
    }
    direct_candidates = survivor_summary["direct_kernel_backfill_candidates"]

    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "SURVIVOR_KERNEL_BRIDGE_BACKFILL_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "authoritative_graph": AUTHORITATIVE_GRAPH,
        "supporting_bridge_source_audit": BRIDGE_SOURCE_JSON,
        "allow_direct_kernel_backfill_now": bool(direct_candidates),
        "direct_kernel_backfill_candidate_count": len(direct_candidates),
        "direct_kernel_backfill_candidates": direct_candidates,
        "survivor_source_class_counts": survivor_summary["class_counts"],
        "examples": survivor_summary["examples"],
        "recommended_next_actions": [
            "Do not run bulk direct survivor-to-kernel backfill under current truth unless a survivor resolves to a live KERNEL_CONCEPT without an existing ACCEPTED_FROM edge.",
            "Treat survivor links that already resolve to REFINED_CONCEPT or EXTRACTED_CONCEPT as evidence of concept-class layering, not as missing direct kernel edges.",
            "Return to skill-kernel-link-seeding-policy-audit after this slice so the skill island remains fail-closed while witness-side class layering is clarified.",
            "If survivor-side bridge strengthening continues later, add an explicit concept-class normalization or promotion policy before any broader kernel backfill claim.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "SURVIVOR_KERNEL_BRIDGE_BACKFILL_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "allow_direct_kernel_backfill_now": report["allow_direct_kernel_backfill_now"],
        "recommended_next_slice_ids": [
            "skill-kernel-link-seeding-policy-audit",
            "clifford-edge-semantics-audit",
        ],
        "direct_kernel_backfill_candidate_count": report["direct_kernel_backfill_candidate_count"],
        "authoritative_graph": AUTHORITATIVE_GRAPH,
    }
    return report, packet


def run_survivor_kernel_bridge_backfill_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_survivor_kernel_bridge_backfill_report(root, ctx)
    report_path = Path(ctx.get("report_json_path") or (root / REPORT_JSON))
    markdown_path = Path(ctx.get("report_md_path") or (root / REPORT_MD))
    packet_path = Path(ctx.get("packet_path") or (root / PACKET_JSON))
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report))
    _write_json(packet_path, packet)
    return {
        "status": report["status"],
        "report_json_path": str(report_path),
        "report_md_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    result = run_survivor_kernel_bridge_backfill_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
