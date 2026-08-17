from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from .operation_ids import KNOWN_OPERATION_IDS
from .protocol import ZipJobRefusal, sha256_bytes, validate_packet, validate_return_zip
from .replay_verifier import packet_replay_is_supported, verify_return_by_replay
from .runtime import ExecutionResult


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def cache_result(cache_root: Path, packet_bytes: bytes, result: ExecutionResult) -> Path:
    cache_root = cache_root.resolve()
    packet_sha = sha256_bytes(packet_bytes)
    if packet_sha != result.input_packet_sha256:
        raise ZipJobRefusal("REFUSE_CACHE_INPUT_DIGEST_MISMATCH")
    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    actual_return_sha = sha256_bytes(result.return_zip_bytes)
    if actual_return_sha != result.return_zip_sha256:
        raise ZipJobRefusal("REFUSE_CACHE_RETURN_DIGEST_MISMATCH")
    if not packet_replay_is_supported(packet_bytes):
        raise ZipJobRefusal("HOLD_CACHE_REPLAY_UNSUPPORTED")
    returned = verify_return_by_replay(packet_bytes, result.return_zip_bytes)
    if returned.job_id != result.job_id or packet.manifest.job_id != result.job_id:
        raise ZipJobRefusal("REFUSE_CACHE_JOB_ID_MISMATCH")
    if result.task_count != len(packet.tasks):
        raise ZipJobRefusal("REFUSE_CACHE_TASK_COUNT_MISMATCH")
    input_path = cache_root / "objects" / f"{packet_sha}.input.zip"
    return_path = cache_root / "objects" / f"{actual_return_sha}.return.zip"
    if input_path.exists() and input_path.read_bytes() != packet_bytes:
        raise ZipJobRefusal("REFUSE_CACHE_OBJECT_COLLISION", input_path.name)
    if return_path.exists() and return_path.read_bytes() != result.return_zip_bytes:
        raise ZipJobRefusal("REFUSE_CACHE_OBJECT_COLLISION", return_path.name)
    db_path = cache_root / "index.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS zip_run_cache (
                input_sha256 TEXT PRIMARY KEY,
                return_sha256 TEXT NOT NULL,
                job_id TEXT NOT NULL,
                input_path TEXT NOT NULL,
                return_path TEXT NOT NULL,
                claim_ceiling TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS zip_run_cache_no_update
            BEFORE UPDATE ON zip_run_cache BEGIN SELECT RAISE(ABORT, 'zip_run_cache_append_only'); END;
            CREATE TRIGGER IF NOT EXISTS zip_run_cache_no_delete
            BEFORE DELETE ON zip_run_cache BEGIN SELECT RAISE(ABORT, 'zip_run_cache_append_only'); END;
            """
        )
        existing = connection.execute(
            "SELECT return_sha256, job_id, input_path, return_path FROM zip_run_cache WHERE input_sha256=?",
            (packet_sha,),
        ).fetchone()
        row = (actual_return_sha, result.job_id, str(input_path), str(return_path))
        if existing is not None and tuple(existing) != row:
            raise ZipJobRefusal("REFUSE_CACHE_INDEX_COLLISION", packet_sha)
        if not input_path.exists():
            _atomic_write(input_path, packet_bytes)
        if not return_path.exists():
            _atomic_write(return_path, result.return_zip_bytes)
        if existing is None:
            connection.execute(
                "INSERT INTO zip_run_cache VALUES (?, ?, ?, ?, ?, ?)",
                (
                    packet_sha,
                    actual_return_sha,
                    result.job_id,
                    str(input_path),
                    str(return_path),
                    "cache_and_index_only;not_admission;not_release",
                ),
            )
        connection.commit()
    finally:
        connection.close()
    return db_path
