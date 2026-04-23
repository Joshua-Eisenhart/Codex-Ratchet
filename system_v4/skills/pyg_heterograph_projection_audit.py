"""
pyg_heterograph_projection_audit.py

Define the first honest read-only PyTorch Geometric projection contract over
the current control-facing graph families.

This module does not change canonical graph ownership. The JSON-backed live
graph remains authoritative; the PyG view is a bounded projection used to prove
data flow and expose real relation families.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from system_v4.skills.graph_store import load_graph_json


REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
LOW_CONTROL_PROBE = "system_v4/a2_state/graphs/a2_low_control_graph_v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_PACKET__CURRENT__v1.json"

SKILL_ID = "pyg-heterograph-projection-audit"
PROJECTION_ID = "PYG_PROJECTION::control_subgraph_v1"
PREFERRED_INTERPRETER = sys.executable

FOCUS_NODE_TYPES = (
    "KERNEL_CONCEPT",
    "SKILL",
    "EXECUTION_BLOCK",
    "B_OUTCOME",
    "B_SURVIVOR",
    "SIM_EVIDENCED",
)

DEFERRED_EDGE_FIELDS = [
    "entropy_state",
    "correlation_entropy",
    "orientation_basis",
    "clifford_grade",
    "obstruction_score",
]


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


def _coerce_numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _try_import_pyg() -> tuple[bool, str]:
    try:
        import torch  # noqa: F401
        from torch_geometric.data import HeteroData  # noqa: F401
        return True, ""
    except Exception as exc:  # pragma: no cover - exercised in non-venv contexts
        return False, f"{type(exc).__name__}: {exc}"


def _low_control_probe_status(root: Path) -> dict[str, Any]:
    path = root / LOW_CONTROL_PROBE
    data = _load_json(path)
    nodes = data.get("nodes", {}) if isinstance(data, dict) else {}
    edges = data.get("edges", []) if isinstance(data, dict) else []
    node_type_counts = Counter(
        node.get("node_type", "?") for node in nodes.values() if isinstance(node, dict)
    )
    relation_counts = Counter(
        edge.get("relation", "?") for edge in edges if isinstance(edge, dict)
    )
    return {
        "path": LOW_CONTROL_PROBE,
        "exists": path.exists(),
        "node_count": len(nodes) if isinstance(nodes, dict) else 0,
        "edge_count": len(edges) if isinstance(edges, list) else 0,
        "node_type_counts": dict(node_type_counts),
        "relation_counts": dict(relation_counts),
        "is_sufficient_alone": set(node_type_counts.keys()) >= {"SKILL", "KERNEL_CONCEPT"},
        "reason_not_sufficient_alone": (
            "current owner surface is all KERNEL_CONCEPT nodes and does not carry the full control-facing family set"
        ),
    }


def _collect_projection_view(root: Path) -> dict[str, Any]:
    data = _load_json(root / AUTHORITATIVE_GRAPH)
    nodes = data.get("nodes", {}) if isinstance(data, dict) else {}
    edges = data.get("edges", []) if isinstance(data, dict) else []

    selected_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if isinstance(node, dict) and node.get("node_type") in FOCUS_NODE_TYPES
    }
    selected_edges = [
        edge
        for edge in edges
        if isinstance(edge, dict)
        and edge.get("source_id") in selected_nodes
        and edge.get("target_id") in selected_nodes
    ]

    node_ids_by_type: dict[str, list[str]] = defaultdict(list)
    for node_id, node in selected_nodes.items():
        node_ids_by_type[str(node.get("node_type"))].append(node_id)
    for ids in node_ids_by_type.values():
        ids.sort()

    index_by_type = {
        node_type: {node_id: idx for idx, node_id in enumerate(node_ids)}
        for node_type, node_ids in node_ids_by_type.items()
    }

    edge_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    pair_counts: Counter[tuple[str, str]] = Counter()
    relation_counts: Counter[tuple[str, str, str]] = Counter()
    for edge in selected_edges:
        source_type = str(selected_nodes[edge["source_id"]]["node_type"])
        target_type = str(selected_nodes[edge["target_id"]]["node_type"])
        relation = str(edge.get("relation", "?"))
        triple = (source_type, relation, target_type)
        edge_groups[triple].append(edge)
        pair_counts[(source_type, target_type)] += 1
        relation_counts[triple] += 1

    edge_contracts: list[dict[str, Any]] = []
    for (source_type, relation, target_type), grouped_edges in sorted(edge_groups.items()):
        numeric_keys: set[str] = set()
        attr_key_counts: Counter[str] = Counter()
        for edge in grouped_edges:
            attributes = edge.get("attributes", {}) or {}
            for key, value in attributes.items():
                attr_key_counts[key] += 1
                if _coerce_numeric(value) is not None:
                    numeric_keys.add(key)
        edge_contracts.append(
            {
                "edge_type": {
                    "source_type": source_type,
                    "relation": relation,
                    "target_type": target_type,
                },
                "edge_count": len(grouped_edges),
                "all_attribute_keys": sorted(attr_key_counts.keys()),
                "numeric_attribute_keys": sorted(numeric_keys),
            }
        )

    node_contracts: list[dict[str, Any]] = []
    for node_type, node_ids in sorted(node_ids_by_type.items()):
        prop_keys: Counter[str] = Counter()
        for node_id in node_ids:
            for key in (selected_nodes[node_id].get("properties", {}) or {}).keys():
                prop_keys[key] += 1
        node_contracts.append(
            {
                "node_type": node_type,
                "node_count": len(node_ids),
                "property_keys": sorted(prop_keys.keys()),
                "canonical_side_table_fields": [
                    "id",
                    "name",
                    "description",
                    "layer",
                    "trust_zone",
                    "authority",
                    "status",
                    "admissibility_state",
                    "tags",
                ],
            }
        )

    observed_limits = []
    if relation_counts.get(("SKILL", "RELATED_TO", "SKILL"), 0) > 0 and not any(
        source == "SKILL" and target == "KERNEL_CONCEPT"
        for source, _, target in relation_counts
    ):
        observed_limits.append(
            "skill nodes currently project as a separate relation family; direct skill-to-kernel bridges are not materially present"
        )
    if relation_counts.get(("B_OUTCOME", "ADJUDICATED_FROM", "EXECUTION_BLOCK"), 0) > 0:
        observed_limits.append(
            "B_OUTCOME currently connects to EXECUTION_BLOCK, not directly to the kernel concept graph"
        )
    if relation_counts.get(("SIM_EVIDENCED", "SIM_EVIDENCE_FOR", "B_SURVIVOR"), 0) > 0:
        observed_limits.append(
            "SIM_EVIDENCED currently connects to B_SURVIVOR, so witness evidence is present but not yet unified into the kernel/skill slice"
        )

    return {
        "selected_nodes": selected_nodes,
        "selected_edges": selected_edges,
        "node_ids_by_type": dict(node_ids_by_type),
        "index_by_type": index_by_type,
        "edge_groups": edge_groups,
        "node_contracts": node_contracts,
        "edge_contracts": edge_contracts,
        "pair_counts": {
            f"{source}->{target}": count for (source, target), count in sorted(pair_counts.items())
        },
        "relation_counts": {
            f"{source}::{relation}::{target}": count
            for (source, relation, target), count in sorted(relation_counts.items())
        },
        "observed_limits": observed_limits,
    }


def _build_pyg_summary(view: dict[str, Any]) -> dict[str, Any]:
    import torch
    from torch_geometric.data import HeteroData

    data = HeteroData()
    for node_type, node_ids in view["node_ids_by_type"].items():
        data[node_type].num_nodes = len(node_ids)
        data[node_type].node_index = torch.arange(len(node_ids), dtype=torch.long)

    edge_store_summaries = []
    for edge_contract in view["edge_contracts"]:
        edge_type = edge_contract["edge_type"]
        triple = (
            edge_type["source_type"],
            edge_type["relation"],
            edge_type["target_type"],
        )
        grouped_edges = view["edge_groups"][triple]
        source_index = view["index_by_type"][edge_type["source_type"]]
        target_index = view["index_by_type"][edge_type["target_type"]]
        src = [source_index[edge["source_id"]] for edge in grouped_edges]
        dst = [target_index[edge["target_id"]] for edge in grouped_edges]
        data[triple].edge_index = torch.tensor([src, dst], dtype=torch.long)

        numeric_keys = edge_contract["numeric_attribute_keys"]
        if numeric_keys:
            edge_attr_rows = []
            for edge in grouped_edges:
                attrs = edge.get("attributes", {}) or {}
                row = []
                for key in numeric_keys:
                    row.append(_coerce_numeric(attrs.get(key)) or 0.0)
                edge_attr_rows.append(row)
            data[triple].edge_attr = torch.tensor(edge_attr_rows, dtype=torch.float32)

        edge_store_summaries.append(
            {
                "edge_type": edge_type,
                "edge_count": len(grouped_edges),
                "has_edge_attr": bool(numeric_keys),
                "edge_attr_keys": numeric_keys,
            }
        )

    return {
        "node_store_count": len(view["node_ids_by_type"]),
        "edge_store_count": len(view["edge_contracts"]),
        "node_stores": [
            {"node_type": node_type, "node_count": len(node_ids)}
            for node_type, node_ids in sorted(view["node_ids_by_type"].items())
        ],
        "edge_stores": edge_store_summaries,
        "training_ready": False,
        "training_ready_reason": "projection contract exists, but feature engineering and bridge completion are still bounded follow-ons",
        "heterodata_repr": repr(data),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    limit_lines = [f"- {item}" for item in report.get("observed_limits", [])] or ["- none"]
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    node_lines = [
        f"- `{item['node_type']}`: {item['node_count']} nodes"
        for item in report.get("node_contracts", [])
    ]
    edge_lines = [
        f"- `{item['edge_type']['source_type']}::{item['edge_type']['relation']}::{item['edge_type']['target_type']}`: {item['edge_count']} edges"
        for item in report.get("edge_contracts", [])
    ]
    return "\n".join(
        [
            "# PyG Heterograph Projection Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- projection_id: `{report['projection_id']}`",
            f"- projection_focus: `{report['projection_focus']}`",
            f"- canonical_graph_owner: `{report['canonical_graph_owner']}`",
            f"- bounded_probe_source: `{report['bounded_probe_source']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            "",
            "## Node Contract",
            *node_lines,
            "",
            "## Edge Contract",
            *edge_lines,
            "",
            "## Observed Limits",
            *limit_lines,
            "",
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_pyg_heterograph_projection_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    authoritative_path = root / AUTHORITATIVE_GRAPH
    probe_status = _low_control_probe_status(root)
    pyg_ok, pyg_error = _try_import_pyg()
    issues: list[str] = []
    if not authoritative_path.exists():
        issues.append("missing authoritative live graph store")

    view = _collect_projection_view(root) if authoritative_path.exists() else {
        "selected_nodes": {},
        "selected_edges": [],
        "node_ids_by_type": {},
        "edge_contracts": [],
        "node_contracts": [],
        "pair_counts": {},
        "relation_counts": {},
        "observed_limits": [],
    }
    pyg_summary = {}
    if not pyg_ok:
        issues.append(f"PyG runtime unavailable: {pyg_error}")
        status = "blocked_missing_tool"
    else:
        pyg_summary = _build_pyg_summary(view)
        status = "ok"

    report = {
        "schema": "PYG_HETEROGRAPH_PROJECTION_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "projection_id": PROJECTION_ID,
        "projection_focus": "read_only_control_subgraph",
        "skill_id": SKILL_ID,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "canonical_graph_owner": AUTHORITATIVE_GRAPH,
        "bounded_probe_source": LOW_CONTROL_PROBE,
        "preferred_interpreter": PREFERRED_INTERPRETER,
        "focus_node_types": list(FOCUS_NODE_TYPES),
        "node_contracts": view["node_contracts"],
        "edge_contracts": view["edge_contracts"],
        "relation_family_counts": view["relation_counts"],
        "node_family_pair_counts": view["pair_counts"],
        "low_control_probe_status": probe_status,
        "pyg_summary": pyg_summary,
        "deferred_edge_fields": list(DEFERRED_EDGE_FIELDS),
        "observed_limits": view["observed_limits"],
        "issues": issues,
        "recommended_next_actions": [
            "Keep canonical graph ownership in the JSON-backed live graph store.",
            "Use this projection as a read-only PyG view over the control-facing families only.",
            "Add a separate graph-bridge audit for skill-to-kernel and witness-to-kernel links before any training claim.",
            "Treat TopoNetX as the next higher-order projection lane rather than widening this PyG slice into full topology ownership.",
        ],
    }
    packet = {
        "schema": "PYG_HETEROGRAPH_PROJECTION_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "projection_id": PROJECTION_ID,
        "status": status,
        "allow_read_only_projection": pyg_ok,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "recommended_next_slice_id": "toponetx-projection-adapter-audit",
        "preferred_interpreter": PREFERRED_INTERPRETER,
        "requires_packages": ["torch", "torch-geometric"],
        "canonical_graph_owner": AUTHORITATIVE_GRAPH,
        "bounded_probe_source": LOW_CONTROL_PROBE,
        "projection_focus": report["projection_focus"],
    }
    return report, packet


def run_pyg_heterograph_projection_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_pyg_heterograph_projection_report(root, ctx)
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
    result = run_pyg_heterograph_projection_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
