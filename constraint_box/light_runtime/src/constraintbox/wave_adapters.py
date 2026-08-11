"""Three deterministic, local-only observation adapters for the CB Light fixture.

They deliberately produce observations, not verdicts.  There is no model or
provider route here, and no adapter can emit a terminal or PASS-like outcome.
Future controller code must bind and evaluate these bytes explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal

from .wave_contracts import (
    ProbeKind,
    ProbePacket,
    canonical_json_bytes,
    packet_sha256,
)


OBSERVATION_SCHEMA = "constraintbox.wave-fixture-observation.v1"
OBSERVATION_KIND = "SYNTHETIC_LOCAL_OBSERVATION"
OBSERVATION_AUTHORITY = "NON_AUTHORITATIVE"
ADAPTER_CLAIM_CEILING = (
    "Deterministic local fake observation only; no model/provider invocation, "
    "skill execution, formal gate, controller, settlement, promotion, portable "
    "adoption, CB Heavy, or release claim."
)


@dataclass(frozen=True)
class ProbeObservation:
    """A replayable non-authoritative observation from one fixed fake adapter."""

    schema: str
    adapter_id: str
    probe_kind: ProbeKind
    packet_sha256: str
    probe_sha256: str
    evidence_refs: tuple[str, ...]
    observation_kind: Literal["SYNTHETIC_LOCAL_OBSERVATION"]
    authority: Literal["NON_AUTHORITATIVE"]
    claim_ceiling: str = ADAPTER_CLAIM_CEILING

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "adapter_id": self.adapter_id,
            "probe_kind": self.probe_kind,
            "packet_sha256": self.packet_sha256,
            "probe_sha256": self.probe_sha256,
            "evidence_refs": list(self.evidence_refs),
            "observation_kind": self.observation_kind,
            "authority": self.authority,
            "claim_ceiling": self.claim_ceiling,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.as_dict())


def _probe_sha256(packet: ProbePacket, kind: ProbeKind) -> str:
    probe = packet.probe_for(kind)
    return sha256(
        canonical_json_bytes(
            {
                "packet_sha256": packet_sha256(packet),
                "kind": probe.kind,
                "node_id": probe.node_id,
                "mmm_sha256": probe.mmm_sha256,
                "constrained_input_sha256": probe.constrained_input_sha256,
                "payload": dict(probe.payload),
                "evidence_refs": list(probe.evidence_refs),
            }
        )
    ).hexdigest()


def _observe(
    packet: ProbePacket,
    *,
    kind: ProbeKind,
    adapter_id: str,
) -> ProbeObservation:
    probe = packet.probe_for(kind)
    return ProbeObservation(
        schema=OBSERVATION_SCHEMA,
        adapter_id=adapter_id,
        probe_kind=kind,
        packet_sha256=packet_sha256(packet),
        probe_sha256=_probe_sha256(packet, kind),
        evidence_refs=probe.evidence_refs,
        observation_kind=OBSERVATION_KIND,
        authority=OBSERVATION_AUTHORITY,
    )


class WitnessObservationAdapter:
    """Local fixture adapter for the witness observation role."""

    adapter_id = "cb-light-fixture-witness-v1"

    def observe(self, packet: ProbePacket) -> ProbeObservation:
        return _observe(packet, kind="witness", adapter_id=self.adapter_id)


class FalsifierObservationAdapter:
    """Local fixture adapter for the protected falsifier observation role."""

    adapter_id = "cb-light-fixture-falsifier-v1"

    def observe(self, packet: ProbePacket) -> ProbeObservation:
        return _observe(packet, kind="falsifier", adapter_id=self.adapter_id)


class EvidenceMapObservationAdapter:
    """Local fixture adapter for the evidence-map observation role."""

    adapter_id = "cb-light-fixture-evidence-map-v1"

    def observe(self, packet: ProbePacket) -> ProbeObservation:
        return _observe(packet, kind="evidence_map", adapter_id=self.adapter_id)


def fixture_observation_adapters() -> tuple[
    WitnessObservationAdapter,
    FalsifierObservationAdapter,
    EvidenceMapObservationAdapter,
]:
    """Return the complete fixed three-adapter set in deterministic order."""

    return (
        WitnessObservationAdapter(),
        FalsifierObservationAdapter(),
        EvidenceMapObservationAdapter(),
    )


__all__ = [
    "ADAPTER_CLAIM_CEILING",
    "OBSERVATION_AUTHORITY",
    "OBSERVATION_KIND",
    "OBSERVATION_SCHEMA",
    "ProbeObservation",
    "WitnessObservationAdapter",
    "FalsifierObservationAdapter",
    "EvidenceMapObservationAdapter",
    "fixture_observation_adapters",
]
