from __future__ import annotations

import hashlib
from typing import Any

from ..contracts import DecisionRecord
from ..intake import canonical_json


def to_lev_evidence_event(
    decision: DecisionRecord,
    *,
    session_id: str,
    event_id: str,
) -> dict[str, Any]:
    """Translate a controller decision without granting Lev or CR truth authority."""
    if not session_id or not event_id:
        raise ValueError("session_id and event_id are required")
    decision_body = decision.to_dict()
    decision_digest = hashlib.sha256(canonical_json(decision_body)).hexdigest()
    return {
        "schema": "constraintbox.lev-evidence-event.v1",
        "session_id": session_id,
        "event_id": event_id,
        "decision_sha256": decision_digest,
        "request_id": decision.request_id,
        "task_kind": decision.task_kind,
        "disposition": decision.disposition.value,
        "reason": decision.reason,
        "claim_ceiling": decision.claim_ceiling,
        "controller_emitted": True,
        "promotion_allowed": False,
    }
