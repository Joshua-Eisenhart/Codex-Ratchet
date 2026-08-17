from __future__ import annotations

import io
import json
import zipfile

import pytest

from constraintbox_zip_agent.nested_lean_cycle import (
    CHILD_JOB_ID,
    LINEAGE_PATH,
    PARENT_JOB_ID,
    SUBCHILD_JOB_ID,
    build_and_execute_nested_lean_cycle,
    build_nested_lean_cycle,
    execute_nested_lean_cycle,
    validate_nested_lean_packet,
)
from constraintbox_zip_agent.protocol import (
    MANIFEST_PATH,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    validate_return_zip,
)
from constraintbox_zip_agent.runtime import execute_packet


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }


def _rebuild_packet(packet: bytes, mutate) -> bytes:
    entries = _entries(packet)
    manifest = json.loads(entries.pop(MANIFEST_PATH))
    manifest.pop("file_sha256_registry")
    mutate(manifest, entries)
    return build_packet(manifest, entries)


def test_executable_model_free_parent_child_subchild_cycle() -> None:
    execution = build_and_execute_nested_lean_cycle()
    cycle = execution.cycle
    parent_return = _entries(execution.result.return_zip_bytes)

    assert cycle.parent_job_id == PARENT_JOB_ID
    assert cycle.child_job_id == CHILD_JOB_ID
    assert cycle.subchild_job_id == SUBCHILD_JOB_ID
    assert (cycle.parent_depth, cycle.child_depth, cycle.subchild_depth) == (0, 1, 2)
    assert execution.result.task_count == 1
    assert parent_return["output/child.return.zip"]
    assert execution.retained_child_return_sha256 == sha256_bytes(
        parent_return["output/child.return.zip"]
    )

    child_return = _entries(parent_return["output/child.return.zip"])
    assert child_return["output/subchild.return.zip"]
    assert execution.retained_subchild_return_sha256 == sha256_bytes(
        child_return["output/subchild.return.zip"]
    )

    # The nested return is independently bound to the exact child and subchild
    # packet bytes, not merely accepted because it is a valid ZIP.
    parent_members = _entries(cycle.packet_bytes)
    child_packet = parent_members["children/child.zip"]
    subchild_packet = _entries(child_packet)["children/subchild.zip"]
    validate_return_zip(
        execution.result.return_zip_bytes,
        input_packet_bytes=cycle.packet_bytes,
    )
    validate_return_zip(
        parent_return["output/child.return.zip"],
        input_packet_bytes=child_packet,
    )
    validate_return_zip(
        child_return["output/subchild.return.zip"],
        input_packet_bytes=subchild_packet,
    )


def test_lineage_is_explicit_and_bounded() -> None:
    cycle = build_nested_lean_cycle()
    parent = validate_nested_lean_packet(cycle.packet_bytes)
    parent_members = _entries(parent.packet_bytes)
    parent_lineage = json.loads(parent_members[LINEAGE_PATH])
    child_packet = parent_members["children/child.zip"]
    child_members = _entries(child_packet)
    child_lineage = json.loads(child_members[LINEAGE_PATH])
    subchild_packet = child_members["children/subchild.zip"]
    subchild_lineage = json.loads(_entries(subchild_packet)[LINEAGE_PATH])

    assert parent_lineage == {
        "schema": "constraintbox.nested_lineage.v1",
        "job_id": PARENT_JOB_ID,
        "parent_job_id": None,
        "depth": 0,
        "allowed_child_job_ids": [CHILD_JOB_ID],
    }
    assert child_lineage["parent_job_id"] == PARENT_JOB_ID
    assert child_lineage["depth"] == 1
    assert child_lineage["allowed_child_job_ids"] == [SUBCHILD_JOB_ID]
    assert subchild_lineage["parent_job_id"] == CHILD_JOB_ID
    assert subchild_lineage["depth"] == 2
    assert subchild_lineage["allowed_child_job_ids"] == []


def test_nested_cycle_replays_byte_identically() -> None:
    packet = build_nested_lean_cycle().packet_bytes
    first = execute_nested_lean_cycle(packet)
    second = execute_nested_lean_cycle(packet)
    assert first.result.return_zip_bytes == second.result.return_zip_bytes
    assert first.result.return_zip_sha256 == second.result.return_zip_sha256


def test_missing_child_packet_is_refused() -> None:
    cycle = build_nested_lean_cycle()

    def remove_child(_manifest, entries):
        del entries["children/child.zip"]

    missing = _rebuild_packet(cycle.packet_bytes, remove_child)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_nested_lean_cycle(missing)
    assert caught.value.reason_code == "REFUSE_NESTED_CHILD_PACKET_MISSING"


def test_forged_child_job_id_is_refused_by_runtime_and_lineage_wrapper() -> None:
    cycle = build_nested_lean_cycle()
    parent_entries = _entries(cycle.packet_bytes)
    child_packet = parent_entries["children/child.zip"]

    def forge_child(manifest, _entries):
        manifest["job_id"] = "forged-child"

    forged_child = _rebuild_packet(child_packet, forge_child)

    def replace_child(_manifest, entries):
        entries["children/child.zip"] = forged_child

    forged_parent = _rebuild_packet(cycle.packet_bytes, replace_child)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(forged_parent)
    assert caught.value.reason_code == "REFUSE_CHILD_DECLARATION_MISMATCH"

    with pytest.raises(ZipJobRefusal) as caught:
        execute_nested_lean_cycle(forged_parent)
    assert caught.value.reason_code == "REFUSE_NESTED_CHILD_ID"


def test_forged_parent_lineage_is_refused_before_execution() -> None:
    cycle = build_nested_lean_cycle()

    def forge_lineage(_manifest, entries):
        lineage = json.loads(entries[LINEAGE_PATH])
        lineage["depth"] = 1
        entries[LINEAGE_PATH] = canonical_json_bytes(lineage)

    forged = _rebuild_packet(cycle.packet_bytes, forge_lineage)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_nested_lean_cycle(forged)
    assert caught.value.reason_code == "REFUSE_NESTED_PARENT_LINEAGE"
