"""
Direct regression smoke for A2 high-intake projection metrics.

This guards the honest-reporting seam for the top A2 owner surface so it no
longer relies on materialization by omission.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_high_intake_graph_builder import write_a2_high_intake_graph


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_prerequisites(root: Path) -> None:
    _write_json(
        root / "system_v4" / "a2_state" / "graphs" / "identity_registry_v1.json",
        {"schema": "IDENTITY_REGISTRY_v1", "nodes": {}, "edges": []},
    )


def _seed_master_graph(root: Path) -> None:
    payload = {
        "schema": "V4_SYSTEM_GRAPH_v1",
        "nodes": {
            "A2_3::EXTRACTED::selected_a": {
                "id": "A2_3::EXTRACTED::selected_a",
                "node_type": "EXTRACTED_CONCEPT",
                "layer": "A2_HIGH_INTAKE",
                "trust_zone": "A2_HIGH_INTAKE",
                "status": "LIVE",
                "name": "selected_a",
            },
            "A2_3::EXTRACTED::selected_b": {
                "id": "A2_3::EXTRACTED::selected_b",
                "node_type": "EXTRACTED_CONCEPT",
                "layer": "A2_3_INTAKE",
                "trust_zone": "A2_3_INTAKE",
                "status": "QUEUED",
                "name": "selected_b",
            },
            "A2_3::EXTRACTED::outside_c": {
                "id": "A2_3::EXTRACTED::outside_c",
                "node_type": "EXTRACTED_CONCEPT",
                "layer": "A2_3",
                "trust_zone": "A2_3",
                "status": "LIVE",
                "name": "outside_c",
            },
            "A2_3::SOURCE::doc_1": {
                "id": "A2_3::SOURCE::doc_1",
                "node_type": "SOURCE_DOCUMENT",
                "layer": "A2_3_SOURCE",
                "status": "SOURCE",
                "name": "doc_1",
            },
            "A2_3::SOURCE::doc_2": {
                "id": "A2_3::SOURCE::doc_2",
                "node_type": "SOURCE_DOCUMENT",
                "layer": "A2_3_SOURCE",
                "status": "SOURCE",
                "name": "doc_2",
            },
        },
        "edges": [
            {
                "source_id": "A2_3::SOURCE::doc_1",
                "target_id": "A2_3::EXTRACTED::selected_a",
                "relation": "SOURCE_MAP_PASS",
                "attributes": {},
            },
            {
                "source_id": "A2_3::SOURCE::doc_1",
                "target_id": "A2_3::EXTRACTED::selected_b",
                "relation": "ENGINE_PATTERN_PASS",
                "attributes": {},
            },
            {
                "source_id": "A2_3::EXTRACTED::selected_a",
                "target_id": "A2_3::EXTRACTED::selected_b",
                "relation": "RELATED_TO",
                "attributes": {},
            },
            {
                "source_id": "A2_3::EXTRACTED::selected_a",
                "target_id": "A2_3::EXTRACTED::outside_c",
                "relation": "DEPENDS_ON",
                "attributes": {},
            },
        ],
    }
    _write_json(root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json", payload)


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="a2_high_metrics_smoke_"))
    try:
        _seed_prerequisites(temp_root)
        _seed_master_graph(temp_root)

        result = write_a2_high_intake_graph(str(temp_root))
        json_path = Path(result["json_path"])
        audit_note_path = Path(result["audit_note_path"])

        report = json.loads(json_path.read_text(encoding="utf-8"))
        audit_text = audit_note_path.read_text(encoding="utf-8")
        summary = report.get("summary", {})
        projection = report.get("projection_diagnostics", {})

        _assert(report.get("build_status") == "MATERIALIZED", "expected explicit high-intake build status")
        _assert(report.get("materialized") is True, "expected high-intake materialized flag to be true")
        _assert(summary.get("node_count") == 3, "expected two extracted nodes plus one anchored source document")
        _assert(summary.get("edge_count") == 3, "expected only internal selected edges to be included")
        _assert(
            summary.get("node_counts_by_type") == {"EXTRACTED_CONCEPT": 2, "SOURCE_DOCUMENT": 1},
            "expected selected node types to stay explicit",
        )
        _assert(summary.get("anchored_source_document_count") == 1, "expected one anchored source document")
        _assert(summary.get("included_extracted_concept_count") == 2, "expected two included extracted concepts")
        _assert(
            summary.get("excluded_node_types") == {"EXTRACTED_CONCEPT": 1, "SOURCE_DOCUMENT": 1},
            "expected excluded node types to stay explicit",
        )
        _assert(projection.get("attempted_internal_edge_count") == 3, "expected three internal selected edges")
        _assert(projection.get("selected_boundary_edge_count") == 1, "expected one boundary edge")
        _assert(projection.get("internal_edge_retention_ratio") == 0.75, "expected exact internal-retention ratio")
        _assert(
            projection.get("selected_node_counts_by_trust_zone")
            == {"": 1, "A2_3_INTAKE": 1, "A2_HIGH_INTAKE": 1},
            "expected trust-zone counts to stay explicit",
        )
        _assert(
            projection.get("selected_node_counts_by_status")
            == {"LIVE": 1, "QUEUED": 1, "SOURCE": 1},
            "expected status counts to stay explicit",
        )
        _assert("build_status: MATERIALIZED" in audit_text, "expected audit note to surface build status")
        _assert("materialized: True" in audit_text, "expected audit note to surface materialized flag")
        _assert("## Projection Diagnostics" in audit_text, "expected audit note to render projection diagnostics")
        _assert(
            "internal_edge_retention_ratio: 0.75" in audit_text,
            "expected audit note to surface the internal-retention metric",
        )
        print("A2 high intake graph metrics smoke")
        print("PASS: A2_HIGH surface now reports explicit materialization and projection metrics")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
