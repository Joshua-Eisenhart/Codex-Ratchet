"""Smoke test for the derived A2 intent-control surface builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.intent_control_surface_builder import (
    build_intent_control_surface,
    SURFACE_REL_PATH,
)
from system_v4.skills.witness_recorder import WitnessRecorder


def test_intent_control_surface_builder_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        refinery = A2GraphRefinery(td)
        raw_intent = refinery.record_intent_signal(
            "Preserve maker intent and save context continuously.",
            source_label="maker",
            intent_kind="MAKER_INTENT",
            tags=["priority:p0"],
        )
        refined_intent = refinery.refine_intent_signal(
            [raw_intent],
            "Active control: preserve intent as graph-native memory and keep context continuous.",
            title="intent_control_contract",
            tags=["graph-contract"],
        )
        assert refined_intent

        recorder = WitnessRecorder(root / "system_v4" / "a2_state" / "witness_corpus_v1.json")
        recorder.record_intent(
            "Preserve maker intent and save context continuously.",
            source="maker",
            tags={"batch": "BATCH_TEST", "phase": "STARTUP", "priority": "P0"},
        )
        recorder.record_context(
            "Batch startup context should remain available to later phases.",
            source="system",
            tags={"batch": "BATCH_TEST", "phase": "STARTUP"},
        )
        recorder.flush()

        result = build_intent_control_surface(td)
        assert result["json_path"] == SURFACE_REL_PATH

        surface_path = root / SURFACE_REL_PATH
        assert surface_path.exists()
        payload = json.loads(surface_path.read_text(encoding="utf-8"))
        assert payload["schema"] == "A2_INTENT_CONTROL_SURFACE_v1"
        assert payload["surface_id"]
        assert payload["maker_intent"]["records"][0]["text"] == (
            "Preserve maker intent and save context continuously."
        )
        assert payload["runtime_context"]["records"][0]["text"] == (
            "Batch startup context should remain available to later phases."
        )
        refined_ids = [rec["node_id"] for rec in payload["refined_intent"]["records"]]
        assert refined_intent in refined_ids
        assert payload["self_audit"]["surface_hash"]
        assert payload["self_audit"]["source_ids"]
        assert payload["control"]["lane_id"] == "INTENT_PRESERVING_CURRENT"
        assert payload["control"]["runtime_policy"]["schema"] == "INTENT_RUNTIME_POLICY_v1"
        assert payload["control"]["runtime_policy"]["focus_terms"] == payload["control"]["focus_terms"]
        assert "intent" in payload["control"]["runtime_policy"]["steering_focus_terms"]
        assert (
            payload["control"]["runtime_policy"]["executable_focus_terms"]
            == payload["control"]["runtime_policy"]["steering_focus_terms"]
        )
        assert payload["control"]["runtime_policy"]["executable_non_negotiables"]
        assert payload["control"]["runtime_policy"]["steering_quality"]["status"] == "strong"
        assert payload["control"]["concept_selection"]["mode"] == "focus-term-gate-then-reorder"
        assert payload["control"]["concept_selection"]["gating_focus_terms"]
        assert payload["control"]["concept_selection"]["gate_min_concepts"] == 2
        assert payload["control"]["candidate_policy"]["mode"] == "suppress-off-focus-term-defs"
        assert payload["control"]["candidate_policy"]["suppress_term_defs_without_focus"] is True
        assert payload["control"]["alternative_policy"]["mode"] == "cap_alternatives_per_primary"
        assert payload["control"]["alternative_policy"]["max_alternatives_per_primary"] == 2
        assert payload["control"]["runtime_policy"]["alternative_policy"]["max_alternatives_per_primary"] == 2
        assert payload["control"]["bias_config"]["max_alternatives_per_primary"] == 2
        assert payload["control"]["executable_focus_terms"] == payload["control"]["steering_focus_terms"]

    print("PASS: test_intent_control_surface_builder_smoke")


if __name__ == "__main__":
    test_intent_control_surface_builder_smoke()
