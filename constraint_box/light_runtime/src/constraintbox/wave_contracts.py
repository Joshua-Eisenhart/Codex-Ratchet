"""Strict, bounded packets for the first local CB Light wave fixture.

This module is deliberately a *contract* boundary.  It does not schedule a
wave, call a model, select a provider, open a database, or settle a gate.
Pydantic and jsonschema are optional ``control-plane`` dependencies, so this
module stays importable in the base CB Light profile and reports a typed HOLD
when validation is requested without them.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Any, Literal, Mapping

from hookkernel.cb_light_domain import canonical_json as canonical_json_bytes


ISSUE_CARD_SCHEMA = "constraintbox.wave-issue-card.v1"
PROBE_PACKET_SCHEMA = "constraintbox.wave-probe-packet.v1"
PACKET_VALIDATION_SCHEMA = "constraintbox.wave-packet-validation.v1"

PROBE_KINDS = ("witness", "falsifier", "evidence_map")
ProbeKind = Literal["witness", "falsifier", "evidence_map"]

MAX_TARGETS = 8
MAX_PROBE_PAYLOAD_ITEMS = 8
MAX_EVIDENCE_REFS = 8
MAX_STATEMENT_CHARS = 512
MAX_PAYLOAD_VALUE_CHARS = 256

_IDENTIFIER_PATTERN = r"^[a-z0-9][a-z0-9_-]{2,63}$"
_DIGEST_PATTERN = r"^[0-9a-f]{64}$"
_PAYLOAD_KEY_PATTERN = r"^[a-z][a-z0-9_.-]{0,31}$"
_EVIDENCE_REF_PATTERN = r"^[a-z0-9][a-z0-9._:/@-]{0,127}$"
_IDENTIFIER_RE = re.compile(_IDENTIFIER_PATTERN)
_DIGEST_RE = re.compile(_DIGEST_PATTERN)
_PAYLOAD_KEY_RE = re.compile(_PAYLOAD_KEY_PATTERN)
_EVIDENCE_REF_RE = re.compile(_EVIDENCE_REF_PATTERN)

# These names would make untrusted probe input look like it can choose an LLM,
# provider, terminal result, or promotion.  No such field belongs in this
# fixture contract; unknown fields are also forbidden by the Pydantic models.
_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "model",
        "model_id",
        "model_name",
        "provider",
        "provider_id",
        "provider_name",
        "pass",
        "pass_state",
        "status",
        "disposition",
        "terminal",
        "terminal_state",
        "result",
        "outcome",
        "decision",
        "verdict",
        "settlement",
        "settled",
        "promotion",
        "promotion_allowed",
        "promoted",
        "adopted",
        "adoption",
        "adoption_allowed",
        "released",
        "release_allowed",
        "completion_allowed",
    }
)

CLAIM_CEILING = (
    "Typed local first-fixture envelope only; no controller, database, model, "
    "provider, skill execution, deterministic gate, settlement, promotion, "
    "portable adoption, CB Heavy, or release claim."
)


class WaveContractDependencyMissing(RuntimeError):
    """The optional strict-envelope profile is unavailable in this interpreter."""


@dataclass(frozen=True)
class IssueCard:
    """A sealed, finite problem statement shared by the three probe roles."""

    schema: str
    issue_id: str
    statement: str
    target_ids: tuple[str, ...]
    required_probe_kinds: tuple[ProbeKind, ...]
    root_input_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "issue_id": self.issue_id,
            "statement": self.statement,
            "target_ids": list(self.target_ids),
            "required_probe_kinds": list(self.required_probe_kinds),
            "root_input_sha256": self.root_input_sha256,
        }


@dataclass(frozen=True)
class ProbeSpec:
    """One constrained local observation role inside a :class:`ProbePacket`."""

    kind: ProbeKind
    node_id: str
    mmm_sha256: str
    constrained_input_sha256: str
    payload: tuple[tuple[str, str], ...]
    evidence_refs: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "node_id": self.node_id,
            "mmm_sha256": self.mmm_sha256,
            "constrained_input_sha256": self.constrained_input_sha256,
            "payload": dict(self.payload),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ProbePacket:
    """One bounded first-fixture packet containing all three required probes.

    ``wave_definition_id`` identifies a fixed packet shape only.  It is not a
    run or attempt identity: a future SQLite/controller layer must allocate a
    fresh attempt ID and bind it to this immutable packet separately.
    """

    schema: str
    packet_id: str
    wave_definition_id: str
    issue: IssueCard
    target_id: str
    probes: tuple[ProbeSpec, ...]

    def probe_for(self, kind: ProbeKind) -> ProbeSpec:
        for probe in self.probes:
            if probe.kind == kind:
                return probe
        # A validated packet always contains all three kinds.  Keeping this
        # explicit protects future controller code from hand-constructed input.
        raise ValueError(f"validated packet has no {kind!r} probe")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "packet_id": self.packet_id,
            "wave_definition_id": self.wave_definition_id,
            "issue": self.issue.as_dict(),
            "target_id": self.target_id,
            "probes": [probe.as_dict() for probe in self.probes],
        }


@dataclass(frozen=True)
class PacketValidation:
    """A typed boundary result; validation itself never settles a wave."""

    schema: str
    disposition: Literal["VALIDATED", "HOLD", "REFUSE"]
    reason_code: str
    detail: str
    packet: ProbePacket | None
    packet_sha256: str | None
    contract_schema_sha256: str | None
    claim_ceiling: str = CLAIM_CEILING

    @property
    def is_validated(self) -> bool:
        return self.disposition == "VALIDATED" and self.packet is not None

    def as_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "schema": self.schema,
            "disposition": self.disposition,
            "reason_code": self.reason_code,
            "detail": self.detail,
            "claim_ceiling": self.claim_ceiling,
        }
        if self.packet_sha256 is not None:
            body["packet_sha256"] = self.packet_sha256
        if self.contract_schema_sha256 is not None:
            body["contract_schema_sha256"] = self.contract_schema_sha256
        return body


def canonical_packet_bytes(packet: ProbePacket) -> bytes:
    """Serialize a validated packet in a hash-seed-independent form."""

    return canonical_json_bytes(packet.as_dict())


def packet_sha256(packet: ProbePacket) -> str:
    return sha256(canonical_packet_bytes(packet)).hexdigest()


def _dependency_missing(name: str) -> WaveContractDependencyMissing:
    return WaveContractDependencyMissing(
        f"The optional wave-contract dependency is unavailable: {name}."
    )


def _load_contract_dependencies():
    """Import optional validators only when packet validation is requested."""

    try:
        from pydantic import (
            BaseModel,
            ConfigDict,
            Field,
            ValidationError,
            field_validator,
            model_validator,
        )
    except ModuleNotFoundError as exc:
        if exc.name in {"pydantic", "pydantic_core"}:
            raise _dependency_missing(exc.name) from exc
        raise

    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        if exc.name == "jsonschema":
            raise _dependency_missing(exc.name) from exc
        raise

    return (
        BaseModel,
        ConfigDict,
        Field,
        ValidationError,
        field_validator,
        model_validator,
        jsonschema,
    )


def _contract_models():
    """Build the strict Pydantic models after optional dependencies are present."""

    (
        BaseModel,
        ConfigDict,
        Field,
        ValidationError,
        field_validator,
        model_validator,
        jsonschema,
    ) = _load_contract_dependencies()

    class IssueCardModel(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

        contract_schema: Literal[ISSUE_CARD_SCHEMA] = Field(
            alias="schema", serialization_alias="schema"
        )
        issue_id: str = Field(
            min_length=3,
            max_length=64,
            pattern=_IDENTIFIER_PATTERN,
        )
        statement: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
        target_ids: list[str] = Field(min_length=1, max_length=MAX_TARGETS)
        required_probe_kinds: list[ProbeKind] = Field(
            min_length=len(PROBE_KINDS), max_length=len(PROBE_KINDS)
        )
        root_input_sha256: str = Field(pattern=_DIGEST_PATTERN)

        @field_validator("statement")
        @classmethod
        def statement_must_not_be_blank(cls, value: str) -> str:
            if not value.strip():
                raise ValueError("statement must not be blank")
            return value

        @field_validator("target_ids")
        @classmethod
        def finite_unique_target_ids(cls, values: list[str]) -> list[str]:
            if any(not _IDENTIFIER_RE.fullmatch(value) for value in values):
                raise ValueError("target_ids must contain bounded identifiers")
            if len(set(values)) != len(values):
                raise ValueError("target_ids must be unique")
            return values

        @field_validator("required_probe_kinds")
        @classmethod
        def exact_first_fixture_probe_kinds(
            cls, values: list[ProbeKind]
        ) -> list[ProbeKind]:
            if set(values) != set(PROBE_KINDS) or len(set(values)) != len(values):
                raise ValueError(
                    "required_probe_kinds must contain witness, falsifier, and evidence_map exactly once"
                )
            return values

    class ProbeSpecModel(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

        kind: ProbeKind
        node_id: str = Field(
            min_length=3,
            max_length=64,
            pattern=_IDENTIFIER_PATTERN,
        )
        mmm_sha256: str = Field(pattern=_DIGEST_PATTERN)
        constrained_input_sha256: str = Field(pattern=_DIGEST_PATTERN)
        payload: dict[str, str] = Field(
            min_length=1, max_length=MAX_PROBE_PAYLOAD_ITEMS
        )
        evidence_refs: list[str] = Field(
            min_length=1, max_length=MAX_EVIDENCE_REFS
        )

        @field_validator("payload")
        @classmethod
        def bounded_payload(cls, value: dict[str, str]) -> dict[str, str]:
            for key, item in value.items():
                if not _PAYLOAD_KEY_RE.fullmatch(key):
                    raise ValueError("payload keys must be bounded identifiers")
                if not item or len(item) > MAX_PAYLOAD_VALUE_CHARS:
                    raise ValueError("payload values must be nonempty and bounded")
            return value

        @field_validator("evidence_refs")
        @classmethod
        def bounded_unique_evidence_refs(cls, values: list[str]) -> list[str]:
            if any(not _EVIDENCE_REF_RE.fullmatch(value) for value in values):
                raise ValueError("evidence_refs must contain bounded opaque references")
            if len(set(values)) != len(values):
                raise ValueError("evidence_refs must be unique")
            return values

    class ProbePacketModel(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

        contract_schema: Literal[PROBE_PACKET_SCHEMA] = Field(
            alias="schema", serialization_alias="schema"
        )
        packet_id: str = Field(
            min_length=3,
            max_length=64,
            pattern=_IDENTIFIER_PATTERN,
        )
        wave_definition_id: str = Field(
            min_length=3,
            max_length=64,
            pattern=_IDENTIFIER_PATTERN,
        )
        issue: IssueCardModel
        target_id: str = Field(
            min_length=3,
            max_length=64,
            pattern=_IDENTIFIER_PATTERN,
        )
        probes: list[ProbeSpecModel] = Field(
            min_length=len(PROBE_KINDS), max_length=len(PROBE_KINDS)
        )

        @model_validator(mode="after")
        def bind_first_fixture_structure(self):
            if self.target_id not in self.issue.target_ids:
                raise ValueError("target_id must be a member of issue.target_ids")

            kinds = [probe.kind for probe in self.probes]
            if set(kinds) != set(PROBE_KINDS) or len(set(kinds)) != len(kinds):
                raise ValueError(
                    "probes must contain witness, mandatory falsifier, and evidence_map exactly once"
                )
            if set(kinds) != set(self.issue.required_probe_kinds):
                raise ValueError("probes must match issue.required_probe_kinds")

            node_ids = [probe.node_id for probe in self.probes]
            if len(set(node_ids)) != len(node_ids):
                raise ValueError("each probe needs a distinct node_id")

            mmm_hashes = [probe.mmm_sha256 for probe in self.probes]
            if len(set(mmm_hashes)) != len(mmm_hashes):
                raise ValueError("each probe needs a distinct MMM digest")

            input_hashes = [probe.constrained_input_sha256 for probe in self.probes]
            if len(set(input_hashes)) != len(input_hashes):
                raise ValueError(
                    "each probe needs a distinct constrained-input digest"
                )
            return self

    return ProbePacketModel, ValidationError, jsonschema


def _forbidden_authority_key(raw: Any) -> str | None:
    """Find a forbidden field name without treating untrusted values as policy."""

    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if isinstance(key, str) and key.lower() in _FORBIDDEN_AUTHORITY_KEYS:
                return key
            nested = _forbidden_authority_key(value)
            if nested is not None:
                return nested
    elif isinstance(raw, list):
        for value in raw:
            nested = _forbidden_authority_key(value)
            if nested is not None:
                return nested
    return None


def _validation_reason(errors: list[dict[str, Any]]) -> str:
    for error in errors:
        if error.get("type") == "extra_forbidden":
            return "REFUSE_UNEXPECTED_FIELD"
        message = str(error.get("msg", "")).lower()
        if "falsifier" in message:
            return "REFUSE_FALSIFIER_REQUIRED"
    return "REFUSE_WAVE_PACKET_INVALID"


def _raw_packet_omits_falsifier(raw: Mapping[str, Any]) -> bool:
    """Recognize the protected missing-falsifier case before generic errors.

    This remains only a reason-code refinement.  Pydantic still performs the
    authoritative type/shape validation after this narrow structural check.
    """

    probes = raw.get("probes")
    if not isinstance(probes, list) or not all(
        isinstance(probe, Mapping) for probe in probes
    ):
        return False
    return all(probe.get("kind") != "falsifier" for probe in probes)


def _packet_from_payload(payload: Mapping[str, Any]) -> ProbePacket:
    issue_payload = payload["issue"]
    issue = IssueCard(
        schema=issue_payload["schema"],
        issue_id=issue_payload["issue_id"],
        statement=issue_payload["statement"],
        target_ids=tuple(sorted(issue_payload["target_ids"])),
        required_probe_kinds=tuple(PROBE_KINDS),
        root_input_sha256=issue_payload["root_input_sha256"],
    )
    order = {kind: index for index, kind in enumerate(PROBE_KINDS)}
    probes = tuple(
        ProbeSpec(
            kind=probe_payload["kind"],
            node_id=probe_payload["node_id"],
            mmm_sha256=probe_payload["mmm_sha256"],
            constrained_input_sha256=probe_payload["constrained_input_sha256"],
            payload=tuple(sorted(probe_payload["payload"].items())),
            evidence_refs=tuple(sorted(probe_payload["evidence_refs"])),
        )
        for probe_payload in sorted(
            payload["probes"],
            key=lambda item: order[item["kind"]],
        )
    )
    return ProbePacket(
        schema=payload["schema"],
        packet_id=payload["packet_id"],
        wave_definition_id=payload["wave_definition_id"],
        issue=issue,
        target_id=payload["target_id"],
        probes=probes,
    )


def _result(
    disposition: Literal["VALIDATED", "HOLD", "REFUSE"],
    reason_code: str,
    detail: str,
    *,
    packet: ProbePacket | None = None,
    contract_schema_sha256: str | None = None,
) -> PacketValidation:
    return PacketValidation(
        schema=PACKET_VALIDATION_SCHEMA,
        disposition=disposition,
        reason_code=reason_code,
        detail=detail,
        packet=packet,
        packet_sha256=packet_sha256(packet) if packet is not None else None,
        contract_schema_sha256=contract_schema_sha256,
    )


def validate_probe_packet(raw: Any) -> PacketValidation:
    """Validate one sealed first-fixture packet without granting any authority.

    The base profile can call this function safely: if Pydantic or jsonschema
    are absent it returns ``HOLD_WAVE_CONTRACT_DEPENDENCY_MISSING`` rather than
    leaking a dependency import error across a future controller boundary.
    """

    try:
        model, validation_error, jsonschema = _contract_models()
    except WaveContractDependencyMissing as exc:
        return _result(
            "HOLD",
            "HOLD_WAVE_CONTRACT_DEPENDENCY_MISSING",
            str(exc),
        )

    if not isinstance(raw, Mapping):
        return _result(
            "REFUSE",
            "REFUSE_WAVE_PACKET_INVALID",
            "A wave probe packet must be an object.",
        )
    forbidden = _forbidden_authority_key(raw)
    if forbidden is not None:
        return _result(
            "REFUSE",
            "REFUSE_FORBIDDEN_AUTHORITY_FIELD",
            f"The field {forbidden!r} is not permitted in a wave probe packet.",
        )
    if _raw_packet_omits_falsifier(raw):
        return _result(
            "REFUSE",
            "REFUSE_FALSIFIER_REQUIRED",
            "The first fixture requires one protected falsifier probe.",
        )

    try:
        value = model.model_validate(dict(raw), strict=True)
    except validation_error as exc:
        return _result(
            "REFUSE",
            _validation_reason(exc.errors()),
            "Strict wave probe packet validation failed.",
        )

    payload = value.model_dump(mode="json", by_alias=True)
    schema = model.model_json_schema(by_alias=True)
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError:
        return _result(
            "HOLD",
            "HOLD_WAVE_SCHEMA_CROSSCHECK_FAILED",
            "The generated JSON Schema rejected the strict wave packet.",
        )

    packet = _packet_from_payload(payload)
    return _result(
        "VALIDATED",
        "STRICT_WAVE_PACKET_VALIDATED",
        "A bounded local probe envelope was validated; no gate or settlement ran.",
        packet=packet,
        contract_schema_sha256=sha256(canonical_json_bytes(schema)).hexdigest(),
    )


__all__ = [
    "CLAIM_CEILING",
    "ISSUE_CARD_SCHEMA",
    "MAX_EVIDENCE_REFS",
    "MAX_PROBE_PAYLOAD_ITEMS",
    "MAX_STATEMENT_CHARS",
    "MAX_TARGETS",
    "PACKET_VALIDATION_SCHEMA",
    "PROBE_KINDS",
    "PROBE_PACKET_SCHEMA",
    "IssueCard",
    "PacketValidation",
    "ProbeKind",
    "ProbePacket",
    "ProbeSpec",
    "WaveContractDependencyMissing",
    "canonical_json_bytes",
    "canonical_packet_bytes",
    "packet_sha256",
    "validate_probe_packet",
]
