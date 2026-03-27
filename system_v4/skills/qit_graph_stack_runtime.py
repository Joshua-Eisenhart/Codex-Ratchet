#!/usr/bin/env python3
"""
qit_graph_stack_runtime.py

Verify the current QIT graph stack as a gradual-integration surface.

Default behavior is read-only with respect to the owner graph:
1. Validate the owner-layer Pydantic schemas.
2. Load the existing QIT owner graph snapshot from disk.
3. Optionally refresh owner/GraphML artifacts only when explicitly requested.
4. Run the current bounded sidecars (TopoNetX, clifford payload mapping, PyG)
   over the loaded owner snapshot.
5. Persist the consolidated status report only when explicitly requested.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import networkx as nx

from graph_tool_integration import (
    build_ga_edge_payloads,
    build_pyg_tensors,
    build_toponetx_complex,
)
from qit_engine_graph_builder import OUT_FILE as QIT_GRAPH_JSON
from qit_engine_graph_builder import write_qit_engine_graph
from qit_owner_schemas import (
    BoundaryEnum,
    CANONICAL_ENGINE_TYPES,
    CANONICAL_OPERATORS,
    CANONICAL_TORI,
    EngineTypeEnum,
    LoopEnum,
    MacroStage,
    ModeEnum,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
GRAPH_DIR = REPO_ROOT / "system_v4" / "a2_state" / "graphs"
REPORT_JSON = AUDIT_DIR / "QIT_GRAPH_STACK_STATUS__CURRENT__v1.json"
REPORT_MD = AUDIT_DIR / "QIT_GRAPH_STACK_STATUS__CURRENT__v1.md"
RUNTIME_EVIDENCE_BRIDGE_JSON = AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json"
RUNTIME_EVIDENCE_BRIDGE_MD = AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md"
QIT_RETRIEVAL_SIDECAR_JSON = AUDIT_DIR / "QIT_RETRIEVAL_SIDECAR__CURRENT__v1.json"
QIT_RETRIEVAL_SIDECAR_MD = AUDIT_DIR / "QIT_RETRIEVAL_SIDECAR__CURRENT__v1.md"
HOPF_WEYL_PROJECTION_JSON = AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json"
HOPF_WEYL_PROJECTION_MD = AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.md"
HOPF_WEYL_EVIDENCE_AUDIT_JSON = AUDIT_DIR / "QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.json"
HOPF_WEYL_EVIDENCE_AUDIT_MD = AUDIT_DIR / "QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.md"
TORUS_TYPE_REPAIR_GAP_JSON = AUDIT_DIR / "QIT_TORUS_TYPE_REPAIR_GAP_REPORT__CURRENT__v1.json"
TORUS_TYPE_REPAIR_GAP_MD = AUDIT_DIR / "QIT_TORUS_TYPE_REPAIR_GAP_REPORT__CURRENT__v1.md"
GRAPHML_PATH = GRAPH_DIR / "qit_engine_graph_v1.graphml"
NESTED_GRAPH_PATH = GRAPH_DIR / "nested_graph_v1.json"
RUNTIME_STATE_PATH = GRAPH_DIR / "qit_runtime_state_v1.json"
HISTORY_GRAPH_PATH = GRAPH_DIR / "qit_history_graph_v1.json"
LIGHTRAG_WORK_DIR = REPO_ROOT / "work" / "lightrag_smoke"
LIGHTRAG_RESULT_PATH = LIGHTRAG_WORK_DIR / "smoke_test_result.json"
LIGHTRAG_MANIFEST_PATH = LIGHTRAG_WORK_DIR / "corpus_manifest.json"
PREFERRED_INTERPRETER = REPO_ROOT / ".venv_spec_graph" / "bin" / "python"
RUNTIME_PACKET_ADAPTER_PATH = REPO_ROOT / "system_v4" / "skills" / "qit_runtime_state_history_adapter.py"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(payload: Any) -> str:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(canon)


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


def _path_sha256_if_exists(raw_path: str | None) -> str | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    if not path.exists() or not path.is_file():
        return None
    return _sha256_path(path)


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _sidecar_env() -> dict[str, str]:
    env = os.environ.copy()
    cache = REPO_ROOT / "work" / "audit_tmp" / "mplcache"
    cache.mkdir(parents=True, exist_ok=True)
    env.setdefault("MPLCONFIGDIR", str(cache))
    env.setdefault("XDG_CACHE_HOME", str(cache))
    return env


def _module_available_in_interpreter(interpreter: Path, name: str) -> bool:
    if not interpreter.exists():
        return False
    result = subprocess.run(
        [str(interpreter), "-c", f"import {name}"],
        capture_output=True,
        text=True,
        env=_sidecar_env(),
    )
    return result.returncode == 0


def _graphml_attr(value: Any) -> str | int | float | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def _validate_owner_schemas() -> dict[str, Any]:
    sample_stage = MacroStage(
        terrain="Se_f",
        engine_type=EngineTypeEnum.LEFT_WEYL,
        stage_index=0,
        loop=LoopEnum.FIBER,
        mode=ModeEnum.EXPAND,
        boundary=BoundaryEnum.OPEN,
    )
    return {
        "operators": len(CANONICAL_OPERATORS),
        "tori": len(CANONICAL_TORI),
        "engine_types": len(CANONICAL_ENGINE_TYPES),
        "sample_stage": sample_stage.model_dump(),
    }


def _owner_content_hash(payload: dict[str, Any]) -> str:
    content_for_hash = {
        key: value for key, value in payload.items() if key not in {"generated_utc", "content_hash"}
    }
    return _canonical_sha256(content_for_hash)


def _load_owner_snapshot(refresh_owner: bool) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    action = "read_existing_snapshot"
    if refresh_owner:
        write_qit_engine_graph()
        action = "rebuilt_owner_snapshot"
    elif not QIT_GRAPH_JSON.exists():
        raise FileNotFoundError(
            f"QIT owner graph snapshot not found at {QIT_GRAPH_JSON}. "
            "Run with --refresh-owner to create it explicitly."
        )

    payload = _load_json(QIT_GRAPH_JSON)
    nodes = payload.get("nodes", {})
    edges = payload.get("edges", [])
    embedded_content_hash = payload.get("content_hash")
    recomputed_content_hash = _owner_content_hash(payload)
    summary = payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {}

    snapshot = {
        "path": str(QIT_GRAPH_JSON),
        "action": action,
        "exists": True,
        "file_sha256": _sha256_path(QIT_GRAPH_JSON),
        "size_bytes": QIT_GRAPH_JSON.stat().st_size,
        "schema": payload.get("schema"),
        "generated_utc": payload.get("generated_utc"),
        "embedded_content_hash": embedded_content_hash,
        "recomputed_content_hash": recomputed_content_hash,
        "embedded_content_hash_matches_recomputed": (
            embedded_content_hash == recomputed_content_hash if embedded_content_hash else None
        ),
        "summary_node_count": summary.get("node_count"),
        "summary_edge_count": summary.get("edge_count"),
        "summary_validation_errors": summary.get("validation_errors", []),
    }
    return payload, nodes, edges, snapshot


def _export_graphml(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    graph = nx.MultiDiGraph()

    for node_id, node in nodes.items():
        attrs = {key: _graphml_attr(value) for key, value in node.items()}
        graph.add_node(node_id, **attrs)

    for idx, edge in enumerate(edges):
        attrs = {
            "relation": _graphml_attr(edge.get("relation", "")),
            "edge_index": idx,
            "attributes_json": json.dumps(edge.get("attributes", {}) or {}, sort_keys=True),
        }
        raw_attrs = edge.get("attributes", {}) or {}
        for key, value in raw_attrs.items():
            attrs[f"attr_{key}"] = _graphml_attr(value)
        graph.add_edge(edge["source_id"], edge["target_id"], key=idx, **attrs)

    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, GRAPHML_PATH)
    return {
        "path": str(GRAPHML_PATH),
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
    }


def _graphml_snapshot(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    refresh_graphml: bool,
) -> dict[str, Any]:
    if refresh_graphml:
        exported = _export_graphml(nodes, edges)
        sha256 = _sha256_path(GRAPHML_PATH)
        size_bytes = GRAPHML_PATH.stat().st_size
        return {
            **exported,
            "exists": True,
            "action": "refreshed_from_owner_snapshot",
            "file_sha256": sha256,
            "size_bytes": size_bytes,
            "parse_error": None,
            "matches_owner_counts": (
                exported["node_count"] == len(nodes) and exported["edge_count"] == len(edges)
            ),
        }

    if not GRAPHML_PATH.exists():
        return {
            "path": str(GRAPHML_PATH),
            "exists": False,
            "action": "not_present_not_refreshed",
            "file_sha256": None,
            "size_bytes": None,
            "node_count": None,
            "edge_count": None,
            "parse_error": None,
            "matches_owner_counts": None,
        }

    try:
        graph = nx.read_graphml(GRAPHML_PATH)
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        parse_error = None
    except Exception as exc:
        node_count = None
        edge_count = None
        parse_error = str(exc)

    return {
        "path": str(GRAPHML_PATH),
        "exists": True,
        "action": "read_existing_snapshot",
        "file_sha256": _sha256_path(GRAPHML_PATH),
        "size_bytes": GRAPHML_PATH.stat().st_size,
        "node_count": node_count,
        "edge_count": edge_count,
        "parse_error": parse_error,
        "matches_owner_counts": (
            node_count == len(nodes) and edge_count == len(edges)
            if parse_error is None
            else None
        ),
    }


def _clifford_projection_summary(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    enriched = build_ga_edge_payloads(edges, nodes)
    grade_counts: dict[int, int] = {}
    relation_counts: dict[str, int] = {}
    preview: list[dict[str, Any]] = []

    for item in enriched:
        payload = item.get("ga_payload", {})
        grade = int(payload.get("grade", 0))
        relation = str(payload.get("relation", "?"))
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        relation_counts[relation] = relation_counts.get(relation, 0) + 1
        if len(preview) < 5:
            preview.append(
                {
                    "relation": relation,
                    "grade": grade,
                    "coefficients": payload.get("coefficients", []),
                }
            )

    return {
        "package_available_current_interpreter": _module_available("clifford"),
        "package_importable_preferred_interpreter": _module_available_in_interpreter(PREFERRED_INTERPRETER, "clifford"),
        "kingdon_available_current_interpreter": _module_available("kingdon"),
        "kingdon_importable_preferred_interpreter": _module_available_in_interpreter(PREFERRED_INTERPRETER, "kingdon"),
        "edges_enriched": len(enriched),
        "grade_counts": grade_counts,
        "relation_counts": relation_counts,
        "preview": preview,
    }


def _promotion_gate_status(owner_payload: dict[str, Any]) -> dict[str, Any]:
    nodes = owner_payload.get("nodes", {}) if isinstance(owner_payload.get("nodes"), dict) else {}
    required_owner_fields = [
        "owner_layer",
        "materialized",
        "build_status",
        "derived_from",
        "selection_contract",
        "content_hash",
        "public_id_index",
    ]
    owner_contract_ok = all(field in owner_payload for field in required_owner_fields)
    public_ids_ok = bool(nodes) and all("public_id" in node for node in nodes.values())
    subcycle_steps = sum(1 for node in nodes.values() if node.get("node_type") == "SUBCYCLE_STEP")

    qit_nested_cross = 0
    if NESTED_GRAPH_PATH.exists():
        nested_graph = _load_json(NESTED_GRAPH_PATH)
        qit_nested_cross = sum(
            int(v)
            for k, v in (nested_graph.get("inter_layer_edges", {}) or {}).get("by_layer_pair", {}).items()
            if "QIT" in k
        )

    return {
        "owner_structure_gate": {
            "status": "PRECHECK_OK" if owner_contract_ok and public_ids_ok and subcycle_steps == 64 else "PRECHECK_MISSING",
            "full_promotion_gate_passed": False,
            "verification_level": "owner_snapshot_structure_only",
            "required_owner_fields_present": owner_contract_ok,
            "public_ids_present_on_all_nodes": public_ids_ok,
            "subcycle_step_count": subcycle_steps,
            "required_subcycle_step_count": 64,
        },
        "cross_layer_alignment_gate": {
            "status": "PRECHECK_OK" if qit_nested_cross > 0 else "PRECHECK_MISSING",
            "full_promotion_gate_passed": False,
            "verification_level": "bridge_presence_only",
            "qit_nested_cross_layer_edges": qit_nested_cross,
        },
        "runtime_state_gate": {
            "status": "PRECHECK_OK" if RUNTIME_STATE_PATH.exists() else "PRECHECK_MISSING",
            "full_promotion_gate_passed": False,
            "verification_level": "file_presence_only",
            "runtime_state_path": str(RUNTIME_STATE_PATH),
            "packet_only_adapter_available": RUNTIME_PACKET_ADAPTER_PATH.exists(),
            "packet_only_adapter_path": str(RUNTIME_PACKET_ADAPTER_PATH),
        },
        "history_graph_gate": {
            "status": "PRECHECK_OK" if HISTORY_GRAPH_PATH.exists() else "PRECHECK_MISSING",
            "full_promotion_gate_passed": False,
            "verification_level": "file_presence_only",
            "history_graph_path": str(HISTORY_GRAPH_PATH),
            "packet_only_adapter_available": RUNTIME_PACKET_ADAPTER_PATH.exists(),
            "packet_only_adapter_path": str(RUNTIME_PACKET_ADAPTER_PATH),
        },
    }


def _lightrag_status() -> dict[str, Any]:
    if LIGHTRAG_RESULT_PATH.exists():
        result = _load_json(LIGHTRAG_RESULT_PATH)
        manifest_exists = LIGHTRAG_MANIFEST_PATH.exists()
        init_success = bool(result.get("init_success"))
        if manifest_exists and init_success:
            status = "sidecar_corpus_ready"
        elif manifest_exists and not init_success:
            status = "sidecar_corpus_ready_needs_embedding_config"
        else:
            status = "smoke_ran_manifest_missing"
        return {
            "status": status,
            "working_dir": str(LIGHTRAG_WORK_DIR),
            "smoke_result_path": str(LIGHTRAG_RESULT_PATH),
            "corpus_manifest_path": str(LIGHTRAG_MANIFEST_PATH),
            "documents_built": result.get("documents_built"),
            "total_corpus_chars": result.get("total_corpus_chars"),
            "init_success": init_success,
            "init_error": result.get("init_error"),
        }
    return {
        "status": "registered_not_integrated",
        "working_dir": str(LIGHTRAG_WORK_DIR),
        "smoke_result_path": str(LIGHTRAG_RESULT_PATH),
        "corpus_manifest_path": str(LIGHTRAG_MANIFEST_PATH),
    }


def _runtime_evidence_bridge_status(owner_snapshot: dict[str, Any]) -> dict[str, Any]:
    if not RUNTIME_EVIDENCE_BRIDGE_JSON.exists():
        return {
            "status": "absent",
            "json_path": str(RUNTIME_EVIDENCE_BRIDGE_JSON),
            "md_path": str(RUNTIME_EVIDENCE_BRIDGE_MD),
        }

    payload = _load_json(RUNTIME_EVIDENCE_BRIDGE_JSON)
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    owner = payload.get("owner_snapshot", {}) if isinstance(payload.get("owner_snapshot"), dict) else {}
    owner_hash_matches = owner.get("qit_graph_content_hash") == owner_snapshot.get("embedded_content_hash")
    runtime_sample_count = int(summary.get("runtime_sample_count", 0) or 0)
    sim_packet_count = int(summary.get("sim_packet_count", 0) or 0)
    complete_mappings = int(summary.get("complete_mappings", 0) or 0)
    partial_mappings = int(summary.get("partial_mappings", 0) or 0)
    unresolved_links = int(summary.get("unresolved_owner_links", 0) or 0)

    if owner_hash_matches and runtime_sample_count > 0 and sim_packet_count > 0 and unresolved_links == 0:
        status = "present"
    else:
        status = "partial"

    return {
        "status": status,
        "json_path": str(RUNTIME_EVIDENCE_BRIDGE_JSON),
        "md_path": str(RUNTIME_EVIDENCE_BRIDGE_MD),
        "schema": payload.get("schema", ""),
        "generated_utc": payload.get("generated_utc", ""),
        "owner_content_hash_matches_current_snapshot": owner_hash_matches,
        "runtime_sample_count": runtime_sample_count,
        "sim_packet_count": sim_packet_count,
        "complete_mappings": complete_mappings,
        "partial_mappings": partial_mappings,
        "unresolved_owner_links": unresolved_links,
    }


def _qit_retrieval_sidecar_status() -> dict[str, Any]:
    if not QIT_RETRIEVAL_SIDECAR_JSON.exists():
        return {
            "status": "absent",
            "json_path": str(QIT_RETRIEVAL_SIDECAR_JSON),
            "md_path": str(QIT_RETRIEVAL_SIDECAR_MD),
        }

    payload = _load_json(QIT_RETRIEVAL_SIDECAR_JSON)
    top_hits = payload.get("top_hits", [])
    return {
        "status": "present" if top_hits else "partial",
        "json_path": str(QIT_RETRIEVAL_SIDECAR_JSON),
        "md_path": str(QIT_RETRIEVAL_SIDECAR_MD),
        "schema": payload.get("schema", ""),
        "generated_utc": payload.get("generated_utc", ""),
        "mode": payload.get("mode", ""),
        "retrieval_role": payload.get("retrieval_role", ""),
        "allow_owner_writes": payload.get("allow_owner_writes"),
        "allow_proof_claims": payload.get("allow_proof_claims"),
        "embedding_backed_query": payload.get("embedding_backed_query"),
        "embedding_backed_query_blocker": payload.get("embedding_backed_query_blocker", ""),
        "document_count": payload.get("document_count", 0),
        "top_hit_count": len(top_hits) if isinstance(top_hits, list) else 0,
        "query": payload.get("query", ""),
    }


def _hopf_weyl_projection_status(owner_snapshot: dict[str, Any]) -> dict[str, Any]:
    if not HOPF_WEYL_PROJECTION_JSON.exists():
        return {
            "status": "absent",
            "json_path": str(HOPF_WEYL_PROJECTION_JSON),
            "md_path": str(HOPF_WEYL_PROJECTION_MD),
        }

    payload = _load_json(HOPF_WEYL_PROJECTION_JSON)
    owner = payload.get("owner_snapshot", {}) if isinstance(payload.get("owner_snapshot"), dict) else {}
    hopf = payload.get("hopf_stage_projection", {}) if isinstance(payload.get("hopf_stage_projection"), dict) else {}
    weyl = payload.get("weyl_projection_readiness", {}) if isinstance(payload.get("weyl_projection_readiness"), dict) else {}
    boundary = payload.get("sidecar_boundary", {}) if isinstance(payload.get("sidecar_boundary"), dict) else {}
    owner_hash_matches = owner.get("qit_graph_content_hash") == owner_snapshot.get("embedded_content_hash")
    stage_count = int(hopf.get("stage_count", 0) or 0)
    torus_carriers = hopf.get("torus_carriers", [])
    torus_count = len(torus_carriers) if isinstance(torus_carriers, list) else 0
    chirality_present = bool(weyl.get("chirality_coupling_edge_present"))
    status = "present" if owner_hash_matches and stage_count > 0 and torus_count == 3 and chirality_present else "partial"

    return {
        "status": status,
        "json_path": str(HOPF_WEYL_PROJECTION_JSON),
        "md_path": str(HOPF_WEYL_PROJECTION_MD),
        "schema": payload.get("schema", ""),
        "generated_utc": payload.get("generated_utc", ""),
        "owner_content_hash_matches_current_snapshot": owner_hash_matches,
        "audit_only": payload.get("audit_only", boundary.get("audit_only")),
        "observer_only": payload.get("observer_only", boundary.get("observer_only", True)),
        "do_not_promote": payload.get("do_not_promote", boundary.get("do_not_promote")),
        "stage_count": stage_count,
        "fiber_stage_count": hopf.get("fiber_stage_count", 0),
        "base_stage_count": hopf.get("base_stage_count", 0),
        "torus_carrier_count": torus_count,
        "shared_clifford_stage_count": hopf.get("shared_clifford_stage_count", 0),
        "weyl_projection_status": weyl.get("projection_status", ""),
        "weyl_branch_nodes_present": weyl.get("weyl_branch_nodes_present"),
        "chirality_coupling_edge_present": chirality_present,
    }


def _hopf_weyl_evidence_audit_status(owner_snapshot: dict[str, Any]) -> dict[str, Any]:
    if not HOPF_WEYL_EVIDENCE_AUDIT_JSON.exists():
        return {
            "status": "absent",
            "json_path": str(HOPF_WEYL_EVIDENCE_AUDIT_JSON),
            "md_path": str(HOPF_WEYL_EVIDENCE_AUDIT_MD),
        }

    payload = _load_json(HOPF_WEYL_EVIDENCE_AUDIT_JSON)
    owner = payload.get("owner_snapshot", {}) if isinstance(payload.get("owner_snapshot"), dict) else {}
    runtime = payload.get("runtime_bridge_alignment", {}) if isinstance(payload.get("runtime_bridge_alignment"), dict) else {}
    neg = payload.get("relevant_negative_evidence", {}) if isinstance(payload.get("relevant_negative_evidence"), dict) else {}
    owner_hash_matches = owner.get("qit_graph_content_hash") == owner_snapshot.get("embedded_content_hash")
    return {
        "status": "present" if owner_hash_matches else "partial",
        "json_path": str(HOPF_WEYL_EVIDENCE_AUDIT_JSON),
        "md_path": str(HOPF_WEYL_EVIDENCE_AUDIT_MD),
        "schema": payload.get("schema", ""),
        "generated_utc": payload.get("generated_utc", ""),
        "audit_only": payload.get("audit_boundary", {}).get("audit_only"),
        "nonoperative": payload.get("audit_boundary", {}).get("nonoperative"),
        "do_not_promote": payload.get("audit_boundary", {}).get("do_not_promote"),
        "owner_content_hash_matches_current_snapshot": owner_hash_matches,
        "runtime_alignment_status": runtime.get("alignment_status", ""),
        "torus_witness_count": len(neg.get("torus_witnesses", [])),
        "chirality_witness_count": len(neg.get("chirality_witnesses", [])),
    }


def _torus_type_repair_gap_status(owner_snapshot: dict[str, Any]) -> dict[str, Any]:
    if not TORUS_TYPE_REPAIR_GAP_JSON.exists():
        return {
            "status": "absent",
            "json_path": str(TORUS_TYPE_REPAIR_GAP_JSON),
            "md_path": str(TORUS_TYPE_REPAIR_GAP_MD),
        }
    payload = _load_json(TORUS_TYPE_REPAIR_GAP_JSON)
    derived = payload.get("derived_from", {}) if isinstance(payload.get("derived_from"), dict) else {}
    summary = payload.get("repair_gap_summary", {}) if isinstance(payload.get("repair_gap_summary"), dict) else {}
    owner_hash_matches = derived.get("owner_snapshot_hash") == owner_snapshot.get("embedded_content_hash")
    return {
        "status": "present" if owner_hash_matches else "partial",
        "json_path": str(TORUS_TYPE_REPAIR_GAP_JSON),
        "md_path": str(TORUS_TYPE_REPAIR_GAP_MD),
        "schema": payload.get("schema", ""),
        "generated_utc": payload.get("generated_utc", ""),
        "owner_content_hash_matches_current_snapshot": owner_hash_matches,
        "audit_only": payload.get("audit_boundary", {}).get("audit_only"),
        "nonoperative": payload.get("audit_boundary", {}).get("nonoperative"),
        "do_not_promote": payload.get("audit_boundary", {}).get("do_not_promote"),
        "torus_gap_count": len(summary.get("torus_placement", {}).get("missing", [])),
        "type_gap_count": len(summary.get("type_split", {}).get("missing", [])),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    owner = report["owner"]
    sidecars = report["sidecars"]
    snapshot = report["snapshot"]
    scope = report["verification_scope"]
    report_surface = report["report_surface"]
    bridge = report["runtime_evidence_bridge"]
    retrieval = report["retrieval_sidecar"]
    hopf_weyl = report["hopf_weyl_projection"]
    hopf_weyl_audit = report["hopf_weyl_evidence_audit"]
    repair_gap = report["torus_type_repair_gap_report"]
    next_actions = "\n".join(f"- {item}" for item in report["next_actions"])
    verifies = "\n".join(f"- {item}" for item in scope["verifies"])
    does_not_verify = "\n".join(f"- {item}" for item in scope["does_not_verify"])
    gate_lines = "\n".join(
        f"- {gate}: `{details['status']}`"
        for gate, details in report["promotion_gates"].items()
    )
    return "\n".join(
        [
            "# QIT Graph Stack Status",
            "",
            f"- status: `{report['status']}`",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- purpose: `{report['purpose']}`",
            f"- snapshot_id: `{snapshot['snapshot_id']}`",
            f"- git_sha: `{report['provenance']['git_sha']}`",
            f"- git_worktree_dirty: `{report['provenance']['git_worktree_dirty']}`",
            f"- owner_builder_sha256: `{report['provenance']['owner_builder_sha256']}`",
            "",
            "## Report Surface",
            f"- surface_class: `{report_surface['surface_class']}`",
            f"- represents: `{report_surface['represents']}`",
            f"- tracked_report_files: `{', '.join(report_surface['tracked_report_files'])}`",
            f"- tracked_report_files_dirty_before_generation: `{report_surface['tracked_report_files_dirty_before_generation']}`",
            f"- write_report_required_for_refresh: `{report_surface['write_report_required_for_refresh']}`",
            "",
            "## Owner Layer",
            f"- qit_graph_json: `{owner['qit_graph_json']}`",
            f"- qit_graph_action: `{owner['qit_graph_action']}`",
            f"- qit_graph_sha256: `{owner['qit_graph_sha256']}`",
            f"- qit_graph_content_hash: `{owner['qit_graph_content_hash']}`",
            f"- qit_graph_content_hash_matches_recomputed: `{owner['qit_graph_content_hash_matches_recomputed']}`",
            f"- graphml_export: `{owner['graphml_export']['path']}`",
            f"- graphml_action: `{owner['graphml_export']['action']}`",
            f"- graphml_sha256: `{owner['graphml_export']['file_sha256']}`",
            f"- node_count: `{owner['node_count']}`",
            f"- edge_count: `{owner['edge_count']}`",
            f"- live_node_types: `{', '.join(owner['live_node_types'])}`",
            f"- schema_ready_not_instantiated: `{', '.join(owner['schema_ready_not_instantiated'])}`",
            "",
            "## Verification Scope",
            f"- mutates_owner_truth: `{scope['mutates_owner_truth']}`",
            f"- mutates_graphml_sidecar: `{scope['mutates_graphml_sidecar']}`",
            "- verifies:",
            verifies,
            "- does_not_verify:",
            does_not_verify,
            "",
            "## Promotion Gates",
            "- gate_status_meaning: `PRECHECK_OK/PRECHECK_MISSING are coarse readiness checks only, not full promotion completion`",
            gate_lines,
            "",
            "## Sidecars",
            f"- preferred sidecar interpreter: `{sidecars['preferred_sidecar_interpreter']['path']}`",
            f"- preferred sidecar interpreter exists: `{sidecars['preferred_sidecar_interpreter']['exists']}`",
            f"- TopoNetX available (current interpreter): `{sidecars['toponetx']['available_current_interpreter']}`",
            f"- TopoNetX importable (preferred interpreter): `{sidecars['toponetx']['importable_preferred_interpreter']}`",
            f"- TopoNetX shape: `{sidecars['toponetx'].get('shape', [])}`",
            f"- clifford available (current interpreter): `{sidecars['clifford']['package_available_current_interpreter']}`",
            f"- clifford importable (preferred interpreter): `{sidecars['clifford']['package_importable_preferred_interpreter']}`",
            f"- kingdon available (current interpreter): `{sidecars['clifford']['kingdon_available_current_interpreter']}`",
            f"- kingdon importable (preferred interpreter): `{sidecars['clifford']['kingdon_importable_preferred_interpreter']}`",
            f"- PyG available (current interpreter): `{sidecars['pyg']['available_current_interpreter']}`",
            f"- PyG importable (preferred interpreter): `{sidecars['pyg']['importable_preferred_interpreter']}`",
            f"- LightRAG status: `{sidecars['lightrag']['status']}`",
            "",
            "## Runtime Evidence Bridge",
            f"- status: `{bridge['status']}`",
            f"- json_path: `{bridge['json_path']}`",
            f"- md_path: `{bridge['md_path']}`",
            f"- owner_content_hash_matches_current_snapshot: `{bridge.get('owner_content_hash_matches_current_snapshot')}`",
            f"- runtime_sample_count: `{bridge.get('runtime_sample_count')}`",
            f"- sim_packet_count: `{bridge.get('sim_packet_count')}`",
            f"- complete_mappings: `{bridge.get('complete_mappings')}`",
            f"- partial_mappings: `{bridge.get('partial_mappings')}`",
            "",
            "## Retrieval Sidecar",
            f"- status: `{retrieval['status']}`",
            f"- json_path: `{retrieval['json_path']}`",
            f"- md_path: `{retrieval['md_path']}`",
            f"- mode: `{retrieval.get('mode')}`",
            f"- retrieval_role: `{retrieval.get('retrieval_role')}`",
            f"- allow_owner_writes: `{retrieval.get('allow_owner_writes')}`",
            f"- allow_proof_claims: `{retrieval.get('allow_proof_claims')}`",
            f"- embedding_backed_query: `{retrieval.get('embedding_backed_query')}`",
            f"- document_count: `{retrieval.get('document_count')}`",
            f"- top_hit_count: `{retrieval.get('top_hit_count')}`",
            "",
            "## Hopf/Weyl Projection",
            f"- status: `{hopf_weyl['status']}`",
            f"- json_path: `{hopf_weyl['json_path']}`",
            f"- md_path: `{hopf_weyl['md_path']}`",
            f"- owner_content_hash_matches_current_snapshot: `{hopf_weyl.get('owner_content_hash_matches_current_snapshot')}`",
            f"- audit_only: `{hopf_weyl.get('audit_only')}`",
            f"- observer_only: `{hopf_weyl.get('observer_only')}`",
            f"- do_not_promote: `{hopf_weyl.get('do_not_promote')}`",
            f"- stage_count: `{hopf_weyl.get('stage_count')}`",
            f"- torus_carrier_count: `{hopf_weyl.get('torus_carrier_count')}`",
            f"- weyl_projection_status: `{hopf_weyl.get('weyl_projection_status')}`",
            "",
            "## Hopf/Weyl Evidence Audit",
            f"- status: `{hopf_weyl_audit['status']}`",
            f"- json_path: `{hopf_weyl_audit['json_path']}`",
            f"- md_path: `{hopf_weyl_audit['md_path']}`",
            f"- owner_content_hash_matches_current_snapshot: `{hopf_weyl_audit.get('owner_content_hash_matches_current_snapshot')}`",
            f"- audit_only: `{hopf_weyl_audit.get('audit_only')}`",
            f"- nonoperative: `{hopf_weyl_audit.get('nonoperative')}`",
            f"- do_not_promote: `{hopf_weyl_audit.get('do_not_promote')}`",
            f"- runtime_alignment_status: `{hopf_weyl_audit.get('runtime_alignment_status')}`",
            f"- torus_witness_count: `{hopf_weyl_audit.get('torus_witness_count')}`",
            f"- chirality_witness_count: `{hopf_weyl_audit.get('chirality_witness_count')}`",
            "",
            "## Torus/Type Repair Gap Report",
            f"- status: `{repair_gap['status']}`",
            f"- json_path: `{repair_gap['json_path']}`",
            f"- md_path: `{repair_gap['md_path']}`",
            f"- owner_content_hash_matches_current_snapshot: `{repair_gap.get('owner_content_hash_matches_current_snapshot')}`",
            f"- audit_only: `{repair_gap.get('audit_only')}`",
            f"- nonoperative: `{repair_gap.get('nonoperative')}`",
            f"- do_not_promote: `{repair_gap.get('do_not_promote')}`",
            f"- torus_gap_count: `{repair_gap.get('torus_gap_count')}`",
            f"- type_gap_count: `{repair_gap.get('type_gap_count')}`",
            "- interpretation: `bounded repair map only; listed gaps are not already repaired and this surface is not promotion evidence`",
            "",
            "## Next Actions",
            next_actions,
            "",
        ]
    )


def build_qit_graph_stack_status(refresh_owner: bool = False, refresh_graphml: bool = False) -> dict[str, Any]:
    schema_status = _validate_owner_schemas()
    graph_payload, nodes, edges, owner_snapshot = _load_owner_snapshot(refresh_owner=refresh_owner)

    graphml = _graphml_snapshot(nodes, edges, refresh_graphml=refresh_graphml)
    toponetx = build_toponetx_complex(nodes, edges)
    clifford = _clifford_projection_summary(nodes, edges)
    pyg = build_pyg_tensors(nodes, edges)
    preferred_interpreter_exists = PREFERRED_INTERPRETER.exists()
    runtime_evidence_bridge = _runtime_evidence_bridge_status(owner_snapshot)
    retrieval_sidecar = _qit_retrieval_sidecar_status()
    hopf_weyl_projection = _hopf_weyl_projection_status(owner_snapshot)
    hopf_weyl_evidence_audit = _hopf_weyl_evidence_audit_status(owner_snapshot)
    torus_type_repair_gap_report = _torus_type_repair_gap_status(owner_snapshot)

    live_node_types = sorted({node.get("node_type", "?") for node in nodes.values()})
    schema_ready_not_instantiated = sorted({"WEYL_BRANCH"} - set(live_node_types))
    promotion_gates = _promotion_gate_status(graph_payload)
    git_sha = _git_sha()
    derived_from = graph_payload.get("derived_from", {}) if isinstance(graph_payload.get("derived_from"), dict) else {}
    owner_builder_path = derived_from.get("builder_program")
    owner_schema_path = derived_from.get("owner_schemas")
    script_path = Path(__file__).resolve()
    relevant_paths = [
        script_path,
        Path(owner_builder_path) if owner_builder_path else None,
        Path(owner_schema_path) if owner_schema_path else None,
        QIT_GRAPH_JSON,
        GRAPHML_PATH,
        RUNTIME_EVIDENCE_BRIDGE_JSON,
        RUNTIME_EVIDENCE_BRIDGE_MD,
        QIT_RETRIEVAL_SIDECAR_JSON,
        QIT_RETRIEVAL_SIDECAR_MD,
        HOPF_WEYL_PROJECTION_JSON,
        HOPF_WEYL_PROJECTION_MD,
        HOPF_WEYL_EVIDENCE_AUDIT_JSON,
        HOPF_WEYL_EVIDENCE_AUDIT_MD,
        TORUS_TYPE_REPAIR_GAP_JSON,
        TORUS_TYPE_REPAIR_GAP_MD,
        REPORT_JSON,
        REPORT_MD,
    ]
    relevant_paths = [path for path in relevant_paths if path is not None]
    relevant_git_status = _git_status_porcelain(relevant_paths)
    worktree_dirty = bool(_git_status_porcelain())
    snapshot_inputs = {
        "git_sha": git_sha,
        "owner_file_sha256": owner_snapshot["file_sha256"],
        "owner_content_hash": owner_snapshot["embedded_content_hash"],
        "graphml_file_sha256": graphml["file_sha256"],
        "graphml_exists": graphml["exists"],
        "owner_builder_sha256": _path_sha256_if_exists(owner_builder_path),
        "owner_schema_sha256": _path_sha256_if_exists(owner_schema_path),
        "script_sha256": _sha256_path(script_path),
    }
    snapshot_id = _canonical_sha256(snapshot_inputs)
    gate_statuses = [details["status"] for details in promotion_gates.values()]
    overall_status = (
        "precheck_ready_not_promoted"
        if gate_statuses and all(status == "PRECHECK_OK" for status in gate_statuses)
        else "precheck_blocked"
    )

    report = {
        "schema": "QIT_GRAPH_STACK_STATUS_v1",
        "status": overall_status,
        "generated_utc": _utc_iso(),
        "purpose": "read-only-by-default verification surface over the current QIT owner snapshot and bounded sidecars",
        "report_surface": {
            "surface_class": "tracked_current_workspace_report",
            "represents": (
                "current workspace state at generation time; may differ from the last committed snapshot "
                "until tracked CURRENT artifacts are committed"
            ),
            "tracked_report_files": [
                str(REPORT_JSON),
                str(REPORT_MD),
            ],
            "tracked_report_files_dirty_before_generation": _git_status_porcelain([REPORT_JSON, REPORT_MD]),
            "write_report_required_for_refresh": True,
        },
        "provenance": {
            "git_sha": git_sha,
            "git_worktree_dirty": worktree_dirty,
            "relevant_git_status": relevant_git_status,
            "script_path": str(script_path),
            "script_sha256": _sha256_path(script_path),
            "owner_builder_path": owner_builder_path,
            "owner_builder_sha256": _path_sha256_if_exists(owner_builder_path),
            "owner_schema_path": owner_schema_path,
            "owner_schema_sha256": _path_sha256_if_exists(owner_schema_path),
        },
        "snapshot": {
            "snapshot_id": snapshot_id,
            **snapshot_inputs,
        },
        "verification_scope": {
            "mutates_owner_truth": refresh_owner,
            "mutates_graphml_sidecar": refresh_graphml,
            "verifies": [
                "owner snapshot file presence, schema tag, counts, and file hash",
                "embedded owner content_hash against a recomputed canonical hash",
                "existing GraphML snapshot hash and parseability when present, or explicit missing status when absent",
                "sidecar availability and projection summaries over the loaded owner snapshot",
                "existing runtime evidence bridge presence and owner-snapshot alignment when present",
                "existing bounded retrieval sidecar presence and safety flags when present",
                "existing Hopf/Weyl carrier projection presence and owner-snapshot alignment when present",
                "existing Hopf/Weyl evidence audit presence and owner-snapshot alignment when present",
                "existing torus/type repair-gap report presence and owner-snapshot alignment when present",
                "coarse promotion-gate state for owner structure, cross-layer alignment, runtime state, and history graph presence",
            ],
            "does_not_verify": [
                "that the owner graph matches docs or runtime semantics beyond the stored snapshot",
                "that the existing GraphML snapshot is fresh unless it was explicitly refreshed in this run",
                "that a present runtime evidence bridge constitutes a promoted runtime-state or history graph",
                "that a present retrieval sidecar constitutes embedding-backed LightRAG retrieval or owner-authoritative memory",
                "that a present Hopf/Weyl projection constitutes promoted torus 2-cells, instantiated Weyl branches, or validated spinor semantics",
                "that a present Hopf/Weyl evidence audit constitutes promotion evidence or validated live Weyl branch semantics",
                "that a present torus/type repair-gap report constitutes repair completion or promotion evidence",
                "that sidecar outputs are promotion-ready owner truth",
                "that any blocked promotion gate should be auto-promoted or auto-repaired",
                "that a PRECHECK_OK promotion gate satisfies the negative-proof, round-trip, no-sidecar-read, or human-audit requirements from the promotion-gates doc",
            ],
        },
        "owner": {
            "qit_graph_json": str(QIT_GRAPH_JSON),
            "qit_graph_action": owner_snapshot["action"],
            "qit_graph_sha256": owner_snapshot["file_sha256"],
            "qit_graph_size_bytes": owner_snapshot["size_bytes"],
            "qit_graph_schema": owner_snapshot["schema"],
            "qit_graph_generated_utc": owner_snapshot["generated_utc"],
            "qit_graph_content_hash": owner_snapshot["embedded_content_hash"],
            "qit_graph_content_hash_recomputed": owner_snapshot["recomputed_content_hash"],
            "qit_graph_content_hash_matches_recomputed": owner_snapshot["embedded_content_hash_matches_recomputed"],
            "graphml_export": graphml,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "live_node_types": live_node_types,
            "schema_ready_not_instantiated": schema_ready_not_instantiated,
            "schema_validation": schema_status,
            "owner_summary_validation_errors": owner_snapshot["summary_validation_errors"],
        },
        "sidecars": {
            "preferred_sidecar_interpreter": {
                "path": str(PREFERRED_INTERPRETER),
                "exists": preferred_interpreter_exists,
            },
            "toponetx": {
                **toponetx,
                "available_current_interpreter": bool(toponetx.get("available", False)),
                "importable_preferred_interpreter": _module_available_in_interpreter(PREFERRED_INTERPRETER, "toponetx"),
            },
            "clifford": clifford,
            "pyg": {
                **pyg,
                "available_current_interpreter": bool(pyg.get("available", False)),
                "importable_preferred_interpreter": _module_available_in_interpreter(PREFERRED_INTERPRETER, "torch_geometric"),
            },
            "lightrag": {
                **_lightrag_status(),
                "role": "read-only retrieval sidecar over internal graph/docs/evidence corpus; not owner memory",
            },
        },
        "runtime_evidence_bridge": runtime_evidence_bridge,
        "retrieval_sidecar": retrieval_sidecar,
        "hopf_weyl_projection": hopf_weyl_projection,
        "hopf_weyl_evidence_audit": hopf_weyl_evidence_audit,
        "torus_type_repair_gap_report": torus_type_repair_gap_report,
        "promotion_gates": promotion_gates,
        "next_actions": [
            "keep owner verification read-only by default and use refresh flags only for intentional artifact regeneration",
            "treat snapshot_id plus file hashes as the join key for future audit/report surfaces",
            "admit explicit QIT bridge links through the registry before claiming nested-graph integration beyond summary-level presence",
            "persist and expand the read-only runtime evidence bridge before promoting runtime/history semantics inward",
            "use the bounded retrieval sidecar as context only until embedding-backed LightRAG query is configured and explicitly kept non-authoritative",
            "treat the Hopf/Weyl projection as a bounded carrier map only; do not infer promoted torus 2-cells or live Weyl branches from its presence",
            "treat the Hopf/Weyl evidence audit as a bounded audit surface only; do not treat it as promotion evidence",
            "treat the torus/type repair-gap report as a bounded repair map only; do not treat listed gaps as already repaired",
            "promote torus/chirality/runtime semantics only after negative-proof and round-trip gates are satisfied",
        ],
    }
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the QIT graph stack without mutating owner truth by default.")
    parser.add_argument(
        "--refresh-owner",
        action="store_true",
        help="Explicitly rebuild the owner QIT JSON snapshot before verification.",
    )
    parser.add_argument(
        "--refresh-graphml",
        action="store_true",
        help="Explicitly rewrite the GraphML sidecar from the loaded owner snapshot before verification.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Persist the tracked JSON/Markdown status artifacts after verification.",
    )
    return parser.parse_args()


def _report_content_hash(report: dict[str, Any]) -> str:
    """Hash the report excluding volatile fields so unchanged audits don't churn."""
    stable = {k: v for k, v in report.items() if k != "generated_utc"}
    return _canonical_sha256(stable)


def main() -> None:
    args = _parse_args()
    report = build_qit_graph_stack_status(
        refresh_owner=args.refresh_owner,
        refresh_graphml=args.refresh_graphml,
    )

    new_hash = _report_content_hash(report)

    old_hash = None
    if REPORT_JSON.exists():
        try:
            old_report = _load_json(REPORT_JSON)
            old_hash = _report_content_hash(old_report)
        except Exception:
            old_hash = None

    report_changed = old_hash != new_hash

    if args.write_report:
        if report_changed:
            _write_json(REPORT_JSON, report)
            _write_text(REPORT_MD, _render_markdown(report))
            print("QIT graph stack status updated (content changed):")
            print(f"  JSON: {REPORT_JSON}")
            print(f"  MD:   {REPORT_MD}")
        else:
            print("QIT graph stack status unchanged — skipped rewrite.")
    else:
        state = "stale_on_disk" if report_changed else "matches_on_disk"
        print(f"QIT graph stack status built in memory only ({state}).")
        print("  Use --write-report to persist tracked status artifacts.")

    print(f"  GraphML: {GRAPHML_PATH} ({report['owner']['graphml_export']['action']})")


if __name__ == "__main__":
    main()
