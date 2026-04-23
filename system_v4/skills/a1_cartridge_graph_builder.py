"""
a1_cartridge_graph_builder.py

Materialize the bounded A1 cartridge owner graph from the live A1 stripped
owner graph plus current cartridge/admissibility doctrine. This pass is
intentionally fail-closed: it will only package exact stripped terms that have
explicit cartridge permission in current repo-held doctrine, and it writes only
the narrow wrapper edge that the live assembler already authorizes.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


A1_STRIPPED = "system_v4/a1_state/a1_stripped_graph_v1.json"
HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/nested_graph_build_a1_cartridge/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_CARTRIDGE__2026_03_20__v1.json"
)
CARTRIDGE_REVIEW = (
    "system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
)
CROSS_JUDGMENT = (
    "system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md"
)
ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
OUTPUT_JSON = "system_v4/a1_state/a1_cartridge_graph_v1.json"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/A1_CARTRIDGE_GRAPH_AUDIT__2026_03_20__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


TERM_PACKAGE_PLAN = {
    "pairwise_correlation_spread_functional": {
        "allowed": False,
        "why": (
            "current cartridge doctrine keeps this exact stripped term as a colder "
            "alias candidate / witness-side term, not as packageable cartridge fuel"
        ),
        "evidence": [
            "A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md",
            "A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md",
            "A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md",
        ],
    },
}


def build_a1_cartridge_graph(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    stripped_path = _resolve(root, A1_STRIPPED)
    handoff_path = _resolve(root, HANDOFF_PACKET)
    cartridge_review_path = _resolve(root, CARTRIDGE_REVIEW)
    cross_judgment_path = _resolve(root, CROSS_JUDGMENT)
    alias_lift_path = _resolve(root, ALIAS_LIFT)

    stripped = _load_json(stripped_path)
    handoff = _load_json(handoff_path)

    stripped_nodes = stripped.get("nodes", {})
    nodes: dict[str, Any] = {}
    edges: list[dict[str, Any]] = []
    blocked_terms: list[dict[str, Any]] = []
    blockers: list[str] = []

    required_surfaces = {
        "a1_stripped_graph": stripped_path,
        "handoff_packet": handoff_path,
        "cartridge_review": cartridge_review_path,
        "cross_judgment": cross_judgment_path,
        "alias_lift_pack": alias_lift_path,
    }
    for label, path in required_surfaces.items():
        if not path.exists():
            blockers.append(f"missing required surface: {label} -> {path}")

    for stripped_id, node in sorted(stripped_nodes.items()):
        term = str(node.get("name", "")).strip()
        plan = TERM_PACKAGE_PLAN.get(term)
        if not plan:
            blocked_terms.append({
                "term": term,
                "reason": "no exact cartridge doctrine plan exists for this stripped term",
            })
            continue
        if not plan["allowed"]:
            blocked_terms.append({
                "term": term,
                "reason": plan["why"],
                "evidence": list(plan.get("evidence", [])),
            })
            continue

        cartridge_id = f"A1_CARTRIDGE::{term}"
        nodes[cartridge_id] = {
            "id": cartridge_id,
            "node_type": "CARTRIDGE_PACKAGE",
            "layer": "A1_CARTRIDGE",
            "trust_zone": "A1_CARTRIDGE",
            "name": term,
            "description": (
                "Minimal cartridge envelope for an exact stripped term that current "
                "repo-held doctrine treats as packageable."
            ),
            "status": "LIVE",
            "source_class": "OWNER_BOUND",
            "admissibility_state": "PACKAGEABLE",
            "lineage_refs": list(node.get("lineage_refs", [])),
            "witness_refs": list(node.get("witness_refs", [])),
            "properties": {
                "source_stripped_id": stripped_id,
                "source_term": term,
                "package_mode": "EXACT_TERM_ONLY",
            },
        }
        edges.append({
            "source_id": cartridge_id,
            "target_id": stripped_id,
            "relation": "PACKAGED_FROM",
            "attributes": {},
        })

    materialized = bool(nodes)
    build_status = "MATERIALIZED" if materialized else "FAIL_CLOSED"
    if not stripped_nodes:
        blockers.append("A1_STRIPPED owner graph is missing or empty")
    if not materialized:
        blockers.append("no exact A1_STRIPPED terms satisfy the current cartridge inclusion rule")

    return {
        "schema": "A1_CARTRIDGE_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "owner_layer": "A1_CARTRIDGE",
        "materialized": materialized,
        "build_status": build_status,
        "derived_from": {
            "a1_stripped_graph": str(stripped_path),
            "handoff_packet": str(handoff_path),
            "cartridge_review": str(cartridge_review_path),
            "cross_judgment": str(cross_judgment_path),
            "alias_lift_pack": str(alias_lift_path),
        },
        "selection_contract": {
            "included_node_rule": (
                "Include only materialized A1_STRIPPED nodes whose exact stripped "
                "term is currently treated by cartridge doctrine as packageable "
                "fuel rather than witness-only or deferred."
            ),
            "edge_rule": (
                "Materialize only PACKAGED_FROM edges from A1_CARTRIDGE to "
                "A1_STRIPPED. Do not promote COMPILED_FROM or infer internal "
                "strategy/dependency topology."
            ),
            "exact_term_gate": "family-level cartridge PASS is insufficient; the exact stripped term must pass",
        },
        "blockers": blockers,
        "blocked_terms": blocked_terms,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "included_terms": [node["properties"]["source_term"] for node in nodes.values()],
            "blocked_term_count": len(blocked_terms),
        },
        "nodes": nodes,
        "edges": edges,
        "handoff_snapshot": {
            "dispatch_id": handoff.get("dispatch_id", ""),
            "queue_status": handoff.get("queue_status", ""),
        },
    }


def render_audit_note(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# A1_CARTRIDGE_GRAPH_AUDIT__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"build_status: {report['build_status']}",
        f"materialized: {report['materialized']}",
        f"node_count: {summary['node_count']}",
        f"edge_count: {summary['edge_count']}",
        "",
        "## Included Terms",
    ]
    if summary["included_terms"]:
        for term in summary["included_terms"]:
            lines.append(f"- {term}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Blocked Terms",
    ])
    if report["blocked_terms"]:
        for item in report["blocked_terms"]:
            evidence = item.get("evidence", [])
            if evidence:
                lines.append(
                    f"- {item['term']}: {item['reason']} "
                    f"(evidence: {', '.join(evidence)})"
                )
            else:
                lines.append(f"- {item['term']}: {item['reason']}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Selection Contract",
        f"- included_node_rule: {report['selection_contract']['included_node_rule']}",
        f"- edge_rule: {report['selection_contract']['edge_rule']}",
        f"- exact_term_gate: {report['selection_contract']['exact_term_gate']}",
        "",
        "## Non-Claims",
        "- This pass does not promote family-level cartridge PASS into exact-term packageability.",
        "- This pass does not materialize internal cartridge strategy edges.",
        "- This pass does not promote downstream A0 COMPILED_FROM edges into cartridge-owner doctrine.",
        "",
    ])
    return "\n".join(lines)


def write_a1_cartridge_graph(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_a1_cartridge_graph(str(root))

    json_path = _resolve(root, OUTPUT_JSON)
    audit_note_path = _resolve(root, AUDIT_NOTE)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    audit_note_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit_note_path.write_text(render_audit_note(report), encoding="utf-8")
    return {"json_path": str(json_path), "audit_note_path": str(audit_note_path)}


if __name__ == "__main__":
    result = write_a1_cartridge_graph(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
