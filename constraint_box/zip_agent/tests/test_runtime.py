from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from constraintbox_zip_agent.cache import cache_result
from constraintbox_zip_agent.cli import main
from constraintbox_zip_agent.failure_wave import (
    CLAIM_CEILING,
    _manifest,
    _task,
    build_demo_packet,
    build_failure_wave_packet,
)
from constraintbox_zip_agent.operation_ids import KNOWN_OPERATION_IDS
from constraintbox_zip_agent.protocol import (
    MANIFEST_PATH,
    MAX_MEMBER_BYTES,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    deterministic_zip,
    runtime_source_sha256,
    sha256_bytes,
    validate_packet,
    validate_return_zip,
)
from constraintbox_zip_agent.runtime import execute_packet
from constraintbox_zip_agent.self_audit import mutation_cases


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}


def _rebuild(packet: bytes, mutate_manifest) -> bytes:
    entries = _entries(packet)
    manifest = json.loads(entries.pop(MANIFEST_PATH))
    manifest.pop("file_sha256_registry")
    mutate_manifest(manifest, entries)
    return build_packet(manifest, entries)


def _rebuild_return(return_zip: bytes, mutate) -> bytes:
    entries = _entries(return_zip)
    manifest = json.loads(entries.pop("RETURN_MANIFEST.json"))
    mutate(manifest, entries)
    manifest["file_sha256_registry"] = {
        path: sha256_bytes(data) for path, data in sorted(entries.items())
    }
    entries["RETURN_MANIFEST.json"] = canonical_json_bytes(manifest)
    return deterministic_zip(entries)


def test_demo_packet_validates_and_runs() -> None:
    packet = build_demo_packet()
    validated = validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    result = execute_packet(packet)
    assert validated.manifest.job_id == "zip-agent-demo"
    assert result.input_packet_sha256 == sha256_bytes(packet)
    returned = validate_return_zip(result.return_zip_bytes, expected_input_sha256=sha256_bytes(packet))
    assert returned.disposition == "ZIP_JOB_EXECUTED_LOCAL"
    assert returned.runtime_source_sha256 == runtime_source_sha256()


def test_execution_is_byte_identical_on_replay() -> None:
    packet = build_demo_packet()
    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    assert first.return_zip_sha256 == second.return_zip_sha256
    assert deterministic_zip(_entries(packet)) == packet
    assert deterministic_zip(_entries(first.return_zip_bytes)) == first.return_zip_bytes


def test_packet_with_trailing_bytes_is_refused() -> None:
    packet = build_demo_packet()
    with pytest.raises(ZipJobRefusal) as caught:
        validate_packet(packet + b"JUNK", known_operations=set(KNOWN_OPERATION_IDS))
    assert caught.value.reason_code == "REFUSE_NON_CANONICAL_ZIP"


def test_return_with_trailing_bytes_is_refused() -> None:
    packet = build_demo_packet()
    returned = execute_packet(packet).return_zip_bytes
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(returned + b"JUNK", input_packet_bytes=packet)
    assert caught.value.reason_code == "REFUSE_NON_CANONICAL_ZIP"


def test_mid_run_runtime_source_drift_holds(monkeypatch) -> None:
    packet = build_demo_packet()
    values = iter(["a" * 64, "b" * 64])
    monkeypatch.setattr(
        "constraintbox_zip_agent.runtime.runtime_source_sha256",
        lambda: next(values),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_RETURN_RUNTIME_SOURCE_DRIFT"
    assert caught.value.detail == "mid_run"


def test_execution_refuses_its_own_oversized_return(monkeypatch) -> None:
    packet = build_demo_packet()

    def oversized(task, _workspace):
        return {task.output_paths[0]: b"x" * (MAX_MEMBER_BYTES + 1)}

    monkeypatch.setattr("constraintbox_zip_agent.runtime.run_local_operation", oversized)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MEMBER_SIZE_LIMIT"


@pytest.mark.parametrize("case", sorted(mutation_cases(build_demo_packet())))
def test_mutations_refuse_with_exact_reason(case: str) -> None:
    mutant, expected = mutation_cases(build_demo_packet())[case]
    with pytest.raises(ZipJobRefusal) as caught:
        validate_packet(mutant, known_operations=set(KNOWN_OPERATION_IDS))
    assert caught.value.reason_code == expected


def test_failure_does_not_write_authoritative_output(tmp_path: Path, capsys) -> None:
    broken = tmp_path / "broken.zip"
    destination = tmp_path / "must-not-exist.return.zip"
    broken.write_bytes(b"not a zip")
    assert main(["run", str(broken), "--return-zip", str(destination)]) == 2
    assert not destination.exists()
    assert json.loads(capsys.readouterr().out)["authoritative_output_written"] is False


def test_cli_refuses_input_output_alias(tmp_path: Path, capsys) -> None:
    packet_path = tmp_path / "same.zip"
    packet_path.write_bytes(build_demo_packet())
    before = packet_path.read_bytes()
    assert main(["run", str(packet_path), "--return-zip", str(packet_path)]) == 2
    assert packet_path.read_bytes() == before
    assert json.loads(capsys.readouterr().out)["disposition"] == "REFUSE_INPUT_OUTPUT_ALIAS"


def test_output_cannot_alias_an_input_member() -> None:
    task_path = "tasks/00_bad.task.json"
    files = {
        "00_RUN_ME_FIRST.md": b"run",
        "inputs/value.json": b"{}",
        task_path: _task(
            task_id="bad",
            sequence=0,
            operation="canonical_json_sha256_v1",
            inputs=["inputs/value.json"],
            outputs=["output/value.json"],
        ),
        "output/value.json": b"preexisting",
    }
    packet = build_packet(
        _manifest(
            job_id="alias-negative",
            task_paths=[task_path],
            outputs=["output/value.json"],
            operations=["canonical_json_sha256_v1"],
        ),
        files,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    assert caught.value.reason_code == "REFUSE_OUTPUT_ALIAS"


def test_nonfinite_json_is_refused_at_operation_boundary() -> None:
    packet = build_demo_packet()

    def mutate(_manifest, files):
        files["inputs/payload.json"] = b'{"x":NaN}'

    bad = _rebuild(packet, mutate)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(bad)
    assert caught.value.reason_code == "REFUSE_INVALID_JSON"


def test_preload_is_held_until_a_connector_exists() -> None:
    task_path = "tasks/00_model.task.json"
    output_path = "output/result.json"
    task = json.loads(
        _task(
            task_id="model-task",
            sequence=0,
            operation="text_sha256_v1",
            inputs=["inputs/prompt.txt"],
            outputs=[output_path],
        )
    )
    task["preload_files"] = ["context/voice.mmm"]
    packet = build_packet(
        _manifest(
            job_id="preload-hold",
            task_paths=[task_path],
            outputs=[output_path],
            operations=["text_sha256_v1"],
        ),
        {
            "00_RUN_ME_FIRST.md": b"run",
            "inputs/prompt.txt": b"prompt",
            "context/voice.mmm": b"salience only",
            task_path: canonical_json_bytes(task),
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_MODEL_CONNECTOR_UNBOUND"


def test_return_tamper_is_refused() -> None:
    result = execute_packet(build_demo_packet())
    entries = _entries(result.return_zip_bytes)
    entries["output/canonical.json"] += b"tamper"
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(deterministic_zip(entries))
    assert caught.value.reason_code == "REFUSE_RETURN_DIGEST_MISMATCH"


def test_return_extra_output_is_refused_even_when_registry_is_coherent() -> None:
    result = execute_packet(build_demo_packet())

    def mutate(_manifest, entries):
        entries["output/extra.json"] = b"{}"

    forged = _rebuild_return(result.return_zip_bytes, mutate)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(forged)
    assert caught.value.reason_code == "REFUSE_RETURN_OUTPUT_SET_MISMATCH"


def test_return_receipt_rebinding_is_refused_against_input_packet() -> None:
    packet = build_demo_packet()
    result = execute_packet(packet)

    def mutate(_manifest, entries):
        path = "receipts/00_canonicalize.json"
        receipt = json.loads(entries[path])
        receipt["operation"] = "text_sha256_v1"
        entries[path] = canonical_json_bytes(receipt)

    forged = _rebuild_return(result.return_zip_bytes, mutate)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(forged, input_packet_bytes=packet)
    assert caught.value.reason_code == "REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH"


def test_return_source_drift_is_held() -> None:
    result = execute_packet(build_demo_packet())

    def mutate(manifest, _entries):
        manifest["runtime_source_sha256"] = "0" * 64

    forged = _rebuild_return(result.return_zip_bytes, mutate)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(forged)
    assert caught.value.reason_code == "HOLD_RETURN_RUNTIME_SOURCE_DRIFT"


def test_task_parameters_are_refused_until_operation_schema_exists() -> None:
    packet = build_demo_packet()

    def mutate(_manifest, files):
        path = "tasks/00_canonicalize.task.json"
        task = json.loads(files[path])
        task["parameters"] = {"ignored": True}
        files[path] = canonical_json_bytes(task)

    changed = _rebuild(packet, mutate)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(changed)
    assert caught.value.reason_code == "REFUSE_OPERATION_PARAMETERS_UNSUPPORTED"


def test_cache_failure_occurs_before_external_return_write(tmp_path: Path, capsys) -> None:
    packet_path = tmp_path / "input.zip"
    return_path = tmp_path / "return.zip"
    bad_cache = tmp_path / "cache-is-file"
    packet_path.write_bytes(build_demo_packet())
    bad_cache.write_text("not a directory", encoding="utf-8")
    rc = main(
        [
            "run",
            str(packet_path),
            "--return-zip",
            str(return_path),
            "--cache-dir",
            str(bad_cache),
        ]
    )
    assert rc == 2
    assert not return_path.exists()
    assert json.loads(capsys.readouterr().out)["authoritative_output_written"] is False


def test_unsupported_cache_refuses_before_execution(tmp_path: Path, capsys, monkeypatch) -> None:
    packet_path = tmp_path / "input.zip"
    return_path = tmp_path / "return.zip"
    packet_path.write_bytes(build_failure_wave_packet(build_demo_packet()))
    calls: list[bytes] = []

    def forbidden_execute(packet: bytes):
        calls.append(packet)
        raise AssertionError("executor must not run for an unsupported cache request")

    monkeypatch.setattr("constraintbox_zip_agent.cli.execute_packet", forbidden_execute)
    rc = main(
        [
            "run",
            str(packet_path),
            "--return-zip",
            str(return_path),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert calls == []
    assert output["disposition"] == "HOLD_CACHE_REPLAY_UNSUPPORTED"
    assert output["authoritative_output_written"] is False
    assert not return_path.exists()


def test_cache_is_content_addressed_single_row_and_append_only(tmp_path: Path) -> None:
    packet = build_demo_packet()
    result = execute_packet(packet)
    db_path = cache_result(tmp_path, packet, result)
    cache_result(tmp_path, packet, result)
    connection = sqlite3.connect(db_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM zip_run_cache").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE zip_run_cache SET job_id='changed'")
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM zip_run_cache")
    finally:
        connection.close()


def test_cache_refuses_invalid_result_before_any_object_write(tmp_path: Path) -> None:
    packet = build_demo_packet()
    result = execute_packet(packet)
    forged = replace(
        result,
        job_id="forged-job",
        return_zip_bytes=b"not-a-return",
        return_zip_sha256=sha256_bytes(b"not-a-return"),
        task_count=999,
    )
    with pytest.raises(ZipJobRefusal):
        cache_result(tmp_path, packet, forged)
    assert not (tmp_path / "objects").exists()
    assert not (tmp_path / "index.sqlite3").exists()


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("return_zip_sha256", "0" * 64, "REFUSE_CACHE_RETURN_DIGEST_MISMATCH"),
        ("job_id", "wrong-job", "REFUSE_CACHE_JOB_ID_MISMATCH"),
        ("task_count", 99, "REFUSE_CACHE_TASK_COUNT_MISMATCH"),
    ],
)
def test_cache_refuses_rebound_result_fields_before_write(
    tmp_path: Path,
    field: str,
    value: object,
    reason: str,
) -> None:
    packet = build_demo_packet()
    result = execute_packet(packet)
    forged = replace(result, **{field: value})
    with pytest.raises(ZipJobRefusal) as caught:
        cache_result(tmp_path, packet, forged)
    assert caught.value.reason_code == reason
    assert not (tmp_path / "objects").exists()


def test_cache_refuses_self_consistent_forged_return_by_replay(tmp_path: Path) -> None:
    packet = build_demo_packet()
    result = execute_packet(packet)

    def mutate(_manifest, entries):
        output_path = "output/canonical.json"
        receipt_path = "receipts/00_canonicalize.json"
        entries[output_path] = b'{"forged":true}'
        receipt = json.loads(entries[receipt_path])
        receipt["output_sha256"][output_path] = sha256_bytes(entries[output_path])
        entries[receipt_path] = canonical_json_bytes(receipt)

    forged_return = _rebuild_return(result.return_zip_bytes, mutate)
    forged = replace(
        result,
        return_zip_bytes=forged_return,
        return_zip_sha256=sha256_bytes(forged_return),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        cache_result(tmp_path, packet, forged)
    assert caught.value.reason_code == "REFUSE_RETURN_REPLAY_MISMATCH"
    assert not (tmp_path / "objects").exists()
    assert not (tmp_path / "index.sqlite3").exists()


def test_cache_holds_non_replay_safe_operation_before_any_write(
    tmp_path: Path,
    monkeypatch,
) -> None:
    packet = build_demo_packet()
    result = execute_packet(packet)
    monkeypatch.setattr(
        "constraintbox_zip_agent.cache.packet_replay_is_supported",
        lambda _packet_bytes: False,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        cache_result(tmp_path, packet, result)
    assert caught.value.reason_code == "HOLD_CACHE_REPLAY_UNSUPPORTED"
    assert not (tmp_path / "objects").exists()
    assert not (tmp_path / "index.sqlite3").exists()


def test_manifest_claim_ceiling_is_literal() -> None:
    packet = validate_packet(build_demo_packet(), known_operations=set(KNOWN_OPERATION_IDS))
    assert packet.manifest.claim_ceiling == CLAIM_CEILING
