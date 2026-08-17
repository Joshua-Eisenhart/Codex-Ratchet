from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_controller import run


def test_missing_child_is_partial_not_full() -> None:
    definition = {"wave_id": "demo", "loop": {"max_rounds": 1}, "children": [{"id": "a"}, {"id": "b"}]}
    execution = run(definition, [{"child_id": "a", "terminal_state": "COMPLETED"}])
    assert execution["schema"] == "constraintbox.wave-execution.v1"
    assert execution["state"] == "PARTIAL"
    assert execution["route_truth"] == "NOT_FULL"
    assert execution["content_interpreted"] is False
    assert execution["promotion_allowed"] is False
