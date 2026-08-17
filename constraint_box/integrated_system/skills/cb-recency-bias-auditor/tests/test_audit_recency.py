from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_recency import audit


def test_unexplained_flip_refuses() -> None:
    assert audit({"decision": "go"}, {"decision": "stop"})["reason"] == "REFUSE_RECENCY_FLIP"
    assert audit({"decision": "go", "causal_evidence": "seed went red"}, {"decision": "stop"})["status"] == "EXPLAINED"
