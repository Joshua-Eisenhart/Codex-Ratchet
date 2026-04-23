"""Smoke test for temp-only projection of archive overlay into node properties."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from system_v4.skills.intent_control_surface_builder import (
    build_stripped_provenance_overlay_projection_payload,
)
from system_v4.skills.v4_graph_builder import GraphNode, SystemGraphBuilder


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v4_graph_builder_overlay_projection_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    overlay_path = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "audit_logs"
        / "STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
    )
    live_refinery_path = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "graphs"
        / "system_graph_a2_refinery.json"
    )
    live_intent_control_path = (
        repo_root / "system_v4" / "a2_state" / "A2_INTENT_CONTROL__CURRENT__v1.json"
    )
    live_stripped_path = (
        repo_root / "system_v4" / "a1_state" / "a1_stripped_graph_v1.json"
    )
    overlay_before = _sha256(overlay_path)
    live_refinery_before = _sha256(live_refinery_path)
    live_intent_control_before = _sha256(live_intent_control_path)
    live_stripped_before = _sha256(live_stripped_path)

    overlay_payload = json.loads(overlay_path.read_text(encoding="utf-8"))
    projection_payload = build_stripped_provenance_overlay_projection_payload(
        overlay_payload
    )
    assert projection_payload["overlay_kind"] == "stripped_provenance_archive_projection"
    assert projection_payload["manual_review_required"] is True
    assert projection_payload["status"] == "audit_only_nonoperative"
    assert projection_payload["runtime_effect"] == "none"
    assert projection_payload["audit_only"] is True
    assert "source_witness_refs" not in projection_payload
    assert "source_lineage_refs" not in projection_payload
    assert "source_node_ids" not in projection_payload

    with tempfile.TemporaryDirectory() as td:
        builder = SystemGraphBuilder(td)
        target_node_id = str(overlay_payload["target"]["node_id"])
        builder.add_node(
            GraphNode(
                id=target_node_id,
                node_type=str(overlay_payload["target"]["node_type"]),
                layer=str(overlay_payload["target"]["layer"]),
                name=str(overlay_payload["target"]["name"]),
                description="Temp-only target for archive overlay projection proof.",
                properties={
                    "runtime_policy": {"status": "live"},
                    "control": {"mode": "active"},
                },
                lineage_refs=["LINEAGE::KEEP"],
                witness_refs=["WITNESS::KEEP"],
            )
        )

        merged = builder.merge_overlay_audit(
            target_node_id,
            "overlay_provenance_audit",
            projection_payload,
        )
        assert merged is True

        node = builder.get_node(target_node_id)
        assert node is not None
        assert node.lineage_refs == ["LINEAGE::KEEP"]
        assert node.witness_refs == ["WITNESS::KEEP"]
        assert node.properties["runtime_policy"] == {"status": "live"}
        assert node.properties["control"] == {"mode": "active"}
        assert node.properties["overlay_provenance_audit"] == projection_payload
        assert (
            builder.graph.nodes[target_node_id]["overlay_provenance_audit"][
                "overlay_kind"
            ]
            == "stripped_provenance_archive_projection"
        )

        builder.save_graph_artifacts("overlay_projection_smoke")
        temp_json = (
            Path(td)
            / "system_v4"
            / "a2_state"
            / "graphs"
            / "system_graph_overlay_projection_smoke.json"
        )
        assert temp_json.exists()

    assert _sha256(overlay_path) == overlay_before
    assert _sha256(live_refinery_path) == live_refinery_before
    assert _sha256(live_intent_control_path) == live_intent_control_before
    assert _sha256(live_stripped_path) == live_stripped_before


def test_v4_graph_builder_overlay_projection_strips_extra_primary_chain_fields_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    overlay_path = (
        repo_root
        / "system_v4"
        / "a2_state"
        / "audit_logs"
        / "STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json"
    )
    overlay_payload = json.loads(overlay_path.read_text(encoding="utf-8"))
    overlay_payload["donor_chain"]["primary_chain"][0]["extra_probe"] = {"nested": "value"}
    overlay_payload["donor_chain"]["primary_chain"][0]["source_concept_id"] = "CANDIDATE::PROBE"
    overlay_payload["donor_chain"]["primary_chain"][0]["via_relations"] = [
        "SOURCE_MAP_PASS",
        "BAD_REL",
        {"bad": "shape"},
        7,
    ]
    dropped_node_id = str(overlay_payload["donor_chain"]["primary_chain"][1]["node_id"])
    overlay_payload["donor_chain"]["primary_chain"][1]["role"] = {"bad": "shape"}
    overlay_payload["donor_chain"]["secondary_context_only"] = [
        {"node_id": "CTX::KEEP", "extra_nested": {"x": 1}},
        {"node_id": 7},
        {"bad": "shape"},
    ]
    overlay_payload["donor_chain"]["basis_edge_relations"] = [
        "REL::KEEP",
        {"bad": "shape"},
        9,
    ]
    overlay_payload["donor_chain"]["supporting_source_doc_ids"] = [
        "DOC::KEEP",
        {"bad": "shape"},
    ]
    overlay_payload["donor_chain"]["bridge_source_node_ids"] = [
        "BRIDGE::KEEP",
        ["bad", "shape"],
    ]
    overlay_payload["disclaimers"] = [
        "NOTE::KEEP",
        {"bad": "shape"},
    ]

    projection_payload = build_stripped_provenance_overlay_projection_payload(
        overlay_payload
    )
    first_item = projection_payload["primary_donor_chain"][0]
    assert first_item["node_id"] == "A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION"
    assert set(first_item.keys()) <= {
        "node_id",
        "role",
        "layer",
        "node_type",
        "name",
        "via_relations",
    }
    assert "extra_probe" not in first_item
    assert "source_concept_id" not in first_item
    assert first_item["via_relations"] == ["SOURCE_MAP_PASS"]
    assert dropped_node_id not in {
        item["node_id"] for item in projection_payload["primary_donor_chain"]
    }
    assert all(
        item["role"]
        in {
            "target_stripped_node",
            "strongest_semantic_donor",
            "source_document_ancestor",
        }
        for item in projection_payload["primary_donor_chain"]
    )
    assert projection_payload["secondary_context_node_ids"] == ["CTX::KEEP"]
    assert projection_payload["basis_edge_relations"] == ["REL::KEEP"]
    assert projection_payload["supporting_source_doc_ids"] == ["DOC::KEEP"]
    assert projection_payload["bridge_source_node_ids"] == ["BRIDGE::KEEP"]
    assert projection_payload["disclaimers"] == ["NOTE::KEEP"]

    with tempfile.TemporaryDirectory() as td:
        builder = SystemGraphBuilder(td)
        target_node_id = str(overlay_payload["target"]["node_id"])
        builder.add_node(
            GraphNode(
                id=target_node_id,
                node_type=str(overlay_payload["target"]["node_type"]),
                layer=str(overlay_payload["target"]["layer"]),
                name=str(overlay_payload["target"]["name"]),
                description="Temp-only target for archive overlay projection sanitization proof.",
            )
        )
        assert (
            builder.merge_overlay_audit(
                target_node_id,
                "overlay_provenance_audit",
                projection_payload,
            )
            is True
        )


if __name__ == "__main__":
    test_v4_graph_builder_overlay_projection_smoke()
    test_v4_graph_builder_overlay_projection_strips_extra_primary_chain_fields_smoke()
    print("PASS: test_v4_graph_builder_overlay_projection_smoke")
