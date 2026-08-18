from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

import pytest

from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
    strict_json_loads,
    validate_return_zip,
)
from constraintbox_zip_agent.provider_task import build_provider_call_packet
from constraintbox_zip_agent.runtime import execute_packet

MARKER = "ZIP_PROVIDER_CALL_LIVE"
AGENT = b"role: write_one\noutput: output/finding.md\nWrite the marker.\n"
OBJECT = b"Write one finding line.\n"
TASK_SOURCE = b"# Provider fixture task\nWrite the declared finding.\n"
MMM_BUNDLE = b"\n\n<!-- MMM voice:test:compact -->\n# Test mini MMM\n"
COMPOSED_PROMPT = b"# MMM SALIENCE PRELOAD\n" + MMM_BUNDLE + b"\n\n# TASK\n" + TASK_SOURCE
BOX_ROOT = Path(__file__).resolve().parents[2]
CONTROLLER_SRC = BOX_ROOT / "src"
if not CONTROLLER_SRC.is_dir():
    CONTROLLER_SRC = BOX_ROOT / "integrated_system" / "runtime" / "controller_src"


def _preload() -> bytes:
    receipt = {
        "schema": "constraintbox.mmm-preload.v2",
        "disposition": "CONTENT_BOUND",
        "run_id": "provider-unit",
        "agent_id": "AGENTS/write_one.md",
        "parent_id": "root",
        "wave_id": "route-smoke",
        "round": 0,
        "depth": 0,
        "bundle_sha256": sha256_bytes(MMM_BUNDLE),
        "bundle_bytes": len(MMM_BUNDLE),
        "composed_prompt_sha256": sha256_bytes(COMPOSED_PROMPT),
        "composed_prompt_bytes": len(COMPOSED_PROMPT),
        "task_sha256": sha256_bytes(TASK_SOURCE),
        "sources": [{"primary_id": "voice:test:compact"}],
    }
    receipt["receipt_self_checksum"] = sha256_bytes(canonical_json_bytes(receipt))
    return canonical_json_bytes(receipt)


def _evidence(*, observed: str = "fixture-model") -> str:
    payload = {
        "schema": "constraintbox.fixture-provider-evidence.v1",
        "disposition": "OBSERVED",
        "model_requested": "fixture-model",
        "model_observed": observed,
        "model_binding_confirmed": observed == "fixture-model",
    }
    return repr(json.dumps(payload, sort_keys=True))


def _script(body: str, *, observed: str = "fixture-model", exit_code: int = 0) -> str:
    return (
        "import json\n"
        "from pathlib import Path\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        f"{body}\n"
        f"Path('meta/provider_evidence.json').write_text({_evidence(observed=observed)}, encoding='utf-8')\n"
        f"raise SystemExit({exit_code})\n"
    )


def _request(
    *,
    script: str | None = None,
    preload: bytes | None = None,
    provider: str = "fixture-subprocess",
    model_requested: str = "fixture-model",
    **provider_fields: object,
) -> bytes:
    preload_raw = _preload() if preload is None else preload
    request: dict[str, object] = {
        "schema": "constraintbox.provider-zip-task-request.v1",
        "run_id": "provider-unit",
        "agent_id": "AGENTS/write_one.md",
        "parent_id": "root",
        "wave_id": "route-smoke",
        "round_index": 0,
        "depth": 0,
        "preload_receipt_sha256": sha256_bytes(preload_raw),
        "provider": provider,
        "route_id": "fixture-local" if provider == "fixture-subprocess" else f"{provider}-local",
        "model_requested": model_requested,
        "expected_marker": MARKER,
        "timeout_seconds": 30,
    }
    if provider != "fixture-subprocess":
        # Live provider adapters are an explicit overlay dependency.  Tests
        # bind the current source tree just as a real request must.
        request["controller_src"] = str(CONTROLLER_SRC)
    if provider == "fixture-subprocess":
        request["fixture_script"] = script or _script(
            "Path('output/finding.md').write_text('finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')"
        )
    request.update(provider_fields)
    return json.dumps(request, sort_keys=True).encode("utf-8")


def _packet(
    *,
    script: str | None = None,
    preload: bytes | None = None,
    composed_prompt: bytes = COMPOSED_PROMPT,
    request: bytes | None = None,
) -> bytes:
    preload_raw = _preload() if preload is None else preload
    return build_provider_call_packet(
        request=request or _request(script=script, preload=preload_raw),
        agent=AGENT,
        object_bytes=OBJECT,
        preload_receipt=preload_raw,
        composed_prompt=composed_prompt,
        mmm_bundle=MMM_BUNDLE,
        task_source=TASK_SOURCE,
    )


def _grok_runner(
    path: Path,
    *,
    observed_model: str,
    stop_reason: str = "end_turn",
    exit_code: int = 0,
) -> Path:
    response = json.dumps(
        {"model": observed_model, "text": "bounded result", "stopReason": stop_reason}
    )
    path.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' '{response}'\n"
        "mkdir -p output && printf '%s\\n' 'finding: ZIP_PROVIDER_CALL_LIVE' > output/finding.md\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _claude_bridge(path: Path, *, observed_model: str, exit_code: int = 0) -> Path:
    path.write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--model'); p.add_argument('--prompt-file')\n"
        "p.add_argument('--budget'); p.add_argument('--timeout-sec')\n"
        "p.add_argument('--tools'); p.add_argument('--cwd')\n"
        "p.add_argument('--out-dir'); p.add_argument('--name'); p.add_argument('--effort')\n"
        "a = p.parse_args()\n"
        "cwd = Path(a.cwd); out_dir = Path(a.out_dir)\n"
        "(cwd / 'output').mkdir(parents=True, exist_ok=True)\n"
        "out_dir.mkdir(parents=True, exist_ok=True)\n"
        "(cwd / 'output' / 'finding.md').write_text('finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')\n"
        "output = out_dir / 'output.json'; receipt = out_dir / 'receipt.json'\n"
        "output.write_text(json.dumps({'ok': True}), encoding='utf-8')\n"
        "receipt.write_text(json.dumps({'model': "
        + repr(observed_model)
        + "}), encoding='utf-8')\n"
        "print(json.dumps({'parsed': {'models': ["
        + repr(observed_model)
        + "], 'total_cost_usd': 0.01}, 'output_path': str(output), 'receipt_path': str(receipt)}))\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _members(return_zip: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(return_zip), "r") as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _json(return_zip: bytes, path: str) -> dict[str, object]:
    return strict_json_loads(_members(return_zip)[path], label=path)


def test_provider_call_zip_task_runs_subprocess_and_binds_receipts() -> None:
    packet = _packet()
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    members = _members(result.return_zip_bytes)
    assert members["output/finding.md"] == b"finding: ZIP_PROVIDER_CALL_LIVE\n"
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    call = _json(result.return_zip_bytes, "output/provider_call.json")
    assert source["terminal_state"] == "COMPLETED"
    assert source["model_observed"] == "fixture-model"
    assert source["output_sha256"] == sha256_bytes(members["output/finding.md"])
    assert call["source_receipt_sha256"] == sha256_bytes(members["output/source_receipt.json"])
    assert call["schema"] == "constraintbox.provider-call.v1"
    assert call["provider_request_id"] == "fixture-local"
    assert call["composed_prompt_sha256"] == sha256_bytes(COMPOSED_PROMPT)
    assert call["preload_receipt_sha256"] == sha256_bytes(_preload())
    assert call["terminal_state"] == "COMPLETED"
    assert call["promotion_allowed"] is False


def test_provider_call_zip_task_replays_byte_identically_for_deterministic_fixture() -> None:
    packet = _packet()
    assert execute_packet(packet).return_zip_bytes == execute_packet(packet).return_zip_bytes


def test_provider_leaf_does_not_inherit_undeclared_host_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CB_TEST_HOST_SECRET", "must-not-cross-provider-boundary")
    packet = _packet(
        script=_script(
            "import os\n"
            "assert 'CB_TEST_HOST_SECRET' not in os.environ\n"
            "assert os.environ.get('PYTHONNOUSERSITE') == '1'\n"
            "Path('output/finding.md').write_text("
            "'finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')"
        )
    )
    execute_packet(packet)


def test_nested_provider_leaf_requires_parent_identity() -> None:
    request = json.loads(_request())
    request["depth"] = 1
    request["parent_id"] = None
    packet = _packet(request=canonical_json_bytes(request))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_REQUEST_SCHEMA"
    assert caught.value.detail == "parent_id"


def test_provider_call_zip_task_refuses_missing_output() -> None:
    packet = _packet(script=_script("pass"))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_MISSING_OUTPUT"


def test_provider_call_zip_task_refuses_marker_missing() -> None:
    packet = _packet(
        script=_script(
            "Path('output/finding.md').write_text('finding: wrong\\n', encoding='utf-8')"
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_MARKER_MISSING"


def test_provider_call_zip_task_refuses_nonzero_subprocess() -> None:
    packet = _packet(script=_script("pass", exit_code=7))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_SUBPROCESS_FAILED"


def test_provider_call_zip_task_refuses_forged_observed_model() -> None:
    packet = _packet(
        script=_script(
            "Path('output/finding.md').write_text('finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')",
            observed="forged-model",
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_MODEL_MISMATCH"


def test_provider_call_zip_task_refuses_missing_model_evidence() -> None:
    packet = _packet(
        script=(
            "from pathlib import Path\n"
            "Path('output').mkdir(exist_ok=True)\n"
            "Path('output/finding.md').write_text("
            "'finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')\n"
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_EVIDENCE_MISSING"


def test_provider_call_zip_task_refuses_request_supplied_observed_model() -> None:
    request = json.loads(_request())
    request["model_observed"] = "fixture-model"
    packet = _packet(request=json.dumps(request, sort_keys=True).encode())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_REQUEST_SCHEMA"


def test_provider_call_zip_task_refuses_preload_prompt_tamper() -> None:
    packet = _packet(composed_prompt=COMPOSED_PROMPT + b"tamper")
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_PRELOAD_BINDING"


def test_provider_call_zip_task_refuses_preload_receipt_tamper() -> None:
    preload = json.loads(_preload())
    preload["agent_id"] = "forged"
    preload_raw = canonical_json_bytes(preload)
    packet = _packet(preload=preload_raw)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_PRELOAD_BINDING"


def test_tampered_provider_receipt_return_is_refused() -> None:
    result = execute_packet(_packet())
    entries = _members(result.return_zip_bytes)
    source = json.loads(entries["output/source_receipt.json"])
    source["model_observed"] = "forged-model"
    entries["output/source_receipt.json"] = json.dumps(source, sort_keys=True).encode("utf-8")
    forged = deterministic_zip(entries)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(forged, expected_input_sha256=result.input_packet_sha256)
    assert caught.value.reason_code == "REFUSE_RETURN_DIGEST_MISMATCH"


def test_grok_adapter_receipt_is_normalized_into_provider_call(tmp_path: Path) -> None:
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="grok-test")
    packet = _packet(
        request=_request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
            max_turns=2,
        )
    )
    result = execute_packet(packet)
    members = _members(result.return_zip_bytes)
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    call = _json(result.return_zip_bytes, "output/provider_call.json")
    assert members["output/finding.md"] == b"finding: ZIP_PROVIDER_CALL_LIVE\n"
    assert source["provider"] == "grok-cli"
    assert source["model_requested"] == "grok-test"
    assert source["model_observed"] == "grok-test"
    assert call["provider_request_id"] == "grok-cli-local"
    assert call["model_requested"] == "grok-test"
    assert call["model_observed"] == "grok-test"
    assert call["terminal_state"] == "COMPLETED"
    assert call["source_receipt_sha256"] == sha256_bytes(members["output/source_receipt.json"])


def test_live_provider_without_declared_controller_is_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CB_CONTROLLER_SRC", raising=False)
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="grok-test")
    request = json.loads(
        _request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
        )
    )
    request.pop("controller_src", None)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=canonical_json_bytes(request)))
    assert caught.value.reason_code == "HOLD_PROVIDER_CONTROLLER_UNBOUND"


def test_codex_route_requires_explicit_runner_and_home(tmp_path: Path) -> None:
    request = json.loads(_request(provider="codex-cli", model_requested="codex-test"))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=canonical_json_bytes(request)))
    assert caught.value.reason_code == "REFUSE_PROVIDER_REQUEST_SCHEMA"
    assert caught.value.detail == "executable"


def test_grok_adapter_model_mismatch_holds_without_return_zip(tmp_path: Path) -> None:
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="other-model")
    packet = _packet(
        request=_request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "MODEL_BINDING" in caught.value.detail


def test_grok_adapter_hold_has_no_declared_finding(tmp_path: Path) -> None:
    runner = _grok_runner(
        tmp_path / "grok-runner",
        observed_model="grok-test",
        stop_reason="cancelled",
    )
    packet = _packet(
        request=_request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "INCOMPLETE" in caught.value.detail


def test_claude_adapter_receipt_is_normalized_into_provider_call(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-sonnet-5")
    packet = _packet(
        request=_request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    result = execute_packet(packet)
    members = _members(result.return_zip_bytes)
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    call = _json(result.return_zip_bytes, "output/provider_call.json")
    assert members["output/finding.md"] == b"finding: ZIP_PROVIDER_CALL_LIVE\n"
    assert source["provider"] == "claude-code"
    assert source["model_requested"] == "sonnet"
    assert source["model_observed"] == "claude-sonnet-5"
    assert call["provider_request_id"] == "claude-code-local"
    assert call["model_requested"] == "sonnet"
    assert call["model_observed"] == "claude-sonnet-5"
    assert call["terminal_state"] == "COMPLETED"
    assert call["source_receipt_sha256"] == sha256_bytes(members["output/source_receipt.json"])


def test_claude_adapter_model_mismatch_holds_without_return_zip(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-haiku-4-5")
    packet = _packet(
        request=_request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "MODEL_BINDING" in caught.value.detail


def test_claude_adapter_hold_has_no_declared_finding(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-sonnet-5", exit_code=3)
    packet = _packet(
        request=_request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "NONZERO" in caught.value.detail
