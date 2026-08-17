from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_routes import verify


def test_fake_full_refuses() -> None:
    definition = {"children": [{"id": "a"}, {"id": "b"}]}
    execution = {"children": [{"child_id": "a"}], "route_truth": "FULL"}
    assert verify(definition, execution)["errors"] == ["missing_children", "fake_full"]
    assert verify(definition, execution)["route_truth"] == "NOT_FULL"
