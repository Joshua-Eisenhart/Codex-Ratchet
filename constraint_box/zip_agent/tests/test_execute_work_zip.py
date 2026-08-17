from __future__ import annotations

import io
import json
import zipfile

import pytest

from constraintbox_zip_agent.execute_work_zip import build_execute_work_zip_packet
from constraintbox_zip_agent.failure_wave import build_demo_packet
from constraintbox_zip_agent.protocol import ZipJobRefusal, sha256_bytes
from constraintbox_zip_agent.runtime import execute_packet


def _auth(work_zip: bytes, *, execute: bool = True) -> dict:
    return {
        "schema": "constraintbox.work-zip-execute.v1",
        "execute": execute,
        "work_zip_sha256": sha256_bytes(work_zip),
        "source": "separate_execute_operation",
    }


def test_execute_requires_separate_authorization() -> None:
    work = build_demo_packet()
    packet = build_execute_work_zip_packet(work_zip=work, authorization=_auth(work, execute=False))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_WORK_ZIP_EXECUTE_NOT_AUTHORIZED"


def test_execute_refuses_one_bit_auth() -> None:
    packet = build_execute_work_zip_packet(
        work_zip=build_demo_packet(),
        authorization={"schema": "constraintbox.work-zip-execute.v1", "execute": True},
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_WORK_ZIP_EXECUTE_SCHEMA"


def test_execute_refuses_confirm_flag() -> None:
    work = build_demo_packet()
    auth = _auth(work)
    auth["confirm_execute"] = True
    packet = build_execute_work_zip_packet(work_zip=work, authorization=auth)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_WORK_ZIP_EXECUTE_SCHEMA"


def test_execute_refuses_digest_mismatch() -> None:
    work = build_demo_packet()
    auth = _auth(work)
    auth["work_zip_sha256"] = "0" * 64
    packet = build_execute_work_zip_packet(work_zip=work, authorization=auth)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_WORK_ZIP_EXECUTE_BINDING"


def test_execute_refuses_non_packet_work_zip() -> None:
    work = b"PK\x03\x04not-a-cb-packet"
    packet = build_execute_work_zip_packet(work_zip=work, authorization=_auth(work))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_WORK_ZIP_NOT_PACKET"


def test_execute_refuses_executor_recursion() -> None:
    inner_work = build_demo_packet()
    inner = build_execute_work_zip_packet(work_zip=inner_work, authorization=_auth(inner_work))
    packet = build_execute_work_zip_packet(work_zip=inner, authorization=_auth(inner))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_WORK_ZIP_EXECUTOR_RECURSION"


def test_separate_execute_runs_a_real_packet() -> None:
    work = build_demo_packet()
    packet = build_execute_work_zip_packet(work_zip=work, authorization=_auth(work))
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/execute_receipt.json"))
        inner = archive.read("output/work.return.zip")
    assert receipt["executed"] is True
    assert receipt["promotion_allowed"] is False
    assert inner.startswith(b"PK")
