"""Receipt-bound append-only deltas for consumed tool-field maps.

The field runner produces a measured quotient.  A consumer must not silently
turn that quotient into a new source of truth: it has to leave a small,
replayable observation that names the exact map, packet, return, operation,
runtime source, and negative controls it used.  This module owns that narrow
artifact.  It deliberately does not rank tools or admit an operation.

The delta is a content-addressed JSON record.  ``apply_map_delta`` copies a
map and appends the record to ``map_delta_history`` only when the supplied map
has the exact digest named by the delta.  A changed base, changed delta, or
missing negative evidence is a refusal; there is no partial write path.
"""

from __future__ import annotations

import copy
import io
import re
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .protocol import (
    ZipJobRefusal,
    canonical_json_bytes,
    runtime_source_sha256,
    sha256_bytes,
    strict_json_loads,
    validate_return_zip,
)


MAP_DELTA_SCHEMA = "constraintbox.measured_tool_map_delta.v1"
MAP_DELTA_CLAIM_CEILING = (
    "local_append_only_map_observation;not_tool_rank;not_admission;not_release"
)
MAP_QUOTIENT_PATH = "output/measured_quotient.json"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_OPERATION_RESULT = re.compile(r"^[A-Z][A-Z0-9._-]{0,63}$")
_FACT_KINDS = ("boundary", "refusal", "replay", "no_write")
_NEGATIVE_RESULTS = frozenset({"REFUSED", "HOLD", "FAILED", "CANCELLED"})


def _digest(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase sha256 digest")
    return value


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, populate_by_name=True)


class MapFact(_StrictModel):
    """One independently evidenced fact attached to a map-consuming run."""

    fact_kind: Literal["boundary", "refusal", "replay", "no_write"]
    tool_id: str = Field(min_length=1, max_length=128)
    observed: bool
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    detail: str = Field(default="", max_length=512)
    fact_id: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def fact_identity(self) -> "MapFact":
        if not _ID.fullmatch(self.tool_id):
            raise ValueError("invalid fact tool id")
        body = self.model_dump(mode="json", exclude={"fact_id"})
        expected = sha256_bytes(canonical_json_bytes(body))
        if self.fact_id != expected:
            raise ValueError("fact_id does not bind fact bytes")
        return self


class MapObservationBuckets(_StrictModel):
    boundary: list[MapFact] = Field(default_factory=list)
    refusal: list[MapFact] = Field(default_factory=list)
    replay: list[MapFact] = Field(default_factory=list)
    no_write: list[MapFact] = Field(default_factory=list)


class MapDelta(_StrictModel):
    schema_: Literal[MAP_DELTA_SCHEMA] = Field(alias="schema")
    delta_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_map_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prior_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prior_return_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prior_quotient_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    operation_id: str = Field(min_length=1, max_length=128)
    operation_result: str = Field(min_length=1, max_length=64)
    operation_result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    required_tool_ids: list[str] = Field(default_factory=list, max_length=512)
    observations: MapObservationBuckets
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    append_only: Literal[True]
    claim_ceiling: Literal[MAP_DELTA_CLAIM_CEILING]

    @model_validator(mode="after")
    def delta_invariants(self) -> "MapDelta":
        if not _ID.fullmatch(self.operation_id):
            raise ValueError("invalid operation_id")
        if not _OPERATION_RESULT.fullmatch(self.operation_result):
            raise ValueError("invalid operation_result")
        if self.required_tool_ids != sorted(set(self.required_tool_ids)):
            raise ValueError("required_tool_ids must be unique and sorted")
        if any(not _ID.fullmatch(tool_id) for tool_id in self.required_tool_ids):
            raise ValueError("invalid required tool id")

        all_facts = [
            fact
            for kind in _FACT_KINDS
            for fact in getattr(self.observations, kind)
        ]
        if len({fact.fact_id for fact in all_facts}) != len(all_facts):
            raise ValueError("duplicate map fact")
        for kind in _FACT_KINDS:
            if any(fact.fact_kind != kind for fact in getattr(self.observations, kind)):
                raise ValueError(f"fact in wrong bucket:{kind}")
        undeclared = sorted(
            {
                fact.tool_id
                for fact in all_facts
                if fact.tool_id != "__operation__" and fact.tool_id not in self.required_tool_ids
            }
        )
        if undeclared:
            raise ValueError(f"undeclared tool facts:{','.join(undeclared)}")

        if not any(fact.observed for fact in self.observations.replay):
            raise ValueError("a map delta requires an observed replay fact")
        if self.operation_result in _NEGATIVE_RESULTS:
            if not any(fact.observed for fact in self.observations.refusal):
                raise ValueError("negative operation requires an observed refusal fact")
            if not any(fact.observed for fact in self.observations.no_write):
                raise ValueError("negative operation requires an observed no-write fact")
        return self


def _fact(
    fact_kind: str,
    value: MapFact | Mapping[str, Any],
) -> MapFact:
    """Normalize one caller fact and bind its identity to its exact fields."""

    if fact_kind not in _FACT_KINDS:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_FACT_KIND", fact_kind)
    if isinstance(value, MapFact):
        if value.fact_kind != fact_kind:
            raise ZipJobRefusal("REFUSE_MAP_DELTA_FACT_BUCKET", value.fact_id)
        return value
    if not isinstance(value, Mapping):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_FACT_SHAPE", fact_kind)
    raw = dict(value)
    supplied_kind = raw.get("fact_kind", fact_kind)
    if supplied_kind != fact_kind:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_FACT_BUCKET", str(supplied_kind))
    raw["fact_kind"] = fact_kind
    try:
        raw["evidence_sha256"] = _digest(raw["evidence_sha256"], label="evidence_sha256")
        raw["fact_id"] = sha256_bytes(
            canonical_json_bytes({key: raw[key] for key in raw if key != "fact_id"})
        )
        return MapFact.model_validate(raw, strict=True)
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_FACT_INVALID", f"{fact_kind}:{exc}") from exc


def make_map_fact(
    *,
    fact_kind: Literal["boundary", "refusal", "replay", "no_write"],
    tool_id: str,
    observed: bool,
    evidence_sha256: str,
    detail: str = "",
) -> dict[str, Any]:
    """Create a caller-friendly, digest-bound fact dictionary.

    ``evidence_sha256`` is deliberately a digest, not prose or an untrusted
    claim.  The caller may hash the exact receipt/result bytes before calling
    this helper.
    """

    raw = {
        "fact_kind": fact_kind,
        "tool_id": tool_id,
        "observed": observed,
        "evidence_sha256": evidence_sha256,
        "detail": detail,
    }
    return _fact(fact_kind, raw).model_dump(mode="json")


def _facts(
    kind: str,
    values: Iterable[MapFact | Mapping[str, Any]],
) -> list[MapFact]:
    try:
        result = [_fact(kind, value) for value in values]
    except TypeError as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_FACTS_NOT_ITERABLE", kind) from exc
    return sorted(result, key=lambda value: value.fact_id)


def _prior_return_member(return_bytes: bytes, path: str) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(return_bytes), "r") as archive:
            return archive.read(path)
    except (KeyError, zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_RETURN_OUTPUT", path) from exc


def _validate_prior_artifacts(
    *,
    prior_map_bytes: bytes,
    prior_packet_bytes: bytes,
    prior_return_bytes: bytes,
    prior_quotient_bytes: bytes,
) -> str:
    if not all(
        isinstance(value, bytes)
        for value in (prior_map_bytes, prior_packet_bytes, prior_return_bytes, prior_quotient_bytes)
    ):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_ARTIFACT_TYPE")
    try:
        prior_map = strict_json_loads(prior_map_bytes, label="prior_map")
        prior_quotient = strict_json_loads(prior_quotient_bytes, label="prior_quotient")
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_MAP_JSON", str(exc)) from exc
    if not isinstance(prior_map, dict) or not isinstance(prior_quotient, dict):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_MAP_SHAPE")
    if sha256_bytes(prior_map_bytes) != sha256_bytes(prior_quotient_bytes):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_QUOTIENT_BASE_MISMATCH")
    try:
        return_manifest = validate_return_zip(
            prior_return_bytes,
            expected_input_sha256=sha256_bytes(prior_packet_bytes),
            input_packet_bytes=prior_packet_bytes,
            require_current_runtime=False,
        )
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_RETURN", str(exc)) from exc
    returned_quotient = _prior_return_member(prior_return_bytes, MAP_QUOTIENT_PATH)
    if returned_quotient != prior_quotient_bytes:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_QUOTIENT_BINDING", MAP_QUOTIENT_PATH)
    return return_manifest.runtime_source_sha256


def _source_digest(
    *,
    source_sha256: str | None,
    source_bytes: bytes | None,
) -> str:
    if source_bytes is not None:
        computed = sha256_bytes(source_bytes)
        if source_sha256 is not None and source_sha256 != computed:
            raise ZipJobRefusal("REFUSE_MAP_DELTA_SOURCE_DIGEST")
        return computed
    if source_sha256 is None:
        return runtime_source_sha256()
    try:
        return _digest(source_sha256, label="source_sha256")
    except ValueError as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_SOURCE_DIGEST", str(exc)) from exc


def build_map_delta(
    *,
    prior_map_bytes: bytes,
    prior_packet_bytes: bytes,
    prior_return_bytes: bytes,
    prior_quotient_bytes: bytes,
    operation_id: str,
    operation_result: str,
    operation_result_bytes: bytes,
    required_tool_ids: Sequence[str],
    boundary_facts: Iterable[MapFact | Mapping[str, Any]] = (),
    refusal_facts: Iterable[MapFact | Mapping[str, Any]] = (),
    replay_facts: Iterable[MapFact | Mapping[str, Any]] = (),
    no_write_facts: Iterable[MapFact | Mapping[str, Any]] = (),
    source_sha256: str | None = None,
    source_bytes: bytes | None = None,
) -> bytes:
    """Build one deterministic map delta without modifying any input.

    The prior packet, verified return, and exact quotient are all checked
    before an artifact is emitted.  A negative result additionally requires
    explicit refusal and no-write observations.  This is intentionally a
    narrow evidence operation, not a semantic admission decision.
    """

    prior_runtime_source = _validate_prior_artifacts(
        prior_map_bytes=prior_map_bytes,
        prior_packet_bytes=prior_packet_bytes,
        prior_return_bytes=prior_return_bytes,
        prior_quotient_bytes=prior_quotient_bytes,
    )
    if not isinstance(operation_result_bytes, bytes):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_RESULT_TYPE")
    if not isinstance(operation_id, str) or not _ID.fullmatch(operation_id):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_OPERATION_ID", str(operation_id))
    if not isinstance(operation_result, str) or not _OPERATION_RESULT.fullmatch(operation_result):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_OPERATION_RESULT", str(operation_result))
    if isinstance(required_tool_ids, (str, bytes)):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_REQUIRED_TOOLS", "string_not_sequence")
    try:
        tool_ids = sorted(set(required_tool_ids))
    except (TypeError, ValueError) as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_REQUIRED_TOOLS", str(exc)) from exc
    if any(not isinstance(tool_id, str) or not _ID.fullmatch(tool_id) for tool_id in tool_ids):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_REQUIRED_TOOLS")
    source = _source_digest(source_sha256=source_sha256, source_bytes=source_bytes)
    if prior_runtime_source != source:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_SOURCE_DRIFT")
    observations = MapObservationBuckets(
        boundary=_facts("boundary", boundary_facts),
        refusal=_facts("refusal", refusal_facts),
        replay=_facts("replay", replay_facts),
        no_write=_facts("no_write", no_write_facts),
    )
    body = {
        "schema": MAP_DELTA_SCHEMA,
        "base_map_sha256": sha256_bytes(prior_map_bytes),
        "prior_packet_sha256": sha256_bytes(prior_packet_bytes),
        "prior_return_sha256": sha256_bytes(prior_return_bytes),
        "prior_quotient_sha256": sha256_bytes(prior_quotient_bytes),
        "operation_id": operation_id,
        "operation_result": operation_result,
        "operation_result_sha256": sha256_bytes(operation_result_bytes),
        "required_tool_ids": tool_ids,
        "observations": observations.model_dump(mode="json"),
        "source_sha256": source,
        "append_only": True,
        "claim_ceiling": MAP_DELTA_CLAIM_CEILING,
    }
    body["delta_sha256"] = sha256_bytes(canonical_json_bytes(body))
    try:
        delta = MapDelta.model_validate(body, strict=True)
    except ValidationError as exc:
        detail = str(exc.errors(include_url=False))
        if "undeclared tool facts" in detail:
            raise ZipJobRefusal("REFUSE_MAP_DELTA_TOOL_UNDECLARED", detail) from exc
        if "replay fact" in detail:
            raise ZipJobRefusal("REFUSE_MAP_DELTA_REPLAY_UNPROVED", detail) from exc
        if "refusal fact" in detail:
            raise ZipJobRefusal("REFUSE_MAP_DELTA_REFUSAL_UNPROVED", detail) from exc
        if "no-write fact" in detail:
            raise ZipJobRefusal("REFUSE_MAP_DELTA_NO_WRITE_UNPROVED", detail) from exc
        raise ZipJobRefusal("REFUSE_MAP_DELTA_INVALID", detail) from exc
    return canonical_json_bytes(delta.model_dump(mode="json", by_alias=True))


def validate_map_delta(delta_bytes: bytes) -> MapDelta:
    """Validate a delta and its content hash without applying it."""

    try:
        raw = strict_json_loads(delta_bytes, label="map_delta")
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_JSON", str(exc)) from exc
    if not isinstance(raw, dict):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_SCHEMA", "not_object")
    provided = raw.get("delta_sha256")
    body = dict(raw)
    body.pop("delta_sha256", None)
    if not isinstance(provided, str) or not _HEX64.fullmatch(provided):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_DIGEST_MISMATCH", "missing_or_invalid")
    if sha256_bytes(canonical_json_bytes(body)) != provided:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_DIGEST_MISMATCH")
    try:
        return MapDelta.model_validate(raw, strict=True)
    except ValidationError as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_SCHEMA", str(exc.errors(include_url=False))) from exc


def apply_map_delta(prior_map_bytes: bytes, delta_bytes: bytes) -> bytes:
    """Append a validated delta to exactly its matching prior map.

    The input bytes are never changed in place.  Applying a delta to a
    different or already-advanced map fails closed, so a replay cannot create
    a second accepted history entry.
    """

    delta = validate_map_delta(delta_bytes)
    if not isinstance(prior_map_bytes, bytes):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_MAP_TYPE")
    actual_base = sha256_bytes(prior_map_bytes)
    if actual_base != delta.base_map_sha256:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_STALE_BASE", actual_base)
    if delta.prior_quotient_sha256 != actual_base:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_QUOTIENT_BASE_MISMATCH")
    try:
        raw = strict_json_loads(prior_map_bytes, label="prior_map")
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_MAP_JSON", str(exc)) from exc
    if not isinstance(raw, dict):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_PRIOR_MAP_SHAPE")
    history = raw.get("map_delta_history", [])
    if not isinstance(history, list) or any(not isinstance(item, dict) for item in history):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_HISTORY_SHAPE")
    if any(item.get("delta_sha256") == delta.delta_sha256 for item in history):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_REPLAY_DUPLICATE")
    previous_head = raw.get("map_delta_head_sha256")
    if history and previous_head != history[-1].get("delta_sha256"):
        raise ZipJobRefusal("REFUSE_MAP_DELTA_HISTORY_HEAD")
    updated = copy.deepcopy(raw)
    updated["map_delta_history"] = [*history, delta.model_dump(mode="json", by_alias=True)]
    updated["map_delta_head_sha256"] = delta.delta_sha256
    updated["map_delta_count"] = len(updated["map_delta_history"])
    updated["map_delta_append_only"] = True
    return canonical_json_bytes(updated)


__all__ = [
    "MAP_DELTA_CLAIM_CEILING",
    "MAP_DELTA_SCHEMA",
    "MapDelta",
    "MapFact",
    "apply_map_delta",
    "build_map_delta",
    "make_map_fact",
    "validate_map_delta",
]
