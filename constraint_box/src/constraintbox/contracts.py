from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Disposition(str, Enum):
    """Operational disposition, never an unrestricted truth value."""

    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"
    PARKED = "PARKED"
    HOLD = "HOLD"


@dataclass(frozen=True)
class TaskRequest:
    """Untrusted request.

    It intentionally contains no executable, profile, tolerance, exemption,
    verdict, or promotion field.
    """

    task_kind: str
    payload: bytes
    request_id: str


@dataclass(frozen=True)
class ProfileOutcome:
    disposition: Disposition
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionRecord:
    schema: str
    request_id: str
    task_kind: str
    profile_id: str | None
    policy_sha256: str
    input_sha256: str | None
    disposition: Disposition
    reason: str
    evidence: dict[str, Any]
    claim_ceiling: str
    controller_emitted: bool = True
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["disposition"] = self.disposition.value
        return value
