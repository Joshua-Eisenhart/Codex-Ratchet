#!/usr/bin/env python3
"""
qit_retrieval_sidecar.py

Bounded QIT retrieval seam over graph-adjacent docs and evidence.

This is intentionally not owner memory and not a proof surface. It builds a
small corpus from QIT docs, stack/evidence reports, and selected SIM evidence,
then runs a lexical fallback query so the retrieval lane is useful before
embedding-backed LightRAG indexing is configured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
SIM_RESULTS_DIR = REPO_ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"
WORK_DIR = REPO_ROOT / "work" / "qit_retrieval_sidecar"
CORPUS_DIR = WORK_DIR / "corpus"
CORPUS_MANIFEST = WORK_DIR / "corpus_manifest.json"
REPORT_JSON = AUDIT_DIR / "QIT_RETRIEVAL_SIDECAR__CURRENT__v1.json"
REPORT_MD = AUDIT_DIR / "QIT_RETRIEVAL_SIDECAR__CURRENT__v1.md"

DEFAULT_QUERY = (
    "Which QIT runtime evidence surfaces are live now, and how do axis 6, "
    "missing Fe, and type flatten negatives map into the current graph lane?"
)

QIT_DOCS = [
    REPO_ROOT / "core_docs" / "QIT_GRAPH_SYNC_README.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_SCHEMA.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_RUNTIME_MODEL.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_LAYER_MAPPING.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_SIDECAR_POLICY.md",
    REPO_ROOT / "core_docs" / "QIT_GRAPH_PROMOTION_GATES.md",
]

AUDIT_DOCS = [
    AUDIT_DIR / "QIT_GRAPH_STACK_STATUS__CURRENT__v1.md",
    AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md",
    AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.md",
]

AUDIT_JSONS = [
    AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json",
    AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json",
]

SIM_JSONS = [
    SIM_RESULTS_DIR / "neg_axis6_shared_stage_matrix_results.json",
    SIM_RESULTS_DIR / "neg_missing_fe_stage_matrix_results.json",
    SIM_RESULTS_DIR / "neg_missing_operator_stage_matrix_results.json",
    SIM_RESULTS_DIR / "neg_native_only_stage_matrix_results.json",
    SIM_RESULTS_DIR / "neg_type_flatten_stage_matrix_results.json",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain(paths: list[Path] | None = None) -> list[str]:
    cmd = ["git", "status", "--short"]
    if paths:
        cmd.append("--")
        cmd.extend(str(path) for path in paths)
    try:
        output = subprocess.check_output(
            cmd,
            cwd=str(REPO_ROOT),
            text=True,
        )
    except Exception:
        return []
    return [line.rstrip() for line in output.splitlines() if line.strip()]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _tokenize(text: str) -> list[str]:
    raw_tokens = re.findall(r"[a-z0-9_:+.-]+", text.lower())
    expanded: list[str] = []
    for token in raw_tokens:
        expanded.append(token)
        for piece in re.split(r"[:_.+-]+", token):
            if piece and piece != token:
                expanded.append(piece)
    return expanded


def _snippet(text: str, query_terms: list[str], width: int = 240) -> str:
    text = " ".join(text.split())
    if not text:
        return ""
    lower = text.lower()
    best_idx = 0
    for term in query_terms:
        idx = lower.find(term)
        if idx >= 0:
            best_idx = idx
            break
    start = max(0, best_idx - width // 3)
    end = min(len(text), start + width)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def _format_markdown_doc(path: Path, family: str) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None
    return {
        "doc_id": path.stem.lower().replace(" ", "_"),
        "family": family,
        "source_path": str(path),
        "source_refs": [str(path)],
        "authoritative": False,
        "owner_input_read_only": family in {"qit_docs", "audit_reports"},
        "text": f"# Source Document: {path.name}\nsource_path: {path}\n\n{text.rstrip()}\n",
    }


def _flatten_scalars(value: Any, prefix: str = "", limit: int = 30, out: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(value, dict):
        for key in sorted(value):
            next_prefix = f"{prefix}.{key}" if prefix else key
            _flatten_scalars(value[key], next_prefix, limit, out)
            if len(out) >= limit:
                break
        return out
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value[:5]):
            preview = ", ".join(str(item) for item in value[:5])
            out.append((prefix or "<root>", f"[{preview}]"))
            return out
        out.append((prefix or "<root>", f"list[{len(value)}]"))
        for idx, item in enumerate(value[:3]):
            _flatten_scalars(item, f"{prefix}[{idx}]" if prefix else f"[{idx}]", limit, out)
            if len(out) >= limit:
                break
        return out
    out.append((prefix or "<root>", str(value)))
    return out


def _format_sim_doc(path: Path) -> dict[str, Any] | None:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return None
    lines = [
        f"# QIT SIM Evidence: {path.stem}",
        f"source_path: {path}",
        f"schema: {payload.get('schema', '')}",
        f"timestamp: {payload.get('timestamp', '')}",
        f"file: {payload.get('file', '')}",
    ]
    for key in (
        "overall",
        "control_equivalence",
        "closest_mixed_axis6",
        "closest_missing_operator",
        "native_only_collapse",
        "flat_type_weighting",
        "by_engine_type",
        "by_loop_role",
        "by_native_operator",
    ):
        if key in payload:
            lines.extend(["", f"## {key}"])
            for scalar_key, scalar_value in _flatten_scalars(payload[key], limit=20):
                lines.append(f"- {scalar_key}: {scalar_value}")
    evidence = payload.get("evidence_ledger", [])
    if isinstance(evidence, list) and evidence:
        lines.extend(["", f"## evidence_ledger ({len(evidence)})"])
        for item in evidence:
            if isinstance(item, dict):
                lines.append(
                    "- token_id={token_id} | status={status} | sim_spec_id={sim_spec_id} | measured_value={measured_value}".format(
                        token_id=item.get("token_id"),
                        status=item.get("status"),
                        sim_spec_id=item.get("sim_spec_id"),
                        measured_value=item.get("measured_value"),
                    )
                )
    return {
        "doc_id": path.stem,
        "family": "sim_evidence",
        "source_path": str(path),
        "source_refs": [str(path)],
        "authoritative": False,
        "owner_input_read_only": False,
        "text": "\n".join(lines) + "\n",
    }


def _dedupe_refs(refs: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for ref in refs:
        if not ref or ref in seen:
            continue
        seen.add(ref)
        deduped.append(ref)
    return deduped


def _format_runtime_bridge_docs(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return []

    docs: list[dict[str, Any]] = []
    owner_snapshot = payload.get("owner_snapshot", {})
    summary = payload.get("summary", {})
    runtime_samples = payload.get("runtime_samples", [])
    sim_packets = payload.get("sim_evidence_packets", [])

    summary_lines = [
        "# Structured QIT Runtime Evidence Bridge",
        f"source_path: {path}",
        f"schema: {payload.get('schema', '')}",
        f"audit_only: {payload.get('audit_only')}",
        f"nonoperative: {payload.get('nonoperative')}",
        f"do_not_promote: {payload.get('do_not_promote')}",
        f"owner_graph_role: {payload.get('owner_graph_role', '')}",
        f"persistence_policy: {payload.get('persistence_policy', '')}",
        f"runtime_capture_mode: {payload.get('runtime_capture_mode', '')}",
        f"live_runtime_capture: {payload.get('live_runtime_capture')}",
        f"owner_content_hash: {owner_snapshot.get('qit_graph_content_hash', '')}",
        f"runtime_sample_count: {summary.get('runtime_sample_count')}",
        f"sim_packet_count: {summary.get('sim_packet_count')}",
        f"complete_mappings: {summary.get('complete_mappings')}",
        f"partial_mappings: {summary.get('partial_mappings')}",
        f"resolved_owner_links: {summary.get('resolved_owner_links')}",
        f"unresolved_owner_links: {summary.get('unresolved_owner_links')}",
    ]
    docs.append(
        {
            "doc_id": "qit_runtime_evidence_bridge_structured",
            "family": "audit_reports",
            "source_path": str(path),
            "source_refs": _dedupe_refs(
                [
                    str(path),
                    owner_snapshot.get("qit_graph_json", ""),
                    owner_snapshot.get("qit_graph_content_hash", ""),
                ]
            ),
            "authoritative": False,
            "owner_input_read_only": True,
            "text": "\n".join(summary_lines) + "\n",
        }
    )

    for sample in runtime_samples:
        history_summary = sample.get("history_summary", {})
        refs = _dedupe_refs(
            [
                str(path),
                sample.get("run_id", ""),
                sample.get("engine_public_id", ""),
                history_summary.get("first_step_public_id", ""),
                history_summary.get("last_step_public_id", ""),
            ]
        )
        lines = [
            f"# Runtime Sample: {sample.get('run_id', '')}",
            f"source_path: {path}",
            f"run_id: {sample.get('run_id', '')}",
            f"engine_public_id: {sample.get('engine_public_id', '')}",
            f"engine_type: {sample.get('engine_type', '')}",
            f"sample_kind: {sample.get('sample_kind', '')}",
            f"runtime_slice_schema: {sample.get('runtime_slice_schema', '')}",
            f"persistence_policy: {sample.get('persistence_policy', '')}",
            f"total_steps: {history_summary.get('total_steps')}",
            f"macro_stages_completed: {history_summary.get('macro_stages_completed')}",
            f"first_step_public_id: {history_summary.get('first_step_public_id', '')}",
            f"last_step_public_id: {history_summary.get('last_step_public_id', '')}",
        ]
        overlay = sample.get("overlay", {})
        flattened_overlay = _flatten_scalars(overlay, prefix="overlay", limit=12)
        if flattened_overlay:
            lines.extend(["", "## overlay"])
            lines.extend(f"- {key}: {value}" for key, value in flattened_overlay)
        docs.append(
            {
                "doc_id": sample.get("run_id", "").replace("::", "__"),
                "family": "runtime_bridge",
                "source_path": str(path),
                "source_refs": refs,
                "authoritative": False,
                "owner_input_read_only": True,
                "text": "\n".join(lines) + "\n",
            }
        )

    for packet in sim_packets:
        resolved_links = packet.get("resolved_links", [])
        refs = _dedupe_refs(
            [
                str(path),
                packet.get("result_path", ""),
                packet.get("neg_witness_public_id", ""),
                *packet.get("target_public_ids", []),
                *[link.get("public_id", "") for link in resolved_links if isinstance(link, dict)],
            ]
        )
        lines = [
            f"# Runtime Bridge SIM Mapping: {packet.get('result_file', '')}",
            f"source_path: {path}",
            f"result_path: {packet.get('result_path', '')}",
            f"status: {packet.get('status', '')}",
            f"schema: {packet.get('schema', '')}",
            f"timestamp: {packet.get('timestamp', '')}",
            f"neg_witness_public_id: {packet.get('neg_witness_public_id', '')}",
            f"target_public_ids: {', '.join(packet.get('target_public_ids', []))}",
            f"unresolved_links: {', '.join(packet.get('unresolved_links', []))}",
        ]
        if resolved_links:
            lines.extend(["", "## resolved_links"])
            for link in resolved_links:
                if isinstance(link, dict):
                    lines.append(
                        "- public_id={public_id} | node_type={node_type} | label={label}".format(
                            public_id=link.get("public_id", ""),
                            node_type=link.get("node_type", ""),
                            label=link.get("label", ""),
                        )
                    )
        summary_excerpt = packet.get("summary_excerpt", {})
        if isinstance(summary_excerpt, dict) and summary_excerpt:
            lines.extend(["", "## summary_excerpt"])
            for scalar_key, scalar_value in _flatten_scalars(summary_excerpt, limit=20):
                lines.append(f"- {scalar_key}: {scalar_value}")
        evidence_ledger = packet.get("evidence_ledger", [])
        if isinstance(evidence_ledger, list) and evidence_ledger:
            lines.extend(["", f"## evidence_ledger ({len(evidence_ledger)})"])
            for item in evidence_ledger[:10]:
                if isinstance(item, dict):
                    lines.append(
                        "- token_id={token_id} | status={status} | sim_spec_id={sim_spec_id} | measured_value={measured_value}".format(
                            token_id=item.get("token_id"),
                            status=item.get("status"),
                            sim_spec_id=item.get("sim_spec_id"),
                            measured_value=item.get("measured_value"),
                        )
                    )
        docs.append(
            {
                "doc_id": f"runtime_bridge__{Path(packet.get('result_file', 'unknown')).stem}",
                "family": "runtime_bridge",
                "source_path": str(path),
                "source_refs": refs,
                "authoritative": False,
                "owner_input_read_only": True,
                "text": "\n".join(lines) + "\n",
            }
        )

    return docs


def _format_hopf_weyl_docs(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return []

    docs: list[dict[str, Any]] = []
    owner_snapshot = payload.get("owner_snapshot", {})
    carrier = payload.get("owner_carrier_evidence", {})
    runtime_bridge = payload.get("runtime_bridge_alignment", {})
    readiness = payload.get("weyl_projection_readiness", {})
    negatives = payload.get("relevant_negative_evidence", {})

    summary_lines = [
        "# Structured Hopf/Weyl Carrier Map",
        f"source_path: {path}",
        "query_anchors: hopf, weyl, torus, chirality, clifford, inner, outer, fiber, base, type1, type2",
        f"schema: {payload.get('schema', '')}",
        f"status: {payload.get('status', '')}",
        f"audit_only: {payload.get('sidecar_boundary', {}).get('audit_only')}",
        f"nonoperative: {payload.get('sidecar_boundary', {}).get('nonoperative')}",
        f"do_not_promote: {payload.get('sidecar_boundary', {}).get('do_not_promote')}",
        f"owner_content_hash: {owner_snapshot.get('qit_graph_content_hash', '')}",
        f"carrier_assignment_scope: {carrier.get('carrier_assignment_scope', '')}",
        f"stage_on_torus_edge_count: {carrier.get('stage_on_torus_edge_count', '')}",
        f"runtime_bridge_status: {runtime_bridge.get('status', '')}",
        f"runtime_bridge_owner_hash_match: {runtime_bridge.get('owner_content_hash_matches_runtime_bridge')}",
        f"weyl_projection_status: {readiness.get('projection_status', '')}",
        f"weyl_branch_nodes_present: {readiness.get('weyl_branch_nodes_present')}",
        f"chirality_coupling_edge_present: {readiness.get('chirality_coupling_edge_present')}",
        f"negative_evidence_total: {negatives.get('total', 0)}",
    ]
    docs.append(
        {
            "doc_id": "qit_hopf_weyl_projection_structured",
            "family": "audit_reports",
            "source_path": str(path),
            "source_refs": _dedupe_refs(
                [
                    str(path),
                    owner_snapshot.get("qit_graph_json", ""),
                    runtime_bridge.get("runtime_bridge_json", ""),
                    owner_snapshot.get("qit_graph_content_hash", ""),
                ]
            ),
            "authoritative": False,
            "owner_input_read_only": True,
            "text": "\n".join(summary_lines) + "\n",
        }
    )

    for torus in carrier.get("torus_carriers", []):
        torus_public_id = torus.get("torus_public_id", "")
        refs = _dedupe_refs(
            [
                str(path),
                torus_public_id,
                *torus.get("stage_public_ids", []),
                *torus.get("engine_public_ids", []),
                runtime_bridge.get("runtime_bridge_json", ""),
                owner_snapshot.get("qit_graph_content_hash", ""),
            ]
        )
        lines = [
            f"# Hopf Carrier: {torus_public_id}",
            f"source_path: {path}",
            "query_anchors: hopf torus carrier clifford fiber base chirality stage runtime alignment",
            f"torus_public_id: {torus_public_id}",
            f"label: {torus.get('label', '')}",
            f"nesting_rank: {torus.get('nesting_rank')}",
            f"stage_count: {torus.get('stage_count')}",
            f"engine_public_ids: {', '.join(torus.get('engine_public_ids', []))}",
            f"stage_public_ids: {', '.join(torus.get('stage_public_ids', []))}",
            f"owner_content_hash: {owner_snapshot.get('qit_graph_content_hash', '')}",
        ]
        docs.append(
            {
                "doc_id": f"hopf_carrier__{torus_public_id.split('::')[-1]}",
                "family": "audit_reports",
                "source_path": str(path),
                "source_refs": refs,
                "authoritative": False,
                "owner_input_read_only": True,
                "text": "\n".join(lines) + "\n",
            }
        )

    for sample in runtime_bridge.get("engine_sample_refs", []):
        engine_public_id = sample.get("engine_public_id", "")
        refs = _dedupe_refs(
            [
                str(path),
                engine_public_id,
                sample.get("first_step_public_id", ""),
                sample.get("last_step_public_id", ""),
                runtime_bridge.get("runtime_bridge_json", ""),
                owner_snapshot.get("qit_graph_content_hash", ""),
            ]
        )
        lines = [
            f"# Hopf/Weyl Runtime Alignment: {engine_public_id}",
            f"source_path: {path}",
            "query_anchors: hopf weyl chirality runtime bridge type1 type2 engine torus",
            f"engine_public_id: {engine_public_id}",
            f"first_step_public_id: {sample.get('first_step_public_id', '')}",
            f"last_step_public_id: {sample.get('last_step_public_id', '')}",
            f"runtime_bridge_json_path: {runtime_bridge.get('runtime_bridge_json', '')}",
            f"owner_content_hash: {owner_snapshot.get('qit_graph_content_hash', '')}",
            f"weyl_projection_status: {readiness.get('projection_status', '')}",
        ]
        docs.append(
            {
                "doc_id": f"hopf_runtime_alignment__{engine_public_id.split('::')[-1]}",
                "family": "audit_reports",
                "source_path": str(path),
                "source_refs": refs,
                "authoritative": False,
                "owner_input_read_only": True,
                "text": "\n".join(lines) + "\n",
            }
        )

    return docs


def _build_corpus_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for path in QIT_DOCS:
        doc = _format_markdown_doc(path, "qit_docs")
        if doc:
            docs.append(doc)
    for path in AUDIT_DOCS:
        doc = _format_markdown_doc(path, "audit_reports")
        if doc:
            docs.append(doc)
    for path in AUDIT_JSONS:
        if path.name == "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json":
            docs.extend(_format_runtime_bridge_docs(path))
        elif path.name == "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json":
            docs.extend(_format_hopf_weyl_docs(path))
    for path in SIM_JSONS:
        doc = _format_sim_doc(path)
        if doc:
            docs.append(doc)
    return docs


def _write_corpus(docs: list[dict[str, Any]]) -> dict[str, Any]:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_docs: list[dict[str, Any]] = []
    for doc in docs:
        out_path = CORPUS_DIR / f"{doc['doc_id']}.txt"
        out_path.write_text(doc["text"], encoding="utf-8")
        manifest_docs.append(
            {
                "doc_id": doc["doc_id"],
                "family": doc["family"],
                "source_path": doc["source_path"],
                "corpus_path": str(out_path),
                "char_count": len(doc["text"]),
                "authoritative": doc["authoritative"],
                "owner_input_read_only": doc["owner_input_read_only"],
                "source_refs": doc.get("source_refs", []),
            }
        )
    manifest = {
        "schema": "QIT_RETRIEVAL_CORPUS_v1",
        "generated_utc": _utc_iso(),
        "document_count": len(manifest_docs),
        "documents": manifest_docs,
    }
    _write_json(CORPUS_MANIFEST, manifest)
    return manifest


def _score_doc(doc: dict[str, Any], query_terms: list[str]) -> tuple[float, float]:
    if not query_terms:
        return 0.0, 0.0
    text = doc["text"]
    doc_terms = _tokenize(text)
    if not doc_terms:
        return 0.0, 0.0
    doc_set = set(doc_terms)
    overlap = sum(1 for term in query_terms if term in doc_set)
    density = overlap / max(len(set(query_terms)), 1)
    phrase_bonus = 0.0
    joined = " ".join(query_terms[:4])
    if joined and joined in text.lower():
        phrase_bonus += 0.5
    family = doc.get("family", "")
    precision_bonus = 0.0
    if family == "runtime_bridge":
        precision_bonus = 0.25
    elif family == "sim_evidence":
        precision_bonus = 0.15
    elif family == "audit_reports":
        precision_bonus = 0.05
    doc_id = doc.get("doc_id", "")
    hopf_query = any(term in {"hopf", "weyl", "torus", "chirality", "clifford", "fiber", "base"} for term in query_terms)
    if hopf_query and (
        doc_id.startswith("hopf_")
        or doc_id.startswith("qit_hopf_weyl_")
        or "hopf" in doc_id
        or "weyl" in doc_id
    ):
        precision_bonus += 0.3
    type_query = any(term in {"type1", "type2", "deductive", "inductive"} for term in query_terms)
    if type_query and ("hopf_runtime_alignment__" in doc_id or "qit_hopf_weyl_projection_structured" == doc_id):
        precision_bonus += 0.15
    ref_bonus = 0.0
    source_refs = doc.get("source_refs", [])
    if source_refs:
        ref_terms = set(_tokenize(" ".join(source_refs)))
        ref_overlap = sum(1 for term in query_terms if term in ref_terms)
        ref_bonus = min(ref_overlap, 4) * 0.08
    return float(density + phrase_bonus + math.log1p(overlap) * 0.1 + precision_bonus + ref_bonus), precision_bonus + ref_bonus


def build_qit_retrieval_sidecar(query: str) -> dict[str, Any]:
    docs = _build_corpus_documents()
    manifest = _write_corpus(docs)
    query_terms = _tokenize(query)
    script_path = Path(__file__).resolve()

    ranked: list[dict[str, Any]] = []
    for doc in docs:
        score, precision_bonus = _score_doc(doc, query_terms)
        if score <= 0.0:
            continue
        ranked.append(
            {
                "doc_id": doc["doc_id"],
                "family": doc["family"],
                "source_path": doc["source_path"],
                "score": round(score, 4),
                "precision_bonus": round(precision_bonus, 4),
                "authoritative": doc["authoritative"],
                "owner_input_read_only": doc["owner_input_read_only"],
                "source_refs": doc.get("source_refs", []),
                "snippet": _snippet(doc["text"], query_terms),
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["doc_id"]))
    top_hits = ranked[:8]

    return {
        "schema": "QIT_RETRIEVAL_SIDECAR_v1",
        "generated_utc": _utc_iso(),
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "owner_graph_role": "read_only_reference_only",
        "report_surface": {
            "surface_class": "tracked_current_workspace_report",
            "represents": (
                "current workspace retrieval-sidecar state at generation time; may differ from the last "
                "committed snapshot until tracked CURRENT artifacts are committed"
            ),
            "tracked_report_files": [
                str(REPORT_JSON),
                str(REPORT_MD),
            ],
            "tracked_report_files_dirty_before_generation": _git_status_porcelain([REPORT_JSON, REPORT_MD]),
            "script_path": str(script_path),
            "script_sha256": _sha256_path(script_path),
            "git_sha": _git_sha(),
        },
        "mode": "lexical_fallback_only",
        "retrieval_role": "context_only_non_authoritative",
        "allow_owner_writes": False,
        "allow_proof_claims": False,
        "embedding_backed_query": False,
        "embedding_backed_query_blocker": "LightRAG embedding_func not configured",
        "query": query,
        "query_terms": query_terms,
        "corpus_manifest_path": str(CORPUS_MANIFEST),
        "document_count": manifest["document_count"],
        "top_hits": top_hits,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    surface = report["report_surface"]
    hit_lines = "\n".join(
        f"- `{hit['doc_id']}` ({hit['family']}, score={hit['score']}, precision_bonus={hit.get('precision_bonus', 0.0)}): {hit['snippet']}"
        + (
            f" | refs: {', '.join(f'`{ref}`' for ref in hit.get('source_refs', [])[:5])}"
            if hit.get("source_refs")
            else ""
        )
        for hit in report["top_hits"]
    )
    return "\n".join(
        [
            "# QIT Retrieval Sidecar",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- nonoperative: `{report['nonoperative']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            f"- owner_graph_role: `{report['owner_graph_role']}`",
            f"- mode: `{report['mode']}`",
            f"- retrieval_role: `{report['retrieval_role']}`",
            f"- allow_owner_writes: `{report['allow_owner_writes']}`",
            f"- allow_proof_claims: `{report['allow_proof_claims']}`",
            f"- embedding_backed_query: `{report['embedding_backed_query']}`",
            f"- embedding_backed_query_blocker: `{report['embedding_backed_query_blocker']}`",
            f"- query: `{report['query']}`",
            f"- corpus_manifest_path: `{report['corpus_manifest_path']}`",
            f"- document_count: `{report['document_count']}`",
            "",
            "## Report Surface",
            f"- surface_class: `{surface['surface_class']}`",
            f"- represents: `{surface['represents']}`",
            f"- git_sha: `{surface['git_sha']}`",
            "",
            "## Top Hits",
            hit_lines or "- none",
            "",
            "## Boundary",
            "- This retrieval surface is sidecar-only and non-authoritative.",
            "- It may read graph-adjacent docs and evidence, but it does not write owner truth.",
            "- Retrieved text is context, not proof.",
            "- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.",
        ]
    )


def write_qit_retrieval_sidecar(query: str) -> dict[str, Any]:
    report = build_qit_retrieval_sidecar(query)
    _write_json(REPORT_JSON, report)
    _write_text(REPORT_MD, _render_markdown(report))
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded QIT retrieval sidecar with lexical fallback.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Query to run over the bounded QIT retrieval corpus.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = write_qit_retrieval_sidecar(args.query)
    print("QIT retrieval sidecar written:")
    print(f"  JSON: {REPORT_JSON}")
    print(f"  MD:   {REPORT_MD}")
    print(f"  docs: {report['document_count']}")
    print(f"  hits: {len(report['top_hits'])}")


if __name__ == "__main__":
    main()
