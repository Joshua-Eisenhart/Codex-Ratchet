from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
from functools import lru_cache

import pytest

from constraintbox_zip_agent.protocol import ZipJobRefusal, canonical_json_bytes, runtime_source_sha256
from constraintbox_zip_agent.runtime import execute_packet
from constraintbox_zip_agent.tool_field_delta import (
    apply_map_delta,
    build_map_delta,
    make_map_fact,
    validate_map_delta,
)
from constraintbox_zip_agent.work_cycle import build_work_cycle_packet


def _tool(distribution: str, import_name: str) -> dict[str, object]:
    return {
        "locked_distribution": distribution,
        "locked_version": importlib.metadata.version(distribution),
        "import_names": [import_name],
    }


@lru_cache(maxsize=1)
def _map_material() -> tuple[bytes, bytes, bytes]:
    packet = build_work_cycle_packet(
        prompt=b"A map-consuming operation must preserve negative evidence.",
        tool_manifest=json.dumps(
            {
                "tools": [
                    _tool("jsonschema", "jsonschema"),
                    _tool("pydantic", "pydantic"),
                    _tool("sympy", "sympy"),
                ]
            }
        ).encode(),
        prior_field_summary=json.dumps(
            {"tool_projection": [{"tool_id": "sympy", "observations": 3}]}
        ).encode(),
        seed=29,
        jobs=2,
        pair_samples=2,
    )
    returned = execute_packet(packet).return_zip_bytes
    with __import__("zipfile").ZipFile(io.BytesIO(returned), "r") as archive:
        quotient = archive.read("output/measured_quotient.json")
    return quotient, packet, returned


def _fact(kind: str, tool_id: str, *, observed: bool = True) -> dict[str, object]:
    evidence = hashlib.sha256(f"{kind}:{tool_id}:{observed}".encode()).hexdigest()
    return make_map_fact(
        fact_kind=kind,  # type: ignore[arg-type]
        tool_id=tool_id,
        observed=observed,
        evidence_sha256=evidence,
        detail=f"observed {kind} for {tool_id}",
    )


def _build(
    *,
    operation_result: str = "ACCEPTED",
    replay: list[dict[str, object]] | None = None,
    refusal: list[dict[str, object]] | None = None,
    no_write: list[dict[str, object]] | None = None,
    boundary: list[dict[str, object]] | None = None,
    required_tools: list[str] | None = None,
    quotient: bytes | None = None,
    packet: bytes | None = None,
    returned: bytes | None = None,
    source_sha256: str | None = None,
) -> bytes:
    map_bytes, map_packet, map_return = _map_material()
    return build_map_delta(
        prior_map_bytes=map_bytes,
        prior_packet_bytes=packet or map_packet,
        prior_return_bytes=returned or map_return,
        prior_quotient_bytes=quotient or map_bytes,
        operation_id="render_human_oracle_v2",
        operation_result=operation_result,
        operation_result_bytes=b"deterministic operation result",
        required_tool_ids=required_tools or ["jsonschema", "pydantic"],
        boundary_facts=boundary if boundary is not None else [_fact("boundary", "pydantic")],
        refusal_facts=refusal if refusal is not None else [_fact("refusal", "jsonschema")],
        replay_facts=replay if replay is not None else [_fact("replay", "pydantic")],
        no_write_facts=no_write if no_write is not None else [_fact("no_write", "jsonschema")],
        source_sha256=source_sha256 or runtime_source_sha256(),
    )


def test_delta_is_deterministic_and_appends_without_mutating_base() -> None:
    first = _build()
    second = _build()
    assert first == second
    delta = validate_map_delta(first)
    map_bytes, _, _ = _map_material()
    updated = apply_map_delta(map_bytes, first)
    assert updated != map_bytes
    assert json.loads(map_bytes) == json.loads(_map_material()[0])
    result = json.loads(updated)
    assert result["map_delta_count"] == 1
    assert result["map_delta_head_sha256"] == delta.delta_sha256
    assert result["map_delta_history"][0]["delta_sha256"] == delta.delta_sha256


def test_replaying_same_delta_on_same_base_is_byte_stable() -> None:
    delta = _build()
    map_bytes, _, _ = _map_material()
    assert apply_map_delta(map_bytes, delta) == apply_map_delta(map_bytes, delta)


def test_stale_or_advanced_base_is_refused() -> None:
    delta = _build()
    map_bytes, _, _ = _map_material()
    stale = canonical_json_bytes({**json.loads(map_bytes), "changed_by_other_run": True})
    with pytest.raises(ZipJobRefusal) as caught:
        apply_map_delta(stale, delta)
    assert caught.value.reason_code == "REFUSE_MAP_DELTA_STALE_BASE"
    advanced = apply_map_delta(map_bytes, delta)
    with pytest.raises(ZipJobRefusal) as caught_again:
        apply_map_delta(advanced, delta)
    assert caught_again.value.reason_code == "REFUSE_MAP_DELTA_STALE_BASE"


def test_tampered_delta_is_refused_before_any_map_write() -> None:
    delta = json.loads(_build())
    delta["operation_result"] = "REFUSED"
    tampered = canonical_json_bytes(delta)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_map_delta(tampered)
    assert caught.value.reason_code == "REFUSE_MAP_DELTA_DIGEST_MISMATCH"


def test_undeclared_tool_fact_is_refused() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        _build(boundary=[_fact("boundary", "not-declared")])
    assert caught.value.reason_code == "REFUSE_MAP_DELTA_TOOL_UNDECLARED"


def test_replay_evidence_is_required() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        _build(replay=[])
    assert caught.value.reason_code == "REFUSE_MAP_DELTA_REPLAY_UNPROVED"


def test_negative_result_requires_refusal_and_no_write_evidence() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        _build(operation_result="REFUSED", refusal=[_fact("refusal", "jsonschema")], no_write=[])
    assert caught.value.reason_code == "REFUSE_MAP_DELTA_NO_WRITE_UNPROVED"

    with pytest.raises(ZipJobRefusal) as caught_false:
        _build(
            operation_result="REFUSED",
            refusal=[_fact("refusal", "jsonschema")],
            no_write=[_fact("no_write", "jsonschema", observed=False)],
        )
    assert caught_false.value.reason_code == "REFUSE_MAP_DELTA_NO_WRITE_UNPROVED"


def test_negative_result_with_explicit_refusal_and_no_write_can_append() -> None:
    delta = _build(
        operation_result="REFUSED",
        refusal=[_fact("refusal", "jsonschema")],
        no_write=[_fact("no_write", "jsonschema")],
    )
    map_bytes, _, _ = _map_material()
    updated = apply_map_delta(map_bytes, delta)
    assert json.loads(updated)["map_delta_history"][0]["operation_result"] == "REFUSED"


def test_mismatched_packet_or_quotient_cannot_bind_a_delta() -> None:
    map_bytes, packet, returned = _map_material()
    with pytest.raises(ZipJobRefusal) as caught_packet:
        _build(packet=packet + b"tamper")
    assert caught_packet.value.reason_code == "REFUSE_MAP_DELTA_PRIOR_RETURN"

    altered_quotient = canonical_json_bytes({**json.loads(map_bytes), "altered": True})
    with pytest.raises(ZipJobRefusal) as caught_quotient:
        _build(quotient=altered_quotient)
    assert caught_quotient.value.reason_code == "REFUSE_MAP_DELTA_QUOTIENT_BASE_MISMATCH"
    assert returned


def test_source_drift_is_refused_even_when_the_digest_is_well_formed() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        _build(source_sha256="f" * 64)
    assert caught.value.reason_code == "REFUSE_MAP_DELTA_SOURCE_DRIFT"
