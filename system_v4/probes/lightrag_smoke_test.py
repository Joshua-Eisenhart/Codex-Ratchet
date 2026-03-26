#!/usr/bin/env python3
"""
LightRAG Smoke Test — Build A Read-Only Retrieval Corpus
========================================================
Bounded proof that the local repo already has enough material for a useful
LightRAG sidecar corpus before any embedding or LLM step:

1. Build retrieval documents from the owner graph, evidence/history surfaces,
   and front-door QIT docs
2. Write a sidecar-only corpus manifest under work/lightrag_smoke/
3. Verify that LightRAG imports and report whether embedding config is still
   needed for actual indexing/querying

This script stays read-only relative to owner truth. It never mutates the
owner graph or A2 state.

Usage:
    python3 system_v4/probes/lightrag_smoke_test.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_RESULTS_DIR = REPO_ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"
QIT_GRAPH_JSON = REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "qit_engine_graph_v1.json"
DOC_INDEX_JSON = REPO_ROOT / "system_v4" / "a2_state" / "doc_index_v4.json"
LIGHTRAG_WORK_DIR = REPO_ROOT / "work" / "lightrag_smoke"
CORPUS_DIR = LIGHTRAG_WORK_DIR / "corpus"

QIT_DOCS = [
    REPO_ROOT / "core_docs" / "QIT_GRAPH_SYNC_README.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_SCHEMA.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_LAYER_MAPPING.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_RUNTIME_MODEL.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_SIDECAR_POLICY.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_PROMOTION_GATES.md",
    REPO_ROOT / "core_docs" / "EMPIRICAL_MATH_ROSETTA.md",
]

SELECTED_SIM_RESULTS = [
    "unified_evidence_report.json",
    "L2_eight_stages_results.json",
    "L3_operators_results.json",
    "exploratory_process_cycle_stage_matrix_results.json",
    "neg_axis6_shared_stage_matrix_results.json",
    "neg_missing_fe_stage_matrix_results.json",
    "neg_missing_operator_stage_matrix_results.json",
    "neg_native_only_stage_matrix_results.json",
    "neg_type_flatten_stage_matrix_results.json",
]


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _flatten_scalars(
    value: Any,
    prefix: str = "",
    out: list[tuple[str, str]] | None = None,
    limit: int = 40,
) -> list[tuple[str, str]]:
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(value, dict):
        for key in sorted(value):
            next_prefix = f"{prefix}.{key}" if prefix else key
            _flatten_scalars(value[key], next_prefix, out, limit)
            if len(out) >= limit:
                break
        return out
    if isinstance(value, list):
        if not value:
            out.append((prefix or "<root>", "[]"))
            return out
        if all(not isinstance(item, (dict, list)) for item in value[:5]):
            preview = ", ".join(str(item) for item in value[:5])
            if len(value) > 5:
                preview += ", ..."
            out.append((prefix or "<root>", f"[{preview}]"))
            return out
        out.append((prefix or "<root>", f"list[{len(value)}]"))
        for idx, item in enumerate(value[:3]):
            _flatten_scalars(item, f"{prefix}[{idx}]" if prefix else f"[{idx}]", out, limit)
            if len(out) >= limit:
                break
        return out
    out.append((prefix or "<root>", str(value)))
    return out


def _latest_history_report() -> Path | None:
    history_dir = SIM_RESULTS_DIR / "history"
    reports = sorted(history_dir.glob("report_*.json"))
    return reports[-1] if reports else None


def _write_corpus_doc(doc: dict[str, Any]) -> None:
    out_path = CORPUS_DIR / f"{doc['doc_id']}.txt"
    out_path.write_text(doc["text"], encoding="utf-8")


def _format_qit_graph_doc(path: Path) -> dict[str, Any] | None:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return None
    nodes = payload.get("nodes", {})
    edges = payload.get("edges", [])
    node_type_counts: dict[str, int] = {}
    rel_counts: dict[str, int] = {}
    for node in nodes.values():
        node_type = str(node.get("node_type", "?"))
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
    for edge in edges:
        rel = str(edge.get("relation", "?"))
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

    lines = [
        "# QIT Owner Graph",
        f"source_path: {path}",
        f"schema: {payload.get('schema')}",
        f"generated_utc: {payload.get('generated_utc')}",
        f"content_hash: {payload.get('content_hash')}",
        f"node_count: {len(nodes)}",
        f"edge_count: {len(edges)}",
        "",
        "## Node Types",
    ]
    for node_type, count in sorted(node_type_counts.items()):
        lines.append(f"- {node_type}: {count}")
    lines.extend(["", "## Edge Relations"])
    for rel, count in sorted(rel_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {rel}: {count}")
    lines.extend(["", "## Sample Public IDs"])
    for node in list(nodes.values())[:12]:
        lines.append(
            f"- {node.get('public_id')} | node_type={node.get('node_type')} | label={node.get('label')}"
        )
    return {
        "doc_id": "qit_owner_graph",
        "family": "owner_graph",
        "source_path": str(path),
        "text": "\n".join(lines) + "\n",
    }


def _format_doc_index_doc(path: Path) -> dict[str, Any] | None:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return None
    documents = payload.get("documents", [])
    layer_counts: dict[str, int] = {}
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        layer = str(doc.get("layer", "?"))
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    lines = [
        "# Internal Document Index",
        f"source_path: {path}",
        f"schema: {payload.get('schema')}",
        f"generated_utc: {payload.get('generated_utc')}",
        f"document_count: {payload.get('document_count')}",
        "",
        "## Layer Counts",
    ]
    for layer, count in sorted(layer_counts.items()):
        lines.append(f"- {layer}: {count}")
    lines.extend(["", "## Sample Documents"])
    for doc in documents[:20]:
        if isinstance(doc, dict):
            lines.append(f"- {doc.get('layer')} | {doc.get('path')}")
    return {
        "doc_id": "internal_doc_index",
        "family": "doc_index",
        "source_path": str(path),
        "text": "\n".join(lines) + "\n",
    }


def _format_json_surface_doc(path: Path, family: str) -> dict[str, Any] | None:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return None
    lines = [
        f"# JSON Surface: {path.stem}",
        f"source_path: {path}",
    ]
    for key in ("schema", "file", "timestamp", "generated_utc", "sim_id", "name", "purpose"):
        if key in payload:
            lines.append(f"{key}: {payload[key]}")

    summary_candidates = (
        "summary",
        "overall",
        "verdict",
        "closest_mixed_axis6",
        "by_engine_type",
        "by_loop_role",
        "by_native_operator",
    )
    for key in summary_candidates:
        if key in payload:
            lines.append("")
            lines.append(f"## {key}")
            for scalar_key, scalar_value in _flatten_scalars(payload[key], limit=24):
                lines.append(f"- {scalar_key}: {scalar_value}")

    evidence = payload.get("evidence_ledger")
    if isinstance(evidence, list) and evidence:
        lines.extend(["", f"## evidence_ledger ({len(evidence)})"])
        for item in evidence[:12]:
            if isinstance(item, dict):
                token = item.get("token_id")
                status = item.get("status")
                sim_spec = item.get("sim_spec_id")
                measured = item.get("measured_value")
                lines.append(
                    f"- token_id={token} | status={status} | sim_spec_id={sim_spec} | measured_value={measured}"
                )

    lines.extend(["", "## scalar_preview"])
    for scalar_key, scalar_value in _flatten_scalars(payload, limit=30):
        lines.append(f"- {scalar_key}: {scalar_value}")

    return {
        "doc_id": path.stem,
        "family": family,
        "source_path": str(path),
        "text": "\n".join(lines) + "\n",
    }


def _format_markdown_doc(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None
    return {
        "doc_id": path.stem.lower().replace(" ", "_"),
        "family": "qit_docs",
        "source_path": str(path),
        "text": f"# Source Document: {path.name}\nsource_path: {path}\n\n{text.rstrip()}\n",
    }


def _build_documents() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    graph_doc = _format_qit_graph_doc(QIT_GRAPH_JSON)
    if graph_doc:
        documents.append(graph_doc)

    doc_index_doc = _format_doc_index_doc(DOC_INDEX_JSON)
    if doc_index_doc:
        documents.append(doc_index_doc)

    for name in SELECTED_SIM_RESULTS:
        path = SIM_RESULTS_DIR / name
        doc = _format_json_surface_doc(path, family="evidence")
        if doc:
            documents.append(doc)

    history_path = _latest_history_report()
    if history_path:
        doc = _format_json_surface_doc(history_path, family="history")
        if doc:
            documents.append(doc)

    for path in QIT_DOCS:
        doc = _format_markdown_doc(path)
        if doc:
            documents.append(doc)

    return documents


def run_smoke_test():
    """Run the LightRAG ingestion smoke test."""
    print(f"\n{'='*60}")
    print("LightRAG SMOKE TEST")
    print(f"{'='*60}")

    # 1. Check import
    try:
        from lightrag import LightRAG
        print(f"  ✓ LightRAG imported successfully")
    except ImportError as e:
        print(f"  ✗ LightRAG import failed: {e}")
        print("    Install with: pip install lightrag-hku")
        return {"status": "IMPORT_FAILED", "error": str(e)}

    # 2. Build a bounded retrieval corpus from current repo-held surfaces
    documents = _build_documents()
    print(f"  ✓ Built {len(documents)} retrieval documents")

    # 3. Write sidecar-only corpus docs and manifest
    LIGHTRAG_WORK_DIR.mkdir(parents=True, exist_ok=True)
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for doc in documents:
        _write_corpus_doc(doc)

    manifest = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "document_count": len(documents),
        "documents": [
            {
                "doc_id": doc["doc_id"],
                "family": doc["family"],
                "source_path": doc["source_path"],
                "char_count": len(doc["text"]),
            }
            for doc in documents
        ],
    }
    manifest_path = LIGHTRAG_WORK_DIR / "corpus_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Just test document formatting worked
    total_chars = sum(len(d["text"]) for d in documents)
    sample_doc = documents[0] if documents else None

    print(f"  ✓ Total corpus size: {total_chars:,} chars across {len(documents)} documents")
    if sample_doc:
        print(f"  ✓ Sample document: {sample_doc['doc_id']}")
        print(f"    First 200 chars: {sample_doc['text'][:200]}...")
    print(f"  ✓ Corpus manifest: {manifest_path}")

    # 4. Try LightRAG init. Current package requires embedding config before
    # vector storage is usable, so this reports readiness rather than querying.
    init_success = False
    init_error = None
    try:
        rag = LightRAG(
            working_dir=str(LIGHTRAG_WORK_DIR),
        )
        init_success = True
        print(f"  ✓ LightRAG initialized (working_dir={LIGHTRAG_WORK_DIR})")
    except Exception as e:
        init_error = str(e)
        print(f"  ⚠ LightRAG init still needs embedding config: {e}")
        print("    Corpus build succeeded; indexing/querying is the remaining step.")

    # 5. Write status summary
    result = {
        "status": "READY" if init_success else "NEEDS_EMBEDDING_CONFIG",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "documents_built": len(documents),
        "total_corpus_chars": total_chars,
        "working_dir": str(LIGHTRAG_WORK_DIR),
        "corpus_manifest": str(manifest_path),
        "init_success": init_success,
        "init_error": init_error,
        "sample_document_name": sample_doc["doc_id"] if sample_doc else None,
    }

    output_path = LIGHTRAG_WORK_DIR / "smoke_test_result.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"\n  Result: {output_path}")
    print(f"  Status: {result['status']}")

    return result


if __name__ == "__main__":
    run_smoke_test()
