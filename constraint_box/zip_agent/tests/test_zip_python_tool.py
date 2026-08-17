from __future__ import annotations

import pytest

from constraintbox_zip_agent.failure_wave import _manifest, _task
from constraintbox_zip_agent.protocol import ZipJobRefusal, build_packet, canonical_json_bytes
from constraintbox_zip_agent.runtime import execute_packet
from constraintbox_zip_agent.zip_python_tool import (
    DEFAULT_MAKE_TOKEN_PY,
    SANDBOX_EXEC,
    choose_containment,
)


def _packet(*, script: bytes = DEFAULT_MAKE_TOKEN_PY, payload: bytes | None = None) -> bytes:
    files = {
        "00_RUN_ME_FIRST.md": b"# zip python tool\n",
        "TOOLS/make_token.py": script,
        "inputs/tool_payload.json": payload or canonical_json_bytes({"z": 1, "a": [3, 2]}),
        "tasks/00_tool.task.json": _task(
            task_id="run-tool",
            sequence=0,
            operation="run_zip_python_tool_v1",
            inputs=["TOOLS/make_token.py", "inputs/tool_payload.json"],
            outputs=["output/tool_evidence.json"],
        ),
    }
    return build_packet(
        _manifest(
            job_id="zip-python-tool",
            task_paths=["tasks/00_tool.task.json"],
            outputs=["output/tool_evidence.json"],
            operations=["run_zip_python_tool_v1"],
        ),
        files,
    )


def test_declared_python_tool_runs_and_emits_token() -> None:
    result = execute_packet(_packet())
    from constraintbox_zip_agent.protocol import sha256_bytes, strict_json_loads
    import zipfile, io

    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        evidence = strict_json_loads(archive.read("output/tool_evidence.json"), label="evidence")
    assert evidence["schema"] == "constraintbox.zip-python-tool-evidence.v2"
    assert evidence["script_path"] == "TOOLS/make_token.py"
    assert evidence["script_sha256"] == sha256_bytes(DEFAULT_MAKE_TOKEN_PY)
    assert len(evidence["canonical_sha256"]) == 64
    assert evidence["canonical_sha256"] == evidence["result_sha256"]
    assert evidence["untrusted_tool_claim_sha256"] != evidence["canonical_sha256"]
    assert "tool_reported_canonical_sha256" not in evidence
    assert evidence["returncode"] == 0
    assert evidence["env_scrubbed"] is True
    chosen = choose_containment()
    assert evidence["containment_profile"] == chosen["containment_profile"]
    assert evidence["network_denied"] is chosen["network_denied"]
    assert evidence["os_sandbox"] is chosen["os_sandbox"]
    assert evidence["containment_hold"] is chosen["containment_hold"]
    assert evidence["host_hooks_used"] is False


def test_tool_missing_output_is_refused() -> None:
    script = b"from pathlib import Path\nPath('output').mkdir(exist_ok=True)\n"
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(script=script))
    assert caught.value.reason_code == "REFUSE_ZIP_PYTHON_TOOL_MISSING_OUTPUT"


def test_tool_outside_tools_root_is_refused() -> None:
    files = {
        "00_RUN_ME_FIRST.md": b"# zip python tool\n",
        "scripts/make_token.py": DEFAULT_MAKE_TOKEN_PY,
        "inputs/tool_payload.json": b'{"a":1}',
        "tasks/00_tool.task.json": _task(
            task_id="run-tool",
            sequence=0,
            operation="run_zip_python_tool_v1",
            inputs=["scripts/make_token.py", "inputs/tool_payload.json"],
            outputs=["output/tool_evidence.json"],
        ),
    }
    packet = build_packet(
        _manifest(
            job_id="zip-python-tool-bad-path",
            task_paths=["tasks/00_tool.task.json"],
            outputs=["output/tool_evidence.json"],
            operations=["run_zip_python_tool_v1"],
        ),
        files,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_ZIP_PYTHON_TOOL_PATH"


def test_parent_escape_tool_path_is_refused() -> None:
    files = {
        "00_RUN_ME_FIRST.md": b"# zip python tool\n",
        "TOOLS/../escape.py": DEFAULT_MAKE_TOKEN_PY,
        "inputs/tool_payload.json": b'{"a":1}',
        "tasks/00_tool.task.json": _task(
            task_id="run-tool",
            sequence=0,
            operation="run_zip_python_tool_v1",
            inputs=["TOOLS/../escape.py", "inputs/tool_payload.json"],
            outputs=["output/tool_evidence.json"],
        ),
    }
    with pytest.raises(ZipJobRefusal) as caught:
        build_packet(
            _manifest(
                job_id="zip-python-tool-escape",
                task_paths=["tasks/00_tool.task.json"],
                outputs=["output/tool_evidence.json"],
                operations=["run_zip_python_tool_v1"],
            ),
            files,
        )
    assert caught.value.reason_code == "REFUSE_UNSAFE_PATH"


def test_tool_does_not_inherit_host_home() -> None:
    script = b"""
from pathlib import Path
import json, os, hashlib
home = os.environ.get("HOME", "")
assert "joshuaeisenhart" not in home
assert os.environ.get("CODEX_HOME") is None
assert os.environ.get("PYTHONPATH") is None
assert "/.local/" not in os.environ.get("PATH", "")
assert "/Users/joshuaeisenhart" not in os.environ.get("PATH", "")
token = hashlib.sha256(b"env-scrub").hexdigest()
Path("output").mkdir(exist_ok=True)
Path("output/tool_result.json").write_text(
    json.dumps({"canonical_sha256": token}) + "\\n", encoding="utf-8"
)
"""
    result = execute_packet(_packet(script=script))
    assert result.return_zip_bytes


def test_non_hex_tool_token_is_refused() -> None:
    script = b"""
from pathlib import Path
Path("output").mkdir(exist_ok=True)
Path("output/tool_result.json").write_text(
    '{"canonical_sha256":"' + ("g" * 64) + '"}\\n', encoding="utf-8"
)
"""
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(script=script))
    assert caught.value.reason_code == "REFUSE_ZIP_PYTHON_TOOL_RESULT"


def test_outbound_network_tool_is_refused_when_sandbox_exists() -> None:
    script = b"""
import socket
socket.create_connection(("1.1.1.1", 443), timeout=2)
"""
    if choose_containment()["containment_profile"] != "seatbelt":
        pytest.skip("seatbelt not selected")
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(script=script))
    assert caught.value.reason_code == "REFUSE_ZIP_PYTHON_TOOL_FAILED"


def test_ambient_host_marker_does_not_substitute_for_seatbelt(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_SANDBOX", "seatbelt")
    chosen = choose_containment()
    assert chosen["containment_profile"] == "seatbelt"
    assert chosen["network_denied"] is True
    result = execute_packet(_packet())
    import io, zipfile
    from constraintbox_zip_agent.protocol import strict_json_loads

    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        evidence = strict_json_loads(archive.read("output/tool_evidence.json"), label="evidence")
    assert evidence["containment_profile"] == "seatbelt"
    assert evidence["ambient_host_sandbox_marker"] == "env:CODEX_SANDBOX"


def test_declared_python_tool_refuses_when_sandbox_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "constraintbox_zip_agent.zip_python_tool.SANDBOX_EXEC",
        __import__("pathlib").Path("/definitely/missing/sandbox-exec"),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet())
    assert caught.value.reason_code == "REFUSE_ZIP_PYTHON_TOOL_SANDBOX_UNAVAILABLE"
