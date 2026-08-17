"""Independent byte replay for a deliberately small local-operation cohort.

This verifier is not a generic provenance oracle.  It only re-executes
operations explicitly classified as local and replay-safe, under the current
runtime source, and compares the complete canonical return ZIP bytes.
Provider, child, ledger, and arbitrary Python operations are intentionally
outside this cohort.
"""

from __future__ import annotations

from .operation_ids import KNOWN_OPERATION_IDS
from .protocol import (
    ZipJobRefusal,
    ZipReturnManifest,
    sha256_bytes,
    validate_packet,
    validate_return_zip,
)


REPLAY_SAFE_OPERATION_IDS = frozenset(
    {
        "canonical_json_sha256_v1",
        "text_sha256_v1",
    }
)


def packet_replay_is_supported(packet_bytes: bytes) -> bool:
    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    operations = {task.operation for task in packet.tasks}
    return bool(operations) and operations.issubset(REPLAY_SAFE_OPERATION_IDS)


def verify_return_by_replay(
    packet_bytes: bytes,
    return_bytes: bytes,
) -> ZipReturnManifest:
    """Re-execute one replay-safe packet and require the exact return bytes."""

    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    operations = sorted({task.operation for task in packet.tasks})
    unsafe = [operation for operation in operations if operation not in REPLAY_SAFE_OPERATION_IDS]
    if unsafe:
        raise ZipJobRefusal("HOLD_RETURN_REPLAY_OPERATION_UNSAFE", ",".join(unsafe))
    observed = validate_return_zip(
        return_bytes,
        expected_input_sha256=sha256_bytes(packet_bytes),
        input_packet_bytes=packet_bytes,
        require_current_runtime=True,
    )
    from .runtime import execute_packet

    replay = execute_packet(packet_bytes)
    if replay.return_zip_bytes != return_bytes:
        raise ZipJobRefusal("REFUSE_RETURN_REPLAY_MISMATCH")
    if replay.return_zip_sha256 != sha256_bytes(return_bytes):
        raise ZipJobRefusal("REFUSE_RETURN_REPLAY_DIGEST_MISMATCH")
    if replay.job_id != observed.job_id or replay.task_count != len(packet.tasks):
        raise ZipJobRefusal("REFUSE_RETURN_REPLAY_BINDING_MISMATCH")
    return observed


__all__ = [
    "REPLAY_SAFE_OPERATION_IDS",
    "packet_replay_is_supported",
    "verify_return_by_replay",
]
