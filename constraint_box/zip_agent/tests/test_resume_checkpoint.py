from __future__ import annotations

from constraintbox_zip_agent.protocol import sha256_bytes, validate_packet, validate_return_zip
from constraintbox_zip_agent.resume_checkpoint import build_resume_checkpoint_packet
from constraintbox_zip_agent.runtime import execute_packet


LEDGER = {
    "disposition": "PROJECT_LEDGER_VERIFIED",
    "event_count": 7,
    "head_sha256": "a" * 64,
    "objects_verified": True,
    "promotion_allowed": False,
}


def _packet(
    material: bytes = b"current state\n",
    captured_at: str = "2026-08-17T00:00:00Z",
) -> bytes:
    return build_resume_checkpoint_packet(
        materials={"state/current.md": material, "state/status.json": b'{"status":"HOLD"}\n'},
        ledger_binding=LEDGER,
        next_actions=["verify", "resume"],
        captured_at=captured_at,
    )


def test_resume_checkpoint_is_deterministic_and_return_is_input_bound() -> None:
    packet = _packet()
    assert packet == _packet()
    validated = validate_packet(packet)
    assert validated.manifest.job_id.startswith("cb-resume-")
    result = execute_packet(packet)
    returned = validate_return_zip(result.return_zip_bytes, input_packet_bytes=packet)
    assert returned.input_packet_sha256 == sha256_bytes(packet)


def test_material_change_changes_checkpoint_identity() -> None:
    before = _packet(b"current state\n")
    after = _packet(b"changed state\n")
    assert sha256_bytes(before) != sha256_bytes(after)
    assert validate_packet(before).manifest.job_id != validate_packet(after).manifest.job_id
    later = _packet(b"current state\n", "2026-08-17T00:00:01Z")
    assert validate_packet(before).manifest.job_id != validate_packet(later).manifest.job_id


def test_unverified_ledger_is_refused_before_packet_build() -> None:
    bad = {**LEDGER, "objects_verified": False}
    try:
        build_resume_checkpoint_packet(
            materials={"state.md": b"state\n"},
            ledger_binding=bad,
            next_actions=["stop"],
            captured_at="2026-08-17T00:00:00Z",
        )
    except ValueError as exc:
        assert "objects" in str(exc)
    else:
        raise AssertionError("unverified ledger was accepted")
