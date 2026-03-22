"""Smoke test that wiggle lanes respect stricter intent-derived alternative caps."""

from __future__ import annotations

import tempfile

from system_v4.skills.a1_brain import A1Brain, Assertion, DefField, KernelCandidate
from system_v4.skills.intent_runtime_policy import build_runtime_policy
from system_v4.skills.wiggle_lane_runner import build_wiggle_envelope


def test_wiggle_lane_intent_alternative_cap_smoke() -> None:
    original_extract = A1Brain.extract_kernel_candidate

    def fake_extract(self, concept_id, name, description, tags, properties):
        return [
            KernelCandidate(
                item_class="AXIOM_HYP",
                id=self._next_id("F"),
                kind="MATH_DEF",
                requires=[],
                def_fields=[DefField("DF_FAKE_01", "structural_form", "BARE", "density_matrix_channel")],
                asserts=[Assertion("A_FAKE_01", "STRUCTURAL", "density_matrix_channel")],
                source_concept_id=concept_id,
            )
        ]

    A1Brain.extract_kernel_candidate = fake_extract  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as td:
            brain = A1Brain(td, eval_mode=True)
            concept_id = "A2_TEST::density_matrix_channel"
            runtime_policy = build_runtime_policy(
                ["intent", "skill", "context"],
                [{"label": "intent_first_class"}],
            )
            envelope = build_wiggle_envelope(
                repo=td,
                brain=brain,
                concept_ids=[concept_id],
                graph_nodes={
                    concept_id: {
                        "id": concept_id,
                        "name": "density_matrix_channel",
                        "description": "Finite dimensional hilbert space density matrix channel.",
                        "tags": ["MATH", "TEST"],
                    }
                },
                intent_control={
                    "surface_id": "A2_INTENT_CONTROL__TEST",
                    "provenance": {"surface_hash": "abc123"},
                    "control": {
                        "runtime_policy": runtime_policy,
                    },
                    "self_audit": {"source_ids": ["WITNESS_CORPUS::0"]},
                },
            )
            lane_alt_counts = [len(packet["alternatives"]) for packet in envelope.lane_packets]
            assert lane_alt_counts == [2, 2]
            assert envelope.merge_report["merged_alternative_count"] == 2
            assert envelope.merged_strategy_packet["inputs"]["intent_control"]["runtime_policy"]["alternative_policy"]["max_alternatives_per_primary"] == 2
    finally:
        A1Brain.extract_kernel_candidate = original_extract  # type: ignore[assignment]

    print("PASS: test_wiggle_lane_intent_alternative_cap_smoke")


if __name__ == "__main__":
    test_wiggle_lane_intent_alternative_cap_smoke()
