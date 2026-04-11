"""
skill_kernel_link_seeding_policy_audit.py

Audit what evidence is insufficient versus sufficient for future SKILL ->
KERNEL_CONCEPT link seeding under the current registry and graph truth.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from system_v4.skills.graph_store import load_graph_json


REPO_ROOT = Path(__file__).resolve().parents[2]

SKILL_REGISTRY = "system_v4/a1_state/skill_registry_v1.json"
AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
BRIDGE_SOURCE_JSON = "system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_PACKET__CURRENT__v1.json"


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


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _collect_policy_inputs(root: Path) -> dict[str, Any]:
    registry = _load_json(root / SKILL_REGISTRY)
    graph = _load_json(root / AUTHORITATIVE_GRAPH)
    rows = registry if isinstance(registry, dict) else {}
    nodes = graph.get("nodes", {}) if isinstance(graph, dict) else {}
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    if not isinstance(nodes, dict):
        nodes = {}
    if not isinstance(edges, list):
        edges = []

    registry_key_counts = Counter()
    registry_concept_field_hits = 0
    skill_ids_with_registry_concept_fields: list[str] = []
    for skill_id, row in rows.items():
        if not isinstance(row, dict):
            continue
        for key in row:
            registry_key_counts[key] += 1
            if ("concept" in key.lower() or "kernel" in key.lower()) and _nonempty(row.get(key)):
                registry_concept_field_hits += 1
                if len(skill_ids_with_registry_concept_fields) < 5:
                    skill_ids_with_registry_concept_fields.append(skill_id)

    skill_property_key_counts = Counter()
    skill_property_concept_field_hits = 0
    skill_node_count = 0
    for node in nodes.values():
        if not isinstance(node, dict) or node.get("node_type") != "SKILL":
            continue
        skill_node_count += 1
        props = node.get("properties", {}) or {}
        for key in props:
            skill_property_key_counts[key] += 1
            if ("concept" in key.lower() or "kernel" in key.lower()) and _nonempty(props.get(key)):
                skill_property_concept_field_hits += 1

    skill_edge_family_counts = Counter()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        if source_id not in nodes or target_id not in nodes:
            continue
        if nodes[source_id].get("node_type") != "SKILL":
            continue
        skill_edge_family_counts[(str(edge.get("relation", "?")), str(nodes[target_id].get("node_type")))] += 1

    return {
        "registry_row_count": sum(1 for row in rows.values() if isinstance(row, dict)),
        "registry_key_counts": dict(registry_key_counts),
        "registry_concept_field_hits": registry_concept_field_hits,
        "skill_ids_with_registry_concept_fields": skill_ids_with_registry_concept_fields,
        "skill_node_count": skill_node_count,
        "skill_property_key_counts": dict(skill_property_key_counts),
        "skill_property_concept_field_hits": skill_property_concept_field_hits,
        "skill_edge_family_counts": {
            f"{relation}::{target_type}": count
            for (relation, target_type), count in sorted(skill_edge_family_counts.items())
        },
    }


def _render_markdown(report: dict[str, Any]) -> str:
    forbidden_lines = [f"- {item}" for item in report.get("forbidden_now", [])]
    sufficient_lines = [f"- {item}" for item in report.get("future_minimally_sufficient_evidence", [])]
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Skill Kernel Link Seeding Policy Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- allow_auto_seeding_now: `{report['allow_auto_seeding_now']}`",
            "",
            "## Forbidden Now",
            *forbidden_lines,
            "",
            "## Future Minimally Sufficient Evidence",
            *sufficient_lines,
            "",
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_skill_kernel_link_seeding_policy_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    registry_path = root / SKILL_REGISTRY
    graph_path = root / AUTHORITATIVE_GRAPH
    bridge_source = _load_json(root / BRIDGE_SOURCE_JSON)

    issues: list[str] = []
    if not registry_path.exists():
        issues.append("missing skill registry")
    if not graph_path.exists():
        issues.append("missing authoritative live graph store")
    if not bridge_source:
        issues.append("missing or unreadable bridge-source audit")

    inputs = _collect_policy_inputs(root) if registry_path.exists() and graph_path.exists() else {
        "registry_row_count": 0,
        "registry_key_counts": {},
        "registry_concept_field_hits": 0,
        "skill_ids_with_registry_concept_fields": [],
        "skill_node_count": 0,
        "skill_property_key_counts": {},
        "skill_property_concept_field_hits": 0,
        "skill_edge_family_counts": {},
    }

    allow_auto_seeding_now = (
        inputs["registry_concept_field_hits"] > 0
        and inputs["skill_property_concept_field_hits"] > 0
    )
    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "allow_auto_seeding_now": allow_auto_seeding_now,
        "skill_registry": SKILL_REGISTRY,
        "authoritative_graph": AUTHORITATIVE_GRAPH,
        "supporting_bridge_source_audit": BRIDGE_SOURCE_JSON,
        "registry_row_count": inputs["registry_row_count"],
        "skill_node_count": inputs["skill_node_count"],
        "registry_concept_field_hits": inputs["registry_concept_field_hits"],
        "skill_property_concept_field_hits": inputs["skill_property_concept_field_hits"],
        "skill_edge_family_counts": inputs["skill_edge_family_counts"],
        "forbidden_now": [
            "Do not seed SKILL -> KERNEL_CONCEPT links from source_path, source_type, skill_type, status, provenance, tags, applicable_trust_zones, applicable_graphs, inputs, outputs, adapters, or related_skills alone.",
            "Do not seed SKILL -> KERNEL_CONCEPT links from inferred SKILL -> SKILL relations such as RELATED_TO or SKILL_FOLLOWS.",
            "Do not seed SKILL -> KERNEL_CONCEPT links from free-text descriptions or SKILL.md prose without an owner-bound concept-id field.",
        ],
        "future_minimally_sufficient_evidence": [
            "An explicit owner-bound concept identity field on the registry row and mirrored skill node properties, such as concept_refs or kernel_concept_ids.",
            "A bounded audited packet or report that names skill_id, target concept ids, and relation semantics, with repo-held provenance.",
            "A durable runtime witness or dispatch record that ties skill execution to explicit concept ids rather than only to phase or graph-family metadata.",
        ],
        "recommended_next_actions": [
            "Keep auto-seeding fail-closed now; current registry rows and graph nodes do not carry owner-bound concept identity on the skill side.",
            "Treat the current skill island as metadata-only for kernel linkage purposes, even though it is graph-complete as a skill inventory.",
            "Move next to clifford-edge-semantics-audit for graph-side edge semantics, while keeping run_real_ratchet dispatch debt in watch-only mode.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "SKILL_KERNEL_LINK_SEEDING_POLICY_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "allow_auto_seeding_now": allow_auto_seeding_now,
        "recommended_next_slice_ids": [
            "clifford-edge-semantics-audit",
        ],
        "skill_edge_family_counts": report["skill_edge_family_counts"],
        "authoritative_graph": AUTHORITATIVE_GRAPH,
    }
    return report, packet


def run_skill_kernel_link_seeding_policy_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_skill_kernel_link_seeding_policy_report(root, ctx)
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
    result = run_skill_kernel_link_seeding_policy_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
