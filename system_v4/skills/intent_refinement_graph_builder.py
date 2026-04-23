"""
intent_refinement_graph_builder.py

Materialize graph-native INTENT_SIGNAL, CONTEXT_SIGNAL, and INTENT_REFINEMENT
nodes from the current witness corpus so the live control surface has real
graph-backed intent inputs, not only raw witness entries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from system_v4.skills.a2_graph_refinery import A2GraphRefinery


WITNESS_REL_PATH = "system_v4/a2_state/witness_corpus_v1.json"
GRAPH_REL_PATH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
AUDIT_REL_PATH = "system_v4/a2_state/audit_logs/A2_INTENT_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1.md"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _existing_signal_id(
    refinery: A2GraphRefinery,
    *,
    node_type: str,
    name: str,
    description: str,
    source_label: str,
) -> str | None:
    for node in refinery.builder.pydantic_model.nodes.values():
        if node.node_type != node_type:
            continue
        if node.name != name:
            continue
        if node.description != description:
            continue
        if str(node.properties.get("source_label", "")) != source_label:
            continue
        return node.id
    return None


def _existing_refinement_id(
    refinery: A2GraphRefinery,
    *,
    title: str,
    description: str,
) -> str | None:
    for node in refinery.builder.pydantic_model.nodes.values():
        if node.node_type != "INTENT_REFINEMENT":
            continue
        if node.name == title and node.description == description:
            return node.id
    return None


def _primary_text(entry: dict[str, Any]) -> str:
    trace = entry.get("witness", {}).get("trace", [])
    if trace and isinstance(trace[0], dict):
        notes = trace[0].get("notes", [])
        if notes:
            return str(notes[0]).strip()
    return ""


def build_intent_refinement_graph(repo_root: str) -> dict[str, Any]:
    repo = Path(repo_root)
    witness_path = repo / WITNESS_REL_PATH
    audit_path = repo / AUDIT_REL_PATH
    witness_corpus = _load_json(witness_path, [])

    refinery = A2GraphRefinery(str(repo))

    raw_intent_ids: list[str] = []
    raw_context_ids: list[str] = []
    refined_ids: list[str] = []

    grouped_intents: dict[str, dict[str, list[str]]] = {}

    for idx, entry in enumerate(witness_corpus if isinstance(witness_corpus, list) else []):
        kind = entry.get("witness", {}).get("kind")
        tags = entry.get("tags", {}) or {}
        source_label = str(tags.get("source", "maker" if kind == "intent" else "system"))
        text = _primary_text(entry)
        if not text:
            continue
        witness_ref = f"WITNESS_CORPUS::{idx}"

        if kind == "intent":
            topic = str(tags.get("topic", "current_intent")).strip() or "current_intent"
            name = f"{str(tags.get('phase', 'INTENT'))}:{source_label}"
            existing = _existing_signal_id(
                refinery,
                node_type="INTENT_SIGNAL",
                name=name,
                description=text,
                source_label=source_label,
            )
            if existing:
                existing_node = refinery.builder.get_node(existing)
                merged_refs = sorted(set(list(getattr(existing_node, "witness_refs", [])) + [witness_ref]))
                if existing_node is not None and merged_refs != list(existing_node.witness_refs):
                    refinery.builder.update_node(existing, witness_refs=merged_refs)
                    refinery.checkpoint()
                node_id = existing
            else:
                node_id = refinery.record_intent_signal(
                    text,
                    source_label=source_label,
                    intent_kind=str(tags.get("phase", "INTENT")),
                    tags=[topic, str(tags.get("priority", ""))],
                    witness_refs=[witness_ref],
                )
            raw_intent_ids.append(node_id)
            grouped = grouped_intents.setdefault(topic, {"source_ids": [], "witness_refs": []})
            grouped["source_ids"].append(node_id)
            if witness_ref not in grouped["witness_refs"]:
                grouped["witness_refs"].append(witness_ref)

        if kind == "context":
            name = f"{str(tags.get('phase', 'CONTEXT'))}:{source_label}"
            existing = _existing_signal_id(
                refinery,
                node_type="CONTEXT_SIGNAL",
                name=name,
                description=text,
                source_label=source_label,
            )
            if existing:
                existing_node = refinery.builder.get_node(existing)
                merged_refs = sorted(set(list(getattr(existing_node, "witness_refs", [])) + [witness_ref]))
                if existing_node is not None and merged_refs != list(existing_node.witness_refs):
                    refinery.builder.update_node(existing, witness_refs=merged_refs)
                    refinery.checkpoint()
                node_id = existing
            else:
                node_id = refinery.record_context_signal(
                    text,
                    source_label=source_label,
                    context_kind=str(tags.get("phase", "CONTEXT")),
                    tags=[str(tags.get("topic", "")), str(tags.get("queue_status", ""))],
                    witness_refs=[witness_ref],
                )
            raw_context_ids.append(node_id)

    for topic, grouped in grouped_intents.items():
        source_ids = list(grouped.get("source_ids", []))
        source_nodes = [
            refinery.builder.get_node(node_id)
            for node_id in source_ids
            if refinery.builder.get_node(node_id) is not None
        ]
        source_texts = [node.description for node in source_nodes if getattr(node, "description", "")]
        if not source_texts:
            continue
        witness_refs = set(grouped.get("witness_refs", []))
        for node in source_nodes:
            for ref in getattr(node, "witness_refs", []):
                if ref:
                    witness_refs.add(ref)
        title = f"{topic}_intent_contract"
        refined_text = (
            f"Current derived intent for {topic.replace('_', ' ')}: "
            + " | ".join(source_texts[:3])
        )
        existing = _existing_refinement_id(
            refinery,
            title=title,
            description=refined_text,
        )
        if existing:
            existing_node = refinery.builder.get_node(existing)
            merged_refs = sorted(set(list(getattr(existing_node, "witness_refs", [])) + list(witness_refs)))
            if existing_node is not None and merged_refs != list(existing_node.witness_refs):
                refinery.builder.update_node(existing, witness_refs=merged_refs)
                refinery.checkpoint()
            refined_id = existing
        else:
            refined_id = refinery.refine_intent_signal(
                source_ids,
                refined_text,
                title=title,
                tags=[topic, "witness-derived"],
                witness_refs=sorted(witness_refs),
            )
        refined_ids.append(refined_id)

    audit_lines = [
        "# A2 Intent Refinement Graph Audit",
        "",
        f"- witness_path: `{WITNESS_REL_PATH}`",
        f"- graph_path: `{GRAPH_REL_PATH}`",
        f"- raw_intent_nodes: `{len(raw_intent_ids)}`",
        f"- raw_context_nodes: `{len(raw_context_ids)}`",
        f"- refined_intent_nodes: `{len(refined_ids)}`",
        "",
        "## Topics",
        "",
    ]
    if grouped_intents:
        audit_lines.extend(
            f"- {topic}: {len(grouped.get('source_ids', []))} source intents"
            for topic, grouped in sorted(grouped_intents.items())
        )
    else:
        audit_lines.append("- none")

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    return {
        "graph_path": GRAPH_REL_PATH,
        "audit_note_path": AUDIT_REL_PATH,
        "raw_intent_nodes": len(raw_intent_ids),
        "raw_context_nodes": len(raw_context_ids),
        "refined_intent_nodes": len(refined_ids),
    }


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    result = build_intent_refinement_graph(str(repo))
    assert "graph_path" in result
    print("PASS: intent_refinement_graph_builder self-test")
