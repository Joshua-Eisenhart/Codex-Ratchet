"""
a1_stripped_graph_builder.py

Materialize the bounded A1 stripped owner graph from the live A1 jargoned owner
graph plus current A1 admissibility doctrine. This pass is intentionally
fail-closed and only emits strip bridges that are explicitly authorized.
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


A1_JARGONED = "system_v4/a1_state/a1_jargoned_graph_v1.json"
HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/nested_graph_build_a1_stripped/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_STRIPPED__2026_03_20__v1.json"
)
FAMILY_SLICE = "system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json"
ROSETTA_BATCH = "system_v3/a1_state/A1_ROSETTA_BATCH__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
LIFT_PACK = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md"
LIVE_HINTS = "system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md"
EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
OUTPUT_JSON = "system_v4/a1_state/a1_stripped_graph_v1.json"
AUDIT_NOTE = "system_v4/a2_state/audit_logs/A1_STRIPPED_GRAPH_AUDIT__2026_03_20__v1.md"
A1_STRIPPED_TERM_PLAN_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
A1_STRIPPED_EXACT_TERM_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_STRIPPED_EXACT_TERM_ALIGNMENT__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1.md"
)
A2_REFINEMENT_FOR_A1_STRIPPED_LANDING_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _should_preserve_existing(existing: dict[str, Any], report: dict[str, Any]) -> bool:
    existing_nodes = existing.get("nodes", {})
    existing_edges = existing.get("edges", [])
    report_nodes = report.get("nodes", {})
    report_edges = report.get("edges", [])
    if not isinstance(existing_nodes, dict) or not isinstance(existing_edges, list):
        return False
    if not isinstance(report_nodes, dict) or not isinstance(report_edges, list):
        return False
    existing_materialized = existing.get("materialized") is True
    report_materialized = report.get("materialized") is True
    return (
        len(existing_nodes) > len(report_nodes)
        or len(existing_edges) > len(report_edges)
        or (existing_materialized and not report_materialized)
    )


TERM_STRIP_PLAN = {
    "correlation_diversity_functional": {
        "allowed": False,
        "doctrine_status": "PASSENGER_ONLY_WITHOUT_EXACT_STRIPPED_LANDING",
        "why": (
            "current doctrine keeps the only available stripped alias "
            "pairwise_correlation_spread_functional witness-side only, so no "
            "exact stripped landing is currently justified for this passenger family term"
        ),
        "supporting_audit_refs": [
            A1_STRIPPED_TERM_PLAN_AUDIT,
            A1_STRIPPED_EXACT_TERM_AUDIT,
            A2_REFINEMENT_FOR_A1_STRIPPED_LANDING_AUDIT,
        ],
        "supporting_source_refs": [
            LIVE_HINTS,
            ROSETTA_BATCH,
            LIFT_PACK,
            A2_DISTILLATION_INPUTS,
        ],
    },
    "probe_induced_partition_boundary": {
        "allowed": False,
        "doctrine_status": "WITNESS_ONLY_DEFERRED",
        "why": "current doctrine keeps this term witness-only and deferred pending colder partition support",
        "supporting_audit_refs": [],
        "supporting_source_refs": [
            LIVE_HINTS,
            LIFT_PACK,
            EXEC_ENTRYPOINT,
            A2_DISTILLATION_INPUTS,
        ],
    },
}


def _resolve_refs(root: Path, raw_paths: list[str]) -> list[str]:
    return [str(_resolve(root, raw_path)) for raw_path in raw_paths]


def _build_term_diagnostic(
    root: Path,
    *,
    term: str,
    matching_jargoned_ids: list[str],
    reason: str,
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    plan = plan or {}
    return {
        "term": term,
        "reason": reason,
        "matching_jargoned_ids": list(matching_jargoned_ids),
        "doctrine_status": str(plan.get("doctrine_status", "")).strip(),
        "supporting_audit_refs": _resolve_refs(root, list(plan.get("supporting_audit_refs", []))),
        "supporting_source_refs": _resolve_refs(root, list(plan.get("supporting_source_refs", []))),
    }


def build_a1_stripped_graph(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    jargoned = _load_json(_resolve(root, A1_JARGONED))
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    family_slice = _load_json(_resolve(root, FAMILY_SLICE))

    selected_family_terms = [str(item).strip() for item in family_slice.get("target_families", []) if str(item).strip()]
    selected_terms = set(selected_family_terms)
    jargoned_nodes = jargoned.get("nodes", {})
    selected_term_to_jargoned_ids: dict[str, list[str]] = {}
    for jargoned_id, node in sorted(jargoned_nodes.items()):
        term = str(node.get("name", "")).strip()
        if term in selected_terms:
            selected_term_to_jargoned_ids.setdefault(term, []).append(jargoned_id)

    nodes: dict[str, Any] = {}
    edges: list[dict[str, Any]] = []
    blocked_terms: list[dict[str, Any]] = []

    for jargoned_id, node in sorted(jargoned_nodes.items()):
        term = str(node.get("name", "")).strip()
        plan = TERM_STRIP_PLAN.get(term)
        if term not in selected_terms:
            continue
        if not plan:
            blocked_terms.append(_build_term_diagnostic(
                root,
                term=term,
                matching_jargoned_ids=selected_term_to_jargoned_ids.get(term, [jargoned_id]),
                reason="no strip doctrine plan for this term",
                plan=None,
            ))
            continue
        if not plan["allowed"]:
            blocked_terms.append(_build_term_diagnostic(
                root,
                term=term,
                matching_jargoned_ids=selected_term_to_jargoned_ids.get(term, [jargoned_id]),
                reason=plan["why"],
                plan=plan,
            ))
            continue

        stripped_id = plan["stripped_id"]
        nodes[stripped_id] = {
            "id": stripped_id,
            "node_type": "REFINED_CONCEPT",
            "layer": "A1_STRIPPED",
            "trust_zone": "A1_STRIPPED",
            "name": plan["stripped_name"],
            "description": plan["description"],
            "status": "LIVE",
            "source_class": "OWNER_BOUND",
            "admissibility_state": plan["admissibility_state"],
            "lineage_refs": list(node.get("lineage_refs", [])),
            "witness_refs": [],
            "properties": {
                "source_jargoned_id": jargoned_id,
                "source_term": term,
                "candidate_sense_id": node.get("properties", {}).get("candidate_sense_id", ""),
                "source_concept_id": node.get("properties", {}).get("source_concept_id", ""),
                "role_in_family": plan["role_in_family"],
                "sponsor_head": plan["sponsor_head"],
                "witness_floor": list(plan["witness_floor"]),
                "dropped_jargon": list(plan["dropped_jargon"]),
            },
        }
        edges.append({
            "source_id": stripped_id,
            "target_id": jargoned_id,
            "relation": "STRIPPED_FROM",
            "attributes": {},
        })
        edges.append({
            "source_id": jargoned_id,
            "target_id": stripped_id,
            "relation": "ROSETTA_MAP",
            "attributes": {},
        })

    materialized = bool(nodes)
    build_status = "MATERIALIZED" if materialized else "FAIL_CLOSED"
    selected_terms_present = [
        term for term in selected_family_terms if selected_term_to_jargoned_ids.get(term)
    ]
    selected_terms_missing = [
        term for term in selected_family_terms if not selected_term_to_jargoned_ids.get(term)
    ]
    present_terms_without_doctrine_plan = [
        _build_term_diagnostic(
            root,
            term=term,
            matching_jargoned_ids=selected_term_to_jargoned_ids.get(term, []),
            reason="no strip doctrine plan for this term",
            plan=None,
        )
        for term in selected_terms_present
        if term not in TERM_STRIP_PLAN
    ]
    present_terms_blocked_by_doctrine = [
        item
        for item in blocked_terms
        if item["term"] in selected_terms_present and item["term"] in TERM_STRIP_PLAN
    ]
    present_terms_blocked_names = [
        term for term in selected_terms_present if any(item["term"] == term for item in present_terms_blocked_by_doctrine)
    ]
    present_terms_without_doctrine_plan_names = [
        term for term in selected_terms_present if any(item["term"] == term for item in present_terms_without_doctrine_plan)
    ]
    materializable_terms = [
        term
        for term in selected_terms_present
        if TERM_STRIP_PLAN.get(term, {}).get("allowed") is True
    ]
    selection_diagnostics = {
        "selected_terms_present_in_a1_jargoned": selected_terms_present,
        "selected_terms_missing_from_a1_jargoned": selected_terms_missing,
        "present_terms_without_doctrine_plan": present_terms_without_doctrine_plan,
        "present_terms_blocked_by_doctrine": present_terms_blocked_by_doctrine,
        "materializable_terms": materializable_terms,
    }
    blockers: list[str] = []
    if not materialized:
        blockers.append("no current A1_JARGONED terms satisfy the stripped-layer inclusion rule")
        if selected_terms_missing:
            blockers.append(
                "selected family terms missing from current A1_JARGONED: "
                + ", ".join(selected_terms_missing)
            )
        if present_terms_blocked_by_doctrine:
            blockers.append(
                "present selected terms remain doctrine-blocked: "
                + ", ".join(present_terms_blocked_names)
            )
        if present_terms_without_doctrine_plan:
            blockers.append(
                "present selected terms have no strip doctrine plan: "
                + ", ".join(present_terms_without_doctrine_plan_names)
            )

    return {
        "schema": "A1_STRIPPED_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "owner_layer": "A1_STRIPPED",
        "materialized": materialized,
        "build_status": build_status,
        "derived_from": {
            "a1_jargoned_graph": str(_resolve(root, A1_JARGONED)),
            "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
            "family_slice": str(_resolve(root, FAMILY_SLICE)),
            "rosetta_batch": str(_resolve(root, ROSETTA_BATCH)),
            "lift_pack": str(_resolve(root, LIFT_PACK)),
            "live_hints": str(_resolve(root, LIVE_HINTS)),
        },
        "selection_contract": {
            "included_node_rule": (
                "Include only materialized A1_JARGONED nodes whose exact stripped "
                "landing term is currently classified by A1 doctrine as at least "
                "PASSENGER_ONLY."
            ),
            "edge_rule": (
                "Materialize only STRIPPED_FROM and ROSETTA_MAP bridges. "
                "Do not write dependency edges until exact stripped-layer anchors exist."
            ),
            "selected_family_terms": selected_family_terms,
        },
        "blockers": blockers,
        "blocked_terms": blocked_terms,
        "selection_diagnostics": selection_diagnostics,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "included_terms": [node["properties"]["source_term"] for node in nodes.values()],
            "blocked_term_count": len(blocked_terms),
            "selected_term_count": len(selected_family_terms),
            "present_selected_term_count": len(selected_terms_present),
            "missing_selected_term_count": len(selected_terms_missing),
            "materializable_term_count": len(materializable_terms),
        },
        "nodes": nodes,
        "edges": edges,
    }


def render_audit_note(report: dict[str, Any]) -> str:
    summary = report["summary"]
    diagnostics = report.get("selection_diagnostics", {})
    lines = [
        "# A1_STRIPPED_GRAPH_AUDIT__2026_03_20__v1",
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
        "## Selection Diagnostics" if report["build_status"] == "MATERIALIZED" else "## Fail-Closed Analysis",
        "- selected_terms_present_in_a1_jargoned:",
    ])
    if diagnostics.get("selected_terms_present_in_a1_jargoned"):
        for term in diagnostics["selected_terms_present_in_a1_jargoned"]:
            lines.append(f"  - {term}")
    else:
        lines.append("  - none")
    lines.extend([
        "- selected_terms_missing_from_a1_jargoned:",
    ])
    if diagnostics.get("selected_terms_missing_from_a1_jargoned"):
        for term in diagnostics["selected_terms_missing_from_a1_jargoned"]:
            lines.append(f"  - {term}")
    else:
        lines.append("  - none")
    lines.extend([
        "- materializable_terms:",
    ])
    if diagnostics.get("materializable_terms"):
        for term in diagnostics["materializable_terms"]:
            lines.append(f"  - {term}")
    else:
        lines.append("  - none")
    lines.extend([
        "- present_terms_without_doctrine_plan:",
    ])
    if diagnostics.get("present_terms_without_doctrine_plan"):
        for item in diagnostics["present_terms_without_doctrine_plan"]:
            lines.append(f"  - {item['term']}: {item['reason']}")
    else:
        lines.append("  - none")
    lines.extend([
        "- present_terms_blocked_by_doctrine:",
    ])
    if diagnostics.get("present_terms_blocked_by_doctrine"):
        for item in diagnostics["present_terms_blocked_by_doctrine"]:
            doctrine_status = item.get("doctrine_status", "")
            lines.append(f"  - {item['term']}: {item['reason']}")
            if doctrine_status:
                lines.append(f"    - doctrine_status: {doctrine_status}")
            if item.get("matching_jargoned_ids"):
                lines.append(f"    - matching_jargoned_ids: {item['matching_jargoned_ids']}")
            if item.get("supporting_audit_refs"):
                lines.append("    - supporting_audit_refs:")
                for ref in item["supporting_audit_refs"]:
                    lines.append(f"      - {ref}")
            if item.get("supporting_source_refs"):
                lines.append("    - supporting_source_refs:")
                for ref in item["supporting_source_refs"]:
                    lines.append(f"      - {ref}")
    else:
        lines.append("  - none")
    lines.extend([
        "",
        "## Blocked Terms",
    ])
    if report["blocked_terms"]:
        for item in report["blocked_terms"]:
            lines.append(f"- {item['term']}: {item['reason']}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Selection Contract",
        f"- included_node_rule: {report['selection_contract']['included_node_rule']}",
        f"- edge_rule: {report['selection_contract']['edge_rule']}",
        "",
        "## Non-Claims",
        "- This pass does not materialize dependency topology inside A1_STRIPPED.",
        "- This pass does not promote witness-only terms into stripped-layer nodes.",
        "- This pass does not claim A1_CARTRIDGE already exists as an owner graph.",
        "",
    ])
    return "\n".join(lines)


def write_a1_stripped_graph(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_a1_stripped_graph(str(root))

    json_path = _resolve(root, OUTPUT_JSON)
    audit_note_path = _resolve(root, AUDIT_NOTE)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    audit_note_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_json(json_path)
    preserved_existing = _should_preserve_existing(existing, report)
    write_payload = existing if preserved_existing else report

    json_path.write_text(json.dumps(write_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit_text = render_audit_note(report)
    if preserved_existing:
        audit_text = "\n".join([
            "# NON_REGRESSION_PRESERVE",
            "",
            "Preserved the existing materialized A1 stripped owner surface instead of overwriting it with a thinner or fail-closed rebuild.",
            f"- attempted_node_count: {len(report.get('nodes', {}))}",
            f"- attempted_edge_count: {len(report.get('edges', []))}",
            f"- attempted_build_status: {report.get('build_status', '')}",
            f"- preserved_node_count: {len(existing.get('nodes', {}))}",
            f"- preserved_edge_count: {len(existing.get('edges', []))}",
            f"- preserved_build_status: {existing.get('build_status', '')}",
            "",
            audit_text,
        ])
    audit_note_path.write_text(audit_text, encoding="utf-8")
    return {"json_path": str(json_path), "audit_note_path": str(audit_note_path)}


if __name__ == "__main__":
    result = write_a1_stripped_graph(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
