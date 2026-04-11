"""
identity_registry_overlap_quarantine.py

Quarantine heuristic identity-overlap edges out of the live identity owner
surface into a separate non-canonical suggestion surface.

This pass is intentionally conservative: it treats all current
`IDENTITY_OVERLAP` edges as lexical suggestions rather than canonical identity
facts and removes them from the owner surface.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from system_v4.skills.graph_store import load_graph_json


REPO_ROOT = Path(__file__).resolve().parents[2]

OWNER_JSON = "system_v4/a2_state/graphs/identity_registry_v1.json"
SUGGESTION_JSON = "system_v4/a2_state/graphs/identity_registry_overlap_suggestions_v1.json"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/IDENTITY_REGISTRY_OVERLAP_QUARANTINE_AUDIT__2026_03_20__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


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
    return json.loads(path.read_text(encoding="utf-8"))


def _top_shared_token_patterns(edges: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for edge in edges:
        attrs = edge.get("attributes", {}) or {}
        tokens = tuple(attrs.get("shared_tokens", []))
        if tokens:
            counts[tokens] += 1
    top: list[dict[str, Any]] = []
    for tokens, count in counts.most_common(limit):
        top.append({"shared_tokens": list(tokens), "count": count})
    return top


def build_quarantine_report(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    owner_path = _resolve(root, OWNER_JSON)
    owner = _load_json(owner_path)

    nodes = owner.get("nodes", {})
    edges = owner.get("edges", [])
    if not isinstance(nodes, dict) or not isinstance(edges, list):
        raise ValueError("identity registry owner surface is not a graph-shaped JSON surface")

    quarantined_edges = [edge for edge in edges if edge.get("relation") == "IDENTITY_OVERLAP"]
    retained_edges = [edge for edge in edges if edge.get("relation") != "IDENTITY_OVERLAP"]

    affected_node_ids: set[str] = set()
    for edge in quarantined_edges:
        source_id = edge.get("source_id", "")
        target_id = edge.get("target_id", "")
        if source_id in nodes:
            affected_node_ids.add(source_id)
        if target_id in nodes:
            affected_node_ids.add(target_id)

    suggestion_nodes = {node_id: nodes[node_id] for node_id in sorted(affected_node_ids)}
    top_patterns = _top_shared_token_patterns(quarantined_edges)

    owner_out = dict(owner)
    owner_out["edges"] = retained_edges
    owner_out.setdefault("summary", {})
    owner_out["summary"]["quarantined_identity_overlap_count"] = len(quarantined_edges)
    owner_out["summary"]["retained_owner_edge_count"] = len(retained_edges)
    owner_out["summary"]["last_identity_overlap_quarantine_utc"] = _utc_iso()

    suggestion_out = {
        "schema": "IDENTITY_REGISTRY_OVERLAP_SUGGESTIONS_v1",
        "generated_utc": _utc_iso(),
        "source_owner_surface": str(owner_path),
        "description": (
            "Non-canonical lexical identity-overlap suggestions quarantined out of the "
            "identity owner surface because they are not strong identity proofs."
        ),
        "quarantine_rule": {
            "quarantined_relation": "IDENTITY_OVERLAP",
            "owner_surface_policy": "owner surface retains only canonical identity facts, not lexical overlap suggestions",
            "keep_rule": "keep none of the current IDENTITY_OVERLAP edges in the owner surface",
        },
        "summary": {
            "node_count": len(suggestion_nodes),
            "edge_count": len(quarantined_edges),
            "top_shared_token_patterns": top_patterns,
        },
        "nodes": suggestion_nodes,
        "edges": quarantined_edges,
    }

    return {
        "generated_utc": _utc_iso(),
        "owner_path": str(owner_path),
        "owner_before_node_count": len(nodes),
        "owner_before_edge_count": len(edges),
        "owner_after_edge_count": len(retained_edges),
        "quarantined_edge_count": len(quarantined_edges),
        "affected_node_count": len(suggestion_nodes),
        "top_shared_token_patterns": top_patterns,
        "owner_surface": owner_out,
        "suggestion_surface": suggestion_out,
    }


def render_audit_note(report: dict[str, Any]) -> str:
    lines = [
        "# IDENTITY_REGISTRY_OVERLAP_QUARANTINE_AUDIT__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"owner_path: {report['owner_path']}",
        f"owner_before_node_count: {report['owner_before_node_count']}",
        f"owner_before_edge_count: {report['owner_before_edge_count']}",
        f"owner_after_edge_count: {report['owner_after_edge_count']}",
        f"quarantined_edge_count: {report['quarantined_edge_count']}",
        f"affected_node_count: {report['affected_node_count']}",
        "",
        "## Quarantine Rule",
        "- All current `IDENTITY_OVERLAP` edges are treated as lexical suggestion edges, not canonical identity facts.",
        "- The identity owner surface keeps nodes but drops heuristic overlap edges.",
        "- Quarantined edges move into `identity_registry_overlap_suggestions_v1.json` as a non-canonical suggestion surface.",
        "",
        "## Top Shared Token Patterns",
    ]
    if report["top_shared_token_patterns"]:
        for item in report["top_shared_token_patterns"]:
            lines.append(f"- {item['count']}: {item['shared_tokens']}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Non-Claims",
        "- This pass does not infer a smaller semantic subset of overlap edges as canonical identity facts.",
        "- This pass does not redesign the identity registry builder.",
        "- This pass does not claim the quarantined suggestion surface is authoritative.",
        "",
    ])
    return "\n".join(lines)


def write_identity_registry_overlap_quarantine(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_quarantine_report(str(root))

    owner_path = _resolve(root, OWNER_JSON)
    suggestion_path = _resolve(root, SUGGESTION_JSON)
    audit_path = _resolve(root, AUDIT_NOTE)

    owner_path.parent.mkdir(parents=True, exist_ok=True)
    suggestion_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    owner_path.write_text(
        json.dumps(report["owner_surface"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    suggestion_path.write_text(
        json.dumps(report["suggestion_surface"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit_path.write_text(render_audit_note(report), encoding="utf-8")

    return {
        "owner_json_path": str(owner_path),
        "suggestion_json_path": str(suggestion_path),
        "audit_note_path": str(audit_path),
    }


if __name__ == "__main__":
    result = write_identity_registry_overlap_quarantine(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
