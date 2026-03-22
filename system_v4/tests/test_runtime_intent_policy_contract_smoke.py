"""Cross-layer smoke test for the normalized runtime intent-policy contract."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.a1_brain import A1Brain, Assertion, DefField, KernelCandidate
from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.intent_control_surface_builder import (
    SURFACE_REL_PATH,
    build_intent_control_surface,
)
from system_v4.skills.wiggle_lane_runner import build_wiggle_envelope
from system_v4.skills.witness_recorder import WitnessRecorder


def test_runtime_intent_policy_contract_smoke() -> None:
    original_extract = A1Brain.extract_kernel_candidate

    def fake_extract(self, concept_id, name, description, tags, properties):
        return [
            KernelCandidate(
                item_class="AXIOM_HYP",
                id=self._next_id("F"),
                kind="MATH_DEF",
                requires=[],
                def_fields=[DefField("DF_FAKE_01", "structural_form", "BARE", "intent_memory_loop")],
                asserts=[Assertion("A_FAKE_01", "STRUCTURAL", "intent_memory_loop")],
                source_concept_id=concept_id,
            )
        ]

    A1Brain.extract_kernel_candidate = fake_extract  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            refinery = A2GraphRefinery(td)
            raw_intent = refinery.record_intent_signal(
                "Preserve maker intent and save context continuously.",
                source_label="maker",
                intent_kind="MAKER_INTENT",
                tags=["priority:p0"],
            )
            assert raw_intent
            refined = refinery.refine_intent_signal(
                [raw_intent],
                "Keep maker intent graph-native and continuously available to A1 steering.",
                title="intent_runtime_policy_contract",
                tags=["graph-contract"],
            )
            assert refined

            recorder = WitnessRecorder(root / "system_v4" / "a2_state" / "witness_corpus_v1.json")
            recorder.record_intent(
                "Preserve maker intent and save context continuously.",
                source="maker",
                tags={"batch": "BATCH_CONTRACT", "phase": "STARTUP", "priority": "P0"},
            )
            recorder.record_context(
                "Batch startup context remains available to later phases.",
                source="system",
                tags={"batch": "BATCH_CONTRACT", "phase": "STARTUP"},
            )
            recorder.flush()

            build_intent_control_surface(td)
            surface = json.loads((root / SURFACE_REL_PATH).read_text(encoding="utf-8"))
            runtime_policy = surface["control"]["runtime_policy"]
            assert runtime_policy["steering_quality"]["status"] == "strong"
            assert runtime_policy["steering_focus_terms"]
            assert runtime_policy["executable_focus_terms"] == runtime_policy["steering_focus_terms"]
            assert runtime_policy["executable_non_negotiables"]

            concept_id = "A2_TEST::intent_memory_loop"
            graph_nodes = {
                concept_id: {
                    "id": concept_id,
                    "name": "intent_memory_loop",
                    "description": "Preserve maker intent continuously in graph-native memory.",
                    "tags": ["INTENT", "MEMORY", "CONTEXT"],
                }
            }

            brain = A1Brain(td, eval_mode=True)
            packet = brain.build_strategy_packet(
                [concept_id],
                graph_nodes,
                strategy_id="A1_STRAT_CONTRACT",
                intent_control=surface,
            )
            envelope = build_wiggle_envelope(
                repo=td,
                brain=brain,
                concept_ids=[concept_id],
                graph_nodes=graph_nodes,
                intent_control=surface,
            )

            assert packet.inputs["intent_control"]["runtime_policy"] == runtime_policy
            assert packet.self_audit["intent_control"]["runtime_policy"] == runtime_policy
            assert packet.inputs["intent_control"]["effective_runtime_policy"]["bias_config"]["max_alternatives_per_primary"] == 2
            assert len(packet.alternatives) == 2

            for lane_packet in envelope.lane_packets:
                assert lane_packet["inputs"]["intent_control"]["runtime_policy"] == runtime_policy
                assert lane_packet["inputs"]["intent_control"]["effective_runtime_policy"]["bias_config"]["max_alternatives_per_primary"] == 2
                assert len(lane_packet["alternatives"]) == 2

            assert envelope.merged_strategy_packet["inputs"]["intent_control"]["runtime_policy"] == runtime_policy
            assert envelope.merge_report["merged_alternative_count"] == 2
    finally:
        A1Brain.extract_kernel_candidate = original_extract  # type: ignore[assignment]

    print("PASS: test_runtime_intent_policy_contract_smoke")


if __name__ == "__main__":
    test_runtime_intent_policy_contract_smoke()
