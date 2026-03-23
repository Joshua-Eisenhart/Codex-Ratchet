"""Smoke test for audit-only overlay merge support in SystemGraphBuilder."""

from __future__ import annotations

import tempfile
from pathlib import Path

from system_v4.skills.v4_graph_builder import GraphNode, SystemGraphBuilder


def test_v4_graph_builder_overlay_merge_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        builder = SystemGraphBuilder(str(root))
        node_id = "TEST::NODE"
        builder.add_node(
            GraphNode(
                id=node_id,
                node_type="REFINED_CONCEPT",
                layer="A2_MID_REFINEMENT",
                name="test_node",
                description="Test node for audit-only overlay merge.",
                properties={
                    "existing": "keep",
                    "runtime_policy": {"status": "live"},
                    "control": {"mode": "active"},
                },
            )
        )

        merged = builder.merge_overlay_audit(
            node_id,
            "overlay_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
                "manual_review_required": True,
            },
        )
        assert merged is True

        node = builder.get_node(node_id)
        assert node is not None
        assert node.properties["existing"] == "keep"
        assert node.properties["runtime_policy"] == {"status": "live"}
        assert node.properties["control"] == {"mode": "active"}
        assert node.lineage_refs == []
        assert node.witness_refs == []
        assert node.source_class == "DERIVED"
        assert node.authority == "SOURCE_CLAIM"
        assert node.properties["overlay_audit"] == {
            "status": "audit_only_nonoperative",
            "runtime_effect": "none",
            "audit_only": True,
            "manual_review_required": True,
        }
        assert builder.graph.nodes[node_id]["existing"] == "keep"
        assert builder.graph.nodes[node_id]["runtime_policy"] == {"status": "live"}
        assert builder.graph.nodes[node_id]["control"] == {"mode": "active"}
        assert builder.graph.nodes[node_id]["overlay_audit"]["manual_review_required"] is True

        merged_second = builder.merge_overlay_audit(
            node_id,
            "overlay_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
                "disclaimers": ["manual review only"],
            },
        )
        assert merged_second is True
        assert builder.get_node(node_id).properties["overlay_audit"] == {
            "status": "audit_only_nonoperative",
            "runtime_effect": "none",
            "audit_only": True,
            "manual_review_required": True,
            "disclaimers": ["manual review only"],
        }
        assert builder.get_node(node_id).properties["runtime_policy"] == {"status": "live"}
        assert builder.get_node(node_id).properties["control"] == {"mode": "active"}

        rejected_forbidden = builder.merge_overlay_audit(
            node_id,
            "overlay_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
                "lineage_refs": ["WITNESS::BAD"],
            },
        )
        assert rejected_forbidden is False
        assert builder.get_node(node_id).properties["overlay_audit"] == {
            "status": "audit_only_nonoperative",
            "runtime_effect": "none",
            "audit_only": True,
            "manual_review_required": True,
            "disclaimers": ["manual review only"],
        }

        rejected_namespace = builder.merge_overlay_audit(
            node_id,
            "random_namespace",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
            },
        )
        assert rejected_namespace is False
        assert "random_namespace" not in builder.get_node(node_id).properties

        rejected_policy_namespace = builder.merge_overlay_audit(
            node_id,
            "runtime_policy",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
            },
        )
        assert rejected_policy_namespace is False

        rejected_control_namespace = builder.merge_overlay_audit(
            node_id,
            "control",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
            },
        )
        assert rejected_control_namespace is False

        rejected_nested_bad = builder.merge_overlay_audit(
            node_id,
            "overlay_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
                "graph_basis": {"witness_refs": ["WITNESS::BAD"]},
            },
        )
        assert rejected_nested_bad is False
        assert builder.get_node(node_id).properties["overlay_audit"] == {
            "status": "audit_only_nonoperative",
            "runtime_effect": "none",
            "audit_only": True,
            "manual_review_required": True,
            "disclaimers": ["manual review only"],
        }

        rejected_authority_lookalike = builder.merge_overlay_audit(
            node_id,
            "overlay_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
                "source_class": "EARNED_STATE",
            },
        )
        assert rejected_authority_lookalike is False

        rejected_shadow_provenance = builder.merge_overlay_audit(
            node_id,
            "overlay_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
                "source_witness_refs": ["WITNESS::SHADOW"],
            },
        )
        assert rejected_shadow_provenance is False

        rejected_non_dict_existing = builder.update_node(
            node_id,
            properties={
                "existing": "keep",
                "overlay_provenance_audit": "bad_shape",
            },
        )
        assert rejected_non_dict_existing is True
        rejected_overlay_shape = builder.merge_overlay_audit(
            node_id,
            "overlay_provenance_audit",
            {
                "status": "audit_only_nonoperative",
                "runtime_effect": "none",
                "audit_only": True,
            },
        )
        assert rejected_overlay_shape is False


if __name__ == "__main__":
    test_v4_graph_builder_overlay_merge_smoke()
    print("PASS: test_v4_graph_builder_overlay_merge_smoke")
