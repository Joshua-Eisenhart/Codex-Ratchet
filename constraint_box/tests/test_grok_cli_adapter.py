from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from constraintbox.grok_cli_adapter import (
    REQUEST_SCHEMA,
    GrokCliAdapterError,
    authenticate,
    run,
)
from constraintbox.mmm_load_gate import MmmLoadError

from test_mmm_load_gate import mmm_bind


def _runner(path: Path, *, returncode: int = 0) -> Path:
    path.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' '{\"model\":\"test-model\",\"text\":\"ok\",\"stopReason\":\"end_turn\"}'\n"
        f"exit {returncode}\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def test_model_usage_keys_are_observed(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    runner.write_text(
        "#!/bin/sh\nprintf '%s\\n' '{\"text\":\"ok\",\"stopReason\":\"end_turn\",\"modelUsage\":{\"test-model\":{\"modelCalls\":1}}}'\n",
        encoding="utf-8",
    )
    runner.chmod(0o700)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(tmp_path / "request.json", runner, prompt, tmp_path)
    receipt = run(request, response_path=tmp_path / "response.json", timeout_seconds=5)
    assert receipt["models_observed_in_output"] == ["test-model"]
    assert receipt["model_binding_confirmed"] is True
    assert receipt["semantic_completion_confirmed"] is True


def _request(
    path: Path,
    runner: Path,
    prompt: Path,
    cwd: Path,
    *,
    hierarchy: bool = False,
    bind_mmm: bool = True,
) -> Path:
    request = {
        "schema": REQUEST_SCHEMA,
        "request_id": "adapter-test",
        "runner_path": str(runner),
        "model": "test-model",
        "prompt_path": str(prompt),
        "cwd": str(cwd),
        "max_turns": 1,
        "permission_mode": "plan",
    }
    if bind_mmm:
        request.update(mmm_bind(prompt))
    if hierarchy:
        request.update(
            {
                "hierarchy_bound": True,
                "parent_id": "child-council",
                "wave_id": "wave-1",
                "round": 1,
                "depth": 2,
            }
        )
    path.write_text(
        json.dumps(request, sort_keys=True),
        encoding="utf-8",
    )
    return path


def test_bounded_call_captures_model_and_response(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(tmp_path / "request.json", _runner(tmp_path / "runner"), prompt, tmp_path)
    response = tmp_path / "response.json"
    receipt = run(request, response_path=response, timeout_seconds=5)
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["model_binding_confirmed"] is True
    assert receipt["models_observed_in_output"] == ["test-model"]
    assert receipt["prompt_sha256"]
    assert response.read_bytes()
    assert "--no-subagents" in receipt["argv"]
    assert "--permission-mode" in receipt["argv"]
    assert receipt["permission_mode_requested"] == "plan"
    assert receipt["dispatch_lease"]["revoked"] is True
    assert not Path(receipt["dispatch_lease"]["nonce_file"]).exists()


def test_workspace_write_permission_is_explicit_request_data(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(tmp_path / "request.json", _runner(tmp_path / "runner"), prompt, tmp_path)
    body = json.loads(request.read_text(encoding="utf-8"))
    body["permission_mode"] = "bypassPermissions"
    request.write_text(json.dumps(body), encoding="utf-8")
    receipt = run(request, response_path=tmp_path / "response.json", timeout_seconds=5)
    mode_index = receipt["argv"].index("--permission-mode")
    assert receipt["argv"][mode_index + 1] == "bypassPermissions"
    assert receipt["permission_mode_requested"] == "bypassPermissions"


def test_zip_leaf_hierarchy_is_accepted_and_bound(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(
        tmp_path / "request.json",
        _runner(tmp_path / "runner"),
        prompt,
        tmp_path,
        hierarchy=True,
    )
    receipt = run(request, response_path=tmp_path / "response.json", timeout_seconds=5)
    assert {key: receipt[key] for key in ("hierarchy_bound", "parent_id", "wave_id", "round", "depth")} == {
        "hierarchy_bound": True,
        "parent_id": "child-council",
        "wave_id": "wave-1",
        "round": 1,
        "depth": 2,
    }


def test_provider_build_usage_suffix_is_bound_without_model_slug_in_source(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner"
    runner.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' "
        "'{\"text\":\"ok\",\"stopReason\":\"end_turn\","
        "\"modelUsage\":{\"test-model-build\":{\"modelCalls\":1}}}'\n",
        encoding="utf-8",
    )
    runner.chmod(0o700)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(tmp_path / "request.json", runner, prompt, tmp_path)

    receipt = run(request, response_path=tmp_path / "response.json", timeout_seconds=5)

    assert receipt["disposition"] == "OBSERVED"
    assert receipt["models_observed_in_output"] == ["test-model-build"]
    assert receipt["model_binding_basis"] == "provider_build_usage_suffix"


def test_nonzero_is_hold(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(
        tmp_path / "request.json",
        _runner(tmp_path / "runner", returncode=3),
        prompt,
        tmp_path,
    )
    receipt = run(request, response_path=tmp_path / "response.json", timeout_seconds=5)
    assert receipt["disposition"] == "HOLD"
    assert receipt["returncode"] == 3


def test_cancelled_zero_exit_is_hold(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    runner.write_text(
        "#!/bin/sh\nprintf '%s\\n' '{\"model\":\"test-model\",\"text\":\"partial\",\"stopReason\":\"cancelled\"}'\n",
        encoding="utf-8",
    )
    runner.chmod(0o700)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(tmp_path / "request.json", runner, prompt, tmp_path)
    receipt = run(request, response_path=tmp_path / "response.json", timeout_seconds=5)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_GROK_CLI_INCOMPLETE"
    assert receipt["stop_reason"] == "cancelled"
    assert receipt["semantic_completion_confirmed"] is False


def test_refuses_unbounded_turn_count(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    request = _request(tmp_path / "request.json", _runner(tmp_path / "runner"), prompt, tmp_path)
    body = json.loads(request.read_text(encoding="utf-8"))
    body["max_turns"] = 99
    request.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(GrokCliAdapterError, match="1..16"):
        run(request, response_path=tmp_path / "response.json")


def test_oauth_authentication_withholds_ambient_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = tmp_path / "runner"
    runner.write_text(
        "#!/bin/sh\n"
        "if [ -n \"${XAI_API_KEY+x}\" ]; then exit 9; fi\n"
        "test \"$1\" = login || exit 8\n"
        "test \"$2\" = --oauth || exit 7\n",
        encoding="utf-8",
    )
    runner.chmod(0o700)
    auth = tmp_path / "auth.json"
    auth.write_text("not-a-real-token", encoding="utf-8")
    auth.chmod(0o600)
    monkeypatch.setenv("XAI_API_KEY", "depleted-route")

    receipt = authenticate(runner, mode="oauth", auth_path=auth, timeout_seconds=5)

    assert receipt["disposition"] == "AUTHENTICATED"
    assert receipt["ambient_api_key_withheld"] is True
    assert receipt["auth_file_present"] is True
    assert receipt["auth_file_owner_only"] is True


def test_authentication_holds_without_auth_file(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    runner.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    runner.chmod(0o700)

    receipt = authenticate(
        runner,
        mode="device-code",
        auth_path=tmp_path / "missing-auth.json",
        timeout_seconds=5,
    )

    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_GROK_AUTH_FILE_MISSING"


def test_missing_mmm_refuses_before_spawn(tmp_path: Path) -> None:
    sentinel = tmp_path / "spawned"
    runner = tmp_path / "runner"
    runner.write_text(f"#!/bin/sh\nprintf spawned > '{sentinel}'\n", encoding="utf-8")
    runner.chmod(0o700)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("no packs", encoding="utf-8")
    with pytest.raises(MmmLoadError) as caught:
        run(
            _request(
                tmp_path / "request.json",
                runner,
                prompt,
                tmp_path,
                bind_mmm=False,
            ),
            response_path=tmp_path / "response.json",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "REFUSE_MMM_LOAD_MISSING"
    assert not sentinel.exists()


def test_confirmed_mmm_is_bound_on_observed_receipt(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    receipt = run(
        _request(tmp_path / "request.json", _runner(tmp_path / "runner"), prompt, tmp_path),
        response_path=tmp_path / "response.json",
        timeout_seconds=5,
    )
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["mmm_load_confirmed"] is True
    assert receipt["mmm_packs"] == ["nominalist", "smt"]
    assert receipt["mmm_sha256"]
