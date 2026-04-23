"""
toponetx_projection_adapter_audit.py

Build the first bounded read-only TopoNetX projection over the low-control
owner graph.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

LOW_CONTROL_GRAPH = "system_v4/a2_state/graphs/a2_low_control_graph_v1.json"
AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
BRIDGE_SOURCE_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_PACKET__CURRENT__v1.json"

PREFERRED_INTERPRETER = sys.executable
ADMITTED_RELATIONS = ("DEPENDS_ON", "EXCLUDES", "STRUCTURALLY_RELATED", "RELATED_TO")
QUARANTINED_RELATIONS = ("OVERLAPS",)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
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


def _prepare_toponetx_env(root: Path) -> None:
    cache_root = root / "work" / "audit_tmp" / "mplcache"
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_root))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root))


def _try_import_toponetx(root: Path) -> tuple[Any | None, str]:
    _prepare_toponetx_env(root)
    try:
        import toponetx as tnx  # type: ignore

        return tnx, ""
    except Exception as exc:  # pragma: no cover - exercised when package missing
        return None, f"{type(exc).__name__}: {exc}"


def _triangle_candidates(edges: list[dict[str, Any]]) -> tuple[int, list[list[str]]]:
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source_id = str(edge.get("source_id"))
        target_id = str(edge.get("target_id"))
        if source_id == target_id:
            continue
        adjacency[source_id].add(target_id)
        adjacency[target_id].add(source_id)

    triangles: set[tuple[str, str, str]] = set()
    for a in adjacency:
        for b in adjacency[a]:
            if b <= a:
                continue
            for c in adjacency[a] & adjacency[b]:
                if c <= b:
                    continue
                triangles.add(tuple(sorted((a, b, c))))

    samples = [list(triangle) for triangle in sorted(triangles)[:5]]
    return len(triangles), samples


def _component_summary(node_ids: list[str], edges: list[dict[str, Any]]) -> dict[str, Any]:
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source_id = str(edge.get("source_id"))
        target_id = str(edge.get("target_id"))
        if source_id == target_id:
            continue
        adjacency[source_id].add(target_id)
        adjacency[target_id].add(source_id)

    seen: set[str] = set()
    component_sizes: list[int] = []
    for node_id in node_ids:
        if node_id in seen:
            continue
        stack = [node_id]
        seen.add(node_id)
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            for neighbor in adjacency.get(current, ()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        component_sizes.append(size)
    component_sizes.sort(reverse=True)
    return {
        "component_count": len(component_sizes),
        "isolated_node_count": sum(1 for size in component_sizes if size == 1),
        "largest_component_sizes": component_sizes[:10],
    }


def _build_projection(root: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    tnx, import_error = _try_import_toponetx(root)
    if tnx is None:
        return {}, [f"TopoNetX unavailable: {import_error}"]

    low_control = _load_json(root / LOW_CONTROL_GRAPH)
    nodes = low_control.get("nodes", {}) if isinstance(low_control, dict) else {}
    edges = low_control.get("edges", []) if isinstance(low_control, dict) else []
    if not isinstance(nodes, dict) or not isinstance(edges, list):
        return {}, ["low-control graph store is unreadable"]

    node_ids = sorted(nodes.keys())
    admitted_edges = [
        edge for edge in edges if isinstance(edge, dict) and edge.get("relation") in ADMITTED_RELATIONS
    ]
    quarantined_edges = [
        edge for edge in edges if isinstance(edge, dict) and edge.get("relation") in QUARANTINED_RELATIONS
    ]
    relation_counts = Counter(edge.get("relation", "?") for edge in admitted_edges)
    quarantined_relation_counts = Counter(edge.get("relation", "?") for edge in quarantined_edges)

    complex_ = tnx.CellComplex()
    for node_id in node_ids:
        complex_.add_node(node_id)
    for edge in admitted_edges:
        complex_.add_cell([edge["source_id"], edge["target_id"]], rank=1)

    triangle_count, triangle_samples = _triangle_candidates(admitted_edges)
    component_summary = _component_summary(node_ids, admitted_edges)

    projection = {
        "projection_shape": {
            "node_cell_count": int(complex_.shape[0]),
            "edge_cell_count": int(complex_.shape[1]),
            "two_cell_count": int(complex_.shape[2]),
        },
        "node_count": len(node_ids),
        "admitted_relation_entry_count": len(admitted_edges),
        "admitted_relation_counts": dict(relation_counts),
        "quarantined_relation_counts": dict(quarantined_relation_counts),
        "admitted_relation_policy": list(ADMITTED_RELATIONS),
        "quarantined_relation_policy": list(QUARANTINED_RELATIONS),
        "candidate_triangle_count": triangle_count,
        "candidate_triangle_samples": triangle_samples,
        "component_summary": component_summary,
    }
    return projection, issues


def _render_markdown(report: dict[str, Any]) -> str:
    projection = report.get("projection", {})
    shape = projection.get("projection_shape", {})
    components = projection.get("component_summary", {})
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# TopoNetX Projection Adapter Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- low_control_probe: `{report['low_control_probe']}`",
            f"- authoritative_graph: `{report['authoritative_graph']}`",
            "",
            "## Projection Shape",
            f"- nodes: `{shape.get('node_cell_count', 0)}`",
            f"- admitted_relation_entries: `{projection.get('admitted_relation_entry_count', 0)}`",
            f"- admitted_edges: `{shape.get('edge_cell_count', 0)}`",
            f"- canonical_two_cells: `{shape.get('two_cell_count', 0)}`",
            f"- candidate_triangles: `{projection.get('candidate_triangle_count', 0)}`",
            f"- component_count: `{components.get('component_count', 0)}`",
            f"- isolated_nodes: `{components.get('isolated_node_count', 0)}`",
            "",
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_toponetx_projection_adapter_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    low_control_path = root / LOW_CONTROL_GRAPH
    bridge_source = _load_json(root / BRIDGE_SOURCE_JSON)

    issues: list[str] = []
    if not low_control_path.exists():
        issues.append("missing low-control owner graph")
    if not bridge_source:
        issues.append("missing or unreadable bridge-source audit")

    projection, projection_issues = _build_projection(root) if low_control_path.exists() else ({}, [])
    issues.extend(projection_issues)

    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "TOPONETX_PROJECTION_ADAPTER_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "preferred_interpreter": PREFERRED_INTERPRETER,
        "low_control_probe": LOW_CONTROL_GRAPH,
        "authoritative_graph": AUTHORITATIVE_GRAPH,
        "supporting_bridge_source_audit": BRIDGE_SOURCE_JSON,
        "projection": projection,
        "recommended_next_actions": [
            "Keep the TopoNetX sidecar kernel-only and read-only; do not widen it into broader control-substrate truth while skill bridges remain heuristic-only.",
            "Keep OVERLAPS quarantined or downranked out of equal-weight topology until a later policy pass proves it belongs in higher-order control structure.",
            "Treat triangle and higher-order motif counts as audit observations only, not as canonical 2-cells.",
            "Use this sidecar to test whether the low-control owner graph has honest non-flat local structure before claiming broader nested-graph progress.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "TOPONETX_PROJECTION_ADAPTER_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "allow_read_only_projection": True,
        "preferred_interpreter": PREFERRED_INTERPRETER,
        "recommended_next_slice_ids": [
            "survivor-kernel-bridge-backfill-audit",
            "skill-kernel-link-seeding-policy-audit",
            "clifford-edge-semantics-audit",
        ],
        "projection_shape": projection.get("projection_shape", {}),
        "low_control_probe": LOW_CONTROL_GRAPH,
        "authoritative_graph": AUTHORITATIVE_GRAPH,
    }
    return report, packet


def run_toponetx_projection_adapter_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_toponetx_projection_adapter_report(root, ctx)
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
    result = run_toponetx_projection_adapter_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
