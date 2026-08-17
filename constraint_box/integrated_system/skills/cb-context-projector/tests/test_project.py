from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.project import project


def test_shared_roots_refuse() -> None:
    kernel = {"object_hash": "a" * 64, "hard_constraints": ["no rebase"], "claim_ceiling": "exists"}
    lanes = [{"id": "a", "source_roots": ["x"]}, {"id": "b", "source_roots": ["x"]}]
    assert project(kernel, lanes)["reason"] == "REFUSE_SHARED_SOURCE_ROOTS"


def test_distinct_roots_project() -> None:
    kernel = {"object_hash": "a" * 64, "hard_constraints": ["no rebase"], "claim_ceiling": "exists"}
    lanes = [{"id": "a", "source_roots": ["x"]}, {"id": "b", "source_roots": ["y"]}]
    receipt = project(kernel, lanes)
    assert receipt["status"] == "PROJECTED"
    assert receipt["packets"][0]["kernel"]["object_hash"] == "a" * 64
