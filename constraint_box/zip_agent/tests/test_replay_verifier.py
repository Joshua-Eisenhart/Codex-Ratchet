from __future__ import annotations

import io
import json
import zipfile

import pytest

from constraintbox_zip_agent.failure_wave import build_demo_packet
from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
)
from constraintbox_zip_agent.replay_verifier import verify_return_by_replay
from constraintbox_zip_agent.runtime import execute_packet


def _forged_return(return_bytes: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(return_bytes), "r") as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    manifest = json.loads(entries.pop("RETURN_MANIFEST.json"))
    output_path = "output/canonical.json"
    receipt_path = "receipts/00_canonicalize.json"
    entries[output_path] = b'{"forged":true}'
    receipt = json.loads(entries[receipt_path])
    receipt["output_sha256"][output_path] = sha256_bytes(entries[output_path])
    entries[receipt_path] = canonical_json_bytes(receipt)
    manifest["file_sha256_registry"] = {
        path: sha256_bytes(data) for path, data in sorted(entries.items())
    }
    entries["RETURN_MANIFEST.json"] = canonical_json_bytes(manifest)
    return deterministic_zip(entries)


def test_replay_verifier_accepts_exact_local_return() -> None:
    packet = build_demo_packet()
    returned = execute_packet(packet).return_zip_bytes
    manifest = verify_return_by_replay(packet, returned)
    assert manifest.job_id == "zip-agent-demo"


def test_replay_verifier_refuses_self_consistent_forged_return() -> None:
    packet = build_demo_packet()
    forged = _forged_return(execute_packet(packet).return_zip_bytes)
    with pytest.raises(ZipJobRefusal) as caught:
        verify_return_by_replay(packet, forged)
    assert caught.value.reason_code == "REFUSE_RETURN_REPLAY_MISMATCH"


def test_replay_verifier_refuses_non_replay_safe_operation() -> None:
    packet = build_demo_packet()
    with zipfile.ZipFile(io.BytesIO(packet), "r") as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    manifest = json.loads(entries.pop("ZIP_JOB_MANIFEST.json"))
    task_path = manifest["task_execution_order"][0]
    task = json.loads(entries[task_path])
    task["operation"] = "run_provider_call_v1"
    entries[task_path] = canonical_json_bytes(task)
    manifest["allowed_operations"] = ["run_provider_call_v1"]
    manifest["file_sha256_registry"] = {
        path: sha256_bytes(data) for path, data in sorted(entries.items())
    }
    entries["ZIP_JOB_MANIFEST.json"] = canonical_json_bytes(manifest)
    unsafe_packet = deterministic_zip(entries)
    with pytest.raises(ZipJobRefusal) as caught:
        verify_return_by_replay(unsafe_packet, execute_packet(packet).return_zip_bytes)
    assert caught.value.reason_code == "HOLD_RETURN_REPLAY_OPERATION_UNSAFE"
