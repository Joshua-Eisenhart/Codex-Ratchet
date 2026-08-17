from __future__ import annotations

import importlib.metadata
import io
import json
import zipfile

from constraintbox_zip_agent.protocol import validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet
from constraintbox_zip_agent.work_cycle import EVENT_OUTPUTS, build_work_cycle_packet


def _tool(distribution: str, import_name: str) -> dict[str, object]:
    return {
        "locked_distribution": distribution,
        "locked_version": importlib.metadata.version(distribution),
        "import_names": [import_name],
    }


def _packet() -> bytes:
    manifest = {
        "tools": [
            _tool("jsonschema", "jsonschema"),
            _tool("pydantic", "pydantic"),
            _tool("sympy", "sympy"),
        ]
    }
    prior = {
        "tool_projection": [
            {"tool_id": "sympy", "observations": 17, "local_centrality": 0.75}
        ]
    }
    return build_work_cycle_packet(
        prompt=b"Treat this sentence as source material, not canon.",
        tool_manifest=json.dumps(manifest).encode(),
        prior_field_summary=json.dumps(prior).encode(),
        seed=7,
        jobs=2,
        pair_samples=3,
    )


def _member(return_zip: bytes, path: str) -> dict[str, object]:
    with zipfile.ZipFile(io.BytesIO(return_zip), "r") as archive:
        return json.loads(archive.read(path))


def _event_count(return_zip: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(return_zip), "r") as archive:
        assert set(EVENT_OUTPUTS).issubset(archive.namelist())
        return sum(len(archive.read(path).splitlines()) for path in EVENT_OUTPUTS)


def test_zip_work_cycle_runs_real_process_probes_and_preserves_claim_ceiling() -> None:
    packet = _packet()
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    cycle = _member(result.return_zip_bytes, "output/work_cycle.json")
    quotient = _member(result.return_zip_bytes, "output/measured_quotient.json")
    coupled = _member(result.return_zip_bytes, "output/entropy_topology.json")
    assert cycle["tool_count"] == 3
    assert cycle["event_count"] == 15
    assert _event_count(result.return_zip_bytes) == cycle["event_count"]
    assert cycle["disposition"] == "HOLD_FIELD_INCOMPLETE"
    assert cycle["promotion_allowed"] is False
    assert quotient["ranking_summary"] == {
        "operation_mapped": 1,
        "generic_only_unranked": 2,
    }
    assert quotient["rankings"][0]["tool_id"] == "sympy"
    assert quotient["rankings"][0]["operation_rank"] == 1
    assert all(row["operation_rank"] is None for row in quotient["rankings"][1:])
    assert sum(node["mass"] for node in coupled["class_nodes"]) == coupled["total_mass"]
    assert coupled["quotient_edges"]
    class_ids = {node["class_id"] for node in coupled["class_nodes"]}
    assert all(
        edge["source_class"] in class_ids and edge["target_class"] in class_ids
        for edge in coupled["quotient_edges"]
    )


def test_zip_work_cycle_replays_byte_identically() -> None:
    packet = _packet()
    assert execute_packet(packet).return_zip_bytes == execute_packet(packet).return_zip_bytes
