from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_collapse import audit


def test_shared_roots_are_not_independent() -> None:
    lanes = [
        {"id": "a", "source_roots": ["x"], "prompt_sha256": "1", "conclusion": "go"},
        {"id": "b", "source_roots": ["x"], "prompt_sha256": "1", "conclusion": "go"},
    ]
    receipt = audit(lanes)
    assert receipt["status"] == "COLLAPSED"
    assert receipt["effective_independent_lanes"] == 1
    assert receipt["agent_count"] == 2


def test_copied_evidence_and_softened_falsifier_collapse() -> None:
    lanes = [
        {"id": "a", "source_roots": ["x"], "prompt_sha256": "1", "provider_ancestry": "p", "copied_evidence": True},
        {"id": "b", "source_roots": ["y"], "prompt_sha256": "2", "provider_ancestry": "p", "falsifier_softened": True},
    ]
    receipt = audit(lanes)
    assert "copied_evidence" in receipt["findings"]
    assert "softened_falsifiers" in receipt["findings"]
    assert "correlated_provider_ancestry" in receipt["findings"]
