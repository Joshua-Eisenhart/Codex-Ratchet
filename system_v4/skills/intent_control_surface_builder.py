"""
intent_control_surface_builder.py

Build one bounded derived A2 intent-control surface from the current witness
corpus plus refinery intent/context nodes. This is an active control packet,
not doctrine and not lower-loop truth.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any

from system_v4.skills.intent_runtime_policy import build_runtime_policy


SCHEMA = "A2_INTENT_CONTROL_SURFACE_v1"
SURFACE_REL_PATH = "system_v4/a2_state/A2_INTENT_CONTROL__CURRENT__v1.json"
AUDIT_REL_PATH = "system_v4/a2_state/audit_logs/A2_INTENT_CONTROL_BUILD_AUDIT__2026_03_20__v1.md"
PROVENANCE_OVERLAY_REL_PATH = (
    "system_v4/a2_state/audit_logs/STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
)
WITNESS_REL_PATH = "system_v4/a2_state/witness_corpus_v1.json"
GRAPH_REL_PATH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "onto",
    "your", "their", "them", "they", "have", "will", "would", "should",
    "must", "need", "needs", "being", "been", "also", "very", "more",
    "most", "than", "then", "just", "only", "still", "make", "makes",
    "made", "thing", "things", "whole", "point", "goal", "goals",
    "are", "all", "not", "self", "stuff", "writing",
    "maker", "system", "user", "queue", "startup", "batch", "phase",
    "live", "current", "first", "class", "kind", "types", "type",
    "record", "records", "graph", "graphs", "witness", "witnesses",
    "runtime", "control", "surface", "surfaces", "derived", "refined",
    "refinement", "refine", "preserve", "preserved", "preserving",
}
QUALITY_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "onto",
    "your", "their", "them", "they", "have", "will", "would", "should",
    "must", "need", "needs", "being", "been", "also", "very", "more",
    "most", "than", "then", "just", "only", "still", "make", "makes",
    "made", "thing", "things", "whole", "point", "goal", "goals",
    "are", "all", "not", "self", "stuff", "writing", "maker", "user",
    "queue", "startup", "batch", "phase", "live", "current", "first",
    "class", "kind", "types", "type", "record", "records", "witness",
    "witnesses", "surface", "surfaces", "derived", "refined", "refinement",
}
STEERING_BLOCKLIST = QUALITY_STOPWORDS | {
    "its", "saved", "saving", "extracting", "design", "sources", "source",
    "intentions", "continuously", "lev",
}
TOPIC_COMPONENT_BLOCKLIST = {
    "intent",
    "graph",
    "graphs",
    "skill",
    "skills",
    "source",
    "sources",
    "witness",
    "derived",
    "refinement",
    "system",
}
CLUSTER_META_TERMS = {
    "a1",
    "a2",
    "a1_state",
    "a2_state",
    "a2_state_v3",
    "archive",
    "archived",
    "audit",
    "audit_tmp",
    "batch",
    "batch_ingest",
    "bounded",
    "claims",
    "current",
    "default",
    "doc",
    "docs",
    "engineering",
    "file",
    "files",
    "final",
    "final_sweep",
    "mass",
    "mass_intake",
    "md",
    "noncanonical",
    "runbook",
    "sim",
    "simpy",
    "simson",
    "state",
    "status",
    "tmp",
    "truth",
    "work",
    "work_archive",
}
EXECUTABLE_CONCEPT_NODE_TYPES = {"EXTRACTED_CONCEPT", "REFINED_CONCEPT"}
EXECUTABLE_MAX_CONCEPT_HIT_RATE = 0.25
EXECUTABLE_HIGH_INTAKE_LAYER = "A2_HIGH_INTAKE"
EXECUTABLE_ANCHOR_LAYERS = {"A2_2_CANDIDATE", "A2_MID_REFINEMENT", "A1_STRIPPED"}
EXECUTABLE_MAX_HIGH_INTAKE_SHARE = 0.9
EXECUTABLE_MIN_ANCHORED_SUPPORT = 6
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "": 9}


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _primary_text(entry: dict[str, Any]) -> str:
    trace = entry.get("witness", {}).get("trace", [])
    if trace and isinstance(trace[0], dict):
        notes = trace[0].get("notes", [])
        if notes:
            return str(notes[0]).strip()
    return ""


def _tokenize(text: str) -> list[str]:
    toks = re.findall(r"[a-z][a-z0-9_]{2,}", text.lower())
    return [tok for tok in toks if tok not in STOPWORDS]


def _tokenize_quality(text: str) -> list[str]:
    toks = re.findall(r"[a-z][a-z0-9_]{2,}", text.lower())
    return [tok for tok in toks if tok not in QUALITY_STOPWORDS]


def _underscore_token_parts(text: str) -> list[str]:
    parts: list[str] = []
    for tok in re.findall(r"[a-z][a-z0-9_]{2,}", text.lower()):
        if "_" not in tok:
            continue
        for part in tok.split("_"):
            if len(part) >= 3:
                parts.append(part)
    return parts


def _cluster_family_terms(source_labels: list[str], *, term: str) -> list[str]:
    family: set[str] = set()
    for label in source_labels:
        raw = str(label).split(":", 1)[-1]
        for part in raw.split("_"):
            if len(part) < 3 or part == term:
                continue
            family.add(part)
    return sorted(family)


def _cluster_semantic_tokens(
    node: dict[str, Any],
    *,
    excluded_terms: set[str],
) -> set[str]:
    text = " ".join(
        [
            str(node.get("name", "")),
            str(node.get("description", "")),
            " ".join(str(tag) for tag in (node.get("tags", []) or [])),
        ]
    ).lower()
    tokens = set(re.findall(r"[a-z][a-z0-9_]{2,}", text))
    return {
        tok
        for tok in tokens
        if tok not in STOPWORDS
        and tok not in QUALITY_STOPWORDS
        and tok not in CLUSTER_META_TERMS
        and tok not in excluded_terms
    }


def _cluster_semantic_tags(
    node: dict[str, Any],
    *,
    excluded_terms: set[str],
) -> set[str]:
    tags = {
        str(tag).lower()
        for tag in (node.get("tags", []) or [])
        if str(tag).strip()
    }
    return {
        tag
        for tag in tags
        if tag not in CLUSTER_META_TERMS
        and tag not in excluded_terms
        and tag not in STOPWORDS
        and tag not in QUALITY_STOPWORDS
    }


def _concept_hit_ids_for_terms(
    concept_corpora: dict[str, str],
    terms: list[str],
) -> set[str]:
    normalized_terms = [str(term).lower() for term in terms if str(term).strip()]
    if not normalized_terms:
        return set()
    return {
        nid
        for nid, corpus in concept_corpora.items()
        if any(term in corpus for term in normalized_terms)
    }


def _sample_concepts(
    node_ids: set[str],
    concept_nodes: dict[str, dict[str, Any]],
    *,
    limit: int = 5,
) -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    for nid in sorted(node_ids)[:limit]:
        node = concept_nodes.get(nid, {})
        samples.append(
            {
                "node_id": nid,
                "name": str(node.get("name", "")),
                "node_type": str(node.get("node_type", "")),
            }
        )
    return samples


def _node_family_label(node_id: str) -> str:
    parts = node_id.split("::")
    if len(parts) >= 2 and parts[0].startswith("A2_"):
        return "::".join(parts[:2])
    return parts[0] if parts else node_id


def _distribution_rows(counter: Counter[str], *, total: int, limit: int = 5) -> list[dict[str, Any]]:
    if total <= 0:
        return []
    return [
        {
            "label": label,
            "count": count,
            "share": round(count / total, 6),
        }
        for label, count in counter.most_common(limit)
    ]


def _distribution_share(rows: list[dict[str, Any]], predicate: str | None = None, *, exact: str | None = None) -> float:
    total = 0.0
    for row in rows:
        label = str(row.get("label", ""))
        if exact is not None and label == exact:
            total += float(row.get("share", 0.0))
        elif predicate is not None and label.endswith(predicate):
            total += float(row.get("share", 0.0))
    return round(total, 6)


def _build_stripped_provenance_overlay_archive(
    *,
    payload: dict[str, Any],
    graph_nodes: dict[str, dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    def _clean_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()

    annotation = dict(
        (payload.get("self_audit", {}) or {}).get(
            "stripped_provenance_annotation_admission", {}
        )
        or {}
    )
    precondition = dict(
        (payload.get("self_audit", {}) or {}).get(
            "stripped_provenance_backfill_precondition", {}
        )
        or {}
    )
    target_node_id = _clean_text(annotation.get("target_node_id", ""))
    target_node = graph_nodes.get(target_node_id, {}) or {}
    basis_node_ids = [
        nid.strip()
        for nid in (annotation.get("basis_node_ids", []) or [])
        if isinstance(nid, str) and nid.strip()
    ]

    source_doc_ids: list[str] = []
    if basis_node_ids:
        strongest_donor_id = basis_node_ids[-1]
        for edge in graph_edges:
            if str(edge.get("target_id", "")) != strongest_donor_id:
                continue
            if str(edge.get("relation", "")) != "SOURCE_MAP_PASS":
                continue
            source_id = str(edge.get("source_id", "")).strip()
            if source_id and source_id not in source_doc_ids:
                source_doc_ids.append(source_id)

    primary_chain: list[dict[str, Any]] = []
    if target_node_id:
        primary_chain.append(
            {
                "node_id": target_node_id,
                "role": "target_stripped_node",
                "layer": _clean_text(target_node.get("layer", "")),
                "node_type": _clean_text(target_node.get("node_type", "")),
                "name": _clean_text(target_node.get("name", "")),
            }
        )
    if basis_node_ids:
        strongest_donor_id = basis_node_ids[-1]
        strongest_donor = graph_nodes.get(strongest_donor_id, {}) or {}
        primary_chain.append(
            {
                "node_id": strongest_donor_id,
                "role": "strongest_semantic_donor",
                "layer": _clean_text(strongest_donor.get("layer", "")),
                "node_type": _clean_text(strongest_donor.get("node_type", "")),
                "name": _clean_text(strongest_donor.get("name", "")),
                "via_relations": ["STRIPPED_FROM", "ROSETTA_MAP"],
            }
        )
    if source_doc_ids:
        source_doc_id = source_doc_ids[0]
        source_doc = graph_nodes.get(source_doc_id, {}) or {}
        primary_chain.append(
            {
                "node_id": source_doc_id,
                "role": "source_document_ancestor",
                "layer": _clean_text(source_doc.get("layer", "")),
                "node_type": _clean_text(source_doc.get("node_type", "")),
                "name": _clean_text(source_doc.get("name", "")),
                "via_relations": ["SOURCE_MAP_PASS"],
            }
        )

    secondary_context: list[dict[str, Any]] = []
    for node_id in basis_node_ids[:-1]:
        node = graph_nodes.get(node_id, {}) or {}
        secondary_context.append(
            {
                "node_id": node_id,
                "layer": _clean_text(node.get("layer", "")),
                "node_type": _clean_text(node.get("node_type", "")),
                "name": _clean_text(node.get("name", "")),
                "role": "secondary_context_only",
            }
        )

    return {
        "schema": "A2_STRIPPED_PROVENANCE_OVERLAY_v1",
        "overlay_id": f"STRIPPED_PROVENANCE_OVERLAY__{_utc_iso()}",
        "classification": {
            "surface_class": "ARCHIVE_ONLY",
            "status": "NONOWNER_AUDIT_OVERLAY",
            "authority_posture": (
                "indirect donor-chain preservation only; not owner surface; "
                "not active control; not node provenance mutation"
            ),
            "ts_utc": _utc_iso(),
        },
        "provenance": {
            "source_surface_path": SURFACE_REL_PATH,
            "source_graph_path": GRAPH_REL_PATH,
            "source_surface_hash": str(
                (payload.get("provenance", {}) or {}).get("surface_hash", "")
            ),
        },
        "target": {
            "node_id": target_node_id,
            "layer": _clean_text(target_node.get("layer", "")),
            "node_type": _clean_text(target_node.get("node_type", "")),
            "name": _clean_text(target_node.get("name", "")),
        },
        "overlay_contract": {
            "purpose": (
                "Preserve the current indirect donor chain for manual review "
                "without mutating target-node provenance fields."
            ),
            "do_not_write_fields": list(annotation.get("forbidden_fields", []) or []),
            "manual_review_required": bool(annotation.get("manual_review_required")),
            "runtime_effect": "none",
        },
        "donor_chain": {
            "primary_chain": primary_chain,
            "secondary_context_only": secondary_context,
            "basis_node_ids": basis_node_ids,
            "basis_edge_relations": list(annotation.get("basis_edge_relations", []) or []),
            "bridge_source_node_ids": list(precondition.get("bridge_source_node_ids", []) or []),
            "supporting_source_doc_ids": source_doc_ids,
        },
        "disclaimers": [
            "No witness_refs are inherited from this overlay.",
            "No lineage_refs are inherited from this overlay.",
            "No intent lineage bridge is claimed from this donor chain to INTENT_REFINEMENT nodes.",
            "Secondary context nodes are semantic/structural neighbors only, not source-truth donors.",
            "This overlay is not an owner surface and must not be treated as active control fuel.",
        ],
        "self_audit": {
            "admissible_now": bool(annotation.get("admissible_now")),
            "decision": str(annotation.get("decision", "")),
            "hard_blockers": list(annotation.get("hard_blockers", []) or []),
            "missing_proof": list(annotation.get("missing_proof", []) or []),
        },
    }


def build_stripped_provenance_overlay_projection_payload(
    overlay_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a temp/smoke-safe node.properties overlay payload from an archive-only
    stripped provenance overlay artifact.

    This is intentionally non-operative:
    - accepts only ARCHIVE_ONLY / NONOWNER_AUDIT_OVERLAY sources
    - returns only namespaced audit-overlay fields
    - does not surface lineage_refs / witness_refs / policy roots
    """
    if not isinstance(overlay_payload, dict):
        return {}
    classification = dict(overlay_payload.get("classification", {}) or {})
    overlay_contract = dict(overlay_payload.get("overlay_contract", {}) or {})
    donor_chain = dict(overlay_payload.get("donor_chain", {}) or {})
    if classification.get("surface_class") != "ARCHIVE_ONLY":
        return {}
    if classification.get("status") != "NONOWNER_AUDIT_OVERLAY":
        return {}
    if overlay_contract.get("runtime_effect") != "none":
        return {}
    if overlay_contract.get("manual_review_required") is not True:
        return {}

    allowed_primary_roles = {
        "target_stripped_node",
        "strongest_semantic_donor",
        "source_document_ancestor",
    }
    allowed_via_relations = {
        "STRIPPED_FROM",
        "ROSETTA_MAP",
        "SOURCE_MAP_PASS",
    }
    primary_donor_chain = []
    for item in (donor_chain.get("primary_chain", []) or []):
        if not isinstance(item, dict):
            continue
        raw_node_id = item.get("node_id", "")
        if not isinstance(raw_node_id, str):
            continue
        node_id = raw_node_id.strip()
        if not node_id:
            continue
        raw_role = item.get("role", "")
        if not isinstance(raw_role, str):
            continue
        role = raw_role.strip()
        if role not in allowed_primary_roles:
            continue
        projected_item = {"node_id": node_id, "role": role}
        for key in ("layer", "node_type", "name"):
            raw_value = item.get(key, "")
            if not isinstance(raw_value, str):
                continue
            value = raw_value.strip()
            if value:
                projected_item[key] = value
        via_relations = [
            rel.strip()
            for rel in (item.get("via_relations", []) or [])
            if isinstance(rel, str)
            and rel.strip()
            and rel.strip() in allowed_via_relations
        ]
        if via_relations:
            projected_item["via_relations"] = via_relations
        primary_donor_chain.append(projected_item)
    secondary_context_node_ids = [
        item.get("node_id", "").strip()
        for item in (donor_chain.get("secondary_context_only", []) or [])
        if isinstance(item, dict)
        and isinstance(item.get("node_id", ""), str)
        and item.get("node_id", "").strip()
    ]
    basis_edge_relations = [
        rel.strip()
        for rel in (donor_chain.get("basis_edge_relations", []) or [])
        if isinstance(rel, str) and rel.strip()
    ]
    supporting_source_doc_ids = [
        node_id.strip()
        for node_id in (donor_chain.get("supporting_source_doc_ids", []) or [])
        if isinstance(node_id, str) and node_id.strip()
    ]
    bridge_source_node_ids = [
        node_id.strip()
        for node_id in (donor_chain.get("bridge_source_node_ids", []) or [])
        if isinstance(node_id, str) and node_id.strip()
    ]
    disclaimers = [
        note.strip()
        for note in (overlay_payload.get("disclaimers", []) or [])
        if isinstance(note, str) and note.strip()
    ]

    return {
        "status": "audit_only_nonoperative",
        "runtime_effect": "none",
        "audit_only": True,
        "overlay_kind": "stripped_provenance_archive_projection",
        "authority_posture": (
            "archive overlay projection only; manual review required; "
            "not provenance mutation; not runtime policy"
        ),
        "manual_review_required": True,
        "primary_donor_chain": primary_donor_chain,
        "secondary_context_node_ids": secondary_context_node_ids,
        "basis_edge_relations": basis_edge_relations,
        "supporting_source_doc_ids": supporting_source_doc_ids,
        "bridge_source_node_ids": bridge_source_node_ids,
        "disclaimers": disclaimers,
    }


def _normalize_intents(witness_corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    intents: list[dict[str, Any]] = []
    for idx, entry in enumerate(witness_corpus):
        if entry.get("witness", {}).get("kind") != "intent":
            continue
        tags = entry.get("tags", {}) or {}
        text = _primary_text(entry)
        if not text:
            continue
        intents.append(
            {
                "witness_ref": f"WITNESS_CORPUS::{idx}",
                "recorded_at": str(entry.get("recorded_at", "")),
                "source": str(tags.get("source", "maker")),
                "batch": str(tags.get("batch", "")),
                "phase": str(tags.get("phase", "")),
                "priority": str(tags.get("priority", "")),
                "topic": str(tags.get("topic", "")),
                "type": str(tags.get("type", "")),
                "text": text,
            }
        )
    intents.sort(
        key=lambda rec: (
            PRIORITY_RANK.get(rec["priority"], 9),
            rec["recorded_at"],
            rec["witness_ref"],
        ),
        reverse=False,
    )
    return intents


def _normalize_contexts(witness_corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for idx, entry in enumerate(witness_corpus):
        if entry.get("witness", {}).get("kind") != "context":
            continue
        tags = entry.get("tags", {}) or {}
        text = _primary_text(entry)
        if not text:
            continue
        contexts.append(
            {
                "witness_ref": f"WITNESS_CORPUS::{idx}",
                "recorded_at": str(entry.get("recorded_at", "")),
                "source": str(tags.get("source", "system")),
                "batch": str(tags.get("batch", "")),
                "phase": str(tags.get("phase", "")),
                "text": text,
            }
        )
    contexts.sort(key=lambda rec: (rec["recorded_at"], rec["witness_ref"]), reverse=True)
    return contexts


def _normalize_refined_intents(graph_nodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    refined: list[dict[str, Any]] = []
    for nid, node in graph_nodes.items():
        if node.get("node_type") != "INTENT_REFINEMENT":
            continue
        props = node.get("properties", {}) or {}
        refined.append(
            {
                "node_id": nid,
                "name": str(node.get("name", nid)),
                "text": str(node.get("description", "")),
                "tags": list(node.get("tags", []) or []),
                "source_intent_ids": list(props.get("source_intent_ids", []) or []),
                "lineage_refs": list(node.get("lineage_refs", []) or []),
                "witness_refs": list(node.get("witness_refs", []) or []),
            }
        )
    refined.sort(key=lambda rec: rec["node_id"], reverse=True)
    return refined


def _derive_focus_terms(
    maker_intents: list[dict[str, Any]],
    refined_intents: list[dict[str, Any]],
) -> list[str]:
    counts: Counter[str] = Counter()
    for rec in maker_intents:
        weight = 2 if rec.get("priority") == "P0" else 1
        for tok in _tokenize(rec["text"]):
            counts[tok] += weight
    for rec in refined_intents:
        for tok in _tokenize(rec["text"]):
            counts[tok] += 2
        for tok in rec.get("tags", []):
            for parsed in _tokenize(str(tok)):
                counts[parsed] += 1
    return [tok for tok, _ in counts.most_common(12)]


def _derive_non_negotiables(
    maker_intents: list[dict[str, Any]],
    refined_intents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    corpus = "\n".join(
        [rec["text"] for rec in maker_intents] + [rec["text"] for rec in refined_intents]
    ).lower()
    intent_refs = [rec["witness_ref"] for rec in maker_intents[:6]]
    refined_refs = [rec["node_id"] for rec in refined_intents[:6]]
    refs = intent_refs + refined_refs

    directives: list[dict[str, Any]] = []

    def add_directive(
        directive_id: str,
        label: str,
        statement: str,
        rationale: str,
        *,
        execution_binding: str,
    ) -> None:
        directives.append(
            {
                "directive_id": directive_id,
                "label": label,
                "statement": statement,
                "rationale": rationale,
                "execution_binding": execution_binding,
                "source_refs": refs,
            }
        )

    if "intent" in corpus and any(word in corpus for word in ("save", "saved", "preserv", "refine")):
        add_directive(
            "INTENT_FIRST_CLASS",
            "intent_first_class",
            "Keep maker/system intent as first-class preserved memory, not disposable context.",
            "Derived from preserved maker intent statements about first-class intent and preservation.",
            execution_binding="preserve_intent_memory",
        )
    if "context" in corpus and any(word in corpus for word in ("continu", "lost", "saving", "preserv")):
        add_directive(
            "CONTEXT_CONTINUITY",
            "context_continuity",
            "Continuously preserve runtime context so active intent and reasoning state are not lost.",
            "Derived from maker intent statements about not losing context across runs.",
            execution_binding="preserve_runtime_context",
        )
    if "skill" in corpus and "graph" in corpus:
        add_directive(
            "SKILL_GRAPH_CO_DEVELOPMENT",
            "skill_graph_co_development",
            "Develop skills and graphs together, with execution tested against refinery-backed graph surfaces.",
            "Derived from maker intent statements about joint graph/skill maturation.",
            execution_binding="audit_only",
        )
    if "graph" in corpus or "witness" in corpus:
        add_directive(
            "GRAPH_NATIVE_MEMORY",
            "graph_native_memory",
            "Persist control-relevant intent and context in graph-native and append-only memory surfaces.",
            "Derived from maker intent statements about graph storage and persistent memory.",
            execution_binding="audit_only",
        )

    return directives


def _derive_executable_non_negotiables(
    non_negotiables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in non_negotiables
        if str(item.get("execution_binding", "audit_only")) != "audit_only"
    ]


def _build_focus_term_quality(
    maker_intents: list[dict[str, Any]],
    refined_intents: list[dict[str, Any]],
    non_negotiables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    support: dict[str, dict[str, Any]] = {}

    def ensure(term: str) -> dict[str, Any]:
        return support.setdefault(
            term,
            {
                "term": term,
                "maker_support": 0,
                "refined_support": 0,
                "directive_support": 0,
                "weighted_score": 0,
                "steering_safe": False,
                "eligible_concept_hit_count": 0,
                "eligible_concept_hit_rate": 0.0,
                "unique_concept_hit_count": 0,
                "redundant_alias_of": "",
                "executable_safe": False,
            },
        )

    for rec in maker_intents:
        tokens = set(_tokenize_quality(rec.get("text", "")))
        tokens.update(_tokenize_quality(rec.get("topic", "")))
        tokens.update(_tokenize_quality(rec.get("type", "")))
        for token in tokens:
            ensure(token)["maker_support"] += 1

    for rec in refined_intents:
        tokens = set(_tokenize_quality(rec.get("text", "")))
        for tag in rec.get("tags", []):
            tokens.update(_tokenize_quality(str(tag)))
        for token in tokens:
            ensure(token)["refined_support"] += 1

    for directive in non_negotiables:
        tokens = set(_tokenize_quality(directive.get("label", "")))
        tokens.update(_tokenize_quality(directive.get("statement", "")))
        for token in tokens:
            ensure(token)["directive_support"] += 1

    quality: list[dict[str, Any]] = []
    for term, rec in support.items():
        rec["weighted_score"] = (
            (int(rec["maker_support"]) * 2)
            + (int(rec["refined_support"]) * 2)
            + (int(rec["directive_support"]) * 3)
        )
        rec["steering_safe"] = (
            term not in STEERING_BLOCKLIST
            and (
                int(rec["directive_support"]) > 0
                or int(rec["refined_support"]) > 0
                or int(rec["maker_support"]) > 1
            )
        )
        quality.append(rec)

    quality.sort(key=lambda item: (-int(item["weighted_score"]), item["term"]))
    return quality


def _derive_focus_terms_from_quality(focus_term_quality: list[dict[str, Any]]) -> list[str]:
    return [
        str(item["term"])
        for item in focus_term_quality
        if int(item.get("weighted_score", 0)) > 0
    ][:12]


def _derive_steering_focus_terms(focus_term_quality: list[dict[str, Any]]) -> list[str]:
    return [
        str(item["term"])
        for item in focus_term_quality
        if item.get("steering_safe") and int(item.get("weighted_score", 0)) >= 2
    ][:8]


def _concept_corpus(node: dict[str, Any]) -> str:
    haystacks = [
        str(node.get("name", "")),
        str(node.get("description", "")),
        " ".join(str(tag) for tag in (node.get("tags", []) or [])),
    ]
    return " ".join(part.lower() for part in haystacks)


def _derive_executable_focus_terms(
    steering_focus_terms: list[str],
    focus_term_quality: list[dict[str, Any]],
    graph_nodes: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_total = len(concept_nodes)
    quality_by_term = {str(item.get("term", "")): item for item in focus_term_quality}
    graph_metrics: dict[str, Any] = {
        "eligible_concept_node_count": concept_total,
        "max_hit_rate": EXECUTABLE_MAX_CONCEPT_HIT_RATE,
        "max_high_intake_share": EXECUTABLE_MAX_HIGH_INTAKE_SHARE,
        "min_anchored_support": EXECUTABLE_MIN_ANCHORED_SUPPORT,
        "pruned_terms": [],
    }
    if concept_total == 0:
        for term in steering_focus_terms:
            rec = quality_by_term.get(term)
            if rec is None:
                continue
            rec["executable_safe"] = True
        return list(steering_focus_terms), graph_metrics

    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    term_hits: dict[str, set[str]] = {}
    for term in steering_focus_terms:
        hits = {
            nid
            for nid, corpus in concept_corpora.items()
            if term and term.lower() in corpus
        }
        term_hits[term] = hits

    executable_terms: list[str] = []
    for term in steering_focus_terms:
        hits = term_hits.get(term, set())
        hit_count = len(hits)
        hit_rate = (hit_count / concept_total) if concept_total else 0.0
        layer_counter: Counter[str] = Counter(
            str(concept_nodes.get(nid, {}).get("layer", "")) for nid in hits
        )
        high_intake_hits = int(layer_counter.get(EXECUTABLE_HIGH_INTAKE_LAYER, 0))
        high_intake_share = (high_intake_hits / hit_count) if hit_count else 0.0
        anchored_support_count = sum(
            count for layer, count in layer_counter.items() if layer in EXECUTABLE_ANCHOR_LAYERS
        )
        other_hits = set().union(
            *(term_hits.get(other, set()) for other in steering_focus_terms if other != term)
        )
        unique_concept_hit_count = len(hits - other_hits)
        redundant_alias_of = ""
        if term.endswith("s") and len(term) > 3:
            singular = term[:-1]
            singular_hits = term_hits.get(singular, set())
            if singular in term_hits and hits and hits.issubset(singular_hits):
                redundant_alias_of = singular
        executable_safe = (
            hit_count > 0
            and hit_rate <= EXECUTABLE_MAX_CONCEPT_HIT_RATE
            and not redundant_alias_of
            and not (
                high_intake_share >= EXECUTABLE_MAX_HIGH_INTAKE_SHARE
                and anchored_support_count < EXECUTABLE_MIN_ANCHORED_SUPPORT
            )
        )
        rec = quality_by_term.get(term)
        if rec is not None:
            rec["eligible_concept_hit_count"] = hit_count
            rec["eligible_concept_hit_rate"] = round(hit_rate, 6)
            rec["unique_concept_hit_count"] = unique_concept_hit_count
            rec["redundant_alias_of"] = redundant_alias_of
            rec["high_intake_share"] = round(high_intake_share, 6)
            rec["anchored_support_count"] = anchored_support_count
            rec["executable_safe"] = executable_safe
        if executable_safe:
            executable_terms.append(term)
        else:
            prune_reason = []
            if hit_count <= 0:
                prune_reason.append("no_hits")
            if hit_rate > EXECUTABLE_MAX_CONCEPT_HIT_RATE:
                prune_reason.append("too_broad")
            if redundant_alias_of:
                prune_reason.append("redundant_alias")
            if (
                high_intake_share >= EXECUTABLE_MAX_HIGH_INTAKE_SHARE
                and anchored_support_count < EXECUTABLE_MIN_ANCHORED_SUPPORT
            ):
                prune_reason.append("high_intake_dominance")
            graph_metrics["pruned_terms"].append(
                {
                    "term": term,
                    "eligible_concept_hit_count": hit_count,
                    "eligible_concept_hit_rate": round(hit_rate, 6),
                    "unique_concept_hit_count": unique_concept_hit_count,
                    "high_intake_share": round(high_intake_share, 6),
                    "anchored_support_count": anchored_support_count,
                    "redundant_alias_of": redundant_alias_of,
                    "prune_reason": prune_reason,
                }
            )

    return executable_terms[:8], graph_metrics


def _derive_executable_focus_refinement_candidates(
    maker_intents: list[dict[str, Any]],
    refined_intents: list[dict[str, Any]],
    graph_nodes: dict[str, dict[str, Any]],
    executable_focus_terms: list[str],
) -> list[dict[str, Any]]:
    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_total = len(concept_nodes)
    if concept_total == 0:
        return []

    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    current_executable_hits = set().union(
        *(
            {
                nid
                for nid, corpus in concept_corpora.items()
                if term and term.lower() in corpus
            }
            for term in executable_focus_terms
        )
    )

    source_map: dict[str, set[str]] = {}
    for rec in maker_intents:
        topic = str(rec.get("topic", "")).strip()
        for part in _underscore_token_parts(topic):
            if part in TOPIC_COMPONENT_BLOCKLIST or part in STEERING_BLOCKLIST:
                continue
            source_map.setdefault(part, set()).add(f"maker_topic:{topic}")

    for rec in refined_intents:
        for tag in rec.get("tags", []):
            tag_text = str(tag).strip()
            for part in _underscore_token_parts(tag_text):
                if part in TOPIC_COMPONENT_BLOCKLIST or part in STEERING_BLOCKLIST:
                    continue
                source_map.setdefault(part, set()).add(f"refined_tag:{tag_text}")

    candidates: list[dict[str, Any]] = []
    for term, source_labels in sorted(source_map.items()):
        hits = {
            nid
            for nid, corpus in concept_corpora.items()
            if term and term.lower() in corpus
        }
        hit_count = len(hits)
        if hit_count == 0:
            continue
        hit_rate = (hit_count / concept_total) if concept_total else 0.0
        if hit_rate > EXECUTABLE_MAX_CONCEPT_HIT_RATE:
            continue
        novel_hits = hits - current_executable_hits
        novel_count = len(novel_hits)
        if novel_count == 0:
            continue
        candidates.append(
            {
                "term": term,
                "source_labels": sorted(source_labels),
                "eligible_concept_hit_count": hit_count,
                "eligible_concept_hit_rate": round(hit_rate, 6),
                "novel_vs_current_executable_count": novel_count,
                "current_executable_overlap_count": hit_count - novel_count,
                "candidate_status": "audit_only",
            }
        )

    candidates.sort(
        key=lambda item: (
            -int(item["novel_vs_current_executable_count"]),
            -int(item["eligible_concept_hit_count"]),
            str(item["term"]),
        )
    )
    return candidates[:6]


def _derive_executable_focus_promotion_readiness(
    executable_focus_refinement_candidates: list[dict[str, Any]],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    executable_focus_terms: list[str],
    gate_min_concepts: int,
) -> list[dict[str, Any]]:
    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    readiness: list[dict[str, Any]] = []
    for item in executable_focus_refinement_candidates:
        source_labels = [str(label) for label in item.get("source_labels", [])]
        hit_count = int(item.get("eligible_concept_hit_count", 0))
        novel_count = int(item.get("novel_vs_current_executable_count", 0))
        overlap_count = int(item.get("current_executable_overlap_count", 0))
        hit_rate = float(item.get("eligible_concept_hit_rate", 0.0))
        term = str(item.get("term", ""))
        family_terms = _cluster_family_terms(source_labels, term=term)
        hit_ids = [
            nid
            for nid, corpus in concept_corpora.items()
            if term and term.lower() in corpus
        ]
        hit_set = set(hit_ids)
        node_has_intra_edge: set[str] = set()
        for edge in graph_edges:
            source_id = str(edge.get("source_id", ""))
            target_id = str(edge.get("target_id", ""))
            if source_id in hit_set and target_id in hit_set and source_id != target_id:
                node_has_intra_edge.add(source_id)
                node_has_intra_edge.add(target_id)
        excluded_terms = set(executable_focus_terms) | {term}
        semantic_token_counter: Counter[str] = Counter()
        semantic_tag_counter: Counter[str] = Counter()
        family_term_hits = 0
        for nid in hit_ids:
            node = concept_nodes.get(nid, {})
            corpus = concept_corpora.get(nid, "")
            if any(part and part in corpus for part in family_terms):
                family_term_hits += 1
            for token in _cluster_semantic_tokens(node, excluded_terms=excluded_terms):
                semantic_token_counter[token] += 1
            for tag in _cluster_semantic_tags(node, excluded_terms=excluded_terms):
                semantic_tag_counter[tag] += 1
        min_support = max(2, math.ceil(hit_count * 0.15)) if hit_count else 2
        top_shared_tokens = [
            {
                "token": token,
                "count": count,
                "share": round(count / hit_count, 6),
            }
            for token, count in semantic_token_counter.most_common()
            if count >= min_support
        ][:5]
        top_shared_tags = [
            {
                "tag": tag,
                "count": count,
                "share": round(count / hit_count, 6),
            }
            for tag, count in semantic_tag_counter.most_common()
            if count >= min_support
        ][:5]
        family_term_coverage = (family_term_hits / hit_count) if hit_count else 0.0
        intra_hit_edge_coverage = (len(node_has_intra_edge) / hit_count) if hit_count else 0.0
        semantic_tag_concentration = (
            float(top_shared_tags[0]["share"]) if top_shared_tags else 0.0
        )
        if semantic_tag_concentration >= 0.2 and intra_hit_edge_coverage >= 0.4:
            cluster_precision_status = "coherent"
        elif (
            intra_hit_edge_coverage >= 0.2
            or semantic_tag_concentration >= 0.15
            or family_term_coverage >= 0.15
        ):
            cluster_precision_status = "mixed"
        else:
            cluster_precision_status = "diffuse"
        dual_provenance = (
            any(label.startswith("maker_topic:") for label in source_labels)
            and any(label.startswith("refined_tag:") for label in source_labels)
        )
        if hit_rate <= 0.01:
            scope_band = "narrow"
        elif hit_rate <= 0.05:
            scope_band = "bounded"
        else:
            scope_band = "broad"
        readiness_flags = {
            "dual_provenance": dual_provenance,
            "solo_gate_ready": hit_count >= gate_min_concepts,
            "novel_gain_ready": novel_count >= gate_min_concepts,
            "bounded_scope": scope_band != "broad",
        }
        if all(readiness_flags.values()) and cluster_precision_status == "coherent":
            readiness_status = "candidate_for_execution_binding_check"
        elif all(readiness_flags.values()):
            readiness_status = "candidate_for_cluster_precision_check"
        else:
            readiness_status = "hold_audit_only"
        missing_proof = ["execution_binding_proof"]
        if cluster_precision_status != "coherent":
            missing_proof.insert(0, "cluster_precision_check")
        readiness.append(
            {
                "term": term,
                "candidate_status": str(item.get("candidate_status", "audit_only")),
                "readiness_status": readiness_status,
                "source_labels": source_labels,
                "eligible_concept_hit_count": hit_count,
                "eligible_concept_hit_rate": round(hit_rate, 6),
                "novel_vs_current_executable_count": novel_count,
                "current_executable_overlap_count": overlap_count,
                "gate_min_concepts": gate_min_concepts,
                "scope_band": scope_band,
                "readiness_flags": readiness_flags,
                "cluster_precision": {
                    "status": cluster_precision_status,
                    "min_support": min_support,
                    "family_terms": family_terms,
                    "family_term_coverage": round(family_term_coverage, 6),
                    "intra_hit_edge_coverage": round(intra_hit_edge_coverage, 6),
                    "top_shared_semantic_tags": top_shared_tags,
                    "top_shared_semantic_tokens": top_shared_tokens,
                },
                "missing_proof": missing_proof,
            }
        )
    readiness.sort(
        key=lambda item: (
            item["readiness_status"] != "candidate_for_execution_binding_check",
            item["readiness_status"] != "candidate_for_cluster_precision_check",
            -int(item["novel_vs_current_executable_count"]),
            -int(item["eligible_concept_hit_count"]),
            str(item["term"]),
        )
    )
    return readiness


def _derive_execution_binding_probes(
    executable_focus_promotion_readiness: list[dict[str, Any]],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    executable_focus_terms: list[str],
    gate_min_concepts: int,
) -> list[dict[str, Any]]:
    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_total = len(concept_nodes)
    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    current_hit_ids = _concept_hit_ids_for_terms(concept_corpora, executable_focus_terms)
    probes: list[dict[str, Any]] = []
    for item in executable_focus_promotion_readiness:
        term = str(item.get("term", ""))
        term_hit_ids = _concept_hit_ids_for_terms(concept_corpora, [term])
        novel_hit_ids = term_hit_ids - current_hit_ids
        projected_hit_ids = current_hit_ids | term_hit_ids
        readiness_status = str(item.get("readiness_status", "hold_audit_only"))
        novel_hit_rate = (len(novel_hit_ids) / concept_total) if concept_total else 0.0
        projected_hit_rate = (len(projected_hit_ids) / concept_total) if concept_total else 0.0

        if readiness_status == "candidate_for_execution_binding_check":
            if len(novel_hit_ids) < gate_min_concepts:
                status = "no_effect"
            elif novel_hit_rate > 0.05:
                status = "too_broad_for_execution"
            else:
                status = "bounded_positive_effect"
        elif readiness_status == "candidate_for_cluster_precision_check":
            status = "blocked_by_cluster_precision"
        else:
            status = "hold_audit_only"

        probes.append(
            {
                "status": status,
                "current_executable_hit_count": len(current_hit_ids),
                "term_hit_count": len(term_hit_ids),
                "novel_hit_count": len(novel_hit_ids),
                "novel_hit_rate": round(novel_hit_rate, 6),
                "projected_executable_hit_count": len(projected_hit_ids),
                "projected_executable_hit_rate": round(projected_hit_rate, 6),
                "projected_focus_term_count": len(set(executable_focus_terms) | ({term} if term else set())),
                "gate_min_concepts": gate_min_concepts,
                "sample_new_focus_matches": _sample_concepts(
                    novel_hit_ids,
                    concept_nodes,
                ),
            }
        )
    return probes


def _derive_executable_focus_semantic_comparison(
    executable_focus_promotion_readiness: list[dict[str, Any]],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    executable_focus_terms: list[str],
) -> dict[str, Any]:
    if not executable_focus_promotion_readiness:
        return {}

    by_term = {
        str(item.get("term", "")): item
        for item in executable_focus_promotion_readiness
        if str(item.get("term", "")).strip()
    }
    if "derivation" in by_term and "integration" in by_term:
        comparison_pair = ["derivation", "integration"]
    else:
        comparison_pair = [
            str(item.get("term", ""))
            for item in executable_focus_promotion_readiness[:2]
            if str(item.get("term", "")).strip()
        ]
    compared = [by_term[term] for term in comparison_pair if term in by_term]
    if len(compared) < 2:
        return {}

    structural_front_runner = compared[0]
    focus_term_set = {str(term).lower() for term in executable_focus_terms if str(term).strip()}
    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    semantic_hygiene_front_runner = compared[0]
    semantic_hygiene_best_score = -10**6
    observations: list[dict[str, Any]] = []
    family_observations: list[dict[str, Any]] = []

    for item in compared:
        term = str(item.get("term", ""))
        source_labels = [
            str(label).split(":", 1)[-1].lower()
            for label in item.get("source_labels", [])
        ]
        cluster = dict(item.get("cluster_precision", {}) or {})
        probe = dict(item.get("execution_binding_probe", {}) or {})
        family_terms = [str(part).lower() for part in cluster.get("family_terms", [])]
        notes: list[str] = []
        score = 0
        hit_ids = _concept_hit_ids_for_terms(concept_corpora, [term])
        family_counter: Counter[str] = Counter()
        layer_counter: Counter[str] = Counter()
        node_type_counter: Counter[str] = Counter()
        family_notes: list[str] = []
        for nid in sorted(hit_ids):
            node = concept_nodes.get(nid, {})
            family_counter[_node_family_label(nid)] += 1
            layer_counter[str(node.get("layer", "?"))] += 1
            node_type_counter[str(node.get("node_type", "?"))] += 1
        top_family_count = family_counter.most_common(1)[0][1] if family_counter else 0
        top_family_share = (top_family_count / len(hit_ids)) if hit_ids else 0.0
        if top_family_share >= 0.75:
            family_posture = "highly_concentrated"
        elif top_family_share >= 0.45:
            family_posture = "mixed_clustered"
        else:
            family_posture = "diffuse_cross_family"
        if family_counter:
            top_family = family_counter.most_common(1)[0][0]
            if top_family.endswith("SOURCE_MAP_PASS"):
                family_notes.append("source_map_family_heavy")
            if "A1_STRIPPED" in family_counter:
                family_notes.append("stripped_family_present")
            if any(label.endswith("ENGINE_PATTERN_PASS") for label in family_counter):
                family_notes.append("engine_pattern_family_present")
        else:
            top_family = ""

        if any(term in raw for raw in source_labels):
            score += 2
            notes.append("direct_maker_topic_alignment")
        if any(raw.endswith("_sources") or "_sources_" in raw for raw in source_labels):
            score -= 2
            notes.append("source_or_provenance_lean")
        if any(part in focus_term_set for part in family_terms if part != term):
            score -= 1
            notes.append("overlaps_current_executable_family")
        if term == "integration":
            score += 1
            notes.append("skill_graph_integration_theme")
        if term == "preservation":
            score -= 1
            notes.append("overlaps_existing_preservation_non_negotiables")
        if term == "derivation":
            notes.append("process_or_family_derivation_theme")

        if score > semantic_hygiene_best_score:
            semantic_hygiene_front_runner = item
            semantic_hygiene_best_score = score

        observations.append(
            {
                "term": term,
                "readiness_status": str(item.get("readiness_status", "")),
                "cluster_status": str(cluster.get("status", "")),
                "execution_binding_probe_status": str(probe.get("status", "")),
                "semantic_notes": notes,
                "semantic_hygiene_score": score,
            }
        )
        family_observations.append(
            {
                "term": term,
                "hit_count": len(hit_ids),
                "family_posture": family_posture,
                "top_family": top_family,
                "top_family_share": round(top_family_share, 6),
                "family_distribution": _distribution_rows(family_counter, total=len(hit_ids)),
                "layer_distribution": _distribution_rows(layer_counter, total=len(hit_ids)),
                "node_type_distribution": _distribution_rows(
                    node_type_counter, total=len(hit_ids)
                ),
                "family_notes": family_notes,
            }
        )

    structural_term = str(structural_front_runner.get("term", ""))
    semantic_term = str(semantic_hygiene_front_runner.get("term", ""))
    return {
        "scope": "audit_only_nonbinding",
        "runtime_effect": "none",
        "comparison_pair": comparison_pair,
        "structural_front_runner": structural_term,
        "semantic_hygiene_front_runner": semantic_term,
        "decision": "keep_audit_only_no_promotion",
        "manual_review_required": True,
        "comparison_basis": [
            "cluster_precision",
            "execution_binding_probe",
            "source_label_semantics",
        ],
        "observations": observations,
        "family_audit": {
            "scope": "audit_only_nonbinding",
            "runtime_effect": "none",
            "basis": [
                "concept_hit_family_distribution",
                "layer_distribution",
                "node_type_distribution",
            ],
            "observations": family_observations,
        },
        "rationale": [
            f"{structural_term} is structurally strongest on the current graph-backed readiness surface.",
            f"{semantic_term} is currently the least misleading semantic runtime term by source-label posture.",
            "Signals remain split, so no staged term is promoted from audit-only status.",
        ],
    }


def _derive_derivation_family_contamination_audit(
    executable_focus_promotion_readiness: list[dict[str, Any]],
    executable_focus_semantic_comparison: dict[str, Any],
    *,
    graph_nodes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    by_term = {
        str(item.get("term", "")): item
        for item in executable_focus_promotion_readiness
        if str(item.get("term", "")).strip()
    }
    derivation = by_term.get("derivation")
    if not derivation:
        return {}

    family_audit = dict(
        (executable_focus_semantic_comparison.get("family_audit", {}) or {})
    )
    family_observations = {
        str(item.get("term", "")): item
        for item in (family_audit.get("observations", []) or [])
        if str(item.get("term", "")).strip()
    }
    derivation_family = family_observations.get("derivation", {})

    intent_refinement_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) == "INTENT_REFINEMENT"
    }
    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    hit_ids = sorted(_concept_hit_ids_for_terms(concept_corpora, ["derivation"]))

    name_only_count = 0
    provenance_sparse_count = 0
    for nid in hit_ids:
        node = concept_nodes.get(nid, {})
        name_text = str(node.get("name", "")).lower()
        desc_tag_text = " ".join(
            [
                str(node.get("description", "")).lower(),
                " ".join(str(tag).lower() for tag in (node.get("tags", []) or [])),
            ]
        )
        if "derivation" in name_text and "derivation" not in desc_tag_text:
            name_only_count += 1
        if not (node.get("witness_refs") or node.get("lineage_refs")):
            provenance_sparse_count += 1

    total_hits = len(hit_ids)
    family_rows = list(derivation_family.get("family_distribution", []) or [])
    layer_rows = list(derivation_family.get("layer_distribution", []) or [])
    node_type_rows = list(derivation_family.get("node_type_distribution", []) or [])
    cluster = dict(derivation.get("cluster_precision", {}) or {})
    top_shared_tags = list(cluster.get("top_shared_semantic_tags", []) or [])

    source_map_share = _distribution_share(
        family_rows, exact="A2_3::SOURCE_MAP_PASS"
    )
    engine_pattern_share = _distribution_share(
        family_rows, exact="A2_3::ENGINE_PATTERN_PASS"
    )
    stripped_share = _distribution_share(layer_rows, exact="A1_STRIPPED")
    high_intake_share = _distribution_share(layer_rows, exact="A2_HIGH_INTAKE")
    extracted_concept_share = _distribution_share(
        node_type_rows, exact="EXTRACTED_CONCEPT"
    )
    refined_concept_share = _distribution_share(
        node_type_rows, exact="REFINED_CONCEPT"
    )
    top_shared_semantic_tag_share = round(
        float(top_shared_tags[0]["share"]) if top_shared_tags else 0.0,
        6,
    )
    name_only_share = round(
        (name_only_count / total_hits) if total_hits else 0.0,
        6,
    )
    provenance_sparse_share = round(
        (provenance_sparse_count / total_hits) if total_hits else 0.0,
        6,
    )

    risk_flags: list[str] = []
    if source_map_share >= 0.7:
        risk_flags.append("source_map_dominance")
    if high_intake_share >= 0.7:
        risk_flags.append("high_intake_dominance")
    if name_only_share >= 0.4:
        risk_flags.append("name_only_carryover")
    if provenance_sparse_share >= 0.8:
        risk_flags.append("provenance_sparse_hits")
    if top_shared_semantic_tag_share >= 0.5:
        risk_flags.append("single_tag_dominance")

    counter_signals: list[str] = []
    if engine_pattern_share >= 0.2:
        counter_signals.append("engine_pattern_family_present")
    if stripped_share >= 0.15:
        counter_signals.append("stripped_layer_present")
    if refined_concept_share >= 0.15:
        counter_signals.append("refined_concepts_present")
    if top_shared_semantic_tag_share >= 0.2:
        counter_signals.append("shared_semantic_tag_signal")

    if "source_map_dominance" in risk_flags and len(counter_signals) <= 1:
        contamination_risk = "high_source_map_carryover_risk"
    elif risk_flags:
        contamination_risk = "mixed_but_not_pure_source_map_carryover"
    else:
        contamination_risk = "low_source_map_carryover_signal"

    rationale = []
    if source_map_share > 0:
        rationale.append(
            f"derivation hits include SOURCE_MAP carryover at share={source_map_share:.6f}"
        )
    if engine_pattern_share > 0:
        rationale.append(
            f"engine-pattern family share={engine_pattern_share:.6f} provides non-source-map counter-signal"
        )
    if stripped_share > 0:
        rationale.append(
            f"A1_STRIPPED share={stripped_share:.6f} shows some upper-surface carryover beyond intake mapping"
        )
    if provenance_sparse_share > 0:
        rationale.append(
            f"provenance_sparse_share={provenance_sparse_share:.6f} indicates many derivation hits remain weakly linked to direct witness lineage"
        )

    derived_refined_node_ids: list[str] = []
    source_witness_refs: set[str] = set()
    for nid, node in intent_refinement_nodes.items():
        text = " ".join(
            [
                str(node.get("name", "")),
                str(node.get("description", "")),
                " ".join(str(tag) for tag in (node.get("tags", []) or [])),
            ]
        ).lower()
        if "skill_derivation_sources" not in text and "derivation" not in text:
            continue
        derived_refined_node_ids.append(nid)
        for witness_ref in (node.get("witness_refs", []) or []):
            if str(witness_ref).strip():
                source_witness_refs.add(str(witness_ref))

    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "evidence_for_future_term_promotion_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not promotion approval"
        ),
        "assessed_term": "derivation",
        "contamination_risk": contamination_risk,
        "risk_flags": risk_flags,
        "counter_signals": counter_signals,
        "graph_basis": {
            "hit_count": total_hits,
            "source_map_share": source_map_share,
            "engine_pattern_share": engine_pattern_share,
            "stripped_share": stripped_share,
            "high_intake_share": high_intake_share,
            "extracted_concept_share": extracted_concept_share,
            "refined_concept_share": refined_concept_share,
            "top_shared_semantic_tag_share": top_shared_semantic_tag_share,
            "name_only_share": name_only_share,
            "provenance_sparse_share": provenance_sparse_share,
        },
        "sample_hit_refs": _sample_concepts(set(hit_ids), concept_nodes),
        "source_witness_refs": sorted(source_witness_refs),
        "derived_refined_node_ids": sorted(derived_refined_node_ids),
        "missing_proof": list(derivation.get("missing_proof", []) or []),
        "rationale": rationale,
    }


def _derive_semantic_sample_comparison(
    executable_focus_promotion_readiness: list[dict[str, Any]],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    executable_focus_terms: list[str],
) -> dict[str, Any]:
    by_term = {
        str(item.get("term", "")): item
        for item in executable_focus_promotion_readiness
        if str(item.get("term", "")).strip()
    }
    left = by_term.get("derivation")
    right = by_term.get("integration")
    if not left or not right:
        return {}

    concept_nodes = {
        nid: node
        for nid, node in graph_nodes.items()
        if str(node.get("node_type", "")) in EXECUTABLE_CONCEPT_NODE_TYPES
    }
    concept_corpora = {nid: _concept_corpus(node) for nid, node in concept_nodes.items()}
    current_hit_ids = _concept_hit_ids_for_terms(concept_corpora, executable_focus_terms)

    def sample_term(item: dict[str, Any]) -> dict[str, Any]:
        term = str(item.get("term", ""))
        cluster = dict(item.get("cluster_precision", {}) or {})
        family_terms = [str(part).lower() for part in cluster.get("family_terms", [])]
        source_labels = sorted(str(label) for label in (item.get("source_labels", []) or []))
        term_hit_ids = sorted(_concept_hit_ids_for_terms(concept_corpora, [term]))
        novel_hit_ids = [nid for nid in term_hit_ids if nid not in current_hit_ids]
        candidate_ids = novel_hit_ids or term_hit_ids

        scored: list[dict[str, Any]] = []
        for nid in candidate_ids:
            node = concept_nodes.get(nid, {})
            name = str(node.get("name", ""))
            desc = str(node.get("description", ""))
            tags = [str(tag) for tag in (node.get("tags", []) or [])]
            corpus = concept_corpora.get(nid, "")
            desc_lower = desc.lower()
            name_lower = name.lower()
            family_label = _node_family_label(nid)
            layer = str(node.get("layer", "?"))
            node_type = str(node.get("node_type", "?"))
            provenance_sparse = not (node.get("witness_refs") or node.get("lineage_refs"))
            has_term_tag = any(term in tag.lower() for tag in tags)
            has_desc_term = term in desc_lower or any(
                family_term in desc_lower for family_term in family_terms
            )
            has_family_term = any(
                family_term and family_term in corpus for family_term in family_terms
            )
            name_only_match = term in name_lower and not has_desc_term and not has_term_tag
            source_map_family = family_label.endswith("SOURCE_MAP_PASS")
            engine_pattern_family = family_label.endswith("ENGINE_PATTERN_PASS")
            stripped_layer = layer == "A1_STRIPPED"
            refined_concept = node_type == "REFINED_CONCEPT"

            semantic_support_score = (
                int(has_term_tag)
                + int(has_desc_term)
                + int(has_family_term)
                + int(engine_pattern_family)
                + int(stripped_layer)
                + int(refined_concept)
            )
            residue_score = (
                int(source_map_family)
                + int(layer == "A2_HIGH_INTAKE")
                + int(provenance_sparse)
                + int(name_only_match)
            )
            if semantic_support_score > residue_score:
                sample_posture = "semantic_support"
            elif residue_score > semantic_support_score:
                sample_posture = "residue_risk"
            else:
                sample_posture = "mixed"

            scored.append(
                {
                    "node_id": nid,
                    "name": name,
                    "node_type": node_type,
                    "family_label": family_label,
                    "layer": layer,
                    "semantic_support_score": semantic_support_score,
                    "residue_score": residue_score,
                    "sample_posture": sample_posture,
                    "provenance_sparse": provenance_sparse,
                    "signals": {
                        "has_term_tag": has_term_tag,
                        "has_desc_term": has_desc_term,
                        "has_family_term": has_family_term,
                        "name_only_match": name_only_match,
                        "source_map_family": source_map_family,
                        "engine_pattern_family": engine_pattern_family,
                        "stripped_layer": stripped_layer,
                        "refined_concept": refined_concept,
                    },
                }
            )

        strong = sorted(
            scored,
            key=lambda row: (
                -int(row["semantic_support_score"]),
                int(row["residue_score"]),
                str(row["node_id"]),
            ),
        )[:3]
        weak = sorted(
            scored,
            key=lambda row: (
                -int(row["residue_score"]),
                int(row["semantic_support_score"]),
                str(row["node_id"]),
            ),
        )[:3]
        ordered_samples: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in strong + weak:
            if row["node_id"] in seen:
                continue
            ordered_samples.append(row)
            seen.add(str(row["node_id"]))

        semantic_support_count = sum(
            1 for row in ordered_samples if row["sample_posture"] == "semantic_support"
        )
        residue_risk_count = sum(
            1 for row in ordered_samples if row["sample_posture"] == "residue_risk"
        )
        mixed_count = sum(1 for row in ordered_samples if row["sample_posture"] == "mixed")
        if semantic_support_count >= residue_risk_count + 2:
            sample_posture = "semantic_support_lean"
        elif residue_risk_count >= semantic_support_count + 2:
            sample_posture = "source_map_residue_lean"
        else:
            sample_posture = "mixed_sample"

        return {
            "term": term,
            "source_labels": source_labels,
            "sample_scope": "novel_vs_current_executable_hits",
            "term_hit_count": len(term_hit_ids),
            "novel_hit_count": len(novel_hit_ids),
            "sample_size": len(ordered_samples),
            "sample_node_ids": [str(row["node_id"]) for row in ordered_samples],
            "sample_posture": sample_posture,
            "semantic_support_sample_count": semantic_support_count,
            "residue_risk_sample_count": residue_risk_count,
            "mixed_sample_count": mixed_count,
            "samples": ordered_samples,
        }

    left_sample = sample_term(left)
    right_sample = sample_term(right)

    if (
        left_sample["semantic_support_sample_count"] > right_sample["semantic_support_sample_count"]
        and left_sample["residue_risk_sample_count"] < right_sample["residue_risk_sample_count"]
    ):
        comparison_result = "derivation_less_residual_audit_only"
    elif (
        right_sample["semantic_support_sample_count"] > left_sample["semantic_support_sample_count"]
        and right_sample["residue_risk_sample_count"] < left_sample["residue_risk_sample_count"]
    ):
        comparison_result = "integration_less_residual_audit_only"
    else:
        comparison_result = "inconclusive_audit_only"

    missing_proof = sorted(
        {
            str(flag)
            for item in (left, right)
            for flag in (item.get("missing_proof", []) or [])
            if str(flag).strip()
        }
    )
    confidence = "low"
    if min(left_sample["sample_size"], right_sample["sample_size"]) >= 4:
        confidence = "medium"

    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "evidence_for_future_term_promotion_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not promotion approval"
        ),
        "comparison_basis": "semantic_sample",
        "comparison_scope": "derivation_vs_integration_sample",
        "left_family": "derivation",
        "right_family": "integration",
        "left_source_labels": left_sample["source_labels"],
        "right_source_labels": right_sample["source_labels"],
        "left_sample_node_ids": left_sample["sample_node_ids"],
        "right_sample_node_ids": right_sample["sample_node_ids"],
        "left": left_sample,
        "right": right_sample,
        "comparison_result": comparison_result,
        "confidence": confidence,
        "missing_proof": missing_proof,
    }


def _derive_derivation_sample_provenance_strength(
    derivation_family_contamination: dict[str, Any],
    semantic_sample_comparison: dict[str, Any],
) -> dict[str, Any]:
    left = dict(semantic_sample_comparison.get("left", {}) or {})
    if not left:
        return {}

    source_labels = sorted(
        str(label) for label in (left.get("source_labels", []) or []) if str(label).strip()
    )
    source_witness_refs = sorted(
        str(ref)
        for ref in (derivation_family_contamination.get("source_witness_refs", []) or [])
        if str(ref).strip()
    )
    derived_refined_node_ids = sorted(
        str(ref)
        for ref in (derivation_family_contamination.get("derived_refined_node_ids", []) or [])
        if str(ref).strip()
    )
    samples = list(left.get("samples", []) or [])
    sample_size = max(1, int(left.get("sample_size", len(samples) or 0)))
    semantic_support_count = int(left.get("semantic_support_sample_count", 0))
    residue_risk_count = int(left.get("residue_risk_sample_count", 0))
    provenance_sparse_count = sum(
        1 for row in samples if bool(row.get("provenance_sparse", False))
    )
    uplift_count = sum(
        1
        for row in samples
        if bool((row.get("signals", {}) or {}).get("stripped_layer", False))
        or bool((row.get("signals", {}) or {}).get("refined_concept", False))
    )
    source_map_family_count = sum(
        1
        for row in samples
        if bool((row.get("signals", {}) or {}).get("source_map_family", False))
    )
    tag_backed_count = sum(
        1
        for row in samples
        if bool((row.get("signals", {}) or {}).get("has_term_tag", False))
        or bool((row.get("signals", {}) or {}).get("has_desc_term", False))
        or bool((row.get("signals", {}) or {}).get("has_family_term", False))
    )
    name_only_count = sum(
        1
        for row in samples
        if bool((row.get("signals", {}) or {}).get("name_only_match", False))
    )

    dual_provenance = any(label.startswith("maker_topic:") for label in source_labels) and any(
        label.startswith("refined_tag:") for label in source_labels
    )
    witness_backed = bool(source_witness_refs)
    lineage_backed = bool(derived_refined_node_ids)
    semantic_support_share = round(semantic_support_count / sample_size, 6)
    residue_risk_share = round(residue_risk_count / sample_size, 6)
    provenance_sparse_share = round(provenance_sparse_count / sample_size, 6)
    uplift_ratio = round(uplift_count / sample_size, 6)
    source_map_sample_share = round(source_map_family_count / sample_size, 6)
    tag_backed_ratio = round(tag_backed_count / sample_size, 6)
    name_only_ratio = round(name_only_count / sample_size, 6)

    risk_flags: list[str] = []
    if provenance_sparse_share >= 0.8:
        risk_flags.append("sample_provenance_sparse")
    if residue_risk_share >= 0.5:
        risk_flags.append("sample_residue_heavy")
    if uplift_ratio < 0.3:
        risk_flags.append("low_cross_zone_uplift")
    if source_map_sample_share > 0.7:
        risk_flags.append("sample_source_map_dominance")
    if not dual_provenance:
        risk_flags.append("missing_dual_provenance")

    if not witness_backed or not lineage_backed:
        assessment_result = "insufficient_for_promotion"
    elif (
        semantic_support_share >= 0.5
        and residue_risk_share < 0.34
        and uplift_ratio >= 0.3
    ):
        assessment_result = "bounded_but_unproven"
    else:
        assessment_result = "mixed_provenance"

    missing_proof = sorted(
        {
            str(flag)
            for flag in (
                list(derivation_family_contamination.get("missing_proof", []) or [])
                + list(semantic_sample_comparison.get("missing_proof", []) or [])
            )
            if str(flag).strip()
        }
    )

    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "evidence_for_future_term_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not promotion approval"
        ),
        "family": "derivation",
        "assessment_result": assessment_result,
        "source_labels": source_labels,
        "source_witness_refs": source_witness_refs,
        "derived_refined_node_ids": derived_refined_node_ids,
        "sample_node_ids": [str(nid) for nid in (left.get("sample_node_ids", []) or [])],
        "provenance_signals": {
            "dual_provenance": dual_provenance,
            "witness_backed": witness_backed,
            "lineage_backed": lineage_backed,
            "sample_semantic_support_share": semantic_support_share,
            "sample_residue_risk_share": residue_risk_share,
            "sample_provenance_sparse_share": provenance_sparse_share,
            "sample_uplift_ratio": uplift_ratio,
            "sample_source_map_share": source_map_sample_share,
            "tag_backed_ratio": tag_backed_ratio,
            "name_only_ratio": name_only_ratio,
        },
        "risk_flags": risk_flags,
        "missing_proof": missing_proof,
    }


def _shortest_path_length(
    adjacency: dict[str, set[str]],
    start: str,
    targets: set[str],
    *,
    max_depth: int = 3,
) -> int | None:
    if start in targets:
        return 0
    seen = {start}
    q: deque[tuple[str, int]] = deque([(start, 0)])
    while q:
        node_id, depth = q.popleft()
        if depth >= max_depth:
            continue
        for neighbor in adjacency.get(node_id, set()):
            if neighbor in seen:
                continue
            next_depth = depth + 1
            if neighbor in targets:
                return next_depth
            seen.add(neighbor)
            q.append((neighbor, next_depth))
    return None


def _derive_derivation_lineage_bridge_audit(
    semantic_sample_comparison: dict[str, Any],
    derivation_sample_provenance_strength: dict[str, Any],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    left = dict(semantic_sample_comparison.get("left", {}) or {})
    if not left:
        return {}

    sample_node_ids = [str(nid) for nid in (left.get("sample_node_ids", []) or [])]
    source_labels = sorted(
        str(label)
        for label in (derivation_sample_provenance_strength.get("source_labels", []) or [])
        if str(label).strip()
    )
    source_witness_refs = sorted(
        str(ref)
        for ref in (
            derivation_sample_provenance_strength.get("source_witness_refs", []) or []
        )
        if str(ref).strip()
    )
    derived_refined_node_ids = sorted(
        str(ref)
        for ref in (
            derivation_sample_provenance_strength.get("derived_refined_node_ids", []) or []
        )
        if str(ref).strip()
    )
    lineage_refs = sorted(
        {
            str(ref)
            for nid in derived_refined_node_ids
            for ref in (graph_nodes.get(nid, {}) or {}).get("lineage_refs", [])
            if str(ref).strip()
        }
    )

    adjacency: dict[str, set[str]] = {}
    for edge in graph_edges:
        source_id = str(edge.get("source_id", ""))
        target_id = str(edge.get("target_id", ""))
        if not source_id or not target_id or source_id == target_id:
            continue
        adjacency.setdefault(source_id, set()).add(target_id)
        adjacency.setdefault(target_id, set()).add(source_id)

    target_intent_nodes = set(derived_refined_node_ids)
    sample_reports: list[dict[str, Any]] = []
    direct_intent_bridge_count = 0
    reachable_within_3_count = 0
    upper_surface_neighbor_count = 0
    no_observed_bridge_count = 0

    for node_id in sample_node_ids:
        neighbors = adjacency.get(node_id, set())
        direct_intent_neighbors = sorted(n for n in neighbors if n in target_intent_nodes)
        if direct_intent_neighbors:
            direct_intent_bridge_count += 1
        shortest_path = _shortest_path_length(
            adjacency,
            node_id,
            target_intent_nodes,
            max_depth=3,
        )
        if shortest_path is not None and shortest_path <= 3:
            reachable_within_3_count += 1
        upper_surface_neighbors = sorted(
            n
            for n in neighbors
            if str((graph_nodes.get(n, {}) or {}).get("layer", "")) == "A1_STRIPPED"
            or str((graph_nodes.get(n, {}) or {}).get("node_type", "")) == "REFINED_CONCEPT"
        )
        if upper_surface_neighbors:
            upper_surface_neighbor_count += 1

        if direct_intent_neighbors:
            bridge_posture = "direct_intent_bridge"
        elif shortest_path is not None and shortest_path <= 2:
            bridge_posture = "short_graph_bridge"
        elif shortest_path == 3:
            bridge_posture = "distant_graph_bridge"
        elif upper_surface_neighbors:
            bridge_posture = "upper_surface_neighbor_only"
        else:
            bridge_posture = "no_observed_bridge"
            no_observed_bridge_count += 1

        sample_reports.append(
            {
                "node_id": node_id,
                "bridge_posture": bridge_posture,
                "direct_intent_neighbors": direct_intent_neighbors,
                "shortest_path_to_intent_refinement": shortest_path,
                "upper_surface_neighbors": upper_surface_neighbors[:5],
            }
        )

    if direct_intent_bridge_count > 0 or reachable_within_3_count >= 2:
        assessment_result = "lineage_visible_but_unproven"
    elif upper_surface_neighbor_count >= 1:
        assessment_result = "bridgeable_via_upper_surfaces_but_unmaterialized"
    else:
        assessment_result = "weak_or_missing_bridge"

    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "evidence_for_future_term_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not promotion approval"
        ),
        "family": "derivation",
        "source_labels": source_labels,
        "source_witness_refs": source_witness_refs,
        "derived_refined_node_ids": derived_refined_node_ids,
        "lineage_refs": lineage_refs,
        "sample_node_ids": sample_node_ids,
        "bridge_status": assessment_result,
        "bridge_signals": {
            "direct_intent_bridge_count": direct_intent_bridge_count,
            "reachable_within_3_hops_count": reachable_within_3_count,
            "upper_surface_neighbor_count": upper_surface_neighbor_count,
            "no_observed_bridge_count": no_observed_bridge_count,
        },
        "sample_bridge_reports": sample_reports,
        "missing_proof": sorted(
            {
                str(flag)
                for flag in (
                    list(
                        derivation_sample_provenance_strength.get("missing_proof", []) or []
                    )
                    + ["execution_binding_proof"]
                )
                if str(flag).strip()
            }
        ),
    }


def _derive_derivation_bridge_materialization_precondition(
    semantic_sample_comparison: dict[str, Any],
    derivation_sample_provenance_strength: dict[str, Any],
    derivation_lineage_bridge: dict[str, Any],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    left = dict(semantic_sample_comparison.get("left", {}) or {})
    if not left:
        return {}

    sample_node_ids = [str(nid) for nid in (left.get("sample_node_ids", []) or [])]
    sample_bridge_reports = [
        dict(row)
        for row in (derivation_lineage_bridge.get("sample_bridge_reports", []) or [])
        if isinstance(row, dict)
    ]
    bridge_reports_by_id = {
        str(row.get("node_id", "")): row
        for row in sample_bridge_reports
        if str(row.get("node_id", "")).strip()
    }
    source_labels = sorted(
        str(label)
        for label in (derivation_sample_provenance_strength.get("source_labels", []) or [])
        if str(label).strip()
    )
    source_witness_refs = sorted(
        str(ref)
        for ref in (
            derivation_sample_provenance_strength.get("source_witness_refs", []) or []
        )
        if str(ref).strip()
    )
    target_refined_intent_id = str(
        (
            derivation_lineage_bridge.get("derived_refined_node_ids", [])
            or derivation_sample_provenance_strength.get("derived_refined_node_ids", [])
            or [""]
        )[0]
    ).strip()
    target_intent_ids = set(
        str(ref)
        for ref in (
            derivation_lineage_bridge.get("derived_refined_node_ids", [])
            or derivation_sample_provenance_strength.get("derived_refined_node_ids", [])
            or []
        )
        if str(ref).strip()
    )

    adjacency: dict[str, set[str]] = {}
    for edge in graph_edges:
        source_id = str(edge.get("source_id", ""))
        target_id = str(edge.get("target_id", ""))
        if not source_id or not target_id or source_id == target_id:
            continue
        adjacency.setdefault(source_id, set()).add(target_id)
        adjacency.setdefault(target_id, set()).add(source_id)

    upper_surface_bridge_source_ids: list[str] = []
    upper_surface_candidate_ids: set[str] = set()
    for row in sample_bridge_reports:
        if str(row.get("bridge_posture", "")) != "upper_surface_neighbor_only":
            continue
        source_id = str(row.get("node_id", "")).strip()
        if source_id:
            upper_surface_bridge_source_ids.append(source_id)
        for neighbor_id in (row.get("upper_surface_neighbors", []) or []):
            neighbor_text = str(neighbor_id).strip()
            if neighbor_text:
                upper_surface_candidate_ids.add(neighbor_text)

    candidate_ids: set[str] = set(upper_surface_candidate_ids)
    for node_id in sample_node_ids:
        node = graph_nodes.get(node_id, {}) or {}
        layer = str(node.get("layer", ""))
        node_type = str(node.get("node_type", ""))
        if layer == "A1_STRIPPED" or node_type == "REFINED_CONCEPT":
            candidate_ids.add(node_id)

    candidate_reviews: list[dict[str, Any]] = []
    for node_id in sorted(candidate_ids):
        node = graph_nodes.get(node_id, {}) or {}
        layer = str(node.get("layer", ""))
        node_type = str(node.get("node_type", ""))
        name = str(node.get("name", ""))
        description = str(node.get("description", ""))
        tags = [str(tag) for tag in (node.get("tags", []) or [])]
        corpus = _concept_corpus(node)
        neighbors = sorted(adjacency.get(node_id, set()))
        is_a1_stripped = layer == "A1_STRIPPED"
        is_refined_concept = node_type == "REFINED_CONCEPT"
        archive_like = "archived work file" in description.lower()
        semantic_description_present = bool(description.strip()) and not archive_like
        has_derivation_language = "derivation" in corpus
        kernel_neighbor_count = sum(1 for n in neighbors if n.startswith("A2_1::KERNEL"))
        refined_neighbor_count = sum(1 for n in neighbors if n.startswith("A2_2::REFINED"))
        source_map_neighbor_count = sum(
            1 for n in neighbors if _node_family_label(n).endswith("SOURCE_MAP_PASS")
        )
        direct_intent_neighbor_count = sum(1 for n in neighbors if n in target_intent_ids)
        shortest_path = (
            _shortest_path_length(adjacency, node_id, target_intent_ids, max_depth=3)
            if target_intent_ids
            else None
        )
        witness_backed = bool(node.get("witness_refs"))
        lineage_backed = bool(node.get("lineage_refs"))
        seeded_from_bridge_path = node_id in upper_surface_candidate_ids

        score = 0
        selection_basis: list[str] = []
        hard_blockers: list[str] = []
        missing_proof: list[str] = []

        if seeded_from_bridge_path:
            score += 3
            selection_basis.append("observed_upper_surface_bridge_path")
        if is_a1_stripped:
            score += 4
            selection_basis.append("a1_stripped_upper_surface")
        if is_refined_concept:
            score += 2
            selection_basis.append("refined_concept")
        if semantic_description_present:
            score += 2
            selection_basis.append("non_archive_semantic_description")
        if has_derivation_language:
            score += 1
            selection_basis.append("derivation_language_present")
        if kernel_neighbor_count > 0:
            score += 2
            selection_basis.append("kernel_neighbor_support")
        if refined_neighbor_count > 0:
            score += 2
            selection_basis.append("refined_neighbor_support")
        if source_map_neighbor_count > 0:
            score += 1
            selection_basis.append("source_map_family_linkage")
        if archive_like:
            score -= 4
            selection_basis.append("archive_like_description_penalty")

        if not (witness_backed or lineage_backed):
            hard_blockers.append("missing_direct_candidate_provenance")
            missing_proof.append("direct_candidate_provenance")
        if direct_intent_neighbor_count == 0 and shortest_path is None:
            hard_blockers.append("no_direct_or_short_graph_bridge_to_intent")
            missing_proof.append("materialized_lineage_bridge")
        if not semantic_description_present:
            hard_blockers.append("candidate_semantics_too_thin")
            missing_proof.append("semantic_middle_surface_proof")
        hard_blockers.append("no_existing_relation_label_for_honest_intent_alignment")
        missing_proof.append("relation_semantics_review")

        candidate_reviews.append(
            {
                "node_id": node_id,
                "name": name,
                "layer": layer,
                "node_type": node_type,
                "score": score,
                "selection_basis": selection_basis,
                "semantic_support": {
                    "a1_stripped": is_a1_stripped,
                    "refined_concept": is_refined_concept,
                    "semantic_description_present": semantic_description_present,
                    "archive_like": archive_like,
                    "has_derivation_language": has_derivation_language,
                    "kernel_neighbor_count": kernel_neighbor_count,
                    "refined_neighbor_count": refined_neighbor_count,
                    "source_map_neighbor_count": source_map_neighbor_count,
                },
                "provenance_support": {
                    "witness_backed": witness_backed,
                    "lineage_backed": lineage_backed,
                },
                "bridge_support": {
                    "seeded_from_bridge_path": seeded_from_bridge_path,
                    "direct_intent_neighbor_count": direct_intent_neighbor_count,
                    "shortest_path_to_intent_refinement": shortest_path,
                },
                "hard_blockers": sorted(set(hard_blockers)),
                "missing_proof": sorted(set(missing_proof)),
            }
        )

    if not candidate_reviews:
        return {
            "status": "audit_only_nonoperative",
            "audit_only": True,
            "runtime_effect": "none",
            "family": "derivation",
            "path_term": "derivation",
            "source_labels": source_labels,
            "source_witness_refs": source_witness_refs,
            "target_refined_intent_id": target_refined_intent_id,
            "single_bridgeable_path": False,
            "bridge_source_node_ids": upper_surface_bridge_source_ids,
            "candidate_middle_node_id": "",
            "materialization_allowed_in_current_surface": False,
            "decision": "keep_self_audit_only_no_candidate",
            "missing_proof": ["semantic_middle_surface_proof", "execution_binding_proof"],
        }

    candidate_reviews.sort(key=lambda row: (-int(row["score"]), str(row["node_id"])))
    selected = candidate_reviews[0]
    materialization_allowed = not selected.get("hard_blockers")
    relation_options = [
        {
            "relation": "RELATED_TO",
            "fit": "weakest_existing_non_overclaiming_label",
            "selected_if_future_materialization_occurs": True,
            "admissible_now": materialization_allowed,
        },
        {
            "relation": "STRUCTURALLY_RELATED",
            "fit": "overstates_structure_equivalence_with_intent_surface",
            "selected_if_future_materialization_occurs": False,
            "admissible_now": False,
        },
        {
            "relation": "REFINES_INTENT",
            "fit": "invalid_direction_and_overclaims_provenance",
            "selected_if_future_materialization_occurs": False,
            "admissible_now": False,
        },
    ]

    missing_proof = sorted(
        {
            str(flag)
            for flag in (
                list(selected.get("missing_proof", []) or [])
                + list(derivation_lineage_bridge.get("missing_proof", []) or [])
                + ["execution_binding_proof"]
            )
            if str(flag).strip()
        }
    )

    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "single_bridgeable_path_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not promotion approval"
        ),
        "family": "derivation",
        "path_term": "derivation",
        "source_labels": source_labels,
        "source_witness_refs": source_witness_refs,
        "target_refined_intent_id": target_refined_intent_id,
        "single_bridgeable_path": (
            len(upper_surface_bridge_source_ids) == 1 and len(upper_surface_candidate_ids) == 1
        ),
        "bridge_source_node_ids": upper_surface_bridge_source_ids,
        "candidate_middle_node_id": str(selected.get("node_id", "")),
        "candidate_middle_node_name": str(selected.get("name", "")),
        "candidate_middle_node_layer": str(selected.get("layer", "")),
        "candidate_middle_node_type": str(selected.get("node_type", "")),
        "candidate_selection_basis": list(selected.get("selection_basis", []) or []),
        "candidate_support": {
            "semantic_support": dict(selected.get("semantic_support", {}) or {}),
            "provenance_support": dict(selected.get("provenance_support", {}) or {}),
            "bridge_support": dict(selected.get("bridge_support", {}) or {}),
        },
        "recommended_relation": "RELATED_TO",
        "relation_option_review": relation_options,
        "materialization_allowed_in_current_surface": materialization_allowed,
        "decision": (
            "keep_self_audit_only_no_edge_materialization"
            if not materialization_allowed
            else "candidate_ready_for_manual_review"
        ),
        "hard_blockers": list(selected.get("hard_blockers", []) or []),
        "missing_proof": missing_proof,
        "candidate_reviews": candidate_reviews[:4],
    }


def _derive_candidate_provenance_backfill_precondition(
    derivation_bridge_materialization_precondition: dict[str, Any],
    *,
    graph_nodes: dict[str, dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    target_node_id = str(
        derivation_bridge_materialization_precondition.get("candidate_middle_node_id", "")
    ).strip()
    if not target_node_id:
        return {}

    target_node = graph_nodes.get(target_node_id, {}) or {}
    target_corpus = _concept_corpus(target_node)

    donor_rows_by_id: dict[str, dict[str, Any]] = {}
    supporting_source_doc_ids: set[str] = set()
    supporting_edge_relations: set[str] = set()
    bridge_source_node_ids = [
        str(nid)
        for nid in (
            derivation_bridge_materialization_precondition.get("bridge_source_node_ids", [])
            or []
        )
        if str(nid).strip()
    ]

    for edge in graph_edges:
        source_id = str(edge.get("source_id", ""))
        target_id = str(edge.get("target_id", ""))
        if target_node_id not in {source_id, target_id}:
            continue
        donor_id = target_id if source_id == target_node_id else source_id
        donor_node = graph_nodes.get(donor_id, {}) or {}
        relation = str(edge.get("relation", ""))
        if not donor_node:
            continue
        donor_layer = str(donor_node.get("layer", ""))
        donor_type = str(donor_node.get("node_type", ""))
        if donor_type not in {
            "EXTRACTED_CONCEPT",
            "REFINED_CONCEPT",
            "KERNEL_CONCEPT",
            "SOURCE_DOCUMENT",
        }:
            continue
        donor_corpus = _concept_corpus(donor_node)
        shared_tokens = sorted(
            {
                tok
                for tok in target_corpus.split()
                if tok and tok in donor_corpus and len(tok) >= 6
            }
        )
        semantic_score = len(shared_tokens)
        if relation in {"STRIPPED_FROM", "ROSETTA_MAP"}:
            semantic_score += 4
        elif relation == "STRUCTURALLY_RELATED":
            semantic_score += 2
        elif relation == "SOURCE_MAP_PASS":
            semantic_score += 1

        hygiene_score = 0
        if donor_id.startswith("A2_2::REFINED"):
            hygiene_score += 5
        elif donor_id.startswith("A2_1::KERNEL"):
            hygiene_score += 4
        elif donor_id.startswith("A2_3::SOURCE_MAP_PASS"):
            hygiene_score += 2
        elif donor_type == "SOURCE_DOCUMENT":
            hygiene_score += 1
        if relation in {"STRIPPED_FROM", "ROSETTA_MAP"}:
            hygiene_score += 2
        elif relation == "STRUCTURALLY_RELATED":
            hygiene_score += 1

        witness_backed = bool(donor_node.get("witness_refs"))
        lineage_backed = bool(donor_node.get("lineage_refs"))
        if witness_backed:
            hygiene_score += 1
        if lineage_backed:
            hygiene_score += 1

        if donor_type == "SOURCE_DOCUMENT":
            supporting_source_doc_ids.add(donor_id)
        supporting_edge_relations.add(relation)
        row = donor_rows_by_id.get(donor_id)
        if row is None:
            donor_rows_by_id[donor_id] = {
                "node_id": donor_id,
                "name": str(donor_node.get("name", "")),
                "layer": donor_layer,
                "node_type": donor_type,
                "relations_to_target": [relation] if relation else [],
                "semantic_score": semantic_score,
                "hygiene_score": hygiene_score,
                "shared_tokens": shared_tokens[:8],
                "witness_backed": witness_backed,
                "lineage_backed": lineage_backed,
            }
        else:
            relations = set(row.get("relations_to_target", []) or [])
            if relation:
                relations.add(relation)
            row["relations_to_target"] = sorted(relations)
            row["semantic_score"] = max(int(row.get("semantic_score", 0)), semantic_score)
            row["hygiene_score"] = max(int(row.get("hygiene_score", 0)), hygiene_score)
            row["shared_tokens"] = sorted(
                {
                    *[str(tok) for tok in (row.get("shared_tokens", []) or [])],
                    *shared_tokens[:8],
                }
            )[:8]
            row["witness_backed"] = bool(row.get("witness_backed")) or witness_backed
            row["lineage_backed"] = bool(row.get("lineage_backed")) or lineage_backed

    donor_rows = list(donor_rows_by_id.values())

    semantic_donor_candidates = [
        row["node_id"]
        for row in sorted(
            donor_rows,
            key=lambda row: (-int(row["semantic_score"]), str(row["node_id"])),
        )
        if row["semantic_score"] > 0
    ]
    hygiene_donor_candidates = [
        row["node_id"]
        for row in sorted(
            donor_rows,
            key=lambda row: (-int(row["hygiene_score"]), str(row["node_id"])),
        )
        if row["hygiene_score"] > 0
    ]
    candidate_backfill_source_node_ids = list(
        dict.fromkeys(hygiene_donor_candidates[:2] + semantic_donor_candidates[:2])
    )
    supporting_bridge_target_ids = list(
        dict.fromkeys(semantic_donor_candidates[:3] + hygiene_donor_candidates[:3])
    )

    hard_blockers: list[str] = []
    missing_proof: list[str] = []
    if not target_node.get("witness_refs") and not target_node.get("lineage_refs"):
        hard_blockers.append("target_has_no_direct_provenance")
        missing_proof.append("direct_candidate_provenance")
    if not any(row["witness_backed"] or row["lineage_backed"] for row in donor_rows):
        hard_blockers.append("donor_chain_has_no_direct_provenance")
        missing_proof.append("donor_witness_lineage_proof")
    if candidate_backfill_source_node_ids:
        hard_blockers.append("basis_is_indirect_graph_chain_only")
    else:
        hard_blockers.append("no_candidate_backfill_donor_chain")
        missing_proof.append("source_concept_id_backfill_proof")
    hard_blockers.append("direct_field_backfill_would_overclaim_provenance")
    missing_proof.extend(
        [
            "noncanonical_field_admission_review",
            "source_concept_id_backfill_proof",
        ]
    )

    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "audit_overlay_precondition_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not admission approval"
        ),
        "target_node_id": target_node_id,
        "target_node_layer": str(target_node.get("layer", "")),
        "target_node_type": str(target_node.get("node_type", "")),
        "candidate_backfill_source_node_ids": candidate_backfill_source_node_ids,
        "supporting_bridge_target_ids": supporting_bridge_target_ids,
        "bridge_source_node_ids": bridge_source_node_ids,
        "recommended_noncanonical_fields": [
            "properties.overlay_provenance_audit.status",
            "properties.overlay_provenance_audit.overlay_kind",
            "properties.overlay_provenance_audit.primary_donor_chain",
            "properties.overlay_provenance_audit.basis_edge_relations",
            "properties.overlay_provenance_audit.supporting_source_doc_ids",
            "properties.overlay_provenance_audit.disclaimers",
        ],
        "do_not_backfill_fields": ["lineage_refs", "witness_refs"],
        "precondition_status": "audit_only_precondition",
        "admissible_now": False,
        "materialization_allowed_in_current_surface": False,
        "relation_chain_summary": {
            "supporting_edge_relations": sorted(supporting_edge_relations),
            "supporting_source_doc_ids": sorted(supporting_source_doc_ids),
        },
        "donor_review": {
            "semantic_donor_candidates": semantic_donor_candidates[:4],
            "hygiene_donor_candidates": hygiene_donor_candidates[:4],
            "rows": donor_rows[:8],
        },
        "decision": "keep_self_audit_only_no_provenance_backfill",
        "hard_blockers": sorted(set(hard_blockers)),
        "missing_proof": sorted(set(missing_proof)),
    }


def _derive_stripped_provenance_annotation_admission(
    stripped_provenance_backfill_precondition: dict[str, Any],
) -> dict[str, Any]:
    if not stripped_provenance_backfill_precondition:
        return {}

    candidate_backfill_source_node_ids = [
        str(nid)
        for nid in (
            stripped_provenance_backfill_precondition.get(
                "candidate_backfill_source_node_ids", []
            )
            or []
        )
        if str(nid).strip()
    ]
    return {
        "status": "audit_only_nonoperative",
        "audit_only": True,
        "runtime_effect": "none",
        "intent": "namespaced_properties_overlay_review_only",
        "doctrine_posture": (
            "not executable policy; not steering guidance; not admission approval"
        ),
        "target_node_id": str(
            stripped_provenance_backfill_precondition.get("target_node_id", "")
        ),
        "target_node_layer": str(
            stripped_provenance_backfill_precondition.get("target_node_layer", "")
        ),
        "annotation_path": "properties.overlay_provenance_audit",
        "admissible_now": False,
        "manual_review_required": True,
        "builder_supports_properties_merge": True,
        "write_scope": "namespaced_audit_overlay_only_no_provenance_field_mutation",
        "basis_node_ids": candidate_backfill_source_node_ids,
        "basis_edge_relations": list(
            (
                stripped_provenance_backfill_precondition.get(
                    "relation_chain_summary", {}
                )
                or {}
            ).get("supporting_edge_relations", [])
            or []
        ),
        "safest_annotation_shape": {
            "field": "properties.overlay_provenance_audit",
            "allowed_fields": [
                "status",
                "overlay_kind",
                "authority_posture",
                "manual_review_required",
                "primary_donor_chain",
                "secondary_context_node_ids",
                "basis_edge_relations",
                "supporting_source_doc_ids",
                "bridge_source_node_ids",
                "disclaimers",
            ],
        },
        "forbidden_fields": [
            "lineage_refs",
            "witness_refs",
            "source_class",
            "trust_zone",
            "authority",
            "admissibility_state",
            "properties.source_concept_id",
            "properties.target_ref",
            "properties.candidate_id",
        ],
        "decision": "keep_fail_closed_namespaced_overlay_only_manual_review",
        "hard_blockers": sorted(
            {
                *[
                    str(flag)
                    for flag in (
                        stripped_provenance_backfill_precondition.get(
                            "hard_blockers", []
                        )
                        or []
                    )
                    if str(flag).strip()
                ],
                "no_grounded_trace_anchor",
            }
        ),
        "missing_proof": sorted(
            [
                str(flag)
                for flag in (
                    stripped_provenance_backfill_precondition.get("missing_proof", [])
                    or []
                )
                if str(flag).strip()
                and str(flag) != "source_concept_id_backfill_proof"
            ]
        ),
    }


def _assess_steering_quality(
    focus_term_quality: list[dict[str, Any]],
    steering_focus_terms: list[str],
    non_negotiables: list[dict[str, Any]],
) -> dict[str, Any]:
    weak_top_terms = [
        str(item["term"])
        for item in focus_term_quality[:6]
        if not item.get("steering_safe")
    ]
    reasons: list[str] = []
    if len(steering_focus_terms) < 3:
        reasons.append("too_few_steering_focus_terms")
    if len(non_negotiables) < 2:
        reasons.append("too_few_non_negotiables")
    if len(weak_top_terms) >= 2:
        reasons.append("weak_top_focus_terms")
    return {
        "status": "degraded" if reasons else "strong",
        "downgrade_applied": bool(reasons),
        "reasons": reasons,
        "descriptive_focus_term_count": len(focus_term_quality),
        "steering_focus_term_count": len(steering_focus_terms),
        "top_weak_terms": weak_top_terms[:4],
    }


def _summarize(records: list[dict[str, Any]], key: str = "text", limit: int = 3) -> str:
    snippets = [str(rec.get(key, "")).strip() for rec in records[:limit] if rec.get(key)]
    return " | ".join(snippets)


def build_intent_control_surface(repo_root: str) -> dict[str, Any]:
    repo = Path(repo_root)
    witness_path = repo / WITNESS_REL_PATH
    graph_path = repo / GRAPH_REL_PATH
    out_path = repo / SURFACE_REL_PATH
    audit_path = repo / AUDIT_REL_PATH

    witness_corpus = _load_json(witness_path, [])
    graph = _load_json(graph_path, {"nodes": {}, "edges": []})
    graph_nodes = graph.get("nodes", {}) if isinstance(graph, dict) else {}

    maker_intents = _normalize_intents(witness_corpus if isinstance(witness_corpus, list) else [])
    runtime_contexts = _normalize_contexts(witness_corpus if isinstance(witness_corpus, list) else [])
    refined_intents = _normalize_refined_intents(graph_nodes if isinstance(graph_nodes, dict) else {})

    non_negotiables = _derive_non_negotiables(maker_intents, refined_intents)
    executable_non_negotiables = _derive_executable_non_negotiables(non_negotiables)
    focus_term_quality = _build_focus_term_quality(maker_intents, refined_intents, non_negotiables)
    focus_terms = _derive_focus_terms_from_quality(focus_term_quality)
    steering_focus_terms = _derive_steering_focus_terms(focus_term_quality)
    executable_focus_terms, executable_focus_graph_metrics = _derive_executable_focus_terms(
        steering_focus_terms,
        focus_term_quality,
        graph_nodes if isinstance(graph_nodes, dict) else {},
    )
    executable_focus_refinement_candidates = _derive_executable_focus_refinement_candidates(
        maker_intents,
        refined_intents,
        graph_nodes if isinstance(graph_nodes, dict) else {},
        executable_focus_terms,
    )
    executable_focus_promotion_readiness = _derive_executable_focus_promotion_readiness(
        executable_focus_refinement_candidates,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
        graph_edges=graph.get("edges", []) if isinstance(graph, dict) else [],
        executable_focus_terms=executable_focus_terms,
        gate_min_concepts=2,
    )
    execution_binding_probes = _derive_execution_binding_probes(
        executable_focus_promotion_readiness,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
        executable_focus_terms=executable_focus_terms,
        gate_min_concepts=2,
    )
    for item, probe in zip(executable_focus_promotion_readiness, execution_binding_probes):
        item["execution_binding_probe"] = probe
    executable_focus_semantic_comparison = _derive_executable_focus_semantic_comparison(
        executable_focus_promotion_readiness,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
        executable_focus_terms=executable_focus_terms,
    )
    derivation_family_contamination = _derive_derivation_family_contamination_audit(
        executable_focus_promotion_readiness,
        executable_focus_semantic_comparison,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
    )
    semantic_sample_comparison = _derive_semantic_sample_comparison(
        executable_focus_promotion_readiness,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
        executable_focus_terms=executable_focus_terms,
    )
    derivation_sample_provenance_strength = _derive_derivation_sample_provenance_strength(
        derivation_family_contamination,
        semantic_sample_comparison,
    )
    derivation_lineage_bridge = _derive_derivation_lineage_bridge_audit(
        semantic_sample_comparison,
        derivation_sample_provenance_strength,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
        graph_edges=graph.get("edges", []) if isinstance(graph, dict) else [],
    )
    derivation_bridge_materialization_precondition = (
        _derive_derivation_bridge_materialization_precondition(
            semantic_sample_comparison,
            derivation_sample_provenance_strength,
            derivation_lineage_bridge,
            graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
            graph_edges=graph.get("edges", []) if isinstance(graph, dict) else [],
        )
    )
    stripped_provenance_backfill_precondition = (
        _derive_candidate_provenance_backfill_precondition(
            derivation_bridge_materialization_precondition,
            graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
            graph_edges=graph.get("edges", []) if isinstance(graph, dict) else [],
        )
    )
    stripped_provenance_annotation_admission = (
        _derive_stripped_provenance_annotation_admission(
            stripped_provenance_backfill_precondition
        )
    )
    steering_quality = _assess_steering_quality(
        focus_term_quality,
        executable_focus_terms,
        non_negotiables,
    )
    queue_notes = [rec for rec in maker_intents if rec.get("type") == "queue_notes"]

    open_tensions: list[str] = []
    if not maker_intents:
        open_tensions.append("No intent witnesses available; control surface is running without preserved maker intent.")
    if not runtime_contexts:
        open_tensions.append("No runtime context witnesses available; control surface lacks live batch context.")
    if not refined_intents:
        open_tensions.append("No INTENT_REFINEMENT graph nodes available; control surface is derived directly from raw intent/context witnesses.")
    if not focus_terms:
        open_tensions.append("No stable focus terms extracted; concept steering remains visibility-only.")
    if steering_quality["downgrade_applied"]:
        open_tensions.append(
            "Intent steering quality degraded; using reorder-only concept selection and disabling candidate suppression."
        )
    pruned_executable_terms = executable_focus_graph_metrics.get("pruned_terms", []) or []
    if pruned_executable_terms:
        open_tensions.append(
            f"Graph-discrimination pruned {len(pruned_executable_terms)} broad or redundant steering terms from executable use."
        )
    if executable_focus_refinement_candidates:
        open_tensions.append(
            f"{len(executable_focus_refinement_candidates)} narrower graph-backed intent-term candidates are available for future executable refinement."
        )
    if executable_focus_promotion_readiness:
        open_tensions.append(
            "No staged semantic executable term is promoted yet; promotion readiness remains audit-only pending cluster precision and execution-binding proof."
        )
    positive_execution_binding_probe_count = sum(
        1
        for item in executable_focus_promotion_readiness
        if (item.get("execution_binding_probe", {}) or {}).get("status")
        == "bounded_positive_effect"
    )
    if positive_execution_binding_probe_count:
        open_tensions.append(
            f"{positive_execution_binding_probe_count} staged semantic term(s) show bounded positive execution-binding probe results but remain audit-only pending manual promotion review."
        )
    if executable_focus_semantic_comparison:
        open_tensions.append(
            "Structural and semantic staged-term signals are compared explicitly, but disagreement still resolves to audit-only."
        )
    if derivation_family_contamination:
        open_tensions.append(
            "Derivation staged-term contamination evidence is tracked in self_audit only and remains non-operative."
        )
    if semantic_sample_comparison:
        open_tensions.append(
            "Semantic sample comparison between derivation and integration is tracked in self_audit only and remains non-operative."
        )
    if derivation_sample_provenance_strength:
        open_tensions.append(
            "Derivation sample provenance strength is tracked in self_audit only and remains non-operative."
        )
    if derivation_lineage_bridge:
        open_tensions.append(
            "Derivation lineage bridge audit is tracked in self_audit only and remains non-operative."
        )
    if derivation_bridge_materialization_precondition:
        open_tensions.append(
            "Derivation bridge materialization preconditions are tracked in self_audit only and remain non-operative."
        )
    if stripped_provenance_backfill_precondition:
        open_tensions.append(
            "Stripped provenance backfill preconditions are tracked in self_audit only and remain non-operative."
        )
    if stripped_provenance_annotation_admission:
        open_tensions.append(
            "Stripped provenance annotation admission is tracked in self_audit only and remains non-operative."
        )

    runtime_policy = build_runtime_policy(
        focus_terms,
        non_negotiables,
        executable_focus_terms=executable_focus_terms,
        executable_non_negotiables=executable_non_negotiables,
        executable_focus_refinement_candidates=executable_focus_refinement_candidates,
        executable_focus_promotion_readiness=executable_focus_promotion_readiness,
        executable_focus_semantic_comparison=executable_focus_semantic_comparison,
    )
    runtime_policy["focus_term_quality"] = focus_term_quality[:12]
    runtime_policy["steering_focus_terms"] = steering_focus_terms
    runtime_policy["executable_focus_terms"] = executable_focus_terms
    runtime_policy["executable_non_negotiables"] = [
        item.get("label", "")
        for item in executable_non_negotiables
        if item.get("label")
    ]
    runtime_policy["executable_focus_graph_metrics"] = executable_focus_graph_metrics
    runtime_policy["executable_focus_refinement_candidates"] = (
        executable_focus_refinement_candidates
    )
    runtime_policy["executable_focus_promotion_readiness"] = (
        executable_focus_promotion_readiness
    )
    runtime_policy["executable_focus_semantic_comparison"] = (
        executable_focus_semantic_comparison
    )
    runtime_policy["steering_quality"] = steering_quality
    runtime_policy["concept_selection"]["focus_terms"] = focus_terms
    runtime_policy["concept_selection"]["gating_focus_terms"] = executable_focus_terms
    runtime_policy["bias_config"]["intent_focus_terms"] = executable_focus_terms
    runtime_policy["bias_config"]["intent_non_negotiables"] = list(
        runtime_policy["executable_non_negotiables"]
    )
    if steering_quality["downgrade_applied"]:
        runtime_policy["concept_selection"]["mode"] = "reorder_only"
        runtime_policy["candidate_policy"]["mode"] = "disabled"
        runtime_policy["candidate_policy"]["apply_on_modes"] = []
        runtime_policy["candidate_policy"]["suppress_term_defs_without_focus"] = False
        runtime_policy["candidate_policy"]["disabled_reason"] = "degraded_steering_quality"

    promotion_ready_count = sum(
        1
        for item in executable_focus_promotion_readiness
        if item.get("readiness_status") != "hold_audit_only"
    )
    cluster_precision_candidate_count = sum(
        1
        for item in executable_focus_promotion_readiness
        if item.get("readiness_status") == "candidate_for_cluster_precision_check"
    )
    execution_binding_candidate_count = sum(
        1
        for item in executable_focus_promotion_readiness
        if item.get("readiness_status") == "candidate_for_execution_binding_check"
    )
    execution_binding_positive_probe_count = sum(
        1
        for item in executable_focus_promotion_readiness
        if (item.get("execution_binding_probe", {}) or {}).get("status")
        == "bounded_positive_effect"
    )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "surface_id": f"A2_INTENT_CONTROL__{_utc_iso()}",
        "classification": {
            "surface_class": "DERIVED_A2",
            "status": "NONCANONICAL_ACTIVE_CONTROL",
            "authority_posture": "intent-preserving derived control surface; not doctrine; not earned truth",
            "scope": "current repo-held runtime and A2 memory surfaces",
            "ts_utc": _utc_iso(),
        },
        "provenance": {
            "graph_json_path": GRAPH_REL_PATH,
            "witness_corpus_path": WITNESS_REL_PATH,
            "graph_node_ids": [rec["node_id"] for rec in refined_intents],
            "witness_entry_refs": [rec["witness_ref"] for rec in maker_intents + runtime_contexts],
            "source_count": len(maker_intents) + len(runtime_contexts) + len(refined_intents),
        },
        "maker_intent": {
            "summary": _summarize(maker_intents),
            "records": maker_intents,
            "queue_notes": queue_notes,
            "priority_order": [rec["priority"] for rec in maker_intents if rec.get("priority")],
            "constraints": non_negotiables,
        },
        "refined_intent": {
            "summary": _summarize(refined_intents),
            "records": refined_intents,
            "decision_rule": "Prefer graph-native intent refinements when present; otherwise preserve raw intent witnesses verbatim.",
            "do_now": [directive["statement"] for directive in non_negotiables],
            "do_not_do": [
                "Do not treat this surface as doctrine or lower-loop truth.",
                "Do not discard raw maker intent when refining it.",
            ],
        },
        "runtime_context": {
            "summary": _summarize(runtime_contexts),
            "records": runtime_contexts,
            "batch_ids": sorted({rec["batch"] for rec in runtime_contexts if rec.get("batch")}),
            "pending_actions": [],
            "expires_on_refresh": True,
        },
        "control": {
            "lane_id": "INTENT_PRESERVING_CURRENT",
            "focus_terms": runtime_policy["focus_terms"],
            "steering_focus_terms": runtime_policy["steering_focus_terms"],
            "executable_focus_terms": runtime_policy["executable_focus_terms"],
            "executable_non_negotiables": runtime_policy["executable_non_negotiables"],
            "executable_focus_graph_metrics": runtime_policy["executable_focus_graph_metrics"],
            "executable_focus_refinement_candidates": runtime_policy[
                "executable_focus_refinement_candidates"
            ],
            "executable_focus_promotion_readiness": runtime_policy[
                "executable_focus_promotion_readiness"
            ],
            "executable_focus_semantic_comparison": runtime_policy[
                "executable_focus_semantic_comparison"
            ],
            "runtime_policy": runtime_policy,
            "bias_config": runtime_policy["bias_config"],
            "control_priorities": [rec["text"] for rec in maker_intents[:5]],
            "packet_policy_notes": [
                "A1 must record consumed intent control explicitly in packet inputs/self_audit.",
                "Intent control is bounded guidance, not lower-loop truth.",
            ],
            "concept_selection": runtime_policy["concept_selection"],
            "candidate_policy": runtime_policy["candidate_policy"],
            "alternative_policy": runtime_policy["alternative_policy"],
        },
        "open_tensions": open_tensions,
        "self_audit": {
            "maker_intent_count": len(maker_intents),
            "runtime_context_count": len(runtime_contexts),
            "refined_intent_count": len(refined_intents),
            "queue_note_count": len(queue_notes),
            "focus_term_count": len(focus_terms),
            "steering_focus_term_count": len(steering_focus_terms),
            "executable_focus_term_count": len(executable_focus_terms),
            "executable_non_negotiable_count": len(executable_non_negotiables),
            "executable_focus_refinement_candidate_count": len(
                executable_focus_refinement_candidates
            ),
            "executable_focus_promotion_ready_count": promotion_ready_count,
            "executable_focus_cluster_precision_candidate_count": (
                cluster_precision_candidate_count
            ),
            "executable_focus_execution_binding_candidate_count": (
                execution_binding_candidate_count
            ),
            "executable_focus_execution_binding_positive_probe_count": (
                execution_binding_positive_probe_count
            ),
            "steering_quality_status": steering_quality["status"],
            "non_negotiable_count": len(non_negotiables),
            "source_ids": [rec["witness_ref"] for rec in maker_intents] + [rec["node_id"] for rec in refined_intents],
            "derivation_family_contamination": derivation_family_contamination,
            "semantic_sample_comparison": {
                "derivation_vs_integration": semantic_sample_comparison,
            },
            "derivation_sample_provenance_strength": (
                derivation_sample_provenance_strength
            ),
            "derivation_lineage_bridge": derivation_lineage_bridge,
            "derivation_bridge_materialization_precondition": (
                derivation_bridge_materialization_precondition
            ),
            "stripped_provenance_backfill_precondition": (
                stripped_provenance_backfill_precondition
            ),
            "stripped_provenance_annotation_admission": (
                stripped_provenance_annotation_admission
            ),
        },
    }
    payload["provenance"]["surface_hash"] = _hash_payload(payload)
    payload["self_audit"]["surface_hash"] = payload["provenance"]["surface_hash"]
    payload["self_audit"]["stripped_provenance_overlay_archive_path"] = (
        PROVENANCE_OVERLAY_REL_PATH
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    overlay_payload = _build_stripped_provenance_overlay_archive(
        payload=payload,
        graph_nodes=graph_nodes if isinstance(graph_nodes, dict) else {},
        graph_edges=graph.get("edges", []) if isinstance(graph, dict) else [],
    )
    overlay_path = repo / PROVENANCE_OVERLAY_REL_PATH
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_text(
        json.dumps(overlay_payload, indent=2) + "\n", encoding="utf-8"
    )

    audit_lines = [
        "# A2 Intent Control Surface Build Audit",
        "",
        f"- schema: `{SCHEMA}`",
        f"- json_path: `{SURFACE_REL_PATH}`",
        f"- maker_intents: `{len(maker_intents)}`",
        f"- runtime_contexts: `{len(runtime_contexts)}`",
        f"- refined_intents: `{len(refined_intents)}`",
        f"- focus_terms: `{len(focus_terms)}`",
        f"- steering_focus_terms: `{len(steering_focus_terms)}`",
        f"- executable_focus_terms: `{len(executable_focus_terms)}`",
        f"- executable_focus_refinement_candidates: `{len(executable_focus_refinement_candidates)}`",
        f"- executable_focus_promotion_ready: `{promotion_ready_count}`",
        f"- executable_focus_cluster_precision_candidates: `{cluster_precision_candidate_count}`",
        f"- executable_focus_execution_binding_candidates: `{execution_binding_candidate_count}`",
        f"- executable_focus_execution_binding_positive_probes: `{execution_binding_positive_probe_count}`",
        f"- non_negotiables: `{len(non_negotiables)}`",
        "",
        "## Focus Terms",
        "",
        ", ".join(focus_terms) if focus_terms else "_none_",
        "",
        "## Executable Focus Refinement Candidates",
        "",
    ]
    if executable_focus_refinement_candidates:
        audit_lines.extend(
            f"- {item['term']}: novel={item['novel_vs_current_executable_count']} hits={item['eligible_concept_hit_count']}"
            for item in executable_focus_refinement_candidates
        )
    else:
        audit_lines.append("- none")
    audit_lines.extend(
        [
            "",
            "## Promotion Readiness",
            "",
        ]
    )
    if executable_focus_promotion_readiness:
        audit_lines.extend(
            (
                f"- {item['term']}: status={item['readiness_status']} "
                f"cluster={item['cluster_precision']['status']} "
                f"exec_probe={item.get('execution_binding_probe', {}).get('status', 'none')} "
                f"solo_gate={item['readiness_flags']['solo_gate_ready']} "
                f"novel={item['novel_vs_current_executable_count']} "
                f"scope={item['scope_band']}"
            )
            for item in executable_focus_promotion_readiness
        )
    else:
        audit_lines.append("- none")
    audit_lines.extend(
        [
            "",
            "## Semantic Comparison",
            "",
        ]
    )
    if executable_focus_semantic_comparison:
        audit_lines.extend(
            [
                f"- comparison_pair: `{', '.join(executable_focus_semantic_comparison.get('comparison_pair', []))}`",
                f"- structural_front_runner: `{executable_focus_semantic_comparison.get('structural_front_runner', '')}`",
                f"- semantic_hygiene_front_runner: `{executable_focus_semantic_comparison.get('semantic_hygiene_front_runner', '')}`",
                f"- decision: `{executable_focus_semantic_comparison.get('decision', '')}`",
            ]
        )
        family_audit = executable_focus_semantic_comparison.get("family_audit", {}) or {}
        family_observations = family_audit.get("observations", []) or []
        if family_observations:
            audit_lines.append("")
            for item in family_observations:
                audit_lines.append(
                    f"- {item['term']} family: posture={item['family_posture']} "
                    f"top_family={item['top_family']} share={item['top_family_share']}"
                )
    derivation_contamination = payload["self_audit"].get(
        "derivation_family_contamination", {}
    ) or {}
    audit_lines.extend(
        [
            "",
            "## Derivation Contamination Audit",
            "",
        ]
    )
    if derivation_contamination:
        basis = derivation_contamination.get("graph_basis", {}) or {}
        audit_lines.extend(
            [
                f"- status: `{derivation_contamination.get('status', '')}`",
                f"- contamination_risk: `{derivation_contamination.get('contamination_risk', '')}`",
                f"- risk_flags: `{', '.join(derivation_contamination.get('risk_flags', [])) or 'none'}`",
                f"- counter_signals: `{', '.join(derivation_contamination.get('counter_signals', [])) or 'none'}`",
                f"- source_map_share: `{basis.get('source_map_share', 0.0)}`",
                f"- engine_pattern_share: `{basis.get('engine_pattern_share', 0.0)}`",
                f"- stripped_share: `{basis.get('stripped_share', 0.0)}`",
                f"- high_intake_share: `{basis.get('high_intake_share', 0.0)}`",
                f"- provenance_sparse_share: `{basis.get('provenance_sparse_share', 0.0)}`",
            ]
        )
    else:
        audit_lines.append("- none")
    semantic_sample = (
        (
            payload["self_audit"].get("semantic_sample_comparison", {}) or {}
        ).get("derivation_vs_integration", {})
        or {}
    )
    audit_lines.extend(
        [
            "",
            "## Semantic Sample Comparison",
            "",
        ]
    )
    if semantic_sample:
        audit_lines.extend(
            [
                f"- status: `{semantic_sample.get('status', '')}`",
                f"- comparison_result: `{semantic_sample.get('comparison_result', '')}`",
                f"- confidence: `{semantic_sample.get('confidence', '')}`",
                f"- left_family: `{semantic_sample.get('left_family', '')}` posture=`{(semantic_sample.get('left', {}) or {}).get('sample_posture', '')}`",
                f"- right_family: `{semantic_sample.get('right_family', '')}` posture=`{(semantic_sample.get('right', {}) or {}).get('sample_posture', '')}`",
                f"- left_sample_node_ids: `{', '.join((semantic_sample.get('left_sample_node_ids', []) or [])) or 'none'}`",
                f"- right_sample_node_ids: `{', '.join((semantic_sample.get('right_sample_node_ids', []) or [])) or 'none'}`",
            ]
        )
    else:
        audit_lines.append("- none")
    derivation_sample_provenance = payload["self_audit"].get(
        "derivation_sample_provenance_strength", {}
    ) or {}
    audit_lines.extend(
        [
            "",
            "## Derivation Sample Provenance Strength",
            "",
        ]
    )
    if derivation_sample_provenance:
        provenance_signals = (
            derivation_sample_provenance.get("provenance_signals", {}) or {}
        )
        audit_lines.extend(
            [
                f"- status: `{derivation_sample_provenance.get('status', '')}`",
                f"- assessment_result: `{derivation_sample_provenance.get('assessment_result', '')}`",
                f"- risk_flags: `{', '.join(derivation_sample_provenance.get('risk_flags', [])) or 'none'}`",
                f"- dual_provenance: `{provenance_signals.get('dual_provenance', False)}`",
                f"- witness_backed: `{provenance_signals.get('witness_backed', False)}`",
                f"- lineage_backed: `{provenance_signals.get('lineage_backed', False)}`",
                f"- sample_semantic_support_share: `{provenance_signals.get('sample_semantic_support_share', 0.0)}`",
                f"- sample_residue_risk_share: `{provenance_signals.get('sample_residue_risk_share', 0.0)}`",
                f"- sample_provenance_sparse_share: `{provenance_signals.get('sample_provenance_sparse_share', 0.0)}`",
                f"- sample_uplift_ratio: `{provenance_signals.get('sample_uplift_ratio', 0.0)}`",
            ]
        )
    else:
        audit_lines.append("- none")
    derivation_lineage_bridge = payload["self_audit"].get(
        "derivation_lineage_bridge", {}
    ) or {}
    audit_lines.extend(
        [
            "",
            "## Derivation Lineage Bridge Audit",
            "",
        ]
    )
    if derivation_lineage_bridge:
        bridge_signals = derivation_lineage_bridge.get("bridge_signals", {}) or {}
        audit_lines.extend(
            [
                f"- status: `{derivation_lineage_bridge.get('status', '')}`",
                f"- bridge_status: `{derivation_lineage_bridge.get('bridge_status', '')}`",
                f"- direct_intent_bridge_count: `{bridge_signals.get('direct_intent_bridge_count', 0)}`",
                f"- reachable_within_3_hops_count: `{bridge_signals.get('reachable_within_3_hops_count', 0)}`",
                f"- upper_surface_neighbor_count: `{bridge_signals.get('upper_surface_neighbor_count', 0)}`",
                f"- no_observed_bridge_count: `{bridge_signals.get('no_observed_bridge_count', 0)}`",
            ]
        )
    else:
        audit_lines.append("- none")
    derivation_bridge_precondition = payload["self_audit"].get(
        "derivation_bridge_materialization_precondition", {}
    ) or {}
    audit_lines.extend(
        [
            "",
            "## Derivation Bridge Materialization Precondition",
            "",
        ]
    )
    if derivation_bridge_precondition:
        audit_lines.extend(
            [
                f"- status: `{derivation_bridge_precondition.get('status', '')}`",
                f"- decision: `{derivation_bridge_precondition.get('decision', '')}`",
                f"- single_bridgeable_path: `{derivation_bridge_precondition.get('single_bridgeable_path', False)}`",
                f"- candidate_middle_node_id: `{derivation_bridge_precondition.get('candidate_middle_node_id', '')}`",
                f"- candidate_middle_node_layer: `{derivation_bridge_precondition.get('candidate_middle_node_layer', '')}`",
                f"- recommended_relation: `{derivation_bridge_precondition.get('recommended_relation', '')}`",
                f"- materialization_allowed_in_current_surface: `{derivation_bridge_precondition.get('materialization_allowed_in_current_surface', False)}`",
                f"- hard_blockers: `{', '.join(derivation_bridge_precondition.get('hard_blockers', [])) or 'none'}`",
            ]
        )
    else:
        audit_lines.append("- none")
    stripped_provenance_precondition = payload["self_audit"].get(
        "stripped_provenance_backfill_precondition", {}
    ) or {}
    audit_lines.extend(
        [
            "",
            "## Stripped Provenance Backfill Precondition",
            "",
        ]
    )
    if stripped_provenance_precondition:
        audit_lines.extend(
            [
                f"- status: `{stripped_provenance_precondition.get('status', '')}`",
                f"- decision: `{stripped_provenance_precondition.get('decision', '')}`",
                f"- target_node_id: `{stripped_provenance_precondition.get('target_node_id', '')}`",
                f"- admissible_now: `{stripped_provenance_precondition.get('admissible_now', False)}`",
                f"- materialization_allowed_in_current_surface: `{stripped_provenance_precondition.get('materialization_allowed_in_current_surface', False)}`",
                f"- candidate_backfill_source_node_ids: `{', '.join(stripped_provenance_precondition.get('candidate_backfill_source_node_ids', [])) or 'none'}`",
                f"- do_not_backfill_fields: `{', '.join(stripped_provenance_precondition.get('do_not_backfill_fields', [])) or 'none'}`",
                f"- hard_blockers: `{', '.join(stripped_provenance_precondition.get('hard_blockers', [])) or 'none'}`",
            ]
        )
    else:
        audit_lines.append("- none")
    stripped_provenance_annotation = payload["self_audit"].get(
        "stripped_provenance_annotation_admission", {}
    ) or {}
    audit_lines.extend(
        [
            "",
            "## Stripped Provenance Annotation Admission",
            "",
        ]
    )
    if stripped_provenance_annotation:
        audit_lines.extend(
            [
                f"- status: `{stripped_provenance_annotation.get('status', '')}`",
                f"- decision: `{stripped_provenance_annotation.get('decision', '')}`",
                f"- annotation_path: `{stripped_provenance_annotation.get('annotation_path', '')}`",
                f"- admissible_now: `{stripped_provenance_annotation.get('admissible_now', False)}`",
                f"- builder_supports_properties_merge: `{stripped_provenance_annotation.get('builder_supports_properties_merge', False)}`",
                f"- forbidden_fields: `{', '.join(stripped_provenance_annotation.get('forbidden_fields', [])) or 'none'}`",
                f"- hard_blockers: `{', '.join(stripped_provenance_annotation.get('hard_blockers', [])) or 'none'}`",
            ]
        )
    else:
        audit_lines.append("- none")
    audit_lines.extend(
        [
            "",
            "## Stripped Provenance Overlay Archive",
            "",
            f"- json_path: `{PROVENANCE_OVERLAY_REL_PATH}`",
            f"- surface_class: `{(overlay_payload.get('classification', {}) or {}).get('surface_class', '')}`",
            f"- status: `{(overlay_payload.get('classification', {}) or {}).get('status', '')}`",
            f"- target_node_id: `{(overlay_payload.get('target', {}) or {}).get('node_id', '')}`",
            f"- primary_chain_count: `{len((overlay_payload.get('donor_chain', {}) or {}).get('primary_chain', []) or [])}`",
        ]
    )
    audit_lines.extend(
        [
            "",
        "## Open Tensions",
        "",
        ]
    )
    if open_tensions:
        audit_lines.extend(f"- {line}" for line in open_tensions)
    else:
        audit_lines.append("- none")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    return {
        "json_path": SURFACE_REL_PATH,
        "audit_note_path": AUDIT_REL_PATH,
        "provenance_overlay_path": PROVENANCE_OVERLAY_REL_PATH,
        "summary": payload["self_audit"],
        "surface_hash": payload["provenance"]["surface_hash"],
    }


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    result = build_intent_control_surface(str(repo))
    assert result["summary"]["maker_intent_count"] >= 0
    assert result["summary"]["runtime_context_count"] >= 0
    print("PASS: intent_control_surface_builder self-test")
