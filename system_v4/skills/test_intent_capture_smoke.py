"""Smoke test for first-class intent capture in the A2 refinery graph."""

from __future__ import annotations

import tempfile

from system_v4.skills.a2_graph_refinery import A2GraphRefinery, RefineryLayer


def test_intent_capture_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        refinery = A2GraphRefinery(td)

        raw_user_intent = refinery.record_intent_signal(
            "Preserve maker intent and system intent as first-class graph memory.",
            source_label="user",
            intent_kind="MAKER_INTENT",
            tags=["persistence", "context"],
            witness_refs=["WITNESS_CORPUS::USER"],
        )
        raw_system_intent = refinery.record_intent_signal(
            "Continuously save context as the system runs so intent is not lost.",
            source_label="system",
            intent_kind="SYSTEM_INTENT",
            tags=["continuous-save", "context"],
            witness_refs=["WITNESS_CORPUS::SYSTEM"],
        )
        refined_intent = refinery.refine_intent_signal(
            [raw_user_intent, raw_system_intent],
            (
                "Operational contract: raw user/system intent is append-safe A2 intake; "
                "derived intent refinements remain explicit A2 graph objects linked back "
                "to their source intent signals."
            ),
            title="persistent_intent_contract",
            tags=["graph-contract"],
        )

        raw_node = refinery.builder.get_node(raw_user_intent)
        refined_node = refinery.builder.get_node(refined_intent)
        assert raw_node is not None
        assert refined_node is not None
        assert raw_node.node_type == "INTENT_SIGNAL"
        assert refined_node.node_type == "INTENT_REFINEMENT"
        assert raw_node.trust_zone == RefineryLayer.A2_3_INTAKE.value
        assert refined_node.trust_zone == RefineryLayer.A2_2_CANDIDATE.value
        assert "intent" in raw_node.tags
        assert "intent-refinement" in refined_node.tags
        assert raw_node.witness_refs == ["WITNESS_CORPUS::USER"]
        assert sorted(refined_node.witness_refs) == ["WITNESS_CORPUS::SYSTEM", "WITNESS_CORPUS::USER"]

        intent_edges = refinery.find_edges(relation_type="REFINES_INTENT")
        assert len(intent_edges) == 2
        assert all(edge["target_id"] == refined_intent for edge in intent_edges)

        # Persistence check: graph survives reload.
        reloaded = A2GraphRefinery(td)
        assert reloaded.builder.get_node(raw_user_intent) is not None
        assert reloaded.builder.get_node(refined_intent) is not None

        intent_nodes = reloaded.find_nodes(tags_any=["intent"])
        assert len(intent_nodes) == 3

    print("PASS: test_intent_capture_smoke")


if __name__ == "__main__":
    test_intent_capture_smoke()
