"""Smoke test for downgraded intent-control steering quality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.intent_control_surface_builder import (
    SURFACE_REL_PATH,
    build_intent_control_surface,
)
from system_v4.skills.witness_recorder import WitnessRecorder


def test_intent_control_surface_builder_downgrade_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        refinery = A2GraphRefinery(td)
        raw_intent = refinery.record_intent_signal(
            "Its saved extracting design sources continuously.",
            source_label="maker",
            intent_kind="MAKER_INTENT",
            tags=["priority:p1"],
        )
        assert raw_intent
        refined = refinery.refine_intent_signal(
            [raw_intent],
            "Its saved extracting design sources continuously.",
            title="weak_runtime_intent",
            tags=["weak-intent"],
        )
        assert refined

        recorder = WitnessRecorder(root / "system_v4" / "a2_state" / "witness_corpus_v1.json")
        recorder.record_intent(
            "Its saved extracting design sources continuously.",
            source="maker",
            tags={"batch": "BATCH_WEAK", "phase": "STARTUP", "priority": "P1"},
        )
        recorder.record_context(
            "Weak batch startup context remains visible.",
            source="system",
            tags={"batch": "BATCH_WEAK", "phase": "STARTUP"},
        )
        recorder.flush()

        build_intent_control_surface(td)
        payload = json.loads((root / SURFACE_REL_PATH).read_text(encoding="utf-8"))
        runtime_policy = payload["control"]["runtime_policy"]

        assert runtime_policy["steering_quality"]["downgrade_applied"] is True
        assert runtime_policy["steering_quality"]["status"] == "degraded"
        assert runtime_policy["concept_selection"]["mode"] == "reorder_only"
        assert runtime_policy["candidate_policy"]["mode"] == "disabled"
        assert runtime_policy["alternative_policy"]["max_alternatives_per_primary"] == 2
        assert payload["control"]["steering_focus_terms"] == runtime_policy["steering_focus_terms"]

    print("PASS: test_intent_control_surface_builder_downgrade_smoke")


if __name__ == "__main__":
    test_intent_control_surface_builder_downgrade_smoke()
